"""
Walk-forward backtest for the Q14-style first-substitution race, pre-registered
in PREREGISTRATION_q14_first_sub_race.md. Only pre-match-knowable covariates
(each team's own shrunk historical first-sub-minute tendency, Elo diff) --
no in-match state, since JTC requires a pre-kickoff submission.

Reads: ml/backtests/rare_event_panel.csv (first-sub minutes, 100 matches)
       data/processed/unified_team_match_panel_with_pit_elo.csv (elo_diff_pre)
Writes: ml/backtests/first_sub_backtest_results.csv

Usage:
    python3 walk_forward_first_sub_backtest.py
"""
import csv
import math
from pathlib import Path
from collections import defaultdict

import numpy as np
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "ml" / "backtests" / "rare_event_panel.csv"
ELO_PANEL = ROOT / "data" / "processed" / "unified_team_match_panel_with_pit_elo.csv"
OUT = ROOT / "topics" / "first-substitution" / "first_sub_backtest_results.csv"

K_SHRINK = 5

rows = list(csv.DictReader(open(PANEL)))
rows = [r for r in rows if r["team_a_first_sub_min"] and r["team_b_first_sub_min"]]
rows.sort(key=lambda r: (r["date"], r["event_id"]))

# elo_diff per (match_id/event_id, team_name)
elo = {}
for r in csv.DictReader(open(ELO_PANEL)):
    if r["data_source"] == "espn_boxscore" and r["elo_diff_pre"] not in ("", "NA"):
        elo[(r["match_id"], r["team_name"])] = float(r["elo_diff_pre"])

results = []
team_history = defaultdict(list)  # team_name -> [first_sub_min, ...], appended in chronological order

for row in rows:
    ta, tb = row["team_a"], row["team_b"]
    min_a, min_b = int(row["team_a_first_sub_min"]), int(row["team_b_first_sub_min"])
    if min_a == min_b:
        continue  # exclude true ties (extremely rare)
    outcome_a_first = 1 if min_a < min_b else 0

    hist_a, hist_b = team_history[ta], team_history[tb]
    global_mean = np.mean([m for v in team_history.values() for m in v]) if any(team_history.values()) else 60.0
    shrunk_a = (len(hist_a) * np.mean(hist_a) + K_SHRINK * global_mean) / (len(hist_a) + K_SHRINK) if hist_a else global_mean
    shrunk_b = (len(hist_b) * np.mean(hist_b) + K_SHRINK * global_mean) / (len(hist_b) + K_SHRINK) if hist_b else global_mean

    ed_a = elo.get((row["event_id"], ta))
    ed_b = elo.get((row["event_id"], tb))
    elo_diff = (ed_a - ed_b) if (ed_a is not None and ed_b is not None) else 0.0

    results.append({
        "event_id": row["event_id"], "date": row["date"], "team_a": ta, "team_b": tb,
        "outcome_a_first": outcome_a_first,
        "shrunk_gap_b_minus_a": shrunk_b - shrunk_a,  # positive = B tends to sub later -> A more likely first
        "elo_diff": elo_diff,
        "n_prior_a": len(hist_a), "n_prior_b": len(hist_b),
    })

    team_history[ta].append(min_a)
    team_history[tb].append(min_b)

print(f"{len(results)} match-rows with both teams' sub-minute history")

# Walk-forward logistic fit: for each row (in chronological order), fit on all
# STRICTLY PRIOR rows, predict this row, then move on.
X_cols = ["shrunk_gap_b_minus_a", "elo_diff"]
briers_model, briers_baseline = [], []
fit_failures = 0
for i, r in enumerate(results):
    train = results[:i]
    if len(train) < 15:
        continue
    X_train = np.array([[t[c] for c in X_cols] for t in train])
    y_train = np.array([t["outcome_a_first"] for t in train])
    if len(set(y_train.tolist())) < 2:
        continue
    try:
        clf = LogisticRegression(C=1.0, max_iter=1000)
        clf.fit(X_train, y_train)
        x_test = np.array([[r[c] for c in X_cols]])
        p_model = clf.predict_proba(x_test)[0, 1]
    except Exception:
        fit_failures += 1
        continue

    actual = r["outcome_a_first"]
    briers_model.append((p_model - actual) ** 2)
    briers_baseline.append((0.5 - actual) ** 2)
    r["p_model"] = p_model
    r["brier_model"] = briers_model[-1]
    r["brier_baseline"] = briers_baseline[-1]

n = len(briers_model)
print(f"Walk-forward folds scored: {n} (fit failures skipped: {fit_failures})")
print(f"Mean Brier -- model: {np.mean(briers_model):.4f}   baseline (50/50): {np.mean(briers_baseline):.4f}")

diffs = np.array(briers_baseline) - np.array(briers_model)  # positive = model better
mean_diff = diffs.mean()
rng = np.random.default_rng(20260714)
boot = [rng.choice(diffs, size=len(diffs), replace=True).mean() for _ in range(2000)]
ci90 = np.percentile(boot, [5, 95])
print(f"Mean diff (baseline - model): {mean_diff:+.4f}  bootstrap 90% band: [{ci90[0]:+.4f}, {ci90[1]:+.4f}]")
print("PASS" if ci90[0] > 0 else "FAIL (not distinguishable from 50/50 at this n)")

scored = [r for r in results if "p_model" in r]
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(scored[0].keys()))
    w.writeheader()
    w.writerows(scored)
print(f"\nWrote {OUT}")
