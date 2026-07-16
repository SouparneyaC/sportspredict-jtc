# Q9 ("Will Argentina have more corner kicks than England?") — comparison-composition backtest summary

Full detail: [`ml/backtests/PREREGISTRATION_corners_comparison.md`](<../../ml/backtests/PREREGISTRATION_corners_comparison.md>)
(preregistration + results). Script: [`ml/backtests/corners_comparison_skellam_backtest.R`](<../../ml/backtests/corners_comparison_skellam_backtest.R>).
Full per-match results: [`ml/backtests/corners_comparison_backtest_results.csv`](<../../ml/backtests/corners_comparison_backtest_results.csv>).
Live prediction row: [`12_corners_comparison_live_prediction.csv`](12_corners_comparison_live_prediction.csv).

## What this tests
Q9 is a **comparison/difference** composition ("does Argentina's corner count exceed England's"), distinct
from both things already tested in `topics/corners/`: the per-team hierarchical GLMM (PASSED — predicts
each team's own count) and the SUM/combined-threshold composition (FAILED — convolving two teams' counts
into a total). This test builds `P(team A corners > team B corners)` from the same walk-forward-refit
per-team lambdas via the Skellam distribution (difference of two Poissons), same no-lookahead discipline
as the rest of the backtest suite (train strictly on `match_date < d`, refit fresh every fold).

**Known limitation, stated up front:** this still assumes independence between the two teams' corner counts
within a match — the same assumption that broke the SUM composition. It is tested empirically here, not
asserted away. See the preregistration doc for the analytic reasoning on why a difference composition's
sensitivity to that correlation runs the opposite direction from a sum composition's.

## Verdict: PASS (primary metric)

Walk-forward, n = 98 matches (matches the existing per-team corners backtest's own match count exactly).

| Metric | Naive 50/50 | k=5 baseline | Hierarchical GLMM |
|---|---|---|---|
| Mean Brier | 0.2500 | 0.2442 | **0.2015** |
| Mean log-loss | 0.6931 | 0.6810 | **0.5926** |

Brier (pre-registered primary metric): mean diff +0.0427 vs baseline (t=2.385, p=0.019, 90% CI [0.0134,
0.0714]) and +0.0485 vs 50/50 (t=2.175, p=0.032, 90% CI [0.0124, 0.0834]) — both CI lower bounds clear
zero, the pre-registered PASS bar. Log-loss is directionally consistent but weaker (p in the 0.06-0.08
range) — reported as the secondary metric it was pre-registered to be.

## Tonight's live number (shadow-deployment only, not yet a live submission basis)

Refit on all WC2026-plus-history data strictly before 2026-07-15 (everything through the QFs), using each
team's PIT elo entering the SF (England 2172.28, Argentina 2253.31, from `elo_post` after their 2026-07-11
QF matches):

- England predicted corners lambda: **4.191**
- Argentina predicted corners lambda: **4.556**
- **P(Argentina corners > England corners) = 0.4805**
- (P(England > Argentina) = 0.3835, P(tie) = 0.1360)

This is a genuinely close, roughly coin-flip-plus-a-touch-toward-Argentina number, driven by Argentina's
modest elo edge over England (+81.04 elo diff) translating into a small corners-lambda edge (4.556 vs
4.191). Per this project's C.5 rule (`writeups/decisions/0002-shadow-deploy-before-live-submission.md`),
this is a shadow-deployment number for comparison against market/submitted odds — not something to set
tonight's Q9 price on its own without going through that gate.
