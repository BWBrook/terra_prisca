"""Ingredient swap between Lovelock & Whitfield (1982) and Caldeira & Kasting (1992).

An analysis built on the two faithful reconstructions, not a reconstruction:
it imports lw1982 and ck1992 and changes neither.

    uv run python -m terra_prisca.biosphere_lifespan.ingredient_swap [outdir]

L&W give the biosphere about 80 Myr; C&K give it 0.77 Gyr. Three ingredients
separate them, each with one setting per paper:

  sun    -- L&W's straight Sun line (0.0733/Gyr) | C&K eq. (1)
  co2    -- L&W's rule, sqrt(CO2) linear in luminosity between dated anchors,
            temperature held constant | C&K's weathering balance with soil CO2
            raised by plants, eqs (1)-(8), temperature free
  plants -- C3, life ends at 150 ppm | C4, life ends at 10 ppm. In C&K this
            sets both the productivity curve's Pmin and the threshold; in L&W
            only the threshold.

Both models are sequences of equilibria, so each lifespan is fixed by the
brightening S*/S0 at which CO2 meets the threshold, and the Sun law turns S*
into time. The eight combinations are scored, and the change from L&W to C&K
is shared among the ingredients by Shapley values (the mean of each
ingredient's effect over all orders of swapping), in ln(lifespan) and in Myr.
The co2 ingredient is then split along its nested steps: C&K's greenhouse at
constant temperature, temperature free with the soil pump held at Pi0, and the
full biology.
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
PLANTS = {"C3": ("C3, life ends at 150 ppm", 150.0, ck.C3), "C4": ("C4, life ends at 10 ppm", 10.0, ck.FAITHFUL)}

# The co2 ingredient and the nested steps between its two settings. Each C&K
# law is a ck1992 reading for the plants in use (only Pmin differs).
LAWS = {
    "lw_rule": "L&W rule: sqrt(CO2) linear in luminosity, T constant",
    "ck_constant_T": "C&K greenhouse and albedo, eqs (2)-(5), T held at T0",
    "ck_pump_held": "C&K weathering, T free, soil pump held at Pi0 (Volk's case W3)",
    "ck_biology": "C&K weathering with plants, eqs (6)-(8): the faithful model",
}
SIDE = {"whk_weathering": "side branch: WHK weathering on Patm, T free (neither paper)",
        "c4_productivity_at_150": "side branch: C4 productivity curve, threshold 150 ppm"}


def brightness(t_gyr: float, sun: str) -> float:
    """S/S0 at t Gyr from today."""
    return float(lw.luminosity(t_gyr * MYR_PER_GYR)) if sun == "straight" else float(ck.solar(t_gyr)) / ck.S0


def time_to(s_ratio: float, sun: str) -> float:
    """Gyr until the Sun reaches s_ratio (the inverse of brightness)."""
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


CK_READINGS = {"faithful": 1.0, "so2_fitted": ck.SO2_FIT_FACTOR}  # SO2 factor of C&K's weathering


def _reading(law: str, plants: str, so2: float = 1.0) -> ck.Reading:
    r = replace(PLANTS[plants][2], so2_factor=so2) if so2 != 1.0 else PLANTS[plants][2]
    if law == "ck_pump_held":
        return replace(r, name=LAWS[law], productivity="constant")
    if law == "whk_weathering":
        return replace(r, name=SIDE[law], weathering="whk")
    return r


def s_star(law: str, plants: str, sun: str = "eq1", threshold_ppm: float | None = None, so2: float = 1.0) -> float:
    """S*/S0: the brightening at which CO2 first falls to the threshold.
    C&K's laws do not depend on the Sun law (CO2 depends on time only through
    S), so they are solved under eq. (1) and mapped."""
    thr = PLANTS[plants][1] if threshold_ppm is None else threshold_ppm
    if law == "lw_rule":
        lum = lw.luminosity if sun == "straight" else (lambda t_myr: brightness(t_myr / MYR_PER_GYR, "eq1"))
        return lw_rule_s_star(thr, lum)
    if law == "ck_constant_T":
        t = ck.constant_T_time(thr * PPM, ck.FAITHFUL, T_MAX_GYR)
    else:
        t = ck.co2_time(thr * PPM, _reading(law, plants, so2), T_MAX_GYR)
    return brightness(t, "eq1") if np.isfinite(t) else float("nan")


def lifespan_myr(law: str, plants: str, sun: str, threshold_ppm: float | None = None, so2: float = 1.0) -> float:
    return time_to(s_star(law, plants, sun, threshold_ppm, so2), sun) * MYR_PER_GYR


ENDS = {"L&W": {"sun": "straight", "co2": "lw_rule", "plants": "C3"},
        "C&K": {"sun": "eq1", "co2": "ck_biology", "plants": "C4"}}
INGREDIENTS = ("sun", "co2", "plants")


def factorial(ck_reading: str = "faithful") -> list[dict]:
    """The eight combinations of the two papers' settings."""
    so2 = CK_READINGS[ck_reading]
    rows = []
    for pick in product(("L&W", "C&K"), repeat=3):
        st = {k: ENDS[p][k] for k, p in zip(INGREDIENTS, pick)}
        sstar = s_star(st["co2"], st["plants"], st["sun"], so2=so2)
        rows.append({"ck_reading": ck_reading, **{f"{k}_from": p for k, p in zip(INGREDIENTS, pick)},
                     "sun": SUNS[st["sun"]], "co2": LAWS[st["co2"]], "plants": PLANTS[st["plants"]][0],
                     "S_star_over_S0": sstar, "lifespan_Myr": time_to(sstar, st["sun"]) * MYR_PER_GYR})
    return rows


