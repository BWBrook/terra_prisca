"""Fresh 30-year recomputation of C07, using only the committed initial row."""
import csv,json
from pathlib import Path
import numpy as np
from terra_prisca.haze_world.population_coupling import reference, temperature_k
from terra_prisca.haze_world.finite_populations import integrate_finite,CellProcess

source=Path('models/haze_world/figures/finite_populations/c07_transient.csv')
with source.open() as f: rows=list(csv.DictReader(f))
cols=['hydrogen_pa','acetogens_gdw_l','methanogens_gdw_l','acetate_mol_l','methane_ratio']
initial=np.array([float(rows[0][k]) for k in cols])
p=reference()
run=integrate_finite(initial,p,30.,CellProcess(),sample_every_censuses=1)
comparisons=[]
for j,t in enumerate(run.t):
    stored=next(r for r in rows if float(r['time_yr'])==t)
    expected=np.array([float(stored[k]) for k in cols])
    comparisons.append(dict(time_yr=float(t),y=run.y[:,j].tolist(),
        temperature_k=float(temperature_k(run.y[-1,j],p.climate)),
        absolute_stock_errors=np.abs(run.y[:,j]-expected).tolist()))
out=dict(scope='Fresh 30-year prefix only; does not rerun 100000-year endpoint or stochastic survival.',
    extinction_events=run.extinction_events,comparisons=comparisons)
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
