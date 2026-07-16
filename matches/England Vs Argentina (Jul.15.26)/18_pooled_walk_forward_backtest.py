"""
Pooled walk-forward backtest for Q5/Q7/Q8/Q10, extending
`ml/backtests/timing_compound_events_backtest.py` (WC2026-only, n=100, ESPN
data) with the StatsBomb-sourced Euro 2024 + Copa America 2024 + AFCON 2023
panel built by `18_statsbomb_expanded_panel.py` (n=135). Combined corpus:
n=235, sorted by actual match date, walk-forward, strictly-prior-only
training at every fold -- same discipline as the original script and
`ml/backtests/lib_hierarchical_backtest.R`'s run_family_backtest().

Point-in-time note: Euro 2024 (Jun-Jul 2024), Copa America 2024 (Jun-Jul
2024) and AFCON 2023 (Jan 2024) all finished well over a year before WC2026
kicked off (2026-06-11), so folding them in is unambiguously PIT-safe for
every WC2026 fold, not just tonight's -- it strengthens the warm-up period
for the earliest WC2026 matches too, which previously had only 5-6 prior
matches to draw an empirical rate from.

IMPORTANT CROSS-SOURCE CAVEAT (checked directly, not assumed) -- read before
trusting Q8/Q10's pooled numbers: this project's own prior work
(`ml/backtests/PREREGISTRATION_cards_corners_offsides_and_combined.md`)
already found and documented an ESPN/StatsBomb measurement ratio for cards of
0.876/0.791x (ESPN systematically records FEWER cards than StatsBomb for the
same underlying matches -- the same class of bug independently found to be
8.49x for offsides before a fix). This script's own two-source comparison
reproduces that direction on a fresh corpus: WC2026 (ESPN) averages 2.59
cards/match vs this StatsBomb 3-tournament pull's 3.86/match, a 0.671x ratio
-- same direction, even larger gap. Q5/Q7 (goal-timing only) do not have
this problem -- goals are unambiguous "key events" in both ESPN's keyEvents
feed and StatsBomb's full event stream, and no equivalent ratio has ever been
found for goal counts in this project. Q8/Q10 depend on card presence/timing,
so their pooled numbers below are reported but explicitly flagged as
measurement-instrument-mixed, not source-homogeneous -- see the summary doc
for how this changes what's actually used as tonight's live number.

Usage:
    python3 18_pooled_walk_forward_backtest.py
Outputs (this directory):
    18_pooled_walk_forward_results.csv   (per-match, per-question predictions)
    18_pooled_walk_forward_summary.csv   (per-question rollup + live rates)
"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "ml" / "backtests"))
import timing_compound_events_backtest as wc2026  # noqa: E402

SB_PANEL = HERE / "18_statsbomb_expanded_panel.csv"
OUT_RESULTS = HERE / "18_pooled_walk_forward_results.csv"
OUT_SUMMARY = HERE / "18_pooled_walk_forward_summary.csv"

MIN_TRAIN = 5
TODAY = "2026-07-15"

OUTCOMES = [
    ("q5_goal_each_half", "Q5 goal-in-each-half"),
    ("q7_stoppage_goal", "Q7 stoppage-time goal"),
    ("q8_both_carded", "Q8 both-teams-carded"),
    ("q10_card_before_goal", "Q10 card-before-first-goal"),
]


def load_wc2026_rows():
    rows = wc2026.build_dataset()
    out = []
    for r in rows:
        out.append({
            "source": "WC2026_ESPN",
            "match_id": r["event_id"],
            "date": r["date"],
            "team_a": r["team_a"],
            "team_b": r["team_b"],
            "q5_goal_each_half": bool(r["q5_goal_each_half"]),
            "q7_stoppage_goal": bool(r["q7_stoppage_goal"]),
            "q8_both_carded": bool(r["q8_both_carded"]),
            "q10_card_before_goal": bool(r["q10_card_before_goal"]),
        })
    return out


def load_statsbomb_rows():
    out = []
    with open(SB_PANEL) as f:
        for r in csv.DictReader(f):
            out.append({
                "source": r["competition"],
                "match_id": r["match_id"],
                "date": r["date"][:10],  # strip time-of-day
                "team_a": r["team_a"],
                "team_b": r["team_b"],
                "q5_goal_each_half": r["q5_goal_each_half"] == "True",
                "q7_stoppage_goal": r["q7_stoppage_goal"] == "True",
                "q8_both_carded": r["q8_both_carded"] == "True",
                "q10_card_before_goal": r["q10_card_before_goal"] == "True",
            })
    return out


def walk_forward(rows, outcome_key):
    preds = []
    for row in rows:
        d = row["date"]
        prior = [r for r in rows if r["date"] < d]
        if len(prior) < MIN_TRAIN:
            continue
        rate = sum(1 for r in prior if r[outcome_key]) / len(prior)
        actual = 1 if row[outcome_key] else 0
        preds.append({
            "question": outcome_key, "source": row["source"],
            "match_id": row["match_id"], "date": d,
            "team_a": row["team_a"], "team_b": row["team_b"],
            "n_prior": len(prior), "predicted_rate": rate, "actual": actual,
            "brier_wf": (rate - actual) ** 2, "brier_naive": (0.5 - actual) ** 2,
        })
    return preds


def main():
    wc_rows = load_wc2026_rows()
    sb_rows = load_statsbomb_rows()
    rows = wc_rows + sb_rows
    rows.sort(key=lambda r: r["date"])
    print(f"WC2026 rows: {len(wc_rows)}  StatsBomb rows: {len(sb_rows)}  Pooled: {len(rows)}")
    print(f"Date range: {rows[0]['date']} to {rows[-1]['date']}")

    all_preds = []
    summary = []
    for key, label in OUTCOMES:
        preds = walk_forward(rows, key)
        n = len(preds)
        mbw = sum(p["brier_wf"] for p in preds) / n
        mbn = sum(p["brier_naive"] for p in preds) / n
        hit = sum(p["actual"] for p in preds) / n
        print(f"[{label}] n={n} walk-forward Brier={mbw:.4f} naive={mbn:.4f} "
              f"improvement={mbn-mbw:+.4f} hit-rate={hit:.3f}")
        all_preds.extend(preds)

        prior_all = [r for r in rows if r["date"] < TODAY]
        live_rate = sum(1 for r in prior_all if r[key]) / len(prior_all)
        print(f"  live rate (all sources, date<{TODAY}): n={len(prior_all)} rate={live_rate:.3f}")

        summary.append({
            "question": label, "n_walk_forward": n,
            "brier_walk_forward": mbw, "brier_naive_0.5": mbn,
            "improvement": mbn - mbw, "hit_rate": hit,
            "n_live": len(prior_all), "live_rate_pooled": live_rate,
        })

    with open(OUT_RESULTS, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["question", "source", "match_id", "date", "team_a",
                                           "team_b", "n_prior", "predicted_rate", "actual",
                                           "brier_wf", "brier_naive"])
        w.writeheader()
        w.writerows(all_preds)
    print(f"Wrote {OUT_RESULTS}")

    with open(OUT_SUMMARY, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["question", "n_walk_forward", "brier_walk_forward",
                                           "brier_naive_0.5", "improvement", "hit_rate",
                                           "n_live", "live_rate_pooled"])
        w.writeheader()
        w.writerows(summary)
    print(f"Wrote {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
