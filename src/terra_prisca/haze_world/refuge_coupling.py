"""Two local microbial habitats and one atmospheric methane inventory.

State: [p_c, XA_c, XM_c, acetate_c, p_w, XA_w, XM_w, acetate_w, r].
Local physical units match population_coupling; time is years.
"""

from dataclasses import dataclass, field

import numpy as np

from . import population_coupling as core
from .methane_budget import temperature_k
from .two_guilds import HENRY_30C_MOL_L_PA

BIOMASS_INDICES = np.array([[1, 2], [5, 6]])
MEASURED_K = (277.15, 303.15)


@dataclass(frozen=True)
class Refuge:
    base: core.Coupled = field(default_factory=core.reference)
    warm_fraction: float = .5
    contrast_k: float = 0.
    dispersal_yr: float = 0.

    def __post_init__(self):
        if not np.isfinite(self.warm_fraction) or not 0 <= self.warm_fraction <= 1:
            raise ValueError("Warm area fraction must lie between zero and one")
        if not all(np.isfinite(x) and x >= 0 for x in (self.contrast_k, self.dispersal_yr)):
            raise ValueError("Contrast and dispersal must be finite and nonnegative")

    @property
    def weights(self):
        return np.array([1 - self.warm_fraction, self.warm_fraction])

    @property
    def offsets(self):
        return self.contrast_k * np.array([-self.warm_fraction, 1 - self.warm_fraction])


def temperatures(y, p):
    return float(temperature_k(y[8], p.base.climate)) + p.offsets


def physiology_bounds(p):
    low = 277.15 if p.base.biology.low_temperature_variant == "none" else 273.
    return low, 303.15


def temperature_flags(y, p):
    bounds = physiology_bounds(p)
    return ["inactive" if w == 0 else "unsupported" if not bounds[0] <= t <= bounds[1]
            else "measured" if MEASURED_K[0] <= t <= MEASURED_K[1] else "cold_continuation"
            for t, w in zip(temperatures(y, p), p.weights)]


def local_state(y, patch):
    return np.r_[np.asarray(y)[4 * patch:4 * patch + 4], y[8]]


def embed_single(y, p):
    single = np.asarray(y, dtype=float)
    if single.shape != (5,):
        raise ValueError("A single-habitat state has five stocks")
    blocks = [single[:4] if w > 0 else np.zeros(4) for w in p.weights]
    return np.r_[*blocks, single[4]]


def fluxes(y, p, *, trial_extension=False):
    """Evaluate local physics; extension is only for numerical exit detection.

    Public physical evaluation rejects undefined temperatures. Integrators may
    extend a solver trial by freezing boundary physiology, then stop accepted
    trajectories at the first supported-domain exit.
    """
    y = np.asarray(y, dtype=float)
    if y.shape != (9,):
        raise ValueError("Two habitats require nine stocks")
    ts = temperatures(y, p)
    bounds = physiology_bounds(p)
    local = []
    for j, w in enumerate(p.weights):
        if w == 0:
            local.append(None)
            continue
        t = float(np.clip(ts[j], *bounds)) if trial_extension else float(ts[j])
        local.append(core.fluxes_at_temperature(local_state(y, j), p.base, t))
    exchange = np.zeros((2, 2))
    if np.all(p.weights > 0):
        stocks = y[BIOMASS_INDICES]
        exchange[0] = p.dispersal_yr * p.weights[1] * (stocks[1] - stocks[0])
        exchange[1] = p.dispersal_yr * p.weights[0] * (stocks[0] - stocks[1])
        exchange *= p.base.enabled
    first = next(f for f in local if f is not None)
    local_methane = sum(w * f["methane_local_mol_l_yr"] for w, f in zip(p.weights, local) if f is not None)
    source = core.inventory_to_ratio(p.base) * local_methane + first["abiotic_ratio_yr"]
    return dict(local=local, temperatures_k=ts, global_temperature_k=float(temperature_k(y[8], p.base.climate)),
                physiology_domains=temperature_flags(y, p), climate_domain=first["climate_domain"],
                exchange_gdw_l_yr=exchange, methane_source_ratio_yr=float(source),
                methane_loss_ratio_yr=first["methane_loss_ratio_yr"],
                abiotic_ratio_yr=first["abiotic_ratio_yr"])


