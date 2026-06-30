# Football Forecasting Literature Notes — Jump Probability Cup Prep

Deep-read notes on 8 papers + cross-sport forecasting practice. Goal: build a mental
toolbox of models, scoring rules, and data requirements for predicting 2026 World Cup
matches under a weighted-Brier / RPS-style scoring system.

All papers live in `sportspredict_research/papers/`.

---

## 0. Quick recap — why this all matters for the Cup

- The Cup scores forecasts with a **weighted Brier score** (proper scoring rule —
  you cannot game it by hedging away from your true beliefs; honesty is optimal).
- Football outcomes are **3-way (Home/Draw/Away)** and **ordinal-ish** (a draw is
  "between" a home win and an away win in goal-difference terms) — this matters for
  which scoring rule is "fair" (see Constantinou & Fenton, §6).
- Two broad modelling families show up across all papers:
  1. **Goal-based models** (Poisson / bivariate Poisson / negative binomial on the
     scoreline), which you then sum to get H/D/A probabilities.
  2. **Rating-based models** (Elo, etc.) feeding a regression (ordered logit) that
     outputs H/D/A probabilities directly.
- A third theme: **how good are your probabilities, really?** — scoring rule
  decompositions (Murphy 1973, Foulley 2021/2106.14345) tell you whether your model's
  weakness is *calibration* (reliability) or *sharpness* (resolution/discrimination).
- A fourth theme: **wisdom of crowds** — averaging/aggregating many forecasts (or
  combining your model with bookmaker odds) is a very strong, very cheap baseline.

---

## 1. Dixon & Coles (1997) — "Modelling Association Football Scores and
Inefficiencies in the Football Betting Market"

**Status:** paywalled (JRSS Series C). Reconstructed via the Sarmanov-family paper
(Michels, Ötting & Karlis 2023, arXiv:2307.02139, fully read — see §6 below, which
states the DC model *exactly* as a special case of the Sarmanov family) plus the
dashee87 blog walkthrough (gathered earlier in this research).

### 1.1 The model

Two **independent** Poisson distributions for home goals (X) and away goals (Y) in a
match between home team *i* and away team *j*:

```
X ~ Poisson(λ)      λ = α_i · β_j · γ      (home goals)
Y ~ Poisson(μ)      μ = α_j · β_i          (away goals)
```

