"""
Daily dashboard fetcher. Pulls current match schedule, your rank, settled match
results, and overall standing from the SportsPredict web API, then prints a
formatted pre-session summary and saves a dated JSON snapshot.

Auth: uses session_cookies from secrets.json (set by setup_session.py) OR
      falls back to the sportspredict_api_key Bearer token if it works on web endpoints.

Output:
    Printed summary to stdout
    bot/data/dashboard_snapshots/dashboard_{YYYY-MM-DD}.json

Usage:
    python3 fetch_dashboard.py
    python3 fetch_dashboard.py --json-only   (skip print, just write file)
"""

import json
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
SECRETS = json.load(open(ROOT / "secrets.json"))

# ── Auth setup ──────────────────────────────────────────────────────────────
API_KEY = SECRETS.get("sportspredict_api_key")
SESSION_COOKIES = SECRETS.get("session_cookies", {})
USER_ID = SECRETS.get("sp_user_id")

BASE_V1  = "https://api.sportspredict.com/api/v1"
BASE_WEB = "https://api.sportspredict.com/api"

EVENT_ID = "aa5572ec-5930-4d99-b06b-f8966333d172"
LOBBY_ID = "8df8038c-fd2c-4a5f-be4e-0e11d5966c05"

SNAPSHOTS_DIR = ROOT / "data" / "dashboard_snapshots"
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)

HEADERS_BEARER = {"Authorization": f"Bearer {API_KEY}"} if API_KEY else {}


