"""
build_statsbomb_panel.py
-------------------------
Flattens StatsBomb open-data event/lineup JSON into two tabular CSVs for
base-rate modeling of JTC's granular markets (fouls, cards, shots-on-target,
corners, offsides, player props).

READ-ONLY against data/external/statsbomb/open-data/ — never writes there.
Writes only:
  data/processed/statsbomb_team_match_panel.csv   (one row per team per match)
  data/processed/statsbomb_player_match_panel.csv (one row per player per match)

Scope (proof of concept): FIFA World Cup 2018 (season_id=3) + 2022
(season_id=106), competition_id=43. 128 matches total. Both are complete
(64/64) and schema-identical (verified in STATSBOMB_DATASET_AUDIT.md and
TRAINING_DATASET_STRATEGY_2026-07-07.md).

Methodology (see TRAINING_DATASET_STRATEGY_2026-07-07.md for source research):
- Shot on target = shot.outcome in {Goal, Saved, Saved To Post}
- Cards read from lineups/{id}.json `cards` array — StatsBomb's own
  aggregation of foul_committed.card + bad_behaviour.card, treated as
  authoritative per the audit rather than re-deriving from events.
- Corners = Pass events with pass.type.name == "Corner" (StatsBomb has no
  standalone Corner event type).
- Offsides = standalone `type.name == "Offside"` events PLUS Pass events with
  `pass.outcome.name == "Pass Offside"` (fixed 2026-07-14). The standalone
  Offside event type is rare in this dataset (5 occurrences across a random
  15-match sample) -- StatsBomb encodes the overwhelming majority of offside
  calls (62/67 in that same sample, ~12:1) as the pass outcome instead. The
  original version of this script only checked the standalone event type,
  undercounting offsides by ~8.5x (verified: team-match mean 0.203 before the
  fix vs ESPN's 2026 mean of 1.725 for the same stat) -- caught during a
  hierarchical-model backtest (ml/backtests/PREREGISTRATION_cards_corners_
  offsides_and_combined.md) whose implausibly large effect size on offsides
  specifically prompted this investigation. This was a genuine extraction
  bug, not a cross-source measurement-convention difference like the other
  stats' smaller ESPN/StatsBomb ratios (SOT 1.3x, corners 1.03x, cards
  0.79-0.88x) -- StatsBomb's underlying data was correct, the parser was
  reading the wrong field.
- Minutes played: summed from lineup positions[] from/to intervals
  (cumulative match-clock, matching the event `minute` field convention).
  Open-ended intervals (`to` is null, i.e. still on at the whistle) are
  closed at the match's last non-shootout event time.
- Period 5 (penalty shootouts) is excluded from all event aggregation, per
  the audit's note that shootout shots aren't run-of-play shots.
- Team goals/result come from the match record (home_score/away_score), not
  re-derived from Shot events, so own goals are handled correctly at team
  level. Player-level `goals` is Shot-event-based and therefore excludes own
  goals (a known, minor simplification — own goals are ~1-2% of goals).
- This is a fixed historical panel, not a rolling/pre-match feature set — no
  walk-forward concerns here since nothing is being applied within a single
  ordered tournament sequence yet. Rolling pre-match averages are a separate
  downstream step, to be built the same way as espn_rolling_averages.csv.

Usage: python3 datasets/build_statsbomb_panel.py
"""

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SB_DATA = ROOT / "data" / "external" / "statsbomb" / "open-data" / "data"
OUT_TEAM = ROOT / "data" / "processed" / "statsbomb_team_match_panel.csv"
OUT_PLAYER = ROOT / "data" / "processed" / "statsbomb_player_match_panel.csv"

TOURNAMENTS = [
    (43, 3, "FIFA World Cup 2018"),
    (43, 106, "FIFA World Cup 2022"),
]

SOT_OUTCOMES = {"Goal", "Saved", "Saved To Post"}
CARD_RED_TYPES = {"Red Card", "Second Yellow"}


def parse_clock(s):
    mm, ss = s.split(":")
    return int(mm) + int(ss) / 60.0


def load_matches():
    matches = {}
    for comp_id, season_id, label in TOURNAMENTS:
        path = SB_DATA / "matches" / str(comp_id) / f"{season_id}.json"
        for m in json.loads(path.read_text()):
            matches[m["match_id"]] = (m, label)
    return matches


