# Post-match analysis — England 1-2 Argentina (WC2026 SF, 2026-07-15)

Settled record: `23_post_match_results.json`. Result: Argentina win 1-2, advance to the final vs Spain;
England eliminated. **Final: +96.05 RBP, 10/15 beat crowd (67%)** — a strong, positive match. Every
one of the 15 submitted numbers matched our final pricing exactly (verified against files 16/17/19/20).

This match is unusually informative because it was the first live test of several methods built *this
cycle*. Below, what each one actually did.

## 1. The winning engine: DIRECT-market discipline on far-from-crowd questions

The four biggest wins were all the same shape — sit at a liquid market number well below the
compressed crowd, and refuse to inflate:

| Question | Us | Crowd | Outcome | RBP |
|---|---|---|---|---|
| 10+ combined corners | 0.25 | 0.45 | NO | **+34.89** |
| 8+ combined SOT | 0.45 | 0.58 | NO | **+32.30** |
| Bellingham score/assist | 0.30 | 0.44 | NO | **+28.32** |
| Kane scores | 0.36 | 0.44 | NO | **+18.03** |

These four alone were +113.5 RBP. Three are DIRECT-market questions (RULE2), one is market-derived
(Q6 SOT). The common thread is RULE17/Mbappé discipline — on Kane and Bellingham we explicitly
declined to push above the market on reputation, and both won large. This is the single clearest
lesson of the match: **the edge is trusting the liquid market when the crowd is compressed, not
out-modelling it.**

## 2. Vindication of this cycle's process investments

- **De-shrinkage pressure test (files 19-20) — directly vindicated.** It named `10+ combined corners`
  the single highest-premium question on the slate (+0.94 modelled, the farthest-from-crowd item). It
  was the single biggest win (+34.89). The whole thesis — points concentrate on far-from-0.5 questions
  where you sit correctly below the compressed crowd — played out almost exactly as mapped.
- **Penalty deep-research (file in `topics/penalties-red-cards/`) — paid off, +11.62.** We held Q3 at
  0.29 rather than nudging up toward the 0.32 knockout base rate, explicitly heeding the documented
  "we keep being too high on penalties" lesson. No penalty was awarded; sitting below the crowd (0.33)
  won. Had the research pushed us up, this would have been smaller or negative.
- **Corners-comparison Skellam model (the one new backtested composition, files 12/17) — correct side,
  +5.73.** Argentina did have more corners; the validated GLMM/Skellam called it and beat the crowd.
  A modest but genuine live win for the one model that passed a real walk-forward this cycle.
- **Álvarez deep-dive — vindicated, +6.44.** Pulling him to ~market (0.58) and finding a *null*
  high-stakes effect (rather than inventing an edge) was correct; he had a SOT, we won the right side.

## 3. The losses, and the one real lesson

| Question | Us | Crowd | Outcome | RBP | Read |
|---|---|---|---|---|---|
| Card before first goal | 0.35 | 0.50 | YES | **-28.43** | flagged lowest-confidence — the flag was right |
| Argentina 2+ goals | 0.30 | 0.39 | YES | -17.37 | market itself underpriced ARG scoring |
| Both teams carded | 0.55 | 0.66 | YES | -10.88 | cards ran high; crowd's higher read won |
| Messi scores | 0.50 | 0.45 | NO | -2.45 | directionally right, stopped short of market |
| Stoppage-time goal | 0.31 | 0.34 | YES | -0.52 | marginal |

**The load-bearing lesson is the card-before-first-goal loss (-28.43), our worst result.** It was the
*exact* question flagged as lowest-confidence in files 18 and 20 — a noisy base-rate signal (card
family, measurement-gap contaminated) sitting *far* from the crowd (0.35 vs 0.50). When a far-from-0.5
position is right it wins big (§1); when it's wrong on a *noisy* signal it loses big. Our own
margin-push research says exactly this: shrink noisy signals toward the crowd. We correctly *identified*
the low confidence but did not *act* on it — we held 0.35 instead of shading toward the crowd's 0.50.
Had we shrunk it even halfway, the loss roughly halves. **Standing rule to apply next time: when a
base-rate signal is flagged low-confidence AND sits far from the crowd, shrink it toward the crowd —
the far-from-crowd premium is only worth collecting on signals we actually trust.** This does not apply
to the DIRECT-market far-from-crowd questions (§1), which are sharp signals and correctly held.

Secondary notes: **Messi** (-2.45) — the high-stakes research was directionally correct (it pulled us
down from 0.65), but the market (0.365) and crowd (0.45) were lower still; RULE17 kept us above market
and we landed on the wrong side of a near-coin-flip. Small cost, but a reminder that when our own deep
research and the market agree on *direction*, going most of the way to the market may be right. **Cards**
(-10.88) and **Argentina 2+ goals** (-17.37) are both cases where the higher crowd/actual read beat
ours; the Argentina-goals one is notable because the *liquid market itself* (0.30) was on the wrong
side of an elimination-stakes scoring outcome — not a pricing error by us so much as the market
under-reading Argentina.

## 4. Net

+96.05 RBP and 10/15 beat-crowd is a top-tier match result, driven by disciplined market-trusting on
the high-premium far-from-crowd questions — precisely the behaviour the de-shrinkage and RULE17 work
prescribed. The single actionable improvement is to convert the "lowest-confidence" flag on noisy
far-from-crowd base rates into an actual shrink toward the crowd, which would have averted most of the
match's worst loss.
