"""
Stage 2: a Poisson regression of goals scored on PIT Elo ratings,
following Hvattum & Arntzen (2010) (research_notes.md S4) -- Elo
difference as the team-strength covariate, plus a home-advantage term.

This IS a regression -- a classical Generalized Linear Model (Poisson
family, log link), with 3 parameters fit by maximum likelihood. It is
NOT a machine-learning model in the black-box sense (no trees, no
neural nets) -- it's the same family of model used in DC97 and
Hvattum & Arntzen, chosen for interpretability (each coefficient has a
direct meaning) and because it plugs directly into the Dixon-Coles
scoreline grid in Stage 3.

Two "observations" are created per historical match (one for each
team's goal count):

    log(lambda) = b0 + b1 * home_adv + b2 * elo_diff

    elo_diff = (own_elo_pre - opponent_elo_pre), from the scoring
               team's perspective
    home_adv = 1 if this team is the listed home team AND neutral=FALSE,
               else 0 -- matches the home_adv definition used by
               predict.py / backtest_harness.py / backtest_diagnostics.py
               (a match on neutral ground confers no home advantage to
               either side, so neither team's row gets home_adv=1).

For a future fixture (home team H vs away team A, neutral=False):

    lambda_H = exp(b0 + b1 + b2 * (Elo_H - Elo_A))
    lambda_A = exp(b0      + b2 * (Elo_A - Elo_H))

Input:  data/processed/elo_match_panel.csv (from elo.py)
Output: data/processed/poisson_goals_coefs.json  (b0, b1, b2 + metadata)

Recency weighting: per DC97 (research_notes.md S1.3/1.4), older matches
are down-weighted by exp(-XI * days_before_most_recent_match). XI is a
tunable decay rate -- XI=0 means "all 50,000+ matches since 1872
weighted equally," which is almost certainly wrong (a team's 1925
strength says little about 2026). XI_DEFAULT below is a placeholder
(~2.4-year half-life); the right value should be chosen by maximizing
out-of-sample predictive likelihood in the backtest harness, not
guessed -- this script exposes it as a parameter for that purpose.

Dependencies: numpy, statsmodels (not yet verified as installed).
"""

import csv
import json
import math
from datetime import date
from pathlib import Path

import numpy as np
import statsmodels.api as sm

ROOT = Path(__file__).resolve().parents[1]
PANEL_CSV = ROOT / "data" / "processed" / "elo_match_panel.csv"
COEFS_OUT = ROOT / "data" / "processed" / "poisson_goals_coefs.json"

XI_DEFAULT = 0.0008  # placeholder decay rate; tune via backtest


def load_panel():
    rows = []
    with open(PANEL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["home_score"] == "":
                continue  # future fixture, no outcome to train on
            rows.append(row)
    return rows


def build_design_matrix(rows, xi=XI_DEFAULT):
    most_recent = max(date.fromisoformat(r["date"]) for r in rows)

    y, X, w = [], [], []
    for r in rows:
        d = date.fromisoformat(r["date"])
        days_ago = (most_recent - d).days
        weight = math.exp(-xi * days_ago)

        elo_home = float(r["elo_home_pre"])
        elo_away = float(r["elo_away_pre"])
        hs, as_ = int(r["home_score"]), int(r["away_score"])
        home_adv = 0.0 if r["neutral"] == "TRUE" else 1.0

        # home team's goal-scoring observation
        y.append(hs)
        X.append([1.0, home_adv, elo_home - elo_away])
        w.append(weight)

        # away team's goal-scoring observation
        y.append(as_)
        X.append([1.0, 0.0, elo_away - elo_home])
        w.append(weight)

    return np.array(y), np.array(X), np.array(w)


def main():
    rows = load_panel()
    y, X, w = build_design_matrix(rows)

    model = sm.GLM(y, X, family=sm.families.Poisson(), freq_weights=w)
    result = model.fit()

    b0, b1, b2 = result.params
    coefs = {
        "intercept": float(b0),
        "home_advantage": float(b1),
        "elo_diff_coef": float(b2),
        "xi_decay": XI_DEFAULT,
        "n_matches": len(rows),
        "n_observations": len(y),
    }

    with open(COEFS_OUT, "w") as f:
        json.dump(coefs, f, indent=2)

    print(result.summary())
    print(f"Wrote {COEFS_OUT}")


if __name__ == "__main__":
    main()
