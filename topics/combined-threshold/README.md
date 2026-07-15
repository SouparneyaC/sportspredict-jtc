# Combined-Threshold Composition

The methodology (not a question type of its own): "N+ combined [stat], both teams" questions,
priced by convolving two independent per-team Poisson lambda predictions (closed form, no
refitting — sum of two independent Poissons is Poisson(lambda_a+lambda_b)). A stub folder for
taxonomy completeness — the actual script and results live with the families it applies to.

## Current status/verdict

| Family | Verdict |
|---|---|
| SOT-combined | **FAIL** — positive within-match correlation between the two teams' SOT counts breaks the independence assumption. |
| Corners-combined | **FAIL** — same reason. |
| Offsides-combined | "Passed" pre-bug-fix for the same reason offsides itself falsely passed (the 8.49x StatsBomb bug); **FAILs post-fix**. |
| Cards-combined | Never run — cards' own per-team model already failed, so combining it was out of scope. |

## Shared inputs / where the actual files live

| Path | Role |
|---|---|
| `ml/backtests/combined_threshold_backtest.py` | The shared composition script — stays in `ml/backtests/` since it fits/writes across all three attempted families at once. |
| `../shots-on-target/combined_sot_backtest_results.csv` | SOT's combined-threshold results. |
| `../corners/combined_corners_backtest_results.csv` | Corners' combined-threshold results. |
| `../offsides/combined_offsides_backtest_results.csv` | Offsides' combined-threshold results (the false-pass/post-fix-fail case). |

## Root-doc mentions

- [`ml/backtests/PREREGISTRATION_cards_corners_offsides_and_combined.md`](../../ml/backtests/PREREGISTRATION_cards_corners_offsides_and_combined.md) — the shared preregistration covering all four families including this compositional test.
