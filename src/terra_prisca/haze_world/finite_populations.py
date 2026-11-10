"""Deterministic cell censuses and continuous mean immigration, in years.

Cell counts use the stated active habitat and cell-mass assumptions. A census
removes an entire below-floor guild; immigration is not a Poisson arrival model.
"""

from dataclasses import dataclass
from time import perf_counter

import numpy as np
from scipy.integrate import ode
from scipy.special import expit

from . import population_coupling as core

GUILDS = ("acetogen", "methanogen")
BIOMASS_SCALE = 1e-3


@dataclass(frozen=True)
class CellProcess:
    minimum_cells: float = 1.
    census_yr: float = 10.
    immigration_cells_yr: tuple[float, float] = (0., 0.)
    cell_mass_gdw: float = 3e-13
    surface_cm2: float = 5.1e18

    def __post_init__(self):
        if not np.isfinite(self.minimum_cells) or self.minimum_cells < 0:
            raise ValueError("The census floor must be finite and nonnegative; zero disables removals")
        if not all(np.isfinite(x) and x > 0 for x in (self.census_yr, self.cell_mass_gdw, self.surface_cm2)):
            raise ValueError("Census interval, cell mass and habitat area must be positive")
        if len(self.immigration_cells_yr) != 2 or not all(np.isfinite(x) and x >= 0 for x in self.immigration_cells_yr):
            raise ValueError("Specify two finite nonnegative mean immigration fluxes")


@dataclass
class FiniteResult:
    t: np.ndarray
    y: np.ndarray
    log_biomass: np.ndarray
    census_activity: np.ndarray
    extinction_events: list[dict]
    arrival_events: list[dict]
    ledger: dict
    min_cells: np.ndarray
    min_log_cells: np.ndarray
    first_extinction_yr: float | None
    first_extinction_by_guild_yr: tuple[float | None, float | None]
    metadata: dict


def _inverse_softplus(value):
    return value + np.log(-np.expm1(-value))


