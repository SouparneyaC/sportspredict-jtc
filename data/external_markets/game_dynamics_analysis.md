# Game Dynamics Analysis - Goal/Foul/Card Timelines Across All 7 Settled Matches

**Purpose**: triggered by JPN-NED Q1 (-25.37, our worst result that match), where Japan was
AHEAD on fouls 6-5 through 86', then Netherlands committed a reactive foul (carded "for a bad
foul") 2-3min after conceding Japan's 88' equalizer, tying the count 7-7 and flipping "Japan
more fouls than Netherlands" from YES to NO. This doc checks whether "conceding a goal
triggers a reactive foul (sometimes a card) from the conceding team within minutes" is a
real, repeatable pattern across all 7 settled World Cup 2026 matches, and what it implies for
pricing "Team A more [count stat] than Team B" props in future (especially higher-stakes
semifinal/final) matches.

**Data source**: ESPN hidden API match summaries (`commentary` + `keyEvents` + `boxscore.statistics`),
fetched 2026-06-14, saved to `raw_summaries/*.json`. Event IDs: KOR-CZE=760414, CAN-BIH=760416,
USA-PAR=760417, QAT-SUI=760420, BRA-MAR=760419, GER-CUR=760422, JPN-NED=760425 (already
extracted in `jpn_ned_2026-06-14.json`).

