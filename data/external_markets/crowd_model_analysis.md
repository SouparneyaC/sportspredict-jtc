# Crowd-consensus model: how SportsPredict's crowd diverges from sharp markets

Analysis date: 2026-06-13. Source data: `settled_markets_ledger.json` (26 questions, 3 matches)
cross-referenced against each match's `sources` block for verified external market prices
(Smarkets/Polymarket/Pinnacle/Kalshi, all VERIFIED_API tier).

## 1. The headline finding: crowd runs systematically ABOVE the verified market

Of the 17 questions (across KOR-CZE, CAN-BIH, USA-PAR) where we have BOTH a SportsPredict
crowd-consensus number AND a verified sharp-market price for the same event:

- **15/17 (88%) crowd >= market**, typically by +1pp to +14pp (median ~5-8pp).
- Only 2/17 go the other way, and one of those (HT-tied, USA-PAR) is a negligible -2pp.
- The one meaningful exception is USA-PAR Q8 (4+ cards): crowd=0.49 vs market=0.576 (-8.6pp).

This is NOT limited to "named team wins" questions - it shows up on player-scoring props too:
- Son Heung-min scores: crowd=0.40 vs market~0.28-0.315 (+8.5 to +12pp)
- Patrik Schick 1+ SOT: crowd=0.67 vs market~0.60 (+7pp)
- Jonathan David scores: crowd=0.38 vs market~0.31-0.345 (+3.5 to +6.9pp)
- BIH 5+ corners / BIH scores 2H: crowd above market by +9.5pp / +7.1pp

## 2. Overall accuracy: market beats crowd against the actual outcome, 11/17 (65%)

For each of the 17 comparisons, which reference (crowd or market) ended up closer to the
actual binary outcome:

| Match | Market closer | Crowd closer |
|---|---|---|
| KOR-CZE | 3 | 1 |
| CAN-BIH | 7 | 0 |
| USA-PAR | 1 | 5 |
| **Total** | **11 (65%)** | **6 (35%)** |

USA-PAR is the outlier - it was the one lopsided blowout (4-1), and the crowd's more
"inflated" numbers happened to track a lopsided result better. CAN-BIH (a tight 1-1 draw)
is where market dominance was most stark (7/7).

## 3. External research corroboration (via 2 parallel research agents, 2026-06-13)

- **"Goal-line oracles" (PMC11785260)**: a wisdom-of-crowd football study found crowds
  systematically overestimate "big"/popular teams (e.g., Man City overestimated by 0.69 xG,
  Arsenal by 0.43 xG) relative to bookmaker odds, and crowd predictions underperformed
  bookmaker odds in backtest. This is the closest documented analog to our finding.
- **Acquiescence/desirability bias** (general survey research + a 2025 LLM-forecasting-ensemble
  paper, PMC11800985): probability-elicitation formats (where individuals submit a number,
  no real money/liquidity) are systematically prone to "favor positive resolutions above
  empirical expectations."
- **SportsPredict / Jump Trading mechanics**: per citybiz coverage, SportsPredict (Jump Trading
  partnership) has users "set the exact mathematical probability" for outcomes, Brier-scored.
  This is exactly the probability-elicitation-poll format the literature says is MOST prone to
  the inflation bias above (vs. a real-money market with liquidity discipline).
- **Host-nation theory - DEBUNKED**: johnknightstats (Substack, using 1982+ World Cup data)
  found host nations perform almost exactly at expectation historically (~+0.01 wins above
  expected across 67 matches), with huge variance (Qatar 2022 was the worst-ever host
  performance, -0.39). Our n=2 (Canada drew, USA won 4-1) spans that whole variance range -
  NOT a validated signal. All 3 hosts (USA, Canada, Mexico) play again 2026-06-18/19, so this
  would only become relevant again then, and even then should not be treated as a hard rule.

## 4. The actionable rule for match-winner questions

Backtest: for each of the 3 settled match-winner questions, squared error vs actual outcome
for three candidate estimates (crowd, market, avg(crowd,market)) vs. what we actually submitted:

| Match | Outcome | Crowd err^2 | Market err^2 | avg err^2 | Our actual err^2 | Our actual RBP |
|---|---|---|---|---|---|---|
| KOR-CZE | Korea won (1) | 0.2401 (best) | 0.3906 (worst) | 0.3108 (mid) | 0.2916 (~avg) | -0.08 |
| CAN-BIH | Canada drew (0) | 0.3844 (worst) | 0.2894 (best) | 0.3352 (mid) | 0.5625 (worse than all 3!) | -14.53 |
| USA-PAR | USA won 4-1 (1) | 0.16 (best) | 0.2862 (worst) | 0.2184 (mid) | 0.2862 (=market, worst of 3) | -8.81 |

Crowd was closer 2/3, market was closer 1/3 - neither is a reliable single anchor (n=3, can't
overfit). But **avg(crowd, market) was NEVER the worst of the three in any match**, while BOTH
of our disasters came from picking what turned out to be the single worst available number
(an unvalidated internal model in CAN-BIH; pure market-deference in USA-PAR, where market
itself was the worst reference that match). This is a minimax-regret argument, not an
accuracy claim.

**RULE: for "Will Team X win the match?" questions, estimate = average(crowd_consensus,
verified_sharp_market).** This supersedes the cruder "shrink toward 50%" heuristic from the
prior edge-analysis memory - shrinking toward market+crowd's actual midpoint is more precise
than shrinking toward an arbitrary 50%.

## 5. The actionable rule for everything else (props, team-stats, compound markets)

Given crowd >= market in 15/17 cases (88%) and market beat crowd on raw accuracy 65% overall,
the existing **tier1_market (undeviated)** approach is correct and should continue: when a
verified market exists, submit close to it, and do NOT chase the crowd's typically-inflated
number. This explains why "tier1_market_deviated" (2 cases, both deviations were UPWARD i.e.
toward the inflated crowd number) underperformed (+1.66/q avg vs +4.39/q for undeviated).

Tier2_realdata (no market exists, build our own model) remains the top-priority, highest-EV
category (5/5, +7.96 avg RBP) and is unaffected by any of this - there's no crowd/market
reference to be biased by in the first place.

## 6. Caveat on RBP formula precision

The above err^2 figures use an ASSUMED formula RBP ∝ (crowd_err^2 - us_err^2) * scale. This
formula does NOT perfectly reproduce all 26 actual RBP values (e.g., CAN-BIH Q9 Dzeko:
us=0.60 is further from outcome=0 than crowd=0.58, which should be a small negative RBP under
this formula, but the actual RBP was +2.89). The scale constant also appears to vary
significantly between questions (implied scale ~1.5 for KOR-CZE Q4, ~67 for USA-PAR Q4, ~82
for CAN-BIH Q4) - SportsPredict's real scoring formula likely includes a per-question
stake/weight we don't have access to. Treat all err^2-based comparisons above as DIRECTIONAL
evidence only, not exact RBP predictions.
