"""Faithful reconstruction of the Budyko (1969) zonal energy-balance model.

Budyko, M. I. (1969). The effect of solar radiation variations on the climate
of the Earth. Tellus 21, 611-619. doi:10.3402/tellusa.v21i5.10109

Units are the paper's: radiation in kcal cm-2 month-1, temperature in deg C,
latitude in degrees. Equation numbers refer to the paper. The model is one
hemisphere, which stands for both (the paper assumes the two change alike).
Interpretive choices are documented in models/budyko_sellers/README.md and
are fields of Reading, so that rejected readings can be run as controls.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

MONTH_DAYS = 30.0  # the month of kcal cm-2 month-1; the paper does not state it
CAL_MIN_TO_KCAL_MONTH = 1440 * MONTH_DAYS / 1000  # cal cm-2 min-1 -> kcal cm-2 month-1


@dataclass(frozen=True)
class Params:
    a: float = 14.0  # eq. (1), kcal cm-2 month-1
    b: float = 0.14  # eq. (1), "B", kcal cm-2 month-1 per deg C
    a1: float = 3.0  # eq. (1)
    b1: float = 0.10  # eq. (1), "B1"
    cloud: float = 0.50  # n, mean planetary cloudiness
    beta: float = 0.235  # eq. (3), kcal cm-2 month-1 per deg C
    solar_constant: float = 1.92  # cal cm-2 min-1
    albedo_free: float = 0.32  # 0-60 deg and wherever ice is absent
    albedo_ice: float = 0.62  # ice-covered area
    albedo_edge: float = 0.50  # southern boundary of the ice cover
    edge_now: float = 72.0  # present mean ice-edge latitude, deg N
    albedo_ice_jump: float = 0.30  # coefficient of S in eqs (6)-(7)
    # Present-day albedo by latitude as stated for Fig. 3 (0.32 at 0-60 deg).
    profile_lat: tuple[float, ...] = (60.0, 70.0, 80.0)
    profile_albedo: tuple[float, ...] = (0.32, 0.50, 0.62)


@dataclass(frozen=True)
class Reading:
    """Choices the paper leaves open; defaults are the faithful reading."""

    obliquity: float = 23.45  # deg, for annual-mean insolation by latitude
    # Present-day albedo: "profile" (the stated 60/70/80 deg values, linearly
    # interpolated) or "step" (0.32 equatorward of 72 deg, 0.62 poleward).
    present_albedo: str = "profile"
    # Planetary albedo alpha_p in eqs (5)-(6): "insolation" (weighted by
    # incoming radiation, so that A sums to zero over the Earth as the paper's
    # derivation of eq. (5) requires) or "area" (area mean of the zonal albedos).
    planetary_albedo: str = "insolation"
    # Present planetary temperature T_p' in eqs (4) and (7): None takes eq. (5).
    tp_now: float | None = None
    # Area basis of S in eq. (6): 1 for one hemisphere (both hemispheres alike),
    # 0.5 if ice grows in one hemisphere but l is counted over the whole globe.
    s_area_factor: float = 1.0
    # Albedo of newly iced latitudes in eq. (7): "step" puts albedo_ice
    # poleward of the edge; "translate" shifts the present profile with it.
    ice_albedo: str = "step"
    # Days per month in the radiation unit kcal cm-2 month-1.
    month_days: float = MONTH_DAYS
    # Temperature at which ice forms: None takes eq. (4) at 72 deg with the
    # boundary albedo 0.50; a number overrides it (e.g. the present profile's
    # own T0 at 72 deg, or a reading of the observed curve).
    t_edge: float | None = None


FAITHFUL = Reading()

# Equal-area grid in x = sin(latitude) for hemispheric means.
_N = 9000
_X = (np.arange(_N) + 0.5) / _N
LAT = np.degrees(np.arcsin(_X))


def hemispheric_mean(f: np.ndarray) -> float:
    return float(np.mean(f))


def annual_insolation(lat, solar_constant: float = 1.92, obliquity: float = 23.45,
                      month_days: float = MONTH_DAYS) -> np.ndarray:
    """Annual-mean top-of-atmosphere insolation, kcal cm-2 month-1, on a circular orbit."""
    lat = np.atleast_1d(np.asarray(lat, dtype=float))
    grid = np.linspace(0.0, 90.0, 1801)
    lam = (np.arange(2880) + 0.5) * 2 * np.pi / 2880
    dec = np.arcsin(np.sin(np.radians(obliquity)) * np.sin(lam))[None, :]
    phi = np.radians(grid)[:, None]
    h0 = np.arccos(np.clip(-np.tan(phi) * np.tan(dec), -1.0, 1.0))
    daily = (h0 * np.sin(phi) * np.sin(dec) + np.cos(phi) * np.cos(dec) * np.sin(h0)) / np.pi
    s0 = solar_constant * 1440 * month_days / 1000
    return s0 * np.interp(np.abs(lat), grid, daily.mean(axis=1))


class Budyko1969:
    def __init__(self, p: Params = Params(), r: Reading = FAITHFUL):
        self.p, self.r = p, r
        self.q = annual_insolation(LAT, p.solar_constant, r.obliquity, r.month_days)
        self.qp = hemispheric_mean(self.q)
        self.k = p.b - p.b1 * p.cloud  # B - B1 n
        self.c = p.a - p.a1 * p.cloud  # a - a1 n
        self.alpha_now = self.present_albedo(LAT)
        weight = self.q / self.qp if r.planetary_albedo == "insolation" else 1.0
        self.alpha_p_now = hemispheric_mean(weight * self.alpha_now)
        self.tp_eq5 = self.planetary_temperature(self.alpha_p_now)
        self.tp_now = self.tp_eq5 if r.tp_now is None else r.tp_now
        self.t_edge = (self.zonal_temperature(self.insolation(p.edge_now), self.edge_albedo(p.edge_now), self.tp_now)
                       if r.t_edge is None else r.t_edge)

    def insolation(self, lat):
        return np.interp(np.abs(np.asarray(lat, dtype=float)), LAT, self.q, left=self.q[0], right=self.q[-1])

    def present_albedo(self, lat):
        lat = np.asarray(lat, dtype=float)
        p = self.p
        if self.r.present_albedo == "step":
            return np.where(lat < p.edge_now, p.albedo_free, p.albedo_ice)
        return np.interp(lat, p.profile_lat, p.profile_albedo)

    def planetary_temperature(self, alpha_p: float, eps: float = 0.0) -> float:
        """Eq. (5), with Q_p scaled by (1 + eps)."""
        return (self.qp * (1 + eps) * (1 - alpha_p) - self.c) / self.k

    def zonal_temperature(self, q, alpha, tp, eps: float = 0.0):
        """Eq. (4), and eq. (7) when tp = T_p' + dT_p and eps = dQ_p/Q_p."""
        p = self.p
        return (q * (1 + eps) * (1 - alpha) - self.c + p.beta * tp) / (p.beta + self.k)

    def albedo(self, lat, edge: float):
        """Albedo with the ice edge at `edge` (deg).

        "step": ice-covered latitudes (poleward of the edge) take 0.62 and
        latitudes freed of ice take 0.32; elsewhere the present albedo holds.
        The edge itself takes the boundary albedo 0.50.
        Eq. (6) still sets the planetary temperature, through 0.30 S."""
        lat = np.asarray(lat, dtype=float)
        p = self.p
        if self.r.ice_albedo == "translate":
            return np.interp(lat - (edge - p.edge_now), p.profile_lat, p.profile_albedo)
        now = self.present_albedo(lat)
        freed = (lat >= p.edge_now) & (lat < edge)
        inner = np.where(lat > edge, p.albedo_ice, np.where(freed, p.albedo_free, now))
        return np.where(lat == edge, p.albedo_edge, inner)

    def edge_albedo(self, edge: float) -> float:
        """Albedo used for the temperature at the ice edge."""
        if self.r.ice_albedo == "translate":
            return float(np.interp(self.p.edge_now, self.p.profile_lat, self.p.profile_albedo))
        return self.p.albedo_edge

    def s_term(self, edge: float) -> float:
        """0.30 S of eq. (6): the change in planetary albedo as the edge moves from 72 deg to `edge`.

        S = l q, with l the fractional area between the edges and q the ratio
        of its mean radiation to the planetary mean. Positive when ice grows."""
        p = self.p
        if self.r.ice_albedo == "translate":
            change = hemispheric_mean(self.q * (self.albedo(LAT, edge) - self.alpha_now)) / self.qp
            return self.r.s_area_factor * change
        lo, hi = sorted((edge, p.edge_now))
        band = (LAT >= lo) & (LAT < hi)
        s = hemispheric_mean(self.q * band) / self.qp
        return self.r.s_area_factor * p.albedo_ice_jump * s * (1 if edge < p.edge_now else -1)

    def delta_tp(self, eps: float, edge: float) -> float:
        """Eq. (6)."""
        s30 = self.s_term(edge)
        return self.qp / self.k * (eps * (1 - self.alpha_p_now - s30) - s30)

    def eps_for_edge(self, edge: float) -> float:
        """Radiation change dQ_p/Q_p that holds the ice edge at `edge`.

        The edge is where eq. (7), evaluated with the boundary albedo 0.50,
        returns the present temperature of the 72 deg boundary. Eq. (7) is
        linear in eps, so this is solved exactly."""
        p = self.p
        q0 = float(self.insolation(edge))
        a0 = self.edge_albedo(edge)
        s30 = self.s_term(edge)
        g = p.beta * self.qp / self.k
        const = q0 * (1 - a0) - self.c + p.beta * self.tp_now - g * s30
        slope = q0 * (1 - a0) + g * (1 - self.alpha_p_now - s30)
        return float(((p.beta + self.k) * self.t_edge - const) / slope)

    def branch(self, edges: np.ndarray) -> dict[str, np.ndarray]:
        """Ice-edge equilibria: eps(phi_0) and T_p, the curves of Fig. 5."""
        edges = np.asarray(edges, dtype=float)
        eps = np.array([self.eps_for_edge(e) for e in edges])
        dtp = np.array([self.delta_tp(x, e) for x, e in zip(eps, edges)])
        return {"edge": edges, "eps": eps, "tp": self.tp_now + dtp}

    def critical(self, edges=np.arange(72.0, 5.0, -0.05)) -> dict[str, float]:
        """Most negative eps on the branch: the runaway point of Fig. 5."""
        b = self.branch(edges)
        i = int(np.argmin(b["eps"]))
        return {"eps": float(b["eps"][i]), "edge": float(b["edge"][i]), "tp": float(b["tp"][i])}

    def stable_edge(self, eps: float) -> float:
        """Ice edge on the stable (poleward) branch for radiation change eps.

        Beyond the critical point there is no partly glaciated equilibrium and
        the ice runs to the equator, so the edge is 0."""
        b = self.branch(np.arange(72.0, 5.0, -0.01))
        i = int(np.argmin(b["eps"]))
        e, x = b["edge"][: i + 1], b["eps"][: i + 1]
        if eps < x[-1]:
            return 0.0
        j = int(np.searchsorted(-x, -eps))
        if j == 0 or x[j - 1] == eps:
            return float(e[max(j - 1, 0)])
        from scipy.optimize import brentq

        return float(brentq(lambda z: self.eps_for_edge(z) - eps, e[j], e[j - 1], xtol=1e-10))

    def profile(self, lat, eps: float = 0.0, edge: float | None = None):
        """Eq. (7): zonal temperature for radiation change eps with the ice edge at `edge`.

        With eps = 0 and edge = None it is the present-day profile T_0 of eq. (4)."""
        lat = np.asarray(lat, dtype=float)
        if edge is None and eps == 0.0:
            return self.zonal_temperature(self.insolation(lat), self.present_albedo(lat), self.tp_now)
        edge = self.stable_edge(eps) if edge is None else edge
        tp = self.tp_now + self.delta_tp(eps, edge)
        return self.zonal_temperature(self.insolation(lat), self.albedo(lat, edge), tp, eps)

    def ice_free(self, lat):
        """Fig. 6, T_q: albedo 0.32 at every latitude, the same beta.

        The planetary temperature follows eq. (6) with eps = 0 for the removal
        of all ice poleward of the present edge."""
        lat = np.asarray(lat, dtype=float)
        tp = self.tp_now + self.delta_tp(0.0, 90.0)
        return self.zonal_temperature(self.insolation(lat), np.full_like(lat, self.p.albedo_free), tp)

    def fixed_albedo_sensitivity(self, alpha_p: float = 0.33) -> float:
        """deg C per 1 % change of radiation with constant planetary albedo (text, p. 613)."""
        return self.qp * 0.01 * (1 - alpha_p) / self.k


def model(**reading) -> Budyko1969:
    return Budyko1969(Params(), replace(FAITHFUL, **reading))
