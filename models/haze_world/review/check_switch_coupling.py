"""Independent audit of the reduced model at historical commit aae88c5.

uv run python models/haze_world/review/check_switch_coupling.py

Loads reviewed source through Git so subsequent repairs do not erase evidence.
Dependencies and climate data are hashed; no historical output is overwritten.
"""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import types

import numpy as np
from scipy.special import expit

from terra_prisca.haze_world.darwinian import climate_slopes, reference
from terra_prisca.haze_world.methane_budget import (
    atmosphere, capture_efficiency, growth_ratio, response, temperature_k,
)

ROOT = Path(__file__).resolve().parents[3]
COMMIT = "aae88c51cebfdd9edab2bb82ce1bf9c0f481fd44"


def reviewed_module(stem):
    path = f"src/terra_prisca/haze_world/{stem}.py"
    source = subprocess.check_output(["git", "show", f"{COMMIT}:{path}"], cwd=ROOT, text=True)
    name = f"terra_prisca.haze_world._audit_aae88c5_{stem}"
    module = types.ModuleType(name)
    module.__file__ = str(ROOT / path)
    sys.modules[name] = module
    exec(compile(source, f"{COMMIT}:{path}", "exec"), module.__dict__)
    return module, sha256(source.encode()).hexdigest()


def independent_jacobian(q, loss, sw, state):
    r, s, t = state["r"], state["s"], state["t_k"]
    rho = float(growth_ratio(t, q))
    rho_t = -2 * q.growth_ratio_max * (t - q.t_opt_k) / q.t_halfwidth_k ** 2 if q.thermal else 0.
    eta_t = q.maintenance_flux / q.donor_flux * rho_t / (rho - 1) ** 2
    cr = atmosphere(q.case)["flux_to_ratio_per_yr"]
    tr = climate_slopes(r, q)[0]
    return np.array([
        [cr * sw.routing(s) * q.donor_flux * eta_t * tr - loss.slope(r),
         -cr * (1 - sw.f_ac) * state["eta"] * q.donor_flux * s * (1 - s)],
        [-sw.selection_per_k_yr * tr, 0.],
    ])


