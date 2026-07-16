# De-shrinkage pressure test — the remaining ten questions (Q1, Q2, Q4, Q5, Q6, Q7, Q8, Q10, Q11, Q15)

England vs Argentina SF, 2026-07-15. Companion to `19_deshrinkage_pressure_test.md`, which covered
the four far-from-crowd DIRECT questions (Q12, Q13, Q14, Q3) plus Q9. This piece extends the same
**bias check — not a re-model** — to the other ten, answering the same two questions for each: (1)
are we shrinking our honest estimate toward 0.5, and (2) if so, is that shrinkage *necessary*
(protective of a noisy signal) or is it leaking free EV off a reliable one?

The answer differs by question type, and the reason it differs is the crux of the whole exercise, so
it is stated up front:

- **Market-anchored questions** (DIRECT mid, or DERIVED from market lines): the exchange price is a
  sharp, un-compressed signal. Shrinking it toward 0.5 is *never* necessary and only leaks EV. The
  check is "are we submitting the mid, and is the book clean."
- **No-market base-rate questions** (BASE): the base rate's reliability is whatever its backtest
  earned. Shrinkage toward 0.5 is *protective and correct* for a noisy/unvalidated base rate, and
  *unnecessary* (EV-leaking) for one that backtested a real edge. The check is "did this base rate
  earn the right to sit where it is."

Join safety: market legs joined on `10_smarkets_quotes_processed.json` labels, never on Q-number.

## 1. The premium map across all 15 (the whole story in one table)

Crowd position from the n=772 model `p_c = 0.5042 + 0.6087·(p_s − 0.5)`; premium = `S·(p_c − p_s)²`
banked by submitting the honest number, `S = 90`. `[done]` = covered in `19_...md`.

| Question | Submit | \|0.5 − sub\| | Crowd (modelled) | Premium | Type / book |
|---|---|---|---|---|---|
| Q12 10+ combined corners | 0.25 | 0.250 | 0.352 | +0.94 | DIRECT `[done]` |
| Q13 England lead HT | 0.27 | 0.230 | 0.364 | +0.80 | DIRECT `[done]` |
| Q3 Penalty awarded | 0.29 | 0.210 | 0.376 | +0.67 | DIRECT `[done]` |
| Q14 Argentina 2+ goals | 0.30 | 0.200 | 0.382 | +0.61 | DIRECT `[done]` |
| **Q15 Bellingham score/assist** | 0.30 | 0.200 | 0.382 | **+0.61** | **DIRECT** |
| **Q7 Stoppage-time goal** | 0.31 | 0.190 | 0.389 | **+0.56** | **BASE (no market)** |
| **Q10 Card before first goal** | 0.35 | 0.150 | 0.413 | **+0.36** | **BASE (no market)** |
| **Q11 Kane scores** | 0.36 | 0.140 | 0.419 | **+0.31** | **DIRECT** |
| Q9 Argentina more corners | 0.44 | 0.060 | 0.468 | +0.07 | DERIVED `[done]` |
| **Q1 Álvarez 1+ SOT** | 0.58 | 0.080 | 0.553 | **+0.07** | **PROP, 1-sided book** |
| **Q6 8+ combined SOT** | 0.45 | 0.050 | 0.474 | **+0.05** | **DERIVED** |
| **Q2 England advance** | 0.55 | 0.050 | 0.535 | **+0.02** | **DIRECT** |
| **Q8 Both teams carded** | 0.55 | 0.050 | 0.535 | **+0.02** | **BASE (no market)** |
| **Q5 Goal in each half** | 0.52 | 0.020 | 0.516 | **+0.00** | **BASE (no market)** |
| **Q4 Messi scores** | 0.50 | 0.000 | 0.504 | **+0.00** | **PROP, 1-sided book** |

**Premium by distance-from-0.5 bucket:**

| Bucket | Questions | Total premium |
|---|---|---|
| Far (>0.18 from 0.5) | Q3, Q7, Q12, Q13, Q14, Q15 | **+4.19** |
| Mid (0.10–0.18) | Q10, Q11 | +0.67 |
| Near 0.5 (<0.10) | Q1, Q2, Q4, Q5, Q6, Q8, Q9 | +0.23 |

82% of all available premium sits in the far bucket. Of the ten questions in this document, only
four carry premium worth any scrutiny at all (Q15, Q7, Q11, Q10); the other six are near-0.5 and
essentially moot.

