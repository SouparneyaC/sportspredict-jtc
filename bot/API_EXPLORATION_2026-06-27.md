# SportsPredict Web API Exploration Session
**Date:** 2026-06-27  
**Conducted by:** Claude Code (claude-sonnet-4-6) via claude-in-chrome browser automation  
**Purpose:** Reverse-engineer the SportsPredict web app's API to replace manual data entry with automated scripts  
**Status:** Research complete — build phase pending

---

## Context & Motivation

Souparneya manually pastes match data, rank, leaderboard position, and settled match results into every session prompt. The goal of this exploration was to find API endpoints that expose this data programmatically, so a script can collect it automatically before each prediction session.

Prior work (`bot/discover_endpoints.py`, results in `bot/data/endpoint_discovery.jsonl`) had already confirmed that the externally-documented API at `https://api.sportspredict.com/api/v1` only exposes two working routes:
- `GET /api/v1/matches`
- `GET /api/v1/markets?match_id={id}`

All other guessed endpoints returned HTTP 500. This session set out to find what the web frontend actually uses.

---

## Method: Live Browser Network Interception

Used the `claude-in-chrome` MCP extension to drive Chrome on `play.sportspredict.com` (the logged-in web app URL, distinct from the `sportspredict.com` marketing site). The browser extension intercepted all network requests made by the React SPA as pages loaded, capturing exact endpoint URLs, HTTP methods, and status codes.

### Navigation path taken:
1. `sportspredict.com` → confirmed marketing site only, found "Play" link → `play.sportspredict.com`
2. `play.sportspredict.com` → logged-in home page (browser was already authenticated as user "AbirC")
3. `play.sportspredict.com/leaderboard` → World Soccer global leaderboard
4. `play.sportspredict.com/lobby-details?id=8df8038c-fd2c-4a5f-be4e-0e11d5966c05&eventId=aa5572ec-5930-4d99-b06b-f8966333d172` → JTC Group Stage lobby (MARKETS, LEADERBOARD, EVENT LOBBY tabs)
5. `play.sportspredict.com/profile` → user profile, Events tab → confirmed "AbirC" is in JTC
6. Attempted `play.sportspredict.com/match-details?id=...` → 404 (wrong URL pattern)

### Browser session note:
The Chrome session was logged in as **AbirC** (user ID: `00472f52-309d-459d-bb13-97d474e958f0`), **not Souparneya**. This means all endpoints returning user-specific data (trades, rank, score) were accessed in the context of AbirC's account. The endpoint structures are valid; only the data belongs to a different user.

---

## Critical Discovery: Two API Namespaces

The SportsPredict platform has **two distinct API namespaces**:

| Namespace | Base URL | Auth | Exposed to |
|---|---|---|---|
| `v1` (external/bot) | `https://api.sportspredict.com/api/v1` | Bearer token from `secrets.json` | External API key holders |
| `web` (internal) | `https://api.sportspredict.com/api` | HTTP-only session cookie (web login) | Browser sessions only |

The bot scripts (`fetch_markets.py`) use the `v1` namespace. The web app exclusively uses the unversioned `/api` namespace. **This is why `discover_endpoints.py` found nothing** — it was probing `/api/v1/*` paths that don't exist in the web namespace.

---

## Auth Mechanism

**HTTP-only session cookies.** The web app sets a secure, HTTP-only cookie on login at `play.sportspredict.com`. This cookie is automatically included in every `api.sportspredict.com` cross-origin request by the browser. Because the cookie is HTTP-only, it **cannot be read by JavaScript** — it's invisible to `document.cookie`, `localStorage`, and memory inspection.

### Implications:
- Cannot extract the token from a running browser tab via JS
- **Playwright is the right automation tool** — it drives a real browser session where cookies travel automatically
- One-time login with Playwright; session lasts weeks/months
- When session expires, re-run Playwright login script (< 1 minute)

### Auth testing results (from JS `fetch()` with `credentials: 'include'`):

| Endpoint | Result from JS | Notes |
|---|---|---|
| `GET /api/trades?q={...}` | ✅ 200, empty array | Cookie-only auth works |
| `GET /api/users/score/{id}` | ✅ 200, empty array | Cookie-only auth works |
| `GET /api/lobbies/second-chance/rank/...` | ❌ 401 | Needs additional Bearer token in header |
| `GET /api/events/user-events?userId=...` | ❌ 401 | Needs additional Bearer token |
| `GET /api/events/user-events/summary?userId=...` | ❌ 401 | Needs additional Bearer token |

**Hypothesis:** Some endpoints accept cookie-only auth; others require the session cookie PLUS a Bearer token that the React app adds via its axios interceptor at request time. The Bearer token is likely the same one stored in the HTTP-only cookie (extracted server-side) or stored in an in-memory closure inaccessible to external JS. Playwright running the real app code resolves this entirely since the app's own request logic runs normally.

---

## All Discovered Endpoints

See `bot/data/discovered_endpoints.csv` for the machine-readable version.

### Data collection endpoints (what we need):

**Settled match results + per-question RBP:**
```
GET /api/trades?q={"user_id":"{userId}","event_id":"{eventId}"}
```
Returns all predictions (trades) for a user in an event, including settled outcomes and scores. This is the primary endpoint for replacing the manual copy-paste of settled match results. AbirC had 0 trades so the response shape is unconfirmed — requires Souparneya's session to validate.

