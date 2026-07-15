# Corners

Pricing for "N+ total corners" questions (both teams). The second family (alongside SOT) to pass
the hierarchical-GLMM backtest.

## Current status/verdict

| Model | Verdict | Key numbers |
|---|---|---|
| Hierarchical Poisson GLMM (same spec as SOT/cards/offsides) | **PASS** | n=196 team-matches/98 matches, mean NLL diff +0.119, p=0.030 (BH-adjusted 0.059). |
| Own-Elo-level refinement | **PASS, promoted as default** | Still beats baseline (p=0.038, mean diff +0.115 — slightly weaker than the original +0.119); top-tercile underprediction bias shrinks 39% (neither figure itself statistically distinguishable from zero, "no downside, real if modest upside"). |
| Combined-threshold composition ("N+ combined corners, both teams") | **FAIL** | Convolving the two teams' independent per-team predictions fails — positive within-match correlation between the two teams' corner counts breaks the independence assumption the composition relies on. |

## Files in this folder

| File | What it is |
|---|---|
| `corners_backtest_results.csv` | Per-team-match predictions, original model. |
| `corners_backtest_results_ownelo.csv` | Same, with the own-Elo-level refinement applied. |
| `combined_corners_backtest_results.csv` | The (failed) combined-threshold composition test. |

## Shared inputs

| Path | Role |
|---|---|
| `ml/backtests/PREREGISTRATION_cards_corners_offsides_and_combined.md` | The shared preregistration — one fused hypothesis set, results table, and Benjamini-Hochberg FDR correction spanning cards + corners + offsides + combined-threshold together. Not split or duplicated per topic; linked from all four. |
| `ml/backtests/lib_hierarchical_backtest.R` | Shared walk-forward backtest engine. |
| `ml/backtests/run_all_family_backtests.R` | Runs the original corners backtest alongside cards/offsides/SOT under the joint FDR correction — stays in `ml/backtests/` as shared driver code. |
| `ml/backtests/run_elo_level_refinement.R`, `ml/backtests/PREREGISTRATION_elo_level_refinement.md` | The own-Elo refinement driver and its preregistration (run jointly for corners + SOT). |
| `ml/backtests/combined_threshold_backtest.py` | Produces `combined_corners_backtest_results.csv` (above) — shared across SOT/corners/offsides, not owned by any one topic. |
| `ml/backtests/apply_to_fra_esp.R` | Live application — refits corners (and offsides) on all prior data and predicts France/Spain SF lambdas. |

## Relevant matches

No dedicated per-match research files (corners is priced from the general team-form model, not
match-specific deep dives) — see the France vs Spain shadow-deployment writeup for the one live
application of this model: [`matches/France Vs Spain (Jul.14.26)/13_ml_vs_market_vs_submitted_comparison.md`](<../../matches/France Vs Spain (Jul.14.26)/13_ml_vs_market_vs_submitted_comparison.md>).

## Root-doc mentions

- [`ML_MODEL_BUILD_RESEARCH_2026-07-13.md`](../../ML_MODEL_BUILD_RESEARCH_2026-07-13.md) — the foundation research recommending the hierarchical-GLMM design this backtest implements.
