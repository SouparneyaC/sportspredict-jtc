"""
One-time session extractor — intercepts auth token from live browser session.

Usage:
    python3 setup_session.py
"""

import json
import random
import sys
import time
from pathlib import Path

import requests

ROOT         = Path(__file__).resolve().parent
SECRETS_PATH = ROOT / "secrets.json"
PLAY_URL     = "https://play.sportspredict.com"
API_BASE     = "https://api.sportspredict.com/api"
EVENT_ID     = "aa5572ec-5930-4d99-b06b-f8966333d172"
LOBBY_ID     = "8df8038c-fd2c-4a5f-be4e-0e11d5966c05"


def _sleek_headers(token):
    return {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/136.0.0.0 Safari/537.36"
        ),
        "Accept":          "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer":         "https://play.sportspredict.com/",
        "Origin":          "https://play.sportspredict.com",
        "Authorization":   f"Bearer {token}",
    }


def _pause():
    time.sleep(random.uniform(1.2, 3.1))


def _validate(token):
    h = _sleek_headers(token)
    tests = [
        ("user-me",       "GET",  f"{API_BASE}/users/me",               None, None),
        ("lobby-stats",   "GET",  f"{API_BASE}/lobbies/lobby-stats/me", None, None),
        ("leaderboard",   "POST", f"{API_BASE}/lobbies/leaderboard",    None,
         {"eventId": EVENT_ID, "lobbyId": LOBBY_ID, "page": 1}),
        ("event-summary", "GET",  f"{API_BASE}/events/user-events/summary", None, None),
    ]
    results = {}
    for label, method, url, params, body in tests:
        _pause()
        try:
            r = requests.post(url, headers=h, json=body, timeout=15) if method == "POST" \
                else requests.get(url, headers=h, params=params, timeout=15)
            preview = ""
            if r.status_code in (200, 201):
                try:
                    data = r.json()
                    preview = f"{len(data)} items" if isinstance(data, list) \
                              else str(list(data.keys()))[:80]
                except Exception:
                    preview = r.text[:80]
            else:
                try:
                    preview = r.json().get("message", "")[:60]
                except Exception:
                    preview = r.text[:60]
            results[label] = (r.status_code, preview)
            print(f"  [{r.status_code}] {label:<16} {preview}")
        except Exception as e:
            results[label] = (0, str(e))
            print(f"  [ERR] {label:<16} {e}")
    return results


def run():
    from playwright.sync_api import sync_playwright

    print("=" * 60)
    print("SportsPredict Session Extractor")
    print("=" * 60)
    print()
    print("Chromium will open. Log in, then browse to the leaderboard.")
    print("The script watches ALL requests to api.sportspredict.com.")
    print()

    captured = {"token": None, "all_headers": []}
    existing_key = json.load(open(SECRETS_PATH)).get("sportspredict_api_key", "")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=100,
            args=["--no-first-run", "--no-default-browser-check",
                  "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/136.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/Chicago",
        )

        def on_request(request):
            url = request.url
            if "sportspredict.com" not in url:
                return
            hdrs = dict(request.headers)
            auth = hdrs.get("authorization", "")
            # Log every API call header set (deduplicated)
            if "api.sportspredict.com" in url and auth not in [x[1] for x in captured["all_headers"]]:
                captured["all_headers"].append((url, auth, list(hdrs.keys())))

            if auth.startswith("Bearer ") and not captured["token"]:
                token = auth.replace("Bearer ", "").strip()
                if token != existing_key and len(token) > 20:
                    captured["token"] = token
                    print(f"  >> Bearer token captured ({len(token)} chars): {token[:30]}...")

        page = context.new_page()
        page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        context.on("request", on_request)

        print("Navigating to play.sportspredict.com ...")
        page.goto(PLAY_URL, wait_until="domcontentloaded", timeout=30000)

        print("Waiting up to 3 minutes. Log in, then click around (matches, leaderboard).")
        print("Press Ctrl+C to stop early if you see the token captured above.\n")

        deadline = time.time() + 180
        while time.time() < deadline:
            time.sleep(2)
            if captured["token"]:
                print("\nToken captured — waiting 3 more seconds for any follow-up requests...")
                time.sleep(3)
                break
            # Status update every 20s
            elapsed = int(time.time() - (deadline - 180))
            if elapsed % 20 == 0 and elapsed > 0:
                print(f"  ... {elapsed}s elapsed, {len(captured['all_headers'])} API calls seen so far")

        # --- Dump what we saw even if no Bearer token ---
        print()
        print(f"API calls intercepted: {len(captured['all_headers'])}")
        for url, auth, keys in captured["all_headers"][:10]:
            short_url = url.replace("https://api.sportspredict.com", "")[:60]
            print(f"  {short_url}")
            print(f"    auth header: {auth[:80] if auth else '(none)'}")
            print(f"    other keys:  {[k for k in keys if k != 'authorization']}")

        # Try localStorage / sessionStorage scan
        print()
        print("Scanning localStorage / sessionStorage for tokens...")
        try:
            ls_items = page.evaluate("""
                () => {
                    const out = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        const k = localStorage.key(i);
                        const v = localStorage.getItem(k);
                        out['LS:' + k] = v ? v.substring(0, 120) : '';
                    }
                    for (let i = 0; i < sessionStorage.length; i++) {
                        const k = sessionStorage.key(i);
                        const v = sessionStorage.getItem(k);
                        out['SS:' + k] = v ? v.substring(0, 120) : '';
                    }
                    return out;
                }
            """)
            for k, v in ls_items.items():
                print(f"  {k}: {v[:100]}")
                # look for anything that resembles a JWT or long token
                if v and len(v) > 30 and not captured["token"]:
                    if "ey" in v or "token" in k.lower() or "auth" in k.lower():
                        captured["token"] = v.strip()
                        print(f"  >> Possible token found in {k}")
        except Exception as e:
            print(f"  Storage scan failed: {e}")

        browser.close()

    print()

    if not captured["token"]:
        print("❌ No auth token found.")
        print()
        print("This means the app is not using a Bearer token in request headers.")
        print("Most likely auth mechanism: HTTP-only cookie set by api.sportspredict.com")
        print()
        print("Next step: run the cookie-capture variant instead.")
        sys.exit(1)

    token = captured["token"]
    print(f"Token: {token[:40]}...")
    print()
    print("Validating token...")
    validation = _validate(token)
    print()

    secrets = {}
    if SECRETS_PATH.exists():
        secrets = json.load(open(SECRETS_PATH))
    secrets["web_session_token"]    = token
    secrets["session_extracted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    with open(SECRETS_PATH, "w") as f:
        json.dump(secrets, f, indent=2)

    print(f"✅ Saved — keys: {list(secrets.keys())}")

    working = [k for k, (s, _) in validation.items() if s in (200, 201)]
    blocked = [k for k, (s, _) in validation.items() if s not in (200, 201)]
    print(f"Working: {working}")
    if blocked:
        print(f"Blocked: {blocked}")


if __name__ == "__main__":
    run()
