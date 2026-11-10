"""N microbial habitats with tracking or buffered temperatures and shared CH4.

State: four local stocks [p, XA, XM, acetate] per patch, then atmospheric r.
Units and local metabolism are those of population_coupling; time is years.
"""

from dataclasses import dataclass, field

import numpy as np

from . import population_coupling as core
from .methane_budget import response, temperature_k
from .two_guilds import HENRY_30C_MOL_L_PA

MEASURED_K = (277.15, 303.15)


@dataclass(frozen=True)
class Patch:
    name: str
    weight: float
    rule: str = "tracking"
    value: float = 0.

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Each patch needs a nonempty name")
        if not np.isfinite(self.weight) or self.weight < 0:
            raise ValueError("Patch weights must be finite and nonnegative")
        if self.rule not in ("tracking", "buffered") or not np.isfinite(self.value):
            raise ValueError("Use a tracking offset or a finite buffered temperature")


@dataclass(frozen=True)
class Habitats:
    base: core.Coupled = field(default_factory=core.reference)
    patches: tuple[Patch, ...] = field(default_factory=lambda: (Patch("bulk", 1.),))
    dispersal_yr: float = 0.

    def __post_init__(self):
        object.__setattr__(self, "patches", tuple(self.patches))
        if not self.patches or not all(isinstance(p, Patch) for p in self.patches):
            raise ValueError("Provide at least one Patch")
        if len(set(self.patch_names)) != self.n_patches:
            raise ValueError("Patch names must be unique")
        if not np.isclose(sum(p.weight for p in self.patches), 1., rtol=0., atol=1e-12):
            raise ValueError("Patch weights must sum to one")
        if not np.isfinite(self.dispersal_yr) or self.dispersal_yr < 0:
            raise ValueError("Dispersal must be finite and nonnegative")

    @property
    def weights(self):
        return np.array([patch.weight for patch in self.patches])

    @property
    def n_patches(self):
        return len(self.patches)

    @property
    def state_size(self):
        return 4 * self.n_patches + 1

    @property
    def biomass_indices(self):
        return 4 * np.arange(self.n_patches)[:, None] + np.array([1, 2])

    @property
    def patch_names(self):
        return tuple(patch.name for patch in self.patches)


def _state(y, p):
    y = np.asarray(y, dtype=float)
    if y.shape != (p.state_size,):
        raise ValueError(f"{p.n_patches} habitats require {p.state_size} stocks")
    return y


def temperatures(y, p):
    global_t = float(temperature_k(_state(y, p)[-1], p.base.climate))
    return np.array([global_t + patch.value if patch.rule == "tracking" else patch.value
                     for patch in p.patches])


def physiology_bounds(p):
    return (277.15 if p.base.biology.low_temperature_variant == "none" else 273.), 303.15


def temperature_flags(y, p):
    low, high = physiology_bounds(p)
    return ["inactive" if patch.weight == 0 else "unsupported" if not low <= t <= high
            else "measured" if MEASURED_K[0] <= t <= MEASURED_K[1] else "cold_continuation"
            for patch, t in zip(p.patches, temperatures(y, p))]


def local_state(y, patch):
    return np.r_[np.asarray(y)[4 * patch:4 * patch + 4], y[-1]]


def embed_single(y, p):
    single = np.asarray(y, dtype=float)
    if single.shape != (5,):
        raise ValueError("A single-habitat state has five stocks")
    return np.r_[*[single[:4] if patch.weight > 0 else np.zeros(4) for patch in p.patches], single[4]]


def fluxes(y, p, *, trial_extension=False):
    """Evaluate physical local fluxes; boundary freezing is trial-only."""
    y = _state(y, p)
    ts = temperatures(y, p)
    bounds = physiology_bounds(p)
    local = []
    for j, patch in enumerate(p.patches):
        if patch.weight == 0:
            local.append(None)
            continue
        t = float(np.clip(ts[j], *bounds)) if trial_extension else float(ts[j])
        local.append(core.fluxes_at_temperature(local_state(y, j), p.base, t))
    exchange = np.zeros((p.n_patches, 2))
    stocks = y[p.biomass_indices]
    for j, patch in enumerate(p.patches):
        if patch.weight:
            for k, source in enumerate(p.patches):
                if k != j and source.weight:
                    exchange[j] += p.dispersal_yr * source.weight * (stocks[k] - stocks[j])
    exchange *= p.base.enabled
    first = next(f for f in local if f is not None)
    local_methane = sum(w * f["methane_local_mol_l_yr"] for w, f in zip(p.weights, local) if f is not None)
    source = core.inventory_to_ratio(p.base) * local_methane + first["abiotic_ratio_yr"]
    global_t = float(temperature_k(y[-1], p.base.climate))
    mean_t = float(p.weights @ ts)
    return dict(local=local, temperatures_k=ts, global_temperature_k=global_t,
                mean_habitat_temperature_k=mean_t, temperature_mean_departure_k=mean_t-global_t,
                physiology_domains=temperature_flags(y, p), climate_domain=first["climate_domain"],
                exchange_gdw_l_yr=exchange, methane_source_ratio_yr=float(source),
                methane_loss_ratio_yr=first["methane_loss_ratio_yr"], abiotic_ratio_yr=first["abiotic_ratio_yr"])


