# Dataset Consolidation Audit — 2026-06-26

**Purpose of this file:** a full record of the exploration done on 2026-06-26 to scope "build one clean row/column dataset from everything we've collected." Read this before starting the actual build, and update it when the build happens so future sessions know what changed, what was decided, and why. This file does not modify any raw data — it is a record of an investigation.

**Trigger:** user asked to go through the entire `sportspredict_research/` folder, gain full context on every file/script/log, and assess how to turn the scattered raw JSON/CSV data into one comprehensive flat dataset — building on the two flat datasets that already exist.

---

## 1. What was done, step by step

1. Listed the full folder tree (`data/`, `datasets/`, `ml/`, `model/`, `bot/`, plus root-level `.md` notebooks) and counted file types (85 JSON, 28 CSV, 27 Python, 26 MD, etc.) to scope the problem.
2. Read `STEPS_FOR_HIGH_POINTS.md` directly (already open in the IDE) — a postmortem analysis of win/loss patterns across 53 matches, built from `datasets/questions_flat.csv` + the raw JSONs. Confirmed it does not modify raw data.
3. Inspected both existing flat datasets directly:
   - `datasets/questions_flat.csv` (523 rows, 14 columns) — no build script found on disk for this one; appears to have been built ad hoc in a past session. `question_text`/`category`/`stage` columns exist but are **empty for ~146 of 522 rows** (some matches like ARG-AUT have nothing in those columns at all).
   - `ml/feature_matrix.csv` (265 rows, 11 columns) — has a real build script, `ml/build_feature_matrix.py`, with documented schema-handling logic (schemas A/B/C/D/E/G).
4. Read `ml/build_feature_matrix.py` in full to understand exactly how it parses the raw JSONs and what it currently extracts.
5. Spawned **three parallel research subagents** (full findings in Section 2) to do deep reads across the raw data without consuming my own context budget on dozens of large files:
   - **Agent A** — read 14 representative raw match JSONs spanning the full date range, to inventory every field that exists across the three schema "eras" the project has gone through.
   - **Agent B** — catalogued every supplementary/external data source in the repo (FIFA rankings, odds, Transfermarkt, travel/altitude, Elo panels, the cloned `international_results` and `soccer-elo` repos, bot market dumps) and assessed join keys and WC2026 coverage for each.
   - **Agent C** — mined the three large research notebooks (`ML_EXPERIMENTS_NOTEBOOK.md`, `research_notes.md`, `[REDACTED_FILENAME]`) plus a grep for "RULE" across the whole folder, to recover the canonical RULE1–RULE15 heuristic list and any explicit feature wishlist already written down.
6. Agent C's report surfaced a file I hadn't yet seen: **`data/DATA_XRAY.md`** — a complete ML-readiness audit written 2026-06-22, which already proposes a 5-step build pipeline. I read this in full directly (not via subagent) since it's load-bearing.
7. Noticed `data/` also contains ~9 more large research `.md` files (`ML_RESEARCH_AGENT_NOTES.md`, `alt_data_sources.md`, `edge_research.md`, `calibration_research_notes.md`, etc.) not yet covered — flagged as not-yet-fully-read (see Section 5, open items).
8. **Verified a real bug** rather than trusting the subagent's claim: ran a direct Python check across all 49 raw match files and confirmed `build_feature_matrix.py` only checks for the key `post_match_results`, but **7 of 49 files use the newer key `post_match` instead** (`col_cdr`, `cro_pan`, `bih_qat`, and 4 others). Confirmed the consequence directly: `COL-CDR` and `CRO-PAN` have **zero rows** in `ml/feature_matrix.csv` even though both are fully-settled, fully-populated matches with rich data. `questions_flat.csv` has a different, overlapping gap (it has COL-CDR but not CRO-PAN), confirming the two existing flat files were built by two different undocumented processes that have each silently dropped different matches.

---

## 2. Subagent findings (full detail)

### Agent A — Raw JSON schema inventory (`data/external_markets/*.json`)

