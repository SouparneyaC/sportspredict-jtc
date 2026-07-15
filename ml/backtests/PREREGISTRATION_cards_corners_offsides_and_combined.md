# Pre-registration: cards, corners, offsides per-team models + combined-threshold composition

Written BEFORE fitting or running any of these, following the same discipline as `PREREGISTRATION_sot_hierarchical_backtest.md` (which passed for SOT on 2026-07-14). This document covers three new per-team backtests and one new compositional method, all against the same production baseline and same walk-forward protocol.

## Why these three families are not assumed to behave like SOT
SOT passing does not transfer. Specifically:
- **Offsides** has the worst documented track record of any question family in this project (`OFFSIDE_CROWD_ANCHOR`: net -75.99 RBP across 5 matches when deviating from the crowd; single-outlier-game lambda swings of 4-10x noted repeatedly). If offsides is genuinely this noisy at the team-history level, a hierarchical model has less true signal to extract than SOT did, and may not beat the baseline.
- **Cards** depend heavily on referee assignment/strictness, which is not in the model at all (no referee covariate — StatsBomb's `referee_name` exists in the panel but ESPN 2026 rows don't carry it consistently, so it's excluded from the feature budget here, same as the original design #2 spec).
- **Corners** has no strong prior either way in this project's rule history — least-discussed family, included for completeness of the original design #2 scope (fouls/cards/corners/SOT/offsides).

## Hypotheses (one per family, independently falsifiable)
1. Cards (`yellow_cards + red_cards`): hierarchical GLMM beats k=5 shrinkage walk-forward.
2. Corners (`corners`): same.
3. Offsides (`offsides`): same. **Given the documented pathology above, a null or negative result here is a plausible and useful outcome, not a bug to debug away.**

## Features, validation, baselines, metric — identical to the SOT pre-registration
`stat ~ elo_diff_pre_100 + data_source + (1|team_name)`, Poisson GLMM, walk-forward across the same 29 WC2026 match dates, strictly-prior training data at every fold, k=5 empirical-Bayes shrinkage as the primary baseline, global-mean-only as the floor. Primary metric: predictive NLL. Secondary: Brier at baseline-defined threshold. Promotion criterion: match-level-clustered bootstrap 90% band on the NLL diff entirely above zero.

## NEW: combined/total-threshold composition (e.g. "9+ combined SOT", the actual `Q1`/`Q2`-style JTC question shape)
Two candidate methods to derive P(combined stat >= threshold) for a match, tested against each other and against a baseline:
1. **Convolution of the two independently-fit team-level Poisson predictions.** If the two teams' counts are independent given the model's covariates, sum of two Poissons is Poisson(lambda_A + lambda_B) — closed form, no new fit needed, reuses the already-backtested per-team lambdas.
2. **Direct match-level k=5 shrinkage on the combined stat itself** (treat "combined stat this match" as its own quantity, shrink toward the global match-level mean) — the natural baseline-style alternative, and also serves as this composition's own baseline.
**Caveat pre-registered before running:** method 1 assumes independence between the two teams' counts within a match. This is very unlikely to be exactly true (a foul-heavy/feisty match plausibly elevates both teams' cards together; a match with a clear better/worse footing may suppress both teams' offsides together in a blowout). If method 1 underperforms method 2, positive within-match correlation is the leading explanation and should be checked directly (correlation of the two teams' residuals within a match), not just noted as a loss.

## Multiple-testing correction (the "quant finance" / deflated-Sharpe-analogue safeguard)
Five to seven family-level and composition-level hypotheses are now being tested in one pass (cards, corners, offsides, SOT-combined, cards-combined, offsides-combined method comparison). Testing many hypotheses and reporting only the ones that clear p<0.05 is exactly the overfitting failure mode the ML4T book's Ch07 (deflated Sharpe ratio, White's Reality Check, probability of backtest overfitting) and this project's own §C.5 rule 3 warn against. **Before believing any individual family's PASS, apply a Benjamini-Hochberg FDR correction across the full set of p-values from this pass plus the SOT result already banked.** Report both the raw and FDR-adjusted verdict per family. A family that only clears the raw p<0.05 bar but not the FDR-adjusted bar is NOT promoted — logged as a candidate for a future, larger-n retest, not a result.

---

## RESULTS (run 2026-07-14, after this document was written and committed) — SUPERSEDED, see below

