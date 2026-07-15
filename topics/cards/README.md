# Cards

Pricing for "N+ total cards" questions (yellow + red, both teams). The one family in the
cards/corners/offsides/combined group that never passed a hierarchical-GLMM backtest, even after
a targeted, hypothesis-driven refit — the most load-bearing null result in the group precisely
*because* it survived a genuine second attempt.

## Current status/verdict

| Model | Verdict | Key numbers |
|---|---|---|
| Hierarchical Poisson GLMM (same spec as SOT/corners/offsides) | **FAIL** | n=196 team-matches/98 matches, mean NLL diff +0.033, p=0.218 (BH-adjusted 0.291). |
| Referee-refined model (adds `(1\|referee_name)` random effect, each team's own shrunk foul rate, an `is_knockout` fixed effect) | **FAIL again** | n=196/98, mean NLL 1.518→1.486, t=1.153, p=0.252, bootstrap 90% band [-0.0147, +0.0773] — crosses zero, essentially unchanged from the original failure. Referee coverage was complete (196/196 test rows had a previously-seen referee), ruling out "referee mostly unseen" as the explanation. |

**Explicit conclusion: cards stays a market/crowd-anchored question, not a model-driven one, for
this tournament** — see `ml/backtests/PREREGISTRATION_cards_referee_fouls_stage.md`'s own RESULT
section. This is treated as more load-bearing than a first-pass failure precisely because it
survived a genuinely targeted fix attempt (referee + fouls + knockout-stage covariates, all
individually plausible) and still didn't move the needle.

## Files in this folder

| File | What it is |
|---|---|
| `walk_forward_cards_referee_backtest.R` | The referee-refined backtest (the second, targeted attempt). |
| `cards_referee_backtest_results.csv` | Per-team-match predictions from the referee-refined model. |
| `cards_backtest_results.csv` | Per-team-match predictions from the original (non-referee) model. |
| `referee_card_panel.csv` | Per-match referee name + total match cards, built from ESPN `gameInfo.officials` — the base data behind the referee refinement, produced by the shared `data/processed/build_halftime_sub_and_referee_panels.py` (see below). |

## Shared inputs

| Path | Role |
|---|---|
| `ml/backtests/PREREGISTRATION_cards_corners_offsides_and_combined.md` | The shared preregistration — one fused hypothesis set, results table, and Benjamini-Hochberg FDR correction spanning cards + corners + offsides + combined-threshold together. Not split or duplicated per topic; linked from all four. |
| `ml/backtests/lib_hierarchical_backtest.R` | Shared walk-forward backtest engine. |
| `data/processed/unified_team_match_panel_with_referee.csv` | Training panel extended with `referee_name_full`/`is_knockout`. |
| `data/processed/build_halftime_sub_and_referee_panels.py` | Builds `referee_card_panel.csv` (this folder) — dual-topic, also builds `halftime_sub_panel.csv` for `../first-substitution/`. |
| `ml/backtests/run_all_family_backtests.R` | The original (non-referee) cards backtest runs through here, alongside corners/offsides/SOT, under the joint FDR correction. |

## Relevant matches

Cards is priced from the general form/base-rate model on every match (no dedicated per-match
research files) — see `matches/Spain_vs_Belgium/POSTMORTEM.md` for the clearest single-match
account of why this family is hard: a -21 RBP loss on "4+ total cards" priced almost exactly at
Smarkets' own line, both wrong — "a shared model/market blind spot on stoppage-time card
accumulation in tense knockout games."

## Root-doc mentions

- [`BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md`](../../BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md) — the France vs Spain pricing session explicitly cites the cards FAIL when deciding to stay market-anchored on that match's card questions.
