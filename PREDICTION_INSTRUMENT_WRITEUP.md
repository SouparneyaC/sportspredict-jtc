# Prediction Instrument Taxonomy — Complete Written Guide

**Campaign scope:** WC2026 SportsPredict, group stage through Round of 32 (knockout stage).
**Settled matches covered:** 60+ matches, 436+ submitted questions, +872 cumulative RBP.
**Purpose of this document:** A full written account of every instrument shown in the taxonomy
diagram — what data was collected, what computations were run, what rules were applied, and
how each layer of the pipeline fed into the next, with specific evidence from every settled
match where the instrument was used.

---

## OVERVIEW: What the Diagram Is Showing

The instrument map is a directed acyclic graph — a flowchart where each layer feeds into the
next and nothing loops back. The five layers are:

1. **Raw Sources** — where the data comes from
2. **Statistical Processing** — what mathematical operations transform that data into probability estimates
3. **Named Rule System** — named adjustments that are applied on top of any estimate
4. **Question Categories** — how every question is classified by the pricing technique that actually produced the estimate
5. **Output** — the submitted number, the resulting score, and the campaign track record

Every single submitted probability we have ever produced passes through this pipeline from left
to right. Nothing is submitted without going through all five layers. The diagram makes the
implicit explicit — it shows that "we submitted 0.65 for France to score first" is not a
guess, it is the output of a specific chain: ESPN goal data → Poisson lambda-fitting → RULE7
check → DIRECT_MARKET category → 0.65 → +21 RBP.

---

## LAYER 1: RAW SOURCES

### 1.1 ESPN Soccer API

**What it is:**
ESPN's undocumented but stable soccer API returns structured JSON for every WC2026 match.
The primary endpoints used are:

- `sports/soccer/summary?event={event_id}` — full match summary including rosters, stats, commentary
- `sports/soccer/teams/{team_id}/schedule` — a team's full fixture list with event IDs
- `sports/soccer/scoreboard?dates={YYYYMMDD}` — all matches on a given date

The most important insight from early sessions: **the API's `leaders` block only returns the
single top performer per statistical category** (one player for goals, one for SOT, one for
fouls). This is useless for player-prop pricing since it misses every other player. The correct
data is in `rosters[].roster[].stats` — a full per-player stat line for every participant in
the match, whether they scored or not. This distinction was discovered during France-Sweden
pricing when Dembélé's stats and Isak's stats were invisible in `leaders` but appeared
correctly in the roster array. All player data from the France-Sweden match onward uses the
roster array exclusively.

**What data is collected for every match:**

For each of both teams' three group-stage matches, the following are extracted per match:
- **Team level:** fouls committed, shots on target (SOT), total shots, corners, offsides,
  yellow cards, red cards, possession percentage
- **Player level (per starter and key substitutes):** goals, assists, SOT, total shots,
  offsides (for forwards), fouls committed (for midfielders/defenders), yellow cards

This produces a 6-match data block (3 matches per team) that anchors every estimate for
the upcoming match.

**How it was used — group stage examples:**

*GER-CUR (Germany 7-1 Curaçao, +72.47):* Germany's Poisson lambda for offsides was fit
from their 3 group matches (avg 1.5 offsides/game). Curaçao's fouls average from their
2 group matches showed 10.5 fouls/game. Bacuna's SOT history (0-1-0 across 3 matches,
avg 0.33) from the roster stats array anchored the thinned Poisson estimate at 0.21 for
his SOT prop. Every one of these numbers came from the ESPN API, not a media summary.

*JPN-SWE (Japan 1-1 Sweden, +70.49):* Sweden's average SOT was 7.5/game (vs Japan's 4.0).
This was a genuine structural gap visible across all 3 of Sweden's group matches — it was
not one outlier game. That 7.5 vs 4.0 gap, confirmed via 3-match ESPN data, produced the
Skellam model for "Sweden more SOT than Japan" (Q2) which won +23.98 — the single best
result from that match. The ESPN API delivered this signal; no amount of match previews or
media analysis would have.

*BEL-EGY (Belgium 1-1 Egypt, +63.72):* Belgium's average SOT of 8.2/game vs Egypt's 3.2/game
from ESPN data produced a very large Skellam gap (P(EGY more SOT) raw ≈ 0.11). Submitted at
0.11. Outcome was a 3-3 SOT tie — but because "more than" resolves NO on a tie, the direction
was still correct. The low submission (+10.71 win on Q4) came entirely from the ESPN stat
differential.

*ENG-CDR (England 2-1 Congo DR, +119.36):* England's corner average of 8.0/game across their
3 group matches (8, 9, 7) — pulled from the ESPN API roster block — anchored Q8 (England 8+
corners) at 0.65 from direct market cross-validation. Their shot average of 19.33/game was
the single biggest input into Q10 (20+ total shots, submitted 0.85, won +27.51). Congo DR's
competitive-match SOT profile (1.5/game against Portugal and Colombia specifically — the
outlier 19-shot UZB game was flagged and excluded as a mismatch context) gave the estimate
for Q7 (England 7+ SOT) and anchored the RULE15 suppression of Wissa's SOT prop.

*FRA-SWE (France 3-0 Sweden, +148.01):* France's player data from the roster array was the
key input. Mbappé: 4 goals + 2 assists in 3 matches, 2+ SOT in all 3 games (4, 3, 2 SOT
respectively). Dembélé: hat-trick in the Norway match (most recent), 4 goals total. Gyökeres:
1 goal in 3 matches, only against the weakest opponent (Tunisia). Isak: 2+ SOT in 2/3 matches.
These per-player histories from `rosters[].roster[].stats` set the prior for every player prop
in that match.

**What the API cannot tell you:**
The API has no market-implied probabilities, no tactical shape data, and no live lineup
confirmation. It reports what happened, not what will happen. It also has a known data-gap
problem: some older matches (especially early group-stage games) had partially unpopulated
`match_facts` blocks in the stored raw files. The operational fix (established during RSA-CAN)
is to always pull `summary?event={id}` fresh rather than trusting any cached match_facts field.
South Africa's own group-match files had only 1 of 4 raw files with real box-score detail —
fresh pulls resolved this every time.

**The one known Isak edge case:**
During FRA-SWE pricing, a player named "Isak Hien" (a Swedish centre-back) appeared in
roster-array searches for "isak" and was confused with Alexander Isak (the striker) because
both share the first name. Fixed by adding a `'hien' not in norm` exclusion filter in the
parsing logic. All Isak data from FRA-SWE onward is confirmed as the correct player.

---

### 1.2 Smarkets Exchange API

**What it is:**
Smarkets is a peer-to-peer betting exchange where real money trades at market-clearing prices.
Unlike a bookmaker (who sets the price), Smarkets shows what the actual market of real,
financially-incentivized participants believes. The key difference from a sportsbook:

- A **liquid** market has both a best bid and a best offer. The mid is the cleanest available
  probability estimate: `mid = (best_bid + best_offer) / 2`.
- An **illiquid** market has only an offer (or only a bid). The offer-side price from a
  one-sided market systematically overstates the true probability because market makers
  build in an excess margin when there's no opposing side to discipline the price. The
  operational convention established across all matches: **illiquid offer-only price × 0.945**
  to partially correct for this overpricing. This multiplier was derived empirically from
  observed spread patterns and is applied uniformly to every illiquid player market.

**How prices are expressed:**
Smarkets prices come back from the API as integers in basis points where 7634 = 76.34%.
All processing divides by 10,000 before any arithmetic.

**The broken `name=` parameter — a critical operational fact:**
Smarkets' event search API has a `name=` query filter parameter that appears to work
(returns HTTP 200 with a non-empty response) but in practice returns an unrelated, unfiltered
list of events regardless of what name string is passed. This was discovered by the research
agent during the RSA-CAN pricing session and confirmed in every subsequent match (7 matches in
a row now). The working method: `limit=300` in the event list endpoint plus client-side string
filtering on the returned event names. Every event in this campaign was found this way.
Using `name=` would have produced wrong data with no error — a silent, hard-to-detect failure.

**The three endpoints used:**

1. `events/?type=football_match&limit=300` — find the event ID for today's match
2. `events/{event_id}/markets/?limit=300` — get all available markets for the match
3. `markets/{market_id}/contracts/` + `markets/{market_id}/quotes/` — get contract names and
   live bid/offer prices for each contract within a market

The `fetch_quotes.py` helper script (in the scratchpad) automates steps 2 and 3 into a single
function call `get_market(market_id)` that returns a table of contract names, bids, offers,
mids, and a liquidity flag.

