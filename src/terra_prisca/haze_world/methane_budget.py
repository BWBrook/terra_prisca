"""Draft coupled methanogen-methane-climate budget: the haze-world skeleton.

This is a new model, not a reconstruction. Every closure the published response
curves do not supply is a named, swept assumption; see models/haze_world/README.md.

State: electron-donor pool D, methanogen biomass B and atmospheric methane M, all
expressed as CH4-equivalent columns divided by the CO2 column, so that M is the
surface CH4/CO2 ratio r used by Arney et al. (2016, doi:10.1089/ast.2015.1422).

    dD/dt = phi - k_D D - U,              U = mu(T) B D / (K + D)
    dB/dt = Y U - delta B
    dM/dt = U + phi_abiotic - M / tau
    T     = closure(M)

Biology and the donor pool relax in years and methane in ~10^4 years, so the
biology is quasi-steady on methane time scales. Eliminating D and B gives

    dr/dt = c [eta(T(r)) Phi + Phi_abiotic] - r / tau
    eta   = max(0, 1 - Phi_K / (Phi (rho(T) - 1)))

where Phi is the donor supply as a CH4-equivalent flux, rho = Y mu / delta is
the methanogens' maximum per-capita growth over loss, Phi_K = K k_D is the supply
at which the abiotic donor level equals the half-saturation constant, and c
converts molecules cm-2 s-1 to ratio units per year. eta is the fraction of the
supply that methanogens capture; it is positive exactly when they can invade.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, replace
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from terra_prisca.haze_response.arney2016 import Response

ARNEY_DIR = Path(__file__).resolve().parents[3] / "models/haze_response/arney2016"
SECONDS_PER_YEAR = 3.15576e7
AVOGADRO = 6.02214076e23
GRAVITY = 9.81  # m s-2
AIR_MOLAR_MASS = 0.028  # kg mol-1, N2-dominated background


@dataclass(frozen=True)
class Params:
    case: str = "B"  # Arney et al. (2016) atmosphere: fixed pCO2, pressure, S/S0 = 0.81
    # Methane loss: first-order with lifetime tau. Assumption; Arney's haze-onset
    # flux of 1-3e11 molecules cm-2 s-1 implies 6-19 kyr for case B (see below).
    lifetime_yr: float = 1.0e4
    abiotic_flux: float = 1.3e9  # molecules cm-2 s-1; upper abiotic estimate quoted by Arney
    donor_flux: float = 1.5e11  # Phi: electron-donor supply, CH4-equivalent molecules cm-2 s-1
    maintenance_flux: float = 1.0e10  # Phi_K = K k_D, molecules cm-2 s-1
    growth_ratio_max: float = 10.0  # rho_max = Y mu_max / delta
    t_opt_k: float = 300.0  # thermal performance: rho = rho_max (1 - ((T - T_opt)/w)^2)+
    t_halfwidth_k: float = 20.0
    thermal: bool = True  # False: temperature-independent control, rho = rho_max
    # Low-methane bridge below Arney's first vertex r1 (value-continuous at r1):
    # T = T0 + (T1 - T0) ln(1 + r/s) / ln(1 + r1/s). Above the last vertex: plateau.
    t_zero_k: float = 265.0
    bridge_scale: float = 0.01


@lru_cache(maxsize=None)
def atmosphere(case: str) -> dict[str, float]:
    with (ARNEY_DIR / "cases.csv").open(newline="") as fh:
        row = next(r for r in csv.DictReader(fh) if r["case"] == case)
    pressure_bar = float(row["surface_pressure_bar"])
    f_co2 = float(row["p_co2_bar"]) / pressure_bar
    column = pressure_bar * 1e5 / (AIR_MOLAR_MASS * GRAVITY) * AVOGADRO / 1e4  # molecules cm-2
    return {"f_co2": f_co2, "column": column, "flux_to_ratio_per_yr": SECONDS_PER_YEAR / (column * f_co2)}


@lru_cache(maxsize=None)
def response(case: str) -> Response:
    return Response.from_csv(ARNEY_DIR / "figure4.csv", case)


def domain(r: float | np.ndarray, p: Params) -> np.ndarray:
    resp = response(p.case)
    r = np.asarray(r, dtype=float)
    return np.where(r < resp.ratios[0], "bridge", np.where(r > resp.ratios[-1], "plateau", "arney"))


def temperature_k(r: float | np.ndarray, p: Params, extend: bool = True) -> float | np.ndarray:
    """Surface temperature at CH4/CO2 ratio r. With extend=False only Arney's
    extracted domain is allowed and anything else raises, as Response does."""
    resp = response(p.case)
    r = np.asarray(r, dtype=float)
    if not extend:
        return resp.temperature_k(r)
    lo, hi = resp.ratios[0], resp.ratios[-1]
    t = np.empty_like(r)
    inside = (r >= lo) & (r <= hi)
    t[inside] = resp.temperature_k(r[inside])
    below = r < lo
    t1 = resp.temperatures_k[0]
    s = p.bridge_scale
    t[below] = p.t_zero_k + (t1 - p.t_zero_k) * np.log1p(np.maximum(r[below], 0.0) / s) / np.log1p(lo / s)
    t[r > hi] = resp.temperatures_k[-1]
    return float(t) if t.ndim == 0 else t


def growth_ratio(t_k: float | np.ndarray, p: Params) -> float | np.ndarray:
    if not p.thermal:
        return np.full_like(np.asarray(t_k, dtype=float), p.growth_ratio_max)
    return p.growth_ratio_max * np.maximum(0.0, 1.0 - ((np.asarray(t_k) - p.t_opt_k) / p.t_halfwidth_k) ** 2)


def capture_efficiency(t_k: float | np.ndarray, p: Params) -> float | np.ndarray:
    """eta: fraction of the donor supply converted to methane at quasi-steady state."""
    if p.donor_flux <= 0:
        return np.zeros_like(np.asarray(t_k, dtype=float))
    excess = np.asarray(growth_ratio(t_k, p)) - 1.0
    with np.errstate(divide="ignore"):
        eta = 1.0 - p.maintenance_flux / (p.donor_flux * np.where(excess > 0, excess, np.nan))
    return np.where(np.isfinite(eta) & (eta > 0), eta, 0.0)


def methane_flux(r: float | np.ndarray, p: Params) -> float | np.ndarray:
    """Total CH4 source (molecules cm-2 s-1) when the climate is set by ratio r."""
    return capture_efficiency(temperature_k(r, p), p) * p.donor_flux + p.abiotic_flux


def tendency(r: float | np.ndarray, p: Params) -> float | np.ndarray:
    """dr/dt of the reduced model, per year."""
    c = atmosphere(p.case)["flux_to_ratio_per_yr"]
    return c * methane_flux(r, p) - np.asarray(r) / p.lifetime_yr


def ratio_for_flux(flux: float, p: Params) -> float:
    """Steady CH4/CO2 ratio sustained by a fixed CH4 flux under linear loss."""
    return p.lifetime_yr * atmosphere(p.case)["flux_to_ratio_per_yr"] * flux


def equilibria(p: Params, n_grid: int = 6001) -> list[dict]:
    """All equilibria of the reduced model, each with its stability and climate domain."""
    r_hi = 1.01 * ratio_for_flux(p.donor_flux + p.abiotic_flux, p)
    resp = response(p.case)
    grid = np.unique(np.r_[np.linspace(0.0, r_hi, n_grid), np.geomspace(1e-9, r_hi, n_grid // 3),
                           resp.ratios[resp.ratios < r_hi]])
    f = tendency(grid, p)
    out = []
    for i in np.flatnonzero(np.sign(f[:-1]) * np.sign(f[1:]) < 0):
        r = brentq(lambda x: float(tendency(x, p)), grid[i], grid[i + 1], xtol=1e-14, rtol=1e-12)
        out.append({"r": r, "stable": bool(f[i] > 0), "t_k": float(temperature_k(r, p)),
                    "eta": float(capture_efficiency(temperature_k(r, p), p)), "domain": str(domain(r, p))})
    return out


def settle(r0: float, p: Params) -> dict:
    """Equilibrium reached by the 1D flow from r0: the nearest root in the direction of flow."""
    roots = equilibria(p)
    f0 = float(tendency(r0, p))
    if f0 > 0:
        return next(e for e in roots if e["r"] > r0)
    if f0 < 0:
        return next(e for e in reversed(roots) if e["r"] < r0)
    return min(roots, key=lambda e: abs(e["r"] - r0))


def sweep(fluxes: np.ndarray, p: Params, r0: float = 0.0) -> list[dict]:
    """Step the donor supply, starting each step from the previous equilibrium."""
    out, r = [], r0
    for phi in fluxes:
        e = settle(r, replace(p, donor_flux=float(phi)))
        out.append({"donor_flux": float(phi), **e})
        r = e["r"]
    return out


def full_derivatives(y: np.ndarray, p: Params, k_donor: float = 0.1, death: float = 1.0) -> np.ndarray:
    """The unreduced (D, B, M) system with yield 1, in ratio units per year."""
    d, b, m = np.maximum(y, 0.0)
    c = atmosphere(p.case)["flux_to_ratio_per_yr"]
    half_sat = c * p.maintenance_flux / k_donor
    mu = death * growth_ratio(temperature_k(m, p), p)
    uptake = mu * b * d / (half_sat + d)
    return np.array([c * p.donor_flux - k_donor * d - uptake,
                     uptake - death * b,
                     uptake + c * p.abiotic_flux - m / p.lifetime_yr])


def integrate_full(y0: np.ndarray, p: Params, years: float, **kw) -> np.ndarray:
    sol = solve_ivp(lambda _t, y: full_derivatives(y, p, **kw), (0.0, years), y0,
                    method="LSODA", rtol=1e-9, atol=1e-14)
    return sol.y[:, -1]
