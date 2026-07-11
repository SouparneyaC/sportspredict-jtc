"""
build_unified_team_match_panel.py
-----------------------------------
Pools the WC2026 team-match panel (ESPN box scores, our own data) with the
WC2018 + WC2022 team-match panel (StatsBomb event-derived counts) into a
single flat CSV, one row per team per match, tagged by season and source.

READ-ONLY against:
  data/processed/espn_match_panel.csv
  data/processed/statsbomb_team_match_panel.csv
Writes only:
  data/processed/unified_team_match_panel.csv

IMPORTANT CAVEAT — measurement heterogeneity, not just schema alignment:
ESPN's per-match stats are a vendor box-score aggregation; StatsBomb's are
derived directly from tagged, timestamped events. These are NOT guaranteed to
count the same thing the same way (this project already hit exactly this
problem once with FBref internationals — see TRAINING_DATASET_STRATEGY doc
Section 4 — "not available"/inconsistent stats were the reason FBref was
rejected in favor of StatsBomb for the historical side). The `data_source`
column exists specifically so nothing downstream silently pools across
sources without knowing it crossed that boundary. A same-team cross-source
rate comparison is printed at the end of this script as a lightweight
plausibility check (not a proof of equivalence — no WC2026 match exists in
both sources to directly cross-validate against).

Column alignment:
  Present in both, aligned name: goals, opponent_goals, result, total_shots,
    shots_on_target, blocked_shots, fouls_committed, yellow_cards, red_cards,
    corners, offsides, passes, pass_pct, clearances, interceptions
  StatsBomb-only (null for ESPN/2026 rows): xg_total, fouls_won,
    passes_completed, referee_name, competition_stage
  ESPN-only (null for StatsBomb/2018+2022 rows): possession_pct, saves,
    effective_tackles, venue_city

Usage: python3 datasets/build_unified_team_match_panel.py
"""

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "datasets"))
from build_master_dataset import CODE_TO_NAME  # reuse existing canonical map, don't duplicate it

ESPN_PANEL = ROOT / "data" / "processed" / "espn_match_panel.csv"
SB_PANEL = ROOT / "data" / "processed" / "statsbomb_team_match_panel.csv"
OUT = ROOT / "data" / "processed" / "unified_team_match_panel.csv"

NAME_TO_CODE = {v: k for k, v in CODE_TO_NAME.items()}

COLUMNS = [
    "season_year", "data_source", "match_id", "match_date", "competition_stage",
    "team_code", "team_name", "opponent_code", "opponent_name", "is_home",
    "goals", "opponent_goals", "result",
    "total_shots", "shots_on_target", "blocked_shots", "xg_total",
    "fouls_committed", "fouls_won", "yellow_cards", "red_cards",
    "corners", "offsides", "passes", "passes_completed", "pass_pct",
    "clearances", "interceptions", "possession_pct", "saves", "effective_tackles",
    "venue", "venue_city", "referee_name",
]


def none_if_blank(v):
    return v if v not in (None, "") else None


def load_espn_rows():
    rows = []
    with open(ESPN_PANEL) as f:
        for r in csv.DictReader(f):
            slug_codes = r["match_slug"].split("-")
            opp_code = slug_codes[1] if slug_codes[0] == r["team_code"] else slug_codes[0]
            goals, opp_goals = int(r["goals"]), int(r["opponent_goals"])
            result = "W" if goals > opp_goals else ("D" if goals == opp_goals else "L")
            pass_pct = float(r["pass_pct"]) * 100 if r["pass_pct"] else None  # ESPN stores as 0-1 fraction
            rows.append({
                "season_year": 2026, "data_source": "espn_boxscore",
                "match_id": r["event_id"], "match_date": r["date"], "competition_stage": None,
                "team_code": r["team_code"], "team_name": CODE_TO_NAME.get(r["team_code"], r["team_code"]),
                "opponent_code": opp_code, "opponent_name": CODE_TO_NAME.get(opp_code, opp_code),
                "is_home": r["home_away"] == "home",
                "goals": goals, "opponent_goals": opp_goals, "result": result,
                "total_shots": r["total_shots"], "shots_on_target": r["shots_on_target"],
                "blocked_shots": r["blocked_shots"], "xg_total": None,
                "fouls_committed": r["fouls"], "fouls_won": None,
                "yellow_cards": r["yellow_cards"], "red_cards": r["red_cards"],
                "corners": r["corners"], "offsides": r["offsides"],
                "passes": r["passes"], "passes_completed": None, "pass_pct": pass_pct,
                "clearances": r["clearances"], "interceptions": r["interceptions"],
                "possession_pct": r["possession_pct"], "saves": r["saves"],
                "effective_tackles": r["effective_tackles"],
                "venue": r["venue"], "venue_city": r["venue_city"], "referee_name": None,
            })
    return rows


