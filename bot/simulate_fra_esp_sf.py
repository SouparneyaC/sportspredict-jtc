"""
Joint match simulation for France vs Spain SF (2026-07-14) -- design #1 from
ML_MODEL_BUILD_RESEARCH_2026-07-13.md C.3: price every goal-structure question
off ONE joint simulation so the answers are mutually consistent by construction.
Nothing here is fitted to the 730-row meta dataset; all parameters come from
liquid Smarkets quotes (09_smarkets_quotes_processed.json) plus the project's
fitted Dixon-Coles rho (-0.06) as the low-score correction.

Pipeline:
  1. Fit (lambda_FRA, lambda_ESP, rho) to normalized market quotes: FTR triple,
     team goals O/U 0.5/1.5, total O/U 1.5/2.5/3.5, BTTS, via least squares
     over the DC-corrected scoreline grid.
  2. Fit a linear within-match goal-intensity slope to the first-goal
     time-bracket market.
  3. Simulate N=200k matches: goal counts (DC grid draw), goal times
     (linear-intensity density), ET sub-simulation if level at 90', penalties
     calibrated so P(Spain advances) matches the liquid To-qualify market.
  4. Independent calibrated layers for cards (fit to 3 card lines),
     team SOT (fit to France SOT line + total SOT line), offsides (empirical
     ESPN lambdas -- no market exists).
  5. Emit 11_simulation_results.json with every question's simulated
     probability + the market anchor + consistency checks.

Usage:
    python3 simulate_fra_esp_sf.py
"""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize
from scipy.stats import poisson

ROOT = Path(__file__).resolve().parent.parent
MATCH_DIR = ROOT / "matches" / "France Vs Spain (Jul.14.26)"
N_SIM = 200_000
RNG = np.random.default_rng(20260714)
MAX_G = 10
RHO_INIT = -0.06  # project MLE from model/dixon_coles.py

# Hydration-break minutes, measured across all 12 FRA/ESP games (supplement):
# first break 23-29' (median ~24), second break 63-76' (median ~67).
BREAK1_MIN = 24
BREAK2_MIN = 67

q = json.load(open(MATCH_DIR / "09_smarkets_quotes_processed.json"))


def norm2(market, yes_key, no_key):
    y, n = market[yes_key]["mid"], market[no_key]["mid"]
    return y / (y + n)


def norm3(market, keys):
    tot = sum(market[k]["mid"] for k in keys)
    return {k: market[k]["mid"] / tot for k in keys}

# ── Normalized market targets ────────────────────────────────────────────────
ftr = norm3(q["FTR"], ["France", "Spain", "Draw"])
TARGETS = {
    "p_fra_win": ftr["France"],
    "p_esp_win": ftr["Spain"],
    "p_draw": ftr["Draw"],
    "fra_o05": norm2(q["France_OU0.5_goals"], "Over 0.5 goals", "Under 0.5 goals"),
    "fra_o15": norm2(q["France_OU1.5_goals"], "Over 1.5 goals", "Under 1.5 goals"),
    "esp_o05": norm2(q["Spain_OU0.5_goals"], "Over 0.5 goals", "Under 0.5 goals"),
    "esp_o15": norm2(q["Spain_OU1.5_goals"], "Over 1.5 goals", "Under 1.5 goals"),
    "tot_o15": norm2(q["OU1.5_goals"], "Over 1.5 goals", "Under 1.5 goals"),
    "tot_o25": norm2(q["OU2.5_goals"], "Over 2.5 goals", "Under 2.5 goals"),
    "tot_o35": norm2(q["OU3.5_goals"], "Over 3.5 goals", "Under 3.5 goals"),
    "btts": norm2(q["BTTS"], "Yes", "No"),
}
TO_QUALIFY_SPAIN = norm2(q["To_qualify"], "Spain", "France")


def dc_grid(lam_f, lam_s, rho):
    """Dixon-Coles-corrected scoreline grid P(F=i, S=j)."""
    pf = poisson.pmf(np.arange(MAX_G + 1), lam_f)
    ps = poisson.pmf(np.arange(MAX_G + 1), lam_s)
    grid = np.outer(pf, ps)
    # tau correction on the 4 low-score cells
    grid[0, 0] *= 1 - lam_f * lam_s * rho
    grid[0, 1] *= 1 + lam_f * rho
    grid[1, 0] *= 1 + lam_s * rho
    grid[1, 1] *= 1 - rho
    return grid / grid.sum()


