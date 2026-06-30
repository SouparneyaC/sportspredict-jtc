"""
Stage 1: compute point-in-time (PIT) Elo ratings for every national team
from martj42's full match history, using the published World Football
Elo Ratings formula:

    R_new = R_old + K * G * (W - We)

    K  = match-importance weight (60/50/40/30/20), from
         data/processed/tournament_kfactor_map.csv
    G  = goal-difference multiplier
           1                        if |goal diff| <= 1
           1.5                      if |goal diff| == 2
           (11 + |goal diff|) / 8   if |goal diff| >= 3
    W  = match result for the home team (1 win, 0.5 draw, 0 loss)
    We = expected result = 1 / (10^(-dr/400) + 1)
    dr = (R_home - R_away) + 100   if neutral == FALSE  (home advantage)
       = (R_home - R_away)         if neutral == TRUE

This is a fixed, deterministic formula -- nothing is "fit" here. Each
team's rating at date T depends only on matches strictly before T, so
the resulting series is point-in-time by construction (no lookahead),
which is the whole reason we're computing this ourselves instead of
scraping eloratings.net (research_notes.md S9.2/S9.4).

Inputs:
  data/international_results/results.csv   (martj42)
  data/processed/tournament_kfactor_map.csv (built earlier)

Outputs:
  data/processed/elo_match_panel.csv
      One row per match (including future NA-score fixtures), with
      each team's Elo rating *before* the match. This is the training
      panel for poisson_goals.py (Stage 2).

  data/processed/elo_current_ratings.csv
      Each team's Elo rating as of the most recent match in the
      dataset -- used by predict.py to price upcoming fixtures.

INITIAL_RATING is a free parameter: no official record of every team's
1872 starting rating survives, and the World Football Elo system itself
was bootstrapped with assumed starting values. Default 1500. For teams
with 50+ years of history this barely matters by 2026; for teams that
entered international football recently it matters more. Validate the
output against data/soccer-elo/csv/ranking_soccer_1901-2023.csv (the
official eloratings.net annual snapshots) before trusting absolute
levels -- relative ordering/differences are what the Poisson model
actually uses, so small absolute offsets matter less than getting the
*shape* of the K/G/We formula right.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_CSV = ROOT / "data" / "international_results" / "results.csv"
KFACTOR_CSV = ROOT / "data" / "processed" / "tournament_kfactor_map.csv"
PANEL_OUT = ROOT / "data" / "processed" / "elo_match_panel.csv"
RATINGS_OUT = ROOT / "data" / "processed" / "elo_current_ratings.csv"

INITIAL_RATING = 1500.0
HOME_ADVANTAGE = 100.0
DEFAULT_K = 30  # fallback for any tournament name not in the map


def load_kfactors():
    kmap = {}
    with open(KFACTOR_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            kmap[row["tournament"]] = int(row["k_factor"])
    return kmap


def goal_diff_multiplier(diff):
    diff = abs(diff)
    if diff <= 1:
        return 1.0
    if diff == 2:
        return 1.5
    return (11 + diff) / 8.0


def expected_result(rating_diff):
    return 1.0 / (10 ** (-rating_diff / 400.0) + 1.0)


def main():
    kmap = load_kfactors()
    ratings = {}  # team -> current Elo rating

    with open(RESULTS_CSV, newline="", encoding="utf-8") as f_in:
        rows = sorted(csv.DictReader(f_in), key=lambda r: r["date"])

    with open(PANEL_OUT, "w", newline="", encoding="utf-8") as f_out:
        writer = csv.writer(f_out)
        writer.writerow([
            "date", "home_team", "away_team", "home_score", "away_score",
            "tournament", "neutral", "k_factor",
            "elo_home_pre", "elo_away_pre",
        ])

        for row in rows:
            home, away = row["home_team"], row["away_team"]
            ratings.setdefault(home, INITIAL_RATING)
            ratings.setdefault(away, INITIAL_RATING)

            elo_home_pre = ratings[home]
            elo_away_pre = ratings[away]

            hs, as_ = row["home_score"], row["away_score"]
            if hs == "NA" or as_ == "NA":
                # future fixture: record PIT ratings for prediction, no update
                writer.writerow([
                    row["date"], home, away, "", "",
                    row["tournament"], row["neutral"], "",
                    f"{elo_home_pre:.4f}", f"{elo_away_pre:.4f}",
                ])
                continue

            hs, as_ = int(hs), int(as_)
            k = kmap.get(row["tournament"], DEFAULT_K)
            neutral = row["neutral"] == "TRUE"

            if hs > as_:
                w_home = 1.0
            elif hs == as_:
                w_home = 0.5
            else:
                w_home = 0.0

            home_adv = 0.0 if neutral else HOME_ADVANTAGE
            dr = (elo_home_pre - elo_away_pre) + home_adv
            we_home = expected_result(dr)
            g = goal_diff_multiplier(hs - as_)

            delta = k * g * (w_home - we_home)
            ratings[home] = elo_home_pre + delta
            ratings[away] = elo_away_pre - delta

            writer.writerow([
                row["date"], home, away, hs, as_,
                row["tournament"], row["neutral"], k,
                f"{elo_home_pre:.4f}", f"{elo_away_pre:.4f}",
            ])

    with open(RATINGS_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["team", "elo_rating"])
        for team, r in sorted(ratings.items(), key=lambda x: -x[1]):
            writer.writerow([team, f"{r:.4f}"])

    print(f"Wrote {PANEL_OUT}")
    print(f"Wrote {RATINGS_OUT} ({len(ratings)} teams)")


if __name__ == "__main__":
    main()
