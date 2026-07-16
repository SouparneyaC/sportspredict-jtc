# Modeling "Will a penalty kick be awarded in regulation?"

Research foundation for the pure penalty-award question type. Written 2026-07-15 ahead of the
England vs Argentina WC2026 semifinal, whose Q3 asks exactly this and which the project currently
prices only off the Smarkets mid (0.29), with no fitted model behind it.

Scope. Two parts. Part 1 mines the project's own settled history of pricing penalty and red-card
questions and computes an empirical penalty base rate from local data. Part 2 is external academic,
cross-sport, and market research. The file closes with a concrete recommendation and a sanity-check
of tonight's 0.29.

A distinction runs through everything below and must be kept sharp: almost all of the project's own
history is the **compound** form, "penalty OR red card" (priced by RULE4, an inclusion-exclusion
combination). Tonight's Q3 is the **pure** form, "penalty awarded," which is a different and simpler
question. The two are separated everywhere in this document.

---

# PART 1 — What the project has already done

## 1.1 The current pricing mechanism (RULE4)

There is no fitted penalty model. Compound penalty-or-red-card questions are priced by RULE4, and
the pure penalty question has always been taken straight from the liquid market.

RULE4's origin, from `ML_EXPERIMENTS_NOTEBOOK.md` line 330, is a compound-question rule born after a
large loss (QAT-SUI Q1, −42.51, an over-extreme independence product on "both teams achieve X"): for
compound questions, weight toward the crowd rather than trusting a naive product of component
probabilities. As applied to penalty-or-red-card, the mechanism recorded in the match files is an
inclusion-exclusion combination of two component rates. The canonical statement is in
`matches/France_vs_Morocco/04_rules_applied.json` (Q10):

> Smarkets Penalty to be awarded: implied Yes = 0.2779. Smarkets Any player to be sent off: Yes mid
> = 0.1472. Combined via inclusion-exclusion assuming rough independence:
> 1−(1−0.2779)(1−0.1472) = 0.3842.

