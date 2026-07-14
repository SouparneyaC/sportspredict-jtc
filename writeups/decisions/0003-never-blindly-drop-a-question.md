# 0003: Dropping a question requires a specific evidentiary reason, not just "no market exists"

**Status:** Accepted

## Context

Early in the campaign, a question with no exact historical precedent (a stoppage-time-card question,
France vs Morocco) was skipped outright. It resolved in a way that a modest, low-confidence base-rate
guess would have won big on — an estimated 220+ RBP given up for free. The lesson recorded at the
time: "no exact settled precedent" is too low a bar for skipping; skipping should be reserved for
when there's no directional reasoning available at all, not just no exact match to a past question.

Later in the campaign (2026-07-14), a full audit of the 25 worst-scoring questions in the project's
settled history, plus a dedicated statistical-power analysis (backtest methodology research,
`BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md`), identified specific, well-evidenced categories
where the project has a genuine negative track record or a proven inability to validate any model —
not just "no market."

## Decision

A question may only be dropped for one of these specific reasons, each requiring real evidence, not
a general sense that the question is hard:
1. A documented negative RBP track record for the *exact* question structure across a real sample
   (not a vague category-level impression).
2. Zero prior occurrences of the question type, combined with a demonstrated statistical-power
   ceiling (e.g. Kupiec-style analysis showing no test could validate a number at the available
   sample size).
3. A purpose-built model tested and found to perform worse than a naive baseline, with no
   informative track record to fall back on instead.

"No market exists" alone is never sufficient justification on its own.

## Consequences

This is easier: dropping is now a defensible, auditable decision instead of a judgment call that's
hard to distinguish from giving up.

This is harder: most questions that feel uncomfortable still have to be answered, with a
low-confidence, near-crowd number rather than skipped — more exposure to genuinely uncertain
questions, deliberately, because the alternative (skipping) has already cost more than it saved.

**Evidence this decision was tested, not just assumed:** France vs Spain (2026-07-14) dropped two
questions (combined offsides, VAR on-field review) under reasons 1 and 2 above. Both resolved YES.
Per this decision's own logic, one match resolving favorably does not overturn the 17-question
offside base rate or the VAR power-analysis finding that justified dropping them — logged honestly
in that match's write-up rather than treated as evidence the drops were wrong.