"""Ingredient swap between Lovelock & Whitfield (1982) and Caldeira & Kasting (1992).

An analysis built on the two faithful reconstructions, not a reconstruction:
it imports lw1982 and ck1992 and changes neither.

    uv run python -m terra_prisca.biosphere_lifespan.ingredient_swap [outdir]

The endpoint compared is the time until atmospheric CO2 falls to the plants'
CO2 limit (the reconstructions give 80 Myr to 150 ppm for L&W and 767 Myr to
10 ppm for C&K), not the end of all life. Three ingredients separate the two,
each with one setting per paper:

  sun    -- L&W's straight Sun line (0.0733/Gyr) | C&K eq. (1)
  co2    -- L&W's rule, sqrt(CO2) linear in luminosity between dated anchors,
            temperature held constant | C&K's weathering balance with soil CO2
            raised by plants, eqs (1)-(8), temperature free
  plants -- C3, CO2 limit 150 ppm | C4, CO2 limit 10 ppm. In C&K this
            sets both the productivity curve's Pmin and the threshold; in L&W
            only the threshold.

Both models are sequences of equilibria, so each time is fixed by the
brightening S*/S0 at which CO2 meets the threshold, and the Sun law turns S*
into time. The eight combinations are scored, and the change from L&W to C&K
is shared among the ingredients by Shapley values (the mean of each
ingredient's effect over all orders of swapping), in ln(time) and in Myr.
The co2 ingredient is then opened up: C&K's greenhouse at constant
temperature, then a square of closure (T held at T0, or weathering balance
with T free) by soil pump (held at Pi0, or responsive), and the warming along
the faithful runs.

Names of laws, Suns, plants and readings are checked; a threshold must be a
positive CO2 level (ppm). One at or above today's 320 ppm is already met
(time 0, as lw1982.lifespan); C&K's laws reject levels below their fit range
(0.01 ppm) and return inf for levels they do not reach within 3 Gyr.
"""

from __future__ import annotations

import csv
import math
import sys
from dataclasses import replace
from itertools import permutations, product
from pathlib import Path

import numpy as np

from . import ck1992 as ck
from . import lw1982 as lw

PPM = 1e-6  # bar per ppm (ck1992 works in bar, lw1982 in ppm)
MYR_PER_GYR = 1000.0
T_MAX_GYR = 3.0

SUNS = {"straight": "L&W straight Sun, 0.0733/Gyr", "eq1": "C&K eq. (1)"}
PLANTS = {"C3": ("C3, CO2 limit 150 ppm", 150.0, ck.C3), "C4": ("C4, CO2 limit 10 ppm", 10.0, ck.FAITHFUL)}

# The co2 ingredient's two settings and the laws between them. Each C&K law
# is a ck1992 reading for the plants in use (only Pmin differs).
LAWS = {
    "lw_rule": "L&W rule: sqrt(CO2) linear in luminosity, T constant",
    "ck_constant_T": "C&K greenhouse and albedo, eqs (2)-(5), T held at T0",
    "ck_pump_held": "C&K weathering balance, T free, soil pump held at Pi0 (Volk's case W3)",
    "ck_biology": "C&K weathering balance with plants, eqs (6)-(8)",
}
SIDE = {"whk_weathering": "side branch: WHK weathering on Patm, T free (neither paper)",
        "c4_productivity_at_150": "side branch: C4 productivity curve, threshold 150 ppm"}


def _check(what: str, name: str, allowed) -> None:
    if name not in allowed:
        raise ValueError(f"unknown {what} {name!r}; expected one of {sorted(allowed)}")


def brightness(t_gyr: float, sun: str) -> float:
    """S/S0 at t Gyr from today."""
    _check("Sun law", sun, SUNS)
    return float(lw.luminosity(t_gyr * MYR_PER_GYR)) if sun == "straight" else float(ck.solar(t_gyr)) / ck.S0


