"""
11_player_prop_backtest_messi_alvarez.py
-----------------------------------------
Data sourcing + walk-forward (no-lookahead) backtest for two WC2026 ENG-ARG SF player
props:
  Q1 -- Julian Alvarez, 1+ shots on target, regulation only (90 min + stoppage)
  Q4 -- Lionel Messi, scores a goal, regulation only (90 min + stoppage)

Methodology matches the ONE validated precedent for this exact question type --
De Bruyne/Lukaku 1+SOT in matches/Spain_vs_Belgium/PRICING_METHODOLOGY.md Q9/Q10:
a k=5 empirical-Bayes shrink of the player's own in-tournament rate toward his
historical StatsBomb (WC2018+WC2022) rate. NOT a fitted regression -- the project's
one fitted-model attempt (topics/player-props/ronaldo_goals_regression.py, n=9)
explicitly failed LOOCV (worse than a train-mean baseline), and RULE5 sets the bar
at n>=10 before trusting any fitted model. Neither player has that much 2026 data
(n=6 own-tournament games each), so this script deliberately reuses the disciplined,
non-fitted EB-shrinkage approach rather than reinventing something fancier.

    pred_i = (n_prior_2026 * rate_2026_prior + k * rate_historical) / (n_prior_2026 + k)

applied strictly walk-forward across Argentina's own 6 WC2026 matches in date order:
rate_2026_prior at fold i uses ONLY 2026 games 1..i-1 (never game i or later).
rate_historical is the fixed pre-tournament StatsBomb rate (already fully "past"
relative to every 2026 fold, so no lookahead there either).

Step 1 data sources:
  - Historical: data/processed/statsbomb_player_match_panel.csv, filtered by exact
    player_name ("Lionel Andrés Messi Cuccittini", "Julián Álvarez").
  - 2026 (this tournament): rosters[].stats field (NOT the `leaders` field -- that
    only surfaces team-level category leaders, the exact mistake documented and
    fixed in matches/Spain_vs_Belgium/PRICING_METHODOLOGY.md Sec 3.5) of the raw
    ESPN event dumps in data/processed/espn_raw_events/:
      760433 Algeria (group), 760456 Austria (group), 760483 Jordan (group),
      760500 Cape Verde (R32, AET), 760509 Egypt (R16), 760513 Switzerland (QF, AET).
    Goal-timing for the two AET matches (Cape Verde R32, Switzerland QF) was
    independently verified against keyEvents clock timestamps to confirm whether
    each goal fell inside regulation (<= "End Regular Time" marker) or in extra
    time -- see notes in the 2026 log dicts below. ESPN has no shot-level (only
    goal-level) clock data, so shots/SOT totals for the two AET matches are
    whole-match totals that may include a small amount of extra-time shot volume
    the boxscore can't separate out; flagged explicitly, not silently ignored.

Step 3 (live number for tonight) uses ALL 6 2026 games + full historical sample --
this is intentionally NOT part of the walk-forward backtest loop (which never sees
game 6 when evaluating fold 6); it's the "final live estimate" computed once, after
the backtest, using the complete data.

Usage: python3 "matches/England Vs Argentina (Jul.15.26)/11_player_prop_backtest_messi_alvarez.py"
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "11_player_prop_backtest_results.json"

K = 5

EVENTS = [
    ("760433", "Algeria", "group"),
    ("760456", "Austria", "group"),
    ("760483", "Jordan", "group"),
    ("760500", "Cape Verde", "R32"),
    ("760509", "Egypt", "R16"),
    ("760513", "Switzerland", "QF"),
]
PLAYERS = {"Julián Álvarez": "alvarez", "Lionel Messi": "messi"}


def get_stat(stats, name):
    for s in stats:
        if s["name"] == name:
            return s["value"]
    return None


def extract_2026_logs():
    """Pull real per-match rosters[].stats for both players across all 6 ARG 2026 games."""
    out = {"alvarez": [], "messi": []}
    for event_id, opponent, stage in EVENTS:
        path = ROOT / "data" / "processed" / "espn_raw_events" / f"espn_event_{event_id}.json"
        d = json.loads(path.read_text())
        date = d.get("header", {}).get("competitions", [{}])[0].get("date")
        for team in d["rosters"]:
            if team.get("team", {}).get("displayName") != "Argentina":
                continue
            for p in team["roster"]:
                name = p.get("athlete", {}).get("displayName", "")
                if name not in PLAYERS:
                    continue
                stats = p["stats"]
                out[PLAYERS[name]].append({
                    "event_id": event_id, "date": date, "opponent": opponent, "stage": stage,
                    "starter": p.get("starter"), "subbed_in": p.get("subbedIn"),
                    "total_shots": get_stat(stats, "totalShots"),
                    "shots_on_target": get_stat(stats, "shotsOnTarget"),
                    "total_goals": get_stat(stats, "totalGoals"),
                    "goal_assists": get_stat(stats, "goalAssists"),
                })
    return out


def historical_rates():
    """WC2018+WC2022 StatsBomb rates, filtered by exact player_name (no join-key shortcuts)."""
    import csv
    path = ROOT / "data" / "processed" / "statsbomb_player_match_panel.csv"
    messi_sot, messi_goals, alvarez_sot = [], [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["player_name"] == "Lionel Andrés Messi Cuccittini":
                messi_sot.append(float(row["shots_on_target"]))
                messi_goals.append(float(row["goals"]))
            elif row["player_name"] == "Julián Álvarez":
                alvarez_sot.append(float(row["shots_on_target"]))
    messi_score_rate = sum(1 for g in messi_goals if g >= 1) / len(messi_goals)
    alvarez_sot_rate = sum(1 for s in alvarez_sot if s >= 1) / len(alvarez_sot)
    return {
        "messi_score_rate": messi_score_rate, "messi_n": len(messi_goals),
        "alvarez_sot_rate": alvarez_sot_rate, "alvarez_n": len(alvarez_sot),
    }


# Regulation-scoped 2026 target series, built from extract_2026_logs() + independent
# keyEvents clock verification for the two AET games (see module docstring).
ALVAREZ_2026_SOT = [
    {"opp": "Algeria", "sot": 0, "note": ""},
    {"opp": "Austria", "sot": 1, "note": ""},
    {"opp": "Jordan", "sot": 1, "note": ""},
    {"opp": "Cape Verde", "sot": 0, "note": "AET match; whole-match total is 0, unambiguous"},
    {"opp": "Egypt", "sot": 1, "note": ""},
    {"opp": "Switzerland", "sot": 1, "note": "AET match; whole-match total incl. his 112' ET goal (a SOT by definition) -- true regulation-only SOT is ambiguous (0 or 1), ESPN has no shot-level clock data"},
]
MESSI_2026_GOAL = [
    {"opp": "Algeria", "goal": 1, "note": ""},
    {"opp": "Austria", "goal": 1, "note": ""},
    {"opp": "Jordan", "goal": 1, "note": ""},
    {"opp": "Cape Verde", "goal": 1, "note": "goal at 29' verified via keyEvents clock, inside regulation (End Regular Time marker was 90'+9')"},
    {"opp": "Egypt", "goal": 1, "note": "goal at 83', regulation, no ET in this match"},
    {"opp": "Switzerland", "goal": 0, "note": "0 goals for the full match incl. ET -- unambiguous, streak broken"},
]


def walk_forward(log, key, hist_rate, k=K):
    rows, prior = [], []
    for g in log:
        n_prior = len(prior)
        rate_prior = (sum(prior) / n_prior) if n_prior else None
        pred = hist_rate if n_prior == 0 else (n_prior * rate_prior + k * hist_rate) / (n_prior + k)
        rows.append({"opponent": g["opp"], "n_prior_2026": n_prior,
                      "rate_2026_prior": round(rate_prior, 4) if rate_prior is not None else None,
                      "pred": round(pred, 4), "actual": g[key], "note": g["note"]})
        prior.append(g[key])
    return rows


def brier(rows):
    return sum((r["pred"] - r["actual"]) ** 2 for r in rows) / len(rows)


def flat_brier(rows, val):
    return sum((val - r["actual"]) ** 2 for r in rows) / len(rows)


def main():
    hist = historical_rates()
    alvarez_rows = walk_forward(ALVAREZ_2026_SOT, "sot", hist["alvarez_sot_rate"])
    messi_rows = walk_forward(MESSI_2026_GOAL, "goal", hist["messi_score_rate"])

    a_model, a_flathist, a_flat50 = brier(alvarez_rows), flat_brier(alvarez_rows, hist["alvarez_sot_rate"]), flat_brier(alvarez_rows, 0.5)
    m_model, m_flathist, m_flat50 = brier(messi_rows), flat_brier(messi_rows, hist["messi_score_rate"]), flat_brier(messi_rows, 0.5)

    a_n2026, a_rate2026 = len(ALVAREZ_2026_SOT), sum(g["sot"] for g in ALVAREZ_2026_SOT) / len(ALVAREZ_2026_SOT)
    a_live = (a_n2026 * a_rate2026 + K * hist["alvarez_sot_rate"]) / (a_n2026 + K)
    m_n2026, m_rate2026 = len(MESSI_2026_GOAL), sum(g["goal"] for g in MESSI_2026_GOAL) / len(MESSI_2026_GOAL)
    m_live = (m_n2026 * m_rate2026 + K * hist["messi_score_rate"]) / (m_n2026 + K)

    result = {
        "historical_rates": hist,
        "walk_forward": {"alvarez_1plus_sot": alvarez_rows, "messi_scores": messi_rows},
        "brier": {
            "alvarez": {"model": a_model, "flat_historical_baseline": a_flathist, "flat_0.5_baseline": a_flat50},
            "messi": {"model": m_model, "flat_historical_baseline": m_flathist, "flat_0.5_baseline": m_flat50},
        },
        "live_tonight": {
            "alvarez_q1_p_1plus_sot": round(a_live, 4),
            "messi_q4_p_scores": round(m_live, 4),
        },
    }
    OUT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
