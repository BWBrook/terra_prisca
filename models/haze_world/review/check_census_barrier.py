"""Check the mean-immigration census barrier from an initially absent guild.

uv run python models/haze_world/review/check_census_barrier.py
"""

from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from terra_prisca.haze_world.finite_experiments import clean, source_hashes
from terra_prisca.haze_world.finite_populations import CellProcess, integrate_finite
from terra_prisca.haze_world.population_coupling import equilibrium_states, fluxes, reference


def main():
    p = replace(reference(), acetate_fraction=0.)
    initial = next(e["y"] for e in equilibrium_states(replace(p, enabled=(True, False)))
                   if e["kind"] == "acetogen" and e["stable"])
    growth = float(fluxes(initial, p)["net_growth_yr"][1])
    rows = []
    for interval in (1., 10.):
        process = CellProcess(census_yr=interval, immigration_cells_yr=(.1, .1))
        result = integrate_finite(initial, p, 100., process, sample_every_censuses=1)
        returns = [e for e in result.arrival_events if e["guild"] == "methanogen"]
        removals = [e for e in result.extinction_events if e["guild"] == "methanogen"]
        predicted = .1 * np.expm1(growth * interval) / growth
        first_count = removals[0]["removed_cells"] if interval == 1 else returns[0]["retained_cells"]
        assert np.isclose(first_count, predicted, rtol=1e-4)
        if interval == 1:
            assert not returns and len(removals) == 100 and result.y[2, -1] == 0
        else:
            assert returns[0]["time_yr"] == 10 and not removals
        rows.append(dict(census_yr=interval, fixed_environment_first_count=predicted,
                         integrated_first_pre_removal_count=first_count,
                         first_retained_methanogen_yr=returns[0]["time_yr"] if returns else None,
                         methanogen_removals=len(removals),
                         final_cells_m=result.y[2, -1] * result.metadata["total_habitat_l"] / process.cell_mass_gdw,
                         cell_process=asdict(process)))
    record = dict(parameters=asdict(p), initial_y=initial, initial_methanogen_growth_yr=growth,
                  duration_yr=100., results=rows, source_sha256=source_hashes(),
                  checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                  protocol="Pure acetogen equilibrium; methanogens exactly absent; both guilds receive mean immigration from t=0",
                  scope="Full coupled short check of a census-induced establishment barrier; different initial protocol from the main seeded invasions, not a 100000-year endpoint or stochastic probability")
    Path(__file__).with_name("census_barrier_check.json").write_text(
        json.dumps(clean(record), indent=2, allow_nan=False) + "\n")
    print(json.dumps(clean(rows), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
