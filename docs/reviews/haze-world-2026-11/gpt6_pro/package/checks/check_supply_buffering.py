"""Fixed/product chemistry supply buffering; compact equilibrium recomputation."""
from dataclasses import replace
from pathlib import Path
import json
import numpy as np
from terra_prisca.haze_world.population_coupling import reference, equilibrium_states
rows=[]
for f in [0.,.5]:
    for potential in [.24,.27,.2999,.3,.3001,.33,.4,.44,.6]:
        for activity in ['fixed','products']:
            p=replace(reference(potential),acetate_fraction=f,activity_feedback=activity)
            for e in equilibrium_states(p):
                if e['stable']:
                    rows.append(dict(f=f,potential=potential,activity=activity,
                       control='community',kind=e['kind'],temperature_k=e['t_k'],
                       r=e['r'],leading_eigenvalue_real=e['max_real_yr'],
                       acetate_mol_l=float(e['y'][3])))
            if f==.5 and potential in [.2999,.3,.3001]:
                for e in equilibrium_states(replace(p,enabled=(False,True))):
                    if e['stable']:
                        rows.append(dict(f=f,potential=potential,activity=activity,
                           control='methanogen_only',kind=e['kind'],temperature_k=e['t_k'],
                           r=e['r'],leading_eigenvalue_real=e['max_real_yr'],
                           acetate_mol_l=float(e['y'][3])))
summary=[]
for f in [0.,.5]:
    for activity in ['fixed','products']:
        vals={r['potential']:r['temperature_k'] for r in rows if r['f']==f and r['activity']==activity and r['control']=='community'}
        slope=(vals[.3001]-vals[.2999])/.0002
        if f==.5:
            cv={r['potential']:r['temperature_k'] for r in rows if r['f']==f and r['activity']==activity and r['control']=='methanogen_only'}
            cslope=(cv[.3001]-cv[.2999])/.0002
        else:cslope=None
        summary.append(dict(f=f,activity=activity,community_slope_k_per_potential=slope,
            control_slope_k_per_potential=cslope,
            signed_gain=slope/cslope if cslope else None,
            absolute_gain=abs(slope/cslope) if cslope else None))
result=dict(rows=rows,local_summary=summary)
Path(__file__).with_name('supply_buffering.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
