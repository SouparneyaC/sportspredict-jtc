# Alternative / Supplementary Data Sources for Prop Markets (2026 World Cup)

Catalog of sources to fill the gaps identified in `data/processed/betting_markets_overview.md`:
team-level fouls/cards/corners/offsides/shots, player-level scoring rates for
"anytime goalscorer/assist" markets, and (lower priority) referee data.

This complements `research_notes.md` (model/scoring methodology) — this file is
purely about **where to get the data**.

---

## (a) Historical international match-event stats (fouls, cards, corners, offsides, shots)

### 1. FBref.com — match reports for international competitions (PRIMARY SOURCE)

- **What it covers**: FBref match report pages (e.g.
  `fbref.com/en/matches/<id>/...`) include a "Team Stats" comparison block with
  **possession, shots, shots on target, fouls, corners, crosses, touches,
  tackles, interceptions, aerials won, clearances, offsides, goal kicks, throw-ins,
  long balls** for both teams, plus a separate cards/events timeline (yellow/red
  cards, substitutions, goals with minute). This is essentially exactly the stat
  set the Jump Cup prop markets need, at the team level, per match.
- **Coverage for internationals**: FBref has dedicated competition pages for World
  Cup, Euros, Copa América, AFCON, and — critically — **World Cup Qualification by
  confederation** (UEFA, CONMEBOL, CONCACAF, CAF, AFC, OFC — e.g.
  `fbref.com/en/comps/6/WCQ----UEFA-M-Stats`, `fbref.com/en/comps/4/...CONMEBOL`,
  etc.) and a **Men's Friendlies** competition page
  (`fbref.com/en/comps/218/Friendlies-M-Stats`). These cover the actual run-up
  matches (2023-2026 qualifiers + 2025/2026 friendlies) for all 48 WC teams,
  with full match-report-level stats as described above.
- **Access method**:
  - **R**: `worldfootballR` package (CRAN + GitHub `JaseZiv/worldfootballR`).
    Has a dedicated vignette "Extracting data from FBref for International
    Matches" (`jaseziv.github.io/worldfootballR/articles/fbref-data-internationals.html`)
    — confirms functions like `fb_match_results()`, `fb_match_summary()`,
    `fb_match_report()`, `fb_team_match_stats()` work for international
    competitions, returning goals/cards/subs (match summary) and team-level
    advanced stats (possession, passing, defense, misc — fouls/corners/offsides
    typically live in the "misc" / team-stats table). worldfootballR also ships
    `load_*()` functions that pull **pre-scraped data from the
    `JaseZiv/worldfootballR_data` GitHub repo**, avoiding live scraping for
    historical seasons.
  - **Python**: `soccerdata` (`probberechts/soccerdata`, PyPI) wraps FBref (and
    ClubElo, Understat, WhoScored, Sofascore). `ScraperFC`
    (`oseymour/ScraperFC`, PyPI) has an `FBrefMatch`/`scrape_matches()` class
    that explicitly tags World Cup support. `fbrefdata`
    (`lorenzodb1/fbrefdata`) is a maintained fork of soccerdata's FBref module.
  - Direct browser fetch of fbref.com returned **HTTP 403** in this session
    (likely bot-protection / needs a real User-Agent or rate-limited scraping) —
    the R/Python packages handle this with proper headers + caching + delay, so
    use the package, not raw `requests`/`httr`.
- **Cost**: Free (scraping a public site — respect FBref's rate limits; both
  `soccerdata` and `worldfootballR` build in caching/delays for this reason).
- **Coverage limitations**:
  - Date range for granular "Team Stats" (fouls/corners/shots/offsides) tables is
    generally **post-~2017** for top competitions; for smaller confederations
    (OFC, some CAF qualifiers) coverage and stat completeness can be patchier —
    **needs verification per-confederation**.
  - 2026 WC group-stage fixtures themselves will populate on FBref live as
    matches are played (the tournament starts 2026-06-11 per the Jump Cup
    window) — so FBref is also the natural **live results re-scrape** source
    for in-tournament model updates, not just historical training data.
  - "Half-time" splits: FBref match reports do NOT generally provide a clean
    half-time score / per-half stat breakdown table; minute-by-minute event
    timelines (goals, cards, subs) DO have minute info, so half/full split for
    **goals** (and cards) can be derived by filtering events by minute <=45 vs
    >45, but per-half **shots/corners/fouls/offsides splits are NOT directly
    available** from the standard match-report team-stats table (that table is
    full-match aggregate only). This is the single biggest remaining gap for the
    236 half-time/second-half markets.
