"""
statsbomb_baserate_test.py
---------------------------
Diagnostic: does a base-rate model built purely from Portugal's and Croatia's
historical WC2018+2022 StatsBomb data beat (or match) what we actually
submitted for the real Portugal vs Croatia match (WC2026 R32, 2026-07-02,
final score 2-1 Portugal, actual result +130.08 RBP, 10/15 beat crowd)?

Inputs (read-only):
  data/processed/statsbomb_team_match_panel.csv
  data/processed/statsbomb_player_match_panel.csv
  data/external/statsbomb/open-data/data/events/*.json (for header-goal,
    half-time-score, and penalty-awarded stats not present in the flattened
    panel — these need event-level period/body_part detail)
  matches/Portugal_vs_Croatia/05_estimates.json (our actual submissions)
  matches/Portugal_vs_Croatia/06_post_match_results.json (actual outcomes)

Output: ml/statsbomb_baserate_results.json + printed comparison table.

Methodology:
- Team rate stats (SOT, shots, cards, corners) come straight from the team
  panel, shrunk toward the 256-row tournament-wide mean using empirical-Bayes
  pooling: lambda_shrunk = (n*team_mean + k*global_mean) / (n+k), k=5 pseudo-
  matches (matches this project's existing "n<10, blend with prior" rule).
- Poisson is used for count thresholds (assuming home/away independence,
  same simplifying assumption the existing Poisson/Dixon-Coles pipeline uses).
- Player stats (goals, SOT, assists) are shrunk the same way against the
  position-relevant player-level global mean is skipped here (too few
  comparable players); instead shrunk toward a fixed weak prior since these
  are rate-of-rare-events (goals/assists) — k=3 pseudo-matches.
- Header goals, HT-tied, and penalty-or-red are empirical tournament-wide
  rates (not team-specific — 9-14 match team samples are too thin to split
  further for genuinely rare events), computed directly from raw event JSON
  read-only.
- "Advance to R16" is explicitly OUT OF SCOPE for this model — it depends on
  group standings/other results, not on Portugal or Croatia's own StatsBomb
  history, so it's excluded from the comparison rather than faked.
"""

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEAM_PANEL = ROOT / "data" / "processed" / "statsbomb_team_match_panel.csv"
PLAYER_PANEL = ROOT / "data" / "processed" / "statsbomb_player_match_panel.csv"
SB_EVENTS = ROOT / "data" / "external" / "statsbomb" / "open-data" / "data" / "events"
MATCH_DIR = ROOT / "matches" / "Portugal_vs_Croatia"
OUT = ROOT / "ml" / "statsbomb_baserate_results.json"