def grid_stats(grid):
    i, j = np.indices(grid.shape)
    return {
        "p_fra_win": grid[i > j].sum(),
        "p_esp_win": grid[i < j].sum(),
        "p_draw": grid[i == j].sum(),
        "fra_o05": grid[i >= 1].sum(),
        "fra_o15": grid[i >= 2].sum(),
        "esp_o05": grid[j >= 1].sum(),
        "esp_o15": grid[j >= 2].sum(),
        "tot_o15": grid[i + j >= 2].sum(),
        "tot_o25": grid[i + j >= 3].sum(),
        "tot_o35": grid[i + j >= 4].sum(),
        "btts": grid[(i >= 1) & (j >= 1)].sum(),
    }


def loss(params):
    lam_f, lam_s, rho = params
    if lam_f <= 0.05 or lam_s <= 0.05 or not -0.3 < rho < 0.3:
        return 1e6
    st = grid_stats(dc_grid(lam_f, lam_s, rho))
    return sum((st[k] - v) ** 2 for k, v in TARGETS.items())


res = minimize(loss, x0=[1.4, 1.2, RHO_INIT], method="Nelder-Mead",
               options={"xatol": 1e-5, "fatol": 1e-10, "maxiter": 5000})
LAM_F, LAM_S, RHO = res.x
fitted = grid_stats(dc_grid(LAM_F, LAM_S, RHO))
print(f"Fitted: lambda_FRA={LAM_F:.4f} lambda_ESP={LAM_S:.4f} rho={RHO:.4f}  (loss={res.fun:.6f})")
print(f"{'target':10s} {'market':>8s} {'fitted':>8s}")
for k, v in TARGETS.items():
    print(f"{k:10s} {v:8.4f} {fitted[k]:8.4f}")

# ── Goal-time density: f(t) proportional to 1 + a*t/90 on [0, 90] ────────────
# Fit a to the first-goal bracket market (P(first goal <= 20'), <= 45').
g1 = q["Goal1_time_bracket"]
br_tot = sum(v["mid"] for v in g1.values())
p_first_le20 = (g1["1-10"]["mid"] + g1["11-20"]["mid"]) / br_tot
p_first_le45 = p_first_le20 + (g1["21-30"]["mid"] + g1["31-40"]["mid"]
                               + 0.5 * g1["41-50"]["mid"]) / br_tot
LAM_TOT = LAM_F + LAM_S


def first_goal_cdf(t_min, a):
    """P(first goal <= t) with intensity c*(1+a*u/90), c set so total = LAM_TOT."""
    # integral of (1+a*u/90) du from 0..t = t + a*t^2/180
    full = 90 + a * 45
    frac = (t_min + a * t_min ** 2 / 180) / full
    return 1 - np.exp(-LAM_TOT * frac)


def timing_loss(a):
    return ((first_goal_cdf(20, a) - p_first_le20) ** 2
            + (first_goal_cdf(45, a) - p_first_le45) ** 2)


a_grid = np.linspace(-0.9, 4.0, 2000)
A_SLOPE = a_grid[np.argmin([timing_loss(a) for a in a_grid])]
print(f"\nTiming slope a={A_SLOPE:.3f}: P(first<=20)={first_goal_cdf(20, A_SLOPE):.4f} "
      f"(mkt {p_first_le20:.4f}), P(first<=45)={first_goal_cdf(45, A_SLOPE):.4f} (mkt {p_first_le45:.4f})")


def draw_goal_times(n_goals_total):
    """Vector of goal times for all sims at once via inverse-CDF sampling."""
    u = RNG.random(n_goals_total)
    # CDF(t) = (t + a t^2/180)/(90 + 45a); invert the quadratic
    a = A_SLOPE
    if abs(a) < 1e-9:
        return 90 * u
    c = (90 + 45 * a) * u
    disc = 1 + 4 * (a / 180) * c
    return (-1 + np.sqrt(disc)) / (2 * a / 180)

# ── Simulate regulation ──────────────────────────────────────────────────────
grid = dc_grid(LAM_F, LAM_S, RHO)
flat = grid.flatten()
draws = RNG.choice(len(flat), size=N_SIM, p=flat / flat.sum())
gf = draws // (MAX_G + 1)   # France goals
gs = draws % (MAX_G + 1)    # Spain goals

# Goal times per sim (needed for the two hydration-window questions)
tot_goals = gf + gs
max_goals = tot_goals.max()
# For each sim, draw tot_goals[i] times; do it vectorized by padding
all_times = draw_goal_times(int(tot_goals.sum()))
# Assign times to sims
idx = np.repeat(np.arange(N_SIM), tot_goals)
goal_before_b1 = np.zeros(N_SIM, dtype=bool)
goal_b1_to_b2 = np.zeros(N_SIM, dtype=bool)
np.logical_or.at(goal_before_b1, idx, all_times < BREAK1_MIN)
np.logical_or.at(goal_b1_to_b2, idx, (all_times >= BREAK1_MIN) & (all_times < BREAK2_MIN))

