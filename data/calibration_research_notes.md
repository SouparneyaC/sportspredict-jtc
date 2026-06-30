# Calibration Research Notes — "Compression Toward 50/50" Finding

**Context.** Backtest of ~49,000 international football matches (walk-forward,
point-in-time) shows: at every predicted P(home win) bucket from 0.1 to 0.9, the
*actual* home-win rate is ~5-8 percentage points HIGHER than predicted, uniformly
across the range. Re-fitting the Dixon-Coles `rho` (placeholder -0.10 → MLE-fitted
-0.06) barely moved this gap. Pipeline: `elo.py` (PIT Elo, INITIAL_RATING=1500 from
1872, hand-built K-factor tiers, flat HOME_ADVANTAGE=100) → `poisson_goals.py`
(statsmodels Poisson GLM, goals ~ Elo-diff + home dummy, exponential recency
weighting, currently b1=0.2562, b2=elo_diff_coef) → `dixon_coles.py` (scoreline grid +
rho).

This document evaluates the leading hypothesis ("attenuation bias from a noisy
homemade Elo covariate") against real literature, surveys cross-domain analogues, and
ranks concrete remediation options.

---

## 1. Does "attenuation bias from a noisy rating covariate" hold up?

### 1.1 The general statistical mechanism — well established

Classical errors-in-variables (EIV) theory is unambiguous: if the true regressor is
`x*` but you observe `x = x* + u` (u = mean-zero noise uncorrelated with x*), then in
a simple linear (or single-index) model the OLS/MLE coefficient on `x` is biased
toward zero by a factor approximately equal to the **reliability ratio**
`λ = Var(x*) / (Var(x*) + Var(u)) = Var(x*)/Var(x)`, i.e. `E[β̂] ≈ λ·β`. This is the
textbook "attenuation bias" / "regression dilution" result.

- **Steve Pischke's LSE EC524 lecture notes on Measurement Error** (econ.lse.ac.uk,
  Spring 2007) give the canonical derivation of this attenuation factor for the
  classical EIV model and discuss the multivariate extension (where attenuation can
  also "leak" bias onto *other* coefficients in the model, not just the mismeasured
  one) — directly relevant since our Poisson model has Elo-diff alongside a home-dummy.
  https://econ.lse.ac.uk/staff/spischke/ec524/Merr_new.pdf
- A concise restatement of the same mechanism: "Attenuation bias, also called
  regression dilution, is a bias in model coefficients caused by measurement error or
  noise in your independent (X) variables, with model coefficients becoming biased
  towards 0." — graduatestatisticstutor.com summary of the standard textbook result
  (Wooldridge, *Introductory Econometrics*, ch. 9, is the usual primary citation for
  this exact statement).
  https://graduatestatisticstutor.com/why-measurement-error-attenuation-bias

### 1.2 Does this mechanism map onto OUR pipeline as described?

**Mechanically: yes, and the direction of the predicted effect matches the
finding.** If the true Elo-difference `(Elo*_home − Elo*_away)` is observed only as a
noisy proxy `(Elo_home − Elo_away)` — noise arising from (a) the arbitrary
INITIAL_RATING=1500 bootstrap for every team in 1872 (more consequential for teams
with shallow modern histories — see §1.3), (b) the hand-built K-factor tournament
tiers (a discretization of "match importance" that is itself a noisy proxy for the
"true" information content of a result), and (c) the flat HOME_ADVANTAGE=100 for
every team/era/venue (when true home advantage plausibly varies by team, opponent,
altitude, crowd, era — see §3.4) — then:

1. The Poisson regression coefficient `b2` (elo_diff_coef) is attenuated toward 0
   relative to its "true Elo" value.
2. A smaller `b2` means `lambda_home / lambda_away` (the expected-goals ratio) is
   *less* sensitive to the true talent gap than it should be for any given observed
   Elo gap.
3. Smaller goal-rate gaps → scoreline grid (Dixon-Coles) → match-result probabilities
   that are pulled toward 1/3-1/3-1/3-ish, i.e. **toward 50/50 for the home/away
   split** — exactly the uniform compression observed.

This is internally consistent and the *direction* is correct. **However**, two
caveats prevent calling it "confirmed":

- **No paper we found performs this exact decomposition for football Elo → Poisson →
  match probabilities.** The mechanism is a textbook one (§1.1) applied by us to this
  pipeline; we did not find a published study that (a) measures the reliability ratio
  of a homemade international-football Elo rating, or (b) demonstrates empirically
  that correcting for it removes a calibration gap of this size. This is a
  **reasoned extrapolation from general EIV theory, not a literature-confirmed
  finding specific to football Elo.** Be honest about this when reporting upward.
