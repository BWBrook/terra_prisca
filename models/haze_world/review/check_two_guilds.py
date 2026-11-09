"""Independent balance, invasion and local-Jacobian review of stage 3.

uv run python models/haze_world/review/check_two_guilds.py

This conditions on the implemented source transfers; it does not calibrate
field conditions or establish global stability. No transient runs are used.
"""

from collections import Counter
from dataclasses import asdict, replace
from hashlib import sha256
import itertools
import json
from pathlib import Path

import numpy as np

from terra_prisca.haze_world.two_guilds import (
    Competition, HENRY_30C_MOL_L_PA, MSB, MSP, delivery, equilibrium, guilds,
    parameter_grid, thresholds,
)

ROOT = Path(__file__).resolve().parents[3]
SUPPLY = 1e-6
TEMPERATURES = (4., 20., 30.)


def resident_jacobians(guild, pressure, biomass, loss):
    """Hand-derived and central-difference Jacobians in pressure, biomass."""
    rate = float(guild.uptake(pressure))
    available = pressure - guild.threshold_pa
    slope = guild.rate_scale / guild.km_pa
    if guild.kinetics == "saturating":
        slope = guild.rate_scale * guild.km_pa / (guild.km_pa + available) ** 2
    analytic = np.array([
        [-slope * biomass / HENRY_30C_MOL_L_PA, -rate / HENRY_30C_MOL_L_PA],
        [guild.yield_g_mol * slope * biomass, 0.],
    ])

    def rhs(state):
        p, x = state
        q = float(guild.uptake(p))
        return np.array([(SUPPLY - q * x) / HENRY_30C_MOL_L_PA,
                         x * (guild.yield_g_mol * (q - guild.maintenance) - loss)])

    center = np.array([pressure, biomass])
    steps = np.array([available, biomass]) * 1e-5
    numeric = np.column_stack([
        (rhs(center + np.eye(2)[i] * step) - rhs(center - np.eye(2)[i] * step)) / (2 * step)
        for i, step in enumerate(steps)
    ])
    assert np.allclose(analytic, numeric, rtol=1e-7, atol=1e-10)
    return analytic, numeric


def main():
    maxima = dict(resource_balance_error_mol_l_h=0., resident_growth_abs_h=0.,
                  invader_growth_h=-np.inf, local_eigenvalue_real_h=-np.inf,
                  jacobian_relative_difference=0., methane_h2_input_fraction=0.)
    statuses = Counter()
    scenarios = []
    for strain, form, threshold_shape in itertools.product(
        (MSB, MSP), ("saturating", "first_order"), ("constant", "fixed_energy")
    ):
        configurations = [replace(c, kinetics=form, threshold_shape=threshold_shape)
                          for c in parameter_grid(strain)]
        assert len(configurations) == 243
        scenarios.extend(asdict(c) for c in configurations)
        for config, temperature in itertools.product(configurations, TEMPERATURES):
            eq = equilibrium(temperature, config, SUPPLY)
            statuses[eq["status"]] += 1
            if eq["status"] != "living":
                continue
            pair = guilds(temperature, config)
            winner = 0 if eq["winner"] == "acetogen" else 1
            resident = pair[winner]
            pressure = eq["pressure_pa"]
            biomass = eq["biomass_g_l"][winner]
            rate = float(resident.uptake(pressure))
            net_growth = resident.yield_g_mol * (rate - resident.maintenance) - config.loss_h
            invader = pair[1 - winner]
            invasion = float(invader.yield_g_mol * (invader.uptake(pressure) - invader.maintenance) - config.loss_h)
            assert invasion == eq["invader_growth_h"]
            analytic, numeric = resident_jacobians(resident, pressure, biomass, config.loss_h)
            relative = np.abs((numeric[analytic != 0] - analytic[analytic != 0]) / analytic[analytic != 0])
            maxima["jacobian_relative_difference"] = max(maxima["jacobian_relative_difference"], max(relative))
            eigenvalues = np.r_[np.linalg.eigvals(analytic).real, np.linalg.eigvals(numeric).real, invasion]
            maxima["local_eigenvalue_real_h"] = max(maxima["local_eigenvalue_real_h"], max(eigenvalues))
            maxima["invader_growth_h"] = max(maxima["invader_growth_h"], invasion)
            maxima["resource_balance_error_mol_l_h"] = max(maxima["resource_balance_error_mol_l_h"], abs(rate * biomass - SUPPLY))
            maxima["resident_growth_abs_h"] = max(maxima["resident_growth_abs_h"], abs(net_growth))
            for fraction in (0., .5, 1.):
                products = delivery(pressure, eq["biomass_g_l"], temperature, config, fraction)
                total = sum(products["catabolic_h2_mol_l_h"]) + sum(products["biomass_h2_mol_l_h"])
                assert abs(total - SUPPLY) < 1e-16
                assert min(products["catabolic_h2_mol_l_h"]) >= 0
                methane_fraction = 4 * products["methane_mol_l_h"] / SUPPLY
                assert 0 <= methane_fraction <= 1 + 1e-12
                maxima["methane_h2_input_fraction"] = max(maxima["methane_h2_input_fraction"], methane_fraction)

    assert statuses["living"] == 5508
    assert maxima["resource_balance_error_mol_l_h"] < 1e-18
    assert maxima["resident_growth_abs_h"] < 1e-16
    assert maxima["invader_growth_h"] < 0
    assert maxima["local_eigenvalue_real_h"] < 0
    for threshold_shape in ("constant", "fixed_energy"):
        config = Competition(methanogen=MSP, threshold_shape=threshold_shape, msp_threshold_4c=200.)
        assert abs(thresholds(4., config)[1] - 200.) < 1e-12
        assert thresholds(15., config)[1] == thresholds(15., replace(config, methanogen=MSB))[1]
    try:
        Competition(maintenance_m30=0., loss_h=0.)
    except ValueError:
        pass
    else:
        raise AssertionError("Zero total demand must not produce a finite stationary population")

    files = (
        "models/haze_world/review/check_two_guilds.py",
        "src/terra_prisca/haze_world/two_guilds.py",
        "src/terra_prisca/haze_world/woodii1998.py",
        "src/terra_prisca/haze_world/hydrogen_uptake.py",
        "models/haze_world/evidence/peters1998_chemostat.csv",
        "models/haze_world/evidence/kotsyurbenko2001_table2.csv",
    )
    condition = dict(temperatures_c=TEMPERATURES, supply_mol_l_h=SUPPLY,
                     structures=8, parameter_sets_per_structure=243,
                     warm_pattern_filter=False, msp_threshold_4c_pa=20.,
                     acetate_routing_fractions=[0., .5, 1.])
    result = dict(
        conditioning=condition, statuses=dict(statuses), maxima={k: float(v) for k, v in maxima.items()},
        msp_threshold_endpoints_verified=True, zero_demand_input_rejected=True,
        configuration_sha256=sha256(json.dumps(scenarios, sort_keys=True).encode()).hexdigest(),
        file_sha256={name: sha256((ROOT / name).read_bytes()).hexdigest() for name in files},
        scope="Local stability and mass-balance review conditional on model transfers; no global, transient, field or climate validation",
    )
    output = Path(__file__).with_name("two_guilds_review.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(statuses=result["statuses"], maxima=result["maxima"]), indent=2))


if __name__ == "__main__":
    main()