def time_to(s_ratio: float, sun: str) -> float:
    """Gyr until the Sun reaches s_ratio (the inverse of brightness); inf if never."""
    _check("Sun law", sun, SUNS)
    if not math.isfinite(s_ratio):
        return float("inf")
    if sun == "straight":
        return (s_ratio - 1.0) / lw.SUN_SLOPE_PER_GYR
    return (1.0 - 1.0 / s_ratio) * ck.TAU0_GYR / ck.SUN_COEFF


def lw_rule_s_star(threshold_ppm: float, lum) -> float:
    """L&W's rule re-anchored on the luminosity law lum(t Myr): the two dated
    anchors (320 ppm today, 70,000 ppm 3,500 Myr ago) are kept, so the rule's
    slope follows the Sun's luminosity at the past anchor."""
    lp = float(lum(lw.T_PAST))
    a, b = math.sqrt(lw.C_NOW), math.sqrt(lw.C_PAST)
    return 1.0 + (lp - 1.0) * (math.sqrt(threshold_ppm) - a) / (b - a)


# Readings of the whole swap. so2: the SO2 factor of C&K's weathering.
# lw_line: under C&K's Sun, L&W's rule is either recalibrated on its two dated
# anchors ("recalibrated", the primary reading) or keeps the sqrt(CO2)-luminosity
# line fitted under L&W's own Sun, so that only the future clock changes ("fixed").
READINGS = {
    "faithful": {"so2": 1.0, "lw_line": "recalibrated"},
    "so2_fitted": {"so2": ck.SO2_FIT_FACTOR, "lw_line": "recalibrated"},
    "lw_line_fixed": {"so2": 1.0, "lw_line": "fixed"},
}
LW_LINES = ("recalibrated", "fixed")


def _reading(law: str, plants: str, so2: float = 1.0) -> ck.Reading:
    r = replace(PLANTS[plants][2], so2_factor=so2) if so2 != 1.0 else PLANTS[plants][2]
    if law == "ck_pump_held":
        return replace(r, name=LAWS[law], productivity="constant")
    if law == "whk_weathering":
        return replace(r, name=SIDE[law], weathering="whk")
    return r


def s_star(law: str, plants: str, sun: str = "eq1", threshold_ppm: float | None = None, so2: float = 1.0,
           lw_line: str = "recalibrated") -> float:
    """S*/S0: the brightening at which CO2 first falls to the threshold; 1 if
    it is already met today, inf if it is not reached.
    C&K's laws do not depend on the Sun law (CO2 depends on time only through
    S), so they are solved under eq. (1) and mapped."""
    _check("CO2 law", law, LAWS.keys() | SIDE.keys())
    _check("plants", plants, PLANTS)
    _check("Sun law", sun, SUNS)
    _check("L&W line", lw_line, LW_LINES)
    thr = PLANTS[plants][1] if threshold_ppm is None else float(threshold_ppm)
    if not (math.isfinite(thr) and thr > 0.0):
        raise ValueError(f"threshold must be a positive CO2 level in ppm, not {thr}")
    if thr >= lw.C_NOW:
        return 1.0
    if law == "lw_rule":
        own = sun == "straight" or lw_line == "fixed"
        lum = lw.luminosity if own else (lambda t_myr: brightness(t_myr / MYR_PER_GYR, "eq1"))
        return lw_rule_s_star(thr, lum)
    if thr * PPM < ck.P_FIT[0]:
        raise ValueError(f"{thr} ppm is below the range of C&K's climate fits ({ck.P_FIT[0] / PPM} ppm)")
    if law == "ck_constant_T":
        try:
            t = ck.constant_T_time(thr * PPM, ck.FAITHFUL, T_MAX_GYR)
        except ValueError:  # no root within T_MAX_GYR
            t = float("inf")
    else:
        t = ck.co2_time(thr * PPM, _reading(law, plants, so2), T_MAX_GYR)
    return brightness(t, "eq1") if math.isfinite(t) else float("inf")


