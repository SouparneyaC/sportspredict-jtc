"""
For every market we CAN predict (match_winner, total_goals_under/over,
btts_and_over -- see classify_markets.py), compute our model's probability
using:
  - ordered_logit (data/processed/ordered_logit_coefs.json) for match_winner
  - Poisson means (poisson_goals_coefs.json) + NB-corrected Dixon-Coles grid
    (nb_dispersion_coefs.json) for goal-total markets

Looks up each match's pre-computed Elo ratings / neutral flag from the
already-built 2026 fixtures in data/processed/elo_match_panel.csv (matched
by team pair, not exact date, since API timestamps are UTC and may be off
by a day from the panel's date).

Output: bot/data/predictions_review.csv -- one row per predictable market,
with our suggested 1-99 submission value, for manual review before
submitting via /predictions.

Usage:
    python3 predict_markets.py
"""

import csv
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "model"))

from ordered_logit import predict_probs  # noqa: E402
from dixon_coles import scoreline_grid_nb, total_goals_over_under  # noqa: E402
from classify_markets import classify  # noqa: E402
from team_code_map import TEAM_CODE_MAP  # noqa: E402

PANEL_CSV = ROOT / "data" / "processed" / "elo_match_panel.csv"
OL_COEFS = json.load(open(ROOT / "data" / "processed" / "ordered_logit_coefs.json"))
POISSON_COEFS = json.load(open(ROOT / "data" / "processed" / "poisson_goals_coefs.json"))
NB_COEFS = json.load(open(ROOT / "data" / "processed" / "nb_dispersion_coefs.json"))

MAX_GOALS = 8

# Question-text team names that differ from elo_match_panel spelling
QUESTION_TEAM_ALIASES = {
    "Czechia": "Czech Republic",
    "Türkiye": "Turkey",
}


def panel_team_name(name):
    return QUESTION_TEAM_ALIASES.get(name, name)


def load_future_panel_rows():
    """team-pair (frozenset) -> panel row, for fixtures with no result yet."""
    rows = {}
    with open(PANEL_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["date"] < "2026-06-10":
                continue
            if row["home_score"] != "":
                continue  # already played/settled
            key = frozenset((row["home_team"], row["away_team"]))
            rows[key] = row
    return rows


def goal_lambdas(panel_row):
    b0, b1, b2 = POISSON_COEFS["intercept"], POISSON_COEFS["home_advantage"], POISSON_COEFS["elo_diff_coef"]
    elo_home = float(panel_row["elo_home_pre"])
    elo_away = float(panel_row["elo_away_pre"])
    home_adv = 0.0 if panel_row["neutral"] == "TRUE" else 1.0
    lam_home = math.exp(b0 + b1 * home_adv + b2 * (elo_home - elo_away))
    lam_away = math.exp(b0 + b2 * (elo_away - elo_home))
    return lam_home, lam_away


def to_submission_int(p):
    """Clamp to [1, 99] integer as required by /predictions."""
    return max(1, min(99, round(p * 100)))


def main():
    future_rows = load_future_panel_rows()
    print(f"Loaded {len(future_rows)} upcoming fixtures from elo_match_panel.csv")

    out_rows = []
    n_skipped_no_panel = 0

    with open(ROOT / "bot" / "data" / "markets_raw.jsonl") as f:
        for line in f:
            d = json.loads(line)
            home_code, away_code = [s.strip() for s in d["match_name"].split(" vs ")]
            home_team = TEAM_CODE_MAP[home_code]
            away_team = TEAM_CODE_MAP[away_code]
            panel_row = future_rows.get(frozenset((home_team, away_team)))

            for m in d["markets"]:
                cat, args = classify(m["question"])
                if cat == "no_model":
                    continue
                if panel_row is None:
                    n_skipped_no_panel += 1
                    continue

                if cat == "match_winner":
                    elo_diff = float(panel_row["elo_home_pre"]) - float(panel_row["elo_away_pre"])
                    home_adv = 0.0 if panel_row["neutral"] == "TRUE" else 1.0
                    probs = predict_probs(elo_diff, home_adv, OL_COEFS["b_elo"], OL_COEFS["b_home"],
                                           OL_COEFS["c1"], OL_COEFS["c2"])
                    q_team = panel_team_name(args[0])
                    if q_team == panel_row["home_team"]:
                        p = probs["home_win"]
                    elif q_team == panel_row["away_team"]:
                        p = probs["away_win"]
                    else:
                        n_skipped_no_panel += 1
                        continue
                    method = "ordered_logit"

                elif cat in ("total_goals_under", "total_goals_over", "btts_and_over"):
                    lam_home, lam_away = goal_lambdas(panel_row)
                    grid = scoreline_grid_nb(lam_home, lam_away, NB_COEFS["alpha"],
                                              rho=NB_COEFS["rho_nb"], max_goals=MAX_GOALS)
                    threshold = int(args[0])
                    if cat == "total_goals_under":
                        p = total_goals_over_under(grid, threshold)["under_or_equal"]
                    elif cat == "total_goals_over":
                        # "N or more" = P(total > N-1)
                        p = total_goals_over_under(grid, threshold - 1)["over"]
                    else:  # btts_and_over
                        p = sum(prob for (i, j), prob in grid.items()
                                if i >= 1 and j >= 1 and (i + j) >= threshold)
                    method = "dixon_coles_nb"

                out_rows.append({
                    "match": d["match_name"],
                    "closing_time": d["closing_time"],
                    "category": cat,
                    "question": m["question"],
                    "market_id": m["id"],
                    "our_prob": round(p, 4),
                    "submit_value_1_99": to_submission_int(p),
                    "method": method,
                })

    out_path = ROOT / "bot" / "data" / "predictions_review.csv"
    with open(out_path, "w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=["match", "closing_time", "category", "question",
                                                   "market_id", "our_prob", "submit_value_1_99", "method"])
        writer.writeheader()
        writer.writerows(out_rows)

    print(f"Wrote {len(out_rows)} predictions to {out_path}")
    print(f"Skipped (no panel match / team-name mismatch): {n_skipped_no_panel}")

    by_cat = {}
    for r in out_rows:
        by_cat[r["category"]] = by_cat.get(r["category"], 0) + 1
    print("By category:", by_cat)


if __name__ == "__main__":
    main()