- `α_i` = **attack strength** of team *i*
- `β_i` = **defence weakness** of team *i* (higher β = worse defence, since it
  multiplies the opponent's λ up)
- `γ` = **home advantage** multiplier (γ > 1 typically)
- In log-linear/GLM form (used in practice, e.g. via `glm(..., family=poisson)`):
  `log(λ) = home + att_i + def_j`, `log(μ) = att_j + def_i`
  — this is literally a Poisson regression with team dummy variables for attack and
  defence, plus a home-effect dummy. (This exact log-linear form is also used in
  Foulley 2021, eq. for the Poisson loglinear model — see §7.)
- Identifiability constraint needed: e.g. sum-to-zero or fix-one-team's defence to
  zero (the Sarmanov paper uses sum-to-zero on defence parameters).

### 1.2 The "Dixon-Coles tau" correction (low-score dependence)

Independent Poisson under-predicts the frequency of **0-0 and 1-1 draws** and
mis-predicts **1-0 / 0-1** scorelines relative to reality (goals aren't quite
independent at low scores — a major early goal changes both teams' tactics). DC fix
this by multiplying the independent-Poisson joint probability by a correction factor
**τ** that only touches the four low-score cells:

```
P(X=x, Y=y) = τ_{λ,μ}(x,y) · Pois(x; λ) · Pois(y; μ)

τ_{λ,μ}(x,y) =
    1 − λμρ        if x=0, y=0
    1 + λρ         if x=0, y=1
    1 + μρ         if x=1, y=0
    1 − ρ          if x=1, y=1
    1              otherwise (x≥2 or y≥2)
```

- `ρ` is a single **dependence parameter** estimated from the data, typically small
  and *negative* in men's football (around −0.1 to −0.2 in the original data).
- Validity constraint: `max(−1/λ, −1/μ) ≤ ρ ≤ min(1/(λμ), 1)` so that all
  probabilities stay non-negative.
- **Important modern finding** (from the Sarmanov-family paper, §6.3 below): this τ
  correction can ONLY produce a narrow range of correlation between home/away goals
  (lower bound around −0.05 to −0.08 for typical λ's). Real-world correlations,
  especially in women's football, can be much more negative (−0.25 to −0.40), so DC's
  correction is "good but limited." For men's top leagues it's usually adequate.

### 1.3 Time-decay weighting (recency)

DC weight each historical match by an exponentially decaying function of how long ago
it was played, so the model emphasizes recent form:

```
φ(t) = exp(−ξ · t)        t = days since the match was played, ξ > 0
```

This weight `φ(t)` multiplies each match's contribution to the log-likelihood. The
half-life of influence is `ln(2)/ξ`. In the original DC paper, ξ ≈ 0.0065/day (a
roughly half-life of ~3 months), but this is a tunable hyperparameter — too small and
you ignore recent form swings (transfers, managerial changes); too large and your
sample becomes too noisy/small.

### 1.4 Likelihood & estimation

Full log-likelihood across all matches m, with parameters θ = {α_i, β_i for all
teams, γ, ρ}:

```
log L(θ) = Σ_m φ(t_m) · [ log τ_{λ_m,μ_m}(x_m,y_m) + log Pois(x_m;λ_m) + log Pois(y_m;μ_m) ]
```

Maximize numerically (e.g. `optim()`/`nlm()` in R — the Michels/Ötting/Karlis paper
literally uses `nlm()`). ρ, γ and all team α/β are estimated jointly.

### 1.5 From scoreline probabilities to H/D/A probabilities

Once you have the joint pmf `P(X=x,Y=y)` for all (x,y) up to some max goal count
(e.g. 0-10), sum:

```
P(Home win) = Σ_{x>y} P(X=x,Y=y)
P(Draw)     = Σ_{x=y} P(X=x,Y=y)
P(Away win) = Σ_{x<y} P(X=x,Y=y)
```

This is exactly the structure used later in Foulley (2021), eq. for `Pr(X_ij=[1]|y)`
etc. (§7.4 below).

### 1.6 Why this is still a great first model in R

- It's a 2×(N teams)+2 parameter model (attack/defence per team + home advantage +
  ρ), trivially fit via `optim`/`bbmle`/`glm` tricks.
- It directly outputs full scoreline distributions → you can compute H/D/A AND
  over/under AND correct-score probabilities from one fit.
- It's the common ancestor of nearly every paper in this list (Karlis-Ntzoufras,
  Crowder et al., the Sarmanov-family extension are all "what's next after DC97").

---

## 2. Karlis & Ntzoufras (2003) — "Analysis of Sports Data by Using Bivariate
Poisson Models" (FULLY READ, 13 pp.)

**Source:** http://www2.stat-athens.aueb.gr/~jbn/papers2/08_Karlis_Ntzoufras_2003_RSSD.pdf

### 2.1 Motivation

DC's τ-correction only nudges 4 scoreline cells and only allows weak/negative
correlation. K&N instead model the **correlation directly** via a genuine bivariate
Poisson distribution — this is the natural "next step" referenced explicitly by the
Sarmanov-family paper.

### 2.2 The Bivariate Poisson distribution

Built via **trivariate reduction**: let `Z1, Z2, Z3` be independent Poisson with
means `λ1, λ2, λ3`. Define:

```
X1 = Z1 + Z3
X2 = Z2 + Z3
```

Then `(X1,X2) ~ BP(λ1, λ2, λ3)`, with:
- `E(X1) = λ1 + λ3`, `E(X2) = λ2 + λ3`
- `Cov(X1,X2) = λ3` (so λ3 directly controls the correlation — and it can only be
  ≥ 0, i.e., this base BP model can only capture **positive** correlation)
- Marginals: `X1 ~ Poisson(λ1+λ3)`, `X2 ~ Poisson(λ2+λ3)` (each marginal is still
  Poisson — nice property)
- If λ3 = 0, X1 ⊥ X2 (reduces to the independent double-Poisson model)

### 2.3 Joint pmf (the key formula, Eq. 1 in the paper)

```
P(X1=x1, X2=x2) = exp(−λ1−λ2−λ3) · (λ1^x1/x1!) · (λ2^x2/x2!)
                  · Σ_{k=0}^{min(x1,x2)} C(x1,k) C(x2,k) k! (λ3/(λ1λ2))^k
```

This is the core formula — it's a Poisson product times a correction polynomial sum
in `k` (the "shared" Poisson component).

### 2.4 Estimation: EM algorithm

Because the model is a sum of latent Poissons, K&N derive an **EM algorithm**:
- E-step: compute `E[Z3 | X1=x1, X2=x2]` — the expected value of the "shared" latent
  count given observed (x1,x2). This has closed form in terms of the BP pmf.
- M-step: re-estimate λ1, λ2, λ3 (and any regression coefficients on them) via
  weighted Poisson GLM regressions using the E-step pseudo-data.
- Iterate to convergence. This is much faster/more stable than direct numerical ML
  for the BP likelihood, especially once λ's depend on covariates via log-links.

### 2.5 Football application model (Eq. 6)

For match between home team `h` and away team `a`:

```
log(λ1) = μ + home + att_h + def_a       (home goals mean component)
log(λ2) = μ + att_a + def_h              (away goals mean component)
log(λ3) = β0  (constant)   or   log(λ3) = β0 + β1·(some covariate)
```

λ3 (the covariance term) can be modeled as a **constant** across all matches (simplest
case — assumes homogeneous correlation) or with covariates. Sum-to-zero constraints
on attack/defence params for identifiability, as in DC.

### 2.6 Diagonal-inflated bivariate Poisson (Eq. 5) — fixing the draw problem

Even the BP model under-predicts **draws** (the diagonal X1=X2 in the scoreline
matrix), especially 1-1 and 2-2. The fix: a finite mixture —

```
P(X1=x1,X2=x2) = (1−p)·BP(x1,x2;λ1,λ2,λ3)              if x1≠x2
P(X1=x1,X2=x2) = (1−p)·BP(x1,x2;λ1,λ2,λ3) + p·D(x1;λ)   if x1=x2
```

where `D(·;λ)` is some distribution over the diagonal (e.g., another Poisson or just
point masses on 0-0/1-1/2-2), and `p` is an inflation probability estimated from data.
This is conceptually identical in spirit to DC's τ correction but more flexible and
statistically principled (an actual mixture model rather than an ad-hoc multiplier).

### 2.7 Model selection (AIC/BIC tables)

The paper compares: independent double Poisson, BP (constant λ3), BP with λ3
depending on covariates, and diagonal-inflated versions, on both football data and
(separately) water-polo data. Findings:
- BP with constant λ3 already beats independent Poisson (AIC/BIC).
- Diagonal inflation gives further improvement, particularly for football where draws
  (and especially 0-0/1-1) are systematically under-fit by plain BP.
- The water-polo application is included to show the BP/diagonal-inflation framework
  generalizes beyond football to any "two competing counts" sport.

### 2.8 Practical takeaway for our R modelling

- BP (`λ3` constant) is a relatively easy upgrade from independent-Poisson: fit via
  EM or directly via `bivpois` package in R (which implements exactly this model).
- If draws are still under-predicted after BP, add diagonal inflation.
- λ3 ≥ 0 constraint means BP can't capture *negative* home/away goal correlation — and
  Foulley (2021) finds real Champions League data has ρ ≈ −0.19 to −0.24 (negative!).
  So for some competitions, BP's positive-only correlation may be the wrong sign — a
  copula-based approach (McHale & Scarf 2011, cited in multiple papers here) or the
  Sarmanov/ANS family (§6) might fit better.

---

## 3. Crowder, Dixon, Ledford & Robinson (2002) — "Dynamic Modelling and
Prediction of English Football League Matches for Betting"

**Status:** paywalled (JRSS Series D / Statistician). Notes from secondary sources
(abstracts, citing literature) — could not access full text or exact equations.

### 3.1 Core idea

Takes the DC97 framework and makes attack/defence parameters **time-varying** rather
than fixed for a whole season — i.e., turns DC97 into a **non-Gaussian state-space
model**:

```
attack_i(t), defence_i(t)  →  evolve over time via an unobserved bivariate
                                stochastic (autoregressive) process
```

Conceptually: `(att_i(t), def_i(t)) = ρ_AR · (att_i(t-1), def_i(t-1)) + noise(t)` —
team strengths follow a random walk / AR(1)-type process that can drift up or down
match-by-match (a team going on a hot/cold streak shows up as drift in att/def).

This is explicitly the dynamic analogue of Elo (which also updates ratings
match-by-match) but built on top of the Poisson-scoreline DC structure rather than
a simple win/loss/draw rating.

### 3.2 Estimation challenge & their solution

Exact inference in non-Gaussian state-space models requires either particle filters
or numerical integration — expensive for ~92 teams × 5 seasons. Crowder et al.
propose a **fast approximation** for parameter estimation and signal extraction
(filtering/smoothing the att/def trajectories) that the literature describes as
"computationally convenient and fast," with results "comparing very favourably" to
the static DC97 approach — i.e., better predictive accuracy for similar computational
cost, achieved without the heavy machinery of, e.g., Rue & Salvesen (2000)'s fully
Bayesian dynamic approach.

### 3.3 Data

92 teams across the four English divisions (top flight + 3 lower divisions),
1992–1997 — i.e., a genuinely large multi-season, multi-division panel. Using all
four divisions (not just the Premier League) gives far more matches per "epoch,"
which helps estimate time-varying parameters that would otherwise be data-starved if
restricted to ~380 top-flight matches/season.

### 3.4 Relevance to our R build

- A full from-scratch implementation of this is hard (no formulas available), BUT the
  *spirit* is achievable cheaply: refit your DC/BP model on a **rolling window**
  (e.g., last N matches or last 1–2 seasons) instead of one fixed full-history fit,
  or combine DC's exponential time-decay (§1.3) with periodic re-estimation. This
  approximates "time-varying strengths" without needing a full state-space filter.
- More modern open literature (found while researching this paper) extends this idea
  further: arXiv:2308.02414 "A State-Space Perspective on Modelling and Inference for
  Online Skill Rating" and a 2025 paper "Bayesian weighted discrete-time dynamic
  models for association football prediction" (arXiv:2508.05891) — both descendants
  of this Crowder et al. line of work, worth a look if we want to go deeper later.

---

## 4. Hvattum & Arntzen (2010) — "Using ELO Ratings for Match Result Prediction in
Association Football"

**Status:** paywalled (Int. J. Forecasting). Notes from secondary sources (academia.edu
preview + abstracts).

### 4.1 Standard Elo update

```
ℓ¹_h = ℓ⁰_h + K · (α_h − γ_h)

γ_h = 1 / (1 + c^((ℓ⁰_a − ℓ⁰_h)/d))     ← expected score for home team
α_h = actual result: 1 (win), 0.5 (draw), 0 (loss)

Standard params: c = 10, d = 400, K = 20
```

(Same skeleton as chess Elo — `c=10, d=400` is the chess convention so a 400-point
gap implies a 10:1 expected-score ratio.)

### 4.2 Goal-based Elo variant (ELOg)

K-factor scales with margin of victory:

```
K_eff = K0 · (1 + δ)^λ
```
where δ = |goal difference|, K0 = 10, λ = 1 (paper's chosen values). Bigger wins move
ratings more — same idea independently re-derived in FiveThirtyEight's NFL/NBA Elo
(§9 below) decades later, suggesting it's a robust, repeatedly-rediscovered
improvement.

### 4.3 From rating difference to H/D/A probabilities: ordered logit

The single covariate is the **rating difference** `x = ℓ_home − ℓ_away` (optionally
plus a home-advantage constant baked into ℓ_home or as a separate term). An
**ordered logistic regression** ("ordered logit") with two cutpoints `κ1 < κ2` maps x
to three ordered categories (Away win < Draw < Home win, or vice versa depending on
sign convention):

```
P(Away win) = logistic(κ1 − β·x)
P(Draw)     = logistic(κ2 − β·x) − logistic(κ1 − β·x)
P(Home win) = 1 − logistic(κ2 − β·x)
```

where `logistic(z) = 1/(1+e^{-z})`. β and the cutpoints κ1, κ2 are fit by maximum
likelihood on historical (rating-diff, outcome) pairs. This is the generic
**proportional-odds ordered logit model** — fit in R via `MASS::polr()` or
`ordinal::clm()`. Intuition: as rating difference x grows, probability mass shifts
monotonically from "away win" through "draw" to "home win," and the two cutpoints
carve up the latent continuous "skill difference → score difference" scale into the
three discrete outcomes.

### 4.4 Data

14 seasons (1993/94–2007/08), top 4 divisions of the English league system, 30,524
matches, sourced from **football-data.co.uk** (a free, well-known source for
historical results + closing bookmaker odds — good candidate source for our own R
data pipeline). Split: 2 seasons to seed initial Elo ratings, 5 seasons to fit the
ordered-logit parameters, 8 seasons (14,927 matches) held out for testing.

### 4.5 Benchmarks & evaluation

Compared against: uniform (1/3,1/3,1/3), historical outcome frequencies, two
"kitchen-sink" ordered logit models from Goddard (2005) using 50/100 covariates
(team form, league position, etc.), and bookmaker-implied probabilities (average and
maximum across bookmakers).

Evaluation: **quadratic loss (= Brier score)**, **informational/log loss**, paired
t-tests; plus economic backtests (flat bet, Kelly criterion).

### 4.6 Headline result

ELO-based ordered logit **beats** uniform/frequency/Goddard's covariate-heavy models
on statistical loss, but **loses to bookmaker odds**. No method (including bookmaker
odds) is reliably profitable after the bookmaker's margin. Authors conclude: "market
odds serve as a superior benchmark," and recommend combining model output with market
information rather than treating either as sufficient alone — directly supports the
"wisdom of crowds" theme in §8.

### 4.7 Why this matters for the Cup

- Elo is dramatically simpler than DC/BP (no per-team attack/defence params, no
  scoreline distribution) yet "good enough" — a great **baseline model** to build
  first and compare your fancier Poisson models against (per the original
  recommendation).
- The ordered-logit recipe (§4.3) is directly reusable: take ANY single-number team
  strength metric (Elo, FIFA ranking points, an SPI-style composite, even your
  Poisson model's implied "expected goal difference") and turn it into calibrated
  H/D/A probabilities via `polr()`.
- The 3-way split of data (seed ratings → fit regression → test) is the right
  template for our own backtesting.

---

## 5. Murphy (1973) — "A New Vector Partition of the Probability Score"

**Status:** paywalled (J. Applied Meteorology). Fully reconstructed via Foulley
(2021)/arXiv:2106.14345, which states and uses Murphy's decomposition directly (their
Eq. 1, attributed to Murphy 1973).

### 5.1 The decomposition (the central formula)

For a binary event with true probability `q`, forecast `P` (random variable), and
binary outcome `X`:

```
E[S(P,X)] = Var(X) − E_P{ [E_X(X|P) − E_X(X)]² } + E_P{ [E_X(X|P) − P]² }
          = UNC          −  RES                   +  REL
```

where `S(P,X) = (P−X)²` is the (half-)Brier score. Three terms:

1. **Uncertainty (UNC)** = `Var(X) = q(1−q)` — the inherent unpredictability of the
   event itself. Out of the forecaster's control; it's the Brier score you'd get from
   a "climatology" forecast (always predicting the long-run base rate).
2. **Resolution (RES)** = `E_P{[E_X(X|P) − E_X(X)]²}` — how much the conditional
   outcome rate, given different forecast values, *varies* around the overall base
   rate. High resolution = your forecasts actually distinguish different real-world
   situations (good and bad). **Higher RES is better** (it's subtracted).
3. **Reliability (REL)** = `E_P{[E_X(X|P) − P]²}` — average squared gap between "what
   actually happens when you say P%" and "P% itself." This is **calibration**.
   **Lower REL is better.**

So: `Brier score = UNC − RES + REL`. A "perfectly calibrated but useless" forecaster
(always predicts the base rate q) has REL=0, RES=0, Brier=UNC — this is the
**reference/worst-useful** score.

### 5.2 Brier Skill Score (BSS)

```
BSS = 1 − BS/BS_ref = (RES − REL) / UNC
```

BSS > 0 means you're beating the "always predict the base rate" forecaster. This is
the natural metric to track: **maximize (RES − REL)/UNC**, i.e., be both
well-calibrated (low REL) AND discriminating (high RES).

### 5.3 Estimating REL/RES from real data — the practical recipe

Given N (forecast, outcome) pairs `{(p_i, x_i)}`:
- If forecasts take only K distinct values `p_k` (k=1..K), with `n_k` instances and
  empirical outcome rate `x̄_k = (Σ outcomes where p_i=p_k)/n_k`:
  ```
  REL = (1/N) Σ_k n_k (x̄_k − p_k)²
  RES = (1/N) Σ_k n_k (x̄_k − x̄)²
  UNC = x̄(1−x̄)
  ```
- In practice (continuous forecasts), **bin** your forecasts (fixed-width bins,
  quantile bins, or — best — isotonic regression / pool-adjacent-violators (PAV)
  algorithm) and apply the same formulas to the binned `(p_d, x̂_d)` pairs.
- A clean, numerically robust shortcut (Siegert 2017, used in §7): compute the mean
  Brier score three ways —
  ```
  S̄(p̂)   = mean score of your actual forecasts vs outcomes
  S̄(x̂)   = mean score using the *recalibrated* forecast (the binned x̂_d) vs outcomes
  S̄(x̄·1) = mean score of the constant "always predict overall mean" forecast
  ```
  then `REL = S̄(p̂) − S̄(x̂)`, `RES = S̄(x̄·1) − S̄(x̂)`, `UNC = S̄(x̄·1)`. This
  automatically satisfies `S̄(p̂) = REL − RES + UNC` exactly, even with continuous
  forecasts.

### 5.4 Why this is THE key diagnostic for the Cup

After every batch of World Cup predictions resolves, you can compute REL and RES for
your H/D/A forecasts (treat each as a separate binary event, "one-vs-rest," per
Foulley §7.5). This tells you:
- High REL (poor calibration) → you're systematically over/under-confident. Fix:
  recalibrate (Platt scaling / isotonic regression / just shrink toward 1/3).
- Low RES (poor resolution/discrimination) → your model isn't distinguishing
  "obviously Brazil beats minnow" from "50/50 toss-up" enough. Fix: better features /
  stronger model, not recalibration.
- This separates "I need a better model" from "I need to trust my model less and
  shrink toward the mean" — two completely different fixes that a single Brier
  number can't distinguish.

---

## 6. Reade, Singleton & Brown framing aside — Constantinou & Fenton (2012) —
"Solving the Problem of Inadequate Scoring Rules for Assessing Probabilistic
Football Forecast Models" (FULLY READ, 11 pp.)

**Source:** http://constantinou.info/downloads/papers/solvingtheproblem.pdf

### 6.1 The core argument

Football has **3 ordered-ish outcomes** (Home win / Draw / Away win — really think of
it as a goal-difference axis: Away win ↔ negative GD, Draw ↔ GD=0, Home win ↔
positive GD). Many popular scoring rules **ignore this ordinal structure** and treat
H/D/A as unordered nominal categories — this systematically misranks forecasters.

### 6.2 The Rank Probability Score (RPS) — THE formula to know

For `r` ordered outcomes, forecast vector `p = (p_1,...,p_r)`, actual outcome vector
`e = (e_1,...,e_r)` (one-hot, e.g. away win = (1,0,0), draw=(0,1,0), home win=(0,0,1)
— ordered consistently with the GD axis):

```
RPS = (1/(r-1)) · Σ_{i=1}^{r-1} ( Σ_{j=1}^{i} (p_j − e_j) )²
```

For football (r=3), with outcomes ordered [Away, Draw, Home]:

```
RPS = (1/2) · [ (p_A − e_A)² + (p_A+p_D − e_A−e_D)² ]
```

i.e., it penalizes errors in the **cumulative distribution function** of the
forecast vs. the actual outcome — predicting "Away" when "Home" happened is penalized
*more* than predicting "Draw" when "Home" happened, because RPS respects the ordering.
Brier score (treating outcomes as nominal) penalizes both errors equally, which is
"unfair" in football because Away-vs-Home is a "bigger miss" than Draw-vs-Home.

**RPS is lower-is-better, range [0,1].**

### 6.3 The 5 benchmark scenarios (Table 1) — the diagnostic test suite

The paper defines 5 canonical forecast scenarios to stress-test scoring rules:
1. A "perfect" forecaster (always assigns 100% to the correct outcome).
2. A forecaster who is well-calibrated but never very confident (e.g., always
   something like 50/30/20 in the right order).
3. A forecaster confidently and consistently wrong about the *direction* (predicts
   Home strongly when Away happens) — should be penalized HARD.
4. A forecaster confidently wrong but only by "one category" (predicts Draw strongly
   when Home/Away happens) — should be penalized LESS than scenario 3.
5. A forecaster who is "uniformly uncertain" (always 1/3,1/3,1/3) — should score
   worse than a calibrated-but-modest forecaster (scenario 2) but not be punished as
   badly as confidently-wrong forecasters.

**Key test:** does a scoring rule rank scenario 3 worse than scenario 4? Brier score
(and several others) FAIL this test in certain configurations — they can rank an
"opposite-direction-confident" forecaster as no worse (or even better) than a
"one-category-off" forecaster. RPS passes.

### 6.4 Other scoring rules examined and critiqued (Appendix has exact formulas)

- **Brier Score**: `Σ_i (p_i − e_i)²` — doesn't respect outcome ordering (the core
  critique).
- **Geometric Mean (of probabilities assigned to the actual outcomes)** — sensitive
  to a single very-low probability assigned to an outcome that occurs (can blow up /
  go to zero), and also ignores ordering.
- **Information/Logarithmic Loss**: `−log(p_actual)` — same ordering-blindness issue,
  plus unbounded penalty for confident-wrong predictions (a single 0.001 forecast
  that resolves "true" tanks your whole average).
- **MLLE (Mean Log Likelihood-type)** and **Binary Decision** scores — both shown to
  have pathological behavior in at least one of the 5 scenarios.
- **Quadratic Loss** — essentially Brier under another name; same critique applies.

### 6.5 Direct relevance to the Jump Probability Cup

- **The Cup itself uses a "weighted Brier score,"** not RPS. Per Constantinou &
  Fenton, plain Brier can under-penalize "confidently wrong about direction" vs.
  "wrong by one category" — so it MIGHT be slightly more forgiving of, e.g.,
  predicting a strong Home win that becomes a strong Away win, vs. predicting a
  draw that becomes a Home win. Whatever the Cup's exact "weighting" is, it's worth
  checking empirically (simulate the 5 benchmark scenarios under the Cup's actual
  formula) whether it behaves more like Brier or more like RPS — this affects
  whether you should ever place a "confident directional" bet vs. hedge toward the
  draw when uncertain.
- Practically: **when genuinely uncertain about direction (could go either way),
  shifting some probability mass toward Draw is "safer" under RPS-like scoring than
  spreading it 50/50 between Home and Away** — because a Draw outcome is "closer" on
  the ordinal scale to either Home or Away than Home and Away are to each other.
  Whether this applies under the Cup's weighted Brier needs to be checked, but it's
  a testable, concrete strategic implication.

---

## 7. Foulley (2021) — "More on Verification of Probability Forecasts for Football
Outcomes: Score Decompositions, Reliability and Discrimination Analyses"
(arXiv:2106.14345, FULLY READ, 23 pp.)

**Source:** arxiv.org/pdf/2106.14345

This paper is the modern, football-specific sequel to Murphy (1973) and Yates (1982),
applied to 4 seasons of UEFA Champions League group-stage data. It's the single most
"practically actionable" paper for self-evaluating our forecasts.

### 7.1 Three decompositions of the (half-)Brier score, all related

**(a) Calibration-Refinement (CR) / Murphy decomposition** (already covered in §5.1):
```
E[S(P,X)] = UNC − RES + REL
```

**(b) Likelihood-Base (LB) factorization (Eq. 2)**:
```
E[S(P,X)] = Var(P) − Var_X[E_P(P|X)] + E_X{[E_P(P|X) − X]²}
          = REF     − DIS              + CB2
```
- **REF (Refinement / Sharpness)** = `Var(P)` — how spread-out your forecasts are.
  A forecaster who always says exactly 30% has REF=0 (no sharpness at all).
- **DIS (Discrimination)** = `Var_X[E_P(P|X)]` — variance, across the two outcome
  groups (X=0 vs X=1), of the *average forecast given that outcome*. High DIS means
  your average forecast was very different for matches that ended up X=1 vs X=0 —
  i.e., your forecasts "discriminate" between future winners and losers.
- **CB2 (Type-2 conditional bias)** = `E_X{[E_P(P|X) − X]²}` — counterpart to
  resolution, from the "outcome-given-forecast" direction reversed.

**(c) Yates (1982) 5-component decomposition (Eq. 4)**:
```
E[S(P,X)] = UNC − 2·COV(P,X) + VPB + VPW + RIL
```
- **COV(P,X)**: covariance between forecast and outcome — **the single biggest
  "good" component** in their empirical results (41-55% of UNC!). This is the most
  basic measure: do higher forecasts correlate with the event actually happening?
- **VPB (variance "between")** = variance of the *mean* forecast across the two
  outcome groups = identical to DIS above.
- **VPW (variance "within")** = average *within-group* variance of forecasts
  ("scattered variance" / noise) — this is "detrimental": it represents forecast
  variability that does NOT track the outcome.
- **RIL (Reliability-In-the-Large)** = squared difference between mean forecast and
  mean outcome (overall/marginal bias — a single number, simpler than full REL).
- Identities linking (b) and (c): `VPB = DIS`, `VPB + VPW = REF`,
  `CB2 = UNC − 2·COV + VPB + RIL`.

### 7.2 Practical estimation recipe (Eq. 5-7) — directly codeable in R

```
S̄(p) = (1/N) Σ S(p_i, x_i)                    # mean empirical Brier score

REL = S̄(p̂) − S̄(x̂)
RES = S̄(x̄·1_N) − S̄(x̂)
UNC = S̄(x̄·1_N)
```
where `x̂_i` = recalibrated/binned forecast (via isotonic regression / PAV is
recommended as "best practice" — avoids arbitrary bin-width choices), and `x̄·1_N` =
constant vector of the overall outcome mean. **This decomposition works for ANY
proper scoring rule**, not just Brier — they explicitly note it generalizes to the
ignorance/log score `L(P,X) = −X log(P) − (1−X) log(1−P)`.

### 7.3 Reliability diagrams & statistical tests

- **Reliability diagram**: plot binned forecast value `p_d` (x-axis) vs. observed
  conditional event proportion `x̂_d` (y-axis, "Conditional Event Probability," CEP).
  Perfect calibration = the 45° line. The paper uses **isotonic regression (PAV
  algorithm)** to choose bins non-parametrically (cited: Dimitriadis, Gneiting &
  Jordan 2021, PNAS — "stable reliability diagrams").
- **Logistic recalibration test** (Cox 1958): fit
  `logit[Pr(X=1)] = α + β·logit(p)`. α=0,β=1 = perfectly calibrated.
  - α>0, β=1 → systematic **under-forecasting** (concave reliability curve)
  - α<0, β=1 → systematic **over-forecasting** (convex curve)
  - α=0, β>1 → **sigmoid** (over-confident at extremes, under-confident in middle)
  - α=0, β<1 → **inverse-sigmoid** (under-confident at extremes — too cautious)
  Wald/LR tests give p-values for departure from (0,1).
- **Discrimination diagram**: similar but plots CEP vs. forecast with marginal
  histograms shown on both axes — visualizes both calibration and how spread-out
  (sharp) your forecast distribution is.
- **Brier-score test** (Spiegelhalter 1986; Seillier-Moiseiwitsch & Dawid 1993): a
  formal test of `H0: perfectly calibrated` based on the decomposition — gives a
  Z-statistic / p-value (used throughout their tables, e.g., "B-TEST" column).
- **Harrell's C-statistic** (= AUC of ROC curve): measures discrimination ability,
  0.5 = no discrimination, 1.0 = perfect. Their Table 3 reports C ≈ 0.79-0.82 for
  Home/Away win forecasts but only ≈ 0.62 for Draw — **Draw is fundamentally the
  hardest outcome to discriminate**, a finding echoed everywhere in this literature.

### 7.4 Their statistical model (a clean, modern Poisson regression — Appendix A)

```
y_ij,k | λ_ij,k^(t) ~ Poisson(λ_ij,k^(t)),  k=1 (home goals), 2 (away goals)

log λ_ij,1 = η + h + β1·Δr_ij + β2·r̄_ij
log λ_ij,2 = η + β1·Δr_ji + β2·r̄_ij

Δr_ij = r_i − r_j   (ELO rating difference, attacker i vs defender j)
r̄_ij  = ½(r_i + r_j)   (ELO rating average)
```
- `η` = intercept, `h` = home effect, `β1` = effect of rating *difference* (team
  quality gap), `β2` = effect of rating *average* (overall match quality/openness).
- **ELO ratings standardized**: `r_i^(t) = (ELO_i^(t) − 1800)/150` — this
  standardization (centering at 1800, scaling by 150) makes the regression
  coefficients interpretable and numerically well-behaved. **Concretely useful for
  our R code**: don't feed raw Elo numbers (1400-2100 range) into a regression —
  rescale first.
- Bayesian estimation (vague/non-informative priors: N(0,10⁴) for η,h; N(0,10³) for
  β's) via WinBUGS/OpenBUGS, with **3-season rolling training windows** (train on
  seasons t-3,t-2,t-1 → forecast season t group stage). This is exactly the
  "rolling re-fit" practical alternative to Crowder et al.'s state-space model
  mentioned in §3.4.
- **Only 4 parameters** beyond team-specific stuff (η, h, β1, β2) — deliberately
  "parsimonious" (their word). Yet achieves good calibration (REL = 3.6-5.3% of UNC)
  and decent resolution (25-30% of UNC) for Home/Away — comparable to bookmaker odds
  resolution (which is 31-35%, slightly better, as expected).

### 7.5 Multi-category (3-outcome) handling

CR decomposition doesn't extend cleanly to 3+ categories (binning is awkward in
higher dimensions — Bröcker 2012 has proposed methods). The pragmatic solution used
throughout: **treat each of {Home win, Draw, Away win} as a separate one-vs-rest
binary event**, compute REL/RES/UNC/Brier for each separately (their Tables 1, 4, 5
all do exactly this), then optionally combine (sum/average) for an overall picture.
Yates' decomposition extends more easily to multi-category (just compute it 3x, one
per outcome).

