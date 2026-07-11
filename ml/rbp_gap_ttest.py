"""
rbp_gap_ttest.py
------------------
Two-sample t-test: does deviating further from the crowd (|our_estimate -
crowd_estimate|) associate with a different average RBP than deviating less?

Source: datasets/master_question_dataset.csv, same usable-row filter as
ml/rbp_linear_regression.py (actually_submitted, our_estimate/crowd_estimate/
outcome/rbp all present) -- 771 rows / 71 matches as of the current rebuild.

Grouping: median split on abs_gap = |our_estimate - crowd_estimate|.
  Group LOW  = abs_gap <= median (questions where we stayed close to the crowd)
  Group HIGH = abs_gap >  median (questions where we deviated a lot)

Methodology:
- Welch's t-test (unequal-variance), not Student's pooled-variance t-test --
  Welch's is the safer modern default (Delacre et al. 2017, "Why Welch's
  t-test should be the default...") and there's no reason to assume the two
  groups have equal RBP variance.
- Levene's test reported alongside as a check on that assumption, not as a
  gate on which test to run.
- Cohen's d reported for effect size (a p-value alone doesn't say whether the
  difference is big enough to matter).
- CAVEAT reported explicitly: rows are NOT fully independent -- ~15 questions
  share one match's context (elo_diff, draw_probability, etc.), the same
  clustering problem already flagged for the OLS regression. A naive
  question-level t-test overstates the effective sample size. As a
  robustness check, the same test is re-run at the match level (aggregating
  each match to its own mean abs_gap and mean rbp first), which is the
  correctly-independent unit -- if the two versions disagree, trust the
  match-level one.

Usage: python3 ml/rbp_gap_ttest.py
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "datasets" / "master_question_dataset.csv"
OUT = ROOT / "ml" / "rbp_gap_ttest_results.json"


def load_usable():
    df = pd.read_csv(MASTER)
    usable = df[
        (df["actually_submitted"] == True)
        & df["our_estimate"].notna()
        & df["crowd_estimate"].notna()
        & df["outcome"].notna()
        & df["rbp"].notna()
    ].copy()
    usable["abs_gap"] = (usable["our_estimate"] - usable["crowd_estimate"]).abs()
    return usable


def cohens_d(a, b):
    n1, n2 = len(a), len(b)
    pooled_std = np.sqrt(((n1 - 1) * a.var(ddof=1) + (n2 - 1) * b.var(ddof=1)) / (n1 + n2 - 2))
    return (a.mean() - b.mean()) / pooled_std


def run_ttest(df, label):
    median_gap = df["abs_gap"].median()
    low = df.loc[df["abs_gap"] <= median_gap, "rbp"]
    high = df.loc[df["abs_gap"] > median_gap, "rbp"]

    t_stat, p_val = stats.ttest_ind(high, low, equal_var=False)  # Welch's
    levene_stat, levene_p = stats.levene(high, low)
    d = cohens_d(high, low)
    se_diff = np.sqrt(high.var(ddof=1) / len(high) + low.var(ddof=1) / len(low))
    diff = high.mean() - low.mean()
    dfree = (high.var(ddof=1) / len(high) + low.var(ddof=1) / len(low)) ** 2 / (
        (high.var(ddof=1) / len(high)) ** 2 / (len(high) - 1)
        + (low.var(ddof=1) / len(low)) ** 2 / (len(low) - 1)
    )
    tcrit = stats.t.ppf(0.975, dfree)
    ci = (diff - tcrit * se_diff, diff + tcrit * se_diff)

    print(f"\n{'=' * 70}\n{label}\n{'=' * 70}")
    print(f"Median |gap| split at: {median_gap:.4f}")
    print(f"LOW  group (abs_gap <= median): n={len(low)}, mean RBP={low.mean():.3f}, std={low.std():.3f}")
    print(f"HIGH group (abs_gap >  median): n={len(high)}, mean RBP={high.mean():.3f}, std={high.std():.3f}")
    print(f"Mean difference (HIGH - LOW): {diff:.3f}  (95% CI: [{ci[0]:.3f}, {ci[1]:.3f}])")
    print(f"Welch's t-test: t={t_stat:.3f}, p={p_val:.4f}")
    print(f"Levene's test for equal variance: stat={levene_stat:.3f}, p={levene_p:.4f}")
    print(f"Cohen's d: {d:.3f}")

    return {
        "n_low": len(low), "n_high": len(high),
        "mean_low": float(low.mean()), "mean_high": float(high.mean()),
        "mean_diff": float(diff), "ci_95": [float(ci[0]), float(ci[1])],
        "t_stat": float(t_stat), "p_value": float(p_val),
        "levene_stat": float(levene_stat), "levene_p": float(levene_p),
        "cohens_d": float(d), "median_split": float(median_gap),
    }


def main():
    df = load_usable()
    print(f"Usable rows: {len(df)}  |  Unique matches: {df['match'].nunique()}")

    question_level = run_ttest(df, "QUESTION-LEVEL (n=771, rows are NOT fully independent -- see caveat)")

    match_level = (
        df.groupby("match")
        .agg(abs_gap=("abs_gap", "mean"), rbp=("rbp", "mean"))
        .reset_index()
    )
    match_result = run_ttest(match_level, f"MATCH-LEVEL ROBUSTNESS CHECK (n={len(match_level)}, correctly independent unit)")

    OUT.write_text(json.dumps({
        "question_level": question_level,
        "match_level": match_result,
    }, indent=2))
    print(f"\nWritten: {OUT}")


if __name__ == "__main__":
    main()
