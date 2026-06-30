# Probabilistic Forecasting Dataset Design
## Research Memo — SportsPredict Probability Cup

**Date:** 2026-06-28  
**Context:** FIFA World Cup 2026 JumpTheCrowd Competition — AbirC (Souparneya), global rank #161, 556 forecasts

---

## Executive Summary

Our dataset is a **tournament-style binary probabilistic forecasting** dataset: ~3,563 forecasters each submit a 0–100 integer probability for YES/NO questions about individual match events, scored against the binary outcome using Relative Brier Points (RBP). This structure has a near-exact analogue in the academic literature — the Good Judgment Project (GJP), which ran from 2011–2015 with ~2,800 forecasters, thousands of geopolitical questions, and over a million forecasts.

**Three actionable takeaways for our dataset:**

1. **The forecast is the atomic unit.** One row = (forecaster × question). Store everything about that pairing: the probability given, the outcome, the Brier score, the question category, and the timing relative to match start. Do not collapse to forecaster-level summaries until analysis.

2. **Separate question difficulty from forecaster skill at derivation time.** Raw Brier scores confound the two: a 0.30 Brier score on "Will Brazil score first?" (crowd 85%) is worse than 0.30 on "Will there be a red card?" (crowd 50%). The literature strongly recommends deriving IRT-based difficulty parameters or at minimum a crowd-baseline-adjusted score — which RBP already partially does.

3. **Question category is a first-class feature.** Our dataset spans at least 4 distinct question archetypes (match outcome, goals threshold, individual player performance, corner/shot counts). The hard-easy effect and systematic calibration biases differ by category — this is the most tractable place to find actionable insight.

---

## 1. Analogous Problems in the Literature

### 1.1 Good Judgment Project (GJP) — Closest Analogue

**Citation:** Mellers et al. (2015), "Identifying and Cultivating Superforecasters as a Method of Improving Probabilistic Predictions." *Perspectives on Psychological Science*, 10(3), 267–281.