So RULE4 for this family is `P(pen OR red) = 1 − (1 − P_pen)(1 − P_red)`, with the two components
sourced from either the separate Smarkets sub-markets, referee career rates, or a tournament-wide
empirical rate, and the result nudged toward the crowd. The pure penalty component `P_pen` inside
that formula is itself never modeled — it is read off the market or a referee's per-game penalty
rate (for example Elfath's 0.27 pens/game career rate, 0.18 this season, in the notebook).

## 1.2 Settled track record

Every settled match folder was scanned (`grep -i penalt` across `05_estimates.json`,
`04_rules_applied.json`, `06_post_match_results.json`). Three structurally different question types
appear, and conflating them would be a mistake:

1. **Pure penalty awarded** — "Will a penalty kick be awarded in regulation?" (tonight's Q3 type).
2. **Compound penalty OR red card** — the RULE4 family.
3. **Match decided by a penalty shootout** — a knockout-progression question, structurally unrelated
   (it depends on the match being level after extra time, not on an in-play foul), listed separately
   for completeness and excluded from all penalty-award aggregates.

### Table A — Pure penalty-award questions (the type that bears directly on tonight)

| Match | Date | Question | Our est. | Crowd | Outcome | RBP | Beat crowd | Instrument |
|---|---|---|---|---|---|---|---|---|
| France_vs_Paraguay | 2026 | Penalty awarded in regulation | 0.28 | 0.27 | YES | +5.31 | Yes | DIRECT market mid |
| mex_ecu_2026-06-30 | 2026-06-30 | Penalty awarded in regulation | 0.26 | 0.25 | NO | +1.71 | Yes | DIRECT market mid (0.258) |

Pure-penalty aggregate: n = 2, mean RBP +3.51, both positive, beat crowd 2/2. Both submissions
were essentially the market mid, trimmed by a hair; both landed on the right side of the crowd. This
is the entire directly-relevant track record — two questions, both priced by copying the market, no
model. It tells us the market-copy approach has not hurt us, and nothing more (n = 2).

### Table B — Compound penalty-OR-red-card questions (RULE4 family)

| Match | Our est. | Crowd | Outcome | RBP | Beat crowd |
|---|---|---|---|---|---|
| Argentina_vs_Switzerland | 0.45 | 0.36 | YES | +24.41 | Yes |
| Australia_vs_Egypt | 0.35 | 0.32 | NO | −1.43 | No |
| Canada_vs_Morocco | 0.34 | 0.32 | NO | +0.77 | Yes |
| France_vs_Morocco | 0.38 | 0.35 | YES | +11.16 | Yes |
| Norway_vs_England | 0.38 | 0.35 | NO | −0.50 | No |
| Portugal_vs_Croatia | 0.37 | 0.32 | YES | +16.08 | Yes |
| Spain_vs_Belgium | 0.33 | n/a | NO | n/a (correct direction) | n/a |
| Switzerland_vs_Algeria | 0.336 | n/a | *unsettled* | — | — |

Compound aggregate (6 with recorded RBP): mean RBP +8.42, sum +50.49, positive on 4/6, beat crowd
4/6. Spain_vs_Belgium settled NO in the correct direction but has no RBP/crowd recorded;
Switzerland_vs_Algeria has no `06_post_match_results.json` and is treated as unsettled.

Combined penalty-family (pure + scored compound, n = 8): mean RBP +7.19, sum +57.51, positive on
6/8, beat crowd 6/8 (75%). Positive overall, driven by the compound wins.

### Table C — Penalty-shootout questions (different family, excluded from the above)

Brazil_vs_Norway (+11.29), Canada_vs_Morocco (+8.43), Mexico_vs_England (+9.82) — all "decided by a
penalty shootout", all priced off the direct market mid, all NO, all beat crowd. Strong record, but
these do not inform the in-play penalty-award question at all and are noted only so the grep hits are
accounted for.

## 1.3 Documented lessons on penalty pricing

The notebook is candid about a recurring failure mode on the **compound** family, and it is worth
quoting because it is the one behavioral bias the project has flagged in its own penalty pricing:

- `ML_EXPERIMENTS_NOTEBOOK.md` line 1451: "Historical pattern: we keep being too high on
  penalty/red card questions. Need to audit this question type across the full ledger." This came
  after a compound loss where the project sat at 0.45 vs crowd 0.37 and it settled NO.
- Line 1013 (a compound loss): "We over-elevated penalty probability based on [a team's] historical
  penalty involvement ... The clean tactical survival match narrative ... didn't support penalties.
  Crowd at 38% was better calibrated."
- Line 1136–1137: "Referee penalty rate is match-type-specific: [a] career 0.5 pens/game rate is
  extraordinary. But in his WC2026 match (a 7-1 blowout), he gave 0 penalties. Blowout context
  suppresses penalty frequency ... discount by ~30-40% for blowout context."

The through-line is that the project's misses on this family have come from pushing **above** the
crowd/market on thin team-specific or referee-specific signals (an extreme referee rate, a team's
recent penalty-involvement streak) that then failed to materialize in a controlled match. The two
pure-penalty submissions, by contrast, simply copied the market and did fine. The documented lesson,
read honestly, argues *against* over-modeling this event off small-sample covariates and *for*
anchoring on a well-measured base rate or the liquid market.

## 1.4 Local data inventory bearing on penalty rates

| Source | Path | Penalty content |
|---|---|---|
| Rare-event panel | `ml/backtests/rare_event_panel.csv` | 100 WC2026 matches, but **no penalty column** — covers goals, hydration-break goals, first-sub race, VAR mentions only. Not usable for penalties as-is. |
| Referee card panel | `topics/cards/referee_card_panel.csv` | Referee-level card rates; red-card component of the compound question, not penalties directly. |
| ESPN raw event dumps | `data/processed/espn_raw_events/*.json` (101 files) | `keyEvents` records penalties as `Penalty - Scored / Saved / Missed` with a `period.number` and clock. Ground-truth-checked below. |
| StatsBomb open-data mirror | `data/external/statsbomb/open-data/` | Full event data for WC2018, WC2022, Euro2024, Copa America 2024, AFCON 2023 (plus partial older WCs). Penalties appear as `Shot` events with `shot.type.name == "Penalty"` and as `Foul Won` with `foul_won.penalty == true`. This is the authoritative corpus. |

## 1.5 Empirical penalty base rate — computed from local StatsBomb data

**Schema ground-truth check (per the project's standing rule).** Before trusting the fields, I
verified them against a known case: the WC2022 final (Argentina 3–3 France, match_id 3869685). The
extraction correctly recovered Messi's 22' regulation penalty and Mbappé's 79' regulation penalty
(both as `Shot` with `shot.type.name == "Penalty"` in periods 1–2, each preceded by a matching
`Foul Won` with `foul_won.penalty == true`), Mbappé's 117' extra-time penalty (period 4), and all
seven shootout penalties (period 5). So period ∈ {1,2} isolates **penalties awarded in regulation**,
which is exactly what Q3 asks; periods ≥ 4 are extra-time/shootout and are excluded.

**Result — five VAR-era major men's tournaments, 263 matches:**

| Tournament | Matches | Reg. penalties | Pens/match | P(≥1 pen in regulation) |
|---|---|---|---|---|
| FIFA World Cup 2018 | 64 | 28 | 0.438 | 0.375 |
| FIFA World Cup 2022 | 64 | 22 | 0.344 | 0.312 |
| UEFA Euro 2024 | 51 | 11 | 0.216 | 0.196 |
| Copa América 2024 | 32 | 10 | 0.312 | 0.219 |
| AFCON 2023 | 52 | 22 | 0.423 | 0.346 |
| **Pooled** | **263** | **93** | **0.354** | **0.300** |

The headline empirical anchor: **P(at least one penalty awarded in regulation) ≈ 0.30** across 263
VAR-era matches; **0.354 penalties per match** on average. The WC2018 figure (28 regulation
penalties) independently validates the extraction — Russia 2018 is famous for a record penalty haul,
and the count lands where public reporting puts it.

**By stage (pooled):**

| Stage | Matches | Pens/match | P(≥1 pen in regulation) |
|---|---|---|---|
| Group | 192 | 0.339 | 0.292 |
| Knockout | 71 | 0.394 | 0.324 |

Knockout matches run slightly higher (0.324 vs 0.292), consistent with more cautious, higher-stakes
play generating more box contact and more scrutiny — but the gap is well within sampling noise at
n = 71 and should be treated as a soft, not a hard, adjustment.

**VAR-era note.** The mirror's pre-VAR World Cups (1958–1990) contain too few matches with event
data (1–6 each) to compute a credible pre-VAR baseline, so I do not report a within-corpus VAR
contrast — that comparison is left to the external literature in Part 2, which quantifies it
properly. All five tournaments above are VAR-era, so 0.30 is already a VAR-era rate.

**WC2026-specific cross-check (ESPN, and an honest data-quality caveat).** The France–Paraguay
penalty (Mbappé, 70', `Penalty - Scored`) is present in the ESPN feed and matches the settled result
in that match folder, so the field is real. Counting `Penalty - Scored/Saved/Missed` events in
periods 1–2 across the 101 WC2026 ESPN files gives 19 regulation penalties, or **P(≥1) ≈ 0.17,
0.19 pens/match** — roughly half the StatsBomb rate. This gap is large enough (≈2.6 SD below 0.30
on 100 trials) that it is almost certainly not pure variance. The most likely explanation is that
ESPN `keyEvents` is a **curated highlights feed that undercounts penalties**, not that WC2026 is
genuinely a low-penalty tournament — StatsBomb's schema is exhaustive and ground-truth-verified,
whereas `keyEvents` demonstrably drops non-highlight events elsewhere in the pipeline. I therefore
treat **StatsBomb 0.30 as the authoritative base rate** and flag the ESPN 0.17 as a probable
undercount / lower bound, not a competing estimate. (A worthwhile follow-up, out of scope tonight:
recount WC2026 penalties from the fuller ESPN `commentary` feed to confirm the undercount.)

---

# PART 2 — External research

Sources were fetched live. Where a page was paywalled or I could reach only an abstract or a
secondary summary, that is stated explicitly.

## 2.1 Academic literature: penalty awards, referees, and VAR

**VAR measurably increased penalty awards — this is the best-quantified finding in the whole
literature, and it matters because it means older/pre-VAR base rates are biased low.** Concrete
numbers I was able to confirm:

- Twelve Yards (analyst blog, citing ESPN's Dale Johnson and league data), read directly: season
  penalties-per-game rose Premier League 0.24 → 0.41 and Bundesliga 0.24 → 0.41; France 0.37 →
  0.47; La Liga 0.39 → 0.41. The same piece cautions that VAR's *net* contribution is more modest
  than the raw jump (e.g. Premier League +9 net penalties: 18 awarded on review, 9 rescinded), i.e.
  VAR both adds missed penalties and removes wrongly-given ones. (twelveyards.substack.com)
- Aggregated search reporting: roughly a 12% increase in penalties across Europe's big-5 leagues
  post-VAR, but highly heterogeneous by league — Spanish referees +32.7%, while the Premier League
  and Bundesliga later showed small declines as the novelty/handball-interpretation settled. So the
  VAR effect is real but non-uniform and has partially reverted.
- Rogerson et al. (2026) meta-analysis in *International Journal of Sports Science & Coaching*
  (SagePub), fetched directly: it pooled 16 club competitions and found **no** VAR-associated
  reduction in home advantage (goal-difference mean −0.02, p = 0.61), and it explicitly notes that
  "some studies found significantly more penalties awarded with VAR" but did **not** itself
  meta-analyze penalty counts. So the penalty-increase claim is supported by individual studies but
  not yet by a pooled meta-estimate — I state that honestly.

**Referee and home-advantage effects.** The classic finding (Boyko et al. and the sports-neuro
literature, via PMC and Taylor & Francis abstracts) is that referees award disproportionately more
contentious/penalty decisions to the home side — one prominent study attributes ~69–71% of
contentious decisions to the home team, driven by crowd noise, with experienced referees showing
smaller bias. A dissenting 2025 study ("No home team bias in elite football referees", JSES) finds
the effect attenuated in the modern (VAR, and post-empty-stadium) era. For a neutral-venue WC
knockout the home-bias channel is muted, which is mildly relevant tonight.

**Poisson framing of rare in-match events.** The goals-modeling literature (Maher; Dixon–Coles; the
double-Poisson Euro/AFCON papers) establishes that low-frequency independent in-match events are
well described by a Poisson process, but every source flags overdispersion and the "too few zeros /
memoryless" caveat. No paper I found models `P(penalty in a match)` directly as its own Poisson
target with covariates — penalties are almost always studied descriptively (rates, referee bias, VAR
effect), not as a fitted forecasting target.

## 2.2 The key design question: flat base rate vs covariate-driven rate

The honest answer from the evidence is that a covariate-driven penalty-award rate is *plausible in
principle* but *poorly supported in practice at any sample the project can reach*.

Arguments that penalties should be derived from offensive load rather than a flat rate: a penalty is
a rare tail outcome of attacking pressure in the box, so a team taking more touches/entries in the
opposition box mechanically exposes itself to more penalty opportunities, and rugby analytics (2.3)
does normalize penalty counts by possession precisely on this logic. The performance-analysis blogs
frame referee penalty variation partly as a function of match physicality and box activity.

Arguments against building such a model here: (1) the penalty xG literature shows a penalty is a
**standardized** event once awarded (fixed xG ≈ 0.76–0.79 across providers), meaning the modeling
difficulty is entirely in the *award* step, which is a refereeing decision, not a mechanical
consequence of shot volume — high box activity raises exposure but the conversion of exposure into an
awarded penalty is a low-rate, referee-mediated, VAR-mediated step with large variance. (2) The
project's own documented losses (§1.3) came precisely from letting covariates (referee rate, team
penalty streak) pull the estimate away from the base rate. (3) The sample-size arithmetic in §Synthesis
makes a fitted covariate model statistically undisciplinable at the project's n.

## 2.3 Cross-sport analogues

The user asked for creative cross-sport transfer. The structurally-identical problem — "will a rare
officiating/set-piece event occur, and how many" — is modeled as a **count process** in every sport
I checked, and the dominant tool is a Poisson or, more honestly, a **negative-binomial** GLM to
handle overdispersion.

| Sport | Event | Modeling approach found | Transfer to football penalties |
|---|---|---|---|
| Rugby league | Penalties + set restarts (~11.2 + 6.0 per game) | Penalties-above-average per referee, **normalized for possession**; Poisson/GLM with referee and team-discipline covariates | Strong conceptual transfer: the possession-normalization is exactly the "derive rate from offensive load" idea. But rugby's rate is ~30× football's, so rugby can *fit* covariates that football's rare event cannot support. |
| NHL | Penalties drawn / power plays | Poisson vs negative-binomial count models; the hockey literature explicitly prefers NB because penalty counts are overdispersed (variance > mean) | Confirms NB over Poisson for officiating counts; but again NHL penalty counts are far higher-frequency, so the covariate fit is feasible there and not here. |
| NFL | Penalty flags per game | Overdispersed count regression (NB), team/referee-crew fixed effects | Same lesson: crew-level effects are real and estimable only because there are dozens of flags per game. |
| Handball | Match goal counts | Underdispersed sparse-count regression (arXiv 1901.05722) — a reminder that the right count distribution is empirical, not assumed | Method-transfer: choose the count distribution from the data, do not assume Poisson. |
| General | Any point event | Hawkes / self-exciting point process + Ogata residual goodness-of-fit (from the quant-finance order-arrival literature already cited in the project's rare-event methodology doc) | Elegant but overkill and un-fittable at n≈1 penalty every 3 matches; noted for completeness. |

The single most useful cross-sport takeaway: **model the count with a negative-binomial GLM, not a
Poisson**, because officiating-event counts are reliably overdispersed — but do so *only when the
event is frequent enough to estimate covariates*, which in football's low-penalty regime it is not.
For football, the count model collapses to what it can actually support: an intercept-only rate,
i.e. a base rate. `P(≥1 penalty) = 1 − exp(−λ)` with λ ≈ 0.354 gives 0.298, essentially identical to
the direct empirical 0.300 — the Poisson intercept and the raw frequency agree, which is reassuring.

## 2.4 How betting markets price "penalty awarded" props

The general football-market efficiency literature (Winkelmann/Oetting/Deutscher SSRN; Elsevier
*IJF* on online football markets) finds main markets broadly efficient with only transient,
non-systematic inefficiencies, and documents a favourite-longshot bias. I found **no** study
specifically on the efficiency of penalty-awarded prop markets — this is a genuine gap, stated
honestly. What is known from the project's own experience is that these props are often **thinly
quoted** (the mex_ecu penalty market had a wide bid 0.2083 / offer 0.3077 around a 0.258 mid; the
France–Morocco penalty market had no posted Yes side at all, only a No mid). So the practical caution
is not that the market is inefficient but that it is often *illiquid*, so the mid can be a noisy
read and the spread wide — worth crossing against an empirical anchor rather than copied blindly.

---

# Synthesis and recommendation

## Is a fitted covariate model viable at the project's sample size?

No. The project's own rare-event methodology note (`BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md`)
already establishes the arithmetic that settles this. Kupiec's worked example needs ~255 i.i.d.
trials to reach even 65% power against a *3×* rate misspecification; the meteorology Brier-skill
literature calls n < 100 unreliable for rare-event skill measurement; and the project will see on the
order of tens of WC2026 penalty realizations, not hundreds. A covariate model (referee rate × team
box-activity × stage) has more parameters than the project has penalty events to fit them on — it
would overfit noise, which is exactly the failure the notebook already recorded when it let referee
rates and team penalty-streaks pull estimates above the crowd (§1.3). The cross-sport review
reinforces this from the other direction: rugby/NHL/NFL can fit covariate count models only because
their officiating events are 10–30× more frequent.

## Recommended approach for this project

A tiered rule, in priority order:

1. **When a liquid penalty market exists, trust it, lightly anchored to the empirical base rate.**
   The two pure-penalty submissions on record both did this and both beat the crowd. Take the market
   mid, and only deviate if it sits materially outside a defensible base-rate band.

2. **The base-rate band comes from the StatsBomb VAR-era corpus computed here: P(≥1 penalty in
   regulation) ≈ 0.30, with a knockout tilt to ≈ 0.32.** This is the single best empirical anchor
   the project has for this question type — 263 schema-verified matches, VAR-era, ground-truth
   checked. It replaces the ad-hoc referee-rate combinations for the pure-penalty case. Do **not**
   use the ESPN WC2026 0.17 as the anchor; it is a probable undercount.

3. **If a stage/matchup adjustment is wanted, apply it as a small, principled shrinkage, not a
   fitted model.** A defensible construction is a Poisson intercept λ ≈ 0.35 (→ P(≥1) = 0.30),
   nudged up modestly for a high-stakes knockout with two high-volume attacks (toward the 0.32
   knockout empirical rate), never beyond roughly 0.34 without a live market saying so. Express the
   uncertainty as a Beta/Beta-Binomial band (e.g. centered near 0.30 with a wide interval) for
   internal record-keeping, exactly as the methodology note recommends for VAR-review questions —
   report a reasoned point estimate with explicit low-to-medium confidence, never a "backtested"
   number.

4. **For the compound penalty-OR-red question, keep RULE4** but source its `P_pen` component from
   the 0.30 base rate rather than from thin referee samples, and honor the documented "we run too
   high" lesson by not pushing above the crowd on team-specific penalty streaks.

In short: option (c)+(b) — trust the liquid market when one exists, disciplined by a properly
calibrated empirical base rate from the StatsBomb corpus. Not (a): do not build a covariate model at
this n.

## Sanity check: does tonight's 0.29 look right?

Yes. The Smarkets mid of 0.29 for "penalty awarded in regulation" sits essentially on top of the
independent empirical anchor: StatsBomb VAR-era P(≥1 penalty in regulation) = 0.300 pooled, 0.324 in
knockout matches, and the Poisson-intercept construction gives 0.298. If anything 0.29 is a hair
below the knockout-specific rate (0.32), so for a semifinal between two high-volume attacking sides
one could justify nudging *up* toward 0.30–0.32 rather than down — but the difference is small and
well inside sampling noise. The market number is well-supported and there is no evidence-based case
for moving it more than a couple of points. Recommendation for tonight's Q3: hold at the market
0.29, or at most 0.30–0.31 to reflect the knockout tilt, and log it as medium confidence with the
0.30 base rate as its documented justification.

---

## Sources

Internal: `topics/penalties-red-cards/README.md`; `matches/*/0[456]_*.json`;
`ML_EXPERIMENTS_NOTEBOOK.md` (RULE4 origin line 330, overpricing lesson line 1451, blowout-suppression
line 1136); `BACKTEST_METHODOLOGY_RARE_EVENTS_2026-07-14.md` (small-sample power arithmetic);
`data/external/statsbomb/open-data/` (competitions 43, 55, 223, 1267); `data/processed/espn_raw_events/`.

External (fetched this session):
- VAR and penalties: [Twelve Yards, "VAR, penalties and empty stadia"](https://twelveyards.substack.com/p/var-penalties-and-empty-stadia); [Rogerson et al. 2026 meta-analysis, IJSSC (SagePub)](https://journals.sagepub.com/doi/10.1177/17543371241242914); [Frontiers/PMC EPL VAR disciplinary study](https://pmc.ncbi.nlm.nih.gov/articles/PMC13044101/); [Spreadex big-5 VAR summary](https://www.spreadex.com/sports/blog/features/var-impact-europe-big-5-premier-league/).
- Referee / home advantage: [Boyko et al., "Referee bias contributes to home advantage" (T&F)](https://www.tandfonline.com/doi/full/10.1080/02640410601038576); [Sports neuro-decision study (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC9407239/); [Carrington et al. 2025, "No home team bias in elite football referees" (JSES)](https://jses.net/wp-content/uploads/2025/12/JSES_Carrington-et-al.-2025_Volume-9-Issue-2-Article-5.pdf).
- Penalty xG: [Jobs In Football, "What is the xG of a penalty?"](https://jobsinfootball.com/blog/what-is-the-xg-of-a-penalty/).
- Cross-sport count modeling: [Poisson NHL playoffs (DiVA)](https://www.diva-portal.org/smash/get/diva2:1106292/FULLTEXT01.pdf); [Rugby League Eye Test, penalties above average by referee](https://www.rugbyleagueeyetest.com/2025/06/09/penalties-set-restarts-above-average-by-referee-and-team-discipline-update/); [PyMC hierarchical rugby model](https://www.pymc.io/projects/examples/en/latest/case_studies/rugby_analytics.html); [Handball underdispersed count regression (arXiv 1901.05722)](https://arxiv.org/pdf/1901.05722).
- Market efficiency: [Winkelmann, Oetting & Deutscher, "Betting Market Inefficiencies in European Football" (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3672233); [Elsevier IJF, "Efficiency of online football betting markets"](https://www.sciencedirect.com/science/article/abs/pii/S0169207018301134).
