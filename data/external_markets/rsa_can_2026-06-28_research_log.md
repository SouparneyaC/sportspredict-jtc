# South Africa vs Canada (2026-06-28) — Research Log

Match: South Africa vs Canada, WC2026 Round of 32 (knockout stage begins today). ESPN event 760486,
Smarkets event 45155173, venue SoFi Stadium, Inglewood CA.

This is the first day the question format has changed structurally: every question is now explicitly
scoped to "regulation (90 minutes + stoppage time)" (since knockout matches can go to extra time), and
three genuinely new question types appeared that have never been seen anywhere in this season's
database: hydration-break-timed markets, substitute-scored-goal, and any-player-multi-goal (brace).

---

## Part 1 — What we already have (my own DB audit, done before dispatching the research agent)

Full command-by-command log: `bash_logs/2026-06-28_RSA-CAN_db_search_bash_log.txt`

**Team history on file:**
- South Africa: GD3 file `rsa_kor_2026-06-24.json` (beat South Korea 1-0). No populated `match_facts`
  block in that file — box-score detail will need a fresh live ESPN pull.
- Canada: GD3 `sui_can_2026-06-24.json` (lost to Switzerland 2-1, no match_facts populated), GD2
  `can_qat_2026-06-18.json` (won 6-0 vs Qatar, **fully populated** match_facts: 9 fouls, 19 corners,
  10 SOT, 32 shots, 1 offside, 1 YC, 0 RC — ESPN event 760440), GD1 `can_bih_2026-06-12.json` (drew
  1-1 vs Bosnia, no match_facts populated).
- No prior South Africa vs Canada meeting this tournament (different groups) — first encounter.

**Precedent check for the new question types:** searched every JSON and MD file in the project for
"hydration", "extra time", "round of 16/32", "substitute...goal", "knockout". Every hit was an
incidental group-stage qualification-stakes mention (e.g. "DRAW = ADVANCE to Round of 32" in
`cur_civ_2026-06-25.json`). **Zero prior questions, zero prior sourcing methodology, zero prior
RBP evidence exists anywhere for hydration-break timing, substitute-goal, or multi-scorer markets.**
`questions_flat.csv` likewise has no minute-level/substitute/multi-scorer columns. This is a genuinely
new category, not something I'd missed in earlier matches.

Also confirmed (read-only, no new API calls — preserves the QUANTkiosk quota): `bot/discover_endpoints.py`'s
cached prior run (`bot/data/endpoint_discovery.jsonl`) shows SportsPredict's own platform API exposes
nothing structurally useful here either (everything 500 except `GET /markets`) — ruled out as a
candidate source for the new question types.

**Conclusion of Part 1:** standard props (cards, corners, fouls, penalties, named-player goals/SOT,
match winner) can be handled with the usual ESPN + Smarkets pipeline once today's match-eve data is
pulled. The 3 new types needed dedicated research — dispatched to a research agent next.

---

## Part 2 — Research agent findings (new question types)

Full agent output: `rsa_can_2026-06-28_new_question_types_sources.md` (same directory)
Full agent command log: `bash_logs/2026-06-28_RSA-CAN_research_agent_bash_log.txt`

Brief given to the agent: find and *verify* (not guess) real sources for hydration-break timing
(Q1/Q3/Q5), substitute-scored goal (Q4), and any-player-multi-goal (Q12), calibrated against this
season's data-source reliability hierarchy ([[feedback_data_source_reliability]] memory — ESPN/Opta
GD-stats, main book consensus, FootyMetrics referee stats = Tier 1; niche aggregator odds absent from
main books, base-rate data without match-script prediction = Tier 3/avoid).

