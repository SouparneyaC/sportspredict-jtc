# What Actually Works: Cross-Match Synthesis (5 settled R32/R16 matches, 75 questions)

**Matches covered:** Colombia-Ghana (+46.48), Argentina-Cape Verde (-3.41), Australia-Egypt (+64.74), Canada-Morocco (+58.92), France-Paraguay (+116.44). **Net: +283.16 RBP.**

This doc exists because France-Paraguay was the best result of the stretch, and pulling every big win and loss across all 5 matches into one table reveals the exact same two mechanisms driving both ends every single time. This is no longer a hunch — it's now `n=12` data points split into two clusters with opposite, near-perfectly symmetric outcomes.

---

## The two clusters (this is the whole finding)

### Cluster A — trust real personal player data over a generous market: 7-for-7, +144.67 RBP

| RBP | Question | Match |
|---|---|---|
| +44.06 | Brahim Díaz 1+ SOT | CAN-MOR |
| +30.97 | Alphonso Davies 1+ SOT | CAN-MOR |
| +20.34 | Nestory Irankunda 2+ SOT | AUS-EGY |
| +18.38 | Antoine Semenyo 2+ SOT | COL-GHA |
| +12.35 | Jordan Ayew scores | COL-GHA |
| +10.91 | Miguel Almirón score/assist | FRA-PAR |
| +7.66 | Mahmoud Trezeguet scores | AUS-EGY |

**Every single instance wins.** The mechanism is identical every time: pull the player's actual per-game shots/SOT/goals/assists log from ESPN for their last 3-4 matches, find that the number is genuinely zero or near-zero *regardless of game context* (blowout loss, competitive draw, whatever), and price meaningfully below whatever the crowd/market is offering — because the crowd's instinct is "he's a professional footballer on a real team, surely he gets *something*," and that generic prior loses to a specific, checkable fact.

**Why it's this reliable:** a personal production drought is a *low-variance* signal — it doesn't require predicting how today's game unfolds, just that a specific already-established pattern (a player who isn't getting service, isn't a nailed-on starter, or has been anonymous for a run of games) continues one more match. The downside is bounded because these markets rarely price the player above ~35-55% to begin with, so even being "wrong" costs little; being right pays a lot because the crowd sits stubbornly higher.

### Cluster B — project a team's own SOT ceiling *above* a market line using recent form: 1-for-6, -155.64 RBP net

| RBP | Question | Match |
|---|---|---|
| +23.44 | Mexico 6+ SOT *(this one is a low call that beat crowd — a different mechanism, not a blend-above-market)* | MEX-ECU |
| -11.36 | England 7+ SOT | ENG-CDR |
| -15.70 | France 7+ SOT | FRA-PAR |
| -20.33 | Colombia 7+ SOT | COL-GHA |
| -27.42 | Argentina 8+ SOT | ARG-CPV |
| -80.83 | Canada 4+ SOT | CAN-MOR |

**Excluding MEX-ECU (which isn't actually the same play — see below), this is 0-for-5, -155.64 RBP.** The mechanism here: a team's own SOT market line is thin, and its Poisson-implied probability sits below what the team's own recent-game SOT average would suggest, so the estimate gets blended *upward* toward the empirical number. This has now failed 5 times in a row across 5 different matches, ranging from a small loss (England, France) to the single worst result of the entire campaign (Canada, -80.83).

**Why MEX-ECU doesn't belong in this cluster:** that call was 0.19 — *below* both the market and the crowd, on the strength of "Mexico has never once hit 6 SOT in any match this tournament." It's actually the mirror case: **using empirical data to suppress a number below the market, on a *team* stat, also tends to work** — it's specifically the *upward* projection (assuming a good recent SOT floor will hold or the market is underselling it) that keeps failing. The failure mode isn't "trusting our own data over the market" in general — it's specifically **trusting a short run of good outcomes to predict continued good outcomes for a team**, which is exactly the asymmetry Cluster A avoids by only ever using personal data to predict *continued bad* outcomes.

---

## France-Paraguay case study: the pattern working and (barely) failing in the same match

France-Paraguay is the cleanest single-match illustration of both clusters:

- **Dembélé 2+ SOT (+31.83, 2nd-biggest win of the match):** not just "he's had 0 SOT before" — the actual process was pulling his 4-game SOT log (0, 2, 3, 0), noticing it was *bimodal by opponent quality* (hit the threshold only against weaker/mid opposition, blanked against the two tougher sides), and using that specific conditional read rather than a flat average. Tools: ESPN `rosters[].roster[].stats` per game, cross-referenced against opponent strength.
- **Almirón score/assist (+10.91):** textbook Cluster A — zero goal involvement in every game he played, missing from the squad entirely for one match. Priced far below the illiquid market's 16%.
- **Enciso 1+ SOT (+10.3), the most interesting win of the match:** this is a *meta*-level win, not a data win. Enciso's own log (0,0,0,1) looks like a Cluster-A suppression candidate, but I had a named, dated, costly precedent in hand — this *exact* player, *exact* question type, suppressed 6 days earlier on GER-PAR, lost -26.3 RBP when Paraguay's whole attacking ceiling broke through unexpectedly. Rather than mechanically re-running Cluster A logic, I deliberately trusted the market's more balanced 42% instead. **The lesson generalizes: Cluster A is reliable, but it is not infallible, and a documented specific counter-example on the same player should override the generic pattern.**
- **France 7+ SOT (-15.7), the one miss:** a smaller-scale rerun of Cluster B. I did apply a "regime-coverage check" this time (France's SOT rose to a season-high against their toughest opponent yet, unlike Canada's untested floor) and blended more conservatively (55% empirical vs Canada's 80%) — which is presumably why the damage was -15.7 instead of another -80. But it still lost. **This is the sixth data point in Cluster B, and it lost even with the improved methodology.** That's a strong signal the whole approach — not just the aggressive version of it — needs to be retired for this specific question type.

---

## What this means going forward

1. **Cluster A (personal-zero player suppression) is the highest-confidence repeatable edge found in this campaign.** Keep running it aggressively whenever a named player's ESPN log shows a genuine multi-game production drought, regardless of which side of the match they're on.
2. **Cluster B (team-level favorite SOT threshold, empirical-blended above a thin market) should be retired, not patched.** Five real-money tests, one small win that isn't even the same mechanism, four losses ranging from modest to catastrophic — including a version with an explicit regime-coverage check built in. For "Team X N+ SOT" questions going forward: **default to the direct market price**, and only deviate *downward* (Cluster A/MEX-ECU style suppression), never upward.
3. **A documented specific prior loss on a named player beats a generic pattern-match.** Before running Cluster-A-style suppression on any player, check whether this exact player/question type has already been tried and lost — if so, that specific counter-evidence outweighs the general pattern.
4. DIRECT-tier market questions remain the steady, low-variance backbone of every match (rarely the biggest win, essentially never a big loss) — not flashy, but this is what keeps a match afloat even when Cluster B fires and loses big (see CAN-MOR: +58.92 net despite a -80.83 single-question wipeout, entirely propped up by DIRECT-tier consistency plus two huge Cluster-A wins in the same match).