def lifespan_myr(law: str, plants: str, sun: str, threshold_ppm: float | None = None, so2: float = 1.0,
                 lw_line: str = "recalibrated") -> float:
    """Myr until CO2 falls to the threshold (the plants' limit by default)."""
    return time_to(s_star(law, plants, sun, threshold_ppm, so2, lw_line), sun) * MYR_PER_GYR


ENDS = {"L&W": {"sun": "straight", "co2": "lw_rule", "plants": "C3"},
        "C&K": {"sun": "eq1", "co2": "ck_biology", "plants": "C4"}}
INGREDIENTS = ("sun", "co2", "plants")


def factorial(reading: str = "faithful") -> list[dict]:
    """The eight combinations of the two papers' settings."""
    _check("reading", reading, READINGS)
    rd = READINGS[reading]
    rows = []
    for pick in product(("L&W", "C&K"), repeat=3):
        st = {k: ENDS[p][k] for k, p in zip(INGREDIENTS, pick)}
        sstar = s_star(st["co2"], st["plants"], st["sun"], so2=rd["so2"], lw_line=rd["lw_line"])
        rows.append({"reading": reading, **{f"{k}_from": p for k, p in zip(INGREDIENTS, pick)},
                     "sun": SUNS[st["sun"]], "co2": LAWS[st["co2"]], "plants": PLANTS[st["plants"]][0],
                     "S_star_over_S0": sstar, "time_to_limit_Myr": time_to(sstar, st["sun"]) * MYR_PER_GYR})
    return rows


def shapley(cells: list[dict]) -> list[dict]:
    """Each ingredient's share of the change from L&W to C&K: its effect
    averaged over the six orders of swapping, with the smallest and largest
    effect it has in any context."""
    life = {tuple(r[f"{k}_from"] for k in INGREDIENTS): r["time_to_limit_Myr"] for r in cells}

    def val(swapped: set) -> float:
        return life[tuple("C&K" if k in swapped else "L&W" for k in INGREDIENTS)]

    rows = []
    orders = list(permutations(INGREDIENTS))
    for ing in INGREDIENTS:
        logs, myrs = [], []
        for order in orders:
            before = set(order[:order.index(ing)])
            a, b = val(before), val(before | {ing})
            logs.append(math.log(b / a))
            myrs.append(b - a)
        factors = [math.exp(x) for x in logs]
        rows.append({"reading": cells[0]["reading"], "ingredient": ing, "L&W setting": _label(ing, "L&W"), "C&K setting": _label(ing, "C&K"),
                     "shapley_factor": math.exp(np.mean(logs)), "shapley_ln": float(np.mean(logs)),
                     "shapley_Myr": float(np.mean(myrs)),
                     "factor_min": min(factors), "factor_max": max(factors),
                     "Myr_min": min(myrs), "Myr_max": max(myrs)})
    total = math.log(val(set(INGREDIENTS)) / val(set()))
    for r in rows:
        r["share_of_ln_change"] = r["shapley_ln"] / total
    return rows


def _label(ing: str, end: str) -> str:
    k = ENDS[end][ing]
    return {"sun": SUNS, "co2": LAWS}.get(ing, {}).get(k) or PLANTS[k][0]


# The co2 ingredient opened up, under the eq. (1) Sun. After C&K's greenhouse
# at constant T, two changes remain: the closure (T held at T0, or weathering
# balancing the volcanic supply with T free) and the soil pump (held at Pi0,
# or responsive through eq. (8)). At constant T the pump only changes the
# diagnosed weathering, not the time.
CO2_STEPS = {
    "lw_rule": ("L&W rule", "T constant (the rule)", "none"),
    "ck_constant_T_pump_held": ("ck_constant_T", "T held at T0", "held at Pi0"),
    "ck_constant_T_pump_responsive": ("ck_constant_T", "T held at T0", "responsive, eq. (8)"),
    "ck_pump_held": ("ck_pump_held", "weathering balance, T free", "held at Pi0"),
    "ck_biology": ("ck_biology", "weathering balance, T free", "responsive, eq. (8)"),
}


