"""Active and dormant microbial pools under one methane atmosphere.

State per habitat: [H2 pressure, active A, active M, acetate, dormant A,
dormant M], followed by shared CH4/CO2. Biomass is gDW/L; time is years.
"""

from dataclasses import dataclass, field

import numpy as np

from . import habitat_coupling as habitat
from . import population_coupling as core


@dataclass(frozen=True)
class Dormancy:
    base: habitat.Habitats = field(default_factory=habitat.Habitats)
    epsilon: float = .01
    switching_factor: float = 10.
    ramp: str = "cubic"

    def __post_init__(self):
        if not isinstance(self.base, habitat.Habitats):
            raise ValueError("Dormancy requires a Habitats model")
        if not np.isfinite(self.epsilon) or self.epsilon < 0:
            raise ValueError("Dormant loss fraction must be finite and nonnegative")
        if not np.isfinite(self.switching_factor) or self.switching_factor < 0:
            raise ValueError("Switching factor must be finite and nonnegative")
        if self.ramp not in ("cubic","linear"):
            raise ValueError("Use the cubic or linear switching ramp")

    @property
    def coupled(self): return self.base.base

    @property
    def n_patches(self): return self.base.n_patches

    @property
    def weights(self): return self.base.weights

    @property
    def patches(self): return self.base.patches

    @property
    def patch_names(self): return self.base.patch_names

    @property
    def dispersal_yr(self): return self.base.dispersal_yr

    @property
    def state_size(self): return 6*self.n_patches+1

    @property
    def biomass_indices(self): return 6*np.arange(self.n_patches)[:, None]+[1, 2]

    @property
    def dormant_indices(self): return 6*np.arange(self.n_patches)[:, None]+[4, 5]


def _state(y, p):
    y = np.asarray(y, dtype=float)
    if y.shape != (p.state_size,): raise ValueError("Wrong dormancy state size")
    return y


def active_state(y, p):
    y = _state(y, p)
    return np.r_[y[:-1].reshape(p.n_patches, 6)[:, :4].ravel(), y[-1]]


def reference_state(y, p):
    y = np.asarray(y, dtype=float)
    if y.shape != (p.base.state_size,): raise ValueError("Wrong reference state size")
    local = np.zeros((p.n_patches, 6)); local[:, :4] = y[:-1].reshape(p.n_patches, 4)
    return np.r_[local.ravel(), y[-1]]


def temperatures(y, p): return habitat.temperatures(active_state(y, p), p.base)


def temperature_flags(y, p): return habitat.temperature_flags(active_state(y, p), p.base)


def supported_ratio_intervals(p): return habitat.supported_ratio_intervals(p.base)


def local_state(y, patch):
    return np.r_[np.asarray(y)[6*patch:6*patch+4], y[-1]]


def switching_response(value,ramp="cubic"):
    """Clipped smoothstep (default) or the separately named linear control."""
    x=np.clip(value,0.,1.)
    if ramp=="cubic":return x*x*(3-2*x)
    if ramp=="linear":return x
    raise ValueError("Unknown switching ramp")


def fluxes(y, p, *, trial_extension=False):
    y = _state(y, p)
    old = active_state(y, p)
    f = habitat.fluxes(old, p.base, trial_extension=trial_extension)
    net = np.zeros((p.n_patches, 2))
    for j, local in enumerate(f["local"]):
        if local is not None: net[j] = local["net_growth_yr"]
    loss = p.coupled.biology.loss_h*core.HOURS_PER_YEAR
    sigma = p.switching_factor*loss*switching_response(-net/loss,p.ramp)
    rho = p.switching_factor*loss*switching_response(net/loss,p.ramp)
    enabled = np.asarray(p.coupled.enabled)
    sigma *= enabled; rho *= enabled
    sigma[p.weights == 0] = 0.; rho[p.weights == 0] = 0.
    dormant = y[p.dormant_indices]
    exchange = np.zeros_like(dormant)
    for j, wj in enumerate(p.weights):
        if wj:
            for k, wk in enumerate(p.weights):
                if k != j and wk:
                    exchange[j] += p.dispersal_yr*wk*(dormant[k]-dormant[j])
    exchange *= enabled
    return f | dict(net_growth_yr=net, sigma_yr=sigma, rho_yr=rho,
        dormant_loss_yr=p.epsilon*loss, dormant_exchange_gdw_l_yr=exchange)


def rhs(y, p, *, trial_extension=False):
    y = _state(y, p); f = fluxes(y, p, trial_extension=trial_extension)
    return _rhs_from_fluxes(y,p,f)


def _rhs_from_fluxes(y,p,f):
    result = np.zeros(p.state_size)
    for j,local in enumerate(f["local"]):
        if local is None:continue
        a=6*j
        result[a]=(local["supply_h2_mol_l_yr"]-sum(local["uptake_h2_mol_l_yr"])-local["outlet_h2_mol_l_yr"])/core.HENRY_30C_MOL_L_PA
        result[a+1:a+3]=y[a+1:a+3]*local["net_growth_yr"]*p.coupled.enabled+f["exchange_gdw_l_yr"][j]
        result[a+3]=local["acetate_production_mol_l_yr"]-local["acetate_recycling_mol_l_yr"]-local["acetate_export_mol_l_yr"]
    result[-1] = f["methane_source_ratio_yr"]-f["methane_loss_ratio_yr"]
    active, dormant = y[p.biomass_indices], y[p.dormant_indices]
    conversion = f["sigma_yr"]*active-f["rho_yr"]*dormant
    result[p.biomass_indices] -= conversion
    result[p.dormant_indices] = (conversion-f["dormant_loss_yr"]*dormant
                                 +f["dormant_exchange_gdw_l_yr"])*p.coupled.enabled
    return result


def inventory(y, p):
    coefficients = np.array([core.ASSIMILATION_A, p.coupled.biology.assimilation_m])
    return habitat.inventory(active_state(y, p), p.base)+float(p.weights @ (y[p.dormant_indices] @ coefficients))


def redox_residual(y, p):
    f, rates = fluxes(y, p), rhs(y, p)
    coefficients = np.array([core.ASSIMILATION_A, p.coupled.biology.assimilation_m])
    conversion = core.inventory_to_ratio(p.coupled)
    stored = 4*rates[-1]/conversion
    external = 4*(f["abiotic_ratio_yr"]-f["methane_loss_ratio_yr"])/conversion
    for j, (w, local) in enumerate(zip(p.weights, f["local"])):
        if local is None: continue
        a = 6*j
        stored += w*(core.HENRY_30C_MOL_L_PA*rates[a]
            + coefficients @ (rates[a+1:a+3]+rates[a+4:a+6])+4*rates[a+3])
        external += w*(local["supply_h2_mol_l_yr"]-local["outlet_h2_mol_l_yr"]
            -4*local["acetate_export_mol_l_yr"]-sum(local["biomass_export_h2_mol_l_yr"])
            -f["dormant_loss_yr"]*float(coefficients @ y[a+4:a+6]))
    return float(stored-external)