- **Concrete next step**: In R, install `worldfootballR`, then for each of the
  48 WC teams pull `fb_match_results(country=..., gender="M", season_end_year=2026,
  tier="", non_dom_league_url = "WCQ"/"Friendlies-M")` to get match URLs for
  2023-2026 qualifiers + friendlies, then loop `fb_team_match_stats()` /
  `fb_match_report()` over those URLs (with `Sys.sleep()` between calls) to
  build a team-match-level fouls/corners/shots/offsides/cards panel. Start with
  a small pilot (one confederation, ~50 matches) to confirm table structure and
  column names before scaling to all 48 teams.

### 2. StatsBomb Open Data — 2022 World Cup full event data (HIGH VALUE, FREE)

- **What it covers**: `github.com/statsbomb/open-data` provides **free,
  full event-level data (every pass, shot, foul, card, corner, offside) for the
  entire 2022 Qatar World Cup** (competition_id 43, season 2022), including
  StatsBomb's "360" freeze-frame data for that tournament. This is the richest
  free dataset available for any World Cup.
- **Access method**: Raw JSON on GitHub (`data/events/<match_id>.json`,
  `data/matches/43/<season_id>.json`), or `statsbombpy`
  (`github.com/statsbomb/statsbombpy`) Python wrapper that reads directly from
  the open-data repo without credentials for the free competitions.
- **Cost**: Free.
- **Coverage limitations**: Only **2022** WC (not 2026, obviously, and not
  qualifiers/friendlies) — but **most of the 48 teams qualifying for 2026 also
  played in 2022** (or have significant squad overlap), so this is a strong
  source of **team-level "true" event rates** (fouls per match, cards per match,
  corners per match, shots/SOT per match, offside frequency) to use as **priors /
  validation data** for a 2026 team-strength model — e.g., regress
  fouls-committed-per-match on Elo rating using the 2022 WC sample to estimate
  the Elo->fouls relationship, then apply it to 2026 team Elos.
- **Concrete next step**: Pull the 2022 WC event JSON via `statsbombpy`
  (`sb.events(match_id=...)`), aggregate to team-match level (fouls committed,
  cards, corners won, shots, shots on target, times offside), join to Elo
  ratings at the time of the 2022 tournament — use this as the **training set**
  for the "Elo -> event-rate" regression described in
  `prop_market_pricing_notes.md`.

### 3. Kaggle — supplementary historical World Cup match-stat datasets

- **"FIFA World Cup 2022: Complete Dataset"**
  (`kaggle.com/datasets/die9origephit/fifa-world-cup-2022-complete-dataset`):
  per-match stats including assists, possession, crosses, yellow/red cards,
  passes, fouls, attempts (shots), and offsides for all 64 2022 WC matches —
  essentially a flat-file version of a subset of the StatsBomb data above.
  Useful as a quick CSV without needing to parse StatsBomb JSON.
- **"Football - FIFA World Cup, 1930-2026"**
  (`kaggle.com/datasets/piterfm/fifa-football-world-cup`): broad
  results/metadata dataset across all WC editions — useful for cross-checking
  team names/IDs and historical match lists, but **not** event-level
  (fouls/cards/etc.) per the listing description; **needs verification** whether
  it has been updated with 2026 fixtures yet.
- **"European Soccer Database"**
  (`kaggle.com/datasets/hugomathien/soccer`): 10,000+ **club** matches (mostly
  European domestic leagues, ~2008-2016) with goal types, possession, corners,
  crosses, fouls, cards. **Club football, not international** — useful only as
  a large supplementary sample for fitting a generic "Elo-diff -> fouls/corners
  ratio" relationship if international samples are too small, with the caveat
  that club-vs-international foul/card rates may differ systematically (referee
  pools, competition intensity).
- **Cost**: Free (Kaggle account required for download).
- **Next step**: Low priority relative to #1/#2 above — use only as a
  cross-check / larger-sample fallback for fitting the Elo->event-rate
  regressions if the FBref+StatsBomb international sample proves too small for
  stable confederation-specific estimates.

### 4. footystats.org

- **What it covers**: Aggregated team/league stats including average
  fouls/corners/cards per match, "BTTS %", over/under splits — mostly
  **club league** focused (presented as season-long team averages, not
  match-by-match raw data).
- **Access method**: Website + a paid API (footystats.org/api) — **needs
  verification** of current pricing and whether international/national-team
  data is included (their public site historically focuses on domestic
  leagues).
- **Cost**: Freemium/paid API — needs verification.
- **Coverage limitations**: Primarily club leagues; international/national-team
  coverage uncertain.
- **Next step**: Low priority — only revisit if FBref/StatsBomb prove
  insufficient for a specific confederation; check their API docs for an
  "international" or "World Cup" league ID before paying for anything.

