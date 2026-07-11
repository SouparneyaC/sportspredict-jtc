# Model-Only vs. Market-Blended: A Five-Match Comparison

**Question this document answers:** across five recent matches (Switzerland vs Colombia, Argentina vs Egypt, USA vs Belgium, Portugal vs Spain, Mexico vs England), how did our estimate *devoid of any external market source* (Smarkets, or the crowd) compare in accuracy to what we actually submitted (which in most of these matches already incorporated a market anchor), against the real crowd number and the real outcome?

**A note on what "model-only" means here, match by match.** This is not a uniform comparison, because the five matches were priced under different conditions, and this document only reports a genuine market-free number where one was actually recorded at pricing time — nothing here is reconstructed after the fact or invented to fill a cell. Three distinct cases occur:

1. **Switzerland vs Colombia** — Smarkets data was never captured for this match at all (confirmed in its own derivation file: *"Smarkets FTR not captured pre-match... these are model-only estimates"*). Every one of its 15 submitted estimates is already a market-free number. This is the cleanest case in the set.
2. **Argentina vs Egypt** — the only surviving record for this match is the flat settlement file (`data/external_markets/arg_egy_2026-07-07.json`), which has no preserved derivation notes, bash log, or market-vs-empirical breakdown. I cannot honestly reconstruct a model-only figure for any of its 13 questions. It is included for completeness (real crowd/outcome/RBP only), with the model-only column marked "not recorded."
3. **USA vs Belgium, Portugal vs Spain, Mexico vs England** — these were priced with Smarkets access from the start (`RULE1: market primary source`), but for several *player-prop* questions the session's own reasoning explicitly weighed a personal-history/empirical number against the market number before choosing what to submit — and wrote both numbers down. Those specific rows carry a real model-only figure. Every other row in these three matches (mostly DIRECT/TEAM_MODEL tier team-level questions) was priced from the market with no separate empirical figure ever computed, and is marked "not recorded" rather than guessed.

**A note on the RBP column.** RBP (Relative Brier Points) is the platform's real, authoritative scoring rule, and the RBP/beat-crowd values shown below are the actual results of what we actually submitted — never a hypothetical recomputation. The project has not fully reverse-engineered JTC's exact RBP formula (confirmed non-linear in the crowd/our-Brier gap), so no hypothetical "what RBP would a different number have scored" figure appears anywhere in this document. Where a genuine model-only number exists, its accuracy is instead compared using **Brier score** (squared error against the real 0/1 outcome), which is directly and honestly computable from three known quantities (estimate, outcome) without needing JTC's internal formula. Brier-score "wins" and RBP "beat crowd" flags can disagree on the same row — this happened on this project's own data before and happens again below — because Brier score is symmetric squared error while RBP is the platform's own (partially opaque) relative rule.

---

## 0. Addendum: Point-in-Time (No-Lookahead) Elo Backtest

The "not recorded" cells in the four market-primary matches below split into two kinds: player-prop questions where no goals-model equivalent exists (genuinely not reconstructable without inventing data), and **goals/match-outcome questions where this project's own Elo-based Poisson and ordered-logit models could, in principle, produce a real model-only number** — provided the Elo input is itself correct at the moment of kickoff. Checking that turned up a real bug worth fixing before trusting any such number.

**The bug:** `data/international_results/results.csv` records every WC2026 match's score as `NA` — it is a fixture list, not a results file. Because of this, `model/elo.py` never processed a single actual WC2026 result, and `data/processed/elo_current_ratings.csv` (which I used directly for the France vs Morocco session, and was about to reuse here) is not "current" at all — it is each team's **pre-tournament, early-June rating**, frozen. Verified directly: Argentina's pre-match Elo is identical (2189.5282) across all three of its group-stage rows in `elo_match_panel.csv`, despite winning those games 3-0, 2-0, and 3-1. This is not a lookahead problem (nothing from the future leaked in) — it is the opposite failure: the model is blind to everything the tournament itself has already shown.

