# Alternative Data Sources for International Football Outcome/Goals ML (2026 WC)

Scope: data sources that could add genuinely **new signal** beyond
`elo_match_panel.csv` (date, teams, scores, neutral, pre-match Elo) for a
GBT/NN match-outcome or goals model — i.e., things Elo structurally cannot
capture: current squad quality/changes, absolute team strength (not just
relative), market expectations, environment (altitude/travel/weather),
rankings methodology differences. Complements `data/alt_data_sources.md`
(which covers prop-market event stats — fouls/cards/corners/players) and
`data/ml_integration_research_notes.md` (model-side ML literature).

---

## RANKED LIST — read this first (~450 words)

**1. Transfermarkt squad market values (`dcaribou/transfermarkt-datasets`,
free, weekly-refreshed, Kaggle/DuckDB/CSV).** This is the single highest-value
addition. It directly covers national teams (`national_teams`,
`national_team_competition_games` for WC/Euro/Copa América/AFCON/Asian Cup),
goes back to ~2005 (Transfermarkt's coverage start), and gives **squad-level
aggregate market value, average squad age, and player-level values** updated
far more frequently (multiple times/season) than Elo, which only updates on
match results. This is exactly the "current squad strength, independent of
recent results" signal Elo cannot provide — it captures transfers, breakout
youngsters, aging squads, and injuries-to-star-players (their value
effectively drops out if unused) **before** those show up in match results.
Concretely: add `squad_value_home`, `squad_value_away`,
`squad_value_diff`/`ratio`, and `avg_age_diff` as features alongside
Elo-diff. Nate Silver's 2026 PELE model (see citations) uses exactly this —
top-23 player market values blended with an Elo-like rating — and is the
closest published analogue to "Elo + market value" for 2026 specifically.

**2. FIFA World Ranking points (free, scrapable/GitHub `cnc8/fifa-world-ranking`
or Kaggle, monthly since 1992/2018-revision since 2018).** Cheap, orthogonal
second opinion to Elo: different update formula (FIFA's current "SUM" method
weights match importance/confederation strength differently than Elo's K-factor
approach), different time-averaging. Adding `fifa_rank_diff` /
`fifa_points_diff` alongside `elo_diff` gives the model two independently-
constructed strength estimates — useful for a tree model to find where they
disagree (disagreement itself can be informative, e.g. signaling a team whose
results don't match its "reputation"/seeding). Very low cost, no QK quota use.

**3. Bookmaker-implied probabilities for World Cup matches (paid odds APIs
or scrapers; check QK first).** The literature is unanimous: bookmaker
consensus probabilities are the single best predictor and consistently beat
Elo/ranking-only and even kitchen-sink ordered-logit models (Hvattum &
Arntzen 2010). For a GBT, a `bookmaker_implied_home_prob` feature (de-vigged,
logit-averaged across books per Leitner/Zeileis/Hornik 2010) would likely
dominate other features but is genuinely "new information" (markets price in
injuries, lineups, weather, motivation that nothing else here captures).
**Check QK API first** — odds data is plausibly already available there and
would conserve external scraping effort.

**4. Altitude/venue elevation data (free — static lookup table, ~16 venues
for 2026).** Static but high-leverage for this specific tournament: several
2026 venues (Mexico City ~2,240m, Guadalajara ~1,566m) are at meaningfully
high altitude, and the literature finds altitude *differential* between a
team's home conditions and the match venue affects goals/win probability —
something a single Elo number never encodes. Trivial to build (one CSV of
venue elevations), join on venue.

**5. Rest days / fixture congestion / travel distance (derivable mostly from
existing data + a venue-distance lookup, free).** Days-since-last-match and
travel distance from team's "home base" to venue are cheap derived features
with modest but real literature support (rest-day effects concentrated when
one team has ≤3 days rest).

**Lower priority / needs more verification**: EA Sports FIFA/FC video-game
ratings (free Kaggle dumps, but lag real-world form and are club-context
ratings projected onto national squads — redundant with #1); FBref advanced
stats (xG/shots/possession) — valuable but mostly post-2017 and uneven by
confederation, better suited to a secondary "form" feature than a core
strength measure; weather APIs (likely small effect, high implementation
cost for forecast-vs-actual mismatch in pre-match prediction).

---

## Detailed source-by-source notes

### 1. Transfermarkt squad market values — `dcaribou/transfermarkt-datasets`

- **What it is**: An open-source, automatically-updated (weekly) extraction
  of Transfermarkt data, packaged as CSVs, a single DuckDB file, and a Kaggle
  dataset (also on data.world). 12 tables: `players`, `games`, `appearances`,
  `player_valuations`, `clubs`, `competitions`, `transfers`, `countries`,
  `national_teams`, and national-team competition games (World Cup, Euro,
  Copa América, AFCON, Asian Cup).
  Repo: `github.com/dcaribou/transfermarkt-datasets`.
- **International coverage**: YES, explicitly — national teams and
  national-team tournament games are first-class tables. Player market
  valuations are timestamped (multiple per year per player), so a squad's
  aggregate value at any historical date can be reconstructed.
- **Access**: Free. Kaggle dataset (no scraping needed) or DuckDB/CSV/parquet
  download from the repo. `dcaribou/transfermarkt-scraper` (Scrapy) exists if
  you need fresher/custom pulls, but the pre-built dataset likely suffices.
- **How it helps our pipeline specifically**:
  - **Addresses Elo's "single lagged scalar" problem.** Elo only moves after
    a match is played and result-determined; squad value can change
    overnight (a star player transfers, gets injured, breaks out at club
    level) and reflects markets pricing in information Elo hasn't "seen" yet.
  - **Addresses the EIV/attenuation issue flagged in prior research**: if Elo
    is a noisy/lagged proxy for "true team strength," squad market value is
    an independent noisy proxy with different noise structure and update
    frequency — including both as features (rather than relying on one
    error-laden proxy) is a standard EIV mitigation (using an instrument /
    second measurement).
  - **Captures absolute team quality, not just relative.** Two teams could
    have the same Elo gap (say +50) at very different absolute levels (e.g.,
    Brazil vs Argentina at the top vs. two mid-table CONCACAF sides) — squad
    value captures this absolute level, which may matter for goal-scoring
    rates (top squads convert chances at higher rates regardless of Elo gap).
  - **Concrete features**: `squad_value_home`, `squad_value_away`, their
    ratio/diff (log scale likely appropriate given heavy right-skew), average
    age, value concentration (e.g., share of value in top-3 players —
    proxies "star-dependence" / vulnerability to one injury).
- **Caveats**: coverage realistically starts ~2005 (when Transfermarkt
  valuations became systematic) — so this feature would be `NA` for most of
  the 1872-2004 panel; either restrict the GBT training window or use
  missing-value-aware tree splits (XGBoost/LightGBM handle NaN natively,
  which is actually convenient here). Smaller federations (OFC, some CAF
  teams) likely have thinner valuation coverage — needs spot-checking.

### 2. FIFA World Ranking (official points/positions)

- **What it is**: FIFA's official monthly team ranking, points-based,
  methodology revised in 2018 to a Elo-like "SUM" system (adds/subtracts
  points based on match result, opponent strength, confederation strength,
  match importance/competition weighting, home/away).
- **International coverage**: 100% — this IS an international-football
  ranking, published monthly since Aug 1992 (men's).
- **Access**: Free. No official bulk API, but `cnc8/fifa-world-ranking`
  (GitHub) provides a scraped CSV (id, rank, country, points, previous
  points, rank change, confederation, rank_date) from 1992 onward; also
  available as a Kaggle dataset ("FIFA Men's World Ranking"). FIFA.com itself
  exposes a JSON endpoint usable via simple scraping if a fresher pull is
  needed (per Héric Libong's Scrapy writeup).
- **How it helps our pipeline specifically**:
  - **A second, independently-constructed strength estimate.** Elo (the
    World Football Elo / eloratings.net variant we compute) and FIFA's SUM
    ranking use different K-factors, different recency weighting, and
    (post-2018) different competition-importance multipliers. Where the two
    disagree about a team's relative strength is itself informative — a
    GBT can learn nonlinear interactions like "when FIFA rank says X is much
    better than Elo says, X tends to underperform its Elo-implied
    probability" (could reflect e.g. FIFA's heavier weighting of recent
    competitive — vs. friendly — matches).
  - **Cheap "free" feature** — essentially zero marginal cost vs. value;
    should be one of the first additions tried.
  - **Important methodological note**: FIFA ranking is *also seeding input*
    for World Cup draws — so it has policy relevance (group difficulty) above
    and beyond a pure strength signal, which a GBT could pick up if seeding
    pot is included as a categorical feature.
- **Caveats**: Pre-1992 unavailable (not an issue for recent-era model
  training/backtesting on 2026); ranking methodology changed materially in
  2018 — a dummy/era flag may help the model not conflate pre/post-2018
  ranking regimes.

### 3. Bookmaker-implied probabilities (World Cup match odds)

- **What it is**: Pre-match win/draw/win odds from multiple bookmakers,
  de-vigged ("overround"-adjusted) and averaged on a logit scale (the
  "bookmaker consensus model" of Leitner, Zeileis & Hornik 2010), used as
  the dominant feature in the most successful published World Cup models
  (Zeileis/Hornik's "FIFA World Cup multiverse," 2022 and 2026 editions).
- **International coverage**: YES for major tournaments (World Cup, Euro,
  major qualifiers) — odds aggregators cover international markets heavily,
  especially close to kickoff. Coverage for low-profile friendlies/qualifiers
  (smaller confederations) will be thinner.
- **Access**: Mixed.
  - Free: some odds-comparison sites (oddschecker, etc.) can be scraped for
    current/near-term odds, but historical odds archives for backtesting
    typically require a paid product (e.g., Football-Data.co.uk has historical
    odds but is **club-league focused** — needs verification whether their
    international/WC odds archives exist).
  - Paid: dedicated odds-data APIs (the Odds API, Betfair historical data,
    etc.) — cost not yet assessed.
  - **CHECK QK FIRST**: given the "Jump Trading Probability Cup" market
    context, QUANTkiosk plausibly already has odds or odds-derived
    probabilities for these matches — flagging for the user to check QK
    endpoints before paying for or scraping a separate odds source. Don't
    spend the 10k/day quota without first confirming odds aren't already
    available more cheaply elsewhere.
- **How it helps our pipeline specifically**:
  - **The single most information-dense feature available**, per Hvattum &
    Arntzen (2010) and the Zeileis/Hornik multiverse models — bookmaker
    consensus consistently beats Elo-only, ranking-only, and ordered-logit
    "kitchen sink" models on Brier/RPS for international matches.
  - It implicitly encodes **everything** Elo misses: current injuries,
    confirmed lineups, weather forecasts, travel fatigue, motivation
    (dead-rubber vs. must-win) — all the "soft" information no static dataset
    captures.
  - Even if you don't want to "just predict the market," including
    `bookmaker_implied_prob` as one GBT feature alongside Elo/squad-value
    lets the model learn a residual/blend — this is literally the structure
    of the Zeileis/Hornik random-forest model (RF blends Poisson-on-Elo,
    bookmaker-consensus, and team covariates).
  - **Caution**: if the eventual goal includes evaluating model edge vs. a
    market (e.g., trading the Jump Cup itself), training a feature directly
    derived from odds risks circularity/leakage depending on what the target
    market is pricing — needs careful framing if used for trading signal
    rather than pure outcome prediction.

### 4. Altitude / venue elevation

- **What it is**: Elevation (meters above sea level) of each match venue,
  optionally combined with each team's "home altitude" (elevation of their
  typical home stadium / capital city) to compute an altitude *differential*.
- **International coverage**: Trivially applicable to any match with a known
  venue — and for the 2026 WC, venues are fixed and known in advance (16
  stadiums across US/Mexico/Canada).
- **Access**: Free — static lookup, easily compiled by hand (16 stadiums) or
  via any geocoding/elevation API (e.g., open-elevation.com, free).
- **Academic support**:
  - McSharry, P.E. (2007), "Effect of altitude on physiological performance:
    a statistical analysis using results of international football games"
    (BMJ, PMC2151172) — found **altitude differential** between competing
    teams' home countries (not just absolute venue altitude) is associated
    with goal-scoring/outcome differences in international matches; teams
    from low-altitude countries underperform at high-altitude venues
    relative to teams already acclimatized to altitude.
  - "Effect of Altitude on Football Performance: Analysis of the 2010 FIFA
    World Cup Data" (J. Strength & Conditioning Research, 2013) — examined
    physical/technical performance changes at South African altitudes
    (Johannesburg ~1,750m) vs. sea level.
  - High-altitude football controversy (Wikipedia) — documents FIFA's
    2007 ban on internationals above 2,500m (later suspended), reflecting
    how seriously this effect is taken competitively.
- **2026-specific relevance**: Mexico City (Estadio Azteca) sits at
  ~2,240m/7,350ft and Guadalajara at ~1,566m/5,138ft — both meaningfully
  above the altitude thresholds discussed in the literature. Any match played
  at these venues, especially involving teams whose players are based at
  sea level, is a candidate for an altitude-adjustment feature.
- **How it helps our pipeline specifically**: a **pure environment feature**
  with zero overlap with Elo — Elo encodes "how good is this team in general"
  but nothing about "how will this specific team perform at this specific
  venue's altitude." Cheap, interpretable, and directly actionable for the
  small number of 2026 matches at Mexico City/Guadalajara.

### 5. Rest days / fixture congestion / travel distance

- **What it is**: (a) days since each team's previous official match
  (derivable entirely from `elo_match_panel.csv` — no new data needed); (b)
  travel distance from each team's home region to the match venue (needs a
  small lookup of team "home base" coordinates + venue coordinates, both
  free/static).
- **International coverage**: Universal — applies to any match in the panel.
- **Access**: Free. (a) is a pure derived feature from existing data
  (mentioned in the user's own framing as something we can already do). (b)
  needs one small static table (country/federation HQ lat-long + venue
  lat-long — both easily compiled).
- **Academic support**:
  - A study of national-team matches in World Cups (1930-2010) and Euros
    (1960-2012) found rest-day effects on performance are concentrated when
    one team has **3 or fewer days of rest** relative to the opponent — i.e.,
    a nonlinear/threshold effect, well-suited to tree-based models which
    naturally find such splits (vs. a linear Elo-style model).
  - Travel-distance research (mostly NFL/club-football literature) finds
    travel contributes to home advantage but with a "small, non-monotonic,
    decreasing" effect — modest but non-zero.
- **How it helps our pipeline specifically**: these are genuinely free
  (mostly already-in-hand) features that address squad-fatigue effects Elo
  cannot see — e.g., a team playing their 3rd match in 7 days during a
  congested qualifying window vs. a well-rested opponent. Given GBTs handle
  threshold/interaction effects well, this is a low-cost, plausible-payoff
  addition — should be bundled with item #2 from `ml_integration_research_
  notes.md` (Elo-momentum) as part of the "free features from existing data"
  batch.

### 6. EA Sports FIFA/FC video game player ratings (lower priority)

- **What it is**: Player attribute ratings (pace, shooting, passing,
  dribbling, defending, physical, overall) from the EA Sports FIFA/FC
  franchise, scraped from sofifa.com, available as annual Kaggle dumps
  (e.g., "EA Sports FC 25 Database, Ratings and Stats") covering 17,000+
  players across 700+ clubs, updated periodically through a season.
- **International coverage**: Indirect — ratings are per-player (club
  context), not per national team, but national-team squads can be
  constructed by mapping named players (from FIFA 26-man squad lists) to
  their FIFA/FC ratings and aggregating (e.g., average overall rating of
  starting XI, weighted by expected minutes).
- **Access**: Free (Kaggle CSV dumps, updated ~annually/per game edition;
  some community datasets scrape sofifa monthly).
- **How it could help, and why it's lower priority**:
  - Conceptually similar signal to Transfermarkt squad value (current squad
    quality, captures transfers/form to some degree) but EA ratings update
    much less frequently (annual game releases, occasional in-season
    updates) and reflect EA's subjective rating process rather than a market
    price — likely **redundant with, and noisier than, Transfermarkt market
    value** for the same purpose.
  - Possible complementary use: EA ratings include **positional/attribute
    detail** (e.g., team-average pace, team-average defending rating) that
    market value doesn't directly give — could support more granular
    features like "team speed differential" if a research direction wants
    tactical-style features. Not a near-term priority given Transfermarkt
    already addresses the main "current squad strength" gap.
  - Some published work (arXiv 2403.07669 survey, and a 2024 ACM paper on
    EA-series-data + betting odds for top-5-league prediction) uses FIFA/FC
    ratings + odds for **club** match prediction — again club-football
    focused, needs adaptation for international squads.

### 7. FBref advanced match stats (xG, shots, possession) — secondary/form feature

- Already cataloged in `data/alt_data_sources.md` (§a, primarily for prop
  markets) — flagged here because xG/possession/shot data, aggregated as
  **rolling team-level "underlying performance" features** (e.g., average xG
  for/against over last N matches), is a recognized way to capture *current
  form* that pure results-based Elo updates only slowly. The
  arXiv:2309.14807 paper's winning CatBoost model used "pi-ratings" (a
  rating derived from goal-difference shocks, conceptually similar to
  rolling xG-based form) as its top feature alongside Elo-like ratings.
- **Caveat for international football**: FBref's granular team-stats tables
  are reliable post-~2017 and patchier for smaller confederations (per the
  existing `alt_data_sources.md` write-up) — usable as a *recent-form*
  overlay (last 1-2 years of qualifiers/friendlies) rather than a
  full-history feature.
- **Access**: Free via `worldfootballR`/`soccerdata` (already documented).

### 8. Weather data (lowest priority)

- **What it is**: Temperature, humidity, precipitation at venue/kickoff time.
- **International coverage**: Universal (any venue/date).
- **Access**: Free APIs (Open-Meteo historical archive is free and covers any
  date/location; current FiveThirtyEight SPI methodology explicitly lists
  weather as one of its "dozens of factors").
- **How it could help**: plausibly small effect on goals (heat/humidity
  affecting late-game fitness, similar mechanism to altitude) but (a) for
  *future* 2026 matches, only a *forecast* (not actual) is available
  pre-match, adding noise; (b) effect sizes in the literature are not large
  relative to implementation cost. **Recommendation**: deprioritize unless
  altitude/rest-day features (cheaper, similar mechanism) prove insufficient
  and there's clear capacity for more environment features.

---

## Academic citations

1. **Hvattum, L.M. & Arntzen, H. (2010).** "Using ELO ratings for match
   result prediction in association football." *International Journal of
   Forecasting*, 26(3), 460-470.
   - Data/features: Elo-difference (+ home advantage) via ordered logit, vs.
     bookmaker odds, vs. Goddard's (2005) ~50-100-covariate ordered logit.
   - Finding: Elo+ordered-logit beat the kitchen-sink covariate model and
     uniform/historical baselines on Brier/log-loss, but **lost to bookmaker
     odds** — i.e., market data adds signal beyond what large hand-built
     covariate sets capture. (Already in `ml_integration_research_notes.md`;
     repeated here because it directly motivates ranking #3, bookmaker odds.)

2. **Groll, A., Ley, C., Schauberger, G., & Van Eetvelde, H. (2019).** "A
   hybrid random forest to predict soccer matches in international
   tournaments." *Journal of Quantitative Analysis in Sports*, 15(4),
   271-287. (Originally arXiv:1806.03208, "Prediction of the FIFA World Cup
   2018 — A random forest approach with an emphasis on estimated team
   ability parameters.")
   - Data/features: random forest on team covariate information (the
     "present status" features — the predecessor of what later became
     market value/FIFA rank/GDP in the 2022/2026 versions) **combined with**
     team "ability parameters" estimated from a Poisson ranking method fit on
     historical match results (an Elo/Poisson-style strength estimate).
   - Finding: adding the ranking-method ability parameters as an extra
     covariate to the random forest **substantially improved predictive
     power** vs. either approach alone — i.e., combining a results-based
     rating (their analogue of our Elo) with team-level "current state"
     covariates (their analogue of squad value/FIFA rank) outperforms either
     in isolation. This is the strongest direct evidence that supplementing
     Elo with current-state team covariates (squad value, etc.) helps.

3. **Groll, A., Hvattum, L.M., Ley, C., et al.** "Hybrid machine learning
   forecasts for the UEFA Euro 2020." (arXiv preprint, extension of the 2019
   JQAS hybrid-RF approach to Euro 2020.)
   - Same hybrid random-forest structure applied to a different international
     tournament — relevant as a second confirmation of the approach
     generalizing beyond a single World Cup.

4. **Zeileis, A., Leitner, C., & Hornik, K.** "Football meets machine
   learning: Forecasting the 2026 FIFA World Cup" (R-bloggers/Zeileis.org,
   2026) and the predecessor "Machine learning of a 2022 FIFA World Cup
   multiverse" (zeileis.org/news/fifa2022/, Nov 2022).
   - Data/features: random forest blending (a) a bivariate Poisson model
     fit on 8 years of national-team match results with exponential
     recency-weighting (their Elo/results-based ability estimate, directly
     analogous to our `elo_home_pre`/`elo_away_pre`); (b) bookmaker-consensus
     win probabilities from ~28 international bookmakers, de-vigged and
     logit-averaged (Leitner/Zeileis/Hornik 2010 "bookmaker consensus
     model"); (c) "present status" covariates — **market value, FIFA rank,
     team structure, population, GDP per capita**.
   - Finding: the random forest is explicitly trained to learn **how to
     blend** these three streams rather than weight them by hand — described
     as outperforming any single stream alone. This is essentially the
     blueprint for "Elo + Transfermarkt market value + FIFA rank + bookmaker
     odds → GBT," i.e., almost exactly what this research recommends for our
     pipeline, applied at full World Cup scale.

5. **Leitner, C., Zeileis, A., & Hornik, K. (2010).** "Forecasting sports
   tournaments by ratings of (prob)abilities: A comparison for the EURO
   2008." *International Journal of Forecasting*, 26(3), 471-481.
   - Introduces the "bookmaker consensus model" (de-vig + logit-average
     across many bookmakers) used as the bookmaker-odds component in #4
     above. Establishes bookmaker consensus as a strong, reproducible
     baseline for international tournament forecasting.

6. **"PELE International Football Rankings"** — Nate Silver, Silver
   Bulletin/natesilver.net (2026), methodology post "How we calculate our
   PELE ratings."
   - Data/features: blends an Elo-like results-based rating (designed to be
     comparable to World Football Elo / FIFA rankings) with **market values
     of each national team's top-23 players at their club teams** (using
     Transfermarkt-era data from 2005 onward), squad age (weighted by market
     value, used to project future improvement/decline), and — pre-2005 —
     country region/GDP/football-legacy factors.
   - Relevance: this is the most current (2026, World-Cup-specific), publicly
     documented "Elo + market value" blend, and explicitly frames market
     value as informing **offense/defense orientation** in addition to
     overall strength — a richer use of squad-value data than a single
     scalar.

7. **McSharry, P.E. (2007).** "Effect of altitude on physiological
   performance: a statistical analysis using results of international
   football games." *British Medical Journal* (PMC2151172).
   - Data/features: international match results + venue/team-country
     altitudes; modeled win probability, goals scored, and goals conceded as
     functions of the **altitude differential** between venue and each team's
     home-country altitude.
   - Finding: significant altitude-differential effects on match outcomes —
     teams from low-altitude countries are disadvantaged at high-altitude
     venues. Directly relevant to 2026 (Mexico City, Guadalajara venues).

8. **"Effect of Altitude on Football Performance: Analysis of the 2010 FIFA
   World Cup Data"** (Journal of Strength & Conditioning Research, 2013).
   - Examined physical/technical performance metrics at South African
     World Cup venues at varying altitudes (incl. Johannesburg ~1,750m);
     supports the general altitude-effect mechanism (reduced distance
     covered, altered ball flight/technical execution) cited in #7.

9. **Rest-days study of national-team World Cup/Euro matches (1930-2010 /
   1960-2012)** — found rest-day effects on performance concentrated when one
   team has ≤3 days rest; pre-1990s rest days mattered more (less effective
   athletic preparation then). Supports a **threshold/nonlinear** rest-days
   feature, well-suited to tree-based splits.

10. **Bunker, R. & Susnjak, T. / arXiv:2309.14807 (2024)** and **Bunker et
    al., "Machine Learning for Soccer Match Result Prediction" (arXiv:2403.07669,
    2024 survey)** — already covered in `ml_integration_research_notes.md`;
    re-flagged here because the survey explicitly calls for testing GBT/DL
    "on a range of datasets with different types of features" — i.e., the
    field's open question is precisely "what happens when you give a GBT
    *more and different* features," which is the question this document's
    ranked list (squad value, FIFA rank, odds, altitude, rest days) is
    designed to answer for our international-football panel.

---

## Summary table

| # | Source | Intl coverage | Access | Cost | Key new signal vs. Elo |
|---|---|---|---|---|---|
| 1 | Transfermarkt squad market value (`dcaribou/transfermarkt-datasets`) | Yes (national teams + WC/Euro/Copa/AFCON/Asian Cup tables) | Kaggle/DuckDB/CSV, free | Free | Current squad strength, updates faster than Elo, captures transfers/injuries indirectly |
| 2 | FIFA World Ranking points | Yes (it IS an intl ranking) | GitHub CSV / Kaggle, since 1992 | Free | Independent strength estimate w/ different methodology — disagreement w/ Elo is informative |
| 3 | Bookmaker-implied probabilities | Yes for major tournaments | Scrape/paid API — **check QK first** | Free-paid | Market-aggregated info on injuries/lineups/weather/motivation; literature's strongest single predictor |
| 4 | Venue altitude / altitude differential | Yes (any venue) | Static lookup, free | Free | Pure environment effect, zero Elo overlap; directly relevant to Mexico City/Guadalajara 2026 venues |
| 5 | Rest days / travel distance | Yes (universal) | Derivable from existing panel + small lookup | Free | Fatigue/congestion effects, nonlinear (≤3-day-rest threshold) |
| 6 | EA Sports FIFA/FC ratings | Indirect (player-level, map to squads) | Kaggle CSV dumps | Free | Squad quality signal, but likely redundant with #1 and updates less often |
| 7 | FBref advanced stats (xG/shots/possession) | Partial (post-2017, uneven by confederation) | worldfootballR/soccerdata scraping | Free | Rolling "current form" / underlying-performance overlay |
| 8 | Weather (temp/humidity) | Yes (universal) | Open-Meteo API, free | Free | Small effect, forecast-only for future matches — low priority |
