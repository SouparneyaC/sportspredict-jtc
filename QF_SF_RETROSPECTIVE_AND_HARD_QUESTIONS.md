# Quarterfinal + Semifinal retrospective — why we won, why we lost, and a record of the hard questions

A cross-match review of every question priced across the six knockout matches from the quarterfinals
and semifinals, built to answer two things: (1) why did each result go the way it did, and (2) which
question *types* are genuinely hard — the "card before the first goal" family — so we have a standing
record of them and their track record. Written 2026-07-15, after the England vs Argentina SF settled.

Reproducible dataset: `data/processed/qf_sf_all_questions.csv` (87 rows — every QF/SF question with
our estimate, crowd, outcome, RBP, and a `hard_type` tag). Extraction pulled from each match's own
settlement file (`06_post_match_results.json`, `14_actual_submission.json`, `23_post_match_results.json`).

## 0. Scope and one data caveat stated up front

Six matches: **QF** — Spain vs Belgium, Norway vs England, Argentina vs Switzerland, France vs Morocco;
**SF** — France vs Spain, England vs Argentina. Spain vs Belgium was priced in the deliberate
*no-crowd/no-market* session, so its settlement records our estimate, outcome, and miss-distance but
**no per-question RBP or crowd** — it is included in the win/loss (correct-direction) review but sits
outside every RBP total below. All RBP aggregates are therefore over the **five** crowd-scored matches
(72 scored questions).

A classifier note, for honesty: the automated `hard_type` tagger initially mis-tagged two player
questions ("Álvarez score or assist", "Álvarez 1+ SOT") as VAR-review because the substring "var" sits
inside "Álvarez". Corrected with a word-boundary match. Consequence worth recording: **there is no
scored VAR-review question in the entire QF/SF set** — the only real one (France vs Spain) was *dropped*
(not submitted), consistent with the standing sample-starvation verdict on VAR questions.

## 1. Per-match record

| Stage | Match | Result | Scored Q | RBP | Beat-crowd |
|---|---|---|---|---|---|
| QF | France vs Morocco | (win) | 14 | **+169.16** | 93% |
| QF | Argentina vs Switzerland | (win) | 15 | **+159.76** | 93% |
| SF | France vs Spain | Spain won | 13 | **+138.33** | 77% |
| SF | England vs Argentina | Argentina won | 15 | **+96.05** | 67% |
| QF | Norway vs England | England won | 15 | **+95.58** | 73% |
| QF | Spain vs Belgium | Spain won | 15 | *−83.0 (match total, per platform; unscored per-Q here)* | n/a |

Five crowd-scored matches: **72 questions, +658.88 RBP, ~81% beat-crowd**. Including Spain-Belgium's
−83.0, the six-match knockout total is ≈ **+576 RBP over ~87 questions** — a strong stretch, but with
one bad match (Spain-Belgium) that the no-crowd experiment produced.

## 2. Category performance (corrected)

| Category | n scored | RBP | beat-crowd | mean/Q |
|---|---|---|---|---|
| Shots on target (team/combined/player) | 7 | +138.7 | 86% | +19.8 |
| Corners (team/combined/comparison) | 7 | +104.6 | 100% | +14.9 |
| Goals-total | 4 | +66.4 | 100% | +16.6 |
| **HARD: hydration-window timing** | 4 | +57.2 | 100% | +14.3 |
| Player-scorer | 7 | +51.6 | 71% | +7.4 |
| Match-outcome | 5 | +37.8 | 80% | +7.6 |
| **HARD: penalty-OR-red (compound)** | 3 | +35.1 | 67% | +11.7 |
| Half-time result | 4 | +31.1 | 100% | +7.8 |
| **HARD: half-comparison** | 1 | +21.7 | 100% | +21.7 |
| Cards (total/both) | 4 | +19.3 | 75% | +4.8 |
| **HARD: event-in-each-half** | 2 | +14.5 | 100% | +7.2 |
| **HARD: novel-scorer-shirt** | 1 | +11.5 | 100% | +11.5 |
| **HARD: path-dependent lead** | 1 | +5.6 | 100% | +5.6 |
| BTTS | 2 | +1.9 | 50% | +0.9 |
| **HARD: stoppage-time goal** | 1 | −0.5 | 0% | −0.5 |
| **HARD: substitution timing** | 1 | −10.6 | 0% | −10.6 |
| **HARD: card-before-goal (race)** | 1 | −28.4 | 0% | −28.4 |

## 3. Hard bucket vs standard bucket — the headline

| Bucket | n | RBP | positive | mean/Q |
|---|---|---|---|---|
| Standard questions | 57 | +553.0 | 47/57 (82%) | **+9.70** |
| **Hard questions** | 15 | +105.9 | 11/15 (73%) | **+7.06** |

Hard questions are **still net positive** but clearly the weaker bucket — lower hit rate and ~27% less
RBP per question — **and they carry the tails**: the single worst result of the entire QF/SF set
(card-before-goal, −28.4) is a hard question, and so are three of the biggest wins (penalty-OR-red
+24.4, hydration +23.3, half-comparison +21.7). Hard questions are where both the disasters and the
jackpots live.

## 4. The record of hard questions (worst to best) — the thing to keep

Every hard question we scored across the QF/SF, ordered by outcome. This is the standing reference for
"how have we actually done on questions like *card before the first goal*."