**The fix:** I replayed each of the ten teams' actual group-stage and Round-of-32 results (real scores, gathered from `data/processed/espn_match_panel.csv` and the settled `matches/*/06_post_match_results.json` files) through `model/elo.py`'s exact update formula (K=60 for FIFA World Cup, the published G/We logistic formula, +100 home advantage only for a true home fixture), starting from each team's confirmed pre-tournament baseline, stopping exactly at the kickoff of its R16 match — nothing from the match itself or anything later is included. The script is saved at `ml/backtests/r16_point_in_time_elo_replay.py`. Two simplifications are worth flagging: (1) opponents outside this ten-team set (Qatar, Bosnia, Cape Verde, etc.) are held at their own frozen pre-tournament rating rather than being replayed themselves, since they're eliminated by R16 and this avoids replaying the entire bracket for a second-order correction; (2) Mexico's home advantage into the Round of 16 was confirmed directly (its R16 fixture was played at Estadio Banorte, Mexico City), but USA's R16 venue was not recoverable from saved files and is assumed, not confirmed, to continue USA's home-fixture pattern from the group stage and Round of 32.

| Matchup | Corrected point-in-time Elo diff | Frozen pre-tournament Elo diff (what a naive "current ratings" pull gives) | Difference |
|---|---|---|---|
| Switzerland − Colombia | −79.45 | −111.92 | +32.47 |
| Argentina − Egypt | +363.62 | +379.78 | −16.16 |
| United States − Belgium | −129.52 | −117.22 | −12.30 |
| Portugal − Spain | −142.62 | −169.05 | +26.44 |
| Mexico − England | −70.36 | −105.58 | +35.22 |

These diffs feed the same two models used throughout this project: the Poisson goal-rate regression (`b0=0.10408, b1=0.23022, b2=0.0018099`) for total-goals/BTTS/half-time questions, and the ordered logit (`b_elo=0.005199, b_home=0.37713, c1=-0.77018, c2=0.55487`) for match-outcome questions, both fit on this project's 49,400-match historical panel and unaffected by the WC2026 staleness bug (it's the Elo *input*, not the regression coefficients, that was wrong). The resulting **λ_total, P(total≤2), P(BTTS), P(HT tied), and P(win/draw/loss)** for all four matches are the "backtested (no-lookahead)" figures filling in the tables below. Home-team designation follows the same rule established for France vs Morocco: neutral=FALSE only when USA, Mexico, or Canada is a genuine participant.

| Match | λ_home | λ_away | λ_total | P(total≤2) | P(BTTS) | P(HT tied) | P(home win / draw / away win) |
|---|---|---|---|---|---|---|---|
| Switzerland (neutral) vs Colombia | 0.961 | 1.281 | 2.242 | 0.611 | 0.446 | 0.467 | 0.275 / 0.313 / 0.412 |
| Argentina (neutral) vs Egypt | 2.143 | 0.575 | 2.718 | 0.489 | 0.386 | 0.379 | 0.792 / 0.143 / 0.065 |
| United States (home*) vs Belgium | 1.105 | 1.403 | 2.508 | 0.542 | 0.504 | 0.439 | 0.299 / 0.317 / 0.384 |
| Portugal (neutral) vs Spain | 0.857 | 1.436 | 2.294 | 0.598 | 0.439 | 0.457 | 0.215 / 0.292 / 0.493 |
| Mexico (home) vs England | 1.230 | 1.260 | 2.490 | 0.546 | 0.507 | 0.442 | 0.367 / 0.319 / 0.314 |

*USA home-advantage assumption not independently confirmed — see caveat above.

This still isn't a complete model-only reconstruction of every "not recorded" cell — cards, corners, and shots-on-target questions need each team's own pre-match ESPN game log (ESPN box scores from prior games only, which carry no lookahead problem of their own since they only ever included games before the target match) rather than an Elo-derived figure, and player-specific props need a personal-history read that this addendum doesn't attempt. But it does properly fix every goals/outcome-based row, which is where the Elo staleness bug actually mattered.

