# Loop 1 — full re-trace, re-run, and map of the England vs Argentina pricing (question-fetch → final)

This is the **first pass** of a two-loop verification ("loop engineering"). It re-traces every step
of the England vs Argentina SF pricing from the moment the 15 questions were fetched to the final
submission set, maps every file/script/data source/calculation, **re-runs every deterministic script
in this session**, and cross-checks each reproduced number against what the documents claim. A second
loop (a separately-spawned agent with its own tooling) repeats this independently — see
`22_LOOP2_agent_audit.md`.

Verification date: 2026-07-15. Environment: Python 3.13.5 (numpy 2.4.6, scipy 1.15.3, pandas 2.2.3),
R 4.5.0 (lme4 2.0.1), macOS.

## 0. Headline verdict

**8 of 8 deterministic scripts re-ran and reproduced their documented headline numbers**, one with a
single minor code-vs-doc discrepancy that does not change any decision (Messi high-stakes n=38 not 37
— see §6). All shared upstream coefficients (PIT Elo, Poisson/ordered-logit/NB, crowd-compression)
were re-extracted from source and cross-checked. The 3 live-API fetch scripts were **not** re-run
(non-deterministic network calls) — their saved outputs were verified for internal consistency
instead. No number that flows into a final submission changed under re-run.

## 1. Verification method

- **Deterministic scripts** (read local data, no network): re-executed in this session; stdout
  headline numbers diffed against the source `.md`.
- **Live-API scripts** (ESPN / Smarkets fetches): flagged and *not* re-run — re-running would issue
  fresh network calls whose results could differ from what was captured at pricing time. Their JSON
  outputs were checked for internal consistency and row counts instead.
- **Shared coefficients**: re-read from their canonical `coefs/*.json` and panel files, and Elo
  cross-checked against `data/processed/wc2026_pit_elo_panel.csv` directly.
- Network-call classification was done by grepping each script for `requests`/`urllib`/`http`/`api.`
  before deciding what was safe to re-run.

## 2. Full file inventory (match folder)

Data-sourcing layer (files 01–10), built first, mirroring the France vs Spain template:

| File | What it is | Source | Verified |
|---|---|---|---|
| `01_match_and_markets.json` | The 15 live JTC questions + market_ids | v1 API fetch 2026-07-15 | matches `bot/data/match_questions/ENG_vs_ARG.json` |
| `02_elo_current_ratings.json` | Stale + corrected PIT Elo (ENG 2172.28 / ARG 2253.31) | `wc2026_pit_elo_panel.csv` lookup | cross-checked vs panel (§5) |
| `02_elo_match_history.csv` | 2,149 historical ENG/ARG matches | `elo_match_panel.csv` | row-count consistent |
| `03_statsbomb_{team,player}_panel.csv` | WC2018/22 StatsBomb slices | `statsbomb_*_match_panel.csv` | filter-only extract |
| `04_transfermarkt_national_teams.csv` | 2 team rows (ENG 3299 / ARG 3437) | `national_teams.csv` | player-roster gap noted in MANIFEST |
| `05_rest_days_features.csv`, `05_team_venue_distances.csv` | rest/travel features | `data/external/travel/*` | upstream-stale flag carried |
| `06_wc2026_venue_altitude_reference.csv` | 16-venue reference | `data/external/altitude/*` | copied as-is |
| `07_all_matches_either_team.csv`, `07_h2h_*.csv` | full history + 15-match H2H | `results.csv` + `espn_match_panel.csv` | scores cross-checked 3 ways |
| `08_odds_history.csv` | 41 historical odds rows | `international_fixture_odds.csv` | no WC2026 rows (known) |
| `09_smarkets_partial_live_snapshot.json` | corners/cards-only auto-pull | `live_market_watch/event_45195225` | 11 markets, partial |
| `10_smarkets_quotes_{raw,processed}.json` | full live quotes, 21 markets | `fetch_eng_arg_smarkets.py` | LIVE fetch (not re-run) |

Analysis layer (files 11–20):

