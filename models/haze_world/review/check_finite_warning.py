"""Reproduce the historical immigrant-coordinate failure and check its repair.

uv run python models/haze_world/review/check_finite_warning.py

No long-run qualification: repaired target checks stop at 100/1000 years.
"""

from hashlib import sha256
import importlib.metadata
import inspect
import json
from pathlib import Path
import subprocess
import sys
import types
import warnings

import numpy as np

from terra_prisca.haze_world import finite_populations as repaired
from terra_prisca.haze_world.finite_experiments import clean, design, initial_state, parameters

ROOT = Path(__file__).resolve().parents[3]
OLD_COMMIT = "2b8b070"


def historical_module():
    path = "src/terra_prisca/haze_world/finite_populations.py"
    commit = subprocess.check_output(["git", "rev-parse", OLD_COMMIT], cwd=ROOT, text=True).strip()
    code = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT, text=True)
    name = "terra_prisca.haze_world._historical_finite_warning"
    module = types.ModuleType(name)
    module.__file__ = str(ROOT / path)
    sys.modules[name] = module
    exec(compile(code, f"{commit}:{path}", "exec"), module.__dict__)
    return module, commit, sha256(code.encode()).hexdigest()


def run(module, case, years, controls=None):
    controls = controls or {}
    p, process = parameters(case)
    actual_ode = module.ode
    clock, diagnostics = {}, []

    def make_ode(function, *args, **kwargs):
        def callback(time, state):
            clock["time_yr"] = float(time)
            return function(time, state)

        solver = actual_ode(callback, *args, **kwargs)
        original_setter = solver.set_integrator

        def setter(name, **options):
            if controls:
                options["rtol"] = controls["rtol"]
                options["atol"] = np.asarray(options["atol"]) * controls["atol_scale"]
                options["max_step"] = controls["max_step"]
            return original_setter(name, **options)

        solver.set_integrator = setter
        return solver

    def context():
        frame = inspect.currentframe().f_back
        try:
            while frame:
                if frame.f_code.co_name == "derivatives" and "anchors" in frame.f_locals:
                    values = frame.f_locals
                    i = values["i"]
                    return clean(dict(time_yr=clock["time_yr"], guild_index=i, z=values["z"],
                                      anchor=values["anchors"][i],
                                      exponent_argument=values["anchors"][i] - values["z"],
                                      physical_trial=values["physical"], growth_yr=values["growth"]))
                frame = frame.f_back
            return None
        finally:
            del frame

    result = None
    report = dict(years=years, numerical_controls=controls)
    module.ode = make_ode
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            original_show = warnings.showwarning

            def show(message, category, filename, lineno, file=None, line=None):
                diagnostics.append(dict(category=category.__name__, message=str(message), trial=context()))
                original_show(message, category, filename, lineno, file, line)

            warnings.showwarning = show
            try:
                result = module.integrate_finite(initial_state(case), p, years, process,
                                                 sample_every_censuses=1)
            except (RuntimeError, ValueError) as error:
                report.update(success=False, error=str(error))
            else:
                report.update(success=True, endpoint=result.y[:, -1],
                              first_extinction_by_guild_yr=result.first_extinction_by_guild_yr,
                              cull_events=len(result.extinction_events), nfev=result.metadata["nfev"],
                              wall_seconds=result.metadata["wall_seconds"])
            finally:
                warnings.showwarning = original_show
            assert len(caught) == len(diagnostics)
    finally:
        module.ode = actual_ode
    report["warnings"] = diagnostics
    return report, result


