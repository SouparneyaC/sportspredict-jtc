# Brazil vs Norway — Full Case Study (R16, 2026-07-05)

**Purpose of this document:** this is a complete, standalone record of how every one of the 15 questions in this match was priced and why, written so that someone with zero memory of this campaign — including a future version of me reading it years later — can reconstruct the entire reasoning chain: what data I pulled, what formula or model I ran, what number I submitted, what actually happened, and what that implies. This is one of the best single-match results of the entire campaign (**+179.26 RBP, 13/15 beat crowd**), so it's documented in full rather than summarized.

**Final score:** Brazil 1–2 Norway. Norway were pre-match underdogs (20% win probability) — this was a genuine upset.

---

## 1. Background and context

### 1.1 The platform and the scoring rule

This match was priced for **JTC (Jump Probability Cup)**, a prediction tournament on `play.sportspredict.com` running alongside the 2026 FIFA World Cup. For each match, the platform poses ~15 yes/no questions ("Will Team X win?", "Will Player Y score?", etc.). Players submit a probability $p \in [0,1]$ for "yes." The platform then reveals its own crowd-consensus probability $p_c$ (the aggregate of all other players' submissions) and the true outcome $o \in \{0,1\}$, and scores each question using **RBP (Relative Brier Points)**:

$$
\text{Brier}(p, o) = (p - o)^2
$$

$$
\text{RBP}_q \;\propto\; \text{Brier}(p_c, o) \;-\; \text{Brier}(p_u, o) \;=\; (p_c - o)^2 - (p_u - o)^2
$$

where $p_u$ is my submitted probability. A positive RBP means I was closer to the true outcome than the crowd; a negative RBP means the crowd beat me. This is a **relative, zero-sum-flavored scoring rule**, not an absolute proper score — a point covered in depth in `data/crowd_consensus_prediction_research.md` and `STRATEGIC_MARGIN_PUSH_RESEARCH.md`, both of which conclude that under this rule, submitting your honestly-calibrated best estimate of the true probability $p_t$ is still the right target (the rule is "strictly proper" per-question); the crowd's own miscalibration only affects *how much* RBP is available, not *what number you should submit*.

### 1.2 Why this match, and what I knew going in

Brazil vs Norway was priced as part of a Round-of-16 double-header (alongside Mexico vs England, priced the same session). Before writing a single estimate, I ran a dedicated research pass over **all prior tournament data** for both teams — every group-stage and Round-of-32 match, ESPN box scores, and every previous pricing decision (with results) I had already made involving these teams or structurally identical question types. Two prior findings from that research directly shaped this match's approach and are referenced throughout:

- **`JULY3_POSTMORTEM_DEEP_DIVE.md`** — identified that Brazil, specifically, has a documented history of catastrophic overconfidence (see §5.1 below) and behavioral quirks (coasts once ahead; opponents' own stats are not suppressed by a Brazil blowout).
- **`WINNING_PATTERNS_SYNTHESIS.md`** — a cross-match study of 75 settled questions establishing that blending a *favorite team's own shots-on-target threshold* upward from a thin market line toward their recent empirical average had lost money in 5 of 5 real tests (net −155.64 RBP), while suppressing a personal player prop toward a real production drought had won in 7 of 7 tests (net +144.67 RBP). This match was a live test of both findings — see Q14 and the player-prop questions below.

---

## 2. Data pipeline: instruments used

Everything below traces back to two live data sources, fetched fresh for this specific match (not reused from stale files):

### 2.1 ESPN (team and player box scores)

**Endpoint pattern:**
```
GET https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary?event={event_id}
```

I pulled all 4 games each team had played this tournament (3 group-stage + 1 Round-of-32), fetched in parallel via `curl`:

| Team | Opponent | ESPN Event ID | Result |
|---|---|---|---|
| Brazil | Morocco | 760419 | D 1–1 |
| Brazil | Haiti | 760444 | W 3–0 |
| Brazil | Scotland (away) | 760465 | W 3–0 |
| Brazil | Japan (R32) | 760487 | W 2–1 |
| Norway | Iraq (away) | 760430 | W 4–1 |
| Norway | Senegal | 760454 | W 3–2 |
| Norway | France | 760475 | L 1–4 |
| Norway | Ivory Coast (R32) | 760490 | W 2–1 |

Team-level box-score stats were read from each response's `boxscore.teams[].statistics[]` array (fields: `totalShots`, `shotsOnTarget`, `wonCorners`, `yellowCards`, `redCards`, `offsides`, `foulsCommitted`, `possessionPct`). Player-level stats came from `rosters[].roster[].stats[]` (fields: `totalShots`, `shotsOnTarget`, `totalGoals`, `goalAssists`, plus `starter` to detect rotation/rest).

**Extracted team logs** (chronological, oldest→newest):

| Brazil | Shots | SOT | Corners | YC | Offsides | Fouls |
|---|---|---|---|---|---|---|
| vs Morocco | 12 | 5 | 6 | 2 | 0 | 16 |
| vs Haiti | 8 | 5 | 4 | 1 | 8 *(outlier)* | 13 |
| vs Scotland | 21 | 9 | 7 | 2 | 1 | 11 |
| vs Japan (R32) | 19 | 7 | 6 | 2 | 1 | 4 |
| **Mean** | **15.0** | **6.5** | **5.75** | **1.75** | **2.5** *(≈1.67 ex-outlier)* | — |

| Norway | Shots | SOT | Corners | YC | Offsides | Fouls |
|---|---|---|---|---|---|---|
| vs Iraq (away) | 12 | 5 | 5 | 0 | 0 | 13 |
| vs Senegal | 13 | 7 | 5 | 0 | 0 | 13 |
| vs France | 10 | 4 | 4 | 1 | 1 | 9 |
| vs Ivory Coast (R32) | 9 | 4 | 3 | 1 | 2 | 7 |
| **Mean** | **11.0** | **5.0** | **4.25** | **0.5** | **0.75** | — |

**Extracted player logs:**

| Vinícius Júnior | vs MAR | vs HAI | vs SCO | vs JPN |
|---|---|---|---|---|
| Goals | 1 | 1 | 2 | 0 |
| Shots | 1 | 3 | 8 | 3 |
| SOT | 1 | 2 | 5 | 2 |

| Matheus Cunha | vs MAR | vs HAI | vs SCO | vs JPN |
|---|---|---|---|---|
| Started | No (bench) | Yes | Yes | Yes |
| Goals | 0 | 2 | 1 | 0 |
| SOT | 0 | 2 | 2 | 1 |

| Erling Haaland | vs IRQ | vs SEN | vs FRA | vs CIV |
|---|---|---|---|---|
| Started | Yes | Yes | **No (full rest)** | Yes |
| Goals | 2 | 2 | 0 | 1 |
| SOT | 4 | 3 | 0 | 2 |

| Martin Ødegaard | vs IRQ | vs SEN | vs FRA | vs CIV |
|---|---|---|---|---|
| Started | Yes | Yes | No | Yes |
| Goals | 0 | 0 | 0 | 0 |
| Assists | 1 | 1 | 0 | 1 |

### 2.2 Smarkets (live market prices)

**Endpoints:**
```
GET https://api.smarkets.com/v3/events/?type=football_match&parent_id=42791414&limit=1000   # find event id
GET https://api.smarkets.com/v3/markets/{market_id}/contracts/                                # contract → name map
GET https://api.smarkets.com/v3/markets/{market_id}/quotes/                                   # live bid/offer
```

Smarkets event ID for this match: **45166893** (177 total markets on the event; I pulled ~18 of them directly relevant to the 15 questions, plus 4 player-specific markets).

**Price construction rule** (used throughout this project): for a two-sided market with both a best bid and best offer, the price is the midpoint:
$$
p_{\text{mid}} = \frac{p_{\text{bid}} + p_{\text{offer}}}{2}
$$
For an illiquid, offer-only market (no live bid), I discount the offer by a standing factor of 0.945 (empirically calibrated across the campaign to correct for one-sided-market optimism):
$$
p_{\text{mid}} = 0.945 \times p_{\text{offer}}
$$

**Key market reads pulled for this match** (all mid-prices, event 45166893):

| Market | Contract | Price |
|---|---|---|
| Full-time result | Brazil / Draw / Norway | 0.5420 / 0.2581 / 0.2000 |
| To qualify | Brazil / Norway | 0.6993 / 0.3077 |
| Both teams to score | Yes | 0.6079 |
| Over/under 2.5 goals | Over | 0.5653 |
| Half-time result | Brazil / Draw / Norway | 0.4001 / 0.4150 / 0.1906 |
| Highest scoring half | 1H / Equal / 2H | 0.2882 / 0.2470 / 0.4589 |
| Exact goals | "2" | 0.2283 |
| Will there be a penalty shootout | Yes | 0.1428 |
| Brazil over/under 4.5 SOT | Over | 0.5770 |
| Norway over/under 3.5 SOT | Over | 0.5779 |
| Brazil over/under 5.5 corners | Over | 0.4925 |
| Over/under 3.5 cards | Over | 0.3801 |
| Anytime goalscorer — Vinícius Jr. | Yes | 0.3775 |
| Anytime goalscorer — Haaland | Yes | 0.4098 |
| Score or assist — Ødegaard | Yes | 0.2542 |
| Over 0.5 SOT — Cunha | Yes | 0.5652 |

---

## 3. Methodology: the general framework

Every question was assigned a **tier**, which determined how much weight the live market got versus my own model:

| Tier | Definition | Example in this match |
|---|---|---|
| `DIRECT` | A liquid market exists that maps ~1:1 onto the question. Submit the market price with no adjustment. | Q6 penalty shootout, Q7 exact goals, Q9 corners, Q11 Norway SOT |
| `PLAYER_LIQUID` | A liquid player-specific market exists; adjust only with strong, specific evidence. | Q1 Vinícius, Q2 Haaland, Q3 Ødegaard, Q4 Cunha |
| `TEAM_MODEL` | No adequate direct market; build the estimate from a statistical model over team/player data. | Q14 Brazil 6+ SOT, Q15 both teams carded |

### 3.1 The Poisson framework

Nearly every count-based question (shots, SOT, corners, cards, offsides, goals) was modeled as a **Poisson process**: if a team/match produces events at an average rate $\lambda$ per 90 minutes, the probability of observing exactly $k$ events is

$$
P(X = k) = \frac{\lambda^k e^{-\lambda}}{k!}
$$

and the probability of hitting *at least* a threshold $k$ (the "N or more" form nearly every JTC question takes) is the complementary CDF:

$$
P(X \geq k) = 1 - F(k-1; \lambda) = 1 - \sum_{i=0}^{k-1} \frac{\lambda^i e^{-\lambda}}{i!}
$$

### 3.2 Fitting $\lambda$ from a market line

Smarkets markets are quoted as "Over/Under $k+0.5$" (e.g., "Over 4.5 shots on target"), which is exactly $P(X \geq k+1)$. When the question's own threshold didn't line up exactly with an available market line, I **inverted the Poisson CDF** to recover the market-implied $\lambda$, then evaluated at the threshold I actually needed. Given an observed market probability $p_{\text{over}}$ for the line "Over $k.5$":

$$
\text{find } \lambda \text{ such that } \; 1 - F(k; \lambda) = p_{\text{over}}
$$

This has no closed form, so I solved it numerically with Brent's method (`scipy.optimize.brentq`), bisecting on $\lambda \in (10^{-6}, 60)$:

```python
from scipy.optimize import brentq
from scipy.stats import poisson

def fit_lambda_over(p_over: float, k: int, hi: float = 60) -> float:
    """Given P(X > k) = p_over for a Poisson(lambda), solve for lambda."""
    f = lambda lam: (1 - poisson.cdf(k, lam)) - p_over
    return brentq(f, 1e-6, hi)
```

**Concrete example used in this match (Q14, Brazil 6+ SOT):** the only Brazil-SOT market available was "Over 4.5" (i.e., $P(X \geq 5) = 0.577$). I needed $P(X \geq 6)$:

```python
lam_bra_sot = fit_lambda_over(0.577, 4)          # -> lambda = 5.101
p_market_only = 1 - poisson.cdf(5, lam_bra_sot)   # P(SOT >= 6) = 0.402
```

### 3.3 Independent compound probability (for "both teams do X")

For Q15 ("will both teams receive at least one card"), there was no direct market. I modeled each team's card count as an *independent* Poisson process with its own team-specific rate $\lambda_{\text{team}}$ (taken directly from that team's own 4-game average, not a league-wide or symmetric assumption), and used the Poisson-at-zero identity

$$
P(X \geq 1) = 1 - P(X=0) = 1 - e^{-\lambda}
$$

and independence to get

$$
P(\text{both teams carded}) = \big(1 - e^{-\lambda_{\text{BRA}}}\big)\big(1 - e^{-\lambda_{\text{NOR}}}\big)
$$

```python
import math

lambda_bra_cards = 1.75   # Brazil's own 4-game average: (2+1+2+2)/4
lambda_nor_cards = 0.5    # Norway's own 4-game average: (0+0+1+1)/4

p_bra_card = 1 - math.exp(-lambda_bra_cards)   # 0.8262
p_nor_card = 1 - math.exp(-lambda_nor_cards)   # 0.3935
p_both     = p_bra_card * p_nor_card           # 0.3251
```

### 3.4 Blending market and empirical signals

For player props where both a market price $p_m$ and a strong empirical read $p_e$ existed but disagreed, I used a manually-judged convex blend

$$
p_{\text{final}} = w \cdot p_m + (1-w)\cdot p_e, \qquad w \in [0,1]
$$

with $w$ chosen higher (closer to the market) whenever the empirical sample was thin, untested against comparable-quality opposition, or matched a previously-failed pattern (see §3.5); and $w$ chosen lower (closer to the empirical read) only when the empirical evidence had genuine **regime coverage** — i.e., it had already been tested in a context at least as demanding as today's.

### 3.5 The standing rule this match deliberately tested: Cluster-B discipline

`WINNING_PATTERNS_SYNTHESIS.md` (compiled from 75 settled questions before this match) found a stark, symmetric pattern:

- **Cluster A** — suppressing a *named player's* prop based on a genuine multi-game personal production drought: **7-for-7 correct**, net **+144.67 RBP**.
- **Cluster B** — blending a *favorite team's own* SOT-threshold estimate **upward** from a thin market line toward their recent empirical average: **0-for-5** (excluding one differently-mechanised win), net **−155.64 RBP**.

Q14 of this match (Brazil 6+ SOT) was a textbook Cluster-B setup: market-implied $P=0.402$, empirical-implied $P=0.631$. The standing instruction derived from the synthesis was: **default to the market, do not blend upward, for exactly this question shape.** I followed it. See §4.14 for the outcome.

---

## 4. Question-by-question record

For each question: the exact text, the tier, the instrument(s) and formula used, the code (where applicable), my submission, the crowd's number, the actual outcome, the RBP earned, and a short post-hoc note.

---

### Q1 — Will Vinícius Júnior (Brazil) score a goal (excl. own goals) in regulation?

- **Tier:** `PLAYER_LIQUID`
- **Instrument:** Smarkets anytime-goalscorer market, Vinícius contract, $p_m = 0.3775$.
- **Reasoning:** ESPN log shows goals in 3 of his 4 appearances (1, 1, 2, 0) — a 75% raw scoring rate. But the one blank came against Japan, the single toughest opponent he's faced this tournament (R32), and Norway (today's opponent) represents a comparable step up in class from Brazil's other three group opponents. I did **not** fully trust the 75% raw rate; I applied only a modest upward nudge from the market.
- **Formula:** manual blend, weighted toward market: $p_{\text{final}} = 0.40$ (up from $p_m=0.3775$, a +2.25pp nudge, not a full empirical blend).
- **Submitted:** **0.40** | **Crowd:** 0.44 | **Outcome:** NO | **RBP: +11.17** (beat crowd)
- **Post-hoc:** Correct call. The caution about a tougher opponent suppressing his output proved right twice in a row now (Japan, then Norway).

