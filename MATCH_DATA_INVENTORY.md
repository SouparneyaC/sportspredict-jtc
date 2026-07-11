# Match Data Inventory — JTC WC2026 Campaign

**Date:** 2026-07-03  
**Scope:** All 71 settled match research files across the campaign  
**Storage locations:**
- `data/external_markets/*.json` — primary per-match research files (71 files)
- `matches/*/` — new structured format introduced with MEX-ECU (4 directories; all have a counterpart JSON above)

---

## Summary Statistics

| Metric | Count |
|---|---|
| Total match files | 71 |
| Settled (post-match outcomes recorded) | 71 |
| Group Stage (GD1–GD3, Jun 11–25) | 59 |
| Round of 32 (Jun 28–Jul 2) | 12 |
| Matches with ESPN GD1/player data | 54 |
| Matches with Smarkets market data | 54 |
| Matches with model output (Elo/Poisson/lambda) | 31 |
| Matches with estimates/submission data | 71 |
| Matches with named rules applied | 37 |
| Matches with crowd estimate captured | 10 |
| Matches with player-level profiles | 19 |
| Matches in new structured format (`matches/`) | 4 |

**Note on "settled":** Two files (fra_swe_2026-06-30.json, mex_ecu_2026-06-30.json) do not contain post-match data in the external_markets JSON because their post-match results were recorded in the `matches/` directory format instead. Both matches are resolved (France 3–0 Sweden; Mexico 2–0 Ecuador).

---

## Schema Era Definitions

The file schema evolved across the campaign as the research process matured. Four main eras:

| Era | Period (approx.) | Characteristics |
|---|---|---|
| **Era 1 / 1a** | Jun 11–13 | Minimal structure: sources + derived estimates + post_match. No ESPN, no Smarkets structured data. |
| **Era 1b** | Jun 14–22 | Added ESPN event IDs, Smarkets event IDs, crowd formula in some files. Still flat question structure. |
| **Era 2a** | Jun 19–22 | Added structured model outputs (Elo, Poisson lambdas), rules_applied blocks, player-level data. |
| **Era 2b** | Jun 23–24 | Full analysis_date schema with player_profiles, edge_ranking, referee data. |
| **Era 3** | Jun 25–Jul 2 | Canonical schema: context_flags, wc2026_espn_stats, smarkets_markets, questions block, knockout_context. |
| **New format** | Jun 30+ | Separate numbered files per layer: 01_espn_data, 02_smarkets_markets, 03_model_derivations, 04_rules_applied, 05_estimates, 06_post_match_results, 07_instrument_trace. |

---

## Per-Match Inventory

Columns:
- **Stage:** GS = Group Stage Day 1–2, GS3 = Group Stage Day 3 (final matchday), R32 = Round of 32
- **Era:** Schema era of the research file
- **ESPN:** Individual team player stats (shots, fouls, offsides) from ESPN GD1 data
- **Smarkets:** Live market prices collected from Smarkets exchange
- **Model:** Elo ratings / Poisson lambda derivations / model outputs recorded
- **Est.:** Submission estimates (pre-match research figures) present
- **Rules:** Named rules (RULE1–15) explicitly documented as applied
- **Crowd:** Crowd consensus estimates captured
- **Player:** Player-level profiles or player prop derivations present
- **New fmt:** Match also has a structured `matches/` directory with separated layers