### 7.6 Negative home/away goal correlation — a specific empirical finding

They derive (Appendix B) a **closed-form expression for the implied correlation**
between home and away goals under a Poisson log-linear model with a shared rating-
difference covariate of opposite sign in each team's linear predictor:

```
ρ_12 = [√(μ1μ2) · (e^{−β²γ} − 1)] / [√(1+μ1(e^{β²γ}−1)) · √(1+μ2(e^{β²γ}−1))]
```
where μ_k = exp(η_k)·exp(β²γ/2), and γ = Var(Δr) (=2 here due to standardization).
This is **always negative for β≠0** — i.e., a Poisson model where both teams' λ's
depend on the *same* rating-difference covariate (with opposite signs) **automatically
induces negative home/away goal correlation**, no τ-correction or BP λ3 needed!
Estimated ρ_12 = −0.19 vs. observed −0.235 (95% CI: [−0.45,−0.06] across seasons,
2014-2019 CL data) — good agreement. **This is a strong argument for including a
team-quality-difference covariate (Elo difference) directly in a simple Poisson
model**, rather than relying solely on DC's τ or BP's λ3 to capture goal dependence.

### 7.7 Their data & comparison benchmark

- 4 seasons (2017-2020) UEFA Champions League group stage, 384 matches, 96/season.
- Bookmaker odds (ODD) from **OddsPortal**, averaging 10-12 bookmakers' odds,
  3-way-normalized: `p_{m,j} = o_{m,j}^{-1} / Σ_k o_{m,k}^{-1}`. (This
  "de-vig"/normalization formula is the standard way to convert odds → probabilities
  and is directly reusable.)
