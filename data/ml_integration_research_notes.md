# ML Integration Research Notes — MEX vs RSA, ~15-Hour Window

**Context.** Existing pipeline: PIT Elo (`elo.py`) → 3-parameter Poisson GLM on
goals (`poisson_goals.py`) → Dixon-Coles scoreline grid (`dixon_coles.py`) →
match-result probabilities. Backtest on ~49,400 matches found a **systematic,
roughly logit-constant ~+0.25 to +0.35 calibration gap** (actual home-win rate
higher than predicted), present for both `neutral=TRUE` and `neutral=FALSE`
matches. A simple Platt-scaling recalibration (1-2 parameters, fit on
held-out backtest data) was the leading time-feasible fix already identified.
Question: can/should an ML model be added in the remaining ~15 hours?

---

## TL;DR — Ranked Recommendations (read this first)

**1. (DO THIS — almost certainly feasible, highest expected payoff per hour)
Implement Hvattum & Arntzen's (2010) ordered-logit step on top of your
existing Elo-diff + home/neutral covariates, fit via `statsmodels`'
`OrderedModel` (proportional-odds / ordered logit, the same family as R's
`MASS::polr()`).** This is genuinely the cleanest "ML-ish" upgrade for
tonight: it is a ~30-50 line addition, trains in seconds on 49k rows, slots
directly into your existing walk-forward backtest harness (just swap the
"Poisson→DC→H/D/A" step for "ordered-logit on [elo_diff, home_adv] →
H/D/A"), and — critically — **it is fit DIRECTLY against the
win/draw/loss outcomes you actually care about**, which by construction
removes the "fit goals, derive outcomes" mismatch that Hvattum & Arntzen
(2010, §4.3) identify as the structural reason Dixon-Coles-style pipelines
can show systematic outcome-level miscalibration. In their own backtest
(English football, 1993-2008, 30,524 matches), Elo-difference + ordered
logit *beat* uniform/historical-frequency baselines and Goddard's (2005)
50-100-covariate "kitchen sink" models on Brier/RPS/log-loss — i.e., a
single well-specified covariate fed through ordered logit can outperform
much richer feature sets fed through worse-specified outcome models. **Run
this in parallel with, not instead of, Platt scaling**: fit ordered logit on
an early holdout, Platt-scale on a later holdout, and compare RPS/Brier/
calibration-bucket tables for (a) Poisson+DC, (b) Poisson+DC+Platt, and (c)
Elo-diff ordered logit, all via your existing harness. Use whichever wins on
the held-out calibration table for tonight's MEX vs RSA prediction — but (b)
and (c) are both defensible "ML/statistical recalibration" deliverables, and
(c) has a stronger theoretical claim to be self-calibrating.

**2. (CONSIDER, TIME-PERMITTING — moderate payoff, moderate risk) Add 1-3
cheap, derivable-from-existing-data features to the ordered-logit (or
Poisson) design matrix**: an Elo-momentum term (e.g., `elo_diff_30d_change =
(elo_home_pre - elo_home_pre_30days_ago) - (elo_away analogue)`) and/or a
"ratings-reliability" proxy (`min(matches_played_to_date)` or `years_since_
team_entered_dataset`, interacted with `elo_diff`) — both directly
addressable from `elo_match_panel.csv` alone (no new API calls). These map
onto two literature-grounded ideas already in your `calibration_research_
notes.md`: the Glicko/TrueSkill "uncertainty/reliability" covariate (§2.1-2.2
of that doc) and FiveThirtyEight's MOV/momentum-style Elo updates. Each is a
1-2 column addition to a design matrix you already build — cheap if (1) is
done first and the harness plumbing is in place. **Do NOT add more than 2-3
features tonight**: with ~10-15k "effective" recency-weighted matches, every
extra feature meaningfully increases overfitting risk for a same-night fit
with no time for proper nested CV.

**3. (DO NOT DO TONIGHT — interesting but too risky) Gradient-boosted trees
(XGBoost/LightGBM/CatBoost).** The literature (Bunker & "Evaluating Soccer
Match Prediction Models," arXiv:2309.14807, 2024) shows CatBoost/XGBoost +
rich engineered ratings (pi-ratings, Berrar ratings, recency features) CAN
beat both Dixon-Coles and ordered logit — but only with (a) much richer
feature sets than you have time to engineer tonight, (b) careful
hyperparameter search across multiple validation folds, and (c) **mandatory
post-hoc Platt/isotonic recalibration**, because boosted trees have a
well-documented (Niculescu-Mizil & Caruana 2005) sigmoid-shaped miscalibration
that pushes probabilities away from 0/1 — meaning GBTs do NOT solve your
calibration problem "for free"; you'd still need the Platt-scaling step
afterward, on top of much more implementation/validation risk, for
(at best) a marginal accuracy gain over (1). With ~10-15k effective rows and
3 features, GBTs are also at meaningful risk of overfitting (rule-of-thumb
threshold for "don't bother with XGBoost" is often cited around 10k rows).
**Verdict: skip for tonight; revisit post-market as a multi-day project once
features from (2) exist and there's time for proper CV.**

**4. (DO NOT DO TONIGHT) Neural networks / deep learning, full Bayesian
rating systems (TrueSkill replacement), SIMEX/errors-in-variables correction
of `b2`.** All require either much more data infrastructure, much more
compute/validation time, or both. None offer a plausible same-night payoff
over (1)+(2), and several (esp. SIMEX) were already flagged as "overkill,
defer" in `calibration_research_notes.md`.

**Bottom line**: "integrating ML" most credibly and safely means (1) Elo-diff
→ ordered logit, run side-by-side with your planned Platt-scaling fix via the
existing backtest harness, with (2) as an optional, capped feature-engineering
add-on if time remains after (1) is validated. This gives you a defensible,
backtested, two-model comparison for the MEX vs RSA prediction within the
window, without taking on GBT/NN implementation and validation risk that the
literature says wouldn't even bypass the need for output recalibration.

---

## 1. What would "integrating ML" concretely mean here?

### 1.1 Multinomial / ordered logistic regression on outcomes — Hvattum & Arntzen (2010) §4.3

Already documented in your `research_notes.md` §4. Key points re-confirmed by
this research pass:

- **Hvattum, L.M. & Arntzen, H. (2010). "Using ELO ratings for match result
  prediction in association football." International Journal of Forecasting,
  26(3), 460-470.** ScienceDirect:
  https://www.sciencedirect.com/science/article/abs/pii/S0169207009001708
  - Single covariate `x = Elo_home - Elo_away` (+ optional home-advantage
    term), fit via proportional-odds ordered logit:
    `P(Away)=logistic(κ1-βx)`, `P(Draw)=logistic(κ2-βx)-logistic(κ1-βx)`,
    `P(Home)=1-logistic(κ2-βx)`.
  - Tested on 30,524 English top-4-division matches (1993/94-2007/08), 8
    seasons (14,927 matches) held out.
  - **Result**: Elo + ordered logit beat uniform baseline, historical
    frequency baseline, AND Goddard's (2005) 50/100-covariate kitchen-sink
    ordered logit models on quadratic loss (Brier) and log loss — but lost to
    bookmaker-implied probabilities. No method (incl. bookmaker odds) was
    reliably profitable net of margin.
  - **Why this matters for calibration**: by construction, ordered logit's
    parameters (`β`, `κ1`, `κ2`) are estimated by maximizing the likelihood of
    the *observed three-way outcomes* — the model is fit on exactly the
    quantity (H/D/A) you're trying to predict, and the cutpoints `κ1, κ2`
    absorb whatever the "baseline" home/draw/away split should be given `x=0`.
    This is structurally different from "fit goals via Poisson, derive H/D/A
    via Dixon-Coles," where the fitting objective (goal counts) is one step
    removed from the evaluation target (H/D/A), leaving room for the kind of
    systematic outcome-level gap you observed even when the goals-level model
    looks reasonable.

- **Is ordered logit "ML"?** By the broad definition used in this research
  area (e.g., Bunker & Susnjak's chapter, see §1.2) — "any supervised
  statistical learning method fit to predict an outcome from features" —
  **yes, ordered logistic regression is squarely within the ML literature's
  taxonomy** (it's discussed alongside XGBoost/CatBoost/neural nets as one
  point on a spectrum of "soccer match result prediction" methods, not
  excluded as "merely statistics"). Practically: it is also the simplest,
  fastest-to-validate option, and the one most likely to actually close your
  specific gap, because it directly targets the failure mode you diagnosed.

- **Would it close the gap better than Platt scaling?** Plausibly **yes, by
  a similar mechanism but estimated jointly rather than as a two-stage
  patch**: Platt scaling fits `logit(p_calibrated) = a*logit(p_model) + b` on
  top of the *already-derived* Dixon-Coles H/D/A probabilities — i.e., it can
  only correct a 1-D summary of whatever the Poisson+DC pipeline produces.
  Ordered logit on `elo_diff` (+ home_adv) instead **re-estimates the entire
  mapping from Elo-diff to H/D/A from scratch against the actual outcomes**,
  which can in principle fix issues that a 1-parameter rescaling of the
  Poisson+DC output cannot (e.g., if the *shape* of the Poisson+DC mapping
  from Elo-diff to P(home win) is wrong, not just its overall level/slope).
  That said: **if the gap really is "constant in logit space across the whole
  0.1-0.9 range and present for both neutral/non-neutral matches"** (as
  reported), a 2-parameter Platt scale (`a, b`) on the Poisson+DC output and a
  2-3 parameter ordered logit on Elo-diff are likely to produce *very
  similar* final probabilities for any single match — both are essentially
  fitting "a logistic curve in `elo_diff`-ish-space to H/D/A outcomes." The
  value of doing ordered logit ANYWAY is (a) it's a genuinely different
  estimation path that serves as a **independent cross-check** on the
  Platt-scaled Poisson+DC output (if both land close to the same MEX vs RSA
  number, that's reassuring; if they diverge a lot, that's itself an important
  finding to report), and (b) it gives you a natural place to add the
  feature-engineering ideas in §1.2/§2 below without touching the
  Elo→Poisson→DC machinery at all.

### 1.2 Gradient-boosted trees (XGBoost/LightGBM/CatBoost)

- **"Evaluating Soccer Match Prediction Models: A Deep Learning Approach and
  Feature Optimization for Gradient-Boosted Trees"** (arXiv:2309.14807,
  published in Machine Learning, Springer Nature, 2024).
  https://arxiv.org/abs/2309.14807 / https://arxiv.org/html/2309.14807
  - Used the 2023 Soccer Prediction Challenge dataset: **>300,000 matches,
    51 leagues, 2001-April 2023**. Built a candidate feature set of **205
    features** (concatenating Elo, pi-ratings, Berrar ratings, recency/form
    features, streaks, seasonal stats) before feature selection.
  - Compared CatBoost (with feature selection: Chi-square, Symmetrical
    Uncertainty, Correlation, Information Gain, ReliefF, Correlation Subset)
    vs. a deep learning model (Inception block + Transformer encoder + MLP
    on 5-match recency windows) vs. baselines (team averages, statistical
    models, XGBoost+Berrar ratings).
  - **Headline result**: CatBoost + pi-ratings achieved the best RPS
    (~0.1925-0.2085 depending on source), beating all 2017 Soccer Prediction
    Challenge entries and the deep-learning model (~0.2098 RPS), though the
    deep-learning model was more *stable* (lower variance across folds:
    σ=0.0051 vs 0.0083).
  - **Scale mismatch with our problem**: this paper's winning configuration
    used 300k+ matches and 205 candidate engineered features (many
    club-football-specific: recent-form rolling stats, streaks, seasonal
    performance — the kind of "recent-N-matches" features that ARE derivable
    from your panel but require non-trivial feature-engineering code written
    and validated tonight).

- **"Chapter 1: Machine Learning for Soccer Match Result Prediction"**
  (Bunker, R. et al., arXiv:2403.07669 — book chapter, "Statistical Learning
  for the Modeling of Soccer Matches," Springer 2024).
  https://arxiv.org/abs/2403.07669
  - Surveys the field broadly: confirms gradient-boosted trees (esp.
    CatBoost) "applied to soccer-specific ratings such as pi-ratings" are
    "currently the best-performing models on datasets containing only goals
    as match features" — but explicitly frames this as **rating choice +
    GBT**, not "GBT alone on raw Elo." The chapter calls for more comparison
    of deep learning / random forest "on a range of datasets with different
    types of features" — i.e., even the survey treats this as not yet settled
    for arbitrary feature sets, and flags **interpretability** as a practical
    gap for GBT/DL models vs. simpler rating-based models.
  - A separate aggregator source (thexgfootballclub Substack, blog-level, cite
    cautiously) reports XGBoost reaching ~67% match-outcome accuracy vs.
    Elo-only baselines around 52-80% and Poisson around 60-65% — wide,
    blog-sourced ranges that should be treated as illustrative only, but
    directionally consistent with "GBT + good ratings can match or beat
    Dixon-Coles," not as evidence GBT beats a *well-calibrated, properly-fit*
    Elo+ordered-logit model on a comparable feature set.

- **"Football Matches Outcomes Prediction Based on Gradient Boosting
  Algorithms and Football Rating System"** (CMS open-access conference
  paper). https://openaccess.cms-conferences.org/publications/book/978-1-958651-37-7/article/978-1-958651-37-7_9
  - Reported a combined model (Model 4, multiple approaches blended)
    achieving 63.2% accuracy — a 10.8% improvement over bookmaker accuracy and
    4.1% over Dixon-Coles in their setup. Notable because it explicitly frames
    **Dixon-Coles as "still one of the leading examples of statistical
    modelling for football [that] has not been significantly improved using
    machine learning techniques"** in isolation — the gains came from
    *combining* approaches/ratings, not from swapping DC wholesale for a
    single GBT.

- **International football specificity**: no paper found that applies
  GBT/XGBoost specifically to **international** (national-team) football with
  an **Elo-only** feature set comparable to yours. All the strong GBT results
  above rely on club-football-specific rich feature sets (pi-ratings,
  Berrar ratings, rolling-form, streaks across 51 leagues) that don't map
  cleanly onto your single international panel without substantial new
  feature-engineering work.

### 1.3 Other literature: xG-free Elo-based ML, DC vs ML comparisons

- **Constantinou & Fenton's "pi-football"** (Knowledge-Based Systems, 2012;
  also Constantinou & Fenton 2013, J. Quantitative Analysis in Sports) — a
  Bayesian network model incorporating both objective historical data and
  "subjective" factors (team news, fitness) not capturable from results data
  alone. Relevant mainly as: (a) another example of a model that goes BEYOND
  pure ratings+goals (their "pi-ratings" — a dynamic rating based on relative
  score discrepancies — are exactly the rating type used as the winning
  feature in arXiv:2309.14807 above), and (b) a reminder that the
  highest-performing published systems generally combine multiple signal
  types, which is out of scope tonight given the no-new-API-calls constraint.
  http://constantinou.info/downloads/papers/Constantinou-Ph.D(restructured).pdf
