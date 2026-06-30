# Granular Data Sources for the 597 Uncovered Jump Cup Markets (Corners, Cards, Offsides, Shots-on-Target, Half-Time Splits, Player Props)

**Scope**: This file extends `data/alt_data_sources.md` (which already identified FBref,
StatsBomb 2022, Kaggle WC2022, Transfermarkt, BALLDONTLIE, WhoScored as primary
candidates) and `data/alt_data_sources_research.md` (Elo-supplementary sources).
That earlier research correctly flagged FBref + StatsBomb 2022 as the strongest
leads but left several open questions — most importantly the **half-time/
per-period stat gap** and whether StatsBomb's free coverage extends beyond the
single 2022 World Cup. Both of those questions are now substantially resolved
below (StatsBomb does, and explicitly includes period/half info). This file
does NOT re-litigate FBref/StatsBomb-2022/BALLDONTLIE basics already covered —
it verifies, extends, and adds new sources (deeper Kaggle search, GitHub repos,
more APIs, Reddit, academic).

Research date: 2026-06-11. Today is the opening day of the 2026 World Cup.

---

## 1. Kaggle

### 1.1 Datasets re-confirmed from existing research (not re-described in depth)
- `die9origephit/fifa-world-cup-2022-complete-dataset` — per-match stats incl.
  cards, fouls, attempts (shots), offsides, crosses, possession for all 64
  2022 WC matches. Already cataloged.
- `hugomathien/soccer` (European Soccer Database) — club-only, 2008-2016.
  Already cataloged.

### 1.2 New finds

**`swaptr/fifa-world-cup-2022-player-data`** and companion
**`swaptr/fifa-world-cup-2022-match-data`** / **`swaptr/fifa-world-cup-2022-statistics`**
(by the same author, forming a linked set)
- **Granularity**: Player-level (per-tournament aggregates: goals, assists,
  minutes, cards) and match-level team stats.
- **Coverage**: 2022 WC only, all 32 teams / 64 matches.
- **Access**: Free CSV download, Kaggle account required.
- **Target markets**: Player props (cards, minutes-based sub probability) and
  team-level cards/fouls — but only as a **2022 prior/training sample**, not
  2026 data. Same caveat as the existing `die9origephit` dataset: useful for
  fitting an "Elo/squad-quality -> event-rate" regression, not for live 2026
  pricing.

**`lchikry/international-football-match-features-and-statistics`**
- **Granularity**: Claims 43k+ international matches with Elo, team-form
  features, AND some player-level data bundled in.
- **Coverage**: Broad international history (not WC-specific); needs
  spot-checking for whether "statistics" includes corners/cards/shots or is
  limited to results+form features (the listing emphasizes "for football
  prediction," suggesting it may be closer to a pre-built modeling dataset
  like our own `elo_match_panel.csv` rather than raw event stats).
