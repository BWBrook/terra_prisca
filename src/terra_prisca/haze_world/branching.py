"""Rare-guild branching probabilities in a recorded, exogenous environment.

Birth and death rates have units 1/year. Migration rows are origins and
columns are destinations, so the corresponding count generator is transposed.
The Poisson initial-count formula is distinguished from fixed integer counts.
"""

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp
from scipy.special import logsumexp

from . import habitat_coupling as habitat
from . import population_coupling as core


@dataclass
class SurvivalSolution:
    times: np.ndarray
    log_survival: np.ndarray
    evaluations: int

    @property
    def initial_log_survival(self):
        return self.log_survival[:, -1]


def migration_matrix(p):
    active = np.flatnonzero(p.weights > 0)
    rates = np.tile(p.dispersal_yr * p.weights[active], (active.size, 1))
    np.fill_diagonal(rates, 0.)
    return rates


def per_cell_rates(y, p, guild):
    """Return active indices, births and deaths without exponentiating biomass.

    Local rates depend on pressure, temperature and products, not on the
    numerical representation of rare biomass. This remains valid when a
    retained logarithmic stock is below physical floating-point range.
    """
    if guild not in (0, 1) or not p.base.enabled[guild]:
        raise ValueError("The target guild must be enabled")
    y = np.asarray(y, dtype=float)
    if y.shape != (p.state_size,) or np.any(~np.isfinite(y)) or np.any(y < 0):
        raise ValueError("Rates require a finite nonnegative physical state")
    active = np.flatnonzero(p.weights > 0)
    temperatures = habitat.temperatures(y, p)
    births, deaths = [], []
    for j in active:
        local = habitat.local_state(y, int(j))
        g = core.activity_guilds_at_temperature(local, p.base, float(temperatures[j]))[guild]
        synthesis = g.yield_g_mol * (g.uptake(local[0]) - g.maintenance)
        birth = max(synthesis, 0.) * core.HOURS_PER_YEAR
        death = (p.base.biology.loss_h + max(-synthesis, 0.)) * core.HOURS_PER_YEAR
        net = core.fluxes_at_temperature(local, p.base, float(temperatures[j]))["net_growth_yr"][guild]
        if not np.isclose(birth - death, net, rtol=1e-10, atol=1e-10):
            raise ArithmeticError("Branching birth minus death differs from physical net growth")
        births.append(birth)
        deaths.append(death)
    return active, np.asarray(births), np.asarray(deaths)


def backward_survival(times, birth, death, migration, *, rtol=1e-9, atol=1e-11,
                      return_solution=False):
    """Log probability that one cell alive at the start has living descendants.

    Sampled birth/death arrays have shape (time, type); rates between samples
    are linear. ``migration[j,k]`` is the constant per-cell j-to-k rate and
    has a zero diagonal. All terminal type survival probabilities equal one.
    The default result is the initial log-probability array. The optional
    solution retains accepted backward times and logarithms, in descending time.
    """
    times = np.asarray(times, dtype=float)
    birth, death, migration = (np.asarray(v, dtype=float) for v in (birth, death, migration))
    if times.ndim != 1 or times.size < 2 or np.any(~np.isfinite(times)) or np.any(np.diff(times) <= 0):
        raise ValueError("Times must be finite and strictly increasing")
    if birth.ndim != 2 or birth.shape[0] != times.size or birth.shape[1] < 1 or death.shape != birth.shape:
        raise ValueError("Birth and death arrays must have shape (time, type)")
    n = birth.shape[1]
    if migration.shape != (n, n) or np.any(np.diag(migration) != 0):
        raise ValueError("Migration must have shape (type,type) and a zero diagonal")
    if any(np.any(~np.isfinite(v)) or np.any(v < 0) for v in (birth, death, migration)):
        raise ValueError("All event rates must be finite and nonnegative")

    def rhs(t, logu):
        k = min(max(int(np.searchsorted(times, t)) - 1, 0), times.size - 2)
        fraction = (t - times[k]) / (times[k + 1] - times[k])
        b = birth[k] + fraction * (birth[k + 1] - birth[k])
        delta = death[k] + fraction * (death[k + 1] - death[k])
        differences = logu[None, :] - logu[:, None]
        # Zero migration must not turn an irrelevant enormous log-ratio into NaN.
        coupled = np.zeros_like(migration)
        positive = migration > 0
        coupled[positive] = -migration[positive] * np.expm1(differences[positive])
        return b * np.expm1(logu) + delta + coupled.sum(axis=1)

    solution = solve_ivp(rhs, (times[-1], times[0]), np.zeros(n), method="LSODA", rtol=rtol, atol=atol)
    if not solution.success or np.any(~np.isfinite(solution.y)):
        raise ArithmeticError("Backward branching integration failed: " + solution.message)
    if np.any(solution.y > 0):
        raise ArithmeticError("Backward integration produced a survival probability above one")
    result = SurvivalSolution(solution.t, solution.y, solution.nfev)
    return result if return_solution else result.initial_log_survival


