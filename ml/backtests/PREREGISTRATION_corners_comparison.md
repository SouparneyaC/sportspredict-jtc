# Pre-registration: corners comparison composition ("does team A have more corners than team B")

Written before fitting or running anything below, following the same discipline as
`PREREGISTRATION_cards_corners_offsides_and_combined.md` and `PREREGISTRATION_sot_hierarchical_backtest.md`.
Triggered by ENG-ARG SF Q9: *"Will Argentina have more corner kicks than England in regulation?"*

## What is already known, and what is genuinely untested
The per-team corners hierarchical Poisson GLMM (`corners ~ elo_diff_pre_100 + data_source + (1|team_name)`,
walk-forward, PIT-safe) already **passed**: n=196 team-matches/98 matches, mean NLL diff +0.119,
p=0.030 raw (0.052-0.0396 depending on run, BH-adjusted) — see `topics/corners/README.md`. That test scored
each team's own predicted corner count against its own actual count.

A **sum** composition ("10+ combined corners, both teams") was tested separately by convolving the two teams'
independently-fit Poisson predictions into Poisson(lambda_A + lambda_B). It **failed**
(`ml/backtests/combined_threshold_backtest.py` -> `topics/corners/combined_corners_backtest_results.csv`,
t=-0.162, one-sided p=0.564) because the two teams' corner counts are positively correlated within a match
(open, corner-heavy matches elevate both teams' counts together; cagey matches suppress both), which breaks
the independence assumption a Poisson-sum composition relies on.

Q9 is neither of those. It is a **difference/comparison** composition: does team A's count exceed team B's.
This has never been tested in this repo. It is not safe to assume it inherits the per-team PASS, and it is
not safe to assume it inherits the sum-composition FAIL either — the two failure modes are not the same
mechanically (see next section). It gets its own falsifiable test.

## Why the difference composition might behave differently from the sum composition (reasoned in advance, not fit to the result)
For independent Poissons, D = X_A - X_B is Skellam-distributed. If the true within-match correlation
rho(X_A, X_B) is positive (the same mechanism documented in the combined-threshold failure), then:
- Var(sum) = Var(X_A) + Var(X_B) + 2*Cov(X_A, X_B) -- positive correlation makes the true sum **more** spread
  out than an independence-assumed convolution predicts, which is exactly the failure mode that broke the
  combined-threshold test (it understates the sum's true variance, so tail/threshold probabilities are
  systematically off).
- Var(diff) = Var(X_A) + Var(X_B) - 2*Cov(X_A, X_B) -- the same positive correlation makes the true
  difference **less** spread out than an independence-assumed Skellam predicts. An independence-assumed
  Skellam would then be too wide, pushing P(A>B) too close to 0.5 relative to the truth, i.e. *underconfident*
  rather than systematically biased in a fixed direction.

This is a plausible mechanical reason the difference composition could survive where the sum composition
did not -- but it is exactly that, a plausible reason, not a result. It is stated here in advance so it
cannot be retrofitted after seeing the numbers either way.

## Explicit limitation flagged before running (not hidden after)
The method below still assumes independence between the two teams' corner counts within a match to build
the Skellam distribution from two separately-predicted marginal lambdas. This is very likely not exactly
true, for the same reason the sum composition's independence assumption was not exactly true. This is being
tested empirically against actual walk-forward outcomes below, not asserted away. If it fails, positive
within-match correlation inflating the tails one way or the other is the leading candidate explanation,
consistent with the mechanism already documented for the sum composition.

## Hypothesis (one, falsifiable)
H1: The point-in-time-refit hierarchical Poisson GLMM's implied Skellam-derived P(team A corners > team B
corners) -- computed from the model's two independently-predicted per-team lambdas at the same walk-forward
fold used for the per-team corners backtest -- beats (a) naive 50/50 and (b) a k=5 empirical-Bayes
shrunk-mean baseline (same Skellam construction, using the shrunk lambda instead of the GLMM lambda), on
mean Brier score and mean log-loss, walk-forward, no lookahead.

## Method (identical protocol to `lib_hierarchical_backtest.R`'s `run_family_backtest()`)
- Same panel: `data/processed/unified_team_match_panel_with_pit_elo.csv`.
- Same formula: `corners ~ elo_diff_pre_100 + data_source + (1|team_name)`, Poisson GLMM (`lme4::glmer`).
- Same fold structure: sort all matches by date; for every WC2026 match date `d` (`data_source ==
  "espn_boxscore"`), train ONLY on rows with `match_date < d`, refit fresh at every fold, predict on that
  date's test match(es). `min_train = 20` team-match rows, same as the existing library default.
- New step (not in the per-team library): within each test fold, for every match with both teams' rows
  present, get both teams' predicted lambda_hier (GLMM) and lambda_baseline (k=5 shrinkage, same
  within-fold `global_mean`/`team_mean` construction as the library). Compute `P(team_A corners > team_B
  corners)` via the Skellam closed form (difference of two independent Poissons), hand-rolled in R as
  `sum_k P(X_B = k) * P(X_A > k)` truncated at k=0..60 (truncation error is negligible at corners-scale
  lambdas, on the order of 1e-15).
- Team-A/team-B assignment within a match is arbitrary but fixed per match (first row encountered) --
  scoring is symmetric, this is not a home/away or ENG/ARG-specific choice.