- Conclusion: their simple Poisson+Elo model is well-calibrated and has decent
  resolution/discrimination, but **bookmaker odds remain superior** (resolution 34.5%
  vs 29.5% for Home win; discrimination 7.7% vs 5.8%) — yet another confirmation that
  market odds are a tough benchmark, and a great "blend with the market" signal if
  available for World Cup matches.

---

## 8. "Wisdom of the Crowds: Forecasting the 2018 FIFA World Cup" (arXiv:2008.13005,
FULLY READ, 32 pp.)

This is the most directly analogous prior "competition" to the Jump Probability Cup —
a public contest (fifaexperts.com, 2018) where many participants submitted H/D/A
probability forecasts for all 64 World Cup matches, scored via Brier score.

### 8.1 Scoring & the S* transform

Standard half-Brier per match per participant:
```
S = Σ_{outcomes i} 1(θ=θ_i)(1−P_i)² + Σ_{i: θ≠θ_i} P_i²
```
i.e., `(1−P_correct)² + P_wrong1² + P_wrong2²` — same structure as the Cup's
per-match scoring. They also define a transform `S* = 1 − 2S` (or similar rescaling)
to map the Brier score onto a more interpretable [-1,1]-ish "skill" scale for
leaderboard display — mostly a presentation device.

### 8.2 Aggregation strategies tested (the "wisdom of crowds" menu)

