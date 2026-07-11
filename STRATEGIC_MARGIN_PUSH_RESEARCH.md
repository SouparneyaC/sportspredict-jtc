# Strategic Margin-Pushing Under Relative (RBP) Scoring: Game Theory + Bet-Sizing Literature Review

**Date:** 2026-07-04
**Author context:** JTC / SportsPredict WC2026, scored by RBP (Relative Brier Points), `RBP_q ∝ (crowd_brier − our_brier)` summed over questions.
**Scope:** A *pure research* memo. Does NOT touch pricing code or estimates. It answers one precise question:

> For a question where we have unusually reliable, high-conviction, non-illiquid data, is there a **principled, mathematically-derived** reason to submit a probability **more extreme than our calibrated estimate** to maximize expected RBP against a crowd that compresses toward 50%? If so, **how much**, bounded by a risk-of-ruin / variance-control logic?

**Companion docs (read first, not duplicated here):**
`data/crowd_consensus_prediction_research.md` §6–7 (derives `E[RBP] ∝ (p_c−p_t)² − (p_s−p_t)²` and concludes: under certainty submit your true belief); `bot/FORECASTING_DATASET_DESIGN.md` §6 (Satopää *aggregate* extremizing — a *different* mechanism). This memo is about extremizing **your own single report** under a **competitive** rule, and the bet-sizing cap on it.

---

## Executive Summary (the honest answer, up front)

1. **Under the RBP rule as actually implemented — additive, per-question — deliberate margin-pushing is strictly negative-EV.** The crowd's Brier is a constant that does not depend on your report, so per-question RBP is a *strictly proper* scoring rule: expected RBP is maximized exactly at your true belief `p_t`, and pushing `δ` past it costs you **exactly `δ²` in expected Brier every single time** (derived in §7.1). The crowd being compressed toward 0.5 changes *how much RBP is on the table*, not *where you should aim*. This confirms and sharpens the existing `crowd_consensus_prediction_research.md` §6 conclusion. **On a per-question basis, do not push.**

2. **Extremizing your own report becomes rational only when your payoff is a *convex (nonlinear) function of your cumulative score* — i.e., a rank / threshold / winner-take-all tournament, not additive accumulation.** This is the unifying result across every game-theory source below (Lichtendahl & Winkler 2007; Frongillo et al. 2021; the 2026 "Endogeneity of Miscalibration" impossibility): the incentive to report more extreme than your belief is *created by the curvature of the payoff*, and it is absent under a linear/additive rule. RBP totalled over a long campaign is (approximately) linear — so the tournament incentive only bites near a **discrete cutoff** (a prize line, a promotion/relegation rank, a "beat competitor X for the stage" duel).

3. **When the convex regime *does* apply, the direction of the optimal distortion flips with your standing** — this is the mutual-fund-tournament result (Chevalier–Ellison 1997; Brown–Harlow–Starks 1996), a clean cross-domain analogue with the *same architecture*: interim **losers increase variance** (push to extremes) late in the evaluation window; interim **winners decrease variance** (shade toward the benchmark/crowd to lock in the lead). Blanket "push harder when confident" is wrong; the correct signal is *behind-vs-ahead near a cutoff*, not confidence.

