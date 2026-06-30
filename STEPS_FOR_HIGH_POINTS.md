# Steps for High Points (and Low Points) — Full Trail Analysis

**Scope:** Every settled question across the WC2026 SportsPredict campaign as of 2026-06-26 (53 matches, 423 actually-submitted questions, +812.15 cumulative RBP, 58.2% beat-crowd rate). Source: `datasets/questions_flat.csv` + the raw match JSON files in `data/external_markets/`. This file does not modify any raw data — it is a derived analysis built by reading the existing record.

On the leaderboard-cherry-picking theory: we have no visibility into other players' full question sets, only our own leaderboard rank per match, so we can't confirm or rule it out directly. What we *can* say: our own process answers every question we're given, every match, win or lose — there's no selective non-submission in our data except the one BIH-QAT process failure documented below (which cost us 0, not a strategic skip). If anything, the biggest lesson in this document is that our worst losses come from a small number of *specific, nameable* failure modes (gut overrides, submission errors, blowout-script misreads) rather than bad luck spread evenly — which is consistent with high scorers elsewhere also having identifiable strong patterns rather than ESP.

---

## PART 1 — STEPS FOR HIGH POINTS (what generates our biggest wins)

### Win Pattern #1: The "2+ offsides" family — defensive underdog correctly identified
**Best examples:** ENG-CRO Q2 Croatia (+15.73), BRA-MAR Q1 Brazil (+20.36), GHA-PAN Q2 Panama (+13.61), GER-CIV Q6 Ivory Coast (+18.70), PAR-AUS Q1 Australia (+20.13), GER-ECU Q7 Ecuador (+21.43)