- **"Combining Machine Learning and Human Experts to Predict Match Outcomes
  in Football: A Baseline Model"** (arXiv:2012.04380) and **"Predicting
  Football Match Outcomes with eXplainable..."** (arXiv:2211.15734) — both
  surfaced in search but not deeply reviewed; both are consistent with the
  general pattern above (GBT/XGBoost as a strong baseline, combined with
  domain ratings, with explainability/calibration as an explicit concern) —
  flagged for future reading, not load-bearing for tonight's decision.

---

## 2. Calibration of ML models for sports prediction — do GBTs/NNs need
recalibration too?

**Short answer: yes, emphatically, for tree ensembles — this is one of the
best-established findings in the calibration literature, and it directly
affects the cost-benefit of "switch to GBT instead of Platt scaling."**

- **Niculescu-Mizil, A. & Caruana, R. (2005). "Predicting Good Probabilities
  With Supervised Learning." ICML 2005.**
  https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf
  - Compares raw probability outputs of 10 supervised learning methods
    (boosted trees, boosted stumps, SVMs, neural nets, bagged trees,
    random forests, logistic regression, naive Bayes, KNN, decision trees)
    before and after Platt scaling and isotonic regression.
  - **Key finding directly relevant here**: "maximum margin methods such as
    boosted trees and boosted stumps push probability mass away from 0 and 1,
    yielding a characteristic sigmoid-shaped distortion in the predicted
    probabilities" — i.e., **boosted trees are systematically
    under-confident at the extremes and need an S-shaped (Platt-scaling-like)
    correction just to become reasonably calibrated.** In contrast, neural
    nets and bagged trees do NOT show this bias and tend to predict
    reasonably calibrated probabilities without correction.
  - "Boosted trees have such poor initial calibration that it is not
    surprising that Platt Calibration and Isotonic Regression significantly
    improve their squared error and cross-entropy. After calibration with
    Platt Scaling or Isotonic Regression, boosted decision trees have better
    squared error and cross-entropy than the other nine learning methods" —
    i.e., GBTs can end up BEST after recalibration, but recalibration is not
    optional, it's part of the standard pipeline.