- **A uniform additive-in-probability shift across the WHOLE 0.1-0.9 range is not
  the textbook EIV signature on its own.** Classical attenuation shrinks a
  *coefficient* — its effect on predicted probabilities from a logistic/Poisson link
  is generally **multiplicative on the log-odds / log-rate scale**, which produces a
  *non-uniform* compression in probability space (bigger absolute pp-gaps near 0.5,
  smaller near the extremes 0.1/0.9, when expressed as raw probability differences —
  though if expressed in log-odds the shrinkage IS uniform). Re-derive the backtest's
  bucket-level gaps in **log-odds space**: if the gap is roughly constant in log-odds
  (not in raw probability), that is much stronger evidence for a single multiplicative
  attenuation factor on `b2` (and is the signature EIV would predict). If the gap is
  closer to constant in *raw probability* across 0.1-0.9, that points more toward an
  **additive miscalibration** (e.g., a missing/mis-set intercept, a systematically
  wrong `rho`, or a structural omitted-variable / functional-form issue) rather than
  pure coefficient attenuation. **This single diagnostic — replot the calibration gap
  in logit space — is the highest-value, lowest-cost first step** (see
  Recommendations).
- A second possibility consistent with "uniform gap, didn't move when rho changed":
  **the home-advantage constant (b1=0.2562, ≈ flat across all matches) plus a flat
  HOME_ADVANTAGE=100 Elo points may itself be miscalibrated** in a way that shows up
  as an apparently "Elo-independent" shift — see §3.4 for whether 100 Elo
  points / b1=0.2562 are too large or too small versus the literature.

### 1.3 The "noisy 1500 bootstrap" sub-mechanism — is it large enough to matter?

The INITIAL_RATING=1500-for-everyone-in-1872 choice means teams that entered
international football early (England, Scotland — playing since 1872) have had ~150
years of match-driven updates to wash out their arbitrary starting value, while teams
that entered recently (e.g., post-1991 post-Soviet states, post-2006 Montenegro/
Serbia split, newly FIFA-affiliated minnows) carry a much larger fraction of
"arbitrary 1500" in their current rating. This is a **heteroskedastic measurement
error** problem (noise variance differs by team/era), which EIV theory says still
produces attenuation on average but with the *bias being worse for matches involving
recently-bootstrapped teams*. A useful empirical check: **split the backtest's
calibration-gap analysis by "team-pair Elo-history-depth"** (e.g., bucket matches by
`min(years_since_team_entered_dataset for both teams)`). If the calibration gap is
markedly larger for matches involving "young" Elo histories, that's strong supporting
evidence for the measurement-error-from-bootstrap component specifically (and would
argue for the Glicko/TrueSkill-style "uncertainty-weighted" remedies in §2).

---

## 2. Cross-domain parallels: explicit uncertainty in rating systems

### 2.1 Glicko / Glicko-2 (chess) — Mark Glickman

- **Source**: Glickman's own "Example of the Glicko-2 system" worked example
  (glicko.net/glicko/glicko2.pdf), and the Glicko Rating System Wikipedia summary.
  https://glicko.net/glicko/glicko2.pdf ,
  https://en.wikipedia.org/wiki/Glicko_rating_system
- **Core idea**: Elo represents a player's strength as a single point estimate `R`.
  Glickman's critique (going back to his 1995 paper "The Glicko System") is that Elo
  has **no model of how confident we should be in `R`** — a player with 5 games and a
  player with 5,000 games can have the identical rating but very different
  *reliability*. Glicko adds **Ratings Deviation (RD)**, the standard error of the
  rating, giving a 95% CI of `[R − 2RD, R + 2RD]`. New/inactive players get
  **high RD** (uncertain), which (a) causes their ratings to move faster when new
  results come in (an implicit Kalman-filter-like update gain), and (b) — crucially
  for calibration — **RD can be propagated into the win-probability formula itself**:
  matches against/between high-RD players produce *win probabilities pulled toward
  0.5* relative to what the point-estimate rating gap alone would imply, because the
  Glicko win-probability formula divides the rating difference by a `g(RD)` factor
  that widens (flattens) the logistic curve when RD is large.
- **Glicko-2** adds a third parameter, **volatility (σ)** — how erratically a
  player's true strength itself fluctuates over time, separate from measurement
  uncertainty about a stable strength.