# ── Extra time + penalties (calibrated to To-qualify) ────────────────────────
level_90 = gf == gs
n_level = level_90.sum()
lam_et_f, lam_et_s = LAM_F / 3, LAM_S / 3   # 30 min at same intensity
et_f = RNG.poisson(lam_et_f, n_level)
et_s = RNG.poisson(lam_et_s, n_level)
et_fra_win = et_f > et_s
et_esp_win = et_s > et_f
et_level = et_f == et_s

# Calibrate P(Spain wins pens) so overall Spain-advance matches market.
p_esp_reg = (gs > gf).mean()
p_esp_et = np.zeros(N_SIM, dtype=bool)
p_esp_et[level_90] = et_esp_win
p_esp_et_m = p_esp_et.mean()
p_pens = np.zeros(N_SIM, dtype=bool)
p_pens[level_90] = et_level
p_pens_m = p_pens.mean()
pen_esp = (TO_QUALIFY_SPAIN - p_esp_reg - p_esp_et_m) / p_pens_m
pen_esp = float(np.clip(pen_esp, 0.05, 0.95))
print(f"\nET/pens: P(level@90)={level_90.mean():.4f} (mkt draw {TARGETS['p_draw']:.4f}), "
      f"P(pens)={p_pens_m:.4f} (mkt {norm2(q['Penalty_shootout'], 'Yes', 'No'):.4f})")
print(f"Calibrated P(Spain wins shootout)={pen_esp:.4f} so Spain-advance hits market {TO_QUALIFY_SPAIN:.4f}")

pens_won_by_esp = np.zeros(N_SIM, dtype=bool)
pens_idx = np.where(p_pens)[0]
pens_won_by_esp[pens_idx] = RNG.random(len(pens_idx)) < pen_esp
spain_advances = (gs > gf) | p_esp_et | pens_won_by_esp

# ── Cards layer (fit NB-ish via Poisson mixture to the 3 card lines) ─────────
card_targets = {
    3: norm2(q["Cards_OU2.5"], "Over 2.5 cards", "Under 2.5 cards"),
    4: norm2(q["Cards_OU3.5"], "Over 3.5 cards", "Under 3.5 cards"),
    5: norm2(q["Cards_OU4.5"], "Over 4.5 cards", "Under 4.5 cards"),
}


def card_loss(params):
    lam, phi = params  # gamma-poisson: shape=lam/phi... keep simple: NB via gamma mixing
    if lam <= 0.1 or phi <= 0.01:
        return 1e6
    shape, scale = 1 / phi, lam * phi
    lam_draws = RNG_CARDS.gamma(shape, scale, 40000)
    x = RNG_CARDS.poisson(lam_draws)
    return sum(((x >= k).mean() - v) ** 2 for k, v in card_targets.items())


RNG_CARDS = np.random.default_rng(7)
best = None
for lam0 in np.linspace(2.2, 4.2, 21):
    for phi0 in np.linspace(0.02, 0.6, 15):
        RNG_CARDS = np.random.default_rng(7)
        l = card_loss([lam0, phi0])
        if best is None or l < best[0]:
            best = (l, lam0, phi0)
_, LAM_CARDS, PHI_CARDS = best
RNG_CARDS = np.random.default_rng(7)
shape, scale = 1 / PHI_CARDS, LAM_CARDS * PHI_CARDS
cards = RNG.poisson(RNG.gamma(shape, scale, N_SIM))
print(f"\nCards: lam={LAM_CARDS:.2f} phi={PHI_CARDS:.3f} -> "
      f"P(3+)={(cards>=3).mean():.4f}/{card_targets[3]:.4f} "
      f"P(4+)={(cards>=4).mean():.4f}/{card_targets[4]:.4f} "
      f"P(5+)={(cards>=5).mean():.4f}/{card_targets[5]:.4f}")

# ── SOT layer ────────────────────────────────────────────────────────────────
fra_sot_o45 = norm2(q["France_SOT_OU4.5"], "Over 4.5 shots on target", "Under 4.5 shots on target")
tot_sot_o95 = norm2(q["Total_SOT_OU9.5"], "Over 9.5 shots on target", "Under 9.5 shots on target")
lam_grid = np.linspace(2.0, 9.0, 1401)
LAM_F_SOT = lam_grid[np.argmin([abs(1 - poisson.cdf(4, l) - fra_sot_o45) for l in lam_grid])]
lam_tot_grid = np.linspace(5.0, 15.0, 2001)
LAM_TOT_SOT = lam_tot_grid[np.argmin([abs(1 - poisson.cdf(9, l) - tot_sot_o95) for l in lam_tot_grid])]
LAM_S_SOT = LAM_TOT_SOT - LAM_F_SOT
sot_f = RNG.poisson(LAM_F_SOT, N_SIM)
sot_s = RNG.poisson(LAM_S_SOT, N_SIM)
print(f"\nSOT: France lam={LAM_F_SOT:.2f} (mkt P(5+)={fra_sot_o45:.4f}), total lam={LAM_TOT_SOT:.2f}, "
      f"Spain lam={LAM_S_SOT:.2f} -> P(Spain 5+)={(sot_s>=5).mean():.4f}, P(France 4+)={(sot_f>=4).mean():.4f}")

