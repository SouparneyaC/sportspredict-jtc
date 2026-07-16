# Q6 (8+ combined SOT) and Q9 (Argentina more corners than England) — final pricing

England vs Argentina SF, 2026-07-15. Written before submission, with full derivation and the
extra high-stakes-knockout sanity check requested. Both questions are regulation-only (90' +
stoppage) per the exact platform wording:

- Q6: "Will there be 8 or more total shots on target (both teams combined) in regulation?"
- Q9: "Will Argentina have more corner kicks than England in regulation?"

Join safety: all cross-file joins below use `match_id` or `team_name`, never row position or
Q-number, per standing project rule.

---

## Q6: 8+ combined SOT — derivation

### Why not the fitted-model combination
`topics/shots-on-target/combined_sot_backtest_results.csv` (sum of two independently-fit
hierarchical-GLMM Poisson lambdas, convolved assuming independence) already failed its own
preregistered backtest: t=0.022, one-sided p=0.491 vs baseline — no edge at all, attributed in
`ml/backtests/PREREGISTRATION_cards_corners_offsides_and_combined.md` to positive within-match
SOT correlation breaking the independence assumption. That result rules out using the *fitted
GLMM* combination tonight. It does not, by itself, rule out a *market-derived* combination — see
the correlation check below, which tests the independence assumption directly rather than
inheriting the old verdict by analogy.

### Method (RULE2_DERIVED, same pattern as France vs Spain Q15 "France 4+ SOT")
Both England and Argentina have tight, genuinely two-sided O/U 3.5 SOT books
(`10_smarkets_quotes_processed.json`):

| Market | Bid | Offer | Mid (Over 3.5, i.e. P(SOT≥4)) |
|---|---|---|---|
| `England_SOT_OU3.5` | 0.5000 | 0.5814 | 0.5407 |
| `Argentina_SOT_OU3.5` | 0.4202 | 0.5000 | 0.4601 |

Solving each team's Poisson lambda so that P(X≥4) matches the mid price:

- lambda_England = 3.870 (check: P(≥4) = 0.5407 ✓)
- lambda_Argentina = 3.485 (check: P(≥4) = 0.4601 ✓)
- lambda_combined = 7.355
- **P(combined SOT ≥ 8) = 1 − Poisson_CDF(7; 7.355) = 0.4540**

Using the bid/offer spread on both legs instead of mid gives a band of 0.398 (low-low) to 0.512
(high-high) — a genuinely wide ~11pp range for a book this notionally "tight," which is itself a
useful reminder of how much residual uncertainty a per-team line leaves once composed.

