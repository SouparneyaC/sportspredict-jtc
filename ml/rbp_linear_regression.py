"""
rbp_linear_regression.py
--------------------------
Diagnostic: regress `rbp` (the actual Relative Brier Points scored per
question) against structural/rule features from the master dataset, to see
what conditions correlate with us gaining or losing points. This is a
different question than the earlier meta-model diagnostic (ml/meta_model.py),
which regressed `outcome` (trying to learn a better probability). Here the
target is the score itself, for interpretability: which features have a
robust, statistically significant relationship with RBP?

Source: datasets/master_question_dataset.csv (943 rows / 107 cols, one row
per (match, question) as of the 2026-07-07 rebuild).

Methodology:
- In-sample fit: statsmodels OLS with cluster-robust standard errors
  (grouped by `match`), because ~15 rows share the same match-level context
  columns (elo_diff, draw_probability, etc.) — plain OLS SEs would be
  overconfident. This mirrors the clustering concern already flagged in
  ml/meta_model.py.
- Out-of-sample validation: the same two schemes as the meta-model
  diagnostic (time-ordered walk-forward + GroupKFold-by-match), compared
  against a zero-parameter baseline (predict the training-fold's mean RBP).
- Missing continuous features (elo_diff, draw_probability, squad_value_diff)
  are median-imputed with a "_missing" indicator column added, same approach
  as the meta-model's SimpleImputer(add_indicator=True).
- Rule flags kept as features only if they fire >=10 times in the usable
  sample (same threshold used previously): rule1, rule5, rule7, rule8,
  rule10, rule12, rule13, rule14, rule15.

Usage: python3 ml/rbp_linear_regression.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import GroupKFold

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "datasets" / "master_question_dataset.csv"
OUT = ROOT / "ml" / "rbp_linear_regression_results.json"

RULE_COLS = ["rule1_fired", "rule5_fired", "rule7_fired", "rule8_fired",
             "rule10_fired", "rule12_fired", "rule13_fired", "rule14_fired", "rule15_fired"]


def load_usable():
    df = pd.read_csv(MASTER)
    usable = df[
        (df["actually_submitted"] == True)
        & df["our_estimate"].notna()
        & df["crowd_estimate"].notna()
        & df["outcome"].notna()
        & df["rbp"].notna()
    ].copy()
    return usable


def engineer_features(df):
    X = pd.DataFrame(index=df.index)
    X["gap"] = df["our_estimate"] - df["crowd_estimate"]
    X["abs_gap"] = X["gap"].abs()
    X["elo_diff"] = df["elo_diff"]
    X["draw_probability"] = df["draw_probability"]
    X["rest_days_diff"] = df["rest_days_diff"]
    X["squad_value_diff_m"] = (df["squad_value_a_eur"] - df["squad_value_b_eur"]) / 1e6
    # NOTE: rule_fired_count is deliberately excluded -- in this sample it is
    # an exact linear combination of the 9 individual rule dummies below
    # (only rules 1/5/7/8/10/12/13/14/15 ever fire; 2/3/4/6/9/11 are always
    # zero), which made the design matrix singular on the first run.
    X["is_player_prop"] = df["is_player_prop"].astype(int)
    for col in RULE_COLS:
        X[col] = df[col].fillna(False).infer_objects(copy=False).astype(int)

    # median-impute continuous features, with missing-indicator columns.
    # elo_diff and draw_probability share the same source (draw_probability
    # is derived from elo_diff per MASTER_DATASET_DICTIONARY.md) so they are
    # missing on exactly the same rows -- collapse into ONE indicator to
    # avoid perfectly collinear duplicate columns (this caused a singular
    # design matrix on the first run).
    elo_ctx_missing = X["elo_diff"].isna()
    X["elo_context_missing"] = elo_ctx_missing.astype(int)
    X["elo_diff"] = X["elo_diff"].fillna(X["elo_diff"].median())
    X["draw_probability"] = X["draw_probability"].fillna(X["draw_probability"].median())

    for col in ["squad_value_diff_m", "rest_days_diff"]:
        miss = X[col].isna()
        if miss.any():
            X[f"{col}_missing"] = miss.astype(int)
            X[col] = X[col].fillna(X[col].median())

    y = df["rbp"].astype(float)
    groups = df["match"]
    return X, y, groups


def fit_ols_with_cluster_se(X, y, groups):
    Xc = sm.add_constant(X)
    model = sm.OLS(y, Xc).fit(cov_type="cluster", cov_kwds={"groups": groups})
    return model


def walk_forward_validation(df, X, y):
    dates = pd.to_datetime(df["date"])
    match_order = (
        df.assign(_date=dates)
        .groupby("match")["_date"].min()
        .sort_values()
        .index.tolist()
    )
    n_matches = len(match_order)
    burn_in = n_matches // 2

    preds, actuals, baseline_preds = [], [], []
    for i in range(burn_in, n_matches):
        train_matches = set(match_order[:i])
        test_match = match_order[i]
        train_idx = df["match"].isin(train_matches)
        test_idx = df["match"] == test_match
        if test_idx.sum() == 0 or train_idx.sum() < 10:
            continue

        model = LinearRegression().fit(X[train_idx], y[train_idx])
        preds.extend(model.predict(X[test_idx]))
        actuals.extend(y[test_idx])
        baseline_preds.extend([y[train_idx].mean()] * test_idx.sum())

    return np.array(preds), np.array(actuals), np.array(baseline_preds)


def grouped_kfold_validation(X, y, groups, n_splits=6):
    gkf = GroupKFold(n_splits=n_splits)
    preds, actuals, baseline_preds = [], [], []
    for train_idx, test_idx in gkf.split(X, y, groups):
        model = LinearRegression().fit(X.iloc[train_idx], y.iloc[train_idx])
        preds.extend(model.predict(X.iloc[test_idx]))
        actuals.extend(y.iloc[test_idx])
        baseline_preds.extend([y.iloc[train_idx].mean()] * len(test_idx))
    return np.array(preds), np.array(actuals), np.array(baseline_preds)


def r2_mse(preds, actuals):
    mse = float(np.mean((preds - actuals) ** 2))
    ss_res = np.sum((actuals - preds) ** 2)
    ss_tot = np.sum((actuals - actuals.mean()) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
    return r2, mse


def main():
    df = load_usable()
    print(f"Usable rows: {len(df)}  |  Unique matches: {df['match'].nunique()}")
    X, y, groups = engineer_features(df)
    print(f"Features ({X.shape[1]}): {list(X.columns)}")
    print(f"RBP: mean={y.mean():.3f}, std={y.std():.3f}, min={y.min():.2f}, max={y.max():.2f}\n")

    print("=" * 80)
    print("IN-SAMPLE OLS (cluster-robust SEs, grouped by match)")
    print("=" * 80)
    model = fit_ols_with_cluster_se(X, y, groups)
    print(model.summary())

    print("\n" + "=" * 80)
    print("OUT-OF-SAMPLE VALIDATION")
    print("=" * 80)

    wf_preds, wf_actuals, wf_base = walk_forward_validation(df, X, y)
    r2_model, mse_model = r2_mse(wf_preds, wf_actuals)
    r2_base, mse_base = r2_mse(wf_base, wf_actuals)
    print(f"\nWalk-forward (n_test={len(wf_actuals)}):")
    print(f"  Model:    R2={r2_model:.4f}  MSE={mse_model:.2f}")
    print(f"  Baseline: R2={r2_base:.4f}  MSE={mse_base:.2f}  (predict expanding train-mean RBP)")
    print(f"  Model beats baseline: {mse_model < mse_base}")

    gk_preds, gk_actuals, gk_base = grouped_kfold_validation(X, y, groups)
    r2_model_gk, mse_model_gk = r2_mse(gk_preds, gk_actuals)
    r2_base_gk, mse_base_gk = r2_mse(gk_base, gk_actuals)
    print(f"\nGrouped 6-fold CV (n_test={len(gk_actuals)}):")
    print(f"  Model:    R2={r2_model_gk:.4f}  MSE={mse_model_gk:.2f}")
    print(f"  Baseline: R2={r2_base_gk:.4f}  MSE={mse_base_gk:.2f}  (predict fold train-mean RBP)")
    print(f"  Model beats baseline: {mse_model_gk < mse_base_gk}")

    coef_table = {
        name: {"coef": float(model.params[name]), "p_value": float(model.pvalues[name])}
        for name in model.params.index
    }
    significant = {k: v for k, v in coef_table.items() if v["p_value"] < 0.05}

    print(f"\nSignificant coefficients (p<0.05, cluster-robust): {list(significant.keys())}")

    OUT.write_text(json.dumps({
        "n_rows": len(df), "n_matches": int(df["match"].nunique()),
        "in_sample_r2": float(model.rsquared), "in_sample_adj_r2": float(model.rsquared_adj),
        "coefficients": coef_table, "significant_at_5pct": significant,
        "walk_forward": {"r2_model": r2_model, "mse_model": mse_model,
                          "r2_baseline": r2_base, "mse_baseline": mse_base,
                          "n_test": len(wf_actuals)},
        "grouped_kfold": {"r2_model": r2_model_gk, "mse_model": mse_model_gk,
                           "r2_baseline": r2_base_gk, "mse_baseline": mse_base_gk,
                           "n_test": len(gk_actuals)},
    }, indent=2))
    print(f"\nWritten: {OUT}")


if __name__ == "__main__":
    main()