# ── Offsides layer (no market; empirical ESPN lambdas) ───────────────────────
LAM_OFF_F, LAM_OFF_S = 7 / 6, 12 / 6   # France 1,1,2,3,0,0 ; Spain 2,2,2,2,1,3
offs = RNG.poisson(LAM_OFF_F, N_SIM) + RNG.poisson(LAM_OFF_S, N_SIM)
print(f"\nOffsides: lam_F={LAM_OFF_F:.2f} lam_S={LAM_OFF_S:.2f} -> P(4+)={(offs>=4).mean():.4f}")

# ── Results ──────────────────────────────────────────────────────────────────
results = {
    "_description": (
        "Joint-simulation outputs for FRA-ESP SF, 200k draws. Goal-structure "
        "questions are mutually consistent by construction (one simulation). "
        "Cards/SOT calibrated to their own market lines; offsides empirical "
        "(no market). Every probability listed with its market anchor where "
        "one exists. Fitted on normalized Smarkets mids fetched 2026-07-14."),
    "fitted_params": {
        "lambda_fra_goals": round(float(LAM_F), 4),
        "lambda_esp_goals": round(float(LAM_S), 4),
        "dixon_coles_rho": round(float(RHO), 4),
        "timing_slope_a": round(float(A_SLOPE), 3),
        "lambda_cards": round(float(LAM_CARDS), 3),
        "cards_overdispersion_phi": round(float(PHI_CARDS), 3),
        "lambda_fra_sot": round(float(LAM_F_SOT), 3),
        "lambda_esp_sot": round(float(LAM_S_SOT), 3),
        "lambda_offsides_combined": round(LAM_OFF_F + LAM_OFF_S, 3),
        "p_spain_wins_shootout_calibrated": round(pen_esp, 4),
        "hydration_break_minutes": [BREAK1_MIN, BREAK2_MIN],
    },
    "market_fit_check": {k: {"market": round(float(v), 4), "fitted": round(float(fitted[k]), 4)}
                         for k, v in TARGETS.items()},
    "question_probs": {
        "Q1_offsides_4plus": {"sim": round(float((offs >= 4).mean()), 4), "market": None},
        "Q2_cards_4plus": {"sim": round(float((cards >= 4).mean()), 4),
                           "market": round(float(card_targets[4]), 4)},
        "Q5_goals_3plus": {"sim": round(float((tot_goals >= 3).mean()), 4),
                           "market": round(float(TARGETS["tot_o25"]), 4)},
        "Q6_extra_time": {"sim": round(float(level_90.mean()), 4),
                          "market": round(float(norm2(q["Extra_time"], "Yes", "No")), 4)},
        "Q7_goal_before_break1": {"sim": round(float(goal_before_b1.mean()), 4),
                                  "market_first_goal_le24_implied": round(float(first_goal_cdf(BREAK1_MIN, A_SLOPE)), 4)},
        "Q9_spain_advances": {"sim": round(float(spain_advances.mean()), 4),
                              "market": round(float(TO_QUALIFY_SPAIN), 4)},
        "Q11_goal_between_breaks": {"sim": round(float(goal_b1_to_b2.mean()), 4), "market": None},
        "Q12_spain_sot_5plus": {"sim": round(float((sot_s >= 5).mean()), 4),
                                "market": "derived: total SOT line minus France SOT line"},
        "Q13_btts": {"sim": round(float(((gf >= 1) & (gs >= 1)).mean()), 4),
                     "market": round(float(TARGETS["btts"]), 4)},
        "Q15_france_sot_4plus": {"sim": round(float((sot_f >= 4).mean()), 4),
                                 "market_5plus": round(float(fra_sot_o45), 4)},
    },
    "consistency_extras": {
        "p_pens": round(float(p_pens_m), 4),
        "market_pens": round(float(norm2(q["Penalty_shootout"], "Yes", "No")), 4),
        "p_fra_win_reg": round(float((gf > gs).mean()), 4),
        "p_esp_win_reg": round(float((gs > gf).mean()), 4),
        "p_first_goal_le20_sim_check": round(float(first_goal_cdf(20, A_SLOPE)), 4),
    },
}
out = MATCH_DIR / "11_simulation_results.json"
with open(out, "w") as f:
    json.dump(results, f, indent=2)
print(f"\nWrote {out}")
print(json.dumps(results["question_probs"], indent=2))
