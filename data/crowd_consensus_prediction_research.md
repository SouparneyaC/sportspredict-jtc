# Predicting the SportsPredict In-House Crowd: Literature Review & Build Plan

**Context:** SportsPredict scores us on `RBP = (crowd_brier - our_brier) * scale`
— a *relative* (crowd-beating) Brier score with no API access to the in-house
crowd's consensus probability before a match closes. Our external-exchange
proxy (Kalshi/Polymarket/Smarkets/offshore books) nailed three niche prop
markets in SK vs Czechia but was *worse* than SportsPredict's crowd on the
marquee match-winner market (we said ~37% SK, the in-house crowd said ~51%,
Korea won). This note surveys academic and applied literature on crowd
mispricing, fan/home-nation bias, and meta-prediction techniques, with an eye
toward building a "predict the in-house crowd's number" model that
complements our "predict the true probability" model.

---

## Executive Summary

- **The in-house crowd is not the same animal as Kalshi/Polymarket.** Real-money
  exchanges are dominated by relatively sharp, loss-averse traders and exhibit
  the *favorite-longshot bias* (longshots overpriced, favorites slightly
  underpriced) (Snowberg & Wolfers 2010). A free-to-play prediction game's
  userbase is closer to "casual sports bettor" populations studied by Levitt
  (2004) and the national-sentiment literature — these populations show the
  *opposite* sign of bias on matches involving their own team: systematic
  **over-optimism about the home/favorite national team**, especially when
  that team is "their" team.

- **Home-nation / national-sentiment bias in football betting is a
  well-documented, *quantified*, and directionally consistent effect**
  (Braun & Kvasnicka 2013; Štěpán & Šíma-style Czech studies). Domestic
  bettors systematically over-rate their own national team's win probability,
  and bookmakers in those markets *price against* that bias (shade odds against
  the popular team) — meaning the "true" line in a country's domestic market
  is measurably below the crowd's naive probability. SK vs Czechia (Korean
  crowd at 51% vs sharp-market 37%) is a textbook example of this gap, just
  larger than typical domestic-league examples (likely because (a) this is a
  win/lose binary World Cup match, very high salience, and (b) SportsPredict's
  userbase for a Korea fixture is plausibly *very* Korea-skewed, more so than
  a generic domestic bookmaker's customer base).

- **"Big/popular team" bias generalizes beyond home nations**: the 2025
  "Goal-line oracles" PLOS ONE study of Premier League crowd forecasts found
  systematic over-prediction of "big-6" club performance and under-prediction
  of smaller/newly-promoted clubs — i.e., popularity/prestige biases crowd
  judgment even absent nationalism. For the World Cup this suggests
  *glamour/star-power teams* (Brazil, Argentina, France, etc.) may carry a
  built-in crowd premium on SportsPredict beyond what "home nation" alone
  predicts.

- **The Surprisingly Popular (SP) algorithm (Prelec, Seung & McCoy, Nature
  2017)** is directly relevant in *spirit*: it operationalizes "predict what
  others will predict, and compare to what they predict others will predict."
  We can't run SP literally (we don't have access to other users' meta-predictions),
  but the same logic motivates building **observable proxies for "what a
  Korea-heavy/fan-driven crowd would guess"** — Google Trends search-interest
  ratios, social buzz, fixture salience/kickoff-time-zone effects, and squad
  star power — as inputs to a *crowd-bias model* that sits alongside our
  *true-probability* model.

- **Under a relative/crowd-beating scoring rule, the formal literature
  (Metaculus incentive-design discussions, "Alignment Problems with Current
  Forecasting Platforms," arXiv 2106.11248) confirms our intuition**: optimal
  play is NOT "report your true belief" — it's "report your true belief,
  *adjusted by your best estimate of the crowd's error*, in the direction that
  maximizes expected distance-advantage over the crowd." If we're confident
  about both (a) our true-probability estimate and (b) the *direction and
  magnitude* of the in-house crowd's bias, the formally optimal submission is
  *between* our true estimate and the *opposite* side of the crowd's bias —
  effectively a deliberate small "anti-crowd" tilt, bounded by our own
  uncertainty about the bias estimate itself (see §6 for the math sketch).

---

## 1. Favorite-Longshot Bias Literature

**Snowberg, E. & Wolfers, J. (2010), "Explaining the Favorite-Longshot Bias: Is
it Risk-Love or Misperceptions?"** *Journal of Political Economy* 118(4), and
the earlier NBER working paper (NBER WP 15923).
Using horse-racing data, the authors show longshots are systematically
*overbet* (offer worse-than-fair returns) while favorites are *underbet*
(better-than-fair returns). They test risk-love (bettors enjoy lottery-like
payoffs) vs misperception (bettors simply get probabilities wrong) as
competing explanations, and the data favor **misperception**: bettors
overestimate the chances of low-probability outcomes. This is the canonical
reference for "crowds compress the probability scale toward 50% / toward the
middle," which is the opposite direction from "crowds overrate their favorite
team's chances" — these are *different* biases (population-level probability
miscalibration vs identity-driven team-specific optimism), and both can be
present simultaneously.

**Levitt, S.D. (2004), "Why Are Gambling Markets Organised So Differently from
Financial Markets?"** *Economic Journal* 114(495).
Levitt's empirical finding (using data from a sports-betting tournament with
both "sharp" and "square" bettors) is that **bookmakers are better forecasters
than the betting public**, and bookmakers deliberately set prices that deviate
from the "market-clearing" price *to exploit known biases in the betting
public* — specifically the bias toward overbetting favorites/popular teams —
accepting some one-sided risk in exchange for a higher expected margin. This
is the theoretical foundation for "the public's revealed preference is a
biased signal, and someone with information about that bias can extract value
from the gap between public sentiment and the true line."

