# Code Audit Findings — Calibration Gap Investigation

Date: 2026-06-10
Scope: (1) `home_team`/`away_team` labeling convention for `neutral=TRUE` matches in
martj42's `results.csv`; (2) line-by-line audit of `elo.py`, `poisson_goals.py`,
`dixon_coles.py`, `predict.py` against `research_notes.md` and the eloratings.net
formula.

---

## Part 1 — `home_team`/`away_team` labeling for neutral matches

### 1.1 No documented rule found

- The dataset's own `data/international_results/README.md` documents `neutral`
  (TRUE/FALSE, "whether the match was played at a neutral venue") but says **nothing**
  about how `home_team` vs `away_team` is assigned when `neutral=TRUE`. It only
  documents the non-neutral case (current team name vs country-at-time-of-match).
- Web search of the upstream GitHub repo (martj42/international_results), its README,
  and general discussion turned up no explicit statement of a convention (alphabetical,
  FIFA seeding, draw position, federation, coin flip, etc.). The repo's git history as
  vendored here is a single squashed "update" commit — no historical commit messages
  shed light on this either.
- Conclusion: **this appears to be undocumented / not governed by a single rule.**
  Likely explanation (see 1.3): it's an artifact of however each tournament's source
  (Wikipedia infobox order, RSSSF fixture listing, official fixture-list ordering) listed
  "Team A v Team B" for that specific competition, which varies by competition/era/source.

### 1.2 Empirical confirmation of the +23.8 Elo skew

Reproduced on the full panel (`data/processed/elo_match_panel.csv`, 49,472 historical
rows):

```
Neutral (n=13,114):     mean(elo_home_pre - elo_away_pre) = +23.93
Non-neutral (n=36,358): mean(elo_home_pre - elo_away_pre) = +6.48

Neutral:     home_team better-rated in 7,311/13,114 = 55.75%
Non-neutral: home_team better-rated in 18,469/36,358 = 50.80%
```

So yes — for neutral matches, `home_team` is the higher-Elo side ~56% of the time vs
~51% for non-neutral (chance baseline ~50%). This is a real, if modest, skew.

### 1.3 Pattern found: alphabetical ordering correlates strongly, but inconsistently by tournament

Across **all 13,114 neutral matches**, `home_team < away_team` alphabetically in
**62.83%** of cases — well above the 50% chance level. But this is NOT a uniform rule;
it varies wildly by tournament:

| Tournament | % home_team alphabetically first |
|---|---|
| Amílcar Cabral Cup | 87.7% |
| Merdeka Tournament | 82.6% |
| South Pacific Games | 79.7% |
| Copa América | 78.7% |
| Friendly | 70.0% |
| King's Cup | 71.6% |
| FIFA World Cup | 64.9% |
| African Cup of Nations | 59.9% |
| FIFA World Cup qualification | 50.6% |
| AFC Asian Cup qualification | 46.6% |
| AFF Championship | 41.5% |
| Southeast Asian Games | 40.2% |

Spot-checked 2018 FIFA World Cup (59 neutral group/knockout matches): alphabetical
home-first in only 12/20 sampled (~60%, consistent with the 64.9% overall figure but
clearly not a hard rule — e.g. "Morocco vs Iran", "France vs Australia" are NOT
alphabetical).

Cross-checked the same 2018 WC sample against Elo: better-rated team was `home_team`
in 33/59 = 55.9% — close to the global 55.75% neutral figure, again a mild skew, not a
hard "Pot 1 / seeding" rule (e.g. Tunisia (1765) was listed home over England (1988),
the much stronger team).

For tournaments with extreme **anti**-alphabetical or near-50/50 ratios (e.g. AFF
Championship 41.5%, Southeast Asian Games 40.2%), spot-checking 1996 AFF Championship
shows a classic **round-robin schedule pattern** — each team appears roughly equally
often as `home_team` and `away_team`, consistent with mechanical pairing order from a
round-robin schedule generator (circle method) rather than any team-quality-based rule.

### 1.4 Bottom line for Part 1

