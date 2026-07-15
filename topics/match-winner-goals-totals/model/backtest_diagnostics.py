"""
Two diagnostics to discriminate between the two leading explanations for the
"~5-8pp compression toward 50/50" calibration gap found by backtest_harness.py:

Check A -- logit-space gap. For each calibration bucket, compute the gap
between predicted and actual P(home win) in TWO scales:
  - raw probability gap:  actual_rate - predicted_rate
  - logit (log-odds) gap: logit(actual_rate) - mean(logit(predicted_p))
If the logit-space gap is roughly CONSTANT across buckets (while the raw gap
varies), that's the signature of a single multiplicative attenuation factor
on the Elo-diff coefficient (b2) -- i.e. the "noisy Elo ruler" explanation.
If the raw-probability gap is the one that's roughly constant instead, that
points toward an additive miscalibration (e.g. home-advantage related).

Check B -- neutral vs non-neutral split. Re-run the same calibration table
separately for matches with neutral=TRUE (no home advantage applies) and
neutral=FALSE. If the gap persists (similar size) for NEUTRAL matches --
where home advantage plays zero role -- that rules out home-advantage as the
(main) cause and points back to Elo-diff/b2 attenuation.

Reuses predict_one/actual_outcome from backtest_harness.py and the same
PIT Elo panel + fitted Poisson coefficients. rho defaults to the MLE-fitted
-0.06 (from fit_rho.py --since 1990-01-01), overridable via --rho.

Usage:
    python3 backtest_diagnostics.py
    python3 backtest_diagnostics.py --since 1990-01-01
"""

import argparse
import csv
import json
import math
from pathlib import Path

import backtest_harness as bh

ROOT = Path(__file__).resolve().parents[3]
PANEL_CSV = ROOT / "data" / "processed" / "elo_match_panel.csv"
COEFS_JSON = ROOT / "topics" / "match-winner-goals-totals" / "coefs" / "poisson_goals_coefs.json"

N_BINS = 10


def logit(p, eps=1e-6):
    p = min(max(p, eps), 1 - eps)
    return math.log(p / (1 - p))


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


class Bucketer:
    def __init__(self):
        self.pred_sum = [0.0] * N_BINS
        self.pred_logit_sum = [0.0] * N_BINS
        self.actual_sum = [0.0] * N_BINS
        self.count = [0] * N_BINS

    def add(self, p_home, actual_is_home_win):
        b = min(int(p_home * N_BINS), N_BINS - 1)
        self.pred_sum[b] += p_home
        self.pred_logit_sum[b] += logit(p_home)
        self.actual_sum[b] += 1.0 if actual_is_home_win else 0.0
        self.count[b] += 1

    def report(self, label):
        print(f"\n=== {label} ===")
        print(f"{'Bucket':>10} {'N':>7} {'Pred':>8} {'Actual':>8} "
              f"{'RawGap':>8} {'LogitPred':>10} {'LogitAct':>10} {'LogitGap':>9}")
        for i in range(N_BINS):
            n = self.count[i]
            if n == 0:
                continue
            pred_avg = self.pred_sum[i] / n
            actual_avg = self.actual_sum[i] / n
            raw_gap = actual_avg - pred_avg
            logit_pred_avg = self.pred_logit_sum[i] / n
            logit_actual = logit(actual_avg)
            logit_gap = logit_actual - logit_pred_avg
            lo, hi = i / N_BINS, (i + 1) / N_BINS
            print(f"{lo:.1f}-{hi:.1f}   {n:>7} {pred_avg:>8.3f} {actual_avg:>8.3f} "
                  f"{raw_gap:>+8.3f} {logit_pred_avg:>10.3f} {logit_actual:>10.3f} {logit_gap:>+9.3f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default=None, help="YYYY-MM-DD")
    parser.add_argument("--rho", type=float, default=-0.06, help="Dixon-Coles rho (default: MLE-fitted -0.06)")
    args = parser.parse_args()

    bh.RHO = args.rho

    coefs = json.load(open(COEFS_JSON))
    b0, b1, b2 = coefs["intercept"], coefs["home_advantage"], coefs["elo_diff_coef"]

    rows = load_rows(args.since)
    print(f"Loaded {len(rows)} matches" + (f" since {args.since}" if args.since else "") +
          f" (rho={args.rho})")

    overall = Bucketer()
    neutral = Bucketer()
    non_neutral = Bucketer()

    for row in rows:
        res, _ = bh.predict_one(row, b0, b1, b2)
        actual = bh.actual_outcome(row)
        p_home = res["home_win"]
        is_home_win = (actual == "home_win")

        overall.add(p_home, is_home_win)
        if row["neutral"] == "TRUE":
            neutral.add(p_home, is_home_win)
        else:
            non_neutral.add(p_home, is_home_win)

    overall.report("ALL MATCHES")
    neutral.report("NEUTRAL=TRUE (no home advantage applies)")
    non_neutral.report("NEUTRAL=FALSE (home advantage applies)")

    print("\nN(neutral=TRUE) =", sum(neutral.count), "  N(neutral=FALSE) =", sum(non_neutral.count))


if __name__ == "__main__":
    main()
