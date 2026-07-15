"""
build_espn_panel.py
-------------------
Pulls actual per-match team statistics from the ESPN public API for every
WC2026 group-stage and Round-of-32 match and writes two output files:

  data/processed/espn_match_panel.csv
      One row per team per match (2 rows per match).
      Columns: event_id, date, match_slug, team_code, team_espn_abbr,
               home_away, goals, opponent_goals,
               fouls, yellow_cards, red_cards, offsides, corners,
               saves, possession_pct, total_shots, shots_on_target,
               blocked_shots, passes, pass_pct, interceptions,
               effective_tackles, clearances, venue, venue_city.

  data/processed/espn_rolling_averages.csv
      One row per team per match, adding columns for that team's rolling
      average of each stat across all prior tournament matches (at time of
      kickoff). Used for pre-match question estimation lookups.

IMPORTANT: All event IDs and team mappings have been verified against the
ESPN API (see verification run on 2026-07-03). The mapping is hardcoded and
should be re-verified if ESPN changes team abbreviations or event IDs.

ESPN API endpoint:
  https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary?event={id}

Usage:
    python3 data/processed/build_espn_panel.py

Rate: ~0.5 s between requests; 88 matches → ~45 s total.
"""

import csv
import json
import ssl
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_PANEL   = ROOT / "data" / "processed" / "espn_match_panel.csv"
OUT_ROLLING = ROOT / "data" / "processed" / "espn_rolling_averages.csv"

# ── Verified event ID map ──────────────────────────────────────────────────
# (date, event_id, espn_abbr_a, espn_abbr_b, our_slug_a, our_slug_b)
# our_slug codes match the naming convention in data/external_markets/*.json
# Verified 2026-07-03 against ESPN scoreboard API + individual summary calls.

