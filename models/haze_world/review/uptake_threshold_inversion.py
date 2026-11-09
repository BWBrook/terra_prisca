"""Invert the published Fig. 3/4 crossover pressures for the A. bakii cessation threshold.

uv run python models/haze_world/review/uptake_threshold_inversion.py
For each rate basis, find the acetogen threshold that makes acetogen and methanogen uptake
equal at each crossover the text reports, with the methanogen threshold at 0 or 2 Pa, and
compare the implied temperature dependence with the van't Hoff shape the paper reports.
"""

import json
from pathlib import Path

import numpy as np

from terra_prisca.haze_world.hydrogen_uptake import ACETOGEN, MSB, MSP, parameters

HERE = Path(__file__).resolve().parent
DH_ACETOGENESIS_J = -270.7e3
R = 8.314
LANDMARKS = [(4.0, MSB, 80.0), (30.0, MSB, 1000.0), (15.0, MSP, 10.0)]


def specific(k, basis):
    return k.vmax_nmol_h / (1.0 if basis == "culture" else k.mass_mg)


def acetogen_threshold(temperature_c, opponent, crossover_pa, basis, methanogen_threshold_pa):
    m, a = parameters(temperature_c, opponent), parameters(temperature_c, ACETOGEN)
    x = crossover_pa - methanogen_threshold_pa
    vm = specific(m, basis) * x / (m.km_pa + x)
    va = specific(a, basis)
    return crossover_pa - vm * a.km_pa / (va - vm) if vm < va else None


def vant_hoff_ratio(t1_c, t2_c):
    return float(np.exp(DH_ACETOGENESIS_J / (4 * R) * (1 / (t2_c + 273.15) - 1 / (t1_c + 273.15))))


def main():
    out = {"enthalpy_J_per_mol_reaction": DH_ACETOGENESIS_J, "vant_hoff_ratio_30_over_4": vant_hoff_ratio(4, 30),
           "bases": {}}
    for basis in ("culture", "dry_mass"):
        implied = {f"{t:g}C_vs_{o.split()[-1]}_at_{p:g}Pa": [acetogen_threshold(t, o, p, basis, pm) for pm in (0.0, 2.0)]
                   for t, o, p in LANDMARKS}
        t4, t30, t15 = (float(np.mean(v)) for v in implied.values())
        out["bases"][basis] = {
            "implied_acetogen_threshold_pa": implied,
            "implied_ratio_30_over_4": t30 / t4,
            "predicted_15C_from_4C_pa": t4 * vant_hoff_ratio(4, 15),
            "predicted_15C_from_30C_pa": t30 / vant_hoff_ratio(15, 30),
            "implied_15C_from_MSP_landmark_pa": t15,
        }
    (HERE / "uptake_threshold_inversion.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