| File | Question(s) | Type | Re-run result |
|---|---|---|---|
| `11_player_prop_backtest_messi_alvarez.{md,py,json}` | Q1, Q4 (first pass) | walk-forward EB | **reproduces** (preds 0.7143→0.6571 Álvarez, 0.6364→0.798 Messi) |
| `12_corners_comparison_backtest_summary.md` + live csv | Q9 | Skellam/GLMM | **reproduces** (see R re-run §4) |
| `13_timing_and_compound_events_backtest_summary.md` | Q5,Q7,Q8,Q10 | base-rate WF | **reproduces** (§4) |
| `14_messi_high_stakes_deep_dive.{md,py,csv,json}` + fetch | Q4 | high-stakes club career | reproduces w/ **one discrepancy** (§6) |
| `15_alvarez_high_stakes_deep_dive.{md,py,csv,json}` + fetch | Q1 | high-stakes club career | **reproduces exactly** |
| `16_direct_market_questions_final_pricing.md` | Q2,3,11,12,13,14,15 | DIRECT market | numbers = raw mids (§7) |
| `17_combined_sot_and_corners_comparison_final.md` | Q6, Q9 | derived/reconciled | Q6 math re-derived (§7) |
| `18_timing_cards_expanded_corpus_final.{md,py,csv}` | Q5,Q7,Q8,Q10 | pooled WF | **reproduces** (panel 135; Q5 −0.0099, Q7 +0.0325, Q8 +0.0170, Q10 −0.0010) |
| `19_deshrinkage_pressure_test.md` | Q12,13,14,3 (+Q9) | bias check | inline calc, reproduced this session |
| `20_deshrinkage_pressure_test_remaining.md` | other 10 | bias check | inline calc, reproduced this session |
| `21_LOOP1_full_audit_and_map.md` | — | **this file** | — |

Cross-repo artifacts created for this match:

| Path | Role | Re-run |
|---|---|---|
| `bot/fetch_eng_arg_smarkets.py` | live Smarkets pull (21 markets) | LIVE — not re-run |
| `ml/backtests/corners_comparison_skellam_backtest.R` + results/summary csv + `PREREGISTRATION_corners_comparison.md` | Q9 GLMM+Skellam backtest | **reproduces exactly** |
| `ml/backtests/timing_compound_events_backtest.py` + results/summary csv | Q5/7/8/10 WF | **reproduces exactly** |
| `topics/cards/card_timing_panel.py` + `.csv` | new per-team card-timing panel | **reproduces** (100 matches, both-carded 55/100) |
| `matches/…/18_statsbomb_expanded_panel.py`, `18_pooled_walk_forward_backtest.py` | Euro/CopaAm/AFCON expansion | **reproduces** (135 matches; 96/37/9 split) |

## 3. Data-lineage map (raw → price)

```
RAW (immutable)
  data/external/statsbomb/open-data/        ── Messi/Álvarez club careers (14,15); Euro/CopaAm/AFCON panels (18); WC18/22 (03)
  data/processed/espn_raw_events/*.json     ── WC2026 goals/cards/SOT timing (11,13,14,15, card_timing_panel)
  data/international_results/results.csv     ── historical Elo/H2H (02,07)
  live ESPN (site.api.espn.com)             ── Messi/Álvarez 2021-2026 recency (14,15 fetch) [LIVE]
  live Smarkets (api.smarkets.com/v3)       ── 21 market quotes (10) [LIVE]
        │
PROCESSED (shared, PIT-safe)
  wc2026_pit_elo_panel.csv                  ── PIT Elo (build_full_tournament_pit_elo.py)  ENG 2172.28 / ARG 2253.31
  unified_team_match_panel_with_pit_elo.csv ── corners GLMM training (corners_comparison R)
  coefs/{poisson,ordered_logit,nb}_*.json   ── classical pipeline coefficients
  rare_event_panel.csv, card_timing_panel.csv ── timing/cards base rates
        │
MATCH ANALYSIS (files 11–20)  ──►  FINAL 15 PRICES (§7)  ──►  de-shrink audit (19,20)  ──►  this audit (21)
```

## 4. Script re-run verification table

