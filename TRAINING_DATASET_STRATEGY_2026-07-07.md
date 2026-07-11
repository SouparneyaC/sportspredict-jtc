# Training-Dataset Strategy: Enhancing the Model for the Knockout Stage

**Date:** 2026-07-07
**Author:** Souparneya Chakrabarti (research conducted via Claude Code)
**Status:** Research + verification complete. Build not yet started (awaiting go-ahead on StatsBomb pull).
**Trigger:** Stuck at rank ~50 on the JTC Probability Cup global leaderboard entering the
knockout stage (Round of 16 concluded 2026-07-07; one match per day from here). Need a
genuine model enhancement, and the binding constraint is training data, not model class.

Related prior docs: [`ML_EXPERIMENTS_NOTEBOOK.md`](ML_EXPERIMENTS_NOTEBOOK.md),
[`META_MODEL_LAB_NOTES.md`](META_MODEL_LAB_NOTES.md),
[`data/alt_data_sources_research.md`](data/alt_data_sources_research.md),
[`data/granular_data_sources_research.md`](data/granular_data_sources_research.md).

---

## 1. Strategic diagnosis: why rank ~50 is a wall

Being frozen at rank 50 with one match a day is the **efficient-market wall**, not bad luck.
The academic consensus (Kaunitz et al. 2017, "Beating the bookies with their own numbers")
is that you generally cannot out-forecast a liquid market head-on; durable edge comes from
finding **specific mispriced questions**, not from being globally "better." At this rank,
everyone left is calibrated on the obvious markets (match winner, over/under). The remaining
edge lives in the questions the crowd prices lazily — and our own loss log
(`ML_EXPERIMENTS_NOTEBOOK.md` §"CRITICAL LOSSES") already names them: **fouls, offsides,
cards, second-half shots-on-target, player props.** Those are exactly the markets where
team/player/referee base rates beat intuition — and exactly where our current data is thinnest.

## 2. We have TWO dataset problems, not one

- **Meta-model / calibration dataset** = `datasets/master_question_dataset.csv`
  (one row per *our prediction*, 943 rows / 85 matches). Answers "given my estimate and the
  crowd's, what's the true probability?" The 2026-07-05 meta-model diagnostic
  (`META_MODEL_LAB_NOTES.md`) proved this is too small to learn a blend — 71 independent
  matches is the real n (every question in a match shares the same context columns), and
  both logreg and HGB lost to crowd-alone out-of-sample. This dataset can never grow faster
  than one match/day. **Not the thing to fix.**
- **Domain training dataset** = the thing we DON'T have. One row per historical
  *team-match* (and *player-match*), with the base rates that actually price a fresh
  question like "will Iran be caught offside 2+ times?" Right now these granular markets
  are priced by hand. **This is the fix.**

## 3. What a strong football-ML dataset looks like (web research)

Serious ML football systems train on a fundamentally different *shape* of data than we have:

| Dimension | Benchmark ML datasets | Our current data |
|---|---|---|
| Unit of row | one historical **match** (or player-match) | one of **our predictions** |
| Row count | Hubáček/Berrar: **216,743 matches**, 52 leagues, since 2000 | 85 matches / 943 rows |
| Core features | Elo/pi-/Berrar ratings, rolling form, rest, home/away, **closing odds** | Elo ✓, squad value ✓, rest ✓; no odds-as-feature, no player level |
| Granular stats | per-match shots, SOT, fouls, corners, cards, offsides, possession, **referee** | ESPN panel exists but only 171 team-match rows (this WC only) |
| Player-level | StatsBomb event data (every shot/foul/pass) | none — why player props hurt us |
| Target | actual match outcome (RPS-scored) | our Brier vs crowd |

Winning systems are **gradient-boosted trees (XGBoost/CatBoost) on 200k+ historical matches**;
the literature is consistent that **feature/rating engineering matters more than model class**,
and that **deep learning did not beat well-featured GBDTs** (ACM 2024) — echoing our own
"7 Systematic" meeting note that simple beats complex. Peduzzi's events-per-variable rule +
our match-level clustering caps the honest feature budget at **~8–12 features**, not 103.

