# Offsides

Pricing for "N+ total offsides" questions (both teams). The cautionary tale of the whole
cards/corners/offsides/combined group: an initial, wildly implausible PASS that turned out to be
a data-quality bug, not signal — and the project's worst-performing question family historically
even before the ML backtest existed (see `OFFSIDE_CROWD_ANCHOR`, below).

## Current status/verdict

| Model | Verdict | Key numbers |
|---|---|---|
| Hierarchical Poisson GLMM, **first run (bugged)** | Implausible PASS — later retracted | p=8.96e-09. Investigated because the effect size was too large to be believable; traced to StatsBomb's offsides extraction counting only the standalone `Offside` event type, missing the dominant `Pass Offside` outcome encoding — an 8.49x historical undercount that the model's `data_source` fixed effect happened to absorb, producing a fake "signal." |
| Hierarchical Poisson GLMM, **after the extraction bug fix** (`datasets/build_statsbomb_panel.py`, ratio corrected 8.49x → 1.35x) | **FAIL** | n=196/98, mean diff +0.001, p=0.627 (later reported as p=0.954 in the FDR-adjusted summary) — confirming the entire original "pass" was the bug, not signal. |
| Combined-threshold composition | **"Passed" pre-fix for the same bug-driven reason, FAILs post-fix** | Not usable. |

This result independently confirms the project's own pre-existing `OFFSIDE_CROWD_ANCHOR` rule
(net -75.99 RBP historical cost of trusting offsides pricing over the crowd, from
`JULY3_POSTMORTEM_DEEP_DIVE.md`) — the ML attempt and the live-trading history agree: offsides
should stay crowd-anchored, not model-driven.

## Files in this folder

| File | What it is |
|---|---|
| `offsides_backtest_results.csv` | Per-team-match predictions from the (failed, post-fix) hierarchical model. |
| `combined_offsides_backtest_results.csv` | The (failed) combined-threshold composition test. |

## Shared inputs

| Path | Role |
|---|---|
| `ml/backtests/PREREGISTRATION_cards_corners_offsides_and_combined.md` | The shared preregistration — one fused hypothesis set, results table, and Benjamini-Hochberg FDR correction spanning cards + corners + offsides + combined-threshold together. Not split or duplicated per topic; linked from all four. Documents the bug discovery and retraction in full. |
| `datasets/build_statsbomb_panel.py` / `.R` | Where the 8.49x offsides-undercounting bug actually lived and was fixed (offsides = standalone `Offside` events **plus** Pass events with `pass.outcome.name=="Pass Offside"`). |
| `ml/backtests/lib_hierarchical_backtest.R`, `run_all_family_backtests.R` | Shared backtest engine and driver. |
| `ml/backtests/combined_threshold_backtest.py` | Produces `combined_offsides_backtest_results.csv` (above). |
| `ml/backtests/apply_to_fra_esp.R` | Live application step — the France vs Spain Q1 (4+ combined offsides) prediction was generated here and then **retracted same-day** once the bug fix reversed this family's pass; see the writeup below. |

## Relevant matches

- [`matches/France Vs Spain (Jul.14.26)/13_ml_vs_market_vs_submitted_comparison.md`](<../../matches/France Vs Spain (Jul.14.26)/13_ml_vs_market_vs_submitted_comparison.md>) — the same-day retraction, in full: the offsides prediction was pulled from the shadow-deployment record after the extraction bug was discovered, keeping only the (unaffected) SOT predictions.
- Historical loss pattern (pre-ML, crowd/market-anchored era): `JULY3_POSTMORTEM_DEEP_DIVE.md`'s `OFFSIDE_CROWD_ANCHOR` rule, `Australia_vs_Egypt` and `Colombia_vs_Ghana` (same-week offside mispricing, -43.09 and -36.94 RBP respectively).

## Root-doc mentions

- [`ML_MODEL_BUILD_RESEARCH_2026-07-13.md`](../../ML_MODEL_BUILD_RESEARCH_2026-07-13.md) — the foundation research recommending the hierarchical-GLMM design; offsides is the one family where following that design directly caught a real upstream data bug.