EVENTS = [
    # date          id      espn_a  espn_b  our_a   our_b
    ("2026-06-11", 760414, "KOR",  "CZE",  "KOR",  "CZE"),
    ("2026-06-11", 760415, "MEX",  "RSA",  "MEX",  "RSA"),
    ("2026-06-12", 760416, "CAN",  "BIH",  "CAN",  "BIH"),
    ("2026-06-12", 760417, "USA",  "PAR",  "USA",  "PAR"),
    ("2026-06-13", 760418, "HAI",  "SCO",  "HAI",  "SCO"),
    ("2026-06-13", 760419, "BRA",  "MAR",  "BRA",  "MAR"),
    ("2026-06-13", 760420, "QAT",  "SUI",  "QAT",  "SUI"),
    ("2026-06-14", 760421, "AUS",  "TUR",  "AUS",  "TUR"),
    ("2026-06-14", 760422, "GER",  "CUW",  "GER",  "CUR"),
    ("2026-06-14", 760423, "CIV",  "ECU",  "CIV",  "ECU"),
    ("2026-06-14", 760424, "SWE",  "TUN",  "SWE",  "TUN"),
    ("2026-06-14", 760425, "NED",  "JPN",  "NED",  "JPN"),
    ("2026-06-15", 760426, "BEL",  "EGY",  "BEL",  "EGY"),
    ("2026-06-15", 760427, "IRN",  "NZL",  "IRN",  "NZL"),
    ("2026-06-15", 760428, "ESP",  "CPV",  "ESP",  "CPV"),
    ("2026-06-15", 760429, "KSA",  "URU",  "SAU",  "URU"),
    ("2026-06-16", 760430, "IRQ",  "NOR",  "IRQ",  "NOR"),
    ("2026-06-16", 760432, "FRA",  "SEN",  "FRA",  "SEN"),
    ("2026-06-16", 760433, "ARG",  "ALG",  "ARG",  "ALG"),
    ("2026-06-17", 760431, "AUT",  "JOR",  "AUT",  "JOR"),
    ("2026-06-17", 760434, "GHA",  "PAN",  "GHA",  "PAN"),
    ("2026-06-17", 760435, "POR",  "COD",  "POR",  "CDR"),
    ("2026-06-17", 760436, "UZB",  "COL",  "UZB",  "COL"),
    ("2026-06-17", 760437, "ENG",  "CRO",  "ENG",  "CRO"),
    ("2026-06-18", 760438, "CZE",  "RSA",  "CZE",  "RSA"),
    ("2026-06-18", 760439, "SUI",  "BIH",  "SUI",  "BIH"),
    ("2026-06-18", 760440, "CAN",  "QAT",  "CAN",  "QAT"),
    ("2026-06-18", 760441, "MEX",  "KOR",  "MEX",  "KOR"),
    ("2026-06-19", 760442, "USA",  "AUS",  "USA",  "AUS"),
    ("2026-06-19", 760443, "TUR",  "PAR",  "TUR",  "PAR"),
    ("2026-06-19", 760444, "BRA",  "HAI",  "BRA",  "HAI"),
    ("2026-06-19", 760445, "SCO",  "MAR",  "SCO",  "MAR"),
    ("2026-06-20", 760446, "ECU",  "CUW",  "ECU",  "CUR"),
    ("2026-06-20", 760447, "NED",  "SWE",  "NED",  "SWE"),
    ("2026-06-20", 760448, "GER",  "CIV",  "GER",  "CIV"),
    ("2026-06-21", 760449, "TUN",  "JPN",  "TUN",  "JPN"),
    ("2026-06-21", 760450, "URU",  "CPV",  "URU",  "CPV"),
    ("2026-06-21", 760451, "BEL",  "IRN",  "BEL",  "IRN"),
    ("2026-06-21", 760452, "NZL",  "EGY",  "NZL",  "EGY"),
    ("2026-06-21", 760453, "ESP",  "KSA",  "ESP",  "SAU"),
    ("2026-06-22", 760454, "NOR",  "SEN",  "NOR",  "SEN"),
    ("2026-06-22", 760455, "JOR",  "ALG",  "JOR",  "ALG"),
    ("2026-06-22", 760456, "ARG",  "AUT",  "ARG",  "AUT"),
    ("2026-06-22", 760457, "FRA",  "IRQ",  "FRA",  "IRQ"),
    ("2026-06-23", 760458, "ENG",  "GHA",  "ENG",  "GHA"),
    ("2026-06-23", 760459, "COL",  "COD",  "COL",  "CDR"),
    ("2026-06-23", 760460, "PAN",  "CRO",  "PAN",  "CRO"),
    ("2026-06-23", 760461, "POR",  "UZB",  "POR",  "UZB"),
    ("2026-06-24", 760462, "BIH",  "QAT",  "BIH",  "QAT"),
    ("2026-06-24", 760463, "SUI",  "CAN",  "SUI",  "CAN"),
    ("2026-06-24", 760464, "MAR",  "HAI",  "MAR",  "HAI"),
    ("2026-06-24", 760465, "SCO",  "BRA",  "SCO",  "BRA"),
    ("2026-06-24", 760466, "RSA",  "KOR",  "RSA",  "KOR"),
    ("2026-06-24", 760467, "CZE",  "MEX",  "CZE",  "MEX"),
    ("2026-06-25", 760468, "ECU",  "GER",  "ECU",  "GER"),
    ("2026-06-25", 760469, "PAR",  "AUS",  "PAR",  "AUS"),
    ("2026-06-25", 760470, "TUR",  "USA",  "TUR",  "USA"),
    ("2026-06-25", 760471, "JPN",  "SWE",  "JPN",  "SWE"),
    ("2026-06-25", 760472, "TUN",  "NED",  "TUN",  "NED"),
    ("2026-06-25", 760473, "CUW",  "CIV",  "CUR",  "CIV"),
    ("2026-06-26", 760474, "SEN",  "IRQ",  "SEN",  "IRQ"),
    ("2026-06-26", 760475, "NOR",  "FRA",  "NOR",  "FRA"),
    ("2026-06-26", 760476, "EGY",  "IRN",  "EGY",  "IRN"),
    ("2026-06-26", 760477, "NZL",  "BEL",  "NZL",  "BEL"),
    ("2026-06-26", 760478, "CPV",  "KSA",  "CPV",  "SAU"),
    ("2026-06-26", 760479, "URU",  "ESP",  "URU",  "ESP"),
    ("2026-06-27", 760480, "CRO",  "GHA",  "CRO",  "GHA"),
    ("2026-06-27", 760481, "COL",  "POR",  "COL",  "POR"),
    ("2026-06-27", 760482, "COD",  "UZB",  "CDR",  "UZB"),
    ("2026-06-27", 760483, "JOR",  "ARG",  "JOR",  "ARG"),
    ("2026-06-27", 760484, "ALG",  "AUT",  "ALG",  "AUT"),
    ("2026-06-27", 760485, "PAN",  "ENG",  "PAN",  "ENG"),
    ("2026-06-28", 760486, "RSA",  "CAN",  "RSA",  "CAN"),
    ("2026-06-29", 760487, "BRA",  "JPN",  "BRA",  "JPN"),
    ("2026-06-29", 760488, "NED",  "MAR",  "NED",  "MAR"),
    ("2026-06-29", 760489, "GER",  "PAR",  "GER",  "PAR"),
    ("2026-06-30", 760490, "CIV",  "NOR",  "CIV",  "NOR"),
    ("2026-06-30", 760491, "MEX",  "ECU",  "MEX",  "ECU"),
    ("2026-06-30", 760492, "FRA",  "SWE",  "FRA",  "SWE"),
    ("2026-07-01", 760493, "BEL",  "SEN",  "BEL",  "SEN"),
    ("2026-07-01", 760494, "USA",  "BIH",  "USA",  "BIH"),
    ("2026-07-01", 760495, "ENG",  "COD",  "ENG",  "CDR"),
    ("2026-07-02", 760496, "POR",  "CRO",  "POR",  "CRO"),
    ("2026-07-02", 760497, "ESP",  "AUT",  "ESP",  "AUT"),
    ("2026-07-02", 760498, "SUI",  "ALG",  "SUI",  "ALG"),
    # R32 final batch (added 2026-07-14; was missing from the original build)
    ("2026-07-03", 760499, "AUS",  "EGY",  "AUS",  "EGY"),
    ("2026-07-03", 760500, "ARG",  "CPV",  "ARG",  "CPV"),
    ("2026-07-03", 760501, "COL",  "GHA",  "COL",  "GHA"),
    # R16 (added 2026-07-14)
    ("2026-07-04", 760502, "CAN",  "MAR",  "CAN",  "MAR"),
    ("2026-07-04", 760503, "PAR",  "FRA",  "PAR",  "FRA"),
    ("2026-07-05", 760504, "BRA",  "NOR",  "BRA",  "NOR"),
    ("2026-07-05", 760505, "MEX",  "ENG",  "MEX",  "ENG"),
    ("2026-07-06", 760506, "POR",  "ESP",  "POR",  "ESP"),
    ("2026-07-06", 760507, "USA",  "BEL",  "USA",  "BEL"),
    ("2026-07-07", 760508, "SUI",  "COL",  "SUI",  "COL"),
    ("2026-07-07", 760509, "ARG",  "EGY",  "ARG",  "EGY"),
    # QF (added 2026-07-14)
    ("2026-07-09", 760510, "FRA",  "MAR",  "FRA",  "MAR"),
    ("2026-07-10", 760511, "ESP",  "BEL",  "ESP",  "BEL"),
    ("2026-07-11", 760512, "NOR",  "ENG",  "NOR",  "ENG"),
    ("2026-07-11", 760513, "ARG",  "SUI",  "ARG",  "SUI"),
]