def shapley(cells: list[dict]) -> list[dict]:
    """Each ingredient's share of the change from L&W to C&K: its effect
    averaged over the six orders of swapping, with the smallest and largest
    effect it has in any context."""
    life = {tuple(r[f"{k}_from"] for k in INGREDIENTS): r["lifespan_Myr"] for r in cells}

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
        rows.append({"ck_reading": cells[0]["ck_reading"], "ingredient": ing, "L&W setting": _label(ing, "L&W"), "C&K setting": _label(ing, "C&K"),
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


def co2_steps() -> list[dict]:
    """The co2 ingredient split into its nested steps, under the eq. (1) Sun,
    for each plant setting. The steps are nested, not interchangeable: the
    greenhouse swap is defined only at constant T (L&W's rule has no T), and
    the soil pump only once T is free."""
    rows = []
    for plants in PLANTS:
        prev = None
        for law in LAWS:
            sstar = s_star(law, plants, "eq1")
            t = time_to(sstar, "eq1") * MYR_PER_GYR
            T = float("nan") if law == "lw_rule" else ck.temperature(sstar * ck.S0, PLANTS[plants][1] * PPM)
            rows.append({"plants": PLANTS[plants][0], "step": LAWS[law], "S_star_over_S0": sstar,
                         "T_at_threshold_K": T, "T_minus_T0_K": T - ck.t0(), "lifespan_Myr": t,
                         "factor": t / prev if prev else float("nan"), "change_Myr": t - prev if prev else float("nan")})
            prev = t
    return rows


def side_branches() -> list[dict]:
    rows = []
    for plants in PLANTS:
        for sun in SUNS:
            sstar = s_star("whk_weathering", plants, "eq1")
            rows.append({"branch": SIDE["whk_weathering"], "plants": PLANTS[plants][0], "sun": SUNS[sun],
                         "S_star_over_S0": sstar, "lifespan_Myr": time_to(sstar, sun) * MYR_PER_GYR})
    for sun in SUNS:
        sstar = s_star("ck_biology", "C4", "eq1", threshold_ppm=150.0)
        rows.append({"branch": SIDE["c4_productivity_at_150"], "plants": "C4 curve, 150 ppm threshold", "sun": SUNS[sun],
                     "S_star_over_S0": sstar, "lifespan_Myr": time_to(sstar, sun) * MYR_PER_GYR})
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
    lw_end = next(r["lifespan_Myr"] for r in cells if all(r[f"{k}_from"] == "L&W" for k in INGREDIENTS))
    ck_end = next(r["lifespan_Myr"] for r in cells if all(r[f"{k}_from"] == "C&K" for k in INGREDIENTS))
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
    a.set_xlabel("Factor on lifespan (dot: Shapley mean; line: range over contexts)")
    a.set_title(f"L&W {lw_end:.0f} Myr to C&K {ck_end:.0f} Myr", fontsize=9, color=ink)
    a.set_ylim(-0.6, len(sh) - 0.4)

    short = ["L&W rule", "C&K greenhouse,\nT constant", "T free,\npump held", "plants\n(faithful)"]
    x = np.arange(len(LAWS))
    for (plants, (lab, _, _)), col in zip(PLANTS.items(), (orange, blue)):
        t = [r["lifespan_Myr"] for r in steps if r["plants"] == lab]
        b.plot(x, t, "-", color=col, lw=2)
        b.plot(x, t, "o", color=col, ms=8, mec="white", mew=1.5)
        b.annotate(lab, (x[-1], t[-1]), xytext=(6, 0), textcoords="offset points", va="center", fontsize=8, color=ink)
    b.set_yscale("log")
    b.set_yticks([50, 100, 200, 500, 1000], ["50", "100", "200", "500", "1,000"])
    b.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    b.set_xticks(x, short, fontsize=8)
    b.set_xlim(-0.3, len(LAWS) + 0.9)
    b.set_ylabel("Lifespan under eq. (1) Sun (Myr)")
    b.set_title("The CO$_2$ law, step by step", fontsize=9, color=ink)
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
    cells = factorial()
    sh = shapley(cells)
    fitted = factorial("so2_fitted")
    steps = co2_steps()
    _write(outdir / "ingredient_swap_cells.csv", cells + fitted)
    _write(outdir / "ingredient_swap_shapley.csv", sh + shapley(fitted))
    _write(outdir / "ingredient_swap_co2_steps.csv", steps)
    _write(outdir / "ingredient_swap_side.csv", side_branches())
    figure(outdir / "ingredient_swap.png", sh, steps, cells)


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("models/biosphere_lifespan/swap"))
