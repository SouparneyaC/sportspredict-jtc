"""
Scrape all publicly accessible data on the 16 competitors visible in the
SportsPredict JTC Group Stage lobby via GET /api/trades?q={event_id}.

Saves everything to bot/data/competitor_data/:
  raw_trades.json               — 73 raw trade records
  raw_markets.json              — all 844 market records for this event/lobby
  raw_user_scores.json          — /api/users/score/{id} for each user (if accessible)
  raw_user_events.json          — /api/events/user-events?userId={id} (if accessible)
  raw_user_events_summary.json  — /api/events/user-events/summary?userId={id} (if accessible)
  competitors_profiles.json     — merged per-user profile with all their picks + outcomes
  competitors_summary.csv       — one row per user: picks, win rate, questions won/lost
  trades_enriched.csv           — one row per trade: user, question, direction, price, outcome, win/loss

Usage:
    python3 scrape_competitors.py
"""

import csv
import json
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
SECRETS = json.load(open(ROOT / "secrets.json"))
API_KEY = SECRETS["sportspredict_api_key"]
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

EVENT_ID  = "aa5572ec-5930-4d99-b06b-f8966333d172"
LOBBY_ID  = "8df8038c-fd2c-4a5f-be4e-0e11d5966c05"
BASE_WEB  = "https://api.sportspredict.com/api"
BASE_V1   = "https://api.sportspredict.com/api/v1"

OUT = ROOT / "data" / "competitor_data"
OUT.mkdir(parents=True, exist_ok=True)

SCRAPE_TS = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def get(url, params=None, label=""):
    r = requests.get(url, headers=HEADERS, params=params, timeout=20)
    status = r.status_code
    if status in (200, 201):
        return r.json()
    print(f"  [{status}] {label or url}")
    return None


def post(url, body, label=""):
    r = requests.post(url, headers=HEADERS, json=body, timeout=20)
    status = r.status_code
    if status in (200, 201):
        return r.json()
    print(f"  [{status}] {label or url}")
    return None


PII_FIELDS = ("user_full_name", "user_email", "full_name", "email", "fullName", "userEmail", "userFullName")


def strip_pii(obj):
    """Competitors' real names/emails are private account data, not part of the
    platform's public leaderboard display -- never persist them to disk. Applied
    immediately after every fetch, before any raw dump or in-memory reuse."""
    if isinstance(obj, dict):
        for k in PII_FIELDS:
            obj.pop(k, None)
        for v in obj.values():
            strip_pii(v)
    elif isinstance(obj, list):
        for item in obj:
            strip_pii(item)
    return obj


# ── Step 1: Fetch all trades ─────────────────────────────────────────────────
print("Step 1: Fetching all trades for event...")
trades = get(f"{BASE_WEB}/trades",
             params={"q": json.dumps({"event_id": EVENT_ID})},
             label="GET /api/trades")
print(f"  → {len(trades)} trades")
strip_pii(trades)
with open(OUT / "raw_trades.json", "w") as f:
    json.dump({"scraped_at": SCRAPE_TS, "count": len(trades), "data": trades}, f, indent=2)

# Extract unique users
users = {}
for t in trades:
    uid = t["user_id"]
    if uid not in users:
        users[uid] = {
            "user_id": uid,
            "user_name": t["user_name"],
            "user_role": t["user_role"],
            "user_img_variants": t["user_img_variants"],
        }
print(f"  → {len(users)} unique competitors found")


# ── Step 2: Fetch all markets ────────────────────────────────────────────────
print("\nStep 2: Fetching all markets for this event/lobby...")
markets_raw = get(f"{BASE_WEB}/markets",
                  params={"q": json.dumps({"event_id": EVENT_ID, "lobby_id": LOBBY_ID})},
                  label="GET /api/markets")
print(f"  → {len(markets_raw)} markets total")
settled_count = sum(1 for m in markets_raw if m["status"] == "settled")
open_count    = sum(1 for m in markets_raw if m["status"] != "settled")
print(f"     Settled: {settled_count}  |  Open/Pending: {open_count}")
with open(OUT / "raw_markets.json", "w") as f:
    json.dump({"scraped_at": SCRAPE_TS, "count": len(markets_raw), "data": markets_raw}, f, indent=2)

# Build market lookup
mkt = {m["id"]: m for m in markets_raw}


# ── Step 3: Per-user extra endpoints ─────────────────────────────────────────
print("\nStep 3: Fetching per-user data for all 16 competitors...")
print("        (Testing: score, events, events/summary, leaderboard rank)")

user_scores   = {}
user_events   = {}
user_summaries = {}