| # | Match | Date | Stage | Era | ESPN | Smarkets | Model | Est. | Rules | Crowd | Player | New fmt |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | KOR vs CZE | 2026-06-11 | GS | 1 | — | — | — | Y | — | — | — | — |
| 2 | CAN vs BIH | 2026-06-12 | GS | 1 | — | — | — | Y | — | — | — | — |
| 3 | BRA-MAR | 2026-06-13 | GS | 1 | — | Y | — | Y | — | — | — | — |
| 4 | Qatar vs Switzerland | 2026-06-13 | GS | 1 | — | Y | — | Y | — | — | — | — |
| 5 | USA vs Paraguay | 2026-06-13 | GS | 1 | — | Y | — | Y | — | — | — | — |
| 6 | CIV-ECU | 2026-06-14 | GS | 1b | Y | Y | — | Y | — | — | — | — |
| 7 | GER-CUR | 2026-06-14 | GS | 1b | — | Y | — | Y | — | — | — | — |
| 8 | JPN-NED | 2026-06-14 | GS | 1b | — | Y | — | Y | — | — | — | — |
| 9 | SWE-TUN | 2026-06-14 | GS | 1b | Y | Y | — | Y | — | — | — | — |
| 10 | BEL-EGY | 2026-06-15 | GS | 1b | Y | Y | — | Y | — | — | — | — |
| 11 | SAU-URU | 2026-06-15 | GS | 1b | Y | Y | — | Y | — | — | — | — |
| 12 | ENG-CRO | 2026-06-17 | GS | 1b | Y | Y | — | Y | — | Y | — | — |
| 13 | GHA-PAN | 2026-06-17 | GS | 1b | Y | Y | — | Y | — | Y | — | — |
| 14 | CAN-QAT | 2026-06-18 | GS | 1 | Y | Y | — | Y | Y | — | — | — |
| 15 | SUI-BIH | 2026-06-18 | GS | 1 | Y | Y | — | Y | — | — | — | — |
| 16 | UZB-COL | 2026-06-18 | GS | 1b | Y | Y | — | Y | — | — | — | — |
| 17 | MEX-KOR | 2026-06-19 | GS | 1 | Y | Y | — | Y | Y | — | — | — |
| 18 | SCO-MAR | 2026-06-19 | GS | 2a | Y | Y | Y | Y | Y | — | — | — |
| 19 | USA-AUS | 2026-06-19 | GS | 2a | Y | Y | — | Y | Y | — | — | — |
| 20 | BRA-HAI | 2026-06-20 | GS | 2a | — | Y | Y | Y | Y | — | — | — |
| 21 | GER-CIV | 2026-06-20 | GS | 2a | — | Y | Y | Y | Y | — | — | — |
| 22 | NED-SWE | 2026-06-20 | GS | 2a | — | Y | Y | Y | Y | — | — | — |
| 23 | TUR-PAR | 2026-06-20 | GS | 2a | — | Y | Y | Y | Y | — | — | — |
| 24 | BEL-IRN | 2026-06-21 | GS | 2a | Y | Y | Y | Y | Y | — | — | — |
| 25 | ECU-CUR | 2026-06-21 | GS | 2a | — | Y | Y | Y | Y | — | Y | — |
| 26 | ESP-KSA | 2026-06-21 | GS | 2a | — | Y | Y | Y | Y | — | — | — |
| 27 | JPN-TUN | 2026-06-21 | GS | 2a | — | Y | Y | Y | Y | — | — | — |
| 28 | URU-CPV | 2026-06-21 | GS | 2a | Y | Y | Y | Y | Y | Y | Y | — |
| 29 | ARG-AUT | 2026-06-22 | GS | 1b | Y | Y | Y | Y | Y | — | — | — |
| 30 | FRA-IRQ | 2026-06-22 | GS | 1b | Y | Y | Y | Y | Y | Y | — | — |
| 31 | JOR-ALG | 2026-06-22 | GS | 1b | Y | — | Y | Y | Y | Y | Y | — |
| 32 | NOR-SEN | 2026-06-22 | GS | 1b | Y | — | Y | Y | Y | Y | Y | — |
| 33 | NZL-EGY | 2026-06-22 | GS | 2a | Y | Y | Y | Y | Y | Y | Y | — |
| 34 | COL-CDR | 2026-06-23 | GS | 2b | Y | — | Y | Y | Y | — | Y | — |
| 35 | CRO-PAN | 2026-06-23 | GS | 2b | Y | — | Y | Y | Y | — | Y | — |
| 36 | ENG-GHA | 2026-06-23 | GS | 2b | Y | — | Y | Y | Y | — | Y | — |
| 37 | POR-UZB | 2026-06-23 | GS | 1b | Y | — | Y | Y | Y | Y | Y | — |
| 38 | BIH-QAT | 2026-06-24 | GS | 2b | Y | — | Y | Y | Y | — | Y | — |
| 39 | CZE-MEX | 2026-06-24 | GS | 2b | Y | — | Y | Y | Y | Y | Y | — |
| 40 | MAR-HAI | 2026-06-24 | GS | 2b | Y | — | Y | Y | Y | — | Y | — |
| 41 | SCO-BRA | 2026-06-24 | GS | 2b | Y | — | Y | Y | Y | — | Y | — |
| 42 | RSA-KOR | 2026-06-24 | GS | 2b | Y | — | Y | Y | Y | Y | Y | — |
| 43 | SUI-CAN | 2026-06-24 | GS | 2b | Y | — | Y | Y | Y | — | Y | — |
| 44 | CUR-CIV | 2026-06-25 | GS | 3 | Y | Y | Y | Y | — | — | — | — |
| 45 | GER-ECU | 2026-06-25 | GS | 3 | Y | Y | Y | Y | Y | — | — | — |
| 46 | JPN-SWE | 2026-06-25 | GS | 3 | Y | Y | — | Y | — | — | — | — |
| 47 | PAR-AUS | 2026-06-25 | GS | 3 | Y | Y | — | Y | — | — | — | — |
| 48 | TUN-NED | 2026-06-25 | GS | 3 | Y | Y | — | Y | — | — | — | — |
| 49 | TUR-USA | 2026-06-25 | GS | 3 | Y | Y | — | Y | — | — | — | — |
| 50 | CPV-SAU | 2026-06-26 | GS3 | 3 | Y | Y | — | Y | — | — | — | — |
| 51 | EGY-IRN | 2026-06-26 | GS3 | 3 | Y | Y | — | Y | — | — | — | — |
| 52 | NZL-BEL | 2026-06-26 | GS3 | 3 | Y | Y | — | Y | — | — | — | — |
| 53 | URU-ESP | 2026-06-26 | GS3 | 3 | Y | Y | — | Y | — | — | — | — |
| 54 | ALG-AUT | 2026-06-27 | GS3 | 3 | Y | Y | — | Y | — | — | — | — |
| 55 | COL-POR | 2026-06-27 | GS3 | 3 | Y | Y | — | Y | — | — | — | — |
| 56 | CDR-UZB | 2026-06-27 | GS3 | 3 | Y | Y | — | Y | — | — | — | — |
| 57 | CRO-GHA | 2026-06-27 | GS3 | 3 | Y | Y | — | Y | — | — | — | — |
| 58 | JOR-ARG | 2026-06-27 | GS3 | 3 | Y | Y | — | Y | — | — | — | — |
| 59 | PAN-ENG | 2026-06-27 | GS3 | 3 | Y | Y | — | Y | — | — | — | — |
| 60 | RSA-CAN | 2026-06-28 | R32 | 3 | Y | Y | — | Y | — | — | — | — |
| 61 | BRA-JPN | 2026-06-29 | R32 | 3 | Y | Y | — | Y | Y | — | — | — |
| 62 | GER-PAR | 2026-06-29 | R32 | 3 | Y | Y | — | Y | Y | — | — | — |
| 63 | FRA-SWE | 2026-06-30 | R32 | 3 | Y | Y | — | Y | Y | — | Y | — |
| 64 | MEX-ECU | 2026-06-30 | R32 | 3 | Y | Y | Y | Y | Y | — | Y | Y |
| 65 | NED-MAR | 2026-06-30 | R32 | 3 | Y | Y | — | Y | Y | — | — | — |
| 66 | NOR-CIV | 2026-06-30 | R32 | 3 | Y | Y | — | Y | Y | — | — | — |
| 67 | BEL-SEN | 2026-07-01 | R32 | 3 | Y | Y | Y | Y | Y | — | Y | — |
| 68 | ENG-CDR | 2026-07-01 | R32 | 3 | Y | Y | Y | Y | Y | — | Y | — |
| 69 | POR-CRO | 2026-07-02 | R32 | 3† | Y | Y | Y | Y | Y | — | — | Y |
| 70 | ESP-AUT | 2026-07-02 | R32 | 3† | Y | Y | Y | Y | Y | — | — | Y |
| 71 | SUI-ALG | 2026-07-02 | R32 | 3† | Y | Y | Y | Y | Y | — | — | Y |

