# "My Performance" Page — Discovery & Scrape Feasibility
**Date:** 2026-07-14
**Conducted by:** Claude Code via claude-in-chrome browser automation, live on Souparneya's own logged-in session (username **AbirC** — confirmed same identity as the human player, see correction in `API_EXPLORATION_2026-06-27.md` context / memory).

## What it is
SportsPredict added a "My Performance" nav item inside the JTC event shell
(top nav bar at `play.sportspredict.com/probability-events/{eventId}/...`).
It routes to:

```
https://play.sportspredict.com/probability-events/{eventId}/performance-summary
```

For JTC: `https://play.sportspredict.com/probability-events/aa5572ec-5930-4d99-b06b-f8966333d172/performance-summary`

The page has an account toggle at top-right: **Me** (Souparneya/AbirC's own
manual forecasts) vs **Abir's Bot** (a separate, much lower-volume bot
identity on the same account — only 1 forecast settled, RBP gap -10.6, vs.
Me's 986 settled). Confirmed these are two distinct trackable identities
under one login.

## The API call
```
POST https://api.sportspredict.com/api/probability/performance
Body (JSON): {"eventId": "...", "lobbyId": "..."}   -- lobbyId param unconfirmed as required, likely also accepts a botId to switch to "Abir's Bot"
Auth: Bearer token, injected by the SPA's axios interceptor
```

**Auth confirmed still the same blocker as the 2026-06-27 session**: calling
this endpoint with `credentials:'include'` only (no Bearer header) returns
`401 Unauthorized`, even in a fully logged-in browser tab. The token is not
attached via `XMLHttpRequest.setRequestHeader` (patched and got nothing) —
axios is using its **fetch adapter**, not XHR, in this browser/axios version.
That means the token lives inside a `Request` object or a headers dict passed
directly to `window.fetch`, not easily interceptable by patching
`setRequestHeader`. The `bot/setup_session.py` Playwright approach still
works for this, since Playwright's `page.on("request")` listens at the
network layer regardless of fetch vs. XHR — it doesn't need to guess which
JS API the app uses internally.

### Response shape (partial, captured from the "Abir's Bot" identity — same schema applies to "Me")
```json
{
  "summary": {
    "averageRbpGapToCrowd": <float>,
    "contrarianWinRate": <float 0-1>,
    "forecastsSettled": <int>,
    "confidenceBias": <float>,
    "percentileRank": <int>
  },
  "highlights": {
    "bestMarket": {"question": "...", "matchName": "...", "userProb": <float>, "crowdProb": <float>, "outcome": <0|1>, "rbp": <float>},
    "worstMarket": {...same shape...},
    "bestMatch": {...} | null,
    "worstMatch": {...} | null
  },
  "calibrationBins": [
    {"bin": "0-10%", "lo": 0, "hi": 0.1, "n": <int>, "hitRate": <float|null>, "avgPredicted": <float|null>},
    ...
  ]
}
```
The UI's Category and Matches tabs are almost certainly additional fields on
this same payload (`byCategory`, `byMatch` or similar) — didn't get a clean
capture of the full body to confirm exact key names, but the UI renders them
without a separate network call, so they're in the same response.

## Data actually pulled for "Me" (Souparneya / AbirC, JTC event, as of 2026-07-14)

**Summary:**
| Metric | Value |
|---|---|
| RBP gap vs crowd | +3.9 (better than 89% of forecasters) |
| Contrarian win rate | 50% |
| Forecasts settled | 986 |
| Confidence bias | +2% |

**Boldest call:** "Will both teams receive at least one card in regulation?" — You 33% vs crowd 62%, result NO, RBP +59.2
**Roughest call:** "Will Canada have 4 or more shots on target in regulation?" — You 80% vs crowd 46%, result NO, RBP -81.1

**Top 3 categories:**
| Category | Forecasts | RBP gap vs crowd | Contrarian win rate | Confidence bias |
|---|---|---|---|---|
| Other | 173 | +6.4 | 52% (13/25) | +4% (optimal) |
| Team shots on target | 92 | +6.2 | 63% (10/16) | +2% (optimal) |
| Total cards | 44 | +6.1 | 67% (2/3) | +8% (optimal) |

**By category type:**
| Category type | Sub-categories | Forecasts | RBP gap vs crowd |
|---|---|---|---|
| Goals & Scoring | 10 | 374 | +3.6 |
| Match Outcome | 5 | 329 | +4.6 |
| Cards & Discipline | 3 | 112 | +4.5 |
| Set Pieces & Possessions | 4 | 171 | +3.0 |

**Best 5 matches (by RBP):**
1. Brazil vs Norway (Round of 16) — +177.5, 13/15 beat crowd
2. France vs Morocco (Quarterfinals) — +168.4, 13/14 beat crowd
3. Argentina vs Switzerland (Quarterfinals) — +159.8, 14/15 beat crowd
4. Belgium vs Senegal (Round of 32) — +159.5, 13/15 beat crowd
5. Mexico vs Ecuador (Round of 32) — +153.1, 11/15 beat crowd

**Toughest 5 matches (by RBP):**
1. Spain vs Belgium (Quarterfinals) — -83.0
2. Argentina vs Austria (Group Stage) — -42.9
3. South Africa vs Korea Republic (Group Stage) — -40.5
4. Qatar vs Switzerland (Group Stage) — -39.8
5. Brazil vs Haiti (Group Stage) — -32.1

**Calibration:** Site's own read: "You're tracking the line — your confidence
consistently matches reality. That's elite calibration." (chart is SVG, raw
bucket-level `n`/`hitRate`/`avgPredicted` numbers weren't extracted from the
DOM — would need the raw JSON via a proper Bearer-token capture, see below.)

## To fully automate this (next step)
Extend `bot/setup_session.py`'s Playwright listener (currently only used to
grab `web_session_token` for the AbirC/bot flow) to also run against
Souparneya's real login, watching specifically for the
`POST /api/probability/performance` call and logging its `Authorization`
header + full response body. Once captured, a `fetch_performance.py` script
analogous to `fetch_dashboard.py` could pull this on demand and diff it
match-over-match — useful for tracking RBP-gap/confidence-bias drift over the
tournament instead of manually re-reading the page each time.
