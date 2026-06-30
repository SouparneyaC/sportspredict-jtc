"""
Extract international-match fixtures + bookmaker odds from the
eatpizzanot/soccer-dataset CSV dump (fixtures.csv, odds.csv, teams.csv,
leagues.csv) into a small, joined table for the alt-data ML project.

International league_ids (from leagues.csv):
  78  FIFA World Cup
  79  UEFA Euro
  80  UEFA Nations League
  81  Copa America
  82  Africa Cup of Nations
  83  Asian Cup
  84  World Cup - Qualification Europe
  85  World Cup - Qualification South America
  86  World Cup - Qualification CONCACAF
  87  Euro Championship - Qualification
  88  International Friendlies

Output: international_fixture_odds.csv with columns:
  fixture_id, date, league_name, home_team, away_team,
  goals_home, goals_away, bookmaker, home_win, draw, away_win, source

Usage:
    python3 extract_international_odds.py
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent

INTL_LEAGUE_IDS = {"78", "79", "80", "81", "82", "83", "84", "85", "86", "87", "88"}


def main():
    leagues = {}
    with open(ROOT / "leagues.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            leagues[row["id"]] = row["name"]

    teams = {}
    with open(ROOT / "teams.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            teams[row["id"]] = row["name"]

    fixtures = {}
    n_intl = 0
    with open(ROOT / "fixtures.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["league_id"] in INTL_LEAGUE_IDS:
                fixtures[row["id"]] = row
                n_intl += 1
    print(f"International fixtures: {n_intl}")

    n_with_odds = 0
    n_odds_rows = 0
    with open(ROOT / "odds.csv", newline="", encoding="utf-8") as f, \
         open(ROOT / "international_fixture_odds.csv", "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(["fixture_id", "date", "league_name", "home_team", "away_team",
                          "goals_home", "goals_away", "bookmaker", "home_win", "draw",
                          "away_win", "source"])
        seen_fixtures = set()
        for row in csv.DictReader(f):
            fx = fixtures.get(row["fixture_id"])
            if fx is None:
                continue
            writer.writerow([
                fx["id"], fx["date"], leagues.get(fx["league_id"], fx["league_id"]),
                teams.get(fx["home_team_id"], fx["home_team_id"]),
                teams.get(fx["away_team_id"], fx["away_team_id"]),
                fx["goals_home"], fx["goals_away"],
                row["bookmaker"], row["home_win"], row["draw"], row["away_win"], row["source"],
            ])
            n_odds_rows += 1
            seen_fixtures.add(row["fixture_id"])
        n_with_odds = len(seen_fixtures)

    print(f"International fixtures with >=1 bookmaker quote: {n_with_odds} "
          f"({n_with_odds / n_intl:.1%})")
    print(f"Total odds rows written: {n_odds_rows}")


if __name__ == "__main__":
    main()
