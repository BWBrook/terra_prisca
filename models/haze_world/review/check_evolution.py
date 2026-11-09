"""Independent singular-strategy and monotone-loss checks for the pilot.

uv run python models/haze_world/review/check_evolution.py OUTPUT_DIRECTORY
Alternative loss shapes are mathematical sensitivities, not recovered chemistry.
"""

from dataclasses import replace
import json
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq

from terra_prisca.haze_world.experiments import flux_for_potential
from terra_prisca.haze_world.methane_budget import (
    Params, atmosphere, capture_efficiency, equilibria, response, temperature_k,
)

KB_EV = 8.617333e-5


def gradient(temperature, optimum, energy, width=20.0):
    x = optimum - temperature
    return energy / (KB_EV * optimum**2) - 2 * x / (width**2 - x**2)


def singular_optimum(temperature, energy):
    if energy == 0:
        return temperature
    return brentq(lambda optimum: gradient(temperature, optimum, energy), temperature, temperature + 19.9999)


def main(out):
    p = Params()
    p = replace(p, donor_flux=float(flux_for_potential(0.22, p)))
    c = atmosphere(p.case)["flux_to_ratio_per_yr"]
    reference = [e for e in equilibria(replace(p, thermal=False)) if e["stable"]][-1]
    rp = reference["r"]
    lo, hi = response(p.case).ratios[[0, -1]]
    results = []
    for law in ("linear", "logarithmic"):
        def loss(r):
            shape = r / rp if law == "linear" else np.log1p(r / 0.001) / np.log1p(rp / 0.001)
            return rp / p.lifetime_yr * shape

        for energy in (0.0, 0.32, 0.65):
            def traits(r):
                temperature = temperature_k(r, p, extend=False)
                optimum = singular_optimum(temperature, energy)
                peak = 10 * np.exp(energy / KB_EV * (1 / 300 - 1 / optimum))
                q = replace(p, t_opt_k=optimum, growth_ratio_max=peak)
                eta = float(capture_efficiency(temperature, q))
                return temperature, optimum, peak, eta

            def tendency(r):
                return c * (p.donor_flux * traits(r)[3] + p.abiotic_flux) - loss(r)

            r = brentq(tendency, lo, hi, xtol=1e-14)
            t, optimum, peak, eta = traits(r)
            fixed_trait = replace(p, t_opt_k=optimum, growth_ratio_max=peak)
            def ecological_flow(ratio):
                value = capture_efficiency(temperature_k(ratio, p, extend=False), fixed_trait)
                return c * (p.donor_flux * value + p.abiotic_flux) - loss(ratio)
            step = 1e-8
            ecological_rate = float((ecological_flow(r + step) - ecological_flow(r - step)) / (2 * step))
            loss_rate = float((loss(r + step) - loss(r - step)) / (2 * step))
            assert ecological_rate < 0 and loss_rate > 0
            x = optimum - t
            curvature = -2 * energy / (KB_EV * optimum**3) - 2 * (400 + x*x) / (400 - x*x)**2
            eps = 1e-3
            def log_fitness(theta):
                return np.log(10) + energy / KB_EV * (1 / 300 - 1 / theta) + np.log1p(-((t - theta) / 20)**2)
            finite_gradient = (log_fitness(optimum + eps) - log_fitness(optimum - eps)) / (2 * eps)
            assert abs(gradient(t, optimum, energy)) < 1e-10
            assert abs(finite_gradient) < 1e-7
            assert curvature < 0 and lo < r < hi and abs(tendency(r)) < 1e-12
            approximate_margin = (0.0 if energy == 0 else brentq(
                lambda margin: energy / (KB_EV * t*t) - 2 * margin / (400 - margin*margin), 0, 19.9999))
            results.append(dict(loss=law, energy_ev=energy, ratio=r, temperature_k=t,
                                optimum_k=optimum, margin_k=x, peak_growth_ratio=peak, capture=eta,
                                ecological_flow_derivative_per_yr=ecological_rate,
                                loss_derivative_per_yr=loss_rate,
                                fixed_environment_fitness_curvature=curvature,
                                reference_control_temperature_k=reference["t_k"],
                                temperature_difference_k=t - reference["t_k"],
                                margin_using_approximate_temperature_denominator_k=approximate_margin))
    out.mkdir(parents=True, exist_ok=True)
    metadata = dict(potential_ratio=0.22, reference_control_growth_ratio=10,
                    reference_control_ratio=rp, log_loss_scale_ratio=0.001,
                    loss_normalization="Both losses equal the same control source at the control ratio",
                    rows=results)
    (out / "evolution_check.json").write_text(json.dumps(metadata, indent=2) + "\n")
    fig, ax = plt.subplots(figsize=(6.5, 4), constrained_layout=True)
    index = np.arange(3)
    for offset, law, colour in ((-0.18, "linear", "#326781"), (0.18, "logarithmic", "#c98332")):
        subset = [r for r in results if r["loss"] == law]
        ax.bar(index + offset, [r["temperature_difference_k"] for r in subset], width=0.36,
               color=colour, label=f"{law} loss")
    ax.set(xticks=index, xticklabels=["0", "0.32", "0.65"], xlabel="Assumed trade-off E (eV)",
           ylabel="Evolved climate minus reference control (K)",
           title="Monotone loss does not fix the thermal contrast")
    ax.legend()
    fig.savefig(out / "loss_sensitivity.png", dpi=160)
    plt.close(fig)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
