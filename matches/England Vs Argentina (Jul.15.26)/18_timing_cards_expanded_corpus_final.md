# Q5, Q7, Q8, Q10 — expanded high-stakes corpus (Euro 2024 + Copa America 2024 + AFCON 2023) and final numbers

Starting point / methodology template: [`13_timing_and_compound_events_backtest_summary.md`](13_timing_and_compound_events_backtest_summary.md)
(WC2026-only, n=100, ESPN-sourced). This piece extends that backtest with a genuinely new data
source — the local StatsBomb open-data mirror's full event-level coverage of three major
tournaments never used in any prior backtest in this project — and revises tonight's four live
numbers accordingly.

Scripts: [`18_statsbomb_expanded_panel.py`](18_statsbomb_expanded_panel.py) (builds the new
135-match StatsBomb panel) + [`18_pooled_walk_forward_backtest.py`](18_pooled_walk_forward_backtest.py)
(pools it with the existing WC2026 script and re-runs the same walk-forward protocol).
Outputs: [`18_statsbomb_expanded_panel.csv`](18_statsbomb_expanded_panel.csv),
[`18_pooled_walk_forward_results.csv`](18_pooled_walk_forward_results.csv),
[`18_pooled_walk_forward_summary.csv`](18_pooled_walk_forward_summary.csv).

## 0. Bottom line

| Question | Old (WC2026-only) | New final number | Verdict |
|---|---|---|---|
| Q5 goal-in-each-half | 0.580 | **0.52** | Still no real predictive edge over 50/50 — expanded corpus *reinforces*, not weakens, that conclusion; central estimate revised down |
| Q7 stoppage-time goal | 0.360 | **0.31** | Genuine edge, independently replicated in the new corpus — real, supported downward revision |
| Q8 both-teams-carded | 0.550 | **0.55 (unchanged)** | Expanded corpus does NOT earn a revision once a known cross-source card-measurement gap is accounted for — stays market/base-rate anchored per standing project doctrine |
| Q10 card-before-first-goal | 0.350 | **0.35 (unchanged)** | Same measurement-gap story as Q8, smaller magnitude — no meaningful revision earned |

Two of four numbers move (Q5, Q7); two stay put (Q8, Q10) for a reason that is itself a genuine
finding, not a shrug — see §3.

## 1. Data engineering — the new corpus

Three competitions pulled from `data/external/statsbomb/open-data/data/` (gitignored, read-only
third-party mirror, never modified):

| Competition | competition_id | season_id | Matches | Group | R16 | QF | SF | Final | 3rd place |
|---|---|---|---|---|---|---|---|---|---|
| Euro 2024 | 55 | 282 | 51 | 36 | 8 | 4 | 2 | 1 | — |
| Copa America 2024 | 223 | 282 | 32 | 24 | — | 4 | 2 | 1 | 1 |
| AFCON 2023 | 1267 | 107 | 52 | 36 | 8 | 4 | 2 | 1 | 1 |
| **Total** | | | **135** | **96** | **16** | **12** | **6** | **3** | **2** |

Matches counts confirmed directly against StatsBomb's own `matches/<comp>/<season>.json` files
before doing anything else — no assumption from the task brief was taken on faith.

**Schema, verified directly from a real event file rather than assumed** (per this project's
standing rule): goals are `type.name=="Shot"` with `shot.outcome.name=="Goal"`, plus
`type.name=="Own Goal For"` (its paired `"Own Goal Against"` event is the same instant on the
other team and is not double-counted). Cards carry a `card.name` field in `{"Yellow Card",
"Second Yellow", "Red Card"}` in one of two event types — `Foul Committed` -> `foul_committed.card`
(the common case) or `Bad Behaviour` -> `bad_behaviour.card` (cards with no associated foul event,
e.g. dissent, off-ball violent conduct). Both confirmed by scanning all 135 matches directly; no
other card-name values appear anywhere in the corpus.