## 2. The two remaining DIRECT-market questions — Q15 and Q11

Both are single-player binary contracts (one player's "yes" traded against its own "no"), so the
bid/offer mid is already the fair probability — there is no multi-way overround to strip, unlike a
2-way O/U book. The check is book quality + confirming we submit the mid.

**Q15 — Bellingham score or assist (0.30).** `Score_or_assist` / Bellingham: bid 0.2703, offer
0.3333, mid 0.3018. Two-sided (real bid AND offer). Spread 6.30pp — the second-widest book on the
slate (already flagged in `16_...md`), so the mid carries real uncertainty, but there is no
detectable directional skew from top-of-book. We submit 0.30 = the mid rounded. **Not shrunk.** This
is a genuine far-from-crowd question (0.30, same distance as Q14) collecting +0.61 RBP of premium,
and it is being collected in full. No change.

**Q11 — Kane scores (0.36).** `Anytime_goalscorer` / Kane: bid 0.3571, offer 0.3623, mid 0.3597 —
a 0.52pp spread, the tightest, sharpest book of the entire slate. We submit 0.36 = the mid. **Not
shrunk.** Collecting +0.31 RBP. The Mexico–England R16 precedent (a near-identical Kane mid nudged
*up* to 0.38, lost to a higher crowd) is exactly why we sit *at* the mid and don't manufacture an
upward view — the Mbappé/RULE17 lesson. No change.

Both confirm the round-1 pattern: DIRECT market mid = the un-shrunk honest number, premium collected
in full.

## 3. The base-rate questions — where "is shrinkage necessary?" is genuinely live

These four (Q7, Q10, Q8, Q5) have no market to de-vig against. Whether to shrink them toward 0.5
depends entirely on how much predictive edge each base rate actually earned in its walk-forward
backtest (`13_...md`, `18_...md`).

**Q7 — stoppage-time goal (0.31). Not shrunk; shrinkage NOT necessary — the signal earned its
extremity.** The base rate moved from 0.360 (WC2026-only) to 0.31 once the Euro2024 + CopaAmerica2024
+ AFCON2023 corpus was pooled in — i.e. more data pushed it *further* from 0.5, not toward it. The
walk-forward edge is real and *independently replicated*: +0.012 Brier over naive-0.5 on WC2026,
+0.047 on the fresh StatsBomb corpus. A signal that beats a coin flip out-of-sample in two separate
corpora has earned the right to sit at its honest base rate; shrinking it toward 0.5 would hand back
the +0.56 RBP of premium it legitimately holds. Hold at 0.31.

**Q10 — card before first goal (0.35). Not shrunk; the one place a small protective shrink would be
defensible — but held, and flagged as lowest-confidence.** This is the softest premium-bearing signal
on the board: its walk-forward edge *shrinks* under pooling (+0.0164 WC2026 → +0.0075 pooled), and it
inherits the documented ESPN/StatsBomb card-measurement gap (0.671× ratio) that contaminates any
cross-source card signal. So unlike Q7, the reliability here is genuinely marginal. Two things keep it
at 0.35 rather than shrunk toward 0.5: it still backtested *positive* (just weakly), and at 0.15 from
0.5 it is not an aggressive number to begin with. The honest disposition: hold at 0.35, but this is
the single number among the premium-bearing group most exposed to being wrong, and if any far-from-0.5
question is going to underperform its premium estimate, this is the likeliest one. Not over-shrunk;
not worth adding shrinkage; watch it.

**Q8 — both teams carded (0.55). Noisy signal, but near 0.5 so the question is moot.** Cards failed a
hierarchical model *twice* — this is the noisiest family in the project, exactly the kind of signal
where protective shrinkage toward 0.5 would normally be correct. But Q8's honest base rate (0.55)
already sits within 0.05 of 0.5, so it is collecting only +0.02 RBP and there is nothing to protect or
leak. The "shrink noisy signals" rule and the "collect far-from-0.5 premium" rule both become
irrelevant this close to a coin flip. Hold at 0.55 (equivalently, market/crowd-anchored per the
standing cards doctrine — same number).

**Q5 — goal in each half (0.52). No edge, and at 0.5 anyway — doubly moot.** The backtest found no
real edge over 50/50 even on the expanded corpus, and the number is 0.02 from 0.5. There is no signal
to shrink and no premium to leak. Hold at 0.52.

## 4. The near-0.5 remainder — Q1, Q2, Q6 (and Q4, Q9 already dispositioned)

These carry trivial premium (≤+0.07 each) so any shrinkage question is low-stakes by construction,
but for completeness:

- **Q1 — Álvarez 1+ SOT (0.58).** The one genuine (if tiny) de-shrink observation in this document:
  the honest n-weighted estimate from the deep dive (`15_...md`) was **0.590**, and we submitted
  0.58 — a 1pp round *toward* 0.5. Restoring 0.59 recovers ≈ +0.02 RBP. Real, directionally correct,
  and immaterial. Worth noting only because it is the sole place a number was rounded to the
  compressed side; if maximal honesty is wanted, 0.59 is the un-shrunk value. The market is one-sided
  (offer-only 0.5682), so there is no clean mid to check against — the 0.59 comes from our own
  large-n pooled estimate, not the thin book.
- **Q2 — England advance (0.55).** DIRECT `To_qualify` mid 0.545, submitted 0.55 — rounded very
  slightly *away* from 0.5, the opposite of shrinkage. RULE14-consistent (checked in `16_...md`).
  Fine.
- **Q6 — 8+ combined SOT (0.45).** Like Q9, this is a signal-*reconciliation* case, not a shrinkage
  case: the market-derived number (0.454) and the empirical corpus (0.55) straddle 0.5 and disagree,
  and we chose the market signal per RULE17. Whichever is right, the number is 0.05 from 0.5, so the
  premium is +0.05 either way. Not a de-shrink question. Hold at 0.45.
- **Q4 (0.50) / Q9 (0.44)** — dispositioned already (`19_...md` for Q9; Q4 is a coin flip with zero
  premium by construction — the whole point of the earlier RULE17/rank discussion).

## 5. Verdict across all 15

**No question is over-shrunk in a way that costs meaningful EV, and — equally important — no question
is dangerously *under*-shrunk (sitting far from 0.5 on a weak, unvalidated signal).** That second
finding is the one worth emphasising: every far-from-0.5 number on the slate is backed by either a
sharp two-sided market (Q3, Q12, Q13, Q14, Q15) or a walk-forward-validated base rate (Q7). The only
soft spot, Q10, sits at a moderate 0.35 and still backtested positive. The book is internally
coherent — extremity is always earned, and the noisy signals (cards Q8, goal-in-each-half Q5) all
happen to live near 0.5 where their noise is harmless.

Concretely:

| Disposition | Questions | Action |
|---|---|---|
| DIRECT market, un-shrunk, premium collected in full | Q3, Q11, Q12, Q13, Q14, Q15 | none |
| BASE, validated edge, correctly un-shrunk | Q7 | none |
| BASE, marginal edge, held but flagged lowest-confidence | Q10 | none (watch) |
| Near-0.5, premium negligible, shrinkage moot | Q2, Q4, Q5, Q6, Q8, Q9 | none |
| Near-0.5, rounded 1pp to compressed side | Q1 (0.58 → could be 0.59) | optional, ≈+0.02 RBP |

**Total EV on the table from all possible de-shrink adjustments across the entire slate: ≈ +0.02
RBP** (the Q1 rounding). Everything else is already collecting its full premium. This confirms, more
completely than round 1 could on its own, that the pipeline is submitting honest un-shrunk numbers
wherever it matters — the safe points are banked, and there is no free EV being left behind.

## 6. Caveats (unchanged from `19_...md`)

Crowd positions are modelled (n=772 population fit), not this match's live crowd; `S ≈ 90` is a
central scale estimate. Premium magnitudes are expected values under the validated average
relationship, robust in *direction* (crowd compressed toward 0.5, us correctly more extreme where it
counts) but not precise to the second decimal. This was a bias check only — it does not test whether
a market or base rate is itself mispriced, only whether we have distorted it toward 0.5.

## 7. Files

Computation inline this session; inputs from `10_smarkets_quotes_processed.json` and the base-rate
verdicts in `13_...md` / `18_...md`. No pricing numbers changed. One optional micro-adjustment noted
(Q1 0.58 → 0.59, ≈ +0.02 RBP) — flagged, not applied, pending your call.
