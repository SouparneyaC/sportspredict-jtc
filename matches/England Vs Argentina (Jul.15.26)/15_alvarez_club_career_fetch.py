"""
Julian Alvarez club-career fetch for ENG-ARG WC2026 SF Q1
("Will Julian Alvarez have 1+ shots on target in regulation?").

Follows the same live-ESPN-fetch pattern established for Messi in
14_messi_recent_form_fetch.py (endpoint discovery, ground-truth verification
before trusting fields), extended across TWO club spells because Alvarez's
"actual current club" turned out NOT to be Manchester City -- confirmed via
ESPN's own player-search API returning subtitle "Atletico Madrid" for athlete
277206 -- he transferred Man City -> Atletico Madrid in July 2024, well before
tonight's kickoff. Both spells are pulled:

  - Manchester City (Jan 2022 - Jul 2024): eng.1 (Premier League) 2022/2023,
    uefa.champions 2022/2023, eng.fa (FA Cup) 2022/2023, eng.league_cup
    2022/2023, fifa.cwc (Club World Cup) 2023, uefa.super_cup 2023,
    eng.charity (Community Shield) 2022/2023.
  - Atletico Madrid (Jul 2024 - present): esp.1 (La Liga) 2024/2025,
    uefa.champions 2024/2025, esp.copa_del_rey 2024/2025, esp.super_cup 2025.

Ground-truth checks performed before trusting shotsOnTarget/totalGoals (see
companion .md, section 3): 2023 FA Cup Final (Man City 2-1 Man Utd, real) and
2023 Club World Cup Final (Man City 4-0 Fluminense, Alvarez scored twice --
real, well-known) both confirmed exactly against the pulled record.

Point-in-time discipline: every event pulled here is already-completed and
dated on or before 2026-07-14 (nothing after tonight's 2026-07-15 kickoff).

Output: 15_alvarez_club_career_espn.json (row per match).
"""
import json
import time
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parent / "15_alvarez_club_career_espn.json"
ATHLETE_ID = "277206"

# (competition_label, club_era, espn_league_slug, season)
TARGETS = [
    ("Premier League", "Man City", "eng.1", 2022),
    ("Premier League", "Man City", "eng.1", 2023),
    ("Champions League", "Man City", "uefa.champions", 2022),
    ("Champions League", "Man City", "uefa.champions", 2023),
    ("FA Cup", "Man City", "eng.fa", 2022),
    ("FA Cup", "Man City", "eng.fa", 2023),
    ("League Cup", "Man City", "eng.league_cup", 2022),
    ("League Cup", "Man City", "eng.league_cup", 2023),
    ("Club World Cup", "Man City", "fifa.cwc", 2023),
    ("UEFA Super Cup", "Man City", "uefa.super_cup", 2023),
    ("Community Shield", "Man City", "eng.charity", 2022),
    ("Community Shield", "Man City", "eng.charity", 2023),
    ("La Liga", "Atletico Madrid", "esp.1", 2024),
    ("La Liga", "Atletico Madrid", "esp.1", 2025),
    ("Champions League", "Atletico Madrid", "uefa.champions", 2024),
    ("Champions League", "Atletico Madrid", "uefa.champions", 2025),
    ("Copa del Rey", "Atletico Madrid", "esp.copa_del_rey", 2024),
    ("Copa del Rey", "Atletico Madrid", "esp.copa_del_rey", 2025),
    ("Spanish Super Cup", "Atletico Madrid", "esp.super_cup", 2025),
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


def extract_row(competition_label, club_era, event_id, data):
    if data is None:
        return None
    h = data.get("header", {})
    comp0 = h.get("competitions", [{}])[0]
    date = comp0.get("date")
    notes = comp0.get("notes", [])
    leg_headline = next((n.get("headline") for n in notes if "Leg" in (n.get("headline") or "")), None)
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
                    "club_era": club_era,
                    "leg_headline": leg_headline,
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
        "event_id": event_id, "competition": competition_label, "club_era": club_era,
        "leg_headline": leg_headline, "date": date, "team": None, "opponent": None,
        "score_str": score_str, "starter": None, "appearances": 0, "shots": None,
        "sot": None, "goals": None, "assists": None,
        "note": "Alvarez not found in rosters for this event (did not play / not in squad)",
    }


def main():
    rows = []
    for label, era, slug, season in TARGETS:
        ids = get_eventlog(slug, season)
        print(f"{label} ({era}) {season}: {len(ids)} played events")
        for eid in ids:
            data = get_summary(slug, eid)
            row = extract_row(label, era, eid, data)
            if row:
                rows.append(row)
            time.sleep(0.03)

    rows.sort(key=lambda r: r["date"] or "")
    OUT.write_text(json.dumps(rows, indent=2))
    print(f"Wrote {len(rows)} rows to {OUT}")


if __name__ == "__main__":
    main()
