# France vs Spain — Semifinal, 2026-07-14

**Final score:** Spain 2-0 France (Mikel Oyarzabal penalty 22', Pedro Porro 58'). Winner: Spain, advances to the final.
**Venue:** AT&T Stadium, Arlington, TX (neutral — neither team is a WC2026 host nation).
**Kickoff → close:** 19:00 UTC → 23:00 UTC.
**Match IDs:** JTC `de7b7b6f-f3a8-4948-af5e-f0f4565728d0` · ESPN event `760514` · Smarkets event `45192700`.
**Source repo:** all raw data, scripts, and intermediate artifacts referenced below live in
`sportspredict_research/matches/France Vs Spain (Jul.14.26)/` and `sportspredict_research/ml/backtests/`
unless otherwise noted.

## Executive summary

**+138.32 RBP, 10 wins / 3 losses on the 13 answered questions (77%), plus two questions deliberately
dropped.** Three things worth knowing before reading further:

1. **Three questions were deliberately priced away from the recommended default** (see [decision
   0001](../../decisions/0001-market-priority-over-domain-model.md) and
   [0002](../../decisions/0002-shadow-deploy-before-live-submission.md)) as live tests of a pure domain
   model and a newly-backtested-but-not-yet-market-validated hierarchical model. Two won decisively
   (+26.73, +28.23 — the two biggest results on the slate). One lost (-12.48). This is genuinely mixed
   evidence from a single match, not proof either posture is generally correct, and is treated that way
   in the postmortem below.
2. **Two questions were dropped** on specific historical/statistical evidence (see
   [decision 0003](../../decisions/0003-never-blindly-drop-a-question.md)), not general discomfort with
   the topic. Both resolved YES — logged honestly, without over-reading a single match against a
   multi-question base rate.
3. **The costliest single loss was the highest-conviction submitted number on the slate** (France 4+
   shots on target, submitted 72%, missed by exactly one shot on target). A reminder that a high
   probability is a bet with real downside, not a near-certainty.

---

## Q1 — Will there be 4+ combined offsides in regulation?

**DROPPED.**

### Pre-match
No Smarkets market exists for this question, or for offside questions generally — confirmed directly
against the fetched market list ([`bot/fetch_fra_esp_smarkets.py`](../../../bot/fetch_fra_esp_smarkets.py) output, `09_smarkets_quotes_processed.json`).
A hierarchical Poisson model (team random intercept + Elo diff + data-source fixed effect,
[`ml/backtests/lib_hierarchical_backtest.R`](../../../ml/backtests/lib_hierarchical_backtest.R)) was pre-registered and walk-forward backtested for this exact
family. It initially appeared to pass with a large effect — investigated before trusting it, and traced to
an 8.49x StatsBomb-vs-ESPN measurement gap caused by a genuine extraction bug ([`datasets/build_statsbomb_panel.py`](../../../datasets/build_statsbomb_panel.py)
only counted the rare standalone `Offside` event type, missing the dominant `Pass Offside` outcome encoding).
Fixed the bug, rebuilt the full data chain, reran — the "signal" collapsed to noise (p=0.63). Separately, a
full audit of the project's settled history (`datasets/master_question_dataset.csv`, 921 scored questions)
found this exact combined-both-teams-N+ phrasing has a real negative track record: n=17, net -63.34 RBP,
53% win rate — worse than the single-team-threshold variant of the same stat (n=20, +181.58, 80%), which
is why the two must be evaluated separately rather than as one "offsides" category.

**Decision:** drop, per decision 0003 reason 1 (documented negative track record for this exact structure).

### Settlement
**Result: YES.** Final combined offsides: France 4 + Spain 5 = 9, well clear of the threshold.
No RBP impact (dropped). Logged for the record: one match resolving favorably does not overturn a
17-question base rate on its own — the drop decision is graded against the evidence available at
decision time, not against this single outcome.

**Scripts/data used:** [`bot/fetch_fra_esp_smarkets.py`](../../../bot/fetch_fra_esp_smarkets.py), [`datasets/build_statsbomb_panel.py`](../../../datasets/build_statsbomb_panel.py) (bug fix),
[`datasets/build_unified_team_match_panel.R`](../../../datasets/build_unified_team_match_panel.R), [`ml/backtests/lib_hierarchical_backtest.R`](../../../ml/backtests/lib_hierarchical_backtest.R),
[`ml/backtests/run_all_family_backtests.R`](../../../ml/backtests/run_all_family_backtests.R), [`ml/backtests/PREREGISTRATION_cards_corners_offsides_and_combined.md`](../../../ml/backtests/PREREGISTRATION_cards_corners_offsides_and_combined.md),
`datasets/master_question_dataset.csv`.