| RBP | Type | Match | Us | Crowd | Outcome |
|---|---|---|---|---|---|
| **−28.4** | card-before-goal (race) | England-Argentina | 0.35 | 0.50 | YES |
| **−10.6** | substitution timing | France-Spain | 0.60 | 0.54 | NO |
| −0.5 | stoppage-time goal | England-Argentina | 0.31 | 0.34 | YES |
| −0.5 | penalty-OR-red | Norway-England | 0.38 | 0.35 | NO |
| +2.7 | event-in-each-half | England-Argentina | 0.52 | 0.51 | NO |
| +5.6 | path-dependent lead | Argentina-Switzerland | 0.32 | 0.33 | NO |
| +8.2 | hydration-window | France-Morocco | 0.50 | 0.52 | NO |
| +11.2 | penalty-OR-red | France-Morocco | 0.38 | 0.35 | YES |
| +11.5 | novel-scorer-shirt | France-Spain | 0.31 | 0.35 | NO |
| +11.7 | hydration-window | Argentina-Switzerland | 0.47 | 0.51 | NO |
| +11.8 | event-in-each-half | Norway-England | 0.48 | 0.51 | NO |
| +14.0 | hydration-window | France-Spain | 0.42 | 0.38 | YES |
| +21.7 | half-comparison | Norway-England | 0.44 | 0.53 | NO |
| +23.3 | hydration-window | France-Spain | 0.75 | 0.61 | YES |
| +24.4 | penalty-OR-red | Argentina-Switzerland | 0.45 | 0.36 | YES |

(Plus, unscored, in the Spain-Belgium no-crowd match: two hydration-window questions, a path-dependent
lead, a penalty-OR-red, and a substitution-timing question — outcomes recorded but no RBP.)

## 5. Why we won and why we lost — the pattern inside the hard bucket

The hard questions split cleanly by **whether the number had a real anchor**:

**The winners all had an anchor.**
- **Hydration-window (4/4, +57.2)** — priced from a genuine historical base rate (goal-in-window
  frequency, ~74% for the between-breaks variant) and, when available, a market. The France-Spain
  "goal between hydration breaks" at 0.75 (+23.3) was the biggest — a high base rate on a wide window,
  correctly kept high above the compressed crowd (0.61).
- **Penalty-OR-red (2/3, +35.1)** — a compound (inclusion-exclusion, RULE4) built on referee card/pen
  rates plus a market check. The Argentina-Switzerland +24.4 came from correctly going *above* the
  crowd (0.45 vs 0.36) on a referee-specific signal that then hit.
- **Half-comparison, event-in-each-half, novel-scorer-shirt** — all *derived from the goal model or a
  market decomposition* (the single-digit-shirt scorer question was a market-implied first-scorer
  share, +11.5), not free-hand.

**The losers were pure no-market heuristics priced far from the crowd.**
- **card-before-goal −28.4** (Eng-Arg): a base rate (0.35) with no market, sitting 15pp below the crowd
  (0.50). It was flagged lowest-confidence *before* the match and still held — the flag was right.
- **substitution-timing −10.6** (Fra-Spa): a first-substitution race model (0.60), no market, deviating
  above the crowd (0.54) on an own-built heuristic that read the wrong side.
- **stoppage-time goal −0.5** (Eng-Arg): a base rate, no market, marginal.

This exactly reproduces the campaign-long finding in `KNOCKOUT_STAGE_PRICING_DEEP_DIVE.md`:
**self-built, no-market timing/race decompositions are the worst-performing instrument**, while the
same "hard" surface priced off a market, a trusted base rate, or a model decomposition is reliably
positive. The hard-ness is not intrinsic to the *question* — it is intrinsic to *pricing it without an
anchor*.

## 6. The standing rules this produces

1. **A hard question with an anchor (market / trusted base rate / model decomposition) is priced like
   any other question** — trust the anchor, sit off the compressed crowd, collect the premium. This is
   most of the hard bucket and it wins (hydration, pen-OR-red, scorer-shirt, each-half, half-comparison).
2. **A hard question *without* an anchor — a pure no-market timing or race heuristic (card-before-goal,
   first-substitution, stoppage-window) — must be shrunk toward the crowd, not sat far from it.** This
   is the single lesson that would have most improved the QF/SF results: the two worst hard losses
   (−28.4, −10.6) were both no-market heuristics deviating *away* from the crowd. When there is no sharp
   signal, the crowd is the best available anchor and the far-from-crowd premium is a trap, not an edge.
   This is the same conclusion the margin-push research reached theoretically (shrink noisy signals) and
   the England-Argentina post-match flagged specifically for card-before-goal.
3. **Keep dropping VAR-review** — still zero scored instances because we keep (correctly) not submitting
   it; the sample never became large enough to price.
4. **The "lowest-confidence" flag must trigger an action, not just a note.** card-before-goal was
   correctly flagged pre-match and still cost −28.4 because the flag changed nothing. Going forward, a
   low-confidence flag on a no-market question should mechanically pull the submission toward the crowd.

## 7. Bottom line

Across the QF/SF the process was strongly positive (≈+576 RBP / 6 matches), driven by the standard
market-anchored questions (+553 over 57) and the *anchored* hard questions (hydration, pen-OR-red,
decompositions). The drag came from a small number of un-anchored no-market timing/race questions,
whose defining error was sitting far from the crowd on a signal we did not actually trust. The
corrective is rule 2 above, and it is now recorded for the final.
