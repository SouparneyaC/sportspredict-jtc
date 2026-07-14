# 0001: A liquid market takes priority over a domain-only model when both exist

**Status:** Accepted

## Context

This project runs a domain pricing pipeline (point-in-time Elo, Poisson goals model, Dixon-Coles
correction, plus a hierarchical partial-pooling model for team-level count stats validated
2026-07-14). It also has access to a real sharp market (Smarkets) for many questions. When the two
disagree, which one governs the submitted number?

A direct backtest (`sportspredict_research/model/backtest_vs_market.py`, 505 historical matches
matched against real bookmaker odds) found the domain model's match-result predictions lose to real
market odds by a small but statistically real margin (mean Brier 0.582 vs. market 0.567, paired
t-test p=0.021). Separately, the pi-ratings literature (Constantinou & Fenton 2013, read in full
this project's ML research pass) needed nearly 2,000 held-out match instances before a well-designed
rating system showed a stable, if modest, positive edge over market — and still lost money in 2 of
5 individual seasons. Both point the same direction: beating a real, liquid market from a domain
model alone is hard and needs a lot of validated evidence before it should be trusted.

## Decision

When a liquid market (real two-sided book, tight spread) exists for a question, submit at or near
the market price by default. A domain model may be used to justify a small nudge, but a domain model
should not be trusted to override a liquid market by a wide margin without match-specific evidence
that the market is missing.

## Consequences

This is easier: for the majority of DIRECT-tier questions (match winner, totals, BTTS), submission
is fast and defensible, and matches the project's own long-run track record (this tier's the
best-performing in the campaign).

This is harder: it caps the upside on questions where the domain model might genuinely be right and
the market wrong — a real cost paid to avoid the larger downside risk documented in 0002.

**Evidence this decision was tested, not just assumed:** France vs Spain (2026-07-14) deliberately
tested a deviation from this rule on the match-winner-adjacent question ("Spain advance to the
final") — see that match's write-up. It won. One live win doesn't overturn 505 historical matches
of evidence, but it's logged honestly as a genuine counter-example, not smoothed over.