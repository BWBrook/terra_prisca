"""Units, Pirt fit and cross-assay compatibility checks; no new population model.

uv run python models/haze_world/review/check_growth_parameters.py OUTPUT_DIRECTORY
"""

import csv
import json
from pathlib import Path
import sys

import numpy as np

from terra_prisca.haze_world.hydrogen_uptake import ACETOGEN, parameters


def main(output):
    data = Path(__file__).resolve().parents[1] / "evidence/peters1998_chemostat.csv"
    with data.open() as handle:
        rows = list(csv.DictReader(handle))
    growth = np.array([float(r["dilution_h^-1"]) for r in rows])
    observed_yield = np.array([float(r["observed_Y_acetate_gDW_mol"]) for r in rows])
    slope, intercept = np.polyfit(growth, growth / observed_yield, 1)
    h2_yield = 1 / (4 * (1 / 7.7 + 0.0206))
    maintenance = 4 * 0.40
    a = parameters(30, ACETOGEN)
    qmax_mmol = a.vmax_nmol_h / a.mass_mg * 1e-3
    checks = dict(
        pirt_fit_to_rounded_means=dict(true_acetate_yield=1 / slope,
                                      maintenance_mmol_acetate_gdw_h=intercept * 1000),
        carbon_balance=dict(true_H2_yield_gdw_mol=h2_yield,
                            maintenance_mmol_H2_gdw_h=maintenance),
        modern_observed_yield_from_mu_over_q=0.054 / 0.0669,
        historical_qmax_mmol_H2_gdw_h=qmax_mmol,
        cross_assay_maintenance_to_qmax_ratio=maintenance / qmax_mmol,
        cross_assay_implied_yields=[])
    for temperature, growth_per_day in ((10, 0.16), (20, 0.53)):
        p = parameters(temperature, ACETOGEN)
        q = p.vmax_nmol_h / p.mass_mg * 1e-6
        checks["cross_assay_implied_yields"].append(dict(temperature_c=temperature,
            yield_gdw_mol_H2=(growth_per_day / 24) / q,
            status="assay-compatibility diagnostic, not a biological estimate"))
    assert 1.6 < h2_yield < 1.7
    assert abs(checks["modern_observed_yield_from_mu_over_q"] - 0.82) < 0.08
    assert checks["cross_assay_maintenance_to_qmax_ratio"] > 7
    output.mkdir(parents=True, exist_ok=True)
    (output / "growth_parameter_checks.json").write_text(json.dumps(checks, indent=2) + "\n")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