- **Access**: Free, Kaggle.
- **Target markets**: Possibly useful as a cross-check/second Elo-like feature
  set (overlaps with item #2 in `alt_data_sources_research.md`, FIFA ranking),
  but unlikely to add new event-level (corners/cards/shots) signal — **low
  priority, needs verification before any integration effort**.

**`xfkzujqjvx97n/football-datasets` ("5.7M+ Records — Most Comprehensive
Football Dataset")**
- **Granularity**: Described as a full "data lake" — players, teams,
  transfers, performances, market values, injuries, AND national-team stats.
- **Coverage**: Very broad (5.7M+ records) but unverified depth — "performances"
  could mean match-level event stats or could mean season aggregates only.
- **Access**: Free, Kaggle.
- **Target markets**: Potentially high value if "performances" includes
  per-match shots/cards/corners for national teams, but this is a large,
  unvetted dataset — **needs a hands-on inspection pass (download + check
  schema) before relying on it**. Flag as a "big swing, verify first" candidate.

**`gokhanergul/football-match-statistics`** and **`kaito510/fifa-world-cup-match-stats`**
- Both club-league-heavy (the former: 18 leagues, ~100k rows, 91 columns,
  includes corner kicks, offsides, fouls, possession, distance covered — very
  rich schema but **club, not international**). The latter is WC-specific but
  needs a content check (likely overlaps with `die9origephit`).
- **Target markets**: `gokhanergul` is the richest **club-level schema** found
  in this search (91 columns incl. corners/offsides/fouls) — if the project
  pursues the "club-season rates as proxy for national-team player behavior"
  approach (per the task framing), this is a strong candidate for the
  **club-side half** of that proxy, complementing FBref player pages already
  identified. Needs schema verification (column names, date range, which 18
  leagues — European top-flight coverage is likely strongest).

### 1.3 Overall Kaggle assessment
No new Kaggle dataset materially beats the combination already identified
(FBref via scraping + StatsBomb 2022 + `die9origephit`/`swaptr` 2022 WC flat
files). Kaggle's WC-specific datasets are uniformly **2022-and-earlier,
match/tournament-aggregate level** — useful as **training priors** for
Elo-to-event-rate regressions (per `alt_data_sources.md` §a #2/#3) but
contribute nothing toward 2026 fixtures directly. The `gokhanergul` 91-column
club dataset and the unvetted `xfkzujqjvx97n` "data lake" are the two
highest-potential **unverified** leads if the team wants a second pass.

---

## 2. GitHub

### 2.1 StatsBomb open-data — MAJOR UPDATE vs. existing research

The existing `alt_data_sources.md` says StatsBomb open-data covers "only 2022
WC." **This is now out of date.** Live verification of
`github.com/statsbomb/open-data` (`data/competitions.json`, fetched directly,
2026-06-11) shows the free open-data competition list now includes, for
**men's** football:

| Competition | Season(s) | Relevance to 2026 WC squads |
|---|---|---|
| FIFA World Cup | 2022, 2018, 1990, 1986, 1974, 1970, 1962, 1958 | 2022/2018 = direct squad overlap with many 2026 qualifiers |
| UEFA Euro | 2024, 2020 | UEFA teams (12 of 48 2026 slots) — recent squads, high overlap |
| Copa America | 2024 | CONMEBOL teams (6 slots) — very recent, high overlap |
| African Cup of Nations | 2023 | CAF teams (9 slots) — very recent, high overlap |
| FIFA U20 World Cup | 1979 | Low relevance (historical, youth) |

**This is a substantially richer dataset than previously documented.** AFCON
2023 and Copa America 2024 in particular give **2024/2023-vintage full
event-level data for exactly the player pools likely to be in 2026 squads** —
much fresher than 2022 WC alone.

**Verified event schema** (pulled `data/events/3857276.json`, a 2022 WC
match, Canada vs Morocco):
- Shot events include a **`period` field** (1 = first half, 2 = second half,
  3/4/5 = extra time periods) directly on every event — meaning **shots,
  shots-on-target (via `shot.outcome`), corners (tagged as `pass.type =
  "Corner"`), fouls, and cards (via `foul_committed.card`) can ALL be split by
  half** with zero additional work. This **directly closes the "half-time
  splits" gap** flagged as the single biggest remaining problem in
  `alt_data_sources.md` (§a #1) — at least for the competitions/seasons
  StatsBomb covers.
- Confirmed in the sample match: 12 shot events (with period, xG, outcome,
  body part), 4 foul-committed events with card info, 8 corner-tagged passes.
- **Shots on target** = shots where `shot.outcome.name` is one of "Goal",
  "Saved", "Saved to Post" etc. (i.e., on-target outcomes) — directly
  derivable, per half.
- **Offsides**: StatsBomb tags an "Offside" event type — present in the schema
  (not explicitly checked in this sample match but is part of StatsBomb's
  standard event vocabulary).

**Access**: Free, no API key, JSON via raw GitHub URLs or `statsbombpy`
(Python). CC-style open license for non-commercial/research use per
StatsBomb's open-data terms (re-check exact license text in
`github.com/statsbomb/open-data/blob/master/LICENSE.pdf` before any
commercial framing — the Jump Cup context is a forecasting competition, likely
fine, but verify).

**Target markets**: This is now the **single best source** for training data
across **all six** target categories simultaneously (corners, cards, offsides,
shots on target, half-time splits, AND player-level events for props — every
event is tagged with `player`), for the subset of teams/years covered. The
practical use is identical to what `alt_data_sources.md` already proposed
(Elo/squad-quality -> event-rate regressions as priors for 2026), but now with
~4x the competition-seasons (8 WCs + 2 Euros + Copa America 2024 + AFCON 2023
vs. just 1 WC), and with **half-split granularity available natively** —
meaningfully reducing the modeling gap for the 236 half-time/first-half/
second-half markets the task description calls out as the biggest blind spot.

### 2.2 openfootball/worldcup.json

- **What it provides**: Match-level data (date, teams, scores, scorers+minutes,
  venues) for World Cups 1930-2026 (yes, includes 2026 fixtures/schedule) in
  simple public-domain JSON, no API key. For 1930-2022 also includes
  "full match details incl. line-ups, (yellow/red card) bookings, player
  substitutions, penalty shootouts" via a linked source.
- **License**: CC0 / public domain — completely unrestricted.
- **Coverage**: 2026 schedule already present (useful for fixture/team-name
  cross-checks against `elo_match_panel.csv`); historical card/booking data
  goes back to 1930 but is **match-summary level** (who got which card, not
  shot/corner/offside counts).
- **Target markets**: Cards (yes, historically, at the booking-event level —
  could give long-run card-rate priors per team/competition cheaply) and
  half-time goal splits (goal-scorer minutes let you bucket goals into
  first/second half). Does NOT cover corners/shots/offsides/SOT. **Low
  integration effort, modest payoff** — good as a free supplementary cards/
  half-time-goals prior, not a primary source.

### 2.3 Understat-based scrapers (`douglasbc/scraping-understat-dataset`,
`collinb9/understatAPI`, `osvaldomx/UnderData`, etc.)

- **What they provide**: Shot-by-shot xG data (location, minute, outcome,
  player) for the "big 5" European leagues + Russian league, 2014/15 onward.
- **International coverage**: **None directly** — Understat does not cover
  national-team/World Cup matches. Only useful indirectly as the
  "club-season shot rate as proxy for national-team player behavior" approach
  the task description allows — i.e., pull a 2026 squad player's club-season
  shot/SOT volume from Understat as a prior for their shot involvement in
  national-team matches.
- **Target markets**: Shots-on-target player props, indirectly, via the
  club-proxy approach — but FBref (already cataloged) provides broadly
  equivalent club-season data plus better international coverage in one
  source, so Understat is **redundant unless FBref's shot-level (not just
  goals/assists) player data proves insufficient**.

### 2.4 Wyscout open soccer-logs (`koenvo/wyscout-soccer-match-event-dataset`,
figshare collection, Pappalardo et al. 2019, *Scientific Data*)

