"""
platt_diagnostic.py
===================
Runs the Platt scaling calibration diagnostic on the flat feature matrix.

Platt scaling: fit a logistic regression with 2 parameters (a, b) such that:
  logit(P(outcome=1)) = a + b * logit(our_estimate)

If b ≈ 1 and a ≈ 0: perfectly calibrated.
If b < 1: overconfident (estimates too extreme, should shrink toward 50%).
If b > 1: underconfident (estimates too compressed toward 50%).
If a ≠ 0: systematic directional bias.

Three analyses are run:
  1. Global Platt fit (all 246 questions)
  2. Walk-forward holdout: train on first 60%, evaluate on last 40%
  3. Reliability diagram data (calibration curve by decile)

All outputs saved to ml/platt_results.json for the notebook.
"""

import csv
import json
import math
import statistics
from pathlib import Path

BASE    = Path(__file__).parent
DATA    = BASE / "feature_matrix.csv"
RESULTS = BASE / "platt_results.json"

# ─── helpers ──────────────────────────────────────────────────────────────────

CLIP = 1e-6   # keep probabilities off 0/1 for logit computation

def logit(p):
    p = max(CLIP, min(1 - CLIP, p))
    return math.log(p / (1 - p))

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def brier(p, y):
    return (p - y) ** 2

def log_loss(p, y):
    p = max(CLIP, min(1 - CLIP, p))
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))

# ─── Newton-Raphson logistic regression (2-parameter) ─────────────────────────

def fit_logistic(X, y, max_iter=200, tol=1e-8):
    """
    Fit logistic regression: log-odds(y) = a + b*X
    X: list of floats (logit of our estimates)
    y: list of ints (0/1)
    Returns (a, b, n_iter)
    """
    a, b = 0.0, 1.0   # good starting point: identity calibration

    for iteration in range(max_iter):
        grad_a, grad_b = 0.0, 0.0
        hess_aa, hess_ab, hess_bb = 0.0, 0.0, 0.0

        for xi, yi in zip(X, y):
            p    = sigmoid(a + b * xi)
            resid = yi - p
            w    = p * (1 - p)
            grad_a  += resid
            grad_b  += resid * xi
            hess_aa += w
            hess_ab += w * xi
            hess_bb += w * xi * xi

        # Newton step: solve H * delta = grad
        det = hess_aa * hess_bb - hess_ab ** 2
        if abs(det) < 1e-12:
            break
        da = ( hess_bb * grad_a - hess_ab * grad_b) / det
        db = (-hess_ab * grad_a + hess_aa * grad_b) / det

        a += da
        b += db
        if abs(da) < tol and abs(db) < tol:
            break

    return a, b, iteration + 1

def bootstrap_ci(X, y, n_boot=1000, alpha=0.05):
    """Bootstrap 95% CI for a and b."""
    import random
    random.seed(42)
    n = len(X)
    a_boot, b_boot = [], []
    for _ in range(n_boot):
        idx = [random.randint(0, n - 1) for _ in range(n)]
        Xb = [X[i] for i in idx]
        yb = [y[i] for i in idx]
        try:
            a, b, _ = fit_logistic(Xb, yb)
            a_boot.append(a)
            b_boot.append(b)
        except Exception:
            pass
    a_boot.sort(); b_boot.sort()
    m = len(a_boot)
    lo = int(m * alpha / 2)
    hi = min(int(m * (1 - alpha / 2)), m - 1)
    return (a_boot[lo], a_boot[hi]), (b_boot[lo], b_boot[hi])

# ─── load data ────────────────────────────────────────────────────────────────