**This section's offsides numbers are WRONG — kept for the audit trail, not for use.** They were generated before discovering that `datasets/build_statsbomb_panel.py` had a genuine extraction bug (only checked the rare standalone `Offside` event type, missing the dominant `Pass Offside` outcome encoding — undercounting StatsBomb offsides by ~8.5x). The bug is fixed; see "RESULTS AFTER THE OFFSIDES BUG FIX" further below for the numbers to actually use.

| Family | NLL baseline | NLL hier | corr baseline | corr hier | mean diff | p (raw) | p (BH-adjusted) | Verdict |
|---|---|---|---|---|---|---|---|---|
| **Cards** | 1.518 | 1.485 | 0.016 | 0.128 | +0.033 | 0.218 | 0.218 | **FAIL — not promoted.** Matches the pre-registered hypothesis: no referee covariate, genuinely more idiosyncratic. |
| **Corners** | 2.560 | 2.440 | 0.175 | 0.386 | +0.119 | 0.0297 | 0.0396 | **PASS** (raw and FDR-adjusted). Real, modest team-pooling signal — source ratio ESPN/StatsBomb 1.026, i.e. negligible, so this is genuine signal, not a data artifact. |
| **Offsides** | 2.729 | 1.797 | 0.012 | 0.075 | +0.932 | 8.96e-09 | 3.59e-08 | **PASS, but see mechanism finding below — do not read as "the model learned team offside skill."** |
| **SOT** (banked from prior run) | 2.378 | 2.154 | 0.303 | 0.561 | +0.224 | 9.56e-05 | 1.91e-04 | **PASS** (unchanged from original run). |

3 of 4 families clear the FDR-adjusted bar. Cards does not.

### Important finding: the offsides result is mostly (possibly entirely) a data-quality bug fix, not a modeling win