1. **Local Wisdom (simple average)**: for each match, average all participants'
   `(p_H, p_D, p_A)` forecasts (then renormalize to sum to 1). Extremely simple,
   surprisingly strong.
2. **Global Wisdom (market consensus)**: use bookmaker/betting-market implied
   probabilities directly as "the crowd."
3. **Top-n averaging**: average only the top-n performing participants from a
   training period (e.g., top 10 by cumulative Brier on earlier matches), under the
   theory that consistently good forecasters' errors are less correlated /
   higher-quality than the full crowd's.
4. **Budescu & Chen (2014) weighted aggregation**: weight each participant's forecast
   by a "contribution weight" derived from their historical performance *relative to
   the group* — specifically based on a **regret-minimization** framework: a
   forecaster's weight increases if removing them from the aggregate would have made
   the aggregate's past performance worse (i.e., they contributed positively), and
   decreases otherwise. Iteratively re-weights based on out-of-sample contribution.
5. **ISP-η (Individual Sequence Prediction with exponential weighting)**: an online-
   learning / "expert advice" algorithm — maintains a weight per forecaster that's
   updated multiplicatively based on recent performance: `w_i ← w_i · exp(−η · loss_i)`,
   then normalizes. η controls how fast the algorithm "forgets" old performance and
   shifts trust toward currently-hot forecasters. Comes with theoretical regret
   bounds from online learning theory (no-regret guarantees vs. the best fixed
   forecaster in hindsight).

