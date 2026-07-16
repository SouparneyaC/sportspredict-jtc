"""
Alvarez high-stakes-vs-regular 1+SOT deep dive, for ENG-ARG WC2026 SF Q1
("Will Julian Alvarez have 1+ shots on target in regulation?").

Combines:
  (a) Copa America 2024 (Argentina), local StatsBomb open-data,
      competition_id=223, season_id=282, player_id=29560 (confirmed from the
      data itself: lineup for match 3939969 lists "Julian Alvarez", jersey 9).
  (b) Manchester City (Jan 2022 - Jul 2024) + Atletico Madrid (Jul 2024 -
      present) club career, live ESPN pull -- 15_alvarez_club_career_espn.json,
      built by 15_alvarez_club_career_fetch.py.

No local StatsBomb coverage of Alvarez's actual career exists: River Plate is
only covered for Liga Profesional (competition_id=81) seasons 1997/98 and
1981 (decades before Alvarez), and Premier League (competition_id=2) local
coverage is only 2015/16 and 2003/04 (also wrong era) -- confirmed by direct
inspection of competitions.json, not assumed. La Liga (competition_id=11)
local coverage stops at 2020/21, years before Alvarez's July 2024 Atletico
Madrid arrival. Hence club career must come entirely from the live ESPN pull.

Pre-registered high-stakes criteria (stated before computing anything, same
discipline as 14_messi_high_stakes_deep_dive.py's precedent):
  1. UCL knockout (R16 onward, leg-tie matches identified by ESPN's own
     "1st Leg"/"2nd Leg" note, plus the Final) -- both club eras.
  2. UCL Final specifically (2023, Man City) -- subset of (1).
  3. Domestic knockout cup: FA Cup + League Cup (Man City), Copa del Rey
     (Atletico Madrid) -- these are single-elimination competitions
     throughout the rounds Alvarez appeared in.
  4. One-off showcase/trophy matches: Club World Cup Final, UEFA Super Cup,
     Community Shield, Spanish Super Cup.
  5. Premier League "rival" games (opponent in {Liverpool, Arsenal,
     Manchester United}) while at Man City.
  6. La Liga Madrid derby (opponent == Real Madrid) while at Atletico Madrid.
  7. Copa America 2024 knockout (Quarter-finals, Semi-finals, Final) for
     Argentina.
"regular" = Premier League/La Liga/UCL-group-or-league-phase matches with none
of the above tags (the closest analogue to 14_messi_...'s "La Liga+CL,
no high-stakes tag" bucket).

SOT convention: ESPN's shotsOnTarget field. Verified against known
ground truth before trusting it (see companion .md): 2023 FA Cup Final
(Man City 2-1 Man Utd, real) and 2023 Club World Cup Final (Man City 4-0
Fluminense, Alvarez scored twice, real, well-known) both match exactly.

Output: 15_alvarez_full_log.csv (row per match, both sources combined),
printed summary stats consumed by the companion .md.
"""
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SB = ROOT / "data" / "external" / "statsbomb" / "open-data" / "data"
OUT_DIR = Path(__file__).resolve().parent
OUT_CSV = OUT_DIR / "15_alvarez_full_log.csv"
ESPN_JSON = OUT_DIR / "15_alvarez_club_career_espn.json"

ALVAREZ_SB_ID = 29560
SOT_OUTCOMES = {"Goal", "Saved", "Saved To Post"}

PL_RIVALS = {"Liverpool", "Arsenal", "Manchester United"}


def parse_clock(s):
    mm, ss = s.split(":")
    return int(mm) + int(ss) / 60.0


def match_end_minute(events):
    events = [e for e in events if e.get("period", 1) != 5]
    return max((e["minute"] + e["second"] / 60.0 for e in events), default=90.0)


def aggregate_alvarez_sb(match_id):
    ev_path = SB / "events" / f"{match_id}.json"
    lu_path = SB / "lineups" / f"{match_id}.json"
    if not ev_path.exists() or not lu_path.exists():
        return None
    events = json.loads(ev_path.read_text())
    lineups = json.loads(lu_path.read_text())

    found, positions, team_id, team_name = False, None, None, None
    for team_entry in lineups:
        for p in team_entry["lineup"]:
            if p["player_id"] == ALVAREZ_SB_ID:
                found = True
                positions = p.get("positions", [])
                team_id, team_name = team_entry["team_id"], team_entry["team_name"]
    if not found:
        return None

    m_end = match_end_minute(events)
    if positions:
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
        if not player or player.get("id") != ALVAREZ_SB_ID:
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


