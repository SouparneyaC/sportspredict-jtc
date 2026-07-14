# 0002: A newly backtested model must be shadow-tested against real outcomes before it can override a submission

**Status:** Accepted

## Context

Four prior attempts to apply machine learning to this project's meta/calibration layer (predicting
when the project's own estimate beats the crowd) all failed, and a retrospective research pass
(`ML_MODEL_BUILD_RESEARCH_2026-07-13.md`) traced the common cause to insufficient process rigor —
each was deployed on a hopeful reading of a small backtest, not validated against real held-out
outcomes at meaningful power.

On 2026-07-14, a domain-class hierarchical model (team-level shots-on-target/corners, pre-registered
and walk-forward backtested) *did* pass a rigorous backtest against the project's old production
baseline. That is a different, easier bar than beating a live market (see 0001) — the backtest never
compared the model against real Smarkets prices, only against the old shrinkage formula.

## Decision

A model that passes a backtest against a baseline is not automatically cleared to override a live
submission. It must first be run in parallel ("shadow mode") against real markets and real settled
outcomes across multiple matches, so its live performance can be measured, not assumed from the
backtest alone.

## Consequences

This is easier: a model with real backtest evidence isn't discarded just because it hasn't been
proven live yet — it gets a defined path to earning trust instead of being shelved indefinitely.

This is harder: it means deliberately not using a model's output on the first live opportunity,
even when time pressure (an imminent match) makes "just use it" tempting.

**Evidence this decision was tested, not just assumed:** France vs Spain (2026-07-14) used the
model's raw output for "Spain 5+ shots on target" as an explicit, flagged shadow-test rather than a
recommendation — see that match's write-up. It won, and by the largest margin on the slate. This is
one live data point in the model's favor; per 0001's own logic, one match doesn't clear the bar this
decision requires. The model remains in shadow mode until it accumulates more live evidence.