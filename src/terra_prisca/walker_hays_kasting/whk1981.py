"""Walker, Hays & Kasting (1981): the silicate-weathering thermostat.

J. Geophys. Res. 86(C10), 9776-9782, doi:10.1029/JC086iC10p09776.

Two algebraic balances, both written as departures from today's state
(T_s = 285 K, T_e = 253 K, P = P0, V = V0):

  eq. (1)  W/W0 = (P/P0)^0.3 exp(dT/13.7)              weathering
  eq. (2)  P/P0 = (V/V0)^(10/3) exp(-dT/4.11)          W = V, solved for P
  eq. (6)  dT   = 2 dTe + 4.6 (P/P0)^0.364 - 4.6       greenhouse, from (3)-(5)

Given the external factors dTe and V/V0, eqs (2) and (6) fix dT and P. The
paper has no time dependence; neither does this module.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy.optimize import brentq

TS0 = 285.0  # present global mean surface temperature, K (Sellers 1965)
TE0 = 253.0  # present effective temperature, K (Goody & Walker 1972)


@dataclass(frozen=True)
class Reading:
    """One reading of the paper's constants. The default is the faithful one:
    eqs (2) and (6) exactly as printed."""

    name: str = "faithful"
    co2_exponent: float = 0.3      # weathering ~ P^0.3 (Lagache)
    efold_K: float = 13.7          # combined temperature e-folding of weathering, eq. (1)
    p_efold_K: float | None = 4.11  # e-folding of P in eq. (2); None means efold_K * co2_exponent
    v_exponent: float | None = 10 / 3  # exponent of V/V0 in eq. (2); None means 1/co2_exponent
    gh_exponent: float = 0.364     # eq. (5): Tg(CO2) = gh_coeff (P/P0)^gh_exponent
    gh_coeff: float = 2.3
    h2o_slope: float = 0.5         # eq. (4): Tg(H2O) = 29.7 + h2o_slope (Ts - 285)
    perfect_thermostat: bool = False  # control: weathering independent of P
    fixed_p: bool = False             # control: no feedback, P held at P0

    @property
    def p_efold(self) -> float:
        return self.p_efold_K if self.p_efold_K is not None else self.efold_K * self.co2_exponent

    @property
    def v_exp(self) -> float:
        return self.v_exponent if self.v_exponent is not None else 1.0 / self.co2_exponent

    @property
    def te_gain(self) -> float:
        """dTs/dTe at fixed P: 1/(1 - h2o_slope), printed as 2 in eq. (6)."""
        return 1.0 / (1.0 - self.h2o_slope)

    @property
    def gh_amp(self) -> float:
        """Coefficient of (P/P0)^gh_exponent in eq. (6): gh_coeff/(1 - h2o_slope), printed as 4.6."""
        return self.gh_coeff / (1.0 - self.h2o_slope)


FAITHFUL = Reading()


def weathering_ratio(p_ratio, dT, r: Reading = FAITHFUL):
    """Eq. (1): W/W0."""
    return np.asarray(p_ratio, float) ** r.co2_exponent * np.exp(np.asarray(dT, float) / r.efold_K)


def co2_ratio(v_ratio, dT, r: Reading = FAITHFUL):
    """Eq. (2): P/P0 that balances weathering against the source V/V0 at dT."""
    return np.asarray(v_ratio, float) ** r.v_exp * np.exp(-np.asarray(dT, float) / r.p_efold)


def surface_dT(dTe, p_ratio, r: Reading = FAITHFUL):
    """Eq. (6): dT = Ts - 285 K for a given dTe = Te - 253 K and P/P0."""
    return r.te_gain * np.asarray(dTe, float) + r.gh_amp * (np.asarray(p_ratio, float) ** r.gh_exponent - 1.0)


def equilibrium(dTe: float, v_ratio: float = 1.0, r: Reading = FAITHFUL) -> tuple[float, float]:
    """(dT, P/P0) satisfying eqs (2) and (6) together.

    g(dT) = dT - surface_dT(dTe, co2_ratio(v, dT)) is strictly increasing in dT
    (the CO2 term falls as dT rises), so the root is unique."""
    if r.fixed_p:
        return float(surface_dT(dTe, 1.0, r)), 1.0
    if r.perfect_thermostat:
        dT = r.efold_K * np.log(v_ratio)
        p = ((dT - r.te_gain * dTe) / r.gh_amp + 1.0)
        return float(dT), float(p ** (1.0 / r.gh_exponent)) if p > 0 else float("nan")

    def g(dT):
        return dT - surface_dT(dTe, co2_ratio(v_ratio, dT, r), r)

    lo, hi = -200.0, 200.0
    dT = brentq(g, lo, hi, xtol=1e-12, rtol=1e-14, maxiter=200)
    return float(dT), float(co2_ratio(v_ratio, dT, r))


def sweep(dTe: np.ndarray, v_ratio: float, r: Reading = FAITHFUL) -> np.ndarray:
    """Columns dTe, dT, P/P0 along a sweep of effective temperature."""
    out = np.array([equilibrium(float(x), v_ratio, r) for x in dTe])
    return np.column_stack([dTe, out])


def sensitivity(dTe: float, v_ratio: float = 1.0, r: Reading = FAITHFUL) -> float:
    """d(dT)/d(dTe) on the equilibrium curve, by implicit differentiation.

    Without feedback it is te_gain (2 K/K); the feedback divides it by
    1 + gh_amp * gh_exponent * (P/P0)^gh_exponent / p_efold."""
    dT, p = equilibrium(dTe, v_ratio, r)
    return r.te_gain / (1.0 + r.gh_amp * r.gh_exponent * p ** r.gh_exponent / r.p_efold)


def dTe_from_luminosity(l_ratio, te0: float = TE0):
    """Te scales as the fourth root of solar luminosity at fixed albedo (p. 9780)."""
    return te0 * (np.asarray(l_ratio, float) ** 0.25 - 1.0)


def doubling_warming(r: Reading = FAITHFUL) -> float:
    """Eq. (6) at fixed Te: warming for P/P0 going from 1 to 2."""
    return float(r.gh_amp * (2.0 ** r.gh_exponent - 1.0))


# Derivations of the printed constants from the quantities the text gives.
ARRHENIUS_K = 4600.0   # Lagache: exp(-4600/T)
RUNOFF_EFOLD_K = 60.0  # Manabe and colleagues: R ~ exp((T-285)/60)
PRECIP_EFOLD_K = 14.1  # Sellers (1965) precipitation, not adopted


def arrhenius_efold(T: float = TS0, E: float = ARRHENIUS_K) -> float:
    """Local e-folding of exp(-E/T) at T: T^2/E."""
    return T * T / E


def combined_efold(direct: float, runoff: float) -> float:
    return 1.0 / (1.0 / direct + 1.0 / runoff)


def unrounded() -> Reading:
    """Every constant recomputed from its stated ingredients, unrounded."""
    direct = arrhenius_efold()
    efold = combined_efold(direct, RUNOFF_EFOLD_K)
    return Reading(name="unrounded constants", efold_K=efold, p_efold_K=None, v_exponent=None)


READINGS = {
    "faithful": FAITHFUL,
    "unrounded": unrounded(),
    "no_runoff": Reading(name="direct temperature only (17.7 K)", efold_K=17.7, p_efold_K=None, v_exponent=None),
    "precip_runoff": Reading(name="runoff following precipitation (14.1 K)",
                             efold_K=combined_efold(17.7, PRECIP_EFOLD_K), p_efold_K=None, v_exponent=None),
    "no_h2o": Reading(name="no water-vapour amplification", h2o_slope=0.0),
}

CONTROLS = {
    "no_feedback": replace(FAITHFUL, name="null: no feedback (P = P0)", fixed_p=True),
    "thermostat": replace(FAITHFUL, name="null: perfect thermostat (W independent of P)", perfect_thermostat=True),
}
