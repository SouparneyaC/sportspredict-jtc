# Revision Notes: JTC_WC2026_Research_Paper.Rmd

Compiled 2026-07-11 from a full read of the current paper (dated July 1, 675 lines),
the France-Morocco and Brazil-Norway case studies, the academic style audit, and nine
supporting research docs. Organized as add/update/remove/verify, section by section,
followed by a style checklist and open questions.

Everything below is cross-checked against the live `datasets/master_question_dataset.csv`
where a number was in dispute between two source docs — those checks are marked ✓VERIFIED.

---

## 0. The headline problem

The paper is frozen at July 1 data (49 matches, 436 questions, +872 RBP). The live
dataset today (2026-07-11) is **85 matches, 921 scored questions, +3,246.04 RBP**
✓VERIFIED directly against `master_question_dataset.csv`. This is not "two matches
behind" — it's roughly double the matches and nearly 4x the cumulative score. Every
headline number in the abstract, intro, and results section needs a fresh pull, and
that pull should happen once, right before final compilation, not now — the tournament
is still live and the dataset is still growing (France-Morocco was the quarterfinal;
there may be a semifinal and final still to come).

**Recommendation:** treat "re-run `build_master_dataset.py` and re-derive every
headline number the night before submission" as a hard checklist item, not optional
polish — three separate source docs in this project already disagree with each other
over stale snapshots (872 vs 812 vs 774 vs 297 RBP at different points), and the
paper should not add a fifth stale number to that pile.

---

## 1. Title, Abstract, Introduction

**Add:**
- The paper needs a second headline finding to sit alongside crowd-compression: the
  systematic, multiply-replicated rejection of learned blending models. Currently this
  is a single paragraph buried in Calibration (§7.2, Platt scaling only). The
  France-Morocco paper already did this well — reframe the paper's central question the
  same way: not "which model fits best" but "which class of model is trustworthy at
  this sample size." This is a stronger, more defensible thesis for a quant-audience
  competition than "I found a crowd bias," because it's the more sophisticated
  methodological claim and it's now backed by *four* independent negative results (see
  §5 below), not one.
- A sentence on leaderboard standing (rank 43 of 3,879, top 1.11%, as of July 10) —
  currently absent from the whole paper. This is the single most externally-legible
  piece of evidence for a Jump Trading audience: it doesn't require trusting my own RBP
  bookkeeping, it's a platform-verified number against an open field of thousands.

**Update:**
- Every number in the abstract (n=384 → whatever the final pull gives once knockout
  crowd data is merged; +872 RBP → current total; 49 matches/436 questions → current
  count; 58.2% beat-crowd → recheck, since this was computed on a 423-question sample
  that's now stale too).
- Date field ("July 1 2026" → submission date).

**Remove:**
- Nothing structural here, but tighten: the abstract runs long relative to the style
  guide's own papers (Karlis & Ntzoufras' abstract is ~4 sentences; this one is closer
  to a mini-results-section). Cut it to the load-bearing numbers only.

---

## 2. Literature Review

