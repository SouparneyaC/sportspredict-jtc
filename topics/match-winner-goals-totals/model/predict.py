"""
End-to-end prediction for a single fixture: load current Elo ratings
(elo.py output) and fitted Poisson coefficients (poisson_goals.py
output), compute (lambda_home, lambda_away), build the Dixon-Coles
scoreline grid, and answer the two market categories we currently
cover with no proxy layers: match result and total goals.

Example (MEX vs RSA, 2026-06-11, Mexico City, neutral=False -- Mexico
is the home team and gets the +1 home-advantage term):

    python3 predict.py "Mexico" "South Africa" --neutral false

This prints:
  - lambda_home, lambda_away (expected goals for each side)
  - P(home win) / P(draw) / P(away win)   -> "Will Mexico win the match?"
  - P(total goals <= 2)                   -> "Will the match have 2 or
                                               fewer total goals?"

Prerequisites (run once, in order):
  1. python3 model/elo.py                                          -> elo_current_ratings.csv, elo_match_panel.csv
  2. python3 topics/match-winner-goals-totals/model/poisson_goals.py -> poisson_goals_coefs.json

RHO_DEFAULT is a placeholder for the Dixon-Coles low-score correlation
parameter (see dixon_coles.fit_rho) -- not yet estimated from data.
"""

import argparse
import csv
import json
import math
from pathlib import Path

from dixon_coles import scoreline_grid, match_result_probs, total_goals_over_under

ROOT = Path(__file__).resolve().parents[3]
RATINGS_CSV = ROOT / "data" / "processed" / "elo_current_ratings.csv"
COEFS_JSON = ROOT / "topics" / "match-winner-goals-totals" / "coefs" / "poisson_goals_coefs.json"

RHO_DEFAULT = -0.1  # placeholder; fit via dixon_coles.fit_rho in the backtest


def load_ratings():
    ratings = {}
    with open(RATINGS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ratings[row["team"]] = float(row["elo_rating"])
    return ratings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("home_team")
    parser.add_argument("away_team")
    parser.add_argument("--neutral", choices=["true", "false"], default="false")
    parser.add_argument("--goal-threshold", type=int, default=2,
                         help="for 'total goals <= N' style markets")
    args = parser.parse_args()

    ratings = load_ratings()
    coefs = json.load(open(COEFS_JSON))

    elo_home = ratings[args.home_team]
    elo_away = ratings[args.away_team]

    home_adv = 0.0 if args.neutral == "true" else 1.0

    b0 = coefs["intercept"]
    b1 = coefs["home_advantage"]
    b2 = coefs["elo_diff_coef"]

    lam_home = math.exp(b0 + b1 * home_adv + b2 * (elo_home - elo_away))
    lam_away = math.exp(b0 + b2 * (elo_away - elo_home))

    grid = scoreline_grid(lam_home, lam_away, rho=RHO_DEFAULT)

    print(f"Elo: {args.home_team}={elo_home:.1f}, {args.away_team}={elo_away:.1f}")
    print(f"Expected goals: lambda_home={lam_home:.3f}, lambda_away={lam_away:.3f}")
    print()

    res = match_result_probs(grid)
    print(f"Will {args.home_team} win the match?  P = {res['home_win']:.3f}")
    print(f"Draw probability:                     P = {res['draw']:.3f}")
    print(f"Will {args.away_team} win the match?  P = {res['away_win']:.3f}")
    print()

    tot = total_goals_over_under(grid, threshold=args.goal_threshold)
    print(f"Will the match have {args.goal_threshold} or fewer total goals?  "
          f"P = {tot['under_or_equal']:.3f}")


if __name__ == "__main__":
    main()