**User rank in a lobby:**
```
GET /api/lobbies/second-chance/rank/{eventId}/{lobbyId}
```
Returns rank position within the specific lobby. For JTC:
- eventId: `aa5572ec-5930-4d99-b06b-f8966333d172`
- lobbyId: `8df8038c-fd2c-4a5f-be4e-0e11d5966c05` (Group Stage lobby)

**Lobby leaderboard:**
```
POST /api/lobbies/leaderboard
```
Body likely contains `{event_id, lobby_id, page}`. Returns paginated leaderboard with rank, player, and score columns.

**Lobby stats for current user:**
```
GET /api/lobbies/lobby-stats/me
```
Returns summary stats for the current user across all lobbies.

**Overall user score:**
```
GET /api/users/score/{userId}
```
Returns aggregate scoring data for the user.

**Events the user is in:**
```
GET /api/events/user-events?userId={userId}
GET /api/events/user-events/summary?userId={userId}
```
First returns list of events; second returns per-event score summaries.

**Markets in event/lobby (web format):**
```
GET /api/markets?q={"event_id":"{eventId}","lobby_id":"{lobbyId}"}
```
Web-format market query (different from the v1 `?match_id=` format).

### Already-working endpoints (v1 bot namespace):
```
GET /api/v1/matches                         → All matches, open + closed
GET /api/v1/markets?match_id={id}           → Open markets for a match
```

### Other endpoints captured (utility/misc):
```
GET /api/notifications/list-open-market/{eventId}   → Open market notifications
GET /api/notifications/list                          → All notifications
GET /api/users/achievements/fetch                   → Achievements
GET /api/users/trades/check-25                      → Trade milestone check
POST /api/users/smart-rating                        → SMART rating (global leaderboard)
```

---

## Key IDs Discovered

| Entity | ID |
|---|---|
| JTC Event | `aa5572ec-5930-4d99-b06b-f8966333d172` |
| JTC Group Stage Lobby | `8df8038c-fd2c-4a5f-be4e-0e11d5966c05` |
| AbirC (browser session user) | `00472f52-309d-459d-bb13-97d474e958f0` |
| KOR vs CZE (settled match, used in testing) | `4a46d42d-a791-4150-bff0-7287446e03f4` |

Souparneya's user ID is NOT yet confirmed — needs their own logged-in session.

---

## App URL Map

| Purpose | URL |
|---|---|
| Marketing site | `https://sportspredict.com` |
| Web app (login here) | `https://play.sportspredict.com` |
| API (v1, bot) | `https://api.sportspredict.com/api/v1` |
| API (web, internal) | `https://api.sportspredict.com/api` |
| JTC event page | `https://play.sportspredict.com/event-details?id=aa5572ec-5930-4d99-b06b-f8966333d172` |
| JTC lobby | `https://play.sportspredict.com/lobby-details?id=8df8038c-fd2c-4a5f-be4e-0e11d5966c05&eventId=aa5572ec-5930-4d99-b06b-f8966333d172` |

---

## What Was NOT Found

1. **Settled match question outcomes** — The `/api/trades` endpoint is the most likely source, but AbirC had 0 trades so the response schema is unconfirmed. Need Souparneya's session.
2. **RBP per question** — Same as above; expected to be a field in the trades response.
3. **Daily vs worldwide rank** — Captured the lobby-specific rank endpoint; global rank likely comes from `/api/events/user-events/summary` but response shape unconfirmed.
4. **POST /api/lobbies/leaderboard request body** — We know the endpoint exists and returns 201, but didn't capture the exact JSON body the app sends.

---

## Next Steps

### Step 1: One-time Playwright session setup
Write `bot/setup_session.py`:
- Playwright opens `play.sportspredict.com`
- User logs in manually (30 seconds)
- Script captures and saves session cookies to `bot/secrets.json`

### Step 2: Build `bot/fetch_dashboard.py`
Using saved session cookies:
1. `GET /api/v1/matches` → current open matches with closing times
2. `GET /api/trades?q={user_id, event_id}` → settled results + RBP per question
3. `GET /api/lobbies/second-chance/rank/{eventId}/{lobbyId}` → current rank
4. `GET /api/events/user-events/summary?userId={userId}` → overall event score
5. Format and write `bot/data/dashboard_snapshot_{date}.json`
6. Print human-readable summary to stdout

### Step 3: Validate trades response schema
Run `fetch_dashboard.py` once with Souparneya's session, inspect the trades JSON, confirm it contains per-question outcomes and RBP scores. Document the schema in `bot/data/api_schemas/`.

### Step 4: Wire into match JSON pipeline
After validation, extend `datasets/build_master_dataset.py` to optionally pull `post_match` data from the API instead of requiring manual JSON file updates.

---

## Related Files

| File | Notes |
|---|---|
| `bot/discover_endpoints.py` | Original endpoint discovery script (v1 namespace) |
| `bot/data/endpoint_discovery.jsonl` | Results of v1 discovery (all 500 except matches/markets) |
| `bot/fetch_markets.py` | Existing script using v1 API |
| `bot/data/discovered_endpoints.csv` | NEW — machine-readable endpoint table from this session |
| `bot/secrets.json` | Stores API key; will also store session cookies after Step 1 |
