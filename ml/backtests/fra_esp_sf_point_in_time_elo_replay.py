"""
Point-in-time Elo replay for France and Spain, entering the 2026-07-14 semifinal
(match_id de7b7b6f-f3a8-4948-af5e-f0f4565728d0).

Same staleness bug as documented in r16_point_in_time_elo_replay.py and every QF replay
since: data/processed/elo_current_ratings.csv is frozen at each team's pre-tournament
baseline (verified again here -- France shows 2129.0524, Spain shows 2225.5610, identical
to their group-stage-entering values).

Spain was already tracked through the R16 (r16_point_in_time_elo_replay.py) and QF
(qf_point_in_time_elo_replay.py) replay scripts -- this script takes Spain's entering-QF
rating verbatim from qf_point_in_time_elo_replay.py's output (2248.18) and adds the actual
QF result:
    Spain 2 - 1 Belgium (matches/Spain_vs_Belgium/06_post_match_results.json, 2026-07-10)

France was not covered by any prior replay script -- built fresh here from real WC2026
scores in data/processed/espn_match_panel.csv (group stage + R32) and
matches/*/06_post_match_results.json (R16, QF):
    Group: France 3-1 Senegal (2026-06-16), France 3-0 Iraq (2026-06-22),
           France 4-1 Norway (2026-06-26)
    R32:   France 3-0 Sweden (2026-06-30)
    R16:   France 1-0 Paraguay (2026-07-04, matches/France_vs_Paraguay/06_post_match_results.json)
    QF:    France 2-0 Morocco (2026-07-09, matches/France_vs_Morocco/06_post_match_results.json)

Opponents outside the currently-tracked set (Senegal, Iraq, Sweden, Paraguay, Morocco,
Norway, Belgium) are held at their frozen pre-tournament elo_current_ratings.csv value --
same deliberate simplification used by every sibling replay script (r16, qf, arg_sui,
nor_eng), applied symmetrically: nor_eng_qf_point_in_time_elo_replay.py held France frozen
(2129.0524) when computing Norway's rating off their group game, so this script returns the
favor and holds Norway frozen here too, rather than pulling nor_eng's own updated Norway
value -- avoids a circular dependency between the two scripts.

Neutral venue: France's entire run was on US soil (MetLife x2, Lincoln Financial, Gillette)
against non-USA/MX/CA opponents, so neutral=True throughout -- venue country alone does not
grant true home advantage, only USA/MX/CA-as-participant does (established convention, see
r16_point_in_time_elo_replay.py). Spain's run (vs Cape Verde/Saudi Arabia/Uruguay/Austria/
Portugal/Belgium) is neutral=True for the same reason.
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


# --- France: fresh replay from pre-tournament baseline ---
FRANCE_BASELINE = 2129.0524
FROZEN_OPP = {
    "Senegal": 1912.8104,
    "Iraq": 1736.5496,
    "Norway": 1983.8379,
    "Sweden": 1775.2510,
    "Paraguay": 1917.7456,
    "Morocco": 1984.8491,
}
FRANCE_GAMES = [
    # (opponent, france_score, opp_score, round)
    ("Senegal", 3, 1, "Group"),
    ("Iraq", 3, 0, "Group"),
    ("Norway", 4, 1, "Group"),
    ("Sweden", 3, 0, "R32"),
    ("Paraguay", 1, 0, "R16"),
    ("Morocco", 2, 0, "QF"),
]

# --- Spain: extend the existing r16 -> qf replay chain with the actual QF result ---
SPAIN_ENTERING_QF = 2248.18  # verbatim from qf_point_in_time_elo_replay.py output
BELGIUM_ENTERING_QF = 2031.57  # verbatim from qf_point_in_time_elo_replay.py output
SPAIN_QF_GAME = ("Belgium", 2, 1)  # Spain 2-1 Belgium, 2026-07-10, neutral

if __name__ == "__main__":
    print("=== France: full replay from pre-tournament baseline ===")
    france_elo = FRANCE_BASELINE
    for opp, fs, os_, rnd in FRANCE_GAMES:
        r_opp = FROZEN_OPP[opp]
        new_elo, w_e = update(france_elo, r_opp, fs, os_, True, False)
        print(f"[{rnd:5s}] France {fs}-{os_} {opp}: {france_elo:.2f} -> {new_elo:.2f} "
              f"({new_elo - france_elo:+.2f}, pre-game W_e={w_e:.3f})")
        france_elo = new_elo

    print()
    print("=== Spain: extending r16/qf replay chain with actual QF result ===")
    spain_elo = SPAIN_ENTERING_QF
    opp, ss, bs = SPAIN_QF_GAME
    new_spain, w_e = update(spain_elo, BELGIUM_ENTERING_QF, ss, bs, True, False)
    print(f"[QF   ] Spain {ss}-{bs} {opp}: {spain_elo:.2f} -> {new_spain:.2f} "
          f"({new_spain - spain_elo:+.2f}, pre-game W_e={w_e:.3f})")
    spain_elo = new_spain

    print()
    print("=== Point-in-time Elo entering the 2026-07-14 SF (correct) ===")
    print(f"France: {france_elo:.2f}")
    print(f"Spain:  {spain_elo:.2f}")
    print(f"Diff (Spain - France): {spain_elo - france_elo:+.2f}")

    print()
    print("=== vs stale pre-tournament-frozen values (what elo_current_ratings.csv / "
          "this match folder's 02_elo_current_ratings.json currently show) ===")
    stale_france, stale_spain = FRANCE_BASELINE, 2225.5610
    print(f"France stale: {stale_france:.2f}  (correct {france_elo:.2f}, delta {france_elo - stale_france:+.2f})")
    print(f"Spain stale:  {stale_spain:.2f}  (correct {spain_elo:.2f}, delta {spain_elo - stale_spain:+.2f})")
    stale_diff = stale_spain - stale_france
    correct_diff = spain_elo - france_elo
    print(f"Stale diff: {stale_diff:+.2f}  Correct diff: {correct_diff:+.2f}  (shift {correct_diff - stale_diff:+.2f})")
