"""
system_architecture_diagram.py
===============================
Generates the OPERATIONAL pipeline diagram (as opposed to
prediction_instrument_map.png, which documents the STATISTICAL/modeling
taxonomy). This diagram shows how a question actually moves through the
system: ingestion -> classification -> per-match data acquisition ->
modeling/rules -> human review gate -> submission/settlement ->
aggregation -> postmortem feedback loop back into the rule engine.

Run: python3 system_architecture_diagram.py
Outputs: system_architecture_map.png, system_architecture_map.pdf
"""

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.patches import ConnectionStyle

# ─── palette (distinct from the taxonomy diagram's win/loss color coding —
#     this diagram encodes PIPELINE STAGE, not performance) ────────────────
C_INGEST   = "#1b2a4a"   # dark navy   - raw ingestion
C_CLASSIFY = "#2f6690"   # steel blue  - classification/routing
C_ACQUIRE  = "#3a7d7a"   # teal        - per-match data acquisition
C_MODEL    = "#6a4c93"   # purple      - modeling & rules engine
C_GATE     = "#c9762c"   # amber       - human review gate
C_SUBMIT   = "#2e7d5b"   # green       - submit & settle
C_FEEDBACK = "#8a3a3a"   # brick red   - aggregation & feedback
C_GOV      = "#5a5a5a"   # gray        - governance band
TEXT_DARK  = "#1a1a1a"
BG         = "#ffffff"

fig, ax = plt.subplots(figsize=(24, 14), dpi=200)
ax.set_xlim(0, 24)
ax.set_ylim(0, 14)
ax.axis("off")
fig.patch.set_facecolor(BG)

# ─── title ──────────────────────────────────────────────────────────────────
ax.text(12, 13.55, "JTC Research Pipeline — Operational Architecture",
        ha="center", va="center", fontsize=22, fontweight="bold", color=TEXT_DARK)
ax.text(12, 13.1, "JTC / SportsPredict WC2026  ·  How a question moves from platform ingestion to a settled, aggregated track record",
        ha="center", va="center", fontsize=11.5, color="#444444", style="italic")

COL_Y_TOP = 12.2
COL_LABEL_Y = 12.55


def col_header(x, w, label, color):
    ax.add_patch(FancyBboxPatch((x, COL_LABEL_Y - 0.28), w, 0.5,
                                 boxstyle="round,pad=0.04,rounding_size=0.06",
                                 linewidth=0, facecolor=color, alpha=0.16))
    ax.text(x + w / 2, COL_LABEL_Y - 0.03, label, ha="center", va="center",
            fontsize=11.5, fontweight="bold", color=color)


def box(cx, cy, w, h, title, body, color, title_size=10.5, body_size=8.6):
    b = FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                        boxstyle="round,pad=0.03,rounding_size=0.09",
                        linewidth=1.3, edgecolor=color, facecolor=color)
    ax.add_patch(b)
    ax.text(cx, cy + h / 2 - 0.24, title, ha="center", va="top",
            fontsize=title_size, fontweight="bold", color="white", wrap=True)
    ax.text(cx, cy - 0.10, body, ha="center", va="center",
            fontsize=body_size, color="white", wrap=True, linespacing=1.5)


def arrow(p0, p1, color="#888888", style="-", rad=0.0, lw=1.6):
    a = FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=14,
                         connectionstyle=ConnectionStyle.Arc3(rad=rad),
                         linewidth=lw, color=color, linestyle=style, zorder=1)
    ax.add_patch(a)


# ─── column geometry ────────────────────────────────────────────────────────
# 7 columns across x in [0.4, 23.6]
col_w = 3.05
col_x = [0.5 + i * (col_w + 0.28) for i in range(7)]

headers = [
    ("1 · INGESTION", C_INGEST),
    ("2 · CLASSIFICATION", C_CLASSIFY),
    ("3 · PER-MATCH ACQUISITION", C_ACQUIRE),
    ("4 · MODELING & RULES", C_MODEL),
    ("5 · HUMAN REVIEW GATE", C_GATE),
    ("6 · SUBMIT & SETTLE", C_SUBMIT),
    ("7 · AGGREGATE & FEEDBACK", C_FEEDBACK),
]
for x, (label, color) in zip(col_x, headers):
    col_header(x, col_w, label, color)