### Sources
- Open International Soccer Database — https://link.springer.com/article/10.1007/s10994-018-5726-0
- Hubáček et al., GBDT on relational data (2017 Soccer Prediction Challenge winner) — https://link.springer.com/article/10.1007/s10994-018-5704-6
- Evaluating soccer match prediction models: deep learning vs GBDT feature optimization (ACM 2024) — https://dl.acm.org/doi/10.1007/s10994-024-06608-w
- Kaunitz et al., "Beating the bookies with their own numbers" (2017) — https://arxiv.org/abs/1710.02824
- football-data.co.uk column notes (shots/corners/fouls/cards/referee + odds) — https://www.football-data.co.uk/notes.txt
- StatsBomb open-data — https://github.com/statsbomb/open-data
- worldfootballR (FBref/Transfermarkt/Understat wrapper for R) — https://jaseziv.github.io/worldfootballR/

## 4. Source evaluation — verified, not assumed (2026-07-07)

### FBref via worldfootballR — installed and probed
- Installed `worldfootballR` 0.6.2 (R 4.5.0). Tidyverse present.
- `load_match_comp_results(comp_name="FIFA World Cup")`: **964 matches, 1930–2022**, cached
  (fast, no scraping), includes **Referee** and **xG** columns. Cache frozen at 2023-08-28.
- **Detailed team stats probe FAILED (the pivotal finding):**
  `fb_advanced_match_stats(stat_type="misc")` on a WC2022 match returned
  **"Stats data not available"** — 0 rows. This is the rule, not the exception, for
  international matches on FBref: results/xG/referee are clean, but granular per-team stats
  (fouls/SOT/corners/cards) are **patchy and inconsistent** — i.e. exactly the
  **heterogeneity we want to avoid.** → FBref is the WRONG source for the granular markets.
- **Keep worldfootballR for one thing:** the cached results give a clean **referee-tendency
  table** (cards/fouls/pens per ref) back to 1930 across all comps — free, fast, and the
  highest-ROI feature for our worst market category (cards/fouls/penalties).

### StatsBomb open data — the homogeneous source we actually want
Verified directly against `data/competitions.json`: **89 competition-seasons.** International
coverage relevant to us:
- **Men's World Cup: 2022, 2018** (full detail), + 1990, 1986, 1974, 1970, 1962, 1958
- **Women's World Cup: 2023, 2019**
- **Euro 2024 & 2020, Copa América 2024, AFCON 2023**

Why it satisfies the "reliable + not heterogeneous" requirement and FBref doesn't:

| Property | StatsBomb open data | FBref internationals |
|---|---|---|
| Collection method | one methodology, every match | aggregated, varying |
| Granular coverage | every match, identical fields | patchy ("not available" on WC2022) |
| Level | event-level → derive **team AND player** | team-match only, when present |
| Fouls/SOT/corners/cards/offsides | every event tagged consistently | inconsistent |
| Cost | free (JSON on GitHub, no scraping) | free |

Because it's one methodology, a team's foul rate at WC2018 is measured the same way as at
WC2022 → pooling across tournaments is statistically legitimate, unlike stitching
ESPN + FBref + Smarkets.

### Caveats (honest)
1. StatsBomb does **NOT** include WC2026 (not open). It is for **training base rates from
   history**, which we then apply to price 2026 questions — the correct use anyway.
2. Pre-2018 men's WCs (1958–1990) are **less granular** (historical special collections).
   The reliable, fully-homogeneous core is **2018 + 2022 men's, 2019 + 2023 women's,
   Euro 2020/2024, Copa 2024, AFCON 2023** ≈ **350–400 matches** with complete identical schema.
3. National-team identity is stable for team base rates; rosters change between tournaments,
   so player features carry per-player-career, team features are the more stable signal.

## 5. Proposed build (not yet started)

1. Download StatsBomb open-data for the ~10 international tournaments above (direct JSON pull).
2. Aggregate events → `data/processed/statsbomb_team_match_panel.csv` and
   `statsbomb_player_match_panel.csv`, **matching existing ESPN panel column names**
   (`build_espn_panel.py`) so they drop into the current feature pipeline.
3. Build `data/processed/referee_tendencies.csv` from worldfootballR cached results.
4. Train a **GBDT per market-type** (fouls / cards / SOT / corners / offsides / player-props)
   on real base rates instead of the hand-tuned RULE1–15 framework. Validate walk-forward
   by date + GroupKFold-by-match (same harness as the existing meta-model diagnostic).

