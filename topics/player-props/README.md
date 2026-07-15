# Player Props

Pricing for player-specific questions (anytime scorer, score-or-assist, multi-goal/hat-trick,
player-level SOT). Currently one case study: a deliberate small-sample methodology demonstration
using Cristiano Ronaldo's StatsBomb WC2018+2022 appearances, explicitly *not* a usable model. Most
player-prop pricing in this project actually happens ad hoc per-match (Poisson/Skellam-based, see
root-level match session logs) rather than through a fitted model — this folder covers the one
fitted-model attempt, not the general player-props pricing methodology.

## Current status/verdict

| Model | Verdict | Key numbers |
|---|---|---|
| OLS (shots_on_target, xg_total, minutes_played + intercept) of Ronaldo's per-match goals, n=9 | **Explicitly not a usable model** — a methodology demonstration | In-sample R²=0.431 but adjusted R²=0.090 (large shrinkage, confirms overfitting). No coefficient significant (all p>0.65). LOOCV MSE 1.846 vs. a train-mean baseline of 1.156 — **the model is worse than just guessing the mean**, exactly what the n=9 caveat predicted going in (project's own RULE5 requires n≥10 before trusting a fitted model). |

## Files in this folder

| File | What it is |
|---|---|
| `ronaldo_goals_regression.py` | The OLS fit + LOOCV, HC3 heteroskedasticity-robust SEs. |
| `ronaldo_goals_regression.R` | R port — cross-checked against the Python version to rounding precision. |
| `ronaldo_goals_regression_results.json` / `_results_r.json` | Output JSONs for both. |

## Shared inputs

| Path | Role |
|---|---|
| `data/processed/statsbomb_player_match_panel.csv` | The 6,131-row player-match panel this regression is fit on (Ronaldo's 9 rows are a small slice of it). |

## Relevant matches

No dedicated per-match files — player props are priced per-match via the general Poisson/Skellam
pipeline documented in the root-level session logs (`ML_EXPERIMENTS_NOTEBOOK.md`), not through this
folder's model.

## Root-doc mentions

- [`ML_EXPERIMENTS_NOTEBOOK.md`](../../ML_EXPERIMENTS_NOTEBOOK.md) — the running record of actual per-match player-prop pricing decisions (RULE7, RULE9, RULE15, the Cluster-A/B patterns) sits here, not in this folder.
