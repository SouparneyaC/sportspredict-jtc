"""
meta_model.py
=============
Problem-A meta-model diagnostic: rather than hand-tuning RULE1/RULE8/RULE12-style
blend weights between our_estimate and crowd_estimate, learn a context-aware blend
from the structural features already sitting in the master dataset (Elo gap, rest
days, squad value gap, which rules fired, draw probability).

This is a DIAGNOSTIC ONLY, in the same spirit as ml/platt_diagnostic.py: it never
touches live pricing. It fits candidate models, validates them out-of-sample two
ways (time-ordered walk-forward, and grouped k-fold by match), and compares their
Brier score against three baselines (crowd alone, our_estimate alone, naive 50/50
average). It only recommends adoption if the improvement is real and stable across
both validation schemes -- otherwise it says so honestly, the same way the Platt
diagnostic concluded "do not apply yet" at n=246.

Data constraint this script is designed around: after filtering to rows with a
submitted estimate, crowd estimate, and known outcome, there are only ~400 usable
rows clustered into ~42 matches (see conversation / MEMORY for the full data
audit). That is a small-data regime -- this script deliberately avoids anything
that isn't heavily regularized, and treats "the model looks better in-sample" as
worthless on its own.

Run from anywhere: python3 ml/meta_model.py
Outputs: ml/meta_model_results.json
"""

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

ROOT = Path(__file__).parent.parent
MASTER = ROOT / "datasets" / "master_question_dataset.csv"
OUT = Path(__file__).parent / "meta_model_results.json"

RULE_MIN_FIRE_COUNT = 10  # drop rule flags that fire fewer than this many times
BURN_IN_MATCHES = 21      # ~50% of 42 matches, mirrors the project's own 60/40-ish OOS splits


# ─── data loading ──────────────────────────────────────────────────────────────

def load_usable_rows():
    df = pd.read_csv(MASTER, low_memory=False)
    usable = df[
        (df["actually_submitted"] == True)
        & df["our_estimate"].notna()
        & df["crowd_estimate"].notna()
        & df["outcome"].notna()
    ].copy()
    return usable


def engineer_features(df):
    df = df.copy()
    df["gap"] = df["our_estimate"] - df["crowd_estimate"]
    df["abs_gap"] = df["gap"].abs()
    df["squad_value_diff_m"] = (df["squad_value_a_eur"] - df["squad_value_b_eur"]) / 1e6
    df["fifa_ranking_diff"] = df["fifa_ranking_2025_b"] - df["fifa_ranking_2025_a"]

    rule_cols = [c for c in df.columns if c.startswith("rule") and c.endswith("_fired")]
    kept_rule_cols = []
    for c in rule_cols:
        fired = (df[c] == True).sum()
        if fired >= RULE_MIN_FIRE_COUNT:
            df[c] = (df[c] == True).astype(float)
            kept_rule_cols.append(c)

    continuous_cols = [
        "our_estimate", "crowd_estimate", "gap", "abs_gap",
        "elo_diff", "rest_days_diff", "squad_value_diff_m",
        "fifa_ranking_diff", "draw_probability", "rule_fired_count",
    ]
    feature_cols = continuous_cols + kept_rule_cols
    return df, feature_cols, kept_rule_cols


# ─── baselines ─────────────────────────────────────────────────────────────────

def baseline_briers(df, mask=None):
    d = df if mask is None else df[mask]
    naive_avg = 0.5 * d["our_estimate"] + 0.5 * d["crowd_estimate"]
    return {
        "n": int(len(d)),
        "crowd_alone": float(brier_score_loss(d["outcome"], d["crowd_estimate"])),
        "our_estimate_alone": float(brier_score_loss(d["outcome"], d["our_estimate"])),
        "naive_50_50_avg": float(brier_score_loss(d["outcome"], naive_avg)),
    }


def estimate_rbp_scale(df):
    """rbp ~= S * (crowd_brier_term - our_brier_term), fit S through the origin
    from rows where rbp is actually recorded, so Brier improvements below can be
    translated into an expected-RBP-equivalent number."""
    d = df[df["rbp"].notna()].copy()
    crowd_term = (d["crowd_estimate"] - d["outcome"]) ** 2
    our_term = (d["our_estimate"] - d["outcome"]) ** 2
    x = (crowd_term - our_term).values
    y = d["rbp"].values
    denom = np.sum(x * x)
    if denom == 0:
        return None
    s = float(np.sum(x * y) / denom)
    return s


