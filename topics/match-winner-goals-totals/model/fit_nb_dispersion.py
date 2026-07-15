"""
Fit a Negative-Binomial (NB2) overdispersion parameter alpha (variance =
mu + alpha*mu^2) for the goal-scoring distribution, addressing the
Poisson-overdispersion pattern found by goal_totals_diagnostics.py:
predicted P(total goals <= 2) was underconfident on the low end (model
0.06, actual 0.12) and overconfident in the 0.6-0.7 range (model 0.61,
actual 0.50) -- the signature of fatter-than-Poisson tails in real
scorelines.

Step 1: fit alpha by maximum likelihood, holding mu = lambda_home /
        lambda_away fixed at the values implied by the existing fitted
        Poisson coefficients (poisson_goals_coefs.json) -- b0/b1/b2
        already model the MEAN correctly (per backtest_harness.py's
        match-result Brier/RPS); only the VARIANCE around that mean is
        being corrected here.

Step 2: re-fit the Dixon-Coles rho parameter using NB marginals + the
        fitted alpha (rho was originally fit assuming Poisson marginals;
        switching the marginal family changes the optimal low-score
        correction slightly). Grid-searched over a narrow range around
        the existing Poisson-fitted rho=-0.06.

Recency weighting for alpha: same exp(-XI*days_ago) scheme as
poisson_goals.py.

Output: topics/match-winner-goals-totals/coefs/nb_dispersion_coefs.json (alpha, rho_nb + metadata)

Usage:
    python3 fit_nb_dispersion.py
"""

import csv
import json
import math
from datetime import date
from pathlib import Path

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import nbinom

from dixon_coles import fit_rho, nb_pmf

ROOT = Path(__file__).resolve().parents[3]
PANEL_CSV = ROOT / "data" / "processed" / "elo_match_panel.csv"
POISSON_COEFS_JSON = ROOT / "topics" / "match-winner-goals-totals" / "coefs" / "poisson_goals_coefs.json"
OUT_JSON = ROOT / "topics" / "match-winner-goals-totals" / "coefs" / "nb_dispersion_coefs.json"

XI_DEFAULT = 0.0008


def load_rows():
    rows = []
    with open(PANEL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["home_score"] == "":
                continue
            rows.append(row)
    return rows


def main():
    rows = load_rows()
    coefs = json.load(open(POISSON_COEFS_JSON))
    b0, b1, b2 = coefs["intercept"], coefs["home_advantage"], coefs["elo_diff_coef"]

    most_recent = max(date.fromisoformat(r["date"]) for r in rows)

    ys, mus, ws = [], [], []
    matches_for_rho = []
    for r in rows:
        d = date.fromisoformat(r["date"])
        days_ago = (most_recent - d).days
        weight = math.exp(-XI_DEFAULT * days_ago)

        elo_home = float(r["elo_home_pre"])
        elo_away = float(r["elo_away_pre"])
        home_adv = 0.0 if r["neutral"] == "TRUE" else 1.0
        hs, as_ = int(r["home_score"]), int(r["away_score"])

        lam_home = math.exp(b0 + b1 * home_adv + b2 * (elo_home - elo_away))
        lam_away = math.exp(b0 + b2 * (elo_away - elo_home))

        ys.append(hs); mus.append(lam_home); ws.append(weight)
        ys.append(as_); mus.append(lam_away); ws.append(weight)

        matches_for_rho.append((hs, as_, lam_home, lam_away))

    ys = np.array(ys, dtype=float)
    mus = np.array(mus, dtype=float)
    ws = np.array(ws, dtype=float)

    def neg_ll(alpha):
        alpha = max(alpha, 1e-8)
        r = 1.0 / alpha
        p = r / (r + mus)
        ll = nbinom.logpmf(ys, r, p)
        return -np.sum(ws * ll)

    result = minimize_scalar(neg_ll, bounds=(1e-6, 5.0), method="bounded")
    alpha = float(result.x)
    print(f"Fitted alpha = {alpha:.5f}  (NLL={result.fun:.2f})")
    print(f"  alpha=0 is Poisson; alpha>0 means fatter-than-Poisson tails")

    # re-fit rho using NB marginals + this alpha, narrow grid around -0.06
    pmf_nb = lambda k, lam: nb_pmf(k, lam, alpha)
    rho_grid = [r / 100 for r in range(-25, 11)]  # -0.25 .. 0.10
    rho_nb = fit_rho(matches_for_rho, lambda_fn=None, rho_grid=rho_grid, pmf=pmf_nb)
    print(f"Re-fitted rho (NB marginals) = {rho_nb}")

    out = {
        "alpha": alpha,
        "rho_nb": rho_nb,
        "n_observations": int(len(ys)),
        "xi_decay": XI_DEFAULT,
    }
    with open(OUT_JSON, "w") as f:
        json.dump(out, f, indent=2)
    print(f"Wrote {OUT_JSON}")


if __name__ == "__main__":
    main()
