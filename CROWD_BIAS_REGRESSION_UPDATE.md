# Crowd-Bias Regression: Update from n=85 to n=384

**Date:** 2026-07-03  
**Author:** Souparneya Chakrabarti  
**Dataset:** `datasets/master_question_dataset.csv`  
**Script:** R (inline, reproducible — see Section 4)

---

## 1. Background and Motivation for This Update

### What existed before

Early in the campaign — approximately nine matches into the group stage — the project fit a regression relating submitted probability estimates to the platform-revealed crowd consensus. The original model was:

```
crowd_estimate ≈ 0.514 + 0.61 × (our_estimate − 0.5)
```

Fitted on **n = 85** question-level observations across nine matches. Reported statistics:

| Statistic | Value |
|---|---|
| n | 85 |
| Intercept | 0.514 |
| Slope | 0.61 |
| Slope SE | 0.0455 |
| 95% CI on slope | [0.518, 0.699] |
| Pearson r | 0.83 |
| Residual SD | 7.17 pp |
| Out-of-sample RMSE | 5.8 pp (BEL–EGY holdout, 1 match) |

This was documented in `JTC_WC2026_Research_Paper.Rmd` (Equation 1) and the project memory file `project_jtc_overview.md`.

### Why it needed updating

The n=85 figure was a snapshot from early in the campaign. By the time the paper was written, the master dataset contained 436 questions with RBP scores across 49 matches — more than 5× the original sample. Running the regression on 85 observations when 384 complete paired observations (our estimate + crowd estimate) are available on disk is unnecessary: it overstates uncertainty, and the coefficients could have drifted materially as the crowd's behaviour evolved across the tournament.

Additionally, at n=85 the confidence intervals on the slope were wide enough that the compression claim ("the crowd compresses ~39% toward 50%") carried meaningful uncertainty. A five-fold expansion in sample size either confirms that finding robustly or forces a revision to it.

A secondary motivation: the regression is referenced in the abstract, Section 5 heading, and Equation (1) of the paper. Any coefficients cited there should reflect the best current evidence, not an early-campaign snapshot.

---

## 2. Data Used

**Source file:** `datasets/master_question_dataset.csv`  
**Built by:** `datasets/build_master_dataset.py` from raw per-match JSON files in `data/external_markets/`

### Filtering criteria

The regression sample was defined as all rows satisfying:

1. `actually_submitted == "True"` — only questions that were actually submitted to the JTC platform (excludes 20 unsubmitted questions: 11 from the BIH–QAT missed-deadline incident, 10 from URU–CPV calibration-only round)
2. `our_estimate` is not NA — a submitted estimate exists
3. `crowd_estimate` is not NA — the crowd consensus was captured post-resolution

This yielded **n = 384** observations.

### Why not 436?

The paper references 436 scored (RBP-bearing) questions. The gap between 436 and 384 arises because:
- 460 rows have `actually_submitted = True`
- Of these, 76 lack a recorded `crowd_estimate` (crowd consensus not captured for those questions at data-collection time)
- Net: 460 − 76 = 384 complete paired observations

An additional constraint: the `master_question_dataset.csv` covers **June 11–25, 2026 only** (the group stage). Knockout-stage matches from June 28 onward (MEX–ECU, FRA–SWE, NED–MAR, ENG–CDR, BEL–SEN, and others) are stored in the newer `matches/{team}_{team}_{date}/` directory format and have not yet been merged into the master dataset. The regression on n=384 is therefore strictly group-stage data.

### Dataset summary

| Variable | n non-null | Range |
|---|---|---|
| `our_estimate` | 406 | [0.04, 1.00] |
| `crowd_estimate` | 434 | [0.17, 0.92] |
| `outcome` | 473 | {0, 1} |
| Regression sample (all three + submitted) | 384 | — |

---

## 3. Regression Model

### Specification

The regression follows the same functional form as the original:

```
crowd_estimate ~ intercept + slope × (our_estimate − 0.5)
```

Centering `our_estimate` at 0.5 makes the intercept directly interpretable as the crowd's expected probability when our estimate is 0.5 (i.e., the crowd's neutral anchor).

Fitted in R using `lm()` with no additional covariates or interaction terms. No heteroskedasticity correction was applied; the residual plot did not reveal gross variance scaling.

---

## 4. Reproducible R Code

