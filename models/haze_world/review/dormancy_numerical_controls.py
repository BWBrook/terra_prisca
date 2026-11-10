"""Reproduce the pre-freeze dormancy controls; raw arrays stay under local/.

    uv run python models/haze_world/review/dormancy_numerical_controls.py

Initial arrays are the exact inputs used in the qualification, including the
tiny stationary resident dormant pool. The physical Radau check removes only
identically inactive habitat coordinates and stops four orders above its
biomass absolute tolerance; it is not a finite-population extinction model.
"""

import argparse
from dataclasses import asdict, replace
from hashlib import sha256
import importlib.metadata
import json
from pathlib import Path
import platform
from time import perf_counter

import numpy as np
from scipy.integrate import solve_ivp

from terra_prisca.haze_world import buffered_experiments as experiments
from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_integration as numerical

ROOT = Path(__file__).resolve().parents[3]
RAMP_ACTIVE = [70.19416051685708, 1e-12, .0005744177342218681, 0.,
               0., 0., 0., 0., 0., 0., 0., 0., .21615000467994544]
WARM_INITIAL = [70.17042432859772, 1e-12, .0005745571702505062, 0., 0., 9.12359101891857e-27,
                19.976919423682602, 1e-12, .0006325150956646063, 0., 0., 1.0199770920082618e-35,
                0., 0., 0., 0., 0., 0., .2171455097093504]


def sources():
    result = experiments.source_hashes()
    for name in ("dormancy.py", "dormancy_integration.py", "bottleneck_integration.py"):
        path = ROOT / "src/terra_prisca/haze_world" / name
        result[str(path.relative_to(ROOT))] = sha256(path.read_bytes()).hexdigest()
    return result


def parameters(configuration, dispersal, epsilon, ramp="cubic"):
    base = experiments.parameters(experiments.Case("numerical_control", 0., configuration,
                                                  dispersal, "A_into_M"))
    return model.Dormancy(base, epsilon=epsilon, ramp=ramp)


def stock(y, p):
    return y[p.biomass_indices] + y[p.dormant_indices]