†POR-CRO, ESP-AUT, SUI-ALG: the `data/external_markets/` JSON is a minimal stub; the full structured research data (ESPN, Smarkets, model, estimates, rules) lives in the `matches/` directory.

---

## Data Layer Coverage by Campaign Phase

| Phase | Matches | ESPN | Smarkets | Model | Rules | Crowd | Player |
|---|---|---|---|---|---|---|---|
| Era 1 early (Jun 11–14) | 9 | 3/9 | 5/9 | 0/9 | 0/9 | 0/9 | 0/9 |
| Era 1b / 2a (Jun 15–22) | 24 | 17/24 | 17/24 | 12/24 | 13/24 | 8/24 | 7/24 |
| Era 2b / 3 Group (Jun 23–27) | 26 | 26/26 | 12/26 | 14/26 | 14/26 | 2/26 | 12/26 |
| R32 (Jun 28–Jul 2) | 12 | 12/12 | 12/12 | 5/12 | 8/12 | 0/12 | 3/12 |
| **Total** | **71** | **54/71** | **54/71** | **31/71** | **37/71** | **10/71** | **19/71** |

---

## Key Observations

### What improved over time
- **ESPN data** went from absent in the first three matches (Era 1, Jun 11–13) to present in 100% of R32 matches — the biggest single improvement in the research process. The largest individual wins in the campaign (MEX-ECU Q12 +49.58 RBP; ENG-CDR Q11 +27.51 RBP) both trace directly to ESPN GD1 behavioural data.
- **Smarkets pricing** became consistent from Era 1b onward. The R32 phase has 12/12 Smarkets coverage.
- **Model outputs** (Elo/Poisson lambdas) were first formally documented in Era 2a (Jun 19–20) and are now present in all new-format matches.
- **Named rules** (RULE1–15) began appearing in CAN-QAT (Jun 18, Era 1) and reached consistent documentation in Era 2a. Coverage in R32 is 8/12.

