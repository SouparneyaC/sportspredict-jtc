"""
Systematic point-in-time Elo builder for the ENTIRE WC2026 tournament,
superseding the piecemeal per-matchup replay scripts (r16_..., qf_...,
arg_sui_qf_..., nor_eng_qf_..., fra_esp_sf_...). Those scripts each hand-built
a replay for a handful of teams headed into one specific match, holding every
opponent outside that set at its frozen pre-tournament baseline. That's fine
for pricing one upcoming match, but it is NOT good enough for training a
model across the whole tournament: every team's rating needs to be genuinely
point-in-time at every match it played, not just the ones a human happened to
replay by hand.

Same formula as model/elo.py (K=60 FIFA World Cup, margin-of-victory G-factor,
+100 home advantage), same neutral-venue convention established across every
prior replay script and validated directly against data/international_results
/results.csv's own neutral column for the 9 USA/MEX/CAN group-stage rows that
still have it populated: true home advantage (+100) applies ONLY when the
United States, Mexico, or Canada is a participant -- venue city alone (e.g. a
Brazil-Morocco game played in New Jersey) does NOT grant it.

Input:  data/processed/espn_match_panel.csv (100 matches post-2026-07-14
        rebuild, 2 rows/match -- see build_espn_panel.py)
        data/processed/elo_current_ratings.csv (pre-tournament baseline for
        all teams; the ONLY legitimate use of this frozen file left in the
        project -- as a t=0 starting point, never as an in-tournament value)
Output: data/processed/wc2026_pit_elo_panel.csv
        One row per team per match: elo_pre (before this match, the only
        value ever safe to use as a feature for THIS match), elo_post
        (after -- safe for any LATER match, never this one or an earlier one).

Cross-check: this script's FRA/ESP output entering the 2026-07-14 SF should
reproduce ml/backtests/fra_esp_sf_point_in_time_elo_replay.py's hand-built
numbers (France 2225.13, Spain 2261.57) to confirm both builds agree.

Usage:
    python3 build_full_tournament_pit_elo.py
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ESPN_PANEL = ROOT / "data" / "processed" / "espn_match_panel.csv"
BASELINE_CSV = ROOT / "data" / "processed" / "elo_current_ratings.csv"
OUT = ROOT / "data" / "processed" / "wc2026_pit_elo_panel.csv"

K = 60
HOME_ADVANTAGE = 100.0
HOST_NATIONS = {"USA", "MEX", "CAN"}

CODE_TO_NAME = {
    "ALG": "Algeria", "ARG": "Argentina", "AUS": "Australia", "AUT": "Austria",
    "BEL": "Belgium", "BIH": "Bosnia and Herzegovina", "BRA": "Brazil",
    "CAN": "Canada", "CDR": "DR Congo", "CIV": "Ivory Coast", "COL": "Colombia",
    "CPV": "Cape Verde", "CRO": "Croatia", "CUR": "Curaçao", "CZE": "Czech Republic",
    "ECU": "Ecuador", "EGY": "Egypt", "ENG": "England", "ESP": "Spain",
    "FRA": "France", "GER": "Germany", "GHA": "Ghana", "HAI": "Haiti",
    "IRN": "Iran", "IRQ": "Iraq", "JOR": "Jordan", "JPN": "Japan",
    "KOR": "South Korea", "KSA": "Saudi Arabia", "SAU": "Saudi Arabia",
    "MAR": "Morocco", "MEX": "Mexico", "NED": "Netherlands", "NOR": "Norway",
    "NZL": "New Zealand", "PAN": "Panama", "PAR": "Paraguay", "POR": "Portugal",
    "QAT": "Qatar", "RSA": "South Africa", "SCO": "Scotland", "SEN": "Senegal",
    "SUI": "Switzerland", "SWE": "Sweden", "TUN": "Tunisia", "TUR": "Turkey",
    "URU": "Uruguay", "USA": "United States", "UZB": "Uzbekistan",
}


def g_factor(goal_diff):
    ad = abs(goal_diff)
    if ad <= 1:
        return 1.0
    if ad == 2:
        return 1.5
    return (11 + ad) / 8.0


def expected_result(rating_diff):
    return 1.0 / (10 ** (-rating_diff / 400.0) + 1.0)


def load_baselines():
    ratings = {}
    with open(BASELINE_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ratings[row["team"]] = float(row["elo_rating"])
    return ratings


def load_matches():
    """Dedupe the 2-rows-per-match ESPN panel into one row per match,
    chronologically ordered, with both teams' scores."""
    by_event = {}
    with open(ESPN_PANEL, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            eid = row["event_id"]
            by_event.setdefault(eid, {})[row["team_code"]] = row
    matches = []
    for eid, teams in by_event.items():
        codes = list(teams.keys())
        if len(codes) != 2:
            print(f"  [WARN] event {eid} has {len(codes)} team rows, skipping")
            continue
        a, b = codes
        ra, rb = teams[a], teams[b]
        matches.append({
            "event_id": eid, "date": ra["date"],
            "team_a": a, "team_b": b,
            "score_a": int(ra["goals"]), "score_b": int(rb["goals"]),
        })
    matches.sort(key=lambda m: (m["date"], m["event_id"]))
    return matches


def main():
    ratings = load_baselines()
    matches = load_matches()
    print(f"Loaded {len(matches)} unique WC2026 matches, "
          f"{len(set(m['team_a'] for m in matches) | set(m['team_b'] for m in matches))} teams")

    missing = set()
    rows = []
    for m in matches:
        na, nb = CODE_TO_NAME.get(m["team_a"]), CODE_TO_NAME.get(m["team_b"])
        for code, name in [(m["team_a"], na), (m["team_b"], nb)]:
            if name is None:
                missing.add(code)
                continue
            if name not in ratings:
                ratings[name] = 1500.0  # true Elo bootstrap default, per model/elo.py
                missing.add(f"{code}({name}) -- no baseline, bootstrapped at 1500")

        if na is None or nb is None:
            continue  # can't process without a name mapping

        ra_pre, rb_pre = ratings[na], ratings[nb]
        a_is_host = m["team_a"] in HOST_NATIONS
        b_is_host = m["team_b"] in HOST_NATIONS
        neutral = not (a_is_host != b_is_host)  # neutral unless exactly one side is a host nation
        home_adv_a = HOME_ADVANTAGE if (not neutral and a_is_host) else 0.0
        home_adv_b = HOME_ADVANTAGE if (not neutral and b_is_host) else 0.0

        sa, sb = m["score_a"], m["score_b"]
        w_a = 1.0 if sa > sb else (0.5 if sa == sb else 0.0)
        w_b = 1.0 - w_a
        we_a = expected_result((ra_pre - rb_pre) + home_adv_a - home_adv_b)
        we_b = 1.0 - we_a
        gd = sa - sb
        gf = g_factor(gd)

        ra_post = ra_pre + K * gf * (w_a - we_a)
        rb_post = rb_pre + K * gf * (w_b - we_b)
        ratings[na], ratings[nb] = ra_post, rb_post

        for code, name, pre, post, is_home_adv, opp_code, opp_name, own_score, opp_score in [
            (m["team_a"], na, ra_pre, ra_post, home_adv_a > 0, m["team_b"], nb, sa, sb),
            (m["team_b"], nb, rb_pre, rb_post, home_adv_b > 0, m["team_a"], na, sb, sa),
        ]:
            rows.append({
                "date": m["date"], "event_id": m["event_id"],
                "team_code": code, "team_name": name,
                "opponent_code": opp_code, "opponent_name": opp_name,
                "goals": own_score, "opponent_goals": opp_score,
                "neutral": neutral, "true_home_advantage": is_home_adv,
                "elo_pre": round(pre, 4), "elo_post": round(post, 4),
            })

    if missing:
        print(f"  [WARN] {len(missing)} code/name issues: {sorted(missing)}")

    rows.sort(key=lambda r: (r["date"], r["event_id"], r["team_code"]))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows ({len(matches)} matches) to {OUT}")

    print("\n=== Final ratings entering the semifinals (cross-check) ===")
    for team in ["France", "Spain", "England", "Argentina", "Norway", "Switzerland"]:
        if team in ratings:
            print(f"  {team:20s} {ratings[team]:.2f}")

    print("\n=== Cross-check vs hand-built fra_esp_sf_point_in_time_elo_replay.py ===")
    print(f"  France: this script={ratings.get('France'):.2f}  hand-built=2225.13")
    print(f"  Spain:  this script={ratings.get('Spain'):.2f}  hand-built=2261.57")


if __name__ == "__main__":
    main()