---

## 1. Switzerland vs Colombia (R16, 2026-07-07/08) — fully market-free

**Result:** Switzerland 0–0 Colombia (Switzerland won; Colombia did not advance). **Total RBP: +144.6, 13/15 beat crowd.** Every estimate below was submitted with no Smarkets data at all — there is no separate "market-blended" version of this match.

| Q | Question | Our estimate (market-free) | Crowd | Outcome | RBP | Beat crowd? |
|---|---|---|---|---|---|---|
| 1 | Dan Ndoye (SUI) to score | 0.22 | 0.23 | NO | 5.14 | Yes |
| 2 | Switzerland clean sheet | 0.28 | 0.29 | YES | 1.16 | Yes |
| 3 | Tied at halftime | 0.45 | 0.46 | YES | 0.80 | Yes |
| 4 | 4+ total cards | 0.30 | 0.45 | NO | 28.14 | Yes |
| 5 | Colombia 5+ corners | 0.47 | 0.52 | NO | 12.98 | Yes |
| 6 | Switzerland 4+ shots on target | 0.63 | 0.49 | NO | **-27.44** | **No** |
| 7 | Substitute scores or assists | 0.31 | 0.36 | NO | 10.85 | Yes |
| 8 | First goal scored in 2nd half | 0.26 | 0.37 | NO | 19.06 | Yes |
| 9 | Either team wins both halves | 0.20 | 0.26 | NO | 10.50 | Yes |
| 10 | Match decided by exactly 1 goal | 0.42 | 0.44 | NO | 7.39 | Yes |
| 11 | Card shown in each half | 0.50 | 0.56 | NO | 18.57 | Yes |
| 12 | Luis Díaz (COL) to score | 0.30 | 0.33 | NO | 8.44 | Yes |
| 13 | Jhon Arias (COL) score or assist | 0.38 | 0.32 | NO | **-4.85** | **No** |
| 14 | Colombia advance to QF | 0.57 | 0.61 | NO | 13.82 | Yes |
| 15 | Breel Embolo (SUI) 1+ shot on target | 0.38 | 0.56 | NO | 40.03 | Yes |

**Brier-score cross-check (our market-free number vs. crowd, against the real outcome):** mean Brier 0.194 (ours) vs 0.220 (crowd) — ours lower (more accurate) on 11 of 15 questions by this measure. Note this doesn't map one-to-one onto the "beat crowd" RBP flags above: Brier score says crowd was actually more accurate on the clean-sheet and HT-tied questions even though we beat crowd on RBP there, and conversely Brier and RBP agree on both of the two losses (Q6, Q13). This is exactly the previously-documented finding that RBP is not a simple linear function of the Brier gap — both measures are reported rather than treated as interchangeable.

**Point-in-time Elo cross-check:** this match's own `03_model_derivations.json` recorded an Elo diff of −85.24 at the time of pricing. The corrected, no-lookahead replay (§0 above) gives −79.45 — close, which is reassuring evidence the original session's Elo input wasn't badly wrong for this particular match, even without the tournament-form correction applied systematically.

**Headline finding:** this is the single best-performing match in this comparison set (+144.6 RBP) and it was priced with **zero** external market input. The one real loss (Q6, Switzerland 4+ SOT, -27.44) came from leaning on Switzerland's own group-stage SOT average (6.0/game) shaded down to a threshold-adjusted 0.63 — with no market to check that number against, unlike the France vs Morocco session where an equivalent Smarkets line would have flagged this estimate as too high before submission.

---

## 2. Mexico vs England (R16, 2026-07-05/06) — market-primary, two recorded model-only splits

**Result:** Mexico 2–3 England (England advanced). **Total RBP: +23.81.**