def integrate_finite(y0, p, years, process=CellProcess(), *, sample_every_censuses=100):
    """Apply t=0 census, then scheduled censuses, reporting after each removal.

    Initial positive stocks below the floor are removed. A partial final
    interval is sampled without an additional census. LSODA history is kept
    across unchanged censuses and reset only when a census changes a stock.
    Minima describe pre-census samples, not continuous trajectory extrema.
    """
    initial = np.asarray(y0, dtype=float).copy()
    if initial.shape != (5,) or np.any(~np.isfinite(initial)) or np.any(initial < 0):
        raise ValueError("Provide five finite nonnegative physical stocks")
    if not np.isfinite(years) or years < 0:
        raise ValueError("Duration must be finite and nonnegative")
    if not isinstance(sample_every_censuses, (int, np.integer)) or sample_every_censuses < 1:
        raise ValueError("Sampling stride must be a positive integer")
    immigration_cells = np.asarray(process.immigration_cells_yr, dtype=float)
    if any(not enabled and (initial[i + 1] != 0 or immigration_cells[i] != 0)
           for i, enabled in enumerate(p.enabled)):
        raise ValueError("Disabled guilds must start absent and receive no immigrants")
    volume = p.habitat_l_cm2 * process.surface_cm2
    if not np.isfinite(volume) or volume <= 0:
        raise ValueError("Total active habitat volume must be positive and representable")
    immigration = immigration_cells * process.cell_mass_gdw / volume
    if np.any((immigration_cells > 0) & (immigration == 0)):
        raise ValueError("Immigration density is below numerical representation")
    allocation = np.array([g.assimilation_mol_g for g in core.activity_guilds(initial, p)])
    cell_log_conversion = np.log(volume) - np.log(process.cell_mass_gdw)
    floor_log_density = np.log(process.minimum_cells) - cell_log_conversion if process.minimum_cells else -np.inf
    modes = np.where(immigration > 0, 2, np.where(initial[1:3] > 0, 1, 0))
    events, arrivals, flags = [], [], []
    minimum_logs = np.full(2, np.inf)
    culled_mass = np.zeros(2)
    culled_cells = np.zeros(2)
    culled_electrons = np.zeros(2)
    first = [None, None]
    previous_present = np.zeros(2, dtype=bool)
    evaluations = resets = 0

    def decode(internal):
        physical = np.asarray(internal).copy()
        logs = np.full(2, -np.inf)
        for i, mode in enumerate(modes):
            z = internal[i + 1]
            if mode == 0:
                physical[i + 1] = 0.
            elif mode == 1:
                physical[i + 1] = BIOMASS_SCALE * np.logaddexp(0., z)
                logs[i] = np.log(BIOMASS_SCALE) + (z if z < -30 else np.log(np.logaddexp(0., z)))
            else:
                stock = immigration[i] * z
                physical[i + 1] = stock
                if stock > 0:
                    logs[i] = np.log(stock)
        return physical, logs

    def encode(physical):
        internal = physical.copy()
        for i, mode in enumerate(modes):
            if mode == 0:
                internal[i + 1] = 0.
            elif mode == 1:
                internal[i + 1] = _inverse_softplus(physical[i + 1] / BIOMASS_SCALE)
            else:
                internal[i + 1] = physical[i + 1] / immigration[i]
                if not np.isfinite(internal[i + 1]):
                    raise ValueError("Immigration is too small to represent the initial stock in scaled coordinates")
        return internal

    def derivatives(_, internal):
        nonlocal evaluations
        evaluations += 1
        physical, _ = decode(internal)
        rates = core.rhs(physical, p)
        growth = core.fluxes(physical, p)["net_growth_yr"]
        for i, mode in enumerate(modes):
            z = internal[i + 1]
            if mode == 0:
                rates[i + 1] = 0.
            elif mode == 1:
                rates[i + 1] = growth[i] * (1. if z < -30 else np.logaddexp(0., z) / expit(z))
            else:
                rates[i + 1] = growth[i] * z + 1.
        return rates

    def census(time, physical, logs, *, initial_census=False):
        nonlocal previous_present
        minimum_logs[:] = np.minimum(minimum_logs, logs + cell_log_conversion)
        changed = False
        for i in range(2):
            # A roundoff guard prevents an exact threshold from toggling on conversion.
            if modes[i] and logs[i] < floor_log_density - 1e-12:
                if not np.isfinite(logs[i]):
                    continue  # Already absent; mean immigration is not a counted arrival.
                mass = float(max(physical[i + 1], 0.) * volume)
                cells = float(np.exp(logs[i] + cell_log_conversion))
                electrons = float(mass * allocation[i])
                events.append(dict(time_yr=float(time), guild=GUILDS[i],
                                   reason="initial_below_floor" if initial_census else "census_below_floor",
                                   removed_cells=cells, log_removed_cells=float(logs[i] + cell_log_conversion),
                                   removed_gdw=mass, removed_h2_mol=electrons))
                culled_mass[i] += mass
                culled_cells[i] += cells
                culled_electrons[i] += electrons
                if first[i] is None:
                    first[i] = float(time)
                physical[i + 1], logs[i] = 0., -np.inf
                if immigration[i] == 0:
                    modes[i] = 0
                changed = True
        present = np.isfinite(logs)
        if not initial_census:
            for i in range(2):
                if present[i] and not previous_present[i]:
                    arrivals.append(dict(time_yr=float(time), guild=GUILDS[i],
                                         retained_cells=float(np.exp(logs[i] + cell_log_conversion)),
                                         log_retained_cells=float(logs[i] + cell_log_conversion)))
        previous_present = present
        flags.append(int(present[0]) | (int(present[1]) << 1))
        return changed

    initial_logs = np.full(2, -np.inf)
    np.log(initial[1:3], out=initial_logs, where=initial[1:3] > 0)
    census(0., initial, initial_logs, initial_census=True)
    internal = encode(initial)
    times, samples, sample_logs = [0.], [initial.copy()], [initial_logs.copy()]

    def make_solver(state, time):
        return ode(derivatives).set_integrator("lsoda", rtol=2e-8,
            atol=[1e-7, 1e-8, 1e-8, 1e-11, 1e-11], nsteps=100000).set_initial_value(state, time)

    started = perf_counter()
    solver = make_solver(internal, 0.) if years else None
    n_censuses = int(np.floor(years / process.census_yr))
    time_tolerance = 16 * np.finfo(float).eps * max(1., years)
    if abs((n_censuses + 1) * process.census_yr - years) <= time_tolerance:
        n_censuses += 1
    last_census = 0.
    for k in range(1, n_censuses + 1):
        scheduled = k * process.census_yr
        time = years if abs(scheduled - years) <= time_tolerance else scheduled
        internal = solver.integrate(time)
        if not solver.successful() or np.any(~np.isfinite(internal)):
            raise RuntimeError(f"Finite population integration failed before census {k}")
        physical, logs = decode(internal)
        if np.any(physical[1:3] < 0):
            raise RuntimeError("Immigrant population coordinate crossed its physical boundary")
        changed = census(time, physical, logs)
        if changed:
            internal = encode(physical)
            solver = make_solver(internal, time)
            resets += 1
        last_census = time
        if k % sample_every_censuses == 0 or time == years:
            times.append(float(time))
            samples.append(physical.copy())
            sample_logs.append(logs.copy())
    if years > last_census:
        internal = solver.integrate(years)
        if not solver.successful() or np.any(~np.isfinite(internal)):
            raise RuntimeError("Finite population integration failed in final partial interval")
        physical, logs = decode(internal)
        if np.any(physical[1:3] < 0):
            raise RuntimeError("Immigrant population coordinate crossed its physical boundary")
        times.append(float(years))
        samples.append(physical.copy())
        sample_logs.append(logs.copy())
    elif years and times[-1] != years:
        physical, logs = decode(internal)
        times.append(float(years))
        samples.append(physical.copy())
        sample_logs.append(logs.copy())
    imported_cells = immigration_cells * years
    ledger = dict(immigrant_cells=imported_cells, immigrant_gdw=imported_cells * process.cell_mass_gdw,
                  immigrant_h2_mol=imported_cells * process.cell_mass_gdw * allocation,
                  culled_cells=culled_cells, culled_gdw=culled_mass, culled_h2_mol=culled_electrons)
    return FiniteResult(
        np.asarray(times), np.asarray(samples).T, np.asarray(sample_logs).T, np.asarray(flags, dtype=np.uint8),
        events, arrivals, ledger, np.exp(minimum_logs), minimum_logs,
        min((x for x in first if x is not None), default=None), tuple(first),
        dict(total_habitat_l=float(volume), immigration_gdw_l_yr=immigration,
             cell_mass_gdw=process.cell_mass_gdw, surface_cm2=process.surface_cm2,
             minimum_cells=process.minimum_cells, census_yr=process.census_yr,
             census_log_roundoff_tolerance=1e-12,
             n_censuses=len(flags), last_census_yr=float(last_census),
             sample_every_censuses=sample_every_censuses, solver_resets=resets, nfev=evaluations,
             wall_seconds=perf_counter() - started,
             census_order="Continuous mean immigration; at t=0 and scheduled censuses remove below-floor guilds; then report",
             minimum_scope="Pre-census samples including initial stocks, not continuous extrema",
             arrival_scope="First retained-at-census stock following census absence; not stochastic arrivals",
             immigration_coordinate="Linear biomass divided by one year's mean immigration density; no stock clipping",
             cell_process="Assumed deterministic census and mean immigration, not empirical extinction probabilities"),
    )