- **Direct relevance to us**: Glicko's RD is *exactly* the kind of "confidence/
  reliability" companion quantity our Elo lacks. An analogous quantity for our Elo —
  e.g., "effective number of rating-relevant matches played" or "years since
  bootstrap" as a proxy for RD — could be: (a) used to **down-weight** or
  **flatten** the win-probability curve for matches involving high-uncertainty teams
  (mechanically similar to Glicko's `g(RD)` divisor), or (b) included as an
  **additional regression covariate** (interaction term: Elo-diff × reliability) in
  `poisson_goals.py`, which is a cheap, no-architecture-change way to let the model
  learn that Elo-diff is more/less informative depending on data depth.

### 2.2 TrueSkill (Microsoft Research, Xbox Live)

- **Source**: Microsoft Research's TrueSkill project page and original paper
  ("TrueSkill(TM): A Bayesian Skill Rating System", Herbrich, Minka & Graepel, NeurIPS
  2006).
  https://www.microsoft.com/en-us/research/project/trueskill-ranking-system/ ,
  https://www.microsoft.com/en-us/research/publication/trueskilltm-a-bayesian-skill-rating-system/
- **Core idea**: each player/team is a **Gaussian belief** `N(μ, σ²)` over true skill,
  updated via approximate Bayesian inference (factor graphs / expectation
  propagation) after each game, generalizing Elo (which is the maximum-likelihood
  point-update analog of this).
- **New player problem**: new players start with a **wide prior**, e.g. `μ=25,
  σ=8.333` (so `σ` is fully 1/3 of `μ` — a huge relative uncertainty). This
  high σ means: (a) matchmaking treats their predicted outcome distribution as wide
  (less confident win probabilities), and (b) each game updates `μ` aggressively
  (large effective learning rate) until σ shrinks. **This is the textbook fix for
  exactly our "INITIAL_RATING=1500 for everyone in 1872" problem** — instead of a
  single deterministic starting value, a new entity should start with a *wide*
  uncertainty band that narrows as data accumulates, and that uncertainty should
  *propagate into the predicted outcome distribution* (flattening it toward 50/50
  for new/uncertain teams) rather than being silently dropped.
- **Calibration story**: TrueSkill's `P(player A beats player B)` is computed
  directly from the *difference of the two Gaussian belief distributions*
  (a Gaussian itself, by additivity), so uncertainty in either player's rating
  mechanically widens/flattens the predicted win probability — i.e., **uncertainty
  is a first-class input to the calibration of the output probability**, not an
  afterthought. This is the single biggest structural difference from a "flat Elo →
  logistic/Poisson" pipeline like ours, where the rating is treated as if it were
  measured without error once it's handed to the regression.

### 2.3 Other domains

- **Tennis Elo**: "How well do Elo-based ratings predict professional tennis
  matches?" (Vaughan Williams et al., Nottingham Trent University working paper,
  irep.ntu.ac.uk/id/eprint/42038) explicitly defines a **calibration ratio** =
  `Σ(predicted P(higher-rated player wins)) / (number of matches the higher-rated
  player actually won)`. A ratio > 1 = the model *overestimates* the favorite's
  chances (overconfidence in favourites); < 1 = underconfidence. This paper also
  finds that **bookmaker odds outperform pure Elo on both accuracy and calibration**
  for men's tennis — consistent with Hvattum & Arntzen's football finding (already in
  our `research_notes.md` §4.6) that market odds beat Elo-based models, and reinforces
  that **a derived rating alone, fed through a single-index model, is generally
  NOT well-calibrated out of the box** in multiple sports — recalibration against a
  held-out sample (or against market data, where available) is the norm, not the
  exception.
  https://irep.ntu.ac.uk/id/eprint/42038/1/1400774_Vaughan_Williams.pdf
- **Esports (Decoding Machine Learning Benchmarks / rating-system evaluation
  papers)**: "The Evaluation of Rating Systems in Online Free-for-All Games"
  (arXiv:2008.06787) and "...in Team-based Battle Royale Games" (arXiv:2105.14069)
  both compare Elo-style vs. Glicko vs. TrueSkill-style systems on large-scale
  matchmaking data and consistently find that **uncertainty-aware systems
  (Glicko/TrueSkill) produce better-calibrated match-outcome predictions than
  point-estimate Elo**, particularly early in a player's history — directly
  analogous to our "young Elo history" sub-hypothesis in §1.3.
  https://arxiv.org/pdf/2008.06787 , https://arxiv.org/pdf/2105.14069
- **Credit scoring**: a clean conceptual parallel (a single derived "score" feeding a
  probability-of-default model) but the credit literature's standard fix is
  **post-hoc recalibration of the score-to-PD mapping** (logistic recalibration,
  Platt scaling, isotonic regression, "calibration by bins" / Hosmer-Lemeshow
  testing) rather than correcting the score itself for measurement error — i.e., the
  credit-scoring convention is to treat the score as fixed and **recalibrate the
  output**, which is the pragmatic, "doesn't require re-deriving the whole pipeline"
  approach (see §3.1). General summary: "Approaches for Credit Scorecard
  Calibration: An Empirical Analysis" (ResearchGate,
  researchgate.net/publication/318702064) surveys logistic regression, Platt
  scaling, GAM, isotonic regression, and Gaussian Naive Bayes recalibrators for
  exactly this "noisy/derived score → probability" setting.

