"""
One-off, read-only exploration script: tests a short curated list of plausible
API endpoints (docs/schema routes first, then leaderboard/rank/settled-results
candidates) against the SportsPredict API to find out what's actually exposed
beyond the two endpoints already in use (/matches, /markets).

Writes every response (or error) to disk immediately as it goes, one line per
attempt, capped at a small fixed list -- this is a deliberately small, one-time
quota spend, not a script meant to be rerun repeatedly.

Output: bot/data/endpoint_discovery.jsonl

Usage:
    python3 discover_endpoints.py
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

# a known, long-settled match/event for testing match-scoped endpoints
SETTLED_MATCH_ID = "4a46d42d-a791-4150-bff0-7287446e03f4"  # KOR vs CZE, closed 2026-06-12
SETTLED_EVENT_ID = "aa5572ec-5930-4d99-b06b-f8966333d172"

CANDIDATES = [
    # docs / schema discovery -- if any of these work, they reveal the full API
    ("GET", "/docs", None),
    ("GET", "/openapi.json", None),
    ("GET", "/swagger.json", None),
    ("GET", "/", None),
    # account / profile / rank
    ("GET", "/users/me", None),
    ("GET", "/me", None),
    ("GET", "/profile", None),
    ("GET", "/rank", None),
    ("GET", "/leaderboard", None),
    ("GET", "/leaderboard/daily", None),
    ("GET", "/leaderboard/global", None),
    ("GET", "/standings", None),
    # settled match / question results
    (f"GET", f"/matches/{SETTLED_MATCH_ID}", None),
    (f"GET", f"/matches/{SETTLED_MATCH_ID}/results", None),
    (f"GET", f"/markets", {"match_id": SETTLED_MATCH_ID, "status": "settled"}),
    (f"GET", f"/events/{SETTLED_EVENT_ID}", None),
    (f"GET", f"/events/{SETTLED_EVENT_ID}/leaderboard", None),
]

OUT_PATH = ROOT / "data" / "endpoint_discovery.jsonl"


def main():
    print(f"Testing {len(CANDIDATES)} candidate endpoints, 1.2s apart...")
    with open(OUT_PATH, "w", encoding="utf-8") as out:
        for method, path, params in CANDIDATES:
            url = f"{BASE_URL}{path}"
            try:
                resp = requests.request(method, url, headers=HEADERS, params=params, timeout=15)
                body_preview = None
                try:
                    body_preview = resp.json()
                except ValueError:
                    body_preview = resp.text[:300]
                result = {
                    "method": method, "path": path, "params": params,
                    "status_code": resp.status_code,
                    "body_preview": body_preview if resp.status_code == 200 else str(body_preview)[:300],
                }
            except requests.RequestException as e:
                result = {"method": method, "path": path, "params": params, "error": str(e)}

            out.write(json.dumps(result) + "\n")
            out.flush()
            tag = "OK " if result.get("status_code") == 200 else f"{result.get('status_code', 'ERR')}"
            print(f"  [{tag}] {method} {path} {params or ''}")
            time.sleep(1.2)

    print(f"\nDone. Full results in {OUT_PATH}")


if __name__ == "__main__":
    main()