for uid, udata in users.items():
    uname = udata["user_name"]
    time.sleep(0.4)  # stay well under rate limit

    # Score
    score = get(f"{BASE_WEB}/users/score/{uid}", label=f"score/{uname}")
    user_scores[uid] = score

    # Events they're in
    evts = get(f"{BASE_WEB}/events/user-events",
               params={"userId": uid}, label=f"user-events/{uname}")
    user_events[uid] = evts

    # Event summary (scores per event)
    summ = get(f"{BASE_WEB}/events/user-events/summary",
               params={"userId": uid}, label=f"events-summary/{uname}")
    user_summaries[uid] = summ

    ok_fields = []
    if score   is not None: ok_fields.append(f"score({type(score).__name__})")
    if evts    is not None: ok_fields.append(f"events({len(evts) if isinstance(evts,list) else type(evts).__name__})")
    if summ    is not None: ok_fields.append(f"summary({len(summ) if isinstance(summ,list) else type(summ).__name__})")
    status_str = ", ".join(ok_fields) if ok_fields else "all 401"
    print(f"  {uname:<25} → {status_str}")

with open(OUT / "raw_user_scores.json", "w") as f:
    json.dump({"scraped_at": SCRAPE_TS, "data": user_scores}, f, indent=2)
with open(OUT / "raw_user_events.json", "w") as f:
    json.dump({"scraped_at": SCRAPE_TS, "data": user_events}, f, indent=2)
with open(OUT / "raw_user_events_summary.json", "w") as f:
    json.dump({"scraped_at": SCRAPE_TS, "data": user_summaries}, f, indent=2)


# ── Step 4: Leaderboard (all pages) ──────────────────────────────────────────
print("\nStep 4: Fetching full leaderboard (all pages)...")
leaderboard_all = []
page = 1
while True:
    lb = post(f"{BASE_WEB}/lobbies/leaderboard",
              {"eventId": EVENT_ID, "lobbyId": LOBBY_ID, "page": page},
              label=f"leaderboard page {page}")
    if not lb or (isinstance(lb, list) and len(lb) == 0):
        break
    if isinstance(lb, list):
        leaderboard_all.extend(lb)
        print(f"  Page {page}: {len(lb)} entries")
        if len(lb) < 20:
            break
    else:
        print(f"  Unexpected leaderboard shape: {type(lb)}")
        break
    page += 1
    time.sleep(0.3)

print(f"  → {len(leaderboard_all)} leaderboard entries total")
strip_pii(leaderboard_all)
with open(OUT / "raw_leaderboard.json", "w") as f:
    json.dump({"scraped_at": SCRAPE_TS, "count": len(leaderboard_all), "data": leaderboard_all}, f, indent=2)


# ── Step 5: Per-user trades filtered by user_id ───────────────────────────────
print("\nStep 5: Fetching trades filtered per user...")
per_user_trades = {}
for uid, udata in users.items():
    uname = udata["user_name"]
    time.sleep(0.3)
    ut = get(f"{BASE_WEB}/trades",
             params={"q": json.dumps({"user_id": uid, "event_id": EVENT_ID})},
             label=f"trades/{uname}")
    per_user_trades[uid] = strip_pii(ut) if ut is not None else []
    n = len(per_user_trades[uid]) if per_user_trades[uid] else 0
    print(f"  {uname:<25} → {n} trades")

with open(OUT / "raw_per_user_trades.json", "w") as f:
    json.dump({"scraped_at": SCRAPE_TS, "data": per_user_trades}, f, indent=2)


# ── Step 6: Build enriched profiles ──────────────────────────────────────────
print("\nStep 6: Building enriched competitor profiles...")

profiles = {}
for uid, udata in users.items():
    user_trades = [t for t in trades if t["user_id"] == uid]

    picks = []
    wins = 0
    for t in user_trades:
        m = mkt.get(t["market_id"], {})
        outcome_val = m.get("current_value")
        is_settled  = m.get("status") == "settled"

        if is_settled and outcome_val is not None:
            actual_yes = (outcome_val == 100)
            bet_yes    = (t["position"] == "long")
            won        = (actual_yes == bet_yes)
            if won:
                wins += 1
        else:
            won = None

        picks.append({
            "market_id":       t["market_id"],
            "question":        m.get("question", "?"),
            "match_id":        m.get("match_id"),
            "direction":       "YES" if t["position"] == "long" else "NO",
            "entry_price":     int(t["entry_price"]),
            "market_status":   m.get("status"),
            "outcome":         "YES" if outcome_val == 100 else ("NO" if outcome_val == 0 else None),
            "outcome_raw":     outcome_val,
            "won":             won,
            "trade_date":      t["created_date"],
        })

    settled_picks = [p for p in picks if p["won"] is not None]
    win_rate = round(wins / len(settled_picks), 3) if settled_picks else None

    profiles[uid] = {
        **udata,
        "total_picks":    len(picks),
        "settled_picks":  len(settled_picks),
        "wins":           wins,
        "losses":         len(settled_picks) - wins,
        "win_rate":       win_rate,
        "avg_entry_price": round(sum(p["entry_price"] for p in picks) / len(picks), 1) if picks else None,
        "extra_score":    user_scores.get(uid),
        "extra_events":   user_events.get(uid),
        "extra_summary":  user_summaries.get(uid),
        "picks":          picks,
    }

