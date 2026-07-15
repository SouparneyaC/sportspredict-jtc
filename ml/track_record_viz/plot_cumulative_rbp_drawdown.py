"""
Candidate A from TRACK_RECORD_VISUALIZATION_RESEARCH_2026-07-15.md: a cumulative
RBP-over-match-number line chart with an underwater drawdown panel.

Two stacked panels sharing an x-axis of match number (chronological, not calendar date --
follows MacKay 2025's own Figure 2, and avoids visually compressing the group stage,
which has many matches in a short calendar window, against the more sparsely-spaced
knockout rounds). Top: cumulative RBP. Bottom: current cumulative minus running peak
("underwater" drawdown), so losing streaks read as visually distinct valleys, following
the pyfolio tearsheet convention of separating cumulative performance from drawdown
rather than cramming both onto one axis.

Also produces a second, simpler exhibit -- cumulative_rbp_simple.png/.pdf -- the same
cumulative-RBP line alone, no drawdown panel, for embedding in README.md's landing
"campaign so far" section, where the fuller two-panel analytical version (this script's
main output) would be more chart than a landing page needs. Same underlying data and
computation as the main chart; not a separate/re-derived figure.

Run:
    python3 ml/track_record_viz/plot_cumulative_rbp_drawdown.py
Outputs:
    ml/track_record_viz/cumulative_rbp_drawdown.png (+.pdf) -- full 2-panel chart
    ml/track_record_viz/cumulative_rbp_simple.png (+.pdf)   -- top panel only, for README.md
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from lib_track_record_data import C_NEGATIVE, C_NEUTRAL, C_POSITIVE, match_level, shared_y_pad

ROOT = Path(__file__).resolve().parents[2]
OUT_PNG = Path(__file__).resolve().parent / "cumulative_rbp_drawdown.png"
OUT_PDF = Path(__file__).resolve().parent / "cumulative_rbp_drawdown.pdf"
SIMPLE_PNG = Path(__file__).resolve().parent / "cumulative_rbp_simple.png"
SIMPLE_PDF = Path(__file__).resolve().parent / "cumulative_rbp_simple.pdf"

DPI = 200


def build():
    matches = match_level()
    n_matches = len(matches)
    n_questions = int(matches["n_questions_scored"].sum())

    cum = matches["match_rbp_total"].cumsum()
    peak = cum.cummax()
    drawdown = cum - peak
    max_dd_idx = drawdown.idxmin()

    # Figure width scales with data volume rather than a fixed guess -- 0.12in/match
    # lands at ~10in at the current 83 matches, inside the pyfolio tearsheet's own
    # common 10-16in width range; the 10in floor keeps the chart legible if this script
    # is run early in a smaller future campaign.
    fig_width = max(10, n_matches * 0.12)
    fig, (ax_cum, ax_dd) = plt.subplots(
        2, 1, sharex=True, figsize=(fig_width, 7.5),
        gridspec_kw={"height_ratios": [2, 1]},  # mirrors the pyfolio tearsheet proportion
        dpi=DPI,
    )

    ax_cum.plot(matches["match_number"], cum, color=C_POSITIVE, linewidth=1.6,
                marker="o", markersize=3, zorder=3)
    ax_cum.axhline(0, color=C_NEUTRAL, linewidth=0.8, linestyle="--", zorder=1)
    cum_lo, cum_hi = shared_y_pad(list(cum) + [0])
    ax_cum.set_ylim(cum_lo, cum_hi)
    ax_cum.set_ylabel("Cumulative RBP")
    ax_cum.set_title("JTC Campaign Track Record: Cumulative RBP by Match")

    ax_dd.fill_between(matches["match_number"], drawdown, 0, color=C_NEGATIVE, alpha=0.3,
                        zorder=2)
    ax_dd.plot(matches["match_number"], drawdown, color=C_NEGATIVE, linewidth=1.0, zorder=3)
    ax_dd.axhline(0, color=C_NEUTRAL, linewidth=0.8, linestyle="--", zorder=1)
    dd_lo, dd_hi = shared_y_pad(list(drawdown) + [0])
    ax_dd.set_ylim(dd_lo, dd_hi)
    ax_dd.set_ylabel("Drawdown\n(cum. RBP - running peak)")
    ax_dd.set_xlabel("Match number (chronological order; see caption)")

    for a in (ax_cum, ax_dd):
        a.spines["top"].set_visible(False)
        a.spines["right"].set_visible(False)

    max_dd = drawdown.loc[max_dd_idx]
    max_dd_match = matches.loc[max_dd_idx, "match"]
    fig.text(
        0.01, 0.005,
        f"n={n_matches} settled matches, {n_questions} individually-scored questions as of "
        f"{matches['date'].max().date()}. Cumulative total: {cum.iloc[-1]:+.2f} RBP. "
        f"Largest drawdown: {max_dd:.2f} at match #{matches.loc[max_dd_idx, 'match_number']} "
        f"({max_dd_match}). "
        f"MacKay (2025) derives ~100 individually-scored questions for a 1-SD skill/luck "
        f"separation and ~400 for 95% confidence; this campaign's {n_questions} questions "
        f"clear both, but this chart's own x-axis unit is the coarser 83-match aggregate, "
        f"which MacKay's derivation does not directly cover -- read any visual trend here as "
        f"suggestive, not a statistically confirmed skill signal.",
        fontsize=6.5, color="#555555", wrap=True,
    )

    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(OUT_PNG, dpi=DPI, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")
    plt.close(fig)

    build_simple(matches, cum, n_matches, n_questions)

    return matches, cum, drawdown


def build_simple(matches, cum, n_matches, n_questions):
    """The same cumulative-RBP line as build()'s top panel, alone -- no drawdown panel,
    no caption -- for README.md, where a single clean line reads better at a glance
    than the fuller two-panel analytical chart. Same data, same computation; the only
    difference is what's omitted, not a re-derivation.
    """
    fig_width = max(10, n_matches * 0.12)
    fig, ax = plt.subplots(figsize=(fig_width, 4.5), dpi=DPI)

    ax.plot(matches["match_number"], cum, color=C_POSITIVE, linewidth=1.6,
            marker="o", markersize=3, zorder=3)
    ax.axhline(0, color=C_NEUTRAL, linewidth=0.8, linestyle="--", zorder=1)
    cum_lo, cum_hi = shared_y_pad(list(cum) + [0])
    ax.set_ylim(cum_lo, cum_hi)
    ax.set_xlabel("Match number (chronological order)")
    ax.set_ylabel("Cumulative RBP")
    ax.set_title("JTC Campaign Track Record: Cumulative RBP by Match")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.savefig(SIMPLE_PNG, dpi=DPI, bbox_inches="tight")
    fig.savefig(SIMPLE_PDF, bbox_inches="tight")
    plt.close(fig)


def verify(matches, cum, drawdown):
    for path, min_size, magic in [
        (OUT_PNG, 20_000, b"\x89PNG"), (OUT_PDF, 5_000, b"%PDF-"),
        (SIMPLE_PNG, 15_000, b"\x89PNG"), (SIMPLE_PDF, 4_000, b"%PDF-"),
    ]:
        assert path.exists(), f"missing output {path}"
        size = path.stat().st_size
        assert size > min_size, f"{path} suspiciously small ({size} bytes)"
        with open(path, "rb") as f:
            head = f.read(8)
        assert head.startswith(magic), f"{path} does not start with expected magic bytes"

    # Reopen the figure's axes state is gone after plt.close(); re-derive expected
    # finite, non-degenerate limits directly from the data instead.
    cum_lo, cum_hi = shared_y_pad(list(cum) + [0])
    dd_lo, dd_hi = shared_y_pad(list(drawdown) + [0])
    for lo, hi in [(cum_lo, cum_hi), (dd_lo, dd_hi)]:
        assert np.isfinite(lo) and np.isfinite(hi) and hi > lo, "degenerate axis range"

    assert (drawdown <= 1e-9).all(), "drawdown should never be positive by construction"
    print(f"[verify] OK: {OUT_PNG.name} and {OUT_PDF.name} exist, sized, valid headers, "
          f"axis ranges finite and non-degenerate.")


if __name__ == "__main__":
    matches, cum, drawdown = build()
    verify(matches, cum, drawdown)
    print(f"Saved {OUT_PNG.name} and {OUT_PDF.name}")