**Timing convention** differs from ESPN's and was verified before use: StatsBomb's `minute` field
is cumulative match time (period-2 events continue counting from 45, not reset to 0), confirmed
against a real `Half End` event. Stoppage-time goals are therefore detected as period-1 events with
`minute >= 45` or period-2 events with `minute >= 90` — the standard convention, not ESPN's "+N"
tag (which StatsBomb's schema doesn't have), but measuring the same thing. Regulation scope
(periods 1-2 only) matches every question's own wording, identical to the WC2026 script.

**Ground-truth check** (per this project's standing rule to verify an unfamiliar field against a
known case before trusting it): the Euro 2024 Final (Spain 2-1 England, 2024-07-14) reproduces the
real scoreline and run of play exactly — Nico Williams's opener at StatsBomb minute 46 (real 47'),
Cole Palmer's equalizer at minute 72 (real 73'), Mikel Oyarzabal's winner at minute 85 (real 86') —
StatsBomb's minute running consistently ~1 minute behind the broadcast clock is a known, harmless
convention, not a bug. The four bookings in that match (Kane 24', Olmo 30', Stones 53', Watkins in
second-half stoppage) are all real, checkable cards from that final. Confirmed correct before
trusting the same fields for the other 134 matches.

## 2. Stage-conditioned rates in the new corpus

| Question | Group (n=96) | Knockout-core R16+QF+SF+F (n=37) | SF-or-Final only (n=9) | 3rd place (n=2) |
|---|---|---|---|---|
| Q5 goal-in-each-half | 0.479 | 0.459 | 0.333 | 0.500 |
| Q7 stoppage-time goal | 0.292 | 0.216 | 0.111 | 0.500 |
| Q8 both-teams-carded | 0.740 | 0.838 | 0.778 | 0.500 |
| Q10 card-before-goal | 0.490 | 0.514 | 0.333 | 1.000 |

**Sample-size honesty, stated plainly per the task's own framing**: the SF-or-Final column is
n=9 (6 real semifinals + 3 real finals — Euro 2024 SF×2+Final, Copa America 2024 SF×2+Final,
AFCON 2023 SF×2+Final). This is nowhere near enough for a new statistically powered backtest — a
single upset or a single 5-card brawl swings that column by 11 points — and none of the SF-or-Final
numbers above are used as a standalone pricing input anywhere in this doc. The knockout-core column
(R16+QF+SF+Final, n=37, excluding the 2 third-place playoffs per the task's own literal
definition) is the genuinely useful comparison against group-stage, closer to the n=37-61 range
that supported the Messi high-stakes finding (`14_messi_high_stakes_deep_dive.md`).

Reading the knockout-core column against group: Q5 and Q7 both drop modestly in knockout football
(goals slightly less likely in both halves, stoppage-time goals notably less likely — 0.292 to
0.216). Q8 and Q10 both rise in knockout football (cards up 10 points, card-before-goal up 2
points). Before treating any of this as signal, §3 checks whether it's real or an artifact.

## 3. The critical check: does pooling actually help predict WC2026 matches?

Ran the exact walk-forward protocol from `13_...md` (`MIN_TRAIN=5`, matches sorted by date,
predicted rate = empirical mean of strictly-prior matches only) over the pooled 235-match corpus
(WC2026's 100 + this session's 135). Euro 2024/Copa America 2024/AFCON 2023 all finished well over
a year before WC2026 even started, so folding them in is unambiguously PIT-safe for every WC2026
fold, and strengthens the thin warm-up period for the earliest June 2026 matches.

**Aggregate pooled walk-forward (all 235 predictions, n=228 after warm-up):**

| Question | Brier (pooled WF) | Brier (naive 0.5) | Improvement |
|---|---|---|---|
| Q5 | 0.2599 | 0.2500 | -0.0099 |
| Q7 | 0.2175 | 0.2500 | +0.0325 |
| Q8 | 0.2330 | 0.2500 | +0.0170 |
| Q10 | 0.2510 | 0.2500 | -0.0010 |

Read naively, Q8's aggregate number looks like a new, real edge that didn't exist in the WC2026-only
backtest (+0.0170 here vs -0.0071 there). **This is the load-bearing check that shows that reading
is wrong.** The aggregate mixes two different questions — "does the model predict StatsBomb matches
well" and "does the model predict WC2026 matches well" — and only the second one matters for
pricing tonight. Splitting the same pooled predictions by which corpus the *target* match actually
belongs to:

| Question | WC2026-target Brier (pooled training) | WC2026-target improvement | Original WC2026-only improvement | StatsBomb-target improvement |
|---|---|---|---|---|
| Q5 | 0.2511 | -0.0011 | -0.0005 | -0.0167 |
| Q7 | 0.2360 | +0.0140 | +0.0120 | +0.0469 |
| Q8 | 0.2753 | **-0.0253** | -0.0071 | +0.0501 |
| Q10 | 0.2425 | +0.0075 | +0.0164 | -0.0075 |

This is the honest verdict: **pooling in the StatsBomb cards data makes Q8's WC2026 predictions
measurably worse, not better** (-0.0253 vs the already-weak -0.0071) — the StatsBomb-target column's
strong +0.0501 is StatsBomb matches predicting other StatsBomb matches well (a homogeneous-source
effect), not a transferable signal for tonight. Q10 shows the same direction of contamination on a
smaller scale (edge shrinks from +0.0164 to +0.0075 but stays positive). Q5 and Q7 — the two
questions with no card dependency — are essentially unaffected by pooling (Q5 stays "no edge" at
almost the same magnitude; Q7's edge is preserved and even modestly reinforced), consistent with
goals being a reliably captured "key event" in both ESPN's and StatsBomb's feeds with no known
completeness gap.

**Root cause, checked and confirmed rather than guessed:** this project's own prior work
(`ml/backtests/PREREGISTRATION_cards_corners_offsides_and_combined.md`) already found and
documented an ESPN/StatsBomb measurement ratio for cards of **0.876/0.791x** — ESPN's `keyEvents`
feed systematically records fewer cards than StatsBomb's full event stream for the same underlying
matches (the same class of bug independently found to be a much larger 8.49x for offsides before a
fix). This session's own two-source comparison reproduces that exact direction on a brand-new
corpus: WC2026 (ESPN) averages **2.59 cards/match** across 100 matches vs this StatsBomb pull's
**3.86 cards/match** across 135 matches — a **0.671x** ratio, same direction as the previously
documented figure, if anything a larger gap on this specific set of tournaments. Card counts are
not comparable 1:1 across the two sources, so Q8 and Q10 — both card-presence/card-timing
questions — inherit this confound directly; Q5 and Q7 do not.

**Illustrative correction (approximate, not a validated transform — a linear ratio applied to a
binary outcome rate is a rough sensitivity check, not a rigorous statistical correction, and is
labeled as such):** scaling the StatsBomb both-carded rate by the freshly measured 0.671 ratio,
0.763 x 0.671 = **0.512** — strikingly close to WC2026's own native 0.550. Doing the same for Q10,
0.504 x 0.671 = **0.338** — again close to WC2026's native 0.350. Once the known measurement gap is
roughly priced in, most of the apparent "StatsBomb shows much higher card rates" story evaporates;
it looks like it's mostly explained by StatsBomb recording more cards per match overall (fuller
event coverage), not by these three tournaments' matches genuinely having more cards than WC2026's.

**A second, independent piece of evidence against leaning on the StatsBomb knockout-cards finding:**
StatsBomb's own within-source group-vs-knockout-core comparison shows cards rising with stakes
(0.740 to 0.838). But WC2026's *own* internal group-vs-knockout split (same ESPN measurement
instrument that will resolve tonight's match, so no cross-source confound) shows the **opposite
direction** — group 0.611, knockout (R32+R16+QF, n=28; no completed SF/Final available in this
corpus yet, see limitation below) 0.393. Two same-instrument-internally-valid comparisons pointing
opposite ways is itself the honest result: the "cards rise with stakes" story is not solid enough,
even setting the cross-source issue aside, to justify moving Q8 up.

