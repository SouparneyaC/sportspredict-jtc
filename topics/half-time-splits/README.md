# Half-Time Splits

Pricing for half-time result and other HT-split questions. No dedicated scripts of its own — a
stub folder completing the 14-topic taxonomy. This is the one family that's almost always
DIRECT-tier (a liquid market line exists), so it's priced by trusting the market rather than
through a domain model — see `writeups/decisions/0001-market-priority-over-domain-model.md`.

## Current status

DIRECT-tier questions as a whole (of which HT splits are the largest sub-category) have the
project's best-performing beat-crowd rate historically (73.5%, per
`PREDICTION_INSTRUMENT_WRITEUP.md`'s category-performance table) — precisely because they're
market-anchored rather than model-driven.

## Shared inputs

No dedicated data/script — priced directly from each match's own Smarkets/market quote
(`matches/*/02_smarkets_markets.json` or `09_smarkets_*.json`).

## Root-doc mentions

- [`PREDICTION_INSTRUMENT_WRITEUP.md`](../../PREDICTION_INSTRUMENT_WRITEUP.md) — the DIRECT_MARKET tier's performance table and rationale.