def build_copa_america_rows():
    rows = []
    mpath = SB / "matches" / "223" / "282.json"
    matches = json.loads(mpath.read_text())
    for m in matches:
        stat = aggregate_alvarez_sb(m["match_id"])
        if stat is None or stat["minutes_played"] <= 0:
            continue
        is_home = stat["team_id"] == m["home_team"]["home_team_id"]
        opponent = m["away_team"]["away_team_name"] if is_home else m["home_team"]["home_team_name"]
        stage = m.get("competition_stage", {}).get("name")
        tags = []
        if stage in ("Quarter-finals", "Semi-finals", "Final"):
            tags.append("CopaAmerica2024_knockout")
        rows.append({
            "source": "StatsBomb",
            "match_id": m["match_id"],
            "date": m["match_date"],
            "competition": "Copa America 2024",
            "stage_or_round": stage,
            "opponent": opponent,
            "is_starter": stat["is_starter"],
            "shots": stat["shots"],
            "sot": stat["shots_on_target"],
            "goals": stat["goals"],
            "valid_stats": True,
            "high_stakes_tags": tags,
        })
    return rows


def classify_knockout_leg(comp, leg_headline):
    return comp == "Champions League" and bool(leg_headline)


def classify_ucl_final(comp, leg_headline, date):
    # Finals have no "Leg" note and fall in May/June; identified alongside
    # knockout-leg matches as the terminal, single-match round.
    if comp != "Champions League" or leg_headline:
        return False
    month = int(date[5:7]) if date else 0
    return month in (5, 6)


def tag_espn_row(r):
    tags = []
    comp = r["competition"]
    era = r["club_era"]
    opp = r.get("opponent") or ""
    leg = r.get("leg_headline")
    date = r.get("date")

    ucl_knockout = classify_knockout_leg(comp, leg)
    ucl_final = classify_ucl_final(comp, leg, date)
    if ucl_knockout or ucl_final:
        tags.append("UCL_knockout_R16plus")
    if ucl_final:
        tags.append("UCL_final")
    if comp in ("FA Cup", "League Cup", "Copa del Rey"):
        tags.append("Domestic_cup_knockout")
    if comp in ("Club World Cup", "UEFA Super Cup", "Community Shield", "Spanish Super Cup"):
        tags.append("Oneoff_final_trophy")
    if era == "Man City" and comp == "Premier League" and opp in PL_RIVALS:
        tags.append("PL_rival")
    if era == "Atletico Madrid" and comp == "La Liga" and opp == "Real Madrid":
        tags.append("LaLiga_Madrid_derby")
    return tags


def build_espn_rows():
    raw = json.loads(ESPN_JSON.read_text())
    rows = []
    n_dropped_unused_sub = 0
    n_dropped_ambiguous_bench = 0
    n_kept_started_no_stats = 0
    for r in raw:
        app = r.get("appearances")
        starter = r.get("starter")
        if app in (0.0, 0):
            n_dropped_unused_sub += 1
            continue  # unambiguous unused substitute -- dropped, not zero-filled (same discipline as Messi's Copa America DNP row)
        if app is None and starter is not True:
            n_dropped_ambiguous_bench += 1
            continue  # appearances field missing AND not a confirmed starter -- can't distinguish
            # "came on and played" from "unused bench" for this competition's sparse ESPN records;
            # dropped rather than guessed, matching this project's join-safety/no-guessing discipline
        if app is None and starter is True:
            n_kept_started_no_stats += 1
            # confirmed starter (played at least some regulation minutes) but ESPN's per-match
            # stats object is empty for this competition (FA Cup / Copa del Rey gap, see companion .md
            # section 2) -- kept in the log (participation confirmed) but valid_stats=False so it is
            # excluded from the SOT rate calculation below, not zero-filled.
        valid = r.get("sot") is not None
        rows.append({
            "source": "ESPN",
            "match_id": r["event_id"],
            "date": r["date"],
            "competition": r["competition"],
            "stage_or_round": r.get("leg_headline") or r["club_era"],
            "opponent": r.get("opponent"),
            "is_starter": r.get("starter"),
            "shots": r.get("shots"),
            "sot": r.get("sot"),
            "goals": r.get("goals"),
            "valid_stats": valid,
            "high_stakes_tags": tag_espn_row(r),
        })
    print(f"[ESPN row filtering] dropped {n_dropped_unused_sub} unambiguous unused-sub rows "
          f"(appearances=0), dropped {n_dropped_ambiguous_bench} ambiguous bench rows "
          f"(appearances=None, not a confirmed starter), kept {n_kept_started_no_stats} "
          f"confirmed-starter rows with missing stats objects (excluded from rate calc, logged).")
    return rows


def rate_ci(n, k):
    if n == 0:
        return (None, None, None)
    p = k / n
    z = 1.96
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return (p, max(0.0, center - half), min(1.0, center + half))