# ─── models ────────────────────────────────────────────────────────────────────

def make_logreg():
    return Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
        ("clf", LogisticRegression(C=0.3, max_iter=2000)),
    ])


def make_hgb():
    return HistGradientBoostingClassifier(
        max_depth=2, max_iter=60, learning_rate=0.05,
        l2_regularization=1.0, random_state=0,
    )


def fit_predict(model, X_train, y_train, X_test):
    model.fit(X_train, y_train)
    return model.predict_proba(X_test)[:, 1]


# ─── validation scheme 1: time-ordered walk-forward (expanding window) ────────

def walk_forward_oos(df, feature_cols, model_fn):
    match_order = (
        df.groupby("match")["date"].first().sort_values().index.tolist()
    )
    burn_in = set(match_order[:BURN_IN_MATCHES])
    test_matches = match_order[BURN_IN_MATCHES:]

    oos_idx, oos_pred = [], []
    for i, m in enumerate(test_matches):
        train_matches = set(match_order[: BURN_IN_MATCHES + i])
        train_mask = df["match"].isin(train_matches)
        test_mask = df["match"] == m

        X_train = df.loc[train_mask, feature_cols]
        y_train = df.loc[train_mask, "outcome"]
        X_test = df.loc[test_mask, feature_cols]

        model = model_fn()
        preds = fit_predict(model, X_train, y_train, X_test)
        oos_idx.extend(df.loc[test_mask].index.tolist())
        oos_pred.extend(preds.tolist())

    return pd.Series(oos_pred, index=oos_idx), burn_in, test_matches


# ─── validation scheme 2: grouped k-fold by match (robustness check) ──────────

def grouped_kfold_oos(df, feature_cols, model_fn, n_splits=6):
    groups = df["match"].values
    gkf = GroupKFold(n_splits=n_splits)
    oos_pred = pd.Series(index=df.index, dtype=float)

    for train_idx, test_idx in gkf.split(df, groups=groups):
        X_train, y_train = df.iloc[train_idx][feature_cols], df.iloc[train_idx]["outcome"]
        X_test = df.iloc[test_idx][feature_cols]
        model = model_fn()
        preds = fit_predict(model, X_train, y_train, X_test)
        oos_pred.iloc[test_idx] = preds

    return oos_pred


# ─── feature importance (fit once on full data, for interpretability only) ────

def logreg_coefficients(df, feature_cols):
    model = make_logreg()
    model.fit(df[feature_cols], df["outcome"])
    clf = model.named_steps["clf"]
    imputer = model.named_steps["impute"]
    # feature names after imputer's add_indicator may append missing-indicator columns
    n_indicator = clf.coef_.shape[1] - len(feature_cols)
    names = list(feature_cols) + [f"missing_indicator_{i}" for i in range(n_indicator)]
    coefs = clf.coef_[0]
    order = np.argsort(-np.abs(coefs))
    return [{"feature": names[i], "std_coef": float(coefs[i])} for i in order]


def hgb_importances(df, feature_cols):
    from sklearn.inspection import permutation_importance
    model = make_hgb()
    model.fit(df[feature_cols], df["outcome"])
    r = permutation_importance(model, df[feature_cols], df["outcome"],
                                scoring="neg_brier_score", n_repeats=20, random_state=0)
    order = np.argsort(-r.importances_mean)
    return [{"feature": feature_cols[i], "importance_mean": float(r.importances_mean[i])}
            for i in order]


# ─── main ──────────────────────────────────────────────────────────────────────

