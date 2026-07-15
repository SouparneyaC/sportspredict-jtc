# Match Winner / FTR + Goals Totals / BTTS / Over-Under

The project's classical/deterministic core pipeline: point-in-time Elo → Poisson goals GLM →
Dixon-Coles low-score correction → prediction, plus a parallel ordered-logit track fit directly
on match outcome. The largest single topic folder (18 files) and the most-cited path across the
rest of the repo — this is the production pipeline behind most of the project's match-winner and
goal-total submissions, not a newer experimental family like the `ml/backtests/` group.

## Current status/verdict

This is a fitted, deployed classical pipeline, not a pass/fail backtest family — status is
tracked as calibration findings rather than a single verdict.

| Component | Status | Key numbers |
|---|---|---|
| Poisson goals GLM | Fitted, in production | `intercept=0.10408, home_advantage=0.23022, elo_diff_coef=0.0018099` (n=49,400 matches / 98,800 observations, recency decay `xi=0.0008`). |
| Ordered logit (match result) | Fitted, in production | `b_elo=0.005199, b_home=0.37713, c1=-0.77018, c2=0.55487` (same panel). Calibrated against P(home win) by construction — addresses a ~5-8pp compression-toward-50/50 gap the Poisson-based pipeline shows. |
| NB overdispersion correction | Fitted, in production | `alpha=0.0992, rho_nb=-0.05` — corrects a "fatter-than-Poisson tails" underconfidence at the low end of the goal-totals distribution. |
| **Fixed bug (2026-07-10)**: neutral-flag mismatch | Fixed | `poisson_goals.py` originally assigned `home_adv=1` unconditionally even on neutral-venue matches (~26%/13,100 of 49k rows), biasing the home-advantage coefficient down (buggy `b1=0.25622` vs. fixed `b1=0.23022`) and compressing all non-neutral win probabilities toward 50/50. |
| Calibration diagnostic (`backtest_vs_market.py`) | Ongoing reference check | Ordered-logit probabilities vs. de-vigged bookmaker odds, by favorite-strength bucket. |

## Files in this folder

### `model/` — 14 scripts
| File | What it is |
|---|---|
| `poisson_goals.py` | Stage 2: Poisson GLM, `log(lambda) = b0 + b1*home_adv + b2*elo_diff`. |
| `dixon_coles.py` | Stage 3: scoreline grid + Dixon-Coles low-score correction (Poisson or NB marginals). No file I/O of its own — pure functions, imported by the rest. |
| `ordered_logit.py` | Parallel track: fits match outcome directly on Elo diff + home advantage. |
| `predict.py` / `predict_ordered_logit.py` | End-to-end single-fixture prediction CLIs for the two tracks. |
| `fit_rho.py` | CLI to fit Dixon-Coles rho by MLE. |
| `fit_nb_dispersion.py` | Fits the NB2 overdispersion correction. |
| `backtest_harness.py` / `backtest_single.py` / `backtest_vs_market.py` | Full historical backtest, single-match sanity check, and live-market comparison. |
| `backtest_diagnostics.py` / `goal_totals_diagnostics.py` / `goal_totals_diagnostics_nb.py` / `ordered_logit_diagnostics.py` | Calibration/decile diagnostics for each sub-model. |

### `coefs/` — 4 fitted-coefficient JSONs
`poisson_goals_coefs.json`, `ordered_logit_coefs.json`, `nb_dispersion_coefs.json`,
`model_standard_errors.json` (SEs for all three models — not produced by any script in this
folder, a standalone compiled artifact).

## Shared inputs

| Path | Role |
|---|---|
| `model/elo.py`, `data/processed/elo_current_ratings.csv`, `data/processed/elo_match_panel.csv` | Point-in-time Elo — **stays in `model/`**, the one file in the original `model/` directory not specific to this topic (every topic's own-Elo covariate depends on it too). |
| `datasets/build_master_dataset.py` | Reads `coefs/poisson_goals_coefs.json` and `coefs/ordered_logit_coefs.json` as a fallback whenever a raw match file lacks its own recorded model output. |
| `bot/predict_markets.py` | The live per-market prediction script — imports `ordered_logit.py`/`dixon_coles.py` directly (via `sys.path.insert`) and reads all three fitted-coefs JSONs. |

## Relevant matches

This is the general-purpose pipeline used across nearly every match for match-winner and
goal-totals questions — see any `matches/*/03_model_derivations.json` for a worked per-match
application (`lambda_fits`, `derived_probs`, the `elo` block).

## Root-doc mentions

- [`JTC_PROJECT_WRITEUP.md`](../../JTC_PROJECT_WRITEUP.md) — Section 5 documents the full modeling stack this folder implements.
- [`PROJECT_TODO.md`](../../PROJECT_TODO.md) — documents the exact before/after Poisson coefficients from the neutral-flag bug fix.