def aggregate_match(match_id):
    events = json.loads((SB_DATA / "events" / f"{match_id}.json").read_text())
    lineups = json.loads((SB_DATA / "lineups" / f"{match_id}.json").read_text())

    events = [e for e in events if e.get("period", 1) != 5]  # drop shootout
    match_end_min = max((e["minute"] + e["second"] / 60.0 for e in events), default=90.0)

    team_stats = defaultdict(lambda: defaultdict(float))
    team_names = {}
    player_stats = defaultdict(lambda: defaultdict(float))

    for e in events:
        team = e.get("team")
        if not team:
            continue
        tid = team["id"]
        team_names[tid] = team["name"]
        ts = team_stats[tid]
        etype = e["type"]["name"]
        player = e.get("player")
        ps = player_stats[player["id"]] if player else None

        if etype == "Shot":
            shot = e["shot"]
            outcome = shot["outcome"]["name"]
            xg = shot.get("statsbomb_xg", 0.0)
            is_sot = outcome in SOT_OUTCOMES
            ts["total_shots"] += 1
            ts["xg_total"] += xg
            if is_sot:
                ts["shots_on_target"] += 1
            if outcome == "Blocked":
                ts["blocked_shots"] += 1
            if ps is not None:
                ps["shots"] += 1
                ps["xg_total"] += xg
                if is_sot:
                    ps["shots_on_target"] += 1
                if outcome == "Goal":
                    ps["goals"] += 1
        elif etype == "Foul Committed":
            ts["fouls_committed"] += 1
            if ps is not None:
                ps["fouls_committed"] += 1
        elif etype == "Foul Won":
            ts["fouls_won"] += 1
            if ps is not None:
                ps["fouls_won"] += 1
        elif etype == "Offside":
            ts["offsides"] += 1
        elif etype == "Clearance":
            ts["clearances"] += 1
        elif etype == "Interception":
            ts["interceptions"] += 1
        elif etype == "Pass":
            p = e["pass"]
            ts["passes"] += 1
            if p.get("outcome") is None:
                ts["passes_completed"] += 1
            if p.get("type", {}).get("name") == "Corner":
                ts["corners"] += 1
            if p.get("outcome", {}).get("name") == "Pass Offside":
                ts["offsides"] += 1
            if ps is not None:
                if p.get("goal_assist"):
                    ps["assists"] += 1
                if p.get("shot_assist"):
                    ps["key_passes"] += 1

    player_rows = []
    for team_entry in lineups:
        tid = team_entry["team_id"]
        tname = team_entry["team_name"]
        team_names[tid] = tname
        for p in team_entry["lineup"]:
            yellow = sum(1 for c in p["cards"] if c["card_type"] == "Yellow Card")
            red = sum(1 for c in p["cards"] if c["card_type"] in CARD_RED_TYPES)
            team_stats[tid]["yellow_cards"] += yellow
            team_stats[tid]["red_cards"] += red

            positions = p.get("positions", [])
            minutes = sum(
                max(0.0, (parse_clock(iv["to"]) if iv["to"] else match_end_min) - parse_clock(iv["from"]))
                for iv in positions
            )
            is_starter = any(iv["start_reason"] == "Starting XI" for iv in positions)
            primary_pos = positions[0]["position"] if positions else None
            all_pos = ";".join(sorted({iv["position"] for iv in positions}))

            ps = player_stats.get(p["player_id"], {})
            player_rows.append({
                "player_id": p["player_id"],
                "player_name": p["player_name"],
                "team_id": tid,
                "team_name": tname,
                "jersey_number": p["jersey_number"],
                "position_primary": primary_pos,
                "positions_played": all_pos,
                "is_starter": is_starter,
                "minutes_played": round(minutes, 1),
                "shots": int(ps.get("shots", 0)),
                "shots_on_target": int(ps.get("shots_on_target", 0)),
                "goals": int(ps.get("goals", 0)),
                "assists": int(ps.get("assists", 0)),
                "key_passes": int(ps.get("key_passes", 0)),
                "fouls_committed": int(ps.get("fouls_committed", 0)),
                "fouls_won": int(ps.get("fouls_won", 0)),
                "yellow_cards": yellow,
                "red_cards": red,
                "xg_total": round(ps.get("xg_total", 0.0), 4),
            })

    return team_stats, team_names, player_rows


