"""
One-off fetch of Smarkets bid/offer/mid quotes for the markets relevant to the
England vs Argentina SF (2026-07-15) question set. Same pattern as
fetch_fra_esp_smarkets.py. Event 45195225, full 180-market list discovered live
via GET /events/{event_id}/markets/.

Usage:
    python3 fetch_eng_arg_smarkets.py
"""
import json
import time
from pathlib import Path

import requests

BASE = "https://api.smarkets.com/v3"
OUT_DIR = Path(__file__).resolve().parent.parent / "matches" / "England Vs Argentina (Jul.15.26)"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# label -> market_id, from live discovery of event 45195225's 180 markets
MARKETS = {
    # Match-level anchors
    "To_qualify": "151061214",              # Q2: England advance to final
    "Full_time_result": "151061081",
    "Both_teams_to_score": "151061083",
    "Half_time_result": "151061088",        # Q13: England lead at halftime
    # Goals
    "Argentina_OU1.5_goals": "151061140",   # Q14: Argentina 2+ goals
    "England_OU0.5_goals": "151061129",
    "FH_OU0.5_goals": "151061123",          # Q5: goal in each half (decomposition)
    "SH_OU0.5_goals": "151061126",          # Q5: goal in each half (decomposition)
    "Goal1_time_bracket": "151061307",
    # Corners
    "OU9.5_corners": "151061261",           # Q12: 10+ total corners
    "Corners_handicap_ENGm0.5_ARGp0.5": "151061209",  # Q9: Argentina more corners than England
    # Cards
    "Cards_OU1.5": "151061245",
    "Cards_OU2.5": "151061247",
    "England_cards_OU1.5": "151061297",     # Q8: both teams carded (decomposition)
    "Argentina_cards_OU1.5": "151061298",   # Q8: both teams carded (decomposition)
    "Team_to_have_first_card": "151061282", # Q10: card before first goal (decomposition)
    "Penalty_to_be_awarded": "151061106",   # Q3: penalty kick awarded
    # SOT (team-level, for Q6 combined-SOT derivation)
    "England_SOT_OU3.5": "151061398",
    "Argentina_SOT_OU3.5": "151061446",
    # Player props
    "Anytime_goalscorer": "151061557",      # Q4 Messi, Q11 Kane
    "Score_or_assist": "151064133",         # Q15 Bellingham
    "Player_SOT_OU0.5": "151064112",        # Q1 Alvarez
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
    raw, processed = {}, {}
    raw_path = OUT_DIR / "10_smarkets_quotes_raw.json"
    proc_path = OUT_DIR / "10_smarkets_quotes_processed.json"
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
        time.sleep(1.5)

    with open(raw_path, "w") as f:
        json.dump(raw, f, indent=2)
    with open(proc_path, "w") as f:
        json.dump(processed, f, indent=2)
    print(f"\nWrote {proc_path}")


if __name__ == "__main__":
    main()