### 8.3 Results (Table 2 — final rankings)

- **Aggregation strategies (especially simple averaging / Local Wisdom and the
  market-based Global Wisdom) ranked at or near the TOP of the entire leaderboard**,
  beating the vast majority of individual human/model participants.
- The betting market (Global Wisdom) was extremely hard to beat — consistent with
  every other paper in this collection.
- Top-n averaging and the more sophisticated weighting schemes (Budescu-Chen, ISP-η)
  did **not** reliably beat simple averaging in this dataset — added complexity
  didn't pay off; simple unweighted averaging of diverse forecasts was remarkably
  robust. (Classic "wisdom of crowds" result: diversity + independence of errors
  matters more than individual sophistication.)

### 8.4 Assertiveness metric

```
Assertiveness = (3/2) Σ_i (P_i − 1/3)²  ∈ [0,1]
```
Measures how far a forecast is from the uniform (1/3,1/3,1/3) — i.e., how "confident"
/ non-hedged a forecaster is. =0 for uniform, =1 for a forecast putting 100% on one
outcome. Used to characterize *forecaster style* (timid vs. bold) independent of
accuracy — useful for understanding the leaderboard distribution (bold-but-wrong
forecasters get punished hard by Brier, per Constantinou & Fenton's scenario 3).

### 8.5 Maximin strategy proof (Appendix C) — the "safe floor" forecast

**Theorem**: under Brier scoring, the **non-randomized maximin strategy** (the
forecast that minimizes your *worst-case* expected score, with no information at all)
is the **uniform forecast (1/3, 1/3, 1/3)**.

*Proof sketch (geometric/polarization identity)*: For any forecast `p=(p_H,p_D,p_A)`
and any possible true outcome `θ`, the Brier score `S(p,θ) = ||p − e_θ||²` (squared
Euclidean distance from p to the one-hot vector for θ). The worst-case θ for a given
p is whichever corner of the simplex (e_H, e_D, or e_A) is *farthest* from p. The
point `p*` that **minimizes the maximum distance to the three corners** of the
probability simplex is the **centroid** = (1/3,1/3,1/3) — by symmetry, it's
equidistant from all three corners, and any other point is strictly closer to one
corner and farther from another, increasing the max. Hence (1/3,1/3,1/3) is the
unique maximin point.

**Practical implication**: if you have *zero* information about a match, guessing
(1/3,1/3,1/3) caps your worst-case loss. Any deviation from uniform is a *bet* — only
deviate where your model gives you genuine edge (calibrated, non-zero RES per Murphy
decomposition). This is a nice formal justification for "don't force a confident
prediction on matches you have no real read on."

### 8.6 Simulation analysis (Tables 3-6, Figures 7-9)

The paper also runs simulations (synthetic forecasters with varying skill/calibration
levels) to show how aggregation performance depends on (a) the number of forecasters,
(b) the diversity/correlation of their errors, and (c) the average individual skill
level. Headline: aggregation gains are largest when individual forecasters are
**diverse** (low error correlation) even if individually mediocre — a crowd of
*correlated* mediocre forecasters doesn't average out to something good. This is the
quantitative version of "diversity beats individual ability" for crowds.

### 8.7 Practical takeaway for the Cup

- **If the Cup platform shows a live "consensus" or aggregate of other participants'
  picks, that consensus is itself a very strong forecast** — comparable to or
  better than most individuals' own models historically.
- A good strategy: build your own model (Poisson/Elo-based), AND look at any
  available market/crowd consensus, and **blend** the two (e.g., simple average) —
  this directly mirrors what worked best in 2018.
- Don't be afraid to default to (1/3,1/3,1/3)-ish (or close to the historical base
  rate, which for football H/D/A is closer to ~45/27/28, see below) for matches where
  your model has no edge — per the maximin proof, this minimizes your downside.