**The steps:**
1. Pull ESPN per-match offside counts for the underdog/defensive team across their prior WC2026 matches.
2. Fit a simple Poisson with λ = their observed average (often 0.5–1.0 for a team that sits deep and doesn't run in behind).
3. Compute P(≥2) raw from Poisson — almost always lands 8–15%.
4. Submit at or near that raw number, with a floor around 0.10–0.15 for tail safety.
5. Crowd consistently prices these as near coin-flip (40–50%) because it doesn't weight "this team structurally doesn't make forward runs" — it anchors on the generic idea that any attacking team can get 2 offsides.

**Why it works:** this is the single most repeated, most validated rule in the whole campaign. It is a structural/tactical fact (deep-block teams don't get caught offside) that the crowd doesn't price in, not a statistical fluke.

**The critical caveat (see Loss Pattern #1 below): this rule INVERTS completely once the team is chasing a large deficit.**

---

### Win Pattern #2: ESPN-verified team-stat mismatches, submitted near-raw (WINNING TRAIL)
**Best examples:** JPN-SWE Q1 Sweden offsides (+21.58), JPN-SWE Q2 Japan 2H SOT (+23.98), TUR-USA Q2 Turkey offsides (+14.82)

**The steps:**
1. Pull both teams' full ESPN boxscores from every prior WC2026 match (fouls, SOT, offsides, corners, cards).
2. When one team's average on a stat is roughly double (or more) the opponent's across multiple matches — not one outlier game — trust the gap fully.
3. Run Poisson (single-stat questions) or Skellam (head-to-head comparison questions) off the raw averages.
4. Submit within ±5pp of the model output. No narrative shading, no "but maybe this time is different."
5. The crowd reliably treats comparison questions ("will X have more Y than Z") as near-50/50 even when the underlying data is lopsided — this is the single largest, most reliable source of edge in the whole project.

**Why it works:** Sweden's 7.5 vs Japan's 4.0 average SOT isn't noise — it's a real talent/tactical gap that holds match after match. The crowd defaults to a "anything can happen" prior on comparison questions; we instead trust a 2-game ESPN sample when it's consistent and directionally large.

---

### Win Pattern #3: "Winner-narrative inflation" — crowd over-credits volume stats to whoever wins
**Best examples:** ENG-GHA Q1 HT-BTTS-SOT (+35.50, the single biggest win in the dataset), GHA-PAN Q8 Ghana 3+ SOT (+25.69), NZL-EGY Q4 Egypt corners (+22.85), GER-CUR Q3 Curaçao fouls (+23.36)

**The steps:**
1. Identify a question where the crowd's intuition is "the team that's winning/dominant will also rack up the secondary volume stat" (more SOT, more corners, more fouls).
2. Check the underlying ESPN data for whether the dominant/winning team actually has a low-event, efficient profile (e.g., Ghana won 1-0 with just 2 total SOT; Curaçao, when comfortably losing, simply stopped fouling).
3. When the data shows "efficient win" or "disengaged loser" rather than "dominant volume," submit well below the crowd's number.

**Why it works:** the crowd's heuristic — "winning team = doing more of everything" — is wrong often enough to be a structural, repeatable edge. England-Ghana is the clearest case: Ghana had literally zero shots in the first half of their prior match, and the crowd still priced "both teams get a HT shot on target" at 61% out of a generic prior, not the specific evidence.

**Important symmetry warning:** the mirror-image question type (compound "AND" questions on rare events, see QAT-SUI Q1 below) is also our single biggest loss source — this question *family* is high-variance in both directions. Win Pattern #3 works because the data clearly supported the low estimate, not because compound/rare-event questions are free money.

---

### Win Pattern #4: Correctly discriminating WHEN a team is the attacking side
**Best example:** NOR-SEN Q1 Senegal 2+ offsides (+22.07) — submitted 78% YES (not the usual NO-family pick)

**The steps:**
1. Before defaulting to the "2+ offsides NO-family," check whether THIS team is actually the attacking/high-line side in THIS specific match, using GD1 evidence (e.g., a striker's individual offside history) and the opponent's defensive shape (high line vs deep block).
2. When the evidence says "this team will press forward and the opponent plays a high line," go the other way — high YES.

**Why it matters:** this is proof the rule-set isn't a blind "always bet NO on offsides" — it's a context-dependent read that the model gets right most of the time. The wins from Pattern #1 and the wins from Pattern #4 come from the SAME underlying skill: correctly classifying who is attacking and who is defending.

---

### Win Pattern #5: Sub-to-starter lineup upgrades
**Best example:** NZL-EGY Q9 Trezeguet score/assist (+32.04) — submitted 52% vs crowd's 28%

**The steps:**
1. Check GD1 lineups for players who were on the bench but are expected/confirmed to start GD2/GD3.
2. The crowd anchors heavily on the player's bench-role/limited-minutes stats from the prior match and underprices them once they're a starter.
3. Price using the team's overall goal/SOT rate apportioned to a starting role, not the player's substitute-minutes rate.

---

### Win Pattern #6: RULE15 (extreme-underdog forward suppression), applied correctly
**Best examples:** COL-CDR Q10 Bakambu SOT (+10.45, 2nd confirmation of this exact player), CUR-CIV Q9 Bacuna SOT (+6.53, 2nd confirmation), NED-SWE Q6 Gyökeres 2H SOT (+18.04)

**The steps:**
1. When a team is priced under ~15% to win, suppress their primary forward's SOT/scoring probability into a 0.20–0.35 band regardless of club-level rate.
2. This has now repeated across multiple different players and matches — it's graduated from "hypothesis" to "rule."

---

### Win Pattern #9: Trusting modeled/liquid-market decomposition over a crowd's narrative-driven inflation

**Example:** NED-MAR (Round of 32, 2026-06-30) — **+120.3 RBP, our best match of the entire season**, 12/15 beat crowd, final score Netherlands 1-1 Morocco

**The two biggest individual wins, same root mechanism:**
- Q8 "Brobbey 2+ SOT" (**+24.84**, biggest win of the match): a genuinely liquid two-sided market (bid 0.2041 / offer 0.2174, mid 0.2108) was trusted directly, while the crowd priced it at 0.36 — almost certainly over-trusting a "two strong, attacking teams" narrative around an evenly-matched fixture rather than the player's actual, market-measured output ceiling.
- Q13 "Both teams receive a card" (**+23.37**, 2nd-biggest win): team-level card lambdas backed out from each team's own O/U card market (NED≈1.52, MAR≈1.46) gave a properly-decomposed joint probability of 0.57-0.60, while the crowd priced it at 0.65 — again over-trusting a "two physical/competitive teams, of course both get carded" narrative instead of doing the actual per-team math.

**The lesson:** when a match is framed as "evenly matched and competitive" (as this one explicitly was, with FTR at 40/32/27), the crowd appears to systematically over-extrapolate that framing into EVERY individual prop within the match — assuming a competitive game means more of everything (more shots from both attackers, more cards from both teams) without doing the underlying per-component math. A genuinely liquid market price, or a careful team-level lambda decomposition, consistently catches this overreach. This is the single most reliable source of edge in a "coin-flip" knockout match: not the headline win-probability question, but the secondary props where the crowd lets the headline narrative bleed into everything.

**Secondary, smaller validation — Loss Pattern #8's correction worked:** Q2 (card after 2nd hydration break, the same self-constructed timing-decomposition method that produced our single worst result ever, -39.68 in RSA-CAN) was deliberately trimmed from a raw model output of 0.77 down to 0.65 specifically because of that prior loss. The result still missed (outcome NO), but the loss was only **-3.51** instead of a -30/-40-scale miss — direct evidence that applying explicit humility discounts to unverified derived models, even when the model's direction still ends up wrong, meaningfully shrinks the damage. Keep applying this discount going forward; it is now confirmed twice (once as the original failure, once as the successful correction).

---

## PART 2 — STEPS FOR LOW POINTS (what generates our biggest losses, and why)

### Loss Pattern #1: Blowout/chasing context INVERTS the offside, foul, and corner rules
**Best examples:** BRA-HAI Q2 Haiti 2+ offsides (**-42.56**, our 2nd-worst result of the whole campaign), POR-UZB Q1 Uzbekistan 2+ offsides (-26.35), TUR-PAR Q2 Turkey 2+ offsides (-20.26), ARG-AUT Q4 Austria more corners (-19.91)

**The steps that went wrong:**
1. We saw a team with a clean defensive/low-event history (0 offsides in GD1, etc.) and applied the standard NO-family discount.
2. We did not separately check the actual *scoreline context* of this specific match: a team chasing a 3-goal or 5-goal deficit abandons its compact shape in the second half and pushes players forward desperately — generating exactly the offsides/corners/fouls their "calm" GD1 history said they wouldn't.
3. Haiti (down 0-3), Uzbekistan (down 0-5), and Turkey (down 0-1, chasing) all did this. It is now a confirmed, repeated failure mode, not a one-off.

**The fix already written into the record:** *"Never go below 0.25 on any 2+ offsides question"* (from the POR-UZB postmortem) — a floor specifically to cap the downside when this pattern fires against us. This is the single most important standing rule correction in the dataset.

---

### Loss Pattern #2: Personal-conviction overrides beat the researched number — and lose
**Worst example of the entire campaign:** BRA-MAR Q8 "Will Brazil win the match?" — **-51.97 RBP**, our single worst result ever.

**What happened, in detail:**
- The researched number (RULE1: market 57.87% blended with predicted crowd inflation) recommended **0.58–0.60**.
- We submitted **1.00** — a gut override with zero researched basis.
- Brazil drew 1-1. Outcome = NO.
- Squared-error math: submitting 1.00 and being wrong costs the maximum possible penalty (squared error of exactly 1.0). Submitting the researched 0.60 would have given a squared error of 0.36 — which would have *beaten* the crowd's own (too-high) 0.67 estimate (squared error 0.4489).
- **The lesson, stated plainly: every single researched number available — the market, the crowd-adjusted estimate, even a crude average of the two — would have won this question. Only the 100% override lost it.** A 100% (or 0%) submission has no upside ceiling beyond what ~0.90–0.95 already captures, but it has unlimited downside the moment it's wrong.

**Standing rule going forward: never submit 0 or 1 (or anything outside roughly 0.05–0.95) on a match-outcome question, no matter how certain it feels. The math makes near-certainty just as profitable as certainty, with a fraction of the downside.**

---

### Loss Pattern #3: Pure submission/process errors (not modeling errors)
**Best examples:** ENG-CRO Q7 Kane 2H SOT (**-44.54**, 2nd-worst result ever), NZL-EGY Q4 Egypt corners (submission mapping error — happened to land on the right side, +22.85, "fortuitously"), BIH-QAT (entire match — 0 RBP earned, analysis never submitted at all)

**What happened:**
- ENG-CRO Q7: the model recommended **0.43** (from the Smarkets market). We *submitted 0.20* — a transcription/mapping error, not a researched disagreement. Kane did get a 2H SOT. Without the error, this question alone would have been **+45.77** instead of -44.54 — a swing of over 90 RBP from a single keystroke-level mistake.
- NZL-EGY Q4: a similar off-by-one submission error (submitted 42% instead of the intended 65%) happened to still beat the crowd because the outcome landed on the side the wrong number was closer to — pure luck masking a real process gap.
- BIH-QAT: the full 11-question analysis was completed (model_outputs, question_analysis, edge_ranking all present in the raw file) but **never submitted to the platform** before the deadline. Total RBP = 0 — not a loss in the leaderboard sense, but a complete waste of the research effort and a missed opportunity (several of the unsubmitted estimates, e.g. Qatar 2+ offsides at 0.25 vs crowd 0.43 vs actual YES, would have been strong wins).

**This is the most actionable category in the whole report, because it's not a modeling problem — it's a checklist problem.** Three separate incidents (Kane, the NZL-EGY corners mapping, and the BIH-QAT non-submission) all stem from the gap between "we computed the right number" and "the right number reached the platform." A final submission read-back step (compare what's about to be submitted, value-by-value, against the file's `final_estimates`/`question_analysis` block before confirming) would have prevented all three, worth a combined swing of well over 100 RBP.

---

### Loss Pattern #4: Compound ("AND") questions on rare events are high-variance in BOTH directions
**Worst example:** QAT-SUI Q1 "At halftime, will both teams have at least 1 shot on target?" — **-42.51 RBP** (our 3rd-worst result), final total for that match -39.21 (2nd-worst match overall)

**What happened:**
- This was genuinely well-researched: n=5 verified ESPN 1H-SOT samples for Qatar (values [0,0,0,0,2]), Poisson λ≈0.27, joint probability with Switzerland's 85% ≈ 0.20. Reliability was explicitly upgraded from "low" to "medium" because a larger sample converged with the original estimate.
- The outcome was YES anyway — at λ=0.27, P(≥1)=23.6% isn't actually that rare, and a compound AND-question multiplies two estimates together, which compounds variance, not just edge.
- Contrast this directly with **Win Pattern #3's #1 example, ENG-GHA Q1** — literally the same question type, same low-estimate structure, and it WON our biggest amount (+35.50) instead of losing.

**The lesson: this specific question family (compound HT/2H "both teams" SOT questions) is a genuine coin-flip-with-edge bet, not a sure thing, even when the underlying research is sound. Treat conviction on this family as capped — don't go below ~0.18-0.20 even when the math says lower, because the cost of being wrong on an extreme estimate is asymmetric (see Loss Pattern #2's squared-error math) and this family has now produced both our single biggest win AND one of our single biggest losses from nearly identical setups.**

---

### Loss Pattern #5: Internal logical-consistency violations (RULE14)
**Best example:** SAU-URU Q7 "Will Uruguay have more 2H SOT than Saudi Arabia?" — **-35.66 RBP** (4th-worst result)

**What happened:**
- The same match had Q4 ("Uruguay more 2H goals") submitted at **0.57**, but Q7 ("Uruguay more 2H SOT") was submitted at **0.30**.
- This is a logical impossibility: a team cannot be MORE likely to out-score their opponent in a half than to out-shoot them on target in that half (you need the SOT to get the goal). P(more goals) ≤ P(more SOT), always.
- The thin ESPN sample for Q7 pulled the estimate down independently of Q4, and nobody cross-checked the two related questions against each other before submitting.
- Crowd, by contrast, priced Q7 close to Q4's market-implied direction (0.67) and was right.

**The fix: before submitting a batch of questions for one match, run a consistency pass across logically related pairs (more-goals vs more-SOT, win vs more-2H-goals, etc.) and resolve any contradiction toward the better-evidenced side — usually the live market, not a thin ESPN sample.**

---

### Loss Pattern #6: Treating a small-sample "crisis" streak as a stable rate
**Best examples:** GER-ECU Q8 BTTS+3goals (-24.10), GER-ECU Q10 under-2.5 (-21.02), GER-ECU Q2 Ecuador fouls (-22.01) — three losses in one match, same root cause

**What happened:**
- Ecuador had scored 0 goals in 2 WC2026 matches despite 16 total shots on target — a genuine "finishing crisis," and we leaned hard into it continuing for a third match (must-win elimination game).
- 16 SOT, 0 goals is not a stable skill signal — it's an extreme outlier conversion rate that was always likely to regress. A must-win elimination match, with maximum motivation and nothing to lose, is precisely the highest-variance, highest-regression-to-mean moment — and that's exactly when Ecuador's finishing crisis broke (they scored twice and won 2-1).
- We should have shaded these numbers TOWARD the regression, not doubled down on the streak continuing.

**Companion loss in the same family:** ARG-AUT Q6/Q9 (Sabitzer, -31.86) and Q4 (Austria corners, -19.91) — both stemmed from treating Sabitzer's 0-SOT performance from GD1 (when Austria was the *dominant* team) as transferable evidence for GD3 (when Austria was the *desperate underdog chasing a deficit*) — a different role entirely, producing the opposite shot-attempt incentive.

**The fix: before reusing a player's or team's prior-match stat as a prior, check whether the situational role (dominant vs chasing, starter vs sub, defending a lead vs trailing) is actually the same. A 0-SOT or 0-goal streak earned in one tactical role does not transfer to a different tactical role.**

---

### Loss Pattern #7: Narrative-shading a real signal AWAY from raw, on a binary low-count threshold
**Example:** CPV-SAU Q4 "Will Cape Verde be caught offside 2 or more times?" — **-15.32 RBP**, final score 0-0

**What happened:**
- The raw Poisson off Cape Verde's own ESPN data (λ=1.5) gave 0.44. We then shaded it DOWN to 0.32 with a plausible-sounding narrative ("an even matchup against a non-high-press opponent should produce fewer high-risk transition forays than the Spain game did").
- Cape Verde sat on exactly 1 offside for nearly the whole match — the cagey-match read was directionally correct — then picked up a 2nd in stoppage time while pushing for a winner in a still-scoreless game that BOTH teams needed to win. Outcome flipped to YES.
- The crowd (0.47) ended up closer to the truth than our shaded number, and closer to our OWN raw, unshaded number (0.44) than our final submission was.
- **Direct same-match contrast:** Q1 in this match ("Cape Verde more fouls than Saudi Arabia") trusted a real discipline signal near-raw and won the single biggest RBP of the match (+17.76). Q4 took an equally real signal and talked itself down from it. Same match, same team, opposite outcomes — entirely explained by whether the data was trusted or second-guessed.

**The new sub-pattern this confirms:** on any low-count binary threshold question (2+ offsides, 4+ cards, etc.), late-match desperation specifically from a **mutual must-win stalemate** — two teams that both need a result, still scoreless deep into the game — elevates stoppage-time event risk. This sits alongside the established chasing-a-deficit inversion (Loss Pattern #1) as a second distinct trigger for the same kind of late-match risk-taking, but it fires even when nobody is actually behind on the scoreboard.

**The fix: when a context-based shade and a raw data-based number disagree, the burden of proof is on the shade, not the raw number — and it should never push the estimate by more than a few points without a specific, named mechanism (not just "this situation feels different"). Re-confirms WINNING TRAIL's "submit near-raw" rule from the win side; this is its loss-side mirror.**

---

### Win Pattern #7: Decomposing a market correctly instead of naively summing illiquid contracts

**Example:** RSA-CAN Q12 "Will any player score more than 1 goal?" — **+11.94 RBP**, final score South Africa 0-1 Canada (no brace)

**What happened:** Smarkets' literal "Player to score 2+ goals" market had 44 individual illiquid player contracts whose offer-side prices summed to 0.76 — a meaningless number, since illiquid offer-side overpricing compounds across many thin contracts rather than averaging out. Instead of using that sum, we backed out team-level goal lambdas from the liquid team O/U goal markets (South Africa ≈0.80, Canada ≈1.54) and ran a proper Poisson-binomial decomposition assuming a top-scorer goal-share per team, landing at 0.18 — well below both the trap number (0.76) and the crowd (0.25). Outcome: no brace, our 0.18 was the best-calibrated number on the board.

**The lesson: when a market is built from many individual illiquid contracts covering the same underlying event (any-player props, anytime-X markets), summing the raw offer prices is not valid probability arithmetic — decompose from the nearest liquid team/match-level market instead and model the player-level split explicitly.**

---

### Loss Pattern #8: Self-constructed timing-decomposition models, unverified by any market, carry far more risk than they look like they do

**Example:** RSA-CAN Q1 "Will a card be shown after the second hydration break, including any extra time?" — **-39.68 RBP** (worst result of the match), paired with Q14 "4+ total cards" — **-10.43 RBP**, both NO, final score South Africa 0-1 Canada

**What happened:**
- No market exists for "card after a specific minute," so we built one: fit a total-match card lambda (~4.0) from three card O/U thresholds, then assumed ~40% of all cards land in the final ~25 minutes of regulation (fatigue/time-wasting clustering) plus an extra-time card add-on, landing at 0.78 — a very high-confidence YES.
- Reality: total cards were apparently very low (likely 0-2 given Q14, "4+ cards," also missed NO at 0.57). The card O/U market's own implied lambda overstated the actual outcome, and our timing-share assumption (40% post-69') was never independently verified against anything — it was a plausible-sounding heuristic, not a measured rate.
- Both Q1 and Q14 failed in the same direction from the same root cause (overestimating total cards), which is worse than two independent misses — it means the foundational number (card lambda) was wrong, and the timing-decomposition built on top of it amplified rather than diluted that error.

**The lesson: a multi-step derived estimate (market lambda → assumed timing split → add-on for a secondary scenario) compounds uncertainty at every step. When none of those steps is independently market-verified, treat the final number with much more humility than its tidy derivation suggests — this is a textbook case for shading toward 0.5–0.6 rather than 0.78 on a question this structurally novel, until there's at least one settled precedent to calibrate the timing-share assumption against.**

---

### Loss Pattern #9: RULE15 (extreme-underdog forward suppression) needs to weight the team's own baseline shot/attacking output, not just match competitiveness

**Example:** RSA-CAN Q15 "Will Iqraam Rayners have at least 1 shot on target in regulation?" — **-26.23 RBP** (2nd-worst result of the match), South Africa lost 0-1 (17.7% pre-match win probability)

**What happened:** Trusted an illiquid offer-side player SOT price near-raw (0.5495 → adjusted 0.519) despite South Africa being an extreme underdog. The crowd (0.32) was far better calibrated; actual outcome was NO. This looks superficially like the ARG-AUT Sabitzer case (Win Pattern context: a competitive underdog's creative outlet should NOT be over-suppressed, since competitive/chasing context can mean MORE shots, not fewer) — but South Africa's situation was different in a way we missed: their own team SOT average across all 3 group matches was already low (3.33/game) even in their better performances, independent of any specific match's competitiveness. Sabitzer's Austria, by contrast, had real attacking quality and volume even as an underdog.

**The fix: before applying the "competitive underdog ≠ suppress" exception to a forward-suppression call, check the team's own baseline shot-output level first. A team that is shot-shy across its ENTIRE sample (not just one bad game) should still be discounted even in a competitive scoreline — the exception is for teams with real attacking quality who happen to be underdogs, not for any underdog in a non-blowout match.**

---

## Synthesis: the meta-pattern behind both lists

Every single Part-1 win comes from one move: **trust a specific, verified, multi-match data point over the crowd's generic prior, and submit it close to raw.** Every Part-2 loss comes from one of three failures: **(a) the data point itself didn't transfer because the match context changed (blowout/chasing/role-swap), (b) the number that reached the platform wasn't the number that was researched (override or transcription error), or (c) the bet was on an inherently high-variance compound/rare-event question where even good research has a real chance of landing wrong.**

The actionable takeaways, ranked by expected RBP recovered if fixed:
1. **Add a submission read-back step.** Loss Pattern #3 alone (Kane + BIH-QAT + the NZL-EGY near-miss) represents the single largest recoverable category — over 140 RBP of pure process loss, zero modeling disagreement involved.
2. **Hard floor of 0.25 on any "underdog 2+ offsides" question, and re-check the scoreline/chasing context before applying the NO-family at all.** Recovers an average of -20 to -40 RBP per incident, and this pattern has now fired 4+ times.
3. **Ban submissions outside ~0.05–0.95 on any single-outcome question.** Directly would have flipped BRA-MAR Q8 from -51.97 to a probable win.
4. **Run a logical-consistency check across related questions in the same match batch before submitting** (Loss Pattern #5).
5. **Discount "crisis streak" evidence when the situational role changes** (must-win elimination game, dominant→chasing role swap) (Loss Pattern #6).