- **Niculescu-Mizil, A. (2007/2012 update). "Obtaining Calibrated
  Probabilities from Boosting."** AAAI Workshop / arXiv:1207.1403.
  https://arxiv.org/abs/1207.1403
  - Follow-up specifically on boosting; reinforces the same sigmoid-distortion
    finding and explores corrections (Platt scaling, isotonic, "logistic
    correction" specific to boosting's margin-based loss).
- **Practical implication for "GBT vs Platt-scaled Poisson+DC"**: choosing
  GBT does **not** let you skip the calibration step you were already
  planning — at best it changes WHAT you apply Platt/isotonic scaling TO
  (raw GBT outputs vs. Poisson+DC outputs). So the realistic comparison isn't
  "Platt scaling vs. ML" — it's "Platt-scaled Poisson+DC vs. Platt-scaled GBT
  vs. ordered logit (which targets outcomes directly and may need little/no
  extra recalibration)." Given GBT's much higher implementation/validation
  cost tonight for (at best) a marginal accuracy edge that STILL needs a
  calibration layer, **ordered logit is the more efficient use of the
  remaining hours** — it's simultaneously (a) a defensible "ML" upgrade,
  (b) more directly self-calibrating by construction (H&A 2010), and (c) far
  cheaper to implement/validate than GBT + its required recalibration step.
- **General calibration data-size note**: "when the calibration set is small
  (less than about 2,000 cases), Platt Scaling outperforms Isotonic
  Regression" (same Niculescu-Mizil & Caruana line of work, also echoed in
  the FastML summary already cited in `calibration_research_notes.md`). With
  49,400 matches and a sensible holdout split, you're well above this
  threshold for EITHER method — but if you split further by `neutral` flag or
  by recency (recommended diagnostics from `calibration_research_notes.md`),
  some sub-bucket holdouts could dip below 2,000, in which case prefer Platt
  over isotonic for those slices.