## 6. What NOT to do (settled by our own prior results + the literature)
- No deep learning (needs 10–100× the data; "simple beats complex").
- No wide feature sets (ESPN box-score columns are post-match → leakage if used as raw
  pre-match features; only valid as rolling pre-match averages, which the pipeline already does).
- No isotonic regression (needs ~1000+ points; use penalized spline / Beta calibration instead).
- Never a random row-level CV split (leaks match context; always GroupKFold-by-match + walk-forward).

## 7. Decision point
Awaiting go-ahead to execute step 1 (pull StatsBomb men's WC 2018 + 2022, build the
team-match panel as a proof of concept) before committing to the full multi-tournament pull.

---

## 8. StatsBomb deep-dive: quality, point-in-time, span, columns (verified 2026-07-07)

Hands-on inspection of the actual open-data files (downloaded from
`raw.githubusercontent.com/statsbomb/open-data`), not documentation. Every claim below was
checked against real JSON.

### 8.1 File structure (three tiers + extras)
- `data/competitions.json` — master index (80 competition-seasons). Fields per row:
  `competition_id, season_id, competition_name, season_name, competition_gender,
  competition_youth, competition_international, country_name, match_updated, match_available`.
- `data/matches/{competition_id}/{season_id}.json` — one file per tournament, list of matches.
- `data/events/{match_id}.json` — ~3,400 events per match (~2.8 MB each).
- `data/lineups/{match_id}.json` — player rosters per match.
- `data/three-sixty/{match_id}.json` — freeze-frame tactical data (subset of matches; not needed for our markets).

### 8.2 Point-in-time / timestamps — PRESENT and PRECISE (this was the key question)
Two independent temporal layers, both verified:
- **Match level:** `match_date` (e.g. `2022-12-01`) + `kick_off` (`15:00:00.000`) + `last_updated`.
  → exact chronological ordering for **walk-forward validation** (no leakage across the date boundary).
- **Event level:** every event carries `index` (strict within-match order), `period` (half),
  `timestamp` (`HH:MM:SS.mmm`, millisecond), `minute`, `second`, and `possession` (possession-sequence id).
  → we can compute genuine **point-in-time / "as-of-minute-X" features** and reconstruct match
  state at any instant. Confirmed on a mid-match event: `period=1, timestamp=00:03:27.448,
  minute=3, second=27`. This is the strongest form of point-in-time support — better than the
  match-summary sources (ESPN/FBref) which only give end-of-match totals.

### 8.3 Match-level columns (verified on WC2022, comp 43 / season 106)
`away_score, home_score, home_team{...}, away_team{...}, competition{...},
competition_stage{name} (Group Stage / Round of 16 / …), kick_off, match_date, match_id,
match_status, match_status_360, match_week, referee{name}, season{...}, stadium{name},
metadata{data_version, xy_fidelity_version, shot_fidelity_version}, last_updated`.
Note **`referee`** is present at match level → feeds the referee-tendencies table directly
(no separate worldfootballR pull strictly needed, though worldfootballR extends referee history further back).

### 8.4 Event types + granular-market derivations (all verified on a real match)
~3,400 events/match, ~30 distinct types (Pass, Ball Receipt, Carry, Pressure, Shot,
Foul Committed, Foul Won, Duel, Interception, Block, Clearance, Goal Keeper, Substitution,
Offside, …). The JTC granular markets map cleanly:

| JTC market | Derivation from StatsBomb events | Verified |
|---|---|---|
| Fouls | `type = "Foul Committed"` (count per team/player) | ✓ 31 in sample match |
| Shots / Shots on Target | `type = "Shot"`; SOT = `shot.outcome ∈ {Goal, Saved, Saved To Post}`; every shot has `shot.statsbomb_xg` | ✓ real xG present |
| Yellow/Red cards | `foul_committed.card` **plus** `bad_behaviour.card` (cards are NOT a top-level type) | ✓ 4 yellows derived |
| Corners | `pass.type.name = "Corner"` (per team) | ✓ Canada 6 / Morocco 2 |
| Offsides | `type = "Offside"` + offside pass outcomes | ✓ present as own type |
| Possession / passes / SOT splits by half | filter events by `period` before aggregating | ✓ via period field |