---

## 3. Concrete remediation techniques, ranked by applicability

### 3.1 Post-hoc recalibration (Platt scaling / isotonic regression) — STANDARD AND
LOW-RISK

- **Status in the literature**: both methods are textbook/standard for
  classifier-probability recalibration generally (Platt 1999; Zadrozny & Elkan 2002
  for isotonic). Platt scaling = fit a 1-D logistic regression
  `P_calibrated = σ(a · logit(P_model) + b)` on held-out data; isotonic regression =
  fit a monotonic step function `P_model → P_calibrated` non-parametrically (more
  flexible, needs more data, can overfit with few bins).
  https://en.wikipedia.org/wiki/Platt_scaling ,
  FastML "Classifier calibration with Platt's scaling and isotonic regression"
  (fastml.com/classifier-calibration-with-platts-scaling-and-isotonic-regression).
- **Applied to football specifically**: a worked example (foresportia.com,
  "Algorithm journal: probability calibration in football prediction models")
  reports Platt scaling reducing Brier score from 0.22→0.19 and Expected Calibration
  Error from 0.08→0.06 on 2024 Premier League data, with isotonic regression doing
  slightly better still (Brier 0.18, ECE 0.05) — **NOTE**: this is a blog-level
  source, not peer-reviewed, and it frames the problem as *overconfidence* (opposite
  direction to ours) — treat the magnitude as illustrative-only, not as a directly
  comparable benchmark, but it does establish that **Platt/isotonic recalibration is
  an accepted, commonly-applied step specifically for football win-probability
  outputs**.
  https://www.foresportia.com/en/blog/algorithm-journal-football-prediction-probability-calibration.html
- **Caveats for OUR case**:
  - Platt scaling fits a 2-parameter logistic on `logit(p_model)` — given our gap is
    "uniform across 0.1-0.9," a Platt-scale slope `a > 1` (steepening the logit)
    would be exactly the right shape of correction IF the gap is uniform in
    log-odds (see §1.2's diagnostic). If the gap is closer to uniform in raw
    probability, Platt scaling (which operates multiplicatively in logit-space) will
    under-correct at the extremes and over-correct near 0.5 — isotonic regression
    would handle that shape better but needs enough data per bucket (with 49,000
    matches × buckets of width 0.1, you likely have plenty).
  - **Must be fit on a held-out / walk-forward slice**, not the same data used to fit
    `b0,b1,b2,rho` — otherwise you're just re-fitting noise. Given the existing
    walk-forward backtest harness, the natural design is: fit Platt/isotonic
    recalibration on an early holdout window, validate on a later window, exactly
    mirroring how the Elo/Poisson/DC parameters themselves should be validated.
  - Recalibration at the **match-result (1X2) probability level** is the most direct
    fix for the reported bucket-level finding, but it is a **band-aid on the output**,
    not a fix to `b2`/Elo — it won't fix scoreline-level (Dixon-Coles grid) or
    goal-total markets if those have their own (possibly different-shaped)
    miscalibration. Worth checking whether O/U, BTTS, correct-score markets show the
    *same* compression — if yes, the root cause is upstream (Elo/Poisson, supports
    the EIV hypothesis); if O/U and BTTS are well-calibrated but only 1X2 is off,
    that points toward something specific to the home/away split (e.g., the home
    advantage term, §3.4) rather than a generic "noisy strength index" issue.

### 3.2 Regression calibration / SIMEX — formally correct but likely OVERKILL here

- **What it is**: SIMEX (Simulation-Extrapolation, Cook & Stefanski 1994) and
  "regression calibration" are formal methods for de-attenuating a regression
  coefficient when you have an estimate of the *measurement-error variance* of the
  mismeasured covariate. SIMEX works by deliberately adding extra simulated noise of
  increasing magnitude to the covariate, refitting the model each time, and
  extrapolating the resulting coefficient trend back to the "zero additional noise"
  (i.e., true) case.
  https://pmc.ncbi.nlm.nih.gov/articles/PMC10062410/ (review),
  https://pmc.ncbi.nlm.nih.gov/articles/PMC2710855/ (SIMEX + SE estimation in
  semiparametric models)
