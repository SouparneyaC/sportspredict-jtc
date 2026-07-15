"""
Compile France/Spain form data for the 2026-07-14 SF from the raw ESPN summary
dumps saved in matches/France Vs Spain (Jul.14.26)/espn_raw/. Produces
10_espn_form.json: per-game team stats, Mbappe/Yamal player lines, substitution
timing (who subbed first, first-sub minute), and the SF squad shirt numbers
for the single-digit-shirt question.

Usage:
    python3 compile_fra_esp_espn_form.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "matches" / "France Vs Spain (Jul.14.26)" / "espn_raw"
OUT = ROOT / "matches" / "France Vs Spain (Jul.14.26)" / "10_espn_form.json"

GAMES = [
    ("FRA_SEN_group", "760432", "France"),
    ("FRA_IRQ_group", "760457", "France"),
    ("FRA_NOR_group", "760475", "France"),
    ("FRA_SWE_r32", "760492", "France"),
    ("FRA_PAR_r16", "760503", "France"),
    ("FRA_MAR_qf", "760510", "France"),
    ("ESP_CPV_group", "760428", "Spain"),
    ("ESP_SAU_group", "760453", "Spain"),
    ("ESP_URU_group", "760479", "Spain"),
    ("ESP_AUT_r32", "760497", "Spain"),
    ("ESP_POR_r16", "760506", "Spain"),
    ("ESP_BEL_qf", "760511", "Spain"),
]

TRACKED_PLAYERS = {"Kylian Mbappé", "Kylian Mbappe", "Lamine Yamal"}

TEAM_STATS = ["foulsCommitted", "yellowCards", "redCards", "offsides",
              "wonCorners", "saves", "possessionPct", "totalShots", "shotsOnTarget"]


def team_stats(summary, team_name):
    for t in summary["boxscore"]["teams"]:
        if t["team"]["displayName"] == team_name:
            return {s["name"]: s.get("displayValue") for s in t["statistics"]
                    if s["name"] in TEAM_STATS}
    return None


def scores(summary):
    comp = summary["header"]["competitions"][0]
    out = {}
    for c in comp["competitors"]:
        out[c["team"]["displayName"]] = int(c.get("score", -1))
    return out, comp.get("date"), comp.get("status", {}).get("type", {}).get("detail")


def player_lines(summary):
    """Stat lines for tracked players from the rosters block."""
    lines = {}
    for side in summary.get("rosters", []):
        tname = side.get("team", {}).get("displayName")
        for entry in side.get("roster", []):
            nm = entry.get("athlete", {}).get("displayName", "")
            if nm in TRACKED_PLAYERS:
                stats = {}
                for s in entry.get("stats", []):
                    stats[s["name"]] = s.get("value")
                lines[nm] = {"team": tname, "starter": entry.get("starter"),
                             "jersey": entry.get("athlete", {}).get("jersey"),
                             "subbed_out": entry.get("subbedOut"),
                             "stats": stats}
    return lines


def substitutions(summary):
    """(minute, team) for each sub from keyEvents, sorted by appearance order."""
    subs = []
    for ev in summary.get("keyEvents", []):
        etype = ev.get("type", {}).get("text", "")
        if "Substitution" in etype:
            clock = ev.get("clock", {}).get("displayValue", "")
            team = ev.get("team", {}).get("displayName", "?")
            subs.append({"clock": clock, "team": team})
    return subs


def clock_to_min(clock):
    m = re.match(r"(\d+)", clock or "")
    return int(m.group(1)) if m else None


def sf_rosters(summary):
    """Squad list with jersey numbers from the upcoming-fixture summary."""
    out = {}
    for side in summary.get("rosters", []):
        tname = side.get("team", {}).get("displayName")
        players = []
        for entry in side.get("roster", []):
            ath = entry.get("athlete", {})
            players.append({
                "name": ath.get("displayName"),
                "jersey": ath.get("jersey"),
                "position": ath.get("position", {}).get("abbreviation"),
                "starter": entry.get("starter"),
            })
        out[tname] = players
    return out


def main():
    result = {"_description": (
        "ESPN form data for France and Spain across all 6 WC2026 games each, "
        "compiled from raw summaries in espn_raw/ (fetched live 2026-07-14). "
        "Team stats per game, Mbappe/Yamal per-game lines, substitution timing, "
        "and SF squad shirt numbers (event 760514)."),
        "games": [], "sf_fixture": {}}

    for tag, eid, our_team in GAMES:
        summary = json.load(open(RAW_DIR / f"espn_{tag}_{eid}.json"))
        sc, date, status_detail = scores(summary)
        subs = substitutions(summary)
        first_sub = subs[0] if subs else None
        game = {
            "tag": tag, "espn_event": eid, "date": date, "status": status_detail,
            "score": sc,
            "team_stats": {t["team"]["displayName"]:
                           {s["name"]: s.get("displayValue") for s in t["statistics"]
                            if s["name"] in TEAM_STATS}
                           for t in summary["boxscore"]["teams"]},
            "tracked_players": player_lines(summary),
            "substitutions": subs,
            "first_sub_team": first_sub["team"] if first_sub else None,
            "first_sub_minute": clock_to_min(first_sub["clock"]) if first_sub else None,
        }
        result["games"].append(game)
        print(f"[{tag}] score={sc} first_sub={game['first_sub_team']}@{game['first_sub_minute']}'")

    fixture = json.load(open(RAW_DIR / "espn_FRA_ESP_sf_fixture_760514.json"))
    gi = fixture.get("gameInfo", {})
    result["sf_fixture"] = {
        "espn_event": "760514",
        "venue": gi.get("venue", {}).get("fullName"),
        "venue_city": gi.get("venue", {}).get("address", {}),
        "rosters": sf_rosters(fixture),
    }
    print("SF venue:", result["sf_fixture"]["venue"], result["sf_fixture"]["venue_city"])
    for team, players in result["sf_fixture"]["rosters"].items():
        single = [p["name"] + " #" + str(p["jersey"]) for p in players
                  if p.get("jersey") and p["jersey"].isdigit() and 1 <= int(p["jersey"]) <= 9]
        print(f"{team}: {len(players)} players, single-digit shirts: {single}")

    with open(OUT, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