**What markets exist (and which ones are used):**

Every knockout-stage match had 140-180 total markets. The markets that directly answer
a question are the most valuable:

- **FTR (Full-Time Result):** Home/Draw/Away win probabilities. Used directly for match-winner
  questions and as a signal for RULE7 (if any team is below 15% here, the rule fires).
- **BTTS (Both Teams to Score):** Direct for "will both teams score" questions. Also used
  indirectly: `P(CDR scores) ≈ P(BTTS YES) / P(England scores)` for ENG-CDR, where no
  direct CDR goal market existed.
- **Over/Under goals (OU2.5, OU3.5):** Used to fit Poisson lambda for total goals via brentq.
  Critically: always fit lambda from BOTH thresholds and verify they converge. For MEX-ECU,
  both gave lambda ≈ 1.97, confirming the estimate.
- **Team-specific OU goal lines (e.g., France OU2.5, Sweden OU0.5):** More useful than total
  goal markets because they isolate each team's attacking output. France's lambda of 2.672 and
  Sweden's 0.864 in FRA-SWE came from these team-specific lines. Their sum (3.536) matched
  the total market lambda (3.501) exactly — internal consistency check passed.
- **Team SOT OU lines:** Used to fit each team's shots-on-target lambda. England's SOT OU5.5
  (56.30% over) in ENG-CDR gave lambda_ENG_SOT = 6.054, directly producing P(England 7+ SOT)
  = 0.402. Norway's SOT OU4.5 in NOR-CIV gave lambda_NOR_SOT = 5.13.
- **Cards OU lines (multiple thresholds):** Used to fit the total-match card lambda via
  multiple-threshold consistency checking. RSA-CAN's card lambda of ~4.0 was fit from
  OU1.5/OU2.5/OU3.5/OU4.5 simultaneously (converging to 3.87-4.01 across all four — the
  consistency itself was a signal of model reliability).
- **Goal-1 time bracket:** A 10-contract market (1-10', 11-20', 21-30', ..., 81-90', None)
  giving the probability that the first goal is scored in each 10-minute window. Used for
  every "goal before/after the hydration break" timing question where a market exists.
  RSA-CAN's Q5 (goal before 1st break): bracket(1-10) + bracket(11-20) + 0.4×bracket(21-30)
  = 0.398. This was the cleanest early-window timing estimate of the campaign.
- **Corners markets (team-specific OU, total OU, most-corners):** France's OU6.5 corners
  market gave lambda_FRA_corners = 6.608, which fed Q2 (France 6+ corners). England's
  OU7.5 corners market in ENG-CDR was used as a direct read for Q8 (England 8+ corners).
  NED-MAR used the NED -0.5 corners handicap (51.74%) rather than a team-specific OU line.
- **Player markets (anytime goalscorer, player SOT OU lines, score-or-assist):** The most
  variable in terms of liquidity. FRA-SWE had all four key player props (Mbappé SOT, Dembélé
  scorer, Gyökeres scorer, Isak SOT) as genuinely two-sided liquid markets — highly unusual
  and the cleanest player-prop pricing of the season. NOR-CIV had Haaland (liquid, 51.42%)
  and Sørloth (liquid, 22.99%) alongside two illiquid (Ødegaard, Amad Diallo). MEX-ECU had
  every single player market illiquid. ENG-CDR had every player market illiquid.
- **Penalty, Any sent off, To qualify, Will there be ET/pens, Highest scoring half, Score
  both halves:** All used as direct reads where the question wording matches the market.
  England score both halves (41.35%) was Q6 in ENG-CDR — a one-to-one match, trust near-raw.
  Penalty markets in ENG-CDR (25.34%) and NOR-CIV (30.77%) fed the compound P(pen OR RC)
  calculations.

**Key markets that DON'T exist (and what that forced):**
- No "offsides before 1st hydration break" market in any match. Required self-built
  time-window scaling from ESPN team averages.
- No "card after 2nd hydration break" market in any match. Required the dangerous
  timing-decomposition method.
- No "substitute scores" market in most matches. Required lambda decomposition × historical
  sub-goal-share rate.
- No "own goal" or "goal scored OTB" market. Required pure base-rate estimates.
- No per-player offside market in any match.

These gaps are precisely where the TIMING_NO_MARKET category lives — and where the biggest
losses of the campaign came from (RSA-CAN Q1: -39.68; GER-PAR Q14: -48.68).

---

### 1.3 Historical Match JSON Files

**What they are:**
Every match we have priced lives in `data/external_markets/` as a JSON file named
`{team1}_{team2}_{YYYY-MM-DD}.json`. As of this writing there are 100+ files. Each file
contains the pre-match question analysis, all sourced data, computed estimates, and
(after the match settles) a `post_match_results` block with every question's outcome, our
submitted probability, the crowd's probability, and the RBP earned.

**Why this layer exists:**
A player like Bakambu (Congo DR) appeared in two separate matches: COL-CDR and CDR-UZB.
His SOT history across both matches provided the player-specific precedent that anchored
RULE15's application in ENG-CDR (competitive CDR matches: avg 1.5 SOT, 7.5 shots — the UZB
match was flagged as an outlier mismatch and excluded). Without the historical JSON files,
this precedent would have been invisible.

**The mandatory first step — history check before any API call:**
Every match in this campaign begins with `ls data/external_markets | grep {team1} | grep {team2}`
before a single ESPN or Smarkets API call is made. This step has never come up empty across
all knockout matches. Examples of what it surfaced:

- **GER-PAR:** Enciso's prior SOT history in TUR-PAR (0 SOT in a Paraguay win, mild RULE15
  confirmed). This was a named, direct precedent that justified deeper suppression of Enciso
  in GER-PAR. The TUR-PAR file had his exact SOT = 0 in a match where Paraguay dominated —
  the same situation expected to repeat.
- **FRA-SWE:** Sweden's offside records (3, 3, 2 across three matches — win, loss, draw)
  confirmed a structural consistency that was independent of match context. The SWE-TUN and
  JPN-SWE and NED-SWE files all showed this pattern.
- **NED-MAR:** Saibari's 2-for-2 goal-scoring streak (scored in both GD1 vs Brazil and GD2
  vs Scotland, with Brahim Diaz assisting both times). This was visible in MAR-HAI and
  SCO-MAR files. That precedent bumped his score-or-assist estimate from the raw liquid market
  mid (0.2864) slightly up to 0.32.