def _get(url, params=None, use_bearer=False):
    """GET with cookie session; falls back to Bearer if session absent."""
    headers = HEADERS_BEARER if use_bearer else {}
    cookies = {} if use_bearer else SESSION_COOKIES
    r = requests.get(url, headers=headers, cookies=cookies, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def _post(url, body, use_bearer=False):
    """POST with cookie session; falls back to Bearer if session absent."""
    headers = HEADERS_BEARER if use_bearer else {}
    cookies = {} if use_bearer else SESSION_COOKIES
    r = requests.post(url, headers=headers, cookies=cookies, json=body, timeout=20)
    r.raise_for_status()
    return r.json()


# ── Data fetchers ────────────────────────────────────────────────────────────

def fetch_matches():
    """All matches from v1 API (works with Bearer token)."""
    return _get(f"{BASE_V1}/matches", use_bearer=True)


def fetch_open_markets(match_id):
    """Open market questions for a match (v1, Bearer)."""
    return _get(f"{BASE_V1}/markets", params={"match_id": match_id}, use_bearer=True)


def fetch_trades():
    """All predictions + settled outcomes for current user in JTC event."""
    if not USER_ID:
        return None
    q = json.dumps({"user_id": USER_ID, "event_id": EVENT_ID})
    return _get(f"{BASE_WEB}/trades", params={"q": q})


def fetch_rank():
    """Current rank in the JTC lobby."""
    return _get(f"{BASE_WEB}/lobbies/second-chance/rank/{EVENT_ID}/{LOBBY_ID}")


def fetch_event_summary():
    """Per-event score and rank summary for the user."""
    if not USER_ID:
        return None
    return _get(f"{BASE_WEB}/events/user-events/summary", params={"userId": USER_ID})


def fetch_leaderboard(page=1):
    """Top N players in the JTC lobby leaderboard."""
    return _post(f"{BASE_WEB}/lobbies/leaderboard",
                 {"event_id": EVENT_ID, "lobby_id": LOBBY_ID, "page": page})


# ── Data processing ──────────────────────────────────────────────────────────

def parse_open_matches(matches):
    now = datetime.now(timezone.utc)
    open_matches = []
    for m in matches:
        closing = m.get("closing_time")
        if not closing:
            continue
        try:
            close_dt = datetime.fromisoformat(closing.replace("Z", "+00:00"))
        except ValueError:
            continue
        if close_dt > now:
            delta = close_dt - now
            hours, rem = divmod(int(delta.total_seconds()), 3600)
            mins = rem // 60
            open_matches.append({
                "id": m["id"],
                "name": m["name"],
                "closing_time": closing,
                "closes_in": f"{hours}h {mins}m" if hours > 0 else f"{mins}m",
                "open_market_count": m.get("open_market_count", "?"),
            })
    open_matches.sort(key=lambda x: x["closing_time"])
    return open_matches


def parse_settled_trades(trades):
    if not trades:
        return []
    settled = [t for t in trades if t.get("settled") or t.get("outcome") is not None]
    # Group by match
    by_match = {}
    for t in settled:
        mid = t.get("match_id") or t.get("match", {}).get("id", "unknown")
        mname = t.get("match_name") or t.get("match", {}).get("name", mid)
        if mid not in by_match:
            by_match[mid] = {"name": mname, "questions": [], "total_rbp": 0.0, "beat_crowd": 0, "total": 0}
        score = float(t.get("score") or t.get("rbp") or t.get("points") or 0)
        by_match[mid]["questions"].append({
            "question": t.get("question") or t.get("market", {}).get("question", "?"),
            "our_estimate": t.get("estimate") or t.get("user_estimate"),
            "crowd_estimate": t.get("crowd_estimate") or t.get("crowd"),
            "outcome": t.get("outcome") or t.get("result"),
            "score": score,
        })
        by_match[mid]["total_rbp"] += score
        by_match[mid]["total"] += 1
        if score > 0:
            by_match[mid]["beat_crowd"] += 1
    # Sort by most recent (approximated by match name for now)
    result = list(by_match.values())
    result.sort(key=lambda x: x["total_rbp"], reverse=True)
    return result


# ── Formatters ───────────────────────────────────────────────────────────────

def fmt_open_matches(open_matches):
    if not open_matches:
        return "  (no open matches)"
    lines = []
    for m in open_matches:
        lines.append(f"  {m['name']:<20}  closes in {m['closes_in']:<10}  ({m['open_market_count']} markets)")
    return "\n".join(lines)


def fmt_standing(rank_data, summary_data):
    lines = []
    if rank_data and not isinstance(rank_data, dict) or (rank_data and "statusCode" not in rank_data):
        rank = rank_data.get("rank") or rank_data.get("position") or "?"
        total = rank_data.get("total") or rank_data.get("total_players") or "?"
        lines.append(f"  Lobby Rank:    #{rank} / {total}")
    if summary_data:
        for evt in (summary_data if isinstance(summary_data, list) else [summary_data]):
            if evt.get("event_id") == EVENT_ID or "Jump" in str(evt.get("event_name", "")):
                score = evt.get("score") or evt.get("total_score") or evt.get("rbp") or "?"
                beat  = evt.get("beat_crowd_rate") or evt.get("win_rate") or "?"
                lines.append(f"  Total RBP:     {score}")
                lines.append(f"  Beat-crowd:    {beat}")
                break
    return "\n".join(lines) if lines else "  (standing data unavailable — check auth)"


def fmt_settled(settled):
    if not settled:
        return "  (no settled match data — check auth)"
    lines = []
    for match in settled[:5]:  # show 5 most recent
        pct = f"{match['beat_crowd']}/{match['total']}" if match['total'] else "?"
        rbp = f"{match['total_rbp']:+.1f}"
        lines.append(f"  {match['name']:<20}  {rbp:>8} RBP   beat crowd: {pct}")
    return "\n".join(lines)


def print_dashboard(data):
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    open_matches = data["open_matches"]
    settled = data["settled_matches"]

    print()
    print("=" * 62)
    print(f"  SportsPredict Dashboard — {today}")
    print("=" * 62)

    print(f"\nOPEN MATCHES ({len(open_matches)} upcoming):")
    print(fmt_open_matches(open_matches))

    print(f"\nYOUR JTC STANDING:")
    print(fmt_standing(data.get("rank"), data.get("event_summary")))

    print(f"\nSETTLED MATCHES (last {min(5, len(settled))}):")
    print(fmt_settled(settled))

    print()
    print("=" * 62)
    print()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    json_only = "--json-only" in sys.argv
    errors = []

    if not SESSION_COOKIES and not API_KEY:
        print("❌ No auth credentials found in secrets.json.")
        print("   Run test_web_api.py first. If it fails, run setup_session.py.")
        sys.exit(1)

    if not SESSION_COOKIES:
        print("⚠️  No session_cookies in secrets.json — web API endpoints may return 401.")
        print("   Run setup_session.py to extract your browser session.")
        print()

    data = {
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "open_matches": [],
        "settled_matches": [],
        "rank": None,
        "event_summary": None,
        "leaderboard_top10": None,
        "raw": {},
    }

    # 1. Open matches (v1, Bearer — always works)
    try:
        matches_raw = fetch_matches()
        data["raw"]["matches"] = matches_raw
        data["open_matches"] = parse_open_matches(matches_raw)
        print(f"✅ Matches: {len(data['open_matches'])} open")
    except Exception as e:
        errors.append(f"matches: {e}")
        print(f"❌ Matches failed: {e}")

    # 2. Settled trades (web, session cookie)
    try:
        trades_raw = fetch_trades()
        if trades_raw is None:
            print("⚠️  Skipping trades — no user_id in secrets.json (run setup_session.py)")
        else:
            data["raw"]["trades"] = trades_raw
            data["settled_matches"] = parse_settled_trades(trades_raw)
            print(f"✅ Trades: {len(trades_raw)} total, {len(data['settled_matches'])} settled matches")
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            errors.append("trades: 401 — session cookie invalid or missing")
            print("❌ Trades: 401 Unauthorized — run setup_session.py to refresh session")
        else:
            errors.append(f"trades: {e}")
            print(f"❌ Trades failed: {e}")

    # 3. Rank
    try:
        rank_raw = fetch_rank()
        data["raw"]["rank"] = rank_raw
        data["rank"] = rank_raw
        print(f"✅ Rank fetched")
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            errors.append("rank: 401")
            print("❌ Rank: 401 Unauthorized — run setup_session.py")
        else:
            errors.append(f"rank: {e}")

    # 4. Event summary
    try:
        summary_raw = fetch_event_summary()
        if summary_raw is None:
            print("⚠️  Skipping event summary — no user_id")
        else:
            data["raw"]["event_summary"] = summary_raw
            data["event_summary"] = summary_raw
            print(f"✅ Event summary fetched")
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            errors.append("event_summary: 401")
            print("❌ Event summary: 401 — run setup_session.py")
        else:
            errors.append(f"event_summary: {e}")

    # 5. Leaderboard top 10 (context for your rank)
    try:
        lb_raw = fetch_leaderboard(page=1)
        data["raw"]["leaderboard"] = lb_raw
        data["leaderboard_top10"] = lb_raw
        print(f"✅ Leaderboard fetched")
    except Exception as e:
        errors.append(f"leaderboard: {e}")

    # Save snapshot
    today_str = datetime.now().strftime("%Y-%m-%d")
    snapshot_path = SNAPSHOTS_DIR / f"dashboard_{today_str}.json"
    with open(snapshot_path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"✅ Snapshot saved → {snapshot_path.relative_to(ROOT.parent)}")

    # Print summary
    if not json_only:
        print_dashboard(data)

    if errors:
        print(f"⚠️  {len(errors)} endpoint(s) failed: {', '.join(errors)}")
        print("   Run setup_session.py if you see 401 errors.")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
