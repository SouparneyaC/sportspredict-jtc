"""
One-off diagnostic: test whether the existing sportspredict_api_key from secrets.json
also works on the web API endpoints (/api/ namespace, not /api/v1/).

If the Bearer token works on these endpoints, no Playwright session extraction is needed.
If it returns 401/403 on all web endpoints, run setup_session.py next to extract
the browser session cookie.

Usage:
    python3 test_web_api.py

Output: prints a report and exits 0 if token works, 1 if Playwright session is needed.
"""

import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
SECRETS = json.load(open(ROOT / "secrets.json"))
API_KEY = SECRETS["sportspredict_api_key"]
HEADERS_V1 = {"Authorization": f"Bearer {API_KEY}"}

EVENT_ID = "aa5572ec-5930-4d99-b06b-f8966333d172"
LOBBY_ID = "8df8038c-fd2c-4a5f-be4e-0e11d5966c05"

BASE_V1  = "https://api.sportspredict.com/api/v1"
BASE_WEB = "https://api.sportspredict.com/api"

TESTS = [
    # (label, method, url, params, body)
    ("v1/matches [known working]",   "GET",  f"{BASE_V1}/matches",  None, None),
    ("web/matches [same endpoint?]", "GET",  f"{BASE_WEB}/matches", None, None),
    ("web/trades",  "GET",  f"{BASE_WEB}/trades",
     {"q": json.dumps({"event_id": EVENT_ID})}, None),
    ("web/events/user-events/summary", "GET",
     f"{BASE_WEB}/events/user-events/summary", None, None),
    ("web/lobbies/lobby-stats/me", "GET",
     f"{BASE_WEB}/lobbies/lobby-stats/me", None, None),
    ("web/lobbies/leaderboard", "POST",
     f"{BASE_WEB}/lobbies/leaderboard", None,
     {"event_id": EVENT_ID, "lobby_id": LOBBY_ID, "page": 1}),
]

def run():
    print("=" * 60)
    print("SportsPredict Web API Key Compatibility Test")
    print("=" * 60)

    results = []
    for label, method, url, params, body in TESTS:
        try:
            if method == "GET":
                r = requests.get(url, headers=HEADERS_V1, params=params, timeout=15)
            else:
                r = requests.post(url, headers=HEADERS_V1, json=body, timeout=15)
            ok = r.status_code in (200, 201)
            preview = ""
            if ok:
                try:
                    d = r.json()
                    if isinstance(d, list):
                        preview = f"{len(d)} items"
                    elif isinstance(d, dict):
                        preview = str(list(d.keys()))[:60]
                except Exception:
                    preview = r.text[:60]
            tag = "✅ OK " if ok else f"❌ {r.status_code}"
            print(f"  [{tag}] {label}")
            if ok and preview:
                print(f"         → {preview}")
            results.append(ok)
        except requests.RequestException as e:
            print(f"  [ERR] {label}: {e}")
            results.append(False)

    web_results = results[1:]  # skip the v1/matches baseline
    web_working = sum(web_results)

    print()
    print("=" * 60)
    if web_working >= 3:
        print("✅ RESULT: Existing API key works on web endpoints.")
        print("   → Proceed directly to fetch_dashboard.py")
        print("   → No Playwright setup needed.")
        sys.exit(0)
    elif web_working > 0:
        print(f"⚠️  RESULT: API key works on {web_working}/{len(web_results)} web endpoints.")
        print("   → Partial access. Check which endpoints work above.")
        print("   → May still need setup_session.py for the 401 ones.")
        sys.exit(1)
    else:
        print("❌ RESULT: API key does NOT work on web endpoints.")
        print("   → Run setup_session.py to extract browser session cookie.")
        sys.exit(1)

if __name__ == "__main__":
    run()
