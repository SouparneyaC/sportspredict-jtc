"""
Builds historical panels for the three genuinely no-market FRA-ESP questions
that the count-threshold hierarchical GLMM was never designed for:
  Q4  VAR on-field review (see caveat below -- flagged as likely unmeasurable
      from this data source, panel built anyway for the record)
  Q11 goal-timing-window (does a goal fall between this match's own 1st and
      2nd hydration break) -- CORRECTED: an earlier version of this script
      took the first two "Start Delay" events under 90' as the two hydration
      breaks, which silently included injury stoppages and other
      team-tagged delays (e.g. FRA-PAR's real break sequence was 23'
      drinks / 52' Paraguay injury / 66' France injury / 73' drinks -- the
      naive version picked 23'+52', truncating the true ~23'-73' window by
      21 minutes and mislabeling an injury stoppage as a hydration break).
      Caught via a back-of-envelope sanity check (a uniform-Poisson-timing
      estimate predicted ~72% for FRA-ESP's own window; the naive empirical
      rate across 100 matches came back 40%, an implausibly large gap) before
      it was ever reported. Fixed by filtering Start Delay events on their
      own text field, which ESPN unambiguously tags: "Delay in match for a
      drinks break." (214 occurrences, ~2/match, kept) vs "...because of an
      injury X" or "(TeamName)"-only tags (kept out).
  Q14 first-substitution race (which team subs first)

Reads: data/processed/espn_raw_events/*.json (all 100 WC2026 matches)
Writes: ml/backtests/rare_event_panel.csv (one row per match)

VAR caveat: ESPN's commentary feed only ever says "VAR Decision: X" -- it
never states whether the referee actually went to the pitchside monitor (an
on-field review, what Q4 asks about) versus a booth-only check without one.
Real-world protocol resolves most objective/factual calls (offside lines,
ball-out-of-play) via the booth alone; only closer subjective calls typically
get an on-field review. This data source cannot distinguish the two, so
`any_var_mention` here is a NECESSARY OVERCOUNT of true on-field reviews, not
a clean measurement of Q4's actual target. Documented, not hidden.

Usage:
    python3 build_rare_event_panels.py
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "processed" / "espn_raw_events"
OUT = ROOT / "ml" / "backtests" / "rare_event_panel.csv"

GOAL_TYPES = {"Goal", "Goal - Header", "Goal - Free Kick", "Penalty - Scored", "Own Goal"}


def clock_to_min(clock):
    m = re.match(r"(\d+)", clock or "")
    return int(m.group(1)) if m else None


def main():
    rows = []
    files = sorted(RAW_DIR.glob("*.json"))
    for f in files:
        d = json.load(open(f))
        comp = d.get("header", {}).get("competitions", [{}])[0]
        teams = {c["team"]["displayName"]: c for c in comp.get("competitors", [])}
        if len(teams) != 2:
            continue
        date = comp.get("date", "")[:10]
        eid = comp.get("id") or d.get("header", {}).get("id", "")
        status = comp.get("status", {}).get("type", {}).get("description", "")
        if "Final" not in status and "Full Time" not in status:
            continue  # skip unplayed/in-progress fixtures

        goals, delays, subs = [], [], {}
        var_mentions = 0
        for c in d.get("commentary", []):
            t = c.get("text", "")
            mn = clock_to_min(c.get("time", {}).get("displayValue", ""))
            if re.search(r"\bVAR\b", t, re.I):
                var_mentions += 1

        for ev in d.get("keyEvents", []):
            etype = ev.get("type", {}).get("text", "")
            team = ev.get("team", {}).get("displayName", "?")
            mn = clock_to_min(ev.get("clock", {}).get("displayValue", ""))
            if etype in GOAL_TYPES:
                goals.append(mn)
            elif etype == "Start Delay" and mn is not None and "drinks break" in ev.get("text", "").lower():
                delays.append(mn)
            elif etype == "Substitution" and team not in subs and mn is not None:
                subs[team] = mn

        delays = sorted(set(delays))
        # first two GENUINE hydration-break delays in regulation (<90')
        breaks = [m for m in delays if m < 90][:2]
        break1, break2 = (breaks + [None, None])[:2]

        goal_in_window = None
        if break1 is not None and break2 is not None:
            goal_in_window = any(break1 <= g < break2 for g in goals if g is not None)

        team_names = list(teams.keys())
        first_sub_team = min(subs, key=subs.get) if subs else None

        rows.append({
            "event_id": eid, "date": date, "team_a": team_names[0], "team_b": team_names[1],
            "n_goals": len(goals), "goal_minutes": ";".join(str(g) for g in goals if g is not None),
            "break1_min": break1, "break2_min": break2,
            "goal_between_breaks": goal_in_window,
            "team_a_first_sub_min": subs.get(team_names[0]),
            "team_b_first_sub_min": subs.get(team_names[1]),
            "first_sub_team": first_sub_team,
            "var_mentions": var_mentions, "any_var_mention": var_mentions > 0,
        })

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    n_with_breaks = sum(1 for r in rows if r["break1_min"] is not None and r["break2_min"] is not None)
    n_goal_between = sum(1 for r in rows if r["goal_between_breaks"] is True)
    n_var = sum(1 for r in rows if r["any_var_mention"])
    print(f"Matches processed: {n}")
    print(f"Matches with both hydration breaks detected: {n_with_breaks}")
    print(f"  Of those, goal fell between breaks: {n_goal_between}/{n_with_breaks} "
          f"({n_goal_between/n_with_breaks:.3f})" if n_with_breaks else "")
    print(f"Matches with any VAR mention: {n_var}/{n} ({n_var/n:.3f}) -- OVERCOUNT of true on-field reviews, see caveat")
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
