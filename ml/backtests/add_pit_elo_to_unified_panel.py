"""
Adds a genuinely point-in-time Elo-diff feature to the unified team-match
panel (data/processed/unified_team_match_panel_r.csv, 456 rows: 200 WC2026
ESPN rows + 256 WC2018/2022 StatsBomb rows). This is the feature that feeds
design #2's hierarchical GLMM (elo_diff as the opponent-strength covariate).

- WC2026 rows: joined to data/processed/wc2026_pit_elo_panel.csv on
  (event_id, team_code) -- the systematic full-tournament replay built
  2026-07-14 (ml/backtests/build_full_tournament_pit_elo.py), which tracks
  every team's true evolving rating (no frozen opponents).
- WC2018/2022 rows: joined to data/processed/elo_match_panel.csv (built by
  model/elo.py from the full 49k-match results.csv history) on
  (date, team as home_team-or-away_team) -- already legitimately
  point-in-time since real scores exist for all pre-2026 history; only the
  WC2026 portion of that file has the frozen-value bug.

Output: data/processed/unified_team_match_panel_with_pit_elo.csv
        (same 456 rows + elo_pre, elo_diff_pre, neutral_pit columns)

Usage:
    python3 add_pit_elo_to_unified_panel.py
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UNIFIED = ROOT / "data" / "processed" / "unified_team_match_panel_r.csv"
WC2026_ELO = ROOT / "data" / "processed" / "wc2026_pit_elo_panel.csv"
HIST_ELO = ROOT / "data" / "processed" / "elo_match_panel.csv"
OUT = ROOT / "data" / "processed" / "unified_team_match_panel_with_pit_elo.csv"


def load_2026_elo():
    idx = {}
    with open(WC2026_ELO, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            idx[(row["event_id"], row["team_code"])] = row
    return idx


def load_hist_elo():
    """Index by (date, team_name) -> (own_pre, opp_pre, neutral)."""
    idx = {}
    with open(HIST_ELO, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if not row["tournament"] == "FIFA World Cup":
                continue
            if not (row["date"].startswith("2018") or row["date"].startswith("2022")):
                continue
            idx[(row["date"], row["home_team"])] = (
                float(row["elo_home_pre"]), float(row["elo_away_pre"]), row["neutral"] == "TRUE")
            idx[(row["date"], row["away_team"])] = (
                float(row["elo_away_pre"]), float(row["elo_home_pre"]), row["neutral"] == "TRUE")
    return idx


def main():
    elo26 = load_2026_elo()
    elohist = load_hist_elo()

    with open(UNIFIED, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    matched, missing = 0, []
    out_rows = []
    for row in rows:
        elo_pre = elo_diff = neutral_pit = None
        if row["data_source"] == "espn_boxscore":
            key = (row["match_id"], row["team_code"])
            rec = elo26.get(key)
            if rec:
                elo_pre = float(rec["elo_pre"])
                # opponent's own pre-match rating is the OTHER row for the same event
                opp_rec = elo26.get((row["match_id"], row["opponent_code"]))
                if opp_rec:
                    elo_diff = elo_pre - float(opp_rec["elo_pre"])
                neutral_pit = rec["neutral"]
        else:  # statsbomb_event_data, WC2018/2022
            key = (row["match_date"], row["team_name"])
            rec = elohist.get(key)
            if rec:
                elo_pre = rec[0]
                elo_diff = rec[0] - rec[1]
                neutral_pit = str(rec[2])

        if elo_pre is not None:
            matched += 1
        else:
            missing.append((row["data_source"], row["match_date"], row["team_name"]))

        new_row = dict(row)
        new_row["elo_pre"] = elo_pre
        new_row["elo_diff_pre"] = elo_diff
        new_row["neutral_pit"] = neutral_pit
        out_rows.append(new_row)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    print(f"Matched: {matched}/{len(rows)}")
    if missing:
        print(f"Missing ({len(missing)}):")
        for m in missing[:20]:
            print(" ", m)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