### 5. Opta / WhoScored-derived datasets

- **What it covers**: WhoScored.com displays Opta-sourced match stats
  (fouls, cards, corners, offsides, shots, dribbles, tackles) including for
  international matches and World Cup qualifiers.
- **Access method**: `soccerdata` includes a WhoScored scraper
  (`probberechts/soccerdata`); raw Opta data itself is commercial/paywalled and
  **off-limits cost-wise** for this project.
- **Cost**: WhoScored scraping is free but fragile (site uses heavy
  JS/anti-bot measures — historically one of the harder soccerdata sources to
  keep working). Opta direct = enterprise pricing, not viable.
- **Coverage limitations**: Reliability of the scraper fluctuates with
  WhoScored site changes — **needs verification** it currently works.
- **Next step**: Treat as a **fallback only** if FBref coverage for a specific
  confederation/competition is too thin — don't invest here first.

---

## (b) Player-level data for "anytime goalscorer / assist" markets

### 1. FBref national-team player pages (PRIMARY SOURCE)

- **What it covers**: For every national team, FBref has a squad page with
  **player-level goals, assists, minutes played, goals+assists per 90** broken
  out by competition (recent qualifiers, friendlies, continental tournaments) —
  exactly the "recent form" rate stats needed to price anytime
  goalscorer/assist markets (37 such markets across the 72 group matches).
- **Access method**: `worldfootballR::fb_player_season_stats()` /
  `fb_team_player_stats()` for national teams (international squad URLs follow
  the same FBref structure as club squads — confirmed by the
  "FBref-data-internationals" vignette). In Python, `soccerdata.FBref` /
  `ScraperFC` similarly support player-season stat tables.
- **Cost**: Free.
- **Coverage limitations**: Player **club-season** stats (the bulk of recent
  minutes for most players, since the WC group stage starts right after club
  seasons end) are FBref's strongest data — international-only goals/assists
  samples are small (a handful of caps/year for most players). **Recommended
  approach**: use **club-season G+A/90 (most recent completed season, 2025-26)**
  as the primary signal for a player's current scoring rate, scaled by
  expected international minutes share, rather than relying on sparse
  international-only G+A data. Need to manually map each player's current club
  (transfer windows close ~early June 2026, so squads should be largely settled
  by kickoff — **needs verification** that FBref's national-team squad pages are
  updated with final 2026 WC rosters by the time of pricing).
- **Next step**: Once provisional/final 2026 squads are published (FIFA
  publishes 26-man squads ~1-2 weeks before the tournament — check
  `fifa.com` and `en.wikipedia.org/wiki/2026_FIFA_World_Cup_squads`, which
  already has a page tracking this), pull each named player's most recent
  club-season G+A/90 + minutes share via worldfootballR, and combine with
  team-level expected-goals from the Poisson model (see pricing notes) to
  estimate P(player scores or assists).

### 2. Transfermarkt

- **What it covers**: Squad lists, market values, positions, recent
  appearances/goals — Transfermarkt's "Squad Builder" tool already has
  **2026 World Cup squad-projection pages live**
  (`transfermarkt.us/.../squad-builder-tool-for-each-nation`), and a
  "player to watch from every nation" editorial series — useful for
  **cross-checking squad lists** and identifying likely starters/key attacking
  players, but Transfermarkt's per-player goal/assist stats are less
  systematically structured for bulk extraction than FBref's.
- **Access method**: `worldfootballR::tm_*()` functions (the package wraps
  Transfermarkt too, per its "Extracting data from Transfermarkt" vignette);
  also `dcaribou/transfermarkt-scraper` (standalone Python/Scrapy project) and
  `ScraperFC`'s Transfermarkt module.
- **Cost**: Free (scraping).
- **Coverage limitations**: Squad lists for 2026 are still partly
  **provisional/projected** as of writing (final rosters lock close to the
  tournament) — **needs verification at pricing time** (closer to the actual
  matches) that squads used match the final submitted lists.
- **Next step**: Secondary source — use mainly to validate/cross-check the
  player names appearing in Jump Cup market questions against actual squad
  members (a player not in the final squad obviously prices to ~0).

### 3. BALLDONTLIE FIFA World Cup API

- **What it covers**: Dedicated REST API explicitly covering **2018, 2022, AND
  2026** World Cup editions — teams, stadiums, players, rosters, matches,
  standings, lineups, match events (incl. goal-scorer/assist events), and
  player tournament/match stats (goals, assists). This is the **only source
  found that explicitly claims structured 2026 roster + live event data**.
