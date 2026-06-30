"""
Stage 3: turn (lambda_home, lambda_away) into a full scoreline
probability grid P(home_goals=i, away_goals=j), with the Dixon & Coles
(1997) low-score correlation correction (research_notes.md S1), and
derive probabilities for every market category we currently cover:
match result (1X2), total goals over/under, BTTS, and team
"score >= N goals".

This stage is pure probability arithmetic given (lambda_home,
lambda_away, rho) -- nothing is fit here. rho (the DC low-score
correlation parameter, typically a small negative number around
-0.05 to -0.15) IS estimated from data via maximum likelihood -- see
fit_rho() below, intended to be run once over the historical panel
(elo_match_panel.csv) as part of the backtest harness, the same way
poisson_goals.py fits b0/b1/b2. Until that's done, predict.py uses a
placeholder rho.

Dependency: scipy (for poisson.pmf and, in fit_rho, optimization).
"""

import math

from scipy.stats import poisson


def nb_pmf(k, mu, alpha):
    """Negative-Binomial (NB2) pmf with mean mu and dispersion alpha
    (variance = mu + alpha*mu^2). alpha=0 reduces to Poisson(mu); alpha>0
    gives fatter-than-Poisson tails -- see fit_nb_dispersion.py."""
    if alpha <= 1e-10:
        return poisson.pmf(k, mu)
    r = 1.0 / alpha
    p = r / (r + mu)
    log_pmf = (math.lgamma(k + r) - math.lgamma(r) - math.lgamma(k + 1)
               + r * math.log(p) + k * math.log(1 - p))
    return math.exp(log_pmf)


def tau(i, j, lam_home, lam_away, rho):
    """Dixon-Coles correction factor, applied only to the four
    low-scoring cells where independence is known to be a poor
    approximation (DC97 S2)."""
    if i == 0 and j == 0:
        return 1 - lam_home * lam_away * rho
    if i == 0 and j == 1:
        return 1 + lam_home * rho
    if i == 1 and j == 0:
        return 1 + lam_away * rho
    if i == 1 and j == 1:
        return 1 - rho
    return 1.0


def scoreline_grid(lam_home, lam_away, rho=0.0, max_goals=10):
    """Return a dict {(i, j): P(home=i, away=j)} for i, j in
    0..max_goals, renormalized to sum to 1 (the tau correction and the
    truncation at max_goals can shift the raw total slightly off 1)."""
    grid = {}
    total = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = (poisson.pmf(i, lam_home) * poisson.pmf(j, lam_away)
                 * tau(i, j, lam_home, lam_away, rho))
            grid[(i, j)] = p
            total += p
    for k in grid:
        grid[k] /= total
    return grid


def scoreline_grid_nb(lam_home, lam_away, alpha, rho=0.0, max_goals=10):
    """Same as scoreline_grid, but using Negative-Binomial marginals
    (mean=lam_*, dispersion=alpha) instead of Poisson, to correct for
    the overdispersion found by goal_totals_diagnostics.py. The DC tau
    correction (still parameterized by lam_home/lam_away/rho, the
    means) is applied unchanged to the four low-score cells."""
    grid = {}
    total = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            p = (nb_pmf(i, lam_home, alpha) * nb_pmf(j, lam_away, alpha)
                 * tau(i, j, lam_home, lam_away, rho))
            grid[(i, j)] = p
            total += p
    for k in grid:
        grid[k] /= total
    return grid


def match_result_probs(grid):
    p_home = sum(p for (i, j), p in grid.items() if i > j)
    p_draw = sum(p for (i, j), p in grid.items() if i == j)
    p_away = sum(p for (i, j), p in grid.items() if i < j)
    return {"home_win": p_home, "draw": p_draw, "away_win": p_away}


def total_goals_over_under(grid, threshold):
    """P(total goals > threshold) and P(total goals <= threshold).
    e.g. threshold=2 answers 'Will the match have 2 or fewer total
    goals?' directly via under_or_equal."""
    p_over = sum(p for (i, j), p in grid.items() if (i + j) > threshold)
    return {"over": p_over, "under_or_equal": 1 - p_over}


def btts_prob(grid):
    return sum(p for (i, j), p in grid.items() if i >= 1 and j >= 1)


def team_score_at_least(grid, team, n):
    """team: 'home' or 'away'. P(that team scores >= n goals)."""
    if team == "home":
        return sum(p for (i, j), p in grid.items() if i >= n)
    return sum(p for (i, j), p in grid.items() if j >= n)


def fit_rho(matches, lambda_fn, rho_grid=None, pmf=None):
    """Estimate rho by maximum likelihood over a list of historical
    matches.

    matches: iterable of (home_goals, away_goals, lambda_home, lambda_away)
    lambda_fn: unused placeholder for future per-match lambda recomputation
    rho_grid: candidate rho values to grid-search (coarse-then-fine grid
              search is sufficient for a single scalar parameter; a 1-D
              optimizer like scipy.optimize.minimize_scalar would also
              work and is the natural upgrade once this is wired into
              the backtest harness).
    pmf: marginal pmf function pmf(k, lam) -> probability, defaulting to
         poisson.pmf. Pass dixon_coles.nb_pmf (with alpha bound via a
         lambda) to refit rho for the Negative-Binomial grid -- see
         fit_nb_dispersion.py.

    Returns the rho in rho_grid maximizing total log-likelihood under
    the DC-corrected model with the given marginal pmf.
    """
    if rho_grid is None:
        rho_grid = [r / 100 for r in range(-30, 11)]  # -0.30 .. 0.10
    if pmf is None:
        pmf = poisson.pmf

    best_rho, best_ll = 0.0, float("-inf")
    for rho in rho_grid:
        ll = 0.0
        for hg, ag, lam_h, lam_a in matches:
            p = (pmf(hg, lam_h) * pmf(ag, lam_a)
                 * tau(hg, ag, lam_h, lam_a, rho))
            ll += 0.0 if p <= 0 else math.log(p)
        if ll > best_ll:
            best_ll, best_rho = ll, rho
    return best_rho