- **Realistically applicable to us?** Formally yes — SIMEX doesn't require knowing
  the *true* Elo, only the *measurement-error variance* of our Elo relative to "true"
  Elo, which we don't directly observe but COULD proxy (e.g., bootstrap the Elo
  computation over resampled match histories / alternative INITIAL_RATING values /
  alternative K-factor maps to get a distribution of Elo-diff values per match, and
  use the spread as the "added noise" scale for SIMEX).
- **However**: this is a heavyweight, research-grade correction whose main payoff
  (de-biasing `b2` itself) only matters if you care about the *interpretation* of
  `b2` as a structural parameter. For a **predictive** pipeline, post-hoc
  recalibration (§3.1) achieves the same end result (better-calibrated output
  probabilities) far more cheaply, and a recent paper, **"Empirical Bayes shrinkage
  (mostly) does not correct the measurement error in regression"** (arXiv:2503.19095,
  2025) is a useful caution here too: it shows that naive "denoise-then-regress"
  two-step approaches (which is conceptually close to what an ad-hoc Elo-smoothing
  fix would be) can fail to de-bias and sometimes make things worse — reinforcing
  that if you go down the "fix the covariate" route, do it with a properly validated
  method (SIMEX or full errors-in-variables MLE), not an ad-hoc smoothing step.
  https://arxiv.org/html/2503.19095v1
- **Verdict**: **overkill as a first step**. Revisit only if (a) the §1.2 logit-space
  diagnostic confirms a clean multiplicative-in-logit pattern (the EIV signature),
  AND (b) post-hoc recalibration (§3.1) turns out to be insufficiently stable
  out-of-sample (e.g., the Platt/isotonic correction itself drifts a lot across
  walk-forward folds, suggesting the *underlying* `b2` is the real problem, not just
  the output mapping).

### 3.3 FiveThirtyEight / SPI methodology — initial ratings, HFA, calibration steps

- **Source**: FiveThirtyEight's "How Our Club Soccer Projections Work" methodology
  (archived/secondary sources, since fivethirtyeight.com itself now redirects —
  content reconstructed via GitHub `fivethirtyeight/data` soccer-spi README and
  third-party analyses).
  https://github.com/fivethirtyeight/data/blob/master/soccer-spi/README.md ,
  https://joshyazman.github.io/spi-ratings-analysis/
- **(a) Initial ratings for teams with no history**: SPI does NOT bootstrap from a
  single flat constant the way our Elo does. For club teams, **preseason ratings
  carry over from the prior season via a time-weighted average of the team's rating
  over the past 5 seasons** (not a hard reset), AND ratings are **adjusted for
  player transfers in/out** during the offseason — i.e., a non-Elo, multi-source
  prior. For genuinely new entities (promoted teams, new national-team-eligible
  states), FiveThirtyEight's general practice (documented for NFL/NBA Elo too, per
  our existing research_notes.md §9.2) is to **seed using external information**
  (market data / proxy-league ratings) rather than a flat constant — directly
  contrasting with our flat `INITIAL_RATING=1500`.
- **(b) Home-field advantage**: estimated/validated **empirically from the
  historical home win rate** in the dataset (our research_notes.md §9.1 already
  documents the NFL analogue: ~48 Elo points ≈ matches a ~57% historical home win
  rate). The general principle — **back out the Elo-point HFA from the empirical
  home win rate, rather than asserting a round number** — is the single most directly
  actionable, low-cost check for us: compute the actual historical home-win rate in
  the 49k-match dataset (controlling for team strength) and check whether
  HOME_ADVANTAGE=100 over- or under-shoots it.
- **(c) Explicit calibration step on final probabilities**: the SPI pipeline's final
  step is **Monte Carlo simulation** (10,000 reps) of a Poisson-based match model
  using the offense/defense ratings + HFA + rest days — i.e., **the Poisson model IS
  the calibration step** for FiveThirtyEight (no separate Platt/isotonic layer is
  documented). This suggests FiveThirtyEight relies on getting the *inputs* (ratings,
  HFA) well-calibrated in the first place rather than patching outputs — but note we
  could not find a FiveThirtyEight-published calibration/reliability-diagram audit of
  their soccer win probabilities specifically (their NFL Elo work, by contrast, does
  publish such diagnostics — see research_notes.md §9.3) — so it's unclear whether
  SPI soccer probabilities are, in practice, well-calibrated either. **Don't assume
  "FiveThirtyEight-style = automatically calibrated"** — but DO adopt their
  inputs-focused philosophy (better Elo bootstrap, empirically-derived HFA) as
  complementary to (not instead of) output recalibration.

### 3.4 Empirical magnitude check: home advantage (HOME_ADVANTAGE=100, b1=0.2562)

