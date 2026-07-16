# De-shrinkage pressure test — the four far-from-crowd questions (Q13, Q12, Q14, Q3) + Q9

England vs Argentina SF, 2026-07-15. A **bias check, not a re-model.** The goal is narrow and
specific: confirm that on the questions where the most RBP is available — the ones where our honest
number sits far from 0.5 — we are submitting our genuine best estimate of the truth, and not a
number quietly dragged toward 0.5 by a shrinkage rule or distorted by a thin/one-sided book. This
is the one lever that raises expected points with **zero added variance** (it never widens the
downside the way a Messi-style push would), which is why it's the right move for a rank-43 position
where the tournament math says don't gamble.

Join safety: all market legs joined on `10_smarkets_quotes_processed.json`'s explicit market labels,
never on question position/Q-number, per standing project rule.

## 1. Why these four, and why this is safe points rather than a gamble

Per-question RBP is `S·[(p_c − o)² − (p_s − o)²]`; in expectation, submitting our true belief
`p_s = p_t` earns `S·(p_c − p_t)²`, where `p_c` is where the crowd sits. The crowd is compressed
toward 0.5 (validated model, n=772: `p_c ≈ 0.5042 + 0.6087·(p_t − 0.5)`), so that premium is the
*squared* gap between the compressed crowd and the un-compressed truth — and it **grows the further
the truth is from 0.5.** The points are therefore concentrated on far-from-crowd questions. Our four
lowest submissions (all DIRECT-market) are those questions: Q12 (0.25), Q13 (0.27), Q3 (0.29),
Q14 (0.30). Over-shrinking any of them — nudging it back toward 0.5 — costs `S·δ²` in expected RBP,
the mirror image of the over-*pushing* mistake, except correcting it adds no variance because we're
only moving *back to* our honest number, never past it.

DIRECT-market questions are the right place to run this because the exchange mid is a sharp,
money-weighted probability estimate (unlike the JTC forecaster crowd, it is *not* itself compressed),
so "our honest `p_t`" has a clean external referent to check against: the de-vigged market mid.

## 2. Book-quality read (raw top-of-book, `10_smarkets_quotes_processed.json`)

| Question | Market leg | Bid | Offer | Mid | Two-sided? | Spread |
|---|---|---|---|---|---|---|
| Q12 10+ combined corners | `OU9.5_corners` / Over | 0.2041 | 0.2941 | 0.2491 | Yes | 9.00pp |
| Q13 England lead at HT | `Half_time_result` / England | 0.2703 | 0.2778 | 0.2741 | Yes | 0.75pp |
| Q3 Penalty awarded | `Penalty_to_be_awarded` / Yes | 0.2667 | 0.3175 | 0.2921 | Yes | 5.08pp |
| Q14 Argentina 2+ goals | `Argentina_OU1.5_goals` / Over | 0.2941 | 0.3030 | 0.2985 | Yes | 0.89pp |

**Every book is genuinely two-sided** — a real bid *and* a real offer on both outcomes. None are the
one-sided/offer-only situation that made the Messi and Álvarez player-prop markets untrustworthy
(where a single quote is a biased estimate of true probability). So the mid is a legitimate
probability read on all four. The one caveat is Q12's 9.00pp spread — the widest book on the slate;
the mid remains the best point estimate but carries genuine uncertainty, so it should be read as
"~0.25 ± a bit," not a precise number. Q13 and Q14 are tight (<1pp); Q3 is intermediate (5pp).

**Overround / skew check** (do complementary outcomes sum to ~1?): Q13 3-way = 0.995, Q12 = 0.998,
Q14 = 1.0053, Q3 = 1.0118. All within ~1.2% of fair — consistent with a low-vig exchange, no book
badly skewed. Q3's 1.2% is the largest, consistent with its wider spread (thinner book), but still
small.

## 3. De-vig + compression-premium quantification

