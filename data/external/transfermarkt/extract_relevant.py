"""
Extract the subset of the Transfermarkt dataset relevant to international
football ML features:
  - national_teams.csv          -> copied as-is (119 rows, squad value/avg age/fifa rank per nation)
  - players.csv                 -> filtered to players with a current_national_team_id
                                    (keeps international_caps/goals, market values)
  - player_valuations.csv       -> filtered to those national-team players only
                                    (24MB -> much smaller)
  - games.csv                   -> filtered to national-team competitions
                                    (FIWC=World Cup, EURO, COPA=Copa America,
                                     AFAC=Asian Cup, AFCN=Africa Cup of Nations)

Output written to data/external/transfermarkt/extracted/.
"""

import csv
import shutil
from pathlib import Path

SRC = Path(__file__).resolve().parent / "transfermarkt-datasets"
OUT = Path(__file__).resolve().parent / "extracted"
OUT.mkdir(exist_ok=True)

NATIONAL_COMPS = {"FIWC", "EURO", "COPA", "AFAC", "AFCN"}

csv.field_size_limit(10_000_000)


def main():
    # 1. national_teams.csv -> copy as-is
    shutil.copy(SRC / "national_teams.csv", OUT / "national_teams.csv")
    print("Copied national_teams.csv")

    # 2. players.csv -> filter to players with current_national_team_id set
    nt_player_ids = set()
    with open(SRC / "players.csv", newline="", encoding="utf-8") as f, \
         open(OUT / "national_team_players.csv", "w", newline="", encoding="utf-8") as out:
        reader = csv.DictReader(f)
        writer = csv.DictWriter(out, fieldnames=reader.fieldnames)
        writer.writeheader()
        n = 0
        for row in reader:
            if row["current_national_team_id"]:
                writer.writerow(row)
                nt_player_ids.add(row["player_id"])
                n += 1
    print(f"Wrote national_team_players.csv ({n} players)")

    # 3. player_valuations.csv -> filter to those player_ids
    with open(SRC / "player_valuations.csv", newline="", encoding="utf-8") as f, \
         open(OUT / "national_team_player_valuations.csv", "w", newline="", encoding="utf-8") as out:
        reader = csv.DictReader(f)
        writer = csv.DictWriter(out, fieldnames=reader.fieldnames)
        writer.writeheader()
        n = 0
        for row in reader:
            if row["player_id"] in nt_player_ids:
                writer.writerow(row)
                n += 1
    print(f"Wrote national_team_player_valuations.csv ({n} rows)")

    # 4. games.csv -> filter to national-team competitions
    with open(SRC / "games.csv", newline="", encoding="utf-8") as f, \
         open(OUT / "national_team_games.csv", "w", newline="", encoding="utf-8") as out:
        reader = csv.DictReader(f)
        writer = csv.DictWriter(out, fieldnames=reader.fieldnames)
        writer.writeheader()
        n = 0
        for row in reader:
            if row["competition_id"] in NATIONAL_COMPS:
                writer.writerow(row)
                n += 1
    print(f"Wrote national_team_games.csv ({n} games)")


if __name__ == "__main__":
    main()