**Green, E.A., Lee, H. & Rothschild, D., "The Favorite-Longshot Midas"**
(Wharton/Jacobs Levy Center working paper).
Extends the favorite-longshot literature with a focus on whether the bias
is exploitable net of transaction costs/vig — relevant to us because
SportsPredict's "exploitability" isn't about transaction costs but about a
*relative* score, so even small, consistent directional biases are
worth capturing if we can predict them.

**Implication for us:** the favorite-longshot literature describes a bias that
mostly applies to *real-money* markets (the kind we already use as our
external proxy). It is probably *not* the dominant bias in SportsPredict's
in-house crowd — the in-house crowd's bias on the Korea match looks much more
like an *identity/fan* bias (§2, §4) than a longshot-overpricing bias. But for
matches where neither team has a large "home" fanbase on the platform (e.g.
two non-Korean teams, low-profile fixture), the in-house crowd might revert to
something closer to a generic-public favorite-longshot pattern, i.e. compress
extreme probabilities toward 50% relative to the sharp-market number. Worth
testing once we have a few more settled matches.

---

## 2. Wisdom-of-Crowds Failure Conditions

**Surowiecki, J. (2004), *The Wisdom of Crowds*** (popular book, building on
Galton's 1907 *Nature* note "Vox Populi" about the Plymouth ox-weight-guessing
contest, median guess within 0.8% of true weight).
The classic positive result requires: (1) **diversity** of opinion/information,
(2) **independence** (errors are not correlated across individuals), (3)
**decentralization**, and (4) a good **aggregation mechanism**. Galton's
original result works because each fairgoer's guess error is roughly
idiosyncratic — some overestimate, some underestimate, and these average out.

**Failure mode — correlated errors / herding**: When individuals are exposed
to the same information, narrative, or social signal (e.g., everyone sees the
same news coverage, the same star player's highlight reel, the same "Korea is
the underdog story" narrative), their errors become *positively correlated*
and averaging no longer cancels noise — it amplifies a shared bias. This is
exactly the mechanism by which a platform's national-composition skew (lots
of Korean users seeing Korean media coverage of a Korea match) turns into a
crowd-level bias rather than averaging out.

