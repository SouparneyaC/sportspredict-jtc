"""
Calibration check for "total goals <= GOAL_THRESHOLD" using the
Negative-Binomial scoreline grid (alpha, rho_nb from
fit_nb_dispersion.py), for direct comparison against
goal_totals_diagnostics.py's Poisson-based table.

Usage:
    python3 goal_totals_diagnostics_nb.py
    python3 goal_totals_diagnostics_nb.py --since 2010-01-01 --threshold 2
"""

import argparse
import json
import math
from pathlib import Path

from backtest_diagnostics import Bucketer, load_rows
from dixon_coles import scoreline_grid_nb, total_goals_over_under

ROOT = Path(__file__).resolve().parents[3]
POISSON_COEFS_JSON = ROOT / "topics" / "match-winner-goals-totals" / "coefs" / "poisson_goals_coefs.json"
NB_COEFS_JSON = ROOT / "topics" / "match-winner-goals-totals" / "coefs" / "nb_dispersion_coefs.json"

MAX_GOALS = 8


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default=None, help="YYYY-MM-DD")
    parser.add_argument("--threshold", type=int, default=2)
    args = parser.parse_args()

    pcoefs = json.load(open(POISSON_COEFS_JSON))
    b0, b1, b2 = pcoefs["intercept"], pcoefs["home_advantage"], pcoefs["elo_diff_coef"]

    ncoefs = json.load(open(NB_COEFS_JSON))
    alpha, rho = ncoefs["alpha"], ncoefs["rho_nb"]

    rows = load_rows(args.since)
    print(f"Loaded {len(rows)} matches" + (f" since {args.since}" if args.since else "") +
          f" (alpha={alpha:.5f}, rho={rho}, threshold<={args.threshold})")

    overall = Bucketer()
    neutral = Bucketer()
    non_neutral = Bucketer()

    for row in rows:
        elo_home = float(row["elo_home_pre"])
        elo_away = float(row["elo_away_pre"])
        home_adv = 0.0 if row["neutral"] == "TRUE" else 1.0

        lam_home = math.exp(b0 + b1 * home_adv + b2 * (elo_home - elo_away))
        lam_away = math.exp(b0 + b2 * (elo_away - elo_home))

        grid = scoreline_grid_nb(lam_home, lam_away, alpha, rho=rho, max_goals=MAX_GOALS)
        tot = total_goals_over_under(grid, threshold=args.threshold)
        p_under = tot["under_or_equal"]

        hs, as_ = int(row["home_score"]), int(row["away_score"])
        actual_under = (hs + as_) <= args.threshold

        overall.add(p_under, actual_under)
        if row["neutral"] == "TRUE":
            neutral.add(p_under, actual_under)
        else:
            non_neutral.add(p_under, actual_under)

    overall.report(f"ALL MATCHES (NB) -- P(total goals <= {args.threshold})")
    neutral.report("NEUTRAL=TRUE (NB)")
    non_neutral.report("NEUTRAL=FALSE (NB)")

    print("\nN(neutral=TRUE) =", sum(neutral.count), "  N(neutral=FALSE) =", sum(non_neutral.count))


if __name__ == "__main__":
    main()
