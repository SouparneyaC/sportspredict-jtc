"""
Point-in-time Elo replay for 5 R16 matches (Switzerland-Colombia, Argentina-Egypt,
USA-Belgium, Portugal-Spain, Mexico-England), built to answer a specific question:
what would each team's Elo rating have been at kickoff, using ONLY results known
before that kickoff (no lookahead)?

Why this script exists: `data/processed/elo_current_ratings.csv` and
`data/processed/elo_match_panel.csv` turned out NOT to be a live, incrementally-updated
point-in-time series through the WC2026 tournament. `data/international_results/results.csv`
records every WC2026 match's score as NA (it's a fixture list, not a results file), so
model/elo.py never actually processed a single WC2026 result -- every team's "current"
Elo is frozen at its pre-tournament (early June 2026) friendly-derived value, verified by
checking that e.g. Argentina's pre-match Elo is identical (2189.5282) across all three of
its group-stage rows in elo_match_panel.csv despite winning 3-0, 2-0, and 3-1.

This script fixes that by replaying each of the 10 teams' actual group-stage + Round-of-32
results (real scores gathered from data/processed/espn_match_panel.csv and the settled
matches/*/06_post_match_results.json files) through the exact update formula in
model/elo.py (K=60 for FIFA World Cup, standard G/We logistic formula, +100 home advantage
only when neutral==False), starting from each team's confirmed pre-tournament baseline.
Opponents outside this 10-team set (e.g. Qatar, Bosnia, Cape Verde) are held at their own
frozen pre-tournament rating as a deliberate simplification -- they are eliminated by R16
and this avoids replaying the entire tournament bracket to get a second-order correction.

Home/neutral determination: neutral=FALSE (true home advantage) only when USA, Mexico, or
Canada is a participant (confirmed via data/international_results/results.csv's own
neutral column for every group-stage game); every other pairing is neutral=TRUE regardless
of which US/MX/CA city hosts it. Mexico vs England's R16 fixture was confirmed (via
matches/Mexico_vs_England/espn_match_summary_raw.json gameInfo.venue) to be in Mexico City,
so Mexico keeps true home advantage into the Round of 16; USA vs Belgium's exact R16 venue
was not recoverable from saved files and is assumed (not confirmed) to follow the same
pattern as USA's earlier home fixtures.
"""

import math

INITIAL = {
    'Switzerland': 1951.7868, 'Colombia': 2063.7111, 'Argentina': 2189.5282, 'Egypt': 1809.7527,
    'United States': 1827.4984, 'Belgium': 1944.7165, 'Portugal': 2056.5074, 'Spain': 2225.5610,
    'Mexico': 1984.7936, 'England': 2090.3687,
}
FROZEN_OPP = {
    'Qatar': 1564.5424, 'Bosnia and Herzegovina': 1652.8208, 'Canada': 1901.9781, 'Algeria': 1872.4250,
    'Paraguay': 1917.7456, 'Australia': 1900.7948, 'Turkey': 1974.4414, 'Cape Verde': 1653.4535,
    'Uzbekistan': 1818.9133, 'DR Congo': 1763.2036, 'Iran': 1894.4322, 'New Zealand': 1730.8705,
    'Senegal': 1912.8104, 'Austria': 1885.0498, 'Croatia': 1973.5928, 'Ghana': 1625.5008, 'Jordan': 1774.1438,
    'South Africa': 1663.3169, 'South Korea': 1879.9769, 'Czech Republic': 1806.3989, 'Ecuador': 2028.0889,
    'Saudi Arabia': 1693.8249, 'Uruguay': 1975.0705, 'Panama': 1859.0601,
}
K = 60

def g_factor(goal_diff):
    ad = abs(goal_diff)
    if ad <= 1: return 1.0
    if ad == 2: return 1.5
    return (11 + ad) / 8

def we(r_a, r_b, neutral, a_is_home):
    dr = r_a - r_b
    if not neutral:
        dr += 100 if a_is_home else -100
    return 1 / (10 ** (-dr / 400) + 1)

def update(r_a, r_b, score_a, score_b, neutral, a_is_home):
    if score_a > score_b: w = 1.0
    elif score_a == score_b: w = 0.5
    else: w = 0.0
    w_e = we(r_a, r_b, neutral, a_is_home)
    gd = score_a - score_b
    new_r_a = r_a + K * g_factor(gd) * (w - w_e)
    return new_r_a