Sampled 14 files across the date range. Confirmed the raw JSONs have gone through **three schema eras**:

**Era 1 (≈06-11 to 06-21, e.g. kor_cze, bel_egy, ger_cur, gha_pan, eng_cro):**
- `sources.{kalshi,polymarket,smarkets,espn_recent_form}` — raw market quotes + team recent-form stat averages (n=3–8 games) with outlier notes
- `context_note` — freeform paragraph citing FTR%, RULE references, draw-price thresholds
- `derived_estimates_for_sportspredict_markets.<key>` — per-question `category`, `method` (prose), `raw_skellam`/`raw_poisson`/`raw_offer`, `confidence`, `recommended_estimate`
- `validation.<key>` — pre-submission cross-check notes
- `crowd_pred_estimates` — predicted crowd value via formula `0.514+0.61*(us-0.5)`
- `post_match_results.questions` (list) or `.question_results` (dict) — `q`/key, `question`, `category`, `us`/`our_estimate`, `crowd`, `outcome`, `rbp`, sometimes rich postmortem `note`
- `actual_boxscore`, `goal_and_card_timeline`, `summary`/`learning_notes`, `match_facts`
- `final_submission_estimates` — `{Q#: {estimate, notes}}` (only used today to compute `has_sub_estimate`, the actual content is discarded)

**Era 2 (transitional, e.g. arg_aut 06-22):**
- `elo_ratings`, `model_outputs.poisson_goals` (λ per team), `model_outputs.ordered_logit_match_winner`, `model_outputs.nb_dispersion.alpha`
- `gd1_evidence` — prior-matchday ESPN findings, bulleted
- `rules_in_effect.<RULE#>` — which named rule applied and why
- `crowd_expected_range`, `edge_direction`, cross-match `_confirmation` references
- `UNIFIED_LESSON_<MATCH>` — cross-question root-cause synthesis

**Era 3 (most mature, ≈06-23 to 06-25, e.g. col_cdr, cro_pan, bih_qat, ger_ecu, cur_civ, jpn_swe):**
- `model_inputs`/`model_outputs` — full λ/probability block (`p_*_win/draw`, `p_btts`, `p_total_le2/ge3`, SOT multipliers, corner λ, etc.)
- `market_data` — American odds, devigged probabilities, player scorer odds, `market_model_gap_*`
- `rules_fired.<RULE>` — boolean + explanatory note
- `group_standings_after_gd1`/`group_context`
- `gd1_evidence.<team>_gd1` — full prior boxscore (shots, SOT, fouls, corners, offsides, possession, formation)
- `player_profiles.<player>` — club, position, age, club stats, SOT/90, `rule15_applies` bool + framework note, identity-disambiguation warnings
- `referee_profile` — name, career & season card/penalty rates, fouls/match
- `compound_calculations` — intermediate math chains
- `final_estimates`/`question_analysis.Q#` — `question`, `estimate`, `direction` (YES/NO/_LEAN/STRONG_/TOSS-UP), `key_drivers`, `crowd_expected`, `edge`
- `edge_ranking` — array ranking all of a match's questions by conviction
- `duplicate_flag` (bih_qat — explicitly flags two identically-worded questions)
- `suspensions` — player-out list with reason
- `post_match.outcomes.<key>` — note the **container key is `post_match`, not `post_match_results`**, in this era for several files
- `post_match.key_learnings`/`key_confirmations`/`L#_<NAME>` — labeled lesson entries
- `NO_SUBMISSION_FLAG` + `submitted: null` (bih_qat) — analysis was completed but never reached the platform; RBP=0 for a reason that is NOT "no data"
- Newest sub-variant (ger_ecu, cur_civ, jpn_swe): `wc2026_espn_stats.<team>.matches[]` + `.averages`, `smarkets_markets` nested by market type, `context_flags` (short tags like `GER_ROTATION`), `rules_applied` as an array, `pick_tier`, `reasoning`, `confidence` per question

