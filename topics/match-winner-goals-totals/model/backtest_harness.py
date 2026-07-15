"""
Backtest harness: evaluate the fitted model's predictions against ALL
completed historical matches, using the point-in-time Elo ratings (no
lookahead) already stored in elo_match_panel.csv and the single globally-fit
Poisson coefficients in poisson_goals_coefs.json.

For each match:
  - compute lambda_home, lambda_away (same formula as predict.py)
  - build the Dixon-Coles scoreline grid (rho = RHO_DEFAULT placeholder)
  - get P(home win)/P(draw)/P(away win) and P(total goals <= GOAL_THRESHOLD)
  - compare to the actual result

Outputs:
  1. Mean Brier score and mean Ranked Probability Score (RPS) for the
     match-result market, vs the naive "33/33/33" baseline (Brier=0.667).
  2. Mean Brier score for the "total goals <= GOAL_THRESHOLD" market, vs
     the naive 50/50 baseline (Brier=0.5).
  3. A calibration table: bucket matches by predicted P(home win) into
     deciles, and compare to the actual home-win rate in each bucket. A
     well-calibrated model has predicted ~= actual in every bucket.

Caveat -- mild lookahead: poisson_goals_coefs.json was fit ONCE on the full
historical panel (all ~49k matches), so for older matches the coefficients
were influenced (a little) by data that postdates them. With recency
weighting (xi=0.0008, effective N~6850), this mostly affects matches in the
last ~10 years, where the influence is real but small. A fully rigorous
walk-forward backtest would refit b0/b1/b2 using only data strictly before
each test match (e.g. once per year) -- a natural follow-up once this
coarser version's results are understood.

Usage:
    python3 backtest_harness.py
    python3 backtest_harness.py --since 2010-01-01
    python3 backtest_harness.py --since 2010-01-01 --limit 5000
"""

import argparse
import csv
import json
import math
from pathlib import Path

from dixon_coles import scoreline_grid, match_result_probs, total_goals_over_under

ROOT = Path(__file__).resolve().parents[3]
PANEL_CSV = ROOT / "data" / "processed" / "elo_match_panel.csv"
COEFS_JSON = ROOT / "topics" / "match-winner-goals-totals" / "coefs" / "poisson_goals_coefs.json"

RHO_DEFAULT = -0.1  # placeholder; same as predict.py
GOAL_THRESHOLD = 2
RHO = RHO_DEFAULT
MAX_GOALS = 8

ORDER = ["away_win", "draw", "home_win"]  # ordinal, for RPS


def load_rows(since):
    rows = []
    with open(PANEL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["home_score"] == "":
                continue
            if since and row["date"] < since:
                continue
            rows.append(row)
    return rows


def predict_one(row, b0, b1, b2):
    elo_home = float(row["elo_home_pre"])
    elo_away = float(row["elo_away_pre"])
    home_adv = 0.0 if row["neutral"] == "TRUE" else 1.0

    lam_home = math.exp(b0 + b1 * home_adv + b2 * (elo_home - elo_away))
    lam_away = math.exp(b0 + b2 * (elo_away - elo_home))

    grid = scoreline_grid(lam_home, lam_away, rho=RHO, max_goals=MAX_GOALS)
    res = match_result_probs(grid)
    tot = total_goals_over_under(grid, threshold=GOAL_THRESHOLD)
    return res, tot


def actual_outcome(row):
    hs, as_ = int(row["home_score"]), int(row["away_score"])
    if hs > as_:
        return "home_win"
    if hs == as_:
        return "draw"
    return "away_win"


def brier_3way(res, actual):
    return sum((res[o] - (1.0 if o == actual else 0.0)) ** 2
                for o in ["home_win", "draw", "away_win"])


def rps_3way(res, actual):
    cum_p, cum_a, total = 0.0, 0.0, 0.0
    actual_idx = ORDER.index(actual)
    for i, o in enumerate(ORDER):
        cum_p += res[o]
        cum_a += 1.0 if i == actual_idx else 0.0
        total += (cum_p - cum_a) ** 2
    return total / (len(ORDER) - 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default=None, help="YYYY-MM-DD, only test matches on/after this date")
    parser.add_argument("--limit", type=int, default=None, help="cap number of matches (most recent N)")
    parser.add_argument("--rho", type=float, default=RHO_DEFAULT, help="Dixon-Coles rho (default: placeholder -0.1)")
    args = parser.parse_args()

    global RHO
    RHO = args.rho

    coefs = json.load(open(COEFS_JSON))
    b0, b1, b2 = coefs["intercept"], coefs["home_advantage"], coefs["elo_diff_coef"]

    rows = load_rows(args.since)
    if args.limit:
        rows = rows[-args.limit:]

    n = len(rows)
    print(f"Backtesting {n} matches" + (f" since {args.since}" if args.since else "") + "...")

    brier_sum = 0.0
    rps_sum = 0.0
    goal_brier_sum = 0.0

    n_bins = 10
    bucket_pred_sum = [0.0] * n_bins
    bucket_actual_sum = [0.0] * n_bins
    bucket_count = [0] * n_bins

    for row in rows:
        res, tot = predict_one(row, b0, b1, b2)
        actual = actual_outcome(row)

        brier_sum += brier_3way(res, actual)
        rps_sum += rps_3way(res, actual)

        hs, as_ = int(row["home_score"]), int(row["away_score"])
        actual_under = 1.0 if (hs + as_) <= GOAL_THRESHOLD else 0.0
        goal_brier_sum += (tot["under_or_equal"] - actual_under) ** 2

        p_home = res["home_win"]
        bucket = min(int(p_home * n_bins), n_bins - 1)
        bucket_pred_sum[bucket] += p_home
        bucket_actual_sum[bucket] += 1.0 if actual == "home_win" else 0.0
        bucket_count[bucket] += 1

    print()
    print(f"Mean Brier score (match result, 3-way): {brier_sum / n:.4f}")
    print(f"  (0=perfect, 0.667=naive 33/33/33 baseline, 2=worst)")
    print(f"Mean RPS (match result):                {rps_sum / n:.4f}")
    print(f"  (0=perfect, lower is better)")
    print(f"Mean Brier score (total goals <= {GOAL_THRESHOLD}):    {goal_brier_sum / n:.4f}")
    print(f"  (0=perfect, 0.5=naive 50/50 baseline, 1=worst)")

    print()
    print("Calibration: predicted P(home win) vs actual home-win rate, by decile")
    print(f"{'Bucket':>12} {'N':>8} {'Predicted':>10} {'Actual':>10}")
    for i in range(n_bins):
        if bucket_count[i] == 0:
            continue
        lo, hi = i / n_bins, (i + 1) / n_bins
        pred_avg = bucket_pred_sum[i] / bucket_count[i]
        actual_avg = bucket_actual_sum[i] / bucket_count[i]
        print(f"{lo:.1f}-{hi:.1f}     {bucket_count[i]:>8} {pred_avg:>10.3f} {actual_avg:>10.3f}")


if __name__ == "__main__":
    main()
