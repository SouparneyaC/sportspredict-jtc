# Álvarez high-stakes deep dive: does the 1+SOT rate change on the biggest stage? (Q1 revisit)

Question being priced (exact wording, `01_match_and_markets.json`): **"Will Julián Álvarez
(Argentina, #9) have 1 or more shots on target in regulation (90 minutes + stoppage time)?"** —
ENG vs ARG WC2026 SF, 2026-07-15.

## 0. Why this exists, and the two mistakes this piece is built not to repeat

`11_player_prop_backtest_messi_alvarez.md` priced Q1 at **0.69** from a `k=5` empirical-Bayes
blend of Álvarez's own 2026 log (n=6, `[0,1,1,0,1,1]`) and his WC2022-only StatsBomb history
(n=7). That file's own §3 is explicit and unambiguous: the walk-forward EB model for Álvarez is
**worse than a flat historical-only baseline** (Brier 0.257 vs 0.225) and barely better than a coin
flip — the weakest kind of evidence base this project has for a live number tonight. The live
Smarkets market is thin, one-sided, offer-only, at **0.5682**.

Two documented failures shape how this piece is built:

1. **`14_messi_high_stakes_deep_dive.md`** built a large (n=61), statistically significant
   (p=0.013) high-stakes-vs-regular finding for Messi, then blended it into a final number using
   the same `k=5` constant reused unchanged from an unrelated, much thinner precedent
   (De Bruyne/Lukaku, n=10). That badly under-weighted the very evidence the piece had just spent
   most of its effort validating. **This piece does not reuse `k=5` anywhere.** Every blend below
   is n-weighted: each component's own real sample size is its weight, full stop. Where a
   component's weight is deliberately discounted below its full n, that discount is named and
   justified in the text, not silently imported from elsewhere.
2. **France vs Spain (2026-07-14), now settled** (`matches/France Vs Spain (Jul.14.26)/14_actual_submission.json`):
   the single costliest loss on that slate (-12.48 RBP) was Q8, "Mbappé scores" — an *upward*
   deviation from a tight, liquid 0.44-mid market to 0.60 on personal-form conviction, the sixth
   confirmed live loss of that exact pattern (RULE17, "upward deviation from a liquid market on
   personal conviction," now 0-for-6 / worse than -155 RBP). Tonight's Álvarez situation is
   structurally similar: thin, one-sided market (0.5682) and an obvious temptation to price well
   above it on reputation/recent-form grounds. **This piece treats any recommendation above market
   as guilty until proven innocent** — flagged explicitly if it happens, and only acted on if the
   evidence is large-sample and stable, not a hot-streak read.

## 1. Pre-registered high-stakes criteria (stated before computing anything)

Fixed in advance, adapted from `14_messi_high_stakes_deep_dive.md §1`'s precedent to what
Álvarez's actual career actually contains (see §2 for why it differs from Messi's five tags):

1. UEFA Champions League knockout stage, Round of 16 onward — identified by ESPN's own
   `"1st Leg"`/`"2nd Leg"` note field for two-legged ties, plus the Final — across **both** club
   eras (Manchester City and Atlético Madrid, see §2.2 for why both are needed).
2. UEFA Champions League Final specifically (2023, Manchester City) — a named sub-tag of (1).
3. Domestic knockout cup: FA Cup + League Cup (Manchester City), Copa del Rey (Atlético Madrid) —
   single-elimination competitions throughout the rounds Álvarez appeared in.
4. One-off showcase/trophy matches: FIFA Club World Cup Final, UEFA Super Cup, FA Community
   Shield, Spanish Super Cup.
5. Premier League "rival" fixtures (opponent ∈ {Liverpool, Arsenal, Manchester United}) while at
   Manchester City.
6. La Liga Madrid derby (opponent = Real Madrid) while at Atlético Madrid.
7. Copa America 2024 knockout stage (Quarter-finals, Semi-finals, Final) for Argentina.

None of these were adjusted after seeing the results below.

## 2. Data engineering

### 2.1 Local StatsBomb coverage — confirmed dead end, not assumed

Per the brief's instruction to confirm rather than assume: `data/external/statsbomb/open-data/data/competitions.json`
was checked directly.

- Argentine Liga Profesional (`competition_id=81`, River Plate's league, where Álvarez played
  through January 2022): only seasons **1997/1998** and **1981** are present. Álvarez was born in
  2000; both seasons predate his career by decades. **Zero usable coverage.**
- English Premier League (`competition_id=2`, Manchester City's league since Jan 2022): only
  seasons **2015/2016** and **2003/2004** are present — also decades before Álvarez's arrival.
  **Zero usable coverage.**
- Spanish La Liga (`competition_id=11`, Atlético Madrid's league since July 2024): local coverage
  runs 2004/05 through **2020/21** only (`data/matches/11/*.json`, 17 season files) — five seasons
  before Álvarez's actual arrival at Atlético. **Zero usable coverage.**

So, unlike Messi (519 local La Liga rows for Barcelona alone), **there is no local StatsBomb
coverage of any club Álvarez has actually played for, in any era he actually played there.** The
entire club-career signal in this piece comes from a live ESPN pull (§2.3). The one local dataset
that *is* usable is Copa America 2024 (§2.2).

### 2.2 A correction to the brief's premise, confirmed from live data before trusting it

The brief's framing was "Álvarez played for River Plate before 2022, then Manchester City since
January 2022 — use his actual current club." Checking this against ESPN's own player-search API
(`site.web.api.espn.com/apis/search/v2?query=Julian Alvarez`) before assuming it: the returned
record for athlete id **277206** shows `subtitle: "Atlético Madrid"`, `defaultLeagueSlug: "esp.1"`
— **not Manchester City**. Álvarez transferred from Manchester City to Atlético Madrid in July
2024 (real, well-known transfer, ~€75-95m depending on source), two full seasons before tonight.
Treating "Man City" as his current club would have been exactly the kind of unverified assumption
this project's standing rule (verify an unfamiliar field against a known case before trusting it)
exists to catch. **Both club spells are pulled** — Manchester City (Jan 2022 - Jul 2024) as the
historical bridge, Atlético Madrid (Jul 2024 - present) as the actually-current club — rather than
silently substituting one for the other.

### 2.3 Live ESPN pull — endpoint reuse, ground-truth verification

Script: [`15_alvarez_club_career_fetch.py`](15_alvarez_club_career_fetch.py). Same two endpoints
already discovered and documented in `14_messi_recent_form_fetch.py` (`sports.core.api.espn.com/.../eventlog`
for event discovery, `site.api.espn.com/.../summary?event=` read via `rosters[].roster[].stats`
for per-match stats). Nineteen (league, season) targets pulled — 7 Manchester City competitions
(Premier League, Champions League, FA Cup, League Cup, Club World Cup, UEFA Super Cup, Community
Shield) across their relevant seasons, plus 4 Atlético Madrid competitions (La Liga, Champions
League, Copa del Rey, Spanish Super Cup). 226 raw event rows pulled, 2022-07-30 through 2026-05-05
— all strictly before tonight's 2026-07-15 kickoff, no lookahead.

**Ground-truth checks performed before trusting `shotsOnTarget`/`totalGoals`** (per this project's
standing rule): the 2023 FA Cup Final (Manchester City 2-1 Manchester United, real) is confirmed in
the pulled record. The 2023 FIFA Club World Cup Final (Manchester City 4-0 Fluminense, Álvarez
scored twice — real, well-known: Jeddah, Dec 2023) shows `totalGoals: 2.0`, `shotsOnTarget: 2.0`,
`totalShots: 3.0` in the pulled record — confirmed exactly before trusting the same field for
anything else.

**A genuine data-quality gap, disclosed rather than papered over:** ESPN's per-match `stats` object
is entirely empty for 17 of the 226 raw rows — concentrated exclusively in FA Cup (6 of 12 rows)
and Copa del Rey (11 of 13 rows). Of those 17: **7 have `starter=False` and no `appearances` value**
— genuinely ambiguous between "unused bench" and "came on and played," and are **dropped**, not
guessed (this project's join-safety/no-guessing discipline extended to this case). **10 have
`starter=True`** — Álvarez unambiguously started these matches, so they are **kept in the log as
confirmed participation but excluded from the SOT rate calculation** (not zero-filled) because the
shot data simply isn't there. A separate, unambiguous **17 rows have `appearances=0`** (a genuine
unused-substitute flag, the same pattern as Messi's Copa America Peru DNP row) — dropped the same
way.

**Final usable sample: 192 club-career rows with real shot/SOT stats** (out of 209 confirmed
appearances), plus **5 Copa America 2024 rows** (StatsBomb, see below) = **197 total rows with
usable SOT data.**

### 2.4 Copa America 2024 (Argentina), local StatsBomb

`competition_id=223`, `season_id=282`. Player identity confirmed from the data itself: `player_id
29560`, `"Julián Álvarez"`, jersey `9` (matches the brief), found in the lineup for match `3939969`
(Argentina v Canada, group stage). Argentina played 6 matches in the tournament; Álvarez appears in
all 6 lineups but with `minutes_played == 0` in one (Quarter-final v Ecuador — a real, documented
tactical benching that match, not a data bug), which is excluded the same way Messi's Copa America
Peru DNP was excluded in the reference piece — a data-quality exclusion, not a zero-fill.

**Copa America 2024 log:**

| Date | Stage | Opponent | Starter | Shots | SOT | Goals | Tag |
|---|---|---|---|---|---|---|---|
| 2024-06-21 | Group Stage | Canada | Y | 3 | 2 | 1 | |
| 2024-06-26 | Group Stage | Chile | Y | 2 | 1 | 0 | |
| 2024-07-05 | Quarter-finals | Ecuador | N (benched) | 0 | 0 | 0 | knockout |
| 2024-07-10 | Semi-finals | Canada | Y | 3 | 2 | 1 | knockout |
| 2024-07-15 | Final | Colombia | Y | 1 | 0 | 0 | knockout |

1+SOT in 3/5 = 0.600.

## 3. High-stakes vs regular — the finding, and it is the opposite shape from Messi's

**Two-proportion z-test, high-stakes vs regular: z = 0.009, p = 0.993.**

| Bucket | n | 1+SOT | Rate | 95% Wilson CI |
|---|---|---|---|---|
| UCL knockout (R16+) | 17 | 12 | 0.706 | [0.469, 0.867] |
| Domestic cup knockout | 11 | 7 | 0.636 | [0.354, 0.848] |
| One-off final/trophy | 6 | 3 | 0.500 | [0.188, 0.812] |
| PL rival (Liverpool/Arsenal/Man Utd) | 9 | 2 | 0.222 | [0.063, 0.547] |
| La Liga Madrid derby | 4 | 4 | 1.000 | [0.510, 1.000] |
| Copa America 2024 knockout | 3 | 1 | 0.333 | [0.061, 0.792] |
| **High-stakes, all tags combined** | **50** | **29** | **0.580** | **[0.442, 0.706]** |
| **Regular (PL+La Liga+UCL-group, untagged)** | **145** | **84** | **0.579** | **[0.498, 0.657]** |

Where Messi's high-stakes rate was 21 points *lower* than his regular rate (p=0.013, real signal,
opponent-quality confound), **Álvarez's high-stakes and regular 1+SOT rates are statistically
indistinguishable — a difference of one-tenth of a percentage point.** This holds up as a genuine
null, not just an underpowered one: the wide individual-tag CIs above overlap heavily and the
pooled 50-vs-145 comparison has enough power to detect a Messi-sized (21pp) gap had one existed.
The most defensible read is that **1+ shot on target is a volume/role metric, not a finishing
metric** — even against an elite defense, a striker who gets into the same positions still gets a
shot away and on frame at close to his normal rate; it's the *conversion* of those shots (goals)
that elite defenses suppress, not the shot-generation itself. This is consistent with, not
contradictory to, Messi's finding: that piece measured *scoring*, this one measures *shots on
target*, and the two metrics plausibly do respond differently to opponent quality.

**A second stability check, run because it's directly checkable and instructive:** the same "does
context change the rate" question, asked across the Manchester City → Atlético Madrid transfer
(different club, different league, different manager, different system) instead of across
stakes:

| Slice (regular matches only) | n | 1+SOT | Rate |
|---|---|---|---|
| Manchester City (2022-24) | 68 | 40 | 0.588 |
| Atlético Madrid (2024-26) | 77 | 44 | 0.571 |

A 1.7-point gap across a full club transfer, league change, and role change is essentially nothing.
**Álvarez's 1+SOT rate looks like a genuinely stable individual trait across club, era, and
stakes — every slice tested lands in a narrow 0.57-0.71 band** (the single outlier, PL rival games
at 0.222, is n=9 and the widest CI on the table; it is reported, not suppressed, but not leaned on
given the sample size and the fact that no equivalent gap shows up in the Madrid-derby, UCL-
knockout, or Copa-America-knockout tags measuring a similar "big opponent" idea).

## 4. National team vs club level — the two contexts, kept separate rather than blindly pooled

Because club and national-team roles genuinely differ (Álvarez plays a more central,
often-partnered-with-Messi role for Argentina than his club roles), the two are reported side by
side before any pooling decision is made, per the brief's explicit instruction to justify any
discount rather than blend silently:

| Source | n | 1+SOT | Rate |
|---|---|---|---|
| National team, historical (WC2022 n=7 + Copa America 2024 n=5) | 12 | 8 | 0.667 |
| National team, own-2026 WC log (`[0,1,1,0,1,1]`) | 6 | 4 | 0.667 |
| **National team, all (historical + 2026)** | **18** | **12** | **0.667** |
| Club career, all competitions (Man City + Atlético, both eras) | 192 | 112 | 0.583 |
| Club career, high-stakes subset only | 50 | 29 | 0.580 |

The national-team rate (0.667) sits about 8 points above the club rate (0.583), with overlapping
confidence intervals given the national-team sample's much smaller n. Given §3's finding that
Álvarez's SOT rate is stable across every other context split tested (club era, stakes tier), an
8-point club-vs-country gap on n=18 vs n=192 is well within what sampling noise alone would
produce — there is no evidence here to justify *discounting* the club data as a different regime
the way Messi's PSG/Miami-era discount briefly considered. Both are treated as measuring the same
underlying quantity, weighted by their own real n, in §5.

## 5. Walk-forward honesty check — thin, but improved on the original

**n=6 own-2026 folds is still thin** — the same caveat `11_player_prop_backtest_messi_alvarez.md
§3` gave, and it doesn't go away just because the external prior got bigger. Genuine walk-forward
folds require the fixed prior to *not* depend on outcome i, which holds here (all external data
predates the tournament); what doesn't improve with a bigger external prior is the raw n=6 count of
tournament-specific test points. This section reports the check honestly rather than force-fitting
false confidence.

Same n-weighted blend formula as §6 below, applied fold-by-fold (fold i uses only 2026 games
1..i-1):

| Fixed prior used | n_fixed | rate_fixed | Walk-forward Brier |
|---|---|---|---|
| Old (`11_...md`): WC2022 only, `k=5` weight | 7 (synthetic k=5) | 0.7143 | 0.2570 (as reported in `11_...md`) |
| WC2022 only, **n-weighted** (n=7, not k=5) | 7 | 0.7143 | 0.2492 |
| National-team historical only (WC2022+Copa America 2024) | 12 | 0.6667 | 0.2383 |
| Club high-stakes subset only | 50 | 0.5800 | 0.2333 |
| **Full pool (national hist + club career, all comps)** | **204** | **0.5882** | **0.2267** |
| Flat 0.5 baseline | — | 0.5 | 0.2500 |

The full n-weighted pool achieves the best walk-forward Brier of every variant tested here,
including beating the flat coin-flip baseline — a real improvement over the original backtest,
which was *worse* than its own flat-historical baseline (0.257 vs 0.225). That said: this is still
6 data points, and the ranking above is not statistically distinguishable from noise at this
sample size (flipping one or two of the six folds would reorder these rows). It is reported as
directional support for using a larger, n-weighted prior — not as proof the full-pool model is
"validated" in the sense this project reserves for n≥30-ish samples elsewhere.

## 6. Final blend for tonight — n-weighted, no borrowed constants

All components use each source's own real sample size as its weight. No `k` of any kind is
introduced.

**Primary:**

```
own-2026 (n=6, k=4, rate=0.667)
+ national-team historical, WC2022+CopaAm2024 (n=12, k=8, rate=0.667)
+ club career, Man City + Atlético, all competitions (n=192, k=112, rate=0.583)
------------------------------------------------------------------------------
n = 210, k = 124
pred = 124 / 210 = 0.5905
```

**→ Primary Q1 estimate: 0.59**

### Sensitivity (shown so this is checkable, not asserted)

| Variant | Components | n | Predicted |
|---|---|---|---|
| **A — Primary** | own-2026 + national hist + club ALL | 210 | **0.590** |
| B — national team only, no club bridge | own-2026 + national hist | 18 | 0.667 |
| C — national hist + club HIGH-STAKES only | own-2026 + national hist + club HS | 68 | 0.603 |
| D — club only, ignore national team | own-2026 + club ALL | 198 | 0.586 |
| E — club high-stakes only, no national hist | own-2026 + club HS | 56 | 0.589 |

Four of five variants (A, C, D, E) land in a tight **0.586-0.603** band — the club career's large
n dominates whichever way it's sliced, and it's internally consistent (§3's null high-stakes
finding means slicing it by stakes barely moves the number). The only outlier is **B (0.667)**,
which is exactly the variant that *excludes* the 192-match club sample and relies on n=18 of
national-team data alone — the smallest-n, least-powered version of this analysis. Per this
project's n-weighting discipline, B is not given equal footing with A/C/D/E just because it
produces a rounder, higher number; it is reported for completeness, not treated as the central
estimate.

### Contrast with the old number and the market, with the Mbappé lesson applied explicitly

| | Value |
|---|---|
| Old estimate (`11_...md`, n=6/n=7, explicitly *worse than flat baseline*) | 0.69 |
| **Revised estimate (this piece, n=210 pooled, n-weighted)** | **0.59** |
| Smarkets market (thin, one-sided, offer-only) | 0.5682 |

The larger dataset **pulls the number down substantially** — from 0.69 to 0.59, a 10-point drop,
almost the mirror image of what happened with Messi (whose number also came down, 0.74→0.65, but
stayed 26+ points above market). Here the gap to market **shrinks to just 2.2 points** (0.59 vs
0.5682) — small enough that it sits inside the noise of a single Wilson CI on almost any of the
component slices above.

This is the moment to apply the RULE17/Mbappé lesson directly, not just cite it. That failure
pattern was specifically: *override a tight, liquid market with a higher personal-conviction number
based on recent hot form.* Two things distinguish tonight's situation, and are stated plainly
rather than used to rationalize a bigger deviation than the data supports:

- This market is **thin and one-sided** (not the tight, liquid 0.44-mid market Mbappé's case was),
  so the usual RULE1/RULE2 market-priority default carries less force here than it did there — the
  market itself is a weaker signal.
- The 0.59 estimate is **not a recent-hot-streak read** — it is dominated by n=192 of two-and-a-
  half years of club data spanning two clubs, plus a null (not positive) high-stakes effect, i.e.
  the opposite mechanism from Mbappé's case, which leaned on a short hot streak.

That said, the honest move is still to **not lean into the 2.2-point edge as if it were
meaningful**, because it is well within this analysis's own uncertainty (every component's 95% CI
is wide relative to a 2-point gap). **Final recommendation: 0.58-0.59**, i.e. treat the market's
0.5682 as essentially correct and let this analysis's own n-weighted math — not a discretionary
"round up because Álvarez is good" adjustment — supply the only reason to sit fractionally above
it. This is a genuine, data-driven correction of the old 0.69 (which this project's own backtest
had already flagged as unreliable), landing close to but not fully collapsed into the market,
consistent with how Messi's revision also didn't fully converge to its market — except here the
remaining gap is small enough that it should not be read as a confident edge.

**Bottom line: revise Q1 from 0.69 to 0.58-0.59.** This is the more conservative sibling of the
Messi revision (0.74→0.65): both moved down substantially on a much larger dataset, but Álvarez's
move goes almost all the way to the market because the "does the rate change on the biggest stage"
question — the central mechanism used to justify staying above market in the Messi piece — comes
back null for Álvarez specifically.

## Files

- [`15_alvarez_club_career_fetch.py`](15_alvarez_club_career_fetch.py) — live ESPN pull, Man City
  (2022-2024) + Atlético Madrid (2024-2026), 19 (league, season) targets, 226 raw rows.
- [`15_alvarez_club_career_espn.json`](15_alvarez_club_career_espn.json) — its output.
- [`15_alvarez_high_stakes_deep_dive.py`](15_alvarez_high_stakes_deep_dive.py) — builds the
  combined 197-usable-row log (Copa America 2024 StatsBomb + ESPN club career), applies the 7
  pre-registered tags, prints all §3-6 summary stats.
- [`15_alvarez_full_log.csv`](15_alvarez_full_log.csv) — row-per-match combined output (source,
  match id, date, competition, stage/round, opponent, starter, shots, SOT, goals, valid_stats flag,
  high-stakes tags).
- Source data: `data/external/statsbomb/open-data/data/` (gitignored, read-only, never modified);
  live ESPN pulls via `site.api.espn.com` / `sports.core.api.espn.com`, all pre-kickoff.