BOX_W = col_w - 0.15

# Column 1
box(col_x[0] + col_w / 2, 10.8, BOX_W, 1.55,
    "fetch_markets.py",
    "Pulls every open match/market\nfrom the SportsPredict v1 API.\nWrites immediately, one line per\nmatch (JSONL), no buffering.",
    C_INGEST)
box(col_x[0] + col_w / 2, 8.7, BOX_W, 1.35,
    "markets_raw.jsonl",
    "Immutable raw capture.\nTwo data-loss incidents early\nin the campaign formalized this\n'write-to-disk-first' rule.",
    C_INGEST, body_size=8.3)

# Column 2
box(col_x[1] + col_w / 2, 10.8, BOX_W, 1.75,
    "classify_markets.py",
    "Regex-matches each question\nagainst 4 model-coverable patterns\n(match winner, total goals O/U, BTTS).\nEverything else -> no_model.",
    C_CLASSIFY)
box(col_x[1] + col_w / 2, 8.55, BOX_W, 1.45,
    "Routing decision",
    "model-coverable -> analytic\nElo/Poisson/logit path.\nno_model -> live market +\nmanual research path (Col. 3-4).",
    C_CLASSIFY, body_size=8.3)

# Column 3 (3 boxes)
box(col_x[2] + col_w / 2, 11.05, BOX_W, 1.25,
    "01_espn_data.json",
    "Live roster/box-score fetch,\nboth teams' 3 group games,\nteam- and player-level.",
    C_ACQUIRE, body_size=8.3)
box(col_x[2] + col_w / 2, 9.4, BOX_W, 1.25,
    "02_smarkets_markets.json",
    "Live odds fetch (limit=300 +\nclient-side filter -- the name=\nparam is silently broken).",
    C_ACQUIRE, body_size=8.3)
box(col_x[2] + col_w / 2, 7.75, BOX_W, 1.25,
    "Static joins",
    "Transfermarkt value/age, travel,\naltitude, rest days, FIFA rank,\nreferee career stats.",
    C_ACQUIRE, body_size=8.3)
ax.text(col_x[2] + col_w / 2, 6.75, "→ full session logged verbatim to bash_log.txt",
        ha="center", va="center", fontsize=8.2, color=C_ACQUIRE, style="italic", fontweight="bold")

# Column 4 (2 boxes)
box(col_x[3] + col_w / 2, 10.8, BOX_W, 1.6,
    "03_model_derivations.json",
    "Elo cross-check, Poisson λ-fit\n(brentq), Dixon-Coles/NB grid,\nSkellam for comparison questions.",
    C_MODEL, body_size=8.3)
box(col_x[3] + col_w / 2, 8.7, BOX_W, 1.75,
    "04_rules_applied.json",
    "RULE1-18 engine + tier tag\n(DIRECT / TEAM_MODEL / PLAYER_\nLIQUID / ILLIQUID / TIMING).\nFloors & risk gates applied here.",
    C_MODEL, body_size=8.3)

# Column 5
box(col_x[4] + col_w / 2, 10.4, BOX_W, 2.35,
    "predictions_review.csv",
    "Every suggested number is\nsurfaced for manual read-back\nbefore anything is submitted --\nnever auto-submitted.\n\nPrimary defense against\ntranscription errors (Kane\n-44.54, Brazil -51.97 RBP).",
    C_GATE, body_size=8.4)

# Column 6 (2 boxes)
box(col_x[5] + col_w / 2, 10.8, BOX_W, 1.35,
    "05_estimates.json",
    "Final numbers submitted\nto the JTC platform.",
    C_SUBMIT, body_size=8.6)
box(col_x[5] + col_w / 2, 9.05, BOX_W, 1.55,
    "06_post_match_results.json",
    "Outcome + RBP captured\nper question once the\nmatch settles.",
    C_SUBMIT, body_size=8.6)

# Column 7 (2 boxes)
box(col_x[6] + col_w / 2, 10.9, BOX_W, 1.55,
    "build_master_dataset.py",
    "One flat row per (match, question)\nacross all schema eras ->\nmaster_question_dataset.csv.\nRaw files never touched.",
    C_FEEDBACK, body_size=8.3)
