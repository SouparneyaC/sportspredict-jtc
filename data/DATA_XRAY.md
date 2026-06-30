# Data X-Ray: Jump Trading Competition Prediction Rig

**Written:** 2026-06-22  
**Purpose:** Complete inventory of every dataset, model artifact, and derived file in this project — what exists, what's in it, its quality/completeness, and its ML-readiness. This document is the prerequisite to any ML integration work.

**Core principle:** Model results are only as good as your data.

---

## Architecture Overview

Our data exists in four conceptual layers:

```
LAYER A: Per-Match Research Files (the source of truth)
  → Per-match JSON with pre-match estimates, Smarkets prices, and post-match outcomes

LAYER B: Historical Base Data (the training substrate)
  → 49k+ international matches with results, Elo ratings, rest/travel features

LAYER C: Derived Model Artifacts (fitted statistical models)
  → Poisson GLM, Dixon-Coles, Ordered Logit coefficients; fitted on Layer B

LAYER D: Supplementary Data (enrichment potential)
  → FIFA rankings, Transfermarkt players/valuations, altitude, betting odds
```

---

## LAYER A: Per-Match JSON Files (Primary Research Records)

**Location:** `data/external_markets/{match}_{date}.json`  
**Count:** ~30 match files  
**Role:** Source of truth for all JTC predictions and outcomes

### What's inside each file

Every file has these top-level keys:

| Key | Description |
|-----|-------------|
| `match` | e.g. "GHA-PAN" |
| `sportspredict_match_id` | JTC UUID |
| `smarkets_event_id` | Smarkets market ID |
| `espn_event_id` | ESPN event ID |
| `context_note` | Pre-match narrative: Elo/Poisson lambdas, key rules fired |
| `key_lambdas` | Expected goals per team (λ_home, λ_away), expected SOT |
| `smarkets_prices` | Dict of verified betting market prices (OU goals, BTTS, cards, corners, player SOT, etc.) |
| `rules_applied` | Which named rules (RULE1-RULE15) were used and why |
| `final_submission_estimates` | Our submitted probability per question (Q1–Q10), with confidence + note |
| `post_match_results` | Outcome, crowd estimate, RBP per question, match facts |

### Completeness audit (as of 2026-06-22)

| Match | Date | post_match? | Submissions filled? | Notes |
|-------|------|-------------|---------------------|-------|
| KOR-CZE | 2026-06-11 | YES | NO (0/6) | Early format, no submission estimates stored |
| CAN-BIH | 2026-06-12 | YES | NO (0/10) | Early format |
| USA-PAR | 2026-06-13 | YES | NO (0/10) | Early format |
| QAT-SUI | 2026-06-13 | YES | NO (0/10) | Early format |
| BRA-MAR | 2026-06-14 | YES | NO (0/10) | Early format |
| GER-CUR | 2026-06-14 | YES | NO (0/10) | Early format |
| JPN-NED | 2026-06-14 | YES | NO (0/10) | Early format |
| CIV-ECU | 2026-06-14 | YES | NO (0/10) | Early format; Q10 outcome unknown |
| SWE-TUN | 2026-06-15 | YES | NO (0/10) | Early format |
| BEL-EGY | 2026-06-15 | YES | NO (0/10) | Early format |
| SAU-URU | 2026-06-15 | YES | NO (0/10) | Early format |
| ENG-CRO | 2026-06-17 | YES | NO (0/10) | Missing submission estimates; Q7 submission error |
| GHA-PAN | 2026-06-17 | YES | NO (0/10) | Missing submission estimates |
| SUI-BIH | 2026-06-18 | YES | YES (12/12) | Fully populated; extra `confirmed_question_results_from_platform` |
| CAN-QAT | 2026-06-18 | YES | YES (10/10) | Fully populated |
| UZB-COL | 2026-06-18 | YES | NO (0/10) | Submission estimates were null; reconstructed from JTC platform |
| SCO-MAR | 2026-06-19 | YES | YES (10/10) | Fully populated; crowd estimates are ACTUAL platform values |
| MEX-KOR | 2026-06-19 | YES | YES (10/10) | Fully populated |
| USA-AUS | 2026-06-19 | YES | YES (10/10) | Fully populated |
| BRA-HAI | 2026-06-20 | YES | YES (10/10) | Fully populated |
| GER-CIV | 2026-06-20 | YES | YES (10/10) | Fully populated |
| NED-SWE | 2026-06-20 | YES | YES (10/10) | Fully populated |
| TUR-PAR | 2026-06-20 | YES | YES (10/10) | Fully populated |
| BEL-IRN | 2026-06-21 | YES | YES (10/10) | Fully populated |
| URU-CPV | 2026-06-21 | YES | YES (10/10) | No submission — calibration only |
| ECU-CUR | 2026-06-21 | YES | YES (10/10) | Fully populated |
| ESP-KSA | 2026-06-21 | YES | YES (10/10) | Fully populated |
| JPN-TUN | 2026-06-21 | YES | YES (10/10) | Fully populated |
| NZL-EGY | 2026-06-22 | YES | YES (10/10) | Fully populated |