**Fields rich in the raw data but NOT in either existing flat CSV** (i.e. candidate new columns): `category`/tier label, `question_text` (present as a column in `questions_flat.csv` but empty for ~28% of rows), `stage`/`group`/`game_day`, `rule_applied`/`rules_fired` (which named RULE, as boolean columns), `confidence`, `direction`/`edge_direction`, `edge_rank`, `market_implied_prob` + `market_source`, `model_type` + the actual λ/coefficient used, `submitted` flag (to capture the bih_qat case correctly), `is_player_prop` + `player_name`/`club`/`position`, `data_source_tier`, `gd_evidence_n` (sample size), qualitative postmortem `note` text, `settled_live` flag, and critically: **`recommended_estimate` (pre-match research) vs `our_estimate` (what was actually submitted) as two separate columns** — at least 3 documented cases (Kane ENG-CRO Q7, NZL-EGY Q4, cze_mex Q9) where these differ because of a submission/transcription error, not a modeling disagreement. Collapsing them into one column (as both current CSVs do) destroys the "process error vs. model error" distinction the raw files actually preserve.

**Confirmed schema bug:** `post_match_results` (most files) vs `post_match` (col_cdr, cro_pan, bih_qat, ger_ecu, cur_civ, jpn_swe, +1 more — 7 of 49 total) — `build_feature_matrix.py` only checks the former, so these files are silently skipped. I independently verified this produces zero rows for COL-CDR and CRO-PAN in `ml/feature_matrix.csv` (Section 1, step 8).

Other quirks: outcome encoding varies (int 0/1 vs string YES/NO vs separate `outcome_numeric`); `final_submission_estimates` only exists in some era-1 files; `mex_kor` requires a join between `post_match_results.results` and `final_submission_estimates` since the inline fields are absent there; question numbering isn't always a clean `Q<n>` (some keys are slug+number).

### Agent B — Supplementary/external data sources

Join keys already used in `questions_flat.csv`: `match` (3-letter codes, e.g. "ARG-AUT") + `date` (ISO).

| Source | Granularity | WC2026 coverage | Join key | Verdict |
|---|---|---|---|---|
| `data/external/fifa_ranking/` | team, historical | No (latest snapshot 2020 / through 2024-09) | country name/code + nearest date | Low value, stale |
| `data/external/odds/international_fixture_odds.csv` | match, international only | **Zero actual WC2026 rows** — WC2022 + qualifiers/friendlies only | team name + date | Historical prior only, not live |
| `data/external/transfermarkt/extracted/national_teams.csv` | team, current squad snapshot | Yes (2025 season squad value/age/FIFA rank) | team full name (needs alias map) | **Good static team-strength feature** |
| `data/external/transfermarkt/extracted/national_team_players.csv` | player, current roster | Yes | team id → name | Useful for player-prop questions |
| `data/external/transfermarkt/extracted/national_team_games.csv` | match, major tournaments only | Stops 2026-01-18, no WC2026 group stage | team name + date | Not directly useful |
| `data/external/travel/` (`team_venue_distances.csv`, `rest_days_features.csv`, `wc2026_venue_coords.csv`) | venue/match | Yes, built specifically for WC2026 | team name (has its own `ALIASES` dict for name mismatches — reuse it) | **High value, ready to join** |
| `data/external/altitude/wc2026_venue_altitude.csv` | venue (16 rows) | Yes | city/stadium | **High value, trivial join** (Mexico City 2240m, Guadalajara 1566m) |
| `data/processed/elo_match_panel.csv` | match (49,473 rows) | **Yes — includes full WC2026 schedule through 2026-06-27** with pre-match Elo | team + date | **Core feature, already built** |
| `data/processed/elo_current_ratings.csv` | team snapshot | current | team name | Useful lookup |
| `data/processed/*_coefs.json` | fitted model params | n/a | n/a | These generated `our_estimate` already — informative metadata, not a join source |
| `data/soccer-elo/` | team, annual, through 2023 | No | — | Superseded by project's own Elo pipeline, low value |
| `data/international_results/results.csv` | match (49,473 rows) | **Yes — exact future-dated WC2026 fixture list (date, teams, city, country)** | team + date | **Best source for venue/city per match** — feeds the Elo panel and could directly drive altitude/travel joins instead of re-deriving |
| `bot/data/` (`matches.json`, `markets_raw.jsonl`, `predictions_review.csv`) | match registry / live market dumps | Yes | match name | Useful for auditing submissions, not a new feature source — overlaps with `data/external_markets/` |

