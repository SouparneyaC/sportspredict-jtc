# Shots on Target (SOT)

Pricing for "N+ shots on target" questions, team- and player-level. The most fully-instrumented
question family in the project — the first (and so far only, along with corners) family to pass
the hierarchical-GLMM backtest, and the reference implementation every other family's
preregistration doc points back to.

## Current status/verdict

| Model | Verdict | Key numbers |
|---|---|---|
| Hierarchical Poisson GLMM (`shots_on_target ~ elo_diff_pre_100 + data_source + (1\|team_name)`) vs. k=5 empirical-Bayes baseline | **PASS** | Match-level (n=98) mean NLL improvement +0.224, t=4.071, p=0.0001, bootstrap 90% band [0.138, 0.318] — entirely positive. Correlation with actual SOT nearly doubles (0.303 baseline → 0.561 hierarchical). |
| Own-Elo-level refinement (adds each team's absolute PIT Elo as a second fixed effect) | **PASS, promoted as default** | Still beats baseline (p=0.0001, mean diff +0.225); top-tercile underprediction bias shrinks 11% (not itself statistically distinguishable from zero before or after — "no downside, real if modest upside"). |
| Live market comparison (n=11 matches with a saved Smarkets team-SOT line) | Directional only, not powered | See `sot_vs_market_comparison.csv`. |
| Bounded market/GLMM blend ("Design #3") | Shadow-deployed only, not live-submitted | `w=0.25` fixed weight, ±0.08 probability cap — a direct fix for the CAN-MOR-style blowout failure mode. |

Flagged as needing shadow-deployment before being trusted to override a live submission —
see `decisions/0002-shadow-deploy-before-live-submission.md` in `writeups/`.

## Files in this folder

| File | What it is |
|---|---|
| `PREREGISTRATION_sot_hierarchical_backtest.md` | Hypothesis, features, validation scheme, and promotion criterion — written *before* the model was fit. |
| `walk_forward_sot_backtest.R` | The walk-forward backtest itself (100 WC2026 matches, 29 distinct dates, refit at every fold on strictly-prior data). |
| `sot_backtest_results.csv` | Per-team-match predictions from the original model (197 lines). |
| `sot_backtest_results_ownelo.csv` | Same, with the own-Elo-level refinement applied. |
| `sot_vs_market_comparison.py` / `.csv` | Live Smarkets-market comparison across the 11 matches with a saved team-SOT line. |
| `blend_market_glmm.py` | The bounded market/GLMM blend rule ("Design #3"). |
| `combined_sot_backtest_results.csv` | Sum-of-two-Poissons composition test for "N+ combined SOT, both teams" questions (produced by the shared `combined_threshold_backtest.py`, see below). |

## Shared inputs

Files this topic depends on but doesn't own — never duplicated here, per the project's
raw/processed-data discipline (see root `README.md`).

| Path | Role |
|---|---|
| `model/elo.py`, `data/processed/wc2026_pit_elo_panel.csv`, `ml/backtests/build_full_tournament_pit_elo.py` | Point-in-time Elo — the `elo_diff_pre_100`/`own_elo_pre_100` covariates. |
| `data/processed/unified_team_match_panel_with_pit_elo.csv` | The training panel (WC2026 ESPN + WC2018/2022 StatsBomb, PIT-Elo joined in). |
| `ml/backtests/lib_hierarchical_backtest.R` | Shared walk-forward backtest engine (`run_family_backtest()`, `summarize_backtest()`) — also used by cards/corners/offsides. |
| `ml/backtests/run_elo_level_refinement.R`, `PREREGISTRATION_elo_level_refinement.md` | The own-Elo refinement driver and its preregistration (run jointly for SOT + corners). |
| `ml/backtests/combined_threshold_backtest.py` | Produces `combined_sot_backtest_results.csv` (above) — shared across SOT/corners/offsides, not owned by any one topic. |
| `ml/backtests/apply_to_fra_esp.R` | Final live application — refits SOT (and, at the time, offsides) on all prior data and predicts France/Spain SF lambdas. Writes into `matches/France Vs Spain (Jul.14.26)/12_ml_predictions.csv` (match folders are not reorganized by topic — see project root `REPO_MAP.md`). |

## Relevant matches

Matches with a real, saved Smarkets team-SOT market line (the `sot_vs_market_comparison.py`
comparison set):

`Brazil_vs_Norway`, `France_vs_Paraguay`, `Canada_vs_Morocco`, `Mexico_vs_England`,
`Australia_vs_Egypt`, `Spain_vs_Austria`, `Argentina_vs_CapeVerde`, `Portugal_vs_Croatia`,
`Colombia_vs_Ghana`, `Argentina_vs_Switzerland`, `Spain_vs_Belgium`.

Plus the live shadow-deployment application: [`matches/France Vs Spain (Jul.14.26)/13_ml_vs_market_vs_submitted_comparison.md`](<../../matches/France Vs Spain (Jul.14.26)/13_ml_vs_market_vs_submitted_comparison.md>) (Q12 Spain 5+ SOT, Q15 France 4+ SOT — both GLMM predictions kept for the record, both lower than market/submitted, attributed to the model lacking match-context awareness).

## Root-doc mentions

- [`ML_MODEL_BUILD_RESEARCH_2026-07-13.md`](../../ML_MODEL_BUILD_RESEARCH_2026-07-13.md) — the foundation research recommending the hierarchical-GLMM design this backtest implements.
- [`BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md`](../../BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md) — contrasts SOT's genuinely-backtestable sample size against the rare-event questions that aren't.
