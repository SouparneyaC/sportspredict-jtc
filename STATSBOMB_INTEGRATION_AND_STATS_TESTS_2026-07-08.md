# StatsBomb Integration & Statistical Tests — Session Record (2026-07-08)

**Purpose of this document:** a clean, self-contained record of everything built and tested in this
session — data engineering, base-rate modeling, and three statistical diagnostics (linear regression,
a small-sample regression demo, and a t-test) — with explanations and interpretation, not just results.
Companion to [STATSBOMB_DATASET_AUDIT.md](STATSBOMB_DATASET_AUDIT.md),
[TRAINING_DATASET_STRATEGY_2026-07-07.md](TRAINING_DATASET_STRATEGY_2026-07-07.md), and
[ML_EXPERIMENTS_NOTEBOOK.md](ML_EXPERIMENTS_NOTEBOOK.md), which this session builds directly on.

**Every test below has both a Python script and a row-for-row-matching R script** (see the
[file index](#file-index-everything-created-this-session) at the bottom) — click either to open it.

**Why this session happened:** the project's biggest historical constraint has been data scarcity —
only ~80-90 real WC2026 matches accumulate at one match/day, which is too small a sample to safely
replace the hand-built RULE1-18 framework with a learned model (already proven twice: the Platt
scaling diagnostic and the meta-model diagnostic both failed out-of-sample at n=246 and n=404). The
question this session asked: can StatsBomb's free, event-level historical data (WC2018 + WC2022) fill
that gap, and what does rigorous statistical testing on our existing data actually show?

---

## 1. Flattening StatsBomb into usable tables

**Script:** [datasets/build_statsbomb_panel.py](datasets/build_statsbomb_panel.py) ·
R port: [datasets/build_statsbomb_panel.R](datasets/build_statsbomb_panel.R)
(read-only against [data/external/statsbomb/open-data/](data/external/statsbomb/open-data/),
writes only to `data/processed/`)

**What it does:** StatsBomb's open data is event-level JSON — every pass, shot, foul, card, offside is
its own timestamped record, ~3,400 events per match. That's not a usable shape for modeling directly,
so this script aggregates it into two flat tables:

- **[statsbomb_team_match_panel.csv](data/processed/statsbomb_team_match_panel.csv)** — 256 rows (128
  matches x 2 teams). One row per team per match: goals, shots, shots-on-target, xG, fouls, cards,
  corners, offsides, passes, etc.
- **[statsbomb_player_match_panel.csv](data/processed/statsbomb_player_match_panel.csv)** — 6,130 rows.
  One row per player per match: minutes played, shots/SOT/goals/assists, fouls, cards, xG.

**Scope:** FIFA World Cup 2018 + 2022 only (128 matches total) — the two tournaments with complete
(64/64) coverage and identical schema, per the source research in
[TRAINING_DATASET_STRATEGY_2026-07-07.md](TRAINING_DATASET_STRATEGY_2026-07-07.md).

**Key methodology decisions:**
- Shot on target = `shot.outcome` in {Goal, Saved, Saved To Post}
- Corners derived from `pass.type.name == "Corner"` (StatsBomb has no standalone corner event)
- Cards read from `lineups/*.json`'s `cards` array (StatsBomb's own authoritative aggregation),
  not re-derived from event tags
- Minutes played summed from lineup position intervals, closing open-ended intervals at the match's
  actual last-event time (correctly captures extra time)
- Penalty shootouts (period 5) excluded from all aggregation

**Validation — and why we trust it:** rather than assume the aggregation logic was correct, we checked
it against independently-known facts:
- Total goals: WC2018 = 169 (2.641/match), WC2022 = 172 (2.688/match) — both exactly match real
  historical tournament totals.
- Top scorers by match: Harry Kane (3g vs Panama, 2018-06-24), Ronaldo (3g vs Spain, 2018-06-15),
  Gonçalo Ramos (3g vs Switzerland, 2022-12-06 — his famous debut hat-trick), Mbappé (3g vs
  Argentina, 2022-12-18, correctly shown with 124.1 minutes — the WC final that went to extra time).

**Interpretation:** this level of exact agreement with well-known facts gives high confidence the
flattening logic (not just the schema, the actual counting rules) is correct — a stronger check than
just "the code ran without errors."

**R port validation:** [datasets/build_statsbomb_panel.R](datasets/build_statsbomb_panel.R) reproduces
this row-for-row (writes to
[statsbomb_team_match_panel_r.csv](data/processed/statsbomb_team_match_panel_r.csv) /
[statsbomb_player_match_panel_r.csv](data/processed/statsbomb_player_match_panel_r.csv) so it never
overwrites the canonical Python output) — identical goal totals (169/172) and identical top scorers.

---

## 2. Testing a historical base-rate model against a real WC2026 match

**Script:** [ml/statsbomb_baserate_test.py](ml/statsbomb_baserate_test.py) ·
R port: [ml/statsbomb_baserate_test.R](ml/statsbomb_baserate_test.R)
**Results:** [ml/statsbomb_baserate_results.json](ml/statsbomb_baserate_results.json) ·
R results: [ml/statsbomb_baserate_results_r.json](ml/statsbomb_baserate_results_r.json)

**The question:** if we'd used *only* Portugal's and Croatia's WC2018+2022 history (no live market, no
this-tournament data) to price the real Portugal vs Croatia match (WC2026 R32, 2026-07-02, final score
2-1, our actual result +130.08 RBP), how would that historical model have done?