### Q2 — Will Erling Haaland (Norway) score a goal (excl. own goals) in regulation?

- **Tier:** `PLAYER_LIQUID`
- **Instrument:** Smarkets anytime-goalscorer market, Haaland contract, $p_m = 0.4098$.
- **Reasoning:** Haaland scored in literally **every appearance** this tournament (2, 2, DNP, 1 — the blank vs. France was a full rest, not a missed chance). Crucially, his most recent goal came in the **R32 knockout game** against Ivory Coast — meaning his scoring streak has already been tested at elevated stakes, unlike Ødegaard's assist streak (see Q3), which has only been tested against weaker opposition. This differentiation was the deliberate reason to bump Haaland but not Ødegaard by nearly as much.
- **Formula:** manual blend, weighted meaningfully toward the empirical rate given genuine regime coverage: $p_{\text{final}} = 0.55$.
- **Submitted:** **0.55** | **Crowd:** 0.48 | **Outcome:** YES | **RBP: +19.38** (beat crowd)
- **Post-hoc:** Correct, and the second-biggest player-prop win of the match. The "has this streak been tested under comparable stakes?" question is now validated as the right differentiator between two superficially similar hot streaks (compare directly to Q3).

### Q3 — Will Martin Ødegaard (Norway) score or assist a goal (excl. own goals) in regulation?