**Failure mode — self-selection into the crowd**: A free prediction game's
"crowd" is not a random sample of all football fans; it's *whoever chose to
play that market*. If Korean fans are disproportionately likely to engage with
a Korea-vs-X market (because it's "their" match), the effective sample is
selection-biased toward exactly the population most likely to hold an
optimistic prior about Korea — a second, compounding mechanism beyond simple
correlated-error herding.

**Implication for us:** both mechanisms point the same direction and both are
*observable in principle* — fixture salience to a given national audience (via
search trends, social mentions) is a reasonable proxy for "how skewed is the
self-selected SportsPredict crowd toward that nation's fans for this specific
match."

---

## 3. Surprisingly Popular / Bayesian Truth Serum Literature

**Prelec, D., Seung, H.S. & McCoy, J. (2017), "A Solution to the
Single-Question Crowd Wisdom Problem,"** *Nature* 541, 532–535.
The Surprisingly Popular (SP) algorithm asks each respondent two questions:
(1) what's your answer, and (2) what fraction of others do you think will give
each possible answer (a meta-prediction)? The SP algorithm then favors answers
that are **more popular than people predicted them to be** — the logic being
that if an answer is "surprisingly" more common than the crowd expected, it's
likely because a subset of people have private information that the majority
lacks, and that signal leaks through in their meta-predictions even when their
direct answers are in the minority. Builds on Prelec's earlier **Bayesian
Truth Serum** (2004, *Science*), which scores respondents based on how
"surprising" their answers are relative to the population's *predicted*
answer distribution, incentivizing honesty over conformity.

**Follow-ups**: "Machine Truth Serum" (Springer ML Journal, 2022) extends SP
to ensemble ML settings — using a model's calibration of its own predicted-vs-actual
class distributions as a truth-serum-style correction, conceptually similar
to what we'd want: correct our raw probability using a learned "how does the
crowd's stated belief differ from the true distribution" function.

**Why this matters for us — adapted framing**: We can't literally run SP (we
don't have access to SportsPredict users' meta-predictions). But the *spirit*
of SP — "the gap between what people say and what they'd predict others would
say reveals private information / bias" — translates into: **build a model
that predicts `crowd_probability - true_probability` (the bias term) as a
function of observable fixture characteristics**, then:
```
crowd_estimate ≈ our_true_probability_estimate + bias_model(fixture_features)
```
This is essentially a residual/correction model layered on top of our existing
true-probability model — a practical, data-available analog to SP's
"surprisingly popular" correction.

---

## 4. Football-Specific Crowd/Fan Bias Research

**Goal-line Oracles: Exploring Accuracy of Wisdom of the Crowd for Football
Predictions**, PLOS ONE, Jan 2025 (PMC11785260; LSE Research Online eprint
127328; also covered in an LSE blog post, May 2025).
Crowd-sourced predictions (760 team-level predictions across a Premier League
season) of expected goals (xG) were compared against actual xG and bookmaker
odds. Findings:
- The crowd's *aggregate* prediction tracked actual xG well on average
  (collective intelligence > individual estimates — the basic Surowiecki
  result holds).
- BUT the crowd **systematically overestimated "big-6" clubs** (Arsenal,
  Chelsea, Liverpool, Man City, Man United, Tottenham) and **underestimated
  smaller/promoted clubs** — a quantifiable popularity/prestige bias baked
  into an otherwise well-calibrated aggregate.
- When benchmarked against betting markets, the crowd's edge largely
  disappeared — bookmakers had already priced in (and likely exploited) this
  popularity bias, similar to Levitt's mechanism.