rows = []
with open(DATA, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["rbp"] == "":
            continue   # skip rows without settled RBP
        rows.append({
            "match":          r["match"],
            "date":           r["date"],
            "question_num":   r["question_num"],
            "our_estimate":   float(r["our_estimate"]),
            "crowd_estimate": float(r["crowd_estimate"]),
            "outcome":        int(r["outcome"]),
            "rbp":            float(r["rbp"]),
            "beat_crowd":     int(r["beat_crowd"]),
        })

n = len(rows)
print(f"Loaded {n} settled questions from feature_matrix.csv")

X_all = [logit(r["our_estimate"]) for r in rows]
y_all = [r["outcome"] for r in rows]
p_all = [r["our_estimate"] for r in rows]
c_all = [r["crowd_estimate"] for r in rows]

# ─── ANALYSIS 1: Global Platt fit ─────────────────────────────────────────────

print("\n" + "="*64)
print("ANALYSIS 1: Global Platt Scaling (all 246 questions)")
print("="*64)

a_global, b_global, iters = fit_logistic(X_all, y_all)
print(f"  Intercept  a = {a_global:+.4f}  (0 = no directional bias)")
print(f"  Slope      b = {b_global:+.4f}  (1 = perfectly calibrated)")
print(f"  Converged in {iters} iterations")

# Calibrated probabilities
p_cal = [sigmoid(a_global + b_global * x) for x in X_all]

# Brier scores
bs_raw = statistics.mean(brier(p, y) for p, y in zip(p_all, y_all))
bs_cal = statistics.mean(brier(p, y) for p, y in zip(p_cal, y_all))
bs_crowd = statistics.mean(brier(c, y) for c, y in zip(c_all, y_all))

print(f"\n  Brier score (our raw):        {bs_raw:.4f}")
print(f"  Brier score (Platt-recalib):  {bs_cal:.4f}  (delta = {bs_cal-bs_raw:+.4f})")
print(f"  Brier score (crowd):          {bs_crowd:.4f}  (delta vs raw = {bs_crowd-bs_raw:+.4f})")
print(f"\n  Our raw vs crowd Brier gap:   {bs_crowd - bs_raw:+.5f}")
print(f"  => {'We beat crowd on Brier score overall' if bs_raw < bs_crowd else 'Crowd beats us on Brier score overall'}")

# Bootstrap CI
print(f"\n  Computing bootstrap 95% CI (1000 resamples)...")
ci_a, ci_b = bootstrap_ci(X_all, y_all)
print(f"  95% CI for a: [{ci_a[0]:+.4f}, {ci_a[1]:+.4f}]")
print(f"  95% CI for b: [{ci_b[0]:+.4f}, {ci_b[1]:+.4f}]")
if ci_b[0] <= 1.0 <= ci_b[1]:
    print(f"  => b=1 is WITHIN the 95% CI — no statistically significant miscalibration detected")
else:
    direction = "OVERCONFIDENT (b<1, estimates too extreme)" if b_global < 1 else "UNDERCONFIDENT (b>1, too compressed)"
    print(f"  => b=1 is OUTSIDE the 95% CI — statistically significant miscalibration: {direction}")

# ─── ANALYSIS 2: Walk-forward holdout ─────────────────────────────────────────

print("\n" + "="*64)
print("ANALYSIS 2: Walk-Forward Holdout (train=60%, test=40%)")
print("="*64)

split = int(0.60 * n)
train_rows = rows[:split]
test_rows  = rows[split:]

X_train = [logit(r["our_estimate"]) for r in train_rows]
y_train = [r["outcome"] for r in train_rows]
X_test  = [logit(r["our_estimate"]) for r in test_rows]
y_test  = [r["outcome"] for r in test_rows]
p_test  = [r["our_estimate"] for r in test_rows]
c_test  = [r["crowd_estimate"] for r in test_rows]

a_wf, b_wf, _ = fit_logistic(X_train, y_train)
p_wf_cal = [sigmoid(a_wf + b_wf * x) for x in X_test]

bs_test_raw   = statistics.mean(brier(p, y) for p, y in zip(p_test, y_test))
bs_test_cal   = statistics.mean(brier(p, y) for p, y in zip(p_wf_cal, y_test))
bs_test_crowd = statistics.mean(brier(c, y) for c, y in zip(c_test, y_test))

print(f"  Train: {len(train_rows)} questions ({train_rows[0]['date']} to {train_rows[-1]['date']})")
print(f"  Test:  {len(test_rows)} questions ({test_rows[0]['date']} to {test_rows[-1]['date']})")
print(f"\n  Walk-forward Platt:  a={a_wf:+.4f}  b={b_wf:+.4f}")
print(f"\n  Test Brier (raw):    {bs_test_raw:.4f}")
print(f"  Test Brier (calib):  {bs_test_cal:.4f}  (delta = {bs_test_cal-bs_test_raw:+.4f})")
print(f"  Test Brier (crowd):  {bs_test_crowd:.4f}")
print(f"\n  => Platt recalibration {'IMPROVES' if bs_test_cal < bs_test_raw else 'WORSENS'} out-of-sample Brier by {abs(bs_test_cal-bs_test_raw):.4f}")

# ─── ANALYSIS 3: Reliability diagram (calibration curve) ─────────────────────

print("\n" + "="*64)
print("ANALYSIS 3: Reliability Diagram (calibration buckets)")
print("="*64)

# Sort by our_estimate, bin into deciles
sorted_rows = sorted(rows, key=lambda r: r["our_estimate"])
bucket_size = max(1, n // 10)
buckets = []
for i in range(0, n, bucket_size):
    chunk = sorted_rows[i: i + bucket_size]
    if not chunk: continue
    mean_pred = statistics.mean(r["our_estimate"] for r in chunk)
    mean_outcome = statistics.mean(r["outcome"] for r in chunk)
    n_chunk = len(chunk)
    buckets.append({
        "bucket_i":   len(buckets) + 1,
        "n":          n_chunk,
        "mean_pred":  round(mean_pred, 4),
        "mean_outcome": round(mean_outcome, 4),
        "gap":        round(mean_outcome - mean_pred, 4),
    })

print(f"  {'Bucket':<8} {'N':<5} {'Mean_pred':<12} {'Mean_outcome':<14} {'Gap (out-pred)'}")
print(f"  {'-'*54}")
for b in buckets:
    flag = " <-- OVER" if b["gap"] < -0.05 else (" <-- UNDER" if b["gap"] > 0.05 else "")
    print(f"  {b['bucket_i']:<8} {b['n']:<5} {b['mean_pred']:<12.3f} {b['mean_outcome']:<14.3f} {b['gap']:+.3f}{flag}")

# ─── ANALYSIS 4: RBP breakdown ────────────────────────────────────────────────

print("\n" + "="*64)
print("ANALYSIS 4: RBP by estimate range")
print("="*64)

ranges = [(0.0, 0.3, "LOW (0-30%)"), (0.3, 0.5, "MID-LOW (30-50%)"),
          (0.5, 0.7, "MID-HIGH (50-70%)"), (0.7, 1.0, "HIGH (70-100%)")]
for lo, hi, label in ranges:
    subset = [r for r in rows if lo <= r["our_estimate"] < hi]
    if not subset: continue
    mean_rbp = statistics.mean(r["rbp"] for r in subset)
    beat_pct = 100 * sum(r["beat_crowd"] for r in subset) / len(subset)
    print(f"  {label:<22}: n={len(subset):3d}  mean_rbp={mean_rbp:+.3f}  beat_crowd={beat_pct:.0f}%")

# ─── Save results ─────────────────────────────────────────────────────────────

results = {
    "n_questions": n,
    "date_range": f"{rows[0]['date']} to {rows[-1]['date']}",
    "global_platt": {
        "a": round(a_global, 6),
        "b": round(b_global, 6),
        "interpretation": {
            "a_near_zero": abs(a_global) < 0.1,
            "b_near_one":  abs(b_global - 1.0) < 0.1,
            "b_ci_95":     [round(ci_b[0], 4), round(ci_b[1], 4)],
            "b_includes_1": ci_b[0] <= 1.0 <= ci_b[1],
        },
        "brier_raw":          round(bs_raw, 6),
        "brier_platt_calib":  round(bs_cal, 6),
        "brier_crowd":        round(bs_crowd, 6),
        "brier_improvement":  round(bs_raw - bs_cal, 6),
    },
    "walk_forward": {
        "train_n":    len(train_rows),
        "test_n":     len(test_rows),
        "a":          round(a_wf, 6),
        "b":          round(b_wf, 6),
        "brier_raw":   round(bs_test_raw, 6),
        "brier_calib": round(bs_test_cal, 6),
        "brier_crowd": round(bs_test_crowd, 6),
        "improvement": round(bs_test_raw - bs_test_cal, 6),
    },
    "reliability_diagram": buckets,
    "overall_stats": {
        "beat_crowd_rate":    round(sum(r["beat_crowd"] for r in rows) / n, 4),
        "mean_rbp":           round(statistics.mean(r["rbp"] for r in rows), 4),
        "std_rbp":            round(statistics.stdev(r["rbp"] for r in rows), 4),
        "total_rbp":          round(sum(r["rbp"] for r in rows), 2),
        "yes_rate":           round(sum(r["outcome"] for r in rows) / n, 4),
    },
}

with open(RESULTS, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: {RESULTS}")
print("\n" + "="*64)
print("SUMMARY")
print("="*64)
print(f"  Global Platt:  a={a_global:+.4f}  b={b_global:.4f}")
print(f"  b 95% CI:      [{ci_b[0]:+.4f}, {ci_b[1]:+.4f}]")
print(f"  b includes 1:  {ci_b[0] <= 1.0 <= ci_b[1]}")
print(f"  Global Brier improvement from Platt: {bs_raw - bs_cal:+.5f}")
print(f"  Walk-forward Brier improvement:      {bs_test_raw - bs_test_cal:+.5f}")
print(f"\nInterpretation:")
if abs(a_global) < 0.1:
    print(f"  a ≈ 0 → no systematic directional bias (good)")
else:
    print(f"  a = {a_global:+.3f} → {'we submit TOO LOW on average' if a_global > 0 else 'we submit TOO HIGH on average'}")
if ci_b[0] <= 1.0 <= ci_b[1]:
    print(f"  b CI includes 1 → estimates are well-calibrated in aggregate (no ML correction needed yet)")
elif b_global < 1:
    print(f"  b < 1 ({b_global:.3f}) → OVERCONFIDENT: our extreme estimates should be pulled toward 50%")
else:
    print(f"  b > 1 ({b_global:.3f}) → UNDERCONFIDENT: our estimates are too compressed toward 50%")
