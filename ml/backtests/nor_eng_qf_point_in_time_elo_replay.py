"""
Point-in-time Elo replay for Norway and England, entering the 2026-07-11 QF
(match_id 8fd166b3-1b8b-4834-a761-ba7caf26ed93).

Same staleness bug as documented in r16_point_in_time_elo_replay.py and
qf_point_in_time_elo_replay.py: data/processed/elo_current_ratings.csv is frozen at each
team's pre-tournament baseline. Neither Norway nor England was covered by the existing R16
replay script's 10-team set, so this is a fresh replay built from
data/processed/unified_team_match_panel.csv (verified real scores, not the NA-filled
results.csv) covering group stage + R32 + R16 for both teams.

Norway path: Iraq 4-1 (W), Senegal 3-2 (W), France 1-4 (L) -- group;
             Ivory Coast 2-1 (W) -- R32; Brazil 2-1 (W) -- R16 (confirmed upset,
             matches/Brazil_vs_Norway/06_post_match_results.json).
England path: Croatia 4-2 (W), Ghana 0-0 (D), Panama 2-0 (W) -- group;
              DR Congo 2-1 (W) -- R32; Mexico 3-2 (W) -- R16
              (matches/Mexico_vs_England/06_post_match_results.json).

All games neutral=True (neither Norway nor England is USA/MX/CA, and no game in either
team's path had USA/MX/CA as a participant, even though several were played on US soil --
consistent with the project's home-advantage convention: venue country alone doesn't grant
true home advantage, only USA/MX/CA-as-participant does).

Opponent Elo for non-tracked teams (Iraq, Senegal, France, Croatia, Ghana, Panama,
Ivory Coast, DR Congo, Brazil, Mexico) held at their frozen pre-tournament
elo_current_ratings.csv value, same simplification as r16_point_in_time_elo_replay.py's
FROZEN_OPP dict.
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


# Pre-tournament baselines, from data/processed/elo_current_ratings.csv.
BASELINE = {
    "Norway": 1983.8379,
    "England": 2090.3687,
}

# Frozen opponent ratings (not tracked through the tournament, same simplification as
# r16_point_in_time_elo_replay.py's FROZEN_OPP).
FROZEN_OPP = {
    "Iraq": 1736.5496,
    "Senegal": 1912.8104,
    "France": 2129.0524,
    "Croatia": 1973.5928,
    "Ghana": 1625.5008,
    "Panama": 1859.0601,
    "Ivory Coast": 1814.7168,
    "DR Congo": 1763.2036,
    "Brazil": 2068.6320,
    "Mexico": 1984.7936,
}

# (team, opponent, team_score, opp_score, neutral, team_is_home)
GAMES = [
    ("Norway", "Iraq", 4, 1, True, False),
    ("Norway", "Senegal", 3, 2, True, False),
    ("Norway", "France", 1, 4, True, False),
    ("Norway", "Ivory Coast", 2, 1, True, False),
    ("Norway", "Brazil", 2, 1, True, False),
    ("England", "Croatia", 4, 2, True, False),
    ("England", "Ghana", 0, 0, True, False),
    ("England", "Panama", 2, 0, True, False),
    ("England", "DR Congo", 2, 1, True, False),
    ("England", "Mexico", 3, 2, True, False),
]

if __name__ == "__main__":
    elo = dict(BASELINE)
    print("=== Point-in-time Elo replay: Norway & England entering the 2026-07-11 QF ===")
    for team, opp, ts, os_, neutral, team_home in GAMES:
        r_team = elo[team]
        r_opp = FROZEN_OPP[opp]
        new_team, we_team = update(r_team, r_opp, ts, os_, neutral, team_home)
        elo[team] = new_team
        print(f"{team} {ts}-{os_} {opp} (neutral={neutral}): "
              f"{team} {r_team:.2f} -> {new_team:.2f} ({new_team - r_team:+.2f}), "
              f"pre-game W_e={we_team:.3f}")

    print()
    print("=== Point-in-time Elo entering QF (correct) ===")
    print(f"Norway:  {elo['Norway']:.2f}")
    print(f"England: {elo['England']:.2f}")
    print(f"Diff (England - Norway): {elo['England'] - elo['Norway']:+.2f}")

    print()
    print("=== vs stale pre-tournament-frozen values ===")
    print(f"Norway stale:  {BASELINE['Norway']:.2f}  (correct {elo['Norway']:.2f}, delta {elo['Norway']-BASELINE['Norway']:+.2f})")
    print(f"England stale: {BASELINE['England']:.2f}  (correct {elo['England']:.2f}, delta {elo['England']-BASELINE['England']:+.2f})")
    stale_diff = BASELINE["England"] - BASELINE["Norway"]
    correct_diff = elo["England"] - elo["Norway"]
    print(f"Stale diff: {stale_diff:+.2f}  Correct diff: {correct_diff:+.2f}  (shift {correct_diff-stale_diff:+.2f})")
