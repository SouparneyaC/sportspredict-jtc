# Sports Predict - 2026 World Cup probability markets

Source: `api.sportspredict.com` (public GET endpoints, no auth, no QK quota used).

Re-generate with `python3 fetch_betting_markets.py`.

## Jump Trading Probability Cup
- Event ID: `aa5572ec-5930-4d99-b06b-f8966333d172`
- Window: 2026-06-10T16:00:00.000Z -> 2026-07-19T15:59:00.000Z
- Total open markets: 720
- Distinct matches covered: 72
- Raw snapshot: `jumpcup_markets_raw.json`

| Category | # markets | Our data coverage | Notes |
|---|---:|---|---|
| Half-time / second-half splits & in-game timing | 236 | NO (data gap) | martj42 has no half-time scores or goal-minute data -> can't condition on in-match state without a new data source. |
| Shots (player/team) | 96 | NO (data gap) | No shot data in martj42 (goals + shootouts only). |
| Goals / BTTS / Over-Under (full match) | 73 | YES | Full-time scoreline distribution from Poisson model -> totals, BTTS, team totals (team-level 'score at least N goals' = 1 - P(team scores 0...N-1)). |
| Cards (yellow/red) | 67 | NO (data gap) | No disciplinary data in martj42. |
| Offsides | 61 | NO (data gap) | No match-event stats in martj42. |
| Match result (1X2 / win) | 58 | YES | Elo-based bivariate Poisson / DC97 scoreline model -> P(home win/draw/away win). |
| Fouls | 57 | NO (data gap) | No match-event stats in martj42. |
| Anytime goalscorer (player) | 37 | NO (data gap) | Requires player-level historical scoring rates / squad lists -> not in martj42. |
| Corners | 29 | NO (data gap) | No match-event stats in martj42. |
| Penalty awarded | 6 | NO (data gap) | No match-event stats in martj42. |

<details><summary>Examples per category</summary>

**Half-time / second-half splits & in-game timing**
- ENG vs CRO: "Will Harry Kane have at least 1 shot on target in the second half?" (closes 2026-06-17T20:00:00.000Z)
- ENG vs CRO: "Will England have more shots on target than Croatia in the second half?" (closes 2026-06-17T20:00:00.000Z)
- GHA vs PAN: "Will Panama score the first goal of the second half?" (closes 2026-06-17T23:00:00.000Z)

**Shots (player/team)**
- TUR vs PAR: "Will Julio Enciso have at least 1 shot on target?" (closes 2026-06-20T03:00:00.000Z)
- PAR vs AUS: "Will Julio Enciso have at least 1 shot on target?" (closes 2026-06-26T02:00:00.000Z)
- ALG vs AUT: "Will Algeria have 3 or more shots on target?" (closes 2026-06-28T02:00:00.000Z)

**Goals / BTTS / Over-Under (full match)**
- ENG vs CRO: "Will both teams score AND the match have 3 or more total goals?" (closes 2026-06-17T20:00:00.000Z)
- KOR vs CZE: "Will both teams score AND the match have 3 or more total goals?" (closes 2026-06-12T02:00:00.000Z)
- AUT vs JOR: "Will the match have 2 or fewer total goals?" (closes 2026-06-17T04:00:00.000Z)

**Cards (yellow/red)**
- ENG vs CRO: "Will a penalty kick be awarded OR a red card be shown?" (closes 2026-06-17T20:00:00.000Z)
- GHA vs PAN: "Will Panama receive more cards than Ghana?" (closes 2026-06-17T23:00:00.000Z)
- MEX vs RSA: "Will a penalty kick be awarded OR a red card be shown in the match?" (closes 2026-06-11T19:00:00.000Z)

**Offsides**
- GHA vs PAN: "Will Panama be caught offside 2 or more times?" (closes 2026-06-17T23:00:00.000Z)
- MEX vs RSA: "Will South Africa be caught offside 2 or more times?" (closes 2026-06-11T19:00:00.000Z)
- KOR vs CZE: "Will South Korea be caught offside 2 or more times?" (closes 2026-06-12T02:00:00.000Z)

**Match result (1X2 / win)**
- SUI vs BIH: "Will Switzerland win the match?" (closes 2026-06-18T19:00:00.000Z)
- CIV vs ECU: "Will Ivory Coast win the match?" (closes 2026-06-14T23:00:00.000Z)
- AUT vs JOR: "Will Austria win the match?" (closes 2026-06-17T04:00:00.000Z)

**Fouls**
- ENG vs CRO: "Will England commit more fouls than Croatia?" (closes 2026-06-17T20:00:00.000Z)
- TUN vs JPN: "Will Japan commit more fouls than Tunisia?" (closes 2026-06-21T04:00:00.000Z)
- GER vs Curacao: "Will Curaçao commit more fouls than Germany?" (closes 2026-06-14T17:00:00.000Z)

**Anytime goalscorer (player)**
- ESP vs CPV: "Will Dani Olmo score or assist a goal (excluding own goals)?" (closes 2026-06-15T16:00:00.000Z)
- MEX vs RSA: "Will Oswin Appollis score or assist a goal (excluding own goals)?" (closes 2026-06-11T19:00:00.000Z)
- KOR vs CZE: "Will Son Heung-min score a goal (excluding own goals)?" (closes 2026-06-12T02:00:00.000Z)

**Corners**
- USA vs PAR: "Will Paraguay finish with more corner kicks than United States?" (closes 2026-06-13T01:00:00.000Z)
- AUS vs TUR: "Will Türkiye finish with more corner kicks than Australia?" (closes 2026-06-14T04:00:00.000Z)
- IRN vs New Zealand: "Will New Zealand finish with more corner kicks than Iran?" (closes 2026-06-16T01:00:00.000Z)

**Penalty awarded**
- KOR vs CZE: "Will a penalty kick be awarded in the match?" (closes 2026-06-12T02:00:00.000Z)
- KSA vs URU: "Will a penalty kick be awarded in the match?" (closes 2026-06-15T22:00:00.000Z)
- SUI vs BIH: "Will a penalty kick be awarded in the match?" (closes 2026-06-18T19:00:00.000Z)

</details>

## Recommendation: which markets to target first

Based on current data coverage (martj42 results + computed PIT Elo, see `tournament_kfactor_map.csv`):

1. **Match result (1X2 / win)** - directly buildable now from the Elo + bivariate Poisson / ordered-logit pipeline (research_notes.md build order). Highest confidence, highest market count.
2. **Full-match goal totals & BTTS** (incl. team-level 'score at least N goals') - same Poisson scoreline model gives the full distribution over (home_goals, away_goals); totals/BTTS/team-totals are derived quantities, no extra data needed.

**Not recommended yet** (would need new data sources before we could do better than a coin flip): half-time/second-half splits, anytime goalscorer, shots, cards, fouls, offsides, corners, assists, penalties. These all require match-event or player-level data that martj42 doesn't provide - a future enrichment step (e.g. FBref/Opta-style data for the 2026 World Cup specifically).
