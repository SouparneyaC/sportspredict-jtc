"""
Builds topics/cards/card_timing_panel.csv: per-match, per-team card TIMING data
(minute, team, card type for every card), filling the gap referee_card_panel.csv
leaves open -- that panel only has TOTAL cards per match, no per-team split and
no timing, which is not enough to price:
  Q8  "Will both teams receive at least one card?"        (needs per-team split)
  Q10 "Will a card be shown before the first goal?"        (needs card minute vs goal minute)

Source: data/processed/espn_raw_events/*.json -- the SAME 100-match corpus
`ml/backtests/build_rare_event_panels.py` already reads to build
`ml/backtests/rare_event_panel.csv` (confirmed by direct comparison: every
event_id findable under matches/*/ with a full keyEvents+header dump -- 65
unique ids across espn_<team>_<id>.json / 01_espn_data.json / etc. naming
conventions -- is already a strict subset of the 101 files here, so no
additional matches are gained by also parsing matches/*/; this directory is
already the comprehensive, canonical source). Only matches whose ESPN status
is Final/Full Time/AET/Pens are kept (one file, the France vs Spain SF, is a
pre-match "Scheduled" stub with no keyEvents and is correctly dropped by this
filter). Result: 100 usable matches.

Card event types actually present in this corpus's keyEvents (checked
directly): "yellow-card" (256 occurrences), "red-card" (14), and one instance
of "var---red-card-upgrade" (1, event 760417, Tim Ream/USA vs Paraguay 52') --
inspected directly: no separate yellow-card event exists for that player in
that match, so this is ESPN's tag for a straight red issued after a VAR
review, not a yellow being upgraded on top of an already-counted yellow. It is
counted here as one red card. All three types count toward "at least one
card" / both-teams-carded; a genuine second-yellow-then-red for the same
player would double count under this scheme (one yellow-card event + one
red-card event, both real events in ESPN's own feed) -- that is correct
behavior, not a bug: a match where a player is booked then sent off has
"a card" shown twice, by two separate, real refereeing actions.

Timing precision note (load-bearing for Q7/Q10 in the backtest script, not
used directly in this panel but documented here since it was discovered while
building it): ESPN's `clock.value` (raw seconds) is PINNED to the exact
period-boundary value (2700.0 for first half, 5400.0 for second half, 6300.0/
7200.0 for ET halves) for essentially every event tagged with a "+" stoppage
suffix in `clock.displayValue` (473/502 stoppage-tagged events across ALL
event types checked directly, not just cards -- goals, cards, subs, delays
alike). The seconds field is therefore NOT usable to distinguish stoppage-time
events by magnitude; the human-readable displayValue text (e.g. "45'+3'") is
the only reliable source for whether an event fell in stoppage time and, if
so, how far into it. This panel stores both the truncated base minute (int,
same convention as rare_event_panel.csv's goal_minutes -- leading digits of
displayValue only) AND the raw displayValue string for every card, so the
backtest script can do exact same-minute-tie-breaking against goal events
using the "+N" offset without re-deriving it from clock.value.

Scope: "regulation" only (period 1 and 2), matching every one of tonight's
question wordings ("... in regulation (90 minutes + stoppage time)"). Cards
shown in extra time (period 3/4) or during a penalty shootout (period 5) are
parsed but excluded from the panel's counts, consistent with what Q8/Q10 ask.

Usage:
    python3 card_timing_panel.py
"""
import csv
import glob
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "processed" / "espn_raw_events"
OUT = ROOT / "topics" / "cards" / "card_timing_panel.csv"

CARD_TYPES = {"yellow-card", "red-card", "var---red-card-upgrade"}
REGULATION_PERIODS = {1, 2}


def base_minute(display_value):
    """Leading digit group of e.g. '45'+3'' -> 45. Same convention as
    build_rare_event_panels.py's clock_to_min()."""
    m = re.match(r"(\d+)", display_value or "")
    return int(m.group(1)) if m else None


def main():
    files = sorted(RAW_DIR.glob("*.json"))
    rows = []
    n_zero_card_matches = 0

    for f in files:
        d = json.load(open(f))
        header = d.get("header", {})
        comp = header.get("competitions", [{}])[0]
        status = comp.get("status", {}).get("type", {}).get("description", "")
        if "Final" not in status and "Full Time" not in status:
            continue  # drop unplayed/scheduled stubs (e.g. the FRA-ESP pre-match file)

        teams = {c["team"]["displayName"]: c for c in comp.get("competitors", [])}
        if len(teams) != 2:
            continue
        team_names = list(teams.keys())
        team_a, team_b = team_names[0], team_names[1]
        date = comp.get("date", "")[:10]
        eid = comp.get("id") or header.get("id", "")
        season = header.get("season", {}) or {}
        stage = season.get("name", "unknown")

        card_events = []  # (base_min, team, card_type, display_value)
        for ev in d.get("keyEvents", []) or []:
            etype = ev.get("type", {}).get("type", "")
            period = ev.get("period", {}).get("number")
            if etype not in CARD_TYPES or period not in REGULATION_PERIODS:
                continue
            dv = ev.get("clock", {}).get("displayValue", "")
            bm = base_minute(dv)
            team = ev.get("team", {}).get("displayName", "?")
            card_events.append((bm, team, etype, dv))

        card_events.sort(key=lambda t: (t[0] if t[0] is not None else 999))

        n_a = sum(1 for c in card_events if c[1] == team_a)
        n_b = sum(1 for c in card_events if c[1] == team_b)
        n_total = len(card_events)
        if n_total == 0:
            n_zero_card_matches += 1

        first = card_events[0] if card_events else (None, None, None, None)

        rows.append({
            "event_id": eid,
            "date": date,
            "team_a": team_a,
            "team_b": team_b,
            "stage": stage,
            "n_cards_team_a": n_a,
            "n_cards_team_b": n_b,
            "n_cards_total": n_total,
            "both_teams_carded": n_a >= 1 and n_b >= 1,
            "card_events": ";".join(f"{c[0]}|{c[1]}|{c[2]}|{c[3]}" for c in card_events),
            "first_card_min": first[0],
            "first_card_team": first[1],
            "first_card_type": first[2],
            "first_card_display": first[3],
        })

    fieldnames = [
        "event_id", "date", "team_a", "team_b", "stage",
        "n_cards_team_a", "n_cards_team_b", "n_cards_total", "both_teams_carded",
        "card_events", "first_card_min", "first_card_team", "first_card_type", "first_card_display",
    ]
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    n = len(rows)
    n_both = sum(1 for r in rows if r["both_teams_carded"])
    print(f"Matches processed: {n}")
    print(f"Zero-card matches: {n_zero_card_matches}/{n} ({n_zero_card_matches/n:.3f})")
    print(f"Both-teams-carded: {n_both}/{n} ({n_both/n:.3f})")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
