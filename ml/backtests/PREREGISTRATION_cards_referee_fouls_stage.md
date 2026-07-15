# Pre-registration: cards model refit with referee, fouls, and knockout-stage

Written before refitting. Follow-up to the original cards backtest FAIL
(`PREREGISTRATION_cards_corners_offsides_and_combined.md`, p=0.15-0.25 vs
baseline), prompted by a direct question about whether referee assignment,
foul rate, and match-stage/stakes were incorporated. They were not — the
original model was `cards ~ elo_diff_pre + data_source + (1|team_name)`,
explicitly missing a referee term (flagged as the leading hypothesis for
the failure at the time it was written).

## What was found investigating this, before touching the model
1. **Referee identity is available and was simply never extracted.** ESPN's
   raw event summaries carry it at `gameInfo.officials[0].fullName` (100/101
   2026 matches have it; wasn't pulled into any panel before now).
   StatsBomb's `referee_name` column already had it (254/256 rows). 48
   distinct referees across the StatsBomb portion, several officiating
   10-14 matches each -- enough repetition for a genuine `(1|referee_name)`
   random effect, not just singleton noise.
2. **Fouls and cards are meaningfully correlated** (r=0.449, p<1e-6, n=456)
   -- a team's own foul rate is legitimate, PIT-safe signal (using each
   team's own *historical, strictly-prior* foul rate, never the current
   match's foul count, which isn't known before kickoff).
3. **Cards rate and card timing both shift with tournament stage.** Pooled
   knockout matches (R16+QF+R32-tail, n=15) average 3.53 cards/match vs
   2.55 for group/R32; the share of cards in the final 20 minutes rises
   from 38.2% (group/R32) to 54.7% pooled knockout (chi-square p=0.043,
   n=15 knockout matches -- real but small-sample, flagged honestly, not
   pre-registered before this specific check was run so treat as motivated-
   but-unconfirmed until it's tested walk-forward).

## Refined model
`cards ~ elo_diff_pre_100 + own_elo_pre_100 + data_source + is_knockout + own_foul_rate_shrunk + (1|team_name) + (1|referee_name)`

`is_knockout` = 1 for R32/R16/QF/SF+ event IDs, 0 for group stage (known
pre-match, it's the fixed bracket). `own_foul_rate_shrunk` = each team's
k=5-shrunk historical foul rate as of strictly-prior matches (same PIT
treatment as everything else this session).

## Validation and promotion criterion
Identical walk-forward protocol, same 29 fold dates, same match-clustered
bootstrap. Promotion criterion unchanged: 90% bootstrap band on the NLL
improvement over the k=5 baseline entirely above zero. This refit is
explicitly allowed to fail again -- adding correct-in-principle features
to a model that failed for lack of them is a reasonable hypothesis, not a
guaranteed fix, and this document says so before running it.

---

## RESULT (run 2026-07-14)

**FAIL, again — but now for a much better-understood reason.** n=196 team-match predictions, 98 matches. Mean NLL: baseline 1.518, refined model 1.486. Match-level: mean diff +0.032, t=1.153, **p=0.252**, bootstrap 90% band **[-0.0147, +0.0773]** — crosses zero. Referee coverage was complete (196/196 test rows had a referee the model had seen in training before, so this isn't a "referee identity mostly unseen" problem). Essentially unchanged from the original model's own failure (+0.033, p=0.218) — the confidence interval width barely moved either.

**What this actually tells us, which is more valuable than a pass would have been:** the original hypothesis — "cards fails because referee/fouls/stage aren't in the model" — is now directly ruled out, not just assumed. All three were real, confirmed gaps (referee data existed and was unused; fouls-cards correlation is real, r=0.449; knockout matches do show more and later cards, p=0.043 on a small sample) and fixing all three didn't move the result. Two live explanations, not resolved here: (1) cards may be genuinely driven more by in-match dynamics (game state, specific players on the pitch, live tactical fouling) than anything knowable before kickoff, which no pre-match model of any sophistication can fix; (2) the added model complexity (2 random effects + 3 more fixed effects) may cost more in per-fold estimation variance than it recovers in bias, especially in early-tournament folds with still-modest training data. **Verdict: cards stays a market-anchored / crowd-anchored question, not a model-driven one, for this tournament** — and this is now a much more load-bearing conclusion than before, since it survived a real, targeted attempt to fix it rather than a first-pass failure that might have just been missing an obvious feature.
