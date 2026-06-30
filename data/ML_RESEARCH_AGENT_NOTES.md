# ML Integration Research Notes: JTC Sports Probability Forecasting
## Compiled: June 22, 2026
w
**Purpose:** Deep research to guide ML integration into the Jump Trading Competition (JTC) probability forecasting pipeline. The goal is NOT to build a match outcome predictor from scratch — it is to learn when our estimates are well-calibrated vs. systematically biased vs. the crowd, and to exploit those systematic biases.

**Context:** We submit probability forecasts for 10 binary yes/no props per football match. Performance = RBP = crowd_brier_score - our_brier_score (positive = beat crowd). We have ~300 settled questions as of June 22, 2026.

---

## Section 1: Dataset Construction

### 1A. Cross-Match Feature Design

The feature matrix for any ML layer must capture two things simultaneously: (1) the information content of our estimate relative to the truth, and (2) the structural context that determines whether the crowd is systematically wrong.

**Core feature candidates, in rough priority order:**

**Market anchor features (highest priority):**
- `has_smarkets_price` (binary): Whether a Smarkets market price existed for this prop
- `smarkets_price` (float, or NaN if no market): The raw market-implied probability
- `our_estimate` (float): Our submitted probability
- `logit_diff = logit(our_estimate) - logit(smarkets_price)`: Signed deviation from market in logit space — this is the most compact representation of "how much we deviated from market and in which direction"
- `abs_logit_diff`: Absolute deviation from market
- `market_liquidity_proxy`: If available, a proxy for how liquid the Smarkets market was (e.g., number of runners, spread); liquid markets are harder to beat

**Question type features:**
- `question_type_category` (categorical): One of {tier1_market, tier2_realdata, stats_proxy, match_winner, ...} — encode as one-hot or target-encode with regularization
- `prop_family` (categorical): A coarser grouping — {goals, shots, offsides, fouls, cards, corners, player_individual, match_result} — more stable than fine-grained question type
- `prop_direction`: Is the prop about the FAVORITE doing something vs. the UNDERDOG doing something? (binary or {fav_offensive, fav_defensive, und_offensive, und_defensive})
- `is_player_prop` (binary): Player-specific vs. team-aggregate
- `is_over_under` (binary): Over/under a threshold vs. head-to-head comparison

**Match context features:**
- `elo_diff = elo_home - elo_away`: Pre-match Elo strength differential (normalized)
- `elo_fav_diff`: Elo difference favoring the perceived favorite (always positive)
- `implied_win_prob_favorite`: Win probability of the stronger team from ordered logit
- `match_type`: {WC_group, WC_knockout, friendly, qualifier} — covariate shift correction
- `is_neutral_venue` (binary)
- `rest_days_home`, `rest_days_away`: Days since last match
- `altitude_m`: Venue altitude (particularly relevant for WC2026)
- `total_squad_value_ratio`: log(fav_total_mkt_value / und_total_mkt_value) from Transfermarkt

**Named rule features (see caution in 1D):**
- `rule_fired_count`: How many named rules (RULE1–RULE15) fired for this question
- `rule_direction`: Net direction of fired rules (+1 = toward YES, -1 = toward NO, 0 = mixed/neutral)
- Individual binary indicators for each rule: `rule2_fired`, `rule10_fired`, `rule15_fired`, etc.

**Target variable options:**
- `rbp`: Realized RBP for this question (regression target)
- `beat_crowd`: Binary (1 if rbp > 0) (classification target)
- `optimal_deviation`: logit(outcome_mean_estimate) - logit(crowd_estimate) — conceptually the best possible adjustment, but requires held-out data to estimate properly

**Recommendation on target:** Start with `rbp` as a regression target using a simple linear model. This preserves the continuous signal and avoids thresholding. Do NOT optimize classification accuracy — calibration research (Sec 2 below) shows this is the wrong objective for probability forecasting.

### 1B. The Small-N Problem

**This is the most critical constraint.** With ~300 settled questions (June 22), we are operating far below reliable ML thresholds.

**Events-per-variable (EPV) rule:**
The clinical prediction modeling literature (Peduzzi et al. 1996; Riley et al. 2019, "Minimum sample size for developing a multivariable prediction model") establishes:
- Hard minimum: 10 EPV (10 positive-class outcomes per model variable)
- Recommended: 20 EPV for stable estimates
- Modern guidance: The rule is about *events* (the rarer binary outcome), not total rows

For binary props hovering around 50% base rate: ~300 questions ≈ ~150 YES outcomes. This supports at most **5–15 predictors** before the model becomes unreliable. With EPV=20, we can support at most 7–8 predictors total. Every additional predictor beyond that increases the risk that we're fitting noise.

**What this means practically:**
- No gradient boosting with 50+ features — you will overfit catastrophically
- No separate models per question type — you don't have enough data in any subgroup
- Simple regularized logistic regression or ridge regression on 6–10 carefully chosen features is the appropriate model family right now
- Isotonic regression for calibration adjustment is dangerous at n=300 — use Platt scaling (2-parameter logistic) instead