---

## Q2 — Will there be 4+ total cards in regulation?

### Pre-match
Direct, liquid Smarkets market: `Cards_OU3.5`, normalized mid 0.3973. A hierarchical model including
referee identity (extracted from ESPN's `gameInfo.officials` field, previously unused — 100/101 2026
matches and 254/256 StatsBomb matches have it), each team's own point-in-time shrunk foul rate
(r=0.449 correlation with cards, n=456), and a knockout-stage fixed effect (pooled knockout matches
average 3.53 cards/match vs. 2.55 group-stage, p=0.043 on a small sample) was built and walk-forward
backtested specifically to test whether the original cards model's failure was a missing-feature problem.
It still failed to beat the production baseline (p=0.252, materially unchanged from the original model's
p=0.218) — ruling out "we forgot referee/fouls/stage" as the explanation, not just leaving it assumed.

**Submitted: 0.40** (direct market anchor, per decision 0001). **Crowd: 0.43.**

### Settlement
**Result: NO.** Final: 3 total cards (Rabiot Y 9', Cucurella Y 31', Mbappé Y 86').
**RBP: +9.84. Beat crowd.**

**Scripts/data used:** [`bot/fetch_fra_esp_smarkets.py`](../../../bot/fetch_fra_esp_smarkets.py), [`data/processed/fetch_all_raw_events.py`](../../../data/processed/fetch_all_raw_events.py) (referee
extraction), [`ml/backtests/PREREGISTRATION_cards_referee_fouls_stage.md`](../../../ml/backtests/PREREGISTRATION_cards_referee_fouls_stage.md),
[`ml/backtests/walk_forward_cards_referee_backtest.R`](../../../ml/backtests/walk_forward_cards_referee_backtest.R), `data/processed/unified_team_match_panel_with_referee.csv`.

---

## Q3 — Will Lamine Yamal (Spain, #19) score or assist a goal in regulation?

### Pre-match
Liquid Smarkets player market (`Score_or_assist`, Yamal mid 0.3205). Personal in-tournament rate: 1
score-or-assist in 6 games (0.167), from [`bot/compile_fra_esp_espn_form.py`](../../../bot/compile_fra_esp_espn_form.py)'s per-game extraction,
cross-checked directly against ESPN's individual player stat lines. Applied the project's validated
"Cluster-A suppression" pattern (a 7-for-7 live track record of suppressing props on genuine multi-game
personal droughts) rather than a naive market anchor.

**Submitted: 0.18** (the no-crowd/pure-data shrinkage estimate — a larger downward deviation from the
0.32 crowd/market than the originally-recommended 0.25).

### Settlement
**Result: NO.** Yamal: 0 goals, 0 assists, 0 shots across the full match.
**RBP: +35.62. Beat crowd.** Second-largest win on the slate — the deviation was not just correctly
directioned but correct by a wider margin than the more conservative recommended number would have captured.

**Scripts/data used:** [`bot/fetch_fra_esp_smarkets.py`](../../../bot/fetch_fra_esp_smarkets.py), [`bot/compile_fra_esp_espn_form.py`](../../../bot/compile_fra_esp_espn_form.py),
`data/processed/statsbomb_player_match_panel.csv` (attacker base rate).

---

## Q4 — Will the referee conduct an on-field review at the pitchside VAR monitor?

**DROPPED.**

### Pre-match
No market exists. Zero prior occurrences of this exact question type in the project's settled history —
not thin data, no data. A dedicated research pass
(`sportspredict_research/BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md`, built by a research agent
reading Kupiec 1995's VaR-backtesting methodology via a Federal Reserve working paper) found that even a
full "regulatory year" of 255 i.i.d. observations gives only 65% power to detect a *severe* 3x rate
misspecification in a rare binary event — this project's actual evidence (1 hand-verified on-field review
in 12 matches, and no way to separate on-field from booth-only reviews at scale in ESPN's data) is roughly
1/20th that already-insufficient sample. A Beta(1,10)-prior Beta-Binomial posterior on the 1/12 count gave
a mean of 0.087 (95% CI [0.011, 0.228]) — computed for the record, not as a submission, since it's built
from a much narrower evidence base than a real number would need.

**Decision:** drop, per decision 0003 reason 2 (zero prior occurrences + demonstrated statistical-power ceiling).

### Settlement
**Result: YES.** One VAR check occurred at 83' ("VAR Decision: Other Decision Cancelled" in ESPN's
commentary feed) and was officially ruled by the platform as a qualifying on-field review. No RBP impact
(dropped). This resolves the measurement-ambiguity finding from the pre-match research — ESPN's text alone
couldn't distinguish an on-field review from a booth-only check, but the official platform ruling confirms
this one counted. It becomes the project's 2nd confirmed real occurrence of this question type (previously
1-in-12) — still nowhere near enough to validate a model, but a genuine, banked data point for the future.

