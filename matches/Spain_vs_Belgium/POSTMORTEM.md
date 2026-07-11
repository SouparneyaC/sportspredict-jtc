# Spain vs Belgium Postmortem — QF, 2026-07-10

**Result:** Spain 2-1 Belgium (30' Fabián Ruiz, 41' Charles De Ketelaere, 88' Mikel Merino).
**Record:** 7 of 15 correct direction, 8 wrong. This was a genuinely bad night for the pipeline —
no dispute there. This doc traces exactly where the damage came from, because the initial
read ("Monte Carlo was the problem") doesn't survive contact with the actual settlement data.

---

## 1. Full settlement

| # | Question | Estimate | Outcome | Direction | Miss size | Method |
|---|---|---|---|---|---|---|
| 1 | Spain advances to semis | 0.76 | YES | correct | 0.24 | ordered logit + Dixon-Coles blend |
| 2 | Tied at HT | 0.40 | YES (1-1 at HT) | **wrong** | 0.60 | Monte Carlo sim |
| 3 | Belgium leads at any point | 0.32 | NO | correct | 0.32 | Monte Carlo sim |
| 4 | Sub at halftime | 0.55 | NO (first sub 55') | **wrong** | 0.55 | new base-rate panel |
| 5 | Goal before 24' | 0.46 | NO (first goal 30') | correct | 0.46 | Monte Carlo sim |
| 6 | Goal after 69' | 0.48 | YES (88' goal) | **wrong** | 0.52 | Monte Carlo sim |
| 7 | BTTS | 0.43 | YES | **wrong** | 0.57 | Dixon-Coles + Monte Carlo avg |
| 8 | Yamal score/assist | 0.27 | NO (0G 0A) | correct | 0.27 | direct in-tournament rate |
| 9 | De Bruyne 1+ SOT | 0.45 | YES (1 SOT) | **wrong** | 0.55 | two-stage participation x rate |
| 10 | Lukaku 1+ SOT | 0.46 | NO (0 shots) | correct | 0.46 | two-stage participation x rate |
| 11 | Spain 5+ SOT | 0.60 | YES (8 SOT) | correct | 0.40 | EB-shrunk Poisson |
| 12 | Belgium 3+ SOT | **0.85** | **NO (2 SOT)** | **wrong** | **0.85** | EB-shrunk Poisson |
| 13 | Spain 6+ corners | 0.62 | NO (5 corners) | **wrong** | 0.62 | EB-shrunk Poisson |
| 14 | 4+ total cards | 0.30 | YES (exactly 4: 2+2) | **wrong** | 0.70 | 3-way weighted blend |
| 15 | Penalty or red | 0.33 | NO | correct | 0.33 | component-wise shrinkage |

Average miss distance across all 15: 0.496 — essentially coin-flip-level average error. Actual
match shape: Spain dominated 67.9%/32.1% possession and out-shot Belgium 17-5 (8 SOT to 2), yet
the scoreline stayed close because Belgium's only goal came from a set-piece header, not open
play, and both sides' cards arrived in stoppage time (90'+3', 90'+5').

---

## 2. What actually drove the damage: not Monte Carlo

The 4 Monte Carlo-driven questions (Q2, Q3, Q5, Q6) split exactly 2-2, and **both misses were
already close to a coin flip before the match** (0.40 and 0.48) — sum of miss-distance across
all 4 = 1.90, average 0.475, statistically indistinguishable from noise on genuinely uncertain
path-dependent props. This is what a well-calibrated estimate is *supposed* to do some fraction
of the time. Abandoning the simulation approach on the strength of this one match would be
discarding a sound method because of normal variance, not a demonstrated flaw.

The two largest misses of the entire match, by a wide margin, used **no Monte Carlo at all**:

- **Q12 (Belgium 3+ SOT, priced 0.85, missed by 0.85)** — an empirical-Bayes-shrunk Poisson
  threshold model.
- **Q14 (4+ total cards, priced 0.30, missed by 0.70)** — a 3-way weighted blend (team discipline
  + referee rate + corpus baseline).

Between them, these two questions account for 1.55 of the match's 7.44 total miss-distance —
over 20% of the damage from 2 of 15 questions, neither touching the simulation.

---

## 3. Failure cluster #1: regime-coverage was applied one-directionally