- **What it provides**: Full spatio-temporal event logs (passes, shots, fouls,
  cards, etc.) for **one season each** of La Liga, Serie A, Bundesliga,
  Premier League, Ligue 1, **plus the entire 2018 FIFA World Cup (64 matches)
  and UEFA Euro 2016 (51 matches)**.
- **License**: CC BY 4.0 — fully open, citation-only requirement, very
  permissive (arguably easier than StatsBomb's terms for commercial-adjacent
  use, though the Jump Cup context is non-commercial research anyway).
- **Access**: Figshare download (static files) or via `kloppy` (Python event-
  data standardization library that has a Wyscout loader).
- **Coverage overlap with StatsBomb**: WC 2018 is also in StatsBomb's set;
  Euro 2016 is **not** in StatsBomb's current free set (which has Euro 2020/
  2024) — so Wyscout's Euro 2016 data is **additive**, giving another
  ~51-match international event-level sample, particularly useful for European
  teams' historical event-rate baselines.
- **Target markets**: Same six categories as StatsBomb (full event schema
  includes shots, fouls/cards, set pieces) — **secondary/supplementary** to
  StatsBomb given StatsBomb's broader and more recent international coverage
  (AFCON 2023, Copa America 2024, Euro 2024 are NOT in Wyscout's set). Worth
  using mainly to extend the training sample for European/South American teams
  back one more major tournament (2016) if sample size is a concern.

### 2.5 soccerdata / ScraperFC / worldfootballR_data (re-confirmed + extended)

- Already cataloged as the access method for FBref. One addition: the
  `JaseZiv/worldfootballR_data` GitHub repo hosts **pre-scraped** FBref data
  refreshed "most days" via `load_match_comp_results()` and related
  `load_*()` functions — this means the team can potentially get historical
  FBref match-result/competition tables **without scraping at all** for a
  pilot, then scrape only the specific match-report pages needed for
  corners/cards/shots detail. Lowers the barrier for the "small pilot, ~10-20
  matches" verification step already recommended in `alt_data_sources.md`.
- `sahil-gidwani/football-data-webscraping` and
  `agusrjs/scraping-data-providers` — general-purpose multi-source (FBref +
  Sofascore + Transfermarkt + Understat + WhoScored) scraping toolkits;
  potentially useful as reference implementations but not a new data source
  per se.

### 2.6 Sofascore scrapers

- Multiple repos found (`tunjayoff/sofascore_scraper`,
  `Roho11/SofaScore-Player-Card-Analysis`, `Urbistondo/sofa-score-scraper`,
  part of `probberechts/soccerdata`). Sofascore provides live match stats
  (including corners, shots, cards, fouls per player) and is well-known for
  granular **live** in-play stats with broad international match coverage.
- `Roho11/SofaScore-Player-Card-Analysis` specifically targets **cards
  per game / fouls per game / tackles per game per player + referee
  cards-per-game** — exactly the player-prop-for-cards signal needed — but is
  explicitly club-league-only (Premier League, Champions League, La Liga,
  Serie A) and described as "a personal learning project," MIT-licensed but
  likely fragile/unmaintained (no clear last-update date, anti-bot risk like
  WhoScored).
- **Target markets**: Cards/fouls player props, corners, shots — Sofascore's
  data model is well-suited, and it explicitly does cover internationals on
  the live site (unlike Understat), but **no verified, internationally-scoped,
  currently-working open scraper** was found — same "fragile fallback" status
  as the existing WhoScored note in `alt_data_sources.md`. `soccerdata`'s
  built-in Sofascore module is the most likely to be maintained; worth a quick
  pilot test if FBref's national-team coverage proves thin for a confederation.

---

## 3. Public APIs

### 3.1 API-Football (api-football.com / API-Sports), re-verified

- **Free tier**: 100 requests/day (resets 00:00 UTC, unused requests lost).
  Confirmed via API-Football's own rate-limit documentation.
- **World Cup 2026 coverage**: API-Football has published a dedicated guide
  ("FIFA World Cup 2026: Guide to Using Data with API-SPORTS") confirming
  `/fixtures?league=1&season=2026` returns all 104 matches with venue/date/
  time, `/teams?league=1&season=2026` returns the 48 teams, and `/players`
  returns squad/player profile data (position, nationality, age, height,
  weight).
- **Half-split stats — KEY FINDING**: The `/fixtures/statistics` endpoint
  supports a `half=true` parameter returning **"Fulltime, First & Second Half"**
  splits for: shots on goal, shots off goal, shots inside/outside box, total
  shots, blocked shots, fouls, corner kicks, offsides, possession, yellow/red
  cards, goalkeeper saves, passes (total/accurate). **This is a single
  parameter away from covering all six target market categories with native
  half-time splits** — if it's available on the free tier (needs direct
  verification with an API key) or a low-cost paid tier, this could be the
  single highest-leverage source for **2026 in-tournament** data (i.e., for
  re-pricing/settlement once matches start, today, June 11), though the
  100/day free cap is restrictive for pre-tournament bulk historical pulls
  across 48 teams.
