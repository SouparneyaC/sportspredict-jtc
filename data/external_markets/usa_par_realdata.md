# Real match-level data: USA offsides, Paraguay/USA corners, Enciso injury

Source: ESPN hidden site API (`site.api.espn.com/apis/site/v2/sports/soccer/<league>/summary?event=<id>`),
VERIFIED_API tier, fetched 2026-06-12. Note: ESPN team-stat blocks (Offsides, Corner Kicks Won,
Fouls Committed) are NOT present in every match's boxscore - inconsistent coverage (present for
~half the matches checked).

## USA - offsides data
| Date | Opponent (venue) | USA Offsides | Opp Offsides | USA Corners | Opp Corners | USA Fouls | Possession | Event ID |
|---|---|---|---|---|---|---|---|---|
| 2025-06-15 | Trinidad & Tobago (H, Gold Cup, 5-0 win) | 3 | 1 | 10 | 4 | 10 | 69.7% | 735319 |

Only one match with full team-stat boxscore found for USA. This was a dominant blowout
(possession 69.7%) which likely inflates offsides (more high-tempo attacking transitions
against a packed defense). USA-Paraguay (WC opener, host nation, expected to be more even
but USA still favored ~55%+ possession) - used as anchor with a downward adjustment.

## Paraguay - corners/offsides/fouls data
| Date | Opponent (venue) | PAR Offsides | Opp Offsides | PAR Corners | Opp Corners | PAR Fouls | Opp Fouls | Event ID |
|---|---|---|---|---|---|---|---|---|
| 2025-09-09 | Peru (A, WCQ, 1-0 win) | 2 | 1 | 7 | 7 | 12 | 6 | 684666 |

## Julio Enciso - status
- ESPN Paraguay vs Japan friendly (2025-10-10, event 739959): Enciso did NOT appear in the
  roster/lineup at all (rested/rotated even before the injury).
- WebSearch confirms: stretchered off 2026-06-05 vs Nicaragua (hamstring + quad/waist), coach
  says "encouraging progress", "door left open to start" vs USA but flagged as the #1 lineup
  question mark.
- Net read: significant chance (~40-45%) he doesn't start at all; if he does start, real
  chance of early substitution for fitness management, reducing 2H involvement further.

## Q4 (corners) - Skellam tie-probability model
Smarkets corners handicap: P(USA>PAR)=0.5163 (normalized), P(PAR>=USA)=0.4837.
Solving for Poisson rates lambda_USA, lambda_PAR (total corners ~9-11, consistent with the
10 (USA blowout) and 7+7 (PAR away at Peru) data points) such that Skellam CDF matches
the Smarkets P(PAR>=USA):
- total=9: lambda_USA=4.82, lambda_PAR=4.18, P(tie)=0.132, P(PAR>USA)=0.352
- total=10: lambda_USA=5.32, lambda_PAR=4.68, P(tie)=0.125, P(PAR>USA)=0.358
- total=11: lambda_USA=5.82, lambda_PAR=5.18, P(tie)=0.120, P(PAR>USA)=0.364
-> recommended_estimate = 0.355 (Q4: "Will Paraguay finish with more corner kicks than USA?")

## Q2 (USA offsides >=2) - Poisson model
Single real data point lambda~2.5-3 (blowout match), but USA-Paraguay expected more even
(host favored but Paraguay defends deep/compact per H2H clean-sheet rate 40%). Using
lambda=2.0-2.2 (between the single-match observation and a "typical attacking team" prior):
P(offsides>=2) = 0.594 (lambda=2.0) to 0.645 (lambda=2.2)
-> recommended_estimate = 0.58 (slightly conservative given single-match basis for the anchor)

## Q1 (Enciso 2H SOT) - blended model
Full-match SOT>=1 anchor (Smarkets offer, illiquid) = 0.6024 -> implied Poisson lambda_full=0.922
-> even-half-split lambda_2h=0.461 -> P(2H SOT>=1 | plays normally)=0.369
Injury-adjusted: P(starts)=0.55 (x0.9 fitness-management factor for 2H), P(sub appears in 2H
if not starting)=0.45*0.35
Blended: 0.55*0.9*(1-exp(-0.461*0.85)) + 0.45*0.35*(1-exp(-0.461*0.5)) = 0.193
-> recommended_estimate = 0.20