Because these are derived from **tagged events with the same methodology in every match**, the
resulting per-team / per-half / per-player counts are internally consistent — the homogeneity
we wanted and could not get from FBref.

### 8.5 Player level
`lineups/{match_id}.json`: per player → `player_id, player_name, player_nickname,
jersey_number, country, positions[], cards[]`. Combined with the player tag on every event,
building a **player-match panel** (shots, SOT, fouls committed/won, cards, minutes) is a
straight groupby. Directly attacks the player-prop markets that hurt us most.

### 8.6 Homogeneity across eras — CONFIRMED schema-identical
Compared a WC1970 match against WC2022: **identical schema** — same `data_version 1.1.0`,
same `timestamp`/`location` fields, `statsbomb_xg` on **100% of shots (41/41) even in 1970**.
The variable across eras is **coverage (match count), not schema** → pooling across tournaments
is schema-safe. Data quality spot-check: `location` present on **99% of events** (3359/3388).

### 8.7 Span & coverage — VERIFIED match counts
Old men's WCs are **token coverage** and NOT usable for base rates:

| Men's World Cup | Matches available |
|---|---|
| 2022 | **64 (complete)** |
| 2018 | **64 (complete)** |
| 1990 | 1 |
| 1986 | 0 |
| 1974 | 6 |
| 1970 | 6 |
| 1962 | 1 |
| 1958 | 2 |

**Usable men's international core (2018+), all complete tournaments, identical schema:**

| Tournament | Matches | Date span |
|---|---|---|
| World Cup 2018 | 64 | 2018-06 |
| World Cup 2022 | 64 | 2022-11 → 12 |
| Euro 2020 | 51 | 2021-06 → 07 |
| Euro 2024 | 51 | 2024-06 → 07 |
| AFCON 2023 | 52 | 2024-01-ish |
| Copa América 2024 | 32 | 2024-06 → 07 |
| **TOTAL** | **314 matches** | **2018 → 2024** |

→ ≈ **628 team-match rows** and ≈ **6,900 player-match rows** at fully consistent schema.
Women's (separate, homogeneous, but different base rates — keep in its own panel): Women's WC
2019 & 2023, Women's Euro 2022 & 2025.
Data freshness: `match_updated` = **2026-05** — fresher than the worldfootballR cache (frozen 2023-08).

### 8.8 Honest limitations (so expectations stay calibrated)
1. **No WC2026** in open data — this is a *training* corpus for base rates, applied to 2026. Correct use.
2. **Tournament football only** — no friendlies/qualifiers. Actually well-matched to WC2026's
   high-stakes context, but it means fewer matches per national team than a league dataset.
3. **Scale is modest**: 314 matches ≈ 628 team-match rows is a big upgrade over the 171-row
   ESPN panel and is *homogeneous*, but it is nowhere near the 200k-match domestic-league scale
   the benchmark papers use. Realistic expectation: **good, well-calibrated priors for the
   granular markets** (fouls/cards/SOT/corners/offsides), not a magic global edge.
4. **Roster turnover** 2018→2024 weakens player-level carryover; team-level base rates are the
   more stable signal (some 48 WC2026 teams have several tournaments here, others few/none —
   coverage per team is uneven and must be reported per team before trusting a team's base rate).
5. Old WCs (1958–1990) excluded entirely on coverage grounds despite matching schema.

### 8.9 Verdict
StatsBomb open data **passes** the reliability + homogeneity + point-in-time + player/team-level
test that FBref internationals failed. It is the correct source for a domain training set for
the granular markets. The binding constraint becomes **sample size per team (314 tournament
matches total)**, not schema quality or leakage risk — and that constraint is honestly
disclosed, not hidden. Proof-of-concept build (WC2018 + WC2022 → team-match panel) remains the
recommended first step.

### 8.10 Reproducibility (exact calls used)
```
competitions:  https://raw.githubusercontent.com/statsbomb/open-data/master/data/competitions.json
WC2022 matches: .../data/matches/43/106.json      WC2018: .../43/3.json
Euro2024: .../55/282.json   Euro2020: .../55/43.json
AFCON2023: .../1267/107.json   Copa2024: .../223/282.json
events:  .../data/events/{match_id}.json    lineups: .../data/lineups/{match_id}.json
```
Sample match inspected: `3857276` (Canada 1–2 Morocco, WC2022, ref Raphael Claus).
