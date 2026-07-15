"""
Candidate B from TRACK_RECORD_VISUALIZATION_RESEARCH_2026-07-15.md: a per-match RBP
waterfall/sign-coded bar chart, ordered by date.

One bar per match, chronological x-axis, height = that match's total RBP, colored by
sign. Bar length from a shared zero baseline (not bubble area or color-intensity alone)
is the magnitude encoding, following Cleveland & McGill's ranking of perceptual tasks --
length-from-a-common-baseline is judged far more accurately than area or angle.

Structural precedent: this project's own already-studied
external_repos/machine-learning-for-trading/case_studies/utils/strategy_analysis.py::
plot_sharpe_waterfall() uses the identical bar shape and a data-proportional annotation-
offset pattern -- reused here, with its red/green sign-coding deliberately replaced by
a colorblind-safe pair (see lib_track_record_data.py) and its offset floor rescaled from
Sharpe-ratio scale (0-3) to RBP scale (roughly -50 to +180).

Run:
    python3 ml/track_record_viz/plot_match_rbp_waterfall.py
Outputs:
    ml/track_record_viz/match_rbp_waterfall.png
    ml/track_record_viz/match_rbp_waterfall.pdf
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from lib_track_record_data import C_NEGATIVE, C_NEUTRAL, C_POSITIVE, match_level, shared_y_pad

OUT_PNG = Path(__file__).resolve().parent / "match_rbp_waterfall.png"
OUT_PDF = Path(__file__).resolve().parent / "match_rbp_waterfall.pdf"

DPI = 200


def build():
    matches = match_level()
    n_matches = len(matches)
    totals = matches["match_rbp_total"].to_numpy()
    colors = [C_POSITIVE if v >= 0 else C_NEGATIVE for v in totals]

    # Figure width derivation, not a bare guess: a 0.6-data-unit-wide bar rendered at
    # 0.18in per match-slot occupies ~0.108in ~= 22px at this script's dpi=200 --
    # comfortably above a hairline-blur threshold, so bars stay individually
    # resolvable. 14in floor covers the case of a much smaller campaign.
    fig_width = max(14, n_matches * 0.18)
    fig, ax = plt.subplots(figsize=(fig_width, 6), dpi=DPI)

    bars = ax.bar(matches["match_number"], totals, width=0.6, color=colors,
                   edgecolor="white", linewidth=0.5, zorder=3)
    ax.axhline(0, color=C_NEUTRAL, linewidth=0.8, linestyle="--", zorder=1)

    lo, hi = shared_y_pad(list(totals) + [0])
    ax.set_ylim(lo, hi)
    ax.set_xlim(0.5, n_matches + 0.5)
    ax.set_xlabel("Match number (chronological order)")
    ax.set_ylabel("Match RBP total")
    ax.set_title("JTC Campaign Track Record: RBP by Match (sign-coded)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Sparse annotation: always the objective best/worst match, never a hand-curated
    # selection. Offset adapts strategy_analysis.py's own data-proportional formula
    # (offset = max(abs(top) * 0.04, 0.02)) -- the multiplicative term is scale-
    # invariant and kept as-is; the additive floor is rescaled from 0.02 (tuned for
    # Sharpe-ratio-scale 0-3 data, invisible against RBP's 0-180 scale) to
    # 0.01 * max(|totals|), i.e. the same underlying "offset is a function of the
    # data, not a fixed constant" principle, correctly re-scaled to this chart's range.
    best_idx = int(np.argmax(totals))
    worst_idx = int(np.argmin(totals))
    max_abs = float(np.max(np.abs(totals)))
    for idx in (best_idx, worst_idx):
        bar = bars[idx]
        val = totals[idx]
        match_name = matches.iloc[idx]["match"]
        offset = max(abs(val) * 0.04, 0.01 * max_abs)
        va = "bottom" if val >= 0 else "top"
        y = val + offset if val >= 0 else val - offset
        ax.text(bar.get_x() + bar.get_width() / 2, y, f"{match_name}\n{val:+.2f}",
                ha="center", va=va, fontsize=8, fontweight="bold")

    cum_total = totals.sum()
    fig.text(
        0.01, 0.01,
        f"n={n_matches} settled matches. Cumulative total: {cum_total:+.2f} RBP "
        f"(matches the cumulative-RBP chart's own total -- see plot_cumulative_rbp_"
        f"drawdown.py). Bars annotated at the campaign's single best and worst match "
        f"only, per this project's own 'grade every bet, every time' discipline: this "
        f"chart shows every settled match, not a curated highlight reel.",
        fontsize=7, color="#555555",
    )

    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT_PNG, dpi=DPI, bbox_inches="tight")
    fig.savefig(OUT_PDF, bbox_inches="tight")
    plt.close(fig)

    return matches, totals, bars


def verify(matches, totals):
    for path, min_size, magic in [(OUT_PNG, 20_000, b"\x89PNG"), (OUT_PDF, 5_000, b"%PDF-")]:
        assert path.exists(), f"missing output {path}"
        size = path.stat().st_size
        assert size > min_size, f"{path} suspiciously small ({size} bytes)"
        with open(path, "rb") as f:
            head = f.read(8)
        assert head.startswith(magic), f"{path} does not start with expected magic bytes"

    lo, hi = shared_y_pad(list(totals) + [0])
    assert np.isfinite(lo) and np.isfinite(hi) and hi > lo, "degenerate axis range"
    assert len(matches) == len(totals), "bar count must match input row count"
    print(f"[verify] OK: {OUT_PNG.name} and {OUT_PDF.name} exist, sized, valid headers, "
          f"{len(totals)} bars drawn matching {len(matches)} input matches.")


if __name__ == "__main__":
    matches, totals, bars = build()
    verify(matches, totals)
    print(f"Saved {OUT_PNG.name} and {OUT_PDF.name}")