Bottom line from Agent B: highest-value untapped joins are (1) `international_results/results.csv` for exact venue/city, (2) Transfermarkt squad value/age as a static team-strength feature, (3) the already-built Elo panel. FIFA rankings, odds, and `soccer-elo` add little beyond what the project's own Elo/Poisson pipeline already covers.

### Agent C — RULE taxonomy and feature wishlist from the research notebooks

Found `data/DATA_XRAY.md` (see Section 3) as the key existing planning document. Also recovered the canonical RULE list (cross-referenced against the user's own memory file `project_crowd_bias_model.md`, which is the authoritative source):

1. **RULE1** — match-winner: submit avg(crowd consensus, verified sharp market).
2. **RULE2** — if a verified market exists for a prop, submit at market price undeviated.
3. **RULE3** — no market exists → tier2_realdata (Poisson/Skellam) is top priority.
4. **RULE4** — compound "both teams achieve X" questions: weight toward crowd, don't trust independence-product Poisson on thin samples.
5. **RULE5** — don't over-revise toward an extreme on small-sample (n<10) findings; blend with the prior estimate.
6. **RULE6** — never submit 0%/100%; cap ~90–95% / floor ~5–10%.
7. **RULE7** — for heavy favorites/extreme underdogs, submit unshaded first-pass model estimates on props (don't compress toward 50%).
8. **RULE8** — elevated draw probability (≥~25%) → shrink "more than" props toward 0.50–0.60.
9. **RULE9** — unresolvable player-prop market → fall back to positional/role-based prior.
10. **RULE10** — blowout fouls/corners inversion: winning team can foul ≥ losing team in true blowouts.
11. **RULE11** — not found; appears to have been skipped/folded into others.
12. **RULE12** — pre-submission risk gate for no-market count props (outlier check, shrink toward crowd formula).
13. **RULE13** — near-identical historical rates between two teams → price near 50% (0.45–0.55).
14. **RULE14** — internal logical-consistency check across related questions in the same match (e.g. P(more SOT) ≥ P(more goals)).
15. **RULE15** — losing-team/underdog forward SOT suppression: Scenario A (blowout/trailing 2+/winprob<10%) → suppress −10pp; Scenario B (competitive, trailing 0–1/1–2) → do NOT suppress, may invert. Extreme underdogs (<15% FTR) get a flat 0.25–0.35 band.

Plus unnumbered named heuristics acting as de facto rules: `MAIN_BOOK_ABSENCE`, `HARD_FLOOR_0.25`, the "2+ offsides family", sub-to-starter lineup upgrade, blowout corner reversal, survival-match corner override.

Question-category taxonomy (from the stale `settled_markets_ledger.json` schema): `tier1_market`, `tier2_realdata`, `stats_proxy`, `compound_market_proxy`, `skellam_market_hybrid`, `match_winner_deferred_market`, `match_winner_gut_override` (worst category, n=1, −51.97 RBP).

`ML_RESEARCH_AGENT_NOTES.md` explicitly warns: any `ruleN_fired` column must respect the **discovery-window** — only mark a rule as "fired" for matches after the rule was actually discovered/written down, or the feature leaks future knowledge into past rows.

---

## 3. What `data/DATA_XRAY.md` already specifies (written 2026-06-22, by a past session)

This file is a complete prior ML-readiness audit and is the closest thing to an existing spec. Key points, since it predates several of the most recent (and richest, era-3) matches and should be treated as **directionally right but stale**:

- Defines 4 data layers: **A** = per-match JSON (source of truth), **B** = historical base data (49k+ international results, Elo), **C** = fitted model artifacts (Poisson/NB/ordered-logit coefficients), **D** = supplementary enrichment (FIFA, Transfermarkt, altitude, odds).
- Per-file completeness audit table through 2026-06-22 — confirms matches before ~06-18 don't have machine-readable `final_submission_estimates` and must be backfilled from `post_match_results.question_results`.
- Already proposes the exact 5-step build pipeline:
  1. Flatten all match JSONs into ~300 rows (this is what the two existing CSVs already attempted, incompletely).
  2. Add pre-match features (Elo diff, Poisson λ, rest days, altitude, draw probability, question_category).
  3. Add per-question features (question_type, smarkets_anchor, rule_fired booleans, favorite_win_prob, is_underdog_prop).
  4. **Temporal train/test split — explicitly NOT random** (train on early matches, test on later ones, walk-forward preferred).
  5. Target variable options: RBP regression, beat_crowd classification, or optimal_estimate regression.
- Documents known data-quality issues that any build must handle: schema version drift, the stale ledger, null submission estimates (UZB-COL), URU-CPV being calibration-only (exclude from training), CIV-ECU Q10 outcome unknown, ENG-CRO Q7 submission error contaminating model-performance measurement, and a macOS gotcha (`zcat` doesn't work on `.gz` files — use `gzip -dc`).

---

## 4. Synthesis — what this means for the new flat dataset

Putting the bug-verification (Section 1.8), Agent A/B/C findings, and `DATA_XRAY.md` together:

1. **Neither existing flat file is safe to build on as-is.** `ml/feature_matrix.csv` silently drops 7 of 49 matches (confirmed: COL-CDR, CRO-PAN have zero rows) because of the `post_match`/`post_match_results` key drift. `questions_flat.csv` has a different, undocumented gap and no build script on disk, plus ~28% empty `question_text`/`category` cells. The right move is a **new build script that re-parses every raw JSON from scratch**, handling all 3 schema eras (and both post-match container key names), rather than patching either existing CSV.
2. **The raw JSONs contain far more than either flat file captures** — confidence, direction, market-implied price, model type/λ, rule-fired booleans, player-prop metadata, referee data, and (most importantly for honest evaluation) the recommended-vs-actually-submitted estimate split.
3. **DATA_XRAY.md's 5-step pipeline is still the right shape**, just needs updating for era-3 fields and the post-match key bug it didn't anticipate.
4. **Two genuinely separate deliverables are being conflated** and should probably be sequenced:
   - **(a) A comprehensive per-question dataset** sourced purely from `data/external_markets/*.json` — richer version of what already (partially) exists, no external joins, fixes the dropped-match bug, adds all the new columns above. Self-contained, no team-name normalization needed.
   - **(b) Joining in external pre-match features** (Elo diff, rest days, altitude, squad value) — requires team-name alias resolution across sources (FIFA/Transfermarkt/international_results all spell team names differently) and is a materially bigger, separate piece of work.
5. **Several rows need explicit status flags, not silent exclusion**: bih_qat (researched but never submitted — RBP=0 ≠ no signal), URU-CPV (calibration-only), UZB-COL (estimates reconstructed, not original), CIV-ECU Q10 (outcome unknown), ENG-CRO Q7 / similar (submission error — `recommended_estimate` ≠ `our_estimate`).

---

## 5. Open items / not yet read

- `data/ML_RESEARCH_AGENT_NOTES.md` (54KB) and 8 other large notes in `data/` (`alt_data_sources.md`, `alt_data_sources_research.md`, `calibration_research_notes.md`, `code_audit_findings.md`, `crowd_consensus_prediction_research.md`, `edge_research.md`, `granular_data_sources_research.md`, `ml_integration_research_notes.md`, `ml_methodology_deep_dive_notes.md`, `prop_market_pricing_notes.md`) have **not** been read in this session — flagged in case they contain additional feature ideas or data-quality notes not already surfaced above. Worth a pass before finalizing the build if thoroughness matters more than speed here.
- No decision has yet been made on scope — see the question put to the user in chat about (a) vs (a)+(b) above.

---

## 6. Raw data integrity

No raw file was modified, moved, or deleted during this investigation — only read. The two existing flat datasets (`datasets/questions_flat.csv`, `ml/feature_matrix.csv`) were also only read, not edited. Any new dataset will be written to a new file/path, per standing instruction to never touch raw data or silently overwrite prior derived datasets.

---

## 7. The actual build (same session, after the scoping decisions above)

User chose: (a) build the full per-question + external pre-match features dataset now, and (b) skim the 9 remaining unread research notes first for thoroughness. Both done before writing code. User then added one more instruction mid-build: **focus purely on building a good, accurate dataset — not on ML/feature-selection concerns** (those are a separate downstream problem). Everything below reflects that priority: completeness and correctness of the data itself, not what a model should eventually do with it.

### 7.1 Extra research pass (the 9 previously-unread notes)

A fourth subagent skimmed `ML_RESEARCH_AGENT_NOTES.md` and 8 other large notes in `data/`. Top finding: `code_audit_findings.md` documents a **separate, pre-existing bug** (not touched in this build, noted for awareness) — `model/poisson_goals.py`'s `build_design_matrix()` ignores the `neutral` flag when setting `is_home`, while every other model file gates on it correctly, biasing the home-advantage coefficient on ~26% of training rows. Also surfaced: a concrete EPV-capped ML feature list, half-split data-source gaps (FBref has no per-half splits; StatsBomb open-data does via a `period` field), referee running-distance as a foul predictor, and the Diebold-Mariano test as the correct significance test for "are we beating the crowd." None of this changed the build (per the user's "don't think about ML" instruction) but is worth knowing for later.

### 7.2 Team-name reconciliation

Built a 49-code → canonical-full-name map (`CODE_TO_NAME` in the script) covering every team code that actually appears in the 49 raw match filenames. Two real spelling inconsistencies were caught and fixed:
- The project's own `bot/team_code_map.py` uses inconsistent keys (some 3-letter codes, some full names like `"Curacao"`/`"Haiti"`/`"New Zealand"` instead of `CUR`/`HAI`/`NZL`) and is missing `CDR`/`SAU` entirely — not reused as-is, rebuilt cleanly instead.
- The raw filenames use **both `SAU` and `KSA`** for Saudi Arabia across different files (era drift), and `CDR` (not `COD`) for DR Congo. Verified directly against `col_cdr_2026-06-23.json`'s own `match: "Colombia vs DR Congo"` field.
- Transfermarkt's extract spells two teams differently than every other source: `"Turkiye"` (not "Turkey") and `"Bosnia-Herzegovina"` (not "Bosnia and Herzegovina") — added as explicit aliases after the first build run flagged them as unmatched.

### 7.3 Building the script — bugs found and fixed during construction (not just during the earlier audit)

1. **Calibration-only matches use a third post-match shape.** `uru_cpv`'s `post_match_results` contains neither `.questions`/`.question_results`/`.results`/`.outcomes` but a `.crowd_results` dict (our_estimate/crowd_estimate/outcome only, no rbp, since nothing was submitted). The first script draft didn't handle this and silently dropped the match. Added a dedicated branch.
2. **`bih_qat`'s "never submitted" flag lives one level deeper than expected.** `NO_SUBMISSION_FLAG` is inside `post_match`, not at the file's top level, and its `questions` list uses a field named `our_est_unsubmitted` + `submitted: null` instead of the usual `us`. The first run mis-detected this match as a normal submitted match. Fixed by reading the flag from inside the post-match container and adding an explicit `actually_submitted` field threaded through every extraction path.
3. **`rbp=0` is ambiguous and was initially conflated with "submitted and scored exactly zero."** Changed: `rbp` and `beat_crowd` are now blank (not 0/False) for any question where `actually_submitted` is False, so a never-submitted question can't accidentally look like a real loss in aggregate stats.
4. **The cross-container Q-number assumption was wrong, and not just for old files.** Believed (per the original research-agent report) that era-3 files' `final_estimates`/`question_analysis` Q-numbering reliably matched the post-match `outcomes` Q-numbering, because one spot-check (`col_cdr`) happened to align. Direct verification on `cro_pan_2026-06-23.json` disproved this: `final_estimates.Q1` is about fouls, `post_match.outcomes.Q1` is about offsides — a 4-question rotation between draft and final numbering. Rebuilt the whole pre-match-to-post-match join around topic-word matching (tokenize key + question text, Jaccard ≥0.35, global greedy assignment) instead of trusting position. This also required re-deriving `edge_rank` through the same translation, since `edge_ranking` entries reference the pre-match draft numbering too.
5. **`submission_error_flag` was firing on `bih_qat`'s never-submitted questions**, which is a category error (there's no such thing as a "submission error" on a question that was never submitted). Suppressed the flag (and `submission_diff`) whenever `actually_submitted` is False.
6. **Several matches were missing `elo_diff`/`venue_city` entirely** (USA-PAR, UZB-COL, MEX-KOR, BRA-HAI, TUR-PAR, ECU-CUR, JPN-TUN, NZL-EGY). Root cause: the raw filename's date is one day off from `data/international_results/results.csv`'s date for the same fixture on several US/Canada-hosted matches (timezone artifact — e.g. `usa_par_2026-06-13.json` vs. the results.csv row dated `2026-06-12`). Fixed by adding a ±1-day-tolerant lookup. Also caught and fixed two venue/altitude city-name mismatches (`Zapopan`→`Guadalajara`-area aliasing was already planned, but `Guadalupe`→`Monterrey` for the Estadio BBVA venue, and a stray `"... area"` suffix on one raw venue string, were found only by checking the post-fix gap list).

### 7.4 Validation performed before treating the output as trustworthy

Cross-checked **12 specific RBP values independently documented in `STEPS_FOR_HIGH_POINTS.md`** (a human-written postmortem from a separate prior session) against the new dataset, including the two worst results of the campaign (BRA-MAR Q8 −51.97, ENG-CRO Q7 −44.54) and the single biggest win (ENG-GHA Q1 +35.50). **All 12 matched exactly.** Also confirmed the documented ENG-CRO Q7 submission error (recommended 0.43 vs. submitted 0.20) now surfaces correctly as the right pairing, after fix #4 above — before that fix, the script had been pairing Kane's question with the wrong pre-match record entirely (a value of 0.26, not 0.43) and silently producing a wrong "recommended_estimate," which is exactly the kind of error that's worse than leaving a field blank.

### 7.5 Final output

`datasets/master_question_dataset.csv` — 480 rows (49 matches × ~10 questions, minus the always-skipped calibration/never-submitted rows for RBP purposes), 73 columns. Full column-by-column documentation, including every known gap and the reasoning above, is in `datasets/MASTER_DATASET_DICTIONARY.md`. Coverage of joined external features: Elo diff, rest days, venue/altitude, draw probability, and Poisson λ are 49/49 matches; squad value/FIFA ranking are ~43-47/49 (5 WC2026 teams are simply absent from the Transfermarkt source used); pre-match `recommended_estimate` and related research fields cover 114/480 rows (24%), which reflects a real, pre-existing gap in which matches have machine-readable pre-match research saved, not a join failure.

Total scored RBP across the new dataset: **+872.13** over 436 actually-scored questions (68.1% beat-crowd rate), vs. `questions_flat.csv`'s previously-reported **+812.15** over 433 questions (56.8%) — the difference is fully explained by `questions_flat.csv` having no row at all for `CRO-PAN` (a real, previously entirely-missing match) and likely other row-level extraction differences in that file's undocumented, unsaved build process; it is not a sign of a problem in the new build, which is independently verified against the 12 spot-checks above.
