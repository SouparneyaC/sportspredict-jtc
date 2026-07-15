# Pre-registration: first-substitution race model (Q14-style questions)

Written before fitting, per the same discipline as the SOT/corners/offsides pre-registrations. Scoped by `BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md` §C.3: this question type has an adequate historical panel (100 matches) and is domain-class (predicting a real observed outcome), so — unlike Q4 — a walk-forward-validated model is a legitimate thing to attempt here.

## Hypothesis
A team's own shrunk historical first-substitution-minute tendency, plus pre-match Elo diff (as a proxy for which team is more likely to find itself behind and sub early), predicts which of two teams substitutes first better than a naive 50/50 baseline, when evaluated walk-forward across the 100 WC2026 matches.

## Explicit scoping note (important, catches a mistake before it happens)
The obvious best predictor — which team is actually trailing at a given in-match minute — is NOT usable: JTC requires submission before kickoff, so no in-match state is available. Only pre-match-knowable covariates are used: each team's own historical first-sub-minute average (a real, observed team/manager tendency — e.g. France never subbed before minute 61 in any of its 6 games this tournament, Spain subbed as early as minute 45 three times) and Elo diff.

## Features, validation, baseline, metric
- Outcome: binary, did team A substitute strictly before team B (ties/no-data matches excluded).
- Features: team A's and team B's own shrunk (k=5 empirical-Bayes, same formula as the production baseline) historical mean first-sub-minute, computed from strictly-prior matches only; Elo diff.
- Model: logistic regression on (shrunk_avg_sub_min_B − shrunk_avg_sub_min_A) and elo_diff, refit at every walk-forward fold using only strictly-prior data.
- Baseline: naive 50/50.
- Metric: Brier score, match-level (one row per match, from team A's perspective).
- Promotion criterion: match-level bootstrap 90% band on the Brier improvement over 50/50 entirely on the improving side.

## Honest power caveat, stated in advance
Per the research doc's B.4: even if this model passes, it validates the *process* (do these covariates predict subbing-first across the historical panel), not tonight's specific FRA-ESP race — that single outcome remains one draw and cannot itself confirm or refute the model, however it resolves.

---

## RESULT (run 2026-07-14, after this document was written)

**FAIL — and not just "not distinguishable from baseline." The model is confidently WORSE than naive 50/50.** Walk-forward across 79 scored folds: mean Brier 0.2785 (model) vs 0.2500 (baseline). Bootstrap 90% band on the improvement: **[-0.0536, -0.0030] — entirely negative.** A team's own shrunk historical first-sub-minute tendency plus Elo diff does not predict who subs first; if anything, trusting it actively hurts relative to a coin flip.

**Plausible reasons, not further tested:** substitution timing is likely dominated by in-match score-state and tactical need (neither observable pre-match), swamping any fixed team-level tendency; only 2-3 features on ~79 small-training-set walk-forward folds is exactly the regime where a fitted model overfits noise a naive baseline can't.

**Practical conclusion for Q14 tonight: do not use this model.** The already-submitted number (0.60, from a simple pairwise comparison of France's and Spain's own recent first-sub minutes with a manual outlier check, `04_rules_applied.json`) is not improved on by a fitted cross-team model — if anything this result is evidence the simpler heuristic was the right level of sophistication for this question, consistent with the domain-class-over-meta-class lesson throughout this project. No change recommended.