---

## 3. Feasibility assessment for the 15-hour window

### Almost certainly feasible, likely to help (do tonight)

**A. Elo-diff (+ home/neutral) → ordered logit, via `statsmodels.miscmodels.
ordinal_model.OrderedModel`** (proportional-odds / ordered logit — the Python
equivalent of R's `MASS::polr()`, and you're already using `statsmodels` for
the Poisson GLM, so no new dependency).
- **Inputs**: `elo_home_pre - elo_away_pre` (sign-adjusted per row's home/away
  convention), a `home_adv` dummy (0 if `neutral==TRUE` else 1) — i.e.,
  exactly the covariates you already compute correctly in
  `backtest_harness.py`/`predict.py`/`fit_rho.py` (the *correct*,
  neutral-aware versions, per `code_audit_findings.md` finding 2.2).
- **Target**: 3-level ordered outcome (Away win < Draw < Home win), derived
  trivially from `home_score`/`away_score`.
- **Recency weighting**: `OrderedModel.fit()` supports `freq_weights` /
  can be approximated via weighted MLE — re-use the same `xi=0.0008`
  exponential weights already computed for the Poisson fit.
- **Validation**: plug straight into `backtest_harness.py` /
  `backtest_diagnostics.py` — replace the "Poisson λ → DC grid → H/D/A" step
  with "ordered logit → H/D/A" for a parallel run; both can be evaluated with
  the existing Brier/RPS/calibration-bucket code with minimal changes (the
  ordered-logit path *skips* Dixon-Coles and the goal-totals market entirely —
  flag clearly that this path does NOT produce O/U or BTTS probabilities, only
  1X2; if the prediction market needs those too, you'd still need
  Poisson+DC+Platt for those markets specifically).
