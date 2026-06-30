"""
Pull open "probability event" markets from play.sportspredict.com (Jump
Trading Probability Cup / World Soccer 2026, both built on the 2026 FIFA
World Cup) and write a categorized overview to disk.

API discovered via the front-end JS bundle (api.sportspredict.com, NestJS +
Swagger, public/unauthenticated for these GET endpoints):
  GET /api/events/active                  -> list of active events
  GET /api/events/{eventId}/markets        -> list of markets for an event

Outputs:
  data/processed/<event-slug>_markets_raw.json   (raw API responses, written
                                                   immediately on fetch)
  data/processed/betting_markets_overview.md     (categorized report +
                                                   data-coverage assessment)

Re-run this script any time to refresh the snapshot (each run overwrites the
raw JSON + MD with the latest open markets / odds).
"""

import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

API = "https://api.sportspredict.com/api"
OUT_DIR = Path(__file__).resolve().parent

# Football events of interest (id, human label, output slug)
FOOTBALL_EVENTS = [
    ("aa5572ec-5930-4d99-b06b-f8966333d172", "Jump Trading Probability Cup", "jumpcup"),
]


def fetch_json(path: str):
    result = subprocess.run(
        ["curl", "-s", f"{API}{path}", "-H", "Accept: application/json"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


# Category -> (matcher, our current data-coverage verdict, note)
CATEGORY_RULES = [
    ("Match result (1X2 / win)", lambda ql: "win the match" in ql,
     "YES", "Elo-based bivariate Poisson / DC97 scoreline model -> P(home win/draw/away win)."),
    ("Team scores first", lambda ql: "score first" in ql,
     "YES (extended model)", "Model goals as independent in-match Poisson processes; "
     "P(team scores first) ~ lambda_team / (lambda_home+lambda_away). Needs no new data."),
    ("Goals / BTTS / Over-Under (full match)", lambda ql: (
        ("total goals" in ql and "half" not in ql) or
        ("score" in ql and "or more total goals" in ql) or
        ("both teams score" in ql and "half" not in ql) or
        ("score at least" in ql and "goal" in ql and "excluding own goals" not in ql)),
     "YES", "Full-time scoreline distribution from Poisson model -> totals, BTTS, team totals "
            "(team-level 'score at least N goals' = 1 - P(team scores 0...N-1))."),
    ("Half-time / second-half splits & in-game timing", lambda ql: "half" in ql,
     "NO (data gap)", "martj42 has no half-time scores or goal-minute data -> can't condition on "
     "in-match state without a new data source."),
    ("Anytime goalscorer (player)", lambda ql: (
        "score at least 0.5 goals" in ql or "excluding own goals" in ql),
     "NO (data gap)", "Requires player-level historical scoring rates / squad lists -> not in martj42."),
    ("Shots (player/team)", lambda ql: "shot" in ql,
     "NO (data gap)", "No shot data in martj42 (goals + shootouts only)."),
    ("Cards (yellow/red)", lambda ql: "card" in ql,
     "NO (data gap)", "No disciplinary data in martj42."),
    ("Fouls", lambda ql: "foul" in ql,
     "NO (data gap)", "No match-event stats in martj42."),
    ("Offsides", lambda ql: "offside" in ql,
     "NO (data gap)", "No match-event stats in martj42."),
    ("Corners", lambda ql: "corner" in ql,
     "NO (data gap)", "No match-event stats in martj42."),
    ("Assists", lambda ql: "assist" in ql,
     "NO (data gap)", "Player-level data not in martj42."),
    ("Penalty awarded", lambda ql: "penalty" in ql,
     "NO (data gap)", "No match-event stats in martj42."),
]


def categorize(question: str):
    ql = question.lower()
    for label, matcher, coverage, note in CATEGORY_RULES:
        if matcher(ql):
            return label, coverage, note
    return "Other / misc", "REVIEW", "Doesn't match a known pattern - inspect manually."


def main():
    lines = []
    lines.append("# Sports Predict - 2026 World Cup probability markets\n")
    lines.append("Source: `api.sportspredict.com` (public GET endpoints, no auth, no QK quota used).\n")
    lines.append("Re-generate with `python3 fetch_betting_markets.py`.\n")

    for event_id, label, slug in FOOTBALL_EVENTS:
        event = fetch_json(f"/events/{event_id}")
        markets = fetch_json(f"/events/{event_id}/markets")

        # write raw immediately
        raw_path = OUT_DIR / f"{slug}_markets_raw.json"
        with open(raw_path, "w") as f:
            json.dump(markets, f, indent=2)

        lines.append(f"## {label}")
        lines.append(f"- Event ID: `{event_id}`")
        lines.append(f"- Window: {event['start_date']} -> {event['end_date']}")
        lines.append(f"- Total open markets: {len(markets)}")
        lines.append(f"- Distinct matches covered: {len(set(m['match_name'] for m in markets))}")
        lines.append(f"- Raw snapshot: `{raw_path.name}`\n")

        cat_counts = Counter()
        cat_examples = defaultdict(list)
        cat_coverage = {}
        cat_note = {}
        for m in markets:
            label_cat, coverage, note = categorize(m["question"])
            cat_counts[label_cat] += 1
            cat_coverage[label_cat] = coverage
            cat_note[label_cat] = note
            if len(cat_examples[label_cat]) < 3:
                closing = m["closing_date"]
                cat_examples[label_cat].append(f"{m['match_name']}: \"{m['question']}\" (closes {closing})")

        lines.append("| Category | # markets | Our data coverage | Notes |")
        lines.append("|---|---:|---|---|")
        for cat, n in cat_counts.most_common():
            lines.append(f"| {cat} | {n} | {cat_coverage[cat]} | {cat_note[cat]} |")
        lines.append("")

        lines.append("<details><summary>Examples per category</summary>\n")
        for cat, _ in cat_counts.most_common():
            lines.append(f"**{cat}**")
            for ex in cat_examples[cat]:
                lines.append(f"- {ex}")
            lines.append("")
        lines.append("</details>\n")

    # Recommendations section
    lines.append("## Recommendation: which markets to target first\n")
    lines.append("Based on current data coverage (martj42 results + computed PIT Elo, "
                  "see `tournament_kfactor_map.csv`):\n")
    lines.append("1. **Match result (1X2 / win)** - directly buildable now from the Elo + "
                  "bivariate Poisson / ordered-logit pipeline (research_notes.md build order). "
                  "Highest confidence, highest market count.")
    lines.append("2. **Full-match goal totals & BTTS** (incl. team-level 'score at least N goals') "
                  "- same Poisson scoreline model gives the full distribution over "
                  "(home_goals, away_goals); totals/BTTS/team-totals are derived quantities, "
                  "no extra data needed.")
    lines.append("")
    lines.append("**Not recommended yet** (would need new data sources before we could do better "
                  "than a coin flip): half-time/second-half splits, anytime goalscorer, shots, "
                  "cards, fouls, offsides, corners, assists, penalties. These all require "
                  "match-event or player-level data that martj42 doesn't provide - a future "
                  "enrichment step (e.g. FBref/Opta-style data for the 2026 World Cup specifically).")

    out_path = OUT_DIR / "betting_markets_overview.md"
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
