"""
Build two panels the project has never had before, to fix two gaps flagged in
matches/Spain_vs_Belgium/DATA_SCOPING_MEMO.md:

  1. data/processed/halftime_sub_panel.csv
     One row per WC2026 match with a saved full ESPN summary dump on disk.
     Extracted from `keyEvents` (type=='substitution'): did either team make a
     substitution in the immediate second-half-restart window (period 2,
     clock value <= HALFTIME_WINDOW_SEC)? Answers question 4 ("Will either
     team make a substitution at halftime?") with an actual base rate instead
     of nothing.

  2. topics/cards/referee_card_panel.csv
     One row per match: referee full name (from `gameInfo.officials`), total
     match cards (yellow+red, both teams), and stage. Answers question 15's
     card component with an aggregated per-referee card-rate table instead of
     nothing -- though note this match's own referee is not yet known (ESPN
     has no `gameInfo.officials` for a STATUS_SCHEDULED fixture), so this
     table is useful context/infrastructure, not a direct point estimate for
     Spain vs Belgium specifically.

Source data: every matches/*/espn_*.json file that is a full summary-endpoint
dump (has both 'keyEvents' and 'gameInfo' keys) -- NOT the stripped
espn_match_summary_raw.json files, which lack keyEvents/gameInfo. The same
underlying ESPN event often appears twice on disk (once per team's match
folder, e.g. event 760419 saved as both
matches/Brazil_vs_Norway/espn_bra_760419.json and
matches/Canada_vs_Morocco/espn_mar_760419.json) -- deduped by header event id.

HALFTIME_WINDOW_SEC=47*60 was picked by inspecting the actual observed clock
values for all 643 period-2 substitutions across the corpus: there is a clean
bimodal gap, not a fuzzy boundary -- 74 subs sit at exactly clock==2700.0
(45'00", the whistle for kickoff of the second half) and literally none fall
between 2700 and 3223 (53'43"), where the next cluster of genuine in-half
tactical/injury subs begins. Any threshold between 2701 and 3222 gives an
identical result; 2820 (47') was chosen with margin, not because it's doing
real work.

Caveat printed at the end of main(): sample is WC2026-only, and not
comprehensive -- only matches whose 4 group/knockout ESPN dumps happened to
get saved during earlier case studies are included (~30-40 unique matches out
of ~90 played so far). Treat rates as directional, not precise, especially
once split by stage.
"""

import glob
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HALFTIME_WINDOW_SEC = 47 * 60  # 47'00" -- see docstring for calibration note

OUT_SUB = ROOT / "data" / "processed" / "halftime_sub_panel.csv"
OUT_REF = ROOT / "topics" / "cards" / "referee_card_panel.csv"


def find_full_dumps():
    paths = glob.glob(str(ROOT / "matches" / "*" / "espn_*.json"))
    out = []
    for p in paths:
        if p.endswith("_match_summary_raw.json"):
            continue
        try:
            data = json.load(open(p))
        except Exception:
            continue
        if "keyEvents" in data and "gameInfo" in data:
            out.append((p, data))
    return out


def main():
    dumps = find_full_dumps()
    print(f"Found {len(dumps)} candidate full-dump files")

    by_event = {}
    for path, data in dumps:
        header = data.get("header", {})
        eid = header.get("id")
        if eid is None:
            continue
        if eid in by_event:
            continue  # dedupe -- same match saved from the other team's folder
        by_event[eid] = (path, data)

    print(f"{len(by_event)} unique ESPN events after dedupe")

    sub_rows = []
    ref_rows = []

    for eid, (path, data) in sorted(by_event.items()):
        header = data.get("header", {})
        season = header.get("season", {}) or {}
        stage = season.get("name", "unknown")
        comp = header.get("competitions", [{}])[0]
        date = comp.get("date", "")[:10]
        teams = [c["team"]["displayName"] for c in comp.get("competitors", [])]
        match_label = " vs ".join(teams) if teams else path

        key_events = data.get("keyEvents", []) or []

        halftime_sub = False
        halftime_sub_teams = []
        total_cards = 0
        for ev in key_events:
            etype = ev.get("type", {}).get("type", "")
            period = ev.get("period", {}).get("number")
            clock = ev.get("clock", {}).get("value")
            if etype == "substitution" and period == 2 and clock is not None and clock <= HALFTIME_WINDOW_SEC:
                halftime_sub = True
                team = ev.get("team", {}).get("displayName", "?")
                if team not in halftime_sub_teams:
                    halftime_sub_teams.append(team)
            if etype in ("yellow-card", "red-card"):
                total_cards += 1

        sub_rows.append({
            "event_id": eid,
            "date": date,
            "match": match_label,
            "stage": stage,
            "halftime_sub": int(halftime_sub),
            "halftime_sub_teams": "|".join(halftime_sub_teams),
        })

        officials = data.get("gameInfo", {}).get("officials", [])
        referee = officials[0].get("fullName") if officials else None
        ref_rows.append({
            "event_id": eid,
            "date": date,
            "match": match_label,
            "stage": stage,
            "referee": referee,
            "total_cards": total_cards,
        })

    # --- write panels ---
    import csv
    with open(OUT_SUB, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["event_id", "date", "match", "stage", "halftime_sub", "halftime_sub_teams"])
        w.writeheader()
        w.writerows(sub_rows)

    with open(OUT_REF, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["event_id", "date", "match", "stage", "referee", "total_cards"])
        w.writeheader()
        w.writerows(ref_rows)

    # --- summary stats ---
    print(f"\nWrote {len(sub_rows)} rows to {OUT_SUB}")
    print(f"Wrote {len(ref_rows)} rows to {OUT_REF}")

    print("\n=== Halftime substitution base rate ===")
    by_stage = defaultdict(list)
    for r in sub_rows:
        by_stage[r["stage"]].append(r["halftime_sub"])
        by_stage["ALL"].append(r["halftime_sub"])
    for stage, vals in by_stage.items():
        rate = sum(vals) / len(vals)
        print(f"  {stage:40s} n={len(vals):3d}  rate={rate:.3f}")

    print("\n=== Referee card-rate table (matches with 2+ officiated games in this corpus) ===")
    ref_cards = defaultdict(list)
    for r in ref_rows:
        if r["referee"]:
            ref_cards[r["referee"]].append(r["total_cards"])
    for ref, cards in sorted(ref_cards.items(), key=lambda kv: -len(kv[1])):
        if len(cards) >= 2:
            avg = sum(cards) / len(cards)
            print(f"  {ref:25s} n={len(cards)}  matches={cards}  avg_cards={avg:.2f}")

    n_single = sum(1 for c in ref_cards.values() if len(c) == 1)
    print(f"\n({n_single} referees officiated only 1 match in this corpus -- excluded above, single-match rate is not a rate)")

    all_cards = [r["total_cards"] for r in ref_rows]
    print(f"\nOverall corpus card average (all matches, all referees): {sum(all_cards)/len(all_cards):.2f} (n={len(all_cards)})")


if __name__ == "__main__":
    main()
