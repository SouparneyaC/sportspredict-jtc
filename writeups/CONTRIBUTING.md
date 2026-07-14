# Standard for match write-ups

Every entry under `matches/` follows this shape. See `docs/DOCUMENTATION_STANDARDS.md` for the
research this is built from.

## File layout

`matches/YYYY-MM-DD-team-a-vs-team-b/README.md` — one file per match. Slug is lowercase,
hyphenated, present-tense-neutral (`france-vs-spain`, not `FRA_vs_ESP` or `fra-esp-w`).

## Required sections, in order

1. **Header** — final score, stakes/round, date, link back to source data in the main research repo.
2. **Executive summary** — final RBP, win/loss record, the 2-3 things a reader most needs to know
   before going question-by-question.
3. **Per-question sections**, each with two sub-sections that are never merged:
   - **Pre-match** — the question text, which tier it falls in (direct market / derived / no-market
     domain model / dropped), every script and data source that fed the number, the reasoning, and
     the final submitted probability alongside the market and crowd numbers if they exist. Written
     as if the match hasn't happened yet — no outcome knowledge allowed to leak in here.
   - **Settlement** — the actual outcome, the official RBP, and a graded verdict (beat crowd / below
     crowd, and why in one sentence).
4. **Match-level postmortem** — Google SRE five-question shape: what happened, why, how we
   responded (i.e. what decisions we made under time pressure), what we learned, what changes for
   next time. Written blameless: a wrong call is described by its cause (thin evidence, a specific
   model limitation, a data gap), never as someone having been careless.
5. **Sources / artifacts** — every script, data file, and API endpoint that fed the write-up, with
   its path in the main research repo. If a number in this document can't be traced to something in
   this list, it doesn't belong in the write-up.

## Rules

- **No editing after settlement.** Once the "Settlement" sections are filled in, the "Pre-match"
  sections are frozen — if a pre-match number turns out to have been miscalculated, add a dated
  correction note rather than silently changing the original text. The point is to know what was
  actually believed *before* the outcome was known.
- **Cite standing decisions, don't re-argue them.** If a question follows a rule already recorded in
  `decisions/`, link it instead of re-explaining the reasoning inline.
- **Grade every question, including drops.** A dropped question still gets a settlement note (what
  it would have resolved to), per the CLV discipline in `docs/DOCUMENTATION_STANDARDS.md` §5 — grade
  every bet, every time, not just the ones that flatter the record.