# Stats to extract from ESPN boxscore (ESPN field name -> our column name)
STAT_FIELDS = {
    "foulsCommitted":   "fouls",
    "yellowCards":      "yellow_cards",
    "redCards":         "red_cards",
    "offsides":         "offsides",
    "wonCorners":       "corners",
    "saves":            "saves",
    "possessionPct":    "possession_pct",
    "totalShots":       "total_shots",
    "shotsOnTarget":    "shots_on_target",
    "blockedShots":     "blocked_shots",
    "totalPasses":      "passes",
    "passPct":          "pass_pct",
    "interceptions":    "interceptions",
    "effectiveTackles": "effective_tackles",
    "totalClearance":   "clearances",
}

PANEL_COLS = [
    "event_id", "date", "match_slug", "team_code", "team_espn_abbr",
    "home_away", "goals", "opponent_goals",
] + list(STAT_FIELDS.values()) + ["venue", "venue_city"]


def _ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def fetch_match(event_id, ctx):
    url = (
        "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world"
        f"/summary?event={event_id}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        return json.loads(r.read())


def parse_match(data, event_id, date, our_a, our_b):
    """Extract two team rows from a raw ESPN summary response."""
    comp   = data["header"]["competitions"][0]
    gi     = data.get("gameInfo", {})
    venue  = gi.get("venue", {}).get("fullName", "")
    addr   = gi.get("venue", {}).get("address", {})
    city   = addr.get("city", "")

    match_slug = f"{our_a}-{our_b}"

    # scores keyed by ESPN abbreviation
    scores = {}
    espn_to_our = {}
    for comp_team in comp.get("competitors", []):
        abbr = comp_team["team"]["abbreviation"]
        scores[abbr] = int(comp_team.get("score") or 0)

    # boxscore stats
    bs_teams = data.get("boxscore", {}).get("teams", [])
    rows = []
    for bs_team in bs_teams:
        espn_abbr = bs_team["team"]["abbreviation"]
        home_away = bs_team.get("homeAway", "")

        # Map ESPN abbreviation to our code
        # Use position in EVENTS tuple to map correctly
        if espn_abbr == data["header"]["competitions"][0]["competitors"][0]["team"]["abbreviation"]:
            our_code = our_a
        else:
            our_code = our_b

        opp_abbr = [a for a in scores if a != espn_abbr]
        goals     = scores.get(espn_abbr)
        opp_goals = scores.get(opp_abbr[0]) if opp_abbr else None

        stat_map = {s["name"]: s.get("displayValue") for s in bs_team.get("statistics", [])}

        row = {
            "event_id":        event_id,
            "date":            date,
            "match_slug":      match_slug,
            "team_code":       our_code,
            "team_espn_abbr":  espn_abbr,
            "home_away":       home_away,
            "goals":           goals,
            "opponent_goals":  opp_goals,
            "venue":           venue,
            "venue_city":      city,
        }
        for espn_name, our_name in STAT_FIELDS.items():
            raw = stat_map.get(espn_name)
            if raw is not None:
                try:
                    raw = float(raw)
                    if raw == int(raw) and our_name not in ("possession_pct", "pass_pct"):
                        raw = int(raw)
                except (ValueError, TypeError):
                    pass
            row[our_name] = raw
        rows.append(row)
    return rows


def build_rolling_averages(panel_rows):
    """
    For each row in the panel, compute rolling averages of numeric stat columns
    across all prior matches for that team (strictly before this match's date).
    Returns list of dicts with same keys + rolling_n + rolling_* columns.
    """
    stat_cols = list(STAT_FIELDS.values())
    # Sort by date so we can iterate in order
    sorted_rows = sorted(panel_rows, key=lambda r: (r["date"], r["event_id"]))

    # cumulative tracker: team_code -> {stat: [values so far]}
    history = {}
    rolling_rows = []

    for row in sorted_rows:
        team = row["team_code"]
        if team not in history:
            history[team] = {s: [] for s in stat_cols}

        prior = history[team]
        n = len(prior[stat_cols[0]])

        rolling_row = dict(row)
        rolling_row["rolling_n"] = n
        for s in stat_cols:
            vals = [v for v in prior[s] if v is not None]
            rolling_row[f"rolling_{s}"] = round(sum(vals) / len(vals), 3) if vals else None

        # Now append this match to history
        for s in stat_cols:
            history[team][s].append(row.get(s))

        rolling_rows.append(rolling_row)

    return rolling_rows


def main():
    ctx = _ssl_ctx()
    panel_rows = []
    errors = []

    print(f"Fetching {len(EVENTS)} matches from ESPN API...")
    for i, (date, eid, espn_a, espn_b, our_a, our_b) in enumerate(EVENTS, 1):
        try:
            data = fetch_match(eid, ctx)
            rows = parse_match(data, eid, date, our_a, our_b)
            panel_rows.extend(rows)
            teams_str = f"{our_a} vs {our_b}"
            print(f"  [{i:2d}/{len(EVENTS)}] {eid} {date} {teams_str:<14}  "
                  f"goals: {rows[0]['goals']}-{rows[0]['opponent_goals']}  "
                  f"shots: {rows[0]['total_shots']}/{rows[1]['total_shots']}")
        except Exception as e:
            errors.append((eid, date, our_a, our_b, str(e)))
            print(f"  [{i:2d}/{len(EVENTS)}] {eid} {date} {our_a} vs {our_b}  ERROR: {e}")

        if i < len(EVENTS):
            time.sleep(0.5)

    # Write panel
    OUT_PANEL.parent.mkdir(exist_ok=True)
    with open(OUT_PANEL, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=PANEL_COLS)
        w.writeheader()
        w.writerows(panel_rows)

    # Write rolling averages
    rolling_rows = build_rolling_averages(panel_rows)
    rolling_cols = PANEL_COLS + ["rolling_n"] + [f"rolling_{s}" for s in STAT_FIELDS.values()]
    with open(OUT_ROLLING, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rolling_cols)
        w.writeheader()
        w.writerows(rolling_rows)

    print(f"\n{'='*60}")
    print(f"Matches fetched:  {len(EVENTS) - len(errors)}/{len(EVENTS)}")
    if errors:
        print(f"Errors ({len(errors)}):")
        for eid, date, a, b, err in errors:
            print(f"  {eid} {date} {a} vs {b}: {err}")
    print(f"Panel rows:       {len(panel_rows)} (2 per match)")
    print(f"Teams covered:    {len(set(r['team_code'] for r in panel_rows))}")
    print(f"Output:           {OUT_PANEL}")
    print(f"Rolling averages: {OUT_ROLLING}")


if __name__ == "__main__":
    main()
