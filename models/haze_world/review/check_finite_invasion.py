"""Bounded audit of c9bbac6: refine early crossings without a 100-kyr rerun.

uv run python models/haze_world/review/check_finite_invasion.py

The reviewed fixed-activity population/guild sources are loaded from Git;
new finite/activity variants do not silently change this historical check.
"""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import types

import numpy as np
from scipy.integrate import solve_ivp
from scipy.special import expit

ROOT = Path(__file__).resolve().parents[3]
COMMIT = "c9bbac62b1c798d7b718fe7c0ca781cbfcb460e7"
EARTH_CM2, CELL_GDW, BIOMASS_SCALE = 5.1e18, 3e-13, 1e-3


def reviewed_module(stem):
    path = f"src/terra_prisca/haze_world/{stem}.py"
    code = subprocess.check_output(["git", "show", f"{COMMIT}:{path}"], cwd=ROOT, text=True)
    name = f"terra_prisca.haze_world._finite_review_{stem}"
    module = types.ModuleType(name)
    module.__file__ = str(ROOT / path)
    sys.modules[name] = module
    exec(compile(code, f"{COMMIT}:{path}", "exec"), module.__dict__)
    return module, sha256(code.encode()).hexdigest()


def log_biomass(z):
    return np.log(BIOMASS_SCALE) + (z if z < -30 else np.log(np.logaddexp(0., z)))


def main():
    guild_model, guild_hash = reviewed_module("two_guilds")
    model, model_hash = reviewed_module("population_coupling")
    model.guilds, model.Competition = guild_model.guilds, guild_model.Competition
    p = model.reference(.3)
    volume = p.habitat_l_cm2 * EARTH_CM2
    one_cell = np.log(CELL_GDW / volume)
    control = next(e for e in model.equilibrium_states(replace(p, enabled=(False, True)))
                   if e["kind"] == "methanogen" and e["stable"])
    physical = control["y"].copy()
    physical[1] = 1e-12
    initial = physical.copy()
    for i in (1, 2):
        value = initial[i] / BIOMASS_SCALE
        initial[i] = value + np.log(-np.expm1(-value))

    def rhs(_, internal):
        y = internal.copy()
        y[1:3] = BIOMASS_SCALE * np.logaddexp(0., y[1:3])
        rates = model.rhs(y, p)
        net = model.fluxes(y, p)["net_growth_yr"]
        for i in (1, 2):
            z = internal[i]
            rates[i] = net[i - 1] * (1. if z < -30 else np.logaddexp(0., z) / expit(z))
        return rates

    scenarios = [("reference", n, CELL_GDW, 1.) for n in (1., 1e6, 1e12)]
    scenarios += [("cell_mass_div10", 1., CELL_GDW / 10, 1.),
                  ("cell_mass_times10", 1., CELL_GDW * 10, 1.),
                  ("one_percent_area", 1., CELL_GDW, .01)]
    events = []
    for _, cells, mass, area in scenarios:
        target = np.log(cells * mass / (volume * area))

        def crossing(_, y, threshold=target):
            return log_biomass(y[2]) - threshold

        crossing.direction, crossing.terminal = -1., False
        events.append(crossing)
    solved = solve_ivp(rhs, (0., 30.), initial, method="LSODA", events=events,
                       rtol=2e-9, atol=[1e-8, 1e-9, 1e-9, 1e-12, 1e-12], max_step=.1)
    assert solved.success
    tighter = solve_ivp(rhs, (0., 30.), initial, method="LSODA", events=events,
                         rtol=5e-10, atol=[2e-9, 2e-10, 2e-10, 2e-13, 2e-13], max_step=.025)
    assert tighter.success
    event_difference = max(abs(times[0] - refined[0]) for times, refined in zip(solved.t_events, tighter.t_events))
    assert event_difference < 1e-5
    refined = []
    for (label, cells, mass, area), times, states in zip(scenarios, solved.t_events, solved.y_events):
        assert len(times) >= 1
        state = states[0].copy()
        state[1:3] = BIOMASS_SCALE * np.logaddexp(0., state[1:3])
        f = model.fluxes(state, p)
        refined.append(dict(scenario=label, threshold_cells=cells, cell_gdw=mass, area_fraction=area,
                            first_downcrossing_yr=float(times[0]),
                            historical_five_year_sample_yr=float(5 * np.ceil(times[0] / 5)),
                            temperature_k=f["temperature_k"], pressure_pa=float(state[0]),
                            methanogen_net_growth_yr=float(f["net_growth_yr"][1])))

    reinvasion = []
    for fraction in (0., .5, .9):
        q = replace(p, enabled=(True, False), acetate_fraction=fraction)
        state = next(e for e in model.equilibrium_states(q) if e["kind"] == "acetogen" and e["stable"])
        y = state["y"]
        pair = guild_model.guilds(state["t_k"] - 273.15, q.biology)
        growth = float(pair[1].net_growth(y[0], q.biology.loss_h) * model.HOURS_PER_YEAR)
        reinvasion.append(dict(acetate_fraction=fraction, temperature_k=state["t_k"], pressure_pa=float(y[0]),
                               methanogen_net_growth_yr=growth, could_reinvade=growth > 0,
                               methanogen_rstar_pa=pair[1].rstar(q.biology.loss_h),
                               protocol="A-only equilibria after post-extinction f intervention; not constant-f invasions"))
    mixed = next(e for e in model.equilibrium_states(p) if e["kind"] == "mixed")
    result = dict(reviewed_commit=COMMIT, historical_source_sha256={"population_coupling.py": model_hash, "two_guilds.py": guild_hash},
                  script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
                  habitat_l_cm2=p.habitat_l_cm2, assumed_total_habitat_l=volume,
                  one_global_cell_gdw_l=CELL_GDW / volume, ln_one_global_cell=float(one_cell),
                  initial_acetogen_global_cells=physical[1] * volume / CELL_GDW,
                  initial_acetogen_global_gdw=physical[1] * volume,
                  early_event_horizon_yr=30., event_tolerance_refinement_max_difference_yr=float(event_difference),
                  refined_methanogen_crossings=refined,
                  acetogen_only_reinvasion=reinvasion,
                  mixed_equilibrium_global_cells=list(mixed["y"][1:3] * volume / CELL_GDW),
                  mixed_equilibrium_stable=mixed["stable"],
                  scope="One reference invasion; threshold/habitat/cell-mass readouts are assumptions, not calibrated stochastic extinction")
    result["live_dependency_sha256"] = {
        name: sha256((ROOT / name).read_bytes()).hexdigest() for name in (
            "src/terra_prisca/haze_world/methane_budget.py", "src/terra_prisca/haze_world/darwinian.py",
            "src/terra_prisca/haze_world/hydrogen_uptake.py", "src/terra_prisca/haze_world/woodii1998.py",
            "models/haze_world/evidence/kotsyurbenko2001_table2.csv",
            "models/haze_response/arney2016/cases.csv", "models/haze_response/arney2016/figure4.csv")
    }
    Path(__file__).with_name("finite_invasion_review.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