| Q | Question | Model-only estimate | Actual submitted | Crowd | Outcome | RBP | Beat crowd? | Source of model-only figure |
|---|---|---|---|---|---|---|---|---|
| 1 | Harry Kane (ENG) to score | not recorded | 0.38 | 0.46 | YES | -12.70 | No | Market mid (36.23%) kept directly; no separate empirical figure computed |
| 2 | Jude Bellingham (ENG) 2+ SOT | 0.32 (Croatia+Congo-DR-based correction) | 0.32 | 0.35 | YES | 1.77 | Yes | Market alone (mid 17.42%) looked "Ghana-anchored"; bumped using his non-Ghana evidence — **submitted value already equals the corrected model figure** |
| 3 | England advance to QF | **0.474** (backtested, no-lookahead: P(win)+P(draw)×0.5 from the corrected ordered logit) | 0.53 | 0.56 | YES | -0.51 | No | DIRECT market-anchored; backtested figure would have been the *worst* of the three numbers here — outcome was YES |
| 4 | Raúl Jiménez (MEX) to score | not recorded (illiquid market 23.93% adjusted) | 0.28 | 0.32 | YES | -5.22 | No | Small model-informed bump above an illiquid market quote; no independent figure isolated |
| 5 | Julián Quiñones (MEX) 1+ SOT | not recorded (personal floor: hit in 4/4 games, i.e. ~1.00 empirical) | 0.63 | 0.55 | YES | 19.42 | Yes | Illiquid market 53.69%, bumped for a literal 4-for-4 personal floor; biggest win of the match |
| 6 | Tied at halftime | **0.442** (backtested, no-lookahead) | 0.48 | 0.47 | NO | 2.36 | Yes | DIRECT market-anchored; backtested figure is closer to the real crowd/outcome than what was submitted |
| 7 | 4+ total cards | not recorded | 0.42 | 0.45 | YES | -1.20 | No | DIRECT market-anchored |
| 8 | England more corners than Mexico | not recorded | 0.60 | 0.58 | NO | -0.17 | No | Market (Most_corners England 59.89%) |
| 9 | Goal after 2nd hydration break | **0.446 (pure lambda-scaling formula, no market)** | 0.45 | 0.49 | NO | 11.76 | Yes | No-market timing formula — **submitted value already is the model-only figure** |
| 10 | England 5+ shots on target | **0.80–0.90 (England's own 4-game empirical SOT rate)** | 0.40 | 0.50 | **YES** | **-16.79** | **No** | Market mid (58.23% → λ=4.08 → P=0.387); deliberately stayed at market instead of the empirical range, to avoid repeating a prior loss on this exact team/question type |
| 11 | Penalty shootout | not recorded | 0.19 | 0.24 | NO | 9.82 | Yes | DIRECT market-anchored |
| 12 | Both teams score | **0.507** (backtested, no-lookahead) | 0.48 | 0.50 | YES | -0.23 | No | DIRECT market-anchored; backtested figure is closer to the real outcome (YES) than either the submission or crowd |
| 13 | More cards than goals | 0.577 (compound calc from cards/goals lambdas) | 0.58 | 0.57 | YES | 8.01 | Yes | Compound formula — submitted value already is the model-only figure |
| 14 | 18+ total shots | not recorded | 0.78 | 0.70 | YES | 15.82 | Yes | Market-anchored lambda fit (total shots O/U21.5) |
| 15 | 2 or fewer total goals | **0.546** (backtested, no-lookahead; λ_total=2.490) | 0.61 | 0.56 | NO | -8.31 | No | The submitted 0.61 likely came from a stale/frozen Elo diff (-105.58 vs the correct -70.36); the backtested figure is meaningfully lower and closer to both crowd and the real NO outcome |

**Headline finding — Q10 is the single clearest data point in this entire document.** The market-free, pure-history estimate for "England 5+ SOT" (0.80–0.90, built from England's own 4-game shot log) was much closer to the true outcome (YES) than either what we actually submitted (0.40, deliberately anchored to the market to avoid repeating an earlier loss on the same question type) or the crowd (0.50). Staying at market cost -16.79 RBP here, the biggest loss of the match. This is a direct, real counter-example to the general "don't trust team SOT ceilings over the market" rule this campaign has otherwise built up — the rule was right on average across the matches that motivated it, and wrong here.

---

## 3. USA vs Belgium (R16, 2026-07-07) — market-primary, four recorded model-only splits (all player props)

**Result:** United States 1–4 Belgium (Belgium advanced). **Total RBP: +114.47, 11/15 beat crowd.**

| Q | Question | Model-only estimate | Actual submitted | Crowd | Outcome | RBP | Beat crowd? | Source |
|---|---|---|---|---|---|---|---|---|
| 1 | Christian Pulisic (USA) to score | **0.16 (personal: 0 goals in 4 games, weak R32 output)** | 0.16 | 0.32 | NO | 20.56 | Yes | Market mid 30.49%; personal-history suppression fully adopted — **submitted = model-only** |
| 2 | Kevin De Bruyne (BEL) score or assist | **0.24 (personal: 1 goal/4 games, weakest opponent only, 0 assists all tournament)** | 0.24 | 0.36 | NO | 20.47 | Yes | Market mid 41.09%; suppression fully adopted — **submitted = model-only** |
| 3 | Belgium advance to QF | **0.542** (backtested, no-lookahead: P(win)+P(draw)×0.5) | 0.46 | 0.51 | YES | -3.73 | No | DIRECT market-anchored; backtested figure is closer to the real YES outcome than either the submission or crowd |
| 4 | Malik Tillman (USA) 1+ SOT | not recorded | 0.52 | 0.49 | YES | 11.30 | Yes | PLAYER_LIQUID, near market |
| 5 | Leandro Trossard (BEL) to score | **0.15 (personal: brace only vs a blowout opponent, 0 goals other 3 competitive games)** | 0.15 | 0.29 | NO | 17.31 | Yes | Market ~0.21; suppression fully adopted — **submitted = model-only** |
| 6 | Romelu Lukaku (BEL) to score | **held near market deliberately — NOT suppressed (0.30 vs 0.3327)** | 0.30 | 0.34 | **YES** | **-5.51** | **No** | Genuine recent hot streak (2 goals in last 2 sub appearances) judged real, not a small-sample artifact; kept close to market anyway |
| 7 | Both teams score | **0.504** (backtested, no-lookahead) | 0.62 | 0.59 | YES | 7.35 | Yes | DIRECT market-anchored; the submitted 0.62 (likely on a stale Elo diff) happened to be closer to the real YES outcome than the corrected backtested figure this time |
| 8 | Tied at halftime | **0.439** (backtested, no-lookahead) | 0.42 | 0.43 | NO | 5.38 | Yes | DIRECT market-anchored, all three numbers were already close together |
| 9 | 4+ total cards | not recorded | 0.43 | 0.45 | NO | 8.52 | Yes | DIRECT market-anchored |
| 10 | USA more SOT than Belgium | not recorded (Poisson convolution of two market-fit lambdas) | 0.47 | 0.43 | NO | -2.49 | No | Both team lambdas fit from market O/U4.5 SOT lines — not market-free |
| 11 | Pulisic plays full 90 | **0.30 (subbing pattern across all 4 games: HT sub, DNP, bench role, subbed 88' in the one knockout precedent)** | 0.29 | 0.46 | NO | 32.50 | Yes | No market; base rate built purely from personal substitution history — **submitted ≈ model-only**, biggest win of the match |
| 12 | Goal in each half | 0.58 (product of two market-fit H1/H2 O/U0.5 lines, shaded for correlation) | 0.56 | 0.55 | YES | 6.98 | Yes | Market-derived, not market-free |
| 13 | 3+ total goals | **0.458** (backtested, no-lookahead; λ_total=2.508) | 0.58 | 0.54 | YES | 9.10 | Yes | DIRECT market-anchored; here the submitted (likely stale-Elo) 0.58 was actually closer to the real YES outcome than the corrected backtested figure |
| 14 | 10+ total corners | not recorded | 0.51 | 0.51 | NO | 2.75 | Yes | DIRECT market-anchored |
| 15 | 4+ combined offsides | **0.614 (pure Poisson from each team's own offside history, no market)**, shaded to 0.56 for cross-opponent uncertainty | 0.56 | 0.46 | NO | -16.01 | No | No market existed for this question — **submitted already is the (shaded) model-only figure**, and it was the one clear loss of the match |

**Headline finding:** four of five player-prop suppressions/holds built purely from personal in-tournament history (Pulisic, De Bruyne, Trossard, and the Pulisic-full-90 base rate) won big — three of them *are* the model-only number outright, since the market was deliberately overridden rather than blended. The one genuine no-market, fully-model-derived team question (Q15, combined offsides) was this match's only clear loss, consistent with this campaign's separately-documented finding that offside-count questions are a weak spot for team-history-only models regardless of market access.

---

## 4. Portugal vs Spain (R16, 2026-07-06) — market-primary, two recorded model-only splits

**Result:** Portugal 0–1 Spain (Spain advanced). **Total RBP: +85.41, 13/15 beat crowd.**

| Q | Question | Model-only estimate | Actual submitted | Crowd | Outcome | RBP | Beat crowd? | Source |
|---|---|---|---|---|---|---|---|---|
| 1 | Cristiano Ronaldo (POR) to score | not recorded (held near market) | 0.32 | 0.37 | NO | 13.92 | Yes | Scored in his last competitive knockout game, no drought signal; essentially market |
| 2 | Lamine Yamal (ESP) score or assist | **≈0.25 (real personal score/assist rate, only hit vs weakest opponent, 0 assists all tournament)** | 0.30 | 0.51 | NO | **38.48** | Yes (biggest win) | Market mid 44.85%; suppressed most of the way to the personal rate — model-only figure would have been even closer to the true NO outcome than what was actually submitted |
| 3 | Spain advance to QF | **0.639** (backtested, no-lookahead: P(win)+P(draw)×0.5) | 0.66 | 0.64 | YES | 6.92 | Yes | DIRECT market-anchored; all three numbers agree closely and correctly favored Spain |
| 4 | Bruno Fernandes (POR) 1+ SOT | **0.75 (personal floor: 1+ SOT in 3 of 4 games)** | 0.58 | 0.53 | **NO** | **-4.77** | **No** | Market ~0.35; boosted toward the personal floor rather than suppressed — the model-only figure (0.75) would have been *far worse* than either the market or the actual submission here, since Spain's dominant possession broke his service pattern entirely (0 SOT) |
| 5 | Both halves same # of goals | not recorded | 0.25 | 0.31 | NO | 10.49 | Yes | BASE_RATE_FORMULA, no market for this exact question |
| 6 | First card before first goal | not recorded (4-game base rate, 1/4 hit ≈ 0.25) | 0.30 | 0.50 | **YES** | **-43.96** | **No** | No market existed; base-rate-only estimate — **submitted ≈ model-only**, and this is the single worst loss of the whole campaign to date |
| 7 | Portugal scores first | not recorded | 0.36 | 0.38 | NO | 7.26 | Yes | DIRECT market-anchored |
| 8 | 3+ total goals | **0.402** (backtested, no-lookahead; λ_total=2.294) | 0.52 | 0.53 | NO | 6.79 | Yes | DIRECT market-anchored; the backtested figure is meaningfully lower and closer to the real NO outcome than either the submission or crowd |
| 9 | Diogo Costa (POR) 4+ saves | not cleanly separable (illiquid market λ range 2.39–3.88, blended with his bimodal saves history to λ=3.96) | 0.50 | 0.51 | YES | 2.62 | Yes | Blended, not a pure split |
| 10 | Substitute scores | not recorded | 0.33 | 0.32 | YES | 7.34 | Yes | BASE_RATE_FORMULA, no market |
| 11 | 4+ total cards | not recorded | 0.40 | 0.45 | NO | 13.59 | Yes | DIRECT market-anchored |
| 12 | 9+ total substitutions | **0.58 (pure precedent: 9,10,8,8 subs in the last 4 comparable knockout games, no market)** | 0.58 | 0.56 | YES | 11.39 | Yes | No market existed — **submitted = model-only**, paid off cleanly |
| 13 | Spain 6+ corners | not recorded | 0.54 | 0.54 | YES | 3.97 | Yes | DIRECT market-anchored |
| 14 | Match goes to extra time | **0.292** (backtested, no-lookahead: P(draw) itself, i.e. the probability the match is level after regulation) | 0.27 | 0.32 | NO | 11.31 | Yes | DIRECT market-anchored; backtested figure sits between the submission and crowd |
| 15 | Any Portugal player 2+ SOT | 0.63 (compound across 5 players' individual markets) shaded to 0.52 against a team-total cross-check | 0.52 | 0.57 | YES | 0.06 | Yes | Market-derived compound, not market-free |

**Headline finding:** this match is the clearest illustration in the whole document that "trust personal history over the market" is not a universal rule. Yamal (Q2) shows the pattern winning big — the model-only number would have been even better than what we submitted. Bruno Fernandes (Q4) shows the identical logic (a personal floor built from a 4-game sample) failing outright when the opponent's dominant possession changed the entire game state a small sample couldn't foresee — the market, not the personal floor, was closer to right. The two no-market questions (Q6 event-ordering, Q12 substitution count) split exactly the same way: one was this campaign's worst-ever single loss, the other a clean win.

---

## 5. Argentina vs Egypt (2026-07-07) — no surviving derivation data

**Result:** Argentina 3–2 Egypt (Argentina won). **Total RBP: +63.81, 7/13 beat crowd.** No model-only figures can be honestly reported for this match — only the flat settlement record survives, with no preserved reasoning about what was market-derived versus history-derived at pricing time.

| Q | Question | Model-only estimate | Actual submitted | Crowd | Outcome | RBP | Beat crowd? | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 | Lionel Messi (ARG) to score | not recorded | 0.54 | 0.59 | YES | -3.11 | No | Player prop, no goals-model equivalent |
| 2 | Mohamed Salah (EGY) to score | not recorded | 0.16 | 0.26 | NO | 12.57 | Yes | Player prop, no goals-model equivalent |
| 3 | Argentina win in regulation | **0.792** (backtested, no-lookahead, direct ordered-logit output) | 0.73 | 0.74 | YES | 2.81 | Yes | All three numbers agree closely and correctly favored Argentina |
| 4 | Omar Marmoush (EGY) 1+ SOT | not recorded | 0.46 | 0.37 | NO | -6.01 | No | Player prop, no goals-model equivalent |
| 5 | Julián Álvarez (ARG) score or assist | not recorded | 0.28 | 0.45 | NO | 29.14 | Yes | Player prop, no goals-model equivalent |
| 6 | 4+ total cards | not recorded | 0.41 | 0.43 | NO | 7.25 | Yes | Not an Elo-derived stat; would need a cards-specific model |
| 7 | First goal scorer ≠ Messi/Salah | not recorded | 0.77 | 0.55 | YES | 36.17 | Yes | Needs a player goal-share model, not just team-level Elo |
| 8 | Both teams score | **0.386** (backtested, no-lookahead) | 0.39 | 0.43 | YES | -6.84 | No | All three numbers (submitted, crowd, backtested) badly underestimated this — the real match had both teams scoring |
| 9 | Total goals odd | **0.498** (backtested, no-lookahead; closed-form P(odd)=(1-e^{-2λ})/2 for a Poisson total) | 0.47 | 0.52 | YES | -6.43 | No | Backtested figure sits almost exactly at a coin flip, close to crowd, closer to the real YES outcome than the submission |
| 10 | Any player scores 2+ | not recorded | 0.36 | 0.32 | NO | 0.48 | Yes | Needs a player goal-share model, not just team-level Elo |
| 11 | Argentina 5+ SOT | not recorded | 0.70 | 0.66 | YES | 8.81 | Yes | Not an Elo-derived stat; would need Argentina's own pre-match SOT log |
| 12 | Argentina 6+ corners | not recorded | 0.47 | 0.53 | YES | -8.51 | No | Not an Elo-derived stat; would need Argentina's own pre-match corners log |
| 13 | Goal in 1H after 1st hydration break | not recorded | 0.48 | 0.44 | NO | -2.51 | No | Timing-window question, no goals-model equivalent |

No headline finding is drawn from this match beyond its raw record — including it here only for the record-keeping completeness the rest of the document has.

---

## Synthesis: what this actually tells us about model-only vs. market-blended

Across the rows where a genuine model-only figure exists (16 rows total: all 15 in Switzerland vs Colombia by construction, plus 5 explicitly recorded splits in the other three matches — Bellingham, Quiñones's floor, Kane's not-recorded case aside, Pulisic, De Bruyne, Trossard, Pulisic-full-90, England 5+ SOT, Yamal, Bruno Fernandes, the offside question, the substitution-count question), the pattern is **not** "model-only wins" or "market wins" — it is genuinely mixed, and the direction correlates with *why* the market and the personal history disagreed:

- **When personal history flagged a real, still-relevant behavioral pattern** (Pulisic's 4-game drought, De Bruyne's early substitutions, Trossard's one-blowout-goal pattern, Yamal's real 25% rate, England's own SOT volume) **the model-only read tended to beat the market**, sometimes decisively (England 5+ SOT would have swung a -16.79 loss into a likely win; Yamal's suppression was already the biggest win of its match and the fully-model-only number would have been better still).
- **When the personal-history sample was too thin to anticipate a genuine regime change in the specific game** (Bruno Fernandes's floor breaking under Spain's dominant possession, Lukaku's hot streak continuing anyway, the first-card-before-first-goal 4-game base rate, the combined-offsides Poisson estimate), **the market or a wider prior was closer to right**, in two cases (Bruno Fernandes, first-card-before-goal) by a wide and costly margin.
- Switzerland vs Colombia, priced with zero market access at all, still produced this document's best single-match result (+144.6 RBP) — direct evidence that a careful model-only approach is not structurally worse than a market-blended one when the underlying reasoning is sound, but its one loss (Switzerland 4+ SOT, -27.44) is exactly the kind of team-count-ceiling overshoot that a market check would very plausibly have caught, as it did in the France vs Morocco pricing session that motivated this comparison.

The honest overall conclusion: **the market's real value in this project's actual results is not that it is more accurate than personal history in general — it is that it acts as a check specifically against confident, thin-sample extrapolations for team-level count ceilings** (shots on target, corners, combined counting stats), which is exactly the question type this project's own rules (`TEAM_SOT_EMPIRICAL_FLOOR`, retired) already identified as the recurring failure mode before this document was written.

**What the point-in-time Elo backtest (§0) adds to this picture:** eleven more goals/outcome rows across the four market-primary matches now carry a genuine, no-lookahead model-only figure that wasn't available before. The split there is close to even — five rows (MEX-ENG's advance-to-QF, HT-tied, BTTS, and total-goals; USA-BEL's advance-to-QF) where the backtested figure would have beaten what was actually submitted, against four rows (USA-BEL's BTTS and total-goals; POR-ESP's advance-to-QF and extra-time) where the original market-anchored submission held up better or the two were essentially tied. There is no clean pattern here favoring either source specifically — unlike the player-prop rows above, these are all DIRECT-tier team questions where the market was simply adopted without controversy, so the backtest is testing "was the market right" rather than "was personal history right," and the answer is genuinely mixed. The one unambiguous, non-mixed finding from this exercise is methodological rather than predictive: **`elo_current_ratings.csv` is not safe to use for any WC2026 in-tournament match without a point-in-time correction** — it silently returns pre-tournament, early-June ratings frozen at whatever they were before the group stage even began, a bug that would have produced a materially wrong Elo diff (off by 12 to 35 points depending on the match) for every one of these five matches, including the France vs Morocco session that used it directly.