**Optimism Bias in Fans and Sports Reporters** (PMC4564281).
Documents that fans (and even assigned beat reporters) show measurable
**optimism bias** about their own team's prospects — overestimating win
probability and underestimating loss probability relative to objective
benchmarks. This is a *direct identity effect*, distinct from the "big club"
prestige effect above — it specifically requires the forecaster to have an
affiliation/rooting interest in one of the two teams.

**Braun, S. & Kvasnicka, M. (2013), "National Sentiment and Economic
Behavior: Evidence from Online Betting on European Football,"** *Journal of
Sports Economics* / earlier IZA discussion paper.
Studies odds set by domestic bookmakers for matches involving the
bookmaker-country's own national team. Finds **systematic mispricing
consistent with bettors over-rating their own national team's chances**
(a "perception/loyalty bias"), and shows theoretically and empirically that
domestic bookmakers respond by **shading odds against the home nation** —
i.e., setting a price that is *less generous to the home team* than a neutral
forecaster would, precisely because they know their customer base will
over-bet the home team regardless. The paper frames this as exploitable both
directions: the public's bias creates the gap, and the bookmaker's shaded line
is itself evidence of the bias's magnitude (you can back out the bias by
comparing the shaded domestic line to a neutral/sharp consensus line from
markets without that national skew).

**Home Bias in Sport Betting: Evidence from the Czech Betting Market**
(Štěpán, *Judgment and Decision Making*, ~2017; Cambridge Core / SJDM).
Using Czech ice-hockey betting data (chosen because the Czech national team is
extremely popular domestically and plays ~30 matches/season — lots of
observations), finds bettors are **willing to accept worse odds to bet on
their home/national team**, consistent with an optimism-driven home bias. The
mechanism proposed is the same optimism bias documented in the fan-forecast
literature above.

**Synthesis for SportsPredict / Korea case**: All four of these strands point
the same direction and are mutually reinforcing:
1. Fans of team X are optimistic about team X (PMC4564281, Czech study).
2. This optimism is *priced into* domestic betting markets and bookmakers
   shade against it (Braun & Kvasnicka).
3. Popularity/prestige (independent of nationality) also biases crowds toward
   "famous" teams (Goal-line Oracles — big-6 clubs).
4. A self-selected crowd (only people who chose to predict this market) will
   over-represent the population most affected by (1) and (3) — i.e., Korean
   users disproportionately predicting the Korea match (§2).
 
The SK-vs-Czechia gap (crowd 51% vs sharp-market 37% for SK win, ~14 pts) is
entirely consistent with the *magnitude* of biases reported in these papers
for high-salience domestic-team matches — domestic-bookmaker shading in the
Braun & Kvasnicka study and related literature on national-team odds
mispricing is commonly cited in the high-single-digit to ~15-percentage-point
range for marquee national-team fixtures, though exact magnitudes vary by
study/market/sport.

---

## 5. Practical, Buildable Proxies for "Crowd Composition / Bias"

Translating the above into observable, low-cost signals we can compute *before*
a match:

1. **Google Trends relative search interest** — for each team's country
   (and/or team name as a search term), pull Trends data in the days
   leading up to the match. The *ratio* of search interest between the two
   countries is a proxy for **relative fanbase engagement/awareness**, which
   plausibly correlates with the relative size of each team's "fan bloc" within
   SportsPredict's user pool (assuming SportsPredict's userbase composition
   roughly tracks global football interest patterns, possibly skewed toward
   whichever region the platform is most popular in — worth checking
   SportsPredict's own marketing/App Store country rankings if available).

