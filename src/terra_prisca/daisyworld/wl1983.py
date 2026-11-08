"""Faithful reconstruction of Daisyworld as published by Watson & Lovelock (1983).

Watson, A. J. & Lovelock, J. E. (1983). Biological homeostasis of the global
environment: the parable of Daisyworld. Tellus B 35, 284-289.
doi:10.1111/j.1600-0889.1983.tb00031.x

Equation numbers in comments refer to the paper. Temperatures are in deg C
with the paper's 273 offset. Interpretive choices the paper leaves open are
documented in models/daisyworld/README.md.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy.integrate import solve_ivp

KELVIN_OFFSET = 273.0


@dataclass(frozen=True)
class Params:
    flux: float = 917.0  # S, W m-2 (9.17e5 erg cm-2 s-1, Fig. 1 legend)
    sigma: float = 5.67e-8  # Stefan's constant, W m-2 K-4
    death_rate: float = 0.3  # gamma, eq. (1)
    fertile: float = 1.0  # P, eq. (2)
    q_prime: float = 20.0  # q', K, eq. (7)
    albedo_bare: float = 0.5
    albedo_white: float = 0.75
    albedo_black: float = 0.25
    # Fig. 2: albedo of the cloud over black stands, which replaces the black
    # daisies' albedo in the planetary energy balance (eq. 4-5) only.
    cloud_over_black: float | None = None
    t_opt: float = 22.5  # eq. (3)
    growth_curvature: float = 0.003265  # eq. (3)
    seed: float = 0.01  # reseeding area for extinct species
    white: bool = True  # species present in this experiment
    black: bool = True


def growth_rate(temp: np.ndarray | float, p: Params) -> np.ndarray | float:
    """Eq. (3), clipped at zero outside 5-40 deg C."""
    return np.maximum(0.0, 1.0 - p.growth_curvature * (p.t_opt - temp) ** 2)


def planetary_albedo(a_w: float, a_b: float, p: Params) -> float:
    """Eq. (5), with the Fig. 2 cloud substitution when enabled."""
    black = p.albedo_black if p.cloud_over_black is None else p.cloud_over_black
    return (1.0 - a_w - a_b) * p.albedo_bare + a_w * p.albedo_white + a_b * black


def effective_temperature(albedo: float, lum: float, p: Params) -> float:
    """Eq. (4): sigma (Te + 273)^4 = S L (1 - A)."""
    return (p.flux * lum * (1.0 - albedo) / p.sigma) ** 0.25 - KELVIN_OFFSET


def state(a_w: float, a_b: float, lum: float, p: Params) -> dict[str, float]:
    albedo = planetary_albedo(a_w, a_b, p)
    t_e = effective_temperature(albedo, lum, p)
    return {
        "albedo": albedo,
        "t_e": t_e,
        "t_w": p.q_prime * (albedo - p.albedo_white) + t_e,  # eq. (7)
        "t_b": p.q_prime * (albedo - p.albedo_black) + t_e,
        "x": p.fertile - a_w - a_b,  # eq. (2)
    }


def derivatives(a: np.ndarray, lum: float, p: Params) -> np.ndarray:
    """Eq. (1)."""
    a_w, a_b = a
    s = state(a_w, a_b, lum, p)
    da_w = a_w * (s["x"] * growth_rate(s["t_w"], p) - p.death_rate)
    da_b = a_b * (s["x"] * growth_rate(s["t_b"], p) - p.death_rate)
    return np.array([da_w if p.white else 0.0, da_b if p.black else 0.0])


def steady_state(
    a0: np.ndarray,
    lum: float,
    p: Params,
    tol: float = 1e-9,
    chunk: float = 200.0,
    t_max: float = 1e5,
    extinct_below: float = 1e-6,
) -> tuple[np.ndarray, bool]:
    """Integrate eq. (1) forward until every |da/dt| / max(a, 1e-4) < tol.

    A species can decay below `extinct_below` while the other establishes and then
    be able to grow again in the final environment. Such a state is an equilibrium
    on the boundary but is unstable to invasion, so an enabled species at zero
    with a positive invasion rate is reseeded at p.seed at the same L and the
    integration repeated.
    """
    a = np.asarray(a0, dtype=float)
    present = np.array([p.white, p.black])
    converged = False
    for _ in range(5):
        t = 0.0
        converged = False
        while t < t_max:
            sol = solve_ivp(
                lambda _t, y: derivatives(y, lum, p),
                (0.0, chunk),
                a,
                method="LSODA",
                rtol=1e-10,
                atol=1e-13,
            )
            a = np.clip(sol.y[:, -1], 0.0, None)
            t += chunk
            if np.max(np.abs(derivatives(a, lum, p)) / np.maximum(a, 1e-4)) < tol:
                converged = True
                break
        a[a < extinct_below] = 0.0
        invaders = present & (a == 0.0) & (invasion_rates(a, lum, p) > tol)
        if not invaders.any():
            break
        a = np.where(invaders, p.seed, a)
        converged = False
    return a, converged


def invasion_rates(a: np.ndarray, lum: float, p: Params) -> np.ndarray:
    """Per-capita growth x beta_i - gamma of each species in the environment set by a."""
    s = state(a[0], a[1], lum, p)
    return s["x"] * growth_rate(np.array([s["t_w"], s["t_b"]]), p) - p.death_rate


def sweep(luminosities: np.ndarray, p: Params, start: np.ndarray | None = None) -> dict[str, np.ndarray]:
    """Fig. 1 procedure: step L, starting each step from the previous steady
    state, reseeding any zero population (of a species present) at p.seed."""
    present = np.array([p.white, p.black])
    a = np.zeros(2) if start is None else np.asarray(start, dtype=float)
    keys = ("lum", "a_w", "a_b", "t_e", "t_w", "t_b", "converged")
    out = {k: [] for k in keys}
    for lum in luminosities:
        a0 = np.where(present & (a == 0.0), p.seed, a)
        a, ok = steady_state(a0, lum, p)
        s = state(a[0], a[1], lum, p)
        for k, v in zip(keys, (lum, a[0], a[1], s["t_e"], s["t_w"], s["t_b"], ok)):
            out[k].append(v)
    return {k: np.array(v) for k, v in out.items()}


def hysteresis_sweep(lum_min: float, lum_max: float, step: float, p: Params) -> tuple[dict, dict]:
    """Increasing sweep from a lifeless start, then decreasing from its end."""
    n = int(round((lum_max - lum_min) / step)) + 1
    lums = np.linspace(lum_min, lum_max, n)
    up = sweep(lums, p)
    down = sweep(lums[::-1], p, start=np.array([up["a_w"][-1], up["a_b"][-1]]))
    return up, down


def lifeless_temperature(lum: np.ndarray, p: Params) -> np.ndarray:
    return effective_temperature(p.albedo_bare, lum, p)


EXPERIMENTS: dict[str, Params] = {
    "fig1a_neutral": replace(Params(), white=False, albedo_black=0.5),
    "fig1b_black": replace(Params(), white=False),
    "fig1c_white": replace(Params(), black=False),
    "fig1d_both": Params(),
    "fig2_cloud": replace(Params(), cloud_over_black=0.8),
}
