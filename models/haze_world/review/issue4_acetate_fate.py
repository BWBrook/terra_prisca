"""Issue 4: how the acetate fate f shapes the exact window, the margin and graded sensitivity.

Bounded check on the production equilibrium and spectrum code (no new stage):
the exact-control supply window against f, with and without recycling of
exported biomass to methane; first-loss margins across the window at fixed
products; the acetate-feedback (D1 reference) sensitivity at the same supplies;
the habitat-spread factor Q/(Q-1) of equation (3.1); the planetary acetate flux the
non-methane sink must take; and the imposed-warming window at the geometric mid-window supply.
"""

import json
from pathlib import Path

import numpy as np

from terra_prisca.haze_world import continuum_core as model, dynamic_core as legacy, dynamic_realisation as b1
from terra_prisca.haze_world import continuum_experiments as ce, two_guilds as tg
from terra_prisca.haze_world import methane_budget as budget, population_coupling as core
from terra_prisca.haze_world.paper_figures import esm_tables

OUT = Path(__file__).with_suffix(".json")
FRACTIONS = (0., .5, .6, .7, .8, .9, .95, 1.)
POSITIONS = (.05, .25, .5, .75, .95)
BIOMASS = (0., .5, 1.)


def parts():
    ref = core.reference()
    bio = ref.biology
    state = next(s for s in core.equilibrium_states(ref) if s["kind"] == "mixed" and s["stable"])
    a, m = tg.guilds(state["t_k"] - 273.15, bio)
    eta = [1 - g.assimilation_mol_g * bio.loss_h / (g.maintenance + bio.loss_h / g.yield_g_mol) for g in (a, m)]
    abiotic = budget.atmosphere("B")["flux_to_ratio_per_yr"] * ref.climate.abiotic_flux
    needed = 4 * (state["r"] / ref.climate.lifetime_yr - abiotic) / (core.inventory_to_ratio(ref) * core.HOURS_PER_YEAR)
    outlet = bio.exchange_mol_l_h_pa * (state["y"][0] - bio.atmosphere_pa)
    return dict(eta_A=eta[0], eta_M=eta[1], needed=needed, outlet=outlet, j_ref=core.supply_h2(ref),
                mixed_ratio=state["r"], t_star=state["t_k"])


EARTH_AREA_CM2 = 4 * np.pi * 6.371e8 ** 2
SECONDS_PER_YEAR = 3.15576e7
AVOGADRO = 6.02214076e23


def diverted(q, f, P=.3):
    """Acetate leaving by non-methane routes at the fixed-product mixed state, in Tmol per year.

    Uptake splits so that methanogen and recycled acetogen catabolism meet the methane the climate state needs;
    the global scale is the case-B column flux implied by the assumed 10,000-yr lifetime.
    """
    uptake = P / .3 * q["j_ref"] - q["outlet"]
    u_A = (q["eta_M"] * uptake - q["needed"]) / (q["eta_M"] - f * q["eta_A"])
    ref = core.reference()
    flux = q["mixed_ratio"] / ref.climate.lifetime_yr / budget.atmosphere("B")["flux_to_ratio_per_yr"]
    tmol_ch4 = flux * EARTH_AREA_CM2 * SECONDS_PER_YEAR / AVOGADRO / 1e12
    methane_from_biota = tmol_ch4 - ref.climate.abiotic_flux * EARTH_AREA_CM2 * SECONDS_PER_YEAR / AVOGADRO / 1e12
    scale = methane_from_biota / (q["needed"] / 4)
    acetate = (1 - f) * q["eta_A"] * u_A / 4
    biomass = ((1 - q["eta_A"]) * u_A + (1 - q["eta_M"]) * (uptake - u_A)) / 4
    return dict(f=f, potential=P, acetogen_uptake_share=u_A / uptake,
                methane_tmol_yr=tmol_ch4, biotic_methane_tmol_yr=methane_from_biota,
                diverted_acetate_tmol_yr=acetate * scale, biomass_export_tmol_ch4eq_yr=biomass * scale,
                combined_export_tmol_ch4eq_yr=(acetate + biomass) * scale,
                max_f_at_potential=q["needed"] / (q["eta_A"] * (P / .3 * q["j_ref"] - q["outlet"])))