def load_statsbomb_rows():
    rows = []
    with open(SB_PANEL) as f:
        for r in csv.DictReader(f):
            year = int(r["season_name"])
            rows.append({
                "season_year": year, "data_source": "statsbomb_event_data",
                "match_id": r["match_id"], "match_date": r["match_date"],
                "competition_stage": r["competition_stage"],
                "team_code": NAME_TO_CODE.get(r["team_name"]), "team_name": r["team_name"],
                "opponent_code": NAME_TO_CODE.get(r["opponent_name"]), "opponent_name": r["opponent_name"],
                "is_home": r["is_home"],
                "goals": r["goals"], "opponent_goals": r["opponent_goals"], "result": r["result"],
                "total_shots": r["total_shots"], "shots_on_target": r["shots_on_target"],
                "blocked_shots": r["blocked_shots"], "xg_total": r["xg_total"],
                "fouls_committed": r["fouls_committed"], "fouls_won": r["fouls_won"],
                "yellow_cards": r["yellow_cards"], "red_cards": r["red_cards"],
                "corners": r["corners"], "offsides": r["offsides"],
                "passes": r["passes"], "passes_completed": r["passes_completed"], "pass_pct": r["pass_pct"],
                "clearances": r["clearances"], "interceptions": r["interceptions"],
                "possession_pct": None, "saves": None, "effective_tackles": None,
                "venue": r["stadium_name"], "venue_city": None, "referee_name": r["referee_name"],
            })
    return rows


def cross_source_plausibility_check(rows):
    """For teams appearing under BOTH data sources (different tournaments,
    since no WC2026 match exists in the StatsBomb set), compare per-match
    rates as a rough plausibility check -- NOT proof the sources measure
    identically, just a flag if something is wildly off scale."""
    by_team_source = {}
    for r in rows:
        key = (r["team_name"], r["data_source"])
        by_team_source.setdefault(key, []).append(r)

    teams_in_both = sorted({t for (t, s) in by_team_source if s == "espn_boxscore"}
                            & {t for (t, s) in by_team_source if s == "statsbomb_event_data"})

    print(f"\n{len(teams_in_both)} teams have rows under both sources (cross-tournament, not cross-validating the same match):")
    print(f"{'Team':<15} {'src':<10} {'n':>3} {'fouls':>7} {'SOT':>6} {'cards':>6} {'corners':>8}")
    for team in teams_in_both:
        for source in ("espn_boxscore", "statsbomb_event_data"):
            trows = by_team_source[(team, source)]
            n = len(trows)
            fouls = sum(float(r["fouls_committed"]) for r in trows) / n
            sot = sum(float(r["shots_on_target"]) for r in trows) / n
            cards = sum(float(r["yellow_cards"]) + float(r["red_cards"]) for r in trows) / n
            corners = sum(float(r["corners"]) for r in trows) / n
            tag = "ESPN/26" if source == "espn_boxscore" else "SB/18+22"
            print(f"{team:<15} {tag:<10} {n:>3} {fouls:>7.2f} {sot:>6.2f} {cards:>6.2f} {corners:>8.2f}")


def build():
    rows = load_espn_rows() + load_statsbomb_rows()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: none_if_blank(r.get(c)) for c in COLUMNS})

    by_year = {}
    for r in rows:
        by_year.setdefault(r["season_year"], 0)
        by_year[r["season_year"]] += 1
    print(f"Unified panel written: {OUT}")
    print(f"Total rows: {len(rows)}")
    for y in sorted(by_year):
        print(f"  {y}: {by_year[y]} team-match rows")

    cross_source_plausibility_check(rows)


if __name__ == "__main__":
    build()