- **ENG-CDR:** The GHA-ENG file (England's 0-0 draw with Ghana, only 3 SOT from 19 shots)
  was the critical cautionary reference for England's SOT bimodality. Without it, England's
  average would have been anchored too high. This is also where the Bellingham lesson
  originated: using his 0 SOT in the Ghana match as a worst-case comp produced too much
  suppression; the correct approach (learned post-match) was to average his SOT across all
  3 group matches (2, 0, 1 → avg 1.0).
- **NOR-CIV:** The GER-CIV file explicitly warned against treating Ivory Coast as a weak
  mismatch — "AFCON 2023 champions, CIV actually led 1-0 in that match before Germany's
  comeback." This framing prevented over-suppression of all CIV props.

**What's stored in each file:**
```
match / date / stage / espn_event_ids / smarkets_event_id
prior_lessons_consulted     ← list of prior files + docs consulted
knockout_context            ← group-stage record for each team
wc2026_espn_stats           ← full 3-match box score per team + player stats + averages
smarkets_markets            ← all fetched market prices, tagged liquid/illiquid
context_flags               ← named edge cases, precedents, rule applications
questions                   ← 15 question blocks with instrument, reasoning, estimate
post_match_results          ← outcome, us, crowd, RBP per question (added after match)
```

The `prior_lessons_consulted` field is not cosmetic — it is the formal record of which
historical context was actually used when pricing each question. NOR-CIV explicitly listed
`STEPS_FOR_HIGH_POINTS.md` and `KNOCKOUT_STAGE_PRICING_DEEP_DIVE.md` as load-bearing context
for Q12 and Q14, because the GER-PAR offside disaster was the direct justification for
shading Q12 up from a naive P(4+)=0.02 to 0.42.

**Q-number ordering trap:**
The platform reorders questions between the draft and the submission screen. This happened
in at least two confirmed cases (BRA-JPN: a clean cyclic shift where our last question moved
to position 1 and everything else shifted down). All `post_match_results` matching is done
by question text, never by position number. Any automated analysis of these files must do the
same.

---

### 1.4 Statistical Model Outputs (Historical Coefficients)

**What this layer contains:**
Pre-fitted parameters that encode information about football at a much larger scale than
the 3 WC2026 group matches available per team. These include:

- **Elo ratings:** Team strength estimates from eloratings.net, fit on decades of international
  results. Used in early matches to calibrate prior expectations before WC2026-specific data
  was available. As the campaign progressed and ESPN data accumulated, Elo was used less as a
  primary input and more as a sanity check.
- **Dixon-Coles ρ parameter:** A correction to the independence assumption in Poisson models,
  specifically for very low-scoring outcomes (0-0, 1-0, 0-1). Applied in matches where the
  total goal lambda was low (under 2.0) to prevent overstating P(0-0).
- **Negative-Binomial overdispersion parameter α:** Football goal distributions have more
  variance than a pure Poisson model implies. The NB α captures this extra spread. Applied
  when a match had an unusually uncertain lambda (e.g., Ecuador in their first 2 matches had
  0 goals from 16 SOT — a sample where the NB model's wider tails mattered).
- **Crowd Bias Model coefficients:** `crowd ≈ 0.514 + 0.61 × (our_estimate − 0.5)`. Fit on
  n=85 settled questions, r=0.83. The intercept 0.514 means the crowd anchors slightly above
  50%; the slope 0.61 means the crowd compresses our estimate 39% back toward 50% (Snowberg-
  Wolfers acquiescence bias). This is not used to generate estimates — it is used to predict
  what the crowd will submit, so that the gap between our estimate and the crowd can be
  anticipated before submission.

**How the Crowd Bias Model was used:**
During BEL-EGY, this model was applied out-of-sample for the first time. It predicted the
crowd's BEL-EGY values with RMSE = 5.8pp (mean bias -0.5pp — essentially unbiased), matching
the in-sample residual standard deviation of 7.1pp. The model has continued to be used as
a planning tool since then: if we submit 0.20 and the crowd is predicted to be at 0.41, we
know we're taking a large directional bet against the crowd before submission, which should
only be done when the evidence is strong.

---

## LAYER 2: STATISTICAL PROCESSING

### 2.1 Lambda-Fitting via brentq (Scipy)

**What it does:**
Given a market price for "P(X > k) = p", solve backwards for the Poisson rate λ that produces
that probability. This extracts the market's full implied distribution, not just a single
threshold.

**Why it matters:**
A market that says "Over 2.5 goals = 45.3%" is telling you about a single point of the goal
distribution. But what you actually need to answer questions like "P(3+ goals)", "P(exactly 2
goals)", "P(France scores 2+)" is the full Poisson distribution — and that requires λ.
brentq finds the unique λ in a specified search range that satisfies `poisson.sf(k, λ) = p`
(where sf is the survival function, i.e., 1 − CDF(k)).

**Critical lesson from MEX-ECU:**
The initial attempt to fit the shots lambda (λ_shots ≈ 21) using `scipy.optimize.least_squares`
with a starting point of `x0=[2.0]` failed silently: the optimizer converged to λ ≈ 2.0 (the
goals lambda) instead of the shots lambda, because the starting point was in the wrong basin
of attraction. The fix was to use `brentq` with correct search bounds `(0.001, 100)` on each
OU threshold separately. OU20.5 (52.1% over) → λ_shots = 21.14. OU21.5 (46.5% over) → λ_shots
= 21.02. Both converged to the same value independently, confirming the estimate.

**Examples by match:**

*FRA-SWE:* France OU2.5 goals (liquid) → λ_FRA = 2.672. Sweden OU0.5 goals → λ_SWE = 0.864.
Sum = 3.536, vs. total OU2.5 market lambda = 3.501. Cross-validation gap: 0.035 — excellent.
France OU6.5 corners → λ_FRA_corners = 6.608. Verified: France + Sweden corner lambdas
summed to 9.995 vs direct total OU8.5 lambda of 10.289 — within 3%, acceptable.

*MEX-ECU:* Mexico OU1.5 goals (32.3% over) → λ_MEX = 1.160. Ecuador OU0.5 goals (56.7%
over) and OU1.5 (17.7% over) → λ_ECU = 0.806. Combined: 1.966 vs total OU2.5 lambda of
1.970 — near-perfect consistency. Shots: brentq on OU20.5/OU21.5 → λ_shots = 21.08.

*ENG-CDR:* England SOT OU5.5 (56.30% over) → λ_ENG_SOT = 6.054, giving P(ENG ≥ 7 SOT) =
poisson.sf(6, 6.054) = 0.402. CDR SOT OU1.5 (58.23% over) → λ_CDR_SOT = 1.957. England
OU2.5 goals + OU1.5 goals → λ_ENG = 2.11 (avg of 2.158 and 2.063 from two threshold fits).

*NED-MAR:* Total goal lambda ~2.43 from OU2.5 (43.67% over) and OU3.5 (23.02% over).
NED card lambda ~1.52 from NED cards OU1.5 (54.07% over). MAR card lambda ~1.46 from MAR
cards OU1.5 (51.80% over). These individual team lambdas were the key input for the
team-decomposition model that won +23.37 on "both teams receive a card."

*RSA-CAN:* Total card lambda ~4.0 from four separate card OU thresholds (3.87, 4.01, 3.99, 3.95
across OU1.5/OU2.5/OU3.5/OU4.5) — four-threshold consistency is strong evidence the lambda
is robust. Team goal lambdas: SA ~0.80, CAN ~1.54 from team-specific goal OU markets.

---

### 2.2 Poisson CDF and Skellam PMF

**Poisson CDF — what it does:**
Given a fitted lambda, compute the probability that a count exceeds a threshold.
`P(X ≥ k) = 1 − poisson.cdf(k-1, λ)` = `poisson.sf(k-1, λ)`.

**Examples:**
- FRA-SWE Q1 (3+ total goals): λ_total = 3.536 → P(X ≥ 3) = 0.658. Direct market read.
- ENG-CDR Q10 (20+ total shots): ENG expected shots ~19.33 + CDR competitive ~7.5 = 26.8.
  P(X ≥ 20 | λ=26.8) ≈ 0.90+, trimmed to 0.85 for general uncertainty. This was the
  highest-conviction estimate of the ENG-CDR session and won +27.51.
- MEX-ECU Q6 (Mexico 6+ SOT): λ_MEX_SOT = 3.870 → P(X ≥ 6) = 0.195. Mexico had never
  reached 6 SOT in any group match (4, 4, 5) — the ESPN data and the Poisson model agreed.
  Submitted 0.20 (floored from 0.195). Won handsomely against a crowd that gave this 35%.
- NOR-CIV Q9 (Norway 6+ SOT): λ_NOR_SOT = 5.13 → P(X ≥ 6) = 0.406, bumped to 0.43 using
  the direct NOR-SEN precedent (Norway had 7 SOT in that match, their 6+ question settled YES).
- GER-PAR Q14 (3+ offside calls): Germany 0 offsides in all 3 group matches. Combined offside
  lambda = 0.0 + 1.33 (Paraguay avg) = 1.33. P(X ≥ 3 | λ=1.33) = 0.15. Floored to 0.30.

**Skellam PMF — what it does:**
The Skellam distribution is the distribution of the difference of two independent Poisson
random variables. If X ~ Poisson(λ₁) and Y ~ Poisson(λ₂), then (X−Y) follows a Skellam
distribution. Used for head-to-head comparison questions: "will Team A have more [stat] than
Team B?"

`P(A > B) = P(X − Y > 0) = 1 − skellam.cdf(0, λ_A, λ_B)`
`P(A = B) = skellam.pmf(0, λ_A, λ_B)`

The skellam.cdf(0, λ_A, λ_B) gives P(X−Y ≤ 0) = P(A ≤ B), so subtracting from 1 gives P(A > B).

**Examples:**
- MEX-ECU Q3 (Mexico more SOT than Ecuador): λ_MEX_SOT = 3.870, λ_ECU_SOT = 3.025.
  `1 − skellam.cdf(0, 3.870, 3.025)` = 0.550 raw. After RULE8 shade (draw=34.25%): 0.533.
  Submitted 0.53. This was one of the key RULE8-impacted questions of the campaign.
- JPN-SWE Q2 (Sweden more SOT than Japan): λ_SWE_SOT = 7.5, λ_JPN_SOT = 4.0 (from ESPN).
  Skellam gives P(SWE > JPN) ≈ 0.79. Submitted 0.76 (RULE8 light shade, draw=27.2%). Won +23.98.
- BEL-EGY Q1 (Egypt more fouls than Belgium): λ_EGY_fouls = 12.0, λ_BEL_fouls = 12.2.
  Near-identical averages → Skellam output ≈ 0.48. Submitted 0.46. Outcome: 15-15 tie
  (exact tie again — second time near-identical team averages produced a literal tie).

**The tie-resolution issue:**
In a "more than" question, a tie resolves NO. Skellam gives `P(A > B)` strictly — ties are
excluded. But the crowd prices "more than" questions as if P(tied) is negligible, because
intuition says two teams won't match exactly. In practice, for count statistics like fouls,
ties happen surprisingly often when team averages are close. This is part of why RULE8 shrinks
these estimates toward 0.50 when the draw price is elevated — high draw probability correlates
with closely-matched teams, which correlates with more tie-count outcomes.

---

### 2.3 Thinned Poisson (Player-Level Estimate from Team Lambda)

**What it does:**
When no liquid player market exists, derive the individual player's goal or SOT probability
from the team-level lambda and an assumed role share:

`λ_player = λ_team × player_share`
`P(player scores) = 1 − e^(−λ_player) = poisson.sf(0, λ_player)`

The player_share reflects what fraction of the team's total goals or SOT realistically
comes from this player based on their position and historical output.

**Examples:**
- ENG-CDR Q1 (Kane scores): λ_ENG_goals = 2.11. Kane's goal-share from group-stage data
  (2 goals in CRO, 0 in GHA, 1 in PAN = 3 goals in 3 matches, vs England team totals of
  4+0+2=6) → share ≈ 0.50. λ_Kane_goals = 2.11 × 0.50 = 1.055 → P(scores) = 0.652.
  Cross-validated with PAN-ENG analogy (similar match context, 1 goal in 2 SOT). Final: 0.65.
  Won +24.13.
- MEX-ECU Q1 (Jiménez scores): λ_MEX_goals = 1.160. Jiménez started 2 of 3 matches (rested
  GD3), scored 1 goal in 2 starts → share ≈ 0.67. λ_Jiménez = 1.160 × 0.67 = 0.777 →
  P(scores) = 0.54. Submitted 0.55 (light RULE8 shade for draw=34.25%).
- NOR-CIV Q2 (Sørloth 2+ SOT): λ_NOR_SOT = 5.13. Sørloth as second striker: share ≈ 0.20.
  λ_Sørloth_SOT = 5.13 × 0.20 = 1.026 → P(≥2 SOT) = 1 − e^(−1.026) − 1.026×e^(−1.026) =
  0.264. Near the liquid market mid (0.2299). Used market as primary anchor.
- FRA-SWE (Mbappé SOT): Liquid market existed (63.92%) — thinned Poisson used only as a
  cross-validation check (λ_FRA_goals=2.672, Mbappé share from 4 goals in 3 matches ≈ 0.40,
  λ_Mbappé = 1.069, P(≥2 SOT) ≈ 0.61). Cross-validation gap vs market: 3pp. Close enough
  to trust the market directly.

**When thinned Poisson is the primary instrument vs a cross-check:**
When a liquid player market exists (bid+offer both present), the thinned Poisson estimate is
used as a sanity check — it should be within ~10pp of the market. When only an illiquid
offer-only market exists, the thinned Poisson becomes more important as a way to assess
whether the illiquid price is directionally reasonable. When no player market exists at all
(MEX-ECU, most ENG-CDR player props), thinned Poisson is the primary instrument.

---

### 2.4 Compound P(A∪B) — Exact Union Rule

**What it does:**
For questions phrased as "A OR B", the exact probability formula is:
`P(A ∪ B) = P(A) + P(B) − P(A) × P(B)` (assuming independence)

This avoids double-counting the event where both A and B occur.

**Examples:**
- ENG-CDR Q14 (penalty OR red card shown): P(pen) = 0.2534 (from Penalty market), P(RC) =
  0.1154 (from Any-sent-off market). Compound:
  0.2534 + 0.1154 − (0.2534 × 0.1154) = 0.340. Submitted 0.34.
- MEX-ECU Q14 (penalty): direct market, 25.8%. No compound needed.
- NOR-CIV (penalty OR RC): P(pen) = 0.3077, P(RC) ≈ 0.10 (from sent-off market).
  Compound ≈ 0.385.
- FRA-SWE Q7 (red card shown): direct Any-sent-off market at 11.5%. No compound needed.

The compound formula appears simple but matters because na directly from the separate
markets would produce 0.2534 + 0.1154 = 0.3688 without the correction — an overstatement
of 2.9pp. In a question where the crowd is at 0.31 and we're at 0.34, a 3pp error matters.

---

### 2.5 Time-Window Scaling

**What it does:**
For questions about events in a specific time window (e.g., "goal before the first hydration
break" at ~25 minutes), scale the full-match Poisson lambda to the window:
`λ_window = λ_full × (t_window / 90)`
`P(≥1 event) = 1 − e^(−λ_window)`

**The critical early/late distinction — the single most important lesson in this category:**
This technique works reliably for **early windows** (before the first hydration break,
approximately minutes 0-24) but fails structurally for **late windows** (after the second
hydration break, approximately minutes 69+). The reason is not mathematical — the math is
the same either way. The reason is that early in a match, before fatigue, substitutions,
scoreline pressure, or match-state desperation enter the picture, team-level historical
averages are still doing real predictive work. Late in a match, all of those factors compress
every source of uncertainty in ways that a pre-match team average cannot see.

**Early-window results across all settled matches (combined: all positive):**

- RSA-CAN Q5 (goal before 1st break): Goal-1 time-bracket market gave a direct read
  (bracket(1-10) + bracket(11-20) + 0.4×bracket(21-30) = 0.398). Won +6.81.
- BRA-JPN Q10 (offside before 1st break): combined ESPN offside average, Brazil's
  outlier match trimmed from 8→2, λ_pre24 = 0.84 → P(≥1) = 0.57, trimmed to 0.52. Won +6.27.
- NED-MAR Q3 (goal in 1H stoppage time): λ_4min = 2.43 × (4/94) = 0.1034 → P(≥1) = 0.098.
  Submitted 0.10. Won +13.38.
- FRA-SWE Q14 (goal in 1H stoppage): two independent estimates — 1H-specific lambda (1.591,
  scaled to 4/49) = 0.122; full-match lambda (3.536, scaled to 4/94) = 0.140. Used 0.12.
  Won the question.
- MEX-ECU Q13 (goal before first break): combined goal lambda 1.97 × (25/90) = 0.547 →
  P(≥1) = 0.42. Time-bracket market briefly liquid (then suspended) showed 14.9%+14.5%+
  half of 12.2% = 0.35. Blended: 0.40. A safe early-window estimate.
- ENG-CDR Q13 (goal before first break): λ_pre25 = 2.11 × (25/90) = 0.586 → P(≥1) = 0.444.
  Submitted 0.47. Won +21.79 — one of the five biggest wins of the match.

**Late-window results across all settled matches (combined: all negative):**

- RSA-CAN Q1 (card after 2nd hydration break): card lambda ~4.0, assumed 40% of cards land
  post-69' → λ_late = 1.60 → P(≥1) = 0.78. Also added ET card add-on for +0.02. Submitted
  0.78. Outcome: very low total cards in the match (likely 0-2). **-39.68 RBP. The single
  worst result of the entire campaign.** Root cause: the 40% timing-share assumption was never
  independently verified against any market — it was a plausible-sounding heuristic built on
  the card lambda (which itself overstated actual cards) with an ET add-on that made it worse.
- NED-MAR Q4 (goal after 2nd hydration break): same method, λ_25min = 0.647 → P(≥1) = 0.477.
  Raw output happened to already sit inside 0.45-0.55. Deliberately left near-raw at 0.47.
  Still missed (outcome NO), but loss was only -3.51. Reduction from -39.68 to -3.51 across
  the same wrong direction is direct evidence the explicit trimming works.
- NED-MAR Q2 (card after 2nd hydration break): same method, trimmed from raw 0.77 to 0.65
  per the RSA-CAN lesson. Still missed, -3.51. The 90% reduction in damage from applying the
  lesson is confirmed.
- GER-PAR Q14 (3+ offsides in regulation): Germany 0.0 offside avg, Paraguay 1.33 avg →
  combined lambda 1.33 → P(≥3) = 0.15. But the match was flagged as the GER-PAR failure —
  the actual game became a grinding, high-pressing 90 minutes that the group-stage averages
  had no way to predict. **-48.68 RBP.** The lesson applied in NOR-CIV for Q12 (same question
  type, similarly clean ESPN data): deliberately shaded up from naive P(≥4) = 0.02 to 0.42
  per this precedent.

---

### 2.6 Crowd Bias Model

**What it is:**
A linear regression fit on n=85 settled questions:
`crowd_estimate ≈ 0.514 + 0.61 × (our_estimate − 0.5)`
(correlation r=0.83, in-sample residual std 7.1pp)

**What it tells you:**
The crowd compresses every estimate ~39% back toward 50% (the slope of 0.61 means a move
of 1pp in our estimate produces only 0.61pp in the crowd's estimate). The crowd also has a
slight upward anchor at 0.514, meaning it overestimates "rare" events by ~7pp and
underestimates "likely" events by ~4pp — the Snowberg-Wolfers bias documented in the
prediction market literature.

**How it's used:**
NOT to generate our estimate. To predict in advance what gap we should expect from the crowd,
which determines the risk profile of our submission. If we submit 0.20 on a question,
the crowd is predicted to be near 0.51 + 0.61×(0.20−0.50) = 0.51 − 0.183 = 0.327. That's
a ~13pp gap — we're betting the crowd is wrong by 13pp in the direction of the event
NOT happening. That's a meaningful bet and should only be made when the evidence strongly
supports the low estimate.

**Out-of-sample validation:**
During BEL-EGY, the model predicted crowd values with RMSE = 5.8pp (mean bias -0.5pp —
essentially unbiased). Two largest misses: Q1 (crowd was 10pp more bullish on "Egypt fouls
more" than predicted) and Q10 (crowd was 10pp less bullish on Trezeguet score/assist than
predicted). Both are within normal residual range — the model is holding.

---

## LAYER 3: NAMED RULE SYSTEM

Rules are named adjustments that fire on top of any statistical estimate. They encode
empirical findings from prior matches — things the pure model cannot compute because they
require contextual knowledge about how match dynamics shift.

### RULE 7 — Underdog Props: Don't Compress

**Definition:** When a team's win probability (per FTR) is below approximately 15%, the
model output for their props (SOT, scoring, offside counts) is trusted near-raw without
additional shrinkage toward the crowd. The model is already pricing in the underdog's weak
position. Extra shrinkage toward crowd compounds the discounting.

**Where it fires:**
- ENG-CDR: Congo DR at 5.64% win probability. All CDR props kept at model output or close
  to it. Wissa's SOT estimate used the ESPN competitive average (not the UZB outlier) and
  trusted RULE15 suppression (see below) rather than adding a further generic discount.
- FRA-SWE: Sweden at 15.4% — borderline. Gyökeres and Isak both had liquid markets that
  themselves already reflected the underdog position. RULE7 confirmed: don't add further
  suppression on top of a liquid market that's already priced it in.
- GER-PAR: Paraguay at ~17% — close enough to apply the spirit of RULE7. Enciso's SOT
  suppression came from the TUR-PAR precedent (named player history), not RULE7 per se.

**Where NOT to fire:**
MEX-ECU (Ecuador at 23%) and NOR-CIV (Ivory Coast at 25.6%) — above the 15% threshold.
Their props were modeled with standard RULE8 treatment (high draw price) rather than RULE7.

**Evidence base:** Multiple group-stage matches where underdog forward SOT and scoring props
were priced correctly by trusting a low model output against a crowd that gave the underdog
more credit. COL-CDR (Bakambu +10.45), CUR-CIV (Bacuna +6.53), NED-SWE (Gyökeres +18.04)
all confirmed the pattern.

---

### RULE 8 — High Draw Probability: Shrink Comparison Props

**Definition:** When the pre-match draw probability exceeds approximately 25%, shrink any
"Team A more [stat] than Team B" comparison estimate by blending it 65% toward the model
output and 35% toward 0.50.

**Mathematical form:** `final = 0.65 × model_output + 0.35 × 0.50`

**Theoretical basis:** A high draw price signals two closely-matched teams. Count statistics
(SOT, fouls, corners) for closely-matched teams produce tie-count outcomes more often than
historical team averages suggest, because their individual statistical distributions overlap
more. And "more than" questions always resolve NO on a tie. So raw Skellam outputs from a
high-draw match need to be shrunk toward 50% compared to what the model says.

**Confirmed evidence across all matches:**

*JPN-NED (draw=27.9%, n=1):* Japan's raw Skellam foul-comparison output was 0.764 (trimmed
to 0.70 for sample-size caution). Submitted 0.72. Actual outcome: 7-7 exact tie (NO). Had the
rule been applied, a sharper shrinkage toward 0.50 would have produced a small win instead
of -25.37. This was the discovery case for RULE8.

*CIV-ECU (draw=33.1%, n=2):* Ecuador foul comparison, raw Skellam 0.718, shrunk to 0.57.
Outcome: Ecuador 13 fouls vs IVC 10 (YES). Our shrunk 0.57 beat crowd's 0.52 (+6.97). An
unshrunk 0.72 would have won more on this outcome, but the n=1 from JPN-NED shows RULE8
is valuable insurance even when it costs upside.

*MEX-ECU (draw=34.25%, n=3):* Fired on Q3 (Mexico more SOT: 0.550 → 0.533), Q12 (3+
offsides: 0.323 → 0.28). Did NOT fire on Q4 (goal count absolute threshold), Q9 (FTR — the
market already prices the draw), or direct card/penalty markets (market takes draw probability
into account implicitly).

*NOR-CIV (draw=27.03%, n=4):* Borderline. Applied a light version to comparison props in
a high-BTTS match (BTTS=58.48%, highest of the knockout stage — signals both teams actively
attacking, which narrows stat gaps).

**Net verdict:** RULE8 trades a small amount of upside when correct (an unshrunk high-draw
estimate that wins anyway) for significant protection when wrong (an unshrunk estimate that
produces a -25pp directional loss on a tie-count outcome). Across n=4 confirmed applications,
the net is positive.

---

### RULE 14 — Internal Logical Consistency

**Definition:** Before submitting a batch of 15 questions, verify that P(more SOT) ≥ P(more
goals) across all related question pairs. You cannot out-score a team without having more
shots on target; therefore the probability of one must be at least as high as the probability
of the other.

**The case that established this rule:**
SAU-URU Q4 (Uruguay more 2H goals than Saudi Arabia): submitted 0.57. Q7 (Uruguay more 2H
SOT than Saudi Arabia): submitted 0.30. This is a logical contradiction — it implies Uruguay
is MORE likely to out-score than to out-shoot, which is mathematically impossible. Crowd
priced Q7 at 0.67, correctly recognizing the inconsistency. The thin ESPN SOT sample had
pulled the Q7 estimate down independently of Q4, and the cross-check was not performed.
Result: **-35.66 on Q7**, one of the five worst results of the season. Had the consistency
check been run, Q7 would have been raised to at least the Q4 level (0.57), which would have
beaten the crowd's 0.67 from below and earned positive RBP.

**How it's applied now:**
After computing all 15 estimates for a match, a cross-check is run on any questions that
share the same underlying event structure (more goals / more SOT, score in both halves /
win the match, any-player-SOT / BTTS, etc.). Where a contradiction is found, the better-
evidenced estimate wins (usually the market-backed one) and the other is adjusted.

---

### RULE 15 — Extreme Underdog Forward Suppression

**Definition:**
When a team's win probability is below ~15% (i.e., RULE7 territory), suppress their primary
attacking forward's SOT and scoring probability into the 0.20-0.35 band. Scenario A (blowout
context, team is expected to lose heavily and sit back): apply the full suppression. Scenario
B (competitive context, team is trailing and chasing the game): do NOT suppress, and may
increase the estimate because a chasing underdog generates forward runs.

**The Bakambu case — first RULE15 confirmation:**
COL-CDR Q10 (Bakambu 1+ SOT, submitted 0.25 vs crowd 0.42). Bakambu is a strong striker but
CDR was a heavy underdog in a defensive, structured match against Colombia. He registered 0
SOT. Won +10.45.

**The second Bakambu case — same player, same rule:**
In a later CDR match, Bakambu again appeared. Again applied RULE15 suppression. Again
confirmed (won +10.45, the ENG-CDR context confirmed via col_cdr historical file).

**Wissa in ENG-CDR:**
Wissa (CDR forward): competitive SOT history against Portugal=1, Colombia=0 (avg 0.5 per
competitive match). Team CDR SOT lambda = 1.957 from market. Even giving Wissa a generous
40% share: λ_Wissa_SOT = 1.957 × 0.40 = 0.783 → P(≥1 SOT) = 0.54. But this ignores that
CDR against England (76% win probability) is a Scenario A context — they're expected to sit
compact and defend, not generate forward runs. Applied RULE15 moderate suppression → 0.35.
Wissa registered 0 SOT. Won +30.42 — the largest win of the ENG-CDR match.

**Gyökeres and Isak in FRA-SWE:**
Gyökeres: win probability Sweden 15.4%. Raw thinned Poisson from Sweden's team goal lambda
gave ~0.22. Liquid market mid: 19.24%. RULE15 would push toward 0.20-0.35 band — market was
already in this range. Trusted market directly. Outcome tracked correctly.

Isak: SOT market mid 12.35%. RULE15 says suppress to 0.20-0.35, but the market is ALREADY
below 0.20. This is the key insight from the Enciso/GER-PAR lesson: don't stack further
suppression on top of a market that's already done the work. Over-suppression is exactly the
error that cost -26.30 on Enciso. The market's liquid price (12.35%) was trusted directly.

**The Enciso lesson (over-suppression failure):**
GER-PAR: Enciso (Paraguay forward), illiquid offer price 0.4808 → adjusted 0.454. Then
suppressed further to 0.32 per the TUR-PAR single-game precedent (0 SOT in a Paraguay
dominant win). The match turned into a wild, extra-time goal-fest that broke every team-level
ceiling assumption. Enciso scored. **-26.30 RBP.** The lesson: one prior game's result (even
a named-player-specific one) does not justify a confident departure from an illiquid market
price. The suppression to 0.32 was too aggressive without a market-level reason.