- **Estimated time**: 1-2 hours implementation + 1 hour backtest validation +
  30 min sanity-check against Platt-scaled Poisson+DC for MEX vs RSA
  specifically. Comfortably fits in 15 hours with margin for the diagnostics
  already recommended in `calibration_research_notes.md` (logit-space
  re-plot, neutral/non-neutral decomposition) running in parallel.
- **Risk**: low. Worst case it performs similarly to Platt-scaled Poisson+DC
  (in which case you have two independent confirmations of the same number —
  itself valuable) or reveals a discrepancy worth investigating before the
  market closes.

**B. Walk-forward Platt scaling on Poisson+DC output** (already planned) —
keep this regardless; it's the lowest-risk, field-standard fix and a useful
baseline/comparison point for (A).

### Time-permitting, moderate payoff (do if A finishes early)

**C. 1-3 engineered features added to the ordered-logit (or Poisson) design
matrix, ALL derivable from `elo_match_panel.csv` alone:**
- **Elo momentum/trend**: e.g., `elo_home_pre - elo_home_pre_at(date - 365d)`
  for each team (requires a lookup into the team's own Elo history within the
  panel — a few lines of pandas, no new data). Captures "is this team
  currently rising/falling," which a static point-in-time Elo doesn't.
- **"Reliability" / data-depth covariate**: `min(n_matches_played_to_date)`
  for the two teams, or `years_since_team_first_appears`, optionally
  interacted with `elo_diff`. Directly operationalizes the Glicko/TrueSkill
  "uncertainty" idea from `calibration_research_notes.md` §2.1-2.2 as a cheap
  regression covariate rather than a full Bayesian rating overhaul.