- Outcome: `actual_A_corners > actual_B_corners` (strict; a tie scores as the event not occurring, matching
  Q9's "more corner kicks than" phrasing).

## Baselines
1. Naive 50/50 (P = 0.5 every match).
2. k=5 empirical-Bayes shrunk-mean per team (identical construction to the existing per-team library
   baseline), composed into the same Skellam P(A>B) formula.

## Metrics, statistical bar
Primary: mean Brier score. Secondary: mean log-loss. Per-match paired difference (baseline - hier) and
(50/50 - hier), one-sample t-test, and match-level bootstrap 90% CI (2000 resamples), same construction as
`summarize_backtest()`. **PASS requires the 90% CI lower bound on the Brier (primary) diff to be strictly
above zero**, consistent with how SOT/corners/cards per-team results were judged (`raw_pass` in
`lib_hierarchical_backtest.R`). This is a single new hypothesis (not bundled into the existing 4-family BH
correction, since it is a distinct composition method tested against its own baselines, in the same spirit
as the combined-threshold composition tests being reported un-pooled in the existing preregistration) --
reported with its own raw p-value and CI, not adjusted against the unrelated per-family batch.

## Application step (run only after the backtest verdict is known, not before)
If (and only if, per this project's own C.5 rule / shadow-deploy-before-live-submission decision,
`writeups/decisions/0002-shadow-deploy-before-live-submission.md`) this composition is worth using at all,
refit the same model one more time on all WC2026-plus-history data strictly before 2026-07-15 (i.e.
everything through the QFs) and predict tonight's England vs Argentina lambdas and P(Argentina corners >
England corners). This is a **shadow-deployment number for comparison only** -- not something to submit
live without going through this project's own shadow-deploy gate, regardless of whether the backtest
passes.

---

## RESULTS (run 2026-07-15, after this document was written and committed)

Script: `ml/backtests/corners_comparison_skellam_backtest.R`. Full per-match output:
`ml/backtests/corners_comparison_backtest_results.csv`. Summary stats:
`ml/backtests/corners_comparison_backtest_summary.csv`.

1 of the 29 WC2026 fold dates failed to fit (same benign `glmer` convergence-skip behavior as the existing
library code) and was dropped, same as the per-team backtest's own `fit_failures` logging. 0 test matches
were skipped for missing a paired opponent row. **n = 98 scored matches** -- matches the per-team corners
backtest's own 98-match count exactly, as expected (same fold structure, same underlying matches, just
scored jointly instead of per-team).

| Metric | Naive 50/50 | k=5 baseline (Skellam) | Hierarchical GLMM (Skellam) |
|---|---|---|---|
| Mean Brier | 0.2500 | 0.2442 | **0.2015** |
| Mean log-loss | 0.6931 | 0.6810 | **0.5926** |

| Comparison | Metric | n | mean diff | t-stat | p (raw, one-sided direction) | 90% CI | Verdict |
|---|---|---|---|---|---|---|---|
| hier vs baseline | Brier (primary) | 98 | +0.0427 | 2.385 | 0.019 | [0.0134, 0.0714] | **PASS** (CI lower bound > 0) |
| hier vs baseline | log-loss | 98 | +0.0884 | 1.897 | 0.061 | [0.0106, 0.1611] | **PASS** (CI lower bound > 0; weaker p) |
| hier vs 50/50 | Brier (primary) | 98 | +0.0485 | 2.175 | 0.032 | [0.0124, 0.0834] | **PASS** |
| hier vs 50/50 | log-loss | 98 | +0.1006 | 1.777 | 0.079 | [0.0081, 0.1875] | **PASS** (CI lower bound > 0; weaker p) |

**Verdict: PASS on the pre-registered primary metric (Brier), against both baselines.** The 90% bootstrap CI
lower bound clears zero in all four comparisons (both metrics, both baselines), which was the pre-registered
promotion bar. Log-loss is directionally consistent but weaker (raw p in the 0.06-0.08 range rather than
comfortably under 0.05) -- reported honestly as the secondary metric it was pre-registered to be, not
folded into the primary PASS claim.

**On the independence caveat flagged in advance:** this composition survives where the SUM composition
failed. That is consistent with (not proof of) the analytic reasoning above -- if within-match correlation
is positive, it shrinks the true variance of the *difference* while inflating the true variance of the
*sum*, so an independence-assumed Skellam would be too wide (conservative, pulling toward 0.5) rather than
systematically miscalibrated in a fixed direction the way the sum composition's independence assumption
was. The comparison composition passing is therefore plausible on the mechanism, not just a fluke of this
particular n=98 -- but it is still an assumption baked into the method, and it is not re-verified directly
here (e.g. no direct measurement of the residual correlation in this run). Flagged for any future
extension of this test, not resolved.

## Live shadow-deployment application: England vs Argentina, 2026-07-15

Refit on all 456 panel rows with `match_date < 2026-07-15` (all of WC2026 through the QFs plus the
StatsBomb history), same formula, no held-out data. PIT elo entering the SF (from each team's `elo_post`
after their 2026-07-11 QF, cross-checked against `data/processed/wc2026_pit_elo_panel.csv`): England
2172.28, Argentina 2253.31 (elo_diff England -81.04, Argentina +81.04).

| Team | Predicted corners lambda |
|---|---|
| England | 4.191 |
| Argentina | 4.556 |

**P(Argentina corners > England corners) = 0.4805.** (P(England > Argentina) = 0.3835, P(tie) = 0.1360.)

Saved to `matches/England Vs Argentina (Jul.15.26)/12_corners_comparison_live_prediction.csv`.

**This is a shadow-deployment number only.** Per this project's own C.5 rule
(`writeups/decisions/0002-shadow-deploy-before-live-submission.md`), a newly-tested composition method must
be shadow-deployed (computed for comparison against market/submission) before being trusted to set a live
submission on its own -- it is not being used to directly set tonight's Q9 price by this backtest alone.
