# JTC / SportsPredict Forecasting Research

A solo, ongoing research project forecasting 2026 World Cup matches for the
**Jump Probability Cup (JTC)**, a prediction tournament on
`play.sportspredict.com`. Combines from-scratch statistical modeling
(Elo, Poisson, Dixon-Coles, ordered logit), a tiered data-source reliability
audit, an empirically-fit crowd-bias correction model, a rejected
machine-learning layer (kept and reported rather than deleted, see below),
and a live, tracked track record.

## Start here

- **[`JTC_WC2026_Research_Paper.Rmd`](JTC_WC2026_Research_Paper.Rmd) /
  [`.pdf`](JTC_WC2026_Research_Paper.pdf)** — the paper. Full campaign
  results, the crowd-compression model, and a dedicated section reporting
  four independent tests for why a learned blend of my own estimate and the
  crowd's was rejected in favour of the hand-built pipeline.
- **[`FRA_MAR_Full_Case_Study.Rmd`](FRA_MAR_Full_Case_Study.Rmd) /
  [`.pdf`](FRA_MAR_Full_Case_Study.pdf)** — a complete single-match case
  study (France vs. Morocco, quarterfinal), including two corrections made
  in view rather than absorbed silently before publication.
- **[`BRAZIL_VS_NORWAY_CASE_STUDY.md`](BRAZIL_VS_NORWAY_CASE_STUDY.md)** — a
  second complete single-match case study, documenting the live validation
  (and a same-week counter-example) of a cross-match pricing pattern.
- **[`JTC_PROJECT_WRITEUP.md`](JTC_PROJECT_WRITEUP.md)** — the longer-form
  internal research log the paper above was distilled from; more granular,
  less polished, useful if you want the full reasoning trail behind a
  specific claim in the paper.

This repo is **live** — it changes as the tournament progresses. Matches get
added, rules get revised when they fail, datasets get rebuilt. The structure
below is designed so new matches/experiments slot in without reorganizing
anything.

## Layout

The project is organized in layers, raw → processed → modeled → written up.
Layers map to existing folders; nothing is renamed match-to-match.

| Layer | Folder | What lives there |
|---|---|---|
| Literature | `papers/`, `research_notes.md` | Academic papers (Dixon-Coles, Karlis-Ntzoufras, etc.) and the literature review they're synthesized into |
| Raw, immutable | `data/external_markets/`, `matches/{Team1}_vs_{Team2}/` | One JSON (or, from late June onward, a set of numbered layer files: ESPN data, Smarkets markets, model derivations, rules applied, estimates, post-match results) per match: research inputs, applied rules, final submissions, post-match outcomes. **Never edited after the fact** — reprocessing always reads these and writes to a new derived file |
| Raw, third-party | `data/external/{transfermarkt,odds,fifa_ranking,travel,altitude}/` | Bulk third-party downloads. The large bulk dumps (Transfermarkt's full club-football export, full odds history) are **not committed** — see "Regenerating excluded data" below |
| Extracted/filtered | `data/external/transfermarkt/extracted/`, `data/external/odds/international_fixture_odds.csv` | The small, already-filtered subset of the above that the models actually use — committed in full |
| Processed | `data/processed/`, `data/international_results/`, `data/soccer-elo/` | Point-in-time Elo panels, historical results, derived reference data |
| Mart | `datasets/` | `master_question_dataset.csv` — the flat, one-row-per-question dataset everything else rolls up to, plus its data dictionary and build script. `datasets/archive/` holds superseded snapshots kept for audit purposes, never the active dataset |
| Modeling | `model/` | Elo, Poisson goal-rate regression, Dixon-Coles correction, ordered logit, backtesting harnesses |
| ML / calibration | `ml/` | Feature matrix build, Platt-scaling diagnostic, and the meta-model / linear-regression / t-test experiments reported in the paper's "Rejection of Learned Blending Models" section — all four kept and documented rather than deleted after failing |
| Pipeline / bot | `bot/` | Live data collection: fetching matches/markets from the platform, market classification, competitor benchmarking |
| Operational logs | `bash_logs/` | Per-session research logs, kept for reproducibility/audit trail |
| Docs / writeups | top-level `*.md` | This README, the project writeup, and a series of dated research notes (crowd-bias updates, postmortems, data audits) each covering a specific finding referenced from the paper |

## Regenerating excluded data

Two third-party datasets are excluded from git (large, third-party, freely
re-downloadable) but the code to rebuild the small extracted versions is
included:

- `data/external/transfermarkt/extract_relevant.py` — run against a fresh
  download of the public `transfermarkt-datasets` export to regenerate
  `data/external/transfermarkt/extracted/*.csv`.
- `data/external/odds/extract_international_odds.py` — run against a fresh
  download of the odds source to regenerate
  `data/external/odds/international_fixture_odds.csv`.

## A standing rule worth knowing before touching this repo

Raw data is never mutated in place. Any reprocessing reads an existing raw
file and writes its output to a new, separate file. This is what makes the
per-match JSON files in `data/external_markets/` a trustworthy audit trail.

## Status

Actively maintained through the 2026 World Cup; the tournament is still
live, so headline numbers in the paper carry a stated as-of date rather than
a claim of finality. See the paper's own "Future Work" section for planned
next steps, or [`PAPER_REVISION_NOTES.md`](PAPER_REVISION_NOTES.md) for the
working notes behind the paper's most recent revision.
