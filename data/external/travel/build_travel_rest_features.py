"""
Build two derived feature tables for the alt-data ML project:

1. team_venue_distances.csv
   Great-circle distance (km) from each national team's "home base" (its
   country's capital city, as a proxy for where the team is based / where
   fans and team facilities cluster) to each of the 16 2026 World Cup
   venues. Useful as a "travel burden" feature for the 2026 tournament.

2. rest_days_features.csv
   For every team-match in elo_match_panel.csv, the number of days since
   that team's previous match (rest days). Fully derivable from existing
   data -- no external source needed, but included here since it's part
   of the same "travel & fatigue" feature group.

Usage:
    python3 build_travel_rest_features.py
"""

import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PANEL_CSV = ROOT / "data" / "processed" / "elo_match_panel.csv"
CAPITALS_CSV = Path(__file__).resolve().parent / "country_capitals.csv"
VENUES_CSV = Path(__file__).resolve().parent / "wc2026_venue_coords.csv"
OUT_DISTANCES = Path(__file__).resolve().parent / "team_venue_distances.csv"
OUT_REST = Path(__file__).resolve().parent / "rest_days_features.csv"

# Map elo_match_panel team names -> country_capitals.csv "Country" names
# (only entries needed to resolve real FIFA-member naming mismatches;
# historical/unrecognized entities are left unmatched on purpose).
ALIASES = {
    "Czech Republic": "Czechia",
    "DR Congo": "Democratic Republic of the Congo",
    "Hong Kong": "China, Hong Kong SAR",
    "Iran": "Iran (Islamic Republic of)",
    "Ivory Coast": "Côte d'Ivoire",
    "Laos": "Lao People's Democratic Republic",
    "Macau": "China, Macao SAR",
    "Moldova": "Republic of Moldova",
    "North Korea": "Dem. People's Republic of Korea",
    "North Macedonia": "TFYR Macedonia",
    "Republic of Ireland": "Ireland",
    "Russia": "Russian Federation",
    "South Korea": "Republic of Korea",
    "Syria": "Syrian Arab Republic",
    "Taiwan": "China, Taiwan Province of China",
    "Tanzania": "United Republic of Tanzania",
    "United States": "United States of America",
    "Venezuela": "Venezuela (Bolivarian Republic of)",
    "Vietnam": "Viet Nam",
    "Bolivia": "Bolivia (Plurinational State of)",
    "Brunei": "Brunei Darussalam",
    "Cape Verde": "Cabo Verde",
    "Eswatini": "Swaziland",
}

# UK home nations and a few other FIFA members with no single-country
# capital entry: (lat, lon) of their footballing "home base" city.
MANUAL_COORDS = {
    "England": (51.5072, -0.1276),       # London
    "Scotland": (55.9533, -3.1883),      # Edinburgh
    "Wales": (51.4816, -3.1791),         # Cardiff
    "Northern Ireland": (54.5973, -5.9301),  # Belfast
    "Kosovo": (42.6629, 21.1655),        # Pristina
    "Palestine": (31.9038, 35.2034),     # Ramallah
}


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_team_coords():
    capitals = {}
    with open(CAPITALS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            capitals[row["Country"]] = (float(row["Latitude"]), float(row["Longitude"]))

    teams = set()
    with open(PANEL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            teams.add(row["home_team"])
            teams.add(row["away_team"])

    coords = {}
    unmatched = []
    for team in teams:
        if team in MANUAL_COORDS:
            coords[team] = MANUAL_COORDS[team]
        elif team in capitals:
            coords[team] = capitals[team]
        elif team in ALIASES and ALIASES[team] in capitals:
            coords[team] = capitals[ALIASES[team]]
        else:
            unmatched.append(team)
    return coords, unmatched


def build_distances(coords):
    venues = []
    with open(VENUES_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            venues.append(row)

    with open(OUT_DISTANCES, "w", newline="", encoding="utf-8") as out:
        writer = csv.writer(out)
        writer.writerow(["team", "venue_city", "venue_country", "distance_km"])
        for team, (tlat, tlon) in sorted(coords.items()):
            for v in venues:
                d = haversine_km(tlat, tlon, float(v["latitude"]), float(v["longitude"]))
                writer.writerow([team, v["city"], v["country"], round(d, 1)])
    print(f"Wrote {OUT_DISTANCES} ({len(coords)} teams x {len(venues)} venues)")


def build_rest_days():
    rows = []
    with open(PANEL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["home_score"] == "":
                continue
            rows.append(row)

    last_played = {}
    out_rows = []
    for row in sorted(rows, key=lambda r: r["date"]):
        date = row["date"]
        for side, team in (("home", row["home_team"]), ("away", row["away_team"])):
            prev = last_played.get(team)
            rest_days = (
                (_date_diff(date, prev)) if prev is not None else ""
            )
            out_rows.append({
                "date": date,
                "team": team,
                "side": side,
                "opponent": row["away_team"] if side == "home" else row["home_team"],
                "rest_days": rest_days,
            })
            last_played[team] = date

    with open(OUT_REST, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=["date", "team", "side", "opponent", "rest_days"])
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"Wrote {OUT_REST} ({len(out_rows)} team-match rows)")


def _date_diff(d1, d0):
    from datetime import date
    y1, m1, dd1 = (int(x) for x in d1.split("-"))
    y0, m0, dd0 = (int(x) for x in d0.split("-"))
    return (date(y1, m1, dd1) - date(y0, m0, dd0)).days


def main():
    coords, unmatched = load_team_coords()
    print(f"Resolved home-base coordinates for {len(coords)} teams "
          f"({len(unmatched)} unmatched, mostly historical/non-FIFA entities)")
    build_distances(coords)
    build_rest_days()


if __name__ == "__main__":
    main()