- **Recent goal-difference form**: rolling sum/average of
  `(goals_for - goals_against)` over each team's last N matches — a classic
  "form" feature used across the GBT literature (§1.2), computable purely from
  columns already in the panel.
- **Caveats**: cap at 2-3 new features. With ~10-15k effective
  (recency-weighted) matches and one evening for validation, more features =
  more overfitting risk with no time for proper nested CV / regularization
  tuning. Each added feature should be checked in the walk-forward backtest
  for (i) sign/magnitude sanity and (ii) whether it actually moves the
  calibration-bucket table, not just in-sample fit.
- **Estimated time**: 1-3 hours per feature (engineering + backtest re-run),
  depending on how much of the team-history-lookup machinery can be reused
  across features. Realistically, only attempt if (A)+(B) are done with
  several hours to spare.

### Interesting but too risky/time-consuming for tonight (defer)

**D. Gradient-boosted trees (XGBoost/LightGBM/CatBoost)** — per §1.2/§2:
strong literature support *in principle*, but (i) the winning configurations
in the literature rely on rich feature sets (pi-ratings, Berrar ratings,
50-200 engineered features) you don't have time to build tonight; (ii) GBTs
on ~10-15k effective rows with only 3-5 features are at meaningful overfitting
risk, and the common rule-of-thumb is to be cautious with tree ensembles below
~10k rows; (iii) GBTs are NOT calibrated out of the box (Niculescu-Mizil &
Caruana 2005) — you'd still need the Platt/isotonic step on top, so GBT adds
implementation+validation cost without removing the recalibration requirement;
(iv) no walk-forward CV / hyperparameter search infrastructure currently
exists for a tree model (the existing harness is built around the Elo→Poisson→
DC pipeline's specific output format) — building and trusting that
infrastructure same-night is itself a multi-hour, error-prone task per your
"never shortcuts, be thorough" working principle. **Revisit as a multi-day
post-market project**, ideally after (C)'s features exist (so GBT has a richer
input than raw Elo-diff) and there's time for proper time-series CV.

