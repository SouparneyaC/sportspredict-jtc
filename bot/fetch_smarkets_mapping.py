"""
Build a one-time mapping of Smarkets World Cup 2026 events -> their full
market list (id + name only, no prices) for all 71 fixtures.

This is metadata-only (cheap: 1 call for the event list + 1 call per match
for its ~200 markets = ~72 calls total). Live prices are fetched separately,
on demand, by fetch_smarkets_prices.py using the market ids saved here.

Output: bot/data/external/smarkets_markets_by_match.jsonl
  one line per match: {"event_id", "name", "start_date", "markets": [{"id","name"}, ...]}

Usage:
    python3 fetch_smarkets_mapping.py
"""

import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
OUT_DIR = ROOT / "data" / "external"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / "smarkets_markets_by_match.jsonl"

BASE = "https://api.smarkets.com/v3"
WC2026_PARENT_ID = "42791414"


def main():
    resp = requests.get(f"{BASE}/events/", params={
        "type": "football_match", "parent_id": WC2026_PARENT_ID, "limit": 1000
    }, timeout=30)
    resp.raise_for_status()
    events = resp.json()["events"]
    print(f"Found {len(events)} WC2026 events")

    done_ids = set()
    if OUT_PATH.exists():
        with open(OUT_PATH) as f:
            for line in f:
                done_ids.add(json.loads(line)["event_id"])
        print(f"Resuming: {len(done_ids)} already fetched")

    with open(OUT_PATH, "a") as out:
        for i, e in enumerate(events):
            if e["id"] in done_ids:
                continue
            mr = requests.get(f"{BASE}/events/{e['id']}/markets/",
                               params={"limit": 1000}, timeout=30)
            mr.raise_for_status()
            markets = [{"id": m["id"], "name": m["name"]} for m in mr.json()["markets"]]
            out.write(json.dumps({
                "event_id": e["id"],
                "name": e["name"],
                "start_date": e["start_date"],
                "markets": markets,
            }) + "\n")
            out.flush()
            print(f"[{i+1}/{len(events)}] {e['name']}: {len(markets)} markets")
            time.sleep(0.3)

    print(f"Wrote mapping to {OUT_PATH}")


if __name__ == "__main__":
    main()