def rhs(y, p, *, trial_extension=False):
    y = _state(y, p)
    f = fluxes(y, p, trial_extension=trial_extension)
    result = np.zeros(p.state_size)
    for j, local in enumerate(f["local"]):
        if local is None:
            continue
        start = 4 * j
        result[start] = (local["supply_h2_mol_l_yr"] - sum(local["uptake_h2_mol_l_yr"])
                         - local["outlet_h2_mol_l_yr"]) / HENRY_30C_MOL_L_PA
        result[start+1:start+3] = (y[start+1:start+3] * local["net_growth_yr"] * p.base.enabled
                                   + f["exchange_gdw_l_yr"][j])
        result[start+3] = (local["acetate_production_mol_l_yr"] - local["acetate_recycling_mol_l_yr"]
                           - local["acetate_export_mol_l_yr"])
    result[-1] = f["methane_source_ratio_yr"] - f["methane_loss_ratio_yr"]
    return result


def inventory(y, p):
    y = _state(y, p)
    total = 4 * y[-1] / core.inventory_to_ratio(p.base)
    for j, (weight, t) in enumerate(zip(p.weights, temperatures(y, p))):
        if weight:
            state = local_state(y, j)
            pair = core.activity_guilds_at_temperature(state, p.base, float(t))
            coefficients = [guild.assimilation_mol_g for guild in pair]
            total += weight * (HENRY_30C_MOL_L_PA * state[0] + np.dot(coefficients, state[1:3]) + 4 * state[3])
    return float(total)


def redox_residual(y, p):
    f, rates = fluxes(y, p), rhs(y, p)
    stored = 4 * rates[-1] / core.inventory_to_ratio(p.base)
    external = 4 * (f["abiotic_ratio_yr"] - f["methane_loss_ratio_yr"]) / core.inventory_to_ratio(p.base)
    for j, (weight, local) in enumerate(zip(p.weights, f["local"])):
        if local is None:
            continue
        pair = core.activity_guilds_at_temperature(local_state(y, j), p.base, float(f["temperatures_k"][j]))
        coefficients = [guild.assimilation_mol_g for guild in pair]
        stored += weight * (HENRY_30C_MOL_L_PA * rates[4*j] + np.dot(coefficients, rates[4*j+1:4*j+3])
                            + 4 * rates[4*j+3])
        external += weight * (local["supply_h2_mol_l_yr"] - local["outlet_h2_mol_l_yr"]
                              - 4 * local["acetate_export_mol_l_yr"] - sum(local["biomass_export_h2_mol_l_yr"]))
    return float(stored-external)


def active_indices(p):
    return [*[4*j+k for j, patch in enumerate(p.patches) if patch.weight > 0
              for k in (0, *[i+1 for i, enabled in enumerate(p.base.enabled) if enabled], 3)], p.state_size-1]


def jacobian(y, p, *, r_side=0):
    y = _state(y, p)
    scales = np.maximum(abs(y), np.r_[np.tile([10., 1e-4, 1e-4, 1e-5], p.n_patches), .01])
    center = rhs(y, p)
    matrix = np.empty((p.state_size, p.state_size))
    for j in range(p.state_size):
        step = scales[j] * 1e-5
        delta = np.eye(p.state_size)[j] * step
        if j == p.state_size-1 and r_side:
            derivative = (rhs(y+r_side*delta, p)-center)/(r_side*step)
        else:
            derivative = (rhs(y+delta, p)-rhs(y-delta, p))/(2*step)
        matrix[:, j] = derivative * scales[j] / scales
    active = active_indices(p)
    return matrix[np.ix_(active, active)]


def supported_ratio_intervals(p):
    """Connected closed intervals of nonnegative r with defined physiology.

    Boundary roots use the named logarithmic bridge, piecewise-linear source
    curve and constant high-r plateau; no new radiative continuation is added.
    """
    low, high = physiology_bounds(p)
    tracking = []
    for patch in p.patches:
        if patch.weight == 0:
            continue
        if patch.rule == "buffered":
            if not low <= patch.value <= high:
                return []
        else:
            tracking.append(patch.value)
    if not tracking:
        return [[0., np.inf]]
    minimum, maximum = max(low-offset for offset in tracking), min(high-offset for offset in tracking)
    if minimum > maximum:
        return []
    curve = response(p.base.climate.case)
    ratios, ts = curve.ratios, curve.temperatures_k
    knots = [0., *ratios]
    zero_t = p.base.climate.t_zero_k
    for boundary in (minimum, maximum):
        if zero_t != ts[0] and min(zero_t, ts[0]) <= boundary <= max(zero_t, ts[0]):
            fraction = (boundary-zero_t)/(ts[0]-zero_t)
            knots.append(p.base.climate.bridge_scale * np.expm1(
                fraction * np.log1p(ratios[0]/p.base.climate.bridge_scale)))
        for a, b, ta, tb in zip(ratios[:-1], ratios[1:], ts[:-1], ts[1:]):
            if ta != tb and min(ta, tb) <= boundary <= max(ta, tb):
                knots.append(a+(boundary-ta)*(b-a)/(tb-ta))
    knots = sorted(set(float(x) for x in knots if x >= 0 and np.isfinite(x)))
    candidates = []
    for a, b in zip(knots, [*knots[1:], np.inf]):
        middle = (a+b)/2 if np.isfinite(b) else a+max(1., a)
        t = float(temperature_k(middle, p.base.climate))
        if minimum <= t <= maximum:
            candidates.append([a, b])
    for point in knots:
        if minimum <= float(temperature_k(point, p.base.climate)) <= maximum:
            if not any(a <= point <= b for a, b in candidates):
                candidates.append([point, point])
    result = []
    for a, b in sorted(candidates):
        if result and a <= result[-1][1]:
            result[-1][1] = max(result[-1][1], b)
        else:
            result.append([a, b])
    return result
