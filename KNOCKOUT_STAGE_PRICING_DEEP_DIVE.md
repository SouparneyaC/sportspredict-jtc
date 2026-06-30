# Knockout-Stage Pricing System Deep Dive

**Scope:** the 4 Round-of-32 matches analyzed under the new 15-question "regulation + hydration-break + knockout"
format: South Africa vs Canada (2026-06-28), Germany vs Paraguay (2026-06-29), Brazil vs Japan (2026-06-29),
Netherlands vs Morocco (2026-06-30). 60 questions total, **+158.4 RBP combined**, 41/60 beat crowd (68.3%).

**Purpose:** the knockout format introduced a genuinely new question taxonomy (hydration-break timing, substitute
goals, multi-scorer, knockout-advance markets) with no season history to draw on when it started. Four matches in,
there's now enough settled data to separate what the new process actually does well from what it doesn't — by
*mechanism*, not just by match. This document is that audit: the pipeline as practiced, the quantitative
breakdown by pricing technique, and the specific, evidenced conclusions.

Source data: `data/external_markets/{rsa_can_2026-06-28, ger_par_2026-06-29, bra_jpn_2026-06-29,
ned_mar_2026-06-30}.json` (post_match_results blocks), `bash_logs/2026-06-2{8,9}_*` and `2026-06-30_NED-MAR_*`,
`datasets/questions_flat.csv`, `STEPS_FOR_HIGH_POINTS.md`.

---

## 1. The process as actually practiced (pipeline audit)

Every one of the 4 matches followed the same sequence, visible directly in the bash logs:

1. **Check existing history first.** `ls data/external_markets | grep` for both teams before touching any API —
   this surfaced real, load-bearing precedent every single time (Saibari's 2-for-2 scoring streak, Enciso's prior
   RULE15 confirmation, Brazil's -51.97 conviction-override disaster, Germany's rotated-squad Ecuador loss).
   **This step has never once come up empty and should never be skipped.**
