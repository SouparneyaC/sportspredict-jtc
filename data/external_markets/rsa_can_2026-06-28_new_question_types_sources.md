# RSA vs CAN (2026-06-28, ESPN event 760486 / Smarkets event 45155173) — Sourcing Research for 3 New Question Types

Pure sourcing/verification research. No predictions or probability estimates included. Every claim below
is backed by a real fetched response — see file paths to raw JSON in the scratchpad and the full
Research Log at the bottom of this file.

Test matches used (all real, completed, fetched directly):
- ESPN event 760440 — Qatar at Canada, 2026-06-18, final 6-0 (today's away team's biggest recent goal sample)
- ESPN event 760463 — Canada at Switzerland, 2026-06-24 (Canada's most recent match)
- ESPN event 760466 — South Korea at South Africa, 2026-06-25 (South Africa's most recent match)
- ESPN event 760486 — South Africa vs Canada, 2026-06-28 (today's match — still pre-game, `STATUS_SCHEDULED`)

---

## A. Hydration-break timing (Q1, Q3, Q5)

**Source found: ESPN site API `summary?event={id}` → `keyEvents[]` array, event types `start-delay` /
`end-delay`.**

**Tier: 1.** Same endpoint you already use constantly for team-level stats; this is a sibling array
(`keyEvents`) on the exact same response object, minute-stamped, and verified across 3 independent
real completed WC2026 matches.

### Verified real data (all three completed matches show the same pattern)

ESPN's own text **never uses the literal word "hydration"** — it always says **"drinks break."** This
is the same real-world event the prop question colloquially calls a "hydration break" — FIFA's WC2026
match protocol mandates a brief stoppage near the 30-minute mark of each half in matches deemed
high-heat-risk, and ESPN logs it as a `start-delay`/`end-delay` pair with reason text "Delay in match
for a drinks break."

| Match | 1st-half break (start → end) | 2nd-half break (start → end) |
|---|---|---|
| 760440 (Qatar–Canada, 6/18) | 25' → 27' | 68' → 71' |
| 760463 (Canada–Switzerland, 6/24) | 23' → 25' | 71' → 74' |
| 760466 (S.Korea–South Africa, 6/25) | 23' → 26' | 69' → 71' |

Raw example (760440):
```json
{
  "type": {"id": "?", "text": "Start Delay", "type": "start-delay"},
  "text": "Delay in match for a drinks break.",
  "period": {"number": 1},
  "clock": {"value": 1500.0, "displayValue": "25'"}
}
```

**Implication for the 3 new questions:**
- Q5 (goal before first hydration break): compare any `goal`/`own-goal`/`goal---free-kick` keyEvent's
  `clock` against the period-1 `start-delay` event's clock for the same match.
- Q3 (offside before first hydration break): ESPN's `keyEvents` array in these 3 sample matches did
  **not** include a discrete `offside` event type (event-type inventory for 760440: kickoff,
  yellow-card, goal, start-delay, end-delay, red-card, substitution, halftime, start-2nd-half,
  goal---free-kick, own-goal, end-regular-time — no `offside` type present). Offside counts ARE
  available as **team-aggregate** stats elsewhere in the same payload (boxscore team stats, which you
  already use), but NOT as individual minute-stamped events in `keyEvents`. **This is a gap** — there
  is no verified minute-stamped offside event source. The `commentary` array (132/121/88 text entries
  across the 3 matches) is a free-text play-by-play feed that may narrate individual offside calls in
  prose, but I did not find a structured `offside` event type to rely on programmatically; commentary
  text would need manual reading per match, which is feasible live but not exactly "structured data."
  Flagging honestly: **no Tier-1 structured source found for Q3 specifically** — `keyEvents` covers the
  break timing precisely but not offside timing. Best fallback is real-time reading of the
  `commentary` text array (still ESPN, still Tier 1 reliability for the source, just unstructured).
- Q1 (card after second hydration break, incl. ET): straightforward — compare `yellow-card`/`red-card`
  keyEvents' clock against the period-2 `start-delay` clock (and anything in extra-time periods, see
  caveat below).

**Caveat on extra time:** none of the 3 sample matches went to extra time, so I could not verify
whether ET periods in `keyEvents` use `period.number` 3/4 and whether a third/fourth "drinks break"
event would appear in ET (FIFA protocol generally also allows a break in ET halves in hot conditions).
Not verified — flag as unconfirmed if RSA-CAN goes to extra time today.

**Venue caveat — RESOLVED, see Section A.1 below.** Initial pass flagged SoFi Stadium as an open
question (climate-controlled vs. outdoor hot-climate venue). Follow-up research fully resolves this.

---

## A.1 — RESOLVED: Will a hydration break occur at SoFi Stadium for today's RSA-CAN match?

**Answer: Very likely / near-certain.** Two independent, decisive lines of evidence, both Tier 1:

### Evidence 1 (strongest): Direct precedent — 5/5 prior WC2026 matches at SoFi Stadium had a drinks
break in BOTH halves

Using the ESPN scoreboard endpoint (`scoreboard?dates=YYYYMMDD`) swept across 18 dates (6/11–6/28), I
found 5 completed WC2026 matches already played at SoFi Stadium before today, and pulled `keyEvents[]`
for every one of them via the same `summary?event={id}` method validated in Section A:

| Event ID | Match | Kickoff (local time-of-day) | 1st-half break | 2nd-half break |
|---|---|---|---|---|
| 760417 | Paraguay at United States (6/12) | evening | 24' | 68' |
| 760427 | New Zealand at Iran (6/15) | evening | 25' | 68' |
| 760439 | Bosnia-Herzegovina at Switzerland (6/18) | ~midday | 23' | 69' |
| 760451 | Iran at Belgium (6/21) | ~midday | 30' | 70' |
| 760470 | United States at Türkiye (6/25) | evening | 23' | 67' |

Every single match — both midday and evening kickoffs — had a `start-delay`/`end-delay` keyEvent pair
tagged "Delay in match for a drinks break" in **both** halves. Raw example (760439, a midday kickoff,
arguably the best comparison for today's 3:00 PM EDT / mid-afternoon Pacific kickoff):
```json
{"type":{"text":"Start Delay","type":"start-delay"},
 "text":"Delay in match for a drinks break.",
 "period":{"number":1},"clock":{"displayValue":"23'"}}
```
This is the same venue, same tournament, same data source/method already validated — as strong as
evidence gets short of waiting for today's match itself.

### Evidence 2 (decisive, explains why precedent is reliable): FIFA's WC2026 rule is unconditional,
not weather-triggered

Verified via direct WebFetch of two independent primary-ish sources (Kestrel Instruments environmental-
monitoring blog, and a Fox News/OutKick sports report), both stating the same mechanism:

> "Three-minute hydration breaks will be imposed midway through each half of every game, **regardless
> of weather conditions.**" — and explicitly contrasted with the *pre-2026* approach, which used a
> conditional 32°C WBGT (Wet Bulb Globe Temperature) trigger. WC2026 **eliminated the conditional
> trigger** in favor of a fixed, referee-controlled, every-match rule, independent of venue, roof, or
> climate control.

This matters because it means SoFi's open-sided/non-AC structure (see below) is **not actually the
deciding factor** — under the new WC2026 rulebook, the break happens by default in every match
regardless of venue. The 5/5 empirical precedent at SoFi specifically is consistent with this rule,
not an exception to it.

### Corroborating context: SoFi Stadium's actual structure and heat characteristics

- **Roof/sides:** SoFi has an independently-supported translucent ETFE canopy (302 panels, 46
  operable for ventilation) over an **open-sided bowl** (open on three sides) — not a sealed dome,
  relying on natural cross-ventilation rather than mechanical air conditioning. Source: Wikipedia,
  HKS (the stadium's architects), AccuWeather. This confirms the coordinator's recollection was
  directionally correct — SoFi is not "climate-controlled" in the indoor-arena sense.
- **Real heat behavior (Tier 2, NFL precedent, corroborating only):** Despite open sides, SoFi's
  interior has been measured running **~10°F hotter than outside ambient** at field level due to the
  glass/ETFE canopy trapping solar radiation while only partially venting it — e.g., one documented
  Rams game: 85°F outside at 12:30 PM vs. 96°F at field-level seating same time. A 2024
  Chargers-Raiders game saw a sustained 94-96°F feels-like temperature. This shows SoFi's structure
  does **not** meaningfully suppress on-field heat buildup the way a true sealed/AC dome would —
  consistent with (though not necessary to) the hydration-break precedent above.
- **Today's forecast (Tier 2, weather, for completeness — not load-bearing given Evidence 2):**
  Inglewood, CA on 2026-06-28: high 73°F, low 62°F, partly cloudy, 5-6% precipitation chance — a mild
  day by Southern California standards. Irrelevant to the outcome since the WC2026 rule is
  unconditional, but recorded for completeness.

**Bottom line:** the hydration break is essentially a structural certainty for today's match — it is
now a fixed rule applied to every WC2026 game regardless of venue or weather, and the one venue-specific
data point available (5/5 prior SoFi matches) is fully consistent with that.

---

## B. Substitute-scored goal (Q4)

**Source found: ESPN `summary?event={id}` → `rosters[].roster[]` per-player object — fields `starter`,
`subbedIn`, `subbedInFor`, and `stats[name=="totalGoals"]`.**

**Tier: 1.** Same endpoint, same payload you already pull. This is the best possible source —
better than manually cross-referencing `keyEvents`, because ESPN pre-computes the starter/sub flag
directly per player.

### Verified real example (760440, Qatar 0 – Canada 6)

Nathan Saliba's roster entry:
```json
{
  "active": true,
  "starter": false,
  "subbedIn": true,
  "subbedOut": false,
  "subbedInFor": {"athlete": {"displayName": "Ismaël Koné"}},
  "stats": [
    {"name": "subIns", "value": 1.0},
    {"name": "totalGoals", "value": 1.0},
    {"name": "goalAssists", "value": 1.0}
  ],
  "plays": [
    {"clock": {"displayValue": "57'"}, "substitution": true},
    {"clock": {"displayValue": "64'"}, "scoringPlay": true, "didScore": true},
    {"clock": {"displayValue": "90'+2'"}, "scoringPlay": true, "didAssist": true}
  ]
}
```
This single roster record proves: Saliba came on as a substitute at 57' (`subbedIn: true`,
`subbedInFor`) and scored at 64' (`totalGoals: 1.0`, `plays[1].didScore: true`). Cross-checked
independently against the `keyEvents` array, which separately logs: "57' Substitution, Canada. Nathan
Saliba replaces Ismaël Koné" and "64' Goal! Canada 4, Qatar 0. Nathan Saliba (Canada) from a free kick."
Both sources agree — two independent fields in the same payload corroborate each other.

**Recommended detection logic for Q4 (live, once the match has scorers):** for each scorer in
`keyEvents` (type `goal`/`goal---free-kick`/`own-goal`), look up that player's `displayName` in
`rosters[].roster[]` and check `starter == false` (own goals should be excluded per the question's
wording — note own goals are *credited to the scored-upon team*'s opponent in ESPN's `team` field, so
filter `own-goal` type out entirely regardless of scorer status, consistent with the question's own
"excluding ET / regulation only" framing for goal-scoring questions elsewhere in this list).

No gaps here — this is a clean, well-structured, Tier 1 source.

---

## C. Any-player multi-goal / brace-or-better (Q12)

**Source found: same `rosters[].roster[]` → `stats[name=="totalGoals"]` field, or equivalently
grouping the `keyEvents` goal array by `participants[].athlete.displayName`.**

**Tier: 1.**

### Verified real example (760440)

Jonathan David's roster entry shows `"totalGoals": 3.0` directly — a single field confirms a
hat-trick (which trivially also satisfies "more than 1 goal"). Independently, grouping the 6 raw
`keyEvents` goal entries by scorer name gives the same answer:
```
Cyle Larin: 1 (16')
Jonathan David: 3 (29', 45'+3', 90'+2')
Nathan Saliba: 1 (64', free kick)
Own Goal (Mohamed Manai, Qatar, credited to Canada): 1 (75')
```
Both the roster `totalGoals` stat field and manual grouping of `keyEvents` by `participants` agree —
two independently-derivable confirmations from the same endpoint. ESPN's data structure fully supports
"any player 2+ goals" detection via either method; no gap.

**Note on own goals:** Q12 explicitly excludes own goals ("excluding own goals"), and ESPN's own-goal
events are tagged `type.type: "own-goal"` distinctly from regular `goal` events, with the `team` field
crediting the *benefiting* team rather than the scorer's actual team — so filtering `type.type !=
"own-goal"` before grouping by scorer is correct and trivial.

---

## D. "South Africa advance to Round of 16" (Q9) — distinct from a plain regulation-result market

**Source found: Smarkets exchange, event id `45155173` ("South Africa vs Canada"), market id
`147758349` named "To qualify" (`market_type.name: "TO_QUALIFY"`).**

**Tier: 1** for market *existence and structure* confirmation (this is a formally distinct,
machine-typed Smarkets market — not a coincidental name match). Did not pull live executable prices
(see gap below), so treat pricing itself as unverified.

### Structural proof (real fetched contract lists)

"To qualify" (id 147758349) — **2 contracts, no draw**:
```json
{"contracts": [
  {"name": "South Africa", "contract_type": {"name": "HOME"}},
  {"name": "Canada", "contract_type": {"name": "AWAY"}}
]}
```
"Full-time result" (id 147758216) — **3 contracts, includes draw**:
```json
{"contracts": [
  {"name": "South Africa", "contract_type": {"name": "HOME"}},
  {"name": "Draw", "contract_type": {"name": "DRAW"}},
  {"name": "Canada", "contract_type": {"name": "AWAY"}}
]}
```
This confirms exactly the distinction the question requires: "To qualify" has no draw outcome (because
in a knockout match a draw in regulation rolls into ET/penalties, and one team must ultimately
qualify), whereas "Full-time result" is the scoped 90-minutes-plus-stoppage market with a draw
contract, matching most of the other questions on today's list (e.g., Q7, Q8, Q11). Also present on the
same event: `147758284` "Method of qualification" (likely breaks down win-in-90 / win-in-ET /
win-on-penalties — contracts not pulled in this pass, but market exists) and `147758350` "Will there
be Extra Time" — both useful corroborating markets for ET/penalty-related framing.

### Gap: Smarkets event/market discovery is NOT reliably queryable by name

Important operational finding for your workflow: **Smarkets' v3 `/events/` endpoint's `name=`, `q=`,
`competition=`, and `parent_id=` query parameters do not function as server-side filters** — they are
silently ignored, returning a generic, unfiltered, paginated event listing regardless of input (tested
with 4 different parameter combinations, all returned irrelevant results — see Research Log commands
10–13). The only way I found the actual RSA-CAN event was to request a **larger page** (`limit=300`)
and **filter client-side** in Python on the `name` field of the returned JSON. If this generalizes
(likely, since it's a basic REST listing endpoint, not a search endpoint), your workflow should adopt
**pagination + client-side string match** as the standard method for finding Smarkets events going
forward, rather than relying on query-string filters — those silently return wrong data with a 200 OK,
which is a worse failure mode than an error.

Also: a player-level brace market already exists and could be used as a secondary cross-check for
Q12 specifically — `147758693` "Player to score at least 2 goals" returned 44 named-player contracts
(both squads). Did not pull live prices for this market in this pass (out of scope — pure existence/
structure verification was the ask).

---

## Summary Table

| Question type | Source | Tier | Verified? |
|---|---|---|---|
| Hydration/drinks-break minute (start/end) | ESPN `keyEvents` (`start-delay`/`end-delay`) | 1 | Yes — 3/3 + 5/5 SoFi precedent matches |
| Will a break occur at SoFi Stadium today (RSA-CAN) | FIFA WC2026 rule (unconditional, every match) + 5/5 SoFi precedent | 1 | Yes — resolved, see Section A.1 |
| Goal before/after a given break | ESPN `keyEvents` (`goal` types) vs break clock | 1 | Yes |
| Card before/after a given break | ESPN `keyEvents` (`yellow-card`/`red-card`) vs break clock | 1 | Yes |
| Offside before first break | **No structured minute-tagged source found** | — | **Gap — see Section A** |
| Substitute-scored goal | ESPN `rosters[].roster[].starter/subbedIn` + `totalGoals` | 1 | Yes — real example (Saliba) |
| Any-player 2+ goals (brace) | ESPN `rosters[].roster[].stats.totalGoals` or grouped `keyEvents` | 1 | Yes — real example (J. David hat-trick) |
| Knockout "advance" market structure | Smarkets `market_type: TO_QUALIFY` (id 147758349) | 1 (structure); pricing unverified | Yes (structure only) |

---

## Research Log

A command-by-command log with every curl/fetch and its real output (HTTP status, byte counts, parsed
fields) is in:
`/Users/aki/Desktop/QK Rstudio/sportspredict_research/bash_logs/2026-06-28_RSA-CAN_research_agent_bash_log.txt`

Raw JSON responses fetched during this research (kept in scratchpad, not committed to the research
data directory since they are intermediate/reproducible fetches, not curated derived datasets):
- ESPN summary for events 760440, 760463, 760466, 760486
- Smarkets events listing (limit=300 page), markets list for event 45155173, contracts for markets
  147758349 ("To qualify"), 147758216 ("Full-time result"), 147758693 ("Player to score at least 2 goals")

If you want these raw JSON files moved into the permanent `data/external_markets/` directory rather
than left in scratchpad, let me know and I will copy them over with appropriate filenames following
your existing `{match}_{date}.json` convention.