**E. Neural networks / deep learning** — even less appropriate: the
literature's deep-learning successes (arXiv:2309.14807) use 300k+ matches and
multi-match recency-sequence architectures (Transformers/Inception blocks);
your dataset and timeline support neither the data volume nor the
architecture-validation time these require. Skip entirely for tonight.

**F. SIMEX / errors-in-variables correction of `b2`, full TrueSkill/Glicko
Bayesian rating system replacing Elo** — already correctly flagged as
"overkill, defer" in `calibration_research_notes.md` §3.2/§5; nothing in this
research changes that assessment. A 2025 paper, "Empirical Bayes shrinkage
(mostly) does not correct the measurement error in regression" (arXiv:
2503.19095), reinforces that ad-hoc "denoise-then-regress" shortcuts (which is
the realistic same-night version of this) can fail to de-bias and sometimes
make things worse — so if attempted at all, needs to be done properly, which
is a multi-day undertaking.

### On new data / API calls

Per your standing instruction (10k/day QK API quota, conserve), **no new API
pulls are recommended for tonight's fix**. If a future iteration wanted to
chase the GBT/rich-feature route (D), the highest-value *additional* data
(per the literature surveyed) would be: (a) recent match-level shot/xG-style
stats (not currently in your panel — would meaningfully improve "form"
features beyond goal differentials), and (b) bookmaker/market odds for the
same fixtures (Hvattum & Arntzen 2010 and the tennis-Elo paper in
`calibration_research_notes.md` §2.3 both find market odds outperform
pure-rating models — blending your model's output with market odds, where
available, is a separately-documented, high-value, low-engineering-cost
technique per `research_notes.md` §11 step 6, and does NOT require ML at all).
**Both would require new API calls and explicit user approval** — flagged
here per instruction, not actioned.

---

## 4. Direct answer to "is ordered logit basically the same endpoint as Platt
scaling, just a fancier route?"

Partially yes, partially no — worth stating plainly for the time-pressured
reader:

- **If** the diagnosed gap is exactly "Poisson+DC's mapping from `elo_diff`
  to `P(home win)` has the right *shape* but the wrong *scale/intercept* in
  logit space" — then a 2-parameter Platt scale on the Poisson+DC output and a
  2-3 parameter ordered logit on `elo_diff` will converge to **very similar
  final numbers** for any given match, including MEX vs RSA. In this case,
  doing both is mostly a robustness/cross-check exercise (still valuable, low
  marginal cost).
