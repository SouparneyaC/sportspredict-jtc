"""
Build the tournament-name -> Elo K-factor mapping table.

Source: data/international_results/results.csv (martj42), `tournament` column.
Target: data/processed/tournament_kfactor_map.csv

K-factor tiers follow the published World Football Elo Ratings methodology
(eloratings.net "FAQ / About" page):
  60 - World Cup finals
  50 - Continental championship finals + major intercontinental tournaments
  40 - World Cup and continental (major-confederation) qualifiers, and other
       major tournaments
  30 - All other tournaments (regional cups, games, minor confederations,
       CONIFA, friendship/invitational tournaments, sub-regional qualifiers)
  20 - Friendly matches

This is a one-time, static classification: a tournament's "type" does not
change over time, so there is no point-in-time concern in building it.
"""

import csv
from collections import Counter
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "international_results" / "results.csv"
DST = Path(__file__).resolve().parent / "tournament_kfactor_map.csv"

K60 = {
    "FIFA World Cup",
}

K50 = {
    "UEFA Euro",
    "Copa América",
    "African Cup of Nations",
    "AFC Asian Cup",
    "CONCACAF Championship",
    "Gold Cup",
    "Confederations Cup",
    "Oceania Nations Cup",
    "UEFA Nations League",
    "CONCACAF Nations League",
    "Olympic Games",
}

K40 = {
    "FIFA World Cup qualification",
    "UEFA Euro qualification",
    "African Cup of Nations qualification",
    "AFC Asian Cup qualification",
    "CONCACAF Championship qualification",
    "Gold Cup qualification",
    "Copa América qualification",
    "Oceania Nations Cup qualification",
    "CONCACAF Nations League qualification",
}

K20 = {
    "Friendly",
}

LABELS = {
    60: "World Cup finals",
    50: "Continental championship finals / major intercontinental",
    40: "World Cup & major-confederation qualifiers",
    30: "All other tournaments (regional/minor/invitational/CONIFA)",
    20: "Friendly",
}


def classify(tournament: str) -> int:
    if tournament in K60:
        return 60
    if tournament in K50:
        return 50
    if tournament in K40:
        return 40
    if tournament in K20:
        return 20
    return 30


def main() -> None:
    counts = Counter()
    with open(SRC, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            counts[row["tournament"]] += 1

    rows = []
    for tournament, n in counts.items():
        k = classify(tournament)
        rows.append((tournament, n, k, LABELS[k]))

    rows.sort(key=lambda r: (-r[1], r[0]))

    with open(DST, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["tournament", "match_count", "k_factor", "category"])
        writer.writerows(rows)

    # Summary by tier
    tier_counts = Counter()
    tier_matches = Counter()
    for tournament, n, k, _ in rows:
        tier_counts[k] += 1
        tier_matches[k] += n

    print(f"Wrote {len(rows)} tournament mappings to {DST}")
    print(f"{'K':>4}  {'#tournaments':>12}  {'#matches':>9}  category")
    for k in sorted(tier_counts, reverse=True):
        print(f"{k:>4}  {tier_counts[k]:>12}  {tier_matches[k]:>9}  {LABELS[k]}")


if __name__ == "__main__":
    main()
