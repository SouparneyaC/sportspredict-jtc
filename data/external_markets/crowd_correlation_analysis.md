# Crowd Correlation Analysis (2026-06-15, n=85 questions / 9 matches)

**Triggered by**: "is there a connection/correlation between SportsPredict's crowd and
something else?" - this is the first time we've had enough settled data (85 rows in
`settled_markets_ledger.json`) to run real regressions instead of eyeballing
crowd-vs-us gaps match-by-match.

---

## 1. Crowd is a predictable, COMPRESSED linear function of our estimate

```
corr(us, crowd) = 0.83
Regression:  (crowd - 0.5) = 0.61 * (us - 0.5) + 0.014
  => crowd ≈ 0.514 + 0.61*(us - 0.5)
  residual std ≈ 0.071 (7.1pp)
```

Checked separately for us>0.5 (k=0.618) and us<0.5 (k=0.621) - the compression factor is
essentially IDENTICAL in both directions (~62%). **Crowd moves about 62% as far from 50% as
we do, in whichever direction we point, plus a small ~+1.4pp upward intercept shift even at
us=0.5.** This is the first QUANTIFIED version of the "crowd compresses toward 50%" root
cause finding from `project_crowd_bias_model.md` - previously directional, now a coefficient.

**Practical use**: we can now PREDICT crowd's revealed number from our own pre-match estimate
before submission: `crowd_pred = 0.514 + 0.61*(us-0.5)`. This lets us estimate
`(crowd_pred - us)^2` - a proxy for "how much RBP is on the table" for a given question -
BEFORE the match, without waiting for the leaderboard. The further `us` is from 0.5, the
larger this gap grows (since 0.61<1 means crowd "lags behind" us proportionally more in
absolute terms as us moves to the extremes) - this is the formal version of "be confident when
grounded, that's where the points are."

---

## 2. The asymmetry that explains WHERE our edge comes from

Splitting by direction of our estimate (us>0.5 vs us<0.5) and comparing mean(us), mean(crowd),
mean(outcome):

| Bucket | n | mean(us) | mean(crowd) | mean(outcome) | us calibration error | crowd calibration error |
|---|---|---|---|---|---|---|
| us < 0.5 ("we say unlikely") | 61 | 0.361 | 0.430 | 0.361 | **0.000** | **+0.069** |
| us > 0.5 ("we say likely"), excl. the BRA-MAR Q8 gut-override | 23 | 0.651 | 0.610 | 0.652 | **-0.001** | **-0.042** |

**We are essentially PERFECTLY calibrated in both directions** (once the one known
discipline failure - submitting 1.00 on BRA-MAR Q8 - is excluded; with it included, the
us>0.5 bucket shows us_err=-0.330, entirely driven by that single row).

**Crowd is NOT well-calibrated in either direction, and the errors go in OPPOSITE
directions**:
- When the true rate is LOW (us<0.5 bucket, true rate 36.1%), crowd says 43.0% -
  **crowd OVERESTIMATES rare/unlikely events by ~7pp.**
- When the true rate is HIGH (us>0.5 bucket, true rate 65.2%), crowd says 61.0% -
  **crowd UNDERESTIMATES likely events by ~4pp.**

Both errors are crowd PULLING TOWARD 50% relative to the true rate - exactly the
favorite-longshot / probability-weighting bias (Snowberg & Wolfers) the literature review
predicted, now measured directly: **crowd's compression costs it ~7pp of accuracy on the
"unlikely" side and ~4pp on the "likely" side**. Since 61/85 = 72% of our questions fall in
the "us<0.5" bucket, MOST of our edge comes from the larger (~7pp) error crowd makes on
"unlikely" events.

---

## 3. Honesty check: our edge is real but LUMPY, not uniform

```
Mean Brier (lower=better): us=0.2424, crowd=0.2268  <- crowd's RAW Brier is actually BETTER
us beats crowd on 45/85 = 52.9% of individual questions (barely above coin-flip)
Sum of RBP = +140.60
```