| Script | Documented headline | Re-run headline | Match? |
|---|---|---|---|
| `15_alvarez_high_stakes_deep_dive.py` | HS 0.580 vs reg 0.579, z=0.009 p=0.993; club n=192 rate 0.583; MC 0.588 / Atl 0.571 | identical | ✅ exact |
| `11_player_prop_backtest_messi_alvarez.py` | Álvarez preds 0.714/0.595/0.653/0.696/0.619/0.657; Messi 0.636/0.697/0.740/0.773/0.798/0.818 | identical | ✅ exact |
| `18_statsbomb_expanded_panel.py` | 135 matches; group 96 / knockout-core 37 / SF-Final 9 | identical | ✅ exact |
| `18_pooled_walk_forward_backtest.py` | Q5 −0.0099, Q7 +0.0325, Q8 +0.0170, Q10 −0.0010; live Q5 0.519 Q7 0.311 | identical | ✅ exact |
| `topics/cards/card_timing_panel.py` | 100 matches, 11 zero-card, both-carded 55/100=0.550 | identical | ✅ exact |
| `ml/backtests/timing_compound_events_backtest.py` | Q5 −0.0005 / Q7 +0.0120 / Q8 −0.0071 / Q10 +0.0164; live 0.580/0.360/0.550/0.350 | identical | ✅ exact |
| `ml/backtests/corners_comparison_skellam_backtest.R` | n=98, Brier 0.2015/0.2442/0.2500, 4× raw_pass=TRUE, λ 4.191/4.556, P=0.4805 | identical | ✅ exact |
| `14_messi_high_stakes_deep_dive.py` | (doc) HS n=37 rate 0.378 z=−2.48 p=0.013 | HS n=38 rate 0.368 z=−2.632 p=0.0085 | ⚠️ §6 |

## 5. Coefficient & regression registry (every fitted number, with source)

| Quantity | Value | Source file | n |
|---|---|---|---|
| PIT Elo — England (entering SF) | 2172.2772 | `wc2026_pit_elo_panel.csv` (last row: 2026-07-11 vs Norway `elo_post`) | 6 WC2026 matches replayed |
| PIT Elo — Argentina (entering SF) | 2253.3138 | same (2026-07-11 vs Switzerland `elo_post`) | 6 WC2026 matches replayed |
| Elo diff (ARG − ENG) | +81.04 | derived | — |
| Poisson goals: intercept / home_adv / elo_diff | 0.10408 / 0.23022 / 0.0018099 | `poisson_goals_coefs.json` | 49,400 matches |
| Ordered logit: b_elo / b_home / c1 / c2 | 0.005199 / 0.37713 / −0.77018 / 0.55487 | `ordered_logit_coefs.json` | 49,400 |
| NB dispersion: alpha / rho_nb | 0.09922 / −0.05 | `nb_dispersion_coefs.json` | 98,800 obs |
| (all above have SEs) | see `model_standard_errors.json` | — | — |
| Corners GLMM (live refit) λ England / Argentina | 4.191 / 4.556 | `corners_comparison_skellam_backtest.R` | 456 pre-2026-07-15 rows |
| Q9 P(ARG corners > ENG) | 0.4805 | same (Skellam of the two λ) | — |
| Corners comparison backtest | Brier 0.2015 vs 0.2442; mean diff +0.0427, t=2.385, p=0.019, CI90 [0.0134,0.0714] | `corners_comparison_backtest_summary.csv` | 98 matches |
| Messi high-stakes vs regular (as re-run) | 0.368 (n=38) vs 0.588 (n=490); z=−2.632, p=0.0085 | `14_..._deep_dive.py` | 528 |
| Álvarez high-stakes vs regular | 0.580 (n=50) vs 0.579 (n=145); z=0.009, p=0.993 | `15_..._deep_dive.py` | 195 |
| Crowd-compression regression | p_c = 0.5042 + 0.6087·(p_s−0.5), r=0.829 | `PAPER_REVISION_NOTES.md` | 772 |
| Q6 combined-SOT: λ_ENG / λ_ARG (market-derived) / P(≥8) | 3.870 / 3.485 / 0.454 | `17_..._final.md` (re-derived inline) | — |
| Measured within-match SOT correlation | −0.269 (full) / −0.317 (WC2026) | `17_..._final.md` | 228 / 100 |
| RBP scale S (used in premium calc) | ≈90 (range 78–100) | `STRATEGIC_MARGIN_PUSH_RESEARCH.md` | — |

