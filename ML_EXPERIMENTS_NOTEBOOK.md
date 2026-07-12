# ML Experiments Notebook
**Project:** JumpTheCrowd (JTC) — WC2026 Prediction System  
**Started:** 2026-06-22  
**Purpose:** Permanent record of every ML experiment: what was done, why, data used, methodology, exact results, interpretation, and what it means for next steps.

> **Core principle (saved to memory):** *"Your model results are as good as your data."*  
> Every experiment begins with a data audit. No shortcuts.

---

## Table of Contents

1. [Session 0 — Data Audit & Feature Matrix Build](#session-0)
2. [Experiment 1 — Platt Scaling Diagnostic](#experiment-1)
3. [7 Systematic Session 1 — Meeting Notes & Clues for Our Problems](#7systematic)

---

<a name="session-0"></a>
## Session 0 — Data Audit & Feature Matrix Build
**Date:** 2026-06-22  
**Bash log:** `bash_logs/2026-06-22_ml_platt_diagnostic_bash_log.txt`

### Why we did this

Before any ML work, we needed a single flat table of every question we have ever submitted in JTC, with our estimate, the crowd estimate, the outcome, and the RBP score. The raw data lived in ~30 separate per-match JSON files across 5 different schema versions — none of which shared a common format.

Without a unified flat matrix, any model training or diagnostic would require ad-hoc parsing code inside every experiment, making results unreproducible and error-prone.

### Data used

**Input:** All `.json` files in `data/external_markets/` that:
- Have a `post_match_results` block (i.e., the match has been settled)
- Have a JTC submission (excluding `uru_cpv` which had no submission)

**Script:** `ml/build_feature_matrix.py`

### The 5 JSON schemas we handled

Over the tournament, our match data files accumulated 5 different internal structures (schema evolution as we refined the pipeline):

| Schema | Files | Key distinguishing feature |
|--------|-------|---------------------------|
| A/E    | Most recent matches | `post_match_results.question_results` is a dict; keys are Q1_...; outcome may be `outcome_numeric` (int) or `outcome` (str YES/NO) |
| B      | Older matches (BEL-EGY, GER-CUR, etc.) | `post_match_results.questions` is a **list**; items have keys `q`, `us`, `crowd`, `outcome` (int), `rbp` |
| C      | TUR-PAR, USA-AUS | `post_match_results.results` is a dict; items have `our_est`, `crowd`, `outcome` (str YES/NO), `rbp` |
| D      | MEX-KOR | Same as C but `our_est` and `crowd` are absent — must join from `final_submission_estimates` |
| G      | NZL-EGY | `post_match_results.questions` is a **dict** (not a list) — unique to this file |

The script handles all 5 schemas with a single fall-through detection chain.

### Issues encountered and fixed

1. **Schema B list vs. dict confusion** — first draft assumed `question_results` was always a dict; older files use a list under `questions`. Fixed by checking `isinstance`.
2. **YES/NO string outcomes** — schemas C/D/G store outcome as the string `"YES"` or `"NO"` rather than int 0/1. Fixed with `to_int_outcome()` helper.
3. **MEX-KOR missing estimates** — 6/10 questions have no `our_est`/`crowd` in the results dict and their key names in `final_submission_estimates` didn't match. Accepted 4/10 extracted as partial; the 6 missing are genuinely absent.
4. **NZL-EGY dict-not-list** — `questions` block was a dict keyed Q1...Q10. Added schema G handler before the schema B list handler.

### Output: `ml/feature_matrix.csv`

| Stat | Value |
|------|-------|
| Total rows | 264 |
| Rows with settled RBP | **246** |
| Matches covered | 26 (2026-06-11 to 2026-06-22) |
| YES outcomes | 104 (42.3%) |
| NO outcomes | 142 (57.7%) |
| Beat crowd | 178/246 = **72.4%** |
| Mean RBP/question | **+2.497** |
| Std RBP/question | 10.478 |
| Total RBP (sum) | **+614.22** |

**Columns:** `match, date, question_num, question_key, our_estimate, crowd_estimate, outcome, rbp, beat_crowd, has_sub_estimate, schema`

---

<a name="experiment-1"></a>
## Experiment 1 — Platt Scaling Diagnostic
**Date:** 2026-06-22  
**Script:** `ml/platt_diagnostic.py`  
**Results JSON:** `ml/platt_results.json`  
**Bash log:** `bash_logs/2026-06-22_ml_platt_diagnostic_bash_log.txt`

---

### What is Platt scaling and why run it first?

**Platt scaling** is the simplest possible ML correction you can apply to a set of probabilistic forecasts. It fits a 2-parameter logistic regression:

```
logit(P(outcome = YES)) = a + b × logit(our_estimate)
```

where:
- `logit(p) = log(p / (1 - p))` — converts a probability to log-odds
- `a` is the **intercept**: zero means no systematic directional bias; negative means we systematically submit too high; positive means we systematically submit too low
- `b` is the **slope**: 1.0 = perfect calibration; < 1.0 = overconfident (estimates too extreme, should be pulled toward 50%); > 1.0 = underconfident (estimates too compressed, should be pushed away from 50%)

**Why this before any other ML?** Because calibration is the foundation. If our raw estimates are systematically biased (too high, too low, or too extreme), every more complex model will inherit that bias unless we fix it first. Platt scaling answers the question: *are we, in aggregate, well-calibrated or not?*

This is also the cheapest possible diagnostic — it requires zero additional features, just our existing estimates and the outcomes. It gives us a baseline before we add complexity.

**Academic grounding:** Platt (1999) originally proposed this for SVM output calibration. Niculescu-Mizil & Caruana (2005) showed it outperforms isotonic regression at small n. At n=246, Platt is the correct choice (isotonic regression requires much more data to avoid overfitting).

---

### Data used

| Item | Value |
|------|-------|
| Source file | `ml/feature_matrix.csv` |
| Rows used | 246 (those with non-null `rbp`) |
| Date range | 2026-06-11 to 2026-06-22 |
| Questions | Q1–Q10 (or Q6/Q11 as applicable) per match |
| Input feature | `logit(our_estimate)` — single feature |
| Target | `outcome` (0/1) |

Rows without settled RBP (18 rows: questions that were not scored by JTC, e.g. CAN-QAT Q4, the extra SUI-BIH questions) were excluded.

---

### Methodology

**Optimizer:** Newton-Raphson on the logistic log-likelihood (2-parameter). Starting point: `a=0, b=1` (identity, i.e. our raw estimate is already calibrated). Converged in 5 iterations.

**Bootstrap CI:** 1000 resamples (with replacement), same Newton-Raphson fit per resample. 95% CI extracted as 2.5th and 97.5th percentile of bootstrap distribution. Random seed: 42 for reproducibility.

**Walk-forward holdout:**  
- Train: first 60% of questions (n=147), ordered chronologically by date then match
- Test: last 40% (n=99)
- Fit Platt on train, apply to test, compare Brier score vs raw vs crowd

**Reliability diagram:** Questions sorted by `our_estimate`, split into 11 buckets of ~24 questions each. For each bucket: mean predicted probability vs mean actual outcome rate.

**RBP breakdown:** Questions binned by estimate range (LOW 0-30%, MID-LOW 30-50%, MID-HIGH 50-70%, HIGH 70%+). Mean RBP and beat-crowd rate per bin.

---

### Results

#### Analysis 1: Global Platt fit (n=246)

| Parameter | Value | Interpretation |
|-----------|-------|----------------|
| Intercept `a` | **−0.2110** | Slightly negative → we submit too high on average |
| Slope `b` | **+0.5104** | Nominally < 1 → suggests overconfidence |
| Bootstrap 95% CI for `b` | **[+0.1233, +1.2865]** | Wide — includes b=1 |
| b=1 inside CI? | **YES** | No statistically significant miscalibration |
| Bootstrap 95% CI for `a` | **[−0.4627, +0.1261]** | Also includes zero |
| a=0 inside CI? | **YES** | No statistically significant directional bias |

**Brier scores:**

| Source | Brier Score | vs Our Raw |
|--------|-------------|-----------|
| Our raw estimates | 0.2188 | baseline |
| Crowd estimates | 0.2172 | −0.0016 (crowd wins) |
| Platt-recalibrated | 0.2237 | +0.0049 (WORSE) |

The Platt-recalibrated estimates are **worse** than our raw estimates on global Brier score. This is the key red flag: fitting a calibration curve to 246 data points has absorbed noise rather than signal, so the "correction" introduces error.

#### Analysis 2: Walk-forward holdout

| Item | Value |
|------|-------|
| Train set | 147 questions, 2026-06-11 to 2026-06-19 |
| Test set | 99 questions, 2026-06-19 to 2026-06-22 |
| Walk-forward `a` | −0.4129 |
| Walk-forward `b` | **+0.1960** |
| Test Brier (raw) | 0.2144 |
| Test Brier (Platt calib) | 0.2421 |
| Test Brier (crowd) | 0.2162 |
| Platt improvement | **−0.0277 (WORSENS by 0.028)** |

The walk-forward b drifted from 0.51 (global) to **0.196** (train-on-60%). This dramatic instability is a hallmark of small-n overfitting: the Platt parameters are not stable across time splits. When b=0.20 is applied to the test set, it shrinks all estimates aggressively toward 50% regardless of question type, which is worse than using raw estimates.

#### Analysis 3: Reliability diagram (calibration curve)

| Bucket | N | Mean Pred | Mean Outcome | Gap | Flag |
|--------|---|-----------|--------------|-----|------|
| 1 | 24 | 0.163 | 0.167 | +0.004 | ✓ |
| 2 | 24 | 0.249 | 0.167 | **−0.082** | OVER |
| 3 | 24 | 0.329 | 0.333 | +0.005 | ✓ |
| 4 | 24 | 0.381 | 0.417 | +0.036 | ✓ |
| 5 | 24 | 0.408 | 0.333 | **−0.075** | OVER |
| 6 | 24 | 0.441 | 0.375 | **−0.066** | OVER |
| 7 | 24 | 0.485 | 0.500 | +0.015 | ✓ |
| 8 | 24 | 0.555 | 0.583 | +0.028 | ✓ |
| 9 | 24 | 0.613 | 0.542 | **−0.071** | OVER |
| 10 | 24 | 0.738 | 0.708 | −0.030 | ~ |
| 11 | 6 | 0.917 | 0.833 | **−0.083** | OVER |

5 of 11 buckets show overestimation (predicted > actual) by more than 5pp. Overestimation is concentrated in:
- **Bucket 2 (0.25 range):** we say ~25%, actual YES rate is only 17%
- **Buckets 5–6 (0.40–0.44 range):** a cluster just below 50% where we're calling things YES more than warranted
- **Bucket 9 (0.61 range):** at 60%+ confidence, actual rate is only 54%
- **Bucket 11 (0.92 range):** very high confidence estimates (only 6 questions) — actual rate 83% vs predicted 92%

Well-calibrated buckets: 1, 3, 4, 7, 8 (below 50% and near-50% estimates are accurate).

#### Analysis 4: RBP by estimate range

| Range | N | Mean RBP | Beat Crowd |
|-------|---|----------|-----------|
| LOW (0–30%) | 49 | **+3.049** | **84%** |
| MID-LOW (30–50%) | 111 | +2.741 | 68% |
| MID-HIGH (50–70%) | 63 | +3.146 | 73% |
| HIGH (70–100%) | 22 | **+0.652** | 68% |

The HIGH range (70%+) substantially underperforms. Only 22 questions but mean RBP is +0.65 vs +3.0+ elsewhere. This is consistent with:
1. The "favourite-longshot bias" documented in the crowd bias literature: the market already over-prices favorites' offensive output, so when we also assign high probability to a favourite-related question, we're aligned with the crowd and gain little edge
2. Bucket 11 overconfidence: at 90%+ estimates, we're systematically calling things too high

---

### Interpretation in plain English

**1. We are nominally overconfident (b=0.51), but it's not statistically proven at n=246.**

The slope of 0.51 means "if Platt scaling were definitely right, we should shrink our estimates halfway toward 50%." But the 95% confidence interval spans [0.12, 1.29] — impossibly wide. b=1 (perfectly calibrated) is fully inside that range. We cannot yet tell the difference between "we're genuinely overconfident" and "this is just noise in 246 data points."

**2. Applying Platt correction right now would make things worse.**

Both global and walk-forward tests confirm this. The calibration parameters are unstable — the walk-forward b (0.196) is dramatically different from the global b (0.510). When you train on 147 questions and apply to 99, you lose 0.028 Brier points. The correction is chasing noise.

**3. The crowd beats us slightly on absolute calibration (Brier), but we beat them on relative per-question performance (RBP).**

Our Brier: 0.2188. Crowd Brier: 0.2172. The crowd is marginally better calibrated in aggregate. But we beat the crowd on 72.4% of individual questions. These two facts can coexist: RBP measures relative accuracy per question (where small differences in the right direction matter), while Brier measures absolute squared error (where a few badly miscalibrated questions drag the average down). Our edge is in being directionally right more often, not in being perfectly calibrated.

**4. There is a meaningful structural finding: HIGH-confidence estimates (70%+) underperform.**

This is a genuine signal even at n=22. Mean RBP of +0.65 vs +3.0 elsewhere is a stark gap. Combined with bucket 11 showing 8% overestimation at 90%+ range, the pattern is consistent: when we are very confident, the crowd is also confident, the margin over the crowd shrinks, AND we may be slightly overestimating the probability. This is where RULE15 territory (and the favourite-longshot bias literature) becomes relevant.

**5. The intercept a=−0.21 (we submit slightly too high) is borderline.**

This is not statistically significant (CI includes zero), but combined with the reliability diagram pattern, it's worth watching. If the next 100 questions maintain this pattern, the CI will tighten and it may become actionable.

---

### What this means for next steps

| Decision | Rationale |
|----------|-----------|
| **Do NOT apply Platt correction now** | Walk-forward test shows it worsens Brier by 0.028. At n=246, parameters are unstable. |
| **Monitor at n≈350** | If by ~350 questions the b CI no longer includes 1.0, reconsider applying a conservative Platt correction. |
| **Flag HIGH estimates (70%+) for review** | Mean RBP +0.65 is 5× lower than other ranges. When we assign 70%+, scrutinize whether we're adding genuine edge or just being aligned with the market consensus. |
| **Watch the 60–65% bucket** | Bucket 9 shows −7pp overestimation. When we're around 60-65% confidence, actual YES rate is closer to 54%. Consider nudging such estimates down by ~5pp manually until data settles. |
| **Next ML step: prop-family conditional calibration** | At n≈350–400, we can split by question type (e.g. "will X score?", "total goals over/under", "clean sheet") and run separate Platt fits per family. This is where structural signals can separate from global noise. |
| **logit_diff feature is still the right architecture** | Even when adding more features, the key input remains `logit(our_estimate) - logit(crowd_estimate)` to isolate genuine deviation from market. This decouples our signal from the crowd formula collinearity. |

---

### Files created this session

| File | Purpose |
|------|---------|
| `ml/build_feature_matrix.py` | Extracts flat CSV from all 5 JSON schema versions |
| `ml/feature_matrix.csv` | 246-row flat feature matrix (our core ML dataset) |
| `ml/platt_diagnostic.py` | Runs 4-analysis Platt calibration diagnostic |
| `ml/platt_results.json` | Structured results output for programmatic use |
| `data/DATA_XRAY.md` | Full data inventory (written earlier this session) |
| `data/ML_RESEARCH_AGENT_NOTES.md` | 680-line academic literature synthesis |
| `bash_logs/2026-06-22_ml_platt_diagnostic_bash_log.txt` | All commands + full outputs |

---

### Calibration benchmarks to track over time

As the dataset grows, record here:

| Date | N | Platt b | b CI | Platt better? | Crowd Brier | Our Brier | Beat crowd % |
|------|---|---------|------|---------------|-------------|-----------|--------------|
| 2026-06-22 | 246 | 0.510 | [0.12, 1.29] | NO (−0.028 WF) | 0.2172 | 0.2188 | 72.4% |

*Next update: run `platt_diagnostic.py` again when n reaches ~350 (estimate: mid-July 2026 based on remaining WC group stage + knockout pace).*

---

*Notebook maintained by: Claude Code (Sonnet 4.6)*  
*Last updated: 2026-06-22*

---

<a name="7systematic"></a>
## Lessons from a Quant Workshop Session — Applied to Our Problems
**Date recorded:** 2026-06-22

> Several ideas from a quant/data-science workshop on systematic investing methodology speak directly to problems we're navigating right now. Paraphrased and de-identified here; the applicability is what matters, not the source.

---

### Summary: workshop lessons applied to our project

| Problem we had | Lesson |
|-----------------|----------------------|
| Platt b=0.51 — is it real? | Small sample size is the enemy — a CI of [0.12, 1.29] is not enough to act on. Don't apply the correction yet. |
| Should we apply ML correction? | Simple beats complex at small n — added complexity (e.g. a neural net) can add cost/turnover without adding value; a simpler, well-understood model is often more stable. |
| RULE1–RULE15 in-sample bias | Every rule discovered by looking at our own data is, by definition, in-sample (the Harvey et al. 2016 false-discovery problem, see ML_RESEARCH_AGENT_NOTES). No clean fix exists, but three mitigations help: (1) track how many "looks" each rule emerged from and penalize heavily-iterated ones, (2) trust rules with first-principles theoretical backing more than purely data-mined ones, (3) keep a "graveyard" of failed rules — don't discard them, they prevent re-discovering the same dead end and teach their own lesson. Do not feed all 15 rules as raw features into an ML model — that repeats the over-iteration problem instead of solving it.
| What to do with new data (xG, Elo, etc.) | Add each new data element one at a time against an existing baseline model and check whether the test metric (Brier, not AUC/accuracy) improves. Start with something as simple as a t-test before building anything complex. |
| When to apply corrections | Remaining WC2026 matches are the real out-of-sample test — don't contaminate it by re-looking at already-seen data. |
| Monitoring & maintenance | Track cumulative RBP and beat-crowd rate over time, and per-rule performance, to catch model drift early rather than after a large decline. |
| Data quality | Almost no data source discloses its own construction cleanly — missing pieces and inconsistent reporting are normal. The fix is investing once in getting the table-stakes data pipeline right (schema handling, validation) rather than re-litigating it every time. Our multi-schema `build_feature_matrix.py` handling is exactly that investment. |
| Failure tracking | A negative result (e.g., Platt diagnostic showing no improvement) is good information, not a wasted effort — document it once and don't re-run the same failed approach. |

**The single most important takeaway:** write decisions down and hold to the process you defined, rather than re-litigating it under pressure. This notebook is that discipline in practice — every experiment documented, every rule's discovery context tracked, every failure recorded.

---

*Added to notebook: 2026-06-22*

---

---

<a name="critical-losses"></a>
## ⚠ CRITICAL LOSSES — DO NOT REPEAT

> This section exists so we never forget the most costly mistakes. Read before every submission session.

### Loss #1 — BRA-MAR Q8 (2026-06-14): Brazil win submitted at 1.00
**RBP: −51.97. Our worst-ever single result.**
- We had a researched recommendation of 0.58-0.60 (RULE1: avg(Smarkets, crowd)). It was overridden to 1.00 ("gut conviction").
- Brazil drew 1-1. At p=1.00, squared error is always 1.00 when wrong — the worst possible outcome.
- **RULE6 born**: never submit 0% or 100%. Hard cap at 90-95% YES / 5-10% NO.
- The researched number (0.60) would have BEATEN crowd. Our conviction cost us 52 RBP.

### Loss #2 — QAT-SUI Q1 (2026-06-13): Both teams 1+ SOT at HT submitted at 0.20
**RBP: −42.51. Joint second-worst ever.**
- Qatar and Switzerland both had SOT in HT. Our compound independence-product was too extreme.
- **RULE4 born**: for "both teams achieve X" compound questions, weight toward crowd.

### Loss #3 — BRA-HAI Q2 (2026-06-19): Haiti 2+ offsides submitted at 0.10
**RBP: −42.56. Now joint worst individual Q result.**
- Haiti went 3-0 down early and chased desperately → accumulated offsides on counter-attacks.
- The "2+ offsides family = LOW" rule was misapplied to a team in blowout/chasing mode.
- **2+ offsides family REVISED**: does not apply to teams with win prob <5% or teams in chasing mode.

### Loss #4 — ARG-AUT Q9 (2026-06-22): Sabitzer 1+ SOT submitted at 0.18
**RBP: −31.86. We dropped from rank #195 to #234 worldwide.**
- We submitted 0.18 based on RULE15 + GD1 data (Sabitzer 0 SOT in AUT-JOR when Austria was DOMINANT).
- **Critical mistake**: the AUT-JOR data was from a situation where Austria was *winning* 3-1. We incorrectly extrapolated that to a situation where Austria was *losing* 0-1 and chasing.
- Sabitzer, as captain, pushed forward desperately and shot. The desperation context INVERTS the suppression.
- **RULE15 REVISED**: Scenario A (blowout, losing 2+ goals) → suppress SOT. Scenario B (close deficit, trailing 0-1) → DO NOT suppress. Star players get more desperate shots when chasing by a small margin.
- **The lesson that must stick**: GD1 evidence from a DOMINANT match tells you nothing about a player's behavior as a chasing underdog. Opposite context = opposite inference.

### Loss #5 — ARG-AUT Q6 (2026-06-22): 4+ cards submitted at 0.28
**RBP: −19.17. SAME ROOT CAUSE as Loss #4.**
- We submitted 0.28 based on AUT-JOR pattern (dominant win = <4 cards) and general dominant-match model.
- 4+ cards = YES in a 2-0 Argentina win. Austria fought throughout — competitive underdog, not blown out.
- **The unified lesson** (both Q6 and Q9 failed for the same reason): **We assumed a BLOWOUT match script based on AUT-JOR (3-1, Austria dominant). ARG-AUT was a COMPETITIVE 2-0. Austria trailed 1-0, never gave up, fought the whole match. Competitive underdogs generate more cards AND more SOT than blown-out underdogs.**
- The AUT-JOR calibration was the wrong context. Austria managing a comfortable 3-1 win is completely different from Austria chasing Argentina in a 2-0 deficit.
- **New rule addendum**: only apply "dominant match = fewer cards" suppression when expected winning margin is 3+ goals. For 2-goal expected margins (like ARG 73.7% win at λ_total=2.6), the match is competitive enough that the underdog fights → cards stay near base rate (~0.35-0.42).

---

<a name="match-arg-aut-2026-06-22"></a>
## Match Analysis Session — ARG vs AUT (WC2026 Group C, 2026-06-22)
**Date:** 2026-06-22  
**Bash log:** `bash_logs/2026-06-22_ARG-AUT_match_analysis_bash_log.txt`  
**Match file:** `data/external_markets/arg_aut_2026-06-22.json`

### What we did

Pre-match analysis for Argentina vs Austria (WC2026 Group C, Arlington TX). Both teams had played their GD1 matches by this point, giving us crucial empirical data to calibrate our estimates. We ran the full Elo/Poisson/ordered-logit model stack, then incorporated GD1 evidence, then applied the rule framework (RULE7, RULE15, RULE1, RULE14).

### Data used

| Source | Content | File |
|--------|---------|------|
| `elo_current_ratings.csv` | ARG Elo = 2189.5, AUT Elo = 1885.0, diff = 304.5 | `data/processed/` |
| `poisson_goals_coefs.json` | intercept=0.1041, elo_diff_coef=0.001810, neutral venue | `data/processed/` |
| `ordered_logit_coefs.json` | b_elo=0.005199, c1=−0.7702, c2=0.5549 (neutral) | `data/processed/` |
| ARG-ALG result (external) | ARG 3-0 ALG; ARG caught 2+ offsides vs Algeria (high-line confirmed) | Reported by user |
| AUT-JOR result (external) | AUT 3-1 JOR; Sabitzer 0 SOT even as DOMINANT player | Reported by user |

### GD1 Evidence — The key findings

**From Argentina vs Algeria (3-0 ARG):**
- ARG caught 2+ offsides themselves (Q2 of ALG match) → **confirms ARG plays aggressive high defensive line**
- ARG scored 3 goals → strong attacking form heading into AUT match
- No penalty/red card → clean disciplined win

**From Austria vs Jordan (3-1 AUT) — the BOMBSHELL:**
- Q10: Sabitzer 0 SOT (crowd was 57%) **even when Austria WON 3-1 and was the DOMINANT team**
  - This is the single most important data point in this match preparation
  - If Sabitzer doesn't shoot when Austria is winning comfortably, he will get even fewer opportunities as a massive underdog
  - Completely rewrote Q10 estimate from 0.28-0.35 (RULE15 only) down to 0.15-0.22 (RULE15 + personal data)
- Q8: Austria <6 SOT even in 3-1 dominant win (crowd 50%, outcome NO) → SOT model multiplier revised from ×3.7 to ×3.3 for ARG's Q8
- Q7: <4 total cards in Austria's dominant 3-1 win (crowd 44%, NO) → confirms dominant match = fewer cards pattern
- Q6 (AUT-JOR): Jordan had FEWER corners than Austria (crowd 28%, NO) → confirms dominant team always gets more corners → validates our Q4 low estimate
- Q3 (AUT-JOR): Jordan had FEWER 2H SOT than Austria (crowd 27%, NO) → confirms extreme underdogs don't get more 2H SOT → validates our Q2 low estimate

### Model outputs

| Metric | Value |
|--------|-------|
| λ_ARG | 1.9254 goals/match |
| λ_AUT | 0.6395 goals/match |
| λ_total | 2.5650 |
| P(ARG win) | **73.7%** |
| P(Draw) | 17.7% |
| P(AUT win) | 8.7% |
| RULE8? | NO (draw 17.7% < 25% threshold) |
| RULE7? | YES (AUT 8.7% < 15% = extreme underdog) |
| RULE15? | YES (AUT <15%; Sabitzer further confirmed by GD1 data) |

**Also: The ordered logit formula bug discovered and fixed this session:**
Original code incorrectly labeled `p_aut_win = sigmoid(lin - c1)` — this was actually P(ARG win or draw). Correct formula:
- P(ARG win) = sigmoid(lin − c2)  
- P(draw) = sigmoid(lin − c1) − sigmoid(lin − c2)  
- P(AUT win) = 1 − sigmoid(lin − c1)

### FINAL RESULTS — ARG 2-0 AUT

**Match RBP: −42.24 | 5/9 beat crowd | Running total: ~699.76 (was 742.0)**

| Q | Question | Our Est | Crowd | Outcome | RBP | Result |
|---|----------|---------|-------|---------|-----|--------|
| Q1 | Austria 2+ offsides | 0.40 | 0.48 | NO | +9.90 | ✅ Beat crowd |
| Q2 | Austria more 2H SOT | 0.12 | 0.27 | NO | +8.22 | ✅ Beat crowd |
| Q3 | 2H more goals than 1H | 0.44 | 0.51 | NO | +8.29 | ✅ Beat crowd |
| Q4 | Austria more corners | 0.16 | 0.30 | **YES** | **−19.91** | ❌ Lost |
| Q5 | ≤2 total goals | 0.52 | 0.44 | YES | +10.46 | ✅ Beat crowd |
| Q6 | 4+ total cards | 0.28 | 0.45 | **YES** | **−19.17** | ❌ Lost |
| Q7 | ARG 6+ SOT | 0.65 | 0.54 | **NO** | **−9.90** | ❌ Lost |
| Q8 | ARG scores 2H | 0.68 | 0.68 | YES | +1.74 | ✅ Tiny win |
| Q9 | Sabitzer 1+ SOT | 0.18 | 0.43 | **YES** | **−31.86** | ❌ Lost |
| Q10 | Argentina win | *not submitted* | 0.70 | YES | 0 | — missed |

**Total losses: −80.84. Total wins: +38.61. Net: −42.24.**

### What worked

- **Q1, Q2, Q3** — Team-level structural RULE7 props. These were directional bets on Austria's aggregate output (offsides, 2H SOT), not on match script dynamics. They held even in a competitive match.
- **Q5 (≤2 goals)** — Model was right. AUT's defensive shape suppressed total goals. 52.7% was an accurate estimate.
- **Q8 (ARG scores 2H)** — Near-coin-flip win. ARG scored one goal in each half.

### What failed — unified root cause

**Three of four losses came from the same mistake: we calibrated from AUT-JOR (Austria 3-1 dominant) but ARG-AUT was a competitive 2-0 where Austria fought all 90 minutes.**

**Q4 (Austria more corners, −19.91) — the most surprising result:**
Austria had MORE corners than Argentina despite losing 2-0. How? Austria chased from 1-0 down → kept attacking → got repelled by ARG → accumulated corners. Argentina, comfortable at 2-0, sat back and defended. They didn't need to attack. The chasing team was generating corners, not the winning team.
→ **Corner rule revised**: "dominant team gets more corners" only applies in BLOWOUTS (3+ goals) where the dominant team keeps attacking throughout. In managed 2-0 wins, the CHASING team attacks into corners. Austria chasing 0-1 then 1-2 = they accumulated corners.

**Q6 (4+ cards, −19.17):**
Competitive underdog fighting through 90 minutes = more physical play = cards. AUT-JOR <4 cards was because Jordan resigned. Austria never resigned.

**Q9 (Sabitzer, −31.86):**
Same competitive match script. Already fully documented.

**Q7 (ARG 6+ SOT, −9.90) — a different failure:**
Argentina scored 2 goals but had FEWER than 6 shots on target. This is now a confirmed pattern:
- AUT-JOR: Austria scored 3 goals, <6 SOT
- ARG-AUT: Argentina scored 2 goals, <6 SOT
Elite teams in managed wins are CLINICAL. The SOT multiplier (3.3-3.7× lambda) is too high. **Revised: use 2.8-3.0× for elite teams (Elo > 2000) expected to win by 2-goal margin.** Goals-to-SOT conversion rate is higher than the base model assumes for top teams.

**Q10 (Argentina win) — the missed opportunity:**
We never submitted because Smarkets data was pending for RULE1. We had a preliminary 0.73, crowd was 0.70 — a small but real positive edge we never captured. **Lesson: when Smarkets is unavailable and the model number is clear (73.7%), submit the model number rather than miss the question entirely.**

### The three new rules from this match

1. **Corner competition in managed wins**: trailing/chasing team accumulates corners late. Do not automatically give corners to the "dominant" team unless the game is a blowout. Check if the winning team is likely to sit back — if yes, the chasing team may win corners.

2. **SOT multiplier for elite teams**: reduce from 3.3-3.7× to 2.8-3.0× for top teams (Elo > 2000) in matches expected to end 2-0 or 2-1. Elite teams are clinical, not high-volume shooters.

3. **Submit when Smarkets unavailable**: if Smarkets data isn't available and close time is approaching, submit the model estimate rather than miss the question. A preliminary 0.73 beats 0 RBP.

### Final estimates and rationale

| Q | Question | Our Estimate | Exp. Crowd | Edge | Key driver |
|---|----------|-------------|------------|------|------------|
| Q1 | Austria 2+ offsides | **0.40** | ~0.43 | Neutral | ARG high-line confirmed; lambda raised from 1.3 to 1.5 |
| Q2 | Austria more 2H SOT than ARG | **0.12** | ~0.24 | **12pp YES** | RULE7 + AUT-JOR: Jordan (underdog) got fewer 2H SOT |
| Q3 | 2H more goals than 1H | **0.44** | ~0.45 | Neutral | Model: P=42.9%; no rule overrides |
| Q4 | Austria more corners than ARG | **0.16** | ~0.26 | **10pp YES** | RULE7 + AUT-JOR: Jordan got fewer corners |
| Q5 | Argentina win | **0.73** | ~0.68 | +5pp | RULE1 (Smarkets pending); model 73.7% |
| Q6 | ≤2 total goals | **0.52** | ~0.45 | **+7pp** | Model 52.7%; crowd under-prices defensive AUT |
| Q7 | 4+ total cards | **0.28** | ~0.38 | **10pp** | Dominant match = <4 cards (AUT-JOR confirmed) |
| Q8 | ARG 6+ SOT | **0.65** | ~0.74 | **9pp NO** | AUT-JOR warning: dominant teams can fall <6 SOT; revised multiplier |
| Q9 | ARG scores 2H | **0.68** | ~0.64 | +4pp | lambda=1.059; dominant favorites score in 2H pattern |
| Q10 | Sabitzer 1+ SOT | **0.18** | ~0.38 | **20pp NO** | **BEST EDGE**: 0 SOT even as dominant player (GD1); RULE7 + RULE15 |

### Rules applied

- **RULE7** (extreme underdog): AUT at 8.7% win probability → submit unshaded model estimates for all AUT-positive props (Q1, Q2, Q4, Q10). Do not allow crowd compression to pull estimates toward 50%.
- **RULE15** (losing-team forward SOT suppressed): AUT <15% → range 0.25-0.35 regardless of model. Revised further down by Sabitzer GD1 data to 0.15-0.22.
- **RULE1** (match winner): avg(crowd, Smarkets market). Smarkets pull required but not yet completed (10k quota constraint — must ask user permission). Preliminary: 0.73.
- **RULE8** does NOT fire: draw 17.7% < 25% threshold. No general shrinkage.
- **RULE14** (consistency): P(ARG 6+ SOT) = 0.65 ≥ P(ARG scores 2H) = 0.68 roughly consistent (SOT ≥ goals, though exact threshold different).

### What we still need before submission

1. **Smarkets data for Q5** — need user permission for QK API call (10k daily quota). Without it, Q5 stays at preliminary 0.73.
2. **Lineup confirmation** — especially Sabitzer starter vs sub status. If Sabitzer is NOT starting, Q10 estimate drops further toward 0.10-0.12.

### Key learning from this session

The most important methodological innovation was the **GD1 calibration loop**: using the same tournament's first match results to calibrate estimates for subsequent matches. Sabitzer's 0-SOT data in a dominant win is exactly the kind of player-level signal that Poisson models cannot capture but human scouts can. This will be a repeatable process for all remaining GD2 and GD3 matches.

---

*Added to notebook: 2026-06-22*

---

<a name="fra-irq-analysis"></a>
## Match Analysis Session — France vs Iraq (WC2026 Group D, Philadelphia, 2026-06-22)
**Bash log:** `bash_logs/2026-06-22_FRA-IRQ_match_analysis_bash_log.txt`
**JSON file:** `data/external_markets/fra_irq_2026-06-22.json`
**Context:** Recovery session. ARG-AUT ended -42.24 RBP (rank dropped #195→#234). FRA-IRQ is the immediate recovery opportunity.

---

### Why this session matters

ARG-AUT taught us three new rules (corner reversal in managed wins, SOT multiplier for elite teams, never miss a question). FRA-IRQ is a chance to apply all of them — and to get the GD1 calibration right, which we partially missed in ARG-AUT.

Key improvement this session: **spawned a deep research agent** to pull actual GD1 stats (France vs Senegal, Iraq vs Norway) and live market data before finalizing estimates. This replaced the "UNKNOWN — need user input" placeholders from our preliminary pass.

---

### Model outputs (Poisson + ordered logit)

| Parameter | Value |
|-----------|-------|
| FRA Elo | 2129.0524 |
| IRQ Elo | 1736.5496 |
| Elo diff | 392.5 (larger than ARG-AUT's 304.5 — Iraq even bigger underdog) |
| λ_FRA | 2.258 |
| λ_IRQ | 0.545 |
| P(FRA win) | 81.5% |
| P(Draw) | 12.8% |
| P(IRQ win) | 5.7% |

**RULE7 fires** (IRQ 5.7% < 15%). **RULE8 does NOT fire** (draw 12.8% < 25%).

---

### GD1 calibration data — confirmed by research agent

**France 3-1 Senegal (June 16, New York/New Jersey)**
- HT: 0-0. ALL 3 France goals came after the 66th minute.
- France 1H stats: **1 shot, 0 SOT, 3 corners, 0.02 xG**
- France full match: 11 shots, 8 SOT, 6 corners, 8 fouls, 1.79 xG
- Mbappe 1H: only 14 touches. Career WC record: **1 first-half goal vs 12 second-half goals**
- Cards: 0 (referee Faghani; very clean match)
- **Key takeaway: France are a dramatically slow-starting team. Deschamps' system builds gradually.**

**Iraq 1-4 Norway (June 16, Boston/Gillette)**
- HT: 1-2 (Iraq scored in 39' via counter; Norway scored 29', 43')
- Iraq full match: ~10 shots, **1 SOT in 90 minutes**, 12 fouls
- **Iraq had ZERO shots after the 63rd minute**
- Iraq's only goal: 39th-minute header (first half)
- Cards: Tahseen YC in 86th minute (serious foul — second half)
- **Key takeaway: Iraq's attacking output is essentially zero after the first hour. They collapse offensively under sustained pressure.**

---

### External market and referee data

| Source | Data |
|--------|------|
| Betfair | France win: 1/14 (~93.3% implied) |
| bet365 | France win: -1200 to -1500 (~92-94% implied) |
| Opta supercomputer | FRA 88.5%, Draw 8.5%, IRQ 3% |
| BTTS Yes | +140-180 (~36-42% implied) |
| BTTS No | -200 to -215 (market favourite) |
| Over 3.5 goals | -122 (favored) |
| Total corners Over 7.5 | -315 (near certainty) |

**Referee: Drew Fischer (Canada)**
- Career YC/game: 3.35 | WC2026 YC/game: 3.6
- WC2026 tournament average: 2.17
- Fischer is significantly above average — directly boosts Q3 (Iraq 1+ card in 2H)

**Key player risk: Zaid Ismael (Iraq)** — 3 cards in 7 caps, 10 bookings in 30 club appearances. Racing Post tipped him at 2/1 to be carded.

**Weather risk:** Philadelphia flood watch, 65% storm probability at kickoff (5pm ET). FIFA halts play if lightning within 8 miles. ALL counting stats (SOT, corners, cards, fouls) at risk of disruption.

---

### GD1 calibration — what changed from preliminary estimates

| Q | Preliminary | Final | Δ | Key driver |
|---|-------------|-------|---|------------|
| Q1 Iraq HT corners | 0.08 | **0.07** | −0.01 | France had 3 HT corners vs Senegal; Iraq 3 total vs Spain in 90' |
| Q2 France more fouls | 0.55 | **0.45** | −0.10 | Iraq fouls 10-12 when defending deep (Norway, Spain); France ~8-10 as attacker |
| Q3 Iraq 1+ card 2H | 0.50 | **0.65** | +0.15 | Fischer 3.35 YC/game + Ismael card-prone + Iraq GOT a 2H card in GD1 (86') |
| Q4 BTTS AND 3+ goals | 0.24 | **0.28** | +0.04 | BTTS market 36-42%; France no clean sheet in 6; Iraq scored in GD1 |
| Q5 Iraq 2+ SOT in 2H | 0.22 | **0.15** | −0.07 | Iraq 1 SOT in 90' vs Norway; 0 shots after 63'; France better defensively |
| Q6 France win | 0.81 | **0.88** | +0.07 | Market 92-94%, Opta 88.5%; post-GD1 update; Elo model was conservative |
| Q7 Iraq scores in 2H | 0.26 | **0.18** | −0.08 | Both Iraq GD1 goals came in 1H (39'); 0 shots after 63' vs Norway |
| Q8 Iraq 4+ SOT | 0.14 | **0.08** | −0.06 | Iraq 1 SOT total in 90' vs Norway; France better defensively than Norway |
| Q9 France scores 1H | 0.70 | **0.60** | −0.10 | France 0 SOT in 1H vs Senegal; all 3 goals after 66'; Mbappe 1H WC record |

---

### Final submission estimates

| Q | Question | Estimate | Tier | Rationale |
|---|----------|----------|------|-----------|
| Q1 | Iraq more HT corners | **0.07** | TIER 1 EXTREME NO | Model 5.7%, RULE7, France dominates corners from whistle |
| Q2 | France more fouls | **0.45** | TIER 3 slight NO | Iraq fouls more when defending deep; near coin-flip |
| Q3 | Iraq 1+ card in 2H | **0.65** | TIER 2 YES lean | Fischer + Ismael + Iraq's own GD1 2H card (86') |
| Q4 | BTTS AND 3+ goals | **0.28** | TIER 3 slight YES | Market BTTS 36-42%; France no clean sheet streak |
| Q5 | Iraq 2+ SOT in 2H | **0.15** | TIER 1 EXTREME NO | Iraq 1 SOT in 90' vs Norway; 0 shots after 63' |
| Q6 | France win | **0.88** | TIER 1 push high | Market 92-93%; Opta 88.5%; GD1 results confirm gap |
| Q7 | Iraq scores in 2H | **0.18** | TIER 2 NO lean | All Iraq goals in 1H; 0 shots after 63' vs Norway |
| Q8 | Iraq 4+ SOT | **0.08** | TIER 1 EXTREME NO | **HIGHEST CONFIDENCE in batch.** Iraq 1 SOT/90' vs weaker team |
| Q9 | France scores 1H | **0.60** | TIER 2 moderate YES | France 0 SOT in 1H vs Senegal; GD1 slow start; Iraq weak |

---

### ARG-AUT lessons applied correctly this time

**Match script:** FRA-IRQ is expected to be a BLOWOUT (Elo diff 392.5 >> 2-goal expected margin). Applying blowout script throughout:
- Iraq gives up early → fewer Iraq SOT (Q5, Q8) — confirmed by GD1 data
- Corners go to France from first whistle (Q1 at HT not subject to "chasing team" reversal)
- Cards: Iraq tires and fouls late under Fischer → yes, 2H card likely (Q3)

**Q9 (France 1H goal) — new insight from GD1:** France's own slow-start pattern (0.02 xG in 1H vs Senegal) is a repeatable Deschamps system trait. Pre-tournament form (scored 1H in last 3 wins) was less relevant than actual tournament data. **Lesson: GD1 always beats pre-tournament form for calibration.**

**Q6 (France win) — Elo model underestimated:** Our Elo model gave 81.5%. Sharp markets were at 90-93%. Post-GD1 the gap widened further. **Lesson: For massive mismatches, supplement Elo with sharp market consensus as markets price in current form, lineup, morale, etc.**

---

### Key methodological upgrade: research agent for alt data

This session introduced **deep research agent spawning** as standard pre-match procedure. The agent found:
1. Confirmed GD1 results with halftime split stats (critical for Q9)
2. Live market implied probabilities (critical for Q6)
3. Referee card rate data (critical for Q3)
4. Specific player disciplinary risk profiles (Ismael, critical for Q3)
5. Weather risk flag (affects all counting stats on day of match)

**This is now part of standard pre-match workflow.** Every match analysis going forward should include a research agent pull before finalizing estimates.

---

*Added to notebook: 2026-06-22*

---

<a name="nor-sen-analysis"></a>
## Match Analysis Session — Norway vs Senegal (WC2026 Group D, Philadelphia, 2026-06-22)
**Bash log:** `bash_logs/2026-06-22_NOR-SEN_match_analysis_bash_log.txt`
**JSON file:** `data/external_markets/nor_sen_2026-06-22.json`
**Context:** Analyzed same day as France vs Iraq (simultaneous matches). Recovery session continues. Expanded data boundary: added individual player profiles (Haaland, Mané), market depth ($3.6M Polymarket liquidity), referee card/penalty stats, corner market lines, and head-to-head history.

---

### Why this match is different from France vs Iraq

FRA-IRQ was a blowout template. NOR-SEN is a **genuinely competitive match** with RULE8 firing (Draw 30.4%). The key non-Elo input here is group dynamics: Senegal at 0pts after GD1 MUST get points — their attacking intensity is well above what the Elo model predicts.

This match also introduces the first **Mané individual scorer question** (Q10), requiring a full player profile alongside team-level analysis.

---

### Model outputs

| Parameter | Value |
|-----------|-------|
| NOR Elo | 1983.8 |
| SEN Elo | 1912.8 |
| Elo diff | +71.0 (Norway slight advantage) |
| P(NOR win) | **45.4%** |
| P(Draw) | **30.4%** ← RULE8 fires |
| P(SEN win) | **24.2%** |
| λ_NOR | 1.262 |
| λ_SEN | 0.976 |

**RULE7:** Does NOT fire (both teams > 15%). **RULE8: FIRES** → shrink all extreme/attacking props ~5-8pp toward 50%.

---

### GD1 calibration data

**Norway 4-1 Iraq (June 16):**
- Haaland: 4 SOT, 5 shots, 2 goals in 1H (29', 43'), played full match
- Norway: 12 shots, **5 total SOT**, 13 fouls, 61% possession
- **No penalties or red cards**
- Norway plays **4-3-3 high press with high defensive line** — creates offside traps
- 2H: Norway scored twice more but largely managed the game (Iraq only 2 shots in 2H)

**France 3-1 Senegal (June 16):**
- Senegal: 6 shots, **1 SOT total**, 5 fouls, 4 corners (0.53 xG)
- **Senegal had only 1 total shot in the entire 2nd half**
- **Jackson (SEN) caught offside 3+ times in a single match** (confirmed: disallowed goal + other runs)
- Mané: started, played full match, **0 goals, 1 shot on target** (40')
- **No penalties or red cards** in this match either

---

### External data — new data types captured this session

| Data Type | Source | Key Value |
|-----------|--------|-----------|
| Sharp market odds | Polymarket ($3.6M liquidity) | NOR 43%, Draw 21%, SEN 28% |
| Betting moneyline | ESPN/bet365 | NOR +125-135 (~43-44%), Draw +220-240 |
| BTTS market | Multiple | 54% implied YES |
| Player scorer market | ESPN | Mané +310 (~24%), Haaland ~-150 |
| Corners market line | Robinhood/Kalshi | 9-10 total |
| Referee discipline rate | StatsBet/corner-stats | Elfath 3.84 YC/game career, **0.27 penalties/game** |
| Individual player stats | DraftKings Network | Haaland GD1: 4 SOT in 90' |
| Player career WC record | FIFA | Mané: 1 WC goal in 4 career WC matches |

---

### Referee: Ismail Elfath (USA)
- Career YC/game: **3.84** | 2025/26: 3.73
- Career penalty rate: **0.27/match** (~1 in 4 games)
- 2025/26 season penalty rate: **0.18/match** (below his own career rate)
- WC2022 experience: awarded penalty vs Portugal-Ghana
- Group D GD1 pattern: **ZERO penalties in two matches** (France-Senegal, Norway-Iraq)
- Assessment: Moderate card-giver, not pocket-happy. His below-average penalty rate this season + group trend = suppress Q3 (penalty OR red card)

---

### Mané deep profile (new data type — individual player analysis)

| Metric | Value |
|--------|-------|
| Age | 34 (Al-Nassr) |
| Career international goals | 55 in 129 caps (0.43/cap) |
| WC career goals | **1 in 4 matches** (vs Japan, 2018) |
| GD1 (vs France) | 0 goals, 1 SOT, played 90' |
| Anytime scorer market | +310 (~24% implied) |
| Foul drawing rate | 3+ fouls drawn in 6 of 7 recent competitive starts |
| Role | Left winger who cuts inside — NOT a pure box striker |
| Context | This is his redemption WC (missed 2022 entirely with injury) |

**Key insight:** Mané's career goals rate (0.43/cap) is misleading for WC specifically (0.25/WC game). He's a creator as much as a finisher. Jackson is the primary box target. Align with market at 0.24 rather than the model's 28.9%.

---

### Final estimates vs preliminary model

| Q | Question | Model | Preliminary | Final | Key driver for change |
|---|----------|-------|-------------|-------|-----------------------|
| Q1 | Senegal 2+ offsides | 53.7% | 0.52-0.58 | **0.78** | Jackson 3+ in GD1; Norway high line identical to France's |
| Q2 | NOR more 2H goals | 34.4% | 0.38-0.42 | **0.45** | Senegal 1-shot 2H vs France; NOR scored 2 in 2H vs Iraq |
| Q3 | Penalty OR red card | ~38% | 0.40-0.46 | **0.38** | Zero in 2 GD1 matches; Elfath below career rate |
| Q4 | Senegal more fouls | 50.0% | 0.48-0.52 | **0.48** | SEN only 5 fouls in GD1; coin flip |
| Q5 | 4+ total 2H SOT | 50.4% | 0.48-0.52 | **0.55** | Competitive open game; SEN must-attack in 2H |
| Q6 | Norway win | 45.4% | 0.48-0.52 | **0.45** | Market 43-44%; Polymarket $3.6M at 43% |
| Q7 | HT tied | 46.2% | 0.42-0.46 | **0.42** | Norway scored 29' and 43' in GD1 — early scorers |
| Q8 | 9+ total corners | 13.5%* | 0.28-0.35 | **0.50** | FRA-SEN had 10 corners; combined avg 10-11; market at line |
| Q9 | NOR 6+ SOT | 18.2% | 0.30-0.40 | **0.38** | Norway only 5 SOT vs weaker Iraq; 6+ vs Koulibaly harder |
| Q10 | Mané scores | 28.9% | 0.26-0.32 | **0.24** | Market +310; 1 WC goal in 4 career matches |

*Q8 model used too-low corner multiplier (2.6×). Revised to 3.3× = 34.4%. Team averages and GD1 data push to 50%.

---

### Key lessons from this session

**1. Corner model needs multiplier calibration for competitive matches.**
The 2.6× multiplier produced only 13.5% for 9+ corners. France-Senegal GD1 had 10 total corners. Combined team averages (NOR 5.6 + SEN 6.1) project 10-11 expected. Future: use 3.0-3.5× for competitive matches between mid-to-upper tier teams, not 2.6×.

**2. GD1 offside data is a powerful signal for "2+ offsides" questions.**
Jackson's 3+ offsides in a single GD1 match (against a high defensive line) gives us near-certainty for Q1. This type of individual behavioral pattern from GD1 is exactly what the model can't capture. The GD1 calibration loop is paying off.

**3. Individual player WC records matter separately from career records.**
Mané has 55 international goals (0.43/cap) but only 1 WC goal in 4 WC appearances. His WC underperformance vs career average is meaningful data. Always distinguish career record from WC-specific record for tournament questions.

**4. Sharp prediction market depth is a calibration signal.**
Polymarket with $3.6M traded on this match is a genuinely sharp market. Its NOR 43% estimate is meaningfully more informed than our Elo model (45.4%). For match winner questions, high-liquidity prediction markets should be weighted equally with or above internal models.

**5. Group dynamics (must-win situations) are primary non-Elo inputs.**
Senegal's 0-point, must-win situation elevates their attacking intensity beyond what Elo captures. This was the single most important contextual factor in the whole analysis, driving Q1 (offsides), Q5 (2H SOT), and framing the Q10 (Mané motivation). Always check group standings before finalizing attacking-prop estimates for mid-tournament matches.

---

### Post-Match Results — Norway 3-2 Senegal

**Final score:** Norway 3-2 Senegal (Norway WIN)  
**Total RBP:** +36.49  
**Beat crowd:** 6/10  

| Q | Outcome | Us | Crowd | RBP | vs Crowd |
|---|---------|-----|-------|-----|---------|
| Q1 | YES | 0.78 | 0.50 | **+22.07** | BEAT |
| Q2 | NO | 0.45 | 0.45 | +2.63 | beat |
| Q3 | NO | 0.38 | 0.39 | +2.91 | beat |
| Q4 | NO | 0.48 | 0.55 | **+8.46** | beat |
| Q5 | YES | 0.55 | 0.64 | -5.30 | below |
| Q6 | YES | 0.45 | 0.49 | -1.24 | below |
| Q7 | NO | 0.42 | 0.44 | +3.29 | beat |
| Q8 | YES | 0.50 | 0.53 | -0.37 | below |
| Q9 | YES | 0.38 | 0.42 | -1.58 | below |
| Q10 | NO | 0.24 | 0.30 | **+5.63** | beat |

**Key wins:**
- **Q1 +22.07**: Jackson's 3+ GD1 offsides + Norway high line = near-certainty. Best single-question call of the day. The 0.78 vs 0.50 crowd gap is exactly the kind of structural edge we're building toward.
- **Q4 +8.46**: Norway fouls more — recognized from GD1 foul counts (NOR 13 vs SEN 5). Crowd at 55% thought Senegal fouled more (wrong).
- **Q10 +5.63**: WC-specific record (1 goal in 4 WC matches) correctly separated from career average (0.43/cap). Mané scored 0 despite Senegal scoring 2.

**Key misses:**
- **Q5 -5.30**: We said 55%, crowd said 64%, outcome YES. In a 3-2 match both teams generated lots of 2H shots — we should have pushed harder on YES.
- **Q9 -1.58**: Norway 6+ SOT in a 3-2 competitive match is natural — our GD1 ceiling (5 SOT vs weak Iraq) was too conservative an anchor. In competitive open games, Norway can exceed their GD1 output.

**Rules validated:**
- GD1 offside behavioral data is near-deterministic when tactical context replicates — **VALIDATED STRONGLY** (Q1 +22.07).
- Foul rate data (footystats recent 10) predicts "who fouls more" better than the model — **VALIDATED** (Q4 +8.46).
- WC-specific scoring record vs career average for established internationals — **VALIDATED** (Q10 +5.63).

---

## Match Analysis Session — Jordan vs Algeria

**Date:** 2026-06-22  
**Match:** Jordan vs Algeria (WC2026 Group J, GD2)  
**Venue:** Levi's Stadium, Santa Clara, CA  
**SportsPredict ID:** 5398e565-2759-4c71-abea-77f209bd75f9  
**Data files:** `sportspredict_research/data/external_markets/jor_alg_2026-06-22.json`  
**Bash log:** `sportspredict_research/bash_logs/2026-06-22_JOR-ALG_match_analysis_bash_log.txt`  
**Session type:** Full analysis — ordered logit + Poisson model + research agent (deep search) + GD1 calibration

---

### Context

Third match of a triple-header day. Both Jordan (lost 1-3 to Austria) and Algeria (lost 0-3 to Argentina) come in at 0 points — SURVIVAL MATCH for both. GD3 for both teams is extremely difficult (Jordan vs Argentina; Algeria vs Austria), making this effectively a must-win for both sides. This survival-match dynamic is the defining contextual feature — both teams must attack.

**Group J standings after GD1:**
- Argentina 3pts, Austria 3pts, Jordan 0pts (-2 GD), Algeria 0pts (-3 GD)
- Jordan GD3: vs Argentina. Algeria GD3: vs Austria. Both effectively eliminated if they lose here.

**CRITICAL TEAM NEWS:**
- **Mohamed Amoura OUT** (hamstring). Algeria's top WC qualifier scorer (10 goals). Replaced by Amine Gouiri (Marseille).
- **Riyad Mahrez EXPECTED TO START** (was benched vs Argentina — tactical adjustment for weaker opposition).

---

### Model Outputs

**Ordered logit (neutral venue):**
- Algeria win: 48.9%, Draw: 29.4%, Jordan win: 21.7%
- RULE7: Does NOT fire (both teams above 15%)
- RULE8: FIRES — draw 29.4% ≥ 25% threshold

**Market-implied:**
- Algeria win: 62-65% (significantly above model 48.9%)
- Draw: 19-22%, Jordan win: 14-17%
- Notable gap: market has drastically revised Algeria upward post-GD1 context

**Poisson goals:**
- λ_ALG = 1.3258, λ_JOR = 0.9289, λ_total = 2.2546
- P(ALG scores) = 73.4%, P(JOR scores) = 60.5%
- P(total ≥ 3) = 39.2%, P(HT tie) = 45.9%

---

### GD1 Evidence (Critical)

| Team | Match | Shots | SOT | Fouls | Offsides | Notes |
|------|-------|-------|-----|-------|----------|-------|
| Algeria | vs Argentina | 7 | **0** | 8 | 1 | Historic — zero SOT in 90 minutes |
| Jordan | vs Austria | 11 | **4** | ~10 | unknown | 1st-ever WC goal (Olwan 50') |

**Algeria GD1 context:** Mahrez benched, Amoura absent from squad, vs far superior Argentina. Mahrez came on 64' for 26 min, had 1 shot, 0 SOT. Zero SOT is a historic low but vs the tournament's eventual favorite.

**Jordan GD1 context:** 11 shots, 4 SOT — impressive attacking output for a losing team. Conceded a penalty (VAR handball, 90+12'). Al-Taamari confirmed ≥1 SOT in 87 minutes.

**KEY GD1 DISCOVERY:** Jordan conceded a penalty in GD1. Jordan won/conceded 8 total penalties in last 10 matches (5 won, 3 conceded). Extreme penalty-involvement rate.

---

### Key Data Points from Deep Research

**Team foul rates (footystats recent 10 matches):**
- Algeria: **14.78 fouls/game** — one of the highest in the tournament
- Jordan: **10.44 fouls/game**
- Gap: Algeria fouls 41% more per match than Jordan
- **This is the decisive data point for Q1 (Jordan more fouls).**

**Referee: Slavko Vincic (Slovenia)**
- Career YC/game: 4.13 | WC: 3.33 (notably lower — more restrained at WC)
- Career penalties/game: 0.27
- Style: Balanced, serene, lets game flow. VAR user.
- WC experience: 2022 (Argentina-Saudi, England-Wales)

**Player profiles:**
- **Mahrez**: 35yo, Al-Ahli. 0.41 SOT/game, 0.29 goals/game at club. Rarely plays full 90. Expected to start, likely subbed ~65-70'.
- **Al-Taamari**: 29yo, Rennes. **0.76 SOT/game** — highest individual club SOT rate seen in this analysis series. GD1 confirmed SOT.

**External markets:**
- Over 2.5 goals: -104 to -110 (~51-52% YES) — essentially 50/50
- BTTS Yes: ~50-51% (BTTS No slightly favored at -124 to -132)
- Mahrez anytime scorer: +160 (~38%), Al-Taamari: +350 (~22%)

---

### Analysis and Final Estimates

| Q | Question | Model P | Preliminary | Final | Key driver |
|---|----------|---------|------------|-------|------------|
| Q1 | Jordan more fouls than Algeria | 50.0% | 0.50-0.55 | **0.32** | Algeria 14.78/game vs Jordan 10.44/game — they foul 41% more |
| Q2 | 4+ total SOT in 2H | 51.0% | 0.50-0.55 | **0.50** | Jordan 4 GD1 SOT vs Algeria 0 GD1 SOT — genuine coin flip |
| Q3 | Jordan first AND Algeria 2H goal | 19.1% | 0.18-0.22 | **0.18** | Compound; JOR first-goal ~28-30% × ALG 2H ~70% |
| Q4 | Algeria 2+ offsides | 53.7% | 0.48-0.53 | **0.44** | Algeria only 1 GD1 offside; Amoura (channel runner) OUT |
| Q5 | Penalty OR red card | ~38% | 0.42-0.50 | **0.45** | Jordan 8 penalty involvements in last 10 matches |
| Q6 | Mahrez 1+ SOT in 2H | 56.5% | 0.48-0.58 | **0.42** | 2H-specific; Mahrez sub risk 65-70'; Algeria 0 GD1 SOT |
| Q7 | Jordan scores 1+ goal | 60.5% | 0.55-0.62 | **0.57** | Jordan 90% scoring rate; 4 GD1 SOT; market win-to-nil at +140 |
| Q8 | HT tied | 45.9% | 0.42-0.48 | **0.44** | Model 45.9%, market 43%; Algeria attack limited 1H without Amoura |
| Q9 | 3+ total goals | 39.2% | 0.38-0.44 | **0.48** | Market 51-52%; RULE8 + GD1 pattern + Jordan over-2.5 5/6 |
| Q10 | Al-Taamari 1+ SOT | 59.0% | 0.55-0.62 | **0.58** | 0.76 SOT/game at Rennes; GD1 confirmed; Jordan's primary weapon |

**Edge ranking (largest deviation from expected crowd 50%):**
1. Q1 0.32 — STRONGEST: Algeria fouls 41% more, crowd at ~50% doesn't know this
2. Q10 0.58 — Club rate 0.76 SOT/game; GD1 confirmed; designated counter weapon
3. Q6 0.42 — Model 56.5% too high; 2H-specific condition + sub risk
4. Q4 0.44 — Algeria controlled, 1 GD1 offside; Amoura (the runner) is out
5. Q5 0.45 — Jordan's extreme penalty involvement rate
6. Q7 0.57 — Jordan's 90% recent scoring rate + GD1 attacking output
7. Q9 0.48 — RULE8 + market + GD1 pattern
8. Q8 0.44 — HT context; most likely single score is 0-0
9. Q2 0.50 — Genuine coin flip; both GD1 evidence pulls in opposite directions
10. Q3 0.18 — Low compound probability; Jordan's low first-goal probability is binding constraint

---

### New Lessons from This Session

**1. Foul rate data from recent 10 matches (footystats) is a decisive Q-input for "which team fouls more" questions.**
Algeria's 14.78 fouls/game vs Jordan's 10.44 fouls/game made Q1 a slam-dunk NO. Our model produced 50% (coin flip) from Poisson. The actual foul data produced 0.32. This gap is the edge. Always pull footystats foul/game data before finalizing "X more fouls than Y" questions — the model has no basis for asymmetric fouls.

**2. Zero-SOT GD1 performance is a signal but not determinative — context matters.**
Algeria had 0 SOT in GD1 vs Argentina. But: Mahrez benched, Amoura absent, vs the tournament's strongest team. We cannot treat 0-SOT vs Argentina as a prediction for performance vs Jordan. Discount the GD1 signal by opponent quality and lineup. However, we did revise Mahrez's 2H SOT probability down (from 56.5% to 42%) — correct to take some signal but not the full signal.

**3. "Sub risk" is a genuine individual player prop risk factor, especially for older players.**
Mahrez (35yo) rarely plays full 90 minutes. Q6 asked specifically about 2H SOT. If he's subbed off at 65-70', the 2H condition fails even if he played brilliantly in the 1H. For questions about specific time-window player performance, always check the player's average minutes and sub pattern.

**4. "Both teams must attack" and "cautious draw-heavy match" are opposite dynamics — RULE8 needs context.**
RULE8 fires whenever draw ≥ 25%, and generally shrinks attacking props toward 50%. But in survival matches where BOTH teams need a win, the game is paradoxically open and attacking. Today's JOR-ALG match has 29.4% draw probability from the model but neither team can afford to play for a draw. RULE8 should be applied cautiously in survival-match situations — its logic applies to neutral "draw is acceptable" contexts, not to mutual-must-win scenarios.

**5. Jordan's penalty involvement rate (8 in 10 matches) is a team characteristic, not a fluke.**
Winning 5 penalties AND conceding 3 penalties in the same 10-match window is unusual. This reflects Jordan's style: they go to ground, win contact situations, but also commit cynical fouls when defending. For any match involving Jordan, penalty probability should be elevated above the referee's base rate.

**6. Survival match = elevated foul/card intensity in 2H, not 1H.**
Both teams playing for survival will be cautious early (neither wants to concede first) and more desperate later. Cards, penalties, and reckless tackles accumulate in the 60-90' window. For Q5 (penalty OR red card), the survival match context elevates 2H probability specifically.

---

### Post-Match Results — Jordan 1-2 Algeria

**Final score:** Jordan 1-2 Algeria (Algeria comeback win)  
**Total RBP:** -5.60  
**Beat crowd:** 6/10  

**Derived match narrative (reconstructed from question outcomes):**
- Jordan scored first → led 1-0 at HT (Q3 YES + Q8 NO proves Jordan led at HT, not tied)
- Algeria scored twice in 2H to win (Q9 exactly 3 goals: 1+2=3)
- Jordan defended their lead for 60-70+ minutes → accumulated fouls defending (Q1 YES)
- Al-Taamari registered at least 1 SOT (Q10 YES) — Jordan's weapon delivered
- Mahrez did not register a 2H SOT (Q6 NO) despite expectations he would start
- No penalty, no red card (Q5 NO)
- Algeria had <2 offsides (Q4 NO) — controlled possession as predicted

| Q | Outcome | Us | Crowd | RBP | vs Crowd |
|---|---------|-----|-------|-----|---------|
| Q1 | YES | 0.32 | 0.54 | **-23.23** | BELOW |
| Q2 | YES | 0.50 | 0.60 | -6.60 | below |
| Q3 | YES | 0.18 | 0.23 | -6.03 | below |
| Q4 | NO | 0.44 | 0.51 | **+8.98** | beat |
| Q5 | NO | 0.45 | 0.38 | -3.20 | below |
| Q6 | NO | 0.42 | 0.43 | +3.59 | beat |
| Q7 | YES | 0.57 | 0.52 | **+6.40** | beat |
| Q8 | NO | 0.44 | 0.42 | +0.01 | beat |
| Q9 | YES | 0.48 | 0.48 | +1.38 | beat |
| Q10 | YES | 0.58 | 0.47 | **+13.11** | beat |

---

### Critical Post-Match Analysis — The Q1 Catastrophe

**Q1 (-23.23) was our most confident call (TIER 1 STRONG NO at 0.32) and our biggest loss.**

Our reasoning: Algeria fouls 14.78/game vs Jordan 10.44/game (footystats recent 10). Algeria pressing must-win → they foul. Jordan sits deep → fewer fouls. Crowd at 54% underestimated this, we thought.

**What actually happened:** Jordan scored the first goal and spent 60-70+ minutes DEFENDING a 1-0 lead against desperate Algeria attacks. A team defending fouls more — not the team attacking. Algeria, despite being the historical "high-foul" team, was now in possession attacking — they drew fouls instead of committing them. Jordan's defenders made tackle after tackle to hold the result → Jordan fouls surpassed Algeria's.

**The structural error:** We used base-rate foul data as if it were team identity, not as a proxy for "who typically defends more in their usual matches." Algeria fouls 14.78/game because in THEIR TYPICAL MATCHES, they tend to defend or press more. In this specific match, the roles reversed: Jordan became the defending team (after scoring first), so Jordan fouled more.

**This is identical to the JPN-TUN lesson:**  
- JPN-TUN: Japan (pressing team) fouled MORE than Tunisia. We submitted 0.25 (strong NO). Outcome YES → -17.65.  
- JOR-ALG: Algeria (pressing team) fouled LESS than Jordan. We submitted 0.32 (strong NO). Outcome YES → -23.23.  
- **SAME ROOT CAUSE BOTH TIMES:** The team with the higher historical foul rate doesn't always end up the team that fouls more — it depends on who ends up defending in the actual match.

**New Rule — RULE_FOULS:** For "which team fouls more" questions:
1. First predict which team will DEFEND more in this specific match
2. The team that defends more will foul more
3. Use base rate foul data only to calibrate the MAGNITUDE of the fouls, not to predict which team is the defending team
4. If the underdog scores first (Jordan ~30% likely), they will switch to defending → they will foul more than their base rate suggests
5. Never submit below 0.38 or above 0.62 on any "who fouls more" question without verified match-script information about which team will be defending

**Revised rule for pre-match "who fouls more" questions:**
- Consider: which team is the expected DEFENDER? (usually the underdog or the team likely to absorb pressure)
- But consider: if the underdog scores (plausible in survival matches), they switch to DEFENDING, flipping the foul dynamic
- Given match-script uncertainty in a competitive survival match: never stray beyond 0.38-0.62 regardless of base rate gap
- In JOR-ALG: Jordan's first-goal probability (~30%) + Jordan-defending-leads scenario should have kept our estimate closer to 0.45-0.50, not 0.32

---

### Other Lessons

**Q2 (50% → YES, -6.60):** When a strong team is chasing a deficit in 2H in a must-win survival match, their 2H SOT dramatically exceeds their GD1 baseline. Algeria had 0 SOT in GD1 but were in completely different match state in 2H (trailing, must attack). We should revise up more aggressively for "chasing in 2H" scenarios — closer to 65-70% here, not 50%.

**Q3 (18% → YES, -6.03):** Low-probability compound event occurred. Both we (18%) and crowd (23%) were well below 50% — this was genuinely unlikely but happened. No systematic error; straight variance.

**Q5 (45% → NO, -3.20):** We over-elevated penalty probability based on Jordan's historical penalty involvement (8 in 10 matches). The clean tactical survival match narrative (3 goals, no incidents) didn't support penalties. Crowd at 38% was better calibrated — they may have seen this as a tactical, physical-but-controlled match.

**Q10 (+13.11) — validated:** Al-Taamari's club rate (0.76 SOT/game at Rennes) was the right signal. He was Jordan's primary weapon and delivered. This remains our best individual player SOT methodology.

**Q4 (+8.98) — validated:** Algeria's controlled possession style + Amoura absent = <2 offsides. CONFIRMED.

**Q6 (+3.59) — validated:** Mahrez 2H SOT downward revision from model (56.5% → 42%) was correct. He started but either was subbed off before registering a 2H SOT or Algeria's attacks came from other channels.

---

### Rules Status After This Match

| Rule | Status | Evidence |
|------|--------|----------|
| RULE_FOULS (WHO DEFENDS MORE) | **NEW — CRITICAL** | JPN-TUN -17.65, JOR-ALG -23.23. Same root cause. Never go below 0.38 on any pre-match fouls question. |
| GD1 offside behavioral data | CONFIRMED (NOR-SEN Q1 +22.07) | Still strongest rule in portfolio |
| Club SOT base rate for individual players | CONFIRMED (JOR-ALG Q10 +13.11) | Al-Taamari 0.76 SOT/game → SOT confirmed |
| WC-specific vs career scoring record | CONFIRMED (NOR-SEN Q10 +5.63) | Mané 0.25 WC rate was right |
| Chasing-team 2H SOT | **UPDATED** | When team trails in 2H must-win, SOT OUTPUT IS HIGH regardless of GD1. Push harder toward YES. |
| Footystats foul rate as primary input | **REVISED** | Use as magnitude calibration only; must predict WHICH TEAM DEFENDS first |

---

*Added to notebook: 2026-06-23 (JOR-ALG post-match section)*

---

## Match Analysis Session — Portugal vs Uzbekistan

**Date:** 2026-06-23  
**Match:** Portugal vs Uzbekistan (WC2026 Group K, GD2)  
**Group:** K — Portugal, DR Congo, Colombia, Uzbekistan  
**SportsPredict ID:** 69befda5-5418-4a6e-9516-295139e79565  
**Data files:** `sportspredict_research/data/external_markets/por_uzb_2026-06-23.json`  
**Bash log:** `sportspredict_research/bash_logs/2026-06-23_POR-UZB_match_analysis_bash_log.txt`  
**Session type:** Full analysis — ordered logit + Poisson model + research agent (deep search) + GD1 calibration

---

### Context

Portugal drew GD1 1-1 vs DR Congo (surprise result). Uzbekistan lost GD1 1-3 to Colombia. Both need wins in GD2. Portugal is the overwhelming favorite (Elo diff +237.6 = largest mismatch in our analysis series). RULE7 fires for Uzbekistan.

**Key story:** Portugal had only 1 SOT from 7 shots and 68-79% possession vs DR Congo — severe offensive underperformance. Uzbekistan's GD1 vs Colombia showed textbook deep 3-4-2-1 Cannavaro block: zero opposition-box touches in 1H, first shot at 40', and — most importantly — **0 offsides in 90 minutes** despite trailing 3-1.

---

### Rules In Effect

- **RULE7**: FIRES — Uzbekistan 11.9% win prob. Submit unshaded estimates.
- **RULE8**: Does NOT fire — draw 21.8% < 25%.
- **RULE15**: Fires for Shomurodov (Q5).
- **RULE1**: Q7 match winner uses sharp market (-600 to -700) over model (66.4%).

---

### Model Outputs

| Metric | Value |
|--------|-------|
| Portugal win | 66.4% (model) → 85% (market-weighted) |
| Draw | 21.8% |
| Uzbekistan win | 11.9% |
| λ_POR | 1.706 goals |
| λ_UZB | 0.722 goals |
| P(UZB scores) | 51.4% (model); ~39-40% (market BTTS No 67%) |
| P(BTTS AND 3+) | 31.2% |
| P(UZB 4+ SOT) | 17.4% model → 0.12 final |
| P(UZB 2+ offsides) | 33.1% model → 0.20 final |

---

### GD1 Evidence

| Team | Match | SOT | Offsides | Notes |
|------|-------|-----|----------|-------|
| Portugal | vs DR Congo (1-1) | 1 | ≥1 | Cancelo disallowed for offside 55'. 3 yellow cards. Ronaldo peripheral. Ramos sub 83'. |
| Uzbekistan | vs Colombia (1-3) | 2 | **0** | Zero opp. box touches 1H. First shot at 40'. 3-4-2-1 Cannavaro deep block. |

**Most decisive data point: Uzbekistan's 0 offsides in 90 minutes vs Colombia — even while trailing 3-1 (chasing), their tactical system never runs players behind the line.**

---

### Key Calibration Data

- Referee: Jalal Jayed (Morocco) — career 0.50 pens/game (42/84 matches = highest seen this tournament). 0 cards in GER 7-1 CUR.
- Gonçalo Ramos: PSG, 0.41 goals/90. Confirmed supersub (83' in GD1, ~7 min). Expected similar role.
- Shomurodov: Başakşehir, 0.68 goals/90 last season. GD1: started, no goal. UZB had 2 total SOT.
- Market: Portugal -600 to -700 (87.5%). BTTS No 67%. Over 2.5 at 63%. Over 3.5 at 46%.
- Corners line: Over 8.5 (-150 DraftKings). GD1 combined corners: 5+3=8.
- Portugal qualifying SOT avg: 8.3/game (GD1 was a severe outlier at 1 SOT).

---

### Final Estimates

| Q | Question | Model P | Final | Key Driver |
|---|----------|---------|-------|------------|
| Q1 | UZB 2+ offsides | 33.1% | **0.20** | UZB had 0 GD1 offsides; Cannavaro deep block never runs behind lines |
| Q2 | POR more 2H SOT | 71.1% | **0.80** | RULE7 unshaded; Portugal dominant; UZB barely shoots |
| Q3 | POR 2+ offsides | 76.8% | **0.65** | Portugal attacks aggressively; GER-CUR analogue pulls DOWN from model |
| Q4 | Penalty OR red card | 38% | **0.42** | Jayed career 0.5 pens/game — highest of any referee this tournament |
| Q5 | Shomurodov 2H SOT | 34.1% | **0.25** | RULE15 fires; UZB only 2 GD1 SOT; blowout suppression |
| Q6 | BTTS AND 3+ goals | 31.2% | **0.30** | P(UZB scores) ~39-40% is binding constraint |
| Q7 | Portugal win | 66.4% | **0.85** | Market -600/-700 (87.5%); RULE1 market > model |
| Q8 | 2H 2+ goals | 38.6% | **0.42** | Over 3.5 at 46%; Portugal scoring multiple + potential UZB counter |
| Q9 | UZB 4+ total SOT | 17.4% | **0.12** | Only 2 GD1 SOT; 4+ vs Portugal defense = double GD1 output; RULE7 |
| Q10 | Ramos scores | 40.1% | **0.48** | Goal.com +90 (~52%); supersub role discount; coin flip |

**Edge ranking:**
1. Q1 0.20 — Crowd ~45-52%; GD1 0-offside data creates -30pp edge
2. Q9 0.12 — Crowd ~25-35%; UZB 2 GD1 SOT makes 4+ near-impossible
3. Q2 0.80 — Portugal dominates SOT; UZB passive; RULE7 unshaded
4. Q7 0.85 — Market definitive; crowd may be at 70-78% post GD1 draw
5. Q5 0.25 — RULE15; GD1 SOT evidence; crowd anchors on club form

---

### New Methodological Notes

**1. GER-CUR analogue applies to dominant team's offsides:**
In our GER-CUR match (Germany 7-1 Curaçao), Germany had <2 offsides despite attacking continuously — we scored +13.79 by going 0.43 vs crowd 0.54. The mechanism: when the defending team sits in an extreme deep block, their defensive line is LOW and STATIC → attacking team's forwards can more easily time legal runs → fewer offsides despite heavy attacking. Applied here to Q3 (Portugal 2+ offsides) — revised from model 76.8% to 0.65.

**2. Referee penalty rate is match-type-specific:**
Jalal Jayed's career 0.5 pens/game rate is extraordinary. But in his WC2026 match (GER 7-1 CUR), he gave 0 penalties. Blowout context suppresses penalty frequency. For Q4 in dominant wins: apply referee's career rate but discount by ~30-40% for blowout context. Final: 0.42 (vs unadjusted ~55%).

**3. Uzbekistan 0-offside GD1 overrides blowout reversal rule:**
The blowout reversal rule says: teams chasing a 3-goal deficit push forward → get caught offside. But Uzbekistan had 0 offsides even while trailing 3-1 vs Colombia. Their Cannavaro tactical system is structurally designed to never send players behind lines — this overrides the generic blowout reversal rule. The GD1 evidence is decisive.

---

### Post-Match Results — Portugal 5-0 Uzbekistan

**Final score:** Portugal 5-0 Uzbekistan  
**Total RBP:** -1.11  
**Beat crowd:** 6/10  

| Q | Outcome | Us | Crowd | RBP | vs Crowd |
|---|---------|-----|-------|-----|---------|
| Q1 | YES | 0.20 | 0.41 | **-26.35** | BELOW |
| Q2 | YES | 0.80 | 0.74 | +4.99 | beat |
| Q3 | YES | 0.65 | 0.56 | **+9.38** | beat |
| Q4 | NO | 0.42 | 0.39 | -0.32 | below |
| Q5 | NO | 0.25 | 0.35 | **+8.78** | beat |
| Q6 | NO | 0.30 | 0.35 | +5.72 | beat |
| Q7 | YES | 0.95 | 0.81 | +5.49 | beat |
| Q8 | YES | 0.42 | 0.52 | -8.38 | below |
| Q9 | NO | 0.12 | 0.30 | **+10.61** | beat |
| Q10 | NO | 0.48 | 0.29 | **-11.03** | below |

---

### Critical Post-Match Analysis

**Q1 CATASTROPHE (-26.35) — 3rd consecutive match with extreme low-estimate disaster**

Our call: 0.20 (STRONG NO). Uzbekistan had 0 GD1 offsides. Reasoning seemed airtight.

What happened: Portugal won 5-0. Uzbekistan abandoned Cannavaro's compact system in the 2H and pushed forward desperately → caught offside 2+ times.

**The key distinction we missed:** Uzbekistan's 0 GD1 offsides was in a 1-3 loss to Colombia — a survivable deficit. A 5-0 collapse is a categorically different scenario. ALL teams abandon tactical shape when losing by 4-5 goals. Their system was intact at 1-3; it collapsed at 5-0.

**The blowout reversal rule exists for exactly this reason** — and we correctly wrote it into our methodology. Then we OVERRODE it because of the GD1 0-offside evidence. The override was wrong.

Correct logic: GD1 0-offside evidence is valid for NORMAL game scripts (competitive within 2 goals). In extreme blowout territory (4+ goals), all teams abandon shape → generic blowout reversal applies → revert to ~0.35-0.45 regardless of GD1 tactical evidence.

**Pattern across 3 consecutive matches:**
1. JOR-ALG Q1 (-23.23): extreme estimate 0.32 on fouls → Jordan defended lead → fouled more
2. POR-UZB Q1 (-26.35): extreme estimate 0.20 on offsides → 5-0 blowout → UZB pushed forward → caught
3. Both caused by over-confidence in low count-stat estimates derived from a single GD1 data point

**NEW HARD FLOOR RULE: Never submit below 0.25 on any 2+ offsides, 4+ SOT, or similar count-stat threshold question.** If GD1 data points toward 0.15-0.20, submit 0.25 as the minimum floor. The blowout scenario (which can always occur) produces behavior that overrides any tactical system.

---

**Q10 LOSS (-11.03) — Main book absence was the right signal**

Our call: 0.48 (coin flip). Reasoning: Goal.com listed Ramos at +90 (~52%).

What happened: Ramos scored 0. Portugal's 5 goals came from Ronaldo, Neto, Conceicao, Fernandes. Crowd at 0.29 was far more accurate.

**Root cause:** FanDuel and DraftKings did NOT list Ramos on their scorer markets. We noticed this and flagged it — but then over-weighted the niche Goal.com aggregator (+90) which was likely stale or inaccurate. 

**NEW RULE: Main book absence = scorer probability <35%.** When the top-volume sportsbooks (FanDuel, DraftKings, Betfair) don't include a player in their scorer markets, it is because they assess his scoring probability as LOW. Niche aggregators can have stale/wrong odds. Never go above 0.38 for a player the main books exclude.

---

**What worked:**
- **Q9 +10.61**: UZB <4 total SOT (we: 0.12, crowd: 0.30). RULE7 + GD1 2-SOT data confirmed. Compact system generates almost no SOT in extreme mismatch.
- **Q3 +9.38**: Portugal 2+ offsides (we: 0.65, crowd: 0.56). Calibrated correctly between model's 76.8% and GER-CUR analogue.
- **Q5 +8.78**: Shomurodov 0 2H SOT (we: 0.25, crowd: 0.35). **RULE15 confirmed again.** Expected-losing-team forward in blowout = no 2H SOT.
- **Q6 +5.72**: BTTS NO (we: 0.30, crowd: 0.35). P(UZB scores) ~39% assessment correct — they scored 0.
- **Q7 +5.49**: Portugal win at 0.95 (user adjusted from recommended 0.85; crowd 0.81). Above crowd.

---

### Rules Status Update

| Rule | Status | Evidence |
|------|--------|----------|
| **FLOOR_0.25** | **NEW HARD RULE** | Never below 0.25 on any count-stat threshold question. Blowout reversal always possible. |
| **MAIN_BOOK_ABSENCE** | **NEW HARD RULE** | If FanDuel/DK don't list a player in scorer markets → probability <35%, submit ≤0.38. |
| RULE15 (losing-team forward SOT) | CONFIRMED again | Q5 +8.78. Shomurodov 0 2H SOT in 5-0 blowout. N=10+ now. |
| RULE7 SOT suppression | CONFIRMED | Q9 +10.61. UZB <4 total SOT in 5-0. Compact underdog barely shoots. |
| Blowout reversal (offsides) | CONFIRMED | Overriding GD1 data was wrong. 5-0 forced UZB to abandon system. Q1 -26.35. |
| GD1 evidence floor | **REVISED** | GD1 data is valid for NORMAL game scripts only. In extreme blowout (4+ goals), revert to generic estimates regardless of GD1 tactical evidence. |

---

*Added to notebook: 2026-06-23 (POR-UZB post-match section)*

---

<a name="data-source-reliability-audit"></a>
## Data Source Reliability Audit — Full Match Ledger Analysis
**Date:** 2026-06-23
**Purpose:** Synthesize every data source used across 26+ matches into a ranked reliability guide, grounded in actual RBP evidence. Triggered by three consecutive catastrophic losses tracing back to data source errors.
**Memory file:** `/memory/feedback_data_source_reliability.md`

> "Reliability of data sources is everything. We only pick from reliable data sources." — User instruction, 2026-06-23.

---

### Why This Analysis Was Needed

Three consecutive Q1 disasters across JOR-ALG and POR-UZB (combined -60.61 RBP from Q1 alone plus -11.03 from POR-UZB Q10) shared a single root cause: using data sources in the wrong context, or ignoring stronger signals in favor of weaker ones. The losses were not from bad data. They were from wrong **source selection** and wrong **application** of otherwise-correct data.

Pattern:
1. JOR-ALG Q1 (-23.23): footystats foul averages used as direction signal → match script reversed role
2. POR-UZB Q1 (-26.35): GD1 individual behavioral data (0 offsides) applied without FLOOR_0.25 → blowout override
3. POR-UZB Q10 (-11.03): niche aggregator (Goal.com +90) overrode main book absence signal

---

### TIER 1: RELIABLY PROFITABLE — Always Use, Weight Heavily

#### 1. GD1 Individual Player Behavioral Data (ESPN / Opta Analyst / FotMob)
The single most powerful source in the portfolio. Verified, specific, directly predictive when match script replicates.

| Match | Q | GD1 Data | Our Est | Outcome | RBP |
|-------|---|----------|---------|---------|-----|
| NOR-SEN | Q1 | Jackson 3+ offsides vs France high line | 0.78 | YES | **+22.07** |
| JOR-ALG | Q10 | Al-Taamari SOT confirmed in GD1 | 0.58 | YES | **+13.11** |
| POR-UZB | Q9 | UZB 2 total GD1 SOT vs Colombia | 0.12 | NO | **+10.61** |
| NOR-SEN | Q4 | NOR 13 GD1 fouls vs SEN 5 | 0.48 | NO | **+8.46** |
| POR-UZB | Q5 | Shomurodov passive GD1 output + RULE15 | 0.25 | NO | **+8.78** |
| USA-AUS | Q2 | AUS 0 offsides pattern in GD1 | 0.15 | NO (0 offsides) | **+20.74** |
| GER-CIV | — | CIV 2+ offsides: GD1 behavioral suppression | 0.18 | NO | **+18.70** |

**When it FAILS — wrong application, not wrong data:**

| Match | Q | Failure Mode | RBP |
|-------|---|-------------|-----|
| ARG-AUT | Q9 | Sabitzer 0 GD1 SOT in dominant win → extrapolated to chasing context | **-31.86** |
| JOR-ALG | Q1 | Algeria foul rate applied without predicting which team defends | **-23.23** |
| POR-UZB | Q1 | UZB 0 GD1 offsides applied below FLOOR_0.25 | **-26.35** |
| BRA-HAI | Q2 | Haiti 0.10 offsides — no floor — in 3-0 blowout | **-42.56** |

**Three caveats — always check before applying:**
1. Match-script must match (same defensive role, similar opponent quality, similar scoreline range)
2. **FLOOR_0.25** always applies: never submit below 0.25 on any count-stat question regardless of GD1
3. For foul/defensive questions: predict which team DEFENDS in the actual match first

---

#### 2. Main Sportsbook Consensus (FanDuel + DraftKings + Betfair + bet365 Agreeing)
Near-ground-truth for match winner and BTTS. Player market **absence** is the strongest negative signal.

| Match | Q | Signal | Our Est | Outcome | RBP |
|-------|---|--------|---------|---------|-----|
| POR-UZB | Q7 | Portugal -600/-700 | 0.85/0.95 | YES | **+5.49** |
| POR-UZB | Q6 | BTTS No -190/-200 | 0.30 | NO (UZB scored 0) | **+5.72** |
| FRA-IRQ | Q6 | France -1200/-1500 | 0.88 | YES | confirmed |
| CAN-QAT | match | Canada heavy fav | structural bets | all confirmed | +62.72 total |

**Player market absence failure — POR-UZB Q10 (-11.03):**
Ramos not listed on FanDuel/DraftKings. We followed Goal.com +90 instead. Ramos scored 0. Portugal scored 5. The absence was the signal. We ignored it.

**MAIN_BOOK_ABSENCE RULE:** FanDuel AND DraftKings both exclude a player → probability < 35%. Submit ≤ 0.38. Niche aggregator data is overridden by main book absence.

---

#### 3. FootyMetrics Referee Career Statistics (YC/game, pens/game)
Career sample 80+ matches. Reliable for card/penalty questions.

| Match | Referee | Key Stat | Q | RBP |
|-------|---------|----------|---|-----|
| NOR-SEN | Elfath | 0.27 pens/game (below career) + Group D GD1: 0 pens | Q3 penalty NO | **+2.91** |
| FRA-IRQ | Fischer | 3.35 YC/game (above WC avg 2.17) | Q3 Iraq 2H card YES | **confirmed** |
| SUI-BIH | Pinheiro | HIGH CARD referee | 2H 2+ cards | **+6.52** |

**Caveat:** Blowout suppresses pens/cards. Jayed career 0.50 pens/game but gave 0 pens in GER 7-1 CUR. Apply 30-40% blowout discount when RULE7 fires (extreme mismatch).

---

#### 4. Club-Level SOT per 90 from Top 5 European Leagues
Top 5 leagues (PL, La Liga, Ligue 1, Serie A, Bundesliga) = full weight. Saudi/MLS = 60% weight.

| Player | Club Rate | League | Match Q | RBP |
|--------|-----------|--------|---------|-----|
| Al-Taamari | 0.76 SOT/90 | Rennes (Ligue 1) | JOR-ALG Q10 | **+13.11** |
| Mahrez | 0.41 SOT/90 | Al-Ahli (Saudi) | JOR-ALG Q6 | **+3.59** |
| Gyökeres | Club rate | Top 5 | NED-SWE RULE15 | **+18.04** |

**Caveat:** Scale down for supersubs (< 45 min average). Even correct rates can fail for specific match context.

---

#### 5. Player's WC-Specific Career Record (FIFA)
Tournament performance differs meaningfully from career international average.

| Player | WC Record | Career Record | Applied | Outcome | RBP |
|--------|-----------|--------------|---------|---------|-----|
| Mané | 0.25 goals/WC match | 0.43 goals/cap | 0.24 submitted | NO (scored 0) | **+5.63** |

**Rule:** If WC-specific vs career gap > 0.10, weight WC record 70%, career record 30%.

---

#### 6. Polymarket (> $1M Traded)
NOR-SEN: $3.6M at NOR 43% → Norway won 3-2. Calibration validated. Rule: weight equally with main books at > $1M. Below $500K, directional only.

---

### TIER 2: USEFUL WITH ADJUSTMENTS

| Source | Works | Fails | Adjustment |
|--------|-------|-------|------------|
| Footystats 10-match foul averages | NOR-SEN Q4 +8.46, SUI-BIH +12.71, GER-CUR +23.36 | JOR-ALG Q1 -23.23, JPN-TUN -17.65 | Predict WHICH TEAM DEFENDS first. Never direction alone. Never < 0.38 or > 0.62 without match-script. |
| Market O/U and BTTS lines | BTTS No 67% POR-UZB → +5.72 | Q8 2H 2+ goals calibration off (-8.38) | Over 3.5 at >40% → use 0.55-0.65 for 2H 2+ goals |
| Football Whispers / Covers trends | Jordan over 2.5 in 5/6 → +1.38 | Not precise enough alone | 15-20% weight max, directional only |
| Our own Poisson/ordered logit | RULE7/RULE8 framework | Extreme mismatches (Elo gap > 350) | Elo gap > 350: weight market 90%, model 10% |

---

### TIER 3: UNRELIABLE — AVOID

| Source | Failure Evidence | Rule |
|--------|-----------------|------|
| Niche aggregator scorer odds when absent from main books | POR-UZB Q10 Goal.com +90 → -11.03 | MAIN_BOOK_ABSENCE: submit ≤ 0.38 |
| GD1 behavioral data below 0.25 on count-stat questions | BRA-HAI -42.56, TUR-PAR -20.26, ESP-KSA -7.12, POR-UZB -26.35 | FLOOR_0.25: never submit below 0.25 |
| Raw foul averages without defending-team prediction | JOR-ALG -23.23, JPN-TUN -17.65, NZL-EGY -18.43 | RULE_FOULS: predict defending team first |
| Personal conviction overrides | BRA-MAR Q8 -51.97 (WORST EVER), ENG-CRO Kane -44.55 | RULE6: never below 0.05 or above 0.95 |
| Cross-team GD1 extrapolations | ARG-AUT -42.24, QAT-SUI Q1 -42.51 | GD1 data is valid for THAT TEAM only |

---

### Master Hierarchy: When Sources Conflict

| Priority | Source | Notes |
|----------|--------|-------|
| 1 | GD1 individual player behavioral data (same context) | Apply FLOOR_0.25; check match-script match |
| 2 | Main sportsbook consensus (3+ books agreeing) | Player absence = probability < 35% |
| 3 | FootyMetrics referee career stats | Blowout discount 30-40% |
| 4 | Club-level SOT/90 (top 5 European league) | Scale for sub minutes |
| 5 | WC-specific career record (FIFA) | Weight 70% when gap > 0.10 |
| 6 | Polymarket (> $1M traded) | = main books at this volume |
| 7 | GD1 team-level stats (scenario-weighted) | Not deterministic |
| 8 | Footystats foul averages (match-script first) | Magnitude only, never direction |
| 9 | Football Whispers / trend sites | 15-20% weight, sanity check |
| 10 | Expert previews (CBS Sports, Racing Post) | Sanity check only |
| ❌ | Niche aggregator odds when main books absent | MAIN_BOOK_ABSENCE overrides |
| ❌ | GD1 data for estimates below 0.25 | FLOOR_0.25 hard rule |
| ❌ | Raw foul averages (no match-script prediction) | RULE_FOULS |
| ❌ | Personal conviction without data | RULE6 |

---

## England vs Ghana — WC2026 Group L GD2
**Date:** 2026-06-23 | **Final Score: 0-0 DRAW** | **MAJOR UPSET**

*Added to notebook: 2026-06-23*

### Context
England (Elo 2090.37) vs Ghana (Elo 1625.50). Elo diff: 464.87 — LARGEST in our analysis series. England heavily favored (-600 market, 86.55% model). Ghana used deep block 4-3-3 counter-attacking setup from GD1. Thomas Partey returned after GD1 visa absence. Semenyo started for Ghana.

### Model Outputs (Neutral Venue)
| Metric | Value |
|--------|-------|
| λ_ENG | 2.574 |
| λ_GHA | 0.478 |
| P(ENG win) | 86.55% |
| P(Draw) | 9.48% |
| P(GHA win) | 3.97% ← **RULE7 FIRED** |
| P(ENG scores) | 92.38% |
| P(GHA scores) | 38.00% |

**Market:** FanDuel ENG -600 (85.7% implied). Both consistent with model.

### Rules Applied
- **RULE7:** FIRES (Ghana 3.97% win). Do not compress toward 50% on underdog props.
- **RULE8:** Does NOT fire (draw 9.48% < 25%).
- **RULE15:** FIRES for Semenyo (Q9). Expected-losing-team forward.
- **RULE_FOULS:** Ghana defends from kickoff → Ghana fouls more (Q2).
- **FLOOR_0.25:** Q9 (Semenyo), Q10 (Ghana corners).

### Final Estimates
| Q | Question | Estimate | Direction |
|---|----------|----------|-----------|
| Q1 | Both teams ≥1 HT SOT | 0.23 | STRONG NO |
| Q2 | Ghana more fouls than England | 0.58 | YES |
| Q3 | Both teams ≥1 2H SOT | 0.52 | NEUTRAL |
| Q4 | BTTS AND 3+ goals | 0.30 | NO |
| Q5 | Penalty OR red card | 0.45 | SLIGHT YES |
| Q6 | Ghana more 2H SOT than England | 0.18 | STRONG NO |
| Q7 | England win | 0.86 | STRONG YES |
| Q8 | Kane score or assist | 0.68 | YES |
| Q9 | Semenyo ≥1 SOT | 0.28 | NO |
| Q10 | Ghana 5+ corners | 0.25 | NO |

### Post-Match Results
**Final Score: 0-0** — Massive upset. England's 86% win probability failed to materialise.

| Q | Our Est. | Crowd | Outcome | RBP | Beat Crowd? |
|---|----------|-------|---------|-----|-------------|
| Q1 | 0.23 | 0.61 | NO | **+35.5** | YES |
| Q2 | 0.58 | 0.61 | YES | +0.09 | YES |
| Q3 | 0.52 | 0.66 | YES | -9.28 | NO |
| Q4 | 0.30 | 0.37 | NO | +7.51 | YES |
| Q5 | 0.45 | 0.37 | NO | -4.09 | NO |
| Q6 | 0.18 | 0.22 | NO | +3.60 | YES |
| Q7 | 0.86 | 0.80 | NO | -7.56 | NO |
| Q8 | 0.68 | 0.65 | NO | -0.71 | NO |
| Q9 | 0.28 | 0.45 | NO | **+15.14** | YES |
| Q10 | 0.25 | 0.28 | NO | +4.19 | YES |

**Total RBP: +44.4** | Beat crowd: 6/10 | Below crowd: 4/10

### Key Learnings

**WIN — Q1 +35.5:** Ghana had 0 total shots in 1H (GD1 evidence predicted this). Crowd at 61% was massively wrong. **GD1 individual behavioral data is the most powerful signal in our toolkit.** When you have direct evidence of a team's attacking output in the same context, use it without hesitation.

**WIN — Q9 +15.14:** Semenyo 0 SOT. RULE15 applied correctly. Club form (0.9 SOT/90) was irrelevant against RULE7 + GD1 evidence. Crowd at 45% wildly overpriced club form. **RULE15 + GD1 evidence together = the most reliable suppression signal combination.**

**LOSS — Q3 -9.28:** Both teams 2H SOT (YES). We estimated 52%; crowd 66%. Even massively outmatched Ghana (3.97% model win probability) got ≥1 SOT in 2H. **CALIBRATION UPDATE: "Both teams ≥1 2H SOT" base rate is ~75-80% even in extreme mismatches. The 2H is fundamentally different from 1H for underdog SOT.** Anchor at minimum 60% unless there's specific evidence the underdog won't attack at all in 2H.

**LOSS — Q7 -7.56:** England failed to win in a 0-0 draw. We were at 86%, crowd at 80%. The 9.48% draw scenario materialized. Model was correctly calibrated — high-probability events fail. But we ate more loss than the crowd because we were more confident. **NOTE: In extreme Elo mismatches where the draw probability is ~10%, the crowd's slight compression (80% vs 86%) was better ex-post. This is within variance but worth tracking.**

**LOSS — Q5 -4.09:** Penalty/red card. We went 45% (above crowd 37%). Result NO. **Historical pattern: we keep being too high on penalty/red card questions.** Need to audit this question type across the full ledger.

**KEY MATCH FACT:** England 0-0 Ghana despite 464.87 Elo gap (largest in our series). λ_ENG=2.574 goals expected; actual: 0. This is a reminder that extreme Elo advantage does not guarantee goals — Ghana's deep block 4-3-3 was effective even without Partey in GD1.

---

## Croatia vs Panama — WC2026 Group L GD2
**Date:** 2026-06-23 | **Venue:** Neutral | **Both teams must win**

*Added to notebook: 2026-06-23*

### Context
Group L GD2. Croatia (1973 Elo) vs Panama (1859 Elo). Elo diff: 114.53. Both teams lost GD1 and MUST WIN to stay in contention. Croatia lost 2-4 to England; Panama lost 0-1 to Ghana.

Critically: Luka Sučić (Real Sociedad, AM/W, age 23) and Petar Sučić (Inter Milan, CM, age 22) are two DIFFERENT Croatia players. Petar STARTED vs England (90 min, assist on Baturina goal). Luka was UNUSED SUBSTITUTE vs England — zero tournament minutes entering GD2.

### Model Outputs (Neutral Venue)
| Metric | Value |
|--------|-------|
| λ_CRO | 1.3653 |
| λ_PAN | 0.9019 |
| P(CRO win) | 51.01% |
| P(Draw) | 28.65% ← **RULE8 FIRES** |
| P(PAN win) | 20.34% |
| P(CRO scores) | 74.47% |
| P(PAN scores) | 59.42% |
| P(BTTS) | 44.25% |

**Market:** FanDuel CRO -220 (68.75% win implied). Panama +600 (14.3% implied).
**Market/Model gap:** 17.7pp on Croatia. Largest gap in our current series. Market weights Croatia's WC pedigree (finalist 2018, 3rd place 2022) beyond what Elo captures. Blended CRO win: 59.9%.

### Rules Applied
- **RULE8:** FIRES (draw 28.65%). **Survival match caveat** (JOR-ALG lesson): both teams attack hard regardless of score. Do NOT suppress attacking props aggressively. Apply RULE8 to props cautiously.
- **RULE7:** Market fires (PAN 14.3% < 15% threshold). Applied to player props.
- **RULE15:** Fajardo (Q9). Panama expected losing team per market. Full suppression.
- **RULE_FOULS:** Croatia possession team → Panama defends → Panama fouls more (direction). Croatia historical 13.0/game (magnitude baseline).
- **FLOOR_0.25:** Applied to Q2, Q7, Q9, Q10.

### Key GD1 Evidence
**Croatia vs England (L 2-4):**
- 10 shots, 8 SOT, 12 fouls, **2 corners**, 1 offside, 38% possession
- Both CRO goals in 1H. Zero 2H goals despite chasing.
- Croatia WC corner history: under 6.5 corners in 8 consecutive WC matches.
- Historical avg fouls: 13.0/game.

**Panama vs Ghana (L 0-1):**
- 12 shots, 4 SOT, 11 fouls, **2 corners**, 1 offside, 62% possession, **29 tackles** (most in WC2026 R1)
- 4 SOT despite losing. 2 corners despite 62% possession — NOT a corner-generating team.
- Blackman (YC 70') + Harvey (YC 90') — BOTH on yellow card warnings for GD2.
- Fajardo: sub (62' on), 0 SOT in 28 min vs Ghana compact defensive block.

### Final Estimates
| Q | Question | Estimate | Direction | Key Rationale |
|---|----------|----------|-----------|---------------|
| Q1 | Panama more fouls than Croatia | 0.50 | COIN-FLIP | RULE_FOULS (Panama defends) vs Croatia 13.0/game historical; near coin-flip |
| Q2 | Panama 2+ offsides | 0.32 | NO | Poisson λ=1: P(≥2)=26.4%; Panama only 1 offside in GD1 despite 62% possession |
| Q3 | Panama more 2H SOT than Croatia | 0.30 | STRONG NO | Market Croatia 69% win; Croatia dominates 2H; Skellam P(PAN>CRO) ~30% |
| Q4 | Croatia first goal of 2H | 0.42 | YES_LEAN | Model 40.8%; survival match calibrates up; Croatia 60% rate share of 2H goals |
| Q5 | Croatia more cards than Panama | 0.38 | NO | Panama physical (29 tackles) + 2 on warnings = Panama accumulates more cards |
| Q6 | Panama scores ≥1 goal | 0.55 | YES | P(PAN scores)=59.4% model; BTTS market ~53%; must-win attack urgency |
| Q7 | 9+ total corners | 0.30 | STRONG NO | 2 corners each in GD1; Croatia under 6.5 in 8 WC matches; Poisson λ=7: P(≥9)=27% |
| Q8 | Panama 3+ SOT | 0.45 | SLIGHT_NO | GD1 4 SOT vs Ghana; Croatian defense quality discount; model λ_SOT≈2.5 |
| Q9 | Fajardo ≥1 SOT | 0.28 | NO | RULE15 full (market 14.3%); GD1 0 SOT sub; Ecuador league; FLOOR_0.25 applied |
| Q10 | Luka Sučić ≥1 SOT | 0.30 | NO | Unused sub vs England (zero GD1 data); P(starts)=42%; weighted calc gives 0.295 |

### Edge Ranking
1. **Q7 0.30 STRONG NO** — Corners: GD1 evidence (2 each) + Croatia WC history. Crowd likely ~0.43.
2. **Q3 0.30 STRONG NO** — Panama more 2H SOT: market says Croatia 69% win dominance.
3. **Q9 0.28 NO** — Fajardo: RULE15 full + GD1 0 SOT sub + MAIN_BOOK_ABSENCE signal.
4. **Q10 0.30 NO** — Luka Sučić: unused vs England; crowd may conflate with Petar who started.
5. **Q5 0.38 NO** — Croatia more cards: Panama physical + two on warnings.
6. **Q6 0.55 YES** — Panama scores: survival attack urgency + GD1 capability (4 SOT).
7. **Q4 0.42 YES_LEAN** — Croatia first 2H goal: model 40.8%.
8. **Q2 0.32 NO** — Panama offsides: 1 in GD1; survival match slight bump.
9. **Q8 0.45 SLIGHT_NO** — Panama 3+ SOT: near coin-flip.
10. **Q1 0.50 COIN-FLIP** — Fouls: too close to call.

### Post-Match Results
**Final Score: Croatia 1-0 Panama**

| Platform Q | Question | Our Est. | Crowd | Outcome | RBP | Beat? |
|-----------|----------|----------|-------|---------|-----|-------|
| Q1 | Panama 2+ offsides | 0.32 | 0.44 | NO | **+11.69** | ✅ |
| Q2 | Panama more 2H SOT than Croatia | 0.30 | 0.27 | NO | +0.39 | ✅ |
| Q3 | Croatia first goal of 2H | 0.42 | 0.54 | YES | -9.80 | ❌ |
| Q4 | Panama more fouls than Croatia | 0.50 | 0.57 | YES | -4.70 | ❌ |
| Q5 | Croatia more cards than Panama | 0.38 | 0.36 | NO | -0.14 | ❌ |
| Q6 | Panama scores ≥1 goal | 0.55 | 0.50 | NO | -3.09 | ❌ |
| Q7 | 9+ total corners | 0.30 | 0.51 | YES | **-21.77** | ❌ |
| Q8 | Panama 3+ SOT | 0.45 | 0.49 | NO | +6.80 | ✅ |
| Q9 | Fajardo ≥1 SOT | 0.28 | 0.40 | NO | +10.62 | ✅ |
| Q10 | Luka Sučić ≥1 SOT | 0.30 | 0.37 | NO | +9.53 | ✅ |

**Total RBP: -0.47** | Beat crowd: 5/10 | Below crowd: 5/10

### Key Learnings — POST-MATCH

**CRITICAL FAILURE — Q7 -21.77: Corner estimation in survival matches**
9+ corners YES despite both teams having only 2 corners each in GD1. Root cause: in a both-teams-must-win match, corner production surges beyond GD1 baselines due to attacking desperation. The Under 9.5 -150 market implied P(≥10)≈40%; P(≥9) was therefore ~50-53% (crowd 51% was correct). We anchored too heavily on GD1 (Poisson λ=7, P≥9=27%) and not enough on the market.
**NEW RULE — SURVIVAL MATCH CORNERS:** When both teams are in must-win situations, do NOT anchor corners on GD1 data. Treat corner market line as near-primary source. P(≥9 corners) in a both-must-win match ≈ 50% (treat as coin-flip unless structural reason otherwise). The market Under 9.5 at -150 gave P(≥9)≈50-53% — we should have been at 0.45-0.50, not 0.30.

**MISS — Q4 -4.70: RULE_FOULS should have pushed us higher**
Panama more fouls YES. Our coin-flip (0.50) cost us vs crowd (0.57). RULE_FOULS correctly said Panama defends → Panama fouls more. We hesitated because Croatia has a 13.0/game historical average. But in THIS match with Croatia having possession, Panama was definitively the defending team. RULE_FOULS direction signal should outweigh the magnitude uncertainty from historical averages. Should have been 0.55-0.58 per RULE_FOULS logic.

**MISS — Q3 -9.80: First 2H goal too conservative**
Croatia first 2H goal YES. Our 0.42 was below crowd (0.54). Croatia scored the only goal of the match in the 2H. In tight competitive matches where Croatia is slight favorite, the first 2H goal event is probably worth anchoring closer to 0.50-0.55.

**WINS — RULE15 perfect again: Q9 +10.62 (Fajardo 0 SOT) + Q10 +9.53 (Luka Sučić 0 SOT)**
Both player props came in. RULE15 pattern holds extremely reliably. Fajardo confirmation: n=2 for this specific player (GHA-PAN and CRO-PAN, both 0 SOT, both RULE15 correctly applied).

**WIN — Q1 +11.69: Panama offsides**
Panama had 0 offsides (even fewer than GD1's 1). GD1 behavioral data on Panama's disciplined non-offside-trap play was correct. Crowd at 44% assumed survival match would create more counter-attacks → more offsides; this did not happen.

---

*Added to notebook: 2026-06-23*

---

## Colombia vs DR Congo — WC2026 Group K GD2
**Date:** 2026-06-23 | **Venue:** Estadio Akron, Guadalajara | **Kickoff:** 22:00 ET

*Added to notebook: 2026-06-23*

### Context
Colombia (Elo 2063.71) vs DR Congo (Elo 1763.20). Elo diff: 300.51. Group K GD2. Colombia won GD1 3-1 vs Uzbekistan; DR Congo drew 1-1 vs Portugal. Colombia (3 pts) can clinch knockout qualification with a win. DR Congo (1 pt) effectively must win to stay alive — de facto survival match for CDR.

**RULE7 FIRES: DR Congo 8.85% model / 13.6% market win probability — both below 15% threshold.**

Tactical context: DR Congo plays a disciplined 5-3-2 / 3-5-2 defensive block with Wan-Bissaka and Masuaku as wingbacks. In GD1 vs Portugal, they held Portugal (68% possession) to only **1 total SOT in 7 shots** — exceptional defensive discipline. Colombia plays a high-press 4-2-3-1 under Néstor Lorenzo with Luis Díaz (goal+assist+woodwork vs Uzbekistan) as the key attacking weapon.

### Model Outputs (Neutral Venue)
| Metric | Value |
|--------|-------|
| λ_COL | 1.9117 |
| λ_CDR | 0.6442 |
| P(COL win) | 73.25% |
| P(Draw) | 17.90% |
| P(CDR win) | 8.85% ← **RULE7 FIRES** |
| P(COL scores) | 85.22% |
| P(CDR scores) | 47.49% |
| P(BTTS) | 40.47% |
| P(total ≤ 2) | 52.96% |
| P(COL leads HT) | 50.67% |
| P(COL more 2H SOT) | 76.37% |
| P(COL more 2H goals) | 50.67% |

**Market:** FanDuel COL -195 (62.7% de-vigged), Draw +300 (23.7%), CDR +600 (13.6%).
**Market/Model gap:** 10.5pp on COL win. Market gives more weight to draw and CDR draw.

### Key GD1 Evidence
**Colombia (vs Uzbekistan, W 3-1):** 15 shots, 4 SOT, 11 fouls, 4 corners, 3 offsides, 56% possession. Scored 1H (Muñoz 40') and 2H x2 (Díaz 65', Campaz 90+9'). High-press 4-2-3-1 style. Díaz: 1G+1A+woodwork.

**DR Congo (vs Portugal, D 1-1):** 8 shots, 2 SOT, 10 fouls, 4 corners, 2 offsides, 25% possession. Wissa equalised 45+5'. Held Portugal to **1 total SOT** despite 68% possession. **0 goals in 2H.** Bakambu started 90 min; ~1 SOT (forced save from Costa in 2H). 5-3-2 compact block.

### Referee: Maurizio Mariani (Italy)
- Career: **4.81 YC/game**, 0.37 pens/game (289 matches)
- 2025-26: 3.95 YC/game, **0.24 pens/game**, 24.29 fouls/game
- WC2026 GD1: Saudi Arabia vs Uruguay

### Player Intelligence
**Luis Díaz (Colombia, LW):** Liverpool/Bayern. ~1.5-1.8 SOT/90 (13 PL goals 2024-25). GD1: 1 goal + 1 assist + woodwork. FanDuel scorer +185 (35.1% implied). Score/assist estimated ~47-48%.

**Cédric Bakambu (DR Congo, ST):** Real Betis (La Liga). 1.44 SOT/90 in 561 min (mostly sub). GD1: started 90 min, 1 SOT (forced Costa save in 2H). FanDuel scorer +490, score/assist +230 (30.3% implied). **RULE15 full: <15% underdog → 0.25-0.35 range.**

### Final Estimates
| Q | Question | Estimate | Direction | Key Rationale |
|---|----------|----------|-----------|---------------|
| Q1 | Colombia more 2H SOT than DR Congo | 0.72 | YES | Model 76.37%; RULE7; λ ratio 3:1; CDR defensive block slight shade |
| Q2 | Colombia more 2H goals than DR Congo | 0.55 | YES_LEAN | Model 50.67%; COL 2 goals in 2H GD1; CDR 0 goals in 2H GD1 |
| Q3 | Penalty OR red card | 0.38 | NO_LEAN | Mariani 0.24 pens/game current; RULE7 upward; historical overpricing pattern |
| Q4 | Colombia more fouls than DR Congo | 0.42 | NO_LEAN | RULE_FOULS (CDR defends); JPN-TUN caveat (COL high-press = 11 fouls in GD1) |
| Q5 | Colombia win | 0.72 | YES | Model 73.25%, market 62.7%; RULE1 blended; RULE7 fires |
| Q6 | Colombia leads at HT | 0.52 | YES_LEAN | Model 50.67%; COL led HT in GD1; CDR compact 1H |
| Q7 | Match total ≤ 2 goals | 0.56 | YES_LEAN | Model 52.96%; market Under 2.5 at -155; CDR held Portugal to 1 SOT |
| Q8 | Colombia 5+ corners | 0.48 | NO_LEAN | GD1 baseline 4; compact CDR block adds corners; coin-flip |
| Q9 | Díaz score or assist | 0.48 | YES_LEAN | Market ~47%; GD1 goal+assist; RULE7 context |
| Q10 | Bakambu ≥1 SOT | 0.32 | NO | RULE15 full (<15% underdog); GD1 1 SOT adds minor uplift from 0.25 |

### Edge Ranking
1. **Q10 0.32 NO** — Bakambu: RULE15 full. CDR <15% win. Crowd likely ~0.43. Pattern: Semenyo (+15.14), Fajardo x2 all confirmed.
2. **Q5 0.72 YES** — Colombia win: model 73% vs market 63%. Significant YES above crowd.
3. **Q1 0.72 YES** — Colombia more 2H SOT: model 76.37%. CDR compact but COL dominates.
4. **Q3 0.38 NO** — Penalty/red card: historical overpricing pattern. Crowd likely ~0.42.
5. **Q7 0.56 YES** — ≤2 total goals: market Under -155 + CDR defensive excellence.
6. **Q2 0.55 YES** — Colombia more 2H goals: GD1 patterns align.
7. **Q4 0.42 NO_LEAN** — Colombia fouls: RULE_FOULS vs high-press caveat. Near coin-flip.
8. **Q9 0.48 YES_LEAN** — Díaz score or assist: market-anchored.
9. **Q8 0.48 NO_LEAN** — Colombia 5+ corners: coin-flip.
10. **Q6 0.52 YES_LEAN** — Colombia leads HT: coin-flip.

### Post-Match Results
*(To be filled when results come in)*

| Q | Our Est. | Crowd | Outcome | RBP | Beat? |
|---|----------|-------|---------|-----|-------|
| Q1 | 0.72 | — | — | — | — |
| Q2 | 0.55 | — | — | — | — |
| Q3 | 0.38 | — | — | — | — |
| Q4 | 0.42 | — | — | — | — |
| Q5 | 0.72 | — | — | — | — |
| Q6 | 0.52 | — | — | — | — |
| Q7 | 0.56 | — | — | — | — |
| Q8 | 0.48 | — | — | — | — |
| Q9 | 0.48 | — | — | — | — |
| Q10 | 0.32 | — | — | — | — |

**Total RBP:** —

### Key Watch Items (Pre-match flags)
- **DR Congo's defensive excellence**: Held Portugal to 1 SOT total. If they replicate this vs Colombia, Q1/Q7/Q2 all become less favorable for us. CDR's 5-3-2 is legitimate.
- **Colombia's SOT efficiency problem**: Only 4 SOT from 15 shots in GD1 (26.7%). They need volume to guarantee goals vs a compact block.
- **Díaz form**: Goal + assist + woodwork in GD1 makes Q9 (0.48) a well-supported estimate. Watch for whether Bakambu's GD1 1 SOT performance repeats (validates or challenges our RULE15 suppression).
- **JPN-TUN high-press caveat**: If Colombia fouls aggressively (like their GD1 11 fouls while attacking), Q4 (Colombia more fouls) could resolve YES despite our NO_LEAN.

---

## SUI-CAN — Switzerland vs Canada GD3
**Date:** 2026-06-24 | **Group B** | **Venue:** BC Place, Vancouver  
**Bash log:** `bash_logs/2026-06-24_SUI-CAN_match_analysis_bash_log.txt`  
**JSON:** `data/external_markets/sui_can_2026-06-24.json`

### Model Inputs
- **SUI Elo:** 1951.79 | **CAN Elo:** 1901.98 | **Elo diff:** 49.81
- **λ_SUI:** 1.2144 | **λ_CAN:** 1.0140 | **λ_total:** 2.2284
- **P(SUI win):** 42.65% | **P(Draw):** 31.02% ← **RULE8 FIRES** | **P(CAN win):** 26.32%

### Key Context
- **Both teams ALREADY QUALIFIED** (SUI 4pts, CAN 4pts). Group winner decider only.
- SUI needs WIN to top group. CAN needs only DRAW (better GD: +6 vs +3). Motivation asymmetry favors SUI aggression.
- Xhaka now at **Sunderland FC** (moved July 2025) — 0.09 SOT/90 in 2024-25 Bundesliga (3 SOT in 33 games)
- Jonathan David now at **Juventus** — hat trick (5 SOT) in GD2 vs Qatar (blowout context)
- Referee: **Ramon Abatti Abel (BRA)** — 4.85 YC/game career
- **Koné OUT** (broken leg from GD2)

### GD Evidence
| Match | Shots | SOT | Fouls | Score |
|---|---|---|---|---|
| SUI GD1 vs Qatar | 23 | 7 | 11 | 1-1 (conceded set-piece 90+1') |
| SUI GD2 vs Bosnia | 13 | 7 | 7 | 4-1 (0-0 at HT; all goals after 74') |
| CAN GD1 vs Bosnia | 13 | 4 | — | 1-1 (Larin 83') |
| CAN GD2 vs Qatar | 32 | 10 | 19 | 6-0 (David hat trick; Qatar 0 SOT) |

### Pre-Match Estimates
| Q | Question | Est | Direction | Key Driver |
|---|----------|-----|-----------|------------|
| Q1 | Canada more fouls than Switzerland | **0.63** | YES | CAN 19 fouls (GD2 attacking!); SUI 7 fouls GD2. λ-model 70% |
| Q2 | Switzerland 2+ offsides | **0.42** | NO_LEAN | Canada high press/high line; SUI fast wingers; λ≈1.3 |
| Q3 | 2+ total cards in 2H | **0.60** | YES | Abatti 4.85 YC/game; P(≥2 in 2H | λ=2.4)=64-70% |
| Q4 | BTTS AND total ≥3 goals | **0.30** | NO_LEAN | Model 31.54%; RULE8 shade; market-implied ~30-31% |
| Q5 | Penalty kick awarded | **0.33** | NO_LEAN | Abatti ~0.32/game; historical overpricing pattern |
| Q6 | Switzerland more 2H SOT than Canada | **0.48** | COIN-FLIP | Model 44.97%; RULE8 compresses to ~48% |
| Q7 | Switzerland win | **0.44** | YES_LEAN | Model 42.65%, market 40%; +3pp motivation asymmetry |
| Q8 | 2H total goals ≥2 | **0.30** | NO_LEAN | Model 30.62%; RULE8 cagey match |
| Q9 | Xhaka ≥1 SOT | **0.25** | STRONG NO (FLOOR) | 0.09 SOT/90; computed ~20%; FLOOR_0.25. Crowd ~0.40. |
| Q10 | Jonathan David ≥1 SOT | **0.70** | YES | 2.0+ SOT/90 hist.; Swiss defense discount λ=1.5; crowd ~0.60 |

### Post-Match Results (Final score: Switzerland 2-1 Canada)
| Q | Submitted | Crowd | Outcome | RBP |
|---|-----------|-------|---------|-----|
| Q1 | 0.63 | 0.53 | NO | -9.59 |
| Q2 | 0.42 | 0.50 | NO | +9.88 |
| Q3 | 0.60 | 0.54 | NO | -3.71 |
| Q4 | 0.30 | 0.41 | YES | -11.74 |
| Q5 | 0.33 | 0.29 | NO | -0.61 |
| Q6 | 0.48 | 0.51 | NO | +5.27 |
| Q7 | 0.44 | 0.45 | YES | +1.16 |
| Q8 | 0.30 | 0.43 | YES | -14.28 |
| Q9 | 0.25 | 0.40 | NO | +13.40 |
| Q10 | 0.70 | 0.59 | NO | -11.34 |

**Total RBP: -21.56** | **Beat crowd: 4/10 (Q2, Q6, Q7, Q9)**

**Post-match learnings:**
- Q4 (BTTS+3+ goals) = YES in 2-1: RULE8 over-suppressed this. Both teams scored AND exact 3-goal match. Model 0.315 was closer to truth than our 0.30.
- Q8 (2H 2+ goals) = YES: Same over-suppression issue from RULE8. At least 2 second-half goals.
- Q10 (David SOT) = NO: Swiss defense (Akanji, Elvedi) suppressed David effectively. GD2 hat-trick vs 9-man Qatar was blowout context. Should discount more heavily vs quality opposition.
- Q9 (Xhaka SOT floor) = NO: Structural DM prior confirmed. +13.40 RBP, best result of match.
- Q1 (Canada fouls) = NO: Switzerland fouled more despite expected to be less press-intensive. In 2-1 match, winner can foul more while pressing after conceding.

---

## BIH-QAT — Bosnia and Herzegovina vs Qatar GD3
**Date:** 2026-06-24 | **Group B** | **Venue:** Lumen Field, Seattle  
**Bash log:** `bash_logs/2026-06-24_BIH-QAT_match_analysis_bash_log.txt`  
**JSON:** `data/external_markets/bih_qat_2026-06-24.json`

### Model Inputs
- **BIH Elo:** 1652.82 | **QAT Elo:** 1564.54 | **Elo diff:** 88.28
- **λ_BIH:** 1.3019 | **λ_QAT:** 0.9458 | **λ_total:** 2.2478
- **P(BIH win):** 47.60% | **P(Draw):** 29.76% ← **RULE8 FIRES** | **P(QAT win):** 22.63%
- **RULE7:** Does NOT fire (QAT 22.63% > 15%) — but market prices QAT at 12.6% (near threshold)

### Key Context
- **Both teams NEED to WIN**: A draw nearly eliminates both from 3rd-place advancement (8/12 3rd-place teams advance)
- **Muharemovic SUSPENDED** (BIH red card GD2) — Hadzikadunic replaces him at CB
- **Al Amin + Madibo BOTH SUSPENDED** (QAT red cards GD2) — significant Qatar personnel loss
- **Džeko DID NOT PLAY GD1** (shoulder injury). Started GD2 vs SUI: 0 goals, 0 SOT, 0.12 xG, YC 61'
- **FanDuel Džeko anytime scorer: -110** (implied 52% probability — market extremely bullish vs Qatar)
- Referee: **Jesus Valenzuela (VEN)** — fair, second WC; typical 3.5-4.0 YC/game
- **Market:** BIH -270 (~69.1% de-vigged), Draw +420 (~18.2%), QAT +650 (~12.6%)

### GD Evidence
| Match | Shots | SOT | Fouls | Score |
|---|---|---|---|---|
| BIH GD1 vs Canada | 8 | ~4 | — | 1-1 (Lukic 21'; Larin 78') — Džeko absent |
| BIH GD2 vs Switzerland | 5 | 3 | 18 | 1-4 (Mahmic 90+3'; all SUI goals after 74') |
| QAT GD1 vs Switzerland | 6 | 3 | 12 | 1-1 (Khoukhi 90+4') — Qatar 0 offsides! |
| QAT GD2 vs Canada | 2 | 0 | ~1 | 0-6 (David hat trick; Qatar 2 red cards) |

### Pre-Match Estimates
| Q | Question | Est | Direction | Key Driver |
|---|----------|-----|-----------|------------|
| Q1 | BIH more 2H corners than Qatar | **0.58** | YES_LEAN | BIH dominates → more attacking pressure; model 51.95% + market BIH-dominant |
| Q2 | BIH more 2H goals than Qatar | **0.42** | NO_LEAN | RULE8 (draw 29.76%) shade; model P(BIH>QAT 2H goals) ≈ 37-40% |
| Q3 | Qatar more 2H SOT than Bosnia | **0.22** | STRONG NO | Qatar 0 SOT in GD2; model 28%; market QAT 12.6% win; GD1 Qatar 0 offsides |
| Q4 | Penalty OR red card | **0.38** | NO_LEAN | Valenzuela baseline; historical overpricing pattern |
| Q5 | Qatar more fouls than Bosnia | **0.55** | YES_LEAN | RULE_FOULS: QAT defends; QAT 12 fouls defending in GD1 |
| Q6 | Bosnia more cards than Qatar | **0.40** | NO_LEAN | Qatar defending = Qatar gets more cards |
| Q7 | [Assumed: Qatar more cards than Bosnia] | **0.52** | YES_LEAN | Qatar defending role + GD2 red card history |
| Q8 | Qatar 2+ offsides | **0.25** | STRONG NO (FLOOR) | Qatar **0 offsides in GD1**; barely attacks; FLOOR_0.25 |
| Q9 | Bosnia win | **0.62** | YES | Model 47.60%, market 69.1%; both need win = open match |
| Q10 | Match ≤2 total goals | **0.52** | COIN-FLIP | Model 60.99%, market 50% (Over 2.5 at +100); both teams attacking |
| Q11 | Džeko ≥1 SOT | **0.70** | YES | Market -110 scorer (~52%) → implied SOT ~73%; starter vs Qatar's 0-SOT-allowed defense |

⚠️ **Q6 and Q7 appear to be DUPLICATES** in the question list ("Bosnia more cards than Qatar" × 2). One is likely "Qatar more cards than Bosnia." Confirm before submitting.

### Post-Match Results
| Q | Submitted | Crowd | Outcome | RBP |
|---|-----------|-------|---------|-----|
| Q1 | 0.58 | — | — | — |
| Q2 | 0.42 | — | — | — |
| Q3 | 0.22 | — | — | — |
| Q4 | 0.38 | — | — | — |
| Q5 | 0.55 | — | — | — |
| Q6 | 0.40 | — | — | — |
| Q7 | 0.52 | — | — | — |
| Q8 | 0.25 | — | — | — |
| Q9 | 0.62 | — | — | — |
| Q10 | 0.52 | — | — | — |
| Q11 | 0.70 | — | — | — |

**Total RBP:** — | **Beat crowd:** — /11

### Key Watch Items (Pre-match flags)
- **Q3 STRONG NO**: Qatar more 2H SOT than Bosnia? Qatar had 0 SOT total in GD2 vs Canada. They don't shoot. Crowd will be ~0.38; we're at 0.22.
- **Q8 FLOOR**: Qatar 0 offsides in GD1 vs SUI (90 min). They don't run in behind at all. FLOOR_0.25.
- **Q11 Džeko**: He had 0 SOT in GD2 vs Switzerland but was facing a real defense. Market says -110 to SCORE vs Qatar. Very high SOT probability.
- **Q6/Q7 DUPLICATE**: Flag to user before submission. One must be "Qatar more cards than Bosnia."
- **Both teams must win context**: Reduces effectiveness of RULE8 (draw less likely than model suggests). Match should be open and attacking.

---

## SCO-BRA — Scotland vs Brazil GD3
**Date:** 2026-06-24 | **Group C** | **Venue:** Hard Rock Stadium, Miami  
**Bash log:** `bash_logs/2026-06-24_SCO-BRA_match_analysis_bash_log.txt`  
**JSON:** `data/external_markets/sco_bra_2026-06-24.json`

### Model Inputs
- **BRA Elo:** 2068.63 | **SCO Elo:** 1852.15 | **Elo diff:** 216.48
- **λ_BRA:** 1.6420 | **λ_SCO:** 0.7500 | **λ_total:** 2.3919
- **P(BRA win):** 63.89% | **P(Draw):** 23.05% | **P(SCO win):** 13.06% ← **RULE7 FIRES**

### Key Context
- **Group C:** Brazil 4pts, Morocco 4pts, Scotland 3pts, Haiti 0pts (eliminated)
- **Scotland SURVIVAL MATCH** — needs win or draw. This overrides standard RULE15 suppression for McTominay (he MUST get forward; use 0.50 not 0.25-0.35)
- **Brazil** can afford a draw; want to win for group top spot. **Raphinha OUT** (hamstring)
- **Brazil WC goals pattern:** ALL 4 goals scored in 1H (23', 32', 36', 45+3'). 0 second-half goals — artifact of leads.
- **McTominay (Napoli):** 4 shots, 0 SOT in 2 WC matches; BUT 1.0 SOT/90 at club. Bet365: 11-10 (~52%).
- **Referee:** Cesar Ramos (Mexico) — 4.0 YC/game WC average

### GD Evidence
| Match | Shots | SOT | Fouls | Score |
|---|---|---|---|---|
| SCO GD1 vs Haiti | 9 | 2 | 21 | 1-0 (McGinn 28') |
| SCO GD2 vs Morocco | 6 | 0 | ~11 | 0-1 (conceded 2nd min) |
| BRA GD1 vs Morocco | 12 | 5 | — | 1-1 (Vinicius 32' 1H) |
| BRA GD2 vs Haiti | 7 | 4 | 13 | 3-0 (all 1H: 23'/36'/45+3') |

### Pre-Match Estimates
| Q | Question | Est | Direction | Key Driver |
|---|----------|-----|-----------|------------|
| Q1 | Brazil more 2H SOT than Scotland | **0.70** | YES | Model 66.68%; SCO avg 0-1 SOT/game; survival = counter space |
| Q2 | Scotland 2+ offsides | **0.32** | NO (near floor) | Model ~17%; floor zone; survival attacking adjustment |
| Q3 | Scotland scores first AND Brazil 2H goal | **0.13** | STRONG NO | Compound: ~12-17%; no floor on scenario questions |
| Q4 | Brazil more corners than Scotland | **0.78** | YES | Model 82%; BRA possession; SCO got 2 corners in GD2 |
| Q5 | Scotland ≥1 goal | **0.45** | NO_LEAN | Model 53%, market 37.5% (BTTS No -165); survival uplift |
| Q6 | 3+ total goals | **0.52** | YES_LEAN | Market Over 2.5 at -126; survival = open match |
| Q7 | Brazil score in 2H | **0.62** | YES | 0 WC 2H goals = artifact of 3-0 lead; vs fighting SCO different |
| Q8 | 4+ total cards | **0.62** | YES | Ramos 4.0 WC avg + Scotland physical (21 fouls GD1) |
| Q9 | McTominay ≥1 SOT | **0.50** | COIN-FLIP | Market 52%; Napoli 1.0 SOT/90; survival overrides RULE15 |
| Q10 | Brazil score in 1H | **0.62** | YES | 4/4 WC goals in 1H; Scotland conceded 2nd min vs Morocco |

### Post-Match Results (Final score: Scotland 0-3 Brazil)
| Q | Submitted | Crowd | Outcome | RBP |
|---|-----------|-------|---------|-----|
| Q1 | 0.70 | 0.71 | NO | +3.93 |
| Q2 | 0.32 | 0.42 | NO | +9.65 |
| Q3 | 0.13 | 0.20 | NO | +4.49 |
| Q4 | 0.78 | 0.72 | NO | -7.83 |
| Q5 | 0.45 | 0.44 | NO | +1.86 |
| Q6 | 0.52 | 0.54 | YES | +0.16 |
| Q7 | 0.62 | 0.69 | YES | -3.33 |
| Q8 | 0.62 | 0.44 | NO | -16.78 |
| Q9 | 0.50 | 0.43 | YES | +10.39 |
| Q10 | 0.62 | 0.64 | YES | +0.22 |

**Total RBP: +2.75** | **Beat crowd: 7/10 (Q1, Q2, Q3, Q5, Q6, Q9, Q10)**

**Post-match learnings:**
- Q4 (Brazil more corners) = NO despite 3-0 win: Third consecutive "dominant team fewer corners" result (after MEX-KOR, CZE-MEX). CORNERS ARE NOT PREDICTABLE FROM MATCH DOMINANCE. Near-coin-flip is the correct prior for any corner dominance question.
- Q1 (Brazil more 2H SOT) = NO: Brazil likely scored all 3 in 1H and coasted; Scotland chased in 2H generating more 2H SOT. Blowout structure inverts 2H SOT comparison.
- Q8 (4+ cards) = NO: Even high-card Ramos couldn't manufacture cards in a decided 3-0 win. Blowout = less tension = fewer cards. Over-weighted historical ref rate vs match context.
- Q9 (McTominay SOT) = YES: Survival-match RULE15 override fully validated (+10.39). Must-win context overrides underdog forward suppression.

---

## MAR-HAI — Morocco vs Haiti GD3
**Date:** 2026-06-24 | **Group C** | **Venue:** Mercedes-Benz Stadium, Atlanta  
**Bash log:** `bash_logs/2026-06-24_MAR-HAI_match_analysis_bash_log.txt`  
**JSON:** `data/external_markets/mar_hai_2026-06-24.json`

### Model Inputs
- **MAR Elo:** 1984.85 | **HAI Elo:** 1717.23 | **Elo diff:** 267.62
- **λ_MAR:** 1.8012 | **λ_HAI:** 0.6837 | **λ_total:** 2.4849
- **P(MAR win):** 69.77% | **P(Draw):** 19.90% | **P(HAI win):** 10.33% ← **RULE7 FIRES**

### Key Context
- **Morocco** already qualified. Playing for group position. No urgency.
- **Haiti** ELIMINATED. Dead rubber. 0 goals in 2 WC matches.
- **Nazon (Haiti CF):** DOUBTFUL, unused sub in GD1, 0 WC minutes. RULE15 + FLOOR = 0.25.
- **Saibari (Morocco):** Scored in 2nd and 21st minute in GD1/GD2. FanDuel -110 anytime scorer.
- **Referee:** Danny Makkelie (Netherlands) — 3.40 YC/game career, 0.33 pens/game
- **Haiti's corner surprise:** Haiti averaged 4 corners/game in GD1 and GD2 (matched Brazil in GD2!). Makes Q2 (HT corners) less certain.

### GD Evidence
| Match | Shots | SOT | Fouls | Score |
|---|---|---|---|---|
| MAR GD1 vs Brazil | 14 | 3 | 16 | 1-1 (Saibari 21') |
| MAR GD2 vs Scotland | 12 | 2 | 8 | 1-0 (Saibari 2') |
| HAI GD1 vs Scotland | 13 | 2 | 23 | 0-1 |
| HAI GD2 vs Brazil | 7 | 3 | 14 | 0-3 |

### Pre-Match Estimates
| Q | Question | Est | Direction | Key Driver |
|---|----------|-----|-----------|------------|
| Q1 | Haiti more fouls than Morocco | **0.65** | YES | RULE_FOULS + Haiti 18.5/match vs Morocco 12/match |
| Q2 | Haiti more HT corners than Morocco | **0.35** | NO_LEAN | Morocco dominates but Haiti gets 4 corners/game regardless |
| Q3 | Haiti more cards than Morocco | **0.72** | YES | Haiti 4 YC in 2 games vs Morocco 1 YC — very clear |
| Q4 | Morocco more 2H SOT than Haiti | **0.70** | YES | Model 72.75%; Morocco quality attack; dead rubber Haiti |
| Q5 | 4+ total SOT in 2H | **0.45** | NO_LEAN | Model proxy 51%, evidence-calibrated ~25-40%; Morocco may ease |
| Q6 | Penalty OR red card | **0.38** | NO_LEAN | Makkelie 0.33/game; 0 pens in 4 combined prior matches |
| Q7 | Morocco win | **0.80** | YES | Market -600 (85.7%); dead rubber Haiti; blend → 0.80 |
| Q8 | Morocco score in 1H | **0.70** | YES | Scored 21' (GD1) and 2' (GD2); Haiti weakest defense yet |
| Q9 | Nazon ≥1 SOT | **0.25** | STRONG NO (FLOOR) | RULE15 + doubtful + 0 WC minutes; computed ~11% |
| Q10 | Haiti score in 2H | **0.25** | STRONG NO | 0 goals in 2 WC games; Morocco solid defense; model-market blend |

### Post-Match Results (Final score: Morocco 4-2 Haiti)
| Q | Submitted | Crowd | Outcome | RBP |
|---|-----------|-------|---------|-----|
| Q1 | 0.65 | 0.61 | YES | +5.47 |
| Q2 | 0.35 | 0.25 | NO | -3.62 |
| Q3 | 0.72 | 0.55 | YES | +13.91 |
| Q4 | 0.70 | 0.72 | YES | +1.03 |
| Q5 | 0.45 | 0.62 | YES | -13.51 |
| Q6 | 0.38 | 0.35 | NO | -0.13 |
| Q7 | 0.80 | 0.80 | YES | +1.66 |
| Q8 | 0.70 | 0.66 | YES | +4.22 |
| Q9 | 0.25 | 0.28 | YES | -1.23 |
| Q10 | 0.25 | 0.28 | NO | +3.27 |

**Total RBP: +11.07** | **Beat crowd: 6/10 (Q1, Q3, Q4, Q7, Q8, Q10)**

**Post-match learnings:**
- Morocco 4-2 Haiti: Much higher scoring than model expected. Dead rubber matches can be very open (both teams at reduced defensive intensity).
- Q9 (Nazon SOT) = YES: Despite being doubtful with 0 WC minutes, Nazon played and got a SOT. RULE15 floor (0.25) minimized loss (-1.23). Lesson: in dead rubber, doubtful players may be given minutes freely.
- Q5 (4+ 2H SOT) = YES and we missed (-13.51): In a 4-2 open match, 2H was active for both sides. Our evidence calibration from Morocco's 2-SOT GD2 game was too conservative for a dead-rubber context.
- Q3 (Haiti more cards) = YES, +13.91: Clear structural signal validated. RULE_FOULS + card differential holding up across n=2+ dead rubber games.
- Q10 (Haiti score in 2H) = NO: Both Haiti goals in 1H (4-2 final). Haiti apparently sat back in 2H after scoring early. Our 0.25 was correct despite 4-2 final score.

---

## CZE-MEX — Czechia vs Mexico GD3
**Date:** 2026-06-24 | **Group A** | **Venue:** Estadio Azteca, Mexico City (quasi-home for Mexico)  
**Bash log:** `bash_logs/2026-06-24_CZE-MEX_match_analysis_bash_log.txt`  
**JSON:** `data/external_markets/cze_mex_2026-06-24.json`

### Model Inputs
- **CZE Elo:** 1806.40 | **MEX Elo:** 1984.79 | **Elo diff:** −178.39 (Mexico favored)
- **λ_CZE:** 0.8035 | **λ_MEX:** 1.5326 | **λ_total:** 2.3361
- **P(CZE win):** 18.51% | **P(Draw):** 27.57% ← **RULE8 FIRES** | **P(MEX win):** 53.92%

### Key Context
- **Group A standings**: MEX 6pts (qualified, rotating heavily), CZE 1pt (MUST WIN)
- **Mexico rotation**: Jiménez + Quiñones rested. Ochoa (40yo) starting in goal. B-squad XI.
- **Azteca effect**: 80,000+ Mexican fans at home ground — psychological pressure on CZE beyond model
- **Czechia survival**: Needs WIN to reach 4pts (3rd-place contention). A draw = eliminated.
- **Schick WC form**: 1 SOT in 154 WC minutes (very quiet). Hlozek also shooting (SOT -132 market)
- **Referee:** Yael Falcón Pérez (Argentina) — card rate not confirmed

### GD Evidence
| Match | CZE/RSA shots | SOT | Key fact |
|---|---|---|---|
| KOR 2-1 CZE (GD1) | 7 shots | 4 SOT | Krejčí scored 59' (2H); Schick subbed 64' (5.9/10) |
| CZE 1-1 RSA (GD2) | 14 shots | 3 SOT | Only 32% possession vs RSA; Sadílek 6' goal |
| MEX 2-0 RSA (GD1) | 16 shots | 4 SOT | Quiñones 9', Jiménez 67' |
| MEX 1-0 KOR (GD2) | 4 corners | — | KOR got 4 corners vs MEX 3 — corner advantage volatile! |

### Rules Applied
- **RULE8 FIRES** (draw 27.57%) — cagier match, fewer goals. Confirmed in MEX-KOR (1-0, 1 total goal)
- **RULE_FOULS**: CZE defends → CZE fouls more (Q1 YES)
- **MEX-KOR CORNER PRECEDENT**: KOR got MORE corners than MEX in GD2 — corners volatile (Q4 near coin-flip)
- **ROTATION_EFFECT**: CZE win prob rises from model 18.5% → adjusted 30%
- **AZTECA_EFFECT**: Slight downward on CZE win vs what rotation alone suggests

### Pre-Match Estimates
| Q | Question | Est | Direction | Crowd≈ | Edge | Key Driver |
|---|----------|-----|-----------|--------|------|------------|
| Q1 | CZE more fouls than MEX | **0.62** | YES | 0.59 | +0.03 | RULE_FOULS: CZE underdog defends |
| Q2 | MEX 2+ offsides | **0.58** | YES_LEAN | 0.56 | +0.02 | Model 0.845, RULE8 shrink, rotation |
| Q3 | CZE more 2H SOT than MEX | **0.28** | NO_LEAN | 0.38 | −0.10 | Model 0.189; CZE survival + rotation offset ← BEST EDGE |
| Q4 | MEX more corners | **0.52** | YES_LEAN | 0.53 | −0.01 | MEX-KOR: KOR got more corners; volatile stat |
| Q5 | BTTS AND 3+ goals | **0.32** | NO_LEAN | 0.40 | −0.08 | RULE8; MEX-KOR precedent (1-0) |
| Q6 | CZE win | **0.30** | NO_LEAN | 0.39 | −0.09 | Model 0.185; rotation uplift; Azteca offset |
| Q7 | CZE score in 2H | **0.38** | NO_LEAN | 0.44 | −0.06 | Model 0.331; survival 2H push; Krejčí scored 59' GD1 |
| Q8 | 4+ total cards | **0.45** | NO_LEAN | 0.48 | −0.03 | CZE desperation = physical; ref unknown |
| Q9 | Patrik Schick ≥1 SOT | **0.48** | NO_LEAN | 0.50 | −0.02 | 1 SOT in 154 WC min; Hlozek competes; RULE8 |

### Post-Match Results (Final score: Czechia 0-3 Mexico)
⚠️ **Q9 SUBMISSION ERROR**: Submitted 0.72 instead of 0.48 for Schick SOT. Accidentally used Son's RSA-KOR estimate. Outcome NO → -25.42 RBP catastrophe. Correct estimate (0.48) would have earned positive RBP vs crowd's 0.47.
| Q | Submitted | Crowd | Outcome | RBP |
|---|-----------|-------|---------|-----|
| Q1 | 0.62 | 0.56 | NO | -5.25 |
| Q2 | 0.58 | 0.50 | NO | -6.51 |
| Q3 | 0.28 | 0.38 | NO | +9.02 |
| Q4 | 0.52 | 0.54 | NO | +4.72 |
| Q5 | 0.32 | 0.37 | NO | +5.66 |
| Q6 | 0.30 | 0.27 | NO | +0.31 |
| Q7 | 0.38 | 0.44 | NO | +6.88 |
| Q8 | 0.45 | 0.47 | NO | +4.58 |
| Q9 | **0.72** ⚠️ | 0.47 | NO | **-25.42** ⚠️ |

**Total RBP: -6.01** | **Beat crowd: 6/9 (Q3, Q4, Q5, Q6, Q7, Q8)** | *Without Q9 error: estimated ~+19 RBP*

**Post-match learnings:**
- Q9 SUBMISSION ERROR cost ~-30 RBP swing. PROCESS FIX: when submitting back-to-back matches, verify question text matches estimate before each entry. Never copy last estimate from prior match to next match.
- Q4 (MEX more corners) = NO in 3-0 Mexico win: Now 3/3 data points where dominant team wins but does NOT get more corners. Corner prediction is close to random regardless of dominance.
- Q1 (CZE more fouls) = NO despite RULE_FOULS: Mexico fouled more in their 3-0 win. RULE10 analog applies: winning dominant team presses/fouls more, especially in a big win. Consider moderating RULE_FOULS for mismatches.
- Q3, Q5, Q6, Q7, Q8 all beat crowd: The core structural NO-leans for CZE vs Mexico were all correct. The model's core logic was sound; only the submission error damaged results.

---

## RSA-KOR — South Africa vs South Korea GD3
**Date:** 2026-06-24 | **Group A** | **Venue:** Estadio BBVA, Monterrey  
**Bash log:** `bash_logs/2026-06-24_RSA-KOR_match_analysis_bash_log.txt`  
**JSON:** `data/external_markets/rsa_kor_2026-06-24.json`

### Model Inputs
- **RSA Elo:** 1663.32 | **KOR Elo:** 1879.98 | **Elo diff:** −216.66 (South Korea favored)
- **λ_RSA:** 0.7497 | **λ_KOR:** 1.6425 | **λ_total:** 2.3922
- **P(RSA win):** 15.69% | **P(Draw):** 25.50% ← **RULE8 FIRES (barely)** | **P(KOR win):** 58.81%

### Key Context
- **RSA SUSPENSIONS**: Teboho Mokoena (DM, 2 yellows) + Themba Zwane (red GD1) — BOTH OUT
- **KOR needs only a DRAW** to advance as 2nd in group — less desperate than RSA
- **RSA MUST WIN** + need other results — fully desperate
- **Son GD1 data**: 6 shots, 1 SOT in 69 min (active but low SOT conversion). Expected full 90.
- **RSA GD2 surprise**: 17 shots, 4 SOT vs Czechia with 68% possession — better than Elo suggests
- **Referee:** Facundo Tello (Argentina) — HIGH CARD RATE (infamous 10-red-card match)

### GD Evidence
| Match | Shots | SOT | Key fact |
|---|---|---|---|
| RSA GD1 vs MEX (0-2) | distorted | — | RSA played 9 men from 49'; reds: Sithole, Zwane |
| RSA GD2 vs CZE (1-1) | 17 shots | 4 SOT | 68% poss! Mokoena pen 83'. Better than Elo. |
| KOR GD1 vs CZE (2-1) | 15 shots | 6 SOT | Son: 6 shots, 1 SOT in 69min; comeback 67', 80' |
| KOR GD2 vs MEX (0-1) | — | — | GK error; 58% poss, xG 0.67 vs MEX 0.48. Son: 57'. |

### Rules Applied
- **RULE8 FIRES (barely)** — draw 25.50%: mild shrink of attacking props
- **RULE7 does NOT fire** — RSA 15.69% (borderline, just above 15%)
- **RULE_FOULS**: RSA defends → fouls more. MODERATED: Mokoena (main DM) suspended
- **RULE15 for Son**: Does NOT apply. Son is on the DOMINANT team (58.8% win prob). Today ≠ MEX-KOR where KOR was losing.
- **TELLO_EFFECT**: Card-heavy ref → Q2 (KOR card in 2H) elevated
- **RSA_SUSPENSIONS**: Reduces BTTS (weaker RSA attack), RSA fouls (Mokoena gone), but RSA must-win = still attacking

### Pre-Match Estimates
| Q | Question | Est | Direction | Crowd≈ | Edge | Key Driver |
|---|----------|-----|-----------|--------|------|------------|
| Q1 | KOR 2+ offsides | **0.70** | YES | 0.64 | +0.06 | Model 0.871; RSA depleted midfield → KOR runs free |
| Q2 | KOR card in 2H | **0.52** | YES_LEAN | 0.53 | −0.01 | Tello high-card ref; Lee Kang-in on 1Y; RSA physical |
| Q3 | BTTS AND 3+ goals | **0.30** | NO_LEAN | 0.39 | −0.09 | RULE8; RSA missing Mokoena/Zwane; KOR defense (Kim Min-jae) ← BEST EDGE |
| Q4 | KOR more 2H SOT than RSA | **0.72** | YES | 0.65 | +0.07 | Model 0.844; Son full 90; RSA midfield gap |
| Q5 | RSA more fouls than KOR | **0.60** | YES | 0.57 | +0.03 | RULE_FOULS; moderated (Mokoena suspended) |
| Q6 | HT tied | **0.40** | NO_LEAN | 0.45 | −0.05 | Model 0.403; KOR likely scores early vs depleted RSA |
| Q7 | RSA 3+ SOT | **0.40** | NO_LEAN | 0.45 | −0.05 | RSA had 4 SOT in GD2 (CAN do it); but missing creators |
| Q8 | Appollis ≥1 SOT | **0.38** | NO_LEAN | 0.44 | −0.06 | Near-RULE15; KOR defense; but must-win = Appollis gets forward |
| Q9 | Son ≥1 SOT | **0.72** | YES | 0.65 | +0.07 | GD1: 1 SOT in 69min (YES); full 90; NO RULE15; weaker RSA |

### Post-Match Results (Final score: South Africa 1-0 South Korea — MAJOR UPSET, model 15.7% RSA win)
Platform note: Platform renumbered Q6-Q10. Our Q10 (RSA win) = platform Q6; our Q6-Q9 = platform Q7-Q10.
| Q | Question | Submitted | Crowd | Outcome | RBP |
|---|----------|-----------|-------|---------|-----|
| Q1 | KOR 2+ offsides | 0.70 | 0.52 | NO | -19.17 |
| Q2 | KOR card in 2H | 0.52 | 0.55 | YES | -0.70 |
| Q3 | BTTS AND 3+ goals | 0.30 | 0.35 | NO | +5.66 |
| Q4 | KOR more 2H SOT | 0.72 | 0.60 | YES | +10.81 |
| Q5 | RSA more fouls | 0.60 | 0.57 | NO | -1.77 |
| Q6 | HT tied | 0.40 | 0.43 | YES | -2.18 |
| Q7 | RSA 3+ SOT | 0.40 | 0.52 | YES | -10.69 |
| Q8 | Appollis ≥1 SOT | 0.38 | 0.40 | YES | +0.29 |
| Q9 | Son ≥1 SOT | 0.72 | 0.56 | NO | -16.33 |
| Q10 | RSA win | 0.17 | 0.22 | YES | -5.47 |

**Total RBP: -39.56** | **Beat crowd: 3/10 (Q3, Q4, Q8)**

**Post-match learnings:**
- RSA 1-0 KOR UPSET: Model's 15.7% RSA win happened. Our 0.17 estimate was the correct credible floor. No model can reliably predict 1-in-6 upsets. Structural factors (suspensions) were partially offset by RSA's must-win intensity.
- Son SOT (Q9) = NO: Son went 0 SOT even as the DOMINANT team's star. This is the 3rd consecutive WC game where Son fails to register SOT despite high shot volume in GD1 (6 shots, 1 SOT at 69min). His low SOT-per-shot conversion rate is a structural trait, not match-specific. Son SOT estimates should use 25-35% share rather than 38%.
- KOR 2+ offsides (Q1) = NO: -19.17 RBP our worst result today. Model 0.871, our 0.70 — both very wrong. RSA's low-block defending (not a high line) eliminates most offside trap opportunities. Dominant team running into a deep block does NOT generate high offside counts. This is a NEW RULE candidate: when expected loser plays a deep defensive block (MUST DEFEND), suppress dominant team's offside estimate significantly.
- RSA 3+ SOT (Q7) = YES: Even with Mokoena/Zwane absent, RSA in a must-win match had 3+ SOT. Must-win context drives shot volume regardless of suspensions. Our 0.40 was actually close (crowd had 0.52 and was more right).
- RULE_FOULS misfired (Q5): RSA more fouls = NO. When RSA ended up winning and controlling the match, the fouls pattern inverted (KOR chased and fouled more). RULE_FOULS applies to the expected underdog defending, but if they end up controlling, it flips.

---

## 2026-06-25 GD3 — Germany vs Ecuador & Curacao vs Ivory Coast (PRE-MATCH)

**Date:** 2026-06-25 (match starts ~20:00 CDT)  
**Bash log:** `bash_logs/2026-06-25_GER-ECU_CUR-IVC_bash_log.txt`  
**JSON files:** `ger_ecu_2026-06-25.json`, `cur_civ_2026-06-25.json`

### Why we did this

Applied the WINNING TRAIL methodology identified from the win/loss comparison:
- Verified ESPN boxscores (n=2 per team, WC2026 GD1+GD2)
- First-pass Poisson GLM + Skellam on ESPN averages
- Market-calibrate lambdas against Smarkets FTR
- Submit near-raw (≤5pp adjustment), no stacked narrative layers
- Apply RULE_OFFSIDE_DEFENSIVE_SHAPE (learned from RSA-KOR -19.17)

### Data sources

**ESPN API boxscores (verified, n=2 each):**
| Team | vs | Fouls | SOT | Shots | Offsides | YC |
|------|-----|-------|-----|-------|----------|----|
| GER | CUR (7-1W) | 18 | 12 | 26 | 0 | 0 |
| GER | IVC (2-1W) | 5 | 7 | 16 | 0 | 0 |
| ECU | IVC (GD1 L) | 13 | 1 | 12 | 0 | 1 |
| ECU | CUR (0-0D) | 7 | 15 | 27 | 1 | 1 |
| IVC | ECU (GD1 W) | 10 | 4 | 15 | 0 | 3 |
| IVC | GER (1-2L) | 7 | 2 | 9 | 1 | 0 |
| CUR | GER (1-7L) | 11 | 2 | 8 | 1 | 0 |
| CUR | ECU (0-0D) | 10 | 3 | 10 | 2 | 5 |

ESPN corners return '?' for all WC2026 matches — no corner data available.

**Elo:** GER=1954, ECU=1864, IVC=1728, CUR=1453 (eloratings.net)

**Smarkets (event 45086929 GER-ECU, 45086950 CUR-IVC):**
- GER-ECU FTR: GER=61.6% / Draw=19.6% / ECU=18.4%
- GER-ECU BTTS YES=45.7%, OU2.5 UNDER=66.5%, OVER=33.9%
- CUR-IVC FTR: IVC=83.7% / Draw=11.1% / CUR=5.0%
- CUR-IVC BTTS YES=40.3%, OU2.5 OVER=66.7%, OU3.5 OVER=45.3%

### Poisson model
log(λ) = 0.10408 + 0.0018099 × elo_diff. Market-calibrated effective diff: GER-ECU=245, CUR-IVC=480.
- λ_GER=1.729, λ_ECU=0.712 | λ_IVC=2.645, λ_CUR=0.466

Key Skellam results:
- P(ECU more fouls than GER) = 33.3% → submit 0.35
- P(IVC more fouls than CUR) = 28.2% → submit 0.28
- P(GER 2H goals > ECU 2H goals) = 46.1% (P(0-0 2H) = 39.3%) → submit 0.46
- P(ECU ≥2 offsides) = 9.0% raw → cap 0.10 (GER deep block rule)
- P(IVC first 2H goal) = 71.1% → discount to 0.65

### Final submissions

**GER-ECU:**
| Q | Text | Estimate | Dir |
|---|------|----------|-----|
| Q1 | Both teams ≥1 SOT at HT | **0.85** | YES |
| Q2 | Ecuador more fouls than Germany | **0.35** | NO |
| Q3 | Ecuador more 2H corners than Germany | **0.43** | NO |
| Q4 | Germany more 2H goals than Ecuador | **0.46** | NO lean |
| Q5 | Germany more 2H SOT than Ecuador | **0.50** | TOSS-UP |
| Q6 | Penalty OR Red Card shown | **0.28** | NO |
| Q7 | Ecuador caught offside ≥2 times | **0.10** | NO strong |
| Q8 | BTTS + 3+ total goals | **0.22** | NO |
| Q9 | Ecuador scores ≥1 goal | **0.50** | TOSS-UP |
| Q10 | Match has ≤2 total goals | **0.65** | YES |

**CUR-IVC:**
| Q | Text | Estimate | Dir |
|---|------|----------|-----|
| Q1 | Curaçao caught offside ≥2 times | **0.37** | NO lean |
| Q2 | Ivory Coast more fouls than Curaçao | **0.28** | NO |
| Q3 | Ivory Coast scores first 2H goal | **0.65** | YES |
| Q4 | 2H more goals than 1H goals | **0.38** | NO |
| Q5 | Curaçao more 2H SOT than Ivory Coast | **0.35** | NO |
| Q6 | Curaçao more cards than Ivory Coast | **0.63** | YES |
| Q7 | Curaçao scores ≥1 goal | **0.40** | NO lean |
| Q8 | Ivory Coast ≥5 corners | **0.50** | TOSS-UP |
| Q9 | Leandro Bacuna ≥1 SOT | **0.26** | NO |
| Q10 | Ibrahim Sangaré ≥1 SOT | **0.35** | NO lean |

### Strongest signals
1. **GER-ECU Q7: ECU ≥2 offsides = 0.10** — ECU avg λ=0.5 + GER deep block rotation. Applying RSA-KOR lesson exactly.
2. **GER-ECU Q10: UNDER 2.5 = 0.65** — Market 66.5%, ECU 0 goals in WC2026, GER rotating.
3. **CUR-IVC Q6: CUR more cards = 0.63** — 5 YC from CUR in GD2 survival match; pattern repeating.
4. **CUR-IVC Q2: IVC more fouls = 0.28** — CUR avg 10.5 vs IVC 8.5; strong structural NO.

**Post-match results (fill when available):**
GER-ECU: [ TBD ]
CUR-IVC: [ TBD ]

---