- **Elo-points HFA literature**: the World Football Elo Ratings system (eloratings.net,
  via Wikipedia "World Football Elo Ratings") uses a **flat +100 Elo points** for the
  home team — i.e., our `HOME_ADVANTAGE=100` matches the exact convention of the
  source system we're emulating. Multiple secondary sources (betsplug.com,
  opisthokonta.net "Elo ratings in football: Home field advantage") describe the
  broader empirical range for football HFA as **roughly 60-100 Elo points**, with 100
  being the high end / the eloratings.net convention specifically, and lower values
  (60-80) more typical for *club* competitions.
  https://en.wikipedia.org/wiki/World_Football_Elo_Ratings ,
  https://opisthokonta.net/?p=592
  - **Implication**: 100 is at the *high end* of the literature's range and is a
    club-vs-international distinction may matter — international HFA (where "home"
    can mean a continent/region rather than a single familiar stadium, e.g., a
    "home" World Cup qualifier played 1000km from the team's base) plausibly should
    be LOWER than a club's stadium-specific HFA, not higher. If our 49k-match dataset
    spans both genuinely "home soil" matches and loosely-defined "neutral=FALSE"
    international fixtures, **a flat 100 may be an overstatement for a meaningful
    subset of matches** — another candidate source of the uniform compression (an
    overstated HFA pushes predicted home-win probabilities up across the board,
    which — if the *model's* home-win predictions are systematically too high
    relative to what the Elo-diff alone would justify — could partially offset, or
    interact with, the Elo-attenuation effect in ways that are hard to disentangle
    without decomposing the gap by `neutral` flag).
- **Goals-based HFA literature** (for sanity-checking `b1=0.2562`, which implies
  `exp(0.2562) ≈ 1.292`, i.e., **home teams score ~29% more goals** than they would
  on a neutral field, all else equal):
  - A Premier League Poisson regression example reported a home-advantage
    coefficient of **0.2754** (≈ 1.317×, i.e., ~32% more goals) — directly
    comparable in magnitude to our 0.2562 (~29%). Source: "Predicting Football
    Results with Poisson Regression" (artiebits.com).
    https://artiebits.com/blog/predicting-football-results-with-statistical-modelling/
  - A broader cross-league study (15 leagues) found home advantage worth
    **~0.29 goals per game** in absolute terms (dropping to ~0.15 during COVID-era
    crowd-free matches) — this is an *additive* goals figure rather than a
    log-multiplicative coefficient, so not directly comparable to `b1`, but it
    confirms "home advantage ≈ 0.15-0.3 extra goals/game" as the right ballpark, and
    the COVID finding (HFA roughly halves without crowds) is a useful reminder that
    HFA is **not a fixed physical constant** — it has known, well-documented
    real-world variation (e.g., over time, by crowd presence), which a flat
    `HOME_ADVANTAGE=100` / flat `b1` cannot capture. Source: "Estimating the change in
    soccer's home advantage during the Covid-19 pandemic using bivariate Poisson
    regression," AStA Advances in Statistical Analysis (Springer, 2021).
    https://link.springer.com/article/10.1007/s10182-021-00413-9
  - **Bottom line on b1=0.2562**: this value is **squarely within the published
    range** (~0.15-0.32 in comparable Poisson-on-goals studies) — it is NOT an
    obvious outlier, so b1 itself is unlikely to be the primary driver of the
    calibration gap, though combined with `HOME_ADVANTAGE=100` (already baked into
    the Elo-diff that ALSO enters the regression for non-neutral matches) there may
    be a **double-counting of home advantage** worth checking: the Elo-diff used in
    the Poisson regression already has +100 (for the home team) baked in via the Elo
    update process's `dr` term — wait, actually re-reading `elo.py`, the +100 is only
    used to compute `we_home` (the *expected result* for the Elo *update*), it is
    NOT added to the *stored* `elo_home_pre`/`elo_away_pre` ratings that
    `poisson_goals.py` consumes as `elo_diff`. So there is **no direct
    double-counting of the +100 itself** in the Poisson regression's covariates —
    but it's still worth verifying empirically that `b1` (the home dummy in the
    Poisson model) and the embedded effect of `HOME_ADVANTAGE=100` (which
    *indirectly* shapes the Elo ratings of historically-home-favoured teams over
    time) aren't jointly producing an inflated home-side prediction. This is a
    second-order concern relative to §1.2's logit-space diagnostic, but cheap to
    check by **decomposing the calibration gap separately for `neutral=TRUE` vs
    `neutral=FALSE` matches** — if the gap is present (and similar in size) for
    NEUTRAL matches too (where HOME_ADVANTAGE/b1 play no role), that's strong
    evidence the gap is NOT primarily an HFA-calibration issue, and points back
    toward the Elo-diff/b2 attenuation story.

---

