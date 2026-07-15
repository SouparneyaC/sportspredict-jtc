# Rare-Event Timing

Pricing for timing/window questions: goal between hydration breaks, stoppage-time events,
goal-timing brackets. No dedicated scripts of its own yet — this is a stub folder completing the
14-topic taxonomy; add files here if a dedicated model is ever built for this family.

## Current status

Not sample-starved (unlike VAR review, see `../var-review/`), but faces a different problem:
window-definition fragility and irreducible single-match variance, per the methodology
research below. Priced from empirical base rates, not a fitted model.

**Key finding:** goal-between-hydration-breaks occurred in 74/99 matches with a saved hydration-break
timestamp (~74.7%).

## Shared inputs

| Path | Role |
|---|---|
| `ml/backtests/build_rare_event_panels.py`, `ml/backtests/rare_event_panel.csv` | The shared panel this family is priced from — also spans first-substitution (`../first-substitution/`) and VAR review (`../var-review/`). |

## Root-doc mentions

- [`BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md`](../../BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md) — the full methodological treatment: whether this family can be genuinely backtested given this project's sample size (Task C's answer: yes, but window-definition and variance are the binding constraints, not sample size).