Note: commentary-derived foul counts are occasionally off by 1-2 from the final boxscore
(commentary feed isn't 100% complete) - directionally fine, exact tallies use the boxscore.

---

## Per-match final stats

| Match | Result | Team A fouls | Team B fouls | Diff | Team A cards (Y/R) | Team B cards (Y/R) |
|---|---|---|---|---|---|---|
| KOR-CZE | Korea 2-1 Czechia | KOR 9 | CZE 16 | 7 | 1/0 | 0/0 |
| CAN-BIH | Canada 1-1 Bosnia | CAN 10 | BIH 20 | 10 | 2/0 | 3/0 |
| USA-PAR | USA 4-1 Paraguay | USA 13 | PAR 17 | 4 | 1/0 | 5/0 |
| QAT-SUI | Qatar 1-1 Switzerland | QAT 12 | SUI 11 | 1 | 2/0 | 1/0 |
| BRA-MAR | Brazil 1-1 Morocco | BRA 16 | MAR 14 | 2 | 2/0 | 0/0 |
| GER-CUR | Germany 7-1 Curaçao | GER 18 | CUR 11 | 7 | 0/0 | 0/0 |
| JPN-NED | Netherlands 2-2 Japan | NED 7 | JPN 7 | **0** | 3/0 | 0/0 |

---

## Goal -> "does the conceding team foul soon after?" table

For every goal with meaningful match time remaining (24 total across 7 matches; QAT-SUI's
only goal was a 90+4' own goal with no time left, and 2 late USA-PAR/GER-CUR goals near
full-time are noted but have little follow-up window):

| Match | Goal (min) | Conceding team | Next foul by conceder | Gap (min) | <=5min? | <=10min? | Card "for a bad foul"? |
|---|---|---|---|---|---|---|---|
| KOR-CZE | 59' | South Korea | 62' | 3 | YES | YES | no (37min later) |
| KOR-CZE | 67' | Czechia | 70' | 3 | YES | YES | no |
| KOR-CZE | 80' | Czechia | 83' | 3 | YES | YES | no |
| CAN-BIH | 21' | Canada | 53' | 32 | no | no | no (32min later) |
| CAN-BIH | 78' | Bosnia | 88' | 10 | no | borderline | 90+3' (15min later) |
| USA-PAR | 7' | Paraguay | 9' | 2 | YES | YES | **10' (3min) - YES** |
| USA-PAR | 31' | Paraguay | 38' | 7 | no | YES | no (22min later) |
| USA-PAR | 45+5' | Paraguay | 48'(56') | 6 | no | YES | no |
| USA-PAR | 73' | USA | 73' | 0 | YES | YES | no |
| GER-CUR | 6' | Curaçao | 13' | 7 | no | YES | no |
| GER-CUR | 21' | Germany | 21' | 0 | YES | YES | no |
| GER-CUR | 38' | Curaçao | 40' | 2 | YES | YES | no |
| GER-CUR | 47' | Curaçao | 50' | 3 | YES | YES | no |
| GER-CUR | 68' | Curaçao | 87' | 19 | no | no | no |
| GER-CUR | 78' | Curaçao | 87' | 9 | no | YES | no |
| GER-CUR | 88' | Curaçao | 90+4' | 6 | no | YES | no |
| BRA-MAR | 21' | Brazil | 29' | 8 | no | YES | 37' (16min later) |
| BRA-MAR | 32' | Morocco | 39' | 7 | no | YES | no |
| JPN-NED | 51' | Japan | 62' | 11 | no | no | no |
| JPN-NED | 57' | Netherlands | 61' | 4 | YES | YES | **61' (4min) - YES** |
| JPN-NED | 64' | Japan | 65' | 1 | YES | YES | no |
| JPN-NED | 88' | Netherlands | 90+1' | 2-3 | YES | YES | **90+1' (2-3min) - YES** |

**Totals (n=22 with non-NA gap, 24 goal-events checked):**
- Conceding team commits its NEXT foul within **5 minutes**: **11/24 = 46%**
- Within **10 minutes**: **19/24 = 79%**
- That foul is specifically carded "for a bad foul" within 5 min of conceding: **3/24 = 12.5%**
  (USA-PAR 7'->10', JPN-NED 57'->61', JPN-NED 88'->90+1')

---

## Verdict on "conceding triggers a reactive foul/card"

**Moderately confirmed, directional only (n=24, 7 matches).** ~46% of goals are followed by
the conceding team's next foul within 5 minutes, and ~79% within 10 minutes - both rates feel
elevated relative to a naive baseline (most teams foul roughly once every 5-10 minutes on
average across 90+ min, so "a foul somewhere in the next 10 minutes" isn't guaranteed but is
common - this isn't proof of causation, just a notable co-occurrence rate).

The SPECIFIC "reactive card for a bad foul within minutes of conceding" pattern - the exact
mechanism that decided JPN-NED Q1 - happened **3 times across 24 goal-events (12.5%)**, and
notably **2 of the 3 instances are in JPN-NED itself** (57'->61' and 88'->90+1'), plus one in
USA-PAR (7'->10', Paraguay conceding an early own goal and immediately picking up a reckless
yellow). This is too small a sample to call a "rule," but it's consistent with: **a team that
has just conceded is at elevated risk of an immediate emotional/reactive foul, and
occasionally a card** - worth a mental flag in-running, not a pre-match pricing adjustment
(we can't predict WHEN a goal will happen).

**KOR-CZE is the cleanest "every goal -> quick reaction" case**: all 3 goals were followed by
the conceding team's next foul exactly 3 minutes later, every time. Small sample but striking
regularity.

**CAN-BIH and GER-CUR's 68' goal are the clearest non-hits**: Canada didn't foul again for 32
minutes after conceding at 21' (they were likely sitting deeper/more cautious rather than
reacting emotionally), and Curaçao went 19 minutes without a foul after Germany's 68' goal
(by that point, 5-1 down, Curaçao may have been too demoralized/disengaged to commit fresh
fouls - the "blowout fatigue" effect is the opposite of "reactive anger").

---

## Foul-count differential vs match result (tie-proneness)

| Match | Result type | Foul diff |
|---|---|---|
| QAT-SUI | Draw (1-1) | 1 |
| BRA-MAR | Draw (1-1) | 2 |
| JPN-NED | Draw (2-2) | **0 (exact tie)** |
| CAN-BIH | Draw (1-1) | 10 (outlier) |
| USA-PAR | Decisive (4-1) | 4 |
| KOR-CZE | Decisive (2-1) | 7 |
| GER-CUR | Blowout (7-1) | 7 |

**3 of 4 draws (QAT-SUI, BRA-MAR, JPN-NED) had foul-count differentials of 0-2** - i.e., very
close to, or exactly, tied. The 3 non-draw matches all had differentials >=4. CAN-BIH (a draw
with diff=10) is the clear outlier - Bosnia, playing as the underdog defending a point on the
road, fouled at double Canada's rate (20 vs 10) despite the scoreline being level throughout
much of the match (BIH led 1-0 from 21' to 78').

**This supports RULE8's core intuition** (a closely-contested match-result is associated with
closely-contested counting stats) but CAN-BIH shows it's not universal - an underdog playing
a containment/spoiler game can rack up a large foul tally even in a drawn match. The
distinguishing factor may be WHETHER the underdog is ahead/level (less desperate, fewer
fouls - QAT-SUI, BRA-MAR, JPN-NED's Japan) vs trailing for most of the match (more defensive
fouling out of necessity - CAN-BIH's Bosnia, which led only 21'-78' then defended a draw...
actually Bosnia LED for most of the match here, so this doesn't fully explain it either -
flag as genuinely unexplained, possibly just team-specific discipline/tactics).

---

## Other watch items (not yet patterns, n=1-2 each)

1. **GER-CUR 21'**: Germany's only concession produced an IMMEDIATE (0min) Germany foul in
   the same minute - but Germany went on to score 6 more goals, so this had zero pricing
   relevance. Reactive fouls from a DOMINANT favorite after a rare concession don't seem to
   cascade into anything.
2. **USA-PAR Paraguay**: conceded 3 times in the first half (7', 31', 45+5') and fouled within
   2/7/6 minutes each time, picking up 2 of their eventual 5 yellow cards in the first hour -
   a team that's being blown out early may accumulate cards/fouls steadily through
   frustration, independent of any single "reactive moment."
3. **CAN-BIH had the most cards of any match (5 total) and the largest foul differential
   (10)** despite being a 1-1 draw - if BIH-style fixtures (decided underdog, road match,
   playing for a point) recur, foul/card props on the underdog may run HIGH regardless of
   scoreline competitiveness. This is the one case where our original GER-CUR/QAT-SUI-style
   "underdog fouls more" prior (the one that INFORMED our JPN-NED Q1 estimate) was actually
   correct in direction - just not in JPN-NED specifically.

---

## How to apply going forward

1. **RULE8 (draw-probability shrinkage for "more than" count props) gets modest support**:
   3/4 draws had near-zero foul differentials. But CAN-BIH is a real counterexample, so RULE8
   should be treated as "shrink toward 50%, but don't assume a tie is GUARANTEED even in a
   competitive match" - a 0.55-0.60 estimate (mild lean toward the historically-higher-fouling
   team) rather than JPN-NED's 0.70-0.72 is probably the right calibration for "Team A more
   fouls than Team B" when the pre-match draw price is elevated (>=25%).
2. **The "underdog fouls more" prior (RULE4/RULE7 lineage) isn't wrong - it's conditional on
   the underdog being OUTCLASSED/chasing**, not just "the underdog" by market price. CAN-BIH's
   Bosnia (underdog, but LED the match 21'-78') still fouled heavily - so "underdog" alone
   predicts more fouls; "underdog AND well-organized/competitive" (JPN-NED's Japan, who
   matched Netherlands goal-for-goal) does NOT reliably predict more fouls. The signal isn't
   just market-implied team quality, it's whether the underdog is getting OVERRUN
   (GER-CUR/QAT-SUI pattern, more fouls) vs PLAYING ON EVEN TERMS (JPN-NED, fouls converge).
3. **In-running implication (for live/late pricing if ever applicable)**: a goal in the final
   15 minutes that changes a "more fouls than" prop's live state should be treated as
   genuinely live risk - conceding teams foul again within 5min ~46% of the time, and ~12.5%
   of goals produce a reactive CARD within minutes. A 6-5 lead with 2 minutes left on a count
   prop is NOT safe.
4. **Sample size caveat**: n=24 goal-events, 7 matches. Every number above is directional,
   not statistically robust - re-run this analysis after the next batch of settled matches
   (semis/final) to firm up or revise.