def probability_from_log_intensity(log_intensity):
    """Poisson probability of at least one successful lineage, including tails."""
    log_intensity = float(log_intensity)
    if np.isnan(log_intensity):
        raise ValueError("Log intensity cannot be NaN")
    if log_intensity > np.log(-np.log(np.finfo(float).eps / 2)):
        return 1.
    return float(-np.expm1(-np.exp(log_intensity)))


def _exponentiate(value):
    return float(np.exp(value)) if value <= np.log(np.finfo(float).max) else float("inf")


def lineages(log_counts, logu, scale=1.):
    """Poisson initial counts: intensity, probabilities and count-scale class.

    ``scale`` multiplies all supplied mean counts. Classification scans an
    additional 1e-3 to 1e3 relative to that scale. The half-survival scale is
    likewise an additional count multiplier. For fixed counts use
    ``fixed_count_probability``; the Poisson expression is an approximation
    to fixed-count survival when individual survival probabilities are small.
    """
    log_counts, logu = np.asarray(log_counts, dtype=float), np.asarray(logu, dtype=float)
    if log_counts.shape != logu.shape or log_counts.ndim != 1 or not log_counts.size:
        raise ValueError("Count and probability logs must be matching nonempty vectors")
    if np.any(np.isnan(log_counts)) or np.any(np.isposinf(log_counts)) or np.any(np.isnan(logu)) or np.any(logu > 0):
        raise ValueError("Invalid count or probability logs")
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("Count scale must be finite and positive")
    log_lambda = float(logsumexp(log_counts + logu) + np.log(scale))
    low = probability_from_log_intensity(log_lambda + np.log(1e-3))
    high = probability_from_log_intensity(log_lambda + np.log(1e3))
    classification = "robust_loss" if high < .01 else "robust_persistence" if low > .99 else "contingent"
    half_scale = float(np.log(np.log(2.)) - log_lambda)
    return dict(log_lambda=log_lambda, expected_surviving_lineages=_exponentiate(log_lambda),
                survival_probability=probability_from_log_intensity(log_lambda),
                probability_scale_low=low, probability_scale_high=high, classification=classification,
                log_scale_for_half_survival=half_scale, scale_for_half_survival=_exponentiate(half_scale))


def fixed_count_probability(counts, logu):
    """Exact independent-lineage survival for specified nonnegative integers."""
    counts, logu = np.asarray(counts, dtype=float), np.asarray(logu, dtype=float)
    if counts.shape != logu.shape or counts.ndim != 1 or not counts.size:
        raise ValueError("Counts and probability logs must be matching nonempty vectors")
    if np.any(~np.isfinite(counts)) or np.any(counts < 0) or np.any(counts != np.rint(counts)):
        raise ValueError("Fixed initial counts must be finite nonnegative integers")
    if np.any(np.isnan(logu)) or np.any(logu > 0):
        raise ValueError("Invalid probability logs")
    present = counts > 0
    if not np.any(present):
        return 0.
    counts, logu = counts[present], logu[present]
    if np.any(logu == 0):
        return 1.
    log_hazard = logu.copy()
    resolved = logu > -36
    log_hazard[resolved] = np.log(-np.log1p(-np.exp(logu[resolved])))
    return probability_from_log_intensity(float(logsumexp(np.log(counts) + log_hazard)))
