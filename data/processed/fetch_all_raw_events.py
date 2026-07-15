"""
Fetch raw ESPN event summaries (full keyEvents timeline: goals, cards, subs,
VAR decisions, delays) for all 100 WC2026 matches, not just the 12 already
saved for France/Spain. This is the event-level detail espn_match_panel.csv
does NOT carry (that file is aggregated team totals only) -- needed to build
historical panels for rare-event/timing/race-type questions (VAR reviews,
goal-timing windows, first-substitution race) that the count-threshold
hierarchical GLMM was never designed to answer.

Output: data/processed/espn_raw_events/espn_event_{id}.json (one per match,
skips files that already exist so this is safely re-runnable/resumable).

Usage:
    python3 fetch_all_raw_events.py
"""
import csv
import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data" / "processed" / "espn_match_panel.csv"
OUT_DIR = ROOT / "data" / "processed" / "espn_raw_events"
OUT_DIR.mkdir(exist_ok=True)

# already-copied files use the old naming pattern (espn_TAG_ID.json); build a
# set of event IDs already present under ANY naming pattern
existing_ids = set()
for f in OUT_DIR.glob("*.json"):
    for part in f.stem.split("_"):
        if part.isdigit() and len(part) == 6:
            existing_ids.add(part)

event_ids = sorted({row["event_id"] for row in csv.DictReader(open(PANEL))}, key=int)
todo = [e for e in event_ids if e not in existing_ids]
print(f"{len(event_ids)} total matches, {len(existing_ids)} already fetched, {len(todo)} to fetch")

for i, eid in enumerate(todo, 1):
    out = OUT_DIR / f"espn_event_{eid}.json"
    try:
        r = requests.get(
            "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary",
            params={"event": eid}, timeout=30)
        r.raise_for_status()
        with open(out, "w") as f:
            json.dump(r.json(), f)
        print(f"[{i}/{len(todo)}] {eid} saved")
    except Exception as e:
        print(f"[{i}/{len(todo)}] {eid} FAILED: {e}")
    time.sleep(0.6)

print("Done.")
