"""
Shared data-loading and filtering module for the 4 RBP track-record visualizations
(plot_cumulative_rbp_drawdown.py, plot_match_rbp_waterfall.py,
plot_calibration_reliability.py, plot_match_small_multiples.py).

Plays the same role for these 4 scripts that ml/backtests/lib_hierarchical_backtest.R
plays for the topics/ backtests: one shared codepath for "what counts as a settled,
gradeable row," so the 4 charts can't silently drift to different filtering rules and
tell inconsistent stories from the same campaign.

Source: datasets/master_question_dataset.csv -- confirmed the correct source over the
alternative datasets/questions_flat.csv, which is missing 42 matches and has an
inconsistent match-naming bug (11 matches use "Team vs Team" instead of the "XXX-YYY"
code format everywhere else). Note: two matches (SUI-BIH, USA-AUS) have a row-count
mismatch between the two files; irrelevant here since this module never reads
questions_flat.csv.
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
MASTER_CSV = ROOT / "datasets" / "master_question_dataset.csv"

# Okabe & Ito (2008), "Color Universal Design" -- colorblind-safe qualitative palette.
# Deliberately replaces the red/green (#F44336/#4CAF50) sign-coding this project's own
# already-studied ML4T reference code uses (external_repos/machine-learning-for-trading/
# case_studies/utils/strategy_analysis.py::plot_sharpe_waterfall), which is not
# distinguishable under red-green color vision deficiency.
C_POSITIVE = "#0072B2"  # Okabe-Ito blue        -- beat the crowd (RBP > 0)
C_NEGATIVE = "#D55E00"  # Okabe-Ito vermillion  -- lost to the crowd (RBP < 0)
C_NEUTRAL = "#999999"   # zero-reference lines and other non-data ink only


def load_master():
    """Read the master dataset, parse dates, print raw shape."""
    df = pd.read_csv(MASTER_CSV)
    df["date"] = pd.to_datetime(df["date"])
    print(f"[load_master] {len(df)} raw rows, {df['match'].nunique()} distinct matches, "
          f"dates {df['date'].min().date()} to {df['date'].max().date()}")
    return df


def settled_questions(df=None):
    """The shared 'is this question gradeable' filter.

    Applied in order, each drop counted and printed:
      1. actually_submitted == True   -- a question we never priced has nothing to grade
         (this project's own "grade every bet, every time" discipline, see
         writeups/docs/DOCUMENTATION_STANDARDS.md SS5, applies to charts as much as ledgers)
      2. rbp.notna()                  -- submitted but not yet outcome-resolved

    Verified finding this filter protects against: BIH-QAT and URU-CPV both have all 10
    rows actually_submitted=False and rbp entirely null, yet the raw match_total_rbp
    column reads 0.0 for both -- a placeholder, not a real result. Without step 1, both
    matches would silently plot as a neutral/breakeven real outcome, which they are not.
    """
    if df is None:
        df = load_master()
    n_raw = len(df)

    step1 = df[df["actually_submitted"] == True]  # noqa: E712
    n_dropped_not_submitted = n_raw - len(step1)

    step2 = step1[step1["rbp"].notna()]
    n_dropped_pending_outcome = len(step1) - len(step2)

    print(f"[settled_questions] dropped {n_dropped_not_submitted} rows (never submitted), "
          f"{n_dropped_pending_outcome} rows (submitted, outcome not yet resolved) "
          f"-> {len(step2)} settled rows across {step2['match'].nunique()} matches")
    assert n_dropped_not_submitted + n_dropped_pending_outcome + len(step2) == n_raw

    excluded_matches = sorted(set(df["match"]) - set(step2["match"]))
    if excluded_matches:
        print(f"[settled_questions] matches with zero settled questions (excluded entirely): "
              f"{excluded_matches}")

    return step2.copy()


def match_level(df=None, mismatch_flag_tol=0.5):
    """One row per match: match, date, match_number (1..N), match_rbp_total,
    n_questions_scored, team_a, team_b, final_score.

    match_rbp_total is computed fresh via groupby('match')['rbp'].sum() over
    settled_questions() -- never read from the repeated match_total_rbp CSV column.
    Verified finding: 4 fully-scored matches (ARG-AUT, MEX-KOR, TUR-PAR, USA-AUS -- every
    row has a non-null rbp) carry NaN in the raw match_total_rbp field; reusing that
    column would silently drop 4 real, complete matches.

    Where the raw match_total_rbp field does exist, it's cross-checked against the fresh
    sum with a mismatch_flag_tol=0.5 tolerance. This threshold is not picked by eye: among
    the matches where both values exist, the large majority differ by <=0.02 (ordinary
    two-decimal rounding accumulated over ~9-15 summed terms), while two genuine outliers
    (USA-BIH, CIV-ECU) differ by roughly 65-100x that noise floor -- 0.5 sits inside the
    empirically observed gap between "rounding noise" and "a real discrepancy."

    match_number is assigned by sorting on (date, first CSV row-index of that match) --
    no kickoff-timestamp column exists in the source data, so this is the best available
    proxy for intra-day chronology (verified: within-date CSV row order is already
    monotonic/stable, reflecting the file's own build order). Disclosed as an
    approximation, not hidden.
    """
    settled = settled_questions(df)

    grouped = settled.groupby("match", sort=False).agg(
        date=("date", "first"),
        team_a=("team_a", "first"),
        team_b=("team_b", "first"),
        final_score=("final_score", "first"),
        match_rbp_total=("rbp", "sum"),
        n_questions_scored=("rbp", "count"),
        _first_row_idx=("rbp", lambda s: s.index.min()),
    ).reset_index()

    # Cross-check against the raw repeated column, where it exists.
    raw_totals = settled.groupby("match", sort=False)["match_total_rbp"].first()
    grouped["_raw_total"] = grouped["match"].map(raw_totals)
    comparable = grouped.dropna(subset=["_raw_total"]).copy()
    comparable["_diff"] = (comparable["match_rbp_total"] - comparable["_raw_total"]).abs()
    mismatches = comparable[comparable["_diff"] > mismatch_flag_tol]
    if len(mismatches):
        print(f"[match_level] {len(mismatches)} match(es) where the freshly computed total "
              f"differs from the raw match_total_rbp column by more than {mismatch_flag_tol}: "
              + ", ".join(f"{row['match']} (diff {row['_diff']:.2f})"
                          for _, row in mismatches.iterrows()))

    grouped = grouped.sort_values(["date", "_first_row_idx"]).reset_index(drop=True)
    grouped["match_number"] = np.arange(1, len(grouped) + 1)
    grouped = grouped.drop(columns=["_raw_total", "_first_row_idx"])

    cum_total = grouped["match_rbp_total"].sum()
    best = grouped.loc[grouped["match_rbp_total"].idxmax()]
    worst = grouped.loc[grouped["match_rbp_total"].idxmin()]
    print(f"[match_level] {len(grouped)} matches included, cumulative RBP = {cum_total:.2f}, "
          f"best match = {best['match']} ({best['match_rbp_total']:+.2f}), "
          f"worst match = {worst['match']} ({worst['match_rbp_total']:+.2f})")

    return grouped


def question_level_for_calibration(df=None):
    """Rows usable for a reliability/calibration diagram: needs our_estimate + a
    resolved 0/1 outcome, independent of rbp/match totals (calibration is a property
    of the probability-to-outcome mapping, not of RBP). Filter order, each drop printed:
      1. actually_submitted == True
      2. our_estimate.notna()
      3. outcome.isin([0, 1])
    Computed at runtime, never hardcoded against a prior snapshot.
    """
    if df is None:
        df = load_master()
    n_raw = len(df)

    step1 = df[df["actually_submitted"] == True]  # noqa: E712
    n_dropped_not_submitted = n_raw - len(step1)

    step2 = step1[step1["our_estimate"].notna()]
    n_dropped_no_estimate = len(step1) - len(step2)

    step3 = step2[step2["outcome"].isin([0, 1])]
    n_dropped_no_outcome = len(step2) - len(step3)

    print(f"[question_level_for_calibration] dropped {n_dropped_not_submitted} (never "
          f"submitted), {n_dropped_no_estimate} (no our_estimate), {n_dropped_no_outcome} "
          f"(outcome not resolved 0/1) -> {len(step3)} rows across {step3['match'].nunique()} "
          f"matches")
    assert (n_dropped_not_submitted + n_dropped_no_estimate + n_dropped_no_outcome
            + len(step3) == n_raw)

    return step3.copy()


def question_number(question_num_series):
    """Parse 'Q7' -> 7. Vectorized, returns an Int64 (nullable) series."""
    return question_num_series.str.extract(r"Q(\d+)").astype("Int64")[0]


def shared_y_pad(values):
    """Data-derived y-axis padding: pad = max(span * 0.18, 0.15).

    Reused verbatim from external_repos/machine-learning-for-trading/case_studies/
    utils/strategy_analysis.py::plot_sharpe_waterfall's own vetted formula, applied
    independently wherever this module's callers need y-limits -- so the same
    non-arbitrary padding logic is used consistently rather than four separate
    hand-picked constants across the four scripts.
    """
    values = np.asarray(values, dtype=float)
    lo, hi = float(np.min(values)), float(np.max(values))
    span = hi - lo
    pad = max(span * 0.18, 0.15)
    return lo - pad, hi + pad


if __name__ == "__main__":
    # Smoke test / audit trail: running this module directly prints every filter's
    # counts without producing a chart.
    df = load_master()
    settled_questions(df)
    match_level(df)
    question_level_for_calibration(df)