2. **Social media mention volume / sentiment** (X/Twitter, Reddit r/soccer
   and country-specific subreddits, YouTube highlight view counts for recent
   matches) — a higher-frequency, more "in the moment" signal than Trends;
   spikes around team news (e.g. a star player's injury/return) can shift
   crowd sentiment fast in ways that lag in slower-moving sharp markets.

3. **Host-nation / regional-confederation effects** — for 2026 (US/Mexico/Canada
   co-hosts), host-nation matches will draw outsized attention regardless of
   team strength. Historical base rate: hosts have won 6/23 World Cups (~26%)
   — substantially above their average pre-tournament odds — suggesting a
   *partially real* host effect that markets under-price, compounding with
   a *crowd* effect that likely over-prices it even further. Both the true
   probability AND the crowd's probability may shift toward the host, but by
   different amounts — the gap between the two shifts is the exploitable part.

4. **Kickoff time-zone / "who's awake to vote" effects** — SportsPredict
   submissions presumably accumulate over the days before a match closes, but
   if there's any recency-weighting or if late submissions are more numerous
   near kickoff, the *time-zone-adjusted* kickoff hour for each team's home
   country matters. A match kicking off at a convenient evening hour in Korea
   but the middle of the night in the opponent's country could mean Korean
   users are disproportionately represented in the final crowd consensus.

5. **Squad "star power" / FIFA ranking of marquee players** — proxies:
   transfer-market value of the squad (Transfermarkt aggregate market value,
   already likely in our data pipeline per `alt_data_sources.md`), presence of
   globally-recognized superstars (Messi-tier name recognition), and recent
   highlight/viral-moment activity. A team with a disproportionately famous
   *individual* (even on an otherwise middling team) may draw crowd attention
   and optimism beyond what the team's actual Elo/strength would predict —
   this is the generalized "big-6 club" effect from Goal-line Oracles applied
   to international squads.

6. **SportsPredict's own historical settled-market data** (the best signal of
   all, growing over time): for every settled match, we now have (our true
   estimate, external-market estimate, in-house crowd's revealed consensus,
   actual outcome). After a handful of matches, we can directly regress
   `crowd_consensus - external_market_consensus` against the team-level
   features above (Trends ratio, host-nation flag, star-power index,
   confederation) to fit our own bias-correction model empirically, rather
   than relying purely on outside literature. **This is the single highest-value
   data asset we should be building from match 1 onward** — log every
   settled market's revealed crowd number alongside our pre-match feature
   vector.

---

## 6. "Beat-the-Crowd" Relative Scoring Rules — Formal Treatment

We did not find a paper specifically modeling "Brier score relative to a
revealed-after-the-fact crowd consensus" as its own object of study, but the
adjacent literature on **relative/zero-sum scoring in forecasting platforms**
is directly informative:

- **"Alignment Problems with Current Forecasting Platforms"** (arXiv
  2106.11248) and the related Effective Altruism Forum discussion ("Incentive
  Problems With Current Forecasting Competitions") analyze platforms (like
  Metaculus) where part of your score is *relative to the community
  prediction*. Their key finding: **relative scoring creates an incentive to
  converge toward (or strategically diverge from) the community prediction
  depending on your confidence about your edge** — specifically, "a forecaster
  seeking to optimize her relative score should predict the average community
  forecast … even if she doesn't know anything about the question" as a
  baseline, and should only deviate when she has a genuine information
  advantage over the community.

- **Joint/zero-sum scoring rules** (arXiv 2412.20732, "Joint Scoring Rules:
  Zero-Sum Competition Avoids Performative Prediction," 2024) formalizes the
  idea that under zero-sum/relative scoring, the *only* way to gain is to be
  closer to the truth than your opponent (the "crowd," in our case) — which
  means **your optimal forecast is a function of both (a) your estimate of the
  truth and (b) your estimate of your opponent's forecast**, not just (a) alone.

### Math sketch (our own derivation, building on standard Brier-score theory)

Let `p_true` = true probability of the event, `p_us` = our submitted
probability, `p_crowd` = SportsPredict crowd's consensus. Our score (ignoring
the scale constant) is:

```
RBP ∝ (p_crowd - outcome)^2 - (p_us - outcome)^2
```

In expectation over the true distribution (Brier score's standard
decomposition), `E[(p - outcome)^2] = (p - p_true)^2 + p_true(1-p_true)`. The
variance term `p_true(1-p_true)` is identical for us and the crowd, so:

```
E[RBP] ∝ (p_crowd - p_true)^2 - (p_us - p_true)^2
```

This says: **our expected relative score is maximized purely by minimizing
`(p_us - p_true)^2`** — i.e., under *certainty* about `p_true`, the standard
result holds and you should just report your true belief (`p_us = p_true`),
regardless of `p_crowd`. The crowd's bias doesn't change *your* optimal target
— it only changes *how much you're rewarded* for hitting it (a bigger
`p_crowd - p_true` gap means more available RBP for free, but doesn't change
where you should aim).

**However**, this assumes you *know* `p_true` exactly. In reality we have
uncertainty about `p_true` itself — call our belief distribution over
`p_true` as having mean `p_us*` (our best estimate) and we're choosing what to
*submit*, `p_submit`. If our uncertainty about `p_true` is large relative to
our information about the crowd's bias, the standard proper-scoring-rule
result (submit your best estimate, `p_submit = p_us*`) still dominates —
**deviating toward "anti-crowd" only helps if you have genuine information
about `p_crowd` that's independent of (and more certain than) your information
about `p_true`.**

**The case where deviation IS justified**: if (1) `p_crowd` is *revealed to
correlate with* `p_true` in a *predictable, biased* way — e.g., the crowd
systematically overshoots in the direction of the home/popular team by a
roughly consistent amount `b` for matches with feature X — and (2) this gives
you *additional information about `p_true` itself* (not just about
`p_crowd`), then the correct move is to **update your estimate of `p_true`**
using that information (e.g., if the crowd is consistently 14pts too high on
Korea-salience matches, and you'd otherwise have weighted the in-house crowd's
revealed number as one input to your blended estimate — but we don't get that
number pre-match, so this is moot for `p_true` estimation).

The place where genuine "deviate from `p_us*` toward anti-crowd" logic
*can* be justified is narrower: **only if `p_us*` itself was partly
*derived from* a signal that's correlated with the crowd's bias-inducing
information** (e.g., if our external-market proxy is ALSO contaminated by a
milder version of the same popularity bias — plausible! Real-money markets
aren't immune to fan money either, just less so) — in which case correcting
our OWN estimate for that contamination is just... improving our true-probability
estimate, which is what we should do regardless of the scoring rule.

**Bottom line**: the formally "clean" advice is **don't deliberately submit
something you believe is further from the truth than your honest estimate,
purely to anti-correlate with an expected crowd error** — that's a pure
zero-expected-value gamble on your bias-direction estimate being right, with
asymmetric downside if you're wrong (you've now made your own Brier score
worse AND given up the chance the crowd was right). The *correct* exploitation
of crowd bias is entirely on the **information side**: use everything we know
about crowd bias to (a) decide which markets are worth our limited
attention/conviction (markets where we expect a large `|p_crowd - p_true|` gap
are where the *available* RBP is largest, even if our own edge is the same
percentage-point size in absolute terms — recall `E[RBP] ∝ (p_crowd-p_true)^2 -
(p_us-p_true)^2`, so a bigger crowd error directly inflates our expected score
for the *same* quality of our own estimate), and (b) sanity-check whether our
`p_true` estimate itself has been contaminated by the same bias the crowd has
(in which case fix `p_true`, don't "anti-crowd" on top of an uncorrected
estimate).

---

## 7. Proposed Concrete Next Steps for Our Pipeline

1. **Build a "settled-markets ledger" immediately** (highest priority, lowest
   cost): for every SportsPredict market that settles, scrape/record
   `(market_id, our_pre-match_estimate, external_market_consensus_pre-match,
   sportspredict_crowd_consensus_post-settlement, actual_outcome,
   team_a, team_b, market_type, kickoff_datetime_utc)`. This is the raw
   training data for an empirical crowd-bias model and currently we likely
   have only n=1 (SK vs Czechia) recorded informally — formalize this now,
   per the user's "write to disk immediately" principle (do NOT accumulate in
   memory between matches).