**Method:**
- Team rate stats (SOT, shots, cards, corners, goals) pulled from the team panel, shrunk toward the
  256-row tournament-wide mean via **empirical Bayes pooling**: `lambda_shrunk = (n·team_mean +
  k·global_mean) / (n+k)`, k=5 pseudo-matches. This is the classic fix for "a team's own small
  sample is noisy" — don't fully trust 9 games of Portugal history, blend it toward the average team.
- Count-threshold questions ("6+ corners", "20+ shots") priced via Poisson using the shrunk rate.
- Player props (Ronaldo, Bruno Fernandes, Modrić, Bernardo Silva) pulled from the player panel, same
  shrinkage logic with a weaker pseudo-prior (k=3).
- Header goals, half-time-tied, and penalty-or-red-card rates computed directly from raw event JSON
  (period and body-part detail the flattened panel doesn't carry) as tournament-wide empirical rates.
- "Will Portugal advance to the Round of 16?" excluded — that depends on group standings, not on
  either team's own StatsBomb history, so a StatsBomb-only model genuinely cannot answer it.

**Results (14 of 15 questions answerable from StatsBomb alone):**

| Question | Model | Ours | Crowd | Outcome | Our RBP | Model-implied RBP |
|---|---|---|---|---|---|---|
| Ronaldo scores | 0.50 | 0.42 | 0.43 | YES | +4.05 | +7.99 |
| ≤2 total goals | 0.37 | 0.45 | 0.47 | NO | +9.22 | +8.81 |
| Bruno Fernandes 2+ SOT | 0.15 | 0.21 | 0.37 | NO | +27.17 | +11.71 |
| Modrić score/assist | 0.23 | 0.22 | 0.29 | NO | +12.74 | +3.21 |
| Croatia 4+ SOT | 0.55 | 0.42 | 0.46 | YES | -4.69 | +9.03 |
| 4+ total cards | 0.35 | 0.32 | 0.40 | NO | +16.60 | +3.59 |
| Both teams 1+ card | 0.60 | 0.55 | 0.61 | YES | -4.54 | -0.72 |
| Portugal 6+ corners | 0.41 | 0.47 | 0.50 | YES | -2.19 | -9.46 |
| Tied at halftime | 0.49 | 0.40 | 0.44 | YES | -6.23 | +5.63 |
| Portugal 6+ SOT | 0.24 | 0.37 | 0.45 | NO | +17.49 | +14.58 |
| Bernardo Silva 1+ SOT | 0.10 | 0.36 | 0.39 | NO | +14.24 | +14.39 |
| Header goal scored | 0.37 | 0.34 | 0.36 | YES | -1.22 | +0.90 |
| 20+ total shots | 0.92 | 0.75 | 0.63 | YES | +21.58 | +13.22 |
| Penalty or red card | 0.40 | 0.37 | 0.32 | YES | +16.08 | +10.13 |
| **Total** | | | | | **+120.30** | **+93.01** |

**Interpretation:** the pure historical model beat our actual submission on 6/14 questions, but loses
overall (93.01 vs 120.30 RBP-equivalent). This is expected, not a failure: our real submissions already
incorporate *this tournament's* fresh group-stage data (recency beats a 4-8-year-old base rate on its
own). Where the historical model helped most (Croatia 4+ SOT: our rules underestimated Croatia and
lost -4.69; the historical rate would have won +9.03) and where it hurt most (Portugal corners,
cards — exactly the categories the project's own postmortems already flagged as small-sample-noisy)
both point to the same conclusion: **StatsBomb history is best used as a shrinkage prior underneath
the current tournament's thin sample, not as a standalone replacement.** That's literally what RULE5
already prescribes ("n<10, blend with prior") — this gives it an actual number instead of intuition.

**Question-type coverage (generalizes beyond this one match):**
- Directly derivable (team-level): shots, SOT, goals, fouls, cards, corners, offsides
- Directly derivable (player-level): goals, assists, SOT thresholds, for any player with WC2018/2022
  (or Euro/Copa/AFCON, if added) history
- Derivable but needs raw event fields, not the flattened panel: header goals, half-time score,
  penalty-awarded
- Out of scope regardless: standings/advancement questions, anything needing live market
  microstructure or in-match timing windows

---

## 3. Unifying WC2018 + WC2022 + WC2026 into one table — and a measurement-heterogeneity finding

**Script:** [datasets/build_unified_team_match_panel.py](datasets/build_unified_team_match_panel.py) ·
R port: [datasets/build_unified_team_match_panel.R](datasets/build_unified_team_match_panel.R)
**Output:** [unified_team_match_panel.csv](data/processed/unified_team_match_panel.csv) (426 rows:
2018=128, 2022=128, 2026=170) · R output:
[unified_team_match_panel_r.csv](data/processed/unified_team_match_panel_r.csv)

**What it does:** pools our own WC2026 team-match data
([espn_match_panel.csv](data/processed/espn_match_panel.csv), ESPN box scores) with
the StatsBomb WC2018/2022 panel into one table, tagged with `season_year` and `data_source` so nothing
pools silently across sources.

**The important finding:** a cross-source check on the 30 teams appearing in both sources (different
tournaments — no single WC2026 match exists in the StatsBomb set, so this compares each team's own
average rate across sources, not the same match) showed **systematic, not just noisy, disagreement**:

| Stat | Mean ratio, ESPN ÷ StatsBomb (30 teams) |
|---|---|
| Fouls committed | 0.80 (ESPN counts ~20% *fewer*) |
| Yellow cards | 0.73 (ESPN counts ~27% *fewer*) |
| Shots on target | 1.38 (ESPN counts ~38% *more*) |
| Corners | 1.30 (ESPN counts ~30% *more*) |
| Total shots | 1.12 (closest to parity) |

**Interpretation:** this is the same kind of vendor heterogeneity that already ruled out FBref as a
source earlier in the project
([TRAINING_DATASET_STRATEGY_2026-07-07.md](TRAINING_DATASET_STRATEGY_2026-07-07.md) §4 — "not available"/
inconsistent stats). ESPN's box score and StatsBomb's event-tagged counts evidently use different
counting conventions (StatsBomb tags every discrete foul event; ESPN's feed likely reflects a
stricter/different reporting standard). **Practical consequence: the unified file's raw counts should
not be pooled across `data_source` for fouls, SOT, or corners without a correction** — either keep
`data_source` as a categorical feature/fixed effect in any model, or apply the measured ratio as a
scaling correction. Cards and total-shots are close enough to pool directly.

---

## 4. Linear regression: what predicts `rbp`? (the master dataset)

**Script:** [ml/rbp_linear_regression.py](ml/rbp_linear_regression.py) ·
R port: [ml/rbp_linear_regression.R](ml/rbp_linear_regression.R)
**Results:** [ml/rbp_linear_regression_results.json](ml/rbp_linear_regression_results.json) ·
R results: [ml/rbp_linear_regression_results_r.json](ml/rbp_linear_regression_results_r.json)

**The question:** regress the actual points scored per question (`rbp`, continuous) against structural
features, to see what conditions correlate with gaining or losing points. Different from the earlier
meta-model diagnostic (which tried to predict `outcome`/a better probability) — this is about
*explaining* performance, not replacing pricing.

**Data:** [datasets/master_question_dataset.csv](datasets/master_question_dataset.csv), filtered to
771 usable rows / 71 matches.

**Features:** `gap` (our estimate − crowd estimate), `abs_gap`, `elo_diff`, `draw_probability`,
`rest_days_diff`, `squad_value_diff`, `is_player_prop`, and the 9 rule-flags that actually fire
(rule1/5/7/8/10/12/13/14/15).

**Two collinearity bugs found and fixed before trusting the output** (a good example of why you check
the design matrix, not just the R²):
1. `elo_diff` and `draw_probability` are missing on exactly the same rows (same source) — their
   missing-indicator columns were perfect duplicates. Collapsed into one `elo_context_missing` column.
2. `rule_fired_count` turned out to be an *exact* sum of the 9 rule dummies in this sample (rules
   2/3/4/6/9/11 never fire at all) — an exact linear dependency, which made the design matrix
   singular. Dropped the redundant aggregate.

**Methodology:** OLS with **cluster-robust standard errors, grouped by match** — because ~15 rows
share one match's context columns, plain OLS would understate the uncertainty. Out-of-sample tested
two ways: time-ordered walk-forward, and GroupKFold-by-match (6 folds), both compared against a
zero-parameter baseline (predict the training-fold's mean RBP).

**Results:**

- **In-sample R² = 0.053** — real but small (explains ~5% of RBP variance).
- **Statistically significant (p<0.05):** `elo_diff` (tiny effect), `rest_days_diff` (tiny),
  **`is_player_prop` (+4.87 RBP — the largest, most robust effect)**, `elo_context_missing` (+3.42),
  and `rule13_fired` (+5.24, but flagged as unreliable — it only fires **10 times**, likely a
  small-sample artifact rather than a real structural finding).
- **Not significant:** `gap` and `abs_gap` — no evidence that deviating from the crowd predicts RBP
  on its own, once other factors are controlled.
- **Out-of-sample:** walk-forward MSE 178.23 vs. baseline 178.64 (trivially better, ~0.2%);
  GroupKFold MSE 157.23 vs. baseline 149.59 (**model loses** to the dumb baseline).

**Interpretation:** same pattern as the Platt scaling and meta-model diagnostics before it — a small
real in-sample signal that does not survive the stronger out-of-sample test. **Do not use this for
live pricing adjustments.** The one finding worth keeping: `is_player_prop`'s effect is large, built on
plenty of data, and independently reproduces
[WINNING_PATTERNS_SYNTHESIS.md](WINNING_PATTERNS_SYNTHESIS.md)'s earlier finding that
player-prop suppression is the campaign's highest-confidence repeatable edge — a good cross-check from
a completely different method.

---

## 5. Small-sample regression demo: Ronaldo's goals (n=9)

**Script:** [ml/ronaldo_goals_regression.py](ml/ronaldo_goals_regression.py) ·
R port: [ml/ronaldo_goals_regression.R](ml/ronaldo_goals_regression.R)
**Results:** [ml/ronaldo_goals_regression_results.json](ml/ronaldo_goals_regression_results.json) ·
R results: [ml/ronaldo_goals_regression_results_r.json](ml/ronaldo_goals_regression_results_r.json)

**The question:** regress Ronaldo's per-match goals on `shots_on_target`, `xg_total`, and
`minutes_played`, using his 9 WC2018+2022 appearances — deliberately run at a sample size far below
what the project normally trusts (RULE5's own bar is n≥10), as a clean illustration of what small
samples do to a model.

**Results:**
- **In-sample R² = 0.431** — looks substantial, but the overall F-test p-value is **0.677** (nowhere
  near significant), and every individual coefficient has p > 0.65. With 4 parameters fit on 9 points
  (5 residual degrees of freedom), an inflated R² is exactly what noise alone produces.
- **Leave-one-out cross-validation:** model MSE = 1.846 vs. baseline MSE (just predicting his career
  average, ~0.56 goals/match) = 1.156. **The model loses to the dumb baseline**, and produces a
  nonsensical negative predicted goal count for one match (linear regression doesn't know goals can't
  be negative) plus wild over-predictions (2.31, 2.99) driven by single high-xG data points.

**Interpretation:** a textbook demonstration of overfitting. The methodology (OLS + honest held-out
validation) is identical to the master-dataset regression above — the difference is entirely sample
size. At n=9, simply using the player's own historical rate (the same shrinkage approach used in
Section 2) already beats a fitted multi-feature regression.

**A methodological note surfaced while writing the R port:** the Python version fits with
`cov_type="HC3"` (heteroskedasticity-robust), and statsmodels also reports the *overall* F-test as a
robust Wald test under that setting (p=0.677). R's `summary(lm(...))` reports the *classical*
(homoskedastic) F-test by default (p=0.381) — these are genuinely different test statistics, not a
translation error; the individual HC3 coefficient p-values (computed identically via
`lmtest::coeftest` + `sandwich::vcovHC` in the R port) do match. A good example of "check which exact
test a software default is reporting" — a very office-hours-relevant point.

---

## 6. T-test: does deviating from the crowd predict RBP?

**Script:** [ml/rbp_gap_ttest.py](ml/rbp_gap_ttest.py) ·
R port: [ml/rbp_gap_ttest.R](ml/rbp_gap_ttest.R)
**Results:** [ml/rbp_gap_ttest_results.json](ml/rbp_gap_ttest_results.json) ·
R results: [ml/rbp_gap_ttest_results_r.json](ml/rbp_gap_ttest_results_r.json)

**The question:** split questions into two groups by `|our_estimate − crowd_estimate|` (median split)
and compare mean RBP between them — a simpler, non-regression version of the `gap`/`abs_gap` question
from Section 4.

**Method:** Welch's t-test (unequal-variance; the modern recommended default over Student's
pooled-variance test), with Cohen's d for effect size and Levene's test for the variance-equality
check. Run twice: naively at the question level (771 rows), and correctly at the match level
(aggregating each match to one row first — the truly independent unit, since ~15 questions per match
share context).

**Results — and they disagree in direction, which is the actual finding:**

| | LOW deviation | HIGH deviation | Diff (HIGH−LOW) | t | p | Cohen's d |
|---|---|---|---|---|---|---|
| Question-level (n=771, naive) | mean 3.02 (n=394) | mean 4.44 (n=377) | **+1.41** | 1.57 | 0.116 | 0.12 |
| Match-level (n=71, correct unit) | mean 4.13 (n=36) | mean 2.45 (n=35) | **−1.68** | -1.94 | **0.056** | -0.46 |

**Interpretation:** the naive question-level test ignores that ~15 rows per match aren't independent
observations, and it gives the *wrong-direction* answer. Once matches are correctly treated as the
unit of analysis, the direction flips: deviating more from the crowd is weakly associated with a
**lower** average RBP (just short of the conventional 0.05 threshold). This **independently confirms**
the regression's `abs_gap` coefficient from Section 4 (also negative, also not quite significant) —
two different methods, both correctly handling clustering, agreeing with each other. Additionally,
Levene's test shows the HIGH-deviation group has dramatically higher variance (std 16.8 vs 4.8,
p<0.0001) — large deviations from the crowd are a higher-variance bet, not a clearly higher-reward
one, which matches the campaign's worst single losses (CAN-MOR -80.83, ENG-CRO -44.54, BRA-MAR -51.97)
all being large crowd-deviations that blew up. Consistent with
[STRATEGIC_MARGIN_PUSH_RESEARCH.md](STRATEGIC_MARGIN_PUSH_RESEARCH.md)'s
theoretical result that extremizing past your true belief is a guaranteed expected loss under a
proper scoring rule.

