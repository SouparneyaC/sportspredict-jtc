"""
Combined/total-threshold composition test, pre-registered in
PREREGISTRATION_cards_corners_offsides_and_combined.md. Reuses the
already-fit, already-backtested per-team lambda predictions (no refitting --
sum of two independent Poissons is Poisson(lambda_a+lambda_b), closed form)
to test whether convolving the per-team hierarchical predictions beats (a)
convolving the per-team k=5-baseline predictions and (b) the walk-forward
expanding global match-mean (the same "floor" used throughout this backtest
suite) on the actual JTC question shape: "N+ combined [stat], both teams".

Only run for families whose per-team model passed the FDR-adjusted bar in
run_all_family_backtests.R: SOT, corners, offsides. Cards excluded (failed).

Usage:
    python3 combined_threshold_backtest.py
"""
import csv
import math
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent
FAMILIES = ["sot", "offsides", "corners"]
# Per-family results now live in topics/<slug>/ (moved out of ml/backtests/ during
# the topic-based reorg); this script stays here as shared cross-family infra.
OUTPUT_DIR = {"sot": "../../topics/shots-on-target", "offsides": "../../topics/offsides",
              "corners": "../../topics/corners"}
FILE_MAP = {fam: f"{OUTPUT_DIR[fam]}/{fam}_backtest_results.csv" for fam in FAMILIES}


def poisson_pmf(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def poisson_sf(k, lam):  # P(X >= k)
    return 1 - sum(poisson_pmf(i, lam) for i in range(k))


def nll(actual, lam):
    return -( -lam + actual * math.log(lam) - math.lgamma(actual + 1) )


def main():
    for fam in FAMILIES:
        path = ROOT / FILE_MAP[fam]
        rows = list(csv.DictReader(open(path)))
        by_match = defaultdict(list)
        for r in rows:
            by_match[r["match_id"]].append(r)

        # running expanding global mean of the COMBINED stat, walk-forward by date
        matches = []
        for mid, pair in by_match.items():
            if len(pair) != 2:
                continue
            date = pair[0]["match_date"]
            combined_actual = float(pair[0]["actual"]) + float(pair[1]["actual"])
            combined_lambda_hier = float(pair[0]["lambda_hier"]) + float(pair[1]["lambda_hier"])
            combined_lambda_baseline = float(pair[0]["lambda_baseline"]) + float(pair[1]["lambda_baseline"])
            matches.append({"match_id": mid, "date": date, "actual": combined_actual,
                             "lambda_hier": combined_lambda_hier, "lambda_baseline": combined_lambda_baseline})
        matches.sort(key=lambda m: (m["date"], m["match_id"]))

        # expanding global-mean floor (walk-forward, strictly-prior combined values only)
        prior_vals = []
        results = []
        for m in matches:
            global_mean = sum(prior_vals) / len(prior_vals) if prior_vals else m["lambda_baseline"]
            thresh = round(m["lambda_baseline"])
            actual_int = round(m["actual"])
            results.append({
                **m, "threshold": thresh,
                "nll_hier": nll(actual_int, m["lambda_hier"]),
                "nll_baseline": nll(actual_int, m["lambda_baseline"]),
                "nll_global": nll(actual_int, max(global_mean, 0.05)),
                "brier_hier": (poisson_sf(thresh, m["lambda_hier"]) - (1 if actual_int >= thresh else 0)) ** 2,
                "brier_baseline": (poisson_sf(thresh, m["lambda_baseline"]) - (1 if actual_int >= thresh else 0)) ** 2,
            })
            prior_vals.append(m["actual"])

        n = len(results)
        mean_nll_h = sum(r["nll_hier"] for r in results) / n
        mean_nll_b = sum(r["nll_baseline"] for r in results) / n
        mean_nll_g = sum(r["nll_global"] for r in results) / n
        mean_br_h = sum(r["brier_hier"] for r in results) / n
        mean_br_b = sum(r["brier_baseline"] for r in results) / n

        diffs = [r["nll_baseline"] - r["nll_hier"] for r in results]
        mean_diff = sum(diffs) / n
        var_diff = sum((d - mean_diff) ** 2 for d in diffs) / (n - 1)
        se = (var_diff / n) ** 0.5
        t_stat = mean_diff / se if se > 0 else float("nan")

        print(f"\n=== Combined-threshold: {fam.upper()} (n={n} matches) ===")
        print(f"  Mean NLL: global-only={mean_nll_g:.4f}  baseline-convolved={mean_nll_b:.4f}  hier-convolved={mean_nll_h:.4f}")
        print(f"  Mean Brier: baseline-convolved={mean_br_b:.4f}  hier-convolved={mean_br_h:.4f}")
        print(f"  Mean diff (baseline-hier): {mean_diff:+.4f}  t-stat: {t_stat:.3f}  (n={n}, ~t-dist df={n-1})")

        out = ROOT / Path(OUTPUT_DIR[fam]) / f"combined_{fam}_backtest_results.csv"
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            w.writeheader()
            w.writerows(results)


if __name__ == "__main__":
    main()