**Key gap:** Matches before ~2026-06-18 have `final_submission_estimates` not machine-readable (estimates stored as null or in a different schema version). The early files have the outcomes in `post_match_results` but not the machine-readable submission estimates. To build an ML feature matrix, the early match estimates would need to be extracted from the `post_match_results.question_results` `our_estimate` fields.

### Post-match question_results structure (machine-readable in all files with post_match)

```python
{
  "Q1_...": {
    "our_estimate": float,      # our submitted probability 0-1
    "crowd_estimate": float,    # JTC crowd consensus 0-1
    "outcome": int,             # 1 = YES, 0 = NO
    "rbp": float,               # Relative Brier Points (positive = beat crowd)
    "beat_crowd": bool,
    "notes": str
  },
  ...
}
```

---

## LAYER A2: Settled Markets Ledger (Stale Aggregation)

**File:** `data/external_markets/settled_markets_ledger.json`  
**Status: ⚠️ STALE — last updated 2026-06-15, covers only first 11 matches**

This was our cross-match aggregation table with schema:
- `match`, `q`, `question`, `category`, `us`, `crowd`, `outcome`, `rbp`
- Also has `category_summary` stats by methodology type

**Do NOT use this as an ML training source** — it is missing the most recent ~19 matches. It must be regenerated from the individual JSON files if needed.

**Category definitions it tracks:**
- `tier1_market` — direct Smarkets/Polymarket quote
- `tier2_realdata` — Poisson/Skellam model from ESPN data
- `stats_proxy` — general base rates
- `compound_market_proxy` — P(A) × P(B) from market components
- `skellam_market_hybrid` — Skellam model anchored to market handicap
- `match_winner_deferred_market` — avg(crowd, market)
- `match_winner_gut_override` — human override (worst category, n=1, -51.97)

---

## LAYER A3: Match Log (Master Index)

**File:** `data/external_markets/MATCH_LOG.md`  
**Status:** Last table entry is BEL-EGY (2026-06-15). Needs updating.  
Contains rich per-match postmortems and rule discoveries.

---

## LAYER B: Historical Base Data

### B1: International Match Results

**File:** `data/international_results/results.csv`  
**Rows:** 49,473 (from 1872 to present)  
**Columns:** `date, home_team, away_team, home_score, away_score, tournament, city, country, neutral`  
**Source:** GitHub repo (auto-updated)  
**Quality:** ✅ High — well-maintained community dataset  
**ML role:** Foundation for all statistical modeling; provides the outcome variable (W/D/L, goals) and match identifiers

### B2: Elo Match Panel

**File:** `data/processed/elo_match_panel.csv`  
**Rows:** 49,473 (one per match, mirrors results.csv)  
**Columns:** `date, home_team, away_team, home_score, away_score, tournament, neutral, k_factor, elo_home_pre, elo_away_pre`  
**Quality:** ✅ High — derived by `model/elo.py` running walk-forward on results.csv  
**ML role:** Core feature source. `elo_home_pre - elo_away_pre` = the primary match-strength signal.  
**Key fact:** Uses `xi=0.0008` exponential time-decay weighting (recency-weighted MLE).

### B3: Current Elo Ratings

**File:** `data/processed/elo_current_ratings.csv`  
**Rows:** 337 teams  
**Columns:** `team, elo_rating`  
**Quality:** ✅ High — end state of the walk-forward Elo computation  
**ML role:** Lookup for any new match prediction

### B4: Rest Days / Travel Features

**File:** `data/external/travel/rest_days_features.csv`  
**Rows:** 98,801 (two rows per match — one per team side)  
**Columns:** `date, team, side, opponent, rest_days`  
**Quality:** ⚠️ Medium — rest_days is null for first appearance of each team  
**ML role:** Potential fatigue/recovery feature. Covers full results history.

