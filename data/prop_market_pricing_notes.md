# Pricing Methodology Notes — "Uncovered" Prop Categories (2026 World Cup)

For each category not covered by the Elo + Dixon-Coles/bivariate-Poisson
scoreline model (per `data/processed/betting_markets_overview.md`), this note
proposes a concrete model, covariates, how to lean on the existing Elo/Poisson
backbone, and an honest feasibility/confidence rating.

Scoring-rule background (Brier/RPS, calibration vs resolution, maximin
(1/3,1/3,1/3)-style defaults) is in `research_notes.md` §5-8 and applies
identically here — for any category where we end up near a coin flip, the
maximin lesson (§8.5) is: **price near 50% rather than forcing a confident
guess**, since under Brier scoring an unwarranted confident wrong guess is
costly and a calibrated 50% costs little.

Data sources referenced below are cataloged in `alt_data_sources.md`.

---

## General framework: "Elo/xG as backbone, event-rate model as the engine"

The Elo-based Poisson model already gives us, per match, per team:
- `λ_home`, `λ_away` — expected goals (Poisson means)
- Implied match "competitiveness" (`r̄ = (Elo_home+Elo_away)/2`, per Foulley
  §7.4) and "dominance" (`Δr = Elo_home - Elo_away`)

The recurring idea across nearly all uncovered categories: **most match events
(fouls, cards, corners, shots, offsides) correlate with possession/territorial
dominance, which itself correlates with the Elo gap and with the
expected-goal-difference**. So the general recipe is:

1. Build a small **team-match panel** from FBref/StatsBomb (per
   `alt_data_sources.md`) with columns: team, opponent, date, Elo_diff at
   match time, λ_for/λ_against (from refitting the Poisson model
   retrospectively on that match), and the observed event count (fouls,
   corners, shots, etc.) for that team in that match.
2. Fit a **count regression** (Poisson or Negative Binomial, depending on
   overdispersion) of the event count on `Elo_diff` (and possibly `r̄`,
   home/neutral indicator, confederation).
3. For 2026 matches, plug each team's Elo_diff into the fitted model to get
   `μ_team_event`, then:
   - For "team total >= N" markets: `1 - PoissonCDF(N-1; μ)` (or NB CDF).
   - For "team A more than team B" markets: model the **difference** of two
     count distributions via the **Skellam distribution** (difference of two
     Poissons) — `P(X_A > X_B)` has closed form / easy numeric sum under
     Skellam; if NB is needed (overdispersion), no closed form but easy via
     numerical convolution (sum over a grid of (x_A, x_B) pairs).

This reuses 100% of the Elo/Poisson infrastructure already built — the new
work per category is (a) get the historical event-count panel, (b) fit one
small regression, (c) add the Skellam/CDF post-processing.

---

## 1. Fouls (57 markets — mostly "Team A more fouls than Team B")

- **Model**: Poisson or Negative-Binomial regression of fouls-committed on
  Elo_diff (+ home/neutral). Then Skellam (or NB-difference via convolution)
  for "more fouls than opponent."
- **Covariates & Elo-backbone use**: The standard finding in football
  analytics is that the **weaker/lower-possession team commits more fouls**
  (less time on the ball -> more tactical/defensive fouling, more chasing the
  game). So expect the regression coefficient on "own Elo minus opponent Elo"
  to be **negative** for fouls-committed (stronger team fouls less). This
  proxy (Elo gap -> possession share -> foul rate) is **reasonably
  well-supported** in club-football analytics literature (foul rates correlate
  with out-of-possession time), though the exact magnitude for *international*
  football needs estimation from the FBref/StatsBomb panel — international
  matches have less time together as a unit, different referee pools per
  confederation, and tournament-stage matches (more cautious, less foul-prone
  early, more foul-prone if a team is chasing the game late) which adds
  variance.
- **Confederation/referee effects**: Foul-rate baselines likely vary
  meaningfully by confederation (refereeing styles differ — CONMEBOL and CAF
  matches anecdotally run hotter than UEFA in some competitions). If the panel
  is large enough, add a confederation fixed effect; otherwise pool and accept
  some bias.
