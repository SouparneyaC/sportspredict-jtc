# Documentation Standards — Research Notes

Researched 2026-07-14, before writing anything else in this repo. The question: how do professional
organizations — software/site-reliability engineering orgs, quant trading desks, and professional sports
betting operations — actually document decisions and outcomes in a way that survives contact with time,
turnover, and scrutiny? This repo's structure and the match write-up format are built directly from these
four sources, not invented from scratch.

Every claim below is sourced from a live web search performed this session. **"Source:"** marks a claim
read from a cited page. **"Applied here:"** marks how this repo uses it.

---

## 1. Google SRE — Postmortem Culture

**Source:** [Google SRE Book — Postmortem Culture](https://sre.google/sre-book/postmortem-culture/), [Google SRE Workbook — Postmortem Practices](https://sre.google/workbook/postmortem-culture/), [Google SRE Book — Example Postmortem](https://sre.google/sre-book/example-postmortem/)

A postmortem is written after *every* significant incident — not just failures worth punishing, and
specifically **blameless**: it assumes everyone involved acted on the best information available at the
time, so people can be honest about what happened without fear of it being held against them. The
canonical Google document is a template with a fixed shape: **summary, timeline, root-cause analysis,
impact assessment, and corrective action items with named owners and due dates.**

The postmortem earns its keep by answering five questions in order:
1. What happened? — an objective, time-ordered narrative, not an interpretation.
2. Why did it happen? — contributing factors, not "human error" as the answer (dig past a person's
   mistake to the tooling gap, ambiguous process, or missing check that let the mistake happen).
3. How did we respond? — what mitigations were used, how well they worked.
4. What did we learn?
5. What will we change? — concrete, owned, trackable action items. Without follow-through tracking, a
   postmortem source says it "becomes a historical record instead of a mechanism for change."

**Applied here:** every match gets a postmortem section built on exactly this five-question shape (see
`matches/*/README.md` → "Postmortem"). Root-cause analysis is written the same way — a losing question
gets traced to *why* (missing feature, thin evidence, deliberate deviation), never just logged as a loss.
Action items from a match postmortem are meant to change something in the next match, not just be read.

---

## 2. Architecture Decision Records (ADR / MADR)

**Source:** [MADR — Markdown Architectural Decision Records](https://adr.github.io/madr/), [ADR GitHub org](https://github.com/architecture-decision-record/architecture-decision-record), [The MADR Template Explained](https://ozimmer.ch/practices/2022/11/22/MADRTemplatePrimer.html)

An ADR captures one significant, hard-to-reverse decision at the moment it's made — not after the fact —
so future readers know *why* something was done, not just *what*. The standard shape:
**Status** (proposed / accepted / rejected / superseded), **Context** (the problem, forces, and
constraints that motivated the decision), **Decision** (what was actually chosen), and **Consequences**
(what becomes easier, what becomes harder, what risk was accepted).

Source-confirmed conventions: one decision per ADR, filed under a predictable path (`docs/decisions/` or
`decisions/`, numbered `NNNN-title-in-present-tense.md`) so they're sortable and linkable; committed
directly to the repo as plain Markdown specifically because plain text diffs and reviews cleanly in git,
unlike a Google Doc. A source recommends revisiting an ADR later to check it against what actually
happened — which for this project maps directly onto grading a methodology decision against real RBP.

**Applied here:** `decisions/` holds one file per significant, reusable pricing-methodology decision (e.g.
"market beats domain model when both exist," "a backtested model needs live shadow-testing before it can
override a submission"). These are NOT per-question notes — they're the standing rules a match write-up's
individual questions cite back to, so the rule and its evidence live in one place instead of being
re-explained in every match.

---

## 3. Docs-as-code / README-driven documentation

**Source:** [Documentation as Code Best Practices](https://docs.gitscrum.com/en/best-practices/documentation-as-code), [A Developer's Guide to Docs as Code](https://deepdocs.dev/docs-as-code/), [How to Structure Your README File](https://www.freecodecamp.org/news/how-to-structure-your-readme-file/)

Treat documentation like source: version-controlled, reviewed, and living in the same repo as the thing it
describes, specifically so a change and its documentation land in the same atomic commit instead of
drifting apart. The README is the front door — Readme-Driven Development goes as far as writing the README
*before* the thing it documents, to force clarity about what's actually being built. A `/docs` folder with
a `CONTRIBUTING.md` at the root is the standard extension once a single README gets too small to hold
everything.

**Applied here:** repo root `README.md` is a pure index — what this repo is, how it's organized, a table
of matches — deliberately kept short so it stays readable. All depth lives one level down
(`matches/<date>-<slug>/README.md`, `docs/`, `decisions/`). `CONTRIBUTING.md` states the standard every
match write-up must follow, so a new entry doesn't have to reinvent the format.

---

## 4. Keep a Changelog

**Source:** [keepachangelog.com](https://keepachangelog.com/en/0.3.0/)

A single `CHANGELOG.md`, human-written (not auto-generated from commit logs — a source is explicit that
"a commit log is not a changelog" because commits document code changes, not user-facing changes),
organized by category (Added / Changed / Fixed / Removed) with an "Unreleased" section always at the top
so nothing is forgotten before the next entry.

**Applied here:** `CHANGELOG.md` tracks additions to *this repo* (new matches written up, new decisions
recorded, format changes) — not match outcomes, which belong in the match files themselves.

---

## 5. Professional sports betting — CLV as the grading standard

**Source:** [Pikkit — Closing Line Value](https://pikkit.com/closing-line-value), [OddsJam — CLV explained](https://oddsjam.com/betting-education/closing-line-value)

Sharp bettors and professional syndicates grade every position by **Closing Line Value first, raw P&L
second** — the question isn't just "did this win," it's "was this priced better than the market's own
final, most-informed number." A source states the discipline plainly: **"grade every bet, every time —
selective tracking introduces selection bias and breaks the metric."** Pinnacle's closing line is treated
as the industry benchmark specifically because it's the market regarded as sharpest.

**Applied here:** this maps almost exactly onto how this project already scores itself — RBP is graded
relative to the JTC crowd the same way CLV is graded relative to a closing line, and this repo's discipline
of writing up *every* answered question (wins and losses, including the two questions we deliberately
dropped) is the direct application of "grade every bet, every time." Where this project also has a genuine
market (Smarkets) available, both comparisons — vs. the JTC crowd (RBP) and vs. the sharp market — are
recorded per question, not just the one that flatters the result.

---

## 6. Pre-trade / post-trade structure (transaction cost analysis)

**Source:** [Transaction Cost Analysis — background research this session]

Trading desks split every position into two documented phases: **pre-trade analysis** (known information,
planned action, and the reasoning behind it, written *before* execution) and **post-trade analysis**
(what actually happened, measured against the pre-trade plan, after the fact).

**Applied here:** every question in a match write-up follows this exact two-phase shape —
"Pre-match" (data pulled, scripts run, reasoning, final submitted number) is written and frozen before the
"Settlement" (actual outcome, RBP, and a graded verdict) section is ever touched. This is also just
this project's own long-standing discipline (raw per-match files are "immutable, never edited after
creation") — the research confirms it's not an idiosyncratic habit, it's the standard shape professional
trading operations use for exactly this reason.

---

## Net format adopted for this repo

Combining the five sources above into one shape, every match write-up in `matches/` is:

1. **Match header** — score, date, stakes (docs-as-code: README as entry point).
2. **Per-question sections** — pre-trade (data/scripts/reasoning/submission) → settlement (outcome/RBP/grade),
   the transaction-cost-analysis shape, citing back to `decisions/` ADRs where a standing rule applied.
3. **Match-level postmortem** — the Google SRE five-question shape, blameless, with trackable action items.
4. **Sources / artifacts** — every script and data file that fed into the match, so the write-up is
   reproducible, not just narrated.

No claim in a match write-up should be un-traceable to a specific script, file, or platform screenshot —
the same standard docs-as-code applies to source code: if it isn't in the repo, it isn't documented.