The GJP ran four annual forecasting tournaments (2011–2015) sponsored by IARPA (the US intelligence community's research arm). ~2,800 volunteer forecasters predicted binary and multinomial geopolitical events: "Will Greece exit the Eurozone?", "Will North Korea conduct a nuclear test?", etc.

**Structural similarity to our data:**

| Feature | GJP | Our Data |
|---|---|---|
| Unit of prediction | Binary YES/NO | Binary YES/NO |
| Probability format | 0–100% integer | 0–100% integer |
| Scoring rule | Brier score | Relative Brier Points |
| Forecaster count | ~2,800 | ~3,563 |
| Questions per tournament | ~500 | ~709 |
| Forecasts per player | Variable (0–500+) | 0–709 |
| Temporal structure | Days/weeks before resolution | Hours before match kickoff |
| Public/private leaderboard | Public | Public |

**Key difference:** GJP allowed forecasters to *revise* their predictions before resolution (tracked as multiple forecast records per person per question). Our platform does not appear to allow revisions — each forecaster submits one probability per question. This simplifies our dataset structure considerably.

**Dataset schema used in GJP research** (from Mellers et al. 2015; Baron et al. 2021):

| Column | Type | Notes |
|---|---|---|
| `forecaster_id` | UUID | Anonymized |
| `question_id` | UUID | |
| `probability` | float (0.0–1.0) | Submitted estimate |
| `outcome` | int (0/1) | Resolved YES=1, NO=0 |
| `brier_score` | float | (prob − outcome)² |
| `days_to_resolution` | float | How far from resolution at submission |
| `forecast_sequence` | int | Position among revisions (1=first) |
| `question_category` | string | Domain of the question |
| `question_difficulty` | float | Derived — see §4 |

---

### 1.2 Metaculus Public Dataset

**Source:** Metaculus platform; academic usage in Zou et al. (2022), "Forecasting Future World Events with Neural Networks," *NeurIPS 2022*.

Metaculus hosts binary and numeric questions. The academic dataset extracted for this paper ("AutoCast") includes:

- **Question-level:** background text, resolution criteria, close date, resolve date, domain tag
- **Forecast-level:** timestamp, submitted probability, human crowd median at time of forecast
- **Resolution-level:** final outcome, crowd accuracy vs. individual accuracy

The crowd median at prediction time is structurally identical to what RBP does: it scores you relative to the crowd baseline. Metaculus uses a modified log score (not Brier), but the dataset design is transferable.

**Relevant to us:** Metaculus explicitly records a `community_prediction` at the time each forecast was submitted. This enables computing whether each individual was above or below crowd consensus — which is the key predictor of long-run RBP.

---

### 1.3 Iowa Electronic Markets (IEM) and Prediction Markets

**Source:** Berg et al. (2008), "Results from a Dozen Years of Election Futures Markets Research." *Handbook of Experimental Economics Results*.

Prediction markets differ from our setting: prices are set by supply and demand rather than elicited probabilities. However, the **calibration validation framework** is identical:

- Bucket prices into intervals (0.0–0.1, 0.1–0.2, ..., 0.9–1.0)
- For each bucket, compute fraction of events that resolved YES
- A perfectly calibrated forecaster should have bucket midpoints ≈ empirical frequency

This reliability diagram approach (Murphy 1973) applies directly to our data: group all forecasts where a player predicted 60–70%, and check what fraction of those questions resolved YES. Systematic deviation = miscalibration.

---

### 1.4 Weather Ensemble Forecasting (EMOS)

**Source:** Gneiting et al. (2005), "Calibrated Probabilistic Forecasting Using Ensemble Model Output Statistics and Minimum CRPS Estimation." *Monthly Weather Review*, 133(5), 1098–1118.

Weather forecasting calibration is the most mathematically rigorous parallel domain. EMOS (Ensemble Model Output Statistics) post-processes ensemble model outputs into calibrated probabilistic distributions. Key transferable concepts:

- **Reliability:** Does forecasted probability match empirical frequency?
- **Sharpness:** Does the forecaster commit to definite probabilities (near 0 or 1) rather than hedging at 50?
- **Proper scoring rules:** Only scores that incentivize honest probability reporting (Brier, log score, CRPS) should be used to rank forecasters.

For binary outcomes, the Brier score is the proper scoring rule of choice. Our platform already uses it.

---

### 1.5 Clinical Probability Elicitation

**Source:** O'Hagan et al. (2006), "Uncertain Judgements: Eliciting Experts' Probabilities." *Wiley.*

In clinical trials, epidemiologists elicit prior distributions from domain experts about event probabilities (e.g., "What is the probability this drug reduces mortality by >10%?"). The dataset structure is simpler than ours (fewer questions, fewer forecasters) but the **elicitation methodology** is well-studied. Key finding: domain experts are systematically overconfident at extreme probabilities (>90% or <10%) — the same bias expected in sports forecasting.

---

## 2. Recommended Schema

This is the recommended flat-file schema for our core dataset. One row = one forecast (one player, one question).

### 2.1 Core Table: `forecasts.csv`

| Column | Type | Source | Description |
|---|---|---|---|
| `forecast_id` | UUID | derived | Unique row ID (player_id + market_id) |
| `player_id` | UUID | API | Forecaster's unique identifier |
| `player_name` | string | API | Display name at time of forecast |
| `global_rank` | int | API | Player's rank in probability cup leaderboard |
| `smart_rating` | float | API | JTC Smart Rating (0–100) as proxy for engagement |
| `match_id` | UUID | API | Match identifier |
| `match_name` | string | API | "{HomeTeam} vs {AwayTeam}" |
| `home_team` | string | API | |
| `away_team` | string | API | |
| `match_result` | string | API | "H" (home), "A" (away), "D" (draw) |
| `match_date` | date | API | Match kickoff date (UTC) |
| `market_id` | UUID | API | Question identifier |
| `question_text` | string | API | Full question text as displayed to forecaster |
| `question_category` | string | derived | See §2.2 |
| `question_team` | string | derived | Team the question concerns (if applicable) |
| `question_player` | string | derived | Named player in question (if applicable) |
| `threshold_value` | float | derived | Numeric threshold (e.g., 2.5 for "goals over 2.5") |
| `direction` | string | API | "YES" (user predicted YES) |
| `probability_pct` | int | API | Raw integer 0–100 submitted by forecaster |
| `probability` | float | derived | `probability_pct / 100` |
| `probability_logit` | float | derived | `log(p / (1-p))` — clipped at 0.001, 0.999 |
| `outcome` | int | API | 1=YES, 0=NO |
| `brier_score` | float | derived | `(probability - outcome)²` |
| `log_score` | float | derived | `-log(probability)` if YES, `-log(1-probability)` if NO |
| `crowd_probability` | float | API | Crowd consensus at question close (avg_entry_price / 100) |
| `crowd_logit` | float | derived | Logit of crowd consensus |
| `relative_brier` | float | derived | `crowd_brier - player_brier` (positive = beat crowd) |
| `trade_date` | datetime | API | Timestamp when prediction was submitted |
| `market_status` | string | API | "settled" |
| `season` | string | derived | "WC2026" |
| `competition_round` | string | API | "Group Stage", "Round of 16", etc. |

### 2.2 Question Category Taxonomy

Assign each question to one of these five categories based on question text:

| Category Code | Description | Examples |
|---|---|---|
| `MATCH_RESULT` | Match outcome (winner, draw) | "Will Spain win?", "Will this match end in a draw?" |
| `GOALS` | Goal-related totals | "Will total goals be over 2.5?", "Will there be a 0-0?" |
| `PLAYER_GOAL` | Individual player scoring | "Will Kane score ≥0.5 goals?", "Will Ronaldo score?" |
| `SET_PIECE` | Corners, cards, fouls | "Will corners be >10.5?", "Will there be a red card?" |
| `SHOTS` | Shots on target, total shots | "Will shots on target be >5.5?" |

**Why this matters:** Systematic overconfidence differs by category. Players may be well-calibrated on MATCH_RESULT but overconfident on PLAYER_GOAL (favorite player bias). You cannot detect this without category labels.

### 2.3 Secondary Table: `question_difficulty.csv`

One row per question/market. Derived from the core forecasts table.

| Column | Type | Description |
|---|---|---|
| `market_id` | UUID | |
| `question_text` | string | |
| `question_category` | string | |
| `base_rate` | float | Fraction of similar questions that resolved YES (historical, if available) |
| `crowd_probability` | float | Mean predicted probability across all forecasters |
| `crowd_entropy` | float | `-(p * log(p) + (1-p) * log(1-p))` — max at 50/50 |
| `n_forecasters` | int | Number of players who predicted this question |
| `outcome` | int | |
| `crowd_brier` | float | `(crowd_probability - outcome)²` |
| `discrimination` | float | IRT-derived (see §4.3) |
| `difficulty` | float | IRT-derived |

### 2.4 Secondary Table: `player_calibration.csv`

One row per player. Aggregated from core forecasts table.

| Column | Type | Description |
|---|---|---|
| `player_id` | UUID | |
| `player_name` | string | |
| `global_rank` | int | |
| `total_forecasts` | int | |
| `mean_brier` | float | Simple average Brier score across all questions |
| `mean_log_score` | float | |
| `mean_rbp` | float | Mean relative_brier |
| `total_rbp` | float | Cumulative relative Brier Points (= leaderboard score) |
| `calibration_slope` | float | From logistic regression: outcome ~ logit(probability) — slope=1 is perfect |
| `calibration_intercept` | float | Intercept from above regression — 0 is perfect |
| `mean_probability` | float | Average probability submitted (>0.5 = bold forecaster) |
| `overconfidence_idx` | float | Mean(probability - empirical_fraction) for 10 equal-width buckets |
| `resolution_score` | float | Murphy decomposition: `mean((crowd_p - base_rate)²)` |
| `n_by_category` | JSON | Forecast counts broken down by question_category |
| `mean_brier_by_category` | JSON | Per-category Brier scores |
| `irt_skill` | float | IRT-estimated latent ability (see §4.3) |

---

## 3. Unit of Analysis

The literature is clear on this, and the GJP methodology is the template. There is no single "correct" unit — each level serves different questions:

### 3.1 Forecast Level (player × question) — **Primary table**

Use for:
- Computing individual Brier scores and all derived metrics
- Training predictive models (question features + player history → expected Brier)
- Detecting question-level miscalibration (which questions systematically stump good forecasters?)
- Calibration curve construction per player

**Key rule:** Never aggregate before storing. Always store the atomic forecast.

### 3.2 Question Level (question × resolution) — Secondary

Use for:
- Measuring crowd wisdom vs. individual wisdom
- Question difficulty analysis
- IRT item parameter estimation
- Finding questions where crowd is miscalibrated (prediction market inefficiencies)

### 3.3 Player Level (one row per forecaster) — Tertiary

Use for:
- Leaderboard and ranking
- Cross-tournament skill persistence analysis
- Identifying superforecasters vs. novices
- Demographic analysis (country, engagement)

**Key insight from Baron et al. (2021):** When limited data exists, individual-difference measures (numeracy, past engagement) predict future accuracy. Once ≥25 settled forecasts exist for a player, their past Brier score is the dominant predictor of future Brier score — more than any static trait. Our threshold: **30+ settled forecasts** for reliable skill estimation.

---

## 4. Derived Features and Transformations

### 4.1 Brier Score Decomposition (Murphy 1973)

The Brier Score can be decomposed into three additive components. For a single forecaster across N questions:

```
BS = REL - RES + UNC
```

Where:
- **Uncertainty (UNC):** `mean(base_rate × (1 − base_rate))` — variance in question outcomes. Fixed by the question set; not in the forecaster's control. Use crowd probability as base_rate proxy.
- **Reliability (REL):** Measures how far the forecaster's stated probabilities deviate from observed frequencies within each probability bin. A well-calibrated forecaster has REL ≈ 0.
- **Resolution (RES):** Measures how much the forecaster's probability estimates vary around the base rate. High resolution means the forecaster assigned very different probabilities to questions that had different outcomes — they *discriminated* well.

**Practical computation:**
1. Sort all forecasts by submitted probability
2. Bin into k=10 equal-count bins
3. For each bin k: `REL_k = n_k × (mean_prob_k − empirical_freq_k)²`
4. `REL = Σ REL_k / N`
5. `RES_k = n_k × (empirical_freq_k − overall_base_rate)²`
6. `RES = Σ RES_k / N`

A good forecaster minimizes REL (well-calibrated) and maximizes RES (decisive, discriminating).

### 4.2 Log Score (Ignorance Score)

```
LS = -log₂(p)     if outcome = YES
LS = -log₂(1-p)   if outcome = NO
```

Lower = better. The log score penalizes overconfidence much more heavily than the Brier score. A player who says 99% YES and the event resolves NO gets a log score of ≈6.6 (catastrophic), while the Brier score only penalizes 0.98. For our setting (where extreme overconfidence on player goals is common), log score is a useful complementary metric.

**Implementation note:** Clip probabilities to [0.001, 0.999] before log transformation to avoid infinite penalties.

### 4.3 Item Response Theory (IRT) Skill Decomposition

**Citation:** Merkle & Steyvers (2016), "Choosing a Strictly Proper Scoring Rule." *Decision*, 3(1), 40–55. Also Baron et al. (2014), "Two Reasons to Make Aggregated Probability Forecasts More Extreme."

The core insight: a forecaster who always answers "easy" questions (large crowds > 90%) can look well-calibrated without being skilled. IRT separates:

- **Forecaster ability θᵢ** — the latent skill of player i
- **Question difficulty bⱼ** — inherent unpredictability of question j
- **Question discrimination aⱼ** — how well question j separates skill levels

For each question-player pair, the expected Brier score is modeled as a function of `(θᵢ − bⱼ)`. Players with high `θᵢ` consistently beat the expected Brier for their question difficulty.

**Practical simplification for our dataset:** Use `relative_brier = crowd_brier − player_brier` as an IRT approximation. A positive value means the player beat the crowd on that question. The crowd probability already encodes difficulty — so relative scoring is already doing most of the IRT adjustment. Full IRT fitting requires ≥10 forecasts per question per player, which we have.

### 4.4 Calibration Curve (Reliability Diagram)

For each player (minimum 30 forecasts):
1. Bucket all forecasts into 10 bins: [0–10), [10–20), ..., [90–100]
2. For each bin: compute `mean(outcome)` = observed frequency
3. Plot predicted probability (x) vs. observed frequency (y)
4. Perfect calibration = diagonal (y=x)
5. Fit: `calibration_slope, calibration_intercept` via logistic regression

Interpretation:
- **Slope < 1:** Overconfidence (too extreme)
- **Slope > 1:** Underconfidence (too conservative, hedging near 50%)
- **Intercept > 0:** Systematic YES bias
- **Intercept < 0:** Systematic NO bias

### 4.5 Logit Transformation

Always store and analyze probabilities in log-odds (logit) space for:
- Aggregation: mean logit is better than mean probability (avoids regression to 50%)
- Regression: logit is the natural link for binary outcomes
- Extremizing: GJP found that crowd aggregates improved when pushed 20% further from 50% after averaging in logit space

```python
import numpy as np
def logit(p, clip=1e-3):
    p = np.clip(p, clip, 1 - clip)
    return np.log(p / (1 - p))
```

### 4.6 Recency-Weighted Accuracy

For predicting future performance, recent forecasts should be weighted more heavily than old ones. Use exponential decay:

```
w_t = exp(-λ × days_since_forecast)
weighted_brier = Σ(w_t × brier_t) / Σ(w_t)
```

Recommend `λ = 0.02` (half-life ≈ 35 days). Tune empirically on held-out matches.

---

## 5. Pitfalls to Avoid

These are specific to our data structure, not generic statistical warnings.

### 5.1 Temporal Leakage

**Problem:** Match results are known before you analyze the data. If you accidentally use `match_result` (home win / away win / draw) as a feature to compute question-level difficulty *before* splitting into train/test, you've leaked future information.

**Fix:** Treat each match day as a transaction. When predicting match N's outcome, use only data from matches 1 through N−1 to estimate player skill and question difficulty. In practice: use a rolling-window or expanding-window scheme where `test_date > train_date` for all pairs.

### 5.2 Sparse Forecasters

**Problem:** 3,563 players exist in our global leaderboard, but many have <30 forecasts. A player with 5 forecasts who scored 5/5 looks perfect but has zero reliable skill signal.

**Fix:** Always report forecast count alongside calibration metrics. Flag players with `n < 30` as "insufficient sample" for skill estimation. For modeling: use regularization (shrink estimates toward group mean) rather than excluding sparse players — Bayesian partial pooling is the right tool.

### 5.3 Question Selection Bias

**Problem:** Not every player forecasts every question. Top players (709/709 forecasts) may have different question distributions than casual players (30/709). If difficult questions are systematically avoided by weak forecasters, comparisons become invalid.

**Fix:** For calibration analysis, always condition on `n_forecasters > threshold` per question. Compute participation rate per question and store as a feature. When comparing players A and B, note whether they forecasted the same questions.

### 5.4 Extreme Base Rates

**Problem:** Questions with crowd consensus >90% or <10% distort calibration estimates. With very few YES or NO outcomes in a bin, the empirical frequency is unreliable (high variance). The hard-easy effect predicts that players will be overconfident on low-probability events (e.g., "Will Cabo Verde score 3+ goals?") and underconfident on near-certainties.

**Fix:** Exclude questions with `crowd_probability < 0.05 or > 0.95` from calibration curve fitting. Analyze them separately as "tail questions." Report coverage statistics for your calibration curves.

### 5.5 Multiple Testing Across Question Categories

**Problem:** If you test for miscalibration across 5 question categories and 10 probability bins, that's 50 comparisons. Some will appear significant by chance.

**Fix:** Apply Bonferroni correction or use a hierarchical model with question category as a group-level effect. Report effect sizes, not just p-values.

### 5.6 Crowd as Baseline is Not Fixed

**Problem:** RBP scores you relative to the *crowd baseline*, but the crowd evolves as more players submit predictions. Late predictors forecast against a crowd that already includes early predictors. In our dataset, `crowd_probability` reflects the final crowd average, not the crowd at the moment of individual submission.

**Fix:** Where possible, store the crowd snapshot at the time of each forecast. If this is unavailable (as in our current API), note the limitation clearly and treat `crowd_probability` as a closing-time average. Avoid analysis that assumes the crowd baseline is fixed across all forecasters on a given question.

### 5.7 Two Accounts / Duplicate Users

**Problem:** We confirmed at least 2 players in the top 30 have duplicate accounts (michhaelm HK at ranks 11 and 20; aa0 at ranks 27 and 28). Treating these as independent observations inflates the effective sample.

**Fix:** Deduplicate by `player_name` + `country` before any population-level analysis. Flag suspected duplicates. Exclude duplicates from leaderboard-level statistics.

---

## 6. Crowd Aggregation — Using Our Dataset for Ensemble Forecasting

Beyond analyzing individual calibration, our dataset enables crowd aggregation experiments. Key findings from the literature:

**Simple average is suboptimal.** The crowd mean in probability space is compressed toward 50% due to the mathematical properties of probability averaging. A crowd that is 70% sure about something should have its aggregate pushed further from 50% — the "extremizing" result.

**Recommended aggregation (Satopää et al. 2014):**
```
1. Convert each player's probability p to log-odds: log(p / (1-p))
2. Compute the weighted mean log-odds, weighting by player's historical RBP
3. Convert back to probability: 1 / (1 + exp(-mean_log_odds))
4. Extremize: push result 20% further from 0.5 (empirically validated on GJP data)
```

**Elite forecaster weighting.** GJP found that using the top 2% of forecasters ("superforecasters") and weighting by recent accuracy outperforms the full crowd by ~30% in Brier score reduction. We can replicate this: use our global ranking to identify the top ~70 players and build an elite ensemble.

---

## 7. Structural Comparison to Non-Sports Analogues

| Domain | Dataset | Structural Match | Key Difference |
|---|---|---|---|
| Geopolitical events | Good Judgment Project | Very High | GJP allows forecast revisions; our data does not |
| Political elections | FiveThirtyEight, IEM | High | Elections have weeks of resolution time vs. 90-min matches |
| Community forecasting | Metaculus | High | Metaculus uses log score, not Brier; GJP closer |
| Weather ensembles | ECMWF EMOS datasets | Medium | Weather is a model ensemble, not human elicitation |
| Clinical priors | Expert probability elicitation | Low | Fewer questions, single forecast per expert, no tournament |
| Financial prediction markets | PredictIt, Kalshi | Medium | Markets use prices not elicited probabilities; different incentive structure |

**Bottom line:** The GJP data structure and the academic literature built around it (Mellers 2015, Merkle & Steyvers 2016, Baron et al. 2021) is the correct reference class. Sports tournament context differs only in question domain and resolution time scale — the forecasting and calibration methodology is identical.

---

## 8. Next Steps: What to Model First

Given what we have (AbirC's 556 forecasts once scraped, plus top-30 global players' question-level data from today's matches), here is the recommended modeling sequence:

### Step 1: Scrape and structure the core dataset
- Scrape AbirC's full prediction history from profile page
- Merge with market outcomes from `data/today_2026-06-27/markets_jtc.csv` and `markets_classic.csv`
- Produce `forecasts.csv` following §2.1 schema
- Assign `question_category` labels (5 categories from §2.2)

### Step 2: Compute basic calibration metrics
- Reliability diagram for AbirC across all 556 forecasts
- Per-category Brier scores
- Compare to global rank (does AbirC's calibration justify rank #161?)

### Step 3: Question difficulty analysis
- Compute `crowd_probability` for each question
- Find questions where crowd was systematically wrong (high `crowd_brier`)
- Identify which question categories have the worst crowd calibration

### Step 4: Skill persistence check (once ≥30 matches are available)
- Split by match date: train on first 50% of match days, test on second 50%
- Does early Brier predict late Brier? This validates whether the leaderboard reflects true skill or variance.

### Step 5: Build elite ensemble
- Use top 30 global players' forecasts (we have today's data)
- Compute extremized logit-space aggregate
- Compare to crowd consensus: does the elite ensemble beat the crowd?

---

## References

- Berg, J., Forsythe, R., Nelson, F., & Rietz, T. (2008). Results from a dozen years of election futures markets research. *Handbook of Experimental Economics Results*, 1, 742–751.
- Brier, G. W. (1950). Verification of forecasts expressed in terms of probability. *Monthly Weather Review*, 78(1), 1–3.
- Baron, J., Mellers, B. A., Tetlock, P. E., Stone, E., & Ungar, L. H. (2014). Two reasons to make aggregated probability forecasts more extreme. *Decision Analysis*, 11(2), 133–145.
- Baron, J., Scott, S., Fincher, K., & Metz, S. E. (2015). Why does the hard-easy effect disappear in many within-subject designs? The role of cognitive effort information. *Psychonomic Bulletin & Review*, 22(1), 14–22.
- Gneiting, T., Raftery, A. E., Westveld, A. H., & Goldman, T. (2005). Calibrated probabilistic forecasting using ensemble model output statistics and minimum CRPS estimation. *Monthly Weather Review*, 133(5), 1098–1118.
- Good, I. J. (1952). Rational decisions. *Journal of the Royal Statistical Society: Series B*, 14(1), 107–114. [*Origin of the log score.*]
- Mellers, B., Stone, E., Murray, T., Minster, A., Rohrbaugh, N., Bishop, M., ... & Tetlock, P. (2015). Identifying and cultivating superforecasters as a method of improving probabilistic predictions. *Perspectives on Psychological Science*, 10(3), 267–281.
- Merkle, E. C., & Steyvers, M. (2013). An IRT forecasting model: Linking proper scoring rules to item response theory. *Judgment and Decision Making*, 8(4), 430–448.
- Murphy, A. H. (1973). A new vector partition of the probability score. *Journal of Applied Meteorology*, 12(4), 595–600. [*The canonical Brier decomposition.*]
- Satopää, V. A., Baron, J., Foster, D. P., Mellers, B. A., Tetlock, P. E., & Ungar, L. H. (2014). Combining multiple probability predictions using a simple logit model. *Management Science*, 60(2), 444–457.
- Scott, S. L., & Varian, H. R. (2015). Predicting the present with Bayesian structural time series. *International Journal of Mathematical Modelling and Numerical Optimisation*, 5(1–2), 4–23.
- Siegert, S. (2017). Simplifying and generalising Murphy's Brier score decomposition. *Quarterly Journal of the Royal Meteorological Society*, 143(704), 1178–1183.
- Tetlock, P. E., & Gardner, D. (2015). *Superforecasting: The Art and Science of Prediction*. Crown.
- Zou, A., Xiao, T., Rajkumar, R., & Steinhardt, J. (2022). Forecasting future world events with neural networks. *NeurIPS 2022*.

---

*Document generated: 2026-06-28. Working directory: `/Users/aki/Desktop/QK Rstudio/sportspredict_research/bot/`*