- **Confidence/feasibility**: **Moderate-good**. The Elo->possession->fouls
  proxy is directionally sound and the effect size in club football is
  non-trivial (weaker teams often commit 2-4 more fouls/match than stronger
  ones in mismatches). For "Team A more fouls than Team B" in a close match
  (similar Elo), this collapses toward 50/50 — which is *correct*, not a
  failure. Biggest risk: if the FBref international panel is too small to
  estimate the Elo-coefficient precisely, fall back to the simple historical
  base rate (the team rated as fouling more often historically, regardless of
  opponent) plus a small Elo-direction nudge.

---

## 2. Cards (yellow/red) (67 markets — "Team A more cards than Team B", card totals)

- **Model**: Cards are a **downstream consequence of fouls** (not all fouls
  are carded, but more fouls -> more cards, roughly proportionally) plus a
  "losing team gets more frustrated/cards late" effect. Two reasonable
  approaches:
  1. **Two-stage**: model fouls (as in §1), then model
     P(card | foul) ~ Beta/historical-rate, multiply through. Adds noise at
     each stage.
  2. **Direct**: Poisson/NB regression of cards-per-match directly on
     Elo_diff + a "match competitiveness/stakes" proxy (e.g., |Elo_diff| —
     close matches and matches where a team is losing late tend to escalate).
     Simpler and likely as good given small samples — **prefer this**.
- **Covariates & Elo backbone**: Same direction as fouls (weaker/defending
  team -> more cards), PLUS a **non-monotonic "stakes" effect**: very
  mismatched games (huge Elo gap) may have *fewer* cards (game is "over"
  early, no need to foul tactically) while close, must-win games (small
  |Elo_diff|, especially in must-win final group games) may have *more*.
  Recommend including both `Elo_diff` (direction: who fouls more) and
  `|Elo_diff|` (magnitude: overall match intensity) as covariates.
- **Red cards specifically**: rare events (~0.1-0.3 reds/match typically) —
  best modeled with a **simple historical base rate** (P(at least one red card
  in a WC group match) ~ 5-10% historically, **needs verification** from the
  FBref panel) rather than a regression with too few positive cases to fit
  reliably. Use base rate +/- small adjustment for `|Elo_diff|` (more lopsided
  = slightly more frustration cards on the losing side, weakly supported).
- **Confidence/feasibility**: **Moderate** for yellow-card totals/comparisons
  (same logic as fouls, one step removed, more noise). **Low-moderate** for
  red-card-specific or "X or more cards" markets with high N — these become
  base-rate-dominated; don't expect much edge over a well-estimated historical
  base rate.

---

## 3. Corners (29 markets — "Team A more corners than Team B")

- **Model**: Poisson/NB regression of corners-won on Elo_diff (+ home/neutral),
  then Skellam for the comparison.
- **Covariates & Elo backbone**: This is probably the **strongest** Elo-proxy
  relationship of all the uncovered categories: **corners are a direct
  byproduct of attacking pressure and territorial dominance** — the team
  that's attacking more (higher possession in the final third, more
  crosses/shots blocked) wins more corners. This should correlate strongly
  with our **expected-goals (λ) from the Poisson model directly** — i.e.,
  rather than (or in addition to) Elo_diff, use `λ_team` (the team's own
  expected goals from the scoreline model) as a covariate for corners-won.
  Teams with higher λ (more expected attacking output) should have
  systematically more corners. This is **well-supported** — corners-per-shot
  and corners-per-possession-share are well-documented stable team-level
  ratios in club analytics (e.g., "set piece" analytics communities at
  StatsBomb/Opta).
- **Confidence/feasibility**: **Good** — likely the most reliable of the
  count-comparison props, *given* we can fit the Elo/λ -> corners regression
  on a reasonable international sample (StatsBomb 2022 WC event data, per
  `alt_data_sources.md` (a)#2, gives exact corner counts per team per match —
  use this as the primary fitting set, since corners are simple to extract
  from event data: `type=='Pass'` with `pass_type=='Corner'` or similar
  StatsBomb event-type field — **needs verification** of exact StatsBomb field
  names but corners are a standard event type).

---

## 4. Offsides (61 markets — "Team A caught offside N or more times")

- **Model**: Poisson/NB for offside-count, then `1 - CDF(N-1; μ)` for "N or
  more" markets (most of these 61 are single-team threshold markets, not
  comparisons, per the example: "Will South Africa be caught offside 2 or more
  times?").