2. **ESPN team IDs → `teams/{id}/schedule` → `summary?event={id}` for all 6 group-stage matches** (3 per team).
   Pulled fresh every time rather than trusting cached `match_facts` in older raw files, several of which turned
   out to be unpopulated (RSA-CAN's own South Africa/Canada files had only 1 of 4 with real box-score detail).
3. **Smarkets event discovery via `limit=300` + client-side string filter**, never via the `name=` query
   parameter — confirmed broken (silently returns an unrelated, unfiltered page with HTTP 200) by the research
   agent during RSA-CAN and re-confirmed every match since. This is now standard practice across all 4 matches
   and should stay that way; the alternative (trusting `name=`) would have produced wrong-data-with-no-error.
4. **Full market list pull, then targeted quote fetches** for every question, with a consistent adjustment
   convention: offer-only illiquid player markets × 0.945; bid+offer liquid markets used at the raw mid.
5. **Local Python (scipy: `poisson`, `brentq`, `binom`) for every derived estimate** — lambda-fitting from
   O/U thresholds, Skellam/Poisson team comparisons, and (new this stage) time-window scaling for hydration-break
   questions. Every computation logged with real numeric output, not described in prose only.
6. **Bash log + JSON file + chat table for every match**, post-match results appended additively, lessons fed
   forward into the next match's `prior_lessons_consulted` field and into `STEPS_FOR_HIGH_POINTS.md`.

**One real process defect found and fixed during this deep dive:** `ger_par_2026-06-29.json` and
`bra_jpn_2026-06-29.json` both had a malformed-JSON bug (a `context_flags`/nested-object key written as
`"KEY: text"` instead of `"KEY": "text"`) that would have silently broken any future `json.load()` of those
files. Found and fixed before this analysis ran. **Recommendation: validate every written match JSON with
`python3 -c "import json; json.load(open(f))"` immediately after writing it**, the same way bash commands are
logged — this is a one-line check that would have caught both instances at write time instead of weeks later.

**A second, more interesting defect:** the platform reorders questions between what we draft and what gets
submitted — already known from RSA-CAN, but it recurred for BRA-JPN (a clean cyclic shift: our last question
moved to position 1, everything else shifted down by one). The original recording correctly matched by question
*text*, not position, when the post-match results were entered — but it's a standing trap, confirmed twice now
in 4 matches. **Any automated analysis of `question_results` must match on text, never assume position.**

---

## 2. Quantitative breakdown by pricing technique

Every one of the 60 questions was classified by *how the estimate was actually produced*, not by surface topic.
Five categories emerged cleanly:

| Category | N | Total RBP | Avg RBP | Beat-crowd rate |
|---|---|---|---|---|
| **DIRECT** — a real Smarkets market matches the question ~1:1 | 34 | +142.39 | +4.19 | 73.5% |
| **TEAM_MODEL** — Poisson/Skellam/binomial decomposition from team-level markets, no time window | 6 | +49.83 | +8.30 | 66.7% |
| **PLAYER_LIQUID** — individual player market, both bid AND offer present | 3 | +26.60 | +8.87 | 66.7% |
| **TIMING_WITH_MARKET** — a real Smarkets time-bracket market exists (e.g. "Goal 1 time bracket") | 3 | +17.57 | +5.86 | 100% |
| **PLAYER_ILLIQUID** — individual player market, offer-only, ×0.945 adjustment | 7 | -14.27 | -2.04 | 71.4% |
| **TIMING_NO_MARKET** — self-built time-window decomposition, no market exists at all | 7 | -63.72 | -9.10 | 42.9% |

Two categories are unambiguously net-negative; everything else is solidly positive. The rest of this document is
about why.

---

## 3. What's working

### 3.1 Direct market trust, still the foundation (+142.39 / 34 questions / 73.5% beat-crowd)
Nothing has changed about this since the group stage — when a Smarkets market answers the question almost
word-for-word ("Brazil to score in both halves," "To qualify," "Germany over/under 6.5 corners," "Goal 1 time
bracket" for early-window timing questions), submitting it near-raw remains the single most reliable move in the
whole system. 3 of every 4 direct-market submissions beat the crowd. This volume (34 of 60 questions, well over
half) is also why the overall knockout-stage record is positive even with two weak categories dragging it down.

### 3.2 Team-level decomposition instead of summing illiquid contracts (+49.83 / 6 questions / 66.7% beat-crowd)
This is the single most repeatable *technique-level* win across all 4 matches. The pattern: a Smarkets market
exists in name ("Player to score 2+ goals," "Both teams carded") but is structurally unusable (44 illiquid
per-player contracts whose offer-side prices sum to a meaningless 0.76, or no direct market exists for a compound
condition at all). The fix, applied identically every time: back out **team-level** Poisson lambdas from the
*liquid* team/match markets, then decompose with a binomial top-scorer-share or independent-team-event model.

- RSA-CAN Q12 (any player brace): avoided the 0.76 trap, landed at 0.18 → **+11.94**
- BRA-JPN Q2/Q9 (any player 2+SOT, any player brace): same method twice → **net positive both times**
- NED-MAR Q13 (both teams carded): team card lambdas instead of a "two physical teams" narrative → **+23.37**, 2nd-biggest win of the season

This is now confirmed enough times (5 of 6 instances beat crowd) to treat as a settled rule, not a hypothesis:
**whenever a multi-contract or compound market exists with no clean direct read, decompose from the nearest
liquid team-level market rather than trusting either a literal contract-sum or a narrative guess.**

### 3.3 Liquid (bid+offer) player markets, trusted near-raw (+26.60 / 3 questions, but the *real* story is downside risk — see §4.2)
When a player prop genuinely has both a bid and an offer, it has consistently been safe to trust close to the
mid with little or no extra shading. Brobbey (NED-MAR, +24.84, the single biggest win of the season) is the
clearest example: the crowd over-priced him at 36% off a "two strong, evenly-matched attacking teams" narrative;
the liquid market mid (21%) was right, and trusting it directly — rather than letting the competitive-match
framing pull the estimate up — was the win.

### 3.4 Early-hydration-break-window questions, modeled or market-backed (all positive)
Every question asking about something happening **before** the first hydration break (~24') has gone right,
whether market-backed (Goal-1-time-bracket: RSA-CAN +6.81, BRA-JPN +9.68, GER-PAR +1.08) or purely modeled off
team averages with no market at all (offside-before-break: RSA-CAN +11.21, BRA-JPN +6.27; goal-in-1H-stoppage:
NED-MAR +13.38). The common thread: early in a match, before fatigue, substitutions, scoreline pressure, or
match-state desperation enter the picture, team-level historical averages are still doing real work. See §4.1 for
the sharp contrast with the *second*-half-window version of the same question type.

### 3.5 Specific, current-tournament player precedent, applied directly
Saibari (NED-MAR, +8.0) and the repeated reapplication of Enciso's earlier RULE15 confirmation (GER-PAR, though
this one ultimately lost — see §4.2) both came from the same place: checking what a *named, current-tournament*
player had already done (not a generic team stat) before pricing them. When the precedent and the live market
agree (Saibari), this is close to free money. When they disagree, the precedent does not automatically win — see
below.

---

## 4. What's not working

### 4.1 Self-built timing decomposition with no underlying market — the single worst category (-63.72 / 7 questions / 42.9% beat-crowd)

This is the clearest, most actionable finding in the whole audit. Splitting the 7 instances by **which half of
the match the window falls in** explains almost the entire pattern:

| Window | Instances | Total RBP |
|---|---|---|
| **Early** (before 1st hydration break, ~0-24') | offside-before-break ×2, goal-in-1H-stoppage ×1 | **+30.86** (all 3 positive) |
| **Late** (after 2nd hydration break, ~69'+, incl. ET) | card-after-break ×2, goal-after-break ×1 | **-45.90** (3 of 3 negative) |
| **Full-match count, chaos-sensitive** | 3+ offside calls in regulation (GER-PAR) | **-48.68** (the single worst result) |

The early-window items used the exact same methodology (team average → Poisson, scaled to a time fraction) as the
late-window items and came out fine. The difference isn't the math — it's that **late-match windows compress
every source of uncertainty a match can develop** (fatigue, subs, a team protecting or chasing a scoreline,
time-wasting, stoppage-time desperation) into one number that a pre-match team average has no way to see coming.
GER-PAR's -48.68 is the extreme case: Germany's group-stage 0-offsides-in-3-matches record looked like the
cleanest, most consistent signal in the whole dataset, and it still failed, because the actual match was a
grinding, high-pressing, low-conversion 90 minutes that the group-stage form didn't predict at all.

**The lesson already partially applied and confirmed working:** NED-MAR's card-after-break question used the
identical method that produced RSA-CAN's -39.68 disaster, but the raw model output (0.77) was deliberately
trimmed to 0.65 specifically because of that prior loss. The result still missed, but for -3.51 instead of -39.68
— a ~90% reduction in damage from the same wrong direction. **This is real evidence that applying an explicit
humility discount to a late-window, no-market timing model works, even when the discount isn't enough to flip
the call.** The fix is not "stop building these models" (early-window versions of the same technique work fine)
— it's "shade hard toward 0.5 specifically for anything anchored past the second hydration break, and treat
full-match count thresholds in a knockout match as carrying real chaos risk regardless of how clean the
group-stage signal looks."

### 4.2 Illiquid (offer-only) player props — high beat-rate, fat-tailed downside (-14.27 / 7 questions / 71.4% beat-crowd, but...)

The beat-crowd rate (71.4%) looks fine in isolation. The total RBP is negative anyway, because **two of the
seven losses were catastrophic (-26.23, -26.30) while none of the five wins exceeded +17.21.** This is a
classic asymmetric-risk profile: small, steady wins funding two outsized losses.

- **Rayners (RSA-CAN, -26.23):** trusted the raw illiquid-adjusted price (0.519) too literally; the crowd's much
  lower 0.32 turned out closer to truth. *Under*-suppressed.
- **Enciso (GER-PAR, -26.30):** had a direct, specific, already-confirmed precedent (RULE15 worked on this exact
  player in TUR-PAR) and *over*-suppressed because of it (0.454 market → 0.32 submitted) — and the match broke
  every team-level ceiling assumption in a wild, extra-time goal-fest. *Over*-suppressed.

These are opposite errors with the same root cause: an illiquid, one-sided market is inherently a weaker signal
than a two-sided one, and **a confident departure from it in either direction — whether trusting it more than the
crowd does, or applying an extra lesson-based discount on top of it — carries real tail risk.** Contrast directly
with §3.3: every PLAYER_LIQUID result this stage stayed within ±25 RBP; PLAYER_ILLIQUID produced two of the four
worst results across all 60 questions. **When a player market is offer-only, the safest move is to land closer
to the crowd consensus than conviction (ours or a prior lesson's) suggests, rather than asserting a confident
departure from an inherently thin price.**

### 4.3 Cross-team narrative extrapolation, a fresh instance of an already-known failure mode

BRA-JPN's below-crowd misses (7 of 15) are not randomly scattered — 6 of the 7 cluster specifically around
Brazil's attacking *volume* (2+ goals, 8+ SOT, any-player-2+SOT, 3+ total goals), and in every one of those cases
we were too conservative relative to the crowd. The likely mechanism: the "elite teams win clinically, with
lower SOT/corner volume than naive lambda extrapolation suggests" lesson — genuinely earned from **Argentina**
across ARG-AUT and JOR-ARG — got carried into Brazil's file (`bra_jpn_2026-06-29.json` cites the Argentina
pattern explicitly) and suppressed Brazil's volume estimates below where the market and crowd both sat. Brazil
won 2-1 and *did* produce real attacking volume; the Argentina-specific pattern didn't transfer. This is a fresh,
concrete example of the standing "Cross-Team GD1 Extrapolations" failure mode already named in the data-source
reliability audit — worth re-flagging because it happened across an *entire match's* volume questions at once,
not just one.

---

## 5. Net read

The system is solidly profitable on the new format (+158.4 / 60, 68.3% beat-crowd) and the win is not evenly
distributed — it is concentrated almost entirely in direct-market trust, team-level decomposition, and liquid
player markets, three categories that together cover 43 of 60 questions and contribute +218.82 RBP. The two
weak categories (illiquid player props, no-market timing decomposition) cover the other 17 questions and
together cost -78.0 RBP net. Both have a specific, identifiable mechanism, not a vague "needs more data" problem:
late-match timing windows are structurally harder than early ones regardless of how the model is built, and
illiquid one-sided player markets are asymmetric-risk regardless of which direction the departure goes.

### Concrete next steps
1. **Shade any "after the second hydration break" or full-match chaos-sensitive count question hard toward
   0.45-0.55** unless a genuine market exists — treat the early/late distinction as the operative variable, not
   the topic.
2. **Prefer the crowd consensus over either the raw illiquid market or a prior single-player lesson when a
   player prop is offer-only** — only depart confidently from an illiquid price when there's a *team-level*,
   not just player-level, reason to (e.g., the team's whole measured ceiling, not just one player's history).
3. **Before reusing a "clinical/low-volume favorite" or similar team-archetype lesson, re-verify it against the
   specific team in front of you** — these patterns are real but not universal across "good teams," as the
   Argentina→Brazil mis-transfer shows.
4. **Keep doing exactly what's already being done for direct markets and team-level decomposition** — no change
   needed; this is most of the questions and most of the profit.
5. **Validate every newly-written match JSON file immediately with `json.load()`** before moving on — a one-line
   habit that would have caught two broken files before they sat broken for days.
