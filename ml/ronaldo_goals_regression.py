"""
ronaldo_goals_regression.py
-----------------------------
Diagnostic: simple linear regression of Cristiano Ronaldo's goals-per-match
on in-match performance features, using his 9 WC2018+2022 appearances in
statsbomb_player_match_panel.csv.

IMPORTANT CAVEAT, stated up front: n=9 is far below any sample size this
project normally trusts (RULE5 already sets the bar at n>=10 before trusting
a rate; the Platt/meta-model diagnostics needed n=246-771 before drawing any
conclusion). This script is a methodology demonstration, not a usable model —
treat every coefficient as illustrative, not actionable, until re-run on a
larger sample (e.g. once Euro 2020/2024 and Champions League are added to the
StatsBomb panel, which would add his club-level and additional international
matches).

Source: data/processed/statsbomb_player_match_panel.csv, filtered to
player_name == "Cristiano Ronaldo dos Santos Aveiro" (his full StatsBomb name).

Methodology:
- Features: shots_on_target, xg_total, minutes_played -- kept deliberately
  small (3 features + intercept = 4 params, 5 residual df on 9 rows) rather
  than the larger feature set used in ml/rbp_linear_regression.py, because
  every additional feature at this n makes the fit less trustworthy, not more.
- No clustering needed (each row is already one match, unlike the master
  dataset where ~15 rows share one match).
- In-sample: OLS with HC3 (heteroskedasticity-robust) standard errors --
  cluster-robust doesn't apply here (no repeated-match rows), but a small-n
  robust correction is still better than classical OLS SEs.
- Out-of-sample: leave-one-out cross-validation (LOOCV) -- the correct
  analogue of this project's usual walk-forward/GroupKFold discipline when
  n is this small (9 folds is the most you can do), compared against a
  "predict the training-fold mean goals" baseline.

Usage: python3 ml/ronaldo_goals_regression.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneOut

ROOT = Path(__file__).resolve().parents[1]
PLAYER_PANEL = ROOT / "data" / "processed" / "statsbomb_player_match_panel.csv"
OUT = ROOT / "ml" / "ronaldo_goals_regression_results.json"

PLAYER_NAME = "Cristiano Ronaldo dos Santos Aveiro"
FEATURES = ["shots_on_target", "xg_total", "minutes_played"]


def load_data():
    df = pd.read_csv(PLAYER_PANEL)
    df = df[df["player_name"] == PLAYER_NAME].copy()
    df = df.sort_values("match_date").reset_index(drop=True)
    return df


def main():
    df = load_data()
    print(f"Rows (matches): {len(df)}")
    print(df[["match_date", "opponent_name", "minutes_played", "shots", "shots_on_target", "xg_total", "goals"]]
          .to_string(index=False))

    X = df[FEATURES].astype(float)
    y = df["goals"].astype(float)
    print(f"\nGoals: mean={y.mean():.3f}, total={y.sum():.0f} across {len(y)} matches")

    print("\n" + "=" * 70)
    print(f"IN-SAMPLE OLS (n={len(df)}, HC3 robust SEs) -- ILLUSTRATIVE ONLY, n<<10")
    print("=" * 70)
    Xc = sm.add_constant(X)
    model = sm.OLS(y, Xc).fit(cov_type="HC3")
    print(model.summary())

    print("\n" + "=" * 70)
    print("OUT-OF-SAMPLE: LEAVE-ONE-OUT CROSS-VALIDATION")
    print("=" * 70)
    loo = LeaveOneOut()
    preds, actuals, base_preds = [], [], []
    for train_idx, test_idx in loo.split(X):
        m = LinearRegression().fit(X.iloc[train_idx], y.iloc[train_idx])
        preds.append(m.predict(X.iloc[test_idx])[0])
        actuals.append(y.iloc[test_idx].values[0])
        base_preds.append(y.iloc[train_idx].mean())

    preds, actuals, base_preds = map(np.array, (preds, actuals, base_preds))
    mse_model = float(np.mean((preds - actuals) ** 2))
    mse_base = float(np.mean((base_preds - actuals) ** 2))
    mae_model = float(np.mean(np.abs(preds - actuals)))
    mae_base = float(np.mean(np.abs(base_preds - actuals)))

    print(f"\n{'Match':<25} {'Actual':>7} {'Model pred':>11} {'Baseline pred':>14}")
    for i, row in df.iterrows():
        print(f"{row['match_date']} vs {row['opponent_name']:<12} {actuals[i]:>7.0f} {preds[i]:>11.2f} {base_preds[i]:>14.2f}")

    print(f"\nLOOCV MSE  -- model: {mse_model:.3f}  baseline (predict train-mean): {mse_base:.3f}")
    print(f"LOOCV MAE  -- model: {mae_model:.3f}  baseline: {mae_base:.3f}")
    print(f"Model beats baseline (MSE): {mse_model < mse_base}")

    OUT.write_text(json.dumps({
        "n_matches": len(df), "features": FEATURES,
        "in_sample_r2": float(model.rsquared), "in_sample_adj_r2": float(model.rsquared_adj),
        "coefficients": {name: {"coef": float(model.params[name]), "p_value": float(model.pvalues[name])}
                          for name in model.params.index},
        "loocv": {"mse_model": mse_model, "mse_baseline": mse_base,
                  "mae_model": mae_model, "mae_baseline": mae_base},
        "caveat": "n=9 is far below any sample size this project trusts (RULE5 bar is n>=10). "
                  "Treat as methodology demonstration, not a usable model.",
    }, indent=2))
    print(f"\nWritten: {OUT}")


if __name__ == "__main__":
    main()
