"""Independent local-sensitivity, Jacobian and return-threshold audit of 88fbad8.

uv run python models/haze_world/review/check_darwinian.py OUTPUT_DIRECTORY
Reads the committed endpoint table; does not change the evolutionary variant.
"""

import csv
from dataclasses import replace
import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import brentq

from terra_prisca.haze_world.darwinian import (
    Constraint, reference, singular_theta, strain, tendency,
)
from terra_prisca.haze_world.methane_budget import (
    atmosphere, capture_efficiency, growth_ratio, response, temperature_k,
)


def audit(output):
    p, losses = reference()
    laws = {loss.label: loss for loss in losses}
    conversion = atmosphere(p.case)["flux_to_ratio_per_yr"]
    climate = response(p.case)
    source = Path("models/haze_world/figures/darwinian_endpoints.csv")
    rows = []
    with source.open() as handle:
        inputs = list(csv.DictReader(handle))
    for original in inputs:
        law = laws[original["loss"]]
        constraint = Constraint(
            energy_ev=float(original["energy_ev"]),
            floor_k=float(original["floor_k"]) if original["floor_k"] else -np.inf,
        )

        def balance(r):
            t = float(temperature_k(r, p))
            return float(tendency(r, strain(p, singular_theta(t, constraint), constraint), law))

        approximate = float(original["r"])
        r = brentq(balance, approximate - 1e-5, approximate + 1e-5, xtol=1e-15)
        t = float(temperature_k(r, p, extend=False))
        theta = singular_theta(t, constraint)
        q = strain(p, theta, constraint)
        rho = float(growth_ratio(t, q))
        i = np.searchsorted(climate.ratios, r) - 1
        t_r = float(np.diff(climate.temperatures_k)[i] / np.diff(climate.ratios)[i])
        rho_t = -2 * q.growth_ratio_max * (t - theta) / q.t_halfwidth_k**2
        if law.kind == "power":
            loss_r = law.elasticity * float(law.rate(r)) / r
        else:
            loss_r = law.anchor_ratio / law.lifetime_yr / (
                (law.log_scale + r) * np.log1p(law.anchor_ratio / law.log_scale)
            )
        source_r = conversion * p.maintenance_flux * rho_t * t_r / (rho - 1)**2
        regulation = loss_r / (loss_r - source_r)
        derivative = t_r * conversion * p.donor_flux / (loss_r - source_r)

        k_donor, death = 0.1, 1.0
        half_sat = conversion * p.maintenance_flux / k_donor
        donor = half_sat / (rho - 1)
        biomass = (conversion * p.donor_flux - k_donor * donor) / death
        uptake_d = death * rho * biomass * half_sat / (half_sat + donor)**2
        uptake_m = death * biomass / rho * rho_t * t_r
        jacobian = np.array([
            [-k_donor - uptake_d, -death, -uptake_m],
            [uptake_d, 0, uptake_m],
            [uptake_d, death, uptake_m - loss_r],
        ])
        eigenvalue = float(np.max(np.linalg.eigvals(jacobian).real))
        assert eigenvalue < 0 and abs(balance(r)) < 1e-12
        assert abs(t - float(original["t_k"])) < 5.1e-5

        abiotic_ratio = law.inverse(conversion * p.abiotic_flux)
        rho_needed = 1 + p.maintenance_flux / p.donor_flux
        net_cold_edge = theta - q.t_halfwidth_k * np.sqrt(1 - rho_needed / q.growth_ratio_max)
        weight = np.log1p(abiotic_ratio / p.bridge_scale) / np.log1p(climate.ratios[0] / p.bridge_scale)
        assert 0 <= weight < 1
        critical_t0 = (net_cold_edge - weight * climate.temperatures_k[0]) / (1 - weight)
        row = dict(
            constraint=constraint.label, loss=law.label, energy_ev=constraint.energy_ev,
            floor_k=original["floor_k"], r=r, temperature_k=t, theta_k=theta,
            reported_regulation=float(original["regulation_ecological"]),
            local_regulation=regulation, reported_derivative=float(original["dT_dlnS_ecological"]),
            local_derivative=derivative, full_max_real_eigenvalue=eigenvalue,
            reported_eigenvalue=float(original["full_max_real_eig_per_yr"]),
            abiotic_ratio=abiotic_ratio, net_cold_edge_k=net_cold_edge,
            critical_bridge_t0_k=critical_t0,
        )
        for t0 in (265.0, 283.0):
            abiotic = replace(q, t_zero_k=t0)
            abiotic_t = float(temperature_k(abiotic_ratio, abiotic))
            exponent = float(growth_ratio(abiotic_t, abiotic)) / rho_needed - 1
            invades = exponent > 0
            assert invades == (original[f"invades_lifeless_T0_{t0:g}"] == "True")
            assert invades == bool(capture_efficiency(abiotic_t, abiotic) > 0)
            row[f"abiotic_temperature_T0_{t0:g}"] = abiotic_t
            row[f"invasion_exponent_T0_{t0:g}"] = exponent
        rows.append(row)

    output.mkdir(parents=True, exist_ok=True)
    with (output / "darwinian_local_audit.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary = dict(
        reviewed_commit="88fbad8", endpoints=len(rows), all_full_jacobians_stable=True,
        max_eigenvalue_rounding_error=max(abs(r["full_max_real_eigenvalue"] - r["reported_eigenvalue"]) for r in rows),
        max_regulation_absolute_error=max(abs(r["local_regulation"] - r["reported_regulation"]) for r in rows),
        max_cold_edge_vs_critical_bridge_t0_difference_k=max(abs(r["net_cold_edge_k"] - r["critical_bridge_t0_k"]) for r in rows),
        max_linear_loss_plot_threshold_error_k=max(abs(r["net_cold_edge_k"] - r["critical_bridge_t0_k"]) for r in rows if r["loss"] == "power n=1"),
        reinvasion_labels_reproduced=True,
    )
    (output / "darwinian_local_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    audit(Path(sys.argv[1]))
