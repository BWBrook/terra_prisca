"""Lovelock & Whitfield (1982): life span of the biosphere.

Nature 296, 561-563, doi:10.1038/296561a0.

The paper has no equations. Its reckoning, as stated in the text and drawn in
Fig. 2, is:

  - solar luminosity rises linearly in time (the Sun line, after Newkirk 1980);
  - to hold the mean temperature constant, sqrt(CO2) falls linearly with
    luminosity, from a stated value 3,500 Myr ago to 320 ppm today;
  - extrapolated forward, CO2 reaches 150 ppm, "the lower limit tolerable for
    photosynthesis", in "about 100 Myr".

Time t is in Myr from the present (negative in the past); luminosity L is
relative to today's.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy.optimize import brentq

from terra_prisca.walker_hays_kasting import whk1981

# The Sun line of Fig. 2: straight, through L = 1 today. The paper gives no
# formula; the slope is read from the scan (scan_lw1982.SUN fits 0.0733/Gyr).
SUN_SLOPE_PER_GYR = 0.0733

C_NOW = 320.0     # ppm, today (text)
T_PAST = -3500.0  # Myr, the past anchor (text)
C_PAST = 70000.0  # ppm at T_PAST; the text prints 7,000 (see the model page)
C_LIMIT = 150.0   # ppm, the photosynthetic limit (text)


def luminosity(t, slope_per_gyr: float = SUN_SLOPE_PER_GYR):
    """L/L0 on the straight Sun line of Fig. 2."""
    return 1.0 + slope_per_gyr * np.asarray(t, float) / 1000.0


def gough_luminosity(t, t_sun_gyr: float = 4.7):
    """Gough (1981) eq. (1): L/L0 = 1/[1 + (2/5)(1 - t/t_sun)], t from the Sun's birth.
    Used only as a null for the printed Sun line."""
    age = t_sun_gyr + np.asarray(t, float) / 1000.0
    return 1.0 / (1.0 + 0.4 * (1.0 - age / t_sun_gyr))


@dataclass(frozen=True)
class Reading:
    """CO2 compensating for luminosity at constant temperature.

    power: C**power is linear in L (0.5 is the text's square root; 2/3 the
    alternative the text mentions; 1 a plain linear rule). whk_constant_T
    replaces the two-point rule by WHK eq. (6) with dT = 0.

    sun: "straight" (Fig. 2) or "gough" (Gough 1981). The two dated CO2 anchors
    are kept whatever the Sun law, so the rule is re-anchored on the new
    luminosities. With a straight Sun, (L - 1)/(L_past - 1) = t/t_past and the
    slope cancels: the span to the limit does not depend on it."""

    name: str = "faithful"
    power: float = 0.5
    c_past: float = C_PAST
    t_past: float = T_PAST
    c_now: float = C_NOW
    c_limit: float = C_LIMIT
    sun: str = "straight"
    sun_slope: float = SUN_SLOPE_PER_GYR
    whk_constant_T: bool = False
    whk_feedback: bool = False


FAITHFUL = Reading()


def sun(t, r: Reading = FAITHFUL):
    return gough_luminosity(t) if r.sun == "gough" else luminosity(t, r.sun_slope)


def co2(t, r: Reading = FAITHFUL):
    """Atmospheric CO2 (ppm) along the compensation rule; NaN where the rule has
    no positive solution (the two-point rule once C**power would fall to zero or
    below; WHK eq. (6) once dT = 0 would need P <= 0)."""
    L = sun(t, r)
    if r.whk_constant_T or r.whk_feedback:
        dte = whk1981.dTe_from_luminosity(L)
        return r.c_now * np.vectorize(lambda x: _whk_p(x, r))(dte)
    if r.sun == "straight" and r.sun_slope == 0:
        return np.full_like(L, r.c_now)  # a constant Sun needs no compensation
    lp = sun(r.t_past, r)
    a, b = r.c_now ** r.power, r.c_past ** r.power
    y = a + (b - a) * (L - 1.0) / (lp - 1.0)
    with np.errstate(invalid="ignore"):
        return np.where(y > 0, np.abs(y) ** (1.0 / r.power), np.nan)


def _whk_p(dte: float, r: Reading) -> float:
    if r.whk_feedback:
        return whk1981.equilibrium(float(dte), 1.0)[1]
    # eq. (6) with dT = 0: 0 = 2 dTe + 4.6 (P^0.364 - 1)
    w = whk1981.FAITHFUL
    q = 1.0 - w.te_gain * dte / w.gh_amp
    return q ** (1.0 / w.gh_exponent) if q > 0 else float("nan")


def lifespan(r: Reading = FAITHFUL, step: float = 1.0, horizon: float = 1.0e4) -> float:
    """Myr from today until CO2 falls to c_limit, searched only where the rule
    has a solution; inf if it never reaches the limit there."""
    t = np.arange(0.0, horizon + step, step)
    c = co2(t, r)
    hit = np.nonzero(np.isfinite(c) & (c <= r.c_limit))[0]
    if not hit.size:
        return float("inf")
    i = hit[0]
    if i == 0:
        return 0.0
    if not np.isfinite(c[i - 1]):
        raise ValueError("the rule loses its solution before reaching the limit")
    return brentq(lambda x: float(co2(x, r)) - r.c_limit, t[i - 1], t[i], xtol=1e-9)


def domain_end(r: Reading = FAITHFUL, step: float = 0.01, horizon: float = 1.0e4) -> float:
    """First time after today (Myr, to `step`) at which the rule has no solution."""
    t = np.arange(0.0, horizon + step, step)
    bad = np.nonzero(~np.isfinite(co2(t, r)))[0]
    return float(t[bad[0]]) if bad.size else float("inf")


READINGS = {
    "faithful": FAITHFUL,
    "text_7000": Reading(name="text's 7,000 ppm anchor", c_past=7000.0),
    "two_thirds": Reading(name="2/3 power (text's alternative)", power=2.0 / 3.0),
    "linear_c": Reading(name="CO2 linear in L", power=1.0),
    "whk_constant_T": Reading(name="WHK eq. (6) at constant temperature", whk_constant_T=True),
}

VARIANTS = {
    "whk_feedback": Reading(name="WHK feedback, V/V0 = 1 (temperature free)", whk_feedback=True),
    "gough_sun": Reading(name="Gough (1981) Sun, same dated CO2 anchors", sun="gough"),
}

CONTROLS = {
    "no_brightening": replace(FAITHFUL, name="null: constant Sun", sun_slope=0.0),
}
