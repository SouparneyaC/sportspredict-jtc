# ML vs Smarkets vs submitted — first shadow-test comparison

Retrospective comparison, not a resubmission. Per `ml/backtests/PREREGISTRATION_cards_corners_offsides_and_combined.md`'s application step and the project's own C.5 deployment rule (a newly-fitted model must be shadow-deployed — priced in parallel, not submitted — before it touches a live number), this is the first data point in that shadow-deployment record, not a change to what was actually submitted for this match.

**UPDATE 2026-07-14 (same day): the Q1 row below is RETRACTED.** The offsides ML prediction was built on a hierarchical model that has since been shown to be an artifact of an 8.49x StatsBomb extraction bug (`datasets/build_statsbomb_panel.py` was missing the `Pass Offside` outcome encoding, undercounting historical offsides ~8x). After fixing the bug and re-running the backtest, offsides per-team AND combined both drop to noise (p=0.63, mean diff ≈0) — full detail in the pre-registration doc's "RESULTS AFTER THE OFFSIDES BUG FIX" section. Only SOT (Q12, Q15) has a validated ML prediction; kept below for the record with a strikethrough on Q1.

| Question | ML | Smarkets / derived | Submitted (05_estimates.json) |
|---|---|---|---|
| ~~Q1: 4+ combined offsides~~ | ~~0.360~~ **RETRACTED — no valid ML model** | no market exists | 0.45 |
| Q12: Spain 5+ SOT | **0.360** | 0.493 (market-calibrated sim) | 0.48 |
| Q15: France 4+ SOT | **0.595** | 0.738 (market-calibrated sim) | 0.72 |

Model used: per-team hierarchical Poisson GLMM for SOT (`sot ~ elo_diff_pre + data_source + (1|team)`, FDR-adjusted p=0.0003 in the walk-forward backtest, unaffected by the offsides fix). Cards excluded — failed its backtest (p=0.255) — so Q2 has no ML entry; stick with the submitted market-anchored 0.40. Offsides excluded per the retraction above.

## Reading the pattern, not just the numbers

**ML is lower than the market/derived number on both remaining questions, and lower than what was submitted on both.** The gap is large (Q12: 0.36 vs 0.49; Q15: 0.60 vs 0.74) — driven by lambda: ML's France SOT lambda is 4.15 vs the market-fitted 5.02; Spain 3.94 vs 4.65. The hierarchical model is trained on 456 historical rows via Elo-diff + team identity only — it has no way to see that this is a high-stakes semifinal between two elite, high-possession teams likely to generate an open, shot-heavy game, no lineup information, no sense of "these two specific teams push the pace against each other." The market prices all of that; the model structurally cannot. This is exactly why `RULE2` puts a liquid market ahead of any domain model — the backtest validated this model against the OLD baseline (fixed shrinkage), never against a live market, and that gap is explicitly flagged as a limitation in the pre-registration doc.

On offsides, the retraction turned out to matter for interpretation too: what had looked like "ML and my own manual empirical estimate (0.39) agree, both below the crowd-anchored 0.45" was actually "a buggy model happened to land near a reasonable manual estimate by coincidence." The manual 0.39 stands on its own merits (RULE16's caution about it stands too) but should not be read as corroborated by the retracted ML number.

## What this means going forward, not for this match
This submission is not being changed. What this comparison *is*: the first entry in design #2's shadow-deployment log, now covering SOT only. Per C.5, the model needs to accumulate several of these — ideally against matches where the real outcome later becomes known, so the comparison can be scored, not just eyeballed — before any of its output is trusted enough to influence a live number. Next candidate: ENG vs ARG (2026-07-15).
