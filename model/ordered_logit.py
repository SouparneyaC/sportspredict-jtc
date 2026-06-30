"""
Alternative/parallel stage: an ordered logistic regression (proportional-odds
model) of match outcome (away_win < draw < home_win) on Elo difference and
home advantage, following Hvattum & Arntzen (2010) S4.3.

Unlike poisson_goals.py + dixon_coles.py (which fit GOAL COUNTS and DERIVE
win/draw/loss probabilities from the resulting scoreline grid), this model
is fit DIRECTLY against the win/draw/loss outcomes -- so it is, by
construction, calibrated against P(home win) etc. This is the property the
goals-based pipeline is missing, per backtest_diagnostics.py's findings of a
persistent ~+0.25 to +0.35 logit-space gap.

    eta = b_elo * elo_diff + b_home * home_adv

    P(away_win) = sigmoid(c1 - eta)
    P(draw)     = sigmoid(c2 - eta) - sigmoid(c1 - eta)
    P(home_win) = 1 - sigmoid(c2 - eta)

    elo_diff = elo_home_pre - elo_away_pre
    home_adv = 1 if neutral == FALSE else 0  (matches predict.py /
               backtest_harness.py / poisson_goals.py)

c1 < c2 are fitted "cutpoint" parameters, reparametrized internally as
c2 = c1 + exp(delta) during optimization to enforce ordering.

Recency weighting: same exp(-XI * days_before_most_recent_match) scheme as
poisson_goals.py (XI_DEFAULT=0.0008), applied as a weighted log-likelihood.

Input:  data/processed/elo_match_panel.csv
Output: data/processed/ordered_logit_coefs.json (b_elo, b_home, c1, c2 + metadata)

Usage:
    python3 ordered_logit.py
"""

import csv
import json
import math
from datetime import date
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
PANEL_CSV = ROOT / "data" / "processed" / "elo_match_panel.csv"
COEFS_OUT = ROOT / "data" / "processed" / "ordered_logit_coefs.json"

XI_DEFAULT = 0.0008  # same recency decay as poisson_goals.py


def load_panel():
    rows = []
    with open(PANEL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["home_score"] == "":
                continue  # future fixture, no outcome to train on
            rows.append(row)
    return rows


def build_data(rows, xi=XI_DEFAULT):
    most_recent = max(date.fromisoformat(r["date"]) for r in rows)

    elo_diff, home_adv, y, w = [], [], [], []
    for r in rows:
        d = date.fromisoformat(r["date"])
        days_ago = (most_recent - d).days
        weight = math.exp(-xi * days_ago)

        elo_diff.append(float(r["elo_home_pre"]) - float(r["elo_away_pre"]))
        home_adv.append(0.0 if r["neutral"] == "TRUE" else 1.0)

        hs, as_ = int(r["home_score"]), int(r["away_score"])
        if hs > as_:
            y.append(2)  # home_win
        elif hs == as_:
            y.append(1)  # draw
        else:
            y.append(0)  # away_win
        w.append(weight)

    return (np.array(elo_diff), np.array(home_adv), np.array(y, dtype=int), np.array(w))


def sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def neg_log_likelihood(params, elo_diff, home_adv, y, w):
    b_elo, b_home, c1, delta = params
    c2 = c1 + math.exp(delta)
    eta = b_elo * elo_diff + b_home * home_adv

    p_away = sigmoid(c1 - eta)
    p_le_draw = sigmoid(c2 - eta)
    p_home = 1.0 - p_le_draw
    p_draw = p_le_draw - p_away

    eps = 1e-12
    p_away = np.clip(p_away, eps, 1.0)
    p_draw = np.clip(p_draw, eps, 1.0)
    p_home = np.clip(p_home, eps, 1.0)

    ll = np.where(y == 0, np.log(p_away), np.where(y == 1, np.log(p_draw), np.log(p_home)))
    return -np.sum(w * ll)


def predict_probs(elo_diff, home_adv, b_elo, b_home, c1, c2):
    """Return P(away_win)/P(draw)/P(home_win) for one fixture."""
    eta = b_elo * elo_diff + b_home * home_adv
    p_away = sigmoid(c1 - eta)
    p_le_draw = sigmoid(c2 - eta)
    p_home = 1.0 - p_le_draw
    p_draw = p_le_draw - p_away
    return {"away_win": float(p_away), "draw": float(p_draw), "home_win": float(p_home)}


def main():
    rows = load_panel()
    elo_diff, home_adv, y, w = build_data(rows)

    # initial guesses: b_elo ~ 0.004 (logit/Elo-point, ballpark from
    # standard Elo win-probability scale of ~1/175), b_home ~ 0.3,
    # c1 < c2 chosen so an even match (eta=0) gives roughly the league-wide
    # away/draw/home base rates.
    x0 = np.array([0.004, 0.3, -0.7, 0.0])  # delta=0 -> c2 = c1 + 1

    result = minimize(
        neg_log_likelihood, x0,
        args=(elo_diff, home_adv, y, w),
        method="L-BFGS-B",
    )

    b_elo, b_home, c1, delta = result.x
    c2 = c1 + math.exp(delta)

    print("Optimization success:", result.success, "-", result.message)
    print(f"b_elo  = {b_elo:.6f}")
    print(f"b_home = {b_home:.6f}")
    print(f"c1     = {c1:.4f}")
    print(f"c2     = {c2:.4f}")
    print(f"Negative log-likelihood: {result.fun:.2f}")

    # sanity check: implied probabilities for an even match (elo_diff=0)
    even_neutral = predict_probs(0.0, 0.0, b_elo, b_home, c1, c2)
    even_home = predict_probs(0.0, 1.0, b_elo, b_home, c1, c2)
    print(f"\nEven match, neutral venue: {even_neutral}")
    print(f"Even match, home advantage: {even_home}")

    coefs = {
        "b_elo": float(b_elo),
        "b_home": float(b_home),
        "c1": float(c1),
        "c2": float(c2),
        "xi_decay": XI_DEFAULT,
        "n_matches": len(rows),
    }

    with open(COEFS_OUT, "w") as f:
        json.dump(coefs, f, indent=2)
    print(f"\nWrote {COEFS_OUT}")


if __name__ == "__main__":
    main()