Other travel files:
- `team_venue_distances.csv` — travel distance per match (ML potential: congestion effect)
- `wc2026_venue_coords.csv` — lat/lon of WC2026 venues

### B5: Soccer-Elo Archive (Alternative Elo Source)

**File:** `data/soccer-elo/csv/ranking_soccer_1901-2023.csv`  
**Quality:** External GitHub repo  
**ML role:** Cross-validation / alternative Elo signal if needed

---

## LAYER C: Fitted Statistical Model Artifacts

All fitted on `elo_match_panel.csv` (49,400 matches) with `xi=0.0008` time-decay weighting.

### C1: Poisson Goals Model

**File:** `data/processed/poisson_goals_coefs.json`  
```json
{
  "intercept": 0.104,
  "home_advantage": 0.230,
  "elo_diff_coef": 0.00181,
  "xi_decay": 0.0008,
  "n_matches": 49400,
  "n_observations": 98800
}
```
**Model:** `log(λ_goals) = intercept + home_adv × home + elo_diff_coef × (elo_home - elo_away)`  
**ML role:** Baseline for Poisson λ inputs; still used for per-match prop estimation.

### C2: Negative Binomial Dispersion

**File:** `data/processed/nb_dispersion_coefs.json`  
```json
{"alpha": 0.099, "rho_nb": -0.05, "n_observations": 98800}
```
**ML role:** Over-dispersion correction for goal count props.

### C3: Ordered Logit (Match Winner)

**File:** `data/processed/ordered_logit_coefs.json`  
```json
{
  "b_elo": 0.00520,
  "b_home": 0.377,
  "c1": -0.770,
  "c2": 0.555,
  "xi_decay": 0.0008,
  "n_matches": 49400
}
```
**Model:** Proportional-odds logit on `elo_diff + home_advantage` → P(Away win), P(Draw), P(Home win)  
**Directly implements Hvattum & Arntzen (2010).**  
**ML role:** Current best match-winner estimator. Primary input for Q7-style "will Team X win" questions.

### C4: Model Code

| File | Purpose |
|------|---------|
| `model/elo.py` | Elo rating system with k-factor and time-decay |
| `model/poisson_goals.py` | Poisson GLM, goal-count predictions |
| `model/dixon_coles.py` | Dixon-Coles scoreline grid (adds low-score correlation) |
| `model/ordered_logit.py` | Ordered logit for W/D/L |
| `model/fit_nb_dispersion.py` | NB dispersion fit |
| `model/fit_rho.py` | DC rho parameter fit |
| `model/backtest_harness.py` | Walk-forward backtesting infrastructure |
| `model/backtest_vs_market.py` | Model vs. market comparison |
| `model/backtest_diagnostics.py` | Calibration diagnostics (Brier, RPS, calibration buckets) |
| `model/predict.py` | Main prediction pipeline |
| `model/predict_ordered_logit.py` | Ordered logit prediction path |

---

## LAYER D: Supplementary / Enrichment Data

### D1: FIFA Rankings (Historical)

**File:** `data/external/fifa_ranking/ranking_fifa_historical.csv`  
**Rows:** 67,895  
**Columns:** `team, total_points, date, id, id_num, team_short`  
**Coverage:** Multiple ranking snapshots (structure suggests 2020+ era but needs verification)  
**ML role:** Alternative team-strength signal to Elo; FIFA points encode a different weighting of results  
**Note:** `fifa_ranking-2020-12-10.csv` is a single snapshot (2020)

### D2: Transfermarkt — National Team Players

**File:** `data/external/transfermarkt/extracted/national_team_players.csv`  
**Rows:** 2,455 (current national team squad members)  
**Key columns:** `player_id, name, position, sub_position, market_value_in_eur, international_caps, international_goals, current_national_team_id`  
**ML role:** Squad-level aggregation features — average squad value, positional depth. High potential for prop-level modeling (player SOT questions).

### D3: Transfermarkt — Historical Player Valuations

**File:** `data/external/transfermarkt/extracted/national_team_player_valuations.csv`  
**Rows:** 7,251  
**Key columns:** `player_id, date, market_value_in_eur, current_club_name`  
**ML role:** Time-varying squad value series — could construct "squad value at time of match" features

### D4: Transfermarkt — National Team Games (Competition History)

**File:** `data/external/transfermarkt/extracted/national_team_games.csv`  
**Rows:** 671 (national team competition matches only — WC, Euros, etc.)  
**Key columns:** `game_id, competition_id, season, round, date, home_club_name, away_club_name, home_club_goals, away_club_goals, home_club_formation, away_club_formation, stadium, attendance`  
**ML role:** Formation data is interesting — only 671 rows, coverage likely incomplete