## 6. The one discrepancy found (documented, decision-neutral)

`14_messi_high_stakes_deep_dive.py`, re-run this session, produces **high-stakes n=38, rate 0.368,
z=−2.632, p=0.0085**. The write-up (`14_...md` §3) reports **n=37, rate 0.378, p=0.013**. The
one-row gap is the **Copa America 2024 group-stage match vs Peru**, in which Messi had `minutes=0`
(a real, documented injury absence). The doc's narrative states this row was excluded (dropping the
Copa America denominator 6→5); the script's *high-stakes tag aggregation* actually still counts it,
so the high-stakes bucket is 38, not 37.

Impact assessment:
- **Direction and significance unchanged** — in fact *strengthened*: p falls from 0.013 to 0.0085,
  still comfortably significant, still a ~22pp high-stakes-vs-regular gap.
- **No price changes.** The final Q4 (Messi) number was hand-set to **0.50** during the RULE17/rank
  discussion — deliberately *not* the script's blended output — so this feeds nothing downstream.
- Classified as a **documentation-accuracy defect** (the prose over-claims a data exclusion the code
  doesn't perform on that path), not a modelling or pricing error. Flagged here for correction;
  left un-edited so Loop 2 sees the same state Loop 1 did.

## 7. Final 15-question pricing (as it stands after all loops to date)

| Q | Question | Price | Tier / method | Key input(s) |
|---|---|---|---|---|
| 1 | Álvarez 1+ SOT | 0.58 | PROP, n-weighted pool | club career n=192 rate 0.583; HS null (§5) |
| 2 | England advance to final | 0.55 | DIRECT | To_qualify mid 0.545; RULE14 pass |
| 3 | Penalty awarded | 0.29 | DIRECT | Penalty Yes mid 0.292 |
| 4 | Messi scores | 0.50 | PROP + RULE17 caution | HS rate ~0.43 n-weighted, hand-set (§6, rank discussion) |
| 5 | Goal in each half | 0.52 | BASE | pooled rate 0.519, no edge |
| 6 | 8+ combined SOT | 0.45 | DERIVED from mkt SOT lines | λ 3.870+3.485→P(≥8)=0.454 |
| 7 | Stoppage-time goal | 0.31 | BASE, validated edge | pooled rate 0.311 |
| 8 | Both teams carded | 0.55 | BASE, market-anchored | rate 0.550 |
| 9 | ARG more corners than ENG | 0.44 | GLMM/Skellam ⊕ market | model 0.4805 blended toward market-implied 0.34 |
| 10 | Card before first goal | 0.35 | BASE, marginal edge | rate 0.350 |
| 11 | Kane scores | 0.36 | DIRECT | Anytime mid 0.360 (tightest book) |
| 12 | 10+ combined corners | 0.25 | DIRECT | O/U9.5 Over mid 0.249 |
| 13 | England lead HT | 0.27 | DIRECT | HT England mid 0.274 |
| 14 | Argentina 2+ goals | 0.30 | DIRECT | ARG O/U1.5 Over mid 0.299 |
| 15 | Bellingham score/assist | 0.30 | DIRECT | S/A mid 0.302 |

De-shrink audit (files 19–20): every far-from-0.5 number confirmed un-shrunk; total recoverable EV
from all possible adjustments ≈ +0.02 RBP (the Q1 0.58→0.59 rounding). Nothing else on the table.

## 8. Loop-1 verdict

The pipeline is reproducible and internally consistent. Eight of eight deterministic scripts
regenerate their headline numbers; all shared coefficients trace to a source file and the Elo values
cross-check against the canonical panel to the fourth decimal. One documentation-accuracy discrepancy
(Messi n=38 vs 37) was found and is decision-neutral. The live-fetch scripts were correctly not
re-run and their outputs are internally consistent. Nothing feeding a final price changed. Loop 2 (an
independent agent) now repeats this with its own tooling to catch anything a same-author re-trace
might be blind to.
