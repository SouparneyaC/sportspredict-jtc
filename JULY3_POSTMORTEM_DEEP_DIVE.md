# July 3 Postmortem Deep-Dive — COL-GHA, ARG-CPV, AUS-EGY

**Matches:** Colombia 1-0 Ghana (+46.48 RBP), Argentina 3-2 Cape Verde *after ET* (-3.41 RBP), Australia 1-1 Egypt, Egypt win on... *(shown as Egypt WINNER, likely on penalties/aggregate — regulation was 1-1)* (+64.74 RBP).
**Net: +107.81 RBP across 45 questions.** A good day on aggregate, but it's carrying two catastrophic single-question losses and one systematic bias that shows up three times in three matches. This doc traces each number back to its instrument, then digs into the failure clusters.

---

## 1. Instrument-to-prediction pipeline (all 3 matches)

Every match followed the same pipeline, fully logged in `matches/{Match}/`:

1. **`01_espn_data.json`** — live-fetched ESPN box scores for both teams' 3 group games (shots, SOT, corners, cards, offsides, player-level stats via `rosters[].roster[].stats` and goal/sub timestamps via `keyEvents`).
2. **`02_smarkets_markets.json`** — live-fetched Smarkets odds (event-specific market list + contracts + quotes, `api.smarkets.com/v3`), cross-checked against ESPN's DraftKings pickcenter feed where available.
3. **`03_model_derivations.json`** — Poisson lambda fits (`scipy.optimize.brentq`) from Smarkets O/U lines, Elo cross-checks, rule-trigger flags (RULE7/8/15 etc.).
4. **`04_rules_applied.json`** — per-question tier (DIRECT / TEAM_MODEL / PLAYER_LIQUID / PLAYER_ILLIQUID / TIMING_WITH_MARKET / BASE_RATE_ONLY) and the specific reasoning + rule citations behind each number.
5. **`05_estimates.json`** — the final submitted numbers.

This structure is now confirmed to work well for the *direct* and *liquid-market* tiers (see §2). The failures below cluster almost entirely in **TEAM_MODEL** (Poisson-fit-from-thin-line) and **PLAYER_ILLIQUID** (offer-only, ×0.945) tiers — the two tiers where we substitute a derived number for a direct market read.

---

## 2. What worked (for contrast)

- **DIRECT tier** (FTR, BTTS, HT result, team-to-score-first, corners/cards lines that map 1:1 to a market): near-uniform wins. Examples: AUS-EGY Q3 (2-fewer goals, +14.46), Q15 (20+ shots, +29.46); COL-GHA Q11 (corners, +6.31); ARG-CPV Q12 (scores first, +5.15), Q14 (ahead at HT, +5.94).
- **Zero-production suppression on underdog players** (real ESPN data, not just RULE15 heuristics): Semenyo 2+ SOT (+18.38), Ayew scores (+12.35), Irankunda 2+ SOT (+20.34), Trezeguet scores (+7.66). All four were priced well below crowd on the strength of a genuine 0-in-3 (or near-zero) ESPN group-stage record, and all four correctly resolved NO. **This is the single most reliable edge source across all three matches.**

---

## 3. Failure cluster #1: the offside question is bleeding points, in both directions

This is the clearest, most actionable finding. Pulling every "3(+) or more offside calls" combined-total question from the last 5 knockout matches:

| Match | Our estimate | Crowd | Outcome | RBP | Our method |
|---|---|---|---|---|---|
| MEX-ECU (6/30) | 0.28 | 0.55 | NO | **+49.58** | Own-avg lambda=2.0, shaded down (Ecuador's consistent low record) |
| GER-PAR (6/29) | 0.30 | 0.53 | YES | **-48.68** | FLOOR_0.25 applied, anchored to Germany's 0-offside-in-3 record |
| ENG-CDR (7/1) | 0.55 | 0.56 | YES | **+3.13** | England's own 4-offside-vs-Panama precedent, priced near crowd |
| AUS-EGY (7/3) | 0.32 | 0.53 | YES | **-43.09** | Own-avg lambda=0.667 → raw Poisson 3%, pulled up to match-env lambda=2.0, still landed low |
| COL-GHA (7/3) | 0.75 | 0.59 | NO | **-36.94** | Own-avg lambda=7.0 (COL's 7-offside outlier game), shaded down to 0.75, still too high |

**Net across these 5: -75.99 RBP.** Two wins (+52.71 combined), three losses (-128.71 combined) — the losses are bigger than the wins. Outcomes: 3 YES / 2 NO (60% hit rate). **The crowd's number has landed in a tight 53-59% band all five times, regardless of which teams are playing or what their group-stage offside history looked like** — and that band is a better predictor (60% empirical hit rate ≈ crowd's implied probability) than any of our five team-history-driven models, which ranged wildly from 0.28 to 0.75 depending on whichever team's outlier game we happened to weight most.

**Diagnosis:** combined-match offside counts are dominated by referee strictness, match tempo, and defensive-line tactics on the day — factors our team-level historical-average approach cannot see, and which vary far more than either team's 3-game sample can reveal. We are effectively pattern-matching on noise (a single 7-offside game for Colombia, a single 0-for-3 record for Germany) and producing high-variance estimates around a question where the crowd has quietly converged on a stable, well-calibrated ~55%.

**Recommended rule:** for "N+ combined offside calls" questions specifically, anchor much closer to the crowd's historical band (0.50-0.59) by default, and only deviate materially (>10pp) when there is a *very* strong, multi-game, non-outlier signal on **both** teams pointing the same direction — not just one team's data. This should probably become a new named rule (`OFFSIDE_CROWD_ANCHOR`) given the sample size now available (5 questions, -76 net RBP is a real cost, not noise).

---

## 4. Failure cluster #2: underpricing the favorite's own team-SOT threshold

Four recent "Team X will have N+ shots on target" questions, all for the stronger team in a mismatch:

| Match | Question | Our est. | Crowd | Outcome | RBP | Note |
|---|---|---|---|---|---|---|
| MEX-ECU | Mexico 6+ SOT | 0.19 | 0.35 | NO | **+23.44** | Correct — Mexico's low SOT ceiling (never hit 6 all tournament) was real |
| ENG-CDR | England 7+ SOT | 0.40 | 0.47 | YES | **-11.36** | Underpriced — England's knockout intensity beat their Ghana-game baseline |
| COL-GHA | Colombia 7+ SOT | 0.30 | 0.40 | YES | **-20.33** | Underpriced — market-fit λ=5.44 was *below* Colombia's own group SOT avg (6.33) |
| ARG-CPV | Argentina 8+ SOT | 0.32 | 0.47 | YES | **-27.42** | Underpriced — same pattern, λ=6.42 fit vs. group avg 5.0 in a much easier matchup |

3 of 4 losses, and the common mechanical error is visible in the COL-GHA and ARG-CPV derivations: **the Poisson lambda fitted from a single thin Smarkets O/U line came in lower than the team's own recent empirical SOT average**, and we trusted the market-fitted number over the team's own data. In both cases the team was playing a *weaker* opponent than any team in their group stage, which should push the SOT expectation *up* from the group average, not down to match a thin market line.

**Recommended rule:** when fitting a team's own SOT/shots lambda from a market O/U line, **compare it against the team's own group-stage empirical average first**. If the market-fit lambda is below the empirical average *and* today's opponent is weaker (lower Elo/win-prob) than the team's toughest group opponent, blend upward toward (or past) the empirical average rather than defaulting to the market fit. The market line may simply be thin/stale for a team-specific SOT market — these are consistently among the least-liquid markets we pull (wide spreads noted in almost every match's `02_smarkets_markets.json`).

---

## 5. Failure cluster #3: illiquid "score or assist" markets for out-of-form favorite-side playmakers

Two closely related misses:

| Match | Player | Our est. | Crowd | Outcome | RBP | Real signal available |
|---|---|---|---|---|---|---|
| COL-GHA | James Rodríguez score/assist | 0.42 | 0.40 | NO | **~0** | 0G/0A in 3 group starts |
| ARG-CPV | Julián Álvarez score/assist | 0.58 | 0.39 | NO | **-29.25** | 0G/0A in 3 group games, benched 2 of 3 |

Both players had a **literal zero** goal-involvement record through the group stage. Both markets were illiquid, offer-only prices (James: offer 54% → adj. 51%; Álvarez: offer 69% → adj. 65%), and in both cases we applied only a modest RULE12 trim (to 0.42 and 0.58 respectively) rather than weighting the personal zero-production data as heavily as we did for the *underdog*-side players in §2.

**This is the key asymmetry to fix.** Compare the treatment:
- Semenyo (Ghana, underdog side): 0 SOT in 3 games → priced at **0.10**, a steep discount from the illiquid market's 0.135.
- Álvarez (Argentina, favorite side): 0G/0A in 3 games → priced at **0.58**, barely below the illiquid market's 0.65.

The underlying data was comparably damning in both cases (zero production, several benchings), but we discounted the underdog player far more aggressively than the favorite-side player. The implicit (wrong) reasoning was "Argentina/Colombia score a lot, so *someone* on their attack will likely register" — but that reasoning doesn't transfer to a *specific named player* who has been personally unproductive; it's a team-level fact being misapplied to a player-level question. **Recommended rule (`PERSONAL_ZERO_OVERRIDES_TEAM_CONTEXT`):** a player with 0 goals AND 0 assists across all 3 group starts should be discounted at least as aggressively regardless of which side of the match they're on — team scoring context should shift the estimate by a few points, not override a personal zero streak.

---

## 6. ARG-CPV special context: the Cape Verde near-miracle

Argentina won 3-2, but **the final was after extra time** — regulation (90+stoppage) ended level. This single fact explains most of that match's losses and is worth recording as its own case study:

- Q5 "Argentina win in regulation": priced **0.86** (FTR-direct, cross-validated against Elo and DraftKings) → outcome **NO**. Both independent pre-match signals (536-point Elo gap, 85.5% market) agreed and were both wrong about the *regulation-time* result specifically — the 85.5%/3.5% price was for the match overall being competitive, but the "who's ahead after 90+stoppage" outcome landed in the 10-15% tail both sources implied. This is a reminder that even well-cross-validated heavy-favorite prices still carry real tail risk on regulation-specific questions — not a modeling error, just the tail materializing.
- Q4 "Argentina clean sheet": 0.67 → NO (conceded 2). Same root cause.
- Q6 "Cape Verde 2+ SOT": priced **0.40**, deliberately shaded down from market's 0.51 via RULE15 (blowout suppression, anchored to their 1-SOT Spain-game precedent) → outcome **YES** (-14.32). In hindsight, Cape Verde were not in "blowout victim" mode at all — they were playing the game of their tournament. **RULE15's Scenario-A suppression assumes the underdog gets pinned back and demoralized; that assumption failed here.** Cape Verde's Spain-game precedent (1 SOT under 74% opponent possession) was the wrong analog — their Uruguay game (4 SOT in a 2-2 draw, their most competitive/committed performance) was the better analog for "Cape Verde when they're actually competing," and today they were clearly competing.

**Lesson:** RULE15 Scenario-A suppression should not be applied purely off a win-probability threshold (<10%) without also checking whether the underdog has a *recent competitive-performance* precedent (like Cape Verde's Uruguay game) as well as a *blowout-victim* precedent (like their Spain game). When both exist, don't default to the more suppressive one just because it's the "most analogous opponent quality" — flag the split and shade less aggressively.

---

## 7. Net takeaways / proposed rule changes

1. **New rule `OFFSIDE_CROWD_ANCHOR`**: for combined-total offside questions, anchor within ~10pp of the crowd's typical 50-59% band by default; require strong two-sided (not one-outlier-team) evidence to deviate further. Net cost of not having this rule so far: **-75.99 RBP across 5 questions.**
2. **Amend team-SOT lambda-fitting**: compare market-fit lambda to the team's own group-stage empirical average before finalizing; blend upward when market-fit < empirical average and today's opponent is weaker than the toughest group opponent. Net cost so far: **-35.67 RBP across 4 questions** (3 losses partially offset by 1 big win).
3. **New rule `PERSONAL_ZERO_OVERRIDES_TEAM_CONTEXT`**: a named player with 0G/0A across all 3 group starts gets the same steep discount whether they play for the favorite or the underdog. Net cost so far: **~-29 RBP concentrated in one question**, but the James Rodríguez near-miss shows it's a repeatable pattern, not a one-off.
4. **RULE15 refinement**: check for a competitive-performance precedent (not just a blowout-victim precedent) before applying full Scenario-A suppression to an underdog's attacking output.

Everything else in these three matches — DIRECT-tier markets, and suppression calls backed by genuine zero-production underdog data — continues to work as well as it has all campaign. The three failure clusters above account for essentially all of the value given back today (offsides: -76, favorite SOT: -36, illiquid score-or-assist: -29 ≈ -141 combined, against +107.81 net, meaning the *rest* of the 45 questions netted roughly +249 on their own).

---

## Addendum, 2026-07-04: CAN-MOR live-fired both new rules from this doc — one worked, one blew up (-80.94 RBP)

Canada vs Morocco (Canada lost 0-3) was the first live test of `TEAM_SOT_EMPIRICAL_FLOOR` and `PERSONAL_ZERO_OVERRIDES_TEAM_CONTEXT` above, plus the "de-shrink Tier-A signals" lever from `STRATEGIC_MARGIN_PUSH_RESEARCH.md`. Match went +59.27 net, masking one catastrophic result:

- **Q11 "Canada 4+ SOT" scored -80.94** (priced 0.80, crowd 46%, outcome NO) — by far the worst question of the match. Without it the match would have been **+140.23**, near season-best. This was the live test of `TEAM_SOT_EMPIRICAL_FLOOR`, and it failed.
- **Root cause:** Canada's "4-for-4, never below 4 SOT" floor came from a draw, a blowout *win*, a competitive loss, and a competitive win — it never included a blowout *loss*. Canada lost 0-3, a genuine rout, and a team run over that badly typically stops generating shots on target altogether — a regime the 4-game sample never covered. The market (crowd 46%, raw market-fit lambda implied 35.8%) was already pricing that risk; the empirical overlay ignored it.
- **The margin-push de-shrink made it materially worse.** The original blend (before de-shrinking) was 0.68; de-shrinking to 0.80 per the margin research cost an *additional* ~33.56 RBP on top of an already-too-high call (back-solved counterfactuals using Q11's own implied scale: 0.358 raw-market-only → +15.76; 0.68 original blend → -47.38; 0.80 as submitted → -80.94). Trusting the thin market at face value with **zero** empirical override would have *won* this question outright.
- **The other new rule worked great in the same match:** `PERSONAL_ZERO_OVERRIDES_TEAM_CONTEXT` produced the match's two biggest wins — Davies 1+ SOT (+31.06) and Brahim Díaz 1+ SOT (+44.07), both from trusting real personal zero-production data over a much more generous market.

**The asymmetry this reveals:** suppressing a probability based on real *negative* evidence (a player's zero-production streak) is low-risk — the downside if wrong is bounded and the signal doesn't need to anticipate a regime change. Projecting a probability *up* from a positive historical floor is high-risk, because a short run of good outcomes provides no protection against a regime (here, a blowout loss) it never happened to contain.

**Rule correction — `TEAM_SOT_EMPIRICAL_FLOOR` needs a regime-coverage check before use:** before trusting a team's "consistent floor" stat, verify the sample actually spans the range of game states plausible today — specifically, has this team's floor ever been tested while being blown out, not just while winning big or losing competitively? If the opponent is a strong enough favorite that a rout is plausible (Morocco was priced at 53.6%+ here) and the sample doesn't include a rout-loss game, do not trust the floor uncritically — weight the market more heavily, since the market likely already prices in blowout risk that a 3-4 game sample cannot capture.

**Margin-push research, first real-world check:** this is the first live test of the "de-shrink Tier-A signals" lever from `STRATEGIC_MARGIN_PUSH_RESEARCH.md` §8.2, and it lost money — specifically because the underlying signal wasn't genuinely Tier-A. A floor built from a regime-incomplete sample is not equivalent to a truly reliable direct-market read. The de-shrinking *principle* isn't necessarily wrong, but this instance shows the harder problem is correctly *classifying* a signal as Tier-A in the first place, not just deciding how hard to weight it once classified. Both rules need more validated instances before being trusted as standing policy.