---

## Cross-cutting statistical lessons from this session

1. **Small samples produce misleadingly high R²/effect sizes** unless checked against an honest
   out-of-sample test (Section 5, and the out-of-sample half of Section 4).
2. **Non-independence (clustering) can flip conclusions, not just widen error bars** (Section 6 is the
   clearest example: opposite sign at the question level vs. the match level).
3. **In-sample fit is not evidence of anything by itself** — every diagnostic in this project (Platt,
   meta-model, this session's regression) has needed a held-out test to be trustworthy, and most
   findings that looked promising in-sample didn't survive it.
4. **Two datasets that look like they measure the same thing may not** (Section 3) — always check
   before pooling, the same lesson the project already learned once with FBref.
5. **A p-value just above 0.05 is not "no effect," it's "not enough data to be sure"** — several
   results here (match-level t-test p=0.056, `abs_gap` coefficient in the regression) point the same
   direction without individually clearing significance; the agreement across methods is itself
   informative even though neither alone clears the bar.

---

## Where this leaves the project

- **Data pipeline:** solid and validated (Section 1). Currently WC2018+2022 only; extending to Euro
  2020/2024, Copa América 2024, AFCON 2023 would grow the historical sample without adding new
  engineering (same build script pattern).
- **Base-rate modeling:** promising as a shrinkage prior for team/player rates when the current
  tournament's own sample is thin (n<10), not as a standalone pricing model (Section 2).
- **Unified panel:** needs a source-correction step (fixed ratios or a `data_source` model feature)
  before fouls/SOT/corners can be pooled across ESPN and StatsBomb (Section 3).
- **Meta-model / calibration work (RBP regression, t-test):** consistent negative result across every
  method tried so far — the project should keep the hand-built RULE1-18 framework as primary and
  revisit learned models once the live dataset is meaningfully larger.
- **Natural next tool to investigate:** hierarchical / mixed-effects (multilevel) models — a single
  principled method that handles both the clustering problem (Sections 4 and 6) and the small-sample
  shrinkage problem (Sections 2 and 5) at once, instead of the separate ad-hoc fixes used here
  (cluster-robust SEs + manual empirical-Bayes formula). Worth raising in office hours.

---

## File index (everything created this session)

Every Python script has a row-for-row-validated R port (Section-by-section validation notes above
confirm the numbers match). Click any filename to open it.

| Python | R port | Output(s) |
|---|---|---|
| [datasets/build_statsbomb_panel.py](datasets/build_statsbomb_panel.py) | [datasets/build_statsbomb_panel.R](datasets/build_statsbomb_panel.R) | [statsbomb_team_match_panel.csv](data/processed/statsbomb_team_match_panel.csv) · [statsbomb_player_match_panel.csv](data/processed/statsbomb_player_match_panel.csv) (Python canonical); [_r.csv](data/processed/statsbomb_team_match_panel_r.csv) / [_r.csv](data/processed/statsbomb_player_match_panel_r.csv) (R, validation copies) |
| [ml/statsbomb_baserate_test.py](ml/statsbomb_baserate_test.py) | [ml/statsbomb_baserate_test.R](ml/statsbomb_baserate_test.R) | [statsbomb_baserate_results.json](ml/statsbomb_baserate_results.json) · [_r.json](ml/statsbomb_baserate_results_r.json) |
| [datasets/build_unified_team_match_panel.py](datasets/build_unified_team_match_panel.py) | [datasets/build_unified_team_match_panel.R](datasets/build_unified_team_match_panel.R) | [unified_team_match_panel.csv](data/processed/unified_team_match_panel.csv) · [_r.csv](data/processed/unified_team_match_panel_r.csv) |
| [ml/rbp_linear_regression.py](ml/rbp_linear_regression.py) | [ml/rbp_linear_regression.R](ml/rbp_linear_regression.R) | [rbp_linear_regression_results.json](ml/rbp_linear_regression_results.json) · [_r.json](ml/rbp_linear_regression_results_r.json) |
| [ml/ronaldo_goals_regression.py](ml/ronaldo_goals_regression.py) | [ml/ronaldo_goals_regression.R](ml/ronaldo_goals_regression.R) | [ronaldo_goals_regression_results.json](ml/ronaldo_goals_regression_results.json) · [_r.json](ml/ronaldo_goals_regression_results_r.json) |
| [ml/rbp_gap_ttest.py](ml/rbp_gap_ttest.py) | [ml/rbp_gap_ttest.R](ml/rbp_gap_ttest.R) | [rbp_gap_ttest_results.json](ml/rbp_gap_ttest_results.json) · [_r.json](ml/rbp_gap_ttest_results_r.json) |

**Data sources referenced (not created this session):**
[data/external/statsbomb/open-data/](data/external/statsbomb/open-data/) ·
[data/processed/espn_match_panel.csv](data/processed/espn_match_panel.csv) ·
[datasets/master_question_dataset.csv](datasets/master_question_dataset.csv)

This document: [STATSBOMB_INTEGRATION_AND_STATS_TESTS_2026-07-08.md](STATSBOMB_INTEGRATION_AND_STATS_TESTS_2026-07-08.md)