def build():
    matches = load_matches()
    team_rows, all_player_rows = [], []

    for match_id, (m, tourney_label) in sorted(matches.items()):
        home, away = m["home_team"], m["away_team"]
        home_id, away_id = home["home_team_id"], away["away_team_id"]
        home_name, away_name = home["home_team_name"], away["away_team_name"]
        home_score, away_score = m["home_score"], m["away_score"]

        team_stats, team_names, player_rows = aggregate_match(match_id)

        meta = {
            "match_id": match_id,
            "competition_name": tourney_label,
            "season_name": m["season"]["season_name"],
            "competition_stage": m["competition_stage"]["name"],
            "match_date": m["match_date"],
            "kick_off": m["kick_off"],
            "referee_name": (m.get("referee") or {}).get("name"),
            "stadium_name": (m.get("stadium") or {}).get("name"),
        }

        sides = [
            (home_id, away_id, home_name, away_name, True, home_score, away_score),
            (away_id, home_id, away_name, home_name, False, away_score, home_score),
        ]
        for tid, opp_id, tname, opp_name, is_home, tscore, opp_score in sides:
            s = team_stats.get(tid, {})
            result = "W" if tscore > opp_score else ("D" if tscore == opp_score else "L")
            passes = s.get("passes", 0)
            row = dict(meta)
            row.update({
                "team_id": tid, "team_name": tname,
                "opponent_id": opp_id, "opponent_name": opp_name,
                "is_home": is_home, "goals": tscore, "opponent_goals": opp_score,
                "result": result,
                "total_shots": int(s.get("total_shots", 0)),
                "shots_on_target": int(s.get("shots_on_target", 0)),
                "blocked_shots": int(s.get("blocked_shots", 0)),
                "xg_total": round(s.get("xg_total", 0.0), 4),
                "fouls_committed": int(s.get("fouls_committed", 0)),
                "fouls_won": int(s.get("fouls_won", 0)),
                "yellow_cards": int(s.get("yellow_cards", 0)),
                "red_cards": int(s.get("red_cards", 0)),
                "corners": int(s.get("corners", 0)),
                "offsides": int(s.get("offsides", 0)),
                "passes": int(passes),
                "passes_completed": int(s.get("passes_completed", 0)),
                "pass_pct": round(100 * s.get("passes_completed", 0) / passes, 1) if passes else None,
                "clearances": int(s.get("clearances", 0)),
                "interceptions": int(s.get("interceptions", 0)),
            })
            team_rows.append(row)

        for prow in player_rows:
            row = dict(meta)
            row.update(prow)
            row["opponent_name"] = away_name if prow["team_id"] == home_id else home_name
            all_player_rows.append(row)

    team_cols = [
        "match_id", "competition_name", "season_name", "competition_stage",
        "match_date", "kick_off", "referee_name", "stadium_name",
        "team_id", "team_name", "opponent_id", "opponent_name", "is_home",
        "goals", "opponent_goals", "result",
        "total_shots", "shots_on_target", "blocked_shots", "xg_total",
        "fouls_committed", "fouls_won", "yellow_cards", "red_cards",
        "corners", "offsides", "passes", "passes_completed", "pass_pct",
        "clearances", "interceptions",
    ]
    player_cols = [
        "match_id", "competition_name", "season_name", "competition_stage",
        "match_date", "kick_off", "referee_name", "stadium_name",
        "team_id", "team_name", "opponent_name",
        "player_id", "player_name", "jersey_number",
        "position_primary", "positions_played", "is_starter", "minutes_played",
        "shots", "shots_on_target", "goals", "assists", "key_passes",
        "fouls_committed", "fouls_won", "yellow_cards", "red_cards", "xg_total",
    ]

    OUT_TEAM.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_TEAM, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=team_cols)
        w.writeheader()
        w.writerows(team_rows)

    with open(OUT_PLAYER, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=player_cols)
        w.writeheader()
        w.writerows(all_player_rows)

    print(f"Matches processed: {len(matches)}")
    print(f"Team-match rows:   {len(team_rows)}  -> {OUT_TEAM}")
    print(f"Player-match rows: {len(all_player_rows)}  -> {OUT_PLAYER}")

    total_goals = sum(r["goals"] for r in team_rows)
    total_shots = sum(r["total_shots"] for r in team_rows)
    total_sot = sum(r["shots_on_target"] for r in team_rows)
    n_matches = len(matches)
    print(f"\nSanity check (per match, both teams combined):")
    print(f"  goals/match:  {total_goals / n_matches:.3f}")
    print(f"  shots/match:  {total_shots / n_matches:.3f}")
    print(f"  SOT/match:    {total_sot / n_matches:.3f}")
    for label in ("FIFA World Cup 2018", "FIFA World Cup 2022"):
        rows = [r for r in team_rows if r["competition_name"] == label]
        nm = len(rows) // 2
        g = sum(r["goals"] for r in rows)
        print(f"  {label}: {nm} matches, {g} total goals ({g / nm:.3f}/match)")


if __name__ == "__main__":
    build()