- No single documented or empirically-clean rule (not pure alphabetical, not pure
  Elo/seeding, not pure "host confederation"). The home/away labeling for neutral
  matches looks like a **patchwork of source-specific listing conventions** (Wikipedia
  match-report/infobox order for big tournaments — which itself often lists the
  "favorite"/seed first or alphabetically — vs. round-robin schedule order for
  smaller regional round-robins).
- However, the **net effect across the whole dataset is a real, non-trivial skew**:
  `home_team` in neutral matches is the better-rated (higher pre-match Elo) side ~56%
  of the time vs ~51% for non-neutral matches, and is alphabetically-first ~63% of the
  time vs the implicit ~50% you'd expect from a name-symmetric draw.
- **Implication for the model**: the Elo-difference covariate (`elo_home - elo_away`)
  for neutral matches is *not* drawn from a "label-blind" distribution — it has a
  small positive mean (+23.9) baked in by the labeling convention itself. The Poisson
  model's `b2*(elo_home-elo_away)` term will, on average, correctly push `lambda_home
  > lambda_away` slightly for neutral matches — which is *appropriate* given home_team
  really is somewhat better on average. This is not obviously a "bug" per se, but it
  means **any audit of "the model on neutral matches" needs to remember `home_team`
  isn't a neutral coin-flip identity** — comparisons of "neutral-match home win rate
  vs predicted" should be interpreted with this in mind (see Part 2, finding 2.5).

---

## Part 2 — Code audit findings, ranked by relevance to the calibration gap

### 2.1 [CONFIRMED, HIGH RELEVANCE] `is_home` ignores `neutral` in `poisson_goals.py::build_design_matrix()`

**File**: `model/poisson_goals.py`, lines 81-89.

```python
# home team's goal-scoring observation
y.append(hs)
X.append([1.0, 1.0, elo_home - elo_away])
w.append(weight)