### What is structurally missing or thin
- **Crowd estimates** are only captured in 10/71 files (14%). The crowd consensus is platform-revealed post-resolution and was not systematically back-recorded in the early era files. The crowd-bias regression (Section 5 of the paper) uses the master dataset's `crowd_estimate` column, which has better coverage than the raw JSON files suggest, as the build script also pulls crowd data from the JTC API records.
- **Model derivations** are absent in 40/71 files, primarily early-era matches where the pipeline was run informally and outputs were not saved to the JSON. The ordered logit and Poisson models were run for all matches; the outputs simply weren't persisted in structured form.
- **Player profiles** thin out in the late group-stage Era 3 files (Jun 25–27). These matches were high-volume (up to 6 matches/day on final group-stage matchdays) and the research process prioritised estimates and Smarkets coverage over detailed player documentation under time pressure.

### The new-format transition
The `matches/` directory structure (introduced with MEX-ECU on Jun 30) separates research data into seven numbered layers: ESPN data, Smarkets markets, model derivations, rules applied, estimates, post-match results, and instrument trace. This makes the data audit trail explicit and avoids the schema heterogeneity problem that requires special handling in `build_master_dataset.py`. The three July 2 matches (POR-CRO, ESP-AUT, SUI-ALG) adopted this format in full; their `data/external_markets/` counterparts are minimal stubs used for backward compatibility with existing build scripts.

---

## What This Means for the Paper

The paper (Section 3.1) now reads: *"derived empirically from 61 settled matches and 436+ individually graded questions."*

The correct figure is **71 settled matches** across 53 calendar days (Jun 11–Jul 2). The 436-question count remains accurate for the master CSV, which covers Jun 11–25 only; the additional questions from the 12 R32 matches are not yet merged.

The claim in Section 3.1 should be updated to:

> *"derived empirically from 71 settled matches spanning the complete group stage and the opening round of the knockout phase, encompassing 436+ individually graded questions."*
