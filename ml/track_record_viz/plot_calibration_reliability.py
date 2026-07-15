"""
Candidate C from TRACK_RECORD_VISUALIZATION_RESEARCH_2026-07-15.md: a reliability/
calibration diagram. A DIFFERENT chart from the other 3, answering a different
question -- not "did the campaign trend up or down" (Candidates A/B) but "when I say
X%, does X% of the time it actually happen." Question-level data is the correct unit
here (calibration pools many independent probability judgments; this is one of the
few places in this project where question-level, not match-level, is the right
aggregation).

Binning method: isotonic regression (the CORP/PAV approach), NOT a manually chosen bin
count. Dimitriadis, Gneiting & Jordan (2021, PNAS) demonstrate that an arbitrarily
chosen bin count materially changes a reliability diagram's conclusion -- this directly
answers the "no magic numbers" brief for the one candidate design most exposed to that
exact failure mode.

Confidence band: bootstrap resampling with n_boot=1000, seed=42 -- not an arbitrary
round number, reused verbatim from this same project's own ml/platt_diagnostic.py::
bootstrap_ci() convention rather than inventing a new constant for a sibling
calibration diagnostic.

Run:
    python3 ml/track_record_viz/plot_calibration_reliability.py
Outputs:
    ml/track_record_viz/calibration_reliability.png
    ml/track_record_viz/calibration_reliability.pdf
"""
import random
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from sklearn.isotonic import IsotonicRegression

from lib_track_record_data import C_NEGATIVE, C_NEUTRAL, C_POSITIVE, question_level_for_calibration

OUT_PNG = Path(__file__).resolve().parent / "calibration_reliability.png"
OUT_PDF = Path(__file__).resolve().parent / "calibration_reliability.pdf"

DPI = 200
N_BOOT = 1000  # matches ml/platt_diagnostic.py::bootstrap_ci's own convention exactly
SEED = 42      # ditto -- reused, not re-chosen


def fit_isotonic(x, y):
    iso = IsotonicRegression(y_min=0, y_max=1, increasing=True, out_of_bounds="clip")
    iso.fit(x, y)
    return iso