box(col_x[6] + col_w / 2, 8.85, BOX_W, 1.75,
    "Postmortems & diagnostics",
    "Rule refinements (RULE16-18),\ncrowd-bias regression updates,\nML meta-model checks -- feed\nback into Column 4's rule engine.",
    C_FEEDBACK, body_size=8.3)

# ─── forward arrows between columns ────────────────────────────────────────
fwd_y = 9.6
for i in range(6):
    arrow((col_x[i] + col_w, fwd_y), (col_x[i + 1], fwd_y), color="#999999", lw=1.8)

# ─── feedback loop: column 7 back to column 4's rule engine ────────────────
arrow((col_x[6] + col_w / 2, 7.95), (col_x[3] + col_w / 2, 7.7),
      color=C_FEEDBACK, rad=-0.18, lw=2.2, style="--")
ax.text((col_x[6] + col_x[3]) / 2 + col_w / 2, 6.55,
        "feedback loop — every postmortem can add/revise a named rule for the next match",
        ha="center", va="center", fontsize=9.2, color=C_FEEDBACK, fontweight="bold", style="italic")

# ─── governance band (cross-cutting, spans all columns) ───────────────────
gov_y = 4.9
ax.add_patch(FancyBboxPatch((0.4, gov_y - 0.95), 23.2, 1.9,
                             boxstyle="round,pad=0.05,rounding_size=0.12",
                             linewidth=1.5, edgecolor=C_GOV, facecolor=C_GOV, alpha=0.10))
ax.text(12, gov_y + 0.68, "OPERATIONAL DISCIPLINE  (cross-cutting, applies to every column above)",
        ha="center", va="center", fontsize=12, fontweight="bold", color=C_GOV)
gov_items = [
    "Immutable raw files\n(never edited in place)",
    "Full bash_log.txt transcript\nper match, every session",
    "Git version control,\nno destructive rewrites",
    "Documented schema-era drift\n(6 formats, A-F, all handled)",
    "Persistent project memory\n(carries context across sessions)",
]
gx = [1.9 + i * 4.55 for i in range(5)]
for x, item in zip(gx, gov_items):
    ax.text(x, gov_y - 0.28, item, ha="center", va="center", fontsize=8.8, color=C_GOV, linespacing=1.4)

# ─── legend ─────────────────────────────────────────────────────────────────
legend_y = 2.55
ax.text(0.5, legend_y + 0.55, "LEGEND", fontsize=10, fontweight="bold", color="#333333")
legend_items = [
    ("Ingestion", C_INGEST), ("Classification", C_CLASSIFY), ("Data acquisition", C_ACQUIRE),
    ("Modeling / rules", C_MODEL), ("Human review gate", C_GATE),
    ("Submit / settle", C_SUBMIT), ("Aggregate / feedback", C_FEEDBACK),
]
for i, (label, color) in enumerate(legend_items):
    lx = 0.5 + i * 3.35
    ax.add_patch(FancyBboxPatch((lx, legend_y - 0.05), 0.35, 0.3,
                                 boxstyle="round,pad=0.02,rounding_size=0.04",
                                 linewidth=0, facecolor=color))
    ax.text(lx + 0.48, legend_y + 0.1, label, ha="left", va="center", fontsize=8.8, color="#333333")

# ─── footer ─────────────────────────────────────────────────────────────────
ax.text(12, 0.9,
        "Every submitted estimate to date (71 settled matches, 436+ scored questions, +872 cumulative RBP) has passed through this exact seven-stage pipeline.",
        ha="center", va="center", fontsize=9, color="#555555", style="italic")
ax.text(12, 0.5,
        "See META_MODEL_LAB_NOTES.md and JULY3_POSTMORTEM_DEEP_DIVE.md for analysis built on top of this architecture; prediction_instrument_map.png documents the statistical/modeling taxonomy that runs inside Column 4.",
        ha="center", va="center", fontsize=8, color="#777777")

plt.tight_layout()
fig.savefig("system_architecture_map.png", facecolor=BG, bbox_inches="tight")
fig.savefig("system_architecture_map.pdf", facecolor=BG, bbox_inches="tight")
print("Saved system_architecture_map.png and system_architecture_map.pdf")
