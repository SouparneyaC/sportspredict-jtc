# Player prop backtest: Álvarez 1+SOT (Q1) and Messi scores (Q4) — ENG vs ARG SF, 2026-07-15

Script: [`11_player_prop_backtest_messi_alvarez.py`](11_player_prop_backtest_messi_alvarez.py) (also writes
`11_player_prop_backtest_results.json`). Questions priced (exact wording from `01_match_and_markets.json`):

- **Q1**: "Will Julián Álvarez (Argentina, #9) have 1 or more shots on target in regulation (90 minutes + stoppage time)?"
- **Q4**: "Will Lionel Messi (Argentina, #10) score a goal (excluding own goals) in regulation (90 minutes + stoppage time)?"

## 0. Methodology precedent this follows

Two things in this repo were read first, per instructions, and shaped everything below:

1. **`topics/player-props/README.md`** documents the project's one *fitted* player-prop model
   (Ronaldo goals OLS regression, n=9): in-sample R²=0.431 but adjusted R²=0.090, and LOOCV MSE
   1.846 — **worse than just predicting the training-fold mean (1.156)**. The project's own
   RULE5 sets the bar at n≥10 before trusting a fitted model. Neither Messi nor Álvarez has
   anywhere near that much *own-2026-tournament* data (n=6 games each), so this exercise does not
   attempt a regression.
2. **`matches/Spain_vs_Belgium/PRICING_METHODOLOGY.md` §3.5 and Q9/Q10** is the validated approach
   actually used for this exact question type (De Bruyne/Lukaku 1+SOT props): a **k=5
   empirical-Bayes shrink** of the player's own in-tournament rate toward his historical StatsBomb
   rate — `pred = (n_2026*rate_2026 + k*rate_historical) / (n_2026 + k)`. Not a regression, no
   fitted coefficients, no tuning of `k`. That formula is reused here unchanged.

§3.5 also documents the ESPN field mistake to avoid: the `leaders` field only surfaces team-level
category leaders, not a full per-player boxscore. The correct location, used throughout below, is
`rosters[].stats`, a per-player array with `appearances`, `totalShots`, `shotsOnTarget`,
`totalGoals`, `goalAssists`.

## 1. Data sourcing

### 1.1 Historical (WC2018 + WC2022), `data/processed/statsbomb_player_match_panel.csv`

