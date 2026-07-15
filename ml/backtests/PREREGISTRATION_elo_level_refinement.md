# Pre-registration: own-Elo-level term to fix the diagnosed elite-team underprediction

Written before refitting. Follow-up to the passed SOT/corners hierarchical backtests, targeting the specific bias found while investigating why the GLMM diverged from the market on France/Spain (both elite, high-shot-volume teams): the model's own top predicted-lambda tercile underpredicts actual SOT by a real amount (tercile-slope t=2.097, p=0.038; top-tercile-vs-zero p=0.15, not yet significant alone).

## Hypothesis
`elo_diff_pre` alone (relative to opponent) plus a team random intercept doesn't fully capture that some teams are just structurally high-shot-volume (Spain, France, Argentina) — the random intercept may be over-shrunk for teams with limited WC2026-specific history, since it's pooled with a single global variance across all 48 teams regardless of quality tier. Adding each team's own absolute point-in-time Elo (not just the opponent-relative diff) as a second fixed effect gives the model an additional, less-shrunk lever: `y ~ elo_diff_pre_100 + own_elo_pre_100 + data_source + (1|team_name)`.

## Validation
Identical walk-forward protocol as the original SOT/corners backtests (same 29 fold dates, same k=5 baseline, same match-clustered bootstrap). Two things checked, not just one:
1. Does it still beat baseline overall (the original result must survive)?
2. Does the top-tercile underprediction bias shrink toward zero?

## Promotion criterion
Only replaces the current SOT/corners model if it (a) still clears the original FDR-adjusted bar vs baseline, AND (b) measurably reduces the top-tercile residual bias. If it fixes the bias but stops beating baseline, or beats baseline by less, that's a real tradeoff to report honestly, not a win to claim.

---

## RESULT (run 2026-07-14)

| | Original: beats baseline | Original: top-tercile bias | Refined: beats baseline | Refined: top-tercile bias |
|---|---|---|---|---|
| SOT | p=0.0001 (mean diff +0.224) | +0.556 (p=0.15, ns) | p=0.0001 (mean diff +0.225) | +0.497 (p=0.20, ns) — **11% smaller** |
| Corners | p=0.030 (mean diff +0.119) | +0.231 (p=0.59, ns) | p=0.038 (mean diff +0.115) | +0.141 (p=0.74, ns) — **39% smaller** |

**Both promotion criteria technically met, but modestly, not decisively.** The refined model still clears the original bar (essentially unchanged for SOT, very slightly weaker for corners) and the top-tercile bias shrinks in both families — meaningfully for corners, marginally for SOT. Honest caveat: the top-tercile bias was never statistically distinguishable from zero even in the *original* model (p=0.15 and p=0.59) — so this refinement demonstrably doesn't hurt anything and directionally helps, but it isn't fixing a problem that was itself fully proven in the first place. **Verdict: promote the own-Elo-level term as the new default (no downside found, real if modest upside) — but don't oversell this as "the elite-team bias is now solved."**

