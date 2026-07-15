"""
Fit the Dixon-Coles low-score correlation parameter rho by maximum
likelihood over the historical panel, replacing the RHO_DEFAULT=-0.1
placeholder used by predict.py and backtest_harness.py.

For each completed match, computes (lambda_home, lambda_away) from the
fitted Poisson coefficients and PIT Elo ratings (same as predict_one() in
backtest_harness.py), then grid-searches rho to maximize total
log-likelihood of the actual scorelines under the DC-corrected Poisson
model (dixon_coles.fit_rho).

Usage:
    python3 fit_rho.py
    python3 fit_rho.py --since 1990-01-01
"""

import argparse
import csv
import json
import math
from pathlib import Path

from dixon_coles import fit_rho

ROOT = Path(__file__).resolve().parents[3]
PANEL_CSV = ROOT / "data" / "processed" / "elo_match_panel.csv"
COEFS_JSON = ROOT / "topics" / "match-winner-goals-totals" / "coefs" / "poisson_goals_coefs.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default=None, help="YYYY-MM-DD")
    args = parser.parse_args()

    coefs = json.load(open(COEFS_JSON))
    b0, b1, b2 = coefs["intercept"], coefs["home_advantage"], coefs["elo_diff_coef"]

    matches = []
    with open(PANEL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["home_score"] == "":
                continue
            if args.since and row["date"] < args.since:
                continue

            elo_home = float(row["elo_home_pre"])
            elo_away = float(row["elo_away_pre"])
            home_adv = 0.0 if row["neutral"] == "TRUE" else 1.0

            lam_home = math.exp(b0 + b1 * home_adv + b2 * (elo_home - elo_away))
            lam_away = math.exp(b0 + b2 * (elo_away - elo_home))

            hg, ag = int(row["home_score"]), int(row["away_score"])
            matches.append((hg, ag, lam_home, lam_away))

    print(f"Fitting rho over {len(matches)} matches" +
          (f" since {args.since}" if args.since else "") + "...")

    best_rho = fit_rho(matches, lambda_fn=None)
    print(f"Best-fit rho: {best_rho}")


if __name__ == "__main__":
    main()
