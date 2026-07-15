# Argentina vs Switzerland — Pricing Methodology (QF, 2026-07-12)

**Match:** ARG vs SUI, WC2026 Quarterfinal. `match_id: f444b793-6a20-48a1-862c-e748781b5f91`
**Window:** opens 2026-07-12T01:00 UTC, closes 05:00 UTC.
**Venue:** GEHA Field at Arrowhead Stadium, Kansas City. Neutral.
**Referee:** João Pinheiro (Portugal) — confirmed via web search, corroborated against our own ESPN data on his 2 other WC2026 matches.

## Why this match is the real test of the new discipline

Argentina's point-in-time Elo edge over Switzerland is **+213.96** — almost the identical
magnitude to Spain's +216.61 over Belgium, the match that produced yesterday's postmortem. This
is the first match since that postmortem with the same blowout-level mismatch shape, and it has
the same paired-count-prop structure (Switzerland 3+ SOT / Argentina 5+ SOT, Switzerland 4+
corners / Argentina 7+ corners) that let the Belgium miss happen. Both safeguards from
yesterday were applied here under the conditions they were built for, not just in the abstract.

## SYMMETRIC_REGIME_COVERAGE, applied with a real adjustment

Switzerland's own SOT and corners both decline monotonically as opponent strength rises this
tournament — 7 SOT vs Qatar (Elo 1564), down to 2 SOT vs Colombia (Elo 2064), their strongest
opponent by a wide margin. Argentina (2230) is stronger than every team Switzerland has faced.

Rather than trust the naive 5-game average (which produced 0.84 for 3+ SOT and 0.71 for 4+
corners — numbers that would have repeated exactly the Belgium mistake), a regime-adjusted
estimate was built using only Switzerland's 2 toughest-opponent games (Algeria, Colombia) as the
primary reference class. That brought the numbers down to 0.76 and 0.61 — real movement, not a
check-the-box exercise. Both were still meaningfully above market (0.60 and 0.40), so market was
weighted more heavily still in the final blend: **0.62** and **0.45**. The naive model's original
figures would have been off by roughly 20+ points each, caught before submission this time.

The mirror-direction check (does Switzerland's defense suppress Argentina's own count props?)
found real but moderate evidence — Colombia still managed 15 shots and 7 corners against
Switzerland, only their shot *quality* was suppressed (3 SOT from 15 shots). Argentina's own
props already agreed closely with market, so no extreme override was needed there.

## The other big correction: Julián Álvarez

Álvarez has 0 goals and 0 assists in 5 games this tournament, and — importantly — his underlying
shot volume is also minimal (5 shots total, never more than 2 in a single game). That's
corroborating evidence of genuinely low involvement, not just finishing variance that the market
should shrug off. Market prices his "scores or assists" question at 0.50, a 50-point gap against
the empirical record, the largest gap of the session. This is the same shape as the Lamine Yamal
reputation-inflation pattern this project has now validated three times on a different player —
market pricing a recognizable attacking name on role expectation rather than current tournament
production. Priced at **0.32**, well below market but not at the extreme empirical 0%.

## Summary table

| # | Question | Estimate | Market | Gap | Resolution |
|---|---|---|---|---|---|
| 1 | Argentina advances | 0.77 | 0.7463 | 2.4pp | Agreement |
| 2 | 0-0 at HT | 0.35 | 0.3864 | 3.6pp | Agreement |
| 3 | Switzerland leads at any point | 0.32 | NA | — | Model-only |
| 4 | 2 or fewer goals | 0.58 | 0.5902 | 1pp | Agreement |
| 5 | Goal after 2nd hydration break | 0.47 | NA | — | Late-window discipline |
| 6 | Switzerland 3+ SOT | 0.62 | 0.5962 | 2.4pp (post-correction) | SYMMETRIC_REGIME_COVERAGE, see above |
| 7 | Sub scores/assists | 0.53 | NA | — | Reused corpus base rate |
| 8 | Messi scores | 0.50 | 0.4528 | 4.7pp | Validated precedent, RULE6 |
| 9 | Alvarez scores/assists | 0.32 | 0.50 | 18pp (post-correction) | Reputation-inflation pattern, see above |
| 10 | Embolo 1+ SOT | 0.57 | 0.5525 | 1.8pp | Agreement |
| 11 | Switzerland 4+ corners | 0.45 | 0.3968 | 5.3pp (post-correction) | SYMMETRIC_REGIME_COVERAGE, see above |
| 12 | Argentina 5+ SOT | 0.63 | 0.6583 | 2.8pp | Mirror check, agreement |
| 13 | Argentina 7+ corners | 0.20 | 0.2169 | 1.7pp | Near-miss line calibration |
| 14 | 4+ total cards | 0.37 | 0.4037 | 3.4pp (post-correction) | Weighted toward market, see derivations |
| 15 | Penalty OR red | 0.45 | 0.4205 | 3pp | Agreement |

Every gap that started above the ~15-20pp recheck threshold (Q6, Q9, Q11, Q14) was explicitly
resolved and the final residual gap against market is under 6pp in all four cases.
