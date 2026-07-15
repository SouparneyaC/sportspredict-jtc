"""
Backtest the ordered-logit match-result model against real bookmaker odds
(data/external/odds/international_fixture_odds.csv) -- the closest available
proxy for "the crowd" in the forecasting tournament.

For each fixture that appears in BOTH the odds file and elo_match_panel.csv
(matched on date + team names, with a small alias table for naming
mismatches) and has a final score:

  - market probabilities = de-vigged bookmaker odds (1/odds, renormalized)
  - model probabilities  = ordered_logit.predict_probs(elo_diff, home_adv, ...)
  - actual outcome from the panel's home_score/away_score

Reports, for both model and market:
  - mean Brier (3-way) and RPS
  - win rate (fraction of matches where model's Brier < market's Brier)
  - a sign test / binomial test for whether that win rate differs from 50%
  - a breakdown by market-implied favorite strength (to check for
    favorite-longshot-bias-style edges)

Usage:
    python3 backtest_vs_market.py
"""

import csv
import json
from pathlib import Path

from scipy import stats

from ordered_logit import predict_probs

ROOT = Path(__file__).resolve().parents[3]
PANEL_CSV = ROOT / "data" / "processed" / "elo_match_panel.csv"
ODDS_CSV = ROOT / "data" / "external" / "odds" / "international_fixture_odds.csv"
COEFS_JSON = ROOT / "topics" / "match-winner-goals-totals" / "coefs" / "ordered_logit_coefs.json"

ORDER = ["away_win", "draw", "home_win"]

# Map odds-data team names -> elo_match_panel team names
ALIASES = {
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Cape Verde Islands": "Cape Verde",
    "Congo DR": "DR Congo",
    "FYR Macedonia": "North Macedonia",
    "Rep. Of Ireland": "Republic of Ireland",
    "Türkiye": "Turkey",
    "USA": "United States",
    "andorra": "Andorra",
}

# Skip youth/age-restricted national teams -- not in elo_match_panel
YOUTH_SUFFIXES = (" U23", " U21", " U20", " U19", " U18", " U17")


def norm_team(name):
    if any(name.endswith(s) for s in YOUTH_SUFFIXES):
        return None
    return ALIASES.get(name, name)


def actual_outcome(hs, as_):
    if hs > as_:
        return "home_win"
    if hs == as_:
        return "draw"
    return "away_win"


def brier_3way(res, actual):
    return sum((res[o] - (1.0 if o == actual else 0.0)) ** 2 for o in ORDER)


def rps_3way(res, actual):
    cum_p, cum_a, total = 0.0, 0.0, 0.0
    actual_idx = ORDER.index(actual)
    for i, o in enumerate(ORDER):
        cum_p += res[o]
        cum_a += 1.0 if i == actual_idx else 0.0
        total += (cum_p - cum_a) ** 2
    return total / (len(ORDER) - 1)


def devig(odds_home, odds_draw, odds_away):
    raw = {"home_win": 1.0 / odds_home, "draw": 1.0 / odds_draw, "away_win": 1.0 / odds_away}
    overround = sum(raw.values())
    return {k: v / overround for k, v in raw.items()}, overround


