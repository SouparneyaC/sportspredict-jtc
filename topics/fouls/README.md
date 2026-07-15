# Fouls

Pricing for "which team fouls more" and total-fouls questions. No dedicated scripts of its own —
a stub folder completing the 14-topic taxonomy. Mostly folded into the cards family as a
covariate (`own_foul_rate_shrunk`, motivated by a measured fouls-cards correlation r=0.449,
p<1e-6, n=456 — see `../cards/`) rather than priced as an independent model, but standalone
fouls questions do appear and are priced from a named rule, not a fitted model.

## Current status

No dedicated backtest. Priced via **RULE10**: in blowouts, the winning team fouls at least as
much as the losing team, regardless of historical per-team averages — a pattern that
overrides the naive "team X fouls more on average" read specifically in lopsided matches.

## Shared inputs

| Path | Role |
|---|---|
| `../cards/walk_forward_cards_referee_backtest.R` | Where the fouls-cards correlation was actually measured and used as a covariate (the fouls signal itself, folded into the cards model). |

## Root-doc mentions

- [`data/external_markets/MATCH_LOG.md`](../../data/external_markets/MATCH_LOG.md) — RULE10's origin, alongside the rest of the numbered RULE system.
- [`data/external_markets/game_dynamics_analysis.md`](../../data/external_markets/game_dynamics_analysis.md) — the cross-match foul-timeline analysis (conceding team commits its next foul within 10 minutes 79% of the time) that motivates fouls-timing intuition generally.