**Add:**
- The five extra citations already pulled into `references.bib` for France-Morocco and
  unused here: `peduzzi1996`, `riley2019` (events-per-variable / EPV threshold for
  stable logistic regression coefficients — directly supports the expanded ML-rejection
  section), `harveyliuzhu2016` (most published trading-rule discoveries fail to
  replicate out of sample — directly supports the "named rules get evidence-forced
  revisions" narrative already in §"Named Situational Rules"), `merkle2017` (Brier
  decomposition for heterogeneous question portfolios — supports a more careful
  per-question-family read of the results table), `mamlouk2023` (calibration-based
  model selection beats accuracy-based selection in sports betting — justifies "Brier,
  never classification accuracy" as the only metric used throughout).
- No new citation needed for the StatsBomb panel or Elo bug — those are data/pipeline
  findings, not new literature.

**Keep as-is:** the existing eight-source review (Dixon-Coles, Karlis-Ntzoufras,
Michels et al., Crowder et al., Hvattum-Arntzen, Constantinou-Fenton, Murphy, Foulley,
wisdom-of-crowds) is solid and doesn't need restructuring, just the five additions
above woven in near the ML-rejection section rather than appended as an afterthought.

---

## 3. Data

**Add:**
- A subsection on the StatsBomb WC2018+WC2022 event-level panel (128 matches, 6,131
  player-match rows, 257 team-match rows — this is the *actually built* panel; an
  earlier proposal document sketched a larger 314-match multi-tournament panel that was
  never built, so don't cite that larger number). Include the validation checks that
  make this panel trustworthy: goal totals match known history exactly (WC2018: 169
  goals/2.641 per match; WC2022: 172/2.688), top scorers reproduce correctly (Mbappé 8
  goals 2022 including the final).
- The cross-source measurement heterogeneity finding — ESPN and StatsBomb count the
  same events differently (ESPN records ~20% fewer fouls, ~27% fewer yellow cards, ~38%
  more shots-on-target, ~30% more corners than StatsBomb for the same matches). This is
  a genuinely interesting, citable methodological finding in its own right — real
  papers report exactly this kind of "our two data sources don't agree, here's the
  correction factor" finding (see style notes §4, §8) rather than silently picking one
  source. It belongs in Data, with the practical consequence stated plainly: raw counts
  must never be pooled across `data_source` without this correction.
- Match-data-inventory scale update: the source-reliability tier table's own
  underlying evidence base (MATCH_DATA_INVENTORY.md) already flags that the paper's
  "61 settled matches" language is stale and should read "71 settled matches... 53
  calendar days" as of its own July 3 writing — and that's stale again now at 85+
  matches. Update the live count at final-pull time.

**Update:**
- Master dataset row/column/match counts throughout (480 rows/105 cols/56 matches is
  already inconsistent within the current paper — §Scope says 480 rows, §Master Dataset
  Documentation says 580 rows/105 columns/56 matches — reconcile before adding new
  numbers on top of an unreconciled base).
- The Elo data-quality note needs a new, more serious entry: `elo_current_ratings.csv`
  was frozen at pre-tournament values because `results.csv` never received real 2026
  scores, so no in-progress-tournament Elo rating was ever actually current. This is
  currently undocumented anywhere in the main paper. See §4 below — this belongs in
  Methodology as much as Data, but the underlying data defect belongs here.

**Remove:** nothing — the tiered source-reliability table and pipeline description are
still accurate and well-regarded structurally; just refresh the trailing counts.

---

## 4. Methodology

**Add — the Elo point-in-time bug (this is a must-add, not optional):**
The France-Morocco paper's §5 ("Point-in-Time Elo Correction") is the single most
citable new methodological finding since July 1. Summary: `results.csv` (the
historical-panel source file) records every 2026 World Cup match's score as `NA`, so
`model/elo.py` has never processed a single real 2026 result — every "current" Elo
rating used all tournament has actually been frozen at pre-tournament, early-June
values. A workaround (a point-in-time replay script) was built and validated across
five retrospective matches, moving differentials by 12–35 points relative to the stale
baseline. This is exactly the kind of "we found a real bug, traced it, fixed it or
worked around it, and show the corrected numbers" material the style notes say real
papers include and AI drafts omit. It should get its own subsection in Methodology
(or a forward pointer from Methodology to a fuller treatment in Results/Limitations),
with the explicit caveat already documented: the workaround is match-by-match, not a
pipeline-level fix, so it needs to be re-run for every future knockout match until the
root cause (the source data file) is actually fixed.

**Verify/soften:**
- The existing note about the Poisson `neutral`-flag training bug (§Poisson Goal-Rate
  Regression) already says the fix was applied and coefficients re-fit — this is
  consistent with the live repo state (confirmed fixed 2026-07-10 per the project's own
  bug tracker) but double-check the exact coefficients quoted (`b0=0.1041, b1=0.2302,
  b2=0.001810`) still match `poisson_goals_coefs.json` at final-pull time, since this
  file gets re-fit periodically.
- One correction worth making explicitly: the bug tracker notes the *direction* of the
  bug's effect was originally mispredicted (expected to attenuate b1 downward toward a
  ~0.35 prior; actual effect was the opposite — the buggy version gave a *higher* b1
  than the fixed version). The current paper's phrasing already avoids overclaiming
  here ("suggesting... rather than the neutral-flag mismatch alone") but could be tightened
  to state the direction-reversal finding directly — it's a small, honest, paper-appropriate
  admission that a predicted mechanism didn't hold as predicted.

**Keep as-is:** Elo update formula, Poisson GLM, Dixon-Coles/NB corrections, ordered
logit, lambda-fitting via Smarkets, Skellam distribution for head-to-head props,
walk-forward backtesting discipline — all still accurate and don't need re-deriving.

---

## 5. Rejection of Learned Blending Models (new section, replacing the thin Platt-only treatment)

This is the biggest structural addition. The current paper treats "should I use ML"
as one paragraph inside Calibration, citing only the Platt-scaling diagnostic
(n=246, inconclusive). There are now **four independent negative results**, from four
different documents, all pointing the same direction, at increasing levels of rigor:

1. **Platt-scaling recalibration** (n=246 originally, n=384 in the France-Morocco
   paper's own rerun) — bootstrap 95% CI on the slope comfortably includes 1.0
   (perfect calibration); a walk-forward split shows the fitted slope is itself
   unstable (0.196 out-of-sample vs 0.510 in-sample) and applying the correction
   degrades out-of-sample Brier.
2. **Meta-model (logistic regression + gradient-boosted trees)**, the more rigorous
   sibling of the Platt diagnostic — n=404 (group stage only), two validation schemes
   (time-ordered walk-forward, GroupKFold-by-match). Both models lose to the
   crowd-alone baseline under both schemes, by margins from −147.9 to −1,760.3
   RBP-equivalent. This is the material already written up in full, with tables, in
   the France-Morocco paper's §"Why Not Machine Learning" — it can likely be adapted
   almost directly.
3. **Linear regression on RBP as a function of crowd-deviation** (StatsBomb
   integration doc, n=771 questions/71 matches) — in-sample R²=0.053, only
   `is_player_prop` is a significant predictor, and the model loses to a naive
   baseline out-of-sample (GroupKFold MSE 157.23 vs. baseline 149.59).
4. **The theoretical result in STRATEGIC_MARGIN_PUSH_RESEARCH.md**: under RBP as an
   additive, per-question proper scoring rule (not a convex/rank-based payoff),
   deliberately pushing a submission past a calibrated estimate is strictly
   negative-expected-value, with a guaranteed quadratic cost. This gives the four
   empirical results above a theoretical anchor — it's not just "ML happened to lose
   four times," it's "ML losing is the expected behavior of this specific scoring
   rule at this specific sample size," which is a much stronger claim.

**Recommendation:** structure this as its own top-level section (mirroring
France-Morocco's), reporting all four results in one table, then the EPV literature
(`peduzzi1996`, `riley2019`) as the reason this isn't surprising, then the
`mamlouk2023` calibration-over-accuracy point as the reason Brier (not accuracy) is
the only metric used. This section is what elevates the paper from "a good track
record writeup" to "a methodologically serious argument about model selection under
small-sample constraints" — exactly the kind of finding a quant recruiter would find
more interesting than another win/loss table.

**One live counter-example worth including for honesty, not omitting:** the
Cluster-B "de-shrink toward empirical SOT average" lever proposed in
STRATEGIC_MARGIN_PUSH_RESEARCH was actually live-tested once (Canada-Morocco, "Canada
4+ SOT") and lost badly (−80.83 RBP, now the single worst result in the whole
campaign — see §7 below). That's a clean, real, undramatized illustration of the
paper's own thesis: a theoretically-motivated push, applied to a signal that wasn't
genuinely high-confidence, cost exactly what the theory predicted it would.

---

## 6. Crowd-Bias Model and Decision Rules

**Mostly already current** — the regression coefficients quoted in the existing paper
(`0.511 + 0.60×(p_model−0.5)`, n=384, r=0.828, 95% CI [0.559, 0.641], OOS RMSE 8.44pp,
bias −1.72pp) already match the most recent standalone regression-update memo almost
exactly. Good news: this section needs the least work of any major section.

**Flag, don't necessarily fix:** the n=384 sample is group-stage only (June 11–25);
knockout-stage questions have crowd_estimate data in principle but haven't been merged
into the regression. Whether to re-run the regression on the full 85-match dataset
before submission is worth deciding explicitly — either re-run it and report the
larger n, or add one sentence flagging the group-stage-only scope as a stated
limitation (the current paper doesn't say this restriction anywhere).

**Add to Named Situational Rules:**
- The Cluster A/B pattern from `WINNING_PATTERNS_SYNTHESIS.md` (75 questions, 5
  matches): suppressing a named player's prop on a genuine multi-game production
  drought wins 7-for-7 (+144.67 RBP); blending a favorite team's own SOT threshold
  upward toward its recent empirical average loses 5-for-5 net (−155.64 RBP, later
  confirmed to fail a 6th time in Brazil-Norway's own retrospective and a 7th time —
  reversed as a genuine win — only when the market number itself was trusted instead).
  This is a cleaner, more quantified, more repeatedly-tested version of what the
  existing rules taxonomy is already trying to do, and it directly generalizes the
  existing PLAYER_ILLIQUID / TIMING_NO_MARKET category findings already in the paper's
  knockout audit table.
- The live validation and complication: Brazil-Norway Q14 confirmed the rule
  correctly (stood at market on Brazil's own 6+ SOT question, +22.57 RBP, second
  biggest win of that match) but the very next live application of the "de-shrink"
  version of the same idea (Canada-Morocco) lost −80.83 RBP — the campaign's worst
  result to date. Both belong together as a single honest illustration: a strong prior
  is not an absolute law, and knowing when a signal is genuinely Tier-A rather than
  reflexively pattern-matching is the actual skill being exercised.
- A genuine counter-example to keep the rule honest (style-guide-consistent — real
  papers report the exceptions, not just the wins): Mexico-England, "England 5+ SOT" —
  staying at the market cost −16.79 RBP where a personal-history-grounded empirical
  estimate would have won. The honest generalization (already stated well in the
  France-Morocco paper's own retrospective section) is that the market beats
  extrapolation specifically when a thin team-level sample is being projected toward a
  count threshold, not universally.
- The "both teams do X, decompose independently rather than assume a shared/symmetric
  rate" finding from Brazil-Norway Q15 (+59.43 RBP, now the single best individual
  result in the campaign) — a clean, generalizable, well-reasoned methodological rule
  worth adding as a new named rule alongside RULE1–15.

**Update:**
- "Worst individual result" throughout the paper currently cites Brazil vs. Morocco
  (−51.97 RBP, a personal-conviction override). ✓VERIFIED against the live dataset:
  this is no longer the worst result. Canada vs. Morocco, "Canada 4+ SOT" (−80.83 RBP)
  is now the worst single result in the campaign, and it's arguably the better story
  for a paper — not a one-off lapse in discipline, but a real, traceable methodological
  failure mode (the Cluster-B trap) that had already been named and warned about
  in writing before it happened again.
- "Best individual result" currently cites Mexico-Ecuador Q12 (+49.58 RBP). ✓VERIFIED:
  Brazil vs. Norway, "both teams carded" (+59.43 RBP) is now the best single result.
  Keep the MEX-ECU example too if there's room — it's still a clean illustration of a
  different mechanism (pure ESPN-behavioral-data suppression with no market at all).

---

## 7. Calibration and Validation

**Keep:** the historical-panel calibration gap discussion and the open logit-space/
neutral-split diagnostic recommendation — still an accurate, honest "this remains
unresolved" statement (per the bug tracker, `backtest_diagnostics.py` exists and is
correct but hasn't been confirmed run).

**Move:** the Platt-scaling paragraph currently here should shrink to a cross-reference
into the new §5 (Rejection of Learned Blending Models) rather than carrying the ML
argument alone — right now it's doing double duty as both a calibration diagnostic and
the paper's only stated reason not to use ML, and splitting those two roles will make
both sections cleaner.

---

## 8. Track Record and Results

**Add:**
- A leaderboard/rank trajectory table — this doesn't exist anywhere in the current
  paper and is the single most externally-verifiable piece of evidence available. Three
  snapshots are already documented (2026-06-27: rank 200/3,564, top 5.61%; 2026-06-29:
  rank 177/3,628, top 4.88%; 2026-07-10: rank 43/3,879, top 1.11%, cumulative score
  3,568.30). Frame it carefully the way the France-Morocco paper does: percentile, not
  raw rank, is the comparable statistic since the field itself grew ~9% over the
  window; note the field-composition caveat honestly (no verified claim about who,
  specifically, is being outperformed).
- Case-study-level summaries of Brazil-Norway (+179.26 RBP, 13/15 beat crowd — the
  independent-per-team compound-probability finding) and France-Morocco (+169.17 RBP,
  13/14 beat crowd — the campaign-best result at time of writing, priced with zero
  market anchor available at the start). These don't need the full case-study detail
  that their standalone documents have — a compressed paragraph each, pointing to the
  underlying finding each one validates, is enough for the main paper.
- Refresh or explicitly caveat-and-retain the knockout-stage category-level audit
  table (currently 4 matches/60 questions: South Africa-Canada, Germany-Paraguay,
  Brazil-Japan, Netherlands-Morocco). There are now many more knockout matches
  available to fold in — either recompute the table at the larger n, or keep the
  original 60-question table explicitly labeled as an early-knockout snapshot and add
  a second, larger one if time allows. Don't silently leave a 60-question table
  standing in for what's now available at n>200.

**Update:**
- The individual-match-results table (8 matches, through Mex-Ecu/Fra-Swe/Ned-Mar/
  Eng-Cdr) needs either expansion or explicit reframing as "selected highlights" rather
  than implying completeness — it currently reads as close to a full listing but is
  now a small fraction of settled matches.
- Beat-crowd rate (58.2% cited) — recompute against the current dataset.

---

## 9. Limitations and Future Work

**Add:**
- The Elo point-in-time bug belongs here too (or a forward/back reference to
  Methodology) as an explicitly *open* limitation: the workaround is per-match, not
  fixed at the pipeline source, so it will recur on every future in-progress fixture
  until `results.csv` itself is corrected or bypassed properly.
- The ESPN-vs-StatsBomb measurement heterogeneity finding belongs here as a stated
  data-quality caveat if it isn't already fully absorbed into Data.

**Update:** the "process failures account for 140+ RBP" framing (Kane transcription
error, BIH-QAT missed deadline, NZL-EGY corner-mapping) is still accurate and doesn't
need changing, but check whether any *new* process failures have occurred since July 1
that belong alongside it (none surfaced in the docs reviewed for this pass — worth a
quick check against the bug tracker's Category A/B items, most of which are now
resolved).

**Remove:** the future-work items that are now done should move out of "future" and
into the relevant results section as completed work: the Poisson neutral-flag fix
(done 2026-07-10) is currently still framed partly as forward-looking in a couple of
places — tighten this so completed work isn't sitting in a section titled Future Work.

---

## 10. Style and Language — hard guardrails

This is as important as any content change per your instruction, so treating it as
its own checklist rather than folding into the section notes above:

1. **First person: "I," not "we."** This is a solo project; the current paper (and the
   France-Morocco / Brazil-Norway case studies) all use "we/our/the project's" almost
   universally. This needs a full pass, not a find-and-replace — some instances of "we"
   refer to a genuine methodological plural ("we compare two models") that becomes "I
   compare two models," and some refer to "the project" as an institutional actor that
   should probably just become "I" directly. Flagging this as a scope question below,
   since the case studies are also written in "we."
2. **No bullet lists in body prose.** The current paper has several bulleted lists
   inside body sections that the style audit says should not exist in a published
   paper of this kind: the "Key data quality findings" list in §Data, the numbered
   "Three features of the World Cup forecasting setting" list in §Limitations, and a
   few others. Convert each to prose paragraphs with topic sentences and logical
   connectors ("although," "as a consequence," "in contrast") per the style notes'
   worked examples. The only lists that should survive are formal enumerations of
   named mathematical objects referenced later by their labels.
3. **No bold in body prose.** Scan for any bold text used for emphasis (not currently
   heavy in this paper, but check headers-as-bold-runin patterns like "**RULE1
   (match-winner questions)**" in §Named Situational Rules — these should become plain
   italics on first use or just named inline without bold, per the style notes'
   Section 2).
4. **Headers as noun phrases, not questions or conversational titles.** "Why Not
   Machine Learning" (used in France-Morocco) technically violates the style guide's
   own rule against interpretive/rhetorical headers — consider "Rejection of Learned
   Blending Models" or "Model Selection Under Small-Sample Constraints" instead, for
   both the new section in the main paper and, if revised later, the case study.
5. **No AI-tell phrasing.** Watch specifically for: "In conclusion," / "To summarize,"
   opening the Conclusion (currently avoided, keep avoiding it); hedging with "may/
   could/might" on claims the paper's own analysis has already established directly
   (the style notes' example: don't hedge a claim right after reporting p<0.01 for it);
   generic desiderata-based motivation instead of diagnostic, data-driven motivation
   (the paper is already fairly good on this front — keep grounding every methodological
   choice in a specific data pattern, the way the Poisson-bug and Elo-bug narratives
   already do).
6. **Numbers named before given, and referenced by table/figure number throughout**,
   not just introduced once and left. Already mostly followed; extend the discipline
   into the new §5 material.
7. **Trim the abstract and avoid "mini-results-section" abstracts** — see §1 above.

---

## 11. Open questions before drafting

1. **Scope of the "I not we" rewrite** — main paper only, or also retroactively apply
   to FRA_MAR_Full_Case_Study and BRAZIL_VS_NORWAY_CASE_STUDY if those get referenced
   or partially absorbed into the main paper? (They're currently written in "we" too.)
2. **How much of France-Morocco's "Why Not ML" section to reuse verbatim vs.
   re-derive** — the France-Morocco paper's version is already excellent and directly
   reusable with light editing; folding it into the main paper risks the two documents
   reading as near-duplicates if both are submitted together. Worth deciding whether
   the main paper's version should be the fuller one (with all four negative results)
   and the case study's version stays as the original, narrower one.
3. **Whether to recompute the crowd-bias regression and knockout-audit table on the
   full 85-match dataset**, or explicitly scope both to their original windows and
   note the extension as future work. Recomputing is more work but more defensible for
   a competition submission that will presumably be scrutinized.
4. **Final data pull timing** — given the tournament is still live, when should the
   "final" numbers be locked for submission? Recommend doing the live re-pull as the
   actual last step before compiling to PDF, not now.
5. **Whether the paper should gain a short dedicated leaderboard/external-validation
   section**, or whether the rank trajectory table belongs inside Results as I've
   suggested above.

---

## 12. Decisions (2026-07-11) and final recomputed numbers

Answers to §11: (1) first-person rewrite applies to the main paper **and** both case
studies going forward; (2) the ML-rejection section is reused and expanded from
France-Morocco for the main paper, case study keeps its own narrower version; (3) both
the crowd-bias regression and the knockout category audit are recomputed on the full
live dataset rather than left at their original scope.

**Crowd-bias regression, recomputed on all 772 submitted questions with a paired
crowd estimate (vs. the paper's current n=384, group-stage-only):**
`crowd = 0.5042 + 0.6087 × (our_estimate − 0.5)`, r=0.829, R²=0.6875, 95% CI on slope
[0.580, 0.638], residual SD 7.19pp. Walk-forward OOS (train on first 540
chronologically, test on remaining 232): RMSE 5.85pp, bias 1.08pp — actually tighter
than the original n=384 OOS check (8.44pp), a genuinely positive finding (the
relationship gets more precise, not less, as the sample grows into the knockout
rounds). Direction split: below-0.5 estimates (n=500) average 0.334 vs. crowd's 0.403;
above-0.5 estimates (n=252) average 0.639 vs. crowd's 0.588. Compression: crowd less
extreme than my own estimate on 73.2% of questions, more extreme on 22.5%, equal on
4.3%. **This is essentially the same relationship as the original n=384 fit** — worth
stating explicitly as a stability finding, not just a bigger number.

**Knockout/pricing-technique category audit, recomputed by harmonizing the two
category vocabularies the raw files use** (older `tier1_market`/`tier2_realdata` vs.
newer `DIRECT`/`TEAM_MODEL`/`PLAYER_LIQUID`/`PLAYER_ILLIQUID`/`TIMING_*`) across all 20
matches in the dataset that carry a category tag at all (question-category coverage is
sparse — 210 of 943 rows — so this is a representative sample, not the full campaign;
state that plainly rather than implying completeness):

| Category | n | Total RBP | Avg RBP | Beat-crowd |
|---|---|---|---|---|
| DIRECT | 99 | +365.23 | +3.69 | 69.7% |
| TEAM_MODEL | 65 | +234.03 | +3.60 | 72.3% |
| PLAYER_LIQUID | 20 | +209.74 | +10.49 | 85.0% |
| PLAYER_ILLIQUID | 16 | +116.53 | +7.28 | 68.8% |
| BASE_RATE | 4 | +25.23 | +6.31 | 75.0% |
| TIMING_EARLY | 5 | +17.21 | +3.44 | 40.0% |
| TIMING_NO_MARKET | 1 | +11.76 | +11.76 | 100% |
| **Total** | **210** | **+979.73** | **+4.67** | **71.4%** |

Two things changed from the original 60-question table and both are worth stating
directly rather than silently updating: `PLAYER_ILLIQUID` was net negative
(−14.27 total) in the original table and is now net positive (+116.53) — consistent
with the 0.945 illiquid-discount rule maturing. `TIMING_NO_MARKET`, the original
table's one structurally loss-making category (−63.72 total, −9.10 avg), has nearly
disappeared from the mix (n=1) — consistent with the standing rule adopted specifically
because of that finding (shade late-window, no-market questions to 0.45–0.55, or avoid
them). This is a clean before/after illustration of a rule actually changing behavior
and the behavior change actually paying off, not just a bigger sample.

**Headline totals.** Master dataset (`master_question_dataset.csv`, most recent
rebuild): 85 matches, 921 scored questions, +3,246.04 RBP, 642/921 (69.7%) beat-crowd.
France vs. Morocco (QF, 2026-07-09) is **not yet merged into this rebuild** — its
verified standalone total (+169.17 RBP, 14 questions, 13/14 beat-crowd) should be
stated as a separate, most-recent addition, combined total ≈+3,415 RBP across 86
matches, pending the next dataset rebuild. Flag this the same way the paper already
flags other cross-document discrepancies — don't silently fold it in.

**Best/worst individual results, confirmed against the live CSV:** worst is
Canada vs. Morocco, "Canada 4+ shots on target" (−80.83 RBP); best is Brazil vs.
Norway, "both teams receive at least one card" (+59.43 RBP). Both supersede the
paper's current BRA-MAR (−51.97) / MEX-ECU (+49.58) citations.

**Top matches by total RBP** (for a "selected highlights" results table): Brazil vs.
Norway (+179.27), Belgium vs. Senegal (+159.72), Mexico vs. Ecuador (+154.22), France
vs. Sweden (+148.24), Switzerland vs. Algeria (+137.56), Portugal vs. Croatia
(+130.08), Netherlands vs. Morocco (+120.31), England vs. Curaçao (+119.37), France
vs. Paraguay (+116.44) — plus France vs. Morocco (+169.17, pending merge, would rank
2nd). Weakest: Argentina vs. Austria (−42.23), South Africa vs. South Korea (−39.55),
Qatar vs. Switzerland (−39.19).

Next step: draft the revised `JTC_WC2026_Research_Paper.Rmd` incorporating all of the
above, then convert `FRA_MAR_Full_Case_Study.Rmd` and `BRAZIL_VS_NORWAY_CASE_STUDY.md`
to first-person voice.
