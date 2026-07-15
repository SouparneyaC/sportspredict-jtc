"""
Design #3 from the original research: use the GLMM as a bounded evidence
source alongside the market, never a full replacement -- exactly the
posture the shadow-deploy discipline calls for until GLMM has more than
11 matches of direct market comparison.

Blend rule (deliberately simple and pre-specified, NOT fit/optimized on the
n=11 comparison set -- optimizing the weight on 11 matches would just be
another small-n overfit):
    lambda_blend = w * lambda_glmm + (1-w) * lambda_market,  w = 0.25 (fixed)
    capped so the blended PROBABILITY can move at most +/-0.08 from the
    market-alone probability -- this is the direct fix for the CAN-MOR
    failure mode (a confident domain deviation from a real market blowing
    up a single question by -80 RBP). A wrong GLMM can shift the number a
    little; it structurally cannot cause that scale of damage again.

This script evaluates the blend against market-alone and GLMM-alone on the
existing 20-team-observation / 11-match comparison set (sot_vs_market_
comparison.csv) purely for a directional check -- explicitly NOT a
statistically powered test, same n=11 caveat as before.

Usage:
    python3 blend_market_glmm.py
"""
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
W = 0.25  # fixed, pre-specified -- not fit on the comparison data
CAP = 0.08  # max probability-point deviation from market alone


def nll(actual, lam):
    return -(-lam + actual * math.log(lam) - math.lgamma(actual + 1))


def pois_sf(k, lam):
    return 1 - sum(math.exp(-lam) * lam ** i / math.factorial(i) for i in range(k))


def blend(lam_market, lam_glmm, threshold, w=W, cap=CAP):
    lam_raw_blend = w * lam_glmm + (1 - w) * lam_market
    p_market = pois_sf(threshold, lam_market)
    p_raw_blend = pois_sf(threshold, lam_raw_blend)
    p_capped = max(p_market - cap, min(p_market + cap, p_raw_blend))
    return p_capped, p_market


def main():
    rows = list(csv.DictReader(open(ROOT / "sot_vs_market_comparison.csv")))
    nll_market, nll_glmm, nll_blend = [], [], []
    for r in rows:
        actual = int(float(r["actual"]))
        lam_m, lam_h = float(r["lambda_market"]), float(r["lambda_hier"])
        threshold = int(float(r["threshold"]))

        p_blend, p_market = blend(lam_m, lam_h, threshold)
        # convert probabilities back to an implied lambda for NLL scoring
        # (search a lambda whose P(X>threshold) matches, same method as fetch script)
        def implied_lambda(p, k):
            lo, hi = 0.01, 25.0
            for _ in range(50):
                mid = (lo + hi) / 2
                if pois_sf(k, mid) < p: lo = mid
                else: hi = mid
            return (lo + hi) / 2

        lam_blend = implied_lambda(p_blend, threshold)
        nll_market.append(nll(actual, lam_m))
        nll_glmm.append(nll(actual, lam_h))
        nll_blend.append(nll(actual, lam_blend))
        print(f"{r['match']:28s} {r['team']:12s} actual={actual:2d}  "
              f"market_lam={lam_m:.2f} glmm_lam={lam_h:.2f} blend_lam={lam_blend:.2f}  "
              f"nll: mkt={nll_market[-1]:.2f} glmm={nll_glmm[-1]:.2f} blend={nll_blend[-1]:.2f}")

    n = len(rows)
    print(f"\nn={n} team-observations")
    print(f"Mean NLL -- market alone: {sum(nll_market)/n:.4f}   "
          f"GLMM alone: {sum(nll_glmm)/n:.4f}   blend (w={W}, cap=±{CAP}): {sum(nll_blend)/n:.4f}")
    print("\n(Directional check only, n=11 matches -- not a powered test. The point of the")
    print(" blend isn't to prove it's better here, it's to get SOME validated signal into")
    print(" live pricing while bounding the downside if GLMM is wrong on any single match.)")


if __name__ == "__main__":
    main()
