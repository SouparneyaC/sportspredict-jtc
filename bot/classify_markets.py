"""
Classify every market question across all fetched matches into categories
our existing models can/can't handle.

Categories we CAN predict today:
  - match_winner:      "Will <TEAM> win the match?"          -> ordered_logit P(team wins)
  - total_goals_under: "Will the match have N or fewer total goals?" -> NB-corrected Dixon-Coles
  - total_goals_over:  "Will the match have N or more total goals?"  -> NB-corrected Dixon-Coles
  - btts_and_over:     "Will both teams score AND the match have N or more total goals?" -> scoreline grid

Everything else (halftime markets, second-half markets, cards, corners,
offsides, shots on target, player props, etc.) -> "no_model" -- requires
data sources we don't have.

Usage:
    python3 classify_markets.py
"""

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PATTERNS = [
    ("match_winner", re.compile(r"^Will (.+) win the match\?$")),
    ("total_goals_under", re.compile(r"^Will the match have (\d+) or fewer total goals\?$")),
    ("total_goals_over", re.compile(r"^Will the match have (\d+) or more total goals\?$")),
    ("btts_and_over", re.compile(r"^Will both teams score AND the match have (\d+) or more total goals\?$")),
]


def classify(question):
    for cat, pat in PATTERNS:
        m = pat.match(question)
        if m:
            return cat, m.groups()
    return "no_model", None


def main():
    counts = Counter()
    examples = {}
    with open(ROOT / "data" / "markets_raw.jsonl") as f:
        for line in f:
            d = json.loads(line)
            for m in d["markets"]:
                cat, args = classify(m["question"])
                counts[cat] += 1
                examples.setdefault(cat, m["question"])

    total = sum(counts.values())
    print(f"Total markets: {total}\n")
    for cat, c in counts.most_common():
        print(f"{cat:20s} {c:4d}  e.g. \"{examples[cat]}\"")


if __name__ == "__main__":
    main()
