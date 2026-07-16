"""
Messi high-stakes-vs-regular scoring rate deep dive, for ENG-ARG WC2026 SF Q4
("Will Lionel Messi score a goal (excluding own goals) in regulation?").

Builds Messi's complete shot/goal log from StatsBomb open-data local mirror
(data/external/statsbomb/open-data/, gitignored, never modified) across:
  - Barcelona La Liga  (competition_id=11), seasons 2004/05-2020/21
  - Barcelona Champions League (competition_id=16) -- NOTE: see finding below,
    this corpus only contains CL FINALS, not full campaigns
  - Copa America 2024 (competition_id=223, season_id=282), Argentina
  - MLS 2023 (competition_id=44, season_id=107), Inter Miami

Player identity confirmed from the data itself (not guessed):
  player_id 5503, player_name "Lionel Andrés Messi Cuccittini"
Barcelona team_id confirmed: 217

SOT convention reused unchanged from datasets/build_statsbomb_panel.py:
  shot.outcome.name in {"Goal", "Saved", "Saved To Post"}
Own goals are a separate event type ("Own Goal For"/"Own Goal Against"), never
type.name=="Shot", so they are naturally excluded from the goals count without
any extra filtering.

Minutes-played convention reused unchanged from build_statsbomb_panel.py:
  sum over lineup position stints of (to_minute or match_end_minute) - from_minute,
  where match_end_minute = max event minute+second/60 in that match (shootout
  events, period==5, dropped first).

Output:
  - matches/England Vs Argentina (Jul.15.26)/14_messi_full_log.csv  (row per match Messi appeared in)
  - printed summary stats (high-stakes vs regular comparison), consumed by the
    companion .md writeup.
"""

import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SB = ROOT / "data" / "external" / "statsbomb" / "open-data" / "data"
OUT_DIR = Path(__file__).resolve().parent
OUT_CSV = OUT_DIR / "14_messi_full_log.csv"

MESSI_ID = 5503
BARCA_ID = 217
SOT_OUTCOMES = {"Goal", "Saved", "Saved To Post"}

LALIGA_SEASONS = [90, 42, 4, 1, 2, 27, 26, 25, 24, 23, 22, 21, 41, 40, 39, 38, 37]
CL_SEASONS = [4, 1, 2, 27, 26, 25, 24, 23, 22, 21, 41, 39, 37, 44, 76]


def parse_clock(s):
    mm, ss = s.split(":")
    return int(mm) + int(ss) / 60.0


def match_end_minute(events):
    events = [e for e in events if e.get("period", 1) != 5]  # drop shootout
    return max((e["minute"] + e["second"] / 60.0 for e in events), default=90.0)


def messi_minutes_and_starter(lineups, team_id_hint=None):
    """Return (found, minutes_played, is_starter, team_id, team_name) for Messi in this match."""
    for team_entry in lineups:
        for p in team_entry["lineup"]:
            if p["player_id"] == MESSI_ID:
                positions = p.get("positions", [])
                if not positions:
                    return True, 0.0, False, team_entry["team_id"], team_entry["team_name"]
                return (True, positions, None, team_entry["team_id"], team_entry["team_name"])
    return False, None, None, None, None


def aggregate_messi(match_id):
    """Load events+lineups for match_id, return Messi's stat line or None if he didn't appear."""
    ev_path = SB / "events" / f"{match_id}.json"
    lu_path = SB / "lineups" / f"{match_id}.json"
    if not ev_path.exists() or not lu_path.exists():
        return None
    events = json.loads(ev_path.read_text())
    lineups = json.loads(lu_path.read_text())

    found, positions, _, team_id, team_name = messi_minutes_and_starter(lineups)
    if not found:
        return None

    m_end = match_end_minute(events)
    if isinstance(positions, list):
        minutes = sum(
            max(0.0, (parse_clock(iv["to"]) if iv["to"] else m_end) - parse_clock(iv["from"]))
            for iv in positions
        )
        is_starter = any(iv["start_reason"] == "Starting XI" for iv in positions)
    else:
        minutes, is_starter = 0.0, False

    events = [e for e in events if e.get("period", 1) != 5]
    shots = sot = goals = 0
    for e in events:
        if e.get("type", {}).get("name") != "Shot":
            continue
        player = e.get("player")
        if not player or player.get("id") != MESSI_ID:
            continue
        outcome = e["shot"]["outcome"]["name"]
        shots += 1
        if outcome in SOT_OUTCOMES:
            sot += 1
        if outcome == "Goal":
            goals += 1

    return {
        "minutes_played": round(minutes, 1),
        "is_starter": is_starter,
        "shots": shots,
        "shots_on_target": sot,
        "goals": goals,
        "team_id": team_id,
        "team_name": team_name,
    }