# away team's goal-scoring observation
y.append(as_)
X.append([1.0, 0.0, elo_away - elo_home])
w.append(weight)
```

This is the bug already identified by the user: `is_home` (column 2 of `X`) is set to
1/0 purely based on the `home_team`/`away_team` data labels, with **no reference to
`row["neutral"]`** at all — despite `row["neutral"]` being present in every row of
`elo_match_panel.csv` and being read correctly by `elo.py` (training the Elo ratings
themselves), and by `fit_rho.py`, `backtest_harness.py`, `backtest_diagnostics.py`,
and `backtest_single.py` (all of which compute `home_adv = 0.0 if row["neutral"] ==
"TRUE" else 1.0` before forming `lambda_home`).

**This is exactly the "same quantity computed two different ways in two different
files" pattern the brief asked about**: the Poisson *training* code treats "is this a
home-advantage situation" as `home_team-vs-away_team label` (100% of rows get
is_home∈{1,0} regardless of neutral), while the *prediction/backtest* code treats it
as `neutral flag` (`home_adv=0` for ~26% of rows). Training and inference disagree
about what `b1`/`home_adv` represents for ~13,000 of ~49,400 matches (26.4%).

**Direction & magnitude of bias**: the ~13,051-13,114 "is_home=1 but should be 0"
training rows dilute the true home-advantage signal — classic regression-toward-zero
from contaminating a binary covariate with ~26% mislabeled-as-1 cases that have zero
true effect. This **attenuates `b1` toward zero**. Current `b1=0.2562` (≈+29% goals);
user's rough estimate of the "true" value (~0.35, ≈+42% goals) is consistent with the
attenuation direction and a plausible magnitude given a 26% contamination rate
(0.2562/0.35 ≈ 0.73, and (1-0.264)≈0.736 — strikingly close, consistent with simple
linear dilution intuition for a 0/1 covariate, though the GLM/log-link isn't exactly
linear so this is approximate).

**Connection to symptom**:
- For **non-neutral** matches (74% of data), `predict.py`/`backtest_harness.py` apply
  `home_adv=1`, so `lambda_home` gets the (too-small) `b1`. This **directly**
  under-states `lambda_home` relative to `lambda_away`, producing P(home win) too low
  — i.e. "too cautious" — for non-neutral matches. **This plausibly explains a large
  share of the non-neutral-match gap.**
- For **neutral** matches, `predict.py` applies `home_adv=0`, so `b1` (and its
  attenuation) **does not directly enter** `lambda_home`/`lambda_away` at prediction
  time. **Fixing this bug alone will NOT directly close the neutral-match gap** — the
  persistence of the gap on neutral matches needs another explanation (see 2.5, 2.6).

**Verdict**: highest-confidence, highest-impact finding for the **non-neutral**
portion of the gap. Re-fitting with `is_home = 1.0 if (is_home_team and not neutral)
else 0.0` (and similarly `0.0` for the away observation always, i.e. only the
home_team's row gets `is_home=1`, and only when `neutral==FALSE`) should increase
`b1`, raising `lambda_home/lambda_away` and P(home win) for non-neutral matches —
moving in the right direction to close part of the gap.

---

### 2.2 [NEW FINDING, MEDIUM-HIGH RELEVANCE] Same `neutral`-handling inconsistency exists between `poisson_goals.py` (training) and FIVE other files (prediction/backtest) — broader than just one function

Beyond `build_design_matrix()`, the following files all implement
`home_adv = 0.0 if row["neutral"] == "TRUE" else 1.0` and then `lambda_home =
exp(b0 + b1*home_adv + b2*elo_diff)`:

- `model/predict.py` (line 65, via `--neutral` CLI flag)
- `model/backtest_harness.py` (line 72, `predict_one()`)
- `model/backtest_diagnostics.py` (via `bh.predict_one()`)
- `model/backtest_single.py` (line 67)
- `model/fit_rho.py` (line 48)

All FIVE of these are internally consistent with each other (same formula, same
neutral-gating). Only `poisson_goals.py`'s `build_design_matrix()` is the odd one out.
This means: **the model is trained on one definition of "home advantage applies" and
evaluated/predicted on a different, stricter definition** — a textbook train/serve
skew. This reframes finding 2.1 as not just "one function has a bug" but "the
training pipeline and the entire prediction/evaluation pipeline disagree about a core
semantic," which is worth flagging explicitly since fixing `poisson_goals.py` alone
(and re-fitting) is the *complete* fix — no changes needed to the other 5 files, which
already implement the "correct" (intended) semantics.

---

### 2.3 [NOT A BUG, but worth noting] `elo.py`'s home-advantage formula matches eloratings.net / Wikipedia exactly

Checked line-by-line against the published World Football Elo Ratings formula:

- `R_new = R_old + K * G * (W - We)` ✓ matches `delta = k * g * (w_home - we_home)`
  (lines 135-137).
- `G` (goal-difference multiplier): 1 / 1.5 / (11+|diff|)/8 for |diff|≤1 / ==2 / ≥3 ✓
  matches `goal_diff_multiplier()` (lines 73-79) and the published "½ for 2-goal
  margin, ¾+(N-3)/8 for N≥3" rule exactly (algebraically (11+N)/8 = 1.75+(N-3)/8 for
  N≥3, and 1.5 for N=2).
- `We = 1/(10^(-dr/400)+1)`, `dr = (R_home-R_away)+100` if not neutral, else
  `R_home-R_away` ✓ matches `expected_result()` + lines 130-132 exactly, including the
  +100 home-advantage convention (eloratings.net's stated value).
- K-factor tiers (60/50/40/30/20 for WC finals / continental finals / qualifiers /
  other / friendlies) ✓ match the published tiers, and `tournament_kfactor_map.csv`'s
  classification looks reasonable (spot-checked: FIFA World Cup=60, Copa
  América/UEFA Euro/AFC Asian Cup/African Cup of Nations=50, qualifiers=40,
  Friendly=20, everything else=30).
- `neutral` is read correctly here (`neutral = row["neutral"] == "TRUE"`, line 121) and
  the +100 home-advantage offset is correctly applied ONLY to the *expected-result*
  calculation (`dr`), NOT added to the stored `elo_home_pre`/`elo_away_pre` values that
  feed `poisson_goals.py`. So there's **no double-counting of the +100** via the
  stored Elo ratings themselves (this concern, raised in
  `data/calibration_research_notes.md` §3.4, is correctly resolved — confirmed by
  reading the code).

**Verdict**: `elo.py` is internally correct relative to the published formula. Not a
contributor to the calibration gap (beyond the general "is HOME_ADVANTAGE=100 the
right empirical value" question already discussed in `calibration_research_notes.md`,
which is a calibration-of-an-input question, not a code-correctness bug).

---

### 2.4 [NOT A BUG, minor note] `dixon_coles.py` tau correction matches DC97 spec exactly

`tau(i,j,lam_home,lam_away,rho)` (lines 26-38) matches `research_notes.md` §1.2
formula exactly for all four corrected cells (0,0)/(0,1)/(1,0)/(1,1) and returns 1.0
otherwise. `scoreline_grid()` correctly renormalizes after applying tau and truncating
at `max_goals` (default 10, or 8 in `backtest_harness.py` — a difference in truncation
depth between `predict.py`/`backtest_single.py` (10) and `backtest_harness.py` (8),
but at `lambda` values typical for international football (~1-2.5), `Pois(X>8)` is
already <0.1%, so this is negligible for H/D/A probabilities — not a meaningful
source of the multi-percentage-point gap).

`fit_rho.py`'s grid search range (`-0.30` to `0.10`, step 0.01) is wide enough to have
found the reported -0.06 optimum without hitting a boundary — not a constraint issue.

**Verdict**: not connected to the calibration-gap symptom.

---

### 2.5 [NEW FINDING, LOW-MEDIUM RELEVANCE, connects Part 1 to Part 2] The neutral-match `home_team` Elo skew (+23.8) is *already* (correctly) used by `b2`, but may itself be a source of residual bias if `b2` is mis-scaled

As established in Part 1, for `neutral=TRUE` matches, `home_team` has +23.9 Elo on
average vs `away_team` — i.e., is mildly the "better" side more often than chance.
`predict.py`/`backtest_harness.py` correctly feed `elo_home - elo_away` (positive on
average for these rows) into `b2*(elo_home-elo_away)`, so `lambda_home > lambda_away`
on average for neutral matches even with `home_adv=0` — which is *appropriate* (the
better team should be more likely to score more), not a bug.

**However**, this interacts with the *separately-discussed* (in
`calibration_research_notes.md` §1) hypothesis that `b2` itself is attenuated
(too-small) due to noisy/bootstrapped Elo. If `b2` is too small, then the *correct*
direction-of-skew signal carried by `elo_home - elo_away` on neutral matches is
**under-weighted** — i.e., the model under-predicts how much more likely the
(on-average-somewhat-better) `home_team` is to win neutral matches. This is a
plausible **partial** explanation for "the gap persists on neutral matches": it's not
that neutral matches have some *separate* home-advantage bug, but that **whatever
causes `b2` attenuation (if it exists) affects neutral matches exactly as much as
non-neutral ones**, and Part 1's labeling skew means neutral matches DO have a
(smaller, ~24-Elo-point) "favorite-labeled-as-home_team" signal for `b2` to act on,
just like non-neutral matches have a larger one. So a `b2`-attenuation story is fully
consistent with "gap persists similarly on neutral matches" — this doesn't newly
implicate `b2`, but it does mean **the neutral-match gap is not evidence AGAINST the
b2-attenuation hypothesis** (contrary to a possible naive reading that "neutral
matches have nothing for b2/Elo to get wrong").

**Verdict**: doesn't independently explain the gap, but is relevant context for
interpreting the neutral-match diagnostic in `backtest_diagnostics.py` — the
neutral-match P(home win) is NOT a clean "50/50 + pure Elo-diff effect" baseline; it
inherits the labeling-convention skew documented in Part 1.

---

### 2.6 [SPECULATIVE, LOW RELEVANCE but flagged for completeness] Recency weighting (`XI_DEFAULT=0.0008`) and `most_recent` date — checked, no bug found, but one edge case worth noting

`build_design_matrix()` computes `most_recent = max(date.fromisoformat(r["date"]) for
r in rows)` where `rows` comes from `load_panel()`, which already filters out future
fixtures (`if row["home_score"] == "": continue`). So `most_recent` = the most recent
*completed* match (2026-06-09 in the current panel), not a future fixture date — this
is correct; recency weights are computed relative to "now" as represented by the most
recent real result, not contaminated by the 72 future NA-score rows in
`elo_match_panel.csv`.

One thing to flag (not a bug, but worth knowing): `XI_DEFAULT=0.0008/day` gives a
half-life of `ln(2)/0.0008 ≈ 866 days ≈ 2.4 years`. With 49,400 matches spanning 1872-
2026 (154 years), the *effective* sample (per the docstring's own estimate, "effective
N~6850") is dominated by roughly the last ~10-15 years of matches. This means: (a) the
fitted `b0/b1/b2` are mostly informed by *recent* football, where `HOME_ADVANTAGE=100`
/ crowd effects may differ from the historical average (relevant to
`calibration_research_notes.md` §3.4's COVID-era HFA discussion — recent years include
COVID-affected 2020-2021 matches with reduced/no crowds, which could pull `b1` down
slightly, compounding with finding 2.1's attenuation in the same direction); and (b)
the recency weighting is **applied uniformly to both training observations per match**
(home and away rows get the same `weight`), which is correct/symmetric — no bug there.

**Verdict**: not a coding bug; a modeling-choice note. Could marginally compound
finding 2.1 (both push `b1` down) but is unlikely to be a primary driver — flagged for
completeness per the brief's request.

---

### 2.7 [NOT A BUG] `predict.py` lambda formula is consistent with `poisson_goals.py`'s training design (modulo finding 2.1)

`predict.py` lines 71-72:
```python
lam_home = math.exp(b0 + b1 * home_adv + b2 * (elo_home - elo_away))
lam_away = math.exp(b0 + b2 * (elo_away - elo_home))
```
This is the algebraically correct inverse of the training design matrix rows
`[1.0, is_home, elo_diff]` — i.e., IF `b0/b1/b2` were fit with `is_home` set
consistently with `home_adv` (neutral-aware), this formula would be exactly correct.
The only issue is that `b1` itself is mis-estimated due to finding 2.1 — `predict.py`
itself has no independent bug.

---

## Most Promising Lead

**Fix finding 2.1 first** (`build_design_matrix()` in `poisson_goals.py`): change the
home-team observation's `is_home` from a hardcoded `1.0` to `1.0 if neutral==FALSE
else 0.0` (and leave the away-team observation's `is_home` at `0.0` always — it's
already correct since away teams never get a home-advantage bonus regardless of
neutral). Re-fit `b0/b1/b2`. This is a **one-line, low-risk change** that:

1. Removes a genuine train/predict semantic mismatch (finding 2.2) — the model will
   then be trained on exactly the same `home_adv` definition that `predict.py`,
   `backtest_harness.py`, `fit_rho.py`, etc. already use at inference time.
2. Should increase `b1` from 0.2562 toward something like the user's ~0.35 estimate
   (de-attenuation from removing ~26% zero-effect contamination), which **directly
   increases `lambda_home/lambda_away` and P(home win) for the 74% of matches with
   `neutral=FALSE`** — moving those predictions in exactly the direction needed to
   close the "too cautious" gap.
3. Will NOT, by itself, close the gap for `neutral=TRUE` matches (where `home_adv=0`
   at prediction time regardless of `b1`) — for those, the leading hypothesis remains
   the `b2`/Elo-attenuation story already documented in
   `calibration_research_notes.md` §1, which Part 1's labeling-skew finding (2.5) is
   *consistent with* but doesn't independently confirm or refute.

**Recommended next step after the 2.1 fix**: re-run `backtest_diagnostics.py`'s
neutral vs non-neutral split. If the non-neutral gap shrinks substantially while the
neutral gap is largely unchanged, that (a) confirms 2.1 was a real and significant
contributor for non-neutral matches, and (b) cleanly isolates the remaining
neutral-match gap as a `b2`/Elo-measurement-error question — at which point
`calibration_research_notes.md`'s recommendation #1 (logit-space re-plot) becomes the
right next diagnostic for the *residual* gap.
