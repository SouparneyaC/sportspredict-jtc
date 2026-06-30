"""
Single-match holdout check: take a match that has ALREADY happened (so we
know the actual score), look up the point-in-time Elo ratings as they stood
*before* this match (exactly as elo.py recorded them, with no lookahead),
feed those into the fitted Poisson + Dixon-Coles model as if it were a
future fixture, print the model's predicted probabilities, then reveal the
actual result and check where it falls.

This is a SANITY CHECK / DEMO, not a statistical validation. A single match
can't validate or invalidate a probabilistic model -- a well-calibrated
model that says "75% to win" is correct even in the 25% of cases where the
favourite loses. Real validation requires the walk-forward backtest (many
matches, Brier/RPS scores, calibration plot) described in research_notes.md.

Caveat: poisson_goals_coefs.json was fit on the FULL historical panel, which
includes this match's outcome (mild lookahead). With recency weighting
(xi=0.0008), the effective sample size is ~6850 match-equivalents, so one
match shifts the coefficients by roughly 1/6850 -- negligible for this demo.
The walk-forward backtest refits coefficients using only data strictly
before each test match, which removes this entirely.

Usage:
    python3 backtest_single.py "Russia" "Trinidad and Tobago" 2026-06-09
"""

import argparse
import csv
import json
import math
from pathlib import Path

from dixon_coles import scoreline_grid, match_result_probs, total_goals_over_under

ROOT = Path(__file__).resolve().parents[1]
PANEL_CSV = ROOT / "data" / "processed" / "elo_match_panel.csv"
COEFS_JSON = ROOT / "data" / "processed" / "poisson_goals_coefs.json"

RHO_DEFAULT = -0.1  # placeholder; same as predict.py


def find_match(home_team, away_team, date_str):
    with open(PANEL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (row["date"] == date_str and row["home_team"] == home_team
                    and row["away_team"] == away_team):
                return row
    raise SystemExit(f"No match found: {home_team} vs {away_team} on {date_str}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("home_team")
    parser.add_argument("away_team")
    parser.add_argument("date", help="YYYY-MM-DD")
    parser.add_argument("--goal-threshold", type=int, default=2)
    args = parser.parse_args()

    row = find_match(args.home_team, args.away_team, args.date)
    if row["home_score"] == "":
        raise SystemExit("This fixture hasn't been played yet -- no actual result to compare.")

    coefs = json.load(open(COEFS_JSON))
    b0, b1, b2 = coefs["intercept"], coefs["home_advantage"], coefs["elo_diff_coef"]

    elo_home = float(row["elo_home_pre"])
    elo_away = float(row["elo_away_pre"])
    home_adv = 0.0 if row["neutral"] == "TRUE" else 1.0

    lam_home = math.exp(b0 + b1 * home_adv + b2 * (elo_home - elo_away))
    lam_away = math.exp(b0 + b2 * (elo_away - elo_home))

    grid = scoreline_grid(lam_home, lam_away, rho=RHO_DEFAULT)
    res = match_result_probs(grid)
    tot = total_goals_over_under(grid, threshold=args.goal_threshold)

    print(f"=== PREDICTION (made using only data before {args.date}) ===")
    print(f"Elo: {args.home_team}={elo_home:.1f}, {args.away_team}={elo_away:.1f}")
    print(f"Expected goals: lambda_home={lam_home:.3f}, lambda_away={lam_away:.3f}")
    print(f"P({args.home_team} win) = {res['home_win']:.3f}")
    print(f"P(draw)                 = {res['draw']:.3f}")
    print(f"P({args.away_team} win) = {res['away_win']:.3f}")
    print(f"P(total goals <= {args.goal_threshold})    = {tot['under_or_equal']:.3f}")

    print()
    print("=== ACTUAL RESULT ===")
    hs, as_ = int(row["home_score"]), int(row["away_score"])
    print(f"{args.home_team} {hs} - {as_} {args.away_team}")

    if hs > as_:
        actual = "home_win"
    elif hs == as_:
        actual = "draw"
    else:
        actual = "away_win"
    actual_total_under = (hs + as_) <= args.goal_threshold

    print()
    print("=== SCORING ===")
    print(f"Model's probability for what actually happened ({actual.replace('_', ' ')}): "
          f"{res[actual]:.3f}")
    print(f"Model's probability for 'total <= {args.goal_threshold}' "
          f"(actual: {'yes' if actual_total_under else 'no'}): "
          f"{tot['under_or_equal'] if actual_total_under else tot['over']:.3f}")

    # Brier score for the 3-way match-result market (0 = perfect, 2 = worst,
    # 0.667 = always guessing 1/3-1/3-1/3)
    outcomes = ["home_win", "draw", "away_win"]
    brier = sum((res[o] - (1.0 if o == actual else 0.0)) ** 2 for o in outcomes)
    print(f"Brier score (match result, 3-way): {brier:.3f}")


if __name__ == "__main__":
    main()