This is the real, actionable finding, and it's a repeat of a pattern already documented once in
this project (`JULY3_POSTMORTEM_DEEP_DIVE.md` §4, "underpricing the favorite's own team-SOT
threshold" — same mechanism, opposite direction here).

**Q11 (Spain 5+ SOT) got the opponent-quality check right**: the raw EB-shrunk Poisson output was
0.6249, and the empirical 2026-only rate was even higher (0.7763/0.75). Both were explicitly
shaded down in `PRICING_METHODOLOGY.md` because "Belgium is a materially stronger opponent than 3
of Spain's 4 prior games." Outcome: Spain hit 8 SOT anyway (well above the 5 threshold) — the
shading didn't cost anything, and the reasoning was sound in principle even though Spain cleared
the bar with room to spare.

**Q12 (Belgium 3+ SOT) never got the equivalent check.** The EB-shrunk Poisson output was 0.9116,
built from Belgium's own 5-game 2026 average (6.4 SOT/game) against opponents ranging from
Egypt/Iran/New Zealand/Senegal to a rotated USA side. It was capped at 0.85 purely per RULE6
("never submit near-100%"), which is a mechanical ceiling, not a reasoned opponent-quality
adjustment. Belgium was about to face **by far their most dominant opponent all tournament** —
and the actual game confirmed it: Spain took 67.9% possession and held Belgium to 2 SOT, a
complete collapse relative to their 6.4 average. The same logical check that correctly shaded
Q11 down was never asked of Q12, even though the underlying fact (Spain's dominance) was
identical and already known at pricing time (Spain's group-stage possession numbers were on
file in `matches/Portugal_vs_Spain/`).

**Diagnosis:** the regime-coverage discipline was applied to "our team's own prop, checked against
the opponent" but not systematically to "the opponent's own prop, checked against our team's
strength." Both directions are the same check; only one was run.

**Recommended rule:** when pricing a *combined-team-strength* count prop (SOT, shots, corners) for
either team in a matchup, always compute the regime-coverage adjustment for **both** teams'
threshold questions, not just the side being treated as "our" analytical focus. If one team's
possession/shot-dominance profile this tournament is a clear outlier relative to the opponent's
in-tournament schedule strength, shade the *weaker* team's own-count props down materially, not
just cap them at a mechanical ceiling like RULE6's 0.85-0.95 band. Proposed name:
`SYMMETRIC_REGIME_COVERAGE`.

---

## 4. Failure cluster #2: the cards blend and Smarkets agreed, and both were wrong

Q14 (4+ total cards) was priced at 0.30, matching Smarkets' 0.2976 almost exactly (see
`PRICING_METHODOLOGY.md` §5's cross-check note, made before the match). The actual outcome was
exactly 4 cards (2 Spain, 2 Belgium — all four in the second half, two in stoppage time). This
is a case where independent agreement between our model and the market did not protect against
being wrong — both approaches structurally underweight stoppage-time card accumulation in a
tense, high-stakes knockout match, a pattern this project has already flagged once before in
`KNOCKOUT_STAGE_PRICING_DEEP_DIVE.md` §4.1 for late-window questions generally (that section's
findings were about goal/card timing specifically; this is a related but distinct case — a
match-total count, not a timing question — landing on the same underlying blind spot: matches
that stay close deep into stoppage time generate discipline problems that pre-match team-average
models don't anticipate).

**Recommended rule:** no immediate model change here — n=1 is too thin to redesign the cards
blend from a single match, and the blend's own documented weights already reflect genuine
uncertainty (see the explicit sensitivity table in `03_model_derivations.json`, which showed
P(4+) ranging from 6.6% to 62.8% depending on which input dominated). Flag for future
observation: if match-total card counts keep landing above modeled expectation in tense knockout
games specifically, that's a second instance of the same late-match-chaos blind spot already
identified for timing questions, and would justify a shared fix (shading combined-count
thresholds upward in must-win knockout contexts, not just timing questions).

---

## 5. What worked, for balance

- **Q1 (Spain advances, 0.76)** and **Q11 (Spain 5+ SOT, 0.60)** — both correct, both used the
  corrected Elo/regime-coverage methodology built this session.
- **Q8 (Yamal score/assist, 0.27)** — correct for the 3rd straight match, the most-validated
  single pattern this project has.
- **Q15 (penalty or red, 0.33)** — correct; the referee-specific data (Michael Oliver, 0 reds in
  his 3 prior matches) held up.
- **Q3 and Q5 (Monte Carlo, both correct)** — the simulation approach is not the story of this
  match's losses; see §2.

---

## 6. Bottom line

The user's instinct that "we pivoted and got burned" is right about the outcome (a bad night,
real leaderboard cost) but the evidence points at a different mechanism than the pivot itself.
The Monte Carlo simulation performed exactly as a well-calibrated model should on genuinely
uncertain path-dependent questions — an unremarkable 2/4 split with both misses near 50/50. The
real, fixable gap is `SYMMETRIC_REGIME_COVERAGE` (§3): a real methodological blind spot that cost
0.85 on its own, more than half again the size of the worst Monte Carlo miss. That's the lesson
worth carrying into the next match, not "don't use simulation for path-dependent props."