### D5: Transfermarkt Full Datasets (Compressed)

**Location:** `data/external/transfermarkt/transfermarkt-datasets/*.csv.gz`  
**Files:** games, appearances, clubs, competitions, countries, game_events, game_lineups, games, national_teams, player_valuations, players, transfers  
**Status:** ⚠️ Compressed with gzip; use `gunzip` or `gzip -d` (not `zcat` on macOS). Sizes unknown but likely large.  
**ML role:** Very high potential — appearances data would provide per-player match-level stats; game_lineups would enable starting XI analysis; game_events would enable in-match event modeling. Requires extraction pipeline work.

### D6: Historical Betting Odds

**File:** `data/external/odds/international_fixture_odds.csv`  
**Rows:** 564  
**Columns:** `fixture_id, date, league_name, home_team, away_team, goals_home, goals_away, bookmaker, home_win, draw, away_win, source`  
**Coverage:** Primarily WC2022 knockout rounds + select international friendlies/qualifiers (2022-2026)  
**Quality:** ✅ High (API-Football closing odds, Pinnacle included)  
**ML role:** Can anchor model calibration against market; could train a "model-vs-market blend" signal. Small dataset (564 rows).

### D7: WC2026 Venue Altitude

**File:** `data/external/altitude/wc2026_venue_altitude.csv`  
**Rows:** 17 (one per WC2026 venue)  
**Columns:** `city, country, stadium, altitude_m, notes`  
**ML role:** Altitude is a documented performance factor, especially for visiting teams from sea level. Mexico City (2240m) is the most extreme. Can be joined to WC2026 match venue.

### D8: JTC Market Coverage

**File:** `data/processed/jumpcup_covered_markets.csv`  
**Rows:** 132  
**Columns:** `closing_date, match_name, category, question, market_id`  
**Coverage:** All JTC questions across the tournament  
**ML role:** The "label" schema — understanding exactly which question types exist enables systematic feature engineering

---

## Summary: What Exists vs. What's Missing for ML

### What we have

| Asset | Status | ML-Ready? |
|-------|--------|-----------|
| 49k+ historical match results | ✅ Clean | ✅ Yes |
| Pre-match Elo ratings for all matches | ✅ Clean | ✅ Yes |
| Fitted Poisson/Logit/DC models | ✅ Current | ✅ Yes (as features) |
| Rest days / travel distance | ✅ Exists | ⚠️ Partial (some nulls) |
| FIFA rankings (historical) | ✅ Exists | ⚠️ Needs format check |
| ~30 JTC match JSON files with outcomes | ✅ Exists | ⚠️ Inconsistent schema |
| ~19 JTC matches with full submission data | ✅ Exists | ✅ Yes (recent matches) |
| Per-question: our_estimate, crowd, outcome, RBP | ✅ In JSONs | ⚠️ Not yet flattened |
| Smarkets pre-match prices (per-match) | ✅ In JSONs | ⚠️ Not structured |
| Rules fired per match (RULE1-RULE15) | ✅ In JSONs | ⚠️ Not structured |
| Player valuations / squad data | ✅ Exists | ⚠️ Not linked to matches |
| Historical betting odds | ✅ Exists | ⚠️ Small (564 rows) |
| Altitude by venue | ✅ Exists | ⚠️ WC2026 only |
| Transfermarkt compressed files | ✅ Exists | ⚠️ Not extracted |

### What does NOT yet exist (must be built)

1. **Flat ML feature matrix** — the critical missing artifact. No single table joins:
   - Pre-match features (Elo diff, Poisson λ, rest days, squad value, altitude) 
   - → to JTC question outcomes (our_estimate, crowd, RBP per question)
   
2. **Question-type taxonomy** — no clean mapping of "which JTC question type" (e.g. "2+ offsides family", "player SOT", "fouls comparison") to a categorical feature usable in ML

3. **Named rule firing as a binary feature** — RULE1-RULE15 are documented in free text in JSONs but not encoded as structured binary indicators

4. **Per-match Smarkets price features** — the market prices are in per-match JSON files but not in a flat table joinable with outcomes

5. **Stale ledger** — `settled_markets_ledger.json` only covers the first 11 matches; the 19 most recent are missing from it

---

## The Path to ML: Required Data Pipeline

Before any model can be trained on our JTC experience, this pipeline must be built:

```
Step 1: Flatten all match JSONs
  → Read all *_{date}.json files
  → For each: extract per-question {our_estimate, crowd_estimate, outcome, rbp}
  → Backfill from post_match_results.question_results where submission estimates are null
  → Result: flat table with ~300 rows (30 matches × 10 questions)

Step 2: Add pre-match features to each row
  → Elo_diff at match date (from elo_match_panel.csv)
  → Poisson λ_home, λ_away (from context_note or recompute)
  → rest_days for each team (from rest_days_features.csv)
  → Altitude of venue (from wc2026_venue_altitude.csv)
  → match_draw_probability (from smarkets or ordered logit output)
  → question_category (tier1_market / tier2_realdata / etc.)

Step 3: Add per-question features
  → question_type (offside / fouls / SOT / cards / goals / corners / player_prop / match_winner)
  → smarkets_anchor (the relevant Smarkets price if one existed, else null)
  → rule_fired (which RULE(s) applied — binary columns RULE1..RULE15)
  → favorite_win_prob (model's P(expected-winner wins))
  → is_underdog_prop (was the question about the weaker team's output?)

Step 4: Temporal train/test split (critical — NO random splits)
  → Train: matches 1–20 (KOR-CZE through ~BRA-HAI)
  → Test: matches 21–30 (never touched until final evaluation)
  → Walk-forward is preferred: retrain with each new match, evaluate on next

Step 5: Target variable options
  → RBP (regression) — predict Relative Brier Points per question
  → beat_crowd (binary classification) — predict if we beat crowd
  → optimal_estimate (regression) — predict the ideal probability to submit
```

---

## Research Papers on File

**Location:** `papers/`

| File | Paper |
|------|-------|
| `constantinou_fenton_2012.pdf` | Pi-ratings / Bayesian network for football outcomes |
| `extending_dixon_coles_2307.02139.pdf` | Modern extensions to Dixon-Coles |
| `karlis_ntzoufras_2003.pdf` | Bivariate Poisson model for football scores |
| `verification_prob_forecasts_2106.14345.pdf` | Verifying probabilistic forecasts |
| `wisdom_crowds_2018wc.pdf` | Wisdom of crowds in WC2018 prediction |

---

## Key Data Relationships

```
results.csv (49k matches)
  ↓ Elo walk-forward
elo_match_panel.csv (49k rows, pre-match Elo per side)
  ↓ Poisson GLM fit
poisson_goals_coefs.json → used by predict.py → λ_home, λ_away per new match
  ↓ Dixon-Coles
scoreline grid → P(W/D/L), P(OU goals), P(BTTS)
  ↓ Ordered logit (separate path)
ordered_logit_coefs.json → P(W/D/L) directly from Elo diff

Per-match Smarkets prices → injected as tier1_market anchors → final_submission_estimates
  ↓ submitted to JTC
Post-match: JTC platform reveals crowd + outcome + RBP
  ↓ saved to
post_match_results in each match JSON
  ↓ (not yet aggregated)
[MISSING] flat ML feature matrix
```

---

## Known Data Quality Issues

1. **Schema version drift:** Early match JSONs (pre-2026-06-17) use older key names (`derived_estimates_draft` vs `derived_estimates_for_sportspredict_markets`) and don't store `final_submission_estimates` as a populated dict. Need normalization.

2. **Stale settled ledger:** `settled_markets_ledger.json` was last updated 2026-06-15 and covers only 11 of ~30 matches. Not suitable as an ML training source without rebuilding from scratch.

3. **Null submission estimates:** Even among newer files, UZB-COL had null submission estimates (reconstructed manually). Any automated pipeline must handle null values carefully.

4. **URU-CPV calibration-only:** No submission was made for URU-CPV. The file has `our_estimates_calibration` (would-have estimates) and crowd outcomes. Should be flagged as calibration data only, not training data for the main RBP model.

5. **CIV-ECU Q10 unknown:** Q10 (Sarmiento G+A) outcome is still unknown. Needs platform lookup before including this match.

6. **ENG-CRO Q7 submission error:** We submitted 0.20 for Kane SOT but model recommended 0.43. The stored `our_estimate` in the JSON is the submitted value (0.20), not the model's recommendation. This contaminates model performance measurement — the -44.54 RBP was from human error, not model error.

7. **Transfermarkt gz files:** Cannot be read on macOS with `zcat` (macOS uses BSD zcat expecting .Z files). Use `gzip -dc file.csv.gz | head` or `python3 -c "import gzip; ..."` instead.