- **Covariates & Elo backbone**: Offsides are a byproduct of **attacking style
  (high line / through-ball frequency / counter-attacking pace)** more than
  pure team strength — so the Elo->offsides relationship is **weaker and
  noisier** than for corners/shots. A team can be offside-prone either because
  it attacks a lot (more attacking actions = more offside chances, like
  corners) OR because it plays a specific high-tempo/through-ball style
  somewhat independent of overall quality (e.g., some mid-table teams with
  fast wingers rack up offsides against deep defenses). Recommend: still use
  `λ_team` (expected goals) as the primary covariate (more attacking
  -> more offside chances, same logic as corners but weaker), but expect a
  smaller R² and wider prediction intervals.
- **Confidence/feasibility**: **Moderate-low**. Direction (more
  attacking team -> somewhat more offsides) is plausible but the
  team-specific "playing style" component (which we have no data on without
  the FBref/StatsBomb panel showing each *specific* 2026 squad's tendencies in
  recent matches) likely dominates the Elo-based component. With the StatsBomb
  2022 panel + FBref 2025-26 friendlies/qualifiers panel, you can at least get
  **team-specific historical offside rates** (e.g., "this team averages 2.3
  offsides/match over the last 20 matches") as a strong prior, blended with
  the weak Elo-based league-average. Pure Elo-only (no team-specific history)
  would likely be close to a coin-flip on "2 or more" type thresholds (depends
  heavily on where the threshold N sits relative to the typical 1-3
  offsides/match range).

---

## 5. Shots / shots on target (96 markets — team and PLAYER level, full-match
and half-by-half)

### 5a. Team-level shots/SOT (full match)

- **Model**: Poisson/NB regression of shots (and SOT separately, since SOT/shots
  ratio also varies by team) on `λ_team` (expected goals) — shots are
  *mechanically* upstream of goals in the data-generating process (a team
  scores by taking shots), so **`λ_team` from the Poisson scoreline model is
  almost definitionally informative for shot volume** — this is the
  *strongest* and most directly justified Elo/Poisson-backbone link of any
  category. In fact, one can think of it the other way: λ_team itself is
  often estimated *from* historical shot/xG data in more advanced models; here
  we're using goals-based λ as a (noisier) proxy for the shots that "should"
  accompany that λ.
- **Covariates**: `λ_team`, plus team-specific shots-per-xG-equivalent ratio
  from the historical panel (some teams are higher-volume/lower-quality
  shooters, others more clinical/lower-volume).
- **Confidence/feasibility**: **Good** for team-level full-match shot
  totals/comparisons — same Skellam-comparison framework as corners.

### 5b. Player-level "at least 1 shot on target" (e.g., "Will Harry Kane have
at least 1 SOT?")

