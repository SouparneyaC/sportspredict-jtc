"""
One-off fetch of Smarkets bid/offer/mid quotes for the markets relevant to the
France vs Spain SF (2026-07-14) question set. Same pattern as
fetch_fra_mar_smarkets.py (contracts call to label outcomes, then quotes call
for bid/offer prices in basis points/10000). Event 45192700, discovered via
parent_id=42791414 (WC2026) listing.

Usage:
    python3 fetch_fra_esp_smarkets.py
"""
import json
import time
from pathlib import Path

import requests

BASE = "https://api.smarkets.com/v3"
OUT_DIR = Path(__file__).resolve().parent.parent / "matches" / "France Vs Spain (Jul.14.26)"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# label -> market_id, from 09_smarkets_markets_raw.json (event 45192700)
MARKETS = {
    # Match-level anchors
    "FTR": "150820168",
    "Correct_score": "150820169",
    "BTTS": "150820170",
    "OU1.5_goals": "150820204",
    "OU2.5_goals": "150820205",
    "OU3.5_goals": "150820206",
    "To_qualify": "150820301",
    "Extra_time": "150820302",
    "Penalty_shootout": "150820303",
    "Half_time_result": "150820175",
    "FH_OU0.5_goals": "150820210",
    "Goal1_time_bracket": "150820394",
    "OU0.5_goals_1-10min": "150820422",
    # Cards (Q2)
    "Cards_OU2.5": "150820334",
    "Cards_OU3.5": "150820336",
    "Cards_OU4.5": "150820338",
    "France_cards_OU1.5": "150820384",
    "Spain_cards_OU1.5": "150820385",
    # Team goals (BTTS decomposition / sim calibration)
    "France_OU0.5_goals": "150820216",
    "France_OU1.5_goals": "150820217",
    "Spain_OU0.5_goals": "150820226",
    "Spain_OU1.5_goals": "150820227",
    # SOT (Q12 Spain 5+, Q15 France 4+)
    "France_SOT_OU4.5": "150820486",
    "Total_SOT_OU9.5": "150820582",
    # Player props (Q3 Yamal S/A, Q10 Mbappe score, Q8 first scorer)
    "Anytime_goalscorer": "150820644",
    "Score_or_assist": "150829029",
    "First_goalscorer": "150820640",
    "Player_SOT_OU0.5": "150829008",
    "Player_SOT_OU1.5": "150829010",
    # Not offered on Smarkets for this fixture (checked full 175-market list):
    "Offsides_any": None,        # Q1 -- no offsides market
    "VAR_review": None,          # Q4 -- no VAR market
    "Spain_team_SOT": None,      # Q12 -- only France team SOT + total SOT exist
    "First_substitution": None,  # Q14 -- no substitution market
}


def get_contracts(market_id):
    r = requests.get(f"{BASE}/markets/{market_id}/contracts/", timeout=20)
    r.raise_for_status()
    return {c["id"]: c["name"] for c in r.json()["contracts"]}


def get_quotes(market_id):
    r = requests.get(f"{BASE}/markets/{market_id}/quotes/", timeout=20)
    r.raise_for_status()
    return r.json()


def mid_from_quote(q):
    bids = q.get("bids", [])
    offers = q.get("offers", [])
    bid = bids[0]["price"] / 10000 if bids else None
    offer = offers[0]["price"] / 10000 if offers else None
    if bid is not None and offer is not None:
        mid = (bid + offer) / 2
    else:
        mid = bid if bid is not None else offer
    return {"bid": bid, "offer": offer, "mid": mid}


def main():
    # Resume support: keep successful fetches from a prior (rate-limited) run.
    raw, processed = {}, {}
    raw_path = OUT_DIR / "09_smarkets_quotes_raw.json"
    proc_path = OUT_DIR / "09_smarkets_quotes_processed.json"
    if raw_path.exists():
        raw = json.load(open(raw_path))
        processed = json.load(open(proc_path))
    for label, market_id in MARKETS.items():
        if market_id is None:
            processed[label] = None
            continue
        if label in raw:
            print(f"[{label}] already fetched, skipping")
            continue
        try:
            contracts = get_contracts(market_id)
            quotes = get_quotes(market_id)
        except requests.RequestException as e:
            print(f"  [ERR] {label} ({market_id}): {e}")
            processed[label] = {"error": str(e)}
            continue
        raw[label] = {"market_id": market_id, "contracts": contracts, "quotes": quotes}
        outcome_quotes = {}
        for contract_id, q in quotes.items():
            name = contracts.get(contract_id, contract_id)
            outcome_quotes[name] = mid_from_quote(q)
        processed[label] = outcome_quotes
        print(f"[{label}] {len(outcome_quotes)} outcomes")
        time.sleep(2.5)

    with open(OUT_DIR / "09_smarkets_quotes_raw.json", "w") as f:
        json.dump(raw, f, indent=2)
    with open(OUT_DIR / "09_smarkets_quotes_processed.json", "w") as f:
        json.dump(processed, f, indent=2)
    print(f"\nWrote {OUT_DIR / '09_smarkets_quotes_processed.json'}")


if __name__ == "__main__":
    main()