**Scripts/data used:** [`BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md`](../../../BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md) (research agent), Beta-Binomial
posterior calculation, [`matches/France Vs Spain (Jul.14.26)/03_model_derivations.json`](../../../matches/France%20Vs%20Spain%20%28Jul.14.26%29/03_model_derivations.json) (hand-count).

---

## Q5 — Will the match have 3+ total goals in regulation?

### Pre-match
Direct Smarkets market (`OU2_5_goals`, normalized 0.5038). Cross-checked against a market-calibrated
100k-draw joint simulation ([`bot/simulate_fra_esp_sf.py`](../../../bot/simulate_fra_esp_sf.py)) that fits a Dixon-Coles scoreline grid to the
liquid market lines so all goal-structure questions on the slate answer consistently with each other.
A second, fully crowd-free check — the project's own historical Poisson/Dixon-Coles model
([`data/processed/poisson_goals_coefs.json`](../../../data/processed/poisson_goals_coefs.json), fit on 49,400 historical matches, fed with the corrected
point-in-time Elo, not market-fit) gave 0.383, notably below the market — flagged as a real divergence
(the pure model consistently under-shot goal expectancy for this match relative to market) but not acted
on, per decision 0001.

**Submitted: 0.50** (direct market). **Crowd: 0.53.**

### Settlement
**Result: NO.** Final: 2 total goals. **RBP: +10.10. Beat crowd.**

**Scripts/data used:** [`bot/fetch_fra_esp_smarkets.py`](../../../bot/fetch_fra_esp_smarkets.py), [`bot/simulate_fra_esp_sf.py`](../../../bot/simulate_fra_esp_sf.py), [`model/dixon_coles.py`](../../../model/dixon_coles.py),
[`data/processed/poisson_goals_coefs.json`](../../../data/processed/poisson_goals_coefs.json), [`ml/backtests/build_full_tournament_pit_elo.py`](../../../ml/backtests/build_full_tournament_pit_elo.py).

---

## Q6 — Will the match be tied at 90' and go to extra time?

### Pre-match
Direct Smarkets market (`Will_there_be_ET`, normalized 0.2967) plus the simulation's own draw probability
(0.3053) and the pure historical model's draw probability (0.3053) — three independent methods converged
tightly.

**Submitted: 0.31. Crowd: 0.34.**

### Settlement
**Result: NO.** Spain won 2-0 in regulation. **RBP: +8.66. Beat crowd.**

**Scripts/data used:** same as Q5.

---

## Q7 — Will a goal be scored before the first hydration break?