def main():
    rows = build_copa_america_rows() + build_espn_rows()
    rows.sort(key=lambda r: r["date"] or "")

    cols = ["source", "match_id", "date", "competition", "stage_or_round", "opponent",
            "is_starter", "shots", "sot", "goals", "valid_stats", "high_stakes_tags"]
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            rr = dict(r)
            rr["high_stakes_tags"] = ";".join(rr["high_stakes_tags"])
            w.writerow({k: rr.get(k) for k in cols})
    print(f"Wrote {len(rows)} rows to {OUT_CSV}")

    print("\n=== Match universe counts (played, appearances confirmed) ===")
    from collections import Counter
    print(Counter(r["competition"] for r in rows))

    valid_rows = [r for r in rows if r["valid_stats"]]
    missing_rows = [r for r in rows if not r["valid_stats"]]
    print(f"\nRows with usable shot/SOT stats: {len(valid_rows)}")
    print(f"Rows played but MISSING shot/SOT stats (excluded from rate calc, logged not zero-filled): {len(missing_rows)}")
    print(Counter(r["competition"] for r in missing_rows))

    print("\n=== High-stakes tag counts (1+SOT rate) ===")
    tag_counts, tag_hits = {}, {}
    for r in valid_rows:
        for t in r["high_stakes_tags"]:
            tag_counts[t] = tag_counts.get(t, 0) + 1
            tag_hits[t] = tag_hits.get(t, 0) + (1 if r["sot"] and r["sot"] >= 1 else 0)
    for t in sorted(tag_counts):
        n, k = tag_counts[t], tag_hits[t]
        p, lo, hi = rate_ci(n, k)
        print(f"  {t}: n={n}, 1+SOT={k}, rate={p:.3f}, 95% CI=[{lo:.3f},{hi:.3f}]")

    print("\n=== High-stakes (any tag) vs regular (untagged league/UCL-group matches) ===")
    hs_rows = [r for r in valid_rows if r["high_stakes_tags"]]
    reg_rows = [r for r in valid_rows if not r["high_stakes_tags"]
                and r["competition"] in ("Premier League", "La Liga", "Champions League")]
    n_hs, k_hs = len(hs_rows), sum(1 for r in hs_rows if r["sot"] and r["sot"] >= 1)
    n_reg, k_reg = len(reg_rows), sum(1 for r in reg_rows if r["sot"] and r["sot"] >= 1)
    p_hs, lo_hs, hi_hs = rate_ci(n_hs, k_hs)
    p_reg, lo_reg, hi_reg = rate_ci(n_reg, k_reg)
    print(f"High-stakes: n={n_hs}, 1+SOT={k_hs}, rate={p_hs:.4f}, 95% CI=[{lo_hs:.4f},{hi_hs:.4f}]")
    print(f"Regular:     n={n_reg}, 1+SOT={k_reg}, rate={p_reg:.4f}, 95% CI=[{lo_reg:.4f},{hi_reg:.4f}]")

    if n_hs > 0 and n_reg > 0:
        p_pool = (k_hs + k_reg) / (n_hs + n_reg)
        se = math.sqrt(p_pool * (1 - p_pool) * (1 / n_hs + 1 / n_reg))
        z = (p_hs - p_reg) / se if se > 0 else float("nan")
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
        print(f"Two-proportion z-test: z={z:.3f}, p={p_value:.4f}")

    print("\n=== Copa America 2024 log ===")
    for r in rows:
        if r["competition"] == "Copa America 2024":
            print(f"  {r['date']} {r['stage_or_round']:15s} vs {r['opponent']:12s}: starter={r['is_starter']}, "
                  f"shots={r['shots']}, SOT={r['sot']}, goals={r['goals']}, tags={r['high_stakes_tags']}")

    print("\n=== Overall club-career 1+SOT rate (all valid rows, Man City + Atletico combined) ===")
    club_rows = [r for r in valid_rows if r["source"] == "ESPN"]
    n_c, k_c = len(club_rows), sum(1 for r in club_rows if r["sot"] and r["sot"] >= 1)
    p_c, lo_c, hi_c = rate_ci(n_c, k_c)
    print(f"n={n_c}, 1+SOT={k_c}, rate={p_c:.4f}, 95% CI=[{lo_c:.4f},{hi_c:.4f}]")

    print("\n=== Man City era vs Atletico Madrid era (regular matches only) ===")
    for era in ("Man City", "Atletico Madrid"):
        era_rows = [r for r in reg_rows if r["source"] == "ESPN"]
    # redo properly with era info retained
    raw = json.loads(ESPN_JSON.read_text())
    era_map = {str(r["event_id"]): r["club_era"] for r in raw}
    for era in ("Man City", "Atletico Madrid"):
        era_rows = [r for r in reg_rows if era_map.get(str(r["match_id"])) == era]
        n_e, k_e = len(era_rows), sum(1 for r in era_rows if r["sot"] and r["sot"] >= 1)
        p_e, lo_e, hi_e = rate_ci(n_e, k_e)
        if n_e:
            print(f"  {era} (regular only): n={n_e}, 1+SOT={k_e}, rate={p_e:.4f}, 95% CI=[{lo_e:.4f},{hi_e:.4f}]")


if __name__ == "__main__":
    main()