## 4. Bottom line / is the diagnosis right?

**Most likely explanation, in order of our confidence after this research:**

1. **(Plausible, mechanism well-supported, but UNCONFIRMED for this specific
   pipeline) Attenuation of `b2` (elo_diff_coef) due to noisy Elo-as-covariate** —
   the general EIV mechanism (§1.1) is textbook-solid and the *direction* matches.
   But we found no published study performing this exact correction for
   football-Elo-into-Poisson, so this remains an informed hypothesis, not a
   literature-confirmed diagnosis. The €1.2 logit-space diagnostic (cheap, ~1 hour of
   work using already-collected backtest output) would substantially raise or lower
   our confidence.
2. **(Equally plausible, NOT previously considered, and similarly cheap to check) An
   HFA-related miscalibration** — `HOME_ADVANTAGE=100` is at the high end of the
   published Elo-HFA range and may not fit international play uniformly; `b1=0.2562`
   is in-range but its *interaction* with Elo-derived ratings of historically
   home-advantaged teams deserves a look. The `neutral=TRUE` vs `FALSE` decomposition
   (§3.4) directly tests this and should be done alongside the logit-space check —
   they're cheap enough to do together and would jointly almost fully explain
   whether this is an "Elo noise" problem, an "HFA" problem, or both.
3. **(Less likely but worth ruling out) A residual Dixon-Coles / functional-form
   issue specific to international football** — the literature (extending_dixon_coles
   arXiv:2307.02139, already in `papers/`) notes that international matches show
   **larger heterogeneity in team quality** than club leagues, which can produce
   stronger negative goal-correlation than DC97's original club-football rho range —
   but you already re-fit rho (−0.10→−0.06) with minimal effect on the *match-result*
   calibration gap, which argues against rho/DC-correction as the primary driver
   (rho mainly reshapes the *low-score scoreline* probabilities, with comparatively
   small effect on the aggregate H/D/A split) — this is consistent with what you
   already found, so we don't think this needs more investigation right now.
4. **(Ruled out / not supported by anything found)** No evidence surfaced for a
   "known, separate, well-documented bias in Poisson goal models for international
   football" beyond what's captured in points 1-3 above. The Dixon-Coles
   international-applicability caveat (point 3) is the closest thing to a
   "known issue," and it's already been addressed by your rho refit.

---

## 5. Recommendations, ranked by feasibility/impact

1. **[Highest impact, lowest cost — DO THIS FIRST] Re-plot the calibration gap in
   logit (log-odds) space, AND decompose it by `neutral` flag (TRUE vs FALSE).** Both
   use data you already have from the backtest; no new model runs needed. This single
   analysis discriminates between hypothesis (1) [attenuation — gap roughly constant
   in logit space, present for both neutral and non-neutral matches] and hypothesis
   (2) [HFA miscalibration — gap concentrated in non-neutral matches, and/or not
   constant in logit space]. Do this before changing any code.

