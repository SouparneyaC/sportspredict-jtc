# France vs Spain — Semifinal, 2026-07-14 (closes 23:00 UTC)

match_id: `de7b7b6f-f3a8-4948-af5e-f0f4565728d0`

**Policy: every file in this folder is a duplicate/filtered extract of an existing raw source elsewhere in the repo. Raw source files are never modified — only opened for reading.** If a raw source is updated later, re-run the extraction to refresh these copies; don't hand-edit them.

## Files and their sources

| File | Source (raw, untouched) | Notes |
|---|---|---|
| `01_match_and_markets.json` | `bot/data/matches.json` + `bot/data/markets_raw.jsonl` | The match record + all 15 open JTC questions, fetched via v1 API 2026-07-13. Not yet priced. |
| `02_elo_current_ratings.json` | `data/processed/elo_current_ratings.csv` | France + Spain rows only. **Known frozen at pre-tournament values — does NOT reflect real WC2026 results.** Needs a point-in-time replay before use in modeling, same as R16/QF matches. |
| `02_elo_match_history.csv` | `data/processed/elo_match_panel.csv` | All 1,686 historical matches (any tournament) involving France or Spain. |
| `03_statsbomb_team_panel.csv` | `data/processed/statsbomb_team_match_panel.csv` | 22 rows — France/Spain team-level stats from StatsBomb's WC2018/2022 coverage. |
| `03_statsbomb_player_panel.csv` | `data/processed/statsbomb_player_match_panel.csv` | 524 rows — individual player stats, same matches/scope. |
| `04_transfermarkt_national_teams.csv` | `data/external/transfermarkt/extracted/national_teams.csv` | Squad size, avg age, market value, FIFA ranking for France (id 3377) and Spain (id 3375). |
| `05_rest_days_features.csv` | `data/external/travel/rest_days_features.csv` | 3,360 rows — every historical match (either team, home or away) with computed rest days. |
| `05_team_venue_distances.csv` | `data/external/travel/team_venue_distances.csv` | Distance from France/Spain to each WC2026 venue city. |
| `06_wc2026_venue_altitude_reference.csv` | `data/external/altitude/wc2026_venue_altitude.csv` | Full 16-venue reference, duplicated as-is. **Venue for this specific semifinal not yet confirmed** — keep as lookup until known. |
| `07_h2h_france_vs_spain_only.csv` | `data/international_results/results.csv` | 38 rows — true head-to-head, France vs Spain only, all-time. |
| `07_all_matches_either_team.csv` | `data/international_results/results.csv` | 1,686 rows — broader team-form context (either team vs anyone). |
| `08_odds_history.csv` | `data/external/odds/international_fixture_odds.csv` | 55 rows — historical market odds involving either team. No WC2026 rows yet (known gap, historical prior only). |

## Known gaps found while building this folder

- **Transfermarkt player-level roster (`national_team_players.csv` / `national_team_player_valuations.csv`) returned zero rows for both France and Spain**, whether joined on `current_national_team_id` (3377/3375) or on `country_of_citizenship`. This is a new gap beyond the previously-documented 5 missing WC2026 teams (CIV, CUR, CDR, HAI, CPV) — France and Spain, two of the biggest squads, are simply absent from this particular extract. Not included in this folder; flag if individual player market-value data is needed for Yamal/Mbappé-type questions — will need a different source.
- No ESPN pre-match data (rosters, last-5-games team/player stats) or Smarkets live quotes are in this folder yet — those require a live fetch/research pass, not a duplication of existing local data, and are the next step.
- JTC crowd consensus is not fetchable pre-close via any known endpoint (structural platform limit, not a gap in this folder specifically).

Built 2026-07-13 by filtering the sources above; extraction script not persisted (one-off, ad hoc).

## Pricing-session artifacts (added 2026-07-14, pre-close)

| File | Produced by | Notes |
|---|---|---|
| `03_model_derivations.json` | pricing session | Match context: corrected point-in-time Elo, market FTR, fitted sim params, key form facts. |
| `04_rules_applied.json` | pricing session | Per-question tier + rules + reasoning for all 15 estimates. |
| `05_estimates.json` | pricing session | FINAL pre-submission estimates with confidence tags + RULE14 consistency checks. |
| `09_smarkets_markets_raw.json` | `bot/fetch_fra_esp_smarkets.py` | Full 175-market list, Smarkets event 45192700. |
| `09_smarkets_quotes_raw.json` / `09_smarkets_quotes_processed.json` | `bot/fetch_fra_esp_smarkets.py` | Bid/offer/mid for 29 relevant markets (fetched ~05:30Z 2026-07-14). No offsides/VAR/Spain-team-SOT/substitution markets exist for this fixture. |
| `10_espn_form.json` | `bot/compile_fra_esp_espn_form.py` | All 6 games each team: team stats, Mbappé/Yamal per-game lines, sub timing. Extraction verified against the known FRA-MAR settlement. |
| `10_espn_form_supplement.json` | inline session script | Goal/card minutes, per-team first-sub minutes, delay (hydration-break/VAR) windows, QF squad jersey maps. |
| `11_simulation_results.json` | `bot/simulate_fra_esp_sf.py` | Design-#1 joint 200k-draw simulation, market-calibrated; all goal-structure question probabilities + market fit checks. |
| `espn_raw/` | live ESPN API fetch | 12 game summaries + SF fixture (event 760514). Raw, immutable. |
| `14_actual_submission.json` | captured live, settled 2026-07-14 after Full Time | **The real, final submission — now SETTLED.** Final: Spain 2-0 France (Oyarzabal pen 22', Porro 58'). Record on the 13 answered questions: **9 wins, 4 losses (69%)**. Of the 3 flagged divergences from the market-anchored recommendation: Q7 (Spain advance) and Q10 (Spain SOT, the shadow-tested GLMM number) both WON, clearly beating the market; Q8 (Mbappé, personal-form conviction) LOST, consistent with the pre-match RULE17 caution — genuinely mixed evidence, not a clean verdict. Costliest single loss: Q13 (France 4+ SOT, our highest-conviction number at 72%, missed by exactly 1 shot on target). Full per-question outcomes and box score in the file. |
| `espn_raw/espn_FRA_ESP_sf_760514_FINAL.json` | live ESPN API fetch, post-match | Complete final match record: box score, full key-events timeline, player stats. Raw, immutable. |

Corrected point-in-time Elo (`ml/backtests/fra_esp_sf_point_in_time_elo_replay.py`): France 2225.13, Spain 2261.57 — recorded in `02_elo_current_ratings.json`. Venue confirmed: AT&T Stadium, Arlington TX (170m, altitude non-factor).
