"""Independent crossover-inversion and approximate-landmark sensitivity checks.

uv run python models/haze_world/review/check_uptake_inversion.py OUTPUT_DIRECTORY
Marginal parameter boxes and the 10% landmark shifts are not confidence regions.
"""

from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

from terra_prisca.haze_world.hydrogen_uptake import ACETOGEN, MSB, MSP, parameters

MASS_RANGES = {ACETOGEN: (3.0, 4.2), MSB: (5.8, 8.2), MSP: (6.2, 7.0)}


def inverse(p, va, ka, vm, km, pm):
    rate = vm * (p - pm) / (km + p - pm)
    if not 0 < rate < va:
        return None
    return p - ka * rate / (va - rate)


def rate(p, vmax, km, threshold):
    excess = max(p - threshold, 0.0)
    return vmax * excess / (km + excess)


def main(output):
    corners = []
    for t, opponent, pressure in ((4, MSB, 80), (15, MSP, 10), (30, MSB, 1000)):
        a, m = parameters(t, ACETOGEN), parameters(t, opponent)
        for basis in ("culture", "dry_mass"):
            values = []
            for va, ka, vm, km, ma, mm, pm in product(
                (a.vmax_nmol_h - a.vmax_ci, a.vmax_nmol_h + a.vmax_ci),
                (a.km_pa - a.km_ci, a.km_pa + a.km_ci),
                (m.vmax_nmol_h - m.vmax_ci, m.vmax_nmol_h + m.vmax_ci),
                (m.km_pa - m.km_ci, m.km_pa + m.km_ci),
                MASS_RANGES[ACETOGEN] if basis == "dry_mass" else (1.0,),
                MASS_RANGES[opponent] if basis == "dry_mass" else (1.0,),
                (0.0, 2.0),
            ):
                threshold = inverse(pressure, va / ma, ka, vm / mm, km, pm)
                if threshold is not None:
                    values.append(threshold)
            physical = [v for v in values if 0 <= v < pressure]
            corners.append(dict(temperature_c=t, opponent=opponent, nominal_pressure_pa=pressure,
                                basis=basis, minimum_raw_threshold_pa=min(values),
                                maximum_threshold_pa=max(values),
                                minimum_physical_corner_pa=min(physical),
                                negative_threshold_corners=sum(v < 0 for v in values)))

    witness = []
    inputs = ((4, MSB, 72, 240, 220, 120, 40, 0.1, None),
              (15, MSP, 10, 640, 260, 200, 190, 1.0, 7.0),
              (30, MSB, 900, 700, 570, 620, 140, 1.0, None))
    for t, opponent, pressure, va, ka, vm, km, pm, threshold in inputs:
        ma, mm = 4.2, 5.8 if opponent == MSB else 7.0
        a, m = parameters(t, ACETOGEN), parameters(t, opponent)
        assert a.vmax_nmol_h - a.vmax_ci <= va <= a.vmax_nmol_h + a.vmax_ci
        assert a.km_pa - a.km_ci <= ka <= a.km_pa + a.km_ci
        assert m.vmax_nmol_h - m.vmax_ci <= vm <= m.vmax_nmol_h + m.vmax_ci
        assert m.km_pa - m.km_ci <= km <= m.km_pa + m.km_ci
        if threshold is None:
            threshold = inverse(pressure, va / ma, ka, vm / mm, km, pm)
        aa, bb = rate(pressure, va / ma, ka, threshold), rate(pressure, vm / mm, km, pm)
        if t != 15:
            assert abs(aa - bb) < 1e-12
        else:
            assert aa > bb
        witness.append(dict(temperature_c=t, opponent=opponent, pressure_pa=pressure,
                            acetogen_vmax_culture=va, acetogen_km_pa=ka,
                            methanogen_vmax_culture=vm, methanogen_km_pa=km,
                            acetogen_mass_mg=ma, methanogen_mass_mg=mm,
                            methanogen_threshold_pa=pm, acetogen_threshold_pa=threshold,
                            acetogen_specific_rate=aa, methanogen_specific_rate=bb))
    thresholds = [r["acetogen_threshold_pa"] for r in witness]
    assert 0 < thresholds[0] < thresholds[1] < thresholds[2] < 200
    output.mkdir(parents=True, exist_ok=True)
    result = dict(corner_scope="Nominal landmarks fixed; independent reported marginal ranges, not a joint confidence region",
                  corners=corners, dry_mass_witness=witness,
                  witness_scope="Illustrative 10% lower 4C and 30C crossovers; 15C dominance above 10 Pa treated as an inequality",
                  common_biomass="Same acetogen and MSB mass across temperatures; not a fitted or probabilistic estimate",
                  vant_hoff_30_over_4={str(gc): float(np.exp((-270700 - gc) / (4 * 8.314462618) *
                      (1 / 303.15 - 1 / 277.15))) for gc in (0, -20000, -28000)})
    (output / "inversion_challenge.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