def summarize(result, p):
    return dict(status=result.status, wall_seconds=result.metadata["wall_seconds"],
        accepted_steps=result.metadata["accepted_steps"], nfev=result.metadata["nfev"],
        positivity_retries=result.metadata["allocation_positivity_retries"],
        solver_failure_retries=result.metadata["solver_failure_retries"],
        stage_coordinate_promotions=len(result.metadata["stage_coordinate_switches"]),
        stage_source_restarts=len(result.metadata["stage_source_restarts"]),
        minimum_global_pre_extinction_log10_cells=(result.global_pre_extinction_min_log_biomass
            +result.metadata["global_log_cell_conversion"])/np.log(10),
        final_y=result.y[:, -1], final_temperatures_k=model.temperatures(result.y[:, -1], p),
        extinction_events=result.extinction_events)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-directory", type=Path, default=ROOT/"local/haze/dormancy_numerical_controls")
    parser.add_argument("--receipt", type=Path, default=Path(__file__).with_name("dormancy-numerical-controls-2026-11-10.json"))
    args = parser.parse_args(); args.raw_directory.mkdir(parents=True, exist_ok=True)
    frozen = sources(); rows = {}; payloads = {}

    def save(name, **arrays):
        path = args.raw_directory/(name+".npz"); np.savez_compressed(path, **arrays)
        payloads[name] = dict(path=str(path.relative_to(ROOT)), sha256=sha256(path.read_bytes()).hexdigest())

    ramp_results = []
    for ramp in ("linear", "cubic"):
        p = parameters("none", 0., .003, ramp)
        initial = model.reference_state(RAMP_ACTIVE, p)
        result = numerical.integrate_finite(initial, p, 100., numerical.Census(census_yr=10.), sample_every_censuses=1)
        ramp_results.append(result); rows["ramp_"+ramp] = summarize(result, p)
        save("ramp_"+ramp, t=result.t, y=result.y, log_biomass=result.log_biomass)
    rows["ramp_difference"] = dict(temperature_cubic_minus_linear_k=
        rows["ramp_cubic"]["final_temperatures_k"]-rows["ramp_linear"]["final_temperatures_k"],
        scope="One matched 100-year comparison; no claim of long-term ramp invariance")

    p = parameters("warm", 1e-9, .1); initial = np.array(WARM_INITIAL)
    tolerance_results = []
    for rtol in (2e-8, 2e-9):
        result = numerical.integrate_finite(initial, p, 100., numerical.Census(minimum_cells=0., census_yr=10.),
            sample_every_censuses=1, max_step=10., rtol=rtol)
        tolerance_results.append(result); name = "tolerance_"+str(rtol)
        rows[name] = summarize(result, p)
        save(name, t=result.t, y=result.y, log_biomass=result.log_biomass)
    a, b = tolerance_results
    delta = abs(stock(a.y, p)-stock(b.y, p))/np.maximum(abs(stock(b.y, p)), 1e-29)
    relative = float(np.max(delta[p.weights > 0]))
    dt = float(np.max(abs(a.temperatures_k-b.temperatures_k)))
    assert relative < 2e-5 and dt < 2e-6
    rows["tolerance_difference"] = dict(maximum_combined_stock_relative=relative, maximum_temperature_k=dt,
        maximum_methane_ratio=float(max(abs(a.y[-1]-b.y[-1]))),
        global_minimum_log_stock_difference=a.global_continuous_min_log_biomass-b.global_continuous_min_log_biomass)

    long = numerical.integrate_finite(initial, p, 100000., numerical.Census(census_yr=10.),
        sample_every_censuses=100, max_step=10., rtol=2e-8)
    assert long.status == "completed" and np.all(np.isfinite(long.y)) and np.all(long.y >= 0)
    rows["censused_100k"] = summarize(long, p)
    save("censused_100k", t=long.t, y=long.y, log_biomass=long.log_biomass,
         log_active=long.log_active, log_dormant=long.log_dormant)

    indices = np.r_[np.ravel([np.arange(6*j, 6*j+6) for j, w in enumerate(p.weights) if w]), p.state_size-1].astype(int)
    atol = np.r_[np.tile([1e-9, 1e-25, 1e-25, 1e-18, 1e-25, 1e-25], p.n_patches), 1e-13]
    def expand(z):
        y = np.zeros(p.state_size); y[indices] = z; return y
    def event(t, z):
        return p.weights @ stock(expand(z), p)[:, 0]-1e-21
    event.terminal = True; event.direction = -1
    started = perf_counter()
    independent = solve_ivp(lambda t, z: model.rhs(expand(z), p, trial_extension=True)[indices],
        (0., 1800.), initial[indices], method="Radau", rtol=2e-9, atol=atol[indices],
        events=event, dense_output=True, max_step=5.)
    wall = perf_counter()-started
    assert independent.success and len(independent.t_events[0]) == 1
    comparisons = []
    for t in (1000., 1230.):
        y = long.y[:, np.flatnonzero(long.t == t)[0]]; other = expand(independent.sol(t))
        global_a, other_a = (float(p.weights @ stock(v, p)[:, 0]) for v in (y, other))
        difference = float(model.core.temperature_k(y[-1], p.coupled.climate)-model.core.temperature_k(other[-1], p.coupled.climate))
        assert abs(global_a/other_a-1) < .002 and abs(difference) < 2e-4
        comparisons.append(dict(time_yr=t, temperature_difference_k=difference,
            positive_global_acetogen_gdw_l=global_a, physical_global_acetogen_gdw_l=other_a,
            global_acetogen_relative_difference=global_a/other_a-1))
    times = np.unique(np.r_[np.arange(0., independent.t[-1], 10.), independent.t[-1]])
    physical = np.zeros((p.state_size, len(times))); physical[indices] = independent.sol(times)
    save("physical_radau", t=times, y=physical)
    conversion = p.coupled.habitat_l_cm2*numerical.Census().surface_cm2/numerical.Census().cell_mass_gdw
    rows["physical_radau"] = dict(success=independent.success, terminal_time_yr=independent.t[-1],
        terminal_global_acetogen_cells=1e-21*conversion, wall_seconds=wall,
        accepted_steps=len(independent.t)-1, nfev=independent.nfev, comparisons=comparisons,
        scope="Independent direct physical-coordinate integration; tiny negative active components within absolute tolerance do not decide the combined-stock result")

    assert sources() == frozen
    protocol = dict(source_sha256=frozen, checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        python=platform.python_version(), packages={n:importlib.metadata.version(n) for n in ("numpy", "scipy")},
        ramp_initial_active_state=RAMP_ACTIVE, warm_initial_dormancy_state=WARM_INITIAL,
        ramp_parameters={r:asdict(parameters("none", 0., .003, r)) for r in ("linear", "cubic")},
        warm_parameters=asdict(p), census=asdict(numerical.Census()),
        census_sampling_stride=100, tolerance_horizon_yr=100., tolerance_rtol=[2e-8, 2e-9],
        physical_horizon_yr=1800., physical_event_global_gdw_l=1e-21, physical_atol=atol,
        physical_rtol=2e-9, physical_max_step_yr=5., positive_max_step_yr=10.,
        initialization="Exact recorded qualification arrays; active invader1e-12gDW/L, dormant invader0; resident bank stationary")
    receipt = experiments.clean(dict(execution_status="complete", protocol=protocol, controls=rows, payloads=payloads))
    args.receipt.write_text(json.dumps(receipt, indent=2, allow_nan=False)+"\n")
    print(json.dumps(dict(receipt=str(args.receipt.relative_to(ROOT)), controls=list(rows), execution_status="complete")))


if __name__ == "__main__": main()
