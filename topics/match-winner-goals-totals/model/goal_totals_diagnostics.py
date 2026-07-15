"""
Calibration check for the "total goals <= GOAL_THRESHOLD" market (Dixon-Coles
pipeline), using the same decile-bucket / raw-gap / logit-gap methodology as
backtest_diagnostics.py applied to the match-result market.

backtest_harness.py only reported an aggregate Brier score (0.249 vs naive
0.5) for this market -- that confirms the model beats a coin flip, but says
nothing about whether predicted P(total <= 2) is systematically too high or
too low, the way match-result P(home win) was found to be ~5-8pp too low.

Usage:
    python3 goal_totals_diagnostics.py
    python3 goal_totals_diagnostics.py --since 2010-01-01 --threshold 2
"""

import argparse
import json
from pathlib import Path

import backtest_harness as bh
from backtest_diagnostics import Bucketer, load_rows

ROOT = Path(__file__).resolve().parents[3]
COEFS_JSON = ROOT / "topics" / "match-winner-goals-totals" / "coefs" / "poisson_goals_coefs.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default=None, help="YYYY-MM-DD")
    parser.add_argument("--rho", type=float, default=-0.06, help="Dixon-Coles rho")
    parser.add_argument("--threshold", type=int, default=2, help="goal-total threshold")
    args = parser.parse_args()

    bh.RHO = args.rho
    bh.GOAL_THRESHOLD = args.threshold

    coefs = json.load(open(COEFS_JSON))
    b0, b1, b2 = coefs["intercept"], coefs["home_advantage"], coefs["elo_diff_coef"]

    rows = load_rows(args.since)
    print(f"Loaded {len(rows)} matches" + (f" since {args.since}" if args.since else "") +
          f" (rho={args.rho}, threshold<= {args.threshold})")

    overall = Bucketer()
    neutral = Bucketer()
    non_neutral = Bucketer()

    for row in rows:
        _, tot = bh.predict_one(row, b0, b1, b2)
        p_under = tot["under_or_equal"]

        hs, as_ = int(row["home_score"]), int(row["away_score"])
        actual_under = (hs + as_) <= args.threshold

        overall.add(p_under, actual_under)
        if row["neutral"] == "TRUE":
            neutral.add(p_under, actual_under)
        else:
            non_neutral.add(p_under, actual_under)

    overall.report(f"ALL MATCHES -- P(total goals <= {args.threshold})")
    neutral.report("NEUTRAL=TRUE")
    non_neutral.report("NEUTRAL=FALSE")

    print("\nN(neutral=TRUE) =", sum(neutral.count), "  N(neutral=FALSE) =", sum(non_neutral.count))


if __name__ == "__main__":
    main()