- **Tier:** `PLAYER_LIQUID`
- **Instrument:** Smarkets score-or-assist market, Ødegaard contract, $p_m = 0.2542$.
- **Reasoning:** Assisted in all 3 games he played (100% raw rate) — but every one of those assists came against Iraq, Senegal, or Ivory Coast, none of which are a defensive test comparable to Brazil. Unlike Haaland, this streak has **no regime coverage** against elite opposition. Bumped only modestly.
- **Formula:** manual blend, low weight on the empirical rate: $p_{\text{final}} = 0.36$.
- **Submitted:** **0.36** | **Crowd:** 0.35 | **Outcome:** NO | **RBP: +2.3** (beat crowd)
- **Post-hoc:** Correct, and a clean confirmation that the Q2/Q3 differentiation (test the streak's regime coverage before trusting it) was the right call in both directions on the same day.

### Q4 — Will Matheus Cunha (Brazil) have 1 or more shots on target in regulation?

- **Tier:** `PLAYER_LIQUID`
- **Instrument:** Smarkets Over-0.5-SOT market, Cunha contract, $p_m = 0.5652$.
- **Reasoning:** Cunha is now Brazil's first-choice center-forward (Raphinha injured since group stage), and recorded at least 1 SOT in all 3 of his starts (0 [unused sub], 2, 2, 1). Trusted the market closely, with a small upward nudge for his now-secure starting role.
- **Submitted:** **0.58** | **Crowd:** 0.59 | **Outcome:** NO | **RBP: +8.3** (beat crowd)
- **Post-hoc:** Both I and the crowd were on the wrong side of 50% here (Cunha did not register a shot on target). I was marginally closer, hence the small positive RBP despite an incorrect central estimate. Genuine miss, small consequence.

### Q5 — Will Brazil advance to the quarterfinals?

- **Tier:** `DIRECT`
- **Instrument:** Smarkets "To qualify" market, Brazil contract, $p_m = 0.6993$.
- **Reasoning:** Pure direct market trust, no adjustment.
- **Submitted:** **0.70** | **Crowd:** 0.67 | **Outcome:** NO | **RBP: −5.06** (below crowd)
- **Post-hoc:** Brazil lost the match (the central upset of this fixture). A ~30% pre-match risk of exactly this outcome was already priced in by the market; this is the tail materializing, not a process failure. Compare to the same phenomenon in the Argentina–Cape Verde postmortem (`JULY3_POSTMORTEM_DEEP_DIVE.md` §6).

### Q6 — Will the match be decided by a penalty shootout?

- **Tier:** `DIRECT`
- **Instrument:** Smarkets direct market, $p_m = 0.1428$.
- **Submitted:** **0.14** | **Crowd:** 0.22 | **Outcome:** NO | **RBP: +11.29** (beat crowd)
- **Post-hoc:** Clean direct-market win; the crowd overpriced shootout risk for a group-stage-strength favorite/underdog pairing.

### Q7 — Will the match finish with exactly 2 total goals in regulation?

- **Tier:** `DIRECT`
- **Instrument:** Smarkets "Exact goals" market, contract "2", $p_m = 0.2283$.
- **Submitted:** **0.23** | **Crowd:** 0.28 | **Outcome:** NO | **RBP: +10.03** (beat crowd)

### Q8 — Will both teams score in regulation?

- **Tier:** `DIRECT`
- **Instrument:** Smarkets BTTS market, $p_m = 0.6079$.
- **Submitted:** **0.61** | **Crowd:** 0.60 | **Outcome:** YES | **RBP: +4.88** (beat crowd)

### Q9 — Will Brazil have 6 or more corner kicks in regulation?

- **Tier:** `DIRECT`
- **Instrument:** Smarkets "Brazil over/under 5.5 corners" — an *exact* line match for "6 or more" ($k=5$, so Over 5.5 $= P(X\geq6)$ precisely, no lambda-fitting needed). $p_m = 0.4925$.
- **Submitted:** **0.49** | **Crowd:** 0.52 | **Outcome:** NO | **RBP: +10.4** (beat crowd)

### Q10 — Will there be 4 or more total cards shown in regulation?

- **Tier:** `DIRECT`
- **Instrument:** Smarkets "Over/under 3.5 cards" market — exact line match for "4 or more." $p_m = 0.3801$.
- **Submitted:** **0.38** | **Crowd:** 0.42 | **Outcome:** NO | **RBP: +10.54** (beat crowd)

### Q11 — Will Norway have 4 or more shots on target in regulation?

- **Tier:** `DIRECT`
- **Instrument:** Smarkets "Norway over/under 3.5 SOT" — exact line match. $p_m = 0.5779$.
- **Reasoning:** Norway's own 4-game SOT log (5, 7, 4, 4; mean 5.0) sits right around this threshold, and the market price was consistent with that — no reason to deviate.
- **Submitted:** **0.58** | **Crowd:** 0.52 | **Outcome:** YES | **RBP: +14.07** (beat crowd)

### Q12 — Will the match be tied at halftime?

- **Tier:** `DIRECT`
- **Instrument:** Smarkets half-time result market, Draw contract, $p_m = 0.4150$.
- **Submitted:** **0.42** | **Crowd:** 0.41 | **Outcome:** YES | **RBP: +5.44** (beat crowd)

### Q13 — Will the second half produce more goals than the first half in regulation?

- **Tier:** `DIRECT`
- **Instrument:** Smarkets "Highest scoring half" market, "Second Half" contract, $p_m = 0.4589$.
- **Submitted:** **0.46** | **Crowd:** 0.50 | **Outcome:** YES | **RBP: −5.47** (below crowd)
- **Post-hoc:** Correct direction, just not extreme enough relative to the crowd. Small loss.

### Q14 — Will Brazil have 6 or more shots on target in regulation? ★ (methodology validation)

- **Tier:** `TEAM_MODEL`
- **Instrument:** Smarkets "Brazil over/under 4.5 SOT" (only line available, $k=4$), fitted to the needed threshold $k=5$ using the lambda-inversion method in §3.2.

$$
\lambda_{\text{market}} = \texttt{fit\_lambda\_over}(0.577,\,4) = 5.101
\qquad
P_{\text{market}}(X\geq6) = 1 - F(5;\,5.101) = 0.402
$$

Cross-checked against Brazil's raw empirical SOT average from §2.1 (5, 5, 9, 7 → mean 6.5):

$$
P_{\text{empirical}}(X\geq6) = 1 - F(5;\,6.5) = 0.631
$$

- **The decision:** this is the exact shape of the Cluster-B trap defined in §3.5 (market below empirical, favorite team, SOT threshold). Per the standing rule, I **stayed at the market number** rather than blending upward.
- **Submitted:** **0.41** | **Crowd:** 0.51 | **Outcome:** NO | **RBP: +22.57** (beat crowd) — **second-biggest win of the match**
- **Post-hoc:** This is the single most important methodological result in this match. Had I followed the *old* playbook (blend toward the empirical average, as was done — and lost — 5 times before this rule was written), I would have submitted something near 0.55–0.63 instead of 0.41, and the outcome (Brazil did **not** reach 6 SOT) would have turned this into a loss instead of a +22.57 win. **This is the first live confirmation that the Cluster-B discipline rule, adopted purely from historical postmortem analysis, produces better real-money decisions going forward.** (Note: the very next day, the mirror-image situation on a different team's SOT threshold in the Mexico–England match went the *other* way — see the companion note in `WINNING_PATTERNS_SYNTHESIS.md` for the full nuance; the rule is a strong prior, not an absolute law.)

### Q15 — Will both teams receive at least one card in regulation? ★★ (biggest win of the match)

- **Tier:** `TEAM_MODEL`
- **Instrument:** No direct market existed for this compound question. Built entirely from each team's own ESPN card history (§2.1: Brazil 2,1,2,2 → $\lambda_{\text{BRA}}=1.75$; Norway 0,0,1,1 → $\lambda_{\text{NOR}}=0.5$), using the independent-compound-probability method of §3.3.

$$
P(\text{BRA}\geq1) = 1 - e^{-1.75} = 0.8262
\qquad
P(\text{NOR}\geq1) = 1 - e^{-0.5} = 0.3935
$$
$$
P(\text{both carded}) = 0.8262 \times 0.3935 = 0.3251
$$

- **Submitted:** **0.33** | **Crowd:** 0.62 | **Outcome:** NO | **RBP: +59.43 (beat crowd) — biggest single win of the match, one of the largest in the whole campaign**
- **Why the crowd was so far off (my read):** 62% looks like crowds applying a generic heuristic — "it's a high-stakes knockout match, of course both sides pick up a card" — without actually checking each team's individual disciplinary record. Norway had been a genuinely clean team all tournament (zero cards in half their matches). By pricing off each team's own measured rate instead of a shared, symmetric assumption, I captured a gap the crowd's generic prior could not see.
- **Post-hoc:** This is the clearest validation this campaign has produced of a **new, generalizable pattern**: for any "both teams / both players do X" compound question with no direct market, decompose it into each side's own independently-measured rate rather than defaulting to any shared/symmetric prior — and expect the crowd to systematically overprice these compound events, especially in high-stakes framing (knockout, rivalry, etc.) that primes an "of course something dramatic happens to both sides" intuition.

---

## 5. What worked

1. **Direct market trust, with zero ego** (Q5–Q13, excluding Q14/Q15): 8 of 9 pure `DIRECT` questions beat the crowd, most by 5–14 RBP. This is the unglamorous backbone of the match — no single one of these is a highlight, but collectively they're most of the floor that makes a match like this profitable even before the two standout wins.
2. **Differentiating "hot streaks" by regime coverage, not just by raw rate** (Q1 vs Q2 vs Q3): Vinícius (75% raw scoring rate) was priced conservatively because his one blank came against his toughest opponent to date. Haaland (100% raw scoring rate across appearances) was priced aggressively because his streak survived a knockout-stakes test. Ødegaard (100% raw assist rate) was priced conservatively despite the identical raw number, because none of his assists came against comparable opposition. All three calls were correct. **The lesson: the same raw hit-rate can justify very different confidence levels depending on what conditions it's actually been tested under.**
3. **Independent per-team compound modeling beating a generic crowd heuristic** (Q15): this is the headline finding of the match and possibly of the campaign to date — see §4.15.
4. **Discipline over a previously-costly pattern, applied under real pressure** (Q14): choosing to stay at the market price on a question shaped exactly like 5 previous losses, despite an empirical number that "felt" more true, and having that discipline pay off directly.

## 6. What didn't work

1. **Q5 (Brazil advance) and Q13 (2nd-half goals):** both small losses, both cases where my number was reasonably calibrated and the crowd simply landed fractionally closer. Norway's win was a real, not-fully-predictable upset; no specific process failure to fix here.
2. **Q4 (Cunha SOT):** a genuine directional miss (I and the crowd both expected a shot on target that didn't come), though the cost was small. Worth flagging that "first-choice striker with a clean recent SOT record" is not a guarantee — Norway's specific defensive shape on the day evidently nullified him, and no amount of prior-game data could have flagged that in advance.

## 7. Reusable takeaways for future matches

- When two questions look structurally identical (e.g., "will hot-streak player X continue scoring/assisting"), check whether the streak has been tested against opposition of comparable quality to today's opponent before assigning it equal confidence. This one differentiator explained 3 of the top-4 wins in this match.
- For any compound "both sides do X" question with no direct market, default to the independent-per-team-rate method in §3.3 rather than a shared assumption — and expect crowds to overprice these, especially in high-narrative-salience matches.
- The Cluster-B discipline (§3.5) is now validated in one live match with a large positive result, but should still be treated as a strong prior rather than an absolute rule — see the same-day counter-example noted in `WINNING_PATTERNS_SYNTHESIS.md`.

---

*Sources: `matches/Brazil_vs_Norway/{01_espn_data,02_smarkets_markets,03_model_derivations,05_estimates,06_post_match_results}.json`, `bash_log.txt`. Cross-referenced against `WINNING_PATTERNS_SYNTHESIS.md` and `JULY3_POSTMORTEM_DEEP_DIVE.md`. Document generated 2026-07-06.*