**Inherited data limitation, noted for transparency, not fixed here (out of this session's scope):**
`data/processed/espn_raw_events/` has no completed France-vs-Spain SF file — the one file matching
that fixture (`espn_FRA_ESP_sf_fixture_760514.json`) is a pre-match "Scheduled" stub with no
`keyEvents`, correctly dropped by both the original script and this one, exactly as
`13_...md` already documented. This means the WC2026-internal knockout comparison above has zero
real semifinals in it (only R32/R16/QF) — a real gap in the underlying corpus, inherited from the
base pipeline, not introduced by this session.

## 4. Per-question final numbers and reasoning

**Q5 — goal in each half.** No card-measurement confound (goals are reliably captured in both
sources, ground-truth-checked). Pooling doesn't help but doesn't hurt WC2026-specific accuracy
either (-0.0011 vs -0.0005, both essentially zero). The new corpus (n=135, rate 0.474) sits well
below WC2026's own 0.580 across every stage bucket (group 0.479, knockout-core 0.459), a consistent
downward signal, not noise from one stage bucket. Pooled naive rate across all 235 matches: 0.519.
**Revised to 0.52.** Still explicitly not a "real edge" question — the Brier improvement over naive
0.5 stays negative in both the WC2026-only and pooled walk-forwards. The revision is a central-
estimate correction using a bigger, still-honestly-near-50/50 sample, not a new confidence claim.

**Q7 — stoppage-time goal.** No card-measurement confound. WC2026-specific accuracy is unaffected
by pooling (+0.0140 vs +0.0120) and the StatsBomb-only walk-forward shows an even larger edge
(+0.0469) — independent replication of the same real, modest signal in a completely different
corpus, exactly the kind of confirmation that argues for trusting a bigger number over the old one.
Knockout-stage StatsBomb rates run lower still (0.216 knockout-core, 0.111 SF-or-Final, the latter
too thin to lean on alone) — directionally consistent with, not contradicting, a downward revision.
Pooled naive rate: 0.311. **Revised to 0.31.**

**Q8 — both teams carded.** Card-dependent; the pooled walk-forward's WC2026-specific accuracy gets
measurably *worse* (-0.0253 vs -0.0071) when StatsBomb data is folded into training — direct,
quantified evidence that pooling actively hurts this question, not helps it. The raw StatsBomb rate
(0.763) is explained away almost entirely by a documented, previously-found cross-source
card-counting gap once a rough correction is applied (0.512, close to WC2026's 0.550). WC2026's own
internal knockout-vs-group comparison contradicts the direction StatsBomb's does. This is the
textbook case the task asked to watch for: a bigger dataset that does not earn a confidence
increase. **Kept at 0.55, unchanged** — consistent with `topics/cards/README.md`'s standing
verdict that cards is a market/base-rate-anchored family this tournament, now reinforced by a
second, independently measured reason not to trust a fitted-on-more-data number for this family.

**Q10 — card before first goal.** Same measurement-gap story as Q8, milder (pooling shrinks but
doesn't flip the WC2026-specific edge: +0.0075 vs +0.0164) since Q10 is a race against goal timing
(source-homogeneous) rather than a pure card-count question. The same illustrative ratio correction
(0.504 x 0.671 = 0.338) again lands close to WC2026's native 0.350. StatsBomb's own knockout-core
vs group gap here is small (0.514 vs 0.490, 2.4 points) — even taken at face value it would not
argue for a meaningful move. **Kept at 0.35, unchanged.**

## 5. Files

- [`18_statsbomb_expanded_panel.py`](18_statsbomb_expanded_panel.py) / [`.csv`](18_statsbomb_expanded_panel.csv) — the 135-match Euro2024+CopaAmerica2024+AFCON2023 outcome panel, tagged by stage bucket.
- [`18_pooled_walk_forward_backtest.py`](18_pooled_walk_forward_backtest.py) — pools this panel with `ml/backtests/timing_compound_events_backtest.py`'s WC2026 dataset and re-runs the same walk-forward protocol.
- [`18_pooled_walk_forward_results.csv`](18_pooled_walk_forward_results.csv) — per-match, per-question pooled predictions (235 matches x 4 questions, long format, tagged by source).
- [`18_pooled_walk_forward_summary.csv`](18_pooled_walk_forward_summary.csv) — the 4-row aggregate rollup (matches §3's first table; the WC2026-target-only split in §3's second table was computed ad hoc from the results CSV and is reproducible by filtering `source=="WC2026_ESPN"`).