def compare(left, right, process, volume):
    assert np.array_equal(left.t, right.t)
    floor = process.minimum_cells * process.cell_mass_gdw / volume
    scale = np.maximum(abs(left.y), np.array([1., floor, floor, 1e-9, .001])[:, None])
    state_error = float(np.max(abs(left.y - right.y) / scale))
    absolute = np.max(abs(left.y - right.y), axis=1)
    macro = [0, 3, 4]
    solver_scale = np.array([1e-7, 1e-11, 1e-11])[:, None] + 2e-8 * abs(left.y[macro])
    macro_error = float(np.max(abs(left.y[macro] - right.y[macro]) / solver_scale))
    presence = np.isfinite(left.log_biomass)
    same_presence = bool(np.array_equal(presence, np.isfinite(right.log_biomass)))
    log_error = float(np.max(abs(left.log_biomass[presence] - right.log_biomass[presence])))
    topology = lambda result: [(e["time_yr"], e["guild"], e["reason"]) for e in result.extinction_events]
    same_events = topology(left) == topology(right)
    event_log_error = max((abs(a["log_removed_cells"] - b["log_removed_cells"])
                           for a, b in zip(left.extinction_events, right.extinction_events)), default=0.)
    event_absolute = {key: max((abs(a[key] - b[key]) for a, b in zip(left.extinction_events, right.extinction_events)), default=0.)
                      for key in ("removed_cells", "removed_gdw", "removed_h2_mol")}
    same_activity = bool(np.array_equal(left.census_activity, right.census_activity))
    state_close = macro_error < 10 and same_presence and log_error < 1e-4
    topology_close = same_events and same_activity
    cull_mass_close = event_log_error < 1e-4
    return dict(max_scaled_physical_difference=state_error, max_abs_difference_by_state=absolute,
                max_macro_solver_tolerance_ratio=macro_error, max_log_biomass_difference=log_error,
                same_log_presence=same_presence, same_cull_topology=same_events,
                max_log_culled_cells_difference=event_log_error, same_census_activity=same_activity,
                max_abs_culled_quantity_difference=event_absolute,
                retained_and_macro_concordant=state_close, topology_concordant=topology_close,
                culled_log_concordant=cull_mass_close,
                concordant=state_close and topology_close and cull_mass_close)


def main():
    old, commit, old_hash = historical_module()
    cases = design("main", 100000.)
    target = cases[123]
    failed, _ = run(old, target, 100.)
    assert not failed["success"]
    default, baseline = run(repaired, target, 100.)
    longer, _ = run(repaired, target, 1000.)
    controls = dict(rtol=2e-9, atol_scale=.1, max_step=.1)
    tighter, tight_result = run(repaired, target, 100., controls)
    assert all(r["success"] and not r["warnings"] for r in (default, longer, tighter))
    p, process = parameters(target)
    target_concordance = compare(baseline, tight_result, process, baseline.metadata["total_habitat_l"])
    assert target_concordance["concordant"]
    selected = []
    for index in (3, 35, 50, 75, 83, 107, 127, 141):
        historical, before = run(old, cases[index], 100.)
        current, after = run(repaired, cases[index], 100.)
        assert historical["success"] and current["success"]
        assert not historical["warnings"] and not current["warnings"]
        p, process = parameters(cases[index])
        difference = compare(before, after, process, after.metadata["total_habitat_l"])
        assert difference["retained_and_macro_concordant"] and difference["topology_concordant"]
        selected.append(dict(case_index=index, **difference))
    paths = (Path(__file__), ROOT / "src/terra_prisca/haze_world/finite_populations.py",
             ROOT / "src/terra_prisca/haze_world/population_coupling.py",
             ROOT / "src/terra_prisca/haze_world/finite_experiments.py")
    result = dict(historical_commit=commit, historical_finite_source_sha256=old_hash,
                  packages={name: importlib.metadata.version(name) for name in ("numpy", "scipy")},
                  live_source_sha256={str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in paths},
                  affected_case=dict(index=123, activity="products", fraction=.9, minimum_cells=1.,
                                     relative_immigration_yr=.1, direction="M_into_A", census_yr=10.),
                  historical_100yr=failed, repaired_100yr=default, repaired_1000yr=longer,
                  tighter_100yr=tighter, repaired_numerical_concordance=target_concordance,
                  selected_successful_original_concordance=selected,
                  comparison_tolerances=dict(macro_multiple_of_reference_local_tolerances=10,
                                             retained_and_culled_log_stock_difference=1e-4,
                                             cull_times_guilds_and_census_activity="exact match"),
                  scope="Local 100/1000-year repair checks; no tighter-control 100000-year rerun or phase-map qualification")
    scan = ROOT / "local/haze/finite_populations/diagnostics"
    reports = sorted(scan.glob("*.prefix100.json"))
    if reports:
        records = [json.loads(path.read_text()) for path in reports]
        result["historical_prefix_scan"] = dict(
            reports=len(records), horizon_yr=100,
            warning_case_ids=[r["case"]["case_id"] for r in records if r.get("warnings")],
            failed_case_ids=[r["case"]["case_id"] for r in records if r["status"] != "complete"],
            successful_cases=sum(r["status"] == "complete" for r in records),
            report_set_sha256=sha256("\n".join(path.name + ":" + sha256(path.read_bytes()).hexdigest()
                                              for path in reports).encode()).hexdigest())
    output = Path(__file__).with_name("finite_warning_check.json")
    output.write_text(json.dumps(clean(result), indent=2, allow_nan=False) + "\n")
    print(json.dumps(clean(dict(historical_success=failed["success"], repaired_target=default,
                               tighter_concordance=target_concordance, selected=selected)), indent=2))


if __name__ == "__main__":
    main()