def main():
    coefs = json.load(open(COEFS_JSON))
    b_elo, b_home, c1, c2 = coefs["b_elo"], coefs["b_home"], coefs["c1"], coefs["c2"]

    # index panel by (date, home_team, away_team)
    panel = {}
    with open(PANEL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["home_score"] == "":
                continue
            key = (row["date"], row["home_team"], row["away_team"])
            panel[key] = row

    matched = []
    n_odds_total = 0
    n_no_score = 0
    n_unmatched = 0
    with open(ODDS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            n_odds_total += 1
            if row["goals_home"] == "" or row["goals_away"] == "":
                n_no_score += 1
                continue
            home = norm_team(row["home_team"])
            away = norm_team(row["away_team"])
            if home is None or away is None:
                n_unmatched += 1
                continue
            date = row["date"][:10]
            key = (date, home, away)
            prow = panel.get(key)
            if prow is None:
                n_unmatched += 1
                continue
            try:
                odds_h, odds_d, odds_a = float(row["home_win"]), float(row["draw"]), float(row["away_win"])
            except ValueError:
                continue
            matched.append((row, prow, odds_h, odds_d, odds_a))

    print(f"Odds rows: {n_odds_total}  |  no final score: {n_no_score}  |  "
          f"unmatched to panel: {n_unmatched}  |  matched: {len(matched)}")

    model_briers, market_briers = [], []
    model_rps, market_rps = [], []
    model_wins = market_wins = ties = 0
    bucket_results = {}  # market favorite strength bucket -> [model_brier, market_brier] lists

    for row, prow, odds_h, odds_d, odds_a in matched:
        elo_diff = float(prow["elo_home_pre"]) - float(prow["elo_away_pre"])
        home_adv = 0.0 if prow["neutral"] == "TRUE" else 1.0
        model_p = predict_probs(elo_diff, home_adv, b_elo, b_home, c1, c2)

        market_p, overround = devig(odds_h, odds_d, odds_a)

        hs, as_ = int(prow["home_score"]), int(prow["away_score"])
        actual = actual_outcome(hs, as_)

        mb = brier_3way(model_p, actual)
        kb = brier_3way(market_p, actual)
        mr = rps_3way(model_p, actual)
        kr = rps_3way(market_p, actual)

        model_briers.append(mb)
        market_briers.append(kb)
        model_rps.append(mr)
        market_rps.append(kr)

        if mb < kb - 1e-12:
            model_wins += 1
        elif kb < mb - 1e-12:
            market_wins += 1
        else:
            ties += 1

        # bucket by market's favorite probability (max of the 3)
        fav_p = max(market_p.values())
        if fav_p < 0.40:
            bucket = "toss-up (<0.40)"
        elif fav_p < 0.55:
            bucket = "lean (0.40-0.55)"
        elif fav_p < 0.70:
            bucket = "moderate fav (0.55-0.70)"
        else:
            bucket = "heavy fav (>=0.70)"
        bucket_results.setdefault(bucket, []).append((mb, kb))

    n = len(matched)
    print(f"\n=== Overall (N={n}) ===")
    print(f"Mean Brier  -- model: {sum(model_briers)/n:.4f}   market: {sum(market_briers)/n:.4f}")
    print(f"Mean RPS    -- model: {sum(model_rps)/n:.4f}   market: {sum(market_rps)/n:.4f}")
    print(f"Head-to-head (lower Brier wins): model {model_wins}, market {market_wins}, ties {ties}")

    # sign test: binomial test on model_wins vs (model_wins+market_wins), H0 p=0.5
    decisive = model_wins + market_wins
    if decisive > 0:
        result = stats.binomtest(model_wins, decisive, p=0.5)
        print(f"Sign test on decisive matches (N={decisive}): "
              f"model win rate = {model_wins/decisive:.3f}, p-value = {result.pvalue:.4f}")

    # paired t-test on Brier differences
    diffs = [m - k for m, k in zip(model_briers, market_briers)]
    t_result = stats.ttest_1samp(diffs, 0.0)
    print(f"Paired t-test on (model_brier - market_brier), mean diff = "
          f"{sum(diffs)/n:+.4f}, p-value = {t_result.pvalue:.4f}")

    # Diebold-Mariano-style: same as paired t-test on loss differential here
    # (no autocorrelation adjustment since matches are largely independent)

    print("\n=== By market favorite strength ===")
    for bucket in ["toss-up (<0.40)", "lean (0.40-0.55)", "moderate fav (0.55-0.70)", "heavy fav (>=0.70)"]:
        pairs = bucket_results.get(bucket, [])
        if not pairs:
            continue
        n_b = len(pairs)
        mb_mean = sum(p[0] for p in pairs) / n_b
        kb_mean = sum(p[1] for p in pairs) / n_b
        wins = sum(1 for p in pairs if p[0] < p[1] - 1e-12)
        print(f"{bucket:28s} N={n_b:4d}  model_brier={mb_mean:.4f}  "
              f"market_brier={kb_mean:.4f}  diff={mb_mean-kb_mean:+.4f}  model_win_rate={wins/n_b:.2f}")


if __name__ == "__main__":
    main()
