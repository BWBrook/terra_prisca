"""Bounded Fig. 2/4 checks; requires the archived local transient NPZs.

    uv run python models/haze_world/review/paper_transient_figure_check.py

No trajectories are integrated. The receipt records finite-window periods,
matched B3 stability and the finite-census sources of every plotted Fig. 4 row.
"""

import csv
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.linalg import eigvals
from scipy.signal import find_peaks

from terra_prisca.haze_world import dynamic_core as dc
from terra_prisca.haze_world import dynamic_realisation as dr
from terra_prisca.haze_world import dynamic_transients as dt
from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world.finite_populations import CellProcess
from terra_prisca.haze_world.paper_figures import fig4

ROOT = Path(__file__).resolve().parents[3]
DYN = ROOT / "models/haze_world/figures/dynamic_realisation"
DATA = ROOT / "models/haze_world/paper/figures/data"


def check():
    records = {r["case_id"]: r for r in json.loads((DYN / "transient_manifest.json").read_text())["rows"]}
    record = records["B2_f0_tau1"]
    raw = ROOT / record["uncensored_raw"]
    assert sha256(raw.read_bytes()).hexdigest() == record["uncensored_sha256"]
    with np.load(raw) as data:
        t, temperature = data["t"], data["temperature_k"]
    late = t >= 24000
    peaks, _ = find_peaks(temperature[late], prominence=.3, distance=100)
    peak_times = t[late][peaks]
    periods = np.diff(peak_times)
    windows = [dict(start_yr=left, end_yr=left + 3000,
                    temperature_span_k=float(np.ptp(temperature[(t >= left) & (t <= left + 3000)])))
               for left in (18000, 21000, 24000, 27000)]
    period = dict(raw=record["uncensored_raw"], sha256=record["uncensored_sha256"],
                  peak_times_yr=peak_times.tolist(), periods_yr=periods.tolist(),
                  min_period_yr=float(min(periods)), max_period_yr=float(max(periods)), windows=windows,
                  scope="Finite 30,000-year record; neither settling nor an attracting cycle is established")

    stored = fig4.mixed_stability()
    stability, rhs = [], []
    for chemistry in ("fixed", "products"):
        for f in (0., .5):
            case = next(c for c in dt.design() if c.stage == "B3" and c.chemistry == chemistry and c.fraction == f)
            native = dt.parameters(case)
            p = dr.parameters(chemistry, f, .001, .3)
            assert replace(native, activity_feedback="fixed") == p.base
            state = next(e for e in dc.equilibrium_states(p) if e["kind"] == "mixed" and e["status"] == "accepted")
            y = np.asarray(state["y"]) * [1.01, 1.02, .99, 1.03, 1.001]
            a, b = core.rhs(y, native), dc.physical_rhs(y, p)
            discrepancy = float(np.max(abs(a - b) / np.maximum(abs(a), 1e-14)))
            assert discrepancy < 1e-10
            rhs.append(dict(chemistry=chemistry, fraction=f, equal_base_parameters=True,
                            perturbed_rhs_max_relative_difference=discrepancy))
            build = dr.thermal_builder(state["y"], p)
            for tau in (0., 3., 30.):
                leading = float(eigvals(build(tau)).real.max())
                expected = stored[chemistry, f, tau]
                assert np.isclose(leading, expected, rtol=1e-6, atol=1e-10)
                stability.append(dict(chemistry=chemistry, fraction=f, tau_yr=tau,
                                      recorded_leading_real_yr=expected, recomputed_leading_real_yr=leading,
                                      stable=leading < 0))

    cases = {c.case_id: c for c in dt.design() if c.stage == "B3"}
    census_data, endpoints = {}, []
    for name, case in cases.items():
        record = records[name]
        data = fig4.census_record(record)
        present = np.isfinite(data["log_biomass"][:, -1])
        endpoint = "both" if all(present) else "acetogen_only" if present[0] else "methanogen_only" if present[1] else "empty"
        assert endpoint == record["census_endpoint"]
        expected = "acetogen_only" if case.direction == "A_into_M" else "methanogen_only"
        assert endpoint == expected
        endpoints.append(dict(case_id=name, census_endpoint=endpoint,
                              census_raw=record["census_raw"], census_sha256=record["census_sha256"]))
        if name.startswith("B3_fixed_f0.5_tau3_"):
            census_data[name] = data
    with (DATA / "fig4_trajectories.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        record = records[row["case_id"]]
        assert row["trace"] == "finite_census"
        assert row["census_raw"] == record["census_raw"] and row["census_sha256"] == record["census_sha256"]
        data = census_data[row["case_id"]]
        index = int(np.searchsorted(data["t"], float(row["time_yr"])))
        assert data["t"][index] == float(row["time_yr"])
        guild = ("acetogen", "methanogen").index(row["guild"])
        value = data["log_biomass"][guild, index]
        if np.isfinite(value):
            p, cells = dt.parameters(cases[row["case_id"]]), CellProcess()
            expected = (value + np.log(p.habitat_l_cm2 * cells.surface_cm2 / cells.cell_mass_gdw)) / np.log(10.)
            assert row["present"] == "True" and float(row["log10_cells"]) == expected
        else:
            assert row["present"] == "False" and row["log10_cells"] == ""
    return dict(fig2_period=period, matched_b3=dict(nominal_potential=.3, loss_h=.001, sigma_k=0.,
                lifetime_yr=10000., source_parameter_and_rhs_checks=rhs, stability=stability,
                stable_settings=sum(r["stable"] for r in stability), total_settings=len(stability)),
                census_endpoints=endpoints, fig4_plotted_census_rows_verified=len(rows))


if __name__ == "__main__":
    output = Path(__file__).with_suffix(".json")
    output.write_text(json.dumps(check(), indent=2, allow_nan=False) + "\n")
    print(output)