- **If** the gap instead reflects a *shape* mismatch (e.g., Poisson+DC's
  implied H/D/A curve as a function of `elo_diff` has a different functional
  form than the true outcome curve — plausible given DC adds an extra
  degree of freedom via `rho` and the goal-count→outcome mapping is
  nonlinear) — ordered logit, fit directly on outcomes, can capture a
  different (potentially better-fitting) shape that a simple 2-parameter
  rescaling of Poisson+DC's output cannot. In this case ordered logit could
  meaningfully outperform Platt-scaled Poisson+DC, especially near the tails
  (very lopsided Elo gaps) where Poisson+DC's compounding of Poisson
  goal-distributions + DC's tau-correction could behave non-logistically.
- **Either way**, running both (A) and (B) is the right call given the time
  budget: it's cheap, it directly tests this question empirically on YOUR
  data via the existing harness, and it gives you either (i) confirmation
  from two independent methods (high confidence for MEX vs RSA), or (ii) an
  important discrepancy to investigate/explain before using either number.

---

## Sources Index (this document)

- Hvattum, L.M. & Arntzen, H. (2010). "Using ELO ratings for match result
  prediction in association football." International Journal of Forecasting,
  26(3), 460-470.
  https://www.sciencedirect.com/science/article/abs/pii/S0169207009001708
- "Evaluating Soccer Match Prediction Models: A Deep Learning Approach and
  Feature Optimization for Gradient-Boosted Trees." arXiv:2309.14807 (2023);
  also published in Machine Learning (Springer Nature, 2024).
  https://arxiv.org/abs/2309.14807 / https://link.springer.com/article/10.1007/s10994-024-06608-w
- Bunker, R. et al. "Chapter 1: Machine Learning for Soccer Match Result
  Prediction" (book chapter, "Statistical Learning for the Modeling of Soccer
  Matches," Springer 2024). arXiv:2403.07669.
  https://arxiv.org/abs/2403.07669
- "Football Matches Outcomes Prediction Based on Gradient Boosting Algorithms
  and Football Rating System" (CMS open-access conference proceedings).
  https://openaccess.cms-conferences.org/publications/book/978-1-958651-37-7/article/978-1-958651-37-7_9
- Niculescu-Mizil, A. & Caruana, R. (2005). "Predicting Good Probabilities
  With Supervised Learning." ICML 2005.
  https://www.cs.cornell.edu/~alexn/papers/calibration.icml05.crc.rev3.pdf
- Niculescu-Mizil, A. (2012). "Obtaining Calibrated Probabilities from
  Boosting." arXiv:1207.1403. https://arxiv.org/abs/1207.1403
- "Empirical Bayes shrinkage (mostly) does not correct the measurement error
  in regression." arXiv:2503.19095 (2025). https://arxiv.org/html/2503.19095v1
  (already cited in `calibration_research_notes.md`; re-cited for the SIMEX/
  GBT-feature-engineering-shortcut caution in §3 "Defer" item F)
- Constantinou, A., Fenton, N. & Martin, M. (2012). "pi-football: A Bayesian
  network model for forecasting Association Football match outcomes."
  Knowledge-Based Systems, 36, 322-339.
  http://constantinou.info/downloads/papers/Constantinou-Ph.D(restructured).pdf
- "mord: Ordinal Regression in Python" (package docs — alternative to
  `statsmodels.miscmodels.ordinal_model.OrderedModel` if needed).
  https://pythonhosted.org/mord/
- thexgfootballclub Substack, "Which Machine Learning Models Perform Best for
  Football Match Prediction?" (blog-level source, cited cautiously for
  illustrative accuracy ranges only).
  https://thexgfootballclub.substack.com/p/which-machine-learning-models-perform
- Cross-referenced from `calibration_research_notes.md` (already in this
  directory): Glicko-2 (Glickman), TrueSkill (Herbrich, Minka & Graepel 2006),
  tennis-Elo calibration-ratio paper (Vaughan Williams et al., Nottingham
  Trent), FiveThirtyEight SPI methodology, Platt scaling (Wikipedia / FastML).