def build_match_meta(m, competition_label):
    home, away = m["home_team"], m["away_team"]
    return {
        "match_id": m["match_id"],
        "match_date": m["match_date"],
        "competition": competition_label,
        "season": m["season"]["season_name"],
        "stage": m.get("competition_stage", {}).get("name"),
        "home_team": home["home_team_name"],
        "away_team": away["away_team_name"],
        "home_team_id": home["home_team_id"],
        "away_team_id": away["away_team_id"],
        "home_score": m["home_score"],
        "away_score": m["away_score"],
    }


def tag_high_stakes(row):
    """Apply the 5 pre-registered high-stakes criteria. Returns list of tags."""
    tags = []
    comp = row["competition"]
    stage = row["stage"] or ""
    opponent = row["opponent"]

    if comp == "Champions League" and stage not in ("Group Stage", "Regular Season"):
        tags.append("CL_knockout_R16plus")
    if comp == "Champions League" and stage == "Final":
        tags.append("CL_final")
    if comp == "Copa del Rey" and stage == "Final":
        tags.append("CopaDelRey_final")
    if opponent == "Real Madrid":
        tags.append("El_Clasico")
    if comp == "Copa America 2024":
        tags.append("Copa_America_2024")
    return tags


def main():
    rows = []

    # ---- La Liga (Barcelona) ----
    for season_id in LALIGA_SEASONS:
        mpath = SB / "matches" / "11" / f"{season_id}.json"
        matches = json.loads(mpath.read_text())
        for m in matches:
            hid, aid = m["home_team"]["home_team_id"], m["away_team"]["away_team_id"]
            if BARCA_ID not in (hid, aid):
                continue
            stat = aggregate_messi(m["match_id"])
            if stat is None:
                continue
            meta = build_match_meta(m, "La Liga")
            is_home = hid == BARCA_ID
            meta["opponent"] = m["away_team"]["away_team_name"] if is_home else m["home_team"]["home_team_name"]
            meta["is_home"] = is_home
            meta.update(stat)
            meta["high_stakes_tags"] = tag_high_stakes(meta)
            rows.append(meta)

    # ---- Champions League (Barcelona) ----
    for season_id in CL_SEASONS:
        mpath = SB / "matches" / "16" / f"{season_id}.json"
        if not mpath.exists():
            continue
        matches = json.loads(mpath.read_text())
        for m in matches:
            hid, aid = m["home_team"]["home_team_id"], m["away_team"]["away_team_id"]
            if BARCA_ID not in (hid, aid):
                continue
            stat = aggregate_messi(m["match_id"])
            if stat is None:
                continue
            meta = build_match_meta(m, "Champions League")
            is_home = hid == BARCA_ID
            meta["opponent"] = m["away_team"]["away_team_name"] if is_home else m["home_team"]["home_team_name"]
            meta["is_home"] = is_home
            meta.update(stat)
            meta["high_stakes_tags"] = tag_high_stakes(meta)
            rows.append(meta)

    # ---- Copa del Rey: check availability (expect none in Messi's era) ----
    copa_del_rey_seasons_available = []
    cdr_dir = SB / "matches" / "87"
    if cdr_dir.exists():
        for f in cdr_dir.glob("*.json"):
            matches = json.loads(f.read_text())
            for m in matches:
                copa_del_rey_seasons_available.append(m["season"]["season_name"])
    print(f"Copa del Rey seasons available in corpus: {sorted(set(copa_del_rey_seasons_available))}")

    # ---- Copa America 2024 (Argentina) ----
    mpath = SB / "matches" / "223" / "282.json"
    matches = json.loads(mpath.read_text())
    for m in matches:
        stat = aggregate_messi(m["match_id"])
        if stat is None:
            continue
        meta = build_match_meta(m, "Copa America 2024")
        is_home = stat["team_id"] == m["home_team"]["home_team_id"]
        meta["opponent"] = m["away_team"]["away_team_name"] if is_home else m["home_team"]["home_team_name"]
        meta["is_home"] = is_home
        meta.update(stat)
        meta["high_stakes_tags"] = tag_high_stakes(meta)
        rows.append(meta)

    # ---- MLS 2023 (Inter Miami) ----
    mpath = SB / "matches" / "44" / "107.json"
    matches = json.loads(mpath.read_text())
    for m in matches:
        stat = aggregate_messi(m["match_id"])
        if stat is None:
            continue
        meta = build_match_meta(m, "MLS 2023")
        is_home = stat["team_id"] == m["home_team"]["home_team_id"]
        meta["opponent"] = m["away_team"]["away_team_name"] if is_home else m["home_team"]["home_team_name"]
        meta["is_home"] = is_home
        meta.update(stat)
        meta["high_stakes_tags"] = tag_high_stakes(meta)
        rows.append(meta)

    rows.sort(key=lambda r: r["match_date"])

    # ---- write CSV ----
    import csv
    cols = ["match_id", "match_date", "competition", "season", "stage", "opponent",
            "is_home", "home_team", "away_team", "home_score", "away_score",
            "is_starter", "minutes_played", "shots", "shots_on_target", "goals",
            "high_stakes_tags"]
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            rr = dict(r)
            rr["high_stakes_tags"] = ";".join(rr["high_stakes_tags"])
            w.writerow({k: rr.get(k) for k in cols})
    print(f"Wrote {len(rows)} Messi-appearance rows to {OUT_CSV}")

    # ---- summary stats ----
    def rate_ci(n, k):
        """Wilson 95% CI for k/n."""
        if n == 0:
            return (None, None, None)
        p = k / n
        z = 1.96
        denom = 1 + z**2 / n
        center = (p + z**2 / (2 * n)) / denom
        half = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
        return (p, max(0.0, center - half), min(1.0, center + half))

    print("\n=== Match universe counts ===")
    print("La Liga (Barcelona, Messi appeared):", sum(1 for r in rows if r["competition"] == "La Liga"))
    print("Champions League (Barcelona, Messi appeared):", sum(1 for r in rows if r["competition"] == "Champions League"))
    print("  CL stages present:", sorted(set(r["stage"] for r in rows if r["competition"] == "Champions League")))
    print("Copa America 2024 (Messi appeared):", sum(1 for r in rows if r["competition"] == "Copa America 2024"))
    print("MLS 2023 (Messi appeared):", sum(1 for r in rows if r["competition"] == "MLS 2023"))

    print("\n=== High-stakes tag counts ===")
    tag_counts = defaultdict(int)
    tag_goals = defaultdict(int)
    for r in rows:
        for t in r["high_stakes_tags"]:
            tag_counts[t] += 1
            tag_goals[t] += 1 if r["goals"] >= 1 else 0
    for t in sorted(tag_counts):
        n, k = tag_counts[t], tag_goals[t]
        p, lo, hi = rate_ci(n, k)
        print(f"  {t}: n={n}, scored 1+={k}, rate={p:.3f}, 95% CI=[{lo:.3f},{hi:.3f}]" if n else f"  {t}: n=0")

    print("\n=== High-stakes (any tag, La Liga+CL+CopaAmerica universe) vs regular ===")
    hs_rows = [r for r in rows if r["high_stakes_tags"] and r["competition"] in ("La Liga", "Champions League", "Copa America 2024")]
    reg_rows = [r for r in rows if not r["high_stakes_tags"] and r["competition"] in ("La Liga", "Champions League")]
    n_hs, k_hs = len(hs_rows), sum(1 for r in hs_rows if r["goals"] >= 1)
    n_reg, k_reg = len(reg_rows), sum(1 for r in reg_rows if r["goals"] >= 1)
    p_hs, lo_hs, hi_hs = rate_ci(n_hs, k_hs)
    p_reg, lo_reg, hi_reg = rate_ci(n_reg, k_reg)
    print(f"High-stakes: n={n_hs}, scored 1+={k_hs}, rate={p_hs:.4f}, 95% CI=[{lo_hs:.4f},{hi_hs:.4f}]")
    print(f"Regular:     n={n_reg}, scored 1+={k_reg}, rate={p_reg:.4f}, 95% CI=[{lo_reg:.4f},{hi_reg:.4f}]")

    # two-proportion z-test
    p_pool = (k_hs + k_reg) / (n_hs + n_reg)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_hs + 1 / n_reg))
    z = (p_hs - p_reg) / se if se > 0 else float("nan")
    # two-sided p-value via normal CDF approx (erf)
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    print(f"Two-proportion z-test: z={z:.3f}, p={p_value:.4f}")

    print("\n=== El Clasico specifically ===")
    clasico_rows = [r for r in rows if "El_Clasico" in r["high_stakes_tags"]]
    n_c, k_c = len(clasico_rows), sum(1 for r in clasico_rows if r["goals"] >= 1)
    p_c, lo_c, hi_c = rate_ci(n_c, k_c)
    print(f"n={n_c}, scored 1+={k_c}, rate={p_c:.4f}, 95% CI=[{lo_c:.4f},{hi_c:.4f}]")

    print("\n=== CL Final specifically ===")
    clf_rows = [r for r in rows if "CL_final" in r["high_stakes_tags"]]
    for r in clf_rows:
        print(f"  {r['match_date']} {r['home_team']} vs {r['away_team']}: goals={r['goals']}, shots={r['shots']}, SOT={r['shots_on_target']}, minutes={r['minutes_played']}")

    print("\n=== Copa America 2024 log ===")
    ca_rows = [r for r in rows if r["competition"] == "Copa America 2024"]
    for r in ca_rows:
        print(f"  {r['match_date']} {r['stage']:15s} vs {r['opponent']:12s}: starter={r['is_starter']}, min={r['minutes_played']}, shots={r['shots']}, SOT={r['shots_on_target']}, goals={r['goals']}")

    print("\n=== MLS 2023 (Inter Miami) log ===")
    mls_rows = [r for r in rows if r["competition"] == "MLS 2023"]
    for r in mls_rows:
        print(f"  {r['match_date']} vs {r['opponent']:12s}: starter={r['is_starter']}, min={r['minutes_played']}, shots={r['shots']}, SOT={r['shots_on_target']}, goals={r['goals']}")


if __name__ == "__main__":
    main()