- **Access method**: REST API, requires API key (`app.balldontlie.io`).
  Free tier = 5 req/min, Teams/Stadiums only. "ALL-STAR" ($9.99/mo, 60 req/min)
  and "GOAT" ($39.99/mo, 600 req/min, full access incl. rosters/events/stats) —
  GOAT tier has a 48-hour free trial.
- **Cost**: Free tier insufficient for player stats; paid tiers $9.99-$39.99/mo.
  **Needs verification**: whether ALL-STAR ($9.99) tier includes player
  goals/assists endpoints or only GOAT does (the search summary suggests "most
  data beyond basic team info requires GOAT").
- **Coverage limitations**: New/smaller API provider — data completeness and
  accuracy for 2026 (a future tournament at time of most documentation) needs
  verification once the tournament starts.
- **Next step**: If FBref club-season G+A/90 + Transfermarkt squad
  cross-checks prove insufficient (e.g., for live in-tournament re-pricing as
  goals/assists actually happen), evaluate the 48-hour GOAT free trial to see
  if its live World Cup match-event feed (goal/assist events in real time)
  is worth $39.99/mo for the tournament duration — this would primarily help
  with **live market re-pricing as the tournament progresses**, less so initial
  pre-match pricing.

---

## (c) Referee assignment / tendency data (lower priority)

- **What's needed**: Cards markets (67 markets) and the "penalty OR red card"
  compound markets (6) are mechanically affected by **which referee is
  assigned** — some referees show notably more cards/match than others.
- **Sources** (none deeply verified — all flagged "needs verification"):
  - FBref match reports include the referee's name per match — so a referee's
    **historical average cards-per-match** can in principle be computed from
    the same FBref match-stats pull described in (a)#1, by grouping on referee
    name across all competitions they've officiated (club + international).
  - FIFA does not publish 2026 WC referee-to-match assignments far in advance
    (referee panels are typically announced ~1-2 months pre-tournament, and
    individual match assignments often only days before) — so this data
    **will not be available** for pre-tournament pricing of most/all group
    matches, only possibly for late group-stage matches if assignments are
    announced early enough.
- **Concrete next step**: Deprioritize. If FBref match-report scraping (a)#1 is
  built anyway, add "referee name" as a free extra column while you're at it —
  but don't build a dedicated referee-tendency model unless 2026 WC referee
  assignments become available with enough lead time (check
  `fifa.com` referee announcements ~late May/early June 2026).

---

## Summary table

| Source | Covers | Access | Cost | 2026-readiness |
|---|---|---|---|---|
| FBref (via worldfootballR / soccerdata / ScraperFC) | Team match stats: fouls, corners, shots, SOT, offsides, cards, possession (WC, WCQ by confederation, Friendlies-M) | R/Python package scraping | Free | Qualifiers/friendlies through 2025-26 available now; live 2026 results scrapeable as played |
| StatsBomb Open Data (2022 WC) | Full event data incl. fouls/cards/corners/offsides/shots, 360 freeze-frames | `statsbombpy` / raw GitHub JSON | Free | 2022 only — used as training/prior data, not 2026 fixtures |
| Kaggle WC 2022 datasets | Flat-file subset of StatsBomb-style stats | CSV download | Free | 2022 only |
| FBref national-team player pages | Player G+A, minutes, G+A/90 (club + intl) | worldfootballR / soccerdata | Free | Needs final 2026 squads (check ~early June) |
| Transfermarkt | Squad lists, player profiles, market value | worldfootballR / transfermarkt-scraper | Free | Squad-builder pages for 2026 already live (provisional) |
| BALLDONTLIE FIFA WC API | 2026 rosters, matches, lineups, goal/assist events | REST API | Free tier limited; $9.99-$39.99/mo for full | Explicitly supports 2026 — needs verification of data completeness |
| footystats.org | Aggregated club-league averages (fouls/corners/cards) | Web/API (paid?) | Needs verification | Mostly club leagues — low priority |
| WhoScored/Opta-derived | Match stats incl. internationals | `soccerdata` scraper | Free but fragile | Low priority fallback |

## Key open question for the "recent form" sub-dataset

FBref's **WCQ-by-confederation** pages and **Men's Friendlies** page
(`fbref.com/en/comps/218/Friendlies-M-Stats`) are confirmed to exist and cover
the relevant 2023-2026 window — but exact per-match stat-table completeness for
2025-2026 friendlies/qualifiers (especially for AFC/CAF/OFC teams, who are less
heavily covered than UEFA/CONMEBOL on FBref historically) **needs direct
verification** by pulling a small pilot sample (~10-20 matches across
confederations) before committing to build the full 48-team panel. Direct
browser fetches to fbref.com returned HTTP 403 in this research session — use
`worldfootballR`/`soccerdata`, which are built to handle this (proper
User-Agent + rate limiting), for the pilot.