def build():
    rows = question_level_for_calibration()
    x = rows["our_estimate"].to_numpy(dtype=float)
    y = rows["outcome"].to_numpy(dtype=float)
    n = len(x)

    grid = np.linspace(0.0, 1.0, 200)
    iso = fit_isotonic(x, y)
    fitted_curve = iso.predict(grid)

    # Per-segment empirical points: group the actual training rows by their fitted
    # isotonic level (the PAV algorithm's own pooled segments), not an arbitrary bin
    # count -- mean(x), mean(y), and n per segment, marker area scaled by sqrt(n) as a
    # secondary, supplementary encoding only (per Cleveland & McGill, area is a weaker
    # perceptual channel than position -- used here only for a relative sample-size
    # cue, never as the primary calibration read, which is the position-based curve).
    fitted_at_x = iso.predict(x)
    seg_key = np.round(fitted_at_x, 6)
    segments = []
    for level in np.unique(seg_key):
        mask = seg_key == level
        segments.append((x[mask].mean(), y[mask].mean(), int(mask.sum())))
    seg_x, seg_y, seg_n = map(np.array, zip(*segments))

    # Bootstrap confidence band: n_boot=1000, seed=42, resampling rows with
    # replacement and refitting -- same iteration count/seed/percentile method as
    # ml/platt_diagnostic.py::bootstrap_ci(), reused rather than re-chosen.
    random.seed(SEED)
    boot_curves = np.empty((N_BOOT, len(grid)))
    for b in range(N_BOOT):
        idx = [random.randint(0, n - 1) for _ in range(n)]
        xb, yb = x[idx], y[idx]
        boot_curves[b] = fit_isotonic(xb, yb).predict(grid)
    band_lo = np.percentile(boot_curves, 2.5, axis=0)
    band_hi = np.percentile(boot_curves, 97.5, axis=0)
    # Loose sanity check used later in verify(): band should bracket the point
    # estimate almost everywhere (some boundary artifact is expected near 0/1 where
    # isotonic regression clips).
    bracket_frac = float(np.mean((fitted_curve >= band_lo) & (fitted_curve <= band_hi)))

    fig = plt.figure(figsize=(8, 8), dpi=DPI)
    # Main calibration panel + a shorter sharpness-histogram panel beneath it, sharing
    # the x-axis -- same "two purpose-specific panels rather than one crowded axis"
    # principle Candidate A already applies.
    gs = fig.add_gridspec(4, 1, hspace=0.45)
    ax_main = fig.add_subplot(gs[0:3, 0])
    ax_hist = fig.add_subplot(gs[3, 0], sharex=ax_main)

    ax_main.plot([0, 1], [0, 1], linestyle="--", color=C_NEUTRAL, linewidth=1.0,
                 label="Perfect calibration", zorder=1)
    ax_main.fill_between(grid, band_lo, band_hi, color=C_POSITIVE, alpha=0.15, zorder=2,
                          label=f"{N_BOOT}-resample 95% bootstrap band")
    ax_main.plot(grid, fitted_curve, color=C_POSITIVE, linewidth=1.8, zorder=4,
                 label="Isotonic-regression calibration curve")
    ax_main.scatter(seg_x, seg_y, s=8 * np.sqrt(seg_n), color=C_NEGATIVE,
                     edgecolor="white", linewidth=0.5, alpha=0.85, zorder=5,
                     label="Empirical segment means (marker area ~ sqrt(n))")

    # A square [0,1]x[0,1] axis is a geometric necessity, not a style preference --
    # without it the 45-degree reference line would not actually render at 45 degrees.
    ax_main.set_aspect("equal", adjustable="box")
    ax_main.set_xlim(0, 1)
    ax_main.set_ylim(0, 1)
    ax_main.set_xlabel("Submitted probability (our_estimate)")
    ax_main.set_ylabel("Observed frequency of outcome=1")
    ax_main.set_title("JTC Campaign Reliability Diagram (question-level)")
    ax_main.legend(loc="upper left", fontsize=8, frameon=False)
    ax_main.spines["top"].set_visible(False)
    ax_main.spines["right"].set_visible(False)
    # Both panels share one x-axis (sharex=ax_main below) and now both display it
    # explicitly -- the top panel used to hide its tick labels on the theory that
    # repeating them on the histogram below was redundant, but that made the shared
    # axis too easy to miss at a glance; showing it on both panels is less minimal
    # but unambiguous, which wins here.

    # Sharpness inset: bins="auto" is NumPy's own Freedman-Diaconis-based rule --
    # parameter-free, not a hand-picked integer bin count.
    ax_hist.hist(x, bins="auto", color=C_NEUTRAL, edgecolor="white", linewidth=0.3)
    ax_hist.set_xlim(0, 1)
    ax_hist.set_xlabel("Submitted probability (our_estimate)")
    ax_hist.set_ylabel("Count", fontsize=8)
    ax_hist.spines["top"].set_visible(False)
    ax_hist.spines["right"].set_visible(False)

    fig.text(
        0.01, 0.01,
        f"n={n} individually-scored questions with a resolved outcome across "
        f"{rows['match'].nunique()} matches. Binning: isotonic regression (CORP-style, "
        f"no manually chosen bin count -- Dimitriadis, Gneiting & Jordan 2021, PNAS). "
        f"Band: {N_BOOT}-resample bootstrap, seed={SEED}, matching ml/platt_diagnostic.py's "
        f"own convention. This diagram answers a different question from the campaign-"
        f"trajectory charts (cumulative_rbp_drawdown.png, match_rbp_waterfall.png): are "
        f"submitted probabilities well-calibrated, independent of match date or RBP scale.",
        fontsize=6.5, color="#555555", wrap=True,
    )

    # tight_layout is skipped here (not just left unused): matplotlib itself warns
    # that it isn't compatible with ax_main's set_aspect("equal") -- silently letting
    # it run anyway was exactly what squeezed ax_main's own x-tick labels into the
    # old, too-narrow hspace and made them disappear. subplots_adjust with the
    # generous hspace above is the deliberate replacement.
    fig.subplots_adjust(left=0.10, right=0.97, top=0.95, bottom=0.16)
    fig.savefig(OUT_PNG, dpi=DPI)
    fig.savefig(OUT_PDF)
    plt.close(fig)

    return rows, grid, fitted_curve, band_lo, band_hi, bracket_frac


def verify(rows, grid, fitted_curve, band_lo, band_hi, bracket_frac):
    for path, min_size, magic in [(OUT_PNG, 20_000, b"\x89PNG"), (OUT_PDF, 5_000, b"%PDF-")]:
        assert path.exists(), f"missing output {path}"
        size = path.stat().st_size
        assert size > min_size, f"{path} suspiciously small ({size} bytes)"
        with open(path, "rb") as f:
            head = f.read(8)
        assert head.startswith(magic), f"{path} does not start with expected magic bytes"

    assert np.all(fitted_curve >= -1e-9) and np.all(fitted_curve <= 1 + 1e-9), \
        "fitted curve must stay within [0,1]"
    assert np.all(np.diff(fitted_curve) >= -1e-9), \
        "isotonic curve must be monotonic non-decreasing by construction"
    assert bracket_frac >= 0.95, \
        f"bootstrap band should bracket the point estimate on >=95% of the grid, got {bracket_frac:.3f}"
    print(f"[verify] OK: {OUT_PNG.name} and {OUT_PDF.name} exist, sized, valid headers, "
          f"fitted curve monotonic and in [0,1], bootstrap band brackets it on "
          f"{bracket_frac:.1%} of the grid.")


if __name__ == "__main__":
    rows, grid, fitted_curve, band_lo, band_hi, bracket_frac = build()
    verify(rows, grid, fitted_curve, band_lo, band_hi, bracket_frac)
    print(f"Saved {OUT_PNG.name} and {OUT_PDF.name}")