De-vigged fair probability = raw mid normalized by the complementary-outcome sum. Crowd position
from the n=772 model. Premium = expected RBP banked by submitting the honest number (`S = 90`, the
central estimate from `STRATEGIC_MARGIN_PUSH_RESEARCH.md`'s 78–100 range). "Lose @5pp" = expected
RBP given back if we over-shrank 5 points toward 0.5.

| Question | Submit | De-vigged fair | Crowd (modelled) | Gap (crowd − submit) | Premium banked | Cost if shrunk 5pp |
|---|---|---|---|---|---|---|
| Q12 10+ combined corners | 0.25 | 0.2496 | 0.352 | +0.102 | **+0.94** | −0.23 |
| Q13 England lead at HT | 0.27 | 0.2754 | 0.364 | +0.094 | **+0.80** | −0.23 |
| Q3 Penalty awarded | 0.29 | 0.2887 | 0.376 | +0.086 | **+0.67** | −0.23 |
| Q14 Argentina 2+ goals | 0.30 | 0.2970 | 0.382 | +0.082 | **+0.61** | −0.23 |
| | | | | **Total** | **+3.02** | |

Three things this table establishes:

1. **Every submission sits correctly below the crowd** (gap positive, +8 to +10pp). We are on the
   right side of the compression on all four — collecting the premium, not fighting it.
2. **The de-vigged fair value is within ~0.5pp of our submission on every question** — Q12 identical,
   Q13/Q3/Q14 off by 0.1–0.5pp. Crucially the direction is *symmetric noise*, not a systematic drift:
   Q13 rounded a hair to the aggressive side (submit 0.27 vs fair 0.2754), Q3 and Q14 a hair to the
   conservative side (submit 0.29/0.30 vs fair 0.2887/0.2970). That is exactly what "no shrinkage bias"
   looks like — if we were systematically over-shrinking, every fair value would sit *further* from
   0.5 than our submission, and it doesn't. **No de-vig adjustment changes a single two-decimal
   submission.**
3. **The premium is concentrated at the extreme.** Q12 (farthest from 0.5) banks +0.94; Q14 (closest
   to 0.5) banks +0.61 — a 54% swing driven purely by distance from 0.5. This is the thesis, made
   quantitative.

## 4. Q9 — examined, and correctly out of scope

Q9 (Argentina more corners than England, submitted 0.44) was flagged as the one place we might have
over-shrunk a reliable signal. On inspection it is **not a shrinkage at all.** Our 0.44 is *more*
extreme than the validated Skellam model's own 0.48 (both below 0.5; 0.44 is further from 0.5) — it
was pulled *toward the market's* 0.34, not toward 0.5. The de-shrink lever therefore finds no free
EV here: the only remaining lever is a directional judgment about whether to trust the point-in-time
Elo edge (which drives the model's 0.48) or the live match markets (which imply ~0.34), and that is a
modelling call, not a bias correction. 0.44 stands as an honest, deliberately-reasoned blend
reflecting genuine model risk, documented in `17_combined_sot_and_corners_comparison_final.md`. No
change.

## 5. Verdict

**Nothing is over-shrunk. All four far-from-crowd questions are already submitted at the honest,
un-shrunk number, and are collecting the full +3.02 RBP of compression premium available to them.**
The de-vig refinement is real but immaterial (sub-0.5pp everywhere, rounds away). This is the "mostly
already optimal" outcome that was predicted going in — the value delivered is:

- **Confirmation** we are leaving no safe points on the table on the questions that matter most.
- A **ruled-out risk**: we verified we are not quietly handing back ~0.9 RBP (the 4×0.23 that 5pp of
  over-shrinkage would have cost) — a real, if small, downside that this check closes off.
- A **reusable rule for the final** (and any remaining matches): expected RBP per question scales with
  the *square* of your honest number's distance from 0.5. Put research effort into getting the
  far-from-0.5, high-conviction questions exactly right (that's where +0.6 to +1.0 RBP each lives),
  and spend near-zero effort agonizing over coin-flip questions like Q4 Messi — there is almost no
  premium available near 0.5 no matter what you submit, which is the same reason pushing them is pure
  risk for no reward.

## 6. Honest caveats

- The crowd position is *modelled* (n=772 population fit), not this match's live crowd — the actual
  JTC crowd on tonight's questions could sit somewhat off the modelled `p_c`. The premium figures are
  therefore expected values under the validated average relationship, not guarantees. The *direction*
  (crowd compressed toward 0.5, us correctly more extreme) is robust; the exact per-question RBP is an
  estimate.
- `S ≈ 90` is a central estimate of the RBP scale; the true per-question constant varies. Premium
  magnitudes scale linearly with `S`, so read them as "small and positive, concentrated at the
  extreme," not to the second decimal.
- This test deliberately did **not** re-model any question. It checked book quality, de-vig, and
  shrinkage direction only. If a market itself is mispriced (a separate question from whether we've
  shrunk it), that is not something a bias check can catch — but the knockout-stage calibration audit
  in `16_direct_market_questions_final_pricing.md` §4 already found no systematic knockout-stage
  mispricing in these families, which is the relevant reassurance.

## 7. Files

- Computation inline in this session (book-quality read + de-vig + premium calc); inputs from
  `10_smarkets_quotes_processed.json`. No pricing numbers changed — all four submissions confirmed at
  their existing values (Q12 0.25, Q13 0.27, Q3 0.29, Q14 0.30), Q9 unchanged at 0.44.
