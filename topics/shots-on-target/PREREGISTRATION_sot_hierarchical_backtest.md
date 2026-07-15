# Pre-registration: hierarchical partial-pooling model for team SOT counts

Written BEFORE fitting, per the deployment rule in `ML_MODEL_BUILD_RESEARCH_2026-07-13.md` §C.5 (rule 2: pre-register hypothesis, features, validation scheme, baselines, and a numeric promotion criterion before fitting anything).

**Date:** 2026-07-14. **Author:** this session, at the user's request to actually build and backtest design #2 with proper point-in-time discipline.

## Hypothesis
A hierarchical Poisson GLMM — `shots_on_target ~ elo_diff_pre + data_source + (1|team_name)` — produces better-calibrated predictions of a team's shots-on-target count in a single match than the project's current fixed k=5 empirical-Bayes shrinkage (`lambda_shrunk = (n*team_mean + 5*global_mean) / (n+5)`, documented in `STATSBOMB_INTEGRATION_AND_STATS_TESTS_2026-07-08.md`), when both are evaluated **walk-forward** (strictly-prior data only at every point) across all 100 WC2026 matches.

Chosen family: shots-on-target. Rationale: the most contested, most postmortem'd stat family in the project (RULE17 proposed/invalidated/retired, Cluster-B finding, CAN-MOR's -80.94 single-question blowup, the FRA-ESP Q12/Q15 pricing just done). If any family were going to show a real, recoverable hierarchical-pooling effect, this is the best-instrumented candidate.

## Features (fixed budget, ≤12)
1. `elo_diff_pre` — the team's own point-in-time Elo minus the opponent's point-in-time Elo, from the systematic full-tournament replay (`ml/backtests/build_full_tournament_pit_elo.py` for 2026 rows, `model/elo.py`'s legitimate historical output for 2018/2022 rows). This is the ONE opponent-strength covariate.
2. `data_source` (espn_boxscore vs statsbomb_event_data) — fixed effect for the measured ESPN/StatsBomb SOT convention gap (ratio 1.304 measured this session's panel rebuild, consistent with the 2026-07-08 finding).
3. `(1|team_name)` — team random intercept, the partial-pooling term itself.

Explicitly NOT included: opponent identity/random effect (this backtests each team's OWN count, not a head-to-head joint model — matches how JTC actually prices "Team X N+ SOT" questions), match-state/game-score covariates (not available point-in-time before kickoff), red-card/injury-time covariates (same reason).

## Validation scheme
Walk-forward across the 100 WC2026 matches in chronological order (`match_date`). At each match:
- Training data = every row in the unified panel with `match_date` strictly before this match's date. This always includes the full 256-row StatsBomb 2018/2022 history (legitimately prior — those are past tournaments) plus any WC2026 rows played earlier.
- Both the hierarchical model AND the baseline's `global_mean`/`team_mean`/`n` are recomputed on this same strictly-prior slice — the baseline does not get to see the full-tournament mean either. Same PIT bar for both methods.
- New teams with zero prior rows (Cape Verde, Curaçao, Haiti's first WC2026 appearance — no WC2018/2022 data) fall back to the model's population-level (fixed-effect-only) prediction via `allow.new.levels=TRUE` — this is the correct partial-pooling behavior for a genuinely new team, not a bug to special-case around.

## Baselines
1. **Current fixed k=5 shrinkage** (the actual production method) — primary comparison.
2. **Global mean only** (no team information at all) — sanity floor; the hierarchical model and the shrinkage baseline should both beat this or something is broken.
3. Market/crowd baseline: **not included** — no historical SOT market-line archive exists for most of these 100 matches (only a handful of matches this campaign had a Smarkets SOT quote saved), so a fair market comparison isn't possible at this scale. Flagged as a real limitation, not silently dropped.

## Metric
**Primary:** Poisson predictive negative log-likelihood (`-log dpois(actual, lambda)`) per team-match — a strictly proper scoring rule for count data, avoids picking an arbitrary threshold.
**Secondary, for interpretability against actual JTC questions:** Brier score on the threshold `SOT >= round(baseline_lambda)` — the baseline method's own natural rounding, fixed as the "question" so neither method gets to pick a favorable threshold.

## Promotion criterion (stated as a number, before seeing results)
The hierarchical model is "promoted" (i.e., worth building further / feeding into future match pricing as one evidence source) only if its mean predictive NLL beats the k=5-shrinkage baseline by more than the match-level-clustered bootstrap 90% noise band (2,000 resamples of match-level mean paired differences). Anything smaller is not distinguishable from noise at this n and should NOT be deployed, full stop — same bar the project has applied to every prior ML attempt.

## What would make this different from the four prior rejections
All four prior attempts were meta/calibration-class models (n = matches, predicting when our estimate beats the crowd). This is domain-class: n = team-matches (456 rows), predicting a real measured outcome (SOT count) directly, not a soft crowd-relative label. If this also fails to clear the noise band, that is real evidence the domain-class ceiling is lower than the literature (§B.1) suggested for this specific family — not a process failure, and worth writing up as such rather than discarding silently.

---

## RESULTS (run 2026-07-14, after this document was written and committed)

**PASS.** Walk-forward across 29 distinct WC2026 match dates (196 team-match predictions, 1 fold skipped on a genuine fit error), strictly-prior-data-only at every step (`ml/backtests/walk_forward_sot_backtest.R`, full per-row output in `sot_backtest_results.csv`):

| Method | Mean predictive NLL | Mean Brier @ baseline threshold |
|---|---|---|
| Global mean only (floor) | 2.4650 | 0.2744 |
| **k=5 shrinkage (current production baseline)** | 2.3782 | 0.2457 |
| **Hierarchical GLMM** | **2.1539** | **0.2075** |

Match-level clustered comparison (n=98 team-observations paired by match): mean NLL improvement +0.2242, paired t-test **t=4.071, p=0.0001**, bootstrap 90% band **[0.1377, 0.3180]** — entirely above zero. Promotion criterion met.

**Robustness checks performed before accepting this (not pre-registered, added because a positive first-pass result on an ML claim gets extra scrutiny in this project, per its own history):**
- **Not an early-fold artifact.** Split by tournament third: diff = +0.2305 (first third, avg n_prior=4.5) / +0.2517 (second third) / +0.1568 (final third, avg n_prior=10.6, knockout stage). The edge shrinks as teams accumulate their own WC2026 data (expected — the k=5 baseline gets better too as n grows) but stays positive throughout, including the smallest/latest-stage subsample.
- **Real discrimination, not just averaging.** Correlation with actual SOT: baseline 0.303, hierarchical **0.561** — nearly double. Mean predicted lambda (baseline 4.035, hierarchical 4.135) both close to actual mean (4.219), so the NLL gain is not from a mean-matching trick, it's from better per-team-match discrimination.

**What this does and does not mean.** This is real evidence design #2 is viable for the SOT family specifically, evaluated properly walk-forward. It is NOT yet a deployment: per §C.5 rule 4, this must be shadow-deployed (priced in parallel, not submitted) for at least one full match before it touches a live submission. It also has not been tested on the other stat families (cards, corners, offsides) — this result should not be assumed to generalize to those without running the same pre-registered protocol per family.
