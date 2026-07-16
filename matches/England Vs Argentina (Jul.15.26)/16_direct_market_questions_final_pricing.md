# England vs Argentina (Jul 15 26, Semifinal) — Final Pricing for the 7 DIRECT-Market Questions

Source quotes: `10_smarkets_quotes_processed.json` (bid/offer/mid already computed there; mids independently
re-verified below). Convention: fair mid = (bid+offer)/2, the same convention used throughout this match's
research and consistent with how every prior DIRECT-tier question in this project has been priced (RULE2 —
"if a verified market exists for a prop, submit at market price undeviated").

All joins below are on match_id / team name / player name, never on question position or Q-number.

## 1. The seven numbers

| Q | Question | Market leg | Bid | Offer | Mid | Spread | Submit |
|---|---|---|---|---|---|---|---|
| Q2 | England advance to final | `To_qualify` England | 0.5405 | 0.5495 | 0.5450 | 0.90pp | **0.55** |
| Q3 | Penalty kick awarded | `Penalty_to_be_awarded` Yes | 0.2667 | 0.3175 | 0.2921 | 5.08pp | **0.29** |
| Q11 | Harry Kane scores | `Anytime_goalscorer` Kane | 0.3571 | 0.3623 | 0.3597 | 0.52pp | **0.36** |
| Q12 | 10+ combined corners | `OU9.5_corners` Over | 0.2041 | 0.2941 | 0.2491 | 9.00pp | **0.25** |
| Q13 | England leads at HT | `Half_time_result` England | 0.2703 | 0.2778 | 0.2741 | 0.75pp | **0.27** |
| Q14 | Argentina 2+ goals | `Argentina_OU1.5_goals` Over | 0.2941 | 0.3030 | 0.2985 | 0.89pp | **0.30** |
| Q15 | Bellingham scores or assists | `Score_or_assist` Bellingham | 0.2703 | 0.3333 | 0.3018 | 6.30pp | **0.30** |

Spread ranking, tightest to widest: **Q11 (0.52pp) < Q13 (0.75pp) < Q14 (0.89pp) < Q2 (0.90pp) < Q3 (5.08pp) <
Q15 (6.30pp) < Q12 (9.00pp)**.

**Correction to the task framing:** the brief characterized Q15's Bellingham book as tight/liquid "like Q13's HT
result." That's not what the actual quotes show — Q15's spread (6.30pp) is *wider* than Q3's penalty market
(5.08pp), the one explicitly flagged as the wide/less-trustworthy one. Q15 is genuinely two-sided (both a real
bid and offer, unlike the Messi/Álvarez one-sided situation), so RULE2's "trust the liquid market" default still
applies — but it should be filed alongside Q3 as a wider, thinner book, not grouped with Q13/Q14's near-1pp
spreads. This doesn't change the submitted number (still the raw mid, per the no-deviation instruction below);
it changes how much confidence to place in it if anything moves before kickoff.

## 2. Per-question notes

**Q2 — England advance to final (0.55).** `To_qualify` is DIRECT-tier and has been priced at the raw mid
(rounded to 2dp) in every comparable case this project has run — Mexico_vs_England ("advance to QF," mid 0.5277
→ submitted 0.53), Brazil_vs_Norway (mid 0.6993 → 0.70), Argentina_vs_Switzerland ("advance to SF" → 0.77). Same
treatment here. Spread is tight (0.90pp) — a well-priced book. See §3 for the RULE14 consistency check on this
number.

**Q3 — Penalty awarded (0.29).** 5.08pp spread — wide relative to the other tight books tonight, so treated with
less confidence than Q13/Q14, but still the best available signal; no domain reason to override it (this project
has never built or validated a standalone penalty-rate model). Submit the mid as-is.

**Q11 — Kane scores (0.36).** Tightest book of the seven (0.52pp) — Smarkets is very confident here. Per RULE2
and the instruction to treat this like the Bellingham case rather than the Messi/Álvarez one-sided situation:
default is to trust the market close to raw and explicitly *not* build a reason to push it upward on
reputation/current-tournament-form grounds — that is exactly the shape of the Mbappé loss (France vs Spain,
2026-07-14: submitted 0.60 vs a 0.44 market mid on personal-form conviction, lost -12.48, the second live
confirmation of the RULE17 retirement pattern: upward conviction departures from a tight liquid market on a
big-name striker's reputation lose). Submitted at raw mid, no adjustment.

One relevant, imperfect precedent found in the historical record: in Mexico vs England (R16, 2026-07-06), Kane's
own goalscorer market (`Anytime_goalscorer`, PLAYER_LIQUID tier) had a mid of 0.3623 — almost identical to
tonight's 0.3597. That time the submission nudged slightly *above* market to 0.38 (deliberately, to avoid
repeating an earlier "opponent plays defensively" over-suppression), Kane did score, and the crowd's still-higher
0.46 ended up closer, so the submission still lost -12.70 beat_crowd=false. This is a single data point (n=1),
not strong enough to justify moving off market on its own, and moving toward the crowd here would repeat the
exact upward-conviction move the Mbappé lesson warns against — so it is logged as context, not acted on. Number
stays at the raw 0.36 mid.

