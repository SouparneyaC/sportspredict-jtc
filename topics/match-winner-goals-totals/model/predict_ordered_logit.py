"""
End-to-end match-result prediction using the ordered-logit model
(ordered_logit.py) instead of the Poisson + Dixon-Coles pipeline.

This model is fit DIRECTLY on win/draw/loss outcomes (Hvattum & Arntzen
2010 S4.3), and backtests substantially better-calibrated than the
goals-based pipeline, especially in the high-confidence (0.6-1.0) range
-- see ordered_logit_diagnostics.py.

NOTE: this model only covers the match-result market (P(home win) /
P(draw) / P(away win)). For goal-total markets (e.g. "total goals <= 2"),
continue to use predict.py (Poisson + Dixon-Coles) -- the ordered logit
has no notion of goal counts.

Example:
    python3 predict_ordered_logit.py "Mexico" "South Africa" --neutral false

Prerequisites (run once, in order):
  1. python3 model/elo.py                                          -> elo_current_ratings.csv
  2. python3 topics/match-winner-goals-totals/model/ordered_logit.py -> ordered_logit_coefs.json
"""

import argparse
import csv
import json
from pathlib import Path

from ordered_logit import predict_probs

ROOT = Path(__file__).resolve().parents[3]
RATINGS_CSV = ROOT / "data" / "processed" / "elo_current_ratings.csv"
COEFS_JSON = ROOT / "topics" / "match-winner-goals-totals" / "coefs" / "ordered_logit_coefs.json"


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
    args = parser.parse_args()

    ratings = load_ratings()
    coefs = json.load(open(COEFS_JSON))

    elo_home = ratings[args.home_team]
    elo_away = ratings[args.away_team]
    elo_diff = elo_home - elo_away
    home_adv = 0.0 if args.neutral == "true" else 1.0

    res = predict_probs(elo_diff, home_adv,
                         coefs["b_elo"], coefs["b_home"], coefs["c1"], coefs["c2"])

    print(f"Elo: {args.home_team}={elo_home:.1f}, {args.away_team}={elo_away:.1f} "
          f"(diff={elo_diff:+.1f}), neutral={args.neutral}")
    print()
    print(f"Will {args.home_team} win the match?  P = {res['home_win']:.3f}")
    print(f"Draw probability:                     P = {res['draw']:.3f}")
    print(f"Will {args.away_team} win the match?  P = {res['away_win']:.3f}")


if __name__ == "__main__":
    main()