This looks contradictory at first - crowd has a better average Brier score AND we only "win"
53% of questions, yet we're +140.60 total. The resolution: **RBP's per-question scale varies
enormously (the project's `_schema` notes 1.5x-80x between questions)**. Our wins tend to be
on HIGHER-LEVERAGE questions (well-grounded tier1_market/tier2_realdata-first-pass calls,
which the scoring rule rewards heavily when right) while our losses, when they happen, are
concentrated in a SMALL NUMBER of LARGE-MAGNITUDE misses:
- -51.97 (BRA-MAR Q8, gut override - a discipline failure, not a methodology failure)
- -42.51 (QAT-SUI Q1, correlated-error false validation)
- -33.9 (SWE-TUN Q2, RULE10 blowout-fouls inversion)
- -25.37 (JPN-NED Q1, 88th-min-equalizer foul-tie flip)

These 4 outliers sum to -153.85. Remove just the ONE discipline failure (-51.97) and our
total would be +192.57 - a 37% increase. **Our strategy has POSITIVE EXPECTED VALUE but HIGH
VARIANCE, concentrated in a handful of "confident tier2_realdata, no market to cross-check"
calls that occasionally blow up by 25-45 points.** This is the risk-management problem to
solve - see RULE12 below.

---

## 4. NEW RULE12: pre-submission risk gate (uncertainty-weighted shrinkage)

Formal proper-scoring-rule theory says: if you know `p_true`, submit `p_true` regardless of
crowd (§6 of `crowd_consensus_prediction_research.md`). But our 4 worst-ever results all share
a profile: **tier2_realdata, NO related market to cross-check, a historical-average gap that
LOOKED clean (narrow, non-overlapping ranges), submitted near-raw or only lightly shrunk**.
The problem isn't the scoring-rule logic - it's that our POINT ESTIMATE `us` had much higher
VARIANCE than its apparent precision suggested (RULE10: a team's historical foul rate reflects
its relative dominance in ITS OWN sample, which doesn't transfer to a new opponent).

**RULE12 (risk gate, apply BEFORE submitting any tier2_realdata "X more than Y" /
count-comparison prop with no direct market):**

1. **Classify confidence**, not just direction:
   - HIGH: tier1_market (direct verified market) - submit as-is (RULE2).
   - HIGH: tier2_realdata where a RELATED market (corner/card handicap, goal-margin) exists
     and AGREES with the ESPN-based direction - submit near-raw (RULE7).
   - **LOW**: tier2_realdata "X more than Y" with NO related market, where the gap is driven
     primarily by ONE team's average being an outlier (check: does removing the single
     highest/lowest game from that team's n=5 sample flip or halve the gap? If yes, LOW
     confidence).
   - LOW: any estimate where RULE10's blowout-inversion risk applies (a clear favorite is
     involved AND the prop's direction depends on the UNDERDOG's historical rate holding up).

2. **For LOW-confidence estimates, shrink toward 0.5 using the crowd-prediction formula as a
   FLOOR, not a target**: don't go further from 0.5 than `crowd_pred = 0.514 + 0.61*(us-0.5)`
   would imply for a HIGH-confidence version of the same `us`. I.e., if our LOW-confidence
   `us` is 0.15 (like SWE-TUN Q2), the crowd-implied "compressed" version would be
   `0.514+0.61*(0.15-0.5) = 0.30`. Submitting somewhere in the 0.30-0.40 range (between
   crowd's compression and our raw number) caps the downside: at p_true=1 (worst case),
   sq_err at 0.35 = 0.4225 vs sq_err at 0.15 = 0.7225 - shrinking to 0.35 would have turned
   -33.9 into roughly -16, while only modestly reducing the upside if we'd been right.

3. **Always ask**: "if I removed the single most extreme data point behind this estimate,
   would my number change by more than 10pp?" If yes, that data point IS the estimate, not
   supporting evidence for it - treat as LOW confidence (this retroactively flags Tunisia's
   29-foul outlier vs Mali, which drove their 15.4 average from what would otherwise be ~12).

**This does NOT contradict "submit your true belief"** - it's a recognition that for these
specific prop types, our POINT ESTIMATE process has a known, recurring failure mode (4/85
questions, but -153.85 of damage), and a wider/shrunk estimate IS closer to our true
(uncertainty-inclusive) belief than the raw point estimate.

---

## Sources Cited / Cross-references
- `settled_markets_ledger.json` - the 85-row dataset this analysis is built on.
- `project_crowd_bias_model.md` - RULE1-10, especially RULE7/8/10 (the failure modes RULE12
  is designed to catch).
- `crowd_consensus_prediction_research.md` - §6 formal scoring-rule treatment; §1 favorite-
  longshot bias literature (Snowberg & Wolfers) - now empirically confirmed at ~7pp/~4pp.