```r
df <- read.csv("datasets/master_question_dataset.csv", stringsAsFactors = FALSE)

# Filter to complete, submitted observations
submitted <- df[
  df$actually_submitted == "True" &
  !is.na(df$our_estimate) &
  !is.na(df$crowd_estimate),
]

# Fit regression
model <- lm(crowd_estimate ~ I(our_estimate - 0.5), data = submitted)
summary(model)
confint(model)

# RMSE
sqrt(mean((submitted$crowd_estimate - predict(model))^2))

# Direction split
below <- submitted[submitted$our_estimate < 0.5, ]
above <- submitted[submitted$our_estimate > 0.5, ]

# Time-ordered out-of-sample check (first 250 → last 134)
submitted_sorted <- submitted[order(submitted$date, submitted$question_num), ]
train <- submitted_sorted[1:250, ]
test  <- submitted_sorted[251:nrow(submitted_sorted), ]
model_train <- lm(crowd_estimate ~ I(our_estimate - 0.5), data = train)
pred_test   <- predict(model_train, newdata = test)
sqrt(mean((test$crowd_estimate - pred_test)^2))   # OOS RMSE
mean(test$crowd_estimate - pred_test)              # OOS bias
```

---

## 5. Results

### 5.1 Full-sample regression (n = 384)

```
crowd_estimate = 0.5109 + 0.5998 × (our_estimate − 0.5)
```

| Statistic | Value |
|---|---|
| n | 384 |
| Intercept | 0.5109 |
| Slope | 0.5998 |
| Intercept SE | 0.00388 |
| Slope SE | 0.02077 |
| 95% CI on slope | [0.559, 0.641] |
| Pearson r | 0.828 |
| R² | 0.686 |
| Residual SD | 7.23 pp |
| In-sample RMSE | 7.21 pp |
| F-statistic | 834.5 (df: 1, 382) |
| p-value (slope) | < 2.2 × 10⁻¹⁶ |

### 5.2 Out-of-sample check (time-ordered split)

Training set: first 250 observations by date and question number.  
Test set: remaining 134 observations.

| Statistic | Value |
|---|---|
| Training slope | 0.635 |
| Training intercept | 0.519 |
| OOS RMSE | 8.44 pp |
| OOS bias (mean error) | −1.72 pp |

The slope in the training half (0.635) is slightly higher than in the test half, suggesting mild drift — the crowd may have marginally more compression in the later group stage, or the training sample's composition happens to include more extreme estimates. The OOS bias of −1.72 pp is small relative to the residual SD.

### 5.3 Direction split

| Direction | n | Mean (our estimate) | Mean (crowd estimate) | Crowd overestimates "unlikely" by |
|---|---|---|---|---|
| Our estimate < 0.5 | 249 | 0.337 | 0.413 | +7.7 pp |
| Our estimate > 0.5 | 125 | 0.647 | 0.596 | −5.1 pp (underestimates "likely") |
| Our estimate = 0.5 | 10 | 0.500 | — | — |

The crowd systematically overestimates the probability of events we consider unlikely and underestimates events we consider likely — the precise signature of favourite–longshot bias under a Brier-scored tournament \citep{snowbergwolfers2010}.

### 5.4 Compression evidence

| Statistic | Value |
|---|---|
| Fraction of questions where crowd is less extreme than us (compressed) | 75.8% |
| Fraction of questions where crowd is more extreme than us | 20.3% |
| Fraction equal | 3.9% |

In 3 out of every 4 questions, the crowd's probability sits closer to 0.5 than our submitted estimate — direct evidence of the compression effect the whole strategy is built around.

### 5.5 Mean RBP by estimate confidence bin

| Our estimate range | n | Mean RBP | Beat-crowd rate |
|---|---|---|---|
| < 0.30 (high confidence "NO") | 79 | +3.42 | 78.5% |
| 0.30 – 0.40 | 70 | +1.17 | 72.9% |
| 0.40 – 0.50 | 88 | +2.94 | 64.8% |
| 0.50 – 0.60 | 54 | +1.68 | 55.6% |
| 0.60 – 0.70 | 40 | +2.28 | 75.0% |
| > 0.70 (high confidence "YES") | 31 | −0.81 | 64.5% |

The only estimate bin with a negative mean RBP is the highest-confidence "YES" range (>0.70). This is consistent with the Platt-scaling diagnostic finding: when both the model and the crowd are already confident in the same direction, the gap between them is too small to generate reliable edge. Questions where we believe something is very likely but the crowd also believes it is fairly likely leave little room to win on the spread.