def window(q, f, b):
    """Supply potentials at which methanogens alone and acetogens alone hold T*, with biomass recycled at fraction b."""
    yM = q["eta_M"] + b * (1 - q["eta_M"])
    yA = f * q["eta_A"] + b * (1 - q["eta_A"])
    lo = .3 * (q["outlet"] + q["needed"] / yM) / q["j_ref"]
    hi = float("inf") if yA == 0 else .3 * (q["outlet"] + q["needed"] / yA) / q["j_ref"]
    return lo, hi


def state_metrics(chem, f, P):
    p0 = b1.parameters(chem, f, .001, P)
    out = []
    for s in legacy.equilibrium_states(p0):
        if s["kind"] != "mixed":
            continue
        m = ce.measure(s["y"], model.WeightedParams(p0.base, p0.chemistry))
        out.append(dict(temperature_k=m["temperature_k"], ratio=m["ratio"], Sc=m["Sc"], S0=m["S0"],
                        lag_status=m["lag"]["status"], tau_c=m["lag"]["tau_c"]))
    return out


def forcing_window(f, P):
    """Imposed-warming interval over which a cooling-branch exact state exists (1-K scan, ends bisected to 0.01 K)."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    import issue2_forcing as i2
    grid = np.arange(-20., 12.01, 1.)
    found = [F for F in grid if i2.exists(f, F, .195, P) is not None]
    assert found == list(np.arange(found[0], found[-1] + .5, 1.)), "window not contiguous on the 1-K scan"
    ends = []
    for inside, outside in ((found[0], found[0] - 1.), (found[-1], found[-1] + 1.)):
        while abs(outside - inside) > .01:
            mid = (inside + outside) / 2
            inside, outside = (mid, outside) if i2.exists(f, mid, .195, P) is not None else (inside, mid)
        ends.append(inside)
    i2.set_forcing(0.)
    return dict(f=f, potential=P, F_low=ends[0], F_high=ends[1], width_k=ends[1] - ends[0])


def main():
    q = parts()
    windows = []
    for b in BIOMASS:
        for f in FRACTIONS:
            lo, hi = window(q, f, b)
            windows.append(dict(biomass_recycled=b, f=f, low=lo, high=None if np.isinf(hi) else hi,
                                ratio=None if np.isinf(hi) else hi / lo,
                                fable_estimate=None if f == 0 else q["eta_M"] / (f * q["eta_A"]),
                                spread_factor=None if np.isinf(hi) or hi == lo else (hi / lo) / (hi / lo - 1)))
    bud = esm_tables.coexistence_budget()
    assert np.isclose(windows[1]["high"], bud["high"](.5), rtol=1e-12) and np.isclose(windows[1]["low"], bud["low"], rtol=1e-12)
    sweep = []
    for f in FRACTIONS[1:]:
        lo, hi = window(q, f, 0.)
        supplies = [(pos, lo + pos * (hi - lo)) for pos in POSITIONS] + [(None, .24), (None, .30)]
        for pos, P in supplies:
            for chem in ("fixed", "products"):
                for s in state_metrics(chem, f, P):
                    sweep.append(dict(chemistry=chem, f=f, window_position=pos, potential=P, **s))
    sinks = [diverted(q, f) for f in (0., .5, .7)] + [diverted(q, .9, .24)]
    spans = []
    for f in FRACTIONS[1:]:
        temps = [s["temperature_k"] for s in sweep if s["chemistry"] == "products" and s["f"] == f and s["window_position"] is not None]
        spans.append(dict(f=f, products_temperature_span_k=max(temps) - min(temps), positions=len(temps)))
    forcing = []
    for f in (.5, .7, .9, 1.):
        lo, hi = window(q, f, 0.)
        forcing.append(forcing_window(f, float(np.sqrt(lo * hi))))
    OUT.write_text(json.dumps(dict(parts=q, windows=windows, sweep=sweep, sinks=sinks, spans=spans, forcing=forcing), indent=1) + "\n")


if __name__ == "__main__":
    main()