def co2_steps() -> list[dict]:
    """Each law between the two CO2 settings, for each plant setting: S*, the
    state at the threshold, and the diagnosed weathering F/F0 (1 wherever
    weathering balances; below 1 at constant T, where it need not)."""
    rows = []
    for plants, (lab, thr, base) in PLANTS.items():
        for step, (law, closure, pump) in CO2_STEPS.items():
            row = {"plants": lab, "step": step, "closure": closure, "soil_pump": pump}
            if law == "L&W rule":
                sstar = s_star("lw_rule", plants, "eq1")
                row |= {"S_star_over_S0": sstar, "T_at_threshold_K": float("nan"), "T_minus_T0_K": 0.0,
                        "Pi_ratio": float("nan"), "F_over_F0": float("nan")}
            else:
                sstar = s_star(law, plants, "eq1")
                r = replace(base, productivity="constant") if pump.startswith("held") else base
                T = ck.temperature(sstar * ck.S0, thr * PPM, r)
                row |= {"S_star_over_S0": sstar, "T_at_threshold_K": T, "T_minus_T0_K": T - ck.t0(r),
                        "Pi_ratio": ck.productivity(T, thr * PPM, r), "F_over_F0": ck.weathering(thr * PPM, sstar * ck.S0, r)}
            row["time_to_limit_Myr"] = time_to(sstar, "eq1") * MYR_PER_GYR
            rows.append(row)
    return rows


WARMING_PPM = (320.0, 200.0, 150.0, 100.0, 50.0, 20.0, 10.0)


def warming() -> list[dict]:
    """The faithful C&K runs (C4 and C3-only) at falling CO2 levels: the
    warming grows as productivity declines, not only after it stops."""
    rows = []
    for plants in ("C4", "C3"):
        r = PLANTS[plants][2]
        for ppm in WARMING_PPM:
            t = ck.co2_time(ppm * PPM, r, T_MAX_GYR)
            st = ck.state(t, r)
            rows.append({"run": f"C&K faithful, Pmin {r.p_min / PPM:g} ppm", "plants": plants, "P_atm_ppm": ppm,
                         "t_Myr": t * MYR_PER_GYR, "S_ratio": st["S_ratio"], "T_minus_T0_K": st["T_K"] - ck.t0(r),
                         "Pi_ratio": st["Pi_ratio"], "P_soil_ppm": st["P_soil_ppm"]})
    return rows


def side_branches() -> list[dict]:
    rows = []
    for plants in PLANTS:
        for sun in SUNS:
            sstar = s_star("whk_weathering", plants, "eq1")
            rows.append({"branch": SIDE["whk_weathering"], "plants": PLANTS[plants][0], "sun": SUNS[sun],
                         "S_star_over_S0": sstar, "Pi_ratio_at_threshold": float("nan"),
                         "time_to_limit_Myr": time_to(sstar, sun) * MYR_PER_GYR})
    sstar = s_star("ck_biology", "C4", "eq1", threshold_ppm=150.0)
    pi = ck.productivity(ck.temperature(sstar * ck.S0, 150.0 * PPM), 150.0 * PPM)
    for sun in SUNS:
        rows.append({"branch": SIDE["c4_productivity_at_150"], "plants": "C4 curve, 150 ppm threshold", "sun": SUNS[sun],
                     "S_star_over_S0": sstar, "Pi_ratio_at_threshold": pi,
                     "time_to_limit_Myr": time_to(sstar, sun) * MYR_PER_GYR})
    return rows


def _write(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: f"{v:.6g}" if isinstance(v, float) else v for k, v in r.items()})