2. **[High impact, low-medium cost] Empirically back out the implied HFA from the
   49k-match dataset** (à la FiveThirtyEight's "derive HFA from historical home win
   rate" approach, §3.3b) and compare to `HOME_ADVANTAGE=100` and `b1=0.2562`. If the
   neutral-vs-non-neutral decomposition (step 1) implicates HFA, this tells you by how
   much to adjust — and whether a TIME-VARYING HFA (the COVID-era literature, §3.4,
   shows HFA isn't constant even within club football) is warranted for a 1872-2026
   dataset (it almost certainly varies by era — crowd sizes, travel, professionalism
   all changed enormously over 150 years).

3. **[Medium impact, low cost, standard practice] Add a walk-forward Platt-scaling
   (and/or isotonic regression) recalibration layer on the final 1X2 probabilities**,
   fit on a held-out slice distinct from the Elo/Poisson/rho-fitting data. This is the
   field-standard "fix the symptom cheaply and robustly" step (§3.1) regardless of
   which root cause(s) steps 1-2 identify, and is a natural complement (not a
   substitute) for any upstream fix. Given the gap is large (5-8pp) and consistent,
   even a simple 2-parameter Platt correction is likely to capture most of the
   calibration improvement; check whether it ALSO fixes O/U and BTTS markets (if those
   are similarly miscalibrated) as a useful diagnostic in itself.

4. **[Medium impact, medium cost] If step 1 confirms the EIV/attenuation signature,
   add a "ratings-reliability" covariate** (Glicko/TrueSkill-inspired, §2.1-2.2) —
   e.g., `min(matches_played_by_either_team_to_date)` or
   `years_since_team_entered_dataset`, possibly interacted with `elo_diff` — to
   `poisson_goals.py`. This is a cheap, additive change (one more GLM column) that
   lets the model learn a team/era-varying "trust" in the Elo-diff signal, directly
   addressing the heteroskedastic-measurement-error sub-issue (§1.3) without a full
   architectural rewrite to a Glicko/TrueSkill-style Bayesian rating system.

5. **[Lower priority, high cost — DEFER] Full SIMEX / errors-in-variables correction
   of `b2`, or a full TrueSkill-style Bayesian rating system replacing Elo.** Both are
   "formally correct" responses to the diagnosis but represent a large engineering
   investment; pursue only if steps 1-4 collectively fail to close most of the
   calibration gap, which would suggest the measurement-error problem is larger or
   more structural than a covariate-level patch can fix.

---

## Sources Index

- Pischke, S. (2007). "Lecture Notes on Measurement Error," LSE EC524.
  https://econ.lse.ac.uk/staff/spischke/ec524/Merr_new.pdf
- "Why Does Measurement Error Cause Attenuation Bias in Regression?"
  graduatestatisticstutor.com.
  https://graduatestatisticstutor.com/why-measurement-error-attenuation-bias
- "Empirical Bayes shrinkage (mostly) does not correct the measurement error in
  regression," arXiv:2503.19095 (2025). https://arxiv.org/html/2503.19095v1
- Glickman, M. "Example of the Glicko-2 system." https://glicko.net/glicko/glicko2.pdf
- "Glicko rating system," Wikipedia. https://en.wikipedia.org/wiki/Glicko_rating_system
- Herbrich, Minka & Graepel (2006). "TrueSkill(TM): A Bayesian Skill Rating System,"
  NeurIPS / Microsoft Research.
  https://www.microsoft.com/en-us/research/publication/trueskilltm-a-bayesian-skill-rating-system/
- "TrueSkill Ranking System," Microsoft Research project page.
  https://www.microsoft.com/en-us/research/project/trueskill-ranking-system/
- Vaughan Williams et al. "How well do Elo-based ratings predict professional tennis
  matches?" Nottingham Trent University.
  https://irep.ntu.ac.uk/id/eprint/42038/1/1400774_Vaughan_Williams.pdf
- "The Evaluation of Rating Systems in Online Free-for-All Games," arXiv:2008.06787.
  https://arxiv.org/pdf/2008.06787
- "The Evaluation of Rating Systems in Team-based Battle Royale Games,"
  arXiv:2105.14069. https://arxiv.org/pdf/2105.14069
- "Approaches for Credit Scorecard Calibration: An Empirical Analysis," ResearchGate.
  https://www.researchgate.net/publication/318702064_Approaches_for_Credit_Scorecard_Calibration_An_Empirical_Analysis
- Platt scaling, Wikipedia. https://en.wikipedia.org/wiki/Platt_scaling
- "Classifier calibration with Platt's scaling and isotonic regression," FastML.
  https://fastml.com/classifier-calibration-with-platts-scaling-and-isotonic-regression/
- "Algorithm journal: probability calibration in football prediction models,"
  foresportia.com (blog-level source, cited cautiously, opposite-direction
  miscalibration reported).
  https://www.foresportia.com/en/blog/algorithm-journal-football-prediction-probability-calibration.html
- "World Football Elo Ratings," Wikipedia.
  https://en.wikipedia.org/wiki/World_Football_Elo_Ratings
- "Elo ratings in football: Home field advantage," opisthokonta.net.
  https://opisthokonta.net/?p=592
- "Predicting Football Results with Poisson Regression," artiebits.com.
  https://artiebits.com/blog/predicting-football-results-with-statistical-modelling/
- "Estimating the change in soccer's home advantage during the Covid-19 pandemic
  using bivariate Poisson regression," AStA Advances in Statistical Analysis
  (Springer, 2021). https://link.springer.com/article/10.1007/s10182-021-00413-9
- "Extending the Dixon and Coles model: an application to women's football data,"
  arXiv:2307.02139 (already in `papers/extending_dixon_coles_2307.02139.pdf`) — cited
  for the international/heterogeneity discussion of negative goal-correlation.
- FiveThirtyEight `soccer-spi` data README (GitHub, archival proxy for the
  now-redirected fivethirtyeight.com methodology pages).
  https://github.com/fivethirtyeight/data/blob/master/soccer-spi/README.md
- Joshua Yazman, "Examining FiveThirtyEight's Soccer Power Index Ratings."
  https://joshyazman.github.io/spi-ratings-analysis/
- Hvattum & Arntzen (2010), already cited in `research_notes.md` §4 — re-cited here
  for the "Elo + ordered logit beats baselines but loses to bookmaker odds" finding,
  which parallels the tennis calibration-ratio finding above.