The strongest bins are the high-confidence "NO" range (<0.30, +3.42 avg RBP, 78.5% beat-crowd) — where our low estimate departs furthest from the crowd's compressed-toward-50% anchor — and the moderate-confident "YES" range (0.60–0.70, +2.28, 75%), which benefits from the same mechanism in the opposite direction without yet approaching the diminishing-returns zone above 0.70.

---

## 6. Comparison: Original vs. Updated Model

| | **Original (n=85)** | **Updated (n=384)** | **Change** |
|---|---|---|---|
| n | 85 | 384 | +4.5× |
| Intercept | 0.514 | 0.511 | −0.003 |
| Slope | 0.61 | 0.60 | −0.01 |
| Slope SE | 0.0455 | 0.0208 | −54% |
| 95% CI slope | [0.518, 0.699] | [0.559, 0.641] | Width halved: 0.181 → 0.082 |
| Pearson r | 0.83 | 0.828 | −0.002 |
| Residual SD | 7.17 pp | 7.23 pp | Stable |
| RMSE | 5.8 pp (1-match OOS) | 8.44 pp (time-ordered OOS split) | More conservative estimate |
| Direction split (below 0.5) | 7 pp crowd overestimate | 7.7 pp | Stable |

### Interpretation

The model is **remarkably stable**. The slope moved by only 0.01 (0.61 → 0.60), the intercept by 0.003, and the Pearson r is essentially unchanged. This is strong evidence that the crowd-compression finding is not an artefact of the early-campaign sample: it replicates across the full group stage at 4.5× the original sample size.

The key improvement is not in the coefficients but in the **confidence intervals**. With n=384 and a slope SE of 0.021, the 95% CI is [0.559, 0.641] — comfortably excluding both 0 (no compression) and 1.0 (no compression; crowd tracks us perfectly). This is the first time the compression claim has been statistically robust rather than directionally suggestive.

The higher RMSE at n=384 (7.21 pp in-sample) vs. the original 5.8 pp (one-match OOS) should not be interpreted as degraded fit. The original 5.8 pp was a single-match holdout on BEL–EGY, which could easily have been an unusually easy match. The 7.21 pp figure is a full in-sample residual SD across 384 diverse questions.

---

## 7. What Needs to Change in the Paper

The following locations in `JTC_WC2026_Research_Paper.Rmd` cite the n=85 model and need updating:

| Location | Old text | New text |
|---|---|---|
| Abstract | "fit on n=85 questions (r=0.83)" | "fit on n=384 submitted questions (r=0.83)" |
| Section 5.1, paragraph 1 | "fit on n=85 questions across nine matches (r=0.83, residual SD ≈ 7.1 pp). Out-of-sample validation on a further match (BEL–EGY) produced RMSE = 5.8 pp" | "fit on n=384 submitted questions across the full group stage (r=0.828, residual SD = 7.23 pp). A time-ordered out-of-sample check (first 250 questions as training, remaining 134 as test) produced RMSE = 8.44 pp and a mean bias of −1.72 pp" |
| Equation (1) | `0.514 + 0.61 ×` | `0.511 + 0.60 ×` |
| Section 5.1, direction split | "average (0.361) falls almost exactly on the realized base rate (0.361), while the crowd's average (0.430) overestimates" | Update with 0.337 / 0.413 from the new sample |
| 95% CI | Not reported | Add [0.559, 0.641] |

The slope change from 0.61 to 0.60 is negligible in practical terms (1 percentage point of compression difference), but the n citation is a material inaccuracy in the paper as it currently stands and should be corrected before sharing.

---

## 8. Open Questions for Future Updates

1. **Knockout stage integration.** The current regression covers only the group stage (June 11–25). Once the knockout matches (MEX–ECU, FRA–SWE, NED–MAR, ENG–CDR, and subsequent rounds) are merged into `master_question_dataset.csv`, the regression should be re-run. The question of interest: does the crowd behave differently in knockout matches (higher viewer engagement, more public exposure) vs. group stage?

2. **Question-category stratification.** The compression slope may differ meaningfully between question types (match-winner vs. player SOT vs. timing props). A single pooled slope is the best current estimate but may mask heterogeneity.

3. **Temporal stability.** The train/test split showed a slope shift (0.635 in early data vs. ~0.57 implied in later data). A rolling-window regression on 30-question windows would reveal whether the crowd is becoming more or less compressed over the tournament's duration.

4. **Asymmetry check.** The current model imposes a single slope for both directions (our estimate above and below 0.5). A richer model would allow separate slopes for each half: it is plausible that the crowd compresses more aggressively on low-probability events than high-probability events.