elo = dict(INITIAL)

# (team_A, team_B, score_A, score_B, neutral, a_is_home)
# a_is_home only matters if neutral=False
games = [
    ('Switzerland', 'Qatar', 1, 1, True, False),
    ('Belgium', 'Egypt', 1, 1, True, False),
    ('Spain', 'Cape Verde', 0, 0, True, False),
    ('Argentina', 'Algeria', 3, 0, True, False),
    ('Portugal', 'DR Congo', 1, 1, True, False),
    ('Colombia', 'Uzbekistan', 3, 1, True, False),
    ('England', 'Croatia', 4, 2, True, False),
    ('Switzerland', 'Bosnia and Herzegovina', 4, 1, True, False),
    ('Mexico', 'South Korea', 1, 0, False, True),
    ('United States', 'Australia', 2, 0, False, True),
    ('Belgium', 'Iran', 0, 0, True, False),
    ('Egypt', 'New Zealand', 3, 1, True, False),
    ('Spain', 'Saudi Arabia', 4, 0, True, False),
    ('Argentina', 'Austria', 2, 0, True, False),
    ('England', 'Ghana', 0, 0, True, False),
    ('Colombia', 'DR Congo', 1, 0, True, False),
    ('Portugal', 'Uzbekistan', 5, 0, True, False),
    ('Switzerland', 'Canada', 2, 1, False, False),   # Canada true home; Switzerland away, so a_is_home=False for Switzerland-as-A
    ('Mexico', 'Czech Republic', 3, 0, False, True),
    ('United States', 'Turkey', 2, 3, False, True),
    ('Egypt', 'Iran', 1, 1, True, False),
    ('Belgium', 'New Zealand', 5, 1, True, False),
    ('Spain', 'Uruguay', 1, 0, True, False),
    ('Colombia', 'Portugal', 0, 0, True, False),
    ('Argentina', 'Jordan', 3, 1, True, False),
    ('England', 'Panama', 2, 0, True, False),
    # R32
    ('Mexico', 'Ecuador', 2, 0, False, True),
    ('Switzerland', 'Algeria', 2, 0, True, False),
    ('United States', 'Bosnia and Herzegovina', 2, 0, False, True),
    ('England', 'DR Congo', 2, 1, True, False),
    ('Portugal', 'Croatia', 2, 1, True, False),
    ('Spain', 'Austria', 3, 0, True, False),
    ('Belgium', 'Senegal', 3, 2, True, False),
    ('Argentina', 'Cape Verde', 3, 2, True, False),  # after ET; regulation was level
    ('Egypt', 'Australia', 1, 1, True, False),  # Egypt won on pens; treated as draw for Elo
    ('Colombia', 'Ghana', 1, 0, True, False),
]

for team_a, team_b, sa, sb, neutral, a_home in games:
    r_a = elo[team_a]
    r_b = elo[team_b] if team_b in elo else FROZEN_OPP[team_b]
    new_a = update(r_a, r_b, sa, sb, neutral, a_home)
    if team_b in elo:
        new_b = update(r_b, r_a, sb, sa, neutral, not a_home if not neutral else False)
        elo[team_b] = new_b
    elo[team_a] = new_a

print("=== Point-in-time Elo entering R16 (no lookahead) ===")
for t in sorted(elo):
    print(f"{t:20s} {elo[t]:.2f}   (frozen pre-tournament was {INITIAL[t]:.2f}, delta {elo[t]-INITIAL[t]:+.2f})")

print()
print("=== R16 matchup diffs (correct, point-in-time) vs frozen-baseline diffs (what I'd wrongly get from elo_current_ratings.csv) ===")
matchups = [('Switzerland','Colombia'), ('Argentina','Egypt'), ('United States','Belgium'), ('Portugal','Spain'), ('Mexico','England')]
for a,b in matchups:
    correct_diff = elo[a] - elo[b]
    frozen_diff = INITIAL[a] - INITIAL[b]
    print(f"{a} vs {b}: correct diff={correct_diff:+.2f}   frozen(stale) diff={frozen_diff:+.2f}   difference={correct_diff-frozen_diff:+.2f}")
