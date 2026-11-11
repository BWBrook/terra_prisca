from dataclasses import replace
from pathlib import Path
import json
import numpy as np
from scipy.optimize import brentq
from terra_prisca.haze_world import evolved_kinetics as ek
from terra_prisca.haze_world.population_coupling import reference
b=reference().biology
energies=[0.,.1,.2,.3,.45,.65]
temperatures=np.linspace(273.15,303.15,301)
# Scalar entries copied from separately calculated per-guild best responses:
# This only relaxes the model's assumption that both guilds share one E.
cache={(e,float(t)):ek.best_response(float(t),b,e,refine=False)['rstars_pa'] for e in energies for t in temperatures}
rows=[]
for ea in energies:
 for em in energies:
  values=np.array([cache[ea,float(t)][0]-cache[em,float(t)][1] for t in temperatures])
  roots=[]
  def difference(t):return ek.best_response(float(t),b,ea)['rstars_pa'][0]-ek.best_response(float(t),b,em)['rstars_pa'][1]
  for i in range(len(temperatures)-1):
   if np.isfinite(values[i:i+2]).all() and values[i]*values[i+1]<0:
    t=brentq(difference,temperatures[i],temperatures[i+1],xtol=1e-9)
    slope=(difference(t+.001)-difference(t-.001))/.002
    roots.append({'temperature_k':t,'slope_pa_k':slope,'cooling_range':273.39<=t<=297.008,'acetogen_u':ek.best_response(t,b,ea)['positions_c'][0],'methanogen_u':ek.best_response(t,b,em)['positions_c'][1]})
  rows.append({'ea':ea,'em':em,'roots':roots,'difference_273_15':float(values[0]),'difference_303_15':float(values[-1])})
Path(__file__).with_name('independent_trait_axes.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
