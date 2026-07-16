# Repository Map

A complete table of contents for this repository — every markdown file, script, dataset, and
external data source, what it contains, and how it fits together. Written for a reviewer seeing
this project for the first time (a senior engineer, a researcher, a competition judge) who needs
to find their way around without reading everything.

**Scope note:** this repo has roughly 915-920 project files once two large third-party mirrors are excluded
(both gitignored, both re-clonable, neither ours): `external_repos/machine-learning-for-trading`
(Stefan Jansen's ML4T book, cloned for research reference) and
`data/external/statsbomb/open-data/` (the full public StatsBomb open-data GitHub repo, ~9,000
files, source data for the historical StatsBomb panels). Neither is catalogued file-by-file here;
each gets one entry describing what it is and how it's used.

**Status:** written incrementally as each section was completed — sections were appended as they
finished, not held back for one final pass, so nothing would be lost if the work were interrupted.
All 8 sections are now complete. **2026-07-15:** the repo was reorganized by question-type topic
(see Section 2) — files that were single-topic physically moved into `topics/<slug>/`; genuinely
shared infrastructure stayed put and is now linked from every topic that depends on it. Sections 6
and 8 were updated to reflect the new locations; every other section's file-path references were
checked and fixed where stale (`scripts/verify_md_links.py` now confirms zero broken markdown
links repo-wide). **2026-07-15 (later same day):** the England vs Argentina semifinal was priced,
settled (Argentina won 1-2, +96.05 RBP), and added as `matches/England Vs Argentina (Jul.15.26)/`
(25 files, the most complete match folder to date — data-sourcing 01-10, per-question analysis
11-20, a two-loop reproducibility audit 21-22, settlement + post-match 23-24), along with its
supporting cross-topic backtests (`ml/backtests/corners_comparison_*`, `timing_compound_events_*`),
a new `topics/cards/card_timing_panel.*`, a `topics/penalties-red-cards/PENALTY_MODELING_RESEARCH.md`,
and a root-level QF/SF retrospective. Sections 1, 2, 3, 4, 5, and 6 updated accordingly.

---

## Contents

1. [Root-level research notes (MD files)](#1-root-level-research-notes)
2. [`topics/` — question-type navigation (start here)](#2-topics--question-type-navigation-start-here)
3. [`bot/` — live API pipeline](#3-bot--live-api-pipeline)
4. [`data/` and `datasets/` — data sources and processed panels](#4-data-and-datasets)
5. [`matches/` — per-match research and settlement records](#5-matches--per-match-research-and-settlement-records)
6. [`ml/` and `model/` — shared infrastructure](#6-ml-and-model--shared-infrastructure-family-specific-content-moved-to-topics)
7. [`papers/`, Tactic AI, `bash_logs/`, and misc root files](#7-papers-tactic-ai-bash_logs-and-misc-root-files)
8. [`writeups/` — professional match write-ups](#8-writeups--professional-match-write-ups)

---

## 1. Root-level research notes

26 markdown files sitting at the repo root — the project's running lab notebook, formal writeups,
research memos, and pre-writing surveys. Roughly chronological by subject matter; several
explicitly supersede or get superseded by others, noted per entry.

### `ML_EXPERIMENTS_NOTEBOOK.md`
- **Size/date:** 132,797 bytes (2,167 lines), last modified Jul 12 12:06
- **Purpose:** The project's permanent, chronological lab notebook — a running record of every ML/statistical experiment and every match-by-match pricing session (pre-match research, model outputs, final estimates, and post-match RBP results) since the campaign started 2026-06-22.
- **Contents:** Opens with "Session 0" (building `ml/feature_matrix.csv` from 5 divergent raw JSON schemas) and "Experiment 1" (a Platt-scaling calibration diagnostic on n=246 questions, concluding the correction would currently do more harm than good — bootstrap CI on slope [0.12, 1.29] includes 1.0, walk-forward test worsens Brier by 0.028). A short section paraphrases lessons from an outside quant-workshop session (small-n caution, simple-beats-complex, in-sample rule bias) and maps each lesson onto the project's own problems. A "CRITICAL LOSSES — DO NOT REPEAT" section catalogs the worst individual results (BRA-MAR Q8 at -51.97, QAT-SUI Q1 at -42.51, BRA-HAI Q2 at -42.56, ARG-AUT Q9 at -31.86, ARG-AUT Q6 at -19.17) and the rules born from each (RULE6 never submit 0/100%, RULE4 compound-question crowd-weighting, 2+ offsides family revisions). The bulk of the file (roughly 80%) is match-by-match session logs, each following the same structure: model outputs (Elo, Poisson lambdas, ordered-logit P(win/draw/loss)), GD1 (prior-match) evidence pulled from ESPN/Opta, external market/referee/player data, a table of final estimates with rationale, then a post-match results table (our estimate, crowd, outcome, RBP) and a "lessons learned" writeup that frequently revises a named rule. Matches covered chronologically: ARG-AUT, FRA-IRQ, NOR-SEN, JOR-ALG, POR-UZB, a "Data Source Reliability Audit" synthesizing tiers of trusted data sources from 26+ matches, ENG-GHA, CRO-PAN, COL-CDR, SUI-CAN, BIH-QAT, SCO-BRA, MAR-HAI, CZE-MEX, RSA-KOR, and ends mid-session with GER-ECU/CUR-IVC pre-match estimates (results marked TBD).
- **Key numbers/results:** Feature matrix baseline: 246 settled rows, mean RBP/question +2.497, total +614.22 RBP, beat-crowd 72.4%. Platt diagnostic: global slope b=0.510 (CI [0.12,1.29]), walk-forward b=0.196, Platt-recalibrated Brier 0.2237 vs raw 0.2188 vs crowd 0.2172 (worse). Best-known single new rules from this stretch: RULE_FOULS (predict which team defends before pricing "who fouls more"), FLOOR_0.25 (never submit below 0.25 on count-stat questions), MAIN_BOOK_ABSENCE (player absent from FanDuel/DraftKings scorer markets → cap at ≤0.38). Notable match RBPs: NOR-SEN +36.49, JOR-ALG -5.60, POR-UZB -1.11, ENG-GHA +44.4, CRO-PAN -0.47, SUI-CAN -21.56, SCO-BRA +2.75, MAR-HAI +11.07, CZE-MEX -6.01, RSA-KOR -39.56 (major upset, model had given RSA only 15.7%).
- **Cross-references:** References `ml/build_feature_matrix.py`, `ml/platt_diagnostic.py`, `ml/platt_results.json`, `data/DATA_XRAY.md`, `data/ML_RESEARCH_AGENT_NOTES.md`, memory files, and dozens of per-match `bash_logs/*.txt` and `data/external_markets/*.json` files. Cross-referenced heavily by `JTC_PROJECT_WRITEUP.md` and `PAPER_REVISION_NOTES.md`.
- **Status:** Living document, actively appended to; ends mid-match with pending results, confirming it is not a finished artifact.

### `JTC_PROJECT_WRITEUP.md`
- **Size/date:** 79,826 bytes (354 lines), last modified Jul 10 10:03
- **Purpose:** The project's full formal writeup/report — a single-document synthesis of motivation, literature review, data pipeline, models, crowd-bias findings, calibration, track record, and limitations, aimed at a mixed audience (forecasting-community, ML/quant, sports-analytics).
- **Contents:** 12 numbered sections. Abstract states the campaign's cumulative record and headline finding (crowd consensus is structurally compressed toward 50%, i.e., favorite-longshot bias, and this compression — not raw out-forecasting — is the primary source of edge). Section 3 is an organized literature review of 8 papers grouped by modeling lineage (Dixon-Coles/Poisson family, Elo/ordered-logit, scoring-rule verification/RPS, wisdom-of-crowds). Section 4 documents the data pipeline (tiered source-reliability audit, 3-stage raw→clean→mart pipeline, data dictionary caveats including the "Q-number is not a safe join key" finding). Section 5 documents the modeling stack (point-in-time Elo, Poisson goal-rate regression, Dixon-Coles/NB corrections, ordered logit, walk-forward validation discipline). Section 6 presents the crowd-bias regression (`crowd ≈ 0.514 + 0.61×(our_estimate−0.5)`, n=85) and named situational rules, each with evidence status and revision history. Section 7 covers calibration (historical-panel gap vs. live-record Platt diagnostic). Section 8 is the track record, explicitly flagging a discrepancy between four different cumulative-RBP figures reported at different times and choosing the freshest dataset rebuild as authoritative. Sections 9-12 cover the market-edge backtest pipeline, limitations (two confirmed/traced code bugs — the neutral-flag mismatch marked FIXED 2026-07-10), future work, and an appendix data dictionary.
- **Key numbers/results:** Authoritative-at-writing headline: 49 matches, 436 scored questions, +872.13 cumulative RBP. Best single match: Germany 7-1 Curaçao (+72.47 RBP, 9/10 beat crowd). Worst: Brazil 1-1 Morocco (-51.97 RBP, a gut-override of a researched 0.58-0.60 estimate to 1.00). Crowd-bias regression: n=85, r=0.83, residual SD ~7pp, OOS RMSE 5.8pp on BEL-EGY holdout. Beat-crowd rate 58.2% (423-question sample) vs. 72.4% on an earlier, narrower 246-question sample.
- **Cross-references:** Extremely heavily cross-referenced — cites `ML_EXPERIMENTS_NOTEBOOK.md`, `research_notes.md`, `bot/API_EXPLORATION_2026-06-27.md`, `datasets/build_master_dataset.py`, `datasets/MASTER_DATASET_DICTIONARY.md`, `STEPS_FOR_HIGH_POINTS.md`, `model/*.py`, `ml/*.py`, and `papers/*.pdf`.
- **Status:** A frozen/dated formal writeup as of Jul 10 — explicitly noted in `PAPER_REVISION_NOTES.md` (dated Jul 11) as already stale one day later (paper frozen at July 1 data of 49 matches/436 questions/+872 RBP vs. a live dataset by Jul 11 of 85 matches/921 questions/+3,246.04 RBP). Superseded in currency by later documents but retained as the canonical long-form writeup structure.

### `BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md`
- **Size/date:** 54,869 bytes, last modified Jul 14 13:51 (written same day, ahead of the France vs Spain semifinal)
- **Purpose:** A focused methodological deep-dive asking whether three specific rare/timing/race-type questions (on-field VAR review, goal between hydration breaks, first substitution) can be genuinely backtested given this project's sample size, or must be priced from reasoned domain judgment instead.
- **Contents:** Task A reviews what four classic football-modeling papers (Maher 1982, Dixon & Coles 1997, Constantinou & Fenton 2012/2013, Baio & Blangiardo 2010) actually say about validating rare sub-events — finding none address it directly, with paywalls/blocked fetches noted honestly. Task B imports quantitative-finance rare-event backtesting methodology: Kupiec's Proportion-of-Failures VaR test (only 65% power to detect a 3x rate misspecification even at T=255 trials), Christoffersen's conditional-coverage test, meteorology's rare-event verification literature, and survival-analysis/point-process methodology as frames for race-type and timing-window questions. Task C applies this to the project's own 100-match panel, finding the VAR question genuinely sample-starved (1 verified review in 12 matches) while the timing and race questions are NOT sample-starved but face different problems (window-definition fragility; irreducible single-match variance). Ends with a direct practical answer and a results/decision table for all 15 France-Spain questions.
- **Key numbers/results:** 1 verified on-field review in 12 matches. Goal-between-hydration-breaks: 74/99 matches had a goal in that window (~74.7%). Kupiec's own worked example: T=255 trials gives only 65% power against a 3x rate misspecification.
- **Cross-references:** Explicitly builds on `ML_MODEL_BUILD_RESEARCH_2026-07-13.md` (cites sections directly). References `ml/backtests/PREREGISTRATION_sot_hierarchical_backtest.md`, `PREREGISTRATION_cards_corners_offsides_and_combined.md`, `matches/France Vs Spain (Jul.14.26)/` files, and `ml/backtests/build_rare_event_panels.py`.
- **Status:** A finished, self-contained methodology memo written for one specific live match decision.

### `DOCUMENTATION_RESEARCH.md`
- **Size/date:** 40,559 bytes (224 lines), last modified Jun 29 11:49
- **Purpose:** Research survey answering "how should this project's writeup be structured?" — surveying real capstone/portfolio writeups, forecasting-community writeups, sports-analytics methodology pages, and data-provenance documentation standards, to derive a credible document structure before drafting the main paper.
- **Contents:** Four "buckets" of real, verified exemplars (16 numbered sources), each with URL, structure, and fetch-failure notes where relevant. Bucket 1: academic capstones (UC Berkeley MIDS, Stanford CS229, CMU). Bucket 2: forecasting-community writeups (Good Judgment, Metaculus). Bucket 3: sports-analytics methodology (clubelo.com, FiveThirtyEight SPI, a Kaggle writeup). Bucket 4: data-provenance exemplars (Gebru et al.'s "Datasheets for Datasets," FiveThirtyEight's data dictionary). Closes with a synthesized 12-section recommended document structure and a "what to avoid" list.
- **Cross-references:** The direct precursor/blueprint for `JTC_PROJECT_WRITEUP.md`'s 12-section structure.
- **Status:** A finished, one-time research deliverable; recommendations subsequently implemented in `JTC_PROJECT_WRITEUP.md`.

### `PAPER_REVISION_NOTES.md`
- **Size/date:** 30,631 bytes (489 lines), last modified Jul 11 00:37
- **Purpose:** A structured, section-by-section revision plan for `JTC_WC2026_Research_Paper.Rmd`, compiled from a full re-read of the paper plus case studies and nine supporting research docs, to reconcile stale numbers and add new findings before final submission.
- **Contents:** Organized by paper section with Add/Update/Remove/Verify items, numbers cross-checked against the live master dataset. Section 5 is the most substantial addition: consolidates four independent negative ML results into a unified "ML doesn't help at this sample size" thesis, plus one live counter-example (Canada-Morocco, -80.83 RBP). Section 10 is a hard style checklist derived from `ACADEMIC_STYLE_NOTES.md`. Section 12 records final decisions and recomputes the crowd-bias regression on all 772 questions.
- **Key numbers/results:** Headline dataset gap: paper frozen at 49 matches/436 questions/+872 RBP (Jul 1) vs. live dataset at 85 matches/921 questions/+3,246.04 RBP (Jul 11). Recomputed crowd-bias regression (n=772): `crowd = 0.5042 + 0.6087×(our_estimate−0.5)`, r=0.829. Leaderboard trajectory: rank 200/3,564 → 177/3,628 → top 1.11% (Jul 10).
- **Cross-references:** `JTC_WC2026_Research_Paper.Rmd`, `FRA_MAR_Full_Case_Study.Rmd`, `BRAZIL_VS_NORWAY_CASE_STUDY.md`, `ACADEMIC_STYLE_NOTES.md`, `WINNING_PATTERNS_SYNTHESIS.md`, `STRATEGIC_MARGIN_PUSH_RESEARCH.md`.
- **Status:** A working revision-planning document; ends with "Next step: draft the revised Rmd" — an action plan not yet fully executed into the paper at time of writing.

### `BRIER_RANK_PRESENTATION_NOTES.md`
- **Size/date:** 29,871 bytes (191 lines), last modified Jul 6 13:08
- **Purpose:** Research survey of how published forecasting-tournament papers present Brier-score evidence and rank/leaderboard progression, to determine the best presentation format for the JTC paper's results section.
- **Contents:** Reviews 11 real papers (Mellers et al., Tetlock et al., Inácio et al. 2020, Aldous 2019, Satopaa et al. 2025, Atanasov et al. 2020, Makridakis et al. 2022, a 2024 PLOS ONE football-crowd paper), each summarized for its figures/tables and applicability. Recommends a compact comparison table format, three standard baselines, and draft template sentences modeled on Tetlock 2014/Mellers 2014.
- **Key numbers/results:** Not itself a results document — works from placeholder numbers matching the paper's July 1 snapshot. Notes Atanasov et al.'s "Net Brier Points" metric as essentially matching JTC's own RBP definition.
- **Status:** A finished, one-time literature survey; structural recommendations remain reference guidance though its illustrative numbers are stale.

### `BRAZIL_VS_NORWAY_CASE_STUDY.md`
- **Size/date:** 27,640 bytes (406 lines), last modified Jul 11 00:26
- **Purpose:** A complete, standalone, fully-reproducible record of how all 15 questions in one Round-of-16 match (Brazil vs Norway, 2026-07-05) were priced — documented in full because it is one of the best single-match results of the campaign.
- **Contents:** Explains the JTC scoring rule, the two live data sources used (ESPN box scores, Smarkets with an 0.945 illiquidity discount), the pricing-tier framework (DIRECT/PLAYER_LIQUID/TEAM_MODEL), and the math (Poisson CDF, Brent's-method lambda-inversion, independent-compound probability). Section 4 is a question-by-question ledger (Q1-Q15) with exact reasoning, submission, crowd, outcome, and RBP for every question.
- **Key numbers/results:** Final score Brazil 1-2 Norway (upset; Norway priced at 20% pre-match). Total match RBP: +179.26, 13/15 beat crowd. Biggest win: independent per-team card-rate modeling beating a generic crowd heuristic, +59.43 RBP.
- **Cross-references:** Built on `JULY3_POSTMORTEM_DEEP_DIVE.md` and `WINNING_PATTERNS_SYNTHESIS.md`.
- **Status:** A finished, settled case-study artifact.

### `ACADEMIC_STYLE_NOTES.md`
- **Size/date:** 26,621 bytes (266 lines), last modified Jul 3 14:34
- **Purpose:** A close-reading style audit of five primary published statistics/econometrics papers, compiled to guide revision of the competition paper toward genuine academic register and away from "AI-drafted" tells.
- **Contents:** Eight numbered sections with direct quoted evidence from real papers (Karlis & Ntzoufras 2003, Constantinou & Fenton 2012, and others): prose vs. bullets, bold-text conventions, noun-phrase headers, inline coefficient reporting, regression-table conventions, limitations-section prose, sentence-length variation, and a direct list of what real papers do that AI drafts typically omit.
- **Cross-references:** Directly informs Section 10 of `PAPER_REVISION_NOTES.md`.
- **Status:** A finished, settled reference document; rules treated as fixed policy applied downstream.

### `TRAINING_DATASET_STRATEGY_2026-07-07.md`
- **Size/date:** 16,892 bytes (266 lines), last modified Jul 7 19:26
- **Purpose:** A strategic diagnosis of why the campaign was stuck around rank ~50 entering the knockout stage, concluding the binding constraint is training-data shape/scale, and researching a plan to build a genuine historical domain-training dataset.
- **Contents:** Distinguishes the meta-model/calibration dataset (already known too small, per `META_MODEL_LAB_NOTES.md`) from the missing domain-training dataset. Surveys benchmark football-ML literature. Section 4 hands-on-verifies two candidate sources: FBref via `worldfootballR` (found unreliable for granular international stats) versus StatsBomb open data (verified as the correct, homogeneous source).
- **Key numbers/results:** Usable homogeneous-schema international core identified: 314 matches across WC2018/WC2022/Euro2020/Euro2024/AFCON2023/Copa América 2024, yielding ~628 team-match rows and ~6,900 player-match rows.
- **Status:** "Research + verification complete. Build not yet started (awaiting go-ahead)" — a completed research memo with the actual dataset build deferred (subsequently executed, per `ml/`/`model/` and `data/` sections below).

### `META_MODEL_LAB_NOTES.md`
- **Size/date:** 13,178 bytes (223 lines), last modified Jul 5 00:51
- **Purpose:** A rigorous diagnostic asking whether a learned meta-model (logistic regression or GBDT) trained on existing structural features can outperform the hand-tuned rule-based blend of own-estimate and crowd-estimate.
- **Contents:** Documents the exact filtering used (404 rows/42 matches), feature engineering (19 features), two models tested against three zero-parameter baselines under two validation schemes (walk-forward and GroupKFold-by-match). Converts Brier-score improvement into RBP-equivalent terms.
- **Key numbers/results:** Best baseline (naive 50/50 average) Brier 0.2139. Walk-forward OOS: logistic regression -817.6 RBP-equivalent, HGB -147.9 RBP-equivalent — both worse than crowd. GroupKFold OOS: -1760.3 and -721.1 RBP-equivalent. Explicit decision: do not deploy either model.
- **Cross-references:** One of the "four independent negative results" synthesized in `PAPER_REVISION_NOTES.md` §5.
- **Status:** A finished, settled diagnostic with an explicit no-deploy decision. Also has a rendered `META_MODEL_LAB_NOTES.pdf` companion (59KB, Jul 5) — a PDF export of this same content, confirmed via `pdftotext` (same title/author/body).

### `CROWD_BIAS_REGRESSION_UPDATE.md`
- **Size/date:** 12,895 bytes (255 lines), last modified Jul 3 09:56
- **Purpose:** Re-fits the project's central crowd-compression regression on a 4.5x larger sample (n=384 vs. n=85) to check replication and tighten confidence intervals.
- **Contents:** Full reproducible R code, regression output, an OOS time-ordered check, a favorite-longshot-bias direction split, and a table of mean RBP by estimate-confidence bin.
- **Key numbers/results:** `crowd_estimate = 0.5109 + 0.5998 × (our_estimate − 0.5)`, n=384, r=0.828, 95% CI on slope [0.559, 0.641]. The only negative-RBP confidence bin is >0.70 ("high confidence YES").
- **Status:** Finished and settled; later confirmed (not contradicted) by a further update at n=772 in `PAPER_REVISION_NOTES.md`.

### `WINNING_PATTERNS_SYNTHESIS.md`
- **Size/date:** 7,629 bytes (61 lines), last modified Jul 5 13:44
- **Purpose:** A cross-match synthesis pulling every large win/loss across 5 settled matches (75 questions) into one table, formally naming two opposite, highly reliable pricing behaviors.
- **Contents:** Defines "Cluster A" (trusting a player's real production drought over a generous market price — reliably wins) versus "Cluster B" (projecting a favorite's SOT ceiling upward from a thin market line — reliably loses). Includes a France-Paraguay case study showing both clusters live at once.
- **Key numbers/results:** Cluster A: 7-for-7, net +144.67 RBP. Cluster B: 1-for-6 (excluding a reclassified case), net -155.64 RBP, worst single result -80.83.
- **Cross-references:** Cited and built upon by `BRAZIL_VS_NORWAY_CASE_STUDY.md` and `PAPER_REVISION_NOTES.md` §6.
- **Status:** A settled synthesis with adopted standing policy ("Cluster B should be retired, not patched").

### `ML_MODEL_BUILD_RESEARCH_2026-07-13.md`
- **Size/date:** 91,729 bytes, last modified Jul 14 00:17
- **Purpose:** A "foundation document" written by a research agent immediately before the France vs Spain semifinal to answer whether any new ML build is viable this late in the tournament, studying (A) Stefan Jansen's *Machine Learning for Trading* 3rd-ed. book repo, (B) sports-forecasting/ML literature broadly, and (C) synthesizing against the project's four prior failed ML attempts.
- **Contents:** Section 0 restates ground truth and the four prior ML rejections with a unifying diagnosis (independent unit is matches ~42–85, not questions ~730+; the crowd-alone baseline is hard to beat; the learnable effect is smaller than sampling noise). Task A is a chapter-by-chapter read of the ML4T repo (evidence boundaries, purging/embargo/CPCV, Deflated Sharpe Ratio/PBO, feature engineering discipline) mapped onto JTC's own practice. Task B surveys soccer modeling lineage, ratings/evaluation, the modern xG/ML era, FiveThirtyEight SPI, MLB sabermetrics, NBA/WNBA Elo, forecasting communities (Good Judgment Project, Metaculus), and small-sample evaluation theory. Task C synthesizes a ranked list of 8 candidate ML designs and a five-point enforceable decision rule for future ML deployment.
- **Key numbers/results:** Track record cited: ~+2100 cumulative RBP over ~86 matches. Master dataset ~730–943 rows, growing ~15 rows/match with only 2–3 matches left. Recommended feature budget ~8–12.
- **Cross-references:** Builds on `ML_EXPERIMENTS_NOTEBOOK.md`, `META_MODEL_LAB_NOTES.md`, `TRAINING_DATASET_STRATEGY_2026-07-07.md`, `STATSBOMB_INTEGRATION_AND_STATS_TESTS_2026-07-08.md`, and the France vs Spain match folder.
- **Status:** Living/most-recent research document at time of writing; recommends design #2 (hierarchical partial-pooling on domain panels — the model later built in `ml/backtests/`) as the one viable next ML piece.

### `PREDICTION_INSTRUMENT_WRITEUP.md`
- **Size/date:** 66,070 bytes, last modified Jul 1 19:59
- **Purpose:** A complete written account (companion to a visual taxonomy diagram, `prediction_instrument_map.pdf/.png`) of every instrument in the pricing pipeline, covering group stage through Round of 32.
- **Contents:** 5 layers: Raw Sources (ESPN/Smarkets API quirks, historical match JSON, pre-fitted model outputs), Statistical Processing (lambda-fitting, Poisson/Skellam, compound probability, time-window scaling), the Named Rule System (full write-ups of RULE7/RULE8/RULE14/RULE15/FLOOR_0.25/RULE12 with case studies), Question Categories (performance tables per tier: DIRECT_MARKET, TEAM_MODEL, PLAYER_LIQUID, TIMING_EARLY, PLAYER_ILLIQUID, TIMING_LATE), and Output (submission conventions, process-integrity failures). Ends with a fully worked example tracing one question through all 5 layers.
- **Key numbers/results:** 60+ matches, 436+ questions, +872 cumulative RBP as of Jul 1. Category performance: DIRECT_MARKET 73.5% beat-crowd; TIMING_LATE 42.9% beat-crowd (worst category); TIMING_EARLY 100%.
- **Status:** A settled, comprehensive reference document scoped through Jul 1; superseded in currency (not content) by later docs for matches after its cutoff.

### `research_notes.md`
- **Size/date:** 53,361 bytes, last modified Jun 10 11:19 — the oldest file in the repo, pre-tournament literature prep
- **Purpose:** Deep-read literature notes on 8 academic papers plus cross-sport forecasting practice, written before the campaign started to build a model/scoring-rule toolbox.
- **Contents:** Section-by-section notes on Dixon & Coles (1997), Karlis & Ntzoufras (2003), Crowder/Dixon/Ledford/Robinson (2002), Hvattum & Arntzen (2010), Murphy (1973)'s Brier decomposition, Constantinou & Fenton (2012)'s RPS argument, Foulley (2021), the "Wisdom of the Crowds" WC2018 paper, and cross-sport Elo practice. Ends with a master formula reference sheet.
- **Cross-references:** References papers in `papers/`; later cited as the intellectual foundation for `ML_MODEL_BUILD_RESEARCH_2026-07-13.md`'s Task B.
- **Status:** Foundational literature review, frozen since Jun 10; later docs build on and revisit its conclusions.

### `STATSBOMB_DATASET_AUDIT.md`
- **Size/date:** 43,663 bytes, last modified Jul 7 20:22
- **Purpose:** A comprehensive, read-only audit of the StatsBomb open-data dataset to evaluate its usefulness for base-rate and player-level modeling before integration into the pipeline.
- **Contents:** Full structural documentation of `competitions.json`, `matches/`, `events/` (all 33 event types with frequency counts and sub-schemas), `lineups/`, and `three-sixty/`. Includes a coverage analysis, data-quality section, and 9 concrete integration recommendations.
- **Key numbers/results:** 24 competitions, 3,961 unique matches, ~14.8M total events (estimated). WC2018 + WC2022 both fully covered (64 matches each) — the primary training base for WC2026.
- **Status:** A finished, point-in-time audit (2026-07-07), read-only; the data source consumed by `datasets/build_statsbomb_panel.py`.

### `STRATEGIC_MARGIN_PUSH_RESEARCH.md`
- **Size/date:** 31,811 bytes, last modified Jul 4 11:43
- **Purpose:** A pure game-theory/bet-sizing literature review answering whether there's a principled reason to submit a probability more extreme than one's calibrated estimate, bounded by risk-of-ruin logic.
- **Contents:** Surveys competitive-forecasting game theory (Lichtendahl & Winkler 2007, Frongillo et al. 2021, Lazear & Rosen 1981) and cross-domain analogues (mutual-fund tournaments, Grinold's tracking-error framework). Derives the exact per-question RBP math (pushing costs guaranteed S·δ² in expectation) and explains why Kelly logic doesn't transfer (RBP is additive, not compounding). Synthesizes a narrow, three-condition-gated exception capped at ~3-5 percentage points.
- **Key numbers/results:** E[ΔRBP] = −δ² exactly for any push δ past true belief.
- **Cross-references:** Its central recommendation was live-tested shortly after and partly falsified in `JULY3_POSTMORTEM_DEEP_DIVE.md`'s addendum (CAN-MOR, -80.94 RBP).
- **Status:** Finished research memo; live-tested with a mixed/negative real-world result.

### `MODEL_ONLY_VS_MARKET_BLENDED_COMPARISON.md`
- **Size/date:** 30,827 bytes, last modified Jul 9 13:58
- **Purpose:** Answers, across five R16 matches, how a market-free ("model-only") estimate would have compared to what was actually submitted, the crowd, and the real outcome — honesty-constrained to only report model-only figures actually recorded at pricing time.
- **Contents:** A §0 addendum documents and fixes the frozen-Elo bug (builds `ml/backtests/r16_point_in_time_elo_replay.py`). Five match sections (SUI-COL, MEX-ENG, USA-BEL, POR-ESP, ARG-EGY) each comparing model-only vs. submitted vs. crowd vs. outcome. Closes concluding the market's real value is as a check against confident thin-sample extrapolations, not as a generally superior source.
- **Key numbers/results:** SUI-COL (fully market-free) +144.6 RBP. MEX-ENG Q10: model-only 0.80-0.90 vs. submitted 0.40 vs. crowd 0.50 vs. actual YES — staying at market cost -16.79 RBP.
- **Status:** Finished analytical document with an embedded bug-fix that became a standing tool.

### `STEPS_FOR_HIGH_POINTS.md`
- **Size/date:** 27,430 bytes, last modified Jun 29 22:50
- **Purpose:** A full trail-analysis postmortem covering every settled question through 2026-06-26, codifying nameable patterns behind the campaign's biggest wins and losses.
- **Contents:** Part 1: 9 "Win Patterns" (2+ offsides defensive-underdog family, ESPN-verified mismatches, winner-narrative inflation, RULE15 suppression, market decomposition). Part 2: 9 "Loss Patterns" (blowout-context inversion, personal-conviction overrides — the BRA-MAR Q8 case that founded RULE6, process errors, compound-AND-question variance, the SAU-URU case that founded RULE14).
- **Key numbers/results:** 53 matches, 423 submitted questions, +812.15 cumulative RBP, 58.2% beat-crowd as of 2026-06-26.
- **Cross-references:** Built from `datasets/questions_flat.csv`; heavily cross-referenced by `DATASET_AUDIT_2026-06-26.md`, `KNOCKOUT_STAGE_PRICING_DEEP_DIVE.md`, `PREDICTION_INSTRUMENT_WRITEUP.md`.
- **Status:** Finished postmortem; numeric totals stale relative to the grown dataset, but qualitative rule findings remain actively-cited canon.

### `DATASET_AUDIT_2026-06-26.md`
- **Size/date:** 28,336 bytes, last modified Jul 12 12:04 (title date reflects the original investigation; appended to later)
- **Purpose:** A full record of consolidating scattered raw JSON/CSV research data into one flat dataset, framed as a pre-build scoping document.
- **Contents:** Documents three parallel investigation threads (raw-JSON schema-era inventory, external-source cataloguing, RULE1–15 taxonomy recovery). Identifies a confirmed bug (`build_feature_matrix.py` only checks the JSON key `post_match_results`, silently dropping 7 files using `post_match` instead). Section 7 (added later) documents the actual `master_question_dataset.csv` build and its validation against `STEPS_FOR_HIGH_POINTS.md`.
- **Key numbers/results:** Final output: 480 rows, 73 columns, +872.13 RBP over 436 scored questions (68.1% beat-crowd).
- **Status:** Foundational build-record; own row-count numbers explicitly flagged as stale (dataset since grown to 944+ rows) but preserved as an audit trail.

### `STATSBOMB_INTEGRATION_AND_STATS_TESTS_2026-07-08.md`
- **Size/date:** 24,381 bytes, last modified Jul 8 00:27
- **Purpose:** A self-contained session record building StatsBomb data pipelines and running three statistical diagnostics on the project's own performance data.
- **Contents:** §1 flattens StatsBomb event JSON into two flat tables (256-row team-match panel, 6,130-row player-match panel), every Python script with a matching R port. §2 tests a pure historical base-rate model against Portugal vs Croatia. §3 surfaces the ESPN/StatsBomb measurement-heterogeneity finding. §4 runs a cluster-robust OLS regression of RBP on structural features. §5 is a deliberate small-sample overfitting demo. §6 runs a Welch's t-test on whether deviating from crowd predicts RBP at question-level (wrong unit) vs. match-level (correct unit) — the two give opposite-signed results.
- **Key numbers/results:** POR-CRO base-rate model: +93.01 vs. actual +120.30 RBP-equivalent. T-test: question-level (n=771) +1.41 RBP wrong direction (p=0.116); match-level (n=71, correct) −1.68 RBP (p=0.056) — direction flips. ESPN/StatsBomb ratios: fouls ×0.80, cards ×0.73, SOT ×1.38, corners ×1.30.
- **Cross-references:** Companion to `STATSBOMB_DATASET_AUDIT.md` and `TRAINING_DATASET_STRATEGY_2026-07-07.md`; its t-test independently confirms `STRATEGIC_MARGIN_PUSH_RESEARCH.md`'s theoretical result; cited in `ML_MODEL_BUILD_RESEARCH_2026-07-13.md` as one of the four prior ML rejections.
- **Status:** Finished session record; negative meta/calibration findings treated as settled precedent, data-engineering outputs (the StatsBomb panels) remain actively used.

### `KNOCKOUT_STAGE_PRICING_DEEP_DIVE.md`
- **Size/date:** 16,654 bytes, last modified Jun 30 10:20
- **Purpose:** An audit of the pricing system for the new Round-of-32 15-question format, covering its first 4 matches, organized by pricing mechanism rather than by match.
- **Contents:** Classifies all 60 questions into 6 pricing-technique categories with a performance table. Documents what's working (direct market trust, team-level decomposition, early-hydration-window questions) and what's not (self-built late-window timing decomposition — worst category, illiquid offer-only player props, cross-team narrative extrapolation).
- **Key numbers/results:** 4 matches, 60 questions, +158.4 RBP, 68.3% beat-crowd. TIMING_NO_MARKET -63.72 RBP (worst); early-window timing +30.86 (3/3 positive) vs. late-window -45.90 (3/3 negative).
- **Cross-references:** Its category-performance framework became the standing taxonomy; directly echoed in `JULY3_POSTMORTEM_DEEP_DIVE.md` and `PREDICTION_INSTRUMENT_WRITEUP.md`.
- **Status:** Finished, dated audit; framework remains the standing taxonomy.

### `QF_SF_RETROSPECTIVE_AND_HARD_QUESTIONS.md`
- **Size/date:** ~9,500 bytes, last modified Jul 15 (written after the England vs Argentina SF settled).
- **Purpose:** A cross-match retrospective over all six quarterfinal + semifinal matches, built to (1) explain why each result went the way it did and (2) create a standing record of the "hard" question types — the "card before the first goal" family — with their track record.
- **Contents:** Per-match record table (6 matches), a corrected category-performance table, and a hard-vs-standard bucket split. The centerpiece is a full record of every "hard" question (novel/compound/timing/race — card-before-goal, event-in-each-half, stoppage-time goal, hydration-window, penalty-OR-red, half-comparison, novel-scorer-shirt, path-dependent-lead, VAR) ordered worst-to-best. Includes an honesty note on a classifier bug (the substring "var" inside "Álvarez" mis-tagged two player questions) and that no VAR question was ever scored (always dropped). Backed by the reproducible `data/processed/qf_sf_all_questions.csv` (87 rows).
- **Key numbers/results:** 5 crowd-scored matches, 72 questions, +658.88 RBP. Hard bucket n=15, +105.9, 73% positive, mean +7.06 vs standard bucket n=57, +553.0, 82% positive, mean +9.70. Worst single result: card-before-goal -28.4; hard-bucket jackpots pen-OR-red +24.4, hydration +23.3, half-comparison +21.7. Core finding: hard questions win when they have an anchor (market/trusted base rate/model decomposition) and lose when priced as un-anchored no-market heuristics sitting far from the crowd — reproducing `KNOCKOUT_STAGE_PRICING_DEEP_DIVE.md`'s TIMING_NO_MARKET-is-worst result.
- **Cross-references:** Generalizes `KNOCKOUT_STAGE_PRICING_DEEP_DIVE.md` and the England-Argentina `24_post_match_analysis.md`; the "shrink un-anchored far-from-crowd signals toward the crowd" rule echoes `STRATEGIC_MARGIN_PUSH_RESEARCH.md`.
- **Status:** Finished cross-match postmortem; its standing rule (a low-confidence flag on a no-market question must trigger a shrink toward the crowd, not just a note) recorded for the final.

### `JULY3_POSTMORTEM_DEEP_DIVE.md`
- **Size/date:** 16,681 bytes, last modified Jul 4 14:57
- **Purpose:** A postmortem tracing every RBP number for three July 3 matches back to its pricing instrument, with a same-week addendum live-testing two newly-derived rules.
- **Contents:** Dissects three failure clusters: the offside-question family bleeding points both directions (net -75.99 RBP, proposing `OFFSIDE_CROWD_ANCHOR`), underpricing a favorite's own SOT threshold (net -35.67 RBP, proposing `TEAM_SOT_EMPIRICAL_FLOOR`), and illiquid score-or-assist markets for out-of-form favorite-side players. The addendum reports Canada vs Morocco as the first live test: one rule worked, but `TEAM_SOT_EMPIRICAL_FLOOR` blew up (-80.94 RBP) because the team's sample never included a blowout-loss regime.
- **Key numbers/results:** Net across 3 matches: +107.81 RBP/45 questions. CAN-MOR addendum: +59.27 net masking a -80.94 single-question loss.
- **Cross-references:** Live-tests `STRATEGIC_MARGIN_PUSH_RESEARCH.md`'s de-shrinking lever, calling the CAN-MOR result its "first real-world check" (a partial refutation).
- **Status:** Finished postmortem with a live-tested addendum; one of the more consequential cross-references in the repo despite modest size.

### `MATCH_DATA_INVENTORY.md`
- **Size/date:** 12,687 bytes, last modified Jul 3 10:23
- **Purpose:** A campaign-wide data-completeness inventory across all 71 settled match research files, answering which data layers exist for which matches.
- **Contents:** Defines 6 schema "eras" the file format evolved through. Full 71-row per-match coverage table (ESPN/Smarkets/Model/Estimates/Rules/Crowd/Player/New-format). Closes flagging that the paper's Section 3.1 undercounts the match total (61 vs. actual 71).
- **Key numbers/results:** 71 total match files as of 2026-07-03. Coverage: ESPN 54/71, Crowd only 10/71 (14%), Model 31/71.
- **Status:** Finished, dated snapshot audit informing a specific paper edit; its own "71 matches" figure will itself go stale by design (point-in-time audits, not continuously updated).

### `PROJECT_TODO.md`
- **Size/date:** 10,647 bytes, last modified Jul 10 10:04; **owner-only permissions** (`rw-------`, unlike every other root file)
- **Purpose:** A generated bug-and-fix tracker cross-referencing every tracked item to the specific document that identified it, with re-verification against code/data rather than just trusting what the docs claim.
- **Contents:** Category A (real code bugs): the Poisson neutral-flag mismatch (confirmed fixed), the `post_match`/`post_match_results` key bug (open, deprioritized), the frozen-Elo issue (workaround exists), `backtest_vs_market.py` never run (subsequently run — see `model/` section below). Category B: stale-flag verification. Category C: five strategic next steps.
- **Key numbers/results:** Documents the exact before/after Poisson coefficients from the fix: buggy b1=0.25622 vs. fixed b1=0.23022.
- **Status:** A living/generated tracker — the closest thing in the repo to a maintained issue tracker.

### `README.md`
- **Size/date:** 5,651 bytes, last modified Jul 11 01:33
- **Purpose:** The top-level entry point — a solo, ongoing research project forecasting WC2026 matches for the JTC prediction tournament.
- **Contents:** A "Start here" pointer to the paper and case studies. A layout table mapping the project's logical layers (Literature → Raw/immutable → Processed → Mart → Modeling → ML/calibration → Pipeline/bot → Operational logs → Docs/writeups) to folders. A "Regenerating excluded data" section, and a standing rule: raw data is never mutated in place.
- **Status:** The canonical, actively maintained entry point — explicitly described as changing as the tournament progresses. *(Note: this repo map, `REPO_MAP.md`, is a deeper index that complements this README rather than replacing it — README is the tour, this file is the full catalog.)*

---

## 2. `topics/` — question-type navigation (start here)

The primary entry point for "how do we price question type X" — added 2026-07-15 to fix a
specific, named problem: before this, tracing a single question type (e.g. "total cards") meant
hunting across `ml/backtests/`, `model/`, `data/processed/`, several `matches/*/` folders, and
root-level MD notes with no consistent linking. `matches/*/` (Section 5) remains the right place
to look up "what happened in this specific match"; `topics/` is the complementary axis for
"what's our model/track record for this kind of question across every match."

**How this was built, and why it isn't a 100%-physical move:** files that are genuinely specific
to one question type were physically moved here via `git mv` (preserving history). Files that are
genuinely shared across multiple topics — the point-in-time Elo panels, the StatsBomb/ESPN/unified
training panels, the shared hierarchical-backtest library, the master dataset — were **not**
duplicated or moved, per this repo's own raw/processed-data discipline (see root `README.md`).
They stay in `model/`, `data/processed/`, `datasets/`, and `ml/backtests/` (now much smaller,
holding only genuinely cross-topic infrastructure — see Section 6), and every topic folder that
depends on one of them links to it explicitly in a "Shared inputs" table rather than copying it.

Each topic folder follows the same template: **what this topic covers**, **current status/verdict**
(PASS/FAIL where a backtest exists), **files in this folder**, **shared inputs** (exact paths to
dependencies that live elsewhere), **relevant matches**, and **root-doc mentions**.

| Topic | Folder | Status | Files here |
|---|---|---|---|
| Shots on Target | [`shots-on-target/`](topics/shots-on-target/README.md) | **PASS** (hierarchical GLMM) | 8 |
| Cards | [`cards/`](topics/cards/README.md) | **FAIL** (twice — original + referee-refined) | 6 |
| Corners | [`corners/`](topics/corners/README.md) | **PASS** | 3 |
| Offsides | [`offsides/`](topics/offsides/README.md) | **FAIL** (post-bug-fix; a retracted false-PASS is documented in full) | 2 |
| First Substitution / Timing | [`first-substitution/`](topics/first-substitution/README.md) | **FAIL** (confidently worse than baseline) | 4 |
| Player Props | [`player-props/`](topics/player-props/README.md) | Not usable (n=9 methodology demo) | 4 |
| Match Winner + Goals-Totals/BTTS | [`match-winner-goals-totals/`](topics/match-winner-goals-totals/README.md) | Fitted, in production (the classical pipeline) | 18 |
| Rare-Event Timing | [`rare-event-timing/`](topics/rare-event-timing/README.md) | Stub — no dedicated model yet | 0 (README only) |
| VAR Review | [`var-review/`](topics/var-review/README.md) | Stub — genuinely sample-starved | 0 (README only) |
| Penalties / Red Cards | [`penalties-red-cards/`](topics/penalties-red-cards/README.md) | Researched — no fitted model (base-rate + market); see `PENALTY_MODELING_RESEARCH.md` | 1 (+README) |
| Half-Time Splits | [`half-time-splits/`](topics/half-time-splits/README.md) | Stub — market-anchored, no model needed | 0 (README only) |
| Fouls | [`fouls/`](topics/fouls/README.md) | Stub — folded into Cards as a covariate | 0 (README only) |
| Combined-Threshold Composition | [`combined-threshold/`](topics/combined-threshold/README.md) | Stub — a methodology, not a question type; see the 3 families above | 0 (README only) |

This is the taxonomy actually used across the project's preregistration docs, the RULE1–18
system, and the `tier` tags in `matches/*/04_rules_applied.json` — not an invented one. 8 of the
14 topics have dedicated files; the other 6 are README-only stubs completing the taxonomy so
every question type has exactly one canonical folder to check, even ones without a fitted model.
(Penalties / Red Cards moved from stub to having a dedicated file — `PENALTY_MODELING_RESEARCH.md`,
a deep research doc that reviews our own penalty-pricing track record, computes an empirical
base rate from the StatsBomb corpus, surveys academic + cross-sport modeling, and concludes a
fitted covariate model is un-viable at this sample size, so the family stays market/base-rate-anchored.)

**Reused pattern from `writeups/`:** every topic README's links are verified to resolve, the same
discipline `writeups/README.md` already used for its 100 cross-repo links (see Section 8) — now
extended repo-wide via `scripts/verify_md_links.py`, added as part of this reorg
(percent-decodes every markdown link, checks `os.path.exists`, run repo-wide as the final
verification step).

---

## 3. `bot/` — live API pipeline

The live API bot pipeline for the SportsPredict/JTC platform: endpoint-discovery research, fetch
scripts (SportsPredict web/v1 API, Smarkets betting exchange, ESPN box scores), a prediction
generator, a competitor-scraping tool, session/auth setup, and raw/processed data snapshots under
`bot/data/`.

### `bot/API_EXPLORATION_2026-06-27.md`
Research memo documenting a live browser-network-interception session (Playwright) to reverse-engineer the SportsPredict web app's internal API — the documented external API (`api.sportspredict.com/api/v1`) only exposes `/matches` and `/markets`. Establishes two namespaces: `v1` (Bearer token) and unversioned `web` (browser-only, HTTP-only session cookie). Documents discovered endpoints (`/api/trades`, leaderboard, rank, user summaries) and key IDs (JTC event id, Group Stage lobby id). Lays out the build plan `setup_session.py` → `fetch_dashboard.py`. Superseded in part by `PERFORMANCE_PAGE_DISCOVERY_2026-07-14.md`.

### `bot/FORECASTING_DATASET_DESIGN.md`
Academic-style memo proposing a schema/analysis plan for the JTC forecasting dataset, drawing on the Good Judgment Project, Metaculus, prediction markets, and weather-ensemble (EMOS) calibration literature. Proposes three flat-file schemas (`forecasts.csv`, `question_difficulty.csv`, `player_calibration.csv`), a 5-category question taxonomy, and derived features (Brier decomposition, log score, IRT-style skill, GJP-style "extremizing"). Lists 7 concrete pitfalls (temporal leakage, sparse forecasters, confirmed duplicate accounts in the top-30). Not implemented as code in this directory.

### `bot/PERFORMANCE_PAGE_DISCOVERY_2026-07-14.md`
Discovery notes on a newly added "My Performance" page in the SportsPredict web app (`play.sportspredict.com/probability-events/{eventId}/performance-summary`, backed by `POST /api/probability/performance`). Documents an account toggle between "Me" (Souparneya's manual forecasts, 986 settled) and "Abir's Bot" (a separate low-volume identity, 1 forecast, RBP -10.6) under one login — corrects the earlier assumption that AbirC might be a different user. Captures actual pulled performance data: RBP gap +3.9 vs. crowd (89th percentile), 986 forecasts settled, best match Brazil vs Norway +177.5, worst Spain vs Belgium -83.0. Most recent doc in the directory; proposes an unbuilt `fetch_performance.py`.

### `bot/bash_log_2026-06-27.txt` through `bash_log_2026-06-28.txt` (5 files)
Session transcripts (163–438 lines each) documenting the iterative process of finding the platform's real auth mechanism. Key findings across the series: `/api/trades` exposes public lobby trades (73 trades/16 competitors); `current_value` on settled markets encodes binary outcome (0/100); the critical discovery that the app's auth JWT lives in browser `localStorage`, not cookies (found on the 3rd iteration of `setup_session.py`); the distinction between "daily/lobby" (100-230 scale) and "global" (2000+ scale) leaderboard endpoints; and a manual browser-console scrape (React Router pushState trick) that pulled the full 570-row question-level forecast history later formalized as `bot/data/prob_cup/abirc_forecasts.csv`.

### `bot/classify_markets.py`
Classifies every market question into categories the project's models can handle (`match_winner`, `total_goals_under/over`, `btts_and_over`) via regex, with everything else falling into `no_model`. Exposes a reusable `classify()` function imported by `predict_markets.py`.

### `bot/compile_fra_esp_espn_form.py`
One-off compiler building form-data for France vs Spain from 12 raw ESPN game summaries (all 6 games each team played). Extracts team box-score stats, per-game lines for Mbappé and Yamal, and substitution timing. Also parses the SF fixture for squad rosters/jersey numbers. Writes `matches/France Vs Spain (Jul.14.26)/10_espn_form.json`. Match-specific, hardcoded event IDs.

### `bot/discover_endpoints.py`
Deliberate one-time, low-quota probe of plausible `v1` API endpoints beyond the two known-working ones. Writes results incrementally to `bot/data/endpoint_discovery.jsonl`. Superseded by the finding (in `API_EXPLORATION_2026-06-27.md`) that the real data lives in the separate `web` namespace, not `v1` — this script's premise was the wrong namespace.

### `bot/fetch_dashboard.py`
Daily dashboard fetcher — pulls match schedule, rank, settled results, and standing from the web API, prints a formatted summary, and saves a dated snapshot. Defines fetchers for matches (v1/Bearer), trades/rank/summary/leaderboard (web/cookie). Defensive field-name fallbacks in trade parsing suggest the exact trades schema wasn't fully confirmed at write time. A snapshot exists confirming successful runs.

### `bot/fetch_fra_esp_smarkets.py`
One-off Smarkets quote fetcher for France vs Spain — 26 hardcoded market IDs (FTR, correct score, BTTS, goal lines, cards, team goals, SOT, player props) from event 45192700. Has resume support for rate-limit recovery. Notes 4 markets don't exist for this fixture (offsides, VAR, Spain team SOT, first sub). Directly feeds `simulate_fra_esp_sf.py`.

### `bot/fetch_eng_arg_smarkets.py`
Same pattern for the England vs Argentina SF — 21 market IDs (to-qualify, FTR, BTTS, HT result, team goals, corners O/U + handicap, cards O/U + per-team, penalty, team SOT, and Messi/Kane/Bellingham/Álvarez player props) discovered live from event 45195225's full 180-market list, with resume support for rate-limit recovery. Writes `matches/England Vs Argentina (Jul.15.26)/10_smarkets_quotes_{raw,processed}.json`. The newest of the per-match Smarkets fetchers.

### `bot/fetch_fra_mar_smarkets.py`
Earlier, simpler version of the same pattern for the France vs Morocco QF (event 45178292, 12 hardcoded markets, no resume logic) — the direct precursor to `fetch_fra_esp_smarkets.py` and later `fetch_team_prop_markets.py`.

### `bot/fetch_markets.py`
The original/core `v1`-namespace data-collection script — pulls all open matches and their markets, writes incrementally to `bot/data/matches.json` and `bot/data/markets_raw.jsonl` (361KB accumulated), with resume logic and 429-rate-limit handling. Direct input to `classify_markets.py` and `predict_markets.py`.

### `bot/fetch_smarkets_mapping.py`
One-time build of a metadata-only mapping from every Smarkets WC2026 fixture (71 total) to its full market list (id + name, no prices). Writes `bot/data/external/smarkets_markets_by_match.jsonl`. References a `fetch_smarkets_prices.py` that doesn't exist — that role was filled instead by the match-specific fetch scripts.

### `bot/fetch_team_prop_markets.py`
The generalized, reusable Smarkets team-prop fetcher — CLI tool discovering SOT/cards/corners markets by name-pattern regex for any event, instead of a hand-written per-match script. Newest of the Smarkets scripts; built specifically to grow the sample size for the GLMM-vs-market comparison (see `ml/backtests/sot_vs_market_comparison.py`, "stuck at 11 matches"). Writes to `ml/backtests/live_market_watch/`.

### `bot/markets_sample.json` / `bot/matches_raw.json`
Static schema-reference snapshots (not live pipeline outputs) — one match's `/markets` response (10 questions) and the full `/matches` schedule response, respectively.

### `bot/predict_markets.py`
Computes model probabilities for every classifiable market question, producing a manual-review CSV. Uses `model/ordered_logit.py` for match-winner and a Dixon-Coles/NB-corrected scoreline grid (`model/dixon_coles.py`) for goals/BTTS markets, matched to fixtures via team-code translation. Writes `bot/data/predictions_review.csv` — explicitly for manual review, not auto-submission.

### `bot/scrape_competitors.py`
Scrapes all publicly visible data on the 16 competitors in the JTC lobby via the web-namespace trades endpoint. Runs `strip_pii()` on every record before writing to disk (removes real names/emails) — a fix applied after an earlier scrape (per the bash logs) captured emails before this was added. Builds enriched win-rate/entry-price profiles per competitor across 7 output files.

### `bot/setup_session.py`
The one-time interactive Playwright session extractor nearly every other script's error path points to. Opens a real browser, watches for a Bearer `Authorization` header, falls back to scanning `localStorage`/`sessionStorage` for a JWT if none is seen in headers, validates the captured token against 4 endpoints, and saves it into `secrets.json`.

### `bot/simulate_fra_esp_sf.py`
The joint Monte Carlo match simulation for France vs Spain — the most methodologically sophisticated script in this directory. Fits `(lambda_France, lambda_Spain, rho)` to Smarkets market quotes via a Dixon-Coles-corrected scoreline grid, fits a within-match goal-timing slope to the "first goal bracket" market, and runs 200,000 simulated matches so every goal-structure question (totals, BTTS, timing windows, extra time) answers off one internally-consistent draw rather than separate fitted models. Separately calibrates cards (Gamma-Poisson) and SOT (Poisson) layers to their own market lines; offsides uses empirical lambdas since no market exists. Outputs `11_simulation_results.json`.

### `bot/team_code_map.py`
Static lookup mapping SportsPredict's team codes to the Elo panel's team-name spelling convention (~46 entries), plus a `parse_match_name()` helper. Small, stable dependency of `predict_markets.py`.

### `bot/test_web_api.py`
Quick diagnostic checking whether the existing `v1` Bearer token also works on `web`-namespace endpoints (6 fixed test calls), to decide whether Playwright session extraction is actually needed. Referenced by `fetch_dashboard.py`'s own error messages as the first thing to try.

### `bot/secrets.json`
Credentials store (not read here). Based on how other scripts reference it: `sportspredict_api_key`, `session_cookies`, `sp_user_id`, `web_session_token`, `session_extracted_at`, `bot_name`. Gitignored, owner-only permissions (`-rw-------`).

### `bot/data/` (subdirectory)
Accumulated outputs of the scripts above — 7 files at the top level (`markets_raw.jsonl`, `matches.json`, `predictions_review.csv`, `discovered_endpoints.csv`, etc.) plus 9 subdirectories from specific scrape sessions (`competitor_data/`, `dashboard_snapshots/`, `external/`, `jtc_leaderboard/`, `jtc_predictions/`, `jtc_prob_leaderboard/`, `match_questions/`, `prob_cup/`, `today_2026-06-27/`) — roughly 45-50 files total.

---

## 4. `data/` and `datasets/`

Excluded per scope: `data/external/statsbomb/open-data/` — full clone of the public statsbomb/open-data repo (~9,000 files), gitignored, re-clonable, used as raw source for `build_statsbomb_panel.py`.

Also out of catalog scope (top-level research/notes markdown files directly under `data/`, listed for navigation only, not read in full here): `DATA_XRAY.md` (a full inventory doc of the project's 4 data "layers," written 2026-06-22 — a useful entry point for future ML integration work), `ML_RESEARCH_AGENT_NOTES.md`, `alt_data_sources.md`, `alt_data_sources_research.md`, `calibration_research_notes.md`, `code_audit_findings.md`, `crowd_consensus_prediction_research.md`, `edge_research.md`, `granular_data_sources_research.md`, `ml_integration_research_notes.md`, `ml_methodology_deep_dive_notes.md`, `prop_market_pricing_notes.md`. Also `data/scratch_web_matches.json` (a scratch file).

### `data/processed/build_espn_panel.py`
Pulls per-team-per-match box-score stats from the ESPN public API (`site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary?event={id}`) for a hardcoded list of WC2026 event IDs (98 matches as of the 2026-07-14 update, group stage through QF: `760414`–`760513`). Writes `espn_match_panel.csv` (2 rows/match, ~24 box-score columns) and `espn_rolling_averages.csv` (same, plus a per-team rolling average of each stat across prior tournament matches, computed strictly before each match's date). Docstring caveat: the event-ID/team-abbreviation mapping is hardcoded and "should be re-verified if ESPN changes team abbreviations or event IDs"; last verified 2026-07-03.

### `data/processed/build_halftime_sub_and_referee_panels.py`
Reads every `matches/*/espn_*.json` full-summary dump (files with both `keyEvents` and `gameInfo`), dedupes by ESPN event ID. Writes `halftime_sub_panel.csv` (per match: did either team substitute in the second-half-restart window, clock ≤ 47:00 — a threshold chosen from an observed clean bimodal gap in the data) and `referee_card_panel.csv` (per match: referee name + total match cards). Explicit caveat: sample is WC2026-only and incomplete (~30-40 of ~90 played matches — only those whose ESPN dumps happened to be saved during earlier case-study work) — "treat rates as directional, not precise."

### `data/processed/build_kfactor_map.py`
Classifies every distinct tournament name in `results.csv` into an Elo K-factor tier (60=World Cup finals, 50=continental finals/major intercontinental, 40=WC/major-confederation qualifiers, 30=other tournaments, 20=friendlies) per the eloratings.net published methodology. Writes `tournament_kfactor_map.csv`. Static, one-time classification.

### `data/processed/qf_sf_all_questions.csv`
The reproducible dataset behind `QF_SF_RETROSPECTIVE_AND_HARD_QUESTIONS.md` (Section 1): 87 rows, one per question priced across all six quarterfinal + semifinal matches, with our estimate, crowd, outcome, RBP, beat-crowd, and a `hard_type` tag (card-before-goal, hydration-window, penalty-OR-red, etc.). Extracted from each match's own settlement file (`06_post_match_results.json` / `14_actual_submission.json` / `23_post_match_results.json`); Spain-Belgium's rows carry no RBP/crowd (the deliberate no-crowd session).

### `data/processed/fetch_all_raw_events.py`
Fetches full ESPN event-summary JSON (goal/card/sub/VAR timeline via `keyEvents`, not just aggregated team totals) for every match_id in `espn_match_panel.csv`, resumable, one file per match to `espn_raw_events/espn_event_{id}.json`. Built specifically to support rare-event/timing/race-type questions the aggregate panel and hierarchical GLMM can't answer.

### `data/processed/fetch_betting_markets.py`
Pulls open probability-event markets from the play.sportspredict.com API for the Jump Trading Probability Cup event, categorizes each question by regex/keyword, writes a raw snapshot plus `betting_markets_overview.md` — a coverage report noting which market categories the project's data can price (match result, full-match goals/BTTS/totals) vs. cannot (half-time splits, anytime goalscorer, shots, cards, fouls, offsides, corners, assists, penalties — all flagged "data gap").

### Key `data/processed/` output files
- **`elo_current_ratings.csv`** (337 lines) — current Elo snapshot per team, built by `model/elo.py`.
- **`elo_match_panel.csv`** (49,473 lines) — full historical Elo replay over every match in `international_results/results.csv` since 1872-11-30, with pre-match Elo and applied K-factor. The project's core historical training panel.
- **`espn_match_panel.csv` / `espn_rolling_averages.csv`** (201 lines each) — see `build_espn_panel.py` above.
- **`halftime_sub_panel.csv` / `referee_card_panel.csv`** (60 lines each) — see build script above; known incomplete WC2026-only coverage.
- **`jumpcup_covered_markets.csv`** (132 lines) / **`jumpcup_markets_raw.json`** (720 market objects) — flattened and raw SportsPredict market snapshots.
- **`model_standard_errors.json`, `nb_dispersion_coefs.json`, `ordered_logit_coefs.json`, `poisson_goals_coefs.json`** — fitted coefficients for the project's core statistical models (Poisson GLM, ordered logit, NB dispersion), read directly by `datasets/build_master_dataset.py` as a fallback whenever a raw match file lacks its own recorded model output.
- **`statsbomb_team_match_panel.csv` / `statsbomb_player_match_panel.csv`** (+ R-ported `_r.csv` twins) — 257/6,131 lines; built by `datasets/build_statsbomb_panel.py`/`.R` (see below).
- **`statsbomb_goals_distribution.png` / `statsbomb_shots_vs_sot.png`** — plots from `datasets/explore_statsbomb_data.R`.
- **`tournament_kfactor_map.csv`** (201 lines) — output of `build_kfactor_map.py`.
- **`unified_team_match_panel.csv` / `_r.csv`** (427/457 lines, row-count mismatch not reconciled) — pools the WC2026 ESPN panel with the WC2018+2022 StatsBomb panel, tagged by `data_source`. **Documented caveat in the build script's own docstring: ESPN and StatsBomb are NOT guaranteed to measure the same stat the same way** — the `data_source` column exists specifically so downstream consumers don't silently pool across the measurement-convention boundary; a same-team cross-source rate-comparison sanity check is printed at build time.
- **`unified_team_match_panel_with_pit_elo.csv`** (457 lines) — adds `elo_pre, elo_diff_pre, neutral_pit` via `ml/backtests/add_pit_elo_to_unified_panel.py`.
- **`unified_team_match_panel_with_referee.csv`** (457 lines) — adds `referee_name_full, is_knockout`.
- **`wc2026_pit_elo_panel.csv`** (201 lines) — point-in-time Elo replay for WC2026 matches, built by `ml/backtests/build_full_tournament_pit_elo.py`.
- **`espn_raw_events/`** (~100 files, `espn_event_{id}.json`) — raw, un-flattened ESPN match-summary API responses (full `keyEvents` timeline, per-player rosters, free-text commentary) — the source `espn_match_panel.csv` is aggregated from, used directly for finer-grained question types (hydration-break timing, substitute-scored goals, brace detection).
- **`betting_markets_overview.md`** — human-readable coverage report from `fetch_betting_markets.py`.

### `data/external/altitude/wc2026_venue_altitude.csv`
17 lines (16 venues) — manually curated venue altitude; Mexico City/Estadio Azteca (2240m) flagged as the highest WC2026 venue with a documented physiological effect on visiting teams. Joined into `master_question_dataset.csv` via `venue_city`.

### `data/external/fifa_ranking/`
`fifa_ranking-2020-12-10.csv` (62,425 lines, stale, superseded) and `ranking_fifa_historical.csv` (67,895 lines, more current but still not the primary source) — per `MASTER_DATASET_DICTIONARY.md`, neither is the primary FIFA-ranking source in the master dataset; the more current Transfermarkt `fifa_ranking` field wins instead.

### `data/external/odds/`
`extract_international_odds.py` filters a general multi-league `eatpizzanot/soccer-dataset` CSV dump (`fixtures.csv` 378,563 lines, `odds.csv` 220,287 lines, `teams.csv` 6,406 lines with an unused `rating_mu`/`rating_sigma` TrueSkill-style pair, `leagues.csv` 145 lines) down to 11 hardcoded international `league_id`s, writing `international_fixture_odds.csv` (564 lines — only fixtures with ≥1 bookmaker quote).

### `data/external/transfermarkt/`
`extract_relevant.py` filters the full third-party `transfermarkt-datasets` dump to national-team-relevant subsets in `extracted/`: `national_teams.csv` (119 lines — the **primary** squad-value/age/FIFA-ranking source joined into `master_question_dataset.csv`; explicitly null for Cape Verde, Curaçao, DR Congo, Haiti, Ivory Coast, which are absent from the extract), `national_team_players.csv` (2,455 lines), `national_team_player_valuations.csv` (7,251 lines), `national_team_games.csv` (671 lines, filtered to World Cup/Euro/Copa América/Asian Cup/AFCON).

### `data/external/travel/`
`build_travel_rest_features.py` builds `team_venue_distances.csv` (3,601 lines — haversine distance from each team's capital to each WC2026 venue, with manual alias/coordinate override tables for UK home nations, Kosovo, Palestine, etc.) and `rest_days_features.csv` (98,801 lines), from two raw reference inputs: `country_capitals.csv` (234 lines — third-party capital-city coordinate table) and `wc2026_venue_coords.csv` (17 lines — the 16 venues' lat/long). The script's own docstring notes the rest-days file is "fully derivable from existing data" and is included only for feature-group cohesion — and per `MASTER_DATASET_DICTIONARY.md` it's actually **flagged stale and unused**: it "stops 2026-06-09, before the tournament even started," so `build_master_dataset.py` deliberately recomputes rest days fresh from `results.csv` instead.

### `data/international_results/` (third-party, martj42-style dump)
`README.md` documents 49,398 international full-international results 1872–2024 (sourced from Wikipedia/rsssf.com/football associations). `results.csv` (49,473 lines, through present + future-dated WC2026 fixtures) is **the project's single source of truth for historical match results**, joined against repeatedly across the pipeline. Also `goalscorers.csv` (47,602 lines), `shootouts.csv` (678 lines), `former_names.csv` (37 lines, team-name-change mapping), plus a `LICENSE` and `.github/FUNDING.yml` (standard third-party repo metadata, not project content).

### `data/soccer-elo/` (third-party repo)
Scrapes yearly (Dec 31 snapshot) Elo ratings from eloratings.net for 1901–2023 via Selenium (`code/scrapping.R`, fragile-by-construction but a one-time historical scrape). Output `csv/ranking_soccer_1901-2023.csv` (17,201 lines) — distinct granularity from the project's own match-by-match `elo_match_panel.csv`. Also carries its own `README.md`, `LICENCE`, `.gitattributes`, `.gitignore` (standard third-party repo metadata).

### `data/external_markets/` — the per-match research archive
~100 per-match JSON/JSONL files plus `raw_summaries/` (6 files) and 8 markdown research/analysis logs plus the master `MATCH_LOG.md`. Schema (per-match files, e.g. `bel_egy_2026-06-15.json`): `match, sportspredict_event_id/match_id, smarkets_event_id, espn_event_id, closing_time, context_note, sources` (tagged `VERIFIED_API` vs `UNVERIFIED_SEARCH_SUMMARY`), `derived_estimates_for_sportspredict_markets`/`derived_estimates_draft` (pre-match reasoning + `recommended_estimate` per question), `post_match_results` (final score, RBP, beat-crowd count, per-question `{us, crowd, outcome, rbp, category}`). **Q-numbers are documented as NOT a reliable cross-container join key within a single file** (see `datasets/build_master_dataset.py` below). Also present: `*_smarkets_quotes/parsed/raw.json` (raw Smarkets pulls), `*_wc2026_raw.jsonl`/`*_wc2022_raw.jsonl` (10 files, flattened per-team-per-match stat rows), `settled_markets_ledger.json` (95 questions across 10 matches, self-documenting via its own `_schema` block).

- **`MATCH_LOG.md`** (756 lines, read in full) — the master narrative index: per-match table (score, RBP, beat-crowd count, links) from KOR-CZE (2026-06-11) through TUR-USA (2026-06-25), plus per-match postmortems and the numbered "RULE" heuristics built up match-by-match (RULE1–RULE12+), e.g. RULE6 ("never submit 0%/100% on any probability question," from the BRA-MAR Q8 -51.97 gut-override disaster), RULE8 (shrink count-comparison props toward 50% when pre-match draw probability is elevated), RULE10 (in blowouts, the winning team fouls ≥ the losing team regardless of historical averages), RULE12 (pre-submission risk gate for realdata "X more than Y" props with no market to cross-check). Running total noted mid-document: "+393.31 RBP across 220 graded questions" (partial — `datasets/questions_flat.csv` is the authoritative complete record, +812.15 RBP / 58.2% beat-crowd across 423 questions as of 2026-06-26).
- **`bih_canada_dzeko_realdata.md`** — real ESPN boxscore tables for Bosnia's last 5 matches and Canada's recent friendlies, plus Dzeko's individual stats; notes ESPN's `fifa.friendly` endpoint doesn't expose team-level fouls/corners/possession for friendlies.
- **`can_bih_research_log.md`** — 4-session hunt for corroborating odds sources across Betfair/Oddschecker/Pinnacle/Kalshi/Polymarket/Robinhood/1xBet etc.; catches and removes a hallucinated market (a nonexistent Polymarket corners sub-market fabricated by a prior research agent when a fetch silently failed), introduces the `VERIFIED_API`/`UNVERIFIED_SEARCH_SUMMARY`/`DISPROVEN_REMOVED` tagging convention; root-causes the match's only loss to an oversized home-advantage coefficient wrongly applied to a World-Cup host-nation fixture.
- **`crowd_correlation_analysis.md`** — first regression of SportsPredict crowd vs. project estimates (n=85, 9 matches): `crowd ≈ 0.514 + 0.61*(us − 0.5)` (corr=0.83), a quantified Snowberg-Wolfers favorite-longshot bias; introduces RULE12.
- **`crowd_model_analysis.md`** — earlier (2026-06-13) crowd-vs-verified-market comparison (17 questions, 3 matches): crowd ≥ market 15/17, market beats crowd on raw accuracy 11/17; derives "submit average(crowd, verified_sharp_market)" for match-winner questions.
- **`game_dynamics_analysis.md`** — cross-match goal/foul/card timeline analysis (first 7 settled matches, 24 goal events), triggered by a loss traced to an 88th-minute equalizer; finds the conceding team commits its next foul within 10 minutes 79% of the time.
- **`rsa_can_2026-06-28_new_question_types_sources.md`** — sourcing-verification for 3 new knockout-stage question types (hydration breaks, sub-scored goals, any-player-brace); confirms ESPN's `keyEvents` as Tier-1 for break timing; documents a genuine data gap (no minute-tagged offside events exist in ESPN's structured data); documents Smarkets' `/events/` name/query filters are silently non-functional.
- **`usa_par_realdata.md`** — real ESPN data + worked Skellam/Poisson derivations for 3 specific questions.

### `datasets/build_master_dataset.py`
The project's central data-fusion script: reads every `data/external_markets/*.json` file plus every knockout-stage `matches/*/` directory, joins in Elo, rest days (recomputed fresh, not the stale travel file), venue/altitude, Transfermarkt squad data, ESPN rolling stats, and the model coefficient JSONs — into one long question-level flat file (`master_question_dataset.csv`, read-only against everything else). Solves two documented cross-file hazards: (1) the top-level post-match-results key varies (`post_match_results` vs `post_match`) — an earlier out-of-scope script only checked one and silently dropped ~7 of 49 matches; (2) **Q-numbers are not a reliable join key across a single file's own containers** (verified concretely: `eng_cro`'s Kane SOT question is `q5` in the draft but `Q7` in the final; `cro_pan`'s first 4 questions rotate position by one) — resolved via topic-word Jaccard matching (≥2 shared tokens, Jaccard≥0.35, global greedy assignment) rather than position, unmatched rows left blank rather than risk a silent wrong pairing. *(This is the origin of the project's standing [[feedback_qnumber_join_safety]] rule — never use position/Q-number as a cross-container join key.)*

### `datasets/MASTER_DATASET_DICTIONARY.md` (89 lines, read in full)
Data dictionary for `master_question_dataset.csv`: documents grain (one row per match×question), every column, and honest limitations — 12 R32-stage matches (2026-06-26–06-30) have zero rows because settlement data was never pasted back in; squad fields null for 5 teams absent from Transfermarkt; `recommended_estimate` populated for only ~24% of rows (114/480); explains the Q-number join hazard in detail; notes `our_brier_score` and `rbp` are NOT the same metric. As of the referenced 2026-07-06 rebuild: 730 rows/66 matches/107 columns — the CSV on disk has since grown to 944 lines, i.e. rebuilt again since the dictionary's own header was last updated.

### `datasets/build_statsbomb_panel.py` (+ `.R` port)
Flattens StatsBomb open-data (WC2018+2022, 128 matches) into the team/player match panels. Extensive methodology docstring: SOT = outcome in {Goal, Saved, Saved To Post}; cards from lineups' own array (authoritative over re-deriving from events); corners = Pass events with `pass.type.name=="Corner"`; **offsides = standalone `Offside` events PLUS Pass events with `pass.outcome.name=="Pass Offside"`** — documents the original version checked only the standalone type and undercounted offsides ~8.5x (team-match mean 0.203 vs. ESPN's 2026 mean of 1.725), caught via an implausible effect size during a hierarchical-model backtest and fixed 2026-07-14. The `.R` port mirrors this exactly, writing to distinctly-suffixed `_r.csv` files so it never overwrites the Python output.

### `datasets/build_unified_team_match_panel.py` (+ `.R` port)
Pools the ESPN and StatsBomb panels into `unified_team_match_panel.csv`, tagging `data_source`; same measurement-heterogeneity caveat as the output file above. The `.R` version's cross-source check explicitly adds offsides to its comparison table, with an inline comment noting its earlier absence from this check is what let the 8.5x bug go unnoticed for a full backtest cycle.

### `datasets/explore_statsbomb_data.R`
Interactive/exploratory script — summarizes the panels, spot-checks Portugal's WC appearances and Ronaldo's match log, generates the two PNG plots in `data/processed/`.

### Other `datasets/` files
- **`master_question_dataset.csv`** (944 lines) — the project's primary ML-ready flat file.
- **`questions_flat.csv`** (550 lines) — a simpler, earlier/parallel per-question flattening (referenced in `MATCH_LOG.md` as "the complete settled-question ledger").
- **`archive/master_question_dataset_backup_20260707_103028.csv`** (731 lines) — dated backup matching the 730-row/66-match/107-column snapshot cited in the dictionary.
- **`__pycache__/build_master_dataset.cpython-312.pyc`** — compiled bytecode cache, not a data artifact.

---

## 5. `matches/` — per-match research and settlement records

20 match subdirectories, one per game priced for the JTC platform (play.sportspredict.com), each covering the ~15 probabilistic questions for that fixture. Two generations of file-naming convention are present: an older "01-06" convention (most folders) and a newer, richer numbered-extract convention used on the most recent quarterfinal/semifinal matches (Argentina_vs_Switzerland, Norway_vs_England, Spain_vs_Belgium, "France Vs Spain (Jul.14.26)" reaching 00-14, and "England Vs Argentina (Jul.15.26)" reaching 01-24 — the most complete folder in the repo). `mex_ecu_2026-06-30` is the earliest match and also uses the 01-06 convention but with its own README and an extra `07_instrument_trace.json`.

### Standard match-folder schema
The pipeline: raw data fetch → market fetch → model derivation → rule application → final estimate → post-match settlement.

- **`01_espn_data.json`** — curated ESPN summary for both teams: per-team prior-match arrays (opponent, home/away, result, possession%, shots, SOT, corners, cards, offsides, fouls), computed averages, free-text notes on key players/form. Hand-curated distillation of the raw `espn_*.json` dumps.
- **`02_smarkets_markets.json`** — curated Smarkets market read: event_id, total_markets, an Elo-vs-market cross-check narrative, a `key_prices` block (FTR, BTTS, O/U goals, HT result, clean-sheet, SOT/corner/card O/U, team-to-score-first, goal-timing brackets), and `player_market_data` (anytime scorer/SOT O/U/multi-goal/hat-trick, flagged liquid true/false).
- **`03_model_derivations.json`** — the quantitative layer: `lambda_fits` (Poisson lambdas fit to market-implied O/U lines), `derived_probs`, an `elo` block, `rule_checks` (which named project rules fired and why), `espn_insight` free-text feeding the rule checks.
- **`04_rules_applied.json`** — match_context summary plus a `per_question` array: tier (DIRECT/PLAYER_LIQUID/PLAYER_ILLIQUID/TEAM_MODEL/TIMING_WITH_MARKET etc.), applied rules, resulting estimate, reasoning note — the file showing actual pricing logic per question.
- **`05_estimates.json`** — the final pre-submission estimate set: match metadata, FTR, lambda_goals, rule-fire flags, a `questions` array. Ends with `post_match_results: null` until settlement (some folders never get this filled in).
- **`06_post_match_results.json`** — the settlement file: actual_score, match_rbp_total, beat/below-crowd counts, per-question results (estimate, crowd, outcome, rbp, beat_crowd, diagnostic note), and a `key_lessons` array later mined for cross-match postmortems.
- **`bash_log.txt`** — narrated session transcript of the pricing session (ESPN fetch, Smarkets fetch, model fits, rule discussion). Present in most but not all folders.
- **Raw support files** (most 01-06 folders): `espn_<team>_<id>.json` / `espn_match_summary_raw.json` (full unedited ESPN responses), `smarkets_markets_raw.json`, `smarkets_quotes_processed.json` (+ raw/`_retry2` variants), `player_quotes.json`.

### Newer "00-14" convention (Argentina_vs_Switzerland, Norway_vs_England, Spain_vs_Belgium, "France Vs Spain")
`00_sportspredict_markets_raw.json` (the 15 open JTC questions fetched directly from the platform API, replacing the implicit question list previously embedded in `05_estimates.json`), `01_team_and_player_logs.json`/`01_match_and_markets.json` (expanded logs, sometimes reusing base rates from a sibling folder), `02_smarkets_quotes_raw.json` (curation now happens inline in `03_model_derivations.json`), `PRICING_METHODOLOGY.md` (narrative writeup with a full per-question estimate/market/gap/resolution table — new addition not in the older convention). The "France Vs Spain" folder goes furthest: numbered external-data extracts 02–14 (Elo, StatsBomb, Transfermarkt, rest-days/travel, venue altitude, head-to-head history, odds history, Smarkets, ESPN form, Monte Carlo simulation results, ML predictions, an ML-vs-market-vs-submitted comparison writeup, the actual settled submission), a `MANIFEST.md` documenting every file's raw source, and an `espn_raw/` subfolder of immutable live ESPN pulls — built under a stated policy that every file here is a duplicate/filtered extract of an existing raw source elsewhere in the repo, never hand-edited.

### Per-match summary table

| Match | Date | Score | Total RBP | Beat-crowd | Notes | Deviations from standard schema |
|---|---|---|---|---|---|---|
| mex_ecu_2026-06-30 | 2026-06-30 (R32) | Mexico 2-0 Ecuador | +154.20 | 11/15 | Campaign's largest single-question win at the time: Ecuador 3+ offsides priced 0.28 vs crowd 0.55 (+49.58 RBP). Has its own README.md and a unique `07_instrument_trace.json` tracing each question through all 5 pricing layers. | Has `07_instrument_trace.json` and `README.md` not seen elsewhere; otherwise 01-06 numbering. |
| Argentina_vs_CapeVerde | 2026-07-03 (R32) | Argentina 3-2 Cape Verde (AET) | -3.41 | 8/15 | Whole match explained by one tail event; worst loss was Julián Álvarez score-or-assist (-29.25), directly informing a later "PERSONAL_ZERO_OVERRIDES_TEAM_CONTEXT" rule. | None — full standard 01-06 set. |
| Australia_vs_Egypt | 2026-07-03 | Australia 1-1 Egypt (Egypt advanced) | +64.74 | 10/15 | Biggest loss (3+ offsides, -43.09) mirrored Colombia_vs_Ghana's same-day offside miss, feeding "OFFSIDE_CROWD_ANCHOR." | Extra files: `irankunda_sot.json`, `smarkets_quotes_retry2.json`. |
| Brazil_vs_Norway | 2026-07-05 | Brazil 1-2 Norway (upset) | +179.26 | 13/15 | Best beat-crowd rate at the time; validated independent per-team Poisson for both-teams-do-X (both teams carded, +59.43). | Missing `04_rules_applied.json` (jumps 03→05). |
| Canada_vs_Morocco | 2026-07-04 | Canada 0-3 Morocco | +58.92 | 12/15 | Biggest loss on record at the time: Canada 4+ SOT (-80.83); same match had two of the best wins (Díaz +44.06, Davies +30.97). | None — full standard 01-06 set. |
| "England Vs Argentina (Jul.15.26)" | 2026-07-15 (SF) | England 1-2 Argentina (Argentina advanced) | +96.05 (official) | 10/15 | Most complete folder in the repo (01-24). Biggest wins from DIRECT-market discipline on far-from-crowd questions: 10+ corners +34.89, 8+ SOT +32.30, Bellingham +28.32, Kane +18.03; penalty deep-research call (hold 0.29) won +11.62. Worst loss card-before-first-goal -28.4 — the exact question flagged lowest-confidence pre-match. | Newest generation: numbered extracts 01-10, per-question analysis 11-20 (player-prop high-stakes deep dives, corners-comparison Skellam backtest, timing/compound walk-forwards, de-shrinkage pressure test), a two-loop reproducibility audit (`21_LOOP1_full_audit_and_map.md`, `22_LOOP2_agent_audit.md`), and settlement `23_post_match_results.json` + `24_post_match_analysis.md`. |
| Colombia_vs_Ghana | 2026-07-03 | Colombia 1-0 Ghana | +46.48 | 11/15 | Biggest loss: 3+ offsides (-36.94); second loss favorite-team-SOT underpricing (-20.33). | None — full standard 01-06 set. |
| "France Vs Spain (Jul.14.26)" | 2026-07-14 (SF) | France 0-2 Spain | +138.32 (official) | 10/13 answered (77%) | Newest/most complete folder (00-14, MANIFEST.md, ML shadow-test, Monte Carlo sim). Spain-advance and Spain 5+ SOT (shadow-tested GLMM) both won big; Mbappé-scores lost (-12.48). Costliest loss: France 4+ SOT at 72%, missed by one shot. | Newest generation: `13_..._comparison.md` (same-day retraction of an offsides ML model resting on the 8.49x StatsBomb bug), `14_actual_submission.json` as settlement file, `espn_raw/` subfolder. |
| France_vs_Morocco | 2026-07-09 | France 2-0 Morocco | +169.17 | 13/14 (92.9%, campaign-best at the time) | One loss on the DIRECT/most-trusted tier (-8.75); one question skipped for lack of precedent. | Missing ESPN files entirely; only 03-06 plus unique `jtc_crowd_snapshot.json`. |
| France_vs_Paraguay | 2026-07-04 | Paraguay 0-1 France | +116.44 | 13/15 | Enciso player-prop call (+10.3) cited as cleanest example of learning from a prior -26.3 RBP loss on the same question type. | None — full standard 01-06 set. |
| Mexico_vs_England | 2026-07-05/06 | Mexico 2-3 England | +23.81 | 8/15 | One root miscalibration (underestimating openness of the match) explains 4 of 5 losses. | Missing `04_rules_applied.json`. |
| Norway_vs_England | 2026-07-11 | Norway 1-2 England | +95.58 | 11/15 | Biggest loss (24+ total shots, -23.83) from over-weighting the uncalibrated model vs. a market-calibrated blend. | Newer "00-14"-style folder + `PRICING_METHODOLOGY.md` + bespoke `nor_eng_qf_point_in_time_elo_replay.py`. No raw ESPN dumps or bash_log.txt. |
| Portugal_vs_Croatia | 2026-07-02 | Portugal 2-1 Croatia | +130.08 | 10/15 | Q11 (Portugal 6+ SOT, +17.49) validated anchoring SOT ceiling to performance vs. organized opposition rather than a blowout game. | No `bash_log.txt`. |
| Portugal_vs_Spain | 2026-07-06 | Portugal 0-1 Spain | +85.41 | 13/15 | Biggest win: Yamal score-or-assist NO (+38.48), a "Cluster-A" pattern validated repeatedly later. Biggest loss: novel event-ordering question (-43.96, thin n=4 base rate). | Missing `02/03/04`; only 01, 05, 06, bash_log.txt, raw Smarkets. |
| Spain_vs_Austria | 2026-07-02 | Spain 3-0 Austria | +77.57 | 11/15 | Biggest loss: Spain 8+ SOT YES (-21.2), a third mixed data point on the "favorite's own SOT threshold" question. | Extra `smarkets_prices_raw.json`, largely 404 errors — a failed/partial fetch kept for the record. |
| Spain_vs_Belgium | 2026-07-10 (QF) | Spain 2-1 Belgium | N/A (crowd/market data deliberately excluded from this pricing pass) | 7/15 correct direction | A bad night, fully autopsied in POSTMORTEM.md — root cause was an asymmetrically-applied regime-coverage check (Spain's SOT prop shaded for opponent quality, Belgium's was not), naming the "SYMMETRIC_REGIME_COVERAGE" fix. | Newer "00-14"-style folder; three markdown docs (`POSTMORTEM.md`, `DATA_SCOPING_MEMO.md`, `PRICING_METHODOLOGY.md`, all read in full — see below). |
| Switzerland_vs_Algeria | 2026-07-02 | Not recorded | Not recorded | Not recorded | `05_estimates.json`'s `post_match_results` is `null` — no settlement was ever captured. | Missing `06_post_match_results.json` and `bash_log.txt`; otherwise 01-05. |
| Switzerland_vs_Colombia | 2026-07-07 (R16) | Not recorded | Not recorded | Not recorded | Estimates are ELO/Poisson-model-only; Smarkets FTR was "not captured pre-match." | Smallest/most minimal folder: only 01-05, no support files, no bash_log.txt. |
| USA_vs_Belgium | 2026-07-07 (R16) | Belgium won (score not in folder) | Not recorded | Not recorded | Pre-match estimates suppressed De Bruyne "scores or assists" to 0.24 (market 0.41). Real result (USA 1-4 Belgium) later confirmed by Spain_vs_Belgium's data-scoping memo. | Minimal folder: 01, 05, bash_log.txt, raw Smarkets, plus unique `espn_r16_actual_summary.json`; no `02/03/04`, no RBP settlement (confirmed missing per Spain_vs_Belgium's memo: "would require crowd-consensus data, out of scope"). |

### Notable per-match documents (read in full)
- **Spain_vs_Belgium/POSTMORTEM.md** — documents the 7/15-correct night. Concludes the Monte Carlo simulation was not the culprit (2/4 split, both near-coin-flip pre-match); real damage came from Belgium 3+ SOT (priced 0.85, missed by 0.85, capped only by a mechanical RULE6 ceiling) and 4+ total cards (priced 0.30, matching Smarkets almost exactly — a shared model/market blind spot on stoppage-time card accumulation). Names `SYMMETRIC_REGIME_COVERAGE`.
- **Spain_vs_Belgium/DATA_SCOPING_MEMO.md** — explicitly scopes crowd/market data OUT before pricing begins. Documents a same-session fix log (corrected point-in-time Elo via a new QF-round replay script, recovered USA-Belgium R16 result, built a new halftime-substitution base-rate panel from 57-59 historical dumps, confirmed referee Michael Oliver's above-average card rate). Flags Lamine Yamal has zero major-tournament StatsBomb history (age 11/15 at 2018/2022 WCs) vs. De Bruyne/Lukaku's 10 rows each.
- **Spain_vs_Belgium/PRICING_METHODOLOGY.md**, **Argentina_vs_Switzerland/PRICING_METHODOLOGY.md**, **Norway_vs_England/PRICING_METHODOLOGY.md** — narrative pricing writeups with per-question tables. The Argentina_vs_Switzerland version is explicitly framed as "the real test" of the SYMMETRIC_REGIME_COVERAGE fix on an almost-identical Elo-gap magnitude — reports the fix held.
- **mex_ecu_2026-06-30/README.md** — folder-level index, biggest-wins/losses tables, the campaign's earliest big lesson (Ecuador offsides mispricing, +49.58 RBP, "definitive proof that per-match ESPN data beats the crowd's generic priors").
- **"France Vs Spain (Jul.14.26)"/MANIFEST.md** — two-part manifest: an initial data-scoping table (each file's raw source, known gaps like zero Transfermarkt player rows for both teams) plus a later "pricing-session artifacts" addendum (2026-07-14) documenting the live pricing/simulation/submission files and the final settled result.
- **"France Vs Spain (Jul.14.26)"/13_ml_vs_market_vs_submitted_comparison.md** — first entry in a "shadow-deployment" log comparing an ML model's predictions against market and the actual submission (not a resubmission). Same-day retracts its offsides prediction after discovering the 8.49x StatsBomb undercounting bug; keeps two SOT predictions (hierarchical GLMM) for the record, both lower than market/submitted, attributed to the model lacking match-context awareness — used to argue RULE2 (market priority over an unvalidated model) remains correct.
- **"England Vs Argentina (Jul.15.26)"/19–20_deshrinkage_pressure_test*.md** — a two-part "de-shrinkage" audit checking every question is submitted at its honest un-shrunk number (not dragged toward 0.5), using the RBP premium math `S·(p_c − p_s)²` and per-book de-vig. Finds the pipeline already collects the full crowd-compression premium on the far-from-crowd questions; total recoverable EV from all possible adjustments ≈ +0.02 RBP.
- **"England Vs Argentina (Jul.15.26)"/21_LOOP1_full_audit_and_map.md + 22_LOOP2_agent_audit.md** — a "loop-engineering" two-pass reproducibility audit: Loop 1 (main assistant) re-runs all eight deterministic scripts and re-extracts every coefficient; Loop 2 (a separately-spawned Opus agent, self-documenting its own model/tools/context and grounded in Anthropic's published agentic-tooling guidance) independently repeats it. Both confirm 8/8 scripts reproduce; the only defect found is a decision-neutral missing `minutes_played > 0` filter in the Messi high-stakes script (n=38 emitted vs n=37 correct). A model for how to verify a pricing pipeline end-to-end.
- **"England Vs Argentina (Jul.15.26)"/24_post_match_analysis.md** — the post-match lessons writeup: the winning engine was DIRECT-market discipline on far-from-crowd questions (the four biggest wins), and the worst loss (card-before-goal, -28.4) was the exact question flagged lowest-confidence — producing the standing rule that a low-confidence flag on a no-market question must trigger a shrink toward the crowd, not just a note.

---

## 6. `ml/` and `model/` — shared infrastructure (family-specific content moved to `topics/`)

**Reorganized 2026-07-15** (see Section 2): the family-specific backtests, results, and
preregistration docs that used to fill these two directories now live in `topics/<slug>/` — SOT,
cards, corners, offsides, first-substitution, player-props, and the match-winner/goals-totals
classical pipeline. What's left here is genuinely cross-topic infrastructure: things every family
depends on, that would have to be duplicated (violating this repo's own no-duplicate-data rule)
to live inside any single topic folder.

### `model/` — 1 file
- **`elo.py`** — point-in-time Elo for every national team from `data/international_results/results.csv`, using the published World Football Elo Ratings formula (`R_new = R_old + K*G*(W-We)`), K from `tournament_kfactor_map.csv` (default K=30 fallback), G the goal-difference multiplier, +100 home advantage when non-neutral. INITIAL_RATING=1500.0 (unvalidated). Outputs `data/processed/elo_match_panel.csv` and `data/processed/elo_current_ratings.csv` — the Elo panel every topic's own-Elo covariate depends on. The other 14 files formerly in `model/` (Poisson goals GLM, Dixon-Coles, ordered logit, and their prediction/backtest/diagnostic scripts) moved to `topics/match-winner-goals-totals/model/` — see Section 2.

### `ml/` — 18 top-level files (track-record-wide diagnostics, not topic-scoped)
- **`build_feature_matrix.py`** — flattens every settled match JSON in `data/external_markets/` (6 documented schema variants, labeled A-G) into **`ml/feature_matrix.csv`** (264 rows). **Documented fix (2026-07-10):** added a `post_match` key fallback, recovering 7 previously-silently-dropped matches.
- **`platt_diagnostic.py`** — hand-implemented Platt-scaling calibration check over 246 settled questions. **Result: b=0.510, 95% CI [0.123,1.287] includes 1.0 — recalibration WORSENS Brier both globally and walk-forward. Conclusion: do not apply Platt recalibration.**
- **`meta_model.py`** — Problem-A meta-model: context-aware logistic regression / shallow HGB blend of our_estimate/crowd_estimate, validated two ways against 3 baselines. Estimates an RBP-per-Brier scale `S≈101.3` (reused in `statsbomb_baserate_test.py`). **Result: both models WORSE than baseline OOS — decision: do NOT deploy.**
- **`rbp_gap_ttest.py`/`.R`** — Welch's t-test on whether deviating from crowd predicts RBP, at question level (non-independent, caveated) and match level (the trusted unit). **Result: match-level -1.68 (p=0.056) — deviating more from crowd associates with LOWER RBP at the correctly-independent unit.**
- **`rbp_linear_regression.py`/`.R`** — OLS of actual RBP on gap/elo_diff/draw_probability/rest_days/squad_value/9 rule-fired dummies, cluster-robust SEs by match. **Result: in-sample R²=0.053 (weak). OOS does NOT beat baseline — in-sample signal without OOS value.**
- **`statsbomb_baserate_test.py`/`.R`** — StatsBomb-derived empirical-Bayes-shrunk base-rate model vs. the actual JTC submission for Portugal vs Croatia, using the `S=101.3` RBP scale. **Result: actual submitted RBP 120.30 vs model-implied 93.01 — the base-rate model would have scored WORSE than the actual submission.**
- **Output JSONs** (`rbp_gap_ttest_results.json`/`_r.json`, `rbp_linear_regression_results.json`/`_r.json`, `statsbomb_baserate_results.json`/`_r.json`, `meta_model_results.json`, `platt_results.json`) — all R/Python pairs checked and agree to rounding precision. (`ronaldo_goals_regression.*` and its results moved to `topics/player-props/` — see Section 2.)

### `ml/backtests/` — 25 files, now shared cross-family infrastructure only
The "design #2" hierarchical-GLMM campaign's family-specific outputs (results CSVs,
family-specific preregistrations, walk-forward scripts) moved to `topics/<slug>/`. What stays:

- **`PREREGISTRATION_cards_corners_offsides_and_combined.md`** — the shared preregistration fusing cards+corners+offsides+combined-threshold into one hypothesis set, results table, and Benjamini-Hochberg FDR correction. Documents the 8.49x StatsBomb offsides-undercounting bug discovery and retraction in full. Linked from `topics/cards/`, `topics/corners/`, `topics/offsides/`, and `topics/combined-threshold/` — not split or duplicated per topic.
- **`PREREGISTRATION_cards_referee_fouls_stage.md`** — the referee-refined cards follow-up (still FAIL). Linked from `topics/cards/`.
- **`PREREGISTRATION_elo_level_refinement.md`** — the own-Elo-level refinement, run jointly for SOT + corners (both PASS, promoted). Linked from `topics/shots-on-target/` and `topics/corners/`.
- **`lib_hierarchical_backtest.R`** — the shared walk-forward backtest engine (`run_family_backtest()`/`summarize_backtest()`) every family's own backtest script sources.
- **`run_all_family_backtests.R`**, **`run_elo_level_refinement.R`** — shared drivers that fit/write multiple families' results at once; each routes its output to the correct `topics/<slug>/` location via an explicit per-family output-directory map (added during the reorg).
- **`apply_to_fra_esp.R`** — the live application step: refits the FDR-surviving models on all prior data and predicts France/Spain SF lambdas, writing into `matches/France Vs Spain (Jul.14.26)/12_ml_predictions.csv`.
- **`combined_threshold_backtest.py`** — the sum-of-two-Poissons composition test script, shared across SOT/corners/offsides' combined-threshold outputs (each of which now lives in its own topic folder).
- **`add_pit_elo_to_unified_panel.py`**, **`build_full_tournament_pit_elo.py`** — joins genuinely point-in-time Elo onto the training panel; every family's own-Elo covariate depends on this.
- **`build_rare_event_panels.py`** / **`rare_event_panel.csv`** — the shared panel spanning first-substitution, VAR mentions, and goal-between-hydration-breaks (linked from `topics/first-substitution/`, `topics/var-review/`, `topics/rare-event-timing/`).
- **`corners_comparison_skellam_backtest.R`** + **`corners_comparison_backtest_results.csv`** / **`_summary.csv`** + **`PREREGISTRATION_corners_comparison.md`** — a new (2026-07-15) preregistered walk-forward backtest of a *comparison/difference* composition ("does team A have more corners than team B"), built for England-Argentina Q9. Distinct from both the per-team corners GLMM (PASS) and the sum/combined-threshold composition (FAIL): it composes the two teams' PIT-refit GLMM lambdas via a Skellam distribution. **Result: PASS** (n=98, Brier 0.2015 vs 0.2442 baseline vs 0.2500, 90% CI clears zero on all four comparisons). The prereg reasons in advance why a *difference* composition can survive where the *sum* one failed (positive within-match correlation shrinks a difference's variance but inflates a sum's).
- **`timing_compound_events_backtest.py`** + **`_results.csv`** / **`_summary.csv`** — walk-forward empirical-base-rate backtest (no GLMM, matching the standing judgment that cards/timing families don't support fitted models) of four England-Argentina questions: goal-in-each-half, stoppage-time goal, both-teams-carded, card-before-first-goal. Strict `date < d` folds. Findings: modest real edge on stoppage-time-goal and card-before-goal; none on goal-in-each-half or both-carded. Also independently flagged a goal-type text-matching gap in `rare_event_panel.csv` (undercounts ~10 goals corpus-wide). The pooled/expanded-corpus extension lives in the match folder (`18_*`).
- **Point-in-time Elo hand-replay scripts** (superseded by `build_full_tournament_pit_elo.py`, kept as cross-checks): `r16_point_in_time_elo_replay.py`, `qf_point_in_time_elo_replay.py`, `arg_sui_qf_point_in_time_elo_replay.py`, `nor_eng_qf_point_in_time_elo_replay.py`, `fra_esp_sf_point_in_time_elo_replay.py` — all share the root cause that `results.csv` records every WC2026 score as NA, so `model/elo.py`'s regular pipeline never processes a WC2026 result.
- **`all_families_summary.csv`** — the joint FDR-adjusted verdict table across all 4 families (5 lines).

### `ml/backtests/live_market_watch/`
Single file: `event_45195225_England_Argentina.json` — a raw Smarkets snapshot, a lightweight cache location for live-market snapshots, distinct from the more extensive per-match `matches/*/` folders.

---

## 7. `papers/`, Tactic AI, `bash_logs/`, and misc root files

### `papers/` — 5 reference academic papers underpinning the pipeline
All cited in `references.bib` and both competition papers.
- **`constantinou_fenton_2012.pdf`** — argues football's 3 outcomes are ordinal, not nominal; shows via 5 benchmark scenarios that most scoring rules used in prior football-forecasting literature fail to respect that ordering while the Ranked Probability Score (RPS) passes all 5. Motivates an open Future Work item on whether the JTC platform's own scoring formula behaves like plain Brier or RPS.
- **`karlis_ntzoufras_2003.pdf`** — bivariate Poisson model (3 latent independent Poisson components) capturing positive goal correlation, improving fit of draw frequency vs. independent-Poisson models. Direct theoretical ancestor of the project's Poisson/Dixon-Coles goal model; cited for the limitation that base bivariate Poisson can only capture positive correlation.
- **`extending_dixon_coles_2307.02139.pdf`** (Michels, Ötting & Karlis 2023) — proves the classic Dixon-Coles tau-correction is a special case of the broader Sarmanov family, extending to any scoreline pair, non-Poisson marginals, and much wider (including strongly negative, as in women's football) correlation ranges. Cited in the flagship paper to justify NOT re-fitting rho further, since the project's own ρ̂=−0.05 is already near the DC correction's achievable maximum.
- **`verification_prob_forecasts_2106.14345.pdf`** (Foulley 2021) — applies Murphy's calibration-refinement decomposition and reliability diagrams to Poisson-based Champions League forecasts; finds Draws structurally hardest to discriminate (Harrell's C≈0.62 vs 0.79-0.82). Supplies the project's own Calibration-section framework; its appendix result is cited as justification for putting Elo difference directly into the Poisson means.
- **`wisdom_crowds_2018wc.pdf`** — WC2018 forecasting-contest study; finds unweighted crowd aggregation competitive with the best individuals/models, and that a 64-match tournament is too short to reliably separate skill from luck. Its minimax result (uniform 1/3-1/3-1/3 is optimal under zero information) formally justifies RULE6 (never submit 0%/100%); its crowd-compression finding underlies the project's central thesis. *(Possible citation-mismatch flag: `references.bib` attributes this to Lichtendahl/Winkler/Bickel, but the actual PDF's byline is Inácio/Izbicki/Lopes/Salasar/Poloniato/Diniz — two related "wisdom of crowds" WC studies may have been conflated.)*

### `Tactic AI (Deep Mind)/` — DeepMind TacticAI reference material
`MANIFEST.md` (acquisition log) and `TACTICAI_RESEARCH_NOTES.md` (49KB technical writeup), plus: `papers/` (5 PDFs — the Nature Communications 2024 article, arXiv preprint, 17-page Supplementary Information, and a `related_precursor_and_followup_work/` subfolder with *Game Plan* 2020, *Graph Imputer* 2022, and a June-2026 RL follow-up "Maximising the Set-Piece Return"); `supplementary/` (the official Zenodo figure-generation notebook, not model/training code); `blog_and_media/` (DeepMind's announcement post + media-coverage notes); `code/` (a single file documenting that DeepMind never publicly released TacticAI's model/training code). TacticAI is a GNN (GATv2 + D2-symmetry) system built with Liverpool FC for corner-kick receiver prediction, shot-probability, and defender-repositioning suggestions, evaluated via a 5-expert case study. The research notes close by explicitly connecting to this project: the StatsBomb 360 freeze-frame data is structurally similar in spirit to TacticAI's player-graph representation but far smaller and without a coaching-evaluation loop — recommended as conceptual/exploratory reference only, consistent with the project's repeated finding (across four other ML attempts) that available sample sizes are too small for a from-scratch model here.

### `bash_logs/` — 37 root-level session-transcript files
Per-match(day) transcripts of actual bash commands, stdout, and (in "match_analysis"-style files) hand-computed calibration outputs and final estimate summaries. Early files (mid-June) are large, literal auto-generated command-log exports spanning multiple matches per session (up to 1.5MB); from ~2026-06-22 onward most switch to a hand-written `match_analysis` format (full Q1-Q10 calibration workup per match, model vs. crowd, ending in a summary table). A few document cross-match research/diagnostic tasks rather than one match's pricing (flagged in the index below). One structured (non-log) file: `2026-06-21_postmatch_stats.json` (box-score stats for 8 matches settled around that date, not a bash transcript). Three files (`bel_irn_2026-06-21`, `nzl_egy_2026-06-22`, `uru_cpv_2026-06-21`) use a distinct lowercase "matchcode_date" naming convention, suggesting a different script/session around the same period. *(Note: distinct from `bot/bash_log_2026-06-27.txt` through `06-28.txt` — a separate, larger per-day series covered in Section 3.)*

Full index (chronological within date group, as listed on disk):

| Filename | Size | Notes |
|---|---|---|
| `2026-06-14_GER-CUR_BRA-MAR_JPN-NED_CIV-ECU_BEL-EGY_SAU-URU_SWE-TUN_bash_log.txt` | 178,781 B | multi-match session |
| `2026-06-18_GHA-PAN_UZB-COL_ENG-CRO_SUI-BIH_CAN-QAT_bash_log.txt` | 1,562,248 B, 541 commands | **largest file in the directory**; multi-match session |
| `2026-06-19_BRA-HAI_TUR-PAR_bash_log.txt` | 591 B | near-empty placeholder/header-only, with an appended NED-SWE session marker |
| `2026-06-19_MEX-KOR_USA-AUS_SCO-MAR_bash_log.txt` | 449,621 B | multi-match session |
| `2026-06-19_MEX-KOR_early_bash_log.txt` | 114,729 B, 78 commands | earlier/separate MEX-KOR session; includes tool setup (uv, mempalace install) |
| `2026-06-20_NED-SWE_bash_log.txt` | 14,941 B | |
| `2026-06-21_postmatch_stats.json` | 5,758 B | structured box-score JSON, not a log (see above) |
| `2026-06-22_ARG-AUT_match_analysis_bash_log.txt` | 7,289 B | full Q1-Q10 calibration workup, ARG vs AUT |
| `2026-06-22_FRA-IRQ_match_analysis_bash_log.txt` | 9,457 B | |
| `2026-06-22_JOR-ALG_match_analysis_bash_log.txt` | 14,990 B | |
| `2026-06-22_NOR-SEN_match_analysis_bash_log.txt` | 13,514 B | |
| `2026-06-22_ml_platt_diagnostic_bash_log.txt` | 8,300 B | ML feature matrix build + Platt-scaling diagnostic (not match-specific) |
| `2026-06-23_COL-CDR_match_analysis_bash_log.txt` | 7,757 B | |
| `2026-06-23_CRO-PAN_match_analysis_bash_log.txt` | 8,022 B | |
| `2026-06-23_ENG-GHA_match_analysis_bash_log.txt` | 4,449 B | |
| `2026-06-23_POR-UZB_match_analysis_bash_log.txt` | 13,446 B | |
| `2026-06-23_data_source_reliability_audit_bash_log.txt` | 4,449 B | cross-match data-source reliability audit (not match-specific) |
| `2026-06-24_BIH-QAT_match_analysis_bash_log.txt` | 8,402 B | |
| `2026-06-24_CZE-MEX_match_analysis_bash_log.txt` | 6,451 B | |
| `2026-06-24_MAR-HAI_match_analysis_bash_log.txt` | 7,024 B | |
| `2026-06-24_RSA-KOR_match_analysis_bash_log.txt` | 8,468 B | |
| `2026-06-24_SCO-BRA_match_analysis_bash_log.txt` | 6,749 B | |
| `2026-06-24_SUI-CAN_match_analysis_bash_log.txt` | 7,345 B | |
| `2026-06-25_GER-ECU_CUR-IVC_bash_log.txt` | 6,389 B | |
| `2026-06-28_RSA-CAN_db_search_bash_log.txt` | 6,056 B | |
| `2026-06-28_RSA-CAN_pricing_bash_log.txt` | 3,668 B | |
| `2026-06-28_RSA-CAN_research_agent_bash_log.txt` | 14,914 B | ESPN/Smarkets API reverse-engineering (drinks-break/keyEvents structure, substitute-goal detection fields, Smarkets `name=` filter bug) |
| `2026-06-29_BRA-JPN_bash_log.txt` | 3,872 B | |
| `2026-06-29_GER-PAR_bash_log.txt` | 2,923 B | |
| `2026-06-30_FRA-SWE_bash_log.txt` | 5,231 B | |
| `2026-06-30_MEX-ECU_bash_log.txt` | 4,672 B | |
| `2026-06-30_NED-MAR_bash_log.txt` | 3,283 B | |
| `2026-06-30_NOR-CIV_bash_log.txt` | 4,088 B | |
| `2026-07-01_ENG-CDR_bash_log.txt` | 3,173 B | **last-dated file in the directory** |
| `bel_irn_2026-06-21_bash_log.txt` | 3,400 B | lowercase/reversed naming convention |
| `nzl_egy_2026-06-22_bash_log.txt` | 4,242 B | lowercase/reversed naming convention |
| `uru_cpv_2026-06-21_bash_log.txt` | 4,543 B | lowercase/reversed naming convention |

### Misc root-level files

- **`system_architecture_diagram.py`** / **`system_architecture_map.pdf`/`.png`** — generates the *operational* pipeline diagram (distinct from `prediction_instrument_map`, which documents the statistical/modeling taxonomy). A 7-column flowchart: Ingestion → Classification → Per-Match Acquisition → Modeling & Rules → Human Review Gate (`predictions_review.csv`, the primary defense against transcription errors like the Kane −44.54 and Brazil −51.97 RBP incidents) → Submit & Settle → Aggregate & Feedback (dashed arrow back to Modeling & Rules). A cross-cutting "Operational Discipline" band lists five governance practices (immutable raw files, full bash_log transcripts, git version control with no destructive rewrites, documented schema-era drift across 6 formats, persistent project memory). Footer states 71 matches/436+ questions/+872 RBP as of generation — an earlier snapshot than the final paper's +3,415 RBP/86-match figure.
- **`prediction_instrument_map.pdf`/`.png`** — companion diagram documenting the STATISTICAL/modeling taxonomy (as opposed to the operational flow above); generating script out of this pass's scope — see `PREDICTION_INSTRUMENT_WRITEUP.md` (Section 1) for the written companion description.
- **`references.bib`** — BibTeX library backing both competition papers. 20 entries: the 5 `papers/` PDFs plus supporting literature (Crowder et al. 2002, Hvattum & Arntzen 2010, Murphy 1973, Snowberg & Wolfers 2010, Platt 1999, Brier 1950, Rue & Salvesen 2000, Gebru et al. 2021, Yates 1982, Budescu & Chen 2015, Skellam 1946, Dimitriadis/Gneiting/Jordan 2021, Peduzzi et al. 1996, Riley et al. 2019, Harvey/Liu/Zhu 2016, Merkle et al. 2017, Mamlouk 2023).
- **`sportspredict_research.Rproj`** — standard RStudio project file, confirming the project is developed as an RStudio project alongside the `.Rmd`-based competition papers.
- **`abirc_patch.json`, `abirc_prob_cup_data.json`, `abirc_prob_cup_data_full.json`** — **not** a competitor's data: "AbirC" is the user's own JTC platform username, scraped from the public leaderboard/profile page via an injected browser-console script. `abirc_prob_cup_data.json` (3.2KB) is an early single-match proof-of-concept capture; `abirc_prob_cup_data_full.json` (172KB) is the full 58-match scrape of the user's own settled history (8 of 58 rendered stale from page-load timing); `abirc_patch.json` (24.7KB) is the corrected replacement for those 8 stale matches from a second scrape pass. Schema: match objects with a `questions` array (qNum, result, questionText, you, crowd, outcome, rbp, performance, predicted). Downstream processed into `data/prob_cup/abirc_forecasts.csv` (570 rows) / `abirc_match_summary.csv` (58 rows) — the campaign's independently-verifiable 58-match/570-question/+1,256.26 RBP track record.
- **`.gitignore`** (34 lines) — excludes secrets (`bot/secrets.json`, `*cookies*.json`, `.env`), large regeneratable third-party bulk downloads (raw Transfermarkt dir, raw odds CSVs, the full StatsBomb open-data mirror), OS/editor/tool cruft, and knitr/LaTeX build byproducts — with an explicit comment that `*.tex` is deliberately NOT globally ignored since `FRA_MAR_QF_pricing_paper.tex` is a committed deliverable, not build output.
- **`FRA_MAR_Full_Case_Study.Rmd`/`.pdf`** (2026-07-09) — the most complete single-match case study: France-Morocco QF, the first match with zero crowd/market anchor at pricing time. Documents the full "why not ML" rejection experiment (learned blends lose to trusting crowd alone by −148 to −1,760 RBP-equivalent across two validation schemes), three research errors made and corrected in view (a platform field misread as live crowd consensus — actually a binary open/settled flag; the stale/frozen Elo bug; an overstated "worst category" claim later found to conflate two question types), and the final settlement (France 2-0, +169.17 RBP, 13/14 beat crowd — a campaign best at the time).
- **`FRA_MAR_QF_pricing_paper.tex`/`.pdf`** — a separate standalone LaTeX companion paper on the same match, organized around the StatsBomb event-level panel as its central methodological contribution rather than the Rmd's case-study framing; shares the same underlying pricing decisions/coefficients. An alternate draft/framing, not a sequential revision.
- **`JTC_WC2026_Research_Paper.Rmd`/`.pdf`** (2026-07-11, read in full) — the flagship competition paper: full pipeline documentation, 13-source lit review, the central crowd-compression finding (r=0.83, n=772), 15 named situational rules, the "Rejection of Learned Blending Models" section (4 independent tests all rejecting ML), and the full track record (86 matches, 935 questions, ≈+3,415 RBP, 70% beat-crowd, rank top 5.6%→top 1.1% of ~3,900 participants). Documents the two fixed pipeline bugs (stale Elo; the neutral-flag home-advantage mismatch) and reports both the best (+59.43, Brazil-Norway both-teams-carded) and worst (−80.83, Canada-Morocco 4+ SOT) single-question results without smoothing over the losses.
- **`Paper_draft2.pdf`** (untracked in git) — confirmed byte-identical in extracted text to `JTC_WC2026_Research_Paper.pdf` (both 204,430 bytes); a duplicate/renamed copy, likely a competition-submission-portal upload artifact, not a distinct draft.

---

## 8. `writeups/` — professional match write-ups

A "sports betting shop"-quality documentation layer, structured as its own internally-linked mini-repo inside the main repo. Originally built as a standalone git repo (`jtc-match-writeups`, still pushed separately to a private GitHub repo) and later merged in here so every reference resolves to the actual script/model/data file it describes instead of linking out to a different repo. Every path reference in this section was individually verified to resolve (a 100-link check via a Python script comparing percent-encoded/decoded paths against `os.path.exists`).

- **`README.md`** — index only: explains why this directory lives inside the main repo, the structure (README/CONTRIBUTING/docs/decisions/matches/CHANGELOG), a Matches table (currently one row: France vs Spain, 2026-07-14, +138.32 RBP, 10W-3L), and a Standing Decisions table linking the three ADRs below.
- **`CONTRIBUTING.md`** — the standard every future match write-up must follow (structure/tone/sourcing rules), so new matches stay consistent with the France-Spain template.
- **`docs/DOCUMENTATION_STANDARDS.md`** — the researched industry-practice memo this whole format is built from: Google SRE blameless-postmortem structure, Architecture Decision Records (ADR/MADR: Status/Context/Decision/Consequences), docs-as-code/README-driven development, Keep a Changelog conventions, professional sports-betting Closing-Line-Value grading discipline ("grade every bet, every time"), and trading-desk pre-trade/post-trade analysis structure — cited as the direct precedent for using git-as-documentation here.
- **`decisions/0001-market-priority-over-domain-model.md`** — ADR: a liquid market takes priority over a domain-only model when both exist (RULE1/RULE2's formal writeup).
- **`decisions/0002-shadow-deploy-before-live-submission.md`** — ADR: a newly backtested model must be shadow-tested against real outcomes before it can override a submission (the discipline that kept the FRA-ESP GLMM's SOT predictions as a shadow comparison, not a live resubmission — see Section 6's `apply_to_fra_esp.R`).
- **`decisions/0003-never-blindly-drop-a-question.md`** — ADR: dropping a question requires a specific evidentiary reason, not just "no market exists."
- **`matches/2026-07-14-france-vs-spain/README.md`** — the full formal write-up for the France vs Spain semifinal: what data was pulled, which scripts/models were used, what was actually submitted, what the market/crowd said, and how each question settled, with real clickable links back into `matches/France Vs Spain (Jul.14.26)/` and `ml/backtests/`.
- **`CHANGELOG.md`** — additions to this write-up repo itself (not match outcomes, which live in the match files) — Keep a Changelog format.

---