- **Model**: Player-level shot-attempt rate (shots/90, SOT/90 from recent
  club-season data per FBref, per `alt_data_sources.md` (b)#1), combined with
  **expected minutes played** (starter vs bench — explicitly check squad
  depth charts/recent lineups) and the **team's overall expected shot volume**
  (from 5a) as a scaling factor — i.e., `P(player has >=1 SOT) ≈
  1 - exp(-player_SOT_share * team_expected_SOT * minutes_factor)` (Poisson
  with player's share of team SOT volume as the rate).
- **Confidence/feasibility**: **Moderate**. Star players' shot-volume rates
  from club football (e.g., Harry Kane's SOT/90 at Bayern) are reasonably
  stable and transfer somewhat to international football, though
  international matches vs (often weaker) WC group opponents can shift
  shot volume up for star players on favored teams. Biggest risk is **playing
  time uncertainty** (rotation, injury, tactical role) — needs a
  manually-curated "expected starter" list per match, refreshed close to
  kickoff (lineups are announced ~1hr before kickoff; for pre-match pricing,
  use projected/likely XIs from press previews as a proxy, flagging this as a
  **soft input requiring manual curation**, not a clean data-pipeline output).

### 5c. Half/second-half shot splits (part of the 236 half-time markets)

- See §7 below — this is the hardest sub-category because **no
  standard data source provides clean per-half shot/corner/foul/offside
  breakdowns** (FBref match-report team-stats tables are full-match
  aggregates only, per `alt_data_sources.md`). Confidence is **low** for this
  specific cut unless StatsBomb event-level data (which has timestamps, so
  per-half splits ARE derivable from raw events) is used as the fitting set —
  StatsBomb 2022 WC data CAN give "first half SOT" vs "second half SOT" by
  filtering events on `period`/`minute` fields. Recommend: fit a simple
  **"share of full-match shots/corners/etc. that occur in the second half"**
  ratio from StatsBomb 2022 (likely close to 50/55% second-half across most
  teams, possibly skewed by score-state — losing teams attack more in 2nd
  half), and apply that ratio to the full-match team total from 5a/§3.
  This is a coarse but workable bridge.

---

## 6. Half-time / second-half splits & in-game timing (236 markets — by far the
largest uncovered category)

This is a **heterogeneous bucket** spanning: "will Team X score in the 2nd
half" (goals — derivable!), "more corners/SOT in 2nd half" (needs
event-timing data), "first goal of the 2nd half", player SOT-in-2nd-half, etc.
Break it down:

- **Half-time/second-half GOALS sub-questions** (e.g., "Will South Africa
  score in the second half?"): **GOOD NEWS** — this is the one half-time
  sub-category where we have a real path: the Dixon-Coles/Poisson model gives
  full-match λ; if we **assume goals are split Poisson-proportionally to time**
  (a standard simplifying assumption — e.g., ~45% of goals occur in the first
  45 minutes, ~55% in the second 45+stoppage, a well-known empirical
  regularity that goals skew slightly toward the second half, **needs
  verification of the exact split ratio** but commonly cited around
  45/55 or 44/56), we can split `λ_team` into `λ_team_1H` and `λ_team_2H` and
  directly compute "P(team scores >=1 in 2nd half) = 1 - Pois(0; λ_team_2H)".
  This requires **zero new data** beyond confirming the historical 1H/2H goal
  split ratio (computable from the existing martj42 dataset IF it had
  half-time scores — it doesn't — so this ratio itself needs an external
  source: FBref/StatsBomb minute-stamped goal events, a relatively light ask
  since goal *events* with minutes are commonly available even where full
  shot/corner per-half breakdowns aren't).
- **"First goal of the half" markets**: derivable from the same
  λ_1H/λ_2H split via a simple race/competing-Poisson-processes argument
  (P(team A scores first in window | both teams' rates) has closed form for
  independent Poisson processes — standard result: P(A first) =
  λ_A/(λ_A+λ_B) conditional on at least one goal occurring in the window).
  **Confidence: moderate** — assumes goal-scoring is a homogeneous Poisson
  process within each half, which is a simplification (teams don't score
  uniformly — game-state effects exist) but a reasonable first approximation.
- **Half-time corner/shot/SOT/foul comparisons**: per §5c, needs StatsBomb-style
  timestamped event data to derive 1H/2H splits, then apply the same
  "share of full-match total" ratio approach as §5c. **Confidence: low-moderate**
  — workable but several layers of approximation removed from raw data
  (full-match Elo -> full-match count -> half-split ratio -> Skellam
  comparison). Each layer adds variance; expect these to be among the
  *least* confidently-priced markets even after building the full pipeline.
- **Recommendation**: Within this 236-market bucket, **prioritize the
  goals-based half-split markets first** (good feasibility, reuses the core
  Poisson model + one external ratio), and treat the corner/shot/foul-based
  half-split markets as **lowest priority / near-coinflip** until/unless the
  StatsBomb event-level pipeline is built out.

---

## 7. Compound "penalty OR red card" markets (6 markets)

- **Model**: **Simple historical base rate** for the OR-condition,
  computed directly: `P(penalty OR red) = P(penalty) + P(red) - P(penalty AND
  red)`. Each individual event (penalty awarded, red card shown) is a
  **rare, roughly-independent-ish event** (~10-15% and ~5-10% per match
  respectively, **both estimates need verification** from the FBref/StatsBomb
  panel) — combining two ~10% events via inclusion-exclusion gives something
  in the **~18-23% range** for the OR-condition, i.e., this market resolves
  "NO" roughly 75-80% of the time historically.
- **Covariates & Elo backbone**: Weak. Possibly: more mismatched games
  (`|Elo_diff|` large) -> losing team commits more desperate fouls late ->
  marginally higher red-card probability; closer games -> arguably more
  contested penalty-box situations -> marginally higher penalty probability.
  Both effects are **second-order and likely swamped by noise** at the sample
  sizes available.
- **Confidence/feasibility**: **HONEST FLAG — this is one of the categories
  where, even with effort, we are likely to land close to a stable
  ~75-80%/~20-25% split with very little match-specific differentiation**, NOT
  a 50/50 coin flip exactly, but also not a category where our model will add
  much "resolution" (per Murphy decomposition, research_notes.md §5) beyond
  the base rate. The honest move: compute the base rate carefully (it's
  knowable and non-trivial — getting from "I have no idea" to "it's ~20%, not
  50%" IS real value under Brier scoring), but don't expect match-specific
  Elo-based adjustments to move the needle much. Low marginal effort, modest
  but real value (base rate alone beats uniform 50/50 substantially).

---

## 8. Anytime goalscorer / assist (37 markets, player-level)

- **Model**: For player P on team T facing opponent O:
  ```
  P(P scores) ≈ 1 - exp(-μ_P)
  μ_P = (P's recent club-season goals/90) * (expected_minutes/90)
        * adjustment_factor(λ_T / league_avg_λ_for_T's_league)
  ```
  i.e., take the player's **observed scoring rate from current club football**
  (FBref, per `alt_data_sources.md` (b)#1) as the base rate, scale by expected
  minutes (starter ~80-90min, sub ~15-25min), and apply a **multiplicative
  adjustment** based on how the team's expected-goals in THIS match (`λ_T` from
  the Poisson model, which already accounts for the specific opponent's
  defensive strength) compares to the scoring environment the player's club
  rate was observed in. A simple version:
  `adjustment = λ_T_this_match / λ_T_average_for_team` (i.e., is this a
  higher- or lower-scoring match than average for this team given the
  opponent?).
- **Assists**: same structure using assists/90; for the combined "score OR
  assist" markets (the actual question wording in the examples), use
  `1 - exp(-(μ_goals + μ_assists))` as an approximation (treating
  goal-events and assist-events as roughly independent Poisson processes for
  one player — a simplification, since a player can't both score AND assist
  the same goal, but for "OR" questions at low individual rates the
  double-counted overlap is small).
- **Confidence/feasibility**: **Moderate, with high variance by player
  profile**. Works reasonably well for **high-usage attacking players with
  substantial recent club minutes** (e.g., a starting striker for a top-5
  league club) — their club G+A/90 is a meaningful signal. Works **poorly**
  for: players who recently changed clubs/leagues (rate may not transfer),
  players who are squad rotation risks (binary minutes uncertainty dominates),
  and players from leagues/confederations where FBref data quality is weaker.
  The team-level `λ_T` adjustment is well-justified (it's literally reusing
  the core model's opponent-adjustment), but the player-level base rate is the
  noisier ingredient. **Recommend a manual "starter confidence" tag** per
  named player (high/medium/low likelihood of starting/playing 60+ min) as a
  required input alongside the rate-based estimate — this is the single
  biggest swing factor and isn't reliably automatable from data alone close
  to kickoff.

---

## Summary: feasibility ranking (most to least confident, beyond Elo+Poisson core)

| Category | Confidence | Why |
|---|---|---|
| Half-time goal-based splits (subset of the 236) | Good-Moderate | Direct extension of existing Poisson λ via a 1H/2H goal-split ratio; minimal new data |
| Corners (team comparisons) | Good | Strongest Elo/λ-proxy relationship (attacking pressure -> corners), StatsBomb 2022 gives clean fitting data |
| Team-level shots/SOT (full match) | Good | λ_team is mechanically linked to shot volume |
| Fouls (team comparisons) | Moderate-Good | Well-supported Elo->possession->fouls proxy, needs international-specific calibration |
| Cards (yellow totals/comparisons) | Moderate | One step downstream of fouls, more noise |
| Anytime goalscorer/assist | Moderate (variance by player) | Club rate + λ_T adjustment works for regular starters; minutes uncertainty is the main risk |
| Player-level shots-on-target props | Moderate | Same as above, plus playing-time risk |
| Offsides | Moderate-Low | Weaker Elo link (style-dependent); team-specific history needed |
| Half-time non-goal splits (corners/shots/fouls per half) | Low-Moderate | Needs StatsBomb-derived per-half ratios; multiple approximation layers |
| Penalty OR red card (compound) | Low resolution, but base rate is knowable (~20-25% YES, not 50/50) | Rare-event base rates dominate; little match-specific signal expected |

**Overall recommendation**: After the core Elo+Poisson model, build the
team-match event-count panel (FBref + StatsBomb 2022, per
`alt_data_sources.md`) ONCE, since it feeds fouls, cards, corners, shots, AND
offsides simultaneously via the same Elo/λ-regression + Skellam-comparison
framework — this is the highest-leverage single piece of new infrastructure.