def poisson_pmf(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def poisson_ge(threshold, lam):
    return 1 - sum(poisson_pmf(k, lam) for k in range(threshold))


def shrink(team_mean, n, global_mean, k=5):
    return (n * team_mean + k * global_mean) / (n + k)


def load_team_rates():
    with open(TEAM_PANEL) as f:
        rows = list(csv.DictReader(f))

    def col(r, name):
        return float(r[name]) if r[name] not in (None, "") else 0.0

    stats = ["shots_on_target", "total_shots", "corners", "fouls_committed", "goals"]
    global_mean = {s: sum(col(r, s) for r in rows) / len(rows) for s in stats}
    global_mean["cards"] = sum(col(r, "yellow_cards") + col(r, "red_cards") for r in rows) / len(rows)

    def team_rates(team_name):
        trows = [r for r in rows if r["team_name"] == team_name]
        n = len(trows)
        out = {}
        for s in stats:
            team_mean = sum(col(r, s) for r in trows) / n
            out[s] = shrink(team_mean, n, global_mean[s])
        team_cards_mean = sum(col(r, "yellow_cards") + col(r, "red_cards") for r in trows) / n
        out["cards"] = shrink(team_cards_mean, n, global_mean["cards"])
        out["n_matches"] = n
        return out

    return team_rates("Portugal"), team_rates("Croatia"), global_mean


def load_player_rate(full_name, event_col, n_pseudo=3, weak_prior=0.15):
    with open(PLAYER_PANEL) as f:
        rows = [r for r in csv.DictReader(f) if r["player_name"] == full_name]
    n = len(rows)
    if n == 0:
        return None, 0
    per_match = [float(r[event_col]) if event_col != "score_or_assist" else
                 (1.0 if (int(r["goals"]) > 0 or int(r["assists"]) > 0) else 0.0)
                 for r in rows]
    mean = sum(per_match) / n
    shrunk = (n * mean + n_pseudo * weak_prior) / (n + n_pseudo)
    return shrunk, n


def scan_raw_events_for_derived_stats():
    """Header goals, HT-tied, penalty-or-red — computed directly from raw
    StatsBomb event JSON since the flattened team panel doesn't carry
    body_part or period-level splits."""
    matches_dir = ROOT / "data" / "external" / "statsbomb" / "open-data" / "data" / "matches"
    match_ids = []
    for comp_season in [("43", "3"), ("43", "106")]:
        path = matches_dir / comp_season[0] / f"{comp_season[1]}.json"
        for m in json.loads(path.read_text()):
            match_ids.append(m["match_id"])

    n = len(match_ids)
    header_goal_matches = 0
    ht_tied_matches = 0
    pen_or_red_matches = 0

    for mid in match_ids:
        events = json.loads((SB_EVENTS / f"{mid}.json").read_text())
        events = [e for e in events if e.get("period", 1) != 5]

        has_header_goal = False
        pen_awarded = False
        red_shown = False
        ht_goals = {}

        for e in events:
            etype = e["type"]["name"]
            team_id = e.get("team", {}).get("id")
            if etype == "Shot":
                shot = e["shot"]
                if shot["outcome"]["name"] == "Goal":
                    if e["period"] == 1:
                        ht_goals[team_id] = ht_goals.get(team_id, 0) + 1
                    bp = shot.get("body_part", {}).get("name")
                    if bp == "Head":
                        has_header_goal = True
                    if shot.get("type", {}).get("name") == "Penalty":
                        pen_awarded = True
                elif e["period"] == 1:
                    ht_goals.setdefault(team_id, ht_goals.get(team_id, 0))
                if shot.get("type", {}).get("name") == "Penalty":
                    pen_awarded = True
            elif etype == "Own Goal For" and e["period"] == 1:
                ht_goals[team_id] = ht_goals.get(team_id, 0) + 1
            elif etype == "Foul Committed":
                fc = e.get("foul_committed", {})
                if fc.get("penalty"):
                    pen_awarded = True
                card = fc.get("card", {}).get("name")
                if card in ("Red Card", "Second Yellow"):
                    red_shown = True
            elif etype == "Bad Behaviour":
                card = e.get("bad_behaviour", {}).get("card", {}).get("name")
                if card in ("Red Card", "Second Yellow"):
                    red_shown = True

        if has_header_goal:
            header_goal_matches += 1
        if pen_awarded or red_shown:
            pen_or_red_matches += 1
        vals = list(ht_goals.values())
        # tied at HT also covers the (common) 0-0 case for teams with no event above
        teams_in_match = {e.get("team", {}).get("id") for e in events if e.get("team")}
        for tid in teams_in_match:
            ht_goals.setdefault(tid, 0)
        if len(set(ht_goals.values())) == 1:
            ht_tied_matches += 1

    return {
        "n_matches": n,
        "p_header_goal": header_goal_matches / n,
        "p_ht_tied": ht_tied_matches / n,
        "p_pen_or_red": pen_or_red_matches / n,
    }


def main():
    por, cro, global_mean = load_team_rates()
    print(f"Portugal (n={por['n_matches']} historical matches): {por}")
    print(f"Croatia  (n={cro['n_matches']} historical matches): {cro}")
    print(f"Tournament-wide means: {global_mean}\n")

    print("Scanning raw events for header goals / HT-tied / penalty-or-red (128 matches)...")
    derived = scan_raw_events_for_derived_stats()
    print(derived, "\n")

    ronaldo_goal, n_ron = load_player_rate("Cristiano Ronaldo dos Santos Aveiro", "goals", n_pseudo=3, weak_prior=0.35)
    # SOT-threshold stats need manual per-row computation (not a simple column):
    with open(PLAYER_PANEL) as f:
        rows = [r for r in csv.DictReader(f) if r["player_name"] == "Bruno Miguel Borges Fernandes"]
    n_bruno = len(rows)
    bruno_mean = sum(1.0 if int(r["shots_on_target"]) >= 2 else 0.0 for r in rows) / n_bruno if n_bruno else 0
    bruno_2plus_sot = (n_bruno * bruno_mean + 3 * 0.25) / (n_bruno + 3) if n_bruno else 0.25

    modric_score_assist, n_modric = load_player_rate("Luka Modrić", "score_or_assist", n_pseudo=3, weak_prior=0.30)
    with open(PLAYER_PANEL) as f:
        rows = [r for r in csv.DictReader(f) if r["player_name"] == "Bernardo Mota Veiga de Carvalho e Silva"]
    n_bsilva = len(rows)
    bsilva_mean = sum(1.0 if int(r["shots_on_target"]) >= 1 else 0.0 for r in rows) / n_bsilva if n_bsilva else 0
    bsilva_1plus_sot = (n_bsilva * bsilva_mean + 3 * 0.40) / (n_bsilva + 3) if n_bsilva else 0.40

    print(f"Ronaldo goal rate (n={n_ron}): {ronaldo_goal:.3f}")
    print(f"Bruno 2+ SOT rate (n={n_bruno}): {bruno_2plus_sot:.3f}")
    print(f"Modric score-or-assist rate (n={n_modric}): {modric_score_assist:.3f}")
    print(f"Bernardo Silva 1+ SOT rate (n={n_bsilva}): {bsilva_1plus_sot:.3f}\n")

    lam_cro_sot = cro["shots_on_target"]
    lam_por_sot = por["shots_on_target"]
    lam_total_shots = por["total_shots"] + cro["total_shots"]
    lam_total_cards = por["cards"] + cro["cards"]
    p_por_card = 1 - math.exp(-por["cards"])
    p_cro_card = 1 - math.exp(-cro["cards"])
    p_both_card = p_por_card * p_cro_card

    lam_total_goals = por["goals"] + cro["goals"]
    p_le_2_goals = sum(poisson_pmf(k, lam_total_goals) for k in range(3))

    model_estimates = {
        "Will Cristiano Ronaldo (Portugal) score a goal?": round(ronaldo_goal, 3),
        "Will the match have 2 or fewer total goals?": round(p_le_2_goals, 3),
        "Will Bruno Fernandes (Portugal) have 2 or more shots on target?": round(bruno_2plus_sot, 3),
        "Will Luka Modrić (Croatia) score or assist a goal?": round(modric_score_assist, 3),
        "Will Croatia have 4 or more shots on target?": round(poisson_ge(4, lam_cro_sot), 3),
        "Will there be 4 or more total cards shown?": round(poisson_ge(4, lam_total_cards), 3),
        "Will both teams receive at least one card?": round(p_both_card, 3),
        "Will Portugal have 6 or more corner kicks?": round(poisson_ge(6, por["corners"]), 3),
        "Will the match be tied at halftime?": round(derived["p_ht_tied"], 3),
        "Will Portugal have 6 or more shots on target?": round(poisson_ge(6, lam_por_sot), 3),
        "Will Bernardo Silva (Portugal) have 1 or more shots on target?": round(bsilva_1plus_sot, 3),
        "Will a header goal be scored?": round(derived["p_header_goal"], 3),
        "Will there be 20 or more total shots?": round(poisson_ge(20, lam_total_shots), 3),
        "Will a penalty kick be awarded OR a red card be shown?": round(derived["p_pen_or_red"], 3),
    }

    actual = json.loads((MATCH_DIR / "06_post_match_results.json").read_text())
    outcome_map = {q["text"]: q for q in actual["question_results"]}

    S = 101.3  # RBP per unit of Brier improvement, fit in ml/meta_model_results.json

    print(f"{'Question':<62} {'Model':>6} {'Ours':>6} {'Crowd':>6} {'Outcome':>8} {'OurRBP':>8} {'ModelRBP*':>10}")
    results = []
    for qtext, model_p in model_estimates.items():
        if qtext not in outcome_map:
            continue
        actual_row = outcome_map[qtext]
        outcome = 1 if actual_row["outcome"] == "YES" else 0
        our_est = actual_row["our_estimate"]
        crowd_est = actual_row["crowd_estimate"]
        our_rbp = actual_row["rbp"]
        our_brier = (our_est - outcome) ** 2
        crowd_brier = (crowd_est - outcome) ** 2
        model_brier = (model_p - outcome) ** 2
        model_rbp_equiv = (crowd_brier - model_brier) * S
        results.append({
            "question": qtext, "model_estimate": model_p, "our_estimate": our_est,
            "crowd_estimate": crowd_est, "outcome": actual_row["outcome"],
            "our_rbp": our_rbp, "model_rbp_equiv": round(model_rbp_equiv, 2),
            "model_better_than_us": model_rbp_equiv > our_rbp,
        })
        print(f"{qtext[:60]:<62} {model_p:>6.2f} {our_est:>6.2f} {crowd_est:>6.2f} {actual_row['outcome']:>8} {our_rbp:>8.2f} {model_rbp_equiv:>10.2f}")

    n_model_better = sum(1 for r in results if r["model_better_than_us"])
    total_our_rbp = sum(r["our_rbp"] for r in results)
    total_model_rbp = sum(r["model_rbp_equiv"] for r in results)
    print(f"\nOn these {len(results)} StatsBomb-answerable questions:")
    print(f"  Our actual RBP:        {total_our_rbp:.2f}")
    print(f"  Model-implied RBP:     {total_model_rbp:.2f}")
    print(f"  Model beats us on:     {n_model_better}/{len(results)} questions")

    OUT.write_text(json.dumps({
        "portugal_rates": por, "croatia_rates": cro, "global_mean": global_mean,
        "derived_empirical": derived, "results": results,
        "total_our_rbp": total_our_rbp, "total_model_rbp_equiv": total_model_rbp,
    }, indent=2))
    print(f"\nWritten: {OUT}")


if __name__ == "__main__":
    main()
