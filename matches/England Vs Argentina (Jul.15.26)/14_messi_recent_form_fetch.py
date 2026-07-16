"""
Recency-bridge fetch: Messi's 2021-2026 club/international log via ESPN, live.
Covers the StatsBomb-open-data blind spot (StatsBomb stops at La Liga 2020/21 /
CL 2018/19). Point-in-time discipline: only pulling already-completed historical
matches; nothing dated after tonight's kickoff (2026-07-15).

Uses the same site.api.espn.com summary endpoint pattern already established in
this project's ESPN scripts (data/processed/build_espn_panel.py,
matches/.../11_player_prop_backtest_messi_alvarez.py), and the same
rosters[].roster[].stats field (name/value pairs) verified against the known
2023 Leagues Cup Final ground truth (Messi's free-kick goal, 1-1, Miami won on
penalties) before trusting it for anything else -- confirms totalGoals=1.0 for
that match.

Athlete ID 45843 (Lionel Messi) confirmed via ESPN's own search API.
"""
import json
import time
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parent / "14_messi_recent_form_espn.json"
ATHLETE_ID = "45843"

# (competition_label, espn_league_slug_for_eventlog, espn_league_slug_for_summary, season)
TARGETS = [
    ("Champions League (PSG)", "uefa.champions", "uefa.champions", 2021),
    ("Champions League (PSG)", "uefa.champions", "uefa.champions", 2022),
    ("Concacaf Champions Cup (Inter Miami)", "concacaf.champions", "concacaf.champions", 2024),
    ("Concacaf Champions Cup (Inter Miami)", "concacaf.champions", "concacaf.champions", 2025),
    ("MLS (Inter Miami)", "usa.1", "usa.1", 2024),
    ("MLS (Inter Miami)", "usa.1", "usa.1", 2025),
]

# Leagues Cup final -- not a queryable eventlog league slug, fetched directly by event id
EXTRA_EVENTS = [
    ("Leagues Cup Final (Inter Miami)", "usa.1", "685799"),
]


def get_eventlog(league_slug, season):
    ids = []
    page = 1
    while True:
        url = f"https://sports.core.api.espn.com/v2/sports/soccer/leagues/{league_slug}/seasons/{season}/athletes/{ATHLETE_ID}/eventlog"
        r = requests.get(url, params={"page": page}, timeout=20)
        if r.status_code != 200:
            break
        d = r.json()
        items = d.get("events", {}).get("items", [])
        for it in items:
            if not it.get("played", True):
                continue
            eid = it["event"]["$ref"].split("/")[-1].split("?")[0]
            ids.append(eid)
        page_count = d.get("events", {}).get("pageCount", 1)
        if page >= page_count:
            break
        page += 1
    return ids


def get_summary(summary_slug, event_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{summary_slug}/summary"
    r = requests.get(url, params={"event": event_id}, timeout=20)
    if r.status_code != 200:
        return None
    return r.json()


def extract_row(competition_label, event_id, data):
    if data is None:
        return None
    h = data.get("header", {})
    comp0 = h.get("competitions", [{}])[0]
    season_name = h.get("season", {}).get("name")
    date = comp0.get("date")
    competitors = comp0.get("competitors", [])
    score_str = " / ".join(f"{c['team']['displayName']} {c.get('score')}" for c in competitors)

    rosters = data.get("rosters", [])
    for team in rosters:
        for p in team.get("roster", []):
            if p.get("athlete", {}).get("id") == ATHLETE_ID:
                stats = {s["name"]: s["value"] for s in p.get("stats", [])}
                return {
                    "event_id": event_id,
                    "competition": competition_label,
                    "round_label": season_name,
                    "date": date,
                    "team": team.get("team", {}).get("displayName"),
                    "opponent": next((c["team"]["displayName"] for c in competitors
                                       if c["team"]["displayName"] != team.get("team", {}).get("displayName")), None),
                    "score_str": score_str,
                    "starter": p.get("starter"),
                    "appearances": stats.get("appearances"),
                    "shots": stats.get("totalShots"),
                    "sot": stats.get("shotsOnTarget"),
                    "goals": stats.get("totalGoals"),
                    "assists": stats.get("goalAssists"),
                }
    return {
        "event_id": event_id, "competition": competition_label, "round_label": season_name,
        "date": date, "team": None, "opponent": None, "score_str": score_str,
        "starter": None, "appearances": 0, "shots": None, "sot": None, "goals": None, "assists": None,
        "note": "Messi not found in rosters for this event (did not play / not in squad)",
    }


def main():
    rows = []
    for label, elog_slug, summary_slug, season in TARGETS:
        ids = get_eventlog(elog_slug, season)
        print(f"{label} {season}: {len(ids)} played events")
        for eid in ids:
            data = get_summary(summary_slug, eid)
            row = extract_row(label, eid, data)
            if row:
                rows.append(row)
            time.sleep(0.05)

    for label, summary_slug, eid in EXTRA_EVENTS:
        data = get_summary(summary_slug, eid)
        row = extract_row(label, eid, data)
        if row:
            rows.append(row)

    rows.sort(key=lambda r: r["date"] or "")
    OUT.write_text(json.dumps(rows, indent=2))
    print(f"Wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