**Q12 — 10+ combined corners (0.25).** This is the one that most resembles the France vs Spain Q13 loss on the
surface (a discrete count crossing a threshold), and it has the widest spread of the seven (9.00pp) — genuinely
the least liquid market tonight. But the mechanism of that prior loss doesn't actually transfer: FRA-ESP's Q13
("France 4+ SOT") was RULE2_DERIVED — no market existed for that exact line, so a threshold was inferred one step
away from the nearest real quote and submitted at the team's highest conviction of the night (0.72). Q12 tonight
is not derived — `OU9.5_corners` is a literal, already-quoted, two-sided Smarkets market for exactly this
question, with both a real bid and offer on both sides. The correct response to a wide spread on a real market is
not to manufacture extra conviction on top of it (which is what sank FRA-ESP's Q13) — it's to take the mid as
given and not push it further in either direction. Submitted at the raw mid (0.2491 → 0.25), flagged as the
lowest-confidence number of the seven purely because of the spread, not overridden.

**Q13 — England leads at HT (0.27).** Second-tightest book (0.75pp). See §4 for the strong knockout-stage
historical record on this exact question family.

**Q14 — Argentina 2+ goals (0.30).** Tight book (0.89pp), team-level goals-total threshold — see §4 for
knockout-stage history on this family, which is strongly positive.

**Q15 — Bellingham scores or assists (0.30).** Genuinely two-sided (bid AND offer both present) so RULE2 still
applies as the default, but per §1 this is the second-widest book tonight (6.30pp), wider than the penalty
market. Same logic as Kane: no upward departure on reputation/current-tournament-form grounds. Submitted at raw
mid.

## 3. RULE14 internal consistency check — Q2 vs Full_time_result

RULE14 requires P(advance to final) to be consistent with the regulation-time win probability implied by other
markets, given a plausible extra-time/penalties adjustment. From `10_smarkets_quotes_processed.json`,
`Full_time_result`: England mid 0.3584, Draw mid 0.3306, Argentina mid 0.3101 (sums to 0.9991, ~0.1% overround —
a tight, well-formed book).

- Trivial bound: `To_qualify` England (0.5450) ≥ `Full_time_result` England (0.3584). **Passes** — advancing
  includes winning in regulation plus the draw→ET/pens path, so it must be strictly larger, and it is.
- Magnitude check: the gap (0.5450 − 0.3584 = 0.1866) must be explained by `Draw_prob × P(England wins ET/pens |
  draw)`. Solving: 0.1866 / 0.3306 = **0.5644** — the qualify price implicitly assumes England wins the
  extra-time/penalty decider ~56.4% of the time it goes to a draw.
- Cross-check against the regulation-time strength ratio: England/(England+Argentina) = 0.3584/(0.3584+0.3101) =
  **0.5361**. The two numbers are in the same direction (England favored) and reasonably close (56.4% implied
  ET/pens edge vs. 53.6% regulation-time strength ratio) — a ~2.8pp gap. This is not the kind of discrepancy that
  should trigger an override; a modest live-market ET/pens edge above the raw regulation ratio is plausible
  (bench depth, penalty-taking personnel, momentum effects extra-time markets can price that a two-outcome
  regulation split doesn't capture).

**Verdict: no RULE14 flag.** The `To_qualify` price is internally consistent with `Full_time_result`, submit as
quoted (0.55).

## 4. Knockout-stage (R16+) historical calibration check, by market type

Scope: every match in `matches/` whose *own* stage is Round of 16 or later (excludes R32 and group-stage
matches, and excludes historical files that only reference an opponent's *past* R32/group games). Confirmed R16+
matches with settled results: Mexico_vs_England (R16), Portugal_vs_Spain (R16), Brazil_vs_Norway (R16),
Canada_vs_Morocco (R16), France_vs_Paraguay (R16), Norway_vs_England (QF), Argentina_vs_Switzerland (QF),
France_vs_Morocco (QF), France Vs Spain Jul.14.26 (SF). (Switzerland_vs_Colombia and USA_vs_Belgium are also R16
but their `06_post_match_results.json` files were not present/populated in this repo, so they contribute no
question-level data here.)

**Half-time-result / tied-at-HT questions (7 instances, all R16–QF):** Mexico_vs_England +2.36, Brazil_vs_Norway
+5.44, Canada_vs_Morocco +6.68, France_vs_Paraguay +4.56, Norway_vs_England +1.28, Argentina_vs_Switzerland
+7.93, France_vs_Morocco +7.39. **7/7 beat crowd (100%), net +35.64, avg +5.09.** This is the strongest and most
consistent DIRECT-tier family found anywhere in the knockout-stage record — directly relevant to Q13 tonight, and
it argues for exactly what's already being done: trust the tight market mid without hedging.

**FTR / advance-to-next-round questions (8 instances):** Mexico_vs_England −0.51, Portugal_vs_Spain +6.92,
Brazil_vs_Norway −5.06 (Brazil lost as ~70% favorite — a real upset, not a pricing failure), Canada_vs_Morocco
+6.21, France_vs_Paraguay +5.54, Norway_vs_England +12.98, Argentina_vs_Switzerland +5.65, France_vs_Morocco
−8.75. **5/8 beat crowd (62.5%), net +22.98.** Lower beat-rate than HT-result, but every loss traces to a
genuine upset or near-upset materializing at the priced probability, not a systematic mispricing — i.e. the
markets were calibrated, variance just showed up. One directly comparable case worth flagging: France vs Spain's
internal "Spain advance to final" question (2026-07-14, the true SF-stage analogue of tonight's Q2) deliberately
overrode a 0.41 liquid market anchor with a 0.53 pure-model number and won (+26.73) — but the project's own
write-up on that result calls it "one mixed data point, not proof either posture is generally right," and no
comparably strong overriding model exists for tonight's Q2. Combined with the RULE14 pass in §3, this argues for
staying with the market on Q2.

**Anytime-goalscorer questions (10 instances):** Portugal_vs_Spain (Ronaldo) +13.92, Brazil_vs_Norway (Vinícius)
+11.17, Brazil_vs_Norway (Haaland) +19.38, Canada_vs_Morocco (David) +13.93, Canada_vs_Morocco (Saibari) +12.83,
France_vs_Paraguay (Mbappé) +7.51, Norway_vs_England (Haaland) +22.38, France_vs_Morocco (Mbappé) +1.81, plus
the two Mexico_vs_England losses: Kane −12.70 and Jiménez −5.22. **8/10 beat crowd (80%), net +85.01, avg
+8.50.** Strong family overall; the only losses were both in the same match (Mexico_vs_England) and both cases
where a below-crowd number was submitted and the player then scored — see the Q11 note in §2 for the specific
Kane precedent.

**Team-level goals-total O/U questions (8 instances, includes the same family as Q14):** Mexico_vs_England
("2 or fewer total goals") −8.31, Portugal_vs_Spain +6.79, Brazil_vs_Norway +10.03, Canada_vs_Morocco +9.63,
France_vs_Paraguay +7.63, Norway_vs_England +14.09, Argentina_vs_Switzerland +15.07, France_vs_Morocco +27.10.
**7/8 beat crowd (87.5%), net +82.03.** Strongly positive — good precedent for Q14.

**Corners questions (11 instances, team-specific O/U or head-to-head, not combined-total):** Mexico_vs_England
−0.17, Portugal_vs_Spain +3.97, Brazil_vs_Norway +10.40, Canada_vs_Morocco +12.98, France_vs_Paraguay +7.28,
Norway_vs_England (×3) +3.86/+15.24/+0.40, Argentina_vs_Switzerland (×2) +5.10/+26.71, France_vs_Morocco +13.03.
**10/11 beat crowd (90.9%), net +98.80.** No exact "combined total corners" precedent exists in the history
(all past corners questions were team-specific), so this doesn't transfer directly to Q12's `OU9.5_corners`
format, but it does confirm DIRECT-tier corners markets in general have been reliable in the knockout stage.

**Penalty-awarded questions:** only one exact match of Q3's pure "penalty kick awarded" (not compounded with a
red card) at R16+ — France_vs_Paraguay (R16): submitted 0.28 vs crowd 0.27, resolved YES, +5.31, beat crowd.
Compound "penalty OR red card" questions at R16+ (4 instances): Argentina_vs_Switzerland +24.41,
Canada_vs_Morocco +0.77, France_vs_Morocco +11.16, Norway_vs_England −0.50 → 3/4 beat crowd, net +35.84. Thin
sample, but no sign of a knockout-specific penalty-market bias in either direction.

**Overall finding: no discernible knockout-stage-specific bias for any of these four/five market families.**
Every category above is net positive at R16+ and beats its all-stages equivalent rate from the
`KNOCKOUT_STAGE_PRICING_DEEP_DIVE.md` R32 audit (DIRECT overall 73.5% beat-crowd) or is in the same range. The
one real pattern that recurs is not stage-specific at all — it's the same "don't manufacture upward conviction
on a liquid market for a big-name striker" lesson already documented for Mbappé, now with a second, smaller echo
in Kane's Mexico_vs_England result. That's the one live risk carried into tonight's Q11/Q15, and it's handled by
simply not doing it.

## 5. Summary

All seven numbers submitted at (or within rounding of) the raw bid/offer mid, per RULE2. No RULE14 flags raised
(Q2 checked explicitly, passes). No knockout-stage-specific mispricing pattern found for HT-result, FTR/advance,
goalscorer, corners, or goals-total DIRECT markets — all five families are net positive in the R16+ record, most
strongly HT-result (100% beat-crowd, n=7) and corners (90.9%, n=10). The one flag worth carrying forward is
non-numeric: Q15's spread is wider than the task brief assumed (6.30pp, not tight like Q13) and Q12 is the
thinnest book tonight (9.00pp) — both are logged as lower-confidence but not overridden, consistent with RULE2
and the Mbappé/Kane lesson against manufacturing conviction against a real two-sided price.