def main():
    model, model_hash = reviewed_module("switch_coupling")
    guild_model, guild_hash = reviewed_module("two_guilds")
    q, losses = reference()
    loss = losses[2]
    reference_checks = []
    for sw in (model.Switch(281.5, 0.), model.Switch(282.8, .5)):
        for state in model.mixed_states(q, loss, sw):
            jac = independent_jacobian(q, loss, sw, state)
            x = np.log(state["s"] / (1 - state["s"]))

            def rhs(point):
                r, logit_s = point
                return np.array([
                    float(model.tendency(np.array([r]), expit(logit_s), q, loss, sw)[0]),
                    -sw.selection_per_k_yr * (float(temperature_k(r, q)) - sw.t_switch_k),
                ])

            center = np.array([state["r"], x])
            numeric = np.column_stack([
                (rhs(center + np.eye(2)[i] * step) - rhs(center - np.eye(2)[i] * step)) / (2 * step)
                for i, step in enumerate((1e-8, 1e-5))
            ])
            assert np.allclose(numeric, jac, rtol=1e-5, atol=1e-10)
            assert np.isclose(np.trace(jac), state["sides"][0]["trace"], rtol=1e-5)
            max_reals = []
            for g in (.001, .1, 1., 10., 1000.):
                varied = jac.copy()
                varied[1, 0] *= g / sw.selection_per_k_yr
                max_reals.append(float(max(np.linalg.eigvals(varied).real)))
            reference_checks.append(dict(t_switch_k=sw.t_switch_k, f_ac=sw.f_ac, ratio=state["r"],
                                         slope_k_per_ratio=climate_slopes(state["r"], q)[0],
                                         independent_jacobian=jac.tolist(),
                                         reference_stable=state["stable"],
                                         selection_rates_per_k_yr=[.001, .1, 1., 10., 1000.],
                                         max_real_eigenvalues=max_reals))

    capture_checks = []
    for form, t in (("saturating", 281.534823), ("first_order", 282.780106)):
        config = guild_model.Competition(kinetics=form, threshold_shape="fixed_energy",
                                        exchange_mol_l_h_pa=1e-6 / 300.)
        guilds = guild_model.guilds(t - 273.15, config)
        roots = [g.rstar(config.loss_h) for g in guilds]
        assert abs(roots[0] - roots[1]) < 1e-6
        capture_checks.append(dict(acetogen_kinetics=form, temperature_k=t, roots_pa=roots,
                                   actual_capture=1 - roots[0] / 300.,
                                   inherited_eta=float(capture_efficiency(t, q)),
                                   post_assimilation_factors=[
                                       1 - g.assimilation_mol_g * config.loss_h /
                                       (g.maintenance + config.loss_h / g.yield_g_mol) for g in guilds]))

    resp = response(q.case)
    vertex_ratio, vertex_t = map(float, (resp.ratios[4], resp.temperatures_k[4]))
    sw = model.Switch(vertex_t, 0.)
    eta = float(capture_efficiency(vertex_t, q))
    cr = atmosphere(q.case)["flux_to_ratio_per_yr"]
    vertex_s = (eta * q.donor_flux + q.abiotic_flux - float(loss.rate(vertex_ratio)) / cr) / (eta * q.donor_flux)
    found = model.mixed_states(q, loss, sw)
    assert 0 < vertex_s < 1
    assert not any(abs(e["r"] - vertex_ratio) < 1e-10 for e in found)
    vertex = dict(ratio=vertex_ratio, temperature_k=vertex_t, valid_mixed_share=vertex_s,
                  detected_mixed_ratios=[e["r"] for e in found],
                  exact_grid_root_detected=bool(model._sign_changes(lambda x: x - .5, np.array([0., .5, 1.]))),
                  interval_endpoint_root_detected=bool(model._sign_changes(lambda x: x, np.array([0., .5, 1.]))),
                  tangent_root_detected=bool(model._sign_changes(lambda x: (x - .5) ** 2, np.array([0., .5, 1.]))))

    sw = model.Switch(281.5, 0.)
    cold = next(e for e in model.states(q, loss, sw) if e["kind"] == "no_capture")
    no_capture = dict(**cold, compact_share_eigenvalue_per_yr=-sw.selection_per_k_yr * (cold["t_k"] - sw.t_switch_k),
                      note="Saved s=0 has an unstable composition direction; s=1 gives the same abiotic climate and the opposite sign")
    assert no_capture["stable"] and no_capture["compact_share_eigenvalue_per_yr"] > 0
    baseline_living = next(e for e in model.pure_states(q, loss, model.Switch(250., 0.))
                          if e["kind"] == "methanogen" and e["stable"])
    boundary_switch = model.Switch(baseline_living["t_k"], 0.)
    boundary = next(e for e in model.pure_states(q, loss, boundary_switch)
                    if e["kind"] == "methanogen" and e["stable"])
    boundary["composition_eigenvalue_per_yr"] = -boundary_switch.selection_per_k_yr * (boundary["t_k"] - boundary_switch.t_switch_k)
    assert boundary["composition_eigenvalue_per_yr"] == 0.
    shifted_optimum = replace(q, t_opt_k=275.)
    unstable = next(e for e in model.mixed_states(shifted_optimum, loss, model.Switch(293., 0.))
                    if e["sides"][0]["t_r"] < 0)
    assert unstable["sides"][0]["trace"] > 0 and not unstable["stable"]

    grid = np.geomspace(1e-6, .4, 101)
    equivalent = all(np.array_equal(model.tendency(grid, share, q, loss, model.Switch(281.5, 1.)),
                                   model.tendency(grid, 0., q, loss, model.Switch(281.5, 0.)))
                     for share in (0., .3, 1.))
    assert equivalent
    files = (
        Path(__file__), ROOT / "src/terra_prisca/haze_world/darwinian.py",
        ROOT / "src/terra_prisca/haze_world/methane_budget.py",
        ROOT / "src/terra_prisca/haze_world/hydrogen_uptake.py",
        ROOT / "src/terra_prisca/haze_world/woodii1998.py",
        ROOT / "models/haze_response/arney2016/figure4.csv",
    )
    result = dict(reviewed_commit=COMMIT, reviewed_source_sha256={"switch_coupling.py": model_hash, "two_guilds.py": guild_hash},
                  live_dependency_sha256={str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in files},
                  reference_jacobian_checks=reference_checks, capture_comparison=capture_checks,
                  missed_vertex_and_root_checks=vertex, no_capture_flag_check=no_capture,
                  pure_switch_boundary=boundary, warm_flank_haze_counterexample=unstable,
                  f_ac_one_reduced_climate_rhs_identical=equivalent,
                  scope="Historical reduced-model audit; not a full-population calibration or global stability result")
    output = Path(__file__).with_name("switch_coupling_review.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(dict(capture_comparison=capture_checks, missed_vertex=vertex,
                         no_capture_flag=no_capture, warm_flank_haze_counterexample=unstable), indent=2))


if __name__ == "__main__":
    main()
