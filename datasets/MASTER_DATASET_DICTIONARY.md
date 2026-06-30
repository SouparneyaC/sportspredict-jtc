# master_question_dataset.csv — Data Dictionary

**Built by:** `datasets/build_master_dataset.py` (read-only against all raw data; writes only to `datasets/master_question_dataset.csv`)
**Built from:** every match file in `data/external_markets/*.json` (49 matches) + joined external sources
**Grain:** one row per (match, question) — 480 rows, 49 matches, 73 columns
**Validated against:** 12 specific RBP figures independently documented in `STEPS_FOR_HIGH_POINTS.md` — all match exactly. See `DATASET_AUDIT_2026-06-26.md` Section 7 for the full build log.

Run `python3 datasets/build_master_dataset.py` from anywhere to rebuild it (paths resolve relative to the script, not your cwd). Rerun any time a new match file is added to `data/external_markets/`.

---

## Match-level columns (same value repeated for all ~10 rows of a match)

| Column | Description |
|---|---|
| `file` | source raw JSON filename |
| `match` | normalized 3-letter code pair, e.g. `ARG-AUT` (the canonical join key — use this, not the inconsistent `match` string inside the raw JSON) |
| `team_a`, `team_b` | full team names, order taken from the filename slug (no home/away meaning — all WC2026 matches are effectively neutral-site except true host-nation games) |
| `team_a_code`, `team_b_code` | 3-letter codes |
| `date` | match date, `YYYY-MM-DD` (from filename) |
| `tournament`, `group`, `game_day` | from the raw file when present (era-3 only; blank for earlier files) |
| `venue_raw` | literal venue string from the raw file, when present |
| `venue_city`, `venue_country` | resolved venue (raw file first, else looked up from `data/international_results/results.csv` by team-pair + date, tolerant of a ±1-day offset — see note below) |
| `altitude_m` | venue altitude in meters, joined from `data/external/altitude/wc2026_venue_altitude.csv` via `venue_city` |
| `schema_era` | 1, 2, or 3 — which generation of the raw-file schema this came from (informational/debugging only, see audit doc Section 2) |
| `post_match_key_used` | `post_match_results` or `post_match` — which top-level key this file used. **This column exists specifically because the previous build script (`ml/build_feature_matrix.py`) only checked for `post_match_results` and silently dropped every file using `post_match` (7 of 49 matches, including COL-CDR and CRO-PAN). This script checks both.** |
| `final_score` | literal final score string |
| `match_total_rbp` | total RBP recorded for the match in the raw file (sanity-check against the sum of this match's `rbp` column) |
| `settled_date` | when present |
| `match_submitted` | **False** only for matches where no real platform submission was ever made (currently: `URU-CPV`). Everything else is True. |
| `match_is_calibration_only` | True for `URU-CPV` (no submission was made; the file's numbers are retrospective calibration data only) |
| `elo_team_a_pre`, `elo_team_b_pre`, `elo_diff` (a−b) | pre-match Elo. Prefers the literal value the original researcher used (`model_inputs`/`elo_ratings` in the raw file) when present; otherwise looked up from `data/processed/elo_match_panel.csv` by team-pair + date (±1 day tolerance) |
| `rest_days_a`, `rest_days_b`, `rest_days_diff` | days since each team's previous match, computed directly from `data/international_results/results.csv` (NOT from `data/external/travel/rest_days_features.csv`, which is stale and stops 2026-06-09, before the tournament even started — see audit doc) |
| `squad_value_a_eur`, `squad_value_b_eur` | total squad market value (EUR), from `data/external/transfermarkt/extracted/national_teams.csv` (2025 season snapshot). **Null for Cape Verde, Curaçao, DR Congo, Haiti, Ivory Coast — these 5 teams are simply absent from that 119-row extract, not a join bug.** |
| `squad_avg_age_a`, `squad_avg_age_b` | same source |
| `fifa_ranking_2025_a`, `fifa_ranking_2025_b` | current (2025) FIFA ranking from the same Transfermarkt extract — used in preference to `data/external/fifa_ranking/*.csv`, which is stale (latest snapshot 2020, or historical through 2024-09 at best) |
| `draw_probability` | from the raw file's own `model_outputs.p_draw` when present, else computed from `elo_diff` via `data/processed/ordered_logit_coefs.json` (neutral-venue assumption: `home_advantage` term set to 0, since these are WC2026 group/knockout matches, not classic home/away) |
| `poisson_lambda_a`, `poisson_lambda_b` | expected goals; same precedence (raw file's `model_outputs.lambda_*` first, else computed from `elo_diff` via `data/processed/poisson_goals_coefs.json`) |
| `rules_fired_list` | semicolon-joined list of which named RULEs (RULE1–RULE15) fired for this match, per the raw file |
| `rule_fired_count` | count of the above |
| `rule1_fired` … `rule15_fired` | per-rule boolean (None/blank = rule not mentioned in this file at all, as opposed to False = explicitly considered and did not fire) |

**Note on the ±1-day date tolerance:** several US/Canada-hosted matches have a one-day offset between the raw filename's date and `data/international_results/results.csv`'s date for the same fixture (timezone artifact — e.g. `usa_par_2026-06-13.json` vs. `results.csv`'s `2026-06-12` row for the same United States–Paraguay game). The lookup tries the exact date first, then ±1 day, before giving up.

## Question-level columns (one value per row)

| Column | Description |
|---|---|
| `question_num` | `Q1`, `Q2`, ... — **this is always the post-match/platform numbering** (see note below) |
| `question_text` | full question text, when available from either the post-match record or a successfully-matched pre-match record |
| `question_category` | tier label when available: `tier1_market`, `tier2_realdata`, `stats_proxy`, `compound_market_proxy`, `skellam_market_hybrid`, `match_winner_deferred_market`, `match_winner_gut_override` (see `data/DATA_XRAY.md` for full definitions) |
| `confidence`, `direction` | from the matched pre-match record, when found (`HIGH`/`MEDIUM`/`LOW`, `YES`/`NO`/`LEAN_*`/`STRONG_*`/`TOSS-UP`) |
| `key_drivers` | semicolon-joined bullet points explaining the pre-match reasoning, when available (era-3 files only) |
| `edge_rank` | this match's pre-match conviction ranking (1 = highest edge), from the raw file's `edge_ranking` block, when present |
| `recommended_estimate` | the pre-match researched/recommended probability, **matched to the correct question by topic-word overlap, not by Q-number** (see important note below) |
| `our_estimate` | what was actually recorded as submitted in the post-match record (or the would-have-been value for never-submitted questions — see `actually_submitted`) |
| `submission_diff` | `recommended_estimate − our_estimate`, only computed when the question was actually submitted |
| `submission_error_flag` | True when `abs(submission_diff) > 0.03`. **Only 5 questions across the whole dataset are flagged**, including the documented ENG-CRO Q7 Kane transcription error (recommended 0.43, submitted 0.20, see `STEPS_FOR_HIGH_POINTS.md`). Not all 5 are necessarily mistakes — some may be legitimate last-minute revisions; the column flags magnitude, not intent. |
| `crowd_estimate` | crowd's estimate at settlement |
| `outcome` | 1 = YES, 0 = NO, blank = unknown (e.g. CIV-ECU Q10) |
| `outcome_known` | boolean convenience flag for the above |
| `rbp` | Relative Brier Points actually earned. **Blank (not 0) for any question that was never actually submitted** (see `actually_submitted`) — this is a deliberate change from the raw file's literal `0`, to avoid conflating "never competed" with "competed and scored exactly zero." |
| `beat_crowd` | True/False/blank to match the blank-vs-zero distinction on `rbp` above |
| `actually_submitted` | **False** for the ~20 questions across `BIH-QAT` (11 questions, fully researched but never submitted before the deadline — a documented process failure, see `STEPS_FOR_HIGH_POINTS.md` Loss Pattern #3) and `URU-CPV` (10 questions, calibration-only). For these rows, `our_estimate` is the retrospective "would-have-been" value, not a real platform submission. |
| `is_player_prop`, `player_key` | True + the matched player-profile key when the question text contains a name that appears in the raw file's `player_profiles` block |
| `postmortem_note` | the rich free-text explanation attached to this question's outcome in the raw file, when present (currently discarded by both pre-existing flat datasets) |

### Important: the Q-number cross-container matching problem

**Q-numbers are NOT a reliable join key across containers within the same raw file.** This was discovered and fixed during this build — verified concretely on two different files:

- `eng_cro_2026-06-17.json`: the pre-match draft research numbers Kane's SOT question `q5`, but the final post-match record calls it `Q7`. A naive Q-number join would have paired Kane's question with an unrelated Croatia-offsides question instead.
- `cro_pan_2026-06-23.json`: `final_estimates.Q1` ("fouls") is actually post-match `Q4`; the first four questions are rotated by one position between the draft and final numbering, while questions 5–10 happen to align. So even within the newest, most-structured schema era, position cannot be trusted.

This script resolves pre-match research to the correct post-match question by **topic-word overlap** (tokenizing both the container's key/slug and its `question` text field, dropping stopwords, requiring ≥2 shared tokens and Jaccard ≥0.35, then doing a global greedy best-match assignment per file) — never by assuming the same Qn means the same question across containers. Where no confident match is found, the enrichment columns (`recommended_estimate`, `category`, `confidence`, `direction`, `key_drivers`, `edge_rank`) are left blank rather than risk a silent wrong pairing. Coverage: 114 of 480 rows (24%) have a matched `recommended_estimate` — the rest either have no pre-match research container in the raw file at all (documented gap for matches before ~2026-06-18, see `data/DATA_XRAY.md`), or no confident topic match was found.

**The core scored fields — `our_estimate`, `crowd_estimate`, `outcome`, `rbp` — are NOT affected by this problem.** Those all come directly from the post-match record's own internal Q-numbering, which is self-consistent (verified via 12 independent spot-checks against RBP figures documented in `STEPS_FOR_HIGH_POINTS.md` — all 12 match exactly).

## Known gaps / honest limitations

- `squad_value_*_eur`, `squad_avg_age_*`, `fifa_ranking_2025_*` are null for Cape Verde, Curaçao, DR Congo, Haiti, Ivory Coast (absent from the 119-row Transfermarkt extract used).
- `recommended_estimate` and related pre-match enrichment columns cover ~24% of rows (see above) — a real gap in the source data (not every match has machine-readable pre-match research saved), not just a matching-threshold issue.
- `venue_city`/`altitude_m` rely on a manual city-name alias table (`VENUE_CITY_ALIASES` in the script) reconciling `results.csv`'s fixture-city spelling (e.g. "Zapopan", "Arlington", "Guadalupe") against the altitude file's venue-city spelling (e.g. "Guadalajara", "Dallas", "Monterrey"). Extend that dict if a new venue/city spelling shows up in future matches.
- This dataset does not yet include shot/SOT/card/corner/offside per-match boxscore data as columns (those live inside each raw file's `gd1_evidence`/`wc2026_espn_stats`/`actual_boxscore` blocks, in inconsistent per-era shapes) — flattening those is a reasonable next iteration if needed, but was out of scope for this build (see audit doc for why this was deferred).
