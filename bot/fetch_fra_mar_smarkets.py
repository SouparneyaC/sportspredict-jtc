"""
One-off scratch fetch of Smarkets bid/offer/mid quotes for the priority markets
relevant to the France vs Morocco (2026-07-09) question set. Follows the same
recreated-scratchpad pattern used in prior match sessions (contracts call to
label outcomes, then quotes call for bid/offer prices in basis points/10000).

Usage:
    python3 fetch_fra_mar_smarkets.py
"""
import json
import time
from pathlib import Path

import requests

BASE = "https://api.smarkets.com/v3"
OUT_DIR = Path(__file__).resolve().parent.parent / "matches" / "France_vs_Morocco"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# label -> market_id, taken from the FRA vs Morocco Smarkets market list (event 45178292)
MARKETS = {
    "FTR": "149627266",
    "OU2.5_goals": "149627303",
    "Cards_OU4.5": "149627441",
    "Cards_OU3.5": "149627439",
    "HT_result": "149627273",
    "Penalty": "149627291",
    "Any_sent_off": "149627428",
    "Mbappe_anytime_scorer": "149627747",
    "Player_SOT_OU0.5": "149627999",
    "Player_SOT_OU1.5": "149628001",
    "Morocco_SOT_OU3.5": "149627636",
    "France_corners_OU6.5": "149627466",
    "Sub_to_score": None,  # searched, no dedicated Smarkets market found
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
    raw = {}
    processed = {}
    for label, market_id in MARKETS.items():
        if market_id is None:
            processed[label] = None
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
        print(f"[{label}] {outcome_quotes}")
        time.sleep(0.4)

    with open(OUT_DIR / "smarkets_markets_raw.json", "w") as f:
        json.dump(raw, f, indent=2)
    with open(OUT_DIR / "smarkets_quotes_processed.json", "w") as f:
        json.dump(processed, f, indent=2)
    print(f"\nWrote {OUT_DIR / 'smarkets_quotes_processed.json'}")


if __name__ == "__main__":
    main()