def main():
    df = load_usable_rows()
    df, feature_cols, kept_rule_cols = engineer_features(df)
    df = df.reset_index(drop=True)

    n_matches = df["match"].nunique()
    print(f"Usable rows: {len(df)}  |  unique matches: {n_matches}")
    print(f"Kept rule flags (fired >= {RULE_MIN_FIRE_COUNT}x): {kept_rule_cols}")

    overall_baseline = baseline_briers(df)
    rbp_scale = estimate_rbp_scale(df)
    print(f"\nOverall (in-sample) baselines: {overall_baseline}")
    print(f"Estimated RBP-per-Brier-unit scale S: {rbp_scale}")

    results = {
        "n_rows": len(df),
        "n_matches": n_matches,
        "feature_cols": feature_cols,
        "kept_rule_cols": kept_rule_cols,
        "overall_baseline_brier": overall_baseline,
        "rbp_scale_S": rbp_scale,
        "walk_forward": {},
        "grouped_kfold": {},
    }

    models = {"logreg": make_logreg, "hgb": make_hgb}

    # --- walk-forward ---
    print(f"\n=== Walk-forward (burn-in {BURN_IN_MATCHES} matches) ===")
    for name, fn in models.items():
        oos_pred, burn_in, test_matches = walk_forward_oos(df, feature_cols, fn)
        test_mask = df.index.isin(oos_pred.index)
        bl = baseline_briers(df, test_mask)
        model_brier = float(brier_score_loss(df.loc[oos_pred.index, "outcome"], oos_pred))
        improvement_vs_best_baseline = min(bl["crowd_alone"], bl["our_estimate_alone"], bl["naive_50_50_avg"]) - model_brier
        rbp_equiv = improvement_vs_best_baseline * rbp_scale * len(oos_pred) if rbp_scale else None
        print(f"[{name}] n_test={bl['n']}  model_brier={model_brier:.4f}  "
              f"baselines={bl}  improvement={improvement_vs_best_baseline:+.4f}  "
              f"est_RBP_equiv_over_test_set={rbp_equiv}")
        results["walk_forward"][name] = {
            "n_test": bl["n"], "model_brier": model_brier, "baselines": bl,
            "improvement_vs_best_baseline": improvement_vs_best_baseline,
            "est_rbp_equiv_over_test_set": rbp_equiv,
        }

    # --- grouped k-fold ---
    print(f"\n=== Grouped k-fold (6 folds, grouped by match) ===")
    full_baseline = baseline_briers(df)
    for name, fn in models.items():
        oos_pred = grouped_kfold_oos(df, feature_cols, fn)
        model_brier = float(brier_score_loss(df["outcome"], oos_pred))
        improvement_vs_best_baseline = min(full_baseline["crowd_alone"], full_baseline["our_estimate_alone"],
                                            full_baseline["naive_50_50_avg"]) - model_brier
        rbp_equiv = improvement_vs_best_baseline * rbp_scale * len(df) if rbp_scale else None
        print(f"[{name}] n_test={len(df)}  model_brier={model_brier:.4f}  "
              f"improvement={improvement_vs_best_baseline:+.4f}  "
              f"est_RBP_equiv_over_full_set={rbp_equiv}")
        results["grouped_kfold"][name] = {
            "n_test": len(df), "model_brier": model_brier,
            "improvement_vs_best_baseline": improvement_vs_best_baseline,
            "est_rbp_equiv_over_full_set": rbp_equiv,
        }

    # --- interpretability (fit on full data, not for deployment, just to read) ---
    print("\n=== Logistic regression coefficients (standardized, full-data fit) ===")
    coefs = logreg_coefficients(df, feature_cols)
    for c in coefs[:12]:
        print(f"  {c['feature']:<25s} {c['std_coef']:+.3f}")
    results["logreg_coefficients_full_fit"] = coefs

    print("\n=== HGB permutation importances (full-data fit) ===")
    importances = hgb_importances(df, feature_cols)
    for i in importances[:12]:
        print(f"  {i['feature']:<25s} {i['importance_mean']:+.5f}")
    results["hgb_importances_full_fit"] = importances

    # --- decision ---
    wf_improvements = [results["walk_forward"][m]["improvement_vs_best_baseline"] for m in models]
    gk_improvements = [results["grouped_kfold"][m]["improvement_vs_best_baseline"] for m in models]
    stable_positive = all(v > 0.002 for v in wf_improvements + gk_improvements)
    if stable_positive:
        decision = ("Both models beat the best baseline out-of-sample under BOTH validation "
                    "schemes by a non-trivial margin. Candidate for a paper-trading phase "
                    "(compute meta-model prices alongside the current pipeline, do not submit "
                    "them) before considering live use.")
    else:
        decision = ("Improvement is small, inconsistent between walk-forward and grouped k-fold, "
                    "or negative for at least one model/scheme. Do NOT deploy. Matches the Platt-"
                    "diagnostic precedent: revisit once the master dataset includes the knockout-"
                    "stage matches (more rows, more matches) and re-run this script unchanged.")
    print(f"\n=== Decision ===\n{decision}")
    results["decision"] = decision

    OUT.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nSaved results to {OUT}")


if __name__ == "__main__":
    main()