2. **Compute a per-match "Crowd Bias Score" (CBS) from Google Trends +
   confederation/host flags**, pre-match, for every market:
   - Pull 7-day Google Trends search-interest index for each team's
     country (or "[Country] national team" / "[Country] vs [Opponent]"
     query), normalized.
   - `CBS_raw = trends_ratio(team_A / team_B)` — a >1 value suggests team A's
     fanbase is more "switched on" for this fixture.
   - Add a host-nation indicator (+1 for US/Mexico/Canada in 2026) and a
     squad star-power differential (e.g. Transfermarkt squad value
     differential, or count of players in the global top-50 by market value).
   - Combine into a single score that predicts the *direction and rough
     magnitude* of `p_crowd - p_true_consensus` — fit this empirically once
     we have ~5-10 settled markets from item 1; until then, use it
     qualitatively to FLAG markets where we expect a large gap (high |CBS|).

3. **Prioritize attention/conviction on high-|CBS| markets**, since
   `E[RBP] ∝ (p_crowd - p_true)^2 - (p_us - p_true)^2` — markets where we expect
   the crowd to be most wrong are where the *most RBP is on the table*,
   independent of how good our own model is in absolute terms. Concretely:
   marquee matches involving a single nation with a large, enthusiastic,
   plausibly-overrepresented-on-SportsPredict fanbase (we should try to learn
   SportsPredict's actual user-geography mix if at all possible — even
   indirectly, e.g. via App Store country rankings, language of in-app UI/social
   posts, etc.) are exactly where Korea-vs-Czechia-style gaps will recur.

4. **Run a contamination check on our external-market proxy itself**: for the
   SK-vs-Czechia match-winner market, investigate whether the ~37% figure from
   Kalshi/Polymarket/Smarkets/offshore books *itself* showed any signs of
   "soft money" influence (e.g., did Polymarket's volume/liquidity on this
   market look unusually retail-heavy vs a typical match?). If our external
   proxy is occasionally susceptible to the same (milder) fan-money
   contamination, that's a `p_true`-estimation problem to fix directly (e.g.,
   weight Smarkets/sharp-exchange odds more heavily than Polymarket retail
   flow for marquee-nation matchups), per §6's conclusion that bias-correction
   belongs in the true-probability estimate, not as a bolt-on "anti-crowd"
   adjustment.

5. **Do NOT implement a deliberate "submit something other than our best
   estimate" anti-crowd strategy** based on CBS alone (per §6's formal
   argument) — UNLESS/UNTIL we've validated, from the settled-markets ledger
   (item 1), that CBS reliably predicts `p_crowd - p_true` with a magnitude and
   confidence that would make a *small, bounded* tilt unambiguously
   +EV even after accounting for the risk that our own `p_true` estimate is
   wrong in the same direction as the (uncorrected) crowd. If/when we have that
   validation (say after 10-15 settled high-|CBS| markets), a reasonable
   implementation is a capped tilt: `p_submit = p_us* + alpha * sign(-CBS) *
   min(|CBS_implied_bias|, cap)`, with `alpha` and `cap` calibrated from
   the ledger's realized RBP improvement, reviewed/refit after every
   tournament stage.

---

## Sources Cited

