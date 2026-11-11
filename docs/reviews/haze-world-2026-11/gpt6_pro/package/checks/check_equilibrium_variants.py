"""Compact static counterfactuals. Run with uv from the tagged repository root."""
import json
from dataclasses import replace
from pathlib import Path
from terra_prisca.haze_world.population_coupling import reference, equilibrium_states
p = reference()
co2_corrected = replace(p.biology,
    threshold_a30=20 * (12000 / 1800)**0.5,
    threshold_m30=(12000 / 1800)**0.25)
variants = [
    ('baseline', p),
    ('products', replace(p, activity_feedback='products')),
    ('co2matched', replace(p, biology=co2_corrected)),
    ('co2matched_products', replace(p, biology=co2_corrected, activity_feedback='products')),
    ('capacity0.5', replace(p, biology=replace(p.biology, capacity_ratio=0.74*0.5))),
    ('capacity2', replace(p, biology=replace(p.biology, capacity_ratio=0.74*2))),
]
rows = []
for name, model in variants:
    for eq in equilibrium_states(model):
        rows.append(dict(variant=name, kind=eq['kind'], temperature_k=eq['t_k'],
                         r=eq['r'], stable=eq['stable'],
                         leading_eigenvalue_real=eq['max_real_yr'],
                         biomass_A=float(eq['y'][1]), biomass_M=float(eq['y'][2])))
Path(__file__).with_name('counterfactual_equilibria.json').write_text(json.dumps(rows, indent=2)+'\n')
print(json.dumps(rows, indent=2))