4. **The Kelly / risk-of-ruin analogy does NOT transfer cleanly, and it is important to say so.** Kelly governs *multiplicative* bankroll growth where a bad bet compounds toward ruin. RBP is *additive and bounded* (each question adds a number in roughly `[−S, +S]`); there is no compounding and no literal ruin. So "full Kelly vs fractional Kelly" is the wrong formal frame. The correct frame is a **tracking-error / active-risk budget** (Grinold's information-ratio framework from benchmark-relative asset management): you may deviate from the crowd only up to a variance budget, and the binding constraint is *single-question tail loss*, not bankroll ruin. Fractional-Kelly's *spirit* — take a fraction (¼–½) of the theoretically-optimal bet because your edge estimate is itself uncertain — still applies and gives the haircut on the cap.

5. **The single most useful reframing:** most of the temptation to "push past our calibrated estimate" is really the pipeline *having already shrunk the estimate too hard for a high-reliability signal.* Our RULEs 5/12/13 pull toward 0.5/crowd/prior — correct for *noisy* signals, miscalibrated for a *DIRECT liquid market* or a *4-for-4 empirical* signal. The right fix is **tier-dependent shrinkage** (apply *less* shrinkage to Tier-A sources so you recover `p_t`), **not** anti-crowd overshoot past `p_t`. This is the James–Stein logic run in reverse: shrink less when your individual signal is more reliable than the reference — but never *expand past* the honest estimate (§7.4).

**Bottom line recommendation (full derivation in §8):** Do **not** implement a confidence-driven anti-crowd push as a standing policy. Instead (a) stop over-shrinking Tier-A estimates so you submit the honest `p_t` (which already banks the crowd-compression gap for free), and (b) reserve *deliberate* extremizing for the narrow, explicitly-flagged case of **being behind near a discrete leaderboard cutoff**, capped at **≤ ~5–7 percentage points (a "half-budget" active-risk cap), Tier-A questions only.**

---

# PART I — Half A: Is extremizing your OWN report ever optimal under relative scoring?

## 1. Lichtendahl & Winkler (2007) — the foundational "competition makes you exaggerate" result

**Citation:** Lichtendahl, K.C. Jr. & Winkler, R.L. (2007). "Probability Elicitation, Scoring Rules, and Competition Among Forecasters." *Management Science* 53(11), 1745–1755.
**Links:** [INFORMS/Management Science](https://pubsonline.informs.org/doi/10.1287/mnsc.1070.0729) · [SSRN abstract 961001](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=961001)

**What it models:** Two (or more) forecasters each report a probability on a single event. Each cares about a *mixture* of (a) a standard proper scoring-rule payment and (b) a **bonus for being the *best* (highest-scoring) forecaster** — i.e., a rank/competition term layered on top of the proper score.

**The load-bearing finding (verbatim from the abstract):**
> "a competitive forecaster who wants to do better than another forecaster typically should report more extreme probabilities, exaggerating toward zero or one."

And on the mechanism: the paper derives "a competitive forecaster's best response to truthful reporting" and "equilibrium reporting functions in the case where another forecaster also cares about relative performance." The exaggeration "makes well-calibrated forecasters appear overconfident."

**Extracting the actual condition (why it exaggerates):** The *bonus-for-winning* term is a **convex kink** on top of the proper score — you get a discrete jump only if you *beat* the rival. Beating the rival requires your score to *exceed* theirs, and the probability of that is increased by increasing the **variance/dispersion** of your realized score. A more extreme report (closer to 0 or 1) has higher variance of realized Brier (you either look great or terrible), so it raises `P(you beat the rival)` at the cost of lowering your *expected* proper score. The size of the optimal shift grows with the *weight* on the winning-bonus relative to the proper-score payment, and shrinks to zero as that weight → 0 (pure proper scoring ⇒ truthful).

**Direct relevance to us:** This is the single most on-point paper. Its result is **conditional on a rank/winner term**. RBP as-implemented has *no* such term at the per-question level — it is purely the proper-score payment `(crowd_brier − our_brier)`. So L&W predicts *no* exaggeration for us **except** insofar as our real objective contains a winning-bonus (a leaderboard cutoff). That conditionality is the whole story.

## 2. Frongillo, Gomez, Thilagar & Waggoner (2021) — winner-take-all distorts, variance-seeking is explicit

**Citation:** Frongillo, R., Gomez, R., Thilagar, A. & Waggoner, B. (2021). "Efficient Competitions and Online Learning with Strategic Forecasters." *Proceedings of the 22nd ACM Conference on Economics and Computation (EC '21)*.
**Links:** [ACM DL](https://dl.acm.org/doi/10.1145/3465456.3467635) · [arXiv 2102.08358](https://arxiv.org/abs/2102.08358) · builds on Witkowski et al. 2018 (ELF mechanism)

**Load-bearing statements:**
> "Winner-take-all competitions in forecasting and machine-learning suffer from distorted incentives."

and (from the strategic-behavior characterization):
> "In forecasting competitions with winner-take-all mechanisms, forecasters may misreport to increase the variance of their score, even at the cost of its expectation, to improve their chance of being selected."

**Why this matters:** This states the mechanism of §1 in its cleanest modern form — **misreport to increase variance, accepting lower expected score, because only rank matters.** The paper's fix (the ELF mechanism of Witkowski et al. 2018, and their online-learning selection rules) is a mechanism-design *cure*: it selects a near-optimal forecaster while *restoring* approximate truthfulness. The takeaway for us is the diagnosis: **variance-seeking is a property of the *winner-take-all payoff shape*, and it vanishes when selection is (approximately) score-linear.** RBP totals are approximately linear ⇒ approximately truthful ⇒ no standing push.

## 3. "Endogeneity of Miscalibration" (2026) — the general impossibility: non-affine payoff ⇒ truthful reporting breaks

**Citation:** Lovén, L. & Tarkoma, S. (2026). "The Endogeneity of Miscalibration: Impossibility and Escape in Scored Reporting." arXiv:2605.07671.
**Link:** [arXiv PDF](https://arxiv.org/pdf/2605.07671)

**Core result (paraphrase of the impossibility):** When an agent's overall payoff is a **non-affine (convex/nonlinear) transformation** of a strictly proper scoring rule's output — because of budgets, risk aversion, performance pressure, or non-accuracy bonuses — the scoring rule **can no longer guarantee truthful or calibrated reporting.** The impossibility is *structural*: "no single scoring rule can remain incentive-compatible across all feasible non-affine payoff transformations agents might face." Miscalibration becomes *endogenous* — created by the payoff curvature, not by the agent's error.

**Why this is the unifying theorem for Part I:** It generalizes L&W and Frongillo et al. Truthful reporting is guaranteed *iff* your realized payoff is **affine (linear) in the proper score**. Any convexity — a rank bonus, a prize threshold, a "must beat X" duel, loss aversion near a cutoff — is exactly what makes deliberate miscalibration optimal. **So the entire question "should we push?" reduces to: "is our effective payoff convex in cumulative RBP right now?"** Steady-state accumulation over a long tournament: essentially linear ⇒ no. Near a discrete cutoff you're chasing: locally convex ⇒ maybe, and §5 tells you which direction.

## 4. Lazear & Rosen (1981) — the origin of "relative pay induces different (riskier) behavior"

**Citation:** Lazear, E.P. & Rosen, S. (1981). "Rank-Order Tournaments as Optimum Labor Contracts." *Journal of Political Economy* 89(5), 841–864.
**Links:** [JPE/EconPapers](https://econpapers.repec.org/RePEc:ucp:jpolec:v:89:y:1981:i:5:p:841-64) · [NBER w0401](https://www.nber.org/papers/w0401)

**Load-bearing finding:** Under rank-order pay, "the effort level ... is a function of the **prize spread and not the average level of the prizes**. The bigger the spread, the more effort each player will be forced to exert." Behavior is driven by the *gap between prizes at adjacent ranks*, i.e., the **convex jump at the rank boundary**, not by absolute performance level.

**Relevance:** The theoretical root of the whole family. Translating "effort" → "willingness to take report-variance": the incentive to deviate from the myopically-optimal (honest) action scales with the **prize spread at the rank you're contesting**. For us: near a stage prize cutoff the spread is large (convexity is steep) ⇒ some variance-seeking is rational; deep in the interior of the leaderboard the local spread per question is ~flat ⇒ none is.

---

# PART II — Cross-domain analogues (same architecture, different field)

## 5. Mutual-fund tournaments — the strongest cross-domain match (relative evaluation ⇒ deliberate risk-shifting, direction depends on standing)

### 5a. Chevalier & Ellison (1997)

**Citation:** Chevalier, J. & Ellison, G. (1997). "Risk Taking by Mutual Funds as a Response to Incentives." *Journal of Political Economy* 105(6), 1167–1200.
**Links:** [JPE/EconPapers](https://ideas.repec.org/a/ucp/jpolec/v105y1997i6p1167-1200.html) · [NBER w5234](https://www.nber.org/papers/w5234)

**Finding:** Because fund inflows (the manager's true payoff) are a **convex function of relative performance rank**, managers optimize rank, not raw return. Empirically, **interim-loser funds hold higher-variance portfolios than interim-winner funds** — managers behind their peer benchmark near the annual evaluation deliberately raise portfolio variance, hoping to leap up the rankings, because only relative rank drives the flows.

### 5b. Brown, Harlow & Starks (1996)

**Citation:** Brown, K.C., Harlow, W.V. & Starks, L.T. (1996). "Of Tournaments and Temptations: An Analysis of Managerial Incentives in the Mutual Fund Industry." *Journal of Finance* 51(1), 85–110.
**Links:** [SSRN 7460](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7460) · [EconPapers](https://econpapers.repec.org/RePEc:bla:jfinan:v:51:y:1996:i:1:p:85-110)

**Finding (334 growth funds, 1976–1991):** "**mid-year losers tend to increase fund volatility in the latter part of an annual assessment period to a greater extent than mid-year winners.**" They formalize the *Risk Adjustment Ratio* (RAR = next-period volatility ÷ current-period volatility; RAR > 1 = risk shifted up), and show it is systematically higher for interim laggards.

**Why this is the cleanest analogue to our problem:** Identical architecture — a **relative-performance evaluation against a benchmark/peer group over a finite window**, producing **deliberate strategic variance-shifting**, with the crucial refinement that **the direction depends on standing**: behind ⇒ push out (more extreme/variance); ahead ⇒ pull in (toward benchmark, lock the lead). Mapping to us: the "benchmark" is the crowd, "variance" is report extremity, the "evaluation window" is a tournament stage. It directly warns that a naive "we're confident, so push" rule is wrong: **if we are *ahead* near a cutoff, the tournament-theoretic move is to shade *toward* the crowd, not away from it.**

## 6. Tracking-error / active-risk budget (Grinold information ratio) — the correct *bounding* analogue (and why it beats Kelly here)

**Concept:** Grinold, R. (1989), "The Fundamental Law of Active Management"; standard benchmark-relative asset management (Information Ratio = active return ÷ tracking error).
**Links:** [Tracking error (Wikipedia)](https://en.wikipedia.org/wiki/Tracking_error) · [SSGA on the information ratio](https://www.ssga.com/us/en/intermediary/insights/the-power-of-information-ratio-ir-in-active-management)

**Mechanism:** A benchmark-relative manager is given an **active-risk (tracking-error) budget** — a cap on how far the portfolio may deviate from the benchmark — and maximizes the **Information Ratio** (excess-return-over-benchmark per unit of tracking error) subject to that cap. "Managers with excellent performance are allocated a higher risk budget."

**Why this is the right frame for our *cap* (and Kelly is not):** Our "deviation from the crowd" is *exactly* an active bet against a benchmark. The natural bound is a **tracking-error budget on how far from the crowd we allow ourselves to sit**, scaled by the *quality* (Information-Ratio) of the signal driving the deviation. A DIRECT liquid market is a high-IR signal (big edge, low noise) ⇒ larger deviation budget; a thin illiquid market is a low-IR signal ⇒ near-zero budget (hug the crowd). This maps to our reliability tiers directly (§8) and, unlike Kelly, does **not** falsely assume compounding/ruin.

---

# PART III — Half B: How much can you push before you "blow up"?

## 7. The bet-sizing / risk-of-ruin literature, and where the analogy breaks

### 7.1 The exact per-question RBP mathematics (our derivation)

Let `p_t` = true prob, `p_s` = our submission, `p_c` = crowd, outcome `o ∈ {0,1}`. Ignoring JTC's scale constant `S`:

```
RBP_q = (p_c − o)² − (p_s − o)²
E_o[RBP_q] = (p_c − p_t)² − (p_s − p_t)²      (Brier variance terms cancel — see companion doc §6)
```

`∂E[RBP_q]/∂p_s = −2(p_s − p_t) = 0  ⇒  p_s* = p_t.`  **Per-question RBP is strictly proper; the optimum is the truth, independent of `p_c`.**

Now push `δ` past the truth (submit `p_s = p_t + δ` toward the favored extreme). The realized *change* in RBP versus honest reporting is:
- Outcome favors the push (prob `p_t`): gain `≈ δ·(2(1−p_t) − δ) > 0`
- Outcome against the push (prob `1−p_t`): loss `≈ −δ·(2p_t + δ) < 0`
- **Expected change: `E[ΔRBP] = −δ²` (exactly).** Always a loss, quadratic in the push.

Two facts that define the whole trade-off:
1. **Expected cost of a push is `S·δ²`** — small and quadratic.
2. **Downside when wrong is `S·δ·(2p_t + δ)`** — *linear* in `δ` and can be large. E.g. `p_t = 0.75, δ = 0.10`: worst-case added Brier loss `= 0.10·(1.5+0.10) = 0.16`. At JTC's empirical scale (single-question swings of ±~50 RBP; e.g. the BRA-MAR 1.00 blunder cost −51.97 for a ~0.66 Brier gap ⇒ `S ≈ 78–100` RBP per Brier unit), that is `≈ 13–16 RBP` of downside for a push that earns you *nothing* in expectation.

**This is the core asymmetry:** you pay `S·δ²` guaranteed in expectation to buy a *symmetric-looking but tail-heavy* `±S·δ` swing. That trade is only worth making if the extra *variance itself* has value — which requires convex payoff (Part I). Absent convexity, it is a pure `−δ²` bleed.

### 7.2 Kelly (1956) and fractional Kelly — and the honest statement that it does NOT transfer

**Citations:** Kelly, J.L. (1956), "A New Interpretation of Information Rate," *Bell System Technical Journal*. MacLean, L.C., Thorp, E.O. & Ziemba, W.T. (eds.) (2011), *The Kelly Capital Growth Investment Criterion*, World Scientific. MacLean, Ziemba & Blazenko (1992), *Management Science*.
**Links:** [Good & bad properties of Kelly (MacLean/Thorp/Ziemba PDF)](https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf) · [Kelly criterion (Wikipedia)](https://en.wikipedia.org/wiki/Kelly_criterion)

**What Kelly says:** Betting the full edge (full Kelly) maximizes long-run *log-wealth growth rate* but has punishing drawdowns. **Fractional Kelly** (½ or ¼ of the full stake) sacrifices growth for a large variance reduction: MacLean–Ziemba–Blazenko show **half-Kelly retains ≈ 75% of the growth rate at ≈ 50% of the volatility.** The deeper rationale for fractional Kelly is *parameter uncertainty*: since you don't know your true edge, you shrink the bet to hedge estimation error.

**Where it breaks for RBP (state this plainly):** Kelly is about **multiplicative bankroll growth** — `W_{n+1} = W_n·(1 + f·X)` — where a large loss *compounds* and repeated over-betting drives `W → 0` (ruin). **RBP is additive and bounded**: `Total = Σ RBP_q`, each `RBP_q ∈ [−S, +S]` roughly, no product, no compounding, no absorbing zero. **There is no "ruin" in the Kelly sense** — a single −50 RBP question does not multiply down your future; it subtracts once. So the full "growth-rate-maximizing bet fraction" machinery **does not apply**, and citing "full vs fractional Kelly" as the sizing law here would be a false analogy.

**What *does* survive:** two useful transplants.
- *The fractional-Kelly haircut for parameter uncertainty.* Even where a push is justified (convex regime), your `p_t` estimate and your convexity estimate are both uncertain, so take a **fraction (¼–½)** of whatever "optimal" push the convexity math suggests. This is the emotionally-and-statistically-robust move, same as fractional Kelly.
- *The variance-control framing.* The binding constraint is **single-question tail loss** (`S·δ·(2p_t+δ)`), controlled by an **active-risk budget** (§6), not a bankroll-ruin constraint. This is the correct substitute for Kelly's role.

### 7.3 The winner-take-all / rank literature's variance point restated as a cap

Combining §1–§5: the *benefit* of a push is `(convexity of payoff) × (variance added by the push)`. Variance added by a `δ` push scales like `δ²·[stuff]`; the *cost* is `S·δ²`. So near a cutoff the net is `[½U''·Var_gain − S]·δ²`, and a push helps only when the local payoff convexity `U''` is large enough (steep prize spread, Lazear–Rosen) to overcome the guaranteed `S·δ²` Brier bleed. Deep in the leaderboard interior `U'' ≈ 0` ⇒ never push.

### 7.4 James–Stein / bias–variance — the "opposite direction" result, and why *anti*-shrinkage past `p_t` is unsupported

**Citations:** James, W. & Stein, C. (1961), "Estimation with Quadratic Loss," *Berkeley Symposium*. General bias–variance / empirical-Bayes shrinkage literature.
**Links:** [Stein's Paradox explainer](https://towardsdatascience.com/steins-paradox-ba493f46e181/) · [James–Stein shrinkage estimator (overview)](https://metricgate.com/docs/james-stein-shrinkage-estimator/)

**What shrinkage says:** James–Stein pulls individual estimates **toward** a common reference to reduce total MSE; the optimal shrinkage factor `c` runs from `c=1` (no shrinkage — trust the individual signal fully, when it is low-noise/high-reliability) to `c=0` (full shrinkage to the reference, when the individual signal is pure noise). Shrinkage is *toward* the mean; the reliability of the individual signal sets *how little* you shrink.

**The reverse question the user is really asking:** Is there a symmetric "**anti-shrinkage / expansion**" result that formally justifies pushing an estimate *further from* a shared reference (the crowd) when you believe your signal beats the reference? **Answer: essentially no, not as a variance-reducing move.** Expansion estimators exist (e.g., bias-corrected extensions of James–Stein) but they *correct bias in the shrinkage itself* — they push back *toward the MLE `p_t`*, never *beyond* it. MSE theory gives **no** result that says "move past your own best estimate, away from a reference, to reduce error." The only thing that justifies your point estimate being *further from the crowd* is **evidence that the truth itself is further from the crowd** — i.e., a better `p_t`, not an overshoot of `p_t`.

**The correct reading for us:** The lever is **shrinkage strength, not expansion.** Our pipeline (RULE5 blend-with-prior, RULE12 pull-to-crowd, RULE13 price-near-0.5) is *shrinkage toward the crowd/0.5*. That is calibrated for **noisy** signals (`c` small). For a **DIRECT liquid market or a 4-for-4 empirical** signal, the reliability is high ⇒ the correct `c` is near 1 ⇒ we should be shrinking *much less*. So the honest "extremize" the user wants is **de-shrinkage up to `p_t` for high-reliability tiers**, which recovers the free crowd-compression gap — **never expansion past `p_t`.**

---

# PART IV — Adapting This to Our RBP Setup

## 8. A concrete decision procedure (derived, not gestured at)

### 8.1 The crowd-compression gap is already banked by honest reporting

Our validated crowd model (`project_jtc_overview.md`): `p_c ≈ 0.514 + 0.61·(p_s − 0.5)`. If we submit our honest `p_t`, the crowd sits at `0.514 + 0.61·(p_t − 0.5)`, already compressed toward 0.5. Example `p_t = 0.75` ⇒ `p_c ≈ 0.667`. Honest submission at 0.75 **already** earns `E[RBP] ∝ (0.667−0.75)² − 0 = 0.0069·S ≈ +0.6 RBP` for free, with zero added variance. **Pushing to 0.85 earns nothing extra in expectation and costs `S·0.10² = 0.01·S ≈ +1 RBP of guaranteed expected bleed`** plus `≈13 RBP` of tail downside. The compression is the crowd's error to *collect by aiming true*, not to *chase by aiming past true*.

### 8.2 Reliability tiers → shrinkage, not push (the primary lever)

| Tier | Example source | Shrinkage `c` | Submit |
|---|---|---|---|
| **A — DIRECT / high-conviction** | liquid 2-sided market matching the question ~1:1; ≥4-for-4 consistent multi-game empirical signal | `c ≈ 1` (minimal) | the **de-shrunk `p_t`**, capped at 0.05/0.95 (RULE6) |
| **B — Model decomposition** | Poisson/Skellam from a team-level liquid market | moderate | standard shrinkage |
| **C — Thin / illiquid / small-sample** | offer-only player prop; noisy 3-game team stat | heavy (`c` small) | hug crowd formula / 0.45–0.55 (existing RULEs 12/13/16) |

The knockout deep-dive already validates this ordering empirically: DIRECT +142.39/34q at 73.5% beat-crowd; PLAYER_ILLIQUID −14.27/7q. **The gain from "trusting our high-reliability signal more" comes from under-shrinking Tier A, not from over-shooting it.** This is the actionable core.

### 8.3 The *only* regime where a deliberate push past `p_t` is defensible

All three conditions must hold simultaneously:
1. **Tier A reliability** (§8.2) — never push a Tier B/C estimate.
2. **Locally convex payoff:** you are **behind and near a discrete cutoff** you can realistically reach — a stage prize line, a promotion rank, or an explicit "beat competitor X this stage" duel — where an extra chunk of variance raises `P(cross the line)`. In steady-state accumulation (the normal case), this fails ⇒ no push. (Lazear–Rosen: the prize *spread* at the contested rank must be steep.)
3. **Direction check (Chevalier–Ellison / Brown–Harlow–Starks):** confirm you are the *interim loser* relative to the target. **If you are *ahead* near the cutoff, do the opposite — shade toward the crowd to cut variance and lock the lead.**

### 8.4 The cap, when 8.3 is satisfied (active-risk budget + fractional-Kelly haircut)

Downside of a push is `S·δ·(2p_t + δ)`. Set an **active-risk budget**: cap the worst-case *added* single-question loss at one "tolerable unit" `L` (suggest `L ≈ 10 RBP`, well under a typical ±50 swing). With `S ≈ 90`:

```
S·δ·(2p_t + δ) ≤ L   ⇒   for p_t≈0.75:  90·δ·1.6 ≤ 10   ⇒   δ ≤ 0.069
```

So the raw active-risk cap is **δ ≤ ~0.05–0.07 (5–7 percentage points)** for a mid-high `p_t`; it *shrinks* as `p_t` approaches the extremes (a push near 0.9 has larger downside per point, so the budget allows fewer points). Expressed as fraction of distance-to-bound, `δ = 0.05` from `p_t = 0.75` is **~20% of the remaining distance to 1.0**.

Then apply the **fractional-Kelly haircut for parameter uncertainty** (§7.2): take **½ (or ¼)** of that, because `p_t`, `S`, and your convexity estimate are all uncertain. Net practical cap:

> **Push by at most ~3–5 percentage points (≈½ of a ~7pp active-risk budget), Tier-A questions only, only while behind near a reachable discrete cutoff, and never on a question already inside 0.90–0.95 / 0.05–0.10.** Away from a cutoff, the cap is **0** — submit the honest de-shrunk `p_t`.

### 8.5 Why this is not "telling you what you want to hear"

The literature, read rigorously, comes down **against** a standing confidence-driven margin-push and **for** honest reporting of a *properly de-shrunk* estimate:
- Per-question RBP is strictly proper (§7.1) — pushing is a guaranteed `−δ²` expected bleed with tail downside.
- Extremizing is a *tournament artifact* (L&W, Frongillo, Endogeneity-of-Miscalibration) that only appears under **convex payoff**, and near cutoffs its **direction flips with standing** (mutual-fund tournaments) — so "confident ⇒ push" is not even the right trigger; "behind-near-cutoff ⇒ push, ahead-near-cutoff ⇒ hug" is.
- Kelly/ruin does **not** transfer (additive, bounded, non-compounding score); the correct bound is a tracking-error/active-risk budget with a fractional-Kelly haircut for estimate uncertainty.
- James–Stein gives no license to expand *past* your own estimate; the real gain is **under-shrinking** Tier-A signals so you actually submit `p_t`.

**The one-sentence upshot:** *Stop over-shrinking your high-reliability estimates so you submit the honest number (which already banks the crowd-compression edge risk-free); reserve any deliberate push past that number for the rare, explicitly-flagged case of being behind near a leaderboard cutoff, capped at ~3–5 percentage points on Tier-A questions only.*

---

## Sources Cited

**Competitive / relative-scoring game theory**
- Lichtendahl, K.C. Jr. & Winkler, R.L. (2007). Probability Elicitation, Scoring Rules, and Competition Among Forecasters. *Management Science* 53(11), 1745–1755. [INFORMS](https://pubsonline.informs.org/doi/10.1287/mnsc.1070.0729) · [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=961001)
- Frongillo, R., Gomez, R., Thilagar, A. & Waggoner, B. (2021). Efficient Competitions and Online Learning with Strategic Forecasters. *EC '21*. [ACM](https://dl.acm.org/doi/10.1145/3465456.3467635) · [arXiv 2102.08358](https://arxiv.org/abs/2102.08358)
- Lovén, L. & Tarkoma, S. (2026). The Endogeneity of Miscalibration: Impossibility and Escape in Scored Reporting. [arXiv 2605.07671](https://arxiv.org/pdf/2605.07671)
- Hudson, R. (2024). Joint Scoring Rules: Zero-Sum Competition Avoids Performative Prediction. *AAAI 2025*. [arXiv 2412.20732](https://arxiv.org/abs/2412.20732) · [AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/34944)
- "Alignment Problems With Current Forecasting Platforms" (2021). [arXiv 2106.11248](https://arxiv.org/pdf/2106.11248)
- Lazear, E.P. & Rosen, S. (1981). Rank-Order Tournaments as Optimum Labor Contracts. *JPE* 89(5), 841–864. [EconPapers](https://econpapers.repec.org/RePEc:ucp:jpolec:v:89:y:1981:i:5:p:841-64) · [NBER w0401](https://www.nber.org/papers/w0401)

**Cross-domain: relative-performance risk-shifting**
- Chevalier, J. & Ellison, G. (1997). Risk Taking by Mutual Funds as a Response to Incentives. *JPE* 105(6), 1167–1200. [EconPapers](https://ideas.repec.org/a/ucp/jpolec/v105y1997i6p1167-1200.html) · [NBER w5234](https://www.nber.org/papers/w5234)
- Brown, K.C., Harlow, W.V. & Starks, L.T. (1996). Of Tournaments and Temptations. *Journal of Finance* 51(1), 85–110. [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7460) · [EconPapers](https://econpapers.repec.org/RePEc:bla:jfinan:v:51:y:1996:i:1:p:85-110)
- Grinold information-ratio / tracking-error active-risk budgeting. [Tracking error](https://en.wikipedia.org/wiki/Tracking_error) · [SSGA information ratio](https://www.ssga.com/us/en/intermediary/insights/the-power-of-information-ratio-ir-in-active-management)

**Bet-sizing / risk-of-ruin**
- Kelly, J.L. (1956). A New Interpretation of Information Rate. *Bell System Technical Journal*.
- MacLean, L.C., Thorp, E.O. & Ziemba, W.T. eds. (2011). *The Kelly Capital Growth Investment Criterion*. World Scientific. [Good & bad properties of Kelly (PDF)](https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf) · [Kelly criterion](https://en.wikipedia.org/wiki/Kelly_criterion)
- James, W. & Stein, C. (1961). Estimation with Quadratic Loss. *Berkeley Symposium*. [Stein's Paradox](https://towardsdatascience.com/steins-paradox-ba493f46e181/) · [JS shrinkage overview](https://metricgate.com/docs/james-stein-shrinkage-estimator/)

*Generated 2026-07-04. Pure research memo; no pricing code or estimates modified.*