- Snowberg, E. & Wolfers, J. (2010). "Explaining the Favorite-Longshot Bias: Is
  it Risk-Love or Misperceptions?" *Journal of Political Economy*, 118(4).
  [JPE abstract](https://www.journals.uchicago.edu/doi/abs/10.1086/655844) /
  [NBER WP 15923](https://www.nber.org/system/files/working_papers/w15923/w15923.pdf)
- Green, E.A., Lee, H. & Rothschild, D. "The Favorite-Longshot Midas."
  [Wharton/Jacobs Levy working paper](https://jacobslevycenter.wharton.upenn.edu/wp-content/uploads/2018/08/The-Favorite-Longshot-Midas.pdf)
- Levitt, S.D. (2004). "Why Are Gambling Markets Organised So Differently from
  Financial Markets?" *Economic Journal*, 114(495).
  [PDF](http://pricetheory.uchicago.edu/levitt/Papers/LevittWhyAreGamblingMarkets2004.pdf)
- Surowiecki, J. (2004). *The Wisdom of Crowds*. [Wikipedia overview](https://en.wikipedia.org/wiki/The_Wisdom_of_Crowds)
- Prelec, D., Seung, H.S. & McCoy, J. (2017). "A Solution to the Single-Question
  Crowd Wisdom Problem." *Nature*, 541, 532–535.
  [Nature article](https://www.nature.com/articles/nature21054)
- Prelec, D. (2004). "A Bayesian Truth Serum for Subjective Data." *Science*.
  [MIT Sloan summary](https://nel.mit.edu/bayesian-truth-serum/)
- "Machine Truth Serum: A Surprisingly Popular Approach to Improving Ensemble
  Methods" (2022). *Machine Learning* (Springer).
  [Article](https://link.springer.com/article/10.1007/s10994-022-06183-y)
- "Goal-line oracles: Exploring accuracy of wisdom of the crowd for football
  predictions" (2025). *PLOS ONE*.
  [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0312487) /
  [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11785260/) /
  [LSE eprint](https://eprints.lse.ac.uk/127328/) /
  [LSE blog summary](https://blogs.lse.ac.uk/europpblog/2025/05/29/football-forecasting-harnessing-the-power-of-the-crowd/)
- "Optimism Bias in Fans and Sports Reporters."
  [PMC4564281](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4564281/)
- Braun, S. & Kvasnicka, M. (2013). "National Sentiment and Economic Behavior:
  Evidence from Online Betting on European Football." *Journal of Sports
  Economics* (also IZA/EconStor discussion paper).
  [EconStor PDF](https://www.econstor.eu/bitstream/10419/123709/1/Kvasnicka_2013_National%20Sentiment%20and%20Economic%20Behavior.pdf) /
  [SAGE journal](https://journals.sagepub.com/doi/10.1177/1527002511414718)
- "Home Bias in Sport Betting: Evidence from Czech Betting Market."
  *Judgment and Decision Making*.
  [SJDM](https://sjdm.org/~baron/journal/16/16824/jdm16824.html) /
  [Cambridge Core](https://www.cambridge.org/core/journals/judgment-and-decision-making/article/home-bias-in-sport-betting-evidence-from-czech-betting-market/AF3B2DAC6A17EDED1CEBB22F4049A6AF)
- "Alignment Problems With Current Forecasting Platforms" (2021). arXiv:2106.11248.
  [arXiv](https://arxiv.org/pdf/2106.11248) /
  [EA Forum discussion](https://forum.effectivealtruism.org/posts/ztmBA8v6KvGChxw92/incentive-problems-with-current-forecasting-competitions)
- "Joint Scoring Rules: Zero-Sum Competition Avoids Performative Prediction"
  (2024). arXiv:2412.20732.
  [arXiv](https://arxiv.org/html/2412.20732)
- "Wisdom of the Crowds Forecasting the 2018 FIFA Men's World Cup." arXiv:2008.13005.
  [arXiv PDF](https://arxiv.org/pdf/2008.13005)
- FocusEconomics, "Can the Wisdom of the Crowds Predict the Results of the 2018
  World Cup?" [Blog](https://www.focus-economics.com/blog/can-wisdom-of-the-crowds-predict-results-2018-world-cup/)
- VegasInsider, "World Cup Odds History: How Past Tournaments Shaped Betting
  Markets" (host-nation win-rate context).
  [Article](https://www.vegasinsider.com/soccer/world-cup-odds-history-and-how-they-shape-markets/)
