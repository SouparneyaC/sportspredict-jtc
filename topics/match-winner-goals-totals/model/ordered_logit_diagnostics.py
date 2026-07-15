"""
Calibration + accuracy check for the ordered-logit model (ordered_logit.py),
using the exact same diagnostics as backtest_diagnostics.py /
backtest_harness.py so the two approaches are directly comparable:

  - Brier score and RPS for the match-result market
  - Calibration table (predicted vs actual P(home win), by decile), with
    raw and logit-space gaps, split by ALL / NEUTRAL=TRUE / NEUTRAL=FALSE

Usage:
    python3 ordered_logit_diagnostics.py
    python3 ordered_logit_diagnostics.py --since 2010-01-01
"""

import argparse
import json
from pathlib import Path

from backtest_diagnostics import Bucketer, load_rows
from backtest_harness import actual_outcome, brier_3way, rps_3way
from ordered_logit import predict_probs

ROOT = Path(__file__).resolve().parents[3]
COEFS_JSON = ROOT / "topics" / "match-winner-goals-totals" / "coefs" / "ordered_logit_coefs.json"


def predict_one(row, b_elo, b_home, c1, c2):
    elo_diff = float(row["elo_home_pre"]) - float(row["elo_away_pre"])
    home_adv = 0.0 if row["neutral"] == "TRUE" else 1.0
    return predict_probs(elo_diff, home_adv, b_elo, b_home, c1, c2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default=None, help="YYYY-MM-DD")
    args = parser.parse_args()

    coefs = json.load(open(COEFS_JSON))
    b_elo, b_home, c1, c2 = coefs["b_elo"], coefs["b_home"], coefs["c1"], coefs["c2"]

    rows = load_rows(args.since)
    print(f"Loaded {len(rows)} matches" + (f" since {args.since}" if args.since else ""))
    print(f"Coefs: b_elo={b_elo:.6f} b_home={b_home:.6f} c1={c1:.4f} c2={c2:.4f}")

    overall = Bucketer()
    neutral = Bucketer()
    non_neutral = Bucketer()

    brier_sum = 0.0
    rps_sum = 0.0

    for row in rows:
        res = predict_one(row, b_elo, b_home, c1, c2)
        actual = actual_outcome(row)
        p_home = res["home_win"]
        is_home_win = (actual == "home_win")

        brier_sum += brier_3way(res, actual)
        rps_sum += rps_3way(res, actual)

        overall.add(p_home, is_home_win)
        if row["neutral"] == "TRUE":
            neutral.add(p_home, is_home_win)
        else:
            non_neutral.add(p_home, is_home_win)

    n = len(rows)
    print()
    print(f"Mean Brier score (match result, 3-way): {brier_sum / n:.4f}")
    print(f"  (0=perfect, 0.667=naive 33/33/33 baseline, 2=worst)")
    print(f"Mean RPS (match result):                {rps_sum / n:.4f}")
    print(f"  (0=perfect, lower is better)")

    overall.report("ALL MATCHES")
    neutral.report("NEUTRAL=TRUE (no home advantage applies)")
    non_neutral.report("NEUTRAL=FALSE (home advantage applies)")

    print("\nN(neutral=TRUE) =", sum(neutral.count), "  N(neutral=FALSE) =", sum(non_neutral.count))


if __name__ == "__main__":
    main()