with open(OUT / "competitors_profiles.json", "w") as f:
    json.dump({"scraped_at": SCRAPE_TS, "count": len(profiles), "data": profiles}, f, indent=2)

print(f"  → Profiles built for {len(profiles)} competitors")


# ── Step 7: Write CSVs ───────────────────────────────────────────────────────
print("\nStep 7: Writing CSV files...")

# competitors_summary.csv
summary_rows = []
for uid, p in profiles.items():
    summary_rows.append({
        "user_id":         uid,
        "user_name":       p["user_name"],
        "total_picks":     p["total_picks"],
        "settled_picks":   p["settled_picks"],
        "wins":            p["wins"],
        "losses":          p["losses"],
        "win_rate":        p["win_rate"],
        "avg_entry_price": p["avg_entry_price"],
    })
summary_rows.sort(key=lambda x: -(x["win_rate"] or 0))

with open(OUT / "competitors_summary.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
    w.writeheader()
    w.writerows(summary_rows)
print(f"  → competitors_summary.csv ({len(summary_rows)} rows)")

# trades_enriched.csv
trade_rows = []
for uid, p in profiles.items():
    for pick in p["picks"]:
        trade_rows.append({
            "user_name":     p["user_name"],
            "user_id":       uid,
            "match_id":      pick["match_id"],
            "market_id":     pick["market_id"],
            "question":      pick["question"],
            "direction":     pick["direction"],
            "entry_price":   pick["entry_price"],
            "market_status": pick["market_status"],
            "outcome":       pick["outcome"],
            "won":           pick["won"],
            "trade_date":    pick["trade_date"],
        })
trade_rows.sort(key=lambda x: (x["user_name"], x["trade_date"]))

with open(OUT / "trades_enriched.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(trade_rows[0].keys()))
    w.writeheader()
    w.writerows(trade_rows)
print(f"  → trades_enriched.csv ({len(trade_rows)} rows)")

# markets_settled.csv — all settled question outcomes
settled_rows = []
for m in markets_raw:
    if m["status"] == "settled":
        settled_rows.append({
            "market_id":    m["id"],
            "match_id":     m["match_id"],
            "question":     m["question"],
            "outcome":      "YES" if m["current_value"] == 100 else "NO",
            "initial_value": m["initial_value"],
            "opening_time": m.get("opening_time"),
            "closing_date": m.get("closing_date"),
            "settled_date": m.get("settled_date"),
            "status":       m["status"],
        })
settled_rows.sort(key=lambda x: x["settled_date"] or "")

with open(OUT / "markets_settled.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(settled_rows[0].keys()))
    w.writeheader()
    w.writerows(settled_rows)
print(f"  → markets_settled.csv ({len(settled_rows)} rows — all settled question outcomes)")

# markets_open.csv — open questions still needing prediction
open_rows = []
for m in markets_raw:
    if m["status"] != "settled":
        open_rows.append({
            "market_id":    m["id"],
            "match_id":     m["match_id"],
            "question":     m["question"],
            "current_crowd": m["current_value"],
            "status":       m["status"],
            "opening_time": m.get("opening_time"),
            "closing_date": m.get("closing_date"),
        })
open_rows.sort(key=lambda x: x["closing_date"] or "")

with open(OUT / "markets_open.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(open_rows[0].keys()))
    w.writeheader()
    w.writerows(open_rows)
print(f"  → markets_open.csv ({len(open_rows)} rows — open questions)")


# ── Final summary ─────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("SCRAPE COMPLETE")
print("="*60)
print(f"Scraped at: {SCRAPE_TS}")
print(f"Output dir: {OUT}")
print()
print("Files written:")
for f in sorted(OUT.iterdir()):
    size_kb = f.stat().st_size // 1024
    print(f"  {f.name:<40} {size_kb:>4} KB")

print()
print("COMPETITOR SUMMARY (by win rate):")
print(f"  {'Name':<25} {'Picks':>5}  {'W/L':>7}  {'Win%':>6}  {'Avg Price':>9}")
print("  " + "-"*55)
for row in summary_rows:
    wl = f"{row['wins']}/{row['losses']}" if row['settled_picks'] > 0 else "n/a"
    wr = f"{row['win_rate']*100:.0f}%" if row['win_rate'] is not None else "n/a"
    print(f"  {row['user_name']:<25} {row['total_picks']:>5}  {wl:>7}  {wr:>6}  {str(row['avg_entry_price']):>9}")

if __name__ == "__main__":
    pass