---

## 9. Cross-Sport Forecasting: How Successful Forecasters Source, Clean & Structure
Data

Synthesized from researching FiveThirtyEight's NFL/NBA Elo methodology and a detailed
2025 NFL Elo build-out (Michelle Pellon's blog, which documents a full modern data
pipeline).

### 9.1 The general Elo recipe (NFL/NBA, FiveThirtyEight-style) — directly portable
to football

```
Δ_elo = K · MOV_multiplier · (S − E)

E = 1 / (1 + 10^(−(Elo_opponent − Elo_self − HFA)/400))     # expected score
S = actual result (1 = win, 0.5 = draw, 0 = loss)

MOV_multiplier = ln(|margin|+1) · [2.2 / (|ΔElo|·0.001 + 2.2)]
```

- **K-factor ≈ 20** is a near-universal sweet spot across NFL, NBA, and (per Hvattum
  & Arntzen) football — "large enough that new info matters, small enough ratings
  don't whipsaw."
- **Margin-of-victory multiplier**: `ln(|margin|+1)` gives diminishing returns to
  blowouts (a 5-0 win isn't 5x as informative as 1-0), and the `2.2/(|ΔElo|·0.001+2.2)`
  term **dampens the effect when a big favorite blows out a big underdog** (that was
  "expected," so it shouldn't move ratings as much as a similar blowout between
  evenly-matched teams). **This is a more principled, continuous version of Hvattum &
  Arntzen's discrete `K0(1+δ)^λ` goal-margin adjustment** — worth implementing this
  exact functional form for a goals-based football Elo.
- **Home-field advantage**: calibrated empirically as a fixed Elo-point bonus (NFL:
  ~48 points ≈ 7.5pp win-probability shift), derived from the *historical home win
  rate* (NFL ≈ 57%). For football, do the same: compute the actual historical
  home-win rate in your dataset and back out the equivalent Elo offset.
- **Season-to-season carryover**: not detailed in what we found, but standard
  practice (used by FiveThirtyEight for NBA/NFL) is to **regress ratings toward the
  mean by ~1/3 between seasons** — full carryover overweights last season, full reset
  ignores real persistent quality differences. For international football (World
  Cup), this matters even more given the 4-year gap — consider blending pre-tournament
  Elo with more recent (qualifiers, friendlies) form.
- **Contextual covariates** that repeatedly show up as worth adding: travel
  distance/altitude (penalize visiting team), rest/fatigue (short turnaround
  penalties), and — for international tournaments — squad changes/injuries to key
  players (acknowledged as a real gap even in FiveThirtyEight's models: "doesn't take
  injuries into account other than severe QB injuries" — the football analogue would
  be a missing star striker/keeper).

### 9.2 Data sourcing & pipeline practices

- **Primary sources for historical results + odds**: `football-data.co.uk` (used by
  Hvattum & Arntzen — free, clean CSVs, includes closing odds from multiple
  bookmakers going back to 1990s for major European leagues) and, for US sports,
  Pro-Football-Reference / `nflreadpy`-style packages providing structured historical
  data in Parquet. **For World Cup-specific data**: FIFA match data, Elo ratings from
  eloratings.net (a long-running, well-regarded international football Elo tracker
  going back to 1872), and squad/lineup data where available.
- **Format**: convert raw CSV → **Parquet** for any non-trivial dataset — 80-90%
  size reduction, columnar access, schema evolution. For our scale (a few thousand
  international matches), this is more about good practice than necessity, but
  worth doing in R via `arrow::write_parquet()`.
- **Pipeline structure ("bronze/silver/gold")**:
  - *Bronze*: raw ingested data, untouched, queried directly (e.g., via DuckDB on
    Parquet files — no DB server needed).
  - *Silver*: processed/stateful transformations — e.g., the **chronological,
    match-by-match Elo rollforward**, which is inherently *sequential* (each match's
    rating update depends on the prior state) and is best done as an **imperative
    loop in R/Python**, not a SQL window function or "vectorized" approach. (Their
    explicit lesson: "SQL recursive CTEs proved unwieldy; imperative Python proved
    clearer for sequential state dependencies" — same will be true for an Elo
    rollforward in R: write a simple `for` loop over matches sorted by date,
    maintaining a named vector/list of current ratings.)
  - *Gold*: final aggregates — e.g., **Monte Carlo simulation** of remaining
    fixtures (1,000-10,000 reps) to get probability distributions over final
    outcomes (group standings, knockout bracket survival, etc.) — directly
    applicable to "probability that team X wins the World Cup" type questions if
    the Cup asks for those.
- **Calibration seeding**: using **market data (Vegas win totals / preseason odds)**
  to seed initial ratings before any games are played — for the World Cup, the
  analogue is using **pre-tournament bookmaker odds or FIFA rankings** to set initial
  team strength priors, since in-tournament data alone (a handful of group games) is
  far too sparse to estimate strong team-specific parameters from scratch.

### 9.3 Evaluation discipline

- Track **Brier score AND log loss AND accuracy** together — Brier ≈ 0.20 was
  flagged as "excellent" for NFL (vs. ~0.25 average); log loss vs. the "random"
  baseline of `log(2)≈0.693` shows real skill only when meaningfully below it.
- **Calibration curves** (= reliability diagrams, §7.3) were explicitly part of the
  "gold layer" output — i.e., professional pipelines compute Murphy/Yates-style
  diagnostics as a matter of routine, not as an afterthought.
- **Honest acknowledgment of misses**: the NFL build-out reports its actual Week 10
  misses and which were "statistically expected" (parlayed at 59-61% confidence —
  expected to lose ~40% of the time) vs. which represented real miscalibration (a
  68% pick that lost) — i.e., **don't just track aggregate Brier; review individual
  high-confidence misses** to distinguish bad luck from a systematic model problem.

### 9.4 General "what good sports-forecasting data looks like" — synthesis

For our own World Cup model, the data we'd want (in rough priority order):

1. **Match-level results** (date, teams, score, venue, competition) — the absolute
   minimum, needed for any Poisson/Elo model. Source: eloratings.net history,
   Wikipedia/FBref for recent friendlies & qualifiers.
2. **Team strength priors going in**: a long-running Elo history (eloratings.net) +
   FIFA world rankings + pre-tournament bookmaker odds (outright winner & group-stage
   odds) — needed because in-tournament sample sizes (3 group games) are tiny.
3. **Recency-weighted recent form**: last ~12-24 months of matches per team
   (qualifiers, friendlies, continental tournaments), exponentially time-decayed
   (DC-style, §1.3) — captures squad changes/improvement since the last major
   tournament.
4. **Context covariates**: home/neutral venue (most WC matches are "neutral" but
   host nation gets a boost — 2026 hosts are USA/Canada/Mexico), travel/altitude
   (less relevant for 2026 vs. e.g. 2014 Brazil), rest days between matches,
   confederation strength adjustments (cross-confederation matches are sparser and
   need careful handling).
5. **Squad/injury data**: harder to source systematically but high-value — a model
   blind to "star striker injured" will be systematically overconfident on that
   team. Even a simple manual override/adjustment based on squad news is valuable.
6. **Market data** (bookmaker odds) wherever available — both as a strong standalone
   benchmark/blend candidate (§7.7, §8.7) and as a sanity check on your own model's
   outputs (large divergences from market = either you found a real edge or you have
   a bug — investigate before trusting).

**Cleaning notes that recur across all papers**: ensure consistent team naming/IDs
across data sources (a perennial pain — "USA" vs "United States" vs "USMNT"), exclude
or flag matches affected by exceptional circumstances (the women's-football paper,
§6, explicitly excludes COVID-affected seasons from their dataset — consider whether
any 2020-2022 matches in your training data were "weird" e.g. empty stadiums
affecting home advantage), and decide explicitly how to handle **friendlies vs.
competitive matches** (lower stakes → less predictive of tournament performance;
several Elo systems down-weight friendlies, e.g., eloratings.net uses a match-
importance multiplier `K` that varies by competition type — World Cup finals get the
highest weight, friendlies the lowest).

---

## 10. Master Formula Reference Sheet

| Concept | Formula |
|---|---|
| Brier (half) score, single binary event | `S(P,X) = (P−X)²` |
| Brier score, 3-outcome | `S = Σ_i (p_i − e_i)²` where e is one-hot |
| RPS (3 outcomes, ordered Away/Draw/Home) | `RPS = ½[(p_A−e_A)² + (p_A+p_D−e_A−e_D)²]` |
| Murphy decomposition | `E[S] = UNC − RES + REL` |
| Brier Skill Score | `BSS = (RES−REL)/UNC` |
| DC tau correction | see §1.2 (4-cell correction via ρ) |
| Bivariate Poisson pmf | see §2.3 (Karlis-Ntzoufras Eq.1) |
| Time-decay weight | `φ(t) = exp(−ξt)` |
| Elo expected score | `E = 1/(1+10^{−Δ/400})` (or base-c, divisor-d generalized) |
| Elo update | `R' = R + K·MOV_mult·(S−E)` |
| MOV multiplier (538-style) | `ln(|margin|+1) · 2.2/(|ΔElo|·0.001+2.2)` |
| Ordered logit (3 outcomes) | `P(A)=logistic(κ1−βx)`, `P(D)=logistic(κ2−βx)−logistic(κ1−βx)`, `P(H)=1−logistic(κ2−βx)` |
| Odds → probability (de-vig) | `p_j = o_j^{-1} / Σ_k o_k^{-1}` |
| Maximin forecast (no info) | `(1/3, 1/3, 1/3)` |
| Assertiveness | `(3/2)Σ_i(P_i−1/3)²` |

---

## 11. Suggested Build Order for Our R Models

1. **Baseline 1 — Elo + ordered logit** (§4): cheapest to build, gives a calibration
   sanity check for everything else. Use eloratings.net history as the rating input.
2. **Baseline 2 — Independent Poisson / DC97** (§1): per-team attack/defence + home
   advantage + τ correction + time-decay. Sum to H/D/A.
3. **Upgrade — Bivariate Poisson or Poisson+Elo-covariate** (§2, §7.4/7.6): either
   add a true BP λ3 term, or (simpler, per Foulley's finding) just add a rating-
   difference covariate to the Poisson means — this alone induces realistic negative
   home/away correlation without needing BP/DC machinery.
4. **Recency**: rolling-window refits (Crowder et al-lite, §3.4) on top of whichever
   model you pick.
5. **Diagnostics after every gameweek**: compute REL/RES/UNC (§5.3, §7.2) per outcome
   (one-vs-rest), plot reliability diagrams, and recalibrate (Platt/isotonic) if REL
   is large relative to RES.
6. **Blend with crowd/market** (§8.7): if the SportsPredict platform shows aggregate
   participant probabilities, or if bookmaker World Cup odds are accessible, average
   your model's output with them — historically this **beats almost everyone**.
7. **When uncertain, don't force it** (§8.5): default toward base rates / uniform
   rather than confidently picking a direction with no model edge.