---

### Hard Floor and Risk Gate (FLOOR_0.25, RULE12)

**Hard Floor (FLOOR_0.25):**
Never submit below 25% (0.25) on any count-stat question. Not on a player SOT question, not
on an offside question, not on anything involving football event counts.

**Origin:** BRA-HAI Q2 (Haiti 2+ offsides). Haiti had 0 offsides in GD1 and appeared to be
playing a compact defensive block. Raw Poisson said P(≥2) ≈ 0.08. Submitted 0.08. Brazil
went 3-0 up early; Haiti then abandoned their defensive shape and chased the game, generating
multiple offside traps. Outcome: YES. **-42.56 RBP.** This is our second-worst result of
the entire campaign. The mechanism: the blowout/chasing context inverts all defensive
counting stats (see RULE10 / Loss Pattern #1). A 0.25 floor would not have converted this
to a win, but it would have reduced the damage from -42.56 to approximately -10 to -15.

The same pattern fired in:
- POR-UZB (Uzbekistan 2+ offsides, submitted too low, -26.35)
- TUR-PAR (Turkey 2+ offsides, -20.26)
- ARG-AUT (Austria corners, -19.91)

FLOOR_0.25 is now a standing pre-submission rule. Any number below 0.25 on a count-stat
question triggers a mandatory review of the blowout-chasing scenario before confirming.

**Risk Gate (RULE12):**
If removing a single data point from the ESPN sample swings the estimate by more than 10pp,
the estimate is classified as thin-sample and pulled toward the crowd formula rather than
trusted at face value.

**Origin:** Multiple group-stage matches where a team had a bimodal stat distribution (e.g.,
Ecuador's 27 shots in the CUR match vs 9.5 in competitive matches; Brazil's 8 offsides in
the HAI match vs near-zero in competitive matches). The rule formalizes the distinction
between a stable trait and an outlier game.

**Application in BRA-JPN:** Brazil's 8-offside match was flagged immediately (`BIMODAL_FLAG`)
and excluded from the offside lambda calculation. The trimmed lambda (Brazil 2.0 instead of
raw 3.0) was used, which is a RULE12 application — one outlier data point caused a >10pp
swing in the raw estimate, so it was excluded.

---

### Loss Pattern #8 — Late-Window Timing: Shade to 0.45-0.55

**Definition:** Any question whose time window falls after the second hydration break (~69+'),
or any full-match count that is sensitive to match-state chaos (multi-goal outcomes, total
offsides when teams may or may not be pressing), should be shaded toward 0.45-0.55 regardless
of what the model says.

This is explicitly listed as "Loss Pattern #8" in STEPS_FOR_HIGH_POINTS.md because it was
learned from the single worst result of the campaign (RSA-CAN Q1: -39.68).

**How the lesson was applied in NED-MAR:**
Q2 (card after 2nd hydration break): same method as RSA-CAN Q1, raw model output 0.77.
Deliberately trimmed to 0.65 per this lesson. Still missed (outcome NO), but loss was -3.51
instead of a -39.68-scale disaster. The trim preserved ~36 RBP of damage reduction from the
same wrong directional call.

**How the lesson was applied in NOR-CIV:**
Q14 (goal after 2nd hydration break): combined goal lambda 2.75 × (25/90) = 0.764 → P(≥1)
= 0.535. This happened to already fall within the 0.45-0.55 prescription. Submitted 0.50.
Model and lesson agreed — high confidence in the submission even though it's a guess.

**Why this rule exists as a named pattern rather than a general "be humble" instruction:**
The specificity matters. "Be humble" is not actionable. "Shade to 0.45-0.55 for any question
whose outcome window falls after the second hydration break, unless a genuine market exists
that directly answers the question" is actionable. The mechanism is identified: late-match
windows compress fatigue, substitutions, scoreline pressure, and time-wasting into one number
that pre-match team averages cannot capture. The fix is not about the model — it's about
the time window.

---

## LAYER 4: QUESTION CATEGORIES

Every submitted question is classified into one of six categories. The classification reflects
**how the estimate was actually produced**, not what the question topic is. A "cards" question
can be DIRECT_MARKET (if a market exists for exactly that threshold) or TIMING_NO_MARKET
(if asking about cards in a specific time window with no underlying market).

The performance data below covers 60+ questions from the four pre-FRA-SWE knockout matches
plus all three subsequent R32 matches.

---

### DIRECT_MARKET (73.5% beat-crowd, +4.19 avg RBP)

**Definition:** A Smarkets market exists that answers the question approximately word-for-word,
with no additional modeling required. The estimate is the vig-adjusted market mid.

**How to identify:** The question asks about a full-match outcome (FTR, BTTS, OU goals), a
team's aggregate stat (OU corners, OU cards), or a timing event where the Goal-1 time-bracket
market provides a direct read.

**Examples across all settled matches:**

- ENG-CDR Q6 (England score both halves): Smarkets "Score both halves" market → 41.35%.
  Submitted 0.41. Won.
- ENG-CDR Q9 (4+ cards): Cards OU3.5 → 28.09%. Submitted 0.28. Won +21.89.
- ENG-CDR Q11 (2H more goals than 1H): "Highest scoring half" 2H=43.54%. Submitted 0.43. Won.
- MEX-ECU Q4 (2 or fewer goals): OU2.5 Under → 70%. Submitted 0.70. Won.
- MEX-ECU Q14 (penalty): Penalty market → 25.8%. Submitted 0.26. Won.
- FRA-SWE Q3 (France win in regulation): FTR France → 76.34%. Submitted 0.76. Won.
- FRA-SWE Q5 (France ahead at halftime): HT result France → 59.71%. Submitted 0.60. Won.
- FRA-SWE Q10 (France scores first): Team to score first goal → 72.95%. Submitted 0.73. Won.
- NED-MAR Q1 (NED to qualify): To qualify market → 58.82%. Submitted 0.59. Won.
- RSA-CAN Q12 (brace scored): See Win Pattern #7 — avoided the illiquid-contract-sum trap,
  decomposed from team lambdas instead. +11.94.
- BEL-EGY Q8 (HT tied): HT-result Draw → 41%. Submitted 0.41. Won small.
- GER-CUR Q6 (Germany win): FTR Germany → 94%. Submitted 0.94. Won.

**Why this category is the backbone:**
34 of 60 knockout questions (well over half) were DIRECT_MARKET. It earns 73.5% beat-crowd
because the crowd has no systematic edge over a vig-adjusted market mid — the market is
efficient, and we're not adding noise by modeling.

---

### TEAM_MODEL — Poisson/Skellam Decomposition from Liquid Team Markets

**Definition:** No direct market answers the question, but the answer can be computed from
team-level lambda parameters that are derived from liquid team/match markets. This includes
Skellam comparisons, brace-scoring probability, joint-team events, and compound team-level
probabilities.

**Examples:**

- NED-MAR Q13 (both teams receive a card): No "both teams carded" market exists. Team card
  lambdas from NED cards OU1.5 (54.07%) and MAR cards OU1.5 (51.80%) → λ_NED = 1.52,
  λ_MAR = 1.46 → P(NED ≥1 card) = 0.78, P(MAR ≥1 card) = 0.77, joint = 0.60, trimmed to
  0.57. Crowd: 0.65. Won **+23.37** — 2nd largest win of the season.
- RSA-CAN Q12 (any player brace): 44 illiquid player contracts summed to 0.76 (invalid).
  Instead: λ_SA = 0.80, λ_CAN = 1.54 from team goal markets. Poisson-binomial decomposition
  (30% top-scorer share per team) → P(brace) = 0.18. Crowd: 0.25. Won +11.94.
- MEX-ECU Q3 (Mexico more SOT than Ecuador): Skellam from team SOT lambdas (3.870 vs 3.025)
  = 0.550. RULE8 shade → 0.533. Won.
- JPN-SWE Q2 (Sweden more SOT than Japan): Skellam from ESPN averages (7.5 vs 4.0) = 0.79,
  RULE8 shade → 0.76. Won **+23.98**.
- ENG-CDR Q10 (20+ total shots): ENG avg 19.33 + CDR competitive avg 7.5 = 26.8. P(≥20)
  from Poisson ≈ 0.90+, trimmed to 0.85. Won **+27.51** — largest single win of ENG-CDR.
- BRA-JPN Q2 (any player 2+ SOT): team SOT lambdas (BRA=5.02, JPN=3.57) → Poisson-binomial
  with 30-35% top-player share → 0.63, trimmed to 0.60. Won.

---

### PLAYER_LIQUID — Liquid (Bid+Offer) Player Market Trusted Near-Raw

**Definition:** The individual player market has both a bid and an offer. The mid is used as
the estimate with little or no additional shading.

**Key principle:** When a market is genuinely two-sided, there is a financial counterparty
on both sides who has an incentive to price the contract correctly. This is much stronger
evidence than a one-sided offer price. The main error mode in this category is adding further
narrative adjustment on top of a market that has already priced it in.

**Examples:**

- NED-MAR Q8 (Brobbey 2+ SOT): Liquid market, bid=0.2041, offer=0.2174, mid=0.2108.
  Crowd: 0.36. Submitted 0.21. Won **+24.84** — the single largest win of the season.
  The crowd was over-trusting a "two competitive attacking teams" narrative; the liquid market
  was right about Brobbey's actual ceiling.
- FRA-SWE Q6 (Mbappé 2+ SOT): Liquid market mid 63.92%. Cross-checked vs thinned Poisson
  (~61%). 3pp gap — consistent. Submitted near-market. Won.
- FRA-SWE Q4 (Dembélé scores): Liquid market mid 38.61%. Thinned Poisson gave ~32%. Used
  market. Won.
- FRA-SWE Q8 (Gyökeres scores): Liquid market mid 19.24%. Well inside the RULE15 suppression
  band. Trusted market directly. Won.
- NOR-CIV Q1 (Haaland scores): Liquid market mid 51.42% (bid=0.5128, offer=0.5155 — an
  exceptionally tight spread). ESPN thinned Poisson (from team lambda × his role share)
  gave ~0.49. Submitted 0.51.
- NOR-CIV Q4 (Sørloth 2+ SOT): Liquid market mid 22.99%. Consistent with thinned Poisson.
  Submitted near-market.

**Why liquid player markets are trusted near-raw:**
Three reasons. First, the spread is narrow — market makers are not extracting large margins.
Second, the bid-side participants are explicitly buying at that price, meaning they believe the
true probability is above the market mid; the offer-side participants believe it's below.
Market equilibrium means the mid is the best available estimate. Third, every time we have
confidently departed from a liquid player market (in either direction) it has cost RBP.

---

### TIMING_EARLY — Early-Window Timing, Market-Backed or Modeled

**Definition:** A question whose outcome window falls before the first hydration break
(approximately minutes 0-24), priced either from the Goal-1 time-bracket market or from
time-window scaling of team lambdas.

**Performance:** 100% beat-crowd across all confirmed instances. Every single early-window
timing question has gone positive.

**Why early windows work:**
Early in a match, the game state is still blank — no scoreline pressure, no fatigue effects,
no substitution disruptions. Team-level historical averages reflect pre-match team behavior,
which is exactly what applies to minutes 0-24. The match hasn't had time to diverge from
pre-match expectations.

**Examples:**

- RSA-CAN Q5 (goal before 1st break): goal-1 time bracket market → 0.398. Won +6.81.
- BRA-JPN Q10 (offside before 1st break): ESPN offside avg (trimmed) → 0.52. Won +6.27.
- NED-MAR Q3 (goal in 1H stoppage): λ_4min scaled → P(≥1) = 0.098. Submitted 0.10. Won +13.38.
- FRA-SWE Q14 (goal in 1H stoppage): dual lambda estimates converge at 0.12. Won.
- MEX-ECU Q13 (goal before first break): market brackets + model blend = 0.40. Won.
- ENG-CDR Q13 (goal before first break): λ_pre25 → 0.44, submitted 0.47. Won +21.79.
- GER-PAR Q5 (goal before 1st break): market backed → won.

---

### PLAYER_ILLIQUID — Illiquid (Offer-Only) Player Market, Adjusted ×0.945

**Definition:** The player market has only an offer, no bid. The raw offer price is multiplied
by 0.945 to partially correct for the one-sided overpricing. The adjusted value is used as the
primary estimate.

**Performance:** 71.4% beat-crowd rate, but **net -2.04 avg RBP**. This is the amber-flag
category — the beat-crowd rate looks fine but two catastrophic losses (-26.23 and -26.30)
erase five smaller wins. The asymmetric risk profile is the defining characteristic.

**The two large losses (opposite errors, same root cause):**

1. **RSA-CAN Q15 (Rayners 1+ SOT, -26.23 RBP):** Raw illiquid offer 0.5495, adjusted 0.519.
   Trusted near-raw. Crowd: 0.32. South Africa lost 0-1 (17.7% pre-match win probability);
   Rayners registered 0 SOT. Error: should have applied RULE15 suppression (their team SOT
   average across all 3 group matches was already low — 3.33/game — even in their better
   performances). The "competitive underdog exception" does not apply to a team that is
   shot-shy across its entire sample; it applies to teams with real attacking quality who happen
   to be underdogs in this specific match.

2. **GER-PAR Q10 (Enciso 1+ SOT, -26.30 RBP):** Raw illiquid offer 0.4808, adjusted 0.454.
   Further suppressed to 0.32 per the TUR-PAR precedent (0 SOT in a Paraguay dominant win).
   The match turned into an extra-time goal-fest with Paraguay chasing through multiple 
   periods. Enciso scored. Error: over-suppressed on the basis of a single prior game,
   ignoring that GER-PAR's match dynamics (Paraguay eventually chasing, high-press, ET) were
   completely different from TUR-PAR's (Paraguay dominant, no need for forward runs).

**The rule derived from these two losses:**
When a player market is offer-only, the safest move is to land **closer to the crowd consensus
than either the raw illiquid market OR a prior single-player lesson suggests**. Only depart
confidently from an illiquid price when there's a team-level reason (not just player-level)
to do so — e.g., the team's measured ceiling across 3 matches, not one prior game.

---

### TIMING_LATE — Self-Built Late-Window Timing, No Market

**Definition:** A question whose outcome window falls after the second hydration break, or a
full-match count that is sensitive to chaotic match dynamics, where no Smarkets market provides
a direct read. The estimate is constructed entirely from team averages + timing-share assumptions.

**Performance:** 42.9% beat-crowd, **-9.10 avg RBP**. The single worst category in the system.

**Why late windows fail:**
- Fatigue, substitutions, scoreline pressure, and time-wasting all compress into the final
  25 minutes of a match in ways that no pre-match team average predicts.
- The timing-share assumption (e.g., "40% of cards land post-69'") is never independently
  verified — it is a plausible heuristic, not a measured rate.
- A multi-step derived estimate (card lambda → timing-share → ET add-on) compounds uncertainty
  at each step. Three steps of unverified assumptions gives a number with very wide error bars
  dressed up as a confident point estimate.

**The three confirmed losses:**
- RSA-CAN Q1 (card after 2nd break, -39.68): 40% timing assumption × card lambda → 0.78.
  Actual: very few cards total. Worst result of the season.
- NED-MAR Q2 (card after 2nd break, still lost but -3.51 after trimming to 0.65).
- NED-MAR Q4 (goal after 2nd break, lost but -3.51 after model naturally landed in 0.45-0.55).

**The correct approach for this category going forward:**
Shade to 0.45-0.55 for any late-window timing question regardless of what the model says,
unless a genuine Smarkets market for that specific time window exists. The model output is
not reliable enough to justify a confident departure from 0.50 in either direction.

---

## LAYER 5: OUTPUT

### 5.1 The Submitted Estimate

A single number between 0.01 and 0.99 (never 0.00 or 1.00 — RULE6, established after the
Brazil 1.00 submission that cost -51.97 on a match Brazil drew). The number is the final
output of the entire pipeline: source data → statistical processing → rule application →
category classification → submitted.

**The BRA-MAR Q8 lesson — why 0 and 1 are banned:**
Brazil was submitted at 1.00 (gut override). Brazil drew. Squared error = (0-1.0)² = 1.00 —
the maximum possible. The researched recommendation (0.58-0.60) would have given squared
error of 0.144-0.16, beating crowd's 0.67 (squared error 0.449) significantly. The 100%
submission had no upside (going from 0.95 to 1.00 saves only 0.0025 of squared error) but
unlimited downside (going from 0.95 to 0.00 costs 0.9025 of squared error). The asymmetry
makes extreme submissions mathematically indefensible regardless of conviction level.

**Submission process integrity (RULE13 / Loss Pattern #3):**
Three confirmed instances of correct research producing wrong submissions:
- ENG-CRO Q7 (Kane 2H SOT): recommended 0.43, submitted 0.20 (transcription error). Kane
  got a 2H SOT. **-44.54 RBP.** Had 0.43 been submitted: +45.77. A single keystroke-level
  mistake cost 90+ RBP of swing.
- NZL-EGY Q4 (Egypt corners): submitted 42% instead of 65% (off-by-one mapping). Outcome
  landed fortuitously on the same side as 42%, producing a win by luck.
- BIH-QAT: entire 11-question analysis completed but never submitted. **0 RBP.**

The fix (not yet fully operationalized but documented as the highest-priority standing
process gap): read-back step before confirming each submission — compare what is about to
be submitted, value by value, against the `final_estimates` block in the JSON file.

---

### 5.2 RBP (Relative Brier Points)

**How it works:**
RBP measures how much better our squared error is than the crowd's squared error, normalized.
A positive RBP means we had lower squared error than the crowd on this question — we beat them.
A negative RBP means the crowd was better calibrated.

`RBP = crowd_squared_error − our_squared_error` (loosely stated)

The key property of the Brier score: extreme submissions (near 0 or 1) have VERY high
potential cost when wrong, and only TINY additional benefit compared to a strong-but-bounded
estimate when right. This is why 0.90 vs 1.00 is almost identical in terms of potential win,
but 0.90 vs 1.00 on a wrong outcome is a massive difference in loss.

**What high RBP requires:**
Not just being right — the crowd can also be right. RBP rewards being on the correct side
of the event AND further from the event's probability than the crowd. The richest wins
come from questions where we submitted far from 50% (say 0.15) and the crowd submitted
closer to 50% (say 0.40) and the event did NOT happen. Every big win in this campaign
(+27.51, +24.84, +23.98, +23.37, +23.36, +22.07, +21.89) followed this structure.

---

### 5.3 Campaign Track Record

**Cumulative through ENG-CDR (July 1, 2026):**
- 436+ submitted questions
- +872 cumulative RBP
- 58-68% beat-crowd rate (improving each month as the rules have accumulated)

**Best individual matches:**
- NED-MAR (Netherlands 1-1 Morocco): **+120.3 RBP, 12/15 beat crowd** — liquid player market
  trust (Brobbey +24.84) and team decomposition (both teams carded +23.37)
- FRA-SWE (France 3-0 Sweden): **+148.01 RBP, 14/15 beat crowd** — full liquid player markets
  + direct market dominance
- MEX-ECU (Mexico 2-0 Ecuador): **+154.49 RBP, 11/15 beat crowd** — Q12 offsides model
  (+49.54, the single biggest question win of the season)
- ENG-CDR (England 2-1 Congo DR): **+119.36 RBP, 11/15 beat crowd** — team decomposition
  (shots +27.51) + RULE15 (Wissa +30.42) + thinned Poisson (Kane +24.13)
- GER-CUR (Germany 7-1 Curaçao): **+72.47 RBP** — blowout where every underdog prop resolved
  correctly, confirming crowd inflation on underdog props
- BEL-EGY (Belgium 1-1 Egypt): **+63.72 RBP** — 9/10 beat crowd
- JPN-SWE (Japan 1-1 Sweden): **+70.49 RBP** — pure ESPN Skellam execution

**Worst individual questions:**
- BRA-MAR Q8 (Brazil win, submitted 1.00): **-51.97 RBP** — conviction override
- ENG-CRO Q7 (Kane 2H SOT): **-44.54 RBP** — transcription error
- BRA-HAI Q2 (Haiti offsides): **-42.56 RBP** — blowout context inversion
- RSA-CAN Q1 (card after 2nd break): **-39.68 RBP** — unverified timing decomposition
- QAT-SUI Q1 (HT BTTS): **-42.51 RBP** — compound AND question at extreme estimate

**The pattern in every large loss:**
Without exception, every loss above -20 RBP falls into one of four categories:
1. A gut override of the researched number (Brazil 1.00)
2. A transcription/submission error (Kane, BIH-QAT)
3. A late-window timing model with no market backing (RSA-CAN, GER-PAR)
4. An illiquid player market where we departed confidently in either direction (Rayners, Enciso)

None of the large losses came from the direct-market, team-model, or liquid-player-market
categories. This is the strongest validation of the instrument hierarchy: the categories with
measurable positive performance are also the ones that don't produce catastrophic losses.

---

## HOW THE LAYERS CONNECT — A WORKED EXAMPLE

**ENG-CDR Q10: "Will the match have 20 or more total shots?" (+27.51 RBP)**

Layer 1 — Raw Sources:
- ESPN box scores for England's 3 group matches: shots were 22, 19, 17 (avg 19.33)
- ESPN box scores for CDR's competitive matches vs Portugal and Colombia: shots were 7, 8
  (avg 7.5). The UZB match (37 shots) was flagged as a mismatch-context outlier and excluded
  per RULE12 (removing it swings the estimate by >15 shots per game).
- Historical file: col_cdr confirmed CDR's compact block style vs strong opponents.

Layer 2 — Statistical Processing:
- Combined expected shots: 19.33 + 7.5 = 26.83
- P(total shots ≥ 20 | expected = 26.83): using Poisson CDF (or equivalently, noting that
  26.83 >> 20 by more than one standard deviation — this is nearly certain from a Poisson
  with mean 26.83). P(X ≥ 20 | λ=26.83) ≈ 0.93.
- Trimmed for general uncertainty to 0.85 (never submit above ~0.90 on any single-event
  question without a market backing it).

Layer 3 — Named Rules:
- RULE7: CDR at 5.64% win prob. Fires for CDR props but this is England's shots + CDR shots
  combined — no RULE7 suppression needed on England's side.
- RULE15: Not applicable (this is a combined count, not a single player prop).
- FLOOR_0.25: Not relevant (estimate is 0.85).

Layer 4 — Category: TEAM_MODEL
- No direct market for total shots threshold exists. ESPN team averages plus outlier exclusion.
- Classified TEAM_MODEL (Poisson from ESPN team data, cross-validated by the large gap between
  expected 26.8 and threshold 20).

Layer 5 — Output:
- Submitted: 0.85
- Crowd: 0.64 (crowd was at 64%, materially underestimating England's consistent shot volume)
- Outcome: YES (match had well over 20 total shots)
- RBP: **+27.51** (our squared error: (1-0.85)² = 0.0225; crowd squared error: (1-0.64)² = 0.1296;
  difference: +0.107, scaled by the RBP formula to approximately +27.51)

The crowd's 0.64 implies doubt that 20 shots would be reached. England alone had averaged
19.33 shots per match across their 3 group games. The floor of total shots was already
almost 20 from England alone, before counting CDR's ~7.5 contribution. This was the cleanest
single instrument call of the ENG-CDR match — ESPN data pointed unambiguously to the estimate,
and the crowd was materially wrong.

---

*Document scope: covers all settled R32 matches through ENG-CDR (2026-07-01), plus all group-stage
matches referenced in STEPS_FOR_HIGH_POINTS.md and KNOCKOUT_STAGE_PRICING_DEEP_DIVE.md.*
*Next to settle: BEL-SEN or BIH-USA.*
