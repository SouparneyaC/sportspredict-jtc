# JTC Match Write-ups

Match-by-match research write-ups for the Jump Probability Cup (JTC), a 2026 FIFA World Cup
probabilistic forecasting tournament on `play.sportspredict.com`. Each write-up documents, per
question: what data was pulled, what scripts and models were used, what was actually submitted,
what a liquid market (where one exists) said, what the JTC crowd said, and how it settled.

This directory lives inside the main research repo (`sportspredict_research`) specifically so
every reference below is a real, clickable link to the actual script, model, or data file that
produced it — not a description of one. It's structured the way a professional trading or betting
research desk documents its own decisions: a scaffold in `docs/`, `decisions/`, and `matches/`.
See [`docs/DOCUMENTATION_STANDARDS.md`](docs/DOCUMENTATION_STANDARDS.md) for exactly which
industry practices this format is built from, and why. (This started as a standalone repo,
[`jtc-match-writeups`](https://github.com/SouparneyaC/jtc-match-writeups); merged in here so the
write-ups sit next to the code and data they describe instead of just linking out to it.)

## Structure

```
README.md                    -- this file, an index only
CONTRIBUTING.md              -- the standard every match write-up must follow
docs/
  DOCUMENTATION_STANDARDS.md -- researched industry practice this repo's format is built on
decisions/
  NNNN-*.md                  -- standing methodology decisions (ADR format), cited by match write-ups
matches/
  YYYY-MM-DD-team-vs-team/
    README.md                -- the full write-up
CHANGELOG.md                 -- additions to this repo (not match outcomes -- those live in the match files)
```

## Matches

| Date | Match | Result | RBP | Write-up |
|---|---|---|---|---|
| 2026-07-14 | France vs Spain (Semifinal) | Spain 2-0 France | **+138.32** (10W-3L, 77%) | [matches/2026-07-14-france-vs-spain/](matches/2026-07-14-france-vs-spain/README.md) |

## Standing decisions referenced across write-ups

| ID | Decision |
|---|---|
| [0001](decisions/0001-market-priority-over-domain-model.md) | A liquid market takes priority over a domain-only model when both exist |
| [0002](decisions/0002-shadow-deploy-before-live-submission.md) | A newly backtested model must be shadow-tested against real outcomes before it can override a submission |
| [0003](decisions/0003-never-blindly-drop-a-question.md) | Dropping a question requires a specific evidentiary reason, not just "no market exists" |
