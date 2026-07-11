"""
Point-in-time Elo replay extending r16_point_in_time_elo_replay.py one more round,
to answer: what are Spain's and Belgium's correct Elo ratings entering the
2026-07-10 Spain vs Belgium quarterfinal (match_id 5da5b95b-4b52-4b16-8b8d-dd9547f749ca)?

Why this script exists: the same staleness bug documented in r16_point_in_time_elo_replay.py
(data/international_results/results.csv records every WC2026 match's score as NA past
2026-06-09, so model/elo.py never processed a single real WC2026 result) was confirmed
still present when scoping this match -- data/processed/elo_match_panel.csv shows Spain's
and Belgium's "current" Elo frozen at their pre-tournament values (2225.56 / 1944.72).

This script takes the entering-R16 ratings already computed by r16_point_in_time_elo_replay.py
(Portugal 2087.23, Spain 2229.85, United States 1854.01, Belgium 1983.52) and replays the
actual R16 results, pulled live from the ESPN scoreboard API (confirmed 2026-07-10, no
lookahead beyond what's now public):

  Portugal 0 - 1 Spain     (ESPN event 760506, 2026-07-06, neutral venue)
  United States 1 - 4 Belgium  (ESPN event 760507, 2026-07-06, USA true home advantage)

Same update formula as model/elo.py / r16_point_in_time_elo_replay.py: K=60 for FIFA World
Cup, margin-of-victory G-factor, +100 home term only when neutral==False. USA keeps true
home advantage into the R16 (consistent with every other USA fixture in this project);
Portugal-Spain is neutral since neither team is USA/MX/CA, even though this later moves to
a US venue for the QF (SoFi Stadium, Inglewood CA, 28m altitude, confirmed via ESPN
scoreboard event 760511) -- host-nation neutrality only applies when USA/MX/CA is itself
a participant, not merely the venue.

Net effect: the naive stale-Elo diff (Spain 2225.56 - Belgium 1944.72 = +280.84) overstates
Spain's edge by 64.23 points relative to the correct point-in-time diff, because it was
blind to Belgium's 4-1 demolition of the USA -- a much stronger R16 performance than
Spain's narrow 1-0 over Portugal.
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


# Entering-R16 ratings, taken verbatim from r16_point_in_time_elo_replay.py output.
ENTERING_R16 = {
    "Portugal": 2087.23,
    "Spain": 2229.85,
    "United States": 1854.01,
    "Belgium": 1983.52,
}

# Actual R16 results (ESPN scoreboard, confirmed 2026-07-10).
R16_GAMES = [
    # (team_a, team_b, score_a, score_b, neutral, a_is_home)
    ("Spain", "Portugal", 1, 0, True, False),
    ("Belgium", "United States", 4, 1, False, False),  # USA is true home, so Belgium a_is_home=False
]

if __name__ == "__main__":
    elo = dict(ENTERING_R16)
    print("=== R16 replay: Spain & Belgium entering the QF ===")
    for team_a, team_b, sa, sb, neutral, a_home in R16_GAMES:
        r_a, r_b = elo[team_a], elo[team_b]
        new_a, we_a = update(r_a, r_b, sa, sb, neutral, a_home)
        new_b, we_b = update(r_b, r_a, sb, sa, neutral, (not a_home) if not neutral else False)
        elo[team_a] = new_a
        elo[team_b] = new_b
        print(f"{team_a} {sa}-{sb} {team_b} (neutral={neutral}): "
              f"{team_a} {r_a:.2f} -> {new_a:.2f} ({new_a - r_a:+.2f}), "
              f"{team_b} {r_b:.2f} -> {new_b:.2f} ({new_b - r_b:+.2f})")

    print()
    print("=== Point-in-time Elo entering QF (correct) ===")
    print(f"Spain:   {elo['Spain']:.2f}")
    print(f"Belgium: {elo['Belgium']:.2f}")
    print(f"Diff (Spain - Belgium): {elo['Spain'] - elo['Belgium']:+.2f}")

    print()
    stale_spain, stale_belgium = 2225.56, 1944.72
    print("=== vs stale pre-tournament-frozen values (what elo_match_panel.csv currently returns) ===")
    print(f"Spain stale:   {stale_spain:.2f}  (correct {elo['Spain']:.2f}, delta {elo['Spain']-stale_spain:+.2f})")
    print(f"Belgium stale: {stale_belgium:.2f}  (correct {elo['Belgium']:.2f}, delta {elo['Belgium']-stale_belgium:+.2f})")
    stale_diff = stale_spain - stale_belgium
    correct_diff = elo["Spain"] - elo["Belgium"]
    print(f"Stale diff: {stale_diff:+.2f}  Correct diff: {correct_diff:+.2f}  (shift {correct_diff-stale_diff:+.2f})")
