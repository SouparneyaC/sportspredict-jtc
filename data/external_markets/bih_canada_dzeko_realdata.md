# Real match-level data: BIH fouls/SOT, Canada fouls/SOT, Edin Dzeko shots-on-target

Source: ESPN hidden site API (`site.api.espn.com/apis/site/v2/sports/soccer/<league>/summary?event=<id>`),
fetched directly via WebFetch (no proxy needed, NOT blocked unlike FBref/Sofascore/WhoScored/FotMob HTML).
League codes used: `fifa.worldq.uefa` (BIH WC qualifiers/playoffs), `fifa.friendly` (Canada friendlies).
VERIFIED_API tier - real per-match boxscore data, fetched 2026-06-12.

## Bosnia & Herzegovina - last 5 competitive matches: fouls committed

| Date | Opponent (venue) | BIH Fouls | Opp Fouls | BIH SOT | Opp SOT | Event ID |
|---|---|---|---|---|---|---|
| 2026-03-31 | Italy (H, playoff final) | 18 | 9 | 11 | 3 | 761952 |
| 2026-03-26 | Wales (A, playoff semi) | 20 | 8 | 5 | 3 | 761381 |
| 2025-11-18 | Austria (A) | 9 | 8 | 1 | 3 | 724913 |
| 2025-11-15 | Romania (H) | 15 | 16 | 4 | 3 | 724895 |
| 2025-10-09 | Cyprus (A) | 19 | 16 | 6 | 3 | 725021 |

- **BIH foul rate: mean = 16.2 fouls/match (81 fouls / 5 matches)**, range 9-20. Consistently a
  high-foul team (4 of 5 matches BIH committed MORE fouls than opponent; only Romania match
  BIH fouled less, 15 vs 16, essentially even).
- BIH SOT: 1, 4, 5, 6, 11 -> mean 5.4/match (very high variance - includes a 30-shot demolition
  of Italy and a defensive 8-shot performance vs Austria).

## Canada - last several friendlies: fouls committed

ESPN's `fifa.friendly` summary endpoint for Canada's 2025 friendlies (Venezuela 758716, Ecuador
758183, Colombia 746411, Australia 749807, Wales 733167) did NOT expose a team fouls/corners/
possession boxscore (only partial player-level shot/pass/card data) - **no fouls data obtained
for Canada from this source**. Shots/SOT for Canada in these matches: vs Venezuela 2 shots/1 SOT,
vs Ecuador 2 shots/0 SOT (Jonathan David), vs Colombia 2 shots/1 SOT, vs Australia 4 shots/2 SOT
(Buchanan).

## Edin Dzeko - individual shots/SOT in BIH's last 5 competitive matches

| Date | Opponent | Played? | Shots | SOT | Fouls committed | Notes |
|---|---|---|---|---|---|---|
| 2026-03-31 | Italy | Yes (90+ET) | 3 | 1 | 2 | Subbed at 115' |
| 2026-03-26 | Wales | NOT in lineup | - | - | - | Rested/rotated |
| 2025-11-18 | Austria | No individual stats found (likely didn't play/rest) | - | - | - | - |
| 2025-11-15 | Romania | Yes (90') | 5 | 1 | 2 | Scored 1 goal, 1 yellow card |
| 2025-10-09 | Cyprus | NOT in lineup | - | - | - | Rested/rotated |

- In the 2 matches Dzeko played, he recorded **1 SOT in both** (out of 3 and 5 total shots
  respectively) -> 1 SOT in 2/2 appearances = 100% in this small sample, but sample is tiny.
- He's being rotated heavily (rested vs Wales, Austria, Cyprus) - age 40, BIH using him as an
  impact starter in bigger matches (Italy playoff final, Romania).

## Next steps / still needed
- Canada fouls rate still unconfirmed from real data.
- Larger Dzeko sample (more matches, ideally including club form) would help.
