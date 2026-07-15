"""
Answers a direct question: why wasn't the SOT backtest run against a live
market baseline, and can we build a smaller version of that comparison from
whatever market data we actually have archived?

Scanned every match folder for a saved Smarkets team-level SOT market
(Player_SOT markets excluded -- those are individual props, not what this
model predicts). Found 11 matches (of the 100 in the full walk-forward
panel) with at least one team's line saved, all from this tournament's
knockout stage (Smarkets fetches only started once match-day market-checking
became routine -- roughly R32 onward). None of the 256 WC2018/2022 rows can
ever have this: those are exchange markets from an 8-year-old tournament,
retrospectively unarchivable via any endpoint that exists today.

For each saved line, fits an implied Poisson lambda the same way
simulate_fra_esp_sf.py did (solve for lambda so P(X > threshold) matches the
market's normalized probability), then pulls the ALREADY-COMPUTED walk-forward
ML and baseline predictions for that exact team-match row from
sot_backtest_results.csv (both are PIT-safe -- fit fresh using only data
strictly before that match).

Usage:
    python3 sot_vs_market_comparison.py
"""
import csv
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CODE_TO_NAME = {
    "ALG": "Algeria", "ARG": "Argentina", "AUS": "Australia", "AUT": "Austria",
    "BEL": "Belgium", "BIH": "Bosnia and Herzegovina", "BRA": "Brazil",
    "CAN": "Canada", "CDR": "DR Congo", "CIV": "Ivory Coast", "COL": "Colombia",
    "CPV": "Cape Verde", "CRO": "Croatia", "CUR": "Curaçao", "CZE": "Czech Republic",
    "ECU": "Ecuador", "EGY": "Egypt", "ENG": "England", "ESP": "Spain",
    "FRA": "France", "GER": "Germany", "GHA": "Ghana", "HAI": "Haiti",
    "IRN": "Iran", "IRQ": "Iraq", "JOR": "Jordan", "JPN": "Japan",
    "KOR": "South Korea", "SAU": "Saudi Arabia", "MAR": "Morocco", "MEX": "Mexico",
    "NED": "Netherlands", "NOR": "Norway", "NZL": "New Zealand", "PAN": "Panama",
    "PAR": "Paraguay", "POR": "Portugal", "QAT": "Qatar", "RSA": "South Africa",
    "SCO": "Scotland", "SEN": "Senegal", "SUI": "Switzerland",
    "SWE": "Sweden", "TUN": "Tunisia", "TUR": "Turkey", "URU": "Uruguay",
    "USA": "United States", "UZB": "Uzbekistan",
}
# Full names already used as-is in some files
FULL_NAMES = set(CODE_TO_NAME.values())

# (file, team-label-in-key -> resolved full team name)
SOURCES = [
    ("matches/Brazil_vs_Norway/smarkets_quotes_processed.json",
     {"BRA_SOT_OU4.5": "Brazil", "NOR_SOT_OU3.5": "Norway"}),
    ("matches/France_vs_Paraguay/smarkets_quotes_processed.json",
     {"FRA_SOT_OU7.5": "France", "PAR_SOT_OU2.5": "Paraguay"}),
    ("matches/Canada_vs_Morocco/smarkets_quotes_processed.json",
     {"CAN_SOT_OU2.5": "Canada", "MAR_SOT_OU4.5": "Morocco"}),
    ("matches/Mexico_vs_England/smarkets_quotes_processed.json",
     {"ENG_SOT_OU3.5": "England", "MEX_SOT_OU3.5": "Mexico"}),
    ("matches/Australia_vs_Egypt/smarkets_quotes_processed.json",
     {"Egypt_SOT_OU3.5": "Egypt"}),
    ("matches/Spain_vs_Austria/smarkets_quotes_processed.json",
     {"Spain_SOT_OU6_5": "Spain", "Austria_SOT_OU2_5": "Austria"}),
    ("matches/Argentina_vs_CapeVerde/smarkets_quotes_processed.json",
     {"ARG_SOT_OU6.5": "Argentina", "CPV_SOT_OU1.5": "Cape Verde"}),
    ("matches/Portugal_vs_Croatia/smarkets_quotes_processed.json",
     {"Portugal_SOT_OU4_5": "Portugal", "Croatia_SOT_OU3_5": "Croatia"}),
    ("matches/Colombia_vs_Ghana/smarkets_quotes_processed.json",
     {"COL_SOT_OU5.5": "Colombia", "GHA_SOT_OU2.5": "Ghana"}),
    ("matches/Argentina_vs_Switzerland/02_smarkets_quotes_raw.json",
     {"Argentina_SOT_OU5.5": "Argentina", "Switzerland_SOT_OU2.5": "Switzerland"}),
    ("matches/Spain_vs_Belgium/02_smarkets_quotes_raw.json",
     {"Belgium_SOT_OU2.5": "Belgium"}),
]


def parse_threshold(key):
    m = re.search(r"OU_?(\d+)[._](\d)", key)
    return float(f"{m.group(1)}.{m.group(2)}")


