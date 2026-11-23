"""Issue 5: the planetary size of the reference hydrogen supply, and what a fermentation-fed supply implies.

Arithmetic on stored numbers only (issue4_acetate_fate.json); no model is run.

The per-litre supply J has no planetary volume of its own. Its planetary scale comes from the methane flux
r*/tau that holds the mixed state's methane against the assumed 10-kyr lifetime: the conversion is
biotic methane (Tmol CH4 / yr) divided by the needed catabolic methane flux per litre. At fixed supply potential P
the planetary flux therefore scales as 1/tau.

Fermentation: complete degradation of carbohydrate by fermenters at low hydrogen gives
C6H12O6 + 2 H2O -> 2 CH3COOH + 2 CO2 + 4 H2, so the fermenters deliver a acetate methane-equivalents per hydrogen
methane-equivalent, a = 2. If that acetate shares the acetogens' acetate fate f, a fraction f of it becomes methane
outside the hydrogen competition. Holding T* then needs
    eta_M (J - e) + f a J = n   (methanogens alone)   and   f eta_A (J - e) + f a J = n   (acetogens alone),
which bound the exact window. Here e is the hydrogen outlet at R* and n the hydrogen-equivalent methane need.
"""

import json
from pathlib import Path

ISSUE4 = Path(__file__).with_name("issue4_acetate_fate.json")
OUT = Path(__file__).with_suffix(".json")
HOURS_PER_YEAR = 8766.
LIFETIME_YR = 1.0e4
LIFETIME_RANGE_YR = (6.0e3, 1.9e4)
FERMENTATION_ACETATE_PER_H2 = 2.
CARBON_PER_H2 = 1.5


def main():
    d = json.loads(ISSUE4.read_text())
    q = d["parts"]
    sink = next(s for s in d["sinks"] if s["f"] == .5)
    j, e, n = q["j_ref"], q["outlet"], q["needed"]
    scale = sink["biotic_methane_tmol_yr"] / (n / 4)
    supply = j * scale
    parts = dict(methane_route=4 * sink["biotic_methane_tmol_yr"],
                 export_route=4 * sink["combined_export_tmol_ch4eq_yr"],
                 outlet_to_atmosphere=e * scale)
    assert abs(sum(parts.values()) - supply) < 1e-9 * supply
    to_tmol = lambda P: P / .3 * supply
    windows = {str(w["f"]): dict(f=w["f"], P_lo=w["low"], P_hi=w["high"],
                                 h2_lo_tmol_yr=to_tmol(w["low"]),
                                 h2_hi_tmol_yr=None if w["high"] is None else to_tmol(w["high"]))
               for w in d["windows"] if w["biomass_recycled"] == 0.}
    eff_volume_l = scale * 1e12 / HOURS_PER_YEAR

    a = FERMENTATION_ACETATE_PER_H2
    fermentation = []
    for f in (0., .5, .7, .9, 1.):
        lo = (n + q["eta_M"] * e) / (q["eta_M"] + f * a)
        hi = None if f == 0 else (n + f * q["eta_A"] * e) / (f * q["eta_A"] + f * a)
        at = j if hi is None else (lo * hi) ** .5
        u_A = (q["eta_M"] * (at - e) - (n - f * a * at)) / (q["eta_M"] - f * q["eta_A"])
        fermenter_leaving = (1 - f) * a * at * scale / 4
        acetogen_leaving = (1 - f) * q["eta_A"] * u_A * scale / 4
        fermentation.append(dict(
            f=f, J_lo=lo, J_hi=hi, ratio=None if hi is None else hi / lo,
            P_lo=.3 * lo / j, P_hi=None if hi is None else .3 * hi / j,
            h2_window_lo_tmol_yr=lo * scale, h2_window_hi_tmol_yr=None if hi is None else hi * scale,
            evaluated_at="reference J" if hi is None else "geometric mid-window",
            h2_tmol_yr=at * scale,
            fermenter_acetate_methane_at_reference_supply_tmol_yr=f * a * j * scale / 4,
            fermentation_acetate_tmol_yr=a * at * scale / 4,
            carbohydrate_carbon_fermented_tmol_c_yr=CARBON_PER_H2 * at * scale,
            fermenter_acetate_leaving_tmol_yr=fermenter_leaving,
            acetogen_acetate_leaving_tmol_yr=acetogen_leaving,
            acetate_leaving_total_tmol_yr=fermenter_leaving + acetogen_leaving,
            share_of_biotic_methane_outside_competition=f * a * at / n))
    out = dict(
        source=str(ISSUE4.name),
        scale_tmol_yr_per_mol_l_h=scale,
        effective_volume_l=eff_volume_l,
        reference=dict(P=.3, J_mol_l_h=j, h2_tmol_yr=supply, ch4_equivalent_tmol_yr=supply / 4,
                       parts_tmol_h2_yr=parts,
                       methane_total_tmol_yr=sink["methane_tmol_yr"],
                       methane_flux_molecules_cm2_s=sink["methane_tmol_yr"] * 1e12 * 6.02214076e23
                       / (4 * 3.141592653589793 * 6.371e8 ** 2 * 3.15576e7)),
        lifetime_scaling={f"{t:.0f}": supply * LIFETIME_YR / t for t in LIFETIME_RANGE_YR},
        windows=windows,
        fermentation=fermentation,
    )
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    return out


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
