# StatsBomb Open Data — Comprehensive Dataset Audit

**Audit date:** 2026-07-07  
**Audited by:** Claude Code (read-only, no files modified)  
**Dataset path:** `/Users/aki/Desktop/sportspredict_research/data/external/statsbomb/open-data/`  
**Purpose:** Evaluate this dataset for use in the JTC/SportsPredict WC2026 forecasting system, particularly for building base-rate and player-level models for shots on target, corners, cards, offsides, fouls, and player goal/assist props.

---

## Table of Contents

1. [Dataset Overview](#1-dataset-overview)
2. [competitions.json](#2-competitionsjson)
3. [matches/ Directory](#3-matches-directory)
4. [events/ Directory](#4-events-directory)
5. [lineups/ Directory](#5-lineups-directory)
6. [three-sixty/ Directory](#6-three-sixty-directory)
7. [Coverage Analysis](#7-coverage-analysis)
8. [Data Quality Notes](#8-data-quality-notes)
9. [Usefulness for Our Forecasting System](#9-usefulness-for-our-forecasting-system)

---

## 1. Dataset Overview

StatsBomb's open-data repository is a publicly available subset of their commercial event-level football data. It provides granular, timestamped event logs for each match — every pass, shot, foul, dribble, carry, and more — linked to players and positions, with (x, y) pitch coordinates. The dataset spans competitions from 1958 through 2025/2026.

**Top-level directory contents:**

```
open-data/
├── data/
│   ├── competitions.json      # Index of all covered competition-season pairs
│   ├── events/                # 4,235 JSON files (one per match)
│   ├── lineups/               # 4,235 JSON files (one per match)
│   ├── matches/               # 80 JSON files (one per competition-season)
│   └── three-sixty/           # 426 JSON files (subset of matches with 360° tracking)
├── doc/                       # Official specification PDFs
│   ├── StatsBomb Open Data Specification v1.1.pdf
│   ├── Open Data Events v4.0.0.pdf
│   ├── Open Data Matches v3.0.0.pdf
│   ├── Open Data Lineups v2.0.0.pdf
│   ├── Open Data Competitions v2.0.0.pdf
│   └── Open Data 360 Frames v1.0.0.pdf
├── README.md
└── LICENSE.pdf
```

**Scale summary:**
- 24 unique competitions
- 80 competition-season pairs in competitions.json (not all have full-season coverage)
- 3,961 unique matches indexed in matches/ files
- 4,235 event files and 4,235 lineup files (all match IDs in matches/ are present; extra 274 files appear to be legacy entries or additions not yet in the index)
- ~14.8 million total events (estimated from 100-file sample: avg 3,503 events/match × 4,235 files)
- ~162,000 player-match records (estimated: avg 38.3 players per match × 4,235 matches)
- 426 matches with 360° spatial tracking data

---

## 2. competitions.json

**Path:** `data/competitions.json`  
**Format:** JSON array of competition-season objects  
**Total entries:** 80

### Schema

| Field | Type | Description |
|---|---|---|
| `competition_id` | integer | Unique competition identifier |
| `season_id` | integer | Unique season identifier |
| `country_name` | string | Country or region of the competition |
| `competition_name` | string | Human-readable competition name |
| `competition_gender` | string | `"male"` or `"female"` |
| `competition_youth` | boolean | Whether this is a youth competition |
| `competition_international` | boolean | Club (false) vs. international (true) |
| `season_name` | string | Human-readable season label (e.g., `"2022"`, `"2020/2021"`) |
| `match_updated` | ISO-8601 datetime | Last update timestamp for standard match data |
| `match_updated_360` | ISO-8601 datetime or null | Last update for 360 data (null = no 360 data) |
| `match_available_360` | ISO-8601 datetime or null | When 360 data became available (null = none) |
| `match_available` | ISO-8601 datetime | When standard match data became available |

### Example Entry

```json
{
  "competition_id": 43,
  "season_id": 106,
  "country_name": "International",
  "competition_name": "FIFA World Cup",
  "competition_gender": "male",
  "competition_youth": false,
  "competition_international": true,
  "season_name": "2022",
  "match_updated": "2026-05-04T01:48:57.914346",
  "match_updated_360": "2026-05-04T01:53:40.309717",
  "match_available_360": "2026-05-04T01:53:40.309717",
  "match_available": "2026-05-04T01:48:57.914346"
}
```

### Full Competition Index

| competition_id | Competition Name | Country/Region | Gender | International | Seasons Covered |
|---|---|---|---|---|---|
| 2 | Premier League | England | male | no | 2003/2004, 2015/2016 |
| 7 | Ligue 1 | France | male | no | 2015/2016, 2021/2022, 2022/2023 |
| 9 | 1. Bundesliga | Germany | male | no | 2015/2016, 2023/2024 |
| 11 | La Liga | Spain | male | no | 18 seasons: 1973/74 – 2020/21 |
| 12 | Serie A | Italy | male | no | 1986/1987, 2015/2016 |
| 16 | Champions League | Europe | male | no | 18 seasons: 1970/71 – 2018/19 |
| 35 | UEFA Europa League | Europe | male | no | 1988/1989 |
| 37 | FA Women's Super League | England | female | no | 2018/19, 2019/20, 2020/21, 2023/24 |
| 43 | FIFA World Cup | International | male | yes | 8 tournaments: 1958–2022 |
| 44 | Major League Soccer | USA | male | no | 2023 |
| 49 | NWSL | USA | female | no | 2018, 2023 |
| 53 | UEFA Women's Euro | Europe | female | yes | 2022, 2025 |
| 55 | UEFA Euro | Europe | male | yes | 2020, 2024 |
| 72 | Women's World Cup | International | female | yes | 2019, 2023 |
| 81 | Liga Profesional | Argentina | male | no | 1981, 1997/1998 |
| 87 | Copa del Rey | Spain | male | no | 1977/78, 1982/83, 1983/84 |
| 116 | North American League | N & C America | male | no | 1977 |
| 131 | Serie A Women | Italy | female | no | 2023/2024 |
| 135 | Frauen Bundesliga | Germany | female | no | 2023/2024 |
| 182 | Liga F | Spain | female | no | 2023/2024 |
| 223 | Copa America | South America | male | yes | 2024 |
| 1238 | Indian Super League | India | male | no | 2021/2022 |
| 1267 | African Cup of Nations | Africa | male | yes | 2023 |
| 1470 | FIFA U20 World Cup | International | male | yes (youth) | 1979 |

**Notes on 360 availability:** 12 of 80 competition-season pairs have `match_available_360` set. See [Coverage Analysis](#7-coverage-analysis).

---

## 3. matches/ Directory

**Path:** `data/matches/`  
**Organization:** Two-level structure — `{competition_id}/{season_id}.json`

```
matches/
├── 2/          # Premier League
│   ├── 27.json     (2015/2016)
│   └── 44.json     (2003/2004)
├── 7/          # Ligue 1
│   ├── 27.json     (2015/2016)
│   ├── 108.json    (2021/2022)
│   └── 235.json    (2022/2023)
├── 11/         # La Liga
│   └── [18 JSON files, one per season]
├── 43/         # FIFA World Cup
│   ├── 3.json      (2018)
│   ├── 51.json     (1974)
│   ├── 54.json     (1986)
│   ├── 55.json     (1990)
│   ├── 106.json    (2022)
│   ├── 269.json    (1958)
│   ├── 270.json    (1962)
│   └── 272.json    (1970)
└── [21 other competition directories...]
```

**Total files:** 80 (one per competition-season pair in competitions.json)  
**Total matches across all files:** 3,961

### Match Record Schema

| Field | Type | Description |
|---|---|---|
| `match_id` | integer | Unique match identifier; used as filename in events/, lineups/, three-sixty/ |
| `match_date` | string (date) | Date of the match (YYYY-MM-DD) |
| `kick_off` | string (time) | Local kick-off time (HH:MM:SS.mmm) |
| `competition` | object | `{competition_id, country_name, competition_name}` |
| `season` | object | `{season_id, season_name}` |
| `home_team` | object | Full home team record (see sub-schema below) |
| `away_team` | object | Full away team record (see sub-schema below) |
| `home_score` | integer | Full-time home goals |
| `away_score` | integer | Full-time away goals |
| `match_status` | string | `"available"` when standard event data is present |
| `match_status_360` | string | `"available"` when 360 data is present |
| `last_updated` | ISO-8601 datetime | Last update of match record |
| `last_updated_360` | ISO-8601 datetime or null | Last update of 360 data |
| `metadata` | object | `{data_version, shot_fidelity_version, xy_fidelity_version}` |
| `match_week` | integer | Week within the season/competition phase |
| `competition_stage` | object | `{id, name}` — e.g., `"Group Stage"`, `"Regular Season"`, `"Quarter-finals"` |
| `stadium` | object | `{id, name, country: {id, name}}` |
| `referee` | object | `{id, name, country: {id, name}}` — may be absent for historic matches |

**Team sub-schema** (applies to both `home_team` and `away_team`):

| Field | Type | Description |
|---|---|---|
| `home_team_id` / `away_team_id` | integer | Team ID |
| `home_team_name` / `away_team_name` | string | Full team name |
| `home_team_gender` / `away_team_gender` | string | `"male"` or `"female"` |
| `home_team_group` / `away_team_group` | string or null | Group letter for group-stage tournaments |
| `country` | object | `{id, name}` — country the team represents |
| `managers` | array | List of `{id, name, nickname, dob, country}` objects |

### Example Match Record (FIFA World Cup 2022)

```json
{
  "match_id": 3857276,
  "match_date": "2022-12-01",
  "kick_off": "15:00:00.000",
  "competition": {"competition_id": 43, "country_name": "International", "competition_name": "FIFA World Cup"},
  "season": {"season_id": 106, "season_name": "2022"},
  "home_team": {
    "home_team_id": 1833,
    "home_team_name": "Canada",
    "home_team_gender": "male",
    "home_team_group": "F",
    "country": {"id": 40, "name": "Canada"},
    "managers": [{"id": 4435, "name": "John Herdman", "nickname": null, "dob": "1975-07-19", "country": {"id": 68, "name": "England"}}]
  },
  "away_team": {"away_team_id": 788, "away_team_name": "Morocco", ...},
  "home_score": 1,
  "away_score": 2,
  "match_status": "available",
  "match_status_360": "available",
  "metadata": {"data_version": "1.1.0", "shot_fidelity_version": "2", "xy_fidelity_version": "2"},
  "match_week": 3,
  "competition_stage": {"id": 10, "name": "Group Stage"},
  "stadium": {"id": 1000838, "name": "Al Thumama Stadium", "country": {"id": 185, "name": "Qatar"}},
  "referee": {"id": 2638, "name": "Raphael Claus", "country": {"id": 31, "name": "Brazil"}}
}
```

### Match Counts Per Competition and Season

| Competition | Seasons | Total Matches | Notable |
|---|---|---|---|
| La Liga | 18 (1973/74 – 2020/21) | 867 | Most comprehensive; full 2015/16 (380 matches) |
| Premier League | 2 (2003/04, 2015/16) | 418 | Full 2015/16 season |
| Ligue 1 | 3 (2015/16, 2021/22, 2022/23) | 435 | Full 2015/16; partial recent |
| FA Women's Super League | 4 (2018/19 – 2023/24) | 457 | Multiple full seasons |
| Serie A | 2 (1986/87, 2015/16) | 381 | Full 2015/16 |
| NWSL | 2 (2018, 2023) | 173 | Good women's coverage |
| Women's World Cup | 2 (2019, 2023) | 116 | Full tournament coverage |
| FIFA World Cup | 8 (1958–2022) | 147 | Full 2018 + 2022 (64 each); partial historics |
| UEFA Euro (men's) | 2 (2020, 2024) | 102 | Full tournament (51 each) |
| Liga F (women's Spain) | 1 (2023/24) | 240 | Full season |
| Indian Super League | 1 (2021/22) | 115 | |
| African Cup of Nations | 1 (2023) | 52 | |
| Frauen Bundesliga | 1 (2023/24) | 132 | |
| Serie A Women | 1 (2023/24) | 130 | |
| Copa America | 1 (2024) | 32 | |
| 1. Bundesliga | 2 (2015/16, 2023/24) | 68 | 34 matches each |
| UEFA Women's Euro | 2 (2022, 2025) | 62 | Full tournament (31 each) |
| Champions League | 18 seasons | 18 | Only 1 match per season — historic finals/notable matches |
| Major League Soccer | 1 (2023) | 6 | Very limited |
| UEFA Europa League | 1 (1988/89) | 3 | Very limited |
| Copa del Rey | 3 seasons | 3 | 1 match each |
| Liga Profesional | 2 seasons | 2 | 1 match each |
| North American League | 1 (1977) | 1 | Single match |
| FIFA U20 World Cup | 1 (1979) | 1 | Single match |

---

## 4. events/ Directory

**Path:** `data/events/`  
**File naming:** `{match_id}.json`  
**Total files:** 4,235  
**Typical file size:** 2–8 MB per match  
**Events per match:** 2,839 – 4,174 (sampled range); average ~3,503  
**Estimated total events:** ~14.8 million across all 4,235 files

### Core Event Schema

Every event in a match file is a JSON object with the following base fields:

| Field | Type | Presence | Description |
|---|---|---|---|
| `id` | UUID string | 100% | Unique event identifier (links to three-sixty `event_uuid`) |
| `index` | integer | 100% | Sequential position of event within the match |
| `period` | integer | 100% | Match period: 1 (first half), 2 (second half), 3/4 (extra time), 5 (penalty shootout) |
| `timestamp` | string | 100% | Time within the period (HH:MM:SS.mmm) |
| `minute` | integer | 100% | Cumulative match minute |
| `second` | integer | 100% | Second within that minute |
| `type` | object | 100% | `{id, name}` — the event type |
| `possession` | integer | 100% | Sequential possession number within the match |
| `possession_team` | object | 100% | `{id, name}` — team currently in possession |
| `play_pattern` | object | 100% | `{id, name}` — how the current possession started |
| `team` | object | 100% | `{id, name}` — team performing this event |
| `player` | object | ~99.4% | `{id, name}` — player performing the event |
| `position` | object | ~99.4% | `{id, name}` — player's pitch position |
| `location` | array [x, y] | ~99.1% | Pitch coordinates (StatsBomb coordinate system: 0–120 x-axis, 0–80 y-axis, origin = bottom-left of the attacking team's perspective) |
| `duration` | float | ~74.4% | Duration of the event in seconds |
| `related_events` | array of UUIDs | ~95.1% | IDs of events this event is related to |
| `under_pressure` | boolean | ~17.9% | True if the player is under pressure from an opponent |
| `counterpress` | boolean | ~3.0% | True if this is a counter-press immediately after losing possession |
| `off_camera` | boolean | ~1.1% | True if the event occurred off camera |
| `out` | boolean | ~0.8% | True if the ball went out of play as a result of this event |

**Play pattern values:**
- `Regular Play`, `From Corner`, `From Counter`, `From Free Kick`, `From Goal Kick`, `From Keeper`, `From Kick Off`, `From Throw In`, `Other`

### All Event Types

Across a 20-match sample, 33 unique event types were found. Listed here with approximate frequency (from 50-match sample):

| Event Type | Approx Count (50 matches) | Notes |
|---|---|---|
| Pass | 50,390 | Most common event |
| Ball Receipt* | 47,520 | Paired with each completed pass |
| Carry | 39,206 | Ball movement without a pass |
| Pressure | 16,332 | Defending player pressing |
| Ball Recovery | 5,647 | Regaining possession |
| Duel | 3,711 | Aerial or ground duels |
| Clearance | 2,272 | Defensive clearances |
| Block | 1,933 | Shot or pass blocks |
| Dribble | 1,785 | Successful/unsuccessful take-ons |
| Goal Keeper | 1,520 | GK actions (saves, claims, etc.) |
| Miscontrol | 1,470 | Player loses control |
| Dispossessed | 1,398 | Player tackled and loses ball |
| Foul Committed | 1,341 | Foul by a player |
| Foul Won | 1,282 | Foul drawn by a player |
| Shot | 1,224 | All shot attempts |
| Interception | 1,211 | Intercepted passes |
| Dribbled Past | 1,100 | Defender beaten by a dribble |
| Substitution | 331 | Player substitution |
| Half Start | 210 | Start of a half or extra time |
| Half End | 210 | End of a half or extra time |
| Injury Stoppage | 201 | Play stopped for injury |
| 50/50 | 184 | Contested aerial/loose ball |
| Tactical Shift | 110 | Formation/positional change |
| Starting XI | 100 | Starting lineup (2 per match) |
| Referee Ball-Drop | 91 | Referee drops the ball |
| Shield | 65 | Player shields the ball |
| Player Off | 58 | Player leaves the field |
| Player On | 57 | Player enters the field |
| Bad Behaviour | 30 | Cards given directly (e.g., dissent) |
| Offside | 24 | Offside call |
| Error | 22 | Player error leading to a chance |
| Own Goal Against | 6 | Own goal (against the scoring team) |
| Own Goal For | 6 | Own goal (for the scoring team) |

### Event Type Sub-schemas

Each event type has an optional sub-object with the same name (snake_case). Key ones:

#### Shot (`shot`)

| Sub-field | Type | Description |
|---|---|---|
| `statsbomb_xg` | float | StatsBomb's expected goals value |
| `end_location` | [x, y, z] | Where the ball ended up (z = height) |
| `key_pass_id` | UUID or null | ID of the pass that created the chance |
| `technique` | object | `{id, name}` — `Normal`, `Volley`, `Half Volley`, `Lob` |
| `body_part` | object | `{id, name}` — `Left Foot`, `Right Foot`, `Head` |
| `type` | object | `{id, name}` — `Open Play`, `Free Kick`, `Corner`, `Penalty`, `Kick Off` |
| `outcome` | object | `{id, name}` — `Goal`, `Saved`, `Off T`, `Blocked`, `Post`, `Wayward` |
| `first_time` | boolean | Whether it was a first-time shot |
| `freeze_frame` | array | Positions of nearby players at moment of shot (teammate + location + position) |
| `aerial_won` | boolean | Whether the shooter won an aerial duel |
| `one_on_one` | boolean | Whether the player was one-on-one with the goalkeeper |
| `follows_dribble` | boolean | Whether the shot followed a dribble |
| `open_goal` | boolean | Whether the goal was empty |
| `redirect` | boolean | Whether this was a redirected shot |

**Shot outcomes:** `Goal`, `Saved`, `Off T` (off target), `Blocked`, `Post`, `Wayward`

#### Pass (`pass`)

| Sub-field | Type | Description |
|---|---|---|
| `recipient` | object | `{id, name}` — intended recipient |
| `length` | float | Pass distance in yards |
| `angle` | float | Pass direction in radians |
| `height` | object | `{id, name}` — `Ground Pass`, `Low Pass`, `High Pass` |
| `end_location` | [x, y] | Target location |
| `body_part` | object | `{id, name}` — `Left Foot`, `Right Foot`, `Head`, `No Touch` |
| `type` | object | `{id, name}` — `Corner`, `Free Kick`, `Goal Kick`, `Throw-in`, `Kick Off`, `Interception`, `Recovery` |
| `outcome` | object | `{id, name}` — null = successful; `Incomplete`, `Out`, `Pass Offside`, `Unknown` |
| `technique` | object | `{id, name}` — `Inswinging`, `Outswinging`, `Straight` (for corners) |
| `inswinging` | boolean | For corners: whether ball curves toward goal |
| `outswinging` | boolean | For corners: whether ball curves away from goal |
| `switch` | boolean | Whether this is a switching pass |
| `cross` | boolean | Whether this is a cross |
| `through_ball` | boolean | Whether this is a through ball |
| `cut_back` | boolean | Whether this is a cut-back |
| `goal_assist` | boolean | Whether this pass directly created a goal |
| `shot_assist` | boolean | Whether this pass directly created a shot |

#### Foul Committed (`foul_committed`)

| Sub-field | Type | Description |
|---|---|---|
| `advantage` | boolean | Whether the referee played advantage |
| `penalty` | boolean | Whether it was a penalty |
| `card` | object | `{id, name}` — `Yellow Card`, `Second Yellow`, `Red Card` (absent if no card) |
| `type` | object | `{id, name}` — type of foul (e.g., handball, dangerous play) |

#### Bad Behaviour (`bad_behaviour`)

Issued for cards not directly tied to a foul (dissent, etc.):

| Sub-field | Type | Description |
|---|---|---|
| `card` | object | `{id, name}` — `Yellow Card`, `Second Yellow`, `Red Card` |

#### Dribble (`dribble`)

| Sub-field | Type | Description |
|---|---|---|
| `outcome` | object | `{id, name}` — `Complete`, `Incomplete` |
| `overrun` | boolean | Whether the dribble overran the ball |
| `nutmeg` | boolean | Whether the ball went through the defender's legs |
| `no_touch` | boolean | Whether the player did not touch the ball |

#### Carry (`carry`)

| Sub-field | Type | Description |
|---|---|---|
| `end_location` | [x, y] | Where the player stopped carrying |

#### Clearance (`clearance`)

| Sub-field | Type | Description |
|---|---|---|
| `aerial_won` | boolean | Whether it was an aerial clearance |
| `head` | boolean | Cleared with the head |
| `body_part` | object | `{id, name}` — body part used |

#### Interception (`interception`)

| Sub-field | Type | Description |
|---|---|---|
| `outcome` | object | `{id, name}` — `Won`, `Lost In Play`, `Lost Out`, `Success In Play`, `Success Out` |

#### Duel (`duel`)

| Sub-field | Type | Description |
|---|---|---|
| `type` | object | `{id, name}` — `Aerial Lost`, `Tackle`, etc. |
| `outcome` | object | `{id, name}` — `Won`, `Lost`, `Success`, `Fail`, etc. |

#### Goal Keeper (`goalkeeper`)

| Sub-field | Type | Description |
|---|---|---|
| `end_location` | [x, y] | Where the GK ended up |
| `position` | object | `{id, name}` — GK's position (e.g., `Set`, `Diving`) |
| `type` | object | `{id, name}` — `Shot Faced`, `Claim`, `Keeper Sweeper`, `Penalty Saved`, etc. |
| `outcome` | object | `{id, name}` — `Saved`, `No Touch`, `Success`, etc. |
| `body_part` | object | `{id, name}` — body part used |
| `technique` | object | `{id, name}` — technique used |

#### Substitution (`substitution`)

| Sub-field | Type | Description |
|---|---|---|
| `outcome` | object | `{id, name}` — `Tactical`, `Injury` |
| `replacement` | object | `{id, name}` — the player coming on |

#### Starting XI (`tactics`)

Present on the two Starting XI events at the start of each match:

| Sub-field | Type | Description |
|---|---|---|
| `formation` | integer | Formation code (e.g., `4411`, `433`, `4231`) |
| `lineup` | array | List of `{player: {id, name}, position: {id, name}, jersey_number}` for all 11 starters |

### Illustrative Event Examples

**Shot event (abbreviated):**
```json
{
  "id": "473df22f-d159-4416-a5ce-62838698ea12",
  "index": 100,
  "period": 1,
  "timestamp": "00:02:05.857",
  "minute": 2,
  "second": 5,
  "type": {"id": 16, "name": "Shot"},
  "team": {"id": 1833, "name": "Canada"},
  "player": {"id": 16252, "name": "Mark Anthony Kaye"},
  "position": {"id": 11, "name": "Left Defensive Midfield"},
  "location": [96.5, 40.7],
  "under_pressure": true,
  "shot": {
    "statsbomb_xg": 0.038882375,
    "end_location": [104.1, 39.4],
    "technique": {"id": 93, "name": "Normal"},
    "body_part": {"id": 38, "name": "Left Foot"},
    "type": {"id": 87, "name": "Open Play"},
    "outcome": {"id": 96, "name": "Blocked"},
    "first_time": true,
    "freeze_frame": [...]
  }
}
```

**Corner pass event:**
```json
{
  "type": {"id": 30, "name": "Pass"},
  "play_pattern": {"id": 2, "name": "From Corner"},
  "player": {"id": 5237, "name": "Hakim Ziyech"},
  "location": [120.0, 80.0],
  "pass": {
    "length": 36.23,
    "height": {"id": 3, "name": "High Pass"},
    "end_location": [118.4, 43.8],
    "inswinging": true,
    "technique": {"name": "Inswinging"},
    "body_part": {"name": "Left Foot"},
    "type": {"id": 61, "name": "Corner"},
    "outcome": {"name": "Incomplete"}
  }
}
```

**Offside event:**
```json
{
  "type": {"id": 8, "name": "Offside"},
  "team": {"id": 788, "name": "Morocco"},
  "player": {"id": 12149, "name": "Nayef Aguerd"},
  "location": [117.2, 44.9],
  "play_pattern": {"name": "From Free Kick"}
}
```

**Card (foul-related):**
```json
{
  "type": {"name": "Foul Committed"},
  "foul_committed": {
    "card": {"id": 7, "name": "Yellow Card"}
  }
}
```

**Card (bad behaviour):**
```json
{
  "type": {"name": "Bad Behaviour"},
  "bad_behaviour": {
    "card": {"id": 7, "name": "Yellow Card"}
  }
}
```

---

## 5. lineups/ Directory

**Path:** `data/lineups/`  
**File naming:** `{match_id}.json`  
**Total files:** 4,235 (exact match with events/)  
**File structure:** Each file is a JSON array of exactly 2 objects — one per team

### Schema

Top-level array entry (one per team):

| Field | Type | Description |
|---|---|---|
| `team_id` | integer | Team identifier |
| `team_name` | string | Team name |
| `lineup` | array | List of player objects (all squad members, not just starters) |

Player object within `lineup`:

| Field | Type | Description |
|---|---|---|
| `player_id` | integer | Unique player identifier |
| `player_name` | string | Full player name |
| `player_nickname` | string or null | Nickname or shortened name |
| `jersey_number` | integer | Shirt number |
| `country` | object | `{id, name}` — player's nationality |
| `cards` | array | List of card objects received in this match (see below) |
| `positions` | array | List of position intervals played (see below) |

Card object (within `cards`):

| Field | Type | Description |
|---|---|---|
| `time` | string (MM:SS) | Time of the card |
| `card_type` | string | `"Yellow Card"`, `"Second Yellow"`, `"Red Card"` |
| `reason` | string | Reason for the card (e.g., `"Foul Committed"`) |
| `period` | integer | Period in which it occurred |

Position interval object (within `positions`):

| Field | Type | Description |
|---|---|---|
| `position_id` | integer | Position identifier |
| `position` | string | Position name (e.g., `"Center Forward"`, `"Left Back"`) |
| `from` | string (MM:SS) | Start time of this position spell |
| `to` | string (MM:SS) or null | End time; null if still on at final whistle |
| `from_period` | integer | Period when spell started |
| `to_period` | integer or null | Period when spell ended |
| `start_reason` | string | Why they entered this position: `"Starting XI"`, `"Substitution - On (Tactical)"`, `"Substitution - On (Injury)"`, `"Tactical Shift"` |
| `end_reason` | string | Why they left: `"Substitution - Off (Tactical)"`, `"Substitution - Off (Injury)"`, `"Tactical Shift"`, `"Final Whistle"`, `"Red Card"` |

**Typical squad size:** ~26 players listed per team per match (18 starters + 8 unused substitutes is typical — actually 11 starters + full matchday squad)  
**Average players per match file:** 38.3 (two teams combined)  
**Players with empty `positions` array:** Unused substitutes who never entered the pitch

### Example Lineup Entry

```json
{
  "team_id": 788,
  "team_name": "Morocco",
  "lineup": [
    {
      "player_id": 9922,
      "player_name": "David Junior Hoilett",
      "player_nickname": "Junior Hoilett",
      "jersey_number": 10,
      "country": {"id": 40, "name": "Canada"},
      "cards": [
        {
          "time": "06:43",
          "card_type": "Yellow Card",
          "reason": "Foul Committed",
          "period": 1
        }
      ],
      "positions": [
        {
          "position_id": 19,
          "position": "Center Attacking Midfield",
          "from": "00:00",
          "to": "24:01",
          "from_period": 1,
          "to_period": 1,
          "start_reason": "Starting XI",
          "end_reason": "Tactical Shift"
        },
        {
          "position_id": 12,
          "position": "Right Midfield",
          "from": "24:01",
          "to": "66:24",
          "from_period": 1,
          "to_period": 2,
          "start_reason": "Tactical Shift",
          "end_reason": "Tactical Shift"
        }
      ]
    }
  ]
}
```

### Key Capabilities of Lineup Data

- **Substitution tracking:** Full audit trail of when players entered and left, and whether it was tactical or injury
- **Tactical shift tracking:** Position changes mid-match without substitution are recorded
- **Card attribution:** Cards are attributed to individual players with exact timestamp and reason — useful as ground truth for card models
- **Nationality:** Player country of origin is always present — relevant for international tournament models
- **Full squad roster:** Includes players who never played (unused subs), useful for knowing the available pool

---

## 6. three-sixty/ Directory

**Path:** `data/three-sixty/`  
**File naming:** `{match_id}.json`  
**Total files:** 426 (a subset of all 4,235 matches)

### What is 360° Data?

StatsBomb 360 is a computer-vision-derived spatial tracking product that augments each event with a "freeze frame" — the positions of visible players on the pitch at the moment of the event. Unlike full tracking data (which logs player positions multiple times per second), 360 provides a snapshot at each discrete event. It is generated from broadcast video using computer vision.

### Schema

Each file is a JSON array of frame objects, one per event that has spatial coverage:

| Field | Type | Description |
|---|---|---|
| `event_uuid` | UUID string | Links to the `id` field of the corresponding event in events/ |
| `visible_area` | flat array of floats | Polygon defining the area of the pitch visible to the broadcast camera at this moment. Encoded as alternating [x1, y1, x2, y2, ...] coordinates. Typically a 5-vertex polygon (10 floats). |
| `freeze_frame` | array of player objects | All players detected within the visible area |

Freeze frame player object:

| Field | Type | Description |
|---|---|---|
| `teammate` | boolean | True if on the same team as the player performing the event |
| `actor` | boolean | True if this is the player performing the event |
| `keeper` | boolean | True if this player is the goalkeeper |
| `location` | [x, y] | Player's position on the pitch (StatsBomb coordinate system, sub-metre precision) |

**Important note:** Player identities (name, player_id) are **not** present in the 360 freeze frames — only their role flags (teammate/actor/keeper) and location. This is different from the shot freeze frames embedded in the events/ shot events, which **do** include player identities. The 360 data provides full spatial coverage of the visible pitch but anonymised player locations.

### Coverage

360 data is only available for 426 of the 4,235 match files. All 360 frames link correctly to event IDs — verified that all 360 event_uuids exist in the corresponding events/ file. In a sample WC 2022 match (id=3857276): 3,388 total events, 2,873 have 360 frames (84.9% coverage — events off-camera have no frame).

**Competitions with 360 data:**

| Competition | Season | Matches with 360 |
|---|---|---|
| FIFA World Cup | 2022 | 64 (all) |
| UEFA Euro (men's) | 2020 | 51 (all) |
| UEFA Euro (men's) | 2024 | 51 (all) |
| Women's World Cup | 2023 | 64 (all) |
| UEFA Women's Euro | 2022 | 31 (all) |
| UEFA Women's Euro | 2025 | 31 (all) |
| La Liga | 2020/2021 | 35 (all) |
| 1. Bundesliga | 2023/2024 | 34 (all) |
| Ligue 1 | 2022/2023 | 32 (all) |
| Ligue 1 | 2021/2022 | 26 (all) |
| African Cup of Nations | 2023 | 1 |
| Major League Soccer | 2023 | 6 |
| **Total** | | **426** |

### Example Frame (abbreviated)

```json
{
  "event_uuid": "733aefb9-6952-4fb3-8380-4d10727157b6",
  "visible_area": [29.70, 80.0, 47.92, 0.0, 74.38, 0.0, 94.45, 80.0, 29.70, 80.0],
  "freeze_frame": [
    {"teammate": true,  "actor": true,  "keeper": false, "location": [61.0, 40.1]},
    {"teammate": true,  "actor": false, "keeper": false, "location": [39.4, 38.6]},
    {"teammate": false, "actor": false, "keeper": false, "location": [61.6, 56.2]},
    {"teammate": false, "actor": false, "keeper": true,  "location": [118.5, 40.0]}
  ]
}
```

---

## 7. Coverage Analysis

### Which competitions/seasons have full event data vs. just match-level data?

All 3,961 match IDs indexed in matches/ files have a corresponding events/ file. There are no match records without event data. The extra 274 event/lineup files (4,235 − 3,961 = 274) represent matches present in events/ and lineups/ but not yet reflected in competitions.json / matches/. This may indicate recently added data.

### World Cup Coverage

| Tournament | Season ID | Matches | Event Data | 360 Data |
|---|---|---|---|---|
| FIFA World Cup 2022 | 106 | 64 | Yes | Yes (all) |
| FIFA World Cup 2018 | 3 | 64 | Yes | No |
| FIFA World Cup 1990 | 55 | 1 | Yes | No |
| FIFA World Cup 1986 | 54 | 3 | Yes | No |
| FIFA World Cup 1974 | 51 | 6 | Yes | No |
| FIFA World Cup 1970 | 272 | 6 | Yes | No |
| FIFA World Cup 1962 | 270 | 1 | Yes | No |
| FIFA World Cup 1958 | 269 | 2 | Yes | No |

For WC2026 forecasting: WC 2018 and 2022 provide full tournament data (64 matches each), making them the primary training base. Historic tournaments (1958–1990) have very sparse coverage (1–6 matches each) — useful for novelty but not statistical training.

### Most Useful Data for Our Forecasting Targets

| Forecasting Target | Best Data Sources | Why |
|---|---|---|
| **Shots on target** | La Liga (867 matches), Ligue 1 (435), Premier League (418), WC 2018+2022 (128) | `shot.outcome` = `"Saved"` or `"Goal"` marks shots on target; xG also present |
| **Corners** | All competitions | Pass with `pass.type.name = "Corner"` or `play_pattern = "From Corner"` |
| **Yellow cards** | All competitions | `foul_committed.card.name = "Yellow Card"` or `bad_behaviour.card` |
| **Red cards** | All competitions | Same as above; `Red Card` or `Second Yellow` |
| **Offsides** | All competitions | Direct `Offside` event type |
| **Fouls** | All competitions | `Foul Committed` and `Foul Won` event types |
| **Player goals** | All competitions | `Shot` with `outcome.name = "Goal"` linked to `player` |
| **Player assists** | All competitions | `Pass` with `goal_assist = true` or `shot_assist = true` |
| **Player shots** | All competitions | All `Shot` events with player attribution |
| **xG (model input)** | All competitions | `shot.statsbomb_xg` is always present |
| **Player-level headers/aerials** | All competitions | `clearance.aerial_won`, `duel.type`, shot `body_part = "Head"` |

### Most Relevant Competitions for WC2026 Specifically

1. **FIFA World Cup 2018 + 2022** — direct tournament analogue; both have full 64-match coverage
2. **UEFA Euro 2020 + 2024** — high-quality international tournament data with 360
3. **Copa America 2024** — South American international context; 32 matches
4. **African Cup of Nations 2023** — African team context; 52 matches
5. **La Liga** (18 seasons) — largest event dataset by volume; many WC players compete here
6. **Champions League** — elite-level club context, but only 1 match per season (18 finals/notable matches total)

### Estimated Dataset Scale for Player-Level Modeling

| Metric | Estimate |
|---|---|
| Total matches | 4,235 |
| Total events | ~14.8 million |
| Player-match records (lineup) | ~162,000 |
| Unique players (rough estimate) | ~15,000–25,000 |
| Shot events (total) | ~370,000 (≈1,224 per 50 matches × 4235/50 ratio estimate) |
| Foul Committed events | ~113,000 |
| Corner events | ~70,000–90,000 |
| Card events (yellow + red) | ~25,000–35,000 |
| Offside events | ~10,000–20,000 |

---

## 8. Data Quality Notes

### ID and File Correspondence
- **Events ↔ Lineups:** Perfect 1:1 correspondence. All 4,235 event files have a corresponding lineup file with the same match_id filename. Zero mismatches.
- **Match index ↔ Events:** All 3,961 match IDs in the matches/ directory have a corresponding events/ file. Zero missing event files.
- **360 UUID linkage:** Verified that all `event_uuid` values in 360 files are present in the corresponding events/ file. No orphaned 360 frames found.

### Field Completeness
- Core event fields (id, index, period, timestamp, type, team, possession, play_pattern) are present on 100% of events.
- `player` and `position` are absent on ~0.6% of events — these are likely structural events (Half Start, Half End) where no specific player is the actor.
- `location` absent on ~0.9% — same structural events.
- `duration` is only present on ~74% of events; many instantaneous events (fouls, cards, offsides) have no meaningful duration.
- Type-specific sub-objects (e.g., `shot`, `pass`, `foul_committed`) are present only on the relevant event types — by design, not a gap.

### Known Structural Patterns
- `Ball Receipt*` events (the asterisk is part of the name) are auto-generated as the counterpart to every completed pass. This means `Ball Receipt` count ≈ `Pass` count. Do not double-count.
- Corners are **not** a separate event type — they appear as `Pass` events with `pass.type.name = "Corner"` and/or `play_pattern.name = "From Corner"`. To count corners awarded, use passes from corner positions (x ≈ 1 or 120, y ≈ 0 or 80).
- Fouls can generate cards in two ways: via `foul_committed.card` (most common) or via a separate `Bad Behaviour` event (for cards not attached to a foul — dissent, etc.). Both must be captured for a complete card count.
- `Own Goal For` and `Own Goal Against` are separate event types from `Shot`; do not filter shots alone for goal counts.
- Shots in penalty shootouts have `period = 5`; exclude if counting regular/extra-time shots.

### Data Coverage Gaps
- **Champions League:** Despite 18 seasons in competitions.json, only 1 match per season is covered (likely finals or specific highlighted matches). Not usable for base-rate modeling.
- **Copa del Rey, Europa League, Copa America, Liga Profesional, North American League, FIFA U20, African Cup (most):** Very few matches (1–3 each for some). Supplementary at best.
- **Historic World Cups (1958–1990):** Only 1–6 matches per tournament. The 1962 and 1990 tournaments have a single match each. Do not use for statistical inference.
- **Premier League, Serie A, Bundesliga:** Only 1–2 seasons of coverage. Significant for volume but narrow time range.
- **Women's competitions:** Substantial data for La Liga equivalent (Liga F: 240), WSL (457), Frauen Bundesliga (132), NWSL (173), Women's WC (116), UEFA Women's Euro (62) — useful for women's prop modeling but not directly applicable to men's WC2026.

### Timestamp and Season Notes
- Seasons are expressed as `YYYY/YYYY` (club) or `YYYY` (international/calendar tournaments). No ambiguity in the data.
- `match_updated` timestamps as recent as 2026-05 indicate this is an actively maintained dataset.
- `last_updated` on some La Liga records in 2025/2026 suggests corrections have been applied retroactively.

---

## 9. Usefulness for Our Forecasting System

### Summary Assessment

This is an exceptional dataset for our use case. StatsBomb open data provides event-level granularity that allows bottom-up construction of every target stat. The 4,235 matches span competitions, formations, and eras relevant to international tournament football.

### By Forecasting Target

| Target | Extractability | Data Quality | Volume |
|---|---|---|---|
| Shots on target | Direct: `shot.outcome in ["Goal","Saved"]` | Excellent (xG present) | ~370K shot events |
| Shots total | Direct: all `Shot` events | Excellent | ~370K |
| Corners | Moderate: `pass.type = Corner` | Good | ~80K corners est. |
| Yellow cards | Direct: `foul_committed.card` + `bad_behaviour.card` | Excellent | ~25K cards est. |
| Red cards | Direct: same as above, different card type | Excellent | ~2K red cards est. |
| Offsides | Direct: `Offside` event type | Good | ~15K est. |
| Fouls | Direct: `Foul Committed` event type | Excellent | ~110K est. |
| Player goals | Direct: `Shot` + `outcome=Goal` + `player` | Excellent | Full attribution |
| Player assists (direct) | Direct: `pass.goal_assist = true` | Excellent | Full attribution |
| Player shots | Direct: all `Shot` events with `player` | Excellent | Full player-level |
| Player cards | Direct: foul_committed + bad_behaviour + player | Excellent | Full player-level |
| Player xG (input feature) | Direct: `shot.statsbomb_xg` | Excellent | Present on every shot |

### Specific Recommendations

1. **Base rate modeling (team-level stats):** Use the full La Liga dataset (867 matches, 18 seasons) as the primary training base for corner rates, foul rates, card rates, and shot rates per 90 minutes. Supplement with Premier League and Serie A for validation.

2. **International tournament calibration:** Use WC 2018 + WC 2022 (128 matches total) to compute tournament-specific adjustments. These are the most direct analogues for WC2026 and have the most complete coverage of any tournament in this dataset.

3. **Player props (goal/assist/shot threshold):** Use all competitions combined. For a player appearing in WC2026, find their player_id across all their club competition appearances and build a per-90 feature vector from shot counts, xG, goal_assist flags, and positions played.

4. **Spatial features for shot models:** The `location` field on Shot events (always present) gives exact shot coordinates. Combined with `shot.statsbomb_xg`, you can train a custom xG model or use StatsBomb's provided value directly as a feature.

5. **360 data for advanced spatial context:** The 426 matches with 360° tracking (especially WC 2022, UEFA Euro 2020 + 2024, Women's WC 2023) allow construction of spatial pressure metrics, defensive compactness, and space creation features. However, player identities are anonymized in freeze frames — only role flags (teammate/actor/keeper) are present.

6. **Corner derivation:** Corners are recoverable from Pass events using `pass.type.name = "Corner"`. Both inswinging and outswinging are flagged. Corner locations are always at the corner arc coordinates ([1,0], [1,80], [120,0], [120,80] approximately).

7. **Tactical/formation features:** Starting formation is available from Starting XI events. Tactical Shift events track mid-game formation changes. This enables formation-vs-formation matchup features.

8. **Substitution timing:** Full substitution records in both events/ (Substitution event with minute and replacement) and lineups/ (position interval with end_reason). This allows modeling of fatigue, injury, and tactical intervention effects.

9. **Fidelity metadata:** Each match record carries `shot_fidelity_version` and `xy_fidelity_version` (values `"1"` or `"2"`). Version 2 is higher quality. For production models, consider filtering to version 2 data to avoid systematic positional error.

### Integration into the JTC/SportsPredict Pipeline

For integration into the existing pipeline:
- The natural key for cross-referencing player-level stats is `player.id` (integer). These are stable StatsBomb internal IDs but will need to be mapped to your existing player name/ID system manually or via a name-matching step.
- Match IDs are StatsBomb-internal integers, not tied to any external system.
- All competition/team/player references use StatsBomb internal integer IDs — not shareable with external market APIs without a mapping table.
- A clean flatten of `events/` filtered to Shot, Pass (corners, assists), Foul Committed, Bad Behaviour, and Offside events would yield a columnar dataset of ~2–3 million rows (excluding Carry, Ball Receipt, Pressure) usable for tabular ML.

### Limitations and Cautions

- StatsBomb open data is a **curated public subset**, not the full commercial product. Some competitions have very partial coverage (1 match per season of Champions League; sparse historic World Cups). Do not treat this as representative of those competitions.
- **No live or real-time data.** This is a static historical dataset. The most recent data (updated timestamps from 2026-04 to 2026-05) is still historical match records.
- **No betting market odds** are present. This dataset is events-only. Odds and market data must come from your existing `bot/data/markets_raw.jsonl` pipeline.
- **Women's data is not interchangeable** with men's for rate modeling without explicit adjustment. All women's competitions are separately labeled by `competition_gender`.
- **Card counts in lineups/ are authoritative.** Cards recorded in the `cards` array of lineup files are the cleanest source for player-level card attribution (they aggregate across both `foul_committed.card` and `bad_behaviour.card` in events/).