- **Caveat**: 100 req/day free is enough for ~1-2 matches/day of detailed
  stats pulls, not a 48-team historical panel build. Paid tiers (pricing not
  itemized in this search) would be needed for bulk historical qualifier/
  friendly data. **Recommend**: use the free tier for **live 2026 match
  stats** (1 match's `/fixtures/statistics?half=true` per day comfortably fits
  in 100 req/day) rather than historical training-data collection, where
  FBref/StatsBomb (free, no rate limit beyond politeness) are more efficient.

### 3.2 football-data.org

- **Free tier**: 10 requests/minute, API key via free signup. Good for
  fixtures/results; "World Cup" is historically one of football-data.org's
  free-tier competitions (`competitions/2000` = WC) — but their statistical
  depth (corners/cards/shots) is **much shallower** than API-Football;
  primarily scores, lineups, scorers. **Low priority** for the six target
  categories — useful only as a free fixtures/results cross-check.

### 3.3 SportMonks

- **Free tier**: Effectively unusable for this project — limited to Danish
  Superliga and Scottish Premiership only, no international/WC data on free
  plan.
- **Paid**: SportMonks has a dedicated "World Cup API" product page and a
  2026-specific blog post ("Last-Minute World Cup 2026 Integration: What You
  Can Build in 2-4 Weeks") — their full plans cover detailed match stats
  (incl. presumably corners/cards/shots/half-splits given their general
  "Football Stats API" feature list: team/player/lineup/trend stats,
  head-to-head). **Pricing not retrieved** in this search — would need a
  direct pricing-page check if API-Football's free/low tiers prove
  insufficient. Flagged as a **paid fallback**, not a near-term action.

### 3.4 TheSportsDB

- **Free tier exists** but data is **crowd-sourced/community-edited**, not
  professionally maintained — explicitly described as "fine for hobby
  dashboards, not accuracy-sensitive products." Commercial use requires a
  $9/month Patreon tier. Covers 617 soccer leagues including internationals,
  but granularity is typically limited to scores/lineups/basic events, not
  corners/cards/shots/half-splits. **Not recommended** for any of the six
  target categories given data-quality concerns for a Brier-scored
  competition — at most a free fixture-list cross-check.

### 3.5 BALLDONTLIE FIFA World Cup API — re-confirmed, pricing unchanged

- Confirmed still active (`fifa.balldontlie.io`), covers 2018/2022/2026,
  includes "shot maps" and "attack momentum" in addition to the
  rosters/lineups/events/stats already noted in `alt_data_sources.md`. "Shot
  maps" suggests shot-location/SOT data may be available at GOAT tier
  ($39.99/mo). Pricing unchanged from prior research (ALL-STAR $9.99/mo,
  GOAT $39.99/mo, 48hr GOAT free trial). No new information changes the prior
  recommendation (evaluate the free trial only if FBref/StatsBomb prove
  insufficient for live 2026 re-pricing).

### 3.6 Other APIs surfaced but not deeply assessed
- **Highlightly** (`highlightly.net`) — claims possession, shots on target,
  corners, fouls, cards, passes-completed; freemium, not yet verified for
  international/WC coverage or pricing. Worth a 5-minute pricing-page check if
  API-Football's free tier proves too limited.
- **xmlsoccer.com** — claims shots_on_goal/shots_total/fouls_total/
  corners_total fields; not yet assessed for international coverage or cost.
- **Goalserve / live-score-api.com** — both have "World Cup API" products;
  paid, not assessed.

---

## 4. Reddit / community recommendations

**Direct access blocked**: Both `www.reddit.com/.../1pedmpv/...` and the
`.json` API variant of that URL returned "unable to fetch" errors in this
session (consistent with the task's warning that reddit/old.reddit fetches are
blocked for this environment). Google-cache and site-search approaches
(`site:reddit.com 1pedmpv`) returned no indexed results either — the thread is
likely too recent/low-traffic to be cached by search engines.

**Broader community-recommendation pattern** (from general web search of
r/sportsanalytics / r/soccer / r/MachineLearning football-dataset threads,
which DO surface in search): the consistent recommendations across these
communities for football event-level / player-level open datasets are:
1. **StatsBomb open-data** (by far the most-cited "go-to" for anyone wanting
   real event/shot/xG data with a player dimension, free, used in dozens of
   tutorials and Kaggle notebooks).
2. **Wyscout/Pappalardo et al. 2019 "Soccer match event dataset"** (the
   *Scientific Data* paper) — frequently cited as the other major free
   event-level academic release, particularly for the WC2018/Euro2016
   international coverage.
3. **FBref via worldfootballR/soccerdata** — the most-recommended source for
   "team stats" (corners/fouls/shots aggregates) specifically because it's
   free and covers a very wide range of competitions/years vs. paid Opta/
   Wyscout feeds.
4. **Transfermarkt** — for squad/value/transfer data, not event stats.

These four are **all already covered** (in this file or the existing
`alt_data_sources*.md` files) — so even without reading the specific thread,
its likely recommendations are already accounted for in the current research.
**No action needed beyond what's already planned**; if the specific thread
becomes accessible later (e.g., via a different network path), it's unlikely
to surprise given how consistently these four sources dominate this space.

---

## 5. Academic / research data

### 5.1 StatsBomb open-data releases (re-framed as "academic/research" access)
Already covered in §2.1 above — StatsBomb explicitly frames these releases as
"for research projects and genuine interest in football analytics," and they
are the basis for numerous peer-reviewed xG/event-data papers (e.g., the
ResearchGate paper on "Building reproducible expected-goals models from
public football event data" found in this search uses exactly this dataset).
**Key update vs. prior research**: coverage now spans 8 World Cups (1958-2022),
2 Euros (2020, 2024), Copa America 2024, and AFCON 2023 — not just WC2022.

### 5.2 Pappalardo et al. (2019), "A public data set of spatio-temporal match
events in soccer competitions," *Scientific Data* (Nature), PMC6817871
- Already covered in §2.4 (Wyscout). This is the peer-reviewed paper
  underlying the Wyscout open dataset — CC BY 4.0, includes WC2018 + Euro2016
  full event logs. Citing this paper (rather than just "Wyscout") may be
  appropriate if the eventual write-up needs an academic reference for the
  data provenance.

### 5.3 No other academic player-level international datasets surfaced
Searches for academic groups releasing player-level international datasets
beyond StatsBomb/Wyscout did not surface additional distinct sources — the
field appears to have converged on these two (plus FBref/Transfermarkt as
"scraped" rather than "released" sources) as the dominant free event-level
resources for international football. This is consistent with the existing
research's framing.

---

## Prioritized recommendation (best new capability per unit integration effort)

**1. StatsBomb open-data, expanded scope (AFCON 2023 + Copa America 2024 +
Euro 2024/2020 + 8 historical WCs), via `statsbombpy`.** This is the
single biggest *new* finding in this research round: the existing pipeline's
plan to use StatsBomb "2022 WC only" data as an Elo-to-event-rate training
prior can now draw on **~4x more international event-level matches**,
spanning the most recent major tournament for 4 of the 6 confederations
(UEFA, CONMEBOL, CAF, plus historical WC for all). Critically, the verified
`period` field on every event means **half-time/first-half/second-half splits
for corners, cards, shots, SOT, and offsides are available natively** —
directly addressing the single biggest gap (236 half-split markets) flagged in
prior research, for the subset of 2026 teams with recent AFCON/Copa
America/Euro/WC participation. Integration effort: low — same `statsbombpy`
pipeline already scoped, just point it at more competition/season IDs.

**2. FBref via worldfootballR/soccerdata, using `worldfootballR_data`
pre-scraped tables as the entry point** (already the top pick in
`alt_data_sources.md`, reaffirmed here). Best source for **2025-2026
qualifier/friendly "current form"** team-level corners/cards/shots/fouls/
offsides — the StatsBomb data above is rich but historically anchored
(2022-2024 tournaments), while FBref covers the actual 2025-26 run-up matches.
Combine #1 (priors/baselines) with #2 (recent-form adjustments) as the core
two-source strategy.

**3. API-Football free tier (100 req/day), used narrowly for LIVE 2026
match `half=true` statistics starting today.** Given the tournament has
begun, this is the only source confirmed to deliver **first/second-half-split
shots/corners/cards/offsides for 2026 fixtures themselves** (not proxies) —
useful for in-tournament model recalibration/settlement-style verification,
within the modest free-tier cap (roughly 1 fully-detailed match/day). Lowest
priority of the three for *pre-match modeling* but unique for *live 2026 data*.

**Deprioritized**: openfootball/worldcup.json (useful free cards/goals-by-
minute supplement, minimal effort, but narrow); Wyscout/Pappalardo (additive
Euro2016 sample, but StatsBomb's broader/fresher set likely suffices);
Sofascore/WhoScored scrapers (fragile, club-focused); SportMonks/TheSportsDB/
BALLDONTLIE paid tiers (revisit only if #1-#3 prove insufficient).