**Bayesian approaches for small-n:**
The Bayesian hierarchical partial-pooling framework (Gelman & Hill; Efron & Morris's James-Stein shrinkage) is the right conceptual framework here. Key ideas:
- Rather than estimating a separate "rule effectiveness" for RULE2 vs. RULE10 vs. RULE15, treat them as draws from a common distribution of rule effects and pool
- Shrink each rule's estimated edge toward the grand mean; the more data you have for a specific rule, the more you trust its individual estimate vs. the pooled average
- James-Stein shrinkage: the optimal shrinkage factor is data-driven, with more shrinkage toward the prior when n is small
- In Stan/brms: `effect ~ (1 | rule_id)` gives you this automatically

**Bayesian vs. frequentist at n=300:**
For the purposes of the JTC, the Bayesian framing is conceptually cleaner but computationally heavier. A pragmatic middle ground: use ridge regression (L2 regularization) as a frequentist approximation to a Gaussian prior on coefficients. This provides shrinkage without MCMC. The regularization parameter λ can be tuned via leave-one-out cross-validation (strictly time-ordered).

**Sample size milestones to track as tournament progresses:**
- n < 200 (past): Descriptive statistics and rule discovery only; no ML
- n = 200–500 (NOW): Single regularized model with ≤8 features; interpret coefficients as suggestive, not definitive
- n = 500–1000: Add one interaction term; can start segmenting by prop_family with ≥50 obs per group
- n > 1000: Full hierarchical model justified; separate calibration per question type becomes viable
- n > 2000: Gradient boosting with careful LOOCV becomes reasonable; SHAP analysis becomes trustworthy

**The tournament growth rate:** ~200 new settled questions per week (20 matches × 10 questions). By end of WC2026 (approx. 4–6 weeks), we'll have 800–1400 settled questions. This unlocks the 500–1000 range by mid-tournament end. Do not rush the ML layer.

### 1C. The Heterogeneity Problem

The 10 questions per match span fundamentally different prop types. A "will there be 2+ offsides" question has a completely different generative model from "will Team A win" or "will Player X get a SOT."

**The one-model-vs-many-models tradeoff:**

Arguments for a single global model:
- More data per fit (n=300 total vs. n=30–50 per prop type cluster)
- Forces you to discover generalizable features rather than prop-specific quirks
- Proper scoring rule (Brier score) is the same regardless of prop type, so the target is unified

Arguments for separate models per cluster:
- The relationship between elo_diff and crowd_miscalibration is very different for match_winner props vs. offsides props
- The Smarkets market anchor is extremely informative for match_winner but less so for corner counts
- Risk of the global model learning a confounded signal that averages away the useful variation

**Recommended architecture:**
One global model with `prop_family` as a feature (one-hot encoded). This gives you the data efficiency of pooling while allowing the model to learn different intercepts and, crucially, different slopes for the interaction between `prop_family` and `logit_diff`. This is exactly what hierarchical regression (or fixed-effect categorical features with interaction terms) achieves.

Encoding strategy for `question_type_category`:
- Do NOT use high-cardinality one-hot if you have many categories and few observations per category
- Group into 5–6 `prop_family` buckets: {match_result, goals, shots_cards_fouls, offsides_corners, player_individual, other}
- Mean-target encode with regularization (target encoding with add-k smoothing) if you need the fine-grained type as a feature

### 1D. Temporal Leakage — THE MOST CRITICAL SECTION

**Rule 1: Never use random splits. Always walk-forward.**

Because all data is time-ordered (matches happen in sequence), any test-set observation chronologically precedes some training-set observations in a random split. This violates the fundamental premise that the model only uses past information to predict future observations. Standard k-fold CV is completely inappropriate here.

Walk-forward validation protocol:
1. Sort all 300 settled questions by match date
2. Train on first k observations (say k=150)
3. Predict on observations k+1 through k+m (say next 30 questions = 3 matches)
4. Roll forward: retrain on first k+m, predict on next m
5. Aggregate out-of-fold predictions; compute RBP on those predictions
6. The resulting RBP estimate is a valid lower bound on expected forward performance

Minimum training window: At least 10 matches (100 questions) before making any predictions. The first 10 matches' data should be used as a pure burn-in period.

**Rule 2: Named rules are the biggest leakage risk.**

This is subtle and critical. RULE1 through RULE15 were discovered by observing patterns in the settled question data. When we encode `rule2_fired` as a feature in a model that is evaluated on the same data from which RULE2 was discovered, we have circular leakage: the model "learns" that RULE2 correlates with RBP because RULE2 was defined to capture exactly that correlation.

This is analogous to the "data snooping bias" documented in financial econometrics (Harvey et al. 2016, EFMA 2020). Academic research suggests at least 50% of positive findings from in-sample rule discovery may be false when evaluated out-of-sample.

The appropriate fix depends on the situation:

**Option A (cleanest): Strict holdout of post-discovery data.** 
If RULE2 was discovered from matches 1–20, then include `rule2_fired` as a feature only when evaluating on matches 21+. Never evaluate on any data that was used to discover the rule.

**Option B: Cross-validated discovery.**
Run the rule discovery process separately on each fold. This is expensive but eliminates leakage entirely. Specifically: for each walk-forward fold, discover rules using only the training-window data, then test whether those rules fire beneficially on the held-out window.

**Option C: Treat rules as soft priors.**
Instead of treating rules as features to be "learned" by the ML model (which creates the circular leakage problem), treat the rules as domain-knowledge-based adjustments applied *before* the ML layer sees the data. Then the ML layer is trained on the *residuals* from the rule-adjusted estimate. This is cleaner conceptually.

**Recommendation:** Use Option C as the primary approach. The ML model should predict the gap between (our current rule-adjusted estimate) and the optimal submission. The rule system remains the first-layer signal; ML is purely a recalibration layer on top.

**Rule 3: Do not let the crowd formula contaminate the feature space.**

Our crowd formula is: `crowd ≈ 0.514 + 0.61*(us - 0.5)`. This means `crowd` is a deterministic function of `us` (our estimate). If we include `our_estimate` in the ML feature set and try to predict `rbp = crowd_brier - our_brier`, we are essentially predicting a function that involves `our_estimate` three times: once as a direct feature, once inside `crowd_estimate` (which depends on `our_estimate`), and once inside `our_brier`. This creates non-trivial collinearity and may inflate apparent predictive power.

The cleaner approach: use `logit(our_estimate)` as the single anchor, and use `logit_diff = logit(our_estimate) - logit(smarkets_price)` as the deviation feature. This decouples the market information from our model output.

### 1E. The "Our Estimate is a Model Output" Problem

Our submitted estimate is not an independent signal. It was derived from:
1. A Smarkets market price (if available) — this already embeds crowd information
2. A Poisson/Skellam model — this embeds historical football base rates
3. Named rule adjustments — these are from the same settled data

This creates a fundamental identification problem: if we use `our_estimate` to predict RBP, we are partly predicting a function of the crowd estimate itself (since our estimate partly determines what crowd estimate is observed).

**The information decomposition:**
Think of our estimate as: `our_estimate = market_signal + model_signal + rule_adjustment + noise`

The ML should try to isolate the `model_signal` component — specifically, the part of our estimate that diverges from the market and that diverges in the *right* direction. The best proxy for this is `logit_diff` (our logit minus the market logit), which nets out the shared market information.

For questions with no market: the full logit of our estimate is the signal, but it should be treated as inherently lower-confidence (higher uncertainty) than market-anchored estimates.

---

## Section 2: Calibration and Probability Estimation

### 2A. Why Calibration, Not Accuracy

The foundational result from Bennett & Shawe-Taylor and the JTC-relevant literature (Mamlouk et al. 2023, "Machine learning for sports betting: Should model selection be based on accuracy or calibration?", arXiv 2303.06021) is unambiguous: **calibration dominates accuracy for probability forecasting tasks with a scoring-rule payoff.**

The study trained models on NBA data and evaluated them using actual betting returns. Calibration-based model selection yielded +34.69% ROI vs. -35.17% for accuracy-based selection. In the best case: +36.93% vs. +5.56%. This is not a marginal difference — it is the difference between a profitable and unprofitable system.

Why? Because accuracy (fraction correct) is insensitive to probability distance, while the Brier score (and RBP) penalizes overconfident wrong forecasts severely. A model that says 0.9 when the true probability is 0.6 and the outcome is NO is penalized heavily (squared error = 0.81) even though it "correctly identified" the higher-probability outcome. Calibration measures whether the model's stated probabilities match empirical frequencies, not whether it classifies correctly.

**Implication for JTC:** Never select a model variant based on its classification accuracy or AUC. Select based on Brier score on the walk-forward held-out set. Brier score IS the right loss function; minimize it directly.

### 2B. Brier Score Decomposition for Heterogeneous Questions

The Merkle, Steyvers et al. (2018) paper "Weighted Brier score decompositions for topically heterogenous forecasting tournaments" (Judgment and Decision Making) is directly applicable to our situation. The standard Murphy/Yates Brier decomposition into uncertainty, calibration, and discrimination assumes questions are drawn from the same class of events.

When our 10 questions span different prop types (match_result, offsides, player_SOT, etc.), the base rate for "Alternative A" varies across questions, making the standard decomposition nonsensical. The Merkle et al. fix: use resampling to average over all possible alternative orderings, producing a valid decomposition despite heterogeneous question types.

**Practical implication:** When evaluating our system's calibration, stratify the analysis by `prop_family`. Compute:
- Calibration curve (reliability diagram) for each prop_family separately
- Resolution component per prop_family
- Whether miscalibration is systematic (always overestimate YES) or random noise

**The RBP formulation vs. standard Brier:** The JTC's relative scoring RBP = crowd_brier - our_brier rewards beating the crowd, not minimizing our absolute Brier score. This means we want to shift our estimates *away from 0.5 in the direction of the outcome* more than the crowd did. But this creates a risk: if we're wrong and the crowd was right, we are punished doubly (we moved further from the outcome). The objective is therefore not unconditionally "move further from 50%" but specifically "identify cases where the crowd is systematically biased and move in the correct direction."

### 2C. Ensemble Calibration Methods

When combining multiple signals (Poisson model, market price, rule adjustments), the resulting ensemble probability is often miscalibrated. The standard recalibration pipeline:

**Platt scaling (logistic regression on logit-transformed outputs):**
- Fit: `log-odds(outcome) = a + b * log-odds(our_estimate)` on a calibration set
- Interpretation: b > 1 means our estimates are underconfident (compressed toward 0.5); b < 1 means overconfident
- Advantage: Only 2 parameters, data-efficient, appropriate for n=300
- Limitation: Only corrects monotonic linear miscalibration on logit scale

**Isotonic regression:**
- Non-parametric monotone mapping; no assumptions about the shape
- Disadvantage: Can overfit with n < 1000; produces "staircase" functions
- Verdict: Not appropriate until we have 1000+ settled questions per calibration group

**Beta calibration:**
- More flexible than Platt, captures asymmetric miscalibration (different behavior near 0 vs. near 1)
- Useful if we discover that our model is overconfident specifically on high-probability events but well-calibrated on 50/50s
- 3 parameters; requires n > 500 to be trustworthy

**Recommendation for now:** Platt scaling. Fit it separately for each `prop_family` if n per family ≥ 50; otherwise use a single global Platt scaling. Use logit-space (not probability-space) inputs.

**The logistic recalibration diagnostic:** Before building any ML, run this diagnostic:
```
logit(outcome) ~ intercept + slope * logit(our_estimate)
```
If the fitted slope is systematically < 1, we are overconfident. If > 1, underconfident. If the intercept is nonzero, we have a systematic directional bias. This 2-parameter model tells you a great deal about where the problem lies.

---

## Section 3: Transfer Learning and Domain Adaptation

### 3A. What the 49k Historical Dataset Can and Cannot Give Us

The 49,400 historical matches (1872–2026) with walk-forward Elo ratings are excellent for:
- Estimating home advantage magnitude
- Estimating Elo rating predictive power for match outcomes
- Learning time-decay parameters for the Poisson GLM
- Establishing base rates for goals scored per match by Elo-differential bin

The 49k dataset does NOT contain:
- Shots on target, offsides, fouls, corners, cards — the statistics underlying most JTC props
- Player-level data (who played, who was injured)
- In-match tactical information

This creates a structural gap: our strongest historical signal (Elo) predicts goals and W/D/L, but most JTC props are about the granular in-match statistics we don't have 49k rows of data for.

**What transfer is actually possible:**

1. **Covariate transfer (feature transfer):** Use Elo-derived features (elo_diff, implied win probability) as inputs to models predicting prop outcomes. We already do this. The question is how *much* Elo predicts each prop type.

   Prior knowledge to encode: Elo differential should predict match_winner props strongly, goals props moderately, and have weaker but nonzero relationships with shot-count, offside-count, and foul props (because strong teams create more SOT opportunities, but fouls and offsides are partly tactical and less Elo-dependent).

2. **Prior elicitation from domain knowledge:** For each prop_family, we can use historical football statistics databases (not just our 49k) to establish a strong prior:
   - Average offsides per team per match: ~2–3 (so "2+ offsides" has a base rate around 50–70%)
   - Average SOT per player per match for forwards: ~1–2
   - Average yellow cards: ~2 per match total
   
   These base rates, combined with team-quality adjustments, give us a starting prior that is far better than 50/50 even without JTC-specific data.

3. **Strength-proxy from Transfermarkt:** Thomas Peeters' research (cited in testing the Wisdom of Crowds field paper) showed that Transfermarkt aggregate squad valuations predict international match outcomes comparably to Elo and better than FIFA rankings. Our 2,455 current national team player valuations provide a complementary strength signal for WC2026 that is orthogonal to Elo history.

### 3B. Covariate Shift at WC2026

The WC2026 context differs from the full 49k-match historical distribution in several critical ways:

1. **Match quality:** All WC2026 games involve qualified national teams competing in high-stakes knockout or group matches. The 49k-match history includes friendlies (which have different tactical intensity), early qualifiers (weak vs. weak teams), and pre-competition warm-up matches.

2. **Neutralizing home advantage:** WC2026 is played in the US/Canada/Mexico — mostly neutral venues. Home advantage is structurally suppressed. The ordered logit `b_home` parameter is less relevant.

3. **Altitude distribution:** A cluster of WC2026 venues are at altitude (Mexico City etc.), creating systematic changes in physical fatigue and game pace that don't appear proportionally in the 49k history.

**Handling covariate shift:**
- Weight historical training observations by inverse propensity scores: upweight historical matches that resemble WC2026 conditions (neutral venue, high Elo teams, competitive context)
- Or equivalently: restrict the historical "base rate calibration" set to only competitive international matches between strong teams (Elo > 1600 for both sides)
- For Elo model fitting: this is already partially handled by xi=0.0008 time-decay (recent matches get higher weight)

**The domain adaptation literature** (Primer on Domain Adaptation, arXiv 2001.09994) distinguishes:
- Covariate shift: P(X) differs between train and test but P(Y|X) is the same
- Concept drift: P(Y|X) itself changes

For WC2026, we primarily face covariate shift (the game is the same, just played between different-quality teams at different venues). Importance weighting is the standard fix. Concept drift is less of a concern unless the tournament introduces structural rule changes.

---

## Section 4: Wisdom of Crowds — When Are We Actually Beating the Crowd?

### 4A. Academic Literature on Crowd Biases

**Le (2026) — "Decomposing Crowd Wisdom: Domain-Specific Calibration Dynamics in Prediction Markets" (arXiv:2602.19520)**

This is the most directly relevant recent paper. Using 292 million trades across 327,000 binary contracts on Kalshi and Polymarket, the key findings are:

- Calibration decomposes into four components: universal horizon effect, domain-specific biases, domain-by-horizon interactions, and trade-size scale effects — together explaining 87.3% of calibration variance
- **Political markets** show chronic underconfidence: prices compressed toward 50%
- **Sports markets** "come closest to the calibration ideal at short-to-medium horizons" — disciplined by professional participants and continuous information flow
- **CRITICAL WARNING:** "Consumers of prediction market prices who treat them as face-value probabilities will systematically misinterpret them, and the direction of misinterpretation depends on what is being predicted, when and by whom."

Implication for JTC: Smarkets football market prices are relatively well-calibrated (sports markets are the best-calibrated domain), but there are still domain-specific and horizon-specific deviations. We should not treat them as ground truth.

**Favourite-Longshot Bias (Griffith 1949, updated extensively):**
The most documented systematic bias in sports betting markets: longshots (high-probability of NOT happening) are systematically overpriced relative to their actual frequency; favorites (high-probability events) are underpriced. This is the mirror of underconfidence in the tail.

For JTC props: a JTC crowd that assigns 85% to "Team A (strong favorite) wins" may be systematically underestimating that probability. Conversely, a crowd assigning 15% to "underdog wins" may be overestimating it. However, Le (2026) shows this bias is domain-specific and may be smaller in liquid sports markets than in political prediction markets.

**Goal-Line Oracles study (PMC11785260):**
Crowd predictions of football expected goals show systematic favorite overestimation: the crowd overestimates XG for "big-6" clubs by an average of 0.28 goals per match. This directly validates our empirical RULE-family finding that "crowd over-inflates expected winner doing offensive thing." The mechanism: people believe strong teams create more chances than they actually do in a given match, because they anchor on team quality rather than on match-specific defensive setups.

**Home side offensive bias:** The same mechanism applies to home teams. Crowd anchors on home advantage rather than adjusting for the specific defensive qualities of the away team. This inflates expected home shots, home SOT, home goals.

**Under-pricing underdog defensive suppression:** The flip side of the above. If the crowd overestimates the favorite's offense, it simultaneously underestimates the underdog's defensive contribution to suppressing that offense. This is exactly RULE2 (2+ offsides for defending underdog is usually NO): the crowd anchors on the base rate of offsides rather than modeling the underdog's tactical retreat.

**Crowd Wisdom 2018 WC (Bruza et al., arXiv 2008.13005):**
Crowd-aggregated forecasts were competitive with statistical models for match outcomes. But crowd performance was weakest for specific in-match props (not just match results) — the crowd performs better when anchored on familiar base rates and weaker on tactical/contextual adjustments.

### 4B. The JTC-Specific Crowd Bias Structure

Based on the empirical data we have documented (from our RBP ledger and memory files):

**Confirmed crowd biases (RULE-family, proven n≥5):**
1. Crowd over-inflates "expected winner does offensive thing" by additional ~10pp above crowd formula. This is the biggest identified systematic bias.
2. "2+ offsides" family is now 9/9 NO for defending underdogs. This is a strong empirical signal but discovered in-sample — see leakage caution.
3. Crowd under-prices blowout dynamics (losing team's star forward suppressed = RULE15 candidate).

**Why the crowd formula partially corrects but not fully:**
The crowd formula (crowd ≈ 0.514 + 0.61*(us-0.5)) compresses crowd estimates toward 50% relative to ours. This is consistent with the Le (2026) finding that sports crowd markets show mild underconfidence. But the compression is applied uniformly — it does not apply more compression on "favorite does offensive thing" questions than on "balanced" questions. A question-type-conditional version of the crowd formula might be an ML-learnable refinement.

### 4C. Can ML Discover Additional Systematic Biases?

With 300 questions, we can run a targeted systematic bias search. The structure:

For each `prop_family` × `favorite_context` combination, compute:
- Mean RBP when our estimate is above 60% vs. below 40%
- Mean RBP when elo_diff is in the top quartile vs. bottom quartile
- Mean RBP when `rule_fired_count > 0` vs. = 0

Any cell with mean RBP consistently positive and n > 20 is a candidate for a new rule. This is fundamentally a data-mining exercise and must be treated with Bonferroni-like skepticism (multiple comparisons problem). With 10+ cells being tested, expect 1–2 false positives at p < 0.05 level purely by chance.

The bar for promoting a new rule: effect size > 5 RBP and n > 30 in that cell. Smaller n or effect: treat as hypothesis to monitor, not actionable rule.

---

## Section 5: The Question Difficulty / Information Structure Problem

### 5A. Two Information Regimes

**Regime 1: Market-anchored questions (tier1_market)**
- We have a Smarkets market price
- Our estimate ≈ market price + small rule adjustment
- The variance in our RBP comes primarily from whether our rule adjustment was correct
- The crowd formula gives us a reasonable estimate of what the crowd submitted
- Expected RBP per question: small positive when rules fire correctly, near-zero otherwise

**Regime 2: Model-only questions (tier2_realdata, stats_proxy)**
- No Smarkets market exists; we use Poisson/Skellam/base rates
- Our estimate may diverge significantly from what the crowd submitted
- Both our best results (GER-CUR +72.47 best ever) and worst results come from this regime
- The crowd estimate is also harder to predict (we're applying the crowd formula to a model output, not a market price)
- Expected RBP per question: high variance, both sides

**The ML architecture should treat these regimes differently:**

For Regime 1 (market-anchored): The ML question is "are our rule adjustments correctly calibrated?" The primary feature is `logit_diff`. If rules are well-calibrated, this should be near-zero on average. A well-calibrated ML model for Regime 1 would learn: which rules fire in the right direction and by how much.

For Regime 2 (model-only): The ML question is "where does our Poisson/Skellam model systematically over- or under-estimate vs. realized outcomes?" The primary features are `elo_diff`, `match_type`, `prop_family`, and the specific model parameters that generated the estimate (attack strength differential, etc.).

**Literature on models vs. markets:**
The closing line value (CLV) literature in sports betting establishes that consistently beating the closing line is the primary evidence of genuine edge (Pinnacle closing line = gold standard). The academic work (Bet-Analytix, arXiv 2406.04062) shows that models which achieve positive CLV consistently do so by identifying early mispricing before the market corrects.

For our context: Regime 1 questions already have a liquid market; we cannot beat it consistently on fundamentals alone. Our edge in Regime 1 is structural rule biases (the crowd consistently wrong about a specific prop type). In Regime 2, models can beat markets because no efficient price exists — but the uncertainty is far higher.

**Practical recommendation:** Track RBP separately by regime. If Regime 2 is driving disproportionate variance (both our best and worst results), consider capping the size of our logit deviation from 50% on model-only questions until we have more data to calibrate that regime.

---

## Section 6: Practical Architecture Recommendations

### 6A. The Proposed ML Architecture

Given all constraints above, here is the concrete architecture recommendation:

**Model 1: Platt Recalibration Layer (implement NOW)**

Input: `logit(our_rule_adjusted_estimate)`  
Output: recalibrated probability  
Method: Logistic regression with 2 parameters (intercept + slope)  
Training: Walk-forward, retrain on rolling window, evaluate on next 3 matches  
Split: Last 3 matches (30 questions) as test; all prior as train; retrain each week  

This is the lowest-risk ML step. It learns: "on average, are our estimates too extreme or too compressed?" If slope ≈ 1 and intercept ≈ 0, our estimates are already well-calibrated at the aggregate level.

**Model 2: Prop-Family Conditional Recalibration (implement at n=400)**

Input: `logit(our_estimate)`, `prop_family` (one-hot), `has_smarkets_price` (binary)  
Output: recalibrated probability  
Method: Ridge logistic regression (L2 regularization), λ tuned via LOO-CV  
This allows different calibration slopes per prop type  

**Model 3: Context-Conditional Bias Correction (implement at n=600)**

Input: (Model 2 inputs) + `logit_diff`, `elo_fav_diff`, `prop_direction`, `is_neutral_venue`  
Output: final submitted probability  
Method: Ridge logistic regression with interaction terms between `prop_family` × `prop_direction`  
Target: Walk-forward RBP (or equivalently, beat_crowd binary)  

**What NOT to build:**
- Do not build gradient boosting or neural networks (too few data points, too opaque)
- Do not build separate models per match question (no data)
- Do not build anything with >10 parameters until n > 800

### 6B. Feature List (Final Recommended Set)

For Model 3 (the primary target when we have enough data):

| Feature | Type | Priority | Notes |
|---------|------|----------|-------|
| `logit(our_estimate)` | float | Critical | The raw estimate anchor |
| `has_smarkets_price` | binary | Critical | Regime indicator |
| `logit_diff` | float | Critical | Our deviation from market |
| `prop_family` | categorical | Critical | 6 buckets, one-hot |
| `prop_direction` | categorical | High | {fav_off, fav_def, und_off, und_def} |
| `elo_fav_diff` | float | High | Normalized to [0,1] |
| `is_knockout` | binary | Medium | Tournament round |
| `rule_fired_count` | int | Medium | Net rules signaling |
| `total_squad_value_ratio` | float | Medium | Transfermarkt proxy |
| `altitude_m` | float | Low | WC2026 specific |
| `rest_days_diff` | float | Low | Fatigue proxy |

Total: 11 features. With ridge regularization, this is manageable at n=300 (effective EPV ~15 given ~50% YES rate). The L2 penalty handles the marginal features gracefully.

### 6C. Walk-Forward Protocol (Specific Implementation)

```
Week 1 (now, n≈300): Run Platt recalibration only.
  - Train on matches 1–27 (270 questions)
  - Evaluate on matches 28–30 (30 questions)
  - Report: slope, intercept, walk-forward Brier improvement

Week 2 (n≈500): Add prop_family conditional recalibration.
  - Expand training to all available data
  - 5-fold temporal cross-validation (5 sequential windows)
  - Report: per-family calibration slopes; which families most miscalibrated

Week 3–4 (n≈700): Full Model 3 with context features.
  - Include elo_fav_diff, prop_direction, logit_diff
  - Report: SHAP values for feature importance interpretation
  - Human review: do the learned coefficients match our named rules?

Week 5+ (n≥900): Optional hierarchical model in Stan/brms.
  - Pool rules under common distribution
  - Fit per-prop-family calibration intercepts
  - This replaces the ad-hoc rule-adjustment system with a principled Bayesian one
```

### 6D. Preventing Overfitting with 300 Rows

Specific anti-overfitting measures beyond walk-forward validation:

1. **Regularization:** Ridge (L2) with λ chosen by leave-one-out cross-validation. In R: `glmnet(alpha=0)` with `cv.glmnet` using `type.measure="deviance"`.

2. **Feature count discipline:** Never fit more features than n/20 (the conservative EPV=20 rule). At n=300, that's ≤15 features. Currently recommending 11.

3. **No polynomial/interaction explosion:** Only add an interaction term if it has a strong theoretical justification AND n in each cell > 30.

4. **Bootstrap optimism correction:** For any reported performance metric, compute the optimism-corrected version: take many bootstrap samples, fit on each, evaluate on OOB samples, and subtract the mean optimism from the apparent performance.

5. **Reality check:** If the walk-forward model shows >5 RBP improvement on average per question over baseline, treat that number with extreme skepticism. An additional layer of human sanity-checking the model's predictions before submission is essential.

### 6E. Explainability Requirements

Given that we do NOT want to auto-submit (we want human-in-the-loop), the model must be explainable. Concretely:

- Ridge logistic regression coefficients are directly interpretable: each coefficient is the change in log-odds of "outcome=YES" per unit change in the feature, holding others constant
- Before each match: compute per-question feature contributions using simple linear decomposition: `contribution_i = coeff_i × (feature_i - mean_i)`
- This gives a plain-language summary: "Our estimate is too high because: elo_diff says underdog is competitive (+1.2 RBP expected), prop_direction says favorite doing offensive thing (-2.1 RBP historically), net adjustment: -0.9 expected RBP"
- The human can then override if context justifies it (e.g., the "favorite" is actually playing defensively due to game situation)

### 6F. Minimum N Before Trusting ML Over Hand-Coded Rules

| ML Component | Minimum n | Rationale |
|---|---|---|
| Platt scaling (2 params) | 50 | Stable 2-parameter fit |
| Prop-family conditional recalib | 200 | ~30 obs per family |
| Full Model 3 (11 features) | 400 | EPV=20 rule |
| Gradient boosting | 2000 | Standard tree overfitting threshold |
| Separate model per prop_family | 500 per family | ~3000 total |
| Trust ML over a confirmed named rule (n≥30) | Never (complement, not replace) | Hand rules are theory-grounded; ML estimates magnitude |

**The fundamental principle:** A named rule represents a structural bias (theoretically grounded) that the ML should estimate the MAGNITUDE of, not whether to apply. RULE2 (underdog offsides suppression) was discovered theoretically and validated empirically. The ML should learn "how much adjustment RULE2 justifies" — not "should we apply RULE2 at all." Keep the rule structure; let ML calibrate the coefficients.

---

## Section 7: Literature Search — Key Papers

### 7A. Core Papers (Beyond Our Existing `papers/` Directory)

**1. Le, N.A. (2026). "Decomposing Crowd Wisdom: Domain-Specific Calibration Dynamics in Prediction Markets." arXiv:2602.19520.**
- Key finding: Calibration is domain-specific and time-varying. Sports markets are most well-calibrated; political markets show chronic underconfidence. 87.3% of calibration variance explained by 4 components.
- Relevance: HIGH. Tells us how much to trust Smarkets prices as calibration reference, and what kinds of corrections are appropriate.

**2. Mamlouk, M., et al. (2023). "Machine learning for sports betting: Should model selection be based on accuracy or calibration?" arXiv:2303.06021. Published Machine Learning with Applications, 2024.**
- Key finding: Calibration-based model selection yields +34.69% ROI vs. -35.17% for accuracy-based selection.
- Relevance: HIGH. Directly answers our model evaluation framework question. Use Brier score, not accuracy/AUC.

**3. Merkle, E.C., Steyvers, M., Mellers, B., Tetlock, P.E. (2017). "Weighted Brier score decompositions for topically heterogenous forecasting tournaments." Judgment and Decision Making, 12(3).**
- Key finding: Standard Brier decomposition breaks for heterogeneous question types; introduces weighted decomposition with phantom alternatives and resampling.
- Relevance: HIGH. Our 10 questions per match are heterogeneous. This is the right way to measure our calibration.

**4. Hvattum, L.M., & Arntzen, H. (2010). "Using ELO ratings for match result prediction in association football." International Journal of Forecasting, 26(3), 460–470.**
- Key finding: Elo-based ordered logistic regression is a competitive baseline. Betting odds do significantly better for match outcomes.
- Relevance: MEDIUM. This IS our base model. The finding that odds beat Elo models reinforces our decision to use Smarkets as a Tier 1 anchor.

**5. Bruza, P., et al. (2020). "Wisdom of the crowds forecasting the 2018 FIFA Men's World Cup." arXiv:2008.13005.**
- Key finding: Crowd aggregation is a competitive forecasting strategy; best methods outperform simpler baselines. Crowd performance is weakest on in-match props vs. match outcomes.
- Relevance: MEDIUM. Validates that our opponent (crowd wisdom) is a real and meaningful benchmark.

**6. Le, N.A. / Goal-Line Oracles study (PMC11785260, 2025). "Goal-line oracles: Exploring accuracy of wisdom of the crowd for football predictions."**
- Key finding: Crowd XG predictions overestimate "big-6" teams by 0.28 XG/match on average. Crowd underestimates match-to-match variance (predicted variance 0.33 vs. observed 0.79).
- Relevance: HIGH. Direct validation of our empirically discovered crowd bias — the mechanism behind many of our named rules.

**7. Griffith (1949) / Favourite-Longshot Bias Literature. Most recently reviewed in: Cain, M., Law, D., & Peel, D. (2000). "The favourite-longshot bias and market efficiency in UK football betting." Scottish Journal of Political Economy.**
- Key finding: Longshots (low-probability events) are systematically overpriced in betting markets; favorites underpriced. This is the most documented sports betting market inefficiency.
- Relevance: HIGH. In our context: JTC crowd may overestimate rare prop occurrences (e.g., "will underdog score first") and underestimate high-base-rate events.

**8. Peduzzi, P., et al. (1996). "A simulation study of the number of events per variable in logistic regression analysis." Journal of Clinical Epidemiology, 49(12), 1373–1379.**
Extended by: Riley, R.D., et al. (2019). "Minimum sample size for developing a multivariable prediction model." Statistics in Medicine, 38(7).
- Key finding: Minimum 10 events per variable; recommended 20 EPV for stable logistic regression estimates. Models developed with EPV < 10 show significant coefficient inflation and poor generalizability.
- Relevance: CRITICAL for our n=300 constraint. Sets the hard boundary on model complexity.

**9. Harvey, C.R., Liu, Y., & Zhu, H. (2016). "...and the Cross-Section of Expected Returns." Review of Financial Studies, 29(1), 5–68.**
- Key finding: At least 50% of published trading rule findings are false discoveries due to in-sample data mining. Demonstrates the severity of data snooping bias for rules discovered from historical data.
- Relevance: HIGH for our named rules. RULE2 through RULE15 require out-of-sample validation.

**10. Dixon, M.J., & Coles, S.G. (1997). "Modelling Association Football Scores and Inefficiencies in the Football Betting Market." Journal of the Royal Statistical Society, Series C, 46(2), 265–280.**
- Key finding: Independent Poisson mis-specifies low-scoring outcomes (0-0, 1-1, 1-0); correlation correction improves calibration. Home advantage and attack/defense strength are estimable from goals data.
- Relevance: MEDIUM. This is the base layer of our scoreline model.

**11. Karlis, D., & Ntzoufras, I. (2003). "Analysis of Sports Data by Using Bivariate Poisson Models." Journal of the Royal Statistical Society, Series D, 52(3), 381–393.**
- Key finding: Bivariate Poisson (shared Poisson component) captures score correlation more naturally than Dixon-Coles ρ correction.
- Relevance: MEDIUM. Alternative to Dixon-Coles that might improve our scoreline grid.

**12. Peeters, T. (2018). "Testing the Wisdom of Crowds in the field: Transfermarkt valuations and international soccer results." Journal of Economic Behavior & Organization, 145, 232–242.**
- Key finding: Transfermarkt aggregate squad valuations predict international match outcomes as well as Elo ratings and better than FIFA rankings. Market value is a crowd-sourced strength proxy orthogonal to historical Elo.
- Relevance: HIGH. We have Transfermarkt data for 2,455 current national team players. This is a validated feature.

**13. Lakshmanan, S., et al. (2024). "Predictive Modeling of Lower-Level English Club Soccer Using Crowd-Sourced Player Valuations." arXiv:2411.09085.**
- Key finding: Crowd-sourced Transfermarkt valuations improve match prediction in lower-league contexts where historical match data is sparse. Provides the feature engineering methodology.
- Relevance: MEDIUM. Useful for how to construct Transfermarkt features.

**14. Tetlock, P.E., & Gardner, D. (2015). "Superforecasting: The Art and Science of Prediction." Crown Publishers.**
Extended by: Mellers, B., et al. (2015). "Identifying and Cultivating Superforecasters." Perspectives on Psychological Science.
- Key finding: Superforecasters beat crowd aggregates by 20–40% through explicit calibration practices, reference class forecasting, and regular self-testing against resolved outcomes.
- Relevance: MEDIUM. Provides the behavioral/human layer that complements our statistical models. Our human review before submission should follow superforecaster discipline.

**15. Mamlouk (2023) cited above re: accuracy vs. calibration — already entry #2.**

**16. Bet-analytix / CLV literature: "Closing Odds: The Ultimate Indicator."**
- Key finding: Consistently beating the Pinnacle closing line is the strongest evidence of edge. Bettors who beat CLV produce sustained positive returns; those who don't, don't.
- Relevance: MEDIUM. Analogously, consistently beating Smarkets closing prices on our logit adjustments is evidence our rules have genuine edge, not just luck.

### 7B. Papers Worth Retrieving in Full

These appeared in search results but I could not retrieve the full text. Priority order:

1. **PMC10306238** — "A statistical theory of optimal decision-making in sports betting" — could provide the theoretical framework for when to deviate from market prices
2. **eprints.soton.ac.uk/421405** — "Wisdom of amateur crowds" (ScienceDirect 0377221718306209) — crowd tipster communities vs. professional markets
3. **LSE eprints.lse.ac.uk/103712** — "A Profitable Model For Predicting the Over/Under Market in Football" — direct relevance to our goals/props prediction layer
4. **arXiv:2406.04062** — "Online Learning in Betting Markets: Profit versus Prediction" — online learning framework with implications for sequential RBP optimization
5. **arXiv:2602.19520** (already partially read — the full text is worth a complete read)

---

## Section 8: Synthesis and Judgment

### 8A. What the Research Tells Us That We Didn't Already Know

1. **Sports crowd markets are well-calibrated on average** (Le 2026). This means we should NOT expect large average deviations from Smarkets prices to be systematically profitable. The edge must come from specific structural niches, not from the market being generally wrong.

2. **The calibration, not accuracy, objective is the right one** (Mamlouk 2023). This is independently confirmed. Our optimization target should always be Brier score (or log-score), never classification accuracy.

3. **Crowd overestimates favorites' offensive outputs by ~0.28 XG** (Goal-Line Oracles study). This is a confirmed, published finding that matches our empirical RULE discovery. It is not a fluke. The mechanism is known (anchoring on team quality rather than match-specific defensive context).

4. **In-sample rule discovery has a ~50% false discovery rate** (Harvey et al. 2016). Our named rules discovered from the same JTC data MUST be held to a higher standard than their in-sample performance suggests. RULE2 (9/9 NO in-sample) may have a true edge of only 60% NO out-of-sample.

5. **EPV constraints are binding at n=300** (Riley et al. 2019). We cannot fit more than 7–8 features in a logistic regression without regularization artifacts. This is not a suggestion — it is a hard statistical constraint.

6. **Bayesian hierarchical shrinkage is the theoretically correct approach** but practically complex. Ridge regression (L2 logistic) is a sufficient approximation for now.

7. **Domain-specific calibration** of the Brier decomposition (Merkle et al. 2017) tells us to evaluate separately by prop_family. We should report: which prop families are we most miscalibrated on? That's where to focus the ML.

### 8B. What the Research Does NOT Resolve

1. **Whether 300 settled questions is enough to detect any genuine ML signal.** The honest answer is: probably not for complex models; possibly yes for 2-parameter Platt recalibration. The walk-forward validation will tell us empirically.

2. **The optimal market anchor weighting.** How much should we weight the Smarkets market price vs. our model on questions where both exist? This is an empirically learnable parameter (via our logit_diff coefficient) but requires n > 200 to estimate stably.

3. **Whether our crowd formula (0.514 + 0.61*(us-0.5)) is itself well-calibrated.** This formula was empirically estimated but might need recalibration as we accumulate more data. The Platt recalibration layer on our estimate is effectively updating this formula.

4. **Whether RULE15 (losing-team forwards SOT suppressed) generalizes.** n is too small. Monitor this before encoding it as a feature.

---

## Section 9: Recommended First-Steps Implementation Sequence

This sequence respects the "don't force-fit" principle and respects the data constraints.

### Step 1: Diagnostics (Do This NOW, Week 1)
**Purpose:** Understand current calibration before adding any ML.

1. Compute the 2-parameter Platt recalibration on all 300 settled questions using walk-forward validation:
   - Fit: `logit(outcome) ~ a + b * logit(our_estimate)` on first 150 questions
   - Predict on last 150 questions
   - Record: slope b, intercept a, walk-forward Brier score vs. baseline
   
2. Produce reliability diagrams (calibration curves) stratified by `prop_family`

3. Run the crowd-bias diagnostic: for each prop_family × prop_direction cell with n > 20, compute mean RBP. Flag cells with |mean RBP| > 3 and n > 20.

4. Compute the false discovery corrected version of each named rule's empirical edge: if a rule has been observed n times with k "correct" outcomes, the posterior mean (with Beta(1,1) prior) is (k+1)/(n+2). Compare this to the naive k/n.

**What to do with results:** If Platt scaling slope ≠ 1 significantly (use bootstrap CI), apply it. If a prop_family shows consistently negative RBP on our model-only questions, flag it for conservative treatment.

### Step 2: Platt Scaling Deployment (Week 2)
**Purpose:** Deploy the 2-parameter recalibration as the first ML layer.

1. Retrain on all 300 settled questions with walk-forward LOO
2. Apply recalibrated probabilities as starting point for human review
3. The human can then apply named rule adjustments on top
4. Track whether post-recalibration RBP improves vs. pre-recalibration baseline

### Step 3: Prop-Family Stratification (Week 3, n≈500)
**Purpose:** Learn that different prop types have different calibration needs.

1. Fit separate Platt scaling per `prop_family` with at least 50 obs each
2. Add `has_smarkets_price` as a binary feature (separate intercept for market-anchored vs. model-only)
3. Ridge logistic regression with λ from LOO-CV
4. Report: which prop families benefit most from recalibration?

### Step 4: Full Feature Model (Week 4–5, n≈700)
**Purpose:** Capture context-conditional crowd biases.

1. Add `logit_diff`, `elo_fav_diff`, `prop_direction` as features
2. Add interaction: `prop_direction × prop_family` (this encodes "favorite doing offensive thing" as a feature)
3. Ridge logistic regression; L2 penalty tuned via walk-forward CV
4. SHAP decomposition: verify that the learned coefficients match our theoretical understanding

### Step 5: Hierarchical Bayesian Model (Post-tournament / Future)
**Purpose:** Full probabilistic treatment of rule effects and calibration.

1. Stan/brms model with:
   - Per-rule random effects pooled under common distribution
   - Per-prop-family calibration intercepts
   - Posterior predictive distributions for each question
2. Use posterior uncertainty to set submission ranges (e.g., "model says 0.65 ± 0.12, so clip between 0.55 and 0.75")
3. This is the target architecture for a future competition with more data

### Critical Guardrails Throughout

- **Never submit ML-only without human review.** The human review catches context the ML can't see (e.g., team announced without star player).
- **Flag when the ML model disagrees with our named rules.** Human should investigate and decide.
- **Track every ML prediction vs. submission vs. outcome** to build the audit trail needed to detect if the ML layer is adding or subtracting value.
- **If walk-forward Brier on held-out set is NOT improving over the baseline (rule-adjusted estimate without ML), DO NOT deploy that ML layer.** The null result is also informative: it means our rule system is already near-optimal for our current data.
- **Respect the leakage firewall:** No feature derived from the crowd estimate (which depends on our estimate) in the same model predicting RBP.

---

## Appendix: Outstanding Questions for Human Decision

1. **Which match dates mark the boundary of in-sample rule discovery vs. out-of-sample?** This determines which rules can be treated as validated features vs. hypotheses.

2. **Do we have match-level timestamps for all 300 settled questions?** The walk-forward protocol requires exact chronological ordering.

3. **Can we reconstruct the Smarkets market price for each historical question?** The `logit_diff` feature requires the actual market price, not just whether we used a market.

4. **What is the current best estimate of the crowd formula slope (0.61)?** If this has drifted as the tournament progresses, the crowd_estimate derivation from our_estimate is also drifting.

5. **For RULE15 (losing-team forwards SOT suppressed):** How many observations (all match contexts, not just JTC questions) are in the supporting data? If it's purely JTC data at n < 15, it is NOT ready to encode as a feature.

---

*End of research notes. Document length reflects the complexity of the problem. Implementation should be sequential, conservative, and data-constrained.*
