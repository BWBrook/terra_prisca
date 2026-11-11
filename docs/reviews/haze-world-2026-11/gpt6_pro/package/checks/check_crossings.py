import json,sys
from dataclasses import replace
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
sys.path.insert(0, str(Path.cwd() / 'src'))
from terra_prisca.haze_world.population_coupling import reference
from terra_prisca.haze_world.two_guilds import guilds
p=reference(); base=p.biology

def crossings(c,la=.001,lm=.001):
    def f(t):
        a,m=guilds(t-273.15,c)
        return a.rstar(la)-m.rstar(lm)
    grid=np.linspace(273,303.15,1207)
    roots=[]
    for a,b in zip(grid[:-1],grid[1:]):
        fa,fb=f(a),f(b)
        if np.isfinite(fa) and np.isfinite(fb) and fa*fb<0:
            root=brentq(f,a,b)
            if not roots or abs(root-roots[-1])>1e-6:roots.append(root)
    return roots
out={'reference':crossings(base),'co2_assay_pa':12000.,'co2_climate_pa':1800.,'turnover':[],'physiology':[]}
co2a=(12000/1800)**.5;co2m=(12000/1800)**.25
out['co2_matched_factors']=[co2a,co2m]
out['co2_matched_crossing']=crossings(replace(base,threshold_a30=base.threshold_a30*co2a,threshold_m30=base.threshold_m30*co2m))
for la in [0.0005,.00075,.001,.00125,.0015,.002]:
    for lm in [.0005,.00075,.001,.00125,.0015,.002]:
        out['turnover'].append(dict(loss_a_h=la,loss_m_h=lm,roots_k=crossings(base,la,lm)))
for name in ['capacity_ratio','yield_m','maintenance_m30','threshold_a30','threshold_m30','km_scale_a','km_scale_m','maintenance_energy_j']:
    for factor in [.5,.75,1,1.25,1.5,2]:
        c=replace(base,**{name:getattr(base,name)*factor})
        out['physiology'].append(dict(parameter=name,factor=factor,roots_k=crossings(c)))
print(json.dumps(out,indent=2))
Path(__file__).with_name('crossings.json').write_text(json.dumps(out,indent=2)+'\n')