def rhs(y, p, *, trial_extension=False):
    f = fluxes(y, p, trial_extension=trial_extension)
    result = np.zeros(9)
    for j, local in enumerate(f["local"]):
        if local is None:
            continue
        start = 4 * j
        result[start] = (local["supply_h2_mol_l_yr"] - sum(local["uptake_h2_mol_l_yr"])
                         - local["outlet_h2_mol_l_yr"]) / HENRY_30C_MOL_L_PA
        result[start + 1:start + 3] = (np.asarray(y)[start + 1:start + 3] * local["net_growth_yr"]
                                      * p.base.enabled + f["exchange_gdw_l_yr"][j])
        result[start + 3] = (local["acetate_production_mol_l_yr"] - local["acetate_recycling_mol_l_yr"]
                             - local["acetate_export_mol_l_yr"])
    result[8] = f["methane_source_ratio_yr"] - f["methane_loss_ratio_yr"]
    return result


def inventory(y, p):
    local = 0.
    for j, w in enumerate(p.weights):
        if w == 0:
            continue
        state = local_state(y, j)
        pair = core.activity_guilds_at_temperature(state, p.base, float(temperatures(y, p)[j]))
        a = np.array([g.assimilation_mol_g for g in pair])
        local += w * (HENRY_30C_MOL_L_PA * state[0] + np.dot(a, state[1:3]) + 4 * state[3])
    return float(local + 4 * y[8] / core.inventory_to_ratio(p.base))


def redox_residual(y, p):
    f, rates = fluxes(y, p), rhs(y, p)
    stored = 4 * rates[8] / core.inventory_to_ratio(p.base)
    external = 4 * (f["abiotic_ratio_yr"] - f["methane_loss_ratio_yr"]) / core.inventory_to_ratio(p.base)
    for j, (w, local) in enumerate(zip(p.weights, f["local"])):
        if local is None:
            continue
        pair = core.activity_guilds_at_temperature(local_state(y, j), p.base, float(f["temperatures_k"][j]))
        a = [g.assimilation_mol_g for g in pair]
        stored += w * (HENRY_30C_MOL_L_PA * rates[4 * j] + np.dot(a, rates[4 * j + 1:4 * j + 3])
                       + 4 * rates[4 * j + 3])
        external += w * (local["supply_h2_mol_l_yr"] - local["outlet_h2_mol_l_yr"]
                          - 4 * local["acetate_export_mol_l_yr"] - sum(local["biomass_export_h2_mol_l_yr"]))
    return float(stored - external)


def active_indices(p):
    return [*[4 * j + k for j, w in enumerate(p.weights) if w > 0
              for k in (0, *[i + 1 for i, enabled in enumerate(p.base.enabled) if enabled], 3)], 8]


def jacobian(y, p, *, r_side=0):
    y = np.asarray(y, dtype=float)
    scales = np.maximum(abs(y), [10., 1e-4, 1e-4, 1e-5, 10., 1e-4, 1e-4, 1e-5, .01])
    center = rhs(y, p)
    matrix = np.empty((9, 9))
    for j in range(9):
        h = scales[j] * 1e-5
        delta = np.eye(9)[j] * h
        if j == 8 and r_side:
            derivative = (rhs(y + r_side * delta, p) - center) / (r_side * h)
        else:
            derivative = (rhs(y + delta, p) - rhs(y - delta, p)) / (2 * h)
        matrix[:, j] = derivative * scales[j] / scales
    active = active_indices(p)
    return matrix[np.ix_(active, active)]