def figure(path: Path, sh: list[dict], steps: list[dict], cells: list[dict]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker

    ink, muted, blue, orange = "#2b2b2b", "#8a8a85", "#2a78d6", "#eb6834"
    fig, (a, b) = plt.subplots(1, 2, figsize=(10.0, 4.2), gridspec_kw={"width_ratios": [1, 1.25]})
    lw_end = next(r["time_to_limit_Myr"] for r in cells if all(r[f"{k}_from"] == "L&W" for k in INGREDIENTS))
    ck_end = next(r["time_to_limit_Myr"] for r in cells if all(r[f"{k}_from"] == "C&K" for k in INGREDIENTS))
    names = {"sun": "Sun law", "co2": "CO$_2$ law", "plants": "Plants and threshold"}
    y = np.arange(len(sh))[::-1]
    for yi, r in zip(y, sh):
        a.plot([r["factor_min"], r["factor_max"]], [yi, yi], color=muted, lw=2, solid_capstyle="round")
        a.plot(r["shapley_factor"], yi, "o", color=blue, ms=8, mec="white", mew=1.5)
        a.annotate(f"x{r['shapley_factor']:.2f}", (r["shapley_factor"], yi), xytext=(0, 9),
                   textcoords="offset points", ha="center", fontsize=8, color=ink)
    a.axvline(1.0, color=muted, lw=0.8)
    a.set_xscale("log")
    a.set_xticks([0.5, 1, 2, 5, 10], ["0.5", "1", "2", "5", "10"])
    a.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    a.set_yticks(y, [names[r["ingredient"]] for r in sh])
    a.set_xlabel("Factor on time to the CO$_2$ limit\n(dot: Shapley mean; line: range over contexts)", fontsize=8)
    a.set_title(f"Time to the plants' CO$_2$ limit: L&W {lw_end:.0f} Myr to C&K {ck_end:.0f} Myr",
                fontsize=9, color=ink)
    a.set_ylim(-0.6, len(sh) - 0.4)

    seq = ("lw_rule", "ck_constant_T_pump_held", "ck_pump_held", "ck_biology")
    short = ["L&W rule", "C&K\ngreenhouse", "+ weathering\nbalance", "+ responsive\nsoil pump"]
    x = np.arange(len(seq))
    for (plants, (lab, _, _)), col in zip(PLANTS.items(), (orange, blue)):
        t = [next(r["time_to_limit_Myr"] for r in steps if r["plants"] == lab and r["step"] == k) for k in seq]
        b.plot(x, t, "-", color=col, lw=2)
        b.plot(x, t, "o", color=col, ms=8, mec="white", mew=1.5)
        b.annotate(lab, (x[-1], t[-1]), xytext=(6, 0), textcoords="offset points", va="center", fontsize=8, color=ink)
    b.set_yscale("log")
    b.set_yticks([50, 100, 200, 500, 1000], ["50", "100", "200", "500", "1,000"])
    b.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    b.set_xticks(x, short, fontsize=8)
    b.set_xlim(-0.3, len(seq) + 0.9)
    b.set_ylabel("Time to the CO$_2$ limit, eq. (1) Sun (Myr)", fontsize=8)
    b.set_title("The CO$_2$ law along one path (the order is a choice)", fontsize=9, color=ink)
    for ax in (a, b):
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(colors=ink, labelsize=8)
        ax.grid(axis="x" if ax is a else "y", color="#e4e4e0", lw=0.6)
        ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(path, dpi=120, metadata={"Software": None})
    plt.close(fig)


def main(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    cells = {k: factorial(k) for k in READINGS}
    sh = shapley(cells["faithful"])
    steps = co2_steps()
    _write(outdir / "ingredient_swap_cells.csv", [r for c in cells.values() for r in c])
    _write(outdir / "ingredient_swap_shapley.csv", sh + [r for k in READINGS if k != "faithful" for r in shapley(cells[k])])
    _write(outdir / "ingredient_swap_co2_steps.csv", steps)
    _write(outdir / "ingredient_swap_warming.csv", warming())
    _write(outdir / "ingredient_swap_side.csv", side_branches())
    figure(outdir / "ingredient_swap.png", sh, steps, cells["faithful"])


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models/biosphere_lifespan/swap"))