### Pre-match
Derived from the Smarkets `Goal_1_time_bracket` market (implied P(first goal ≤24') = 0.4331) and the
simulation's timing-slope fit to that same market. Independently cross-checked against a genuine
crowd-free empirical base rate: built a raw-event panel across all 100 played WC2026 matches
([`ml/backtests/build_rare_event_panels.py`](../../../ml/backtests/build_rare_event_panels.py), using each match's own actual "drinks break" timing, not an
assumed universal minute), giving 42/100 = 0.42 — a first pass had wrongly conflated injury stoppages with
real hydration breaks, understating the true window; caught via a sanity check before being reported and
fixed by filtering on ESPN's own delay-reason text.

**Submitted: 0.42. Crowd: 0.38.**

### Settlement
**Result: YES.** Oyarzabal's penalty at 22' preceded this match's own first break (24').
**RBP: +13.96. Beat crowd.** Locked in at halftime, held.

**Scripts/data used:** [`bot/fetch_fra_esp_smarkets.py`](../../../bot/fetch_fra_esp_smarkets.py), [`bot/simulate_fra_esp_sf.py`](../../../bot/simulate_fra_esp_sf.py),
[`ml/backtests/build_rare_event_panels.py`](../../../ml/backtests/build_rare_event_panels.py), [`data/processed/fetch_all_raw_events.py`](../../../data/processed/fetch_all_raw_events.py).

---

## Q8 — Will the first goal be scored by a player wearing a single-digit shirt (1-9)?

### Pre-match
Derived from the Smarkets `First_goalscorer` market, normalized and filtered to single-digit-shirt players
using confirmed matchday squad numbers (`10_espn_form_supplement.json`, extracted from ESPN's roster data)
— giving a market-implied share of 0.2853. Cross-checked against a fully independent empirical method:
each team's actual shirt-number distribution of tournament goals so far (France 5/16 single-digit, Spain
3/10), giving 0.31. The two independent methods agreed closely.

**Submitted: 0.31** (the pure-empirical figure, a small deviation from the blended 0.28 recommendation).

### Settlement
**Result: NO.** First goal scorer Oyarzabal wears **#21**, confirmed directly against ESPN's individual
player roster data — not single-digit. **RBP: +11.49. Beat crowd.** Locked in at halftime, held.

**Scripts/data used:** [`bot/fetch_fra_esp_smarkets.py`](../../../bot/fetch_fra_esp_smarkets.py), [`bot/compile_fra_esp_espn_form.py`](../../../bot/compile_fra_esp_espn_form.py)
(jersey mapping), [`data/processed/fetch_all_raw_events.py`](../../../data/processed/fetch_all_raw_events.py) (final scorer roster confirmation).

---

## Q9 — Will Spain advance to the final?

### Pre-match
Direct, liquid Smarkets market (`To_qualify`, Spain normalized 0.4127, favoring France). The project's
own pure Elo→Poisson→Dixon-Coles model, fed with the corrected point-in-time Elo (a systematic
full-tournament replay, [`ml/backtests/build_full_tournament_pit_elo.py`](../../../ml/backtests/build_full_tournament_pit_elo.py), built and cross-checked this
same week after finding the production Elo file was frozen at pre-tournament values), gave **Spain 0.53**
— favoring Spain, the opposite direction from the market. This is a genuine, flagged disagreement between
two legitimate methods, not a rounding difference.

**Decision, tested deliberately as a live check on [decision 0001](../../decisions/0001-market-priority-over-domain-model.md):**
**submitted 0.53**, the pure model's number, overriding the market-priority default. **Crowd: 0.43.**

### Settlement
**Result: YES.** Spain won 2-0. **RBP: +26.73. Beat crowd.**

**Verdict:** the deviation from the market-priority default won, clearly. Per decision 0001's own logic,
one live match does not overturn 505 historical matches of evidence that market beats model on average —
this is logged as a genuine, valuable counter-example, not proof the general rule was wrong.

**Scripts/data used:** [`ml/backtests/build_full_tournament_pit_elo.py`](../../../ml/backtests/build_full_tournament_pit_elo.py),
`data/processed/wc2026_pit_elo_panel.csv`, [`model/dixon_coles.py`](../../../model/dixon_coles.py),
[`data/processed/poisson_goals_coefs.json`](../../../data/processed/poisson_goals_coefs.json), [`bot/fetch_fra_esp_smarkets.py`](../../../bot/fetch_fra_esp_smarkets.py).

---

## Q10 — Will Kylian Mbappé (France, #10) score a goal in regulation?

### Pre-match
Tight, liquid Smarkets market (`Anytime_goalscorer`, Mbappé mid 0.4405, bid/offer spread only 0.39
percentage points — about as liquid as a player prop gets on this platform). Personal-form-only
alternative: k=3 empirical-Bayes shrinkage of his 5-goals-in-6-games tournament rate (0.833) toward a
generic elite-attacker base rate from StatsBomb WC2018/2022 history (0.141), giving 0.60.

**Decision, tested deliberately as a live check on [decision 0002](../../decisions/0002-shadow-deploy-before-live-submission.md)-adjacent reasoning:**
**submitted 0.60**, the personal-form number, overriding a tight liquid market. This is explicitly the
shape of decision the project's own `RULE17` was retired for after a 0-for-5, -155.64 RBP historical
pattern before this match (upward deviation from a liquid market on personal-form conviction).

### Settlement
**Result: NO.** Mbappé: 0 goals, 3 shots, 0 shots on target, 1 yellow card (86').
**RBP: -12.48. Below crowd.**

**Verdict:** the one of the three flagged live tests that lost, and it lost exactly the way the
pre-match caution predicted it might. A second live data point confirming the underlying pattern
(personal hot streaks are visible, public information a liquid market has almost certainly already
priced in — the market wasn't missing his form, it likely had additional information, such as Spain's
specific defensive quality, that the shrinkage calculation had no way to see).

**Scripts/data used:** [`bot/fetch_fra_esp_smarkets.py`](../../../bot/fetch_fra_esp_smarkets.py), [`bot/compile_fra_esp_espn_form.py`](../../../bot/compile_fra_esp_espn_form.py),
`data/processed/statsbomb_player_match_panel.csv`.

---

## Q11 — Will a goal be scored after the first hydration break but before the second?

### Pre-match
No direct market. Simulation-derived estimate (0.71) from [`bot/simulate_fra_esp_sf.py`](../../../bot/simulate_fra_esp_sf.py), cross-checked
against the same crowd-free 99-100-match empirical panel built for Q7 ([`ml/backtests/build_rare_event_panels.py`](../../../ml/backtests/build_rare_event_panels.py)):
74/99 = 0.747 of matches had a goal fall between their own first and second hydration breaks.

**Submitted: 0.75** (close to the pure-empirical figure). **Crowd: 0.61.**

### Settlement
**Result: YES.** This match's breaks were at 24' and 69'; Pedro Porro's goal (58') fell inside that
window. **RBP: +23.26. Beat crowd.**

**Scripts/data used:** [`bot/simulate_fra_esp_sf.py`](../../../bot/simulate_fra_esp_sf.py), [`ml/backtests/build_rare_event_panels.py`](../../../ml/backtests/build_rare_event_panels.py),
[`data/processed/fetch_all_raw_events.py`](../../../data/processed/fetch_all_raw_events.py).

---

## Q12 — Will Spain have 5+ shots on target in regulation?

### Pre-match
No direct Smarkets market at this exact threshold — derived from the total-SOT line minus the
France-specific SOT line ([`bot/simulate_fra_esp_sf.py`](../../../bot/simulate_fra_esp_sf.py)), giving a market-implied 0.4929. Separately, a
hierarchical partial-pooling Poisson model for team-level SOT (team random intercept + Elo diff +
data-source fixed effect, later refined with each team's own absolute Elo to correct a diagnosed
elite-team underprediction bias) was pre-registered
([`ml/backtests/PREREGISTRATION_sot_hierarchical_backtest.md`](../../../ml/backtests/PREREGISTRATION_sot_hierarchical_backtest.md)), walk-forward backtested across 29
chronological folds, and **passed** against the production baseline (mean NLL 2.154 vs. 2.378, p=0.0003,
match-clustered bootstrap 90% band entirely positive). Per [decision 0002](../../decisions/0002-shadow-deploy-before-live-submission.md),
this backtest evidence alone does not clear the model to override a submission — it has never been
validated against a live market, only against the old production baseline.

**Decision, an explicit shadow-test of the model per decision 0002:** **submitted 0.36**, the model's raw
output, instead of the market-derived 0.49.

### Settlement
**Result: NO.** Spain finished with 2 shots on target from 10 total shots.
**RBP: +28.23. Beat crowd. The single largest result on the entire slate.**

**Verdict:** the shadow-tested model's lower number was decisively closer to reality than the
near-coin-flip market/crowd (~0.49-0.50). This is the first live data point where the model
clearly beat the market on exactly the family it was built and backtested for — real, valuable
evidence, and per decision 0002 still just one data point. The model remains in shadow mode.

**Scripts/data used:** [`ml/backtests/PREREGISTRATION_sot_hierarchical_backtest.md`](../../../ml/backtests/PREREGISTRATION_sot_hierarchical_backtest.md),
[`ml/backtests/PREREGISTRATION_elo_level_refinement.md`](../../../ml/backtests/PREREGISTRATION_elo_level_refinement.md), [`ml/backtests/lib_hierarchical_backtest.R`](../../../ml/backtests/lib_hierarchical_backtest.R),
[`ml/backtests/apply_to_fra_esp.R`](../../../ml/backtests/apply_to_fra_esp.R), [`ml/backtests/blend_market_glmm.py`](../../../ml/backtests/blend_market_glmm.py) (built, not used live this match),
[`bot/fetch_fra_esp_smarkets.py`](../../../bot/fetch_fra_esp_smarkets.py), [`bot/simulate_fra_esp_sf.py`](../../../bot/simulate_fra_esp_sf.py).

---

## Q13 — Will both teams score in regulation?

### Pre-match
Direct, liquid Smarkets market (`BTTS`, normalized 0.5905), cross-checked against the simulation
(0.4571) and the pure historical model (0.4571).

**Submitted: 0.59** (direct market anchor, matching crowd exactly). **Crowd: 0.59.**

### Settlement
**Result: NO.** France failed to score; only Spain did. **RBP: +5.54. Beat crowd** (a small edge from
the unrounded submitted value sitting fractionally below the unrounded crowd value, both displaying as
59% — an early live-preview estimate mischaracterized this as a loss before the official settlement
figure was available; corrected here).

**Scripts/data used:** [`bot/fetch_fra_esp_smarkets.py`](../../../bot/fetch_fra_esp_smarkets.py), [`bot/simulate_fra_esp_sf.py`](../../../bot/simulate_fra_esp_sf.py).

---

## Q14 — Will Spain make the first substitution of the match?

### Pre-match
No market exists. Priced from a simple pairwise comparison of each team's own recent first-substitution
minutes across their 2026 games (`10_espn_form_supplement.json`) — France had never subbed before minute
61 in six games; Spain had subbed as early as minute 45 three times — with an outlier-drop check
(dropping the most extreme observation from each side moves the estimate less than 10 percentage points,
so it was kept). A dedicated, purpose-built walk-forward logistic model (team's own shrunk historical
first-sub tendency + Elo diff, using only pre-match-knowable covariates since in-match trailing state
isn't available before kickoff) was built and backtested specifically to test whether a more rigorous
approach could improve on this heuristic ([`ml/backtests/walk_forward_first_sub_backtest.py`](../../../ml/backtests/walk_forward_first_sub_backtest.py)). It failed —
confidently worse than a naive 50/50 baseline (bootstrap 90% band entirely negative,
[-0.0536, -0.0030]) — so the simple heuristic was kept rather than replaced.

**Submitted: 0.60. Crowd: 0.54.**

### Settlement
**Result: NO.** France made the first substitution of the match — Maxence Lacroix for the injured
William Saliba, 30'. **RBP: -10.64. Below crowd.** Locked in at halftime, held.

**Scripts/data used:** [`bot/compile_fra_esp_espn_form.py`](../../../bot/compile_fra_esp_espn_form.py), [`ml/backtests/build_rare_event_panels.py`](../../../ml/backtests/build_rare_event_panels.py),
[`ml/backtests/PREREGISTRATION_q14_first_sub_race.md`](../../../ml/backtests/PREREGISTRATION_q14_first_sub_race.md), [`ml/backtests/walk_forward_first_sub_backtest.py`](../../../ml/backtests/walk_forward_first_sub_backtest.py).

---

## Q15 — Will France have 4+ shots on target in regulation?

### Pre-match
Direct Smarkets market exists at a different threshold (`France_SOT_OU4.5`, i.e. the 5+ line, normalized
0.5633) — a Poisson lambda was fit to that line and evaluated at the 4+ threshold instead
([`bot/simulate_fra_esp_sf.py`](../../../bot/simulate_fra_esp_sf.py)), giving 0.7358. The same hierarchical SOT model used for Q12 gave a
lower, shadow-test-only figure (0.60), not submitted here.

**Submitted: 0.72** (the market-derived figure — this project's highest-conviction number on the whole
slate). **Crowd: 0.66.**

### Settlement
**Result: NO.** France finished with 3 shots on target from 10 total shots — missing the threshold by
exactly one shot. France had zero shots on target at halftime and found only three across the full 90+
minutes. **RBP: -11.98. Below crowd.**

**Verdict:** the costliest loss of the match, and the one worth remembering longest: a 72% conviction
number derived carefully from a real, liquid market line is still a bet with real downside, not a
near-certainty. Nothing about the process here was wrong — the market itself (66% crowd, market-implied
lambda giving 73.6%) also badly overestimated France's attacking output; this was a case where the whole
market, not just the model, missed how anemic France's second-half performance would be.

**Scripts/data used:** [`bot/fetch_fra_esp_smarkets.py`](../../../bot/fetch_fra_esp_smarkets.py), [`bot/simulate_fra_esp_sf.py`](../../../bot/simulate_fra_esp_sf.py),
[`ml/backtests/apply_to_fra_esp.R`](../../../ml/backtests/apply_to_fra_esp.R).

---

## Match-level postmortem

*(Google SRE five-question shape — blameless: causes are described as evidence gaps or model
limitations, not carelessness.)*

**What happened?** 10 wins, 3 losses, +138.32 RBP — a strong result, driven disproportionately by two
large wins (Q10 Spain SOT +28.23, Q9 Spain advance +26.73) that both came from deliberately overriding
the market-priority default, plus a large win (Q3 Yamal +35.62) from correctly trusting a personal-form
drought over the crowd. The three losses were smaller in magnitude and concentrated in exactly the areas
flagged as higher-risk before kickoff: one deliberate market override that didn't pay off (Q8 Mbappé
-12.48), one high-conviction market-anchored number that still missed (Q13 France SOT -11.98), and one
unaided heuristic on a question with no market to lean on (Q14 first-sub -10.64).

**Why did it happen?** The two big wins from overriding the market share a specific, checkable
explanation: both were about Spain's output specifically, and Spain significantly underperformed its own
recent-form and market-implied attacking numbers (2 SOT against a market expecting ~5, and advancing
despite the market slightly favoring France). The pure model and the shadow-tested GLMM were, in this
specific instance, better calibrated to a below-form Spain than a market that hadn't fully priced it in
yet. The one loss on the same kind of decision (Q8, Mbappé) has the opposite explanation — France's attack
was even worse than Spain's, and personal-form conviction on Mbappé specifically didn't anticipate that.

**How did we respond?** Every flagged divergence was decided *before* kickoff and logged as a deliberate,
bounded test (per decisions 0001/0002), not an ad hoc in-the-moment call. That discipline is why this
match's results are genuinely informative rather than just noise — each divergence has a clear before/after
record to grade.

**What did we learn?** (1) The shadow-tested SOT/corners model's first live test against a real market was
a clear win, on exactly the family it was built for — real, if singular, evidence it may eventually clear
the bar in decision 0002. (2) The Mbappé loss is a second live confirmation of the standing caution against
upward deviation from a liquid market on personal-form conviction alone — that caution remains justified.
(3) France's entire attacking output was overestimated by every method available — market, crowd, and both
of our models — a reminder that a below-form performance from a strong team is a real risk case no single
method here currently protects against well.

**What will we change?** Keep the GLMM in shadow mode (per decision 0002) rather than promoting it after
one win — accumulate more live comparisons, starting with England vs Argentina (2026-07-15), for which the
market-fetch tooling built this week ([`bot/fetch_team_prop_markets.py`](../../../bot/fetch_team_prop_markets.py)) is already primed and has already
pulled an initial market snapshot. Do not treat this match's mixed 2-1 record on flagged divergences as
settling the market-vs-model question either way.

---

## Sources / artifacts

All paths relative to `sportspredict_research/` unless noted.

**Match data & submission record** (all in `matches/France Vs Spain (Jul.14.26)/`):
[`01_match_and_markets.json`](<../../../matches/France Vs Spain (Jul.14.26)/01_match_and_markets.json>),
[`02_elo_current_ratings.json`](<../../../matches/France Vs Spain (Jul.14.26)/02_elo_current_ratings.json>),
[`03_model_derivations.json`](<../../../matches/France Vs Spain (Jul.14.26)/03_model_derivations.json>),
[`04_rules_applied.json`](<../../../matches/France Vs Spain (Jul.14.26)/04_rules_applied.json>),
[`05_estimates.json`](<../../../matches/France Vs Spain (Jul.14.26)/05_estimates.json>),
[`09_smarkets_markets_raw.json`](<../../../matches/France Vs Spain (Jul.14.26)/09_smarkets_markets_raw.json>),
[`09_smarkets_quotes_processed.json`](<../../../matches/France Vs Spain (Jul.14.26)/09_smarkets_quotes_processed.json>),
[`10_espn_form.json`](<../../../matches/France Vs Spain (Jul.14.26)/10_espn_form.json>),
[`10_espn_form_supplement.json`](<../../../matches/France Vs Spain (Jul.14.26)/10_espn_form_supplement.json>),
[`11_simulation_results.json`](<../../../matches/France Vs Spain (Jul.14.26)/11_simulation_results.json>),
[`12_ml_predictions.csv`](<../../../matches/France Vs Spain (Jul.14.26)/12_ml_predictions.csv>),
[`13_ml_vs_market_vs_submitted_comparison.md`](<../../../matches/France Vs Spain (Jul.14.26)/13_ml_vs_market_vs_submitted_comparison.md>),
[`14_actual_submission.json`](<../../../matches/France Vs Spain (Jul.14.26)/14_actual_submission.json>),
[`espn_raw/espn_FRA_ESP_sf_760514_FINAL.json`](<../../../matches/France Vs Spain (Jul.14.26)/espn_raw/espn_FRA_ESP_sf_760514_FINAL.json>).

**Fetch/build scripts:**
[`bot/fetch_markets.py`](../../../bot/fetch_markets.py), [`bot/fetch_fra_esp_smarkets.py`](../../../bot/fetch_fra_esp_smarkets.py), [`bot/fetch_team_prop_markets.py`](../../../bot/fetch_team_prop_markets.py),
[`bot/compile_fra_esp_espn_form.py`](../../../bot/compile_fra_esp_espn_form.py), [`bot/simulate_fra_esp_sf.py`](../../../bot/simulate_fra_esp_sf.py),
[`data/processed/build_espn_panel.py`](../../../data/processed/build_espn_panel.py), [`data/processed/fetch_all_raw_events.py`](../../../data/processed/fetch_all_raw_events.py),
[`datasets/build_statsbomb_panel.py`](../../../datasets/build_statsbomb_panel.py), [`datasets/build_unified_team_match_panel.R`](../../../datasets/build_unified_team_match_panel.R),
[`ml/backtests/build_full_tournament_pit_elo.py`](../../../ml/backtests/build_full_tournament_pit_elo.py), [`ml/backtests/add_pit_elo_to_unified_panel.py`](../../../ml/backtests/add_pit_elo_to_unified_panel.py).

**Modeling / backtesting:**
[`model/dixon_coles.py`](../../../model/dixon_coles.py), [`data/processed/poisson_goals_coefs.json`](../../../data/processed/poisson_goals_coefs.json),
[`ml/backtests/lib_hierarchical_backtest.R`](../../../ml/backtests/lib_hierarchical_backtest.R), [`ml/backtests/run_all_family_backtests.R`](../../../ml/backtests/run_all_family_backtests.R),
[`ml/backtests/apply_to_fra_esp.R`](../../../ml/backtests/apply_to_fra_esp.R), [`ml/backtests/walk_forward_first_sub_backtest.py`](../../../ml/backtests/walk_forward_first_sub_backtest.py),
[`ml/backtests/walk_forward_cards_referee_backtest.R`](../../../ml/backtests/walk_forward_cards_referee_backtest.R), [`ml/backtests/blend_market_glmm.py`](../../../ml/backtests/blend_market_glmm.py),
[`ml/backtests/build_rare_event_panels.py`](../../../ml/backtests/build_rare_event_panels.py), [`ml/backtests/sot_vs_market_comparison.py`](../../../ml/backtests/sot_vs_market_comparison.py).

**Pre-registrations (methodology committed before results were seen):**
[`ml/backtests/PREREGISTRATION_sot_hierarchical_backtest.md`](../../../ml/backtests/PREREGISTRATION_sot_hierarchical_backtest.md),
[`ml/backtests/PREREGISTRATION_cards_corners_offsides_and_combined.md`](../../../ml/backtests/PREREGISTRATION_cards_corners_offsides_and_combined.md),
[`ml/backtests/PREREGISTRATION_elo_level_refinement.md`](../../../ml/backtests/PREREGISTRATION_elo_level_refinement.md),
[`ml/backtests/PREREGISTRATION_cards_referee_fouls_stage.md`](../../../ml/backtests/PREREGISTRATION_cards_referee_fouls_stage.md),
[`ml/backtests/PREREGISTRATION_q14_first_sub_race.md`](../../../ml/backtests/PREREGISTRATION_q14_first_sub_race.md).

**External research:**
[`ML_MODEL_BUILD_RESEARCH_2026-07-13.md`](../../../ML_MODEL_BUILD_RESEARCH_2026-07-13.md), [`BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md`](../../../BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md).

**Live data sources:** Smarkets v3 API (`api.smarkets.com/v3`, event 45192700), ESPN soccer API
(`site.api.espn.com`, event 760514), `play.sportspredict.com` (final RBP/settlement figures).