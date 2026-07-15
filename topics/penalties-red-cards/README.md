# Penalties / Red Cards

Pricing for disciplinary rare-event questions (penalty awarded, red card shown). No dedicated
scripts of its own — a stub folder completing the 14-topic taxonomy. Priced via compound
(inclusion-exclusion) probability combining base rates from the general match-stats pipeline,
not a standalone fitted model.

## Current status

No dedicated backtest exists for this family. Pricing logic (RULE4: compound-question
inclusion-exclusion combination) lives in the root-level lab notebook and per-match rule-application
files, not in a script here.

## Shared inputs

| Path | Role |
|---|---|
| `data/processed/referee_card_panel.csv` moved to `../cards/` | Red-card component overlaps with the cards family's referee-rate data. |
| `matches/*/04_rules_applied.json` | Where RULE4's compound-probability application is actually recorded, per match. |

## Root-doc mentions

- [`ML_EXPERIMENTS_NOTEBOOK.md`](../../ML_EXPERIMENTS_NOTEBOOK.md) — RULE4 (compound-question crowd-weighting) origin and revisions.
