# JTC / SportsPredict Forecasting Research

A solo, ongoing research project forecasting 2026 World Cup matches for the
**Jump Probability Cup (JTC)**, a prediction tournament on
`play.sportspredict.com`. Combines from-scratch statistical modeling
(Elo, Poisson, Dixon-Coles, ordered logit), a tiered data-source reliability
audit, an empirically-fit crowd-bias correction model, and a live, tracked
track record.

**Start here:** [`JTC_PROJECT_WRITEUP.md`](JTC_PROJECT_WRITEUP.md) — the full
writeup (motivation, literature review, data, methodology, crowd-bias model,
calibration, track record, limitations, future work).

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
| Raw, immutable | `data/external_markets/` | One JSON per match: research inputs, applied rules, final submissions, post-match outcomes. **Never edited after the fact** — reprocessing always reads these and writes to a new derived file |
| Raw, third-party | `data/external/{transfermarkt,odds,fifa_ranking,travel,altitude}/` | Bulk third-party downloads. The large bulk dumps (Transfermarkt's full club-football export, full odds history) are **not committed** — see "Regenerating excluded data" below |
| Extracted/filtered | `data/external/transfermarkt/extracted/`, `data/external/odds/international_fixture_odds.csv` | The small, already-filtered subset of the above that the models actually use — committed in full |
| Processed | `data/processed/`, `data/international_results/`, `data/soccer-elo/` | Point-in-time Elo panels, historical results, derived reference data |
| Mart | `datasets/` | `master_question_dataset.csv` — the flat, one-row-per-question dataset everything else rolls up to, plus its data dictionary and build script |
| Modeling | `model/` | Elo, Poisson goal-rate regression, Dixon-Coles correction, ordered logit, backtesting harnesses |
| ML / calibration | `ml/` | Feature matrix build + Platt-scaling calibration diagnostic on the live submission record |
| Pipeline / bot | `bot/` | Live data collection: fetching matches/markets from the platform, market classification, competitor benchmarking |
| Operational logs | `bash_logs/` | Per-session research logs, kept for reproducibility/audit trail |
| Docs / writeups | top-level `*.md` | This README, the project writeup, the documentation-structure research, per-session notebooks |

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

Private repo, actively maintained through the 2026 World Cup. See
[`JTC_PROJECT_WRITEUP.md`](JTC_PROJECT_WRITEUP.md) Section 11 for planned
next steps.
