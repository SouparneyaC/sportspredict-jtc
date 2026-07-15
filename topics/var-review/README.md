# VAR Review

Pricing for "will there be an on-field VAR review" questions. No dedicated scripts of its own —
a stub folder completing the 14-topic taxonomy. Grouped with rare-event timing in the underlying
data build (`build_rare_event_panels.py`) but kept as a separate topic here since it's
conceptually distinct (a discrete event, not a timing window) and has its own, more severe,
sample-size problem.

## Current status

**Genuinely sample-starved** — only 1 verified on-field review in 12 matches with usable data.
Kupiec's Proportion-of-Failures VaR test (imported from quant-finance rare-event backtesting)
gives only 65% power to detect a 3x rate misspecification even at T=255 trials — this project's
sample is far smaller than that. Priced from reasoned domain judgment, not a backtested model.

A genuine data-quality gap also exists: ESPN's `keyEvents` feed can't structurally distinguish a
booth-only VAR check from an actual on-field pitchside review, so any count derived from it is a
necessary overcount. The France vs Spain Q15 case (2026-07-14) is the one live confirmation on
record: the official settlement confirmed the 83' check WAS a genuine on-field review, adding a
2nd confirmed real occurrence to the project's evidence base.

## Shared inputs

| Path | Role |
|---|---|
| `ml/backtests/build_rare_event_panels.py`, `ml/backtests/rare_event_panel.csv` (`var_mentions`, `any_var_mention` columns) | The shared panel this family is priced from. |

## Root-doc mentions

- [`BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md`](../../BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md) — Task A/B/C: literature review, the Kupiec-test power analysis, and the direct practical answer for this exact question.
