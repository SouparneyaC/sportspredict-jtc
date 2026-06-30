"""
Pull all open matches + their markets from the SportsPredict Probability Cup
API and write them to disk immediately (one JSONL line per match's markets
response, written as we go -- never accumulate the full result set in RAM
before saving).

Output:
    bot/data/matches.json        -- raw /matches response
    bot/data/markets_raw.jsonl   -- one line per match: {"match_id": ..., "markets": [...]}

Usage:
    python3 fetch_markets.py
"""

import json
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
SECRETS = json.load(open(ROOT / "secrets.json"))
API_KEY = SECRETS["sportspredict_api_key"]
BASE_URL = "https://api.sportspredict.com/api/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


def main():
    resp = requests.get(f"{BASE_URL}/matches", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    matches = resp.json()
    with open(DATA_DIR / "matches.json", "w") as f:
        json.dump(matches, f, indent=2)
    print(f"Wrote {len(matches)} matches to data/matches.json")

    out_path = DATA_DIR / "markets_raw.jsonl"

    done_ids = set()
    if out_path.exists():
        with open(out_path) as f:
            for line in f:
                done_ids.add(json.loads(line)["match_id"])
        print(f"Resuming: {len(done_ids)} matches already fetched")

    with open(out_path, "a") as out:
        for i, m in enumerate(matches):
            if m["id"] in done_ids:
                continue
            mr = requests.get(f"{BASE_URL}/markets", headers=HEADERS,
                               params={"match_id": m["id"]}, timeout=30)
            if mr.status_code == 429:
                print("Rate limited, stopping early -- rerun to resume")
                break
            mr.raise_for_status()
            markets = mr.json()
            out.write(json.dumps({"match_id": m["id"], "match_name": m["name"],
                                   "opening_time": m["opening_time"],
                                   "closing_time": m["closing_time"],
                                   "markets": markets}) + "\n")
            out.flush()
            print(f"[{i+1}/{len(matches)}] {m['name']}: {len(markets)} markets")
            time.sleep(1.2)  # stay well under 60 req/min

    print(f"Wrote markets for {len(matches)} matches to {out_path}")


if __name__ == "__main__":
    main()
