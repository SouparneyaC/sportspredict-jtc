"""
Reusable Smarkets team-prop-market fetcher, generalized from the one-off
fetch_fra_esp_smarkets.py so growing the live GLMM-vs-market comparison
(currently stuck at 11 matches, see topics/shots-on-target/sot_vs_market_comparison.py)
doesn't require hand-writing a new script per match. Discovers team-level
SOT/cards/corners markets by NAME PATTERN (not hardcoded market IDs), so it
works on any future match without editing.

Usage:
    python3 fetch_team_prop_markets.py <event_id> <team_a_name> <team_b_name>
    python3 fetch_team_prop_markets.py 45195225 England Argentina
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

BASE = "https://api.smarkets.com/v3"
OUT_DIR = Path(__file__).resolve().parent.parent / "ml" / "backtests" / "live_market_watch"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# team-level (not player-level) prop patterns worth tracking for the GLMM comparison
PATTERNS = [
    r"^[A-Za-z]+_SOT_OU",           # e.g. England_SOT_OU4.5
    r"^Total_SOT_OU",
    r"^[A-Za-z]+_corners_OU",
    r"^[A-Za-z]+ over/under \d+\.\d+ shots on target",
    r"^Cards_OU",
    r"^Over/under \d+\.\d+ corners",
    r"^Over/under \d+\.\d+ cards",
]


def discover_markets(event_id):
    r = requests.get(f"{BASE}/events/{event_id}/markets/", params={"limit": 1000}, timeout=30)
    r.raise_for_status()
    markets = r.json()["markets"]
    hits = []
    for m in markets:
        name = m["name"]
        if any(re.search(p, name) for p in PATTERNS) and "Player" not in name:
            hits.append(m)
    return hits


def get_quote(market_id):
    r1 = requests.get(f"{BASE}/markets/{market_id}/contracts/", timeout=20)
    r1.raise_for_status()
    contracts = {c["id"]: c["name"] for c in r1.json()["contracts"]}
    r2 = requests.get(f"{BASE}/markets/{market_id}/quotes/", timeout=20)
    r2.raise_for_status()
    quotes = r2.json()
    out = {}
    for cid, q in quotes.items():
        name = contracts.get(cid, cid)
        bids, offers = q.get("bids", []), q.get("offers", [])
        bid = bids[0]["price"] / 10000 if bids else None
        offer = offers[0]["price"] / 10000 if offers else None
        mid = (bid + offer) / 2 if (bid is not None and offer is not None) else (bid or offer)
        out[name] = {"bid": bid, "offer": offer, "mid": mid}
    return out


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    event_id, team_a, team_b = sys.argv[1], sys.argv[2], sys.argv[3]

    print(f"Discovering team-prop markets for event {event_id}...")
    markets = discover_markets(event_id)
    print(f"Found {len(markets)} team-level prop markets:")
    for m in markets:
        print(f"  {m['id']}  {m['name']}")

    result = {"event_id": event_id, "team_a": team_a, "team_b": team_b,
              "fetched_markets": {}}
    for m in markets:
        try:
            result["fetched_markets"][m["name"]] = {"market_id": m["id"], "quotes": get_quote(m["id"])}
            print(f"  fetched: {m['name']}")
        except Exception as e:
            print(f"  [ERR] {m['name']}: {e}")
        time.sleep(1.0)

    out_path = OUT_DIR / f"event_{event_id}_{team_a}_{team_b}.json".replace(" ", "_")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