### Testing the independence assumption directly (not inherited by analogy)
Rather than assume the old SOT-combined failure transfers, I measured the actual within-match
correlation between the two teams' SOT counts directly, using `data/processed/unified_team_match_
panel_with_pit_elo.csv` (joined on `match_id`):

- Full historical panel (WC2018+2022+2026, n=228 team-match pairs / 114 matches): SOT correlation
  = **−0.269**
- WC2026-only (n=100, `data_source == espn_boxscore`, the exact sample the original backtest
  used): SOT correlation = **−0.317**

This is the opposite sign from what the project's write-ups assumed ("open matches elevate both
teams' SOT together" — plausible reasoning, explicitly flagged in the prereg doc as "not directly
re-verified"). Directly re-verified here: the real relationship is negative, plausibly because shot
volume is somewhat zero-sum within a 90-minute match — one team's territorial/attacking dominance
often comes at the other's expense, not both teams' expense together.

Given the correlation is negative, not positive, I ran a Gaussian-copula Monte Carlo (2M draws) at
the marginals above across a range of rho including the measured value, to see how much this
actually moves P(combined ≥ 8):

| rho | P(combined SOT ≥ 8) |
|---|---|
| 0.00 (independence) | 0.4546 |
| −0.10 | 0.4540 |
| −0.20 | 0.4541 |
| −0.32 (≈ measured) | 0.4538 |
| −0.40 | 0.4540 |

**The correlation direction/magnitude barely moves the answer** (0.4538–0.4546 across the whole
range) — because the threshold (8) sits almost exactly at the combined mean (7.355), and
correlation mainly reshapes the tails, not the region right around the mean. This is a genuinely
useful, reassuring finding: the mechanism that broke the old fitted-GLMM combination isn't a live
risk for tonight's market-derived number, for this specific threshold.

### Sanity check against real high-stakes knockout matches (small n, directional only)
Pulled shots-on-target directly from StatsBomb event data for the 6 semifinals + 3 finals across
Euro 2024, Copa America 2024, and AFCON 2023 (joined on `match_id` from each competition's
`matches/{comp_id}/{season_id}.json`, SOT = shot outcome in {Goal, Saved, Saved To Post}, same
definition as this project's own extraction script):

| Match | Combined SOT |
|---|---|
| Netherlands 1–2 England (Euro24 SF) | 8 |
| Spain 2–1 England (Euro24 Final) | 9 |
| Spain 2–1 France (Euro24 SF) | 5 |
| Argentina 1–0 Colombia (Copa24 Final) | 9 |
| Uruguay 0–1 Colombia (Copa24 SF) | 5 |
| Argentina 2–0 Canada (Copa24 SF) | 5 |
| Nigeria 1–2 Côte d'Ivoire (AFCON23 Final) | 8 |
| Côte d'Ivoire 1–0 Congo DR (AFCON23 SF) | 3 |
| Nigeria 1–1 South Africa (AFCON23 SF) | 11 |

n=9, mean combined SOT = 7.0, **empirical P(combined ≥ 8) = 5/9 = 0.556**. Also checked the
broader corpora: WC2026-only 100-match backtest sample gives 0.590; the full WC2018+2022+2026
panel gives 0.548. All three empirical checks — three genuinely different corpora — sit ~10pp
above the market-derived 0.454, consistently in the same direction.

### Final call: stay close to market math, do not chase the empirical base rate up
Tempting as it is to nudge toward the ~0.55 empirical cluster, this project has already paid for
that exact move: `RULE17_RETIRED_NO_UPWARD_BLEND` was retired specifically because upward blends
away from a liquid market toward outside/empirical evidence went 0-for-5 (−155.64 RBP) before
being retired, and the France vs Spain Q12 note explicitly reused that caution ("upward blends
from thin markets are 0-for-5... stay at derived market, tiny downward regime tilt"). Both
England's and Argentina's SOT lines tonight are tight, live, two-sided books — the single most
relevant piece of information for tonight specifically, more relevant than a 9-match cross-era
historical base rate. The correlation check above also removes the one reason I might have
justified moving off the market math (the old "positive correlation broke it" story doesn't
apply here — measured correlation is negative and near-inert at this threshold anyway).

Also invoking the France vs Spain lesson directly: "France 4+ SOT" was this project's costliest
loss (−11.98 RBP) from pushing a market-derived count-stat number toward false certainty near a
threshold. Q6 is structurally the same shape. The good news here is that 0.454 is already nowhere
near false certainty — it's close to a coin flip — so there's no rounding-toward-conviction risk
to correct for in the first place.

**Final Q6 submission: 0.45** (rounded from 0.4540, the market-derived, correlation-checked
number; empirical corpus checks logged as a directional sanity check that did not move the price,
consistent with this project's own rule against upward blends off a liquid market).

---

## Q9: Argentina more corners than England — reconciliation

### The two anchors
1. **Model (validated, shadow-deployment number):** `12_corners_comparison_backtest_summary.md` /
   `ml/backtests/PREREGISTRATION_corners_comparison.md` — walk-forward Skellam composition of the
   already-separately-passed per-team corners GLMM, n=98, Brier CI [0.0134, 0.0714] entirely above
   zero (p=0.019 vs baseline, p=0.032 vs 50/50). Live application (PIT elo England 2172.28,
   Argentina 2253.31, refit on all pre-2026-07-15 data): lambda_England=4.191, lambda_
   Argentina=4.556, **P(Argentina > England) = 0.4805**, P(tie)=0.1360, P(England>Argentina)=0.3835.
2. **Market (`Corners_handicap_ENGm0.5_ARGp0.5`):** England −0.5 mid 0.5175 (= P(England strictly
   more)), Argentina +0.5 mid 0.4858 (= P(Argentina ties-or-leads) — settles ties to Argentina, a
   different question than Q9's strict "more than").

### First-order fix: strip the tie mismatch out of the market number
The flagged mismatch (ties settle to Argentina in the market, but not in Q9) is real but by
itself only accounts for part of the gap. Back-solving the market's own implied split: total
corners lambda from `OU9.5_corners` (Under 9.5 mid 0.749 → Poisson total lambda T=7.735), then
solving the England/Argentina split fraction that reproduces the England −0.5 mid of 0.5175 via a
Skellam construction:

- Market-implied lambda_England = 4.184 (vs model's 4.191 — **essentially identical**)
- Market-implied lambda_Argentina = 3.551 (vs model's 4.556 — **a full corner/match apart**)
- Market-implied: P(England>Argentina)=0.5175, P(tie)=0.1425, **P(Argentina>England)=0.3401**

So the real disagreement isn't about ties, and it isn't about England's corner output — model and
market agree on England almost exactly. It's entirely about **Argentina's** expected corners:
model says 4.556, market says 3.551. That's the ~14pp gap in the Q9-relevant number (0.4805 vs
0.3401), not a settlement-rule artifact.

### Why the two disagree: this traces to Elo vs. the live match markets, not the composition method
The corners-comparison Skellam *method* is not the suspect here — I stress-tested it the same way
as Q6, running a Gaussian-copula Monte Carlo at the model's own lambdas (4.191/4.556) across the
same range of correlation as measured directly on the panel (corners correlation: −0.075 full
panel espn/statsbomb-none-filtered check is close to the SOT one; espn_boxscore/WC2026-only
corners correlation was measured at −0.336, see script output). Result: P(Argentina>England) moves
from 0.4809 (rho=0) to only 0.4836 (rho=−0.32) — a 0.3pp shift. The composition method is not
where the disagreement lives.

It lives upstream, in the per-team lambda inputs, which for the corners GLMM are driven
substantially by PIT elo_diff. Argentina enters tonight with a real, correctly-computed Elo edge
(2253.31 vs England's 2172.28, +81.04 — verified point-in-time, not the stale/frozen rating; see
`02_elo_current_ratings.json`). But the match-outcome markets flatly disagree with that read:
`To_qualify` has England 0.545 vs Argentina 0.457; `Full_time_result` has England 0.358 vs
Argentina 0.310. **The live market thinks England is the better team tonight; Elo thinks
Argentina is.** The corners split inherits that same disagreement, because it's driven by the same
covariate.

There's a plausible substantive reason for this beyond noise: Argentina's Elo gain has come
through high-scoring, leaky matches (group stage 3-0/2-0/3-1, then 3-2 AET/3-2/3-1 in the knockout
rounds — 11 goals conceded across 6 games, ~1.83/game) while England's has come through a much
tighter defensive record (6 goals conceded across 6 games, 1.0/game, including a 0-0). Elo (built
mostly off results and margins) rewards Argentina's attacking output; a market pricing the actual
matchup can also price defensive solidity, fatigue from Argentina's extra-time R32 game, and
squad-specific information Elo doesn't see. None of this proves the market is right and Elo is
wrong — but it is a coherent story for why they'd diverge in exactly this direction, which makes
the disagreement more credible than "one of these two numbers must just be noise."

### Sanity check from the high-stakes knockout corpus (n=9, directional only)
Corner ties in the 9 SF/Final matches pulled above: 2/9 = 22.2%, vs 13.6% in the model's own
England-Argentina Skellam split, 10.0% in the WC2026-only 100-match backtest sample, and 7.5% in
the full 228-pair historical panel. Directionally consistent with a "high-stakes knockout matches
run tighter/more cagey, closer scorelines" story — but n=9 means one match flips this by 11pp, so
this is logged as a weak, non-powered signal, not a correction applied to the number. (For
whatever it's worth in the other direction: the same correlation-based reasoning that predicts
*lower* ties under negative correlation, tested above for Q6, would predict the *opposite* of what
this small sample shows — flagging this tension honestly rather than resolving it, since neither
side of it is well-powered enough to lean on.)

### Reconciliation and final call
Both anchors already agree on the qualitative direction — model (0.4805) and market-implied-strict
(0.3401) are both under 0.50, i.e. both say Argentina is not favored to have strictly more corners
than England. The disagreement is about magnitude (near-coin-flip vs. clearly-favoring-England),
not about which side to take. That lowers the stakes of this decision relative to a genuine
direction disagreement.

Per this project's own standing doctrine (`writeups/decisions/0002-shadow-deploy-before-live-
submission.md`) and the most recent live evidence for it — the SOT hierarchical GLMM's +28.23 RBP
win on Spain SOT in France vs Spain, the single biggest win of that match, specifically because it
was a properly preregistered, walk-forward-backtested, shadow-deployed number taken over a
near-coin-flip market — a validated model in exactly this position should not be discarded just
because a market disagrees. The corners-comparison composition clears an even more directly
on-point bar than the SOT case did (built and preregistered specifically for this question shape).

But the disagreement here is large (14pp) and traces to a specific, plausible, unresolved
Elo-vs-market disagreement about which team is actually stronger tonight — something the Q9
backtest validates the *composition method* against, not the *Elo-strength read* itself. That is
a real, distinct source of model risk sitting outside what was actually tested, and it deserves a
real (not token) discount, not a full override.

**Final Q9 submission: 0.44** — roughly a 65/35 blend toward the model (0.65×0.4805 +
0.35×0.3401 ≈ 0.4384, rounded to 0.44). This keeps most of the weight on the validated,
doctrine-endorsed number (consistent with what won big last night) while giving real weight to
the market's own implied read and the coherent defensive-record story for why it might be right,
rather than mechanically submitting either 0.48 or 0.34 outright.

---

## Summary of extra-corpus creative check (both questions)

Euro 2024 (comp 55/season 282), Copa America 2024 (comp 223/season 282), and AFCON 2023 (comp
1267/season 107) — 6 SFs + 3 Finals, n=9, pulled directly from StatsBomb event JSON, joined on
each match's own `match_id` (never by row position):

- Q6 sanity check: empirical P(combined SOT≥8) = 5/9 = 0.556, directionally above the
  market-derived 0.454 (as were the two larger WC-only/historical corpora, 0.59 and 0.548) —
  logged, not acted on, per the RULE17 upward-blend caution.
- Q9 sanity check: corner tie rate 22.2% (2/9) vs the model's assumed 13.6%, a weak signal in
  tension with what the correlation-based reasoning would predict, honestly flagged as
  unresolved given n=9.

Both checks are treated as directional sanity checks against a genuinely independent (different
tournaments, different eras) but tiny sample — not new backtests with their own statistical bar.
