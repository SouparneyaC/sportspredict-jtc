# First Substitution / Timing

Pricing for "which team substitutes first" (Q14-style race questions) and the halftime-substitution
base rate. A clean, confidently-negative result — the model actively hurts relative to a coin flip,
which the project treats as evidence the simpler heuristic used in practice was correctly scoped,
not under-sophisticated.

## Current status/verdict

| Model | Verdict | Key numbers |
|---|---|---|
| Walk-forward logistic regression (each team's own shrunk k=5 first-sub-minute tendency + Elo diff as a trailing-team proxy) vs. naive 50/50 | **FAIL, confidently worse than baseline** | 79 scored walk-forward folds across 100 WC2026 matches. Mean Brier 0.2785 (model) vs. 0.2500 (naive 50/50). Bootstrap 90% band on the improvement: **[-0.0536, -0.0030] — entirely negative.** |

Practical conclusion: the already-submitted Q14 heuristic (a simple manual pairwise comparison,
typically ~0.60) is not improved on by this fitted model. In-match score-state is explicitly
out of scope (unavailable pre-kickoff, per JTC's submission timing) — that's very likely the
missing signal a fitted model would need.

## Files in this folder

| File | What it is |
|---|---|
| `PREREGISTRATION_q14_first_sub_race.md` | Hypothesis, features, validation scheme, promotion criterion, and the FAIL result. |
| `walk_forward_first_sub_backtest.py` | The walk-forward logistic-regression backtest. |
| `first_sub_backtest_results.csv` | Per-fold predictions (80 lines, 79 scored folds). |
| `halftime_sub_panel.csv` | Per-match base rate: did either team substitute in the immediate second-half-restart window (clock ≤ 47:00)? Built from ESPN `keyEvents`, feeds the pre-kickoff heuristic actually used in submissions. |

## Shared inputs

| Path | Role |
|---|---|
| `ml/backtests/build_rare_event_panels.py`, `ml/backtests/rare_event_panel.csv` | Shared panel spanning first-sub-minute-per-team, VAR mentions, and goal-between-hydration-breaks — not owned by any one topic. |
| `data/processed/build_halftime_sub_and_referee_panels.py` | Builds `halftime_sub_panel.csv` (this folder) — dual-topic, also builds `referee_card_panel.csv` for `../cards/`. |
| `data/processed/unified_team_match_panel_with_pit_elo.csv` | Elo-diff covariate source. |

## Relevant matches

No dedicated per-match research files — first-sub is priced from the general base rate / manual
heuristic on every match. See `BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md` for the France vs
Spain pre-match decision to stay with the manual heuristic given this backtest's result.

## Root-doc mentions

- [`BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md`](../../BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md) — Task C directly discusses whether first-sub timing is genuinely backtestable at this sample size (concludes: not sample-starved, but window-definition and missing-score-state problems dominate).
