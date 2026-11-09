"""Seeded mutational-rescue controls for strain model 85041a0; run from repo root."""
from pathlib import Path
import sys
import json
import numpy as np
from terra_prisca.haze_world.darwinian import Constraint, reference
from terra_prisca.haze_world.experiments import flux_for_potential
from terra_prisca.haze_world.methane_budget import temperature_k
from terra_prisca.haze_world.strains import Run, StrainModel, seed_escape

outdir = Path(sys.argv[1])
outdir.mkdir(parents=True,exist_ok=True)
p, losses = reference()
controls, extensions = [], []
for seed in (285.0, 285.5):
    for mutation in (0.0, 0.01):
        run = Run(Constraint(), losses[2], mutation=mutation, b_min_rel=1e-9, check_yr=1.0)
        model = StrainModel(p, run)
        phi = float(flux_for_potential(0.22, p))
        abiotic_ratio = float(run.loss.inverse(model.c * p.abiotic_flux))
        abiotic_temperature = float(temperature_k(abiotic_ratio, model.p))
        seed_index = int(abs(model.theta - seed).argmin())
        rho_need = 1.0 + p.maintenance_flux / phi
        initial_growth = float(model.rho(abiotic_temperature)[seed_index] / rho_need - 1.0)
        controls.append(dict(initial_percapita_growth=initial_growth, **seed_escape(p, run, seed)))
        if mutation == 0.0:
            continue
        ref, _ = model.resident_state(phi)
        b_star = float(ref[2:].sum())
        biomass = np.zeros(model.theta.size)
        biomass[seed_index] = 1e-3 * b_star
        assert (biomass > 0).sum() == 1
        assert not np.any((biomass > 0) & (model.rho(abiotic_temperature) > rho_need))
        y0 = np.r_[model.c * phi / run.k_donor, abiotic_ratio, biomass]
        result = model.integrate(y0, lambda t: phi, 20000.0, run.b_min_rel * b_star, record_every_yr=500.0)
        checkpoints = [dict(**s, total_rel=s['total_biomass'] / b_star) for s in result['series']
                       if s['t_yr'] in (500.0, 5000.0, 20000.0)]
        extensions.append(dict(seed_theta=seed, mutation=mutation, b_min_rel=run.b_min_rel,
                               check_yr=run.check_yr, extinct_at_yr=result['extinct_at_yr'], checkpoints=checkpoints))
(outdir / 'seed_mutational_rescue.json').write_text(json.dumps(controls, indent=2) + '\n')
(outdir / 'seed_mutational_rescue_long.json').write_text(json.dumps(extensions, indent=2) + '\n')
print(json.dumps(dict(controls=controls, extensions=extensions), indent=2))
