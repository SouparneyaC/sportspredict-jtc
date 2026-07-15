"""
Point-in-time Elo replay for Argentina and Switzerland, entering the 2026-07-12 QF
(match_id f444b793-6a20-48a1-862c-e748781b5f91).

Same staleness bug as documented in the prior replay scripts this project has built
(qf_point_in_time_elo_replay.py, nor_eng_qf_point_in_time_elo_replay.py): elo_current_ratings.csv
is frozen at pre-tournament baselines. Argentina and Switzerland were both in the original
r16_point_in_time_elo_replay.py 10-team set (their entering-R16 ratings are taken verbatim from
that script's output), so this replay only needs to add each team's R16 game.

Argentina's R16: beat Egypt 3-2 (ESPN event 760509, 2026-07-07, live-confirmed).
Switzerland's R16: 0-0 vs Colombia, won 4-3 on penalties (ESPN event 760508, 2026-07-07,
live-confirmed) -- treated as a draw (0.5-0.5) for Elo purposes, same convention as
Egypt-Australia in r16_point_in_time_elo_replay.py ("won on pens; treated as draw for Elo").

Neutral venue: neither Argentina nor Switzerland is USA/MX/CA, and neither R16 opponent
(Egypt, Colombia) is either -- both games neutral=True.
"""

K = 60


def g_factor(goal_diff):
    ad = abs(goal_diff)
    if ad <= 1:
        return 1.0
    if ad == 2:
        return 1.5
    return (11 + ad) / 8


def we(r_a, r_b, neutral, a_is_home):
    dr = r_a - r_b
    if not neutral:
        dr += 100 if a_is_home else -100
    return 1 / (10 ** (-dr / 400) + 1)


def update(r_a, r_b, score_a, score_b, neutral, a_is_home):
    if score_a > score_b:
        w = 1.0
    elif score_a == score_b:
        w = 0.5
    else:
        w = 0.0
    w_e = we(r_a, r_b, neutral, a_is_home)
    gd = score_a - score_b
    return r_a + K * g_factor(gd) * (w - w_e), w_e


# Entering-R16 ratings, taken verbatim from r16_point_in_time_elo_replay.py output logic
# (Argentina and Switzerland were both in that script's original 10-team set).
# Recomputed here directly from the same INITIAL baselines + group/R32 games for traceability.
INITIAL = {"Argentina": 2189.5282, "Switzerland": 1951.7868}
FROZEN_OPP = {
    "Algeria": 1872.4250, "Austria": 1885.0498, "Jordan": 1774.1438, "Cape Verde": 1653.4535,
    "Qatar": 1564.5424, "Bosnia and Herzegovina": 1652.8208, "Canada": 1901.9781,
    "Egypt": 1809.7527, "Colombia": 2063.7111,
}

GROUP_AND_R32_GAMES = [
    # (team, opponent, team_score, opp_score, neutral, team_is_home)
    ("Argentina", "Algeria", 3, 0, True, False),
    ("Argentina", "Austria", 2, 0, True, False),
    ("Argentina", "Jordan", 3, 1, True, False),
    ("Argentina", "Cape Verde", 3, 2, True, False),  # R32, after ET; regulation was level
    ("Switzerland", "Qatar", 1, 1, True, False),
    ("Switzerland", "Bosnia and Herzegovina", 4, 1, True, False),
    ("Switzerland", "Canada", 2, 1, False, False),  # Canada true home; Switzerland away
    ("Switzerland", "Algeria", 2, 0, True, False),  # R32
]

R16_GAMES = [
    ("Argentina", "Egypt", 3, 2, True, False),
    ("Switzerland", "Colombia", 0, 0, True, False),  # won on pens; treated as a draw for Elo
]

if __name__ == "__main__":
    elo = dict(INITIAL)
    print("=== Group + R32 replay ===")
    for team, opp, ts, os_, neutral, team_home in GROUP_AND_R32_GAMES:
        r_team = elo[team]
        r_opp = FROZEN_OPP[opp]
        new_team, we_team = update(r_team, r_opp, ts, os_, neutral, team_home)
        elo[team] = new_team
        print(f"{team} {ts}-{os_} {opp}: {r_team:.2f} -> {new_team:.2f} ({new_team-r_team:+.2f})")

    print()
    print("=== Entering R16 ===")
    for t in elo:
        print(f"{t}: {elo[t]:.2f}")

    print()
    print("=== R16 replay ===")
    for team, opp, ts, os_, neutral, team_home in R16_GAMES:
        r_team = elo[team]
        r_opp = FROZEN_OPP[opp]
        new_team, we_team = update(r_team, r_opp, ts, os_, neutral, team_home)
        elo[team] = new_team
        print(f"{team} {ts}-{os_} {opp} (pens if 0-0): {r_team:.2f} -> {new_team:.2f} ({new_team-r_team:+.2f})")

    print()
    print("=== Point-in-time Elo entering QF (correct) ===")
    print(f"Argentina:   {elo['Argentina']:.2f}")
    print(f"Switzerland: {elo['Switzerland']:.2f}")
    print(f"Diff (Argentina - Switzerland): {elo['Argentina'] - elo['Switzerland']:+.2f}")

    print()
    stale_arg, stale_sui = INITIAL["Argentina"], INITIAL["Switzerland"]
    print("=== vs stale pre-tournament-frozen values ===")
    print(f"Argentina stale:   {stale_arg:.2f}  (correct {elo['Argentina']:.2f}, delta {elo['Argentina']-stale_arg:+.2f})")
    print(f"Switzerland stale: {stale_sui:.2f}  (correct {elo['Switzerland']:.2f}, delta {elo['Switzerland']-stale_sui:+.2f})")