**Findings, condensed (full detail + raw JSON examples in the agent's MD file):**

1. **Hydration breaks (Q1, Q3, Q5) — Tier 1, mostly solved.** ESPN's existing `summary?event={id}`
   endpoint (the one we already use for every team-stat pull) has a sibling `keyEvents[]` array with
   `start-delay`/`end-delay` events, minute-stamped, text "Delay in match for a drinks break." Verified
   across 3 real completed matches (760440, 760463, 760466): breaks land ~23-25' and ~68-71'. Goals and
   cards can be directly timestamp-compared against this. **Gap found:** no structured minute-tagged
   `offside` event exists in `keyEvents` — only team-aggregate offside counts are available, so Q3
   ("offside before first hydration break") has no clean structured source; commentary text is the only
   fallback.

   **SoFi Stadium venue question — RESOLVED (follow-up research, see below): a hydration break is a
   near-certainty today.** Two independent Tier 1 findings: (a) swept the ESPN scoreboard across 18
   tournament dates and found 5 prior WC2026 matches already played at SoFi Stadium (events 760417,
   760427, 760439, 760451, 760470) — **every single one had a drinks-break `keyEvent` in both halves**
   (1H range 23'-30', 2H range 67'-70'), including midday kickoffs comparable to today's. (b) Verified
   via two independent sources (Kestrel Instruments, Fox/OutKick) that FIFA changed the rule specifically
   for WC2026: hydration breaks are now **mandatory in every match regardless of weather, venue, or
   roof/climate-control status**, replacing the old conditional 32°C WBGT-triggered system — so the
   venue itself was never actually the deciding factor. Corroborating, non-load-bearing detail: SoFi's
   roof is an open-sided ETFE canopy, not a sealed AC dome, and has been measured running ~10°F hotter
   than outside ambient in NFL games — my original "climate-controlled" description was wrong, but it
   doesn't matter given the rule is now unconditional. Today's forecast (73°F, mild) is similarly moot.
   Full detail and raw `keyEvents` examples in Section A.1 of the agent's sourcing file.
2. **Substitute-scored goal (Q4) — Tier 1, fully solved.** Same ESPN payload's `rosters[].roster[]`
   per-player object has direct `starter`/`subbedIn`/`subbedInFor` flags plus a `totalGoals` stat —
   no manual cross-referencing needed. Verified with a real example (Nathan Saliba, subbed on 57',
   scored 64', in the CAN 6-0 QAT match), independently corroborated by the `keyEvents` text feed.
3. **Any-player multi-goal/brace (Q12) — Tier 1, fully solved.** Same roster `totalGoals` field
   (Jonathan David hat-trick, real example) or grouping `keyEvents` goals by scorer — two independent
   methods on the same payload agree. Own goals are separately typed and trivially excluded.
4. **"Advance to Round of 16" (Q9) — Tier 1 for structure.** Smarkets has a genuinely distinct market,
   `market_type: TO_QUALIFY` (id 147758349, 2 contracts, no draw) versus the regulation-scoped
   "Full-time result" (147758216, 3 contracts, includes draw) — confirms this question needs the
   qualify market, not the regulation FTR market most other questions should use. Pricing itself not
   yet pulled (next step, see below).

**Operational finding worth keeping:** Smarkets' `/v3/events/` `name=`/`q=`/`competition=` query
filters are silently non-functional — they return an unrelated, unfiltered page with HTTP 200 rather
than an error. The only reliable discovery method is `limit=300` + client-side string match on the
`name` field. Adopting this as standard practice going forward (the earlier attempts in this same
session to search "South Africa vs Canada" by name returned junk results for exactly this reason).

---

## Next steps (not yet done)

1. Pull live ESPN `keyEvents`/`rosters` for today's match once it's underway (760486 is still
   `STATUS_SCHEDULED` as of this research pass) — can't pre-fetch break timing for a match that hasn't
   started; this confirms timing only retroactively/live, same as any in-play stat.
2. Pull Smarkets pricing for: `147758349` (To qualify), `147758216` (Full-time result), `147758284`
   (Method of qualification), `147758350` (Will there be Extra Time), `147758693` (Player to score 2+
   goals — useful cross-check for Q12), plus the standard corners/cards/penalty/player-SOT markets for
   the other 11 "normal" questions.
3. Live ESPN pull for South Africa's and Canada's most recent box-score detail (rsa_kor, sui_can
   match_facts are unpopulated on file) to calibrate the standard props.
4. Decide a real-time read protocol for Q3 (offside before first break) given no structured source
   exists — most likely: read `commentary` text live around the 0-25' window once the match starts,
   or fall back to a base-rate/Poisson estimate scaled by typical 1H offside share if live reading
   isn't feasible before the SportsPredict closing time.

**Why:** relates to [[feedback_data_source_reliability]], [[feedback_record_everything]],
[[project_sportspredict_edge_analysis]]