def market_prob_over(market_dict):
    """Normalize the two outcomes in a market dict to P(over)."""
    over_key = next(k for k in market_dict if k.lower().startswith("over"))
    under_key = next(k for k in market_dict if k.lower().startswith("under"))
    o, u = market_dict[over_key]["mid"], market_dict[under_key]["mid"]
    if o is None or u is None:
        return None
    return o / (o + u)


def implied_lambda(p_over, threshold):
    """Solve for Poisson lambda such that P(X > threshold) = p_over."""
    k = math.floor(threshold)  # P(X > threshold) = P(X >= k+1) since threshold is X.5
    lo, hi = 0.01, 20.0
    for _ in range(60):
        mid = (lo + hi) / 2
        p = 1 - sum(math.exp(-mid) * mid**i / math.factorial(i) for i in range(k + 1))
        if p < p_over:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def nll(actual, lam):
    return -(-lam + actual * math.log(lam) - math.lgamma(actual + 1))


def main():
    # Load the walk-forward ML/baseline predictions (already PIT-safe)
    wf = {}
    for row in csv.DictReader(open(ROOT / "ml" / "backtests" / "sot_backtest_results.csv")):
        wf[(row["match_date"], row["team_name"])] = row

    results = []
    for relpath, team_map in SOURCES:
        path = ROOT / relpath
        if not path.exists():
            print(f"  [skip] {relpath} not found")
            continue
        d = json.load(open(path))
        for key, team in team_map.items():
            if key not in d:
                continue
            p_over = market_prob_over(d[key])
            if p_over is None:
                continue
            threshold = parse_threshold(key)
            lam_market = implied_lambda(p_over, threshold)

            # find this team's row in the walk-forward results by team name
            # (date not stored in the market file, so match on team name + look
            # for the unique match this team+opponent pairing corresponds to)
            candidates = [v for (d_, t), v in wf.items() if t == team]
            if not candidates:
                print(f"  [no walk-forward row found] {team} ({relpath})")
                continue
            # disambiguate by opponent when possible
            opp_candidates = [c for c in candidates if c["opponent_name"] in team_map.values() or True]
            row = opp_candidates[-1] if len(opp_candidates) > 1 else opp_candidates[0]
            # prefer exact opponent match if the other team in this file is known
            others = [t for k2, t in team_map.items() if t != team]
            if others:
                exact = [c for c in candidates if c["opponent_name"] == others[0]]
                if exact:
                    row = exact[0]

            actual = float(row["actual"])
            lam_hier = float(row["lambda_hier"])
            lam_baseline = float(row["lambda_baseline"])

            results.append({
                "match": relpath.split("/")[1], "team": team, "threshold": threshold,
                "actual": actual, "lambda_market": round(lam_market, 3),
                "lambda_hier": round(lam_hier, 3), "lambda_baseline": round(lam_baseline, 3),
                "nll_market": nll(actual, lam_market), "nll_hier": nll(actual, lam_hier),
                "nll_baseline": nll(actual, lam_baseline),
            })

    print(f"\n{'match':30s} {'team':12s} {'actual':>7s} {'mkt_lam':>8s} {'hier_lam':>9s} {'base_lam':>9s} "
          f"{'nll_mkt':>8s} {'nll_hier':>9s} {'nll_base':>9s}")
    for r in results:
        print(f"{r['match']:30s} {r['team']:12s} {r['actual']:7.0f} {r['lambda_market']:8.2f} "
              f"{r['lambda_hier']:9.2f} {r['lambda_baseline']:9.2f} "
              f"{r['nll_market']:8.3f} {r['nll_hier']:9.3f} {r['nll_baseline']:9.3f}")

    n = len(results)
    mean_mkt = sum(r["nll_market"] for r in results) / n
    mean_hier = sum(r["nll_hier"] for r in results) / n
    mean_base = sum(r["nll_baseline"] for r in results) / n
    print(f"\nn = {n} team-match observations with a real saved market line")
    print(f"Mean NLL -- market: {mean_mkt:.4f}   ML (hierarchical): {mean_hier:.4f}   baseline (k=5): {mean_base:.4f}")

    diffs_mkt_hier = [r["nll_market"] - r["nll_hier"] for r in results]
    mean_diff = sum(diffs_mkt_hier) / n
    var = sum((x - mean_diff) ** 2 for x in diffs_mkt_hier) / (n - 1) if n > 1 else 0
    se = (var / n) ** 0.5 if n > 1 else float("nan")
    t = mean_diff / se if se > 0 else float("nan")
    print(f"\nMean diff (market NLL - ML NLL): {mean_diff:+.4f}  (positive = ML beats market)  t={t:.3f} (n={n}, very low power)")

    with open(ROOT / "ml" / "backtests" / "sot_vs_market_comparison.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)
    print(f"\nWrote sot_vs_market_comparison.csv")


if __name__ == "__main__":
    main()