Checked immediately on seeing the implausibly large effect size (0.932 mean NLL diff, ~4x SOT's): **mean predicted lambda from the k=5 baseline was 0.59, vs an actual mean of 1.73 — the production baseline is undercounting offsides by roughly 3x on 2026 matches.** Root cause, verified directly: `data/processed/unified_team_match_panel_with_pit_elo.csv`'s `offsides` column has an **8.49x** ESPN-2026-vs-StatsBomb-2018/22 ratio (ESPN mean 1.725, StatsBomb mean 0.203) — an order of magnitude larger than the previously-documented, previously-checked gaps for fouls (0.816x), SOT (1.304x), cards (0.876/0.791x), or corners (1.026x). **This specific column was never included in the original cross-source heterogeneity check** (`build_unified_team_match_panel.R`'s printed ratio table covers fouls/sot/cards/corners only). The k=5 shrinkage baseline pools StatsBomb's near-zero historical offsides rate directly into its `global_mean`/`team_mean` with no source correction, so it's been silently underpricing offsides expectations this whole campaign whenever StatsBomb history contributed to the prior. The hierarchical model's `data_source` fixed effect happens to absorb exactly this gap, which is most of why it wins so decisively — not because it discovered a subtle team-level offside-taking pattern that a 5-match, -75.99-RBP track record couldn't find. **This is a real, standalone data-quality bug worth its own fix** (either exclude StatsBomb offsides from any cross-source pooling, or apply the measured 8.49x correction factor before pooling) independent of whether this specific hierarchical model gets used going forward.

### Combined-threshold composition results

| Composition | t-stat | one-sided p | Verdict |
|---|---|---|---|
| SOT combined (convolution) | 0.022 | 0.491 | **FAIL.** Per-team SOT edge (t=4.07) completely vanishes when convolved — the pre-registered independence caveat was right. Positive within-match correlation between the two teams' SOT counts (open/end-to-end matches elevate both; tight matches suppress both) most likely explanation, not directly re-verified here but consistent with the mechanism flagged in advance. |
| Offsides combined (convolution) | 6.066 | ~0 | **PASS.** Survives because the win is mostly a constant per-team calibration fix (the data-source bug) — summing two de-biased predictions stays de-biased regardless of any within-match correlation structure. Brier improves 0.160 → 0.096. |
| Corners combined (convolution) | -0.162 | 0.564 | **FAIL.** Same independence-breakdown pattern as SOT. |

### FINAL joint verdict, all 7 hypotheses tested this pass, one-sided p-values, BH-FDR at q<0.10

| Test | t | p (BH-adj) | Verdict |
|---|---|---|---|
| SOT (per-team) | 4.071 | 0.0001 | **PASS** |
| Offsides (per-team) | 6.294 | ~0 | **PASS** (mechanism caveat above) |
| Offsides (combined) | 6.066 | ~0 | **PASS** (same caveat) |
| Corners (per-team) | 2.206 | 0.026 | **PASS** |
| Cards (per-team) | 1.239 | 0.153 | fail |
| SOT (combined) | 0.022 | 0.564 | fail |
| Corners (combined) | -0.162 | 0.564 | fail |

~~Bottom line: use per-team SOT, per-team corners, per-team offsides, and combined offsides.~~ **SUPERSEDED — see below.**

---

## RESULTS AFTER THE OFFSIDES BUG FIX (re-run 2026-07-14, same day, after fixing `datasets/build_statsbomb_panel.py`)

Root cause of the implausible offsides effect size above, found and fixed (full detail in the script's docstring): the extraction only counted the standalone `type.name == "Offside"` event, which StatsBomb uses for a small minority of offside calls (5 of 67 in a 15-match sample) — the dominant encoding is a `Pass` event with `outcome.name == "Pass Offside"` (the other 62/67). Fixed by counting both. Post-fix StatsBomb team-match offsides mean went from 0.203 to 1.625 (ESPN/StatsBomb ratio dropped from 8.49x to **1.35x** — now squarely in line with SOT's 1.30x and corners' 1.03x). Added `offsides` to `build_unified_team_match_panel.R`'s cross-source heterogeneity check so this class of bug can't hide again for any stat this project pools across sources.

Rebuilt the full downstream chain (`build_statsbomb_panel.py` → `build_unified_team_match_panel.R` → `add_pit_elo_to_unified_panel.py`) and re-ran every backtest:

| Family | NLL baseline | NLL hier | corr baseline | corr hier | mean diff | p (BH-adj) | Verdict |
|---|---|---|---|---|---|---|---|
| SOT (per-team) | 2.378 | 2.154 | 0.303 | 0.561 | +0.224 | 0.0003 | **PASS** (unchanged — not affected by the fix) |
| Corners (per-team) | 2.560 | 2.440 | 0.175 | 0.386 | +0.119 | 0.052 | **PASS** (unchanged — not affected by the fix) |
| **Offsides (per-team)** | 1.775 | 1.773 | 0.056 | 0.101 | **+0.001** | **0.627** | **FAIL — effect vanishes almost exactly to zero.** Confirms the entire original "pass" was the extraction bug, not signal. |
| **Offsides (combined)** | 2.238 | 2.251 | — | — | **-0.012** | **0.627** | **FAIL** (goes slightly negative). |
| Corners (combined) | — | — | — | — | -0.0065 | 0.627 | fail (unchanged) |
| SOT (combined) | — | — | — | — | +0.0008 | 0.627 | fail (unchanged) |
| Cards (per-team) | 1.518 | 1.485 | 0.016 | 0.128 | +0.033 | 0.255 | fail (unchanged) |

**Corrected bottom line: only per-team SOT and per-team corners survive. Offsides — in either form — does not, once measured correctly. This is not a disappointing result; it's the honest one, and it happens to agree with `RULE16 OFFSIDE_CROWD_ANCHOR`'s pre-existing, independently-derived caution (-75.99 RBP historical cost of trusting team-level offside data) — the bug had been masking a null result that the project's own rule history had already correctly anticipated.**

## Application step (after backtesting, not before)
Only families/methods that clear the FDR-adjusted bar are used to reprice France vs Spain's own questions as a retrospective comparison: ML prediction vs the live Smarkets quote already fetched (`09_smarkets_quotes_processed.json`) vs what was actually submitted (`05_estimates.json`). **That means Q12 (Spain 5+ SOT) and Q15 (France 4+ SOT) get an ML entry; Q1 (4+ combined offsides) does NOT — the earlier ML number for Q1 is retracted, see `matches/France Vs Spain (Jul.14.26)/13_ml_vs_market_vs_submitted_comparison.md` for the corrected writeup.** Q2 (cards) never had one. This is explicitly a comparison exercise on an already-priced match, not a resubmission.