Filtered by exact `player_name` (never by row position/Q-number, per the project's standing join-safety rule).

**Lionel Andrés Messi Cuccittini** — n=11 (4 games WC2018, eliminated R16 by France; 7 games WC2022, won the tournament):

| Date | Competition | Opponent | Starter | Minutes | Shots | SOT | Goals | Assists |
|---|---|---|---|---|---|---|---|---|
| 2018-06-16 | WC2018 | Iceland | Y | 95.0 | 11 | 3 | 0 | 0 |
| 2018-06-21 | WC2018 | Croatia | Y | 94.1 | 1 | 0 | 0 | 0 |
| 2018-06-26 | WC2018 | Nigeria | Y | 94.5 | 2 | 1 | 1 | 0 |
| 2018-06-30 | WC2018 | France | Y | 95.0 | 4 | 1 | 0 | 1 |
| 2022-11-22 | WC2022 | Saudi Arabia | Y | 103.8 | 4 | 3 | 1 | 0 |
| 2022-11-26 | WC2022 | Mexico | Y | 96.5 | 2 | 1 | 1 | 1 |
| 2022-11-30 | WC2022 | Poland | Y | 96.0 | 7 | 4 | 0 | 0 |
| 2022-12-03 | WC2022 | Australia | Y | 97.4 | 6 | 2 | 1 | 0 |
| 2022-12-09 | WC2022 | Netherlands | Y | 167.5 | 6 | 2 | 1 | 1 |
| 2022-12-13 | WC2022 | Croatia | Y | 95.0 | 2 | 2 | 1 | 1 |
| 2022-12-18 | WC2022 | France | Y | 211.3 | 5 | 4 | 2 | 0 |

Scored in 7/11 = **0.6364** historical rate. 1+SOT in 10/11 games (not the target for Q4, kept for context).

**Julián Álvarez** — n=7 (WC2022 only; too young for the 2018 squad, not in the StatsBomb panel for that tournament):

| Date | Competition | Opponent | Starter | Minutes | Shots | SOT | Goals | Assists |
|---|---|---|---|---|---|---|---|---|
| 2022-11-22 | WC2022 | Saudi Arabia | N (sub) | 45.6 | 1 | 1 | 0 | 0 |
| 2022-11-26 | WC2022 | Mexico | N (sub) | 34.1 | 0 | 0 | 0 | 0 |
| 2022-11-30 | WC2022 | Poland | Y | 78.1 | 6 | 3 | 1 | 0 |
| 2022-12-03 | WC2022 | Australia | Y | 71.0 | 1 | 1 | 1 | 0 |
| 2022-12-09 | WC2022 | Netherlands | Y | 80.9 | 0 | 0 | 0 | 0 |
| 2022-12-13 | WC2022 | Croatia | Y | 73.8 | 2 | 2 | 2 | 0 |
| 2022-12-18 | WC2022 | France | Y | 101.8 | 1 | 1 | 0 | 0 |

1+SOT in 5/7 = **0.7143** historical rate.

### 1.2 This tournament (WC2026), raw ESPN dumps, `rosters[].stats`

All 6 of Argentina's 2026 matches pulled directly from `data/processed/espn_raw_events/espn_event_<id>.json`:
760433 (Algeria, group), 760456 (Austria, group), 760483 (Jordan, group), 760500 (Cape Verde, R32,
**AET**), 760509 (Egypt, R16), 760513 (Switzerland, QF, **AET**). Cross-checked against the
pre-existing `matches/Argentina_vs_CapeVerde/05_estimates.json` and
`matches/Argentina_vs_Switzerland/01_team_and_player_logs.json` (games 1–5 match exactly; game 6,
the Switzerland QF, is new — those files predate that match).

**Julián Álvarez, 2026 log:**

| Date | Opponent | Stage | Starter | Shots | SOT | Goals | Note |
|---|---|---|---|---|---|---|---|
| 2026-06-17 | Algeria | Group | N (sub) | 0 | 0 | 0 | |
| 2026-06-22 | Austria | Group | N (sub) | 1 | 1 | 0 | |
| 2026-06-28 | Jordan | Group | Y | 1 | 1 | 0 | |
| 2026-07-03 | Cape Verde | R32 (AET) | N (sub) | 1 | 0 | 0 | whole-match total, 0 is unambiguous regardless of period |
| 2026-07-07 | Egypt | R16 | Y | 2 | 1 | 0 | |
| 2026-07-12 | Switzerland | QF (AET) | Y | 3 | 1 | 1 (112′, ET) | whole-match SOT total; his only on-target shot may *be* the 112′ ET goal — regulation-only SOT is genuinely ambiguous (0 or 1); ESPN has no shot-level clock data, only goal-level, so this can't be resolved further |

Own-2026 1+SOT log: **[0, 1, 1, 0, 1, 1]**, raw rate 4/6 = 0.667.

**Lionel Messi, 2026 log:**

| Date | Opponent | Stage | Starter | Shots | SOT | Goals | Note |
|---|---|---|---|---|---|---|---|
| 2026-06-17 | Algeria | Group | Y | 6 | 4 | 3 | |
| 2026-06-22 | Austria | Group | Y | 7 | 4 | 2 | |
| 2026-06-28 | Jordan | Group | N (sub) | 2 | 1 | 1 | |
| 2026-07-03 | Cape Verde | R32 (AET) | Y | 9 | 6 | 1 | goal independently verified at 29′ via `keyEvents` clock — inside regulation (`End Regular Time` marker was 90′+9′) |
| 2026-07-07 | Egypt | R16 | Y | 5 | 2 | 1 (+1 assist) | goal at 83′, regulation, no ET in this match |
| 2026-07-12 | Switzerland | QF (AET) | Y | 4 | 1 | 0 (+1 assist) | 0 goals for the full match including ET, unambiguous — the 5-game scoring streak broke here |

Own-2026 scored-goal log: **[1, 1, 1, 1, 1, 0]**, raw rate 5/6 = 0.833.

**Data-quality caveat, stated plainly**: ESPN's `keyEvents` array has clock timestamps for goals
(used above to confirm the Cape Verde and Egypt goals fall inside regulation) but *not* for
individual shots. So the shots/SOT totals for the two matches that went to extra time (Cape Verde
R32, Switzerland QF) are whole-match totals and could include a small amount of extra-time shot
volume that the "regulation only" question wording doesn't count. This affects one cell only
(Álvarez's Switzerland-QF SOT=1) — flagged in the table above rather than silently treated as clean.

## 2. Walk-forward backtest — strictly no lookahead

Same k=5 empirical-Bayes formula as Q9/Q10 De Bruyne/Lukaku:

```
pred_i = (n_prior_2026 * rate_2026_prior + k * rate_historical) / (n_prior_2026 + k)
```

At fold *i* (Argentina's *i*-th WC2026 match, in date order), `rate_2026_prior` uses **only**
2026 games 1..i-1 — never game *i* or any later game. `rate_historical` is the fixed
pre-tournament StatsBomb rate, itself entirely prior in time to every 2026 fold. Fold 1 has zero
own-2026 data, so it collapses to the pure historical rate.

### 2.1 Álvarez — P(1+ SOT), walk-forward

| Fold | Opponent | n prior 2026 | Rate prior 2026 | **Prediction** | **Actual** | Squared error |
|---|---|---|---|---|---|---|
| 1 | Algeria | 0 | — | 0.7143 | 0 | 0.5102 |
| 2 | Austria | 1 | 0.000 | 0.5952 | 1 | 0.1639 |
| 3 | Jordan | 2 | 0.500 | 0.6531 | 1 | 0.1203 |
| 4 | Cape Verde | 3 | 0.667 | 0.6964 | 0 | 0.4850 |
| 5 | Egypt | 4 | 0.500 | 0.6190 | 1 | 0.1451 |
| 6 | Switzerland | 5 | 0.600 | 0.6571 | 1 | 0.1175 |

**Brier score (walk-forward EB model): 0.2570**
**Brier score (flat historical-only baseline, ignore 2026 entirely): 0.2245**
**Brier score (flat 0.5 baseline): 0.2500**

The walk-forward EB model is **worse** than simply always predicting the fixed historical rate
(0.257 vs 0.225), and barely distinguishable from a coin flip (0.250). Álvarez's 2026 SOT log
alternates (0,1,1,0,1,1) in a pattern the historical prior didn't anticipate, and shrinking toward
noisy short-run 2026 sub-rates at low `n_prior` actively hurt calibration in two of six folds
(folds 1 and 4, both misses on the "off" side).

### 2.2 Messi — P(scores), walk-forward

| Fold | Opponent | n prior 2026 | Rate prior 2026 | **Prediction** | **Actual** | Squared error |
|---|---|---|---|---|---|---|
| 1 | Algeria | 0 | — | 0.6364 | 1 | 0.1322 |
| 2 | Austria | 1 | 1.000 | 0.6970 | 1 | 0.0918 |
| 3 | Jordan | 2 | 1.000 | 0.7403 | 1 | 0.0675 |
| 4 | Cape Verde | 3 | 1.000 | 0.7727 | 1 | 0.0517 |
| 5 | Egypt | 4 | 1.000 | 0.7980 | 1 | 0.0408 |
| 6 | Switzerland | 5 | 1.000 | 0.8182 | 0 | 0.6694 |

**Brier score (walk-forward EB model): 0.1756**
**Brier score (flat historical-only baseline): 0.1777**
**Brier score (flat 0.5 baseline): 0.2500**

The walk-forward EB model edges out the flat historical baseline (0.1756 vs 0.1777) and clearly
beats a coin flip. But the margin over the historical-only baseline is trivial (0.002) and is
entirely an artifact of a 5-game hot streak that then broke exactly on fold 6 — the one fold
carrying almost all the Brier-score mass (0.669 of a 1.056 total). A model that had shrunk *harder*
toward the streak (i.e. `k` smaller than 5) would have scored worse on fold 6; a model with `k`
much larger would look close to the flat-historical baseline. This is not evidence the EB approach
is "validated" for Messi specifically — it's one streak-breaks-on-the-last-fold data point.

## 3. Honesty verdict on sample size

**n=6 own-tournament folds per player is thin, exactly the kind of sample this project's own
precedents (the Ronaldo n=9 regression, `BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md`) warn
against over-trusting.** Two concrete findings support treating this as illustrative, not validated:

- For **Álvarez**, the walk-forward EB model is outright *worse* than the naive flat-historical
  baseline — the same qualitative failure mode as the Ronaldo regression (a more elaborate
  time-varying estimate loses to a simpler fixed one at this sample size).
- For **Messi**, the EB model's apparent edge over the flat baseline is a razor-thin 0.002 Brier
  points, produced almost entirely by which side of a single binary outcome (fold 6) landed on.
  Flip that one coin and the ranking reverses.

Six folds is not enough to distinguish "the k=5 EB-shrinkage formula genuinely adds information for
this specific matchup" from "noise." This backtest does **not** give real statistical confidence
that the walk-forward numbers below are better calibrated than the plain historical rate would be.

**The right conclusion, matching the Ronaldo case's own honesty, is: use the disciplined,
non-fitted k=5 EB-shrinkage estimate (below) because it is the project's validated methodology for
this question type on a stronger sample elsewhere (De Bruyne/Lukaku, n=10 historical each) — not
because this particular n=6 backtest proves it is well-calibrated for Messi/Álvarez. Treat the
final numbers with the same explicit uncertainty the Ronaldo writeup demanded, not as a
backtested-and-confirmed model.**

## 4. Live number for tonight (Step 3 — separate from the backtest above)

Using **all 6** 2026 games (not held out this time, since tonight genuinely is the next
unseen match) plus the full historical sample, same k=5 formula:

**Álvarez, Q1 — P(1+ SOT):**
2026 log `[0,1,1,0,1,1]`, rate = 4/6 = 0.6667. Historical rate 0.7143 (n=7).
`(6*0.6667 + 5*0.7143) / 11 = 0.6883`

**→ Q1 estimate: 0.69**

**Messi, Q4 — P(scores):**
2026 log `[1,1,1,1,1,0]`, rate = 5/6 = 0.8333. Historical rate 0.6364 (n=11).
`(6*0.8333 + 5*0.6364) / 11 = 0.7438`

**→ Q4 estimate: 0.74**

Participation note: unlike De Bruyne (a genuine DNP risk in the Spain-Belgium precedent), both
Messi and Álvarez have made an appearance (`appearances: 1.0`, no zero-minute games) in all 6 of
Argentina's 2026 matches — no rotation, no unused-squad game for either, and tonight is the
biggest game of the tournament. No separate participation-probability discount is applied; the
numbers above are the full estimate, not one stage of a two-stage calculation.

These two numbers (0.69, 0.74) should be read with the explicit caveat from §3: they are the
project's disciplined judgment-based EB-shrinkage estimates, consistent with the one validated
precedent for this question type — not numbers a well-calibrated n=6 backtest has separately
proven correct.

## Files

- Script: [`11_player_prop_backtest_messi_alvarez.py`](11_player_prop_backtest_messi_alvarez.py)
- Machine-readable output: `11_player_prop_backtest_results.json` (written by the script)
- Historical source: `data/processed/statsbomb_player_match_panel.csv`
- 2026 sources: `data/processed/espn_raw_events/espn_event_{760433,760456,760483,760500,760509,760513}.json`
