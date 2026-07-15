# JTC / SportsPredict Forecasting Research

A solo, ongoing research project that predicts outcomes of 2026 FIFA World Cup football matches
for the **Jump Probability Cup (JTC)**, a forecasting tournament on `play.sportspredict.com`. This
repository is the complete lab notebook: every model, every dataset, every prediction, every win
and every loss, kept and documented rather than cleaned up after the fact.

You don't need to know anything about football to follow this README. Wherever a football term
first appears, it's explained inline.

---

## Table of contents

1. [What is this, actually?](#1-what-is-this-actually)
2. [How the tournament works, in plain English](#2-how-the-tournament-works-in-plain-english)
3. [What this repo does about it](#3-what-this-repo-does-about-it)
4. [Current status](#4-current-status)
5. [How to find things in this repo](#5-how-to-find-things-in-this-repo)
6. [Repository structure](#6-repository-structure)
7. [The methodology, in two passes](#7-the-methodology-in-two-passes)
8. [Where the data comes from](#8-where-the-data-comes-from)
9. [Running things yourself](#9-running-things-yourself)
10. [Project rules worth knowing before you touch anything](#10-project-rules-worth-knowing-before-you-touch-anything)
11. [Key findings so far](#11-key-findings-so-far)
12. [Full documentation index](#12-full-documentation-index)
13. [Status](#13-status)

---

## 1. What is this, actually?

Picture a competition where, instead of picking winners, you have to say **how confident** you
are. Not "France wins" but "I think France has a 62% chance of winning." You do this for roughly
15 questions per football match — not just who wins, but things like whether there will be more
than 8 corners, whether a specific player scores, whether either team gets a red card. Then your
confidence numbers get compared against the actual outcome *and* against everyone else's numbers,
using a scoring rule that rewards being well-calibrated (confident when you're right, appropriately
uncertain when you're not) rather than just being right.

That competition is the JTC. This repository is one person's (Souparneya's) attempt to answer
those questions systematically — using real statistical models fit on decades of match history,
rather than gut feel — and to keep an honest, complete record of what worked, what didn't, and why.

## 2. How the tournament works, in plain English

- **The platform** (`play.sportspredict.com`) posts a set of questions before each World Cup
  match, closing when the match kicks off.
- **Everyone submits a probability** (0–100%) for each question. There's also a **crowd
  consensus** — roughly, the average of everyone else's submissions — which acts as a benchmark.
- **After the match**, each question resolves YES or NO (or a number, for things like total
  goals), and everyone gets scored.
- **The scoring rule** is a variant of the **Brier score** (the standard way statisticians score
  probability forecasts — smaller is better, and it punishes overconfidence harshly: saying "99%
  sure" and being wrong costs far more than saying "60% sure" and being wrong). The platform's own
  version, **Relative Brier Points (RBP)**, scores you *relative to the crowd* — beating the crowd
  earns positive RBP, losing to it costs points. This is the number you'll see everywhere in this
  repo (e.g. "+138.32 RBP").
- **Football terms used throughout**, translated: a match has two **halves** (45 minutes each,
  plus **extra time** in knockout rounds if still tied); a **corner** is a restart awarded when
  the ball goes out over the defending team's goal line off a defender; a **card** (yellow or red)
  is a referee's disciplinary sanction; **shots on target (SOT)** are shots that would have scored
  without a save or block; **offside** is a positional rule violation that cancels an attack;
  **VAR** is video-assisted refereeing, used to review contested decisions; a **hydration break**
  is a scheduled water break in hot conditions (used as a natural checkpoint for some questions,
  e.g. "will a goal happen between the two hydration breaks").

## 3. What this repo does about it

The short version: **pull historical data → fit statistical models → combine model output with
any real market price that exists → apply hard-won situational rules → submit a number → record
what actually happened → learn from it.**

Longer version, as an actual pipeline:

1. **Historical data collection** (`data/`, `datasets/`) — nearly 50,000 international football
   matches back to 1872, plus detailed event-level data (every shot, card, corner) for the last
   two World Cups, plus squad values, travel distance, venue altitude, and betting-market history.
2. **Classical statistical models** (`topics/match-winner-goals-totals/`, `model/`) — an Elo
   rating system (the same family of rating used in chess) adapted for football, feeding a
   Poisson goal-scoring model and a Dixon-Coles correction (a well-known 1997 refinement for
   low-scoring sports), plus a separate ordered-logistic-regression model fit directly on match
   outcomes.
3. **A newer machine-learning layer** (`topics/shots-on-target/`, `topics/cards/`,
   `topics/corners/`, `topics/offsides/`, etc.) — hierarchical statistical models (partial-pooling
   Poisson regressions) tested per question-type, under a strict **pre-registration** discipline:
   the hypothesis, the validation method, and the pass/fail bar are all written down *before* the
   model is fit, so there's no "try ten things, report the one that worked" bias. Two families
   passed (shots on target, corners); three failed (cards, offsides, first-substitution timing) —
   and the failures are documented just as thoroughly as the successes.
4. **Live market and crowd data** (`bot/`) — where a real, liquid betting market exists (via the
   Smarkets exchange), that price generally beats the model and gets priority. A large chunk of
   this project's research is about *when* to trust the market, when to trust the model, and when
   the crowd itself is a useful (if biased) signal.
5. **Named situational rules** — patterns discovered by tracing specific wins and losses back to
   their cause, written down, and reused (e.g. "never submit exactly 0% or 100%," or "in a
   lopsided match, the winning team fouls at least as much as the losing team regardless of
   historical averages"). There are 18 of these at the time of writing.
6. **Settlement and postmortems** (`matches/`, `writeups/`) — every match's final result, every
   question's actual RBP, and a written account of what was learned.

## 4. Current status

Pulled directly from the platform's own performance page on 2026-07-14 (source:
[`bot/PERFORMANCE_PAGE_DISCOVERY_2026-07-14.md`](bot/PERFORMANCE_PAGE_DISCOVERY_2026-07-14.md)):

| Metric | Value |
|---|---|
| Forecasts settled | 986 |
| RBP gap vs. the crowd | +3.9 (better than 89% of forecasters on the platform) |
| Contrarian win rate | 50% (when disagreeing with the crowd, right half the time) |
| Confidence bias | +2% (very close to perfectly calibrated) |

A note on precision, in the spirit of this project's own habit of disclosing data-quality issues
rather than hiding them: several **locally-computed** cumulative-RBP totals exist in this repo's
history (from different rebuilds of `datasets/master_question_dataset.csv` at different points in
the campaign), and they don't all agree with each other — this is tracked and explained in
[`JTC_PROJECT_WRITEUP.md`](JTC_PROJECT_WRITEUP.md) §8. The table above is the one number in this
README that comes directly from the platform itself rather than a local recomputation, which is
why it's the one quoted here.

The tournament is still in progress (knockout stage, semifinals settled as of this writing), so
none of these numbers are final.

## 5. How to find things in this repo

This repo has three complementary ways to navigate it, each answering a different question:

| If you want to know... | Go to... |
|---|---|
| "How do we price *this kind of question* — e.g. total cards — across every match?" | [`topics/`](topics/) — one folder per question type, each with its own model, track record, and links to everything relevant. **Start here for anything methodology-related.** |
| "What happened in *this specific match*?" | [`matches/<Team1>_vs_<Team2>/`](matches/) — the full research trail and settlement record for one fixture. |
| "Where is *this exact file*, and what does it contain?" | [`REPO_MAP.md`](REPO_MAP.md) — a complete, file-by-file catalog of the entire repository (~860 files), organized by directory. |
| "Give me the polished, narrative writeup of a match, like a professional trading desk would produce." | [`writeups/`](writeups/) — formal, cross-linked match reports, plus the standing decisions (see below) that govern how every match is priced. |

For everything else — the reasoning behind a specific rule, a specific number, a specific decision
— [`REPO_MAP.md`](REPO_MAP.md) is the map of the whole territory and links out to the right file.

## 6. Repository structure

```
topics/              Question-type navigation (start here) — one folder per question family:
                        shots-on-target/, cards/, corners/, offsides/, first-substitution/,
                        player-props/, match-winner-goals-totals/, plus 6 smaller stub topics
matches/              One folder per match: raw data pulled, models applied, final prediction,
                        and (once played) the settled outcome and score
writeups/             Polished, cross-linked narrative writeups + standing methodology decisions
model/                model/elo.py — the Elo update formula and historical-panel builder every
                        topic depends on. Point-in-time for 2026 fixtures specifically comes from
                        a replay layer on top (ml/backtests/), not this file alone — see §11
ml/                   Track-record-wide diagnostics: calibration checks, and four separate,
                        honestly-reported experiments testing whether a learned blending model
                        could beat the hand-built pipeline (answer: not yet, and here's why)
  ml/backtests/          Shared backtesting infrastructure for the topics/ model families
data/                  Raw and processed data: ~50,000 historical matches, ESPN box scores,
                        StatsBomb event data, betting markets, squad values, travel/altitude
datasets/              The flattened, analysis-ready master dataset built from data/
bot/                   The live pipeline: pulls matches/markets from the platform and from
                        Smarkets (a betting exchange), generates draft predictions for review
papers/                Five academic papers this project's models are built on
scripts/               Small repo-maintenance utilities (e.g. the markdown link checker)
bash_logs/             Raw session transcripts, kept for reproducibility
*.md (repo root)       ~26 research memos and postmortems — the project's running lab notebook;
                        see REPO_MAP.md §1 for what each one covers
JTC_WC2026_Research_Paper.{Rmd,pdf}   The formal write-up of the whole campaign
FRA_MAR_Full_Case_Study.{Rmd,pdf}     A complete single-match case study
REPO_MAP.md            Complete file-by-file catalog of this repository
```

## 7. The methodology, in two passes

**Plain English:** every team gets a skill rating that goes up when they win and down when they
lose, adjusted by how good the opponent was (the same idea chess ratings use). That rating
predicts how many goals each team is likely to score, which in turn answers "who wins" and "how
many total goals" questions. For anything more specific — cards, corners, shots on target — a
newer set of models learns each team's own tendency, blended carefully with the tournament-wide
average so one unusual match doesn't overwhelm the estimate, and adjusted by strength of opponent.
Every one of these models is tested by pretending to stand at a past point in time, using only
data that would genuinely have been available then, and checking whether it would actually have
beaten a much simpler benchmark. Most of the time, the honest answer is "not by enough to trust."

**Technical:** a K=60 point-in-time Elo system (FIFA World Cup weighting, margin-of-victory
G-factor, home-advantage restricted to genuine USA/MEX/CAN participants) feeds a Poisson
goal-rate GLM with a Dixon-Coles low-score correction and Negative-Binomial overdispersion
adjustment, plus a parallel ordered-logistic-regression track fit directly on match outcome. A
newer layer adds hierarchical (partial-pooling) Poisson GLMMs per question family — team random
intercepts, an Elo-difference fixed effect, a data-source fixed effect distinguishing ESPN
box-score data from StatsBomb event-level data — validated via walk-forward backtesting with
match-clustered bootstrap significance testing and Benjamini-Hochberg FDR correction across
families, under a pre-registration discipline (hypothesis and promotion criterion written and
committed before any model is fit). See [`topics/`](topics/) for the full, family-by-family
results, and [`JTC_WC2026_Research_Paper.pdf`](JTC_WC2026_Research_Paper.pdf) for the complete
write-up with citations.

## 8. Where the data comes from

| Source | What it provides | Used for |
|---|---|---|
| [martj42/international_results](data/international_results/) | ~50,000 international match results, 1872–present | The historical training panel for Elo and the goal models |
| [StatsBomb open data](data/external/statsbomb/) | Event-level data (every pass, shot, card, corner) for the last two World Cups | Training data for the newer hierarchical models |
| ESPN | Box scores and play-by-play for every 2026 World Cup match, pulled live | Point-in-time team form, referee data, timing data |
| Smarkets | A real betting exchange — live market prices where they exist | The benchmark this project's own estimates are checked against, and priority source when liquid |
| Transfermarkt | Squad market value, average age, FIFA ranking | Contextual features (does a big favorite have an unusually weak/strong squad) |
| SportsPredict's own API | The questions themselves, the crowd consensus, and settled results | Everything — this is the platform the whole project serves |

Full sourcing, licensing, and data-quality notes for each are in
[`REPO_MAP.md`](REPO_MAP.md) §4.

## 9. Running things yourself

There's no single install script — this is a research repo, not a packaged tool — but everything
is plain Python and R with common libraries, no exotic dependencies.

**Python** (3.x): `pandas`, `numpy`, `scipy`, `statsmodels`, `scikit-learn`, `matplotlib`,
`requests`.

**R**: `dplyr`, `lme4` (for the hierarchical GLMMs), `jsonlite`, `lmtest`, `sandwich` (cluster-
robust standard errors), `ggplot2`. The two formal papers (`.Rmd` files) additionally need
`rmarkdown` to knit to PDF.

A representative example — rebuilding the historical Elo panel from scratch:

```bash
python3 model/elo.py
```

Note this alone reproduces the pre-tournament baseline, not a current 2026 rating (see §11) —
for a genuinely current point-in-time Elo panel, run:

```bash
python3 ml/backtests/build_full_tournament_pit_elo.py
```

Or running one of the topic backtests (from the repo root, since paths are root-relative):

```bash
Rscript topics/shots-on-target/walk_forward_sot_backtest.R
```

Each script's own docstring/header comment documents its inputs and outputs. After moving or
renaming any file, run the repo-wide link checker:

```bash
python3 scripts/verify_md_links.py
```

## 10. Project rules worth knowing before you touch anything

- **Raw data is never mutated in place.** Any reprocessing reads an existing raw file and writes
  its output to a new, separate file. This is what makes the per-match records a trustworthy audit
  trail.
- **Genuinely shared data and infrastructure is never duplicated per topic.** The Elo panels, the
  training datasets, and the shared backtesting library live in one place (`model/`,
  `data/processed/`, `ml/backtests/`) and are linked from every `topics/` folder that depends on
  them, not copied into each one.
- **Negative results are kept, not deleted.** Four separate attempts at a learned blending model
  failed to beat the hand-built pipeline; all four are documented in `ml/` with their actual
  numbers, because a repo that only shows what worked isn't a trustworthy record of what was
  actually tried.
- **New models are pre-registered.** The hypothesis, the validation method, and the pass/fail bar
  are written down before the model is fit — see any `PREREGISTRATION_*.md` file for the pattern.

## 11. Key findings so far

- **The crowd is structurally biased, not just imperfect — but deliberately exploiting that bias
  doesn't work, and the project's own data says so.** The platform's crowd consensus compresses
  toward 50% in a measurable, fittable way (`crowd ≈ 0.50 + 0.61 × (our estimate − 0.50)`,
  independently re-fit three times as the sample grew — n=85, n=384, n=772 — with the slope
  essentially unchanged each time, r≈0.83 throughout). That part is solid. What doesn't hold up:
  a match-level test of whether deviating further from the crowd earns more RBP (the statistically
  correct way to ask the question, since ~15 questions per match aren't independent observations)
  finds the *opposite* — more deviation is weakly associated with *lower* RBP (n=71 matches,
  p=0.056). A regression of RBP on crowd-deviation gets R²=0.053 and loses to a naive baseline
  out-of-sample. And there's a closed-form reason why: under this scoring rule, deliberately
  pushing a submission past a genuinely calibrated estimate costs exactly S·δ² in expectation — a
  guaranteed loss with no offsetting upside. The one live attempt to do this anyway (Canada vs.
  Morocco, pushing past a calibrated market price) cost **-80.83 RBP, the campaign's worst single
  result**. The real source of edge is narrower and less flattering: at the original n=85 check,
  the crowd's *raw* Brier score was actually *better* than the project's own (0.2268 vs. 0.2424),
  and the individual-question win rate was 52.9% — barely above a coin flip. The positive
  cumulative RBP came from winning big on a handful of high-leverage, well-grounded calls, while
  occasionally losing big on overconfident ones — removing just the single worst loss from that
  sample would have raised total RBP by 37%. The crowd-compression regression is genuinely useful
  as a **diagnostic** (it flags which questions the crowd is likely wrong about, and RULE12 uses
  the compressed value as a floor when shrinking a low-confidence estimate) — it just isn't a lever
  you can safely pull harder for more points. See
  [`JTC_WC2026_Research_Paper.pdf`](JTC_WC2026_Research_Paper.pdf) (the "Rejection of Learned
  Blending Models" section) for the full four-test case.
- **The point-in-time Elo claim is true, but only because a known staleness bug is actively routed
  around, not because it can't happen.** `data/international_results/results.csv` records every
  2026 World Cup match's score as `NA` (it's a fixture list, not a results file), so the base
  `model/elo.py` pipeline never actually processes a single 2026 result — its output,
  `data/processed/elo_current_ratings.csv`, is genuinely frozen at pre-tournament (early June)
  values (confirmed: file untouched since June 10, the day before the tournament started). The bug
  was caught by a sanity check: Argentina's listed Elo was *identical* (2189.5282) across all three
  of its group-stage matches despite winning 3-0, 2-0, and 3-1 — a rating that doesn't move after
  three wins is not a live rating. Left uncorrected, this kind of staleness is not cosmetic: in one
  traced case (Spain vs. Belgium, quarterfinal), the frozen rating overstated Spain's Elo edge by
  **64.23 points** relative to the correct point-in-time value, because it was blind to Belgium's
  4-1 demolition of the USA in the round before. Every actual 2026 prediction in this repo uses a
  separate, dedicated point-in-time replay (`ml/backtests/build_full_tournament_pit_elo.py` for the
  systematic panel, plus a same-day, fixture-specific replay script for whichever match is being
  priced next) that replays real results through the same update formula — not the frozen base
  output. This is disclosed, not hidden, specifically so a reviewer checking the "point-in-time
  Elo" claim in this README can verify it rather than take it on faith.
- **A liquid market beats a domain model, every time one exists.** See
  [`writeups/decisions/0001-market-priority-over-domain-model.md`](writeups/decisions/0001-market-priority-over-domain-model.md).
- **Machine learning helps in some places and not others, and both are worth knowing.** The
  hierarchical models pass for shots on target and corners; they fail for cards (even after a
  second, more targeted attempt with referee data) and offsides (where an early false-positive
  pass turned out to be an 8.49x data-extraction bug, caught and retracted the same day it was
  found — see [`topics/offsides/`](topics/offsides/README.md)).
- **Confident personal overrides of researched estimates are the single worst pattern in this
  project's history.** The worst individual result on record (-51.97 RBP) came from overriding a
  carefully researched 58–60% estimate to a gut-call 100% — which is why RULE6 ("never submit 0%
  or 100%") exists and is enforced everywhere now.

## 12. Full documentation index

- **[`REPO_MAP.md`](REPO_MAP.md)** — complete file-by-file catalog of the whole repository.
- **[`topics/`](topics/)** — question-type navigation; start here for methodology questions.
- **[`writeups/`](writeups/)** — polished match writeups and standing methodology decisions.
- **[`JTC_WC2026_Research_Paper.pdf`](JTC_WC2026_Research_Paper.pdf)** — the formal paper: full
  campaign results, the crowd-compression model, and the case for why a learned blend of estimate
  and crowd was rejected in favor of the hand-built pipeline.
- **[`FRA_MAR_Full_Case_Study.pdf`](FRA_MAR_Full_Case_Study.pdf)** and
  **[`BRAZIL_VS_NORWAY_CASE_STUDY.md`](BRAZIL_VS_NORWAY_CASE_STUDY.md)** — two complete
  single-match case studies, including corrections made in view rather than absorbed silently.
- **[`JTC_PROJECT_WRITEUP.md`](JTC_PROJECT_WRITEUP.md)** — the longer, less-polished internal
  research log the paper was distilled from; useful for the full reasoning trail behind any
  specific claim.
- **[`PROJECT_STRUCTURE_RESEARCH_2026-07-14.md`](PROJECT_STRUCTURE_RESEARCH_2026-07-14.md)** — the
  research behind why this repo is organized the way it is (the `topics/` layer, in particular).

## 13. Status

Actively maintained through the 2026 World Cup; the tournament is still live, so headline numbers
carry a stated as-of date rather than a claim of finality. See
[`PROJECT_TODO.md`](PROJECT_TODO.md) for open items, or
[`PAPER_REVISION_NOTES.md`](PAPER_REVISION_NOTES.md) for the working notes behind the paper's most
recent revision.
