"""Read-only independent Issue 4 budget audit; no integrations."""
import csv, hashlib, json, math
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
from terra_prisca.haze_world import population_coupling as core

import argparse
parser=argparse.ArgumentParser(description="Bounded Issue 4 independent check; no integrations")
parser.add_argument("--output",type=Path,required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[2]
source=root/'models/haze_world/review/issue4_acetate_fate.json'
record=json.loads(source.read_text()); ref=core.reference(); bio=ref.biology

def pair(t_c): return core.guilds(t_c,bio)
t_c=brentq(lambda t: pair(t)[0].rstar(bio.loss_h)-pair(t)[1].rstar(bio.loss_h),4.,30.)
guilds=pair(t_c); pressure=guilds[0].rstar(bio.loss_h)
eta=np.array([1-g.assimilation_mol_g*bio.loss_h/float(g.uptake(pressure)) for g in guilds]); a,m=eta
np.testing.assert_allclose(eta,[record['parts']['eta_A'],record['parts']['eta_M']],rtol=1e-12)
with (root/'models/haze_response/arney2016/cases.csv').open() as fh:
    case=next(x for x in csv.DictReader(fh) if x['case']=='B')
area_m2=4*math.pi*(6.371e6)**2
co2_moles=float(case['p_co2_bar'])*1e5/(.028*9.81)*area_m2
methane_total=co2_moles*record['parts']['mixed_ratio']/ref.climate.lifetime_yr/1e12
abiotic=ref.climate.abiotic_flux*(area_m2*1e4)*3.15576e7/6.02214076e23/1e12
biotic=methane_total-abiotic
assert math.isclose(methane_total,record['sinks'][0]['methane_tmol_yr'],rel_tol=1e-12)
K=ref.habitat_l_cm2*(area_m2*1e4)*core.HOURS_PER_YEAR/(4*1e12)
n=biotic/K
J=core.supply_h2(ref); e=bio.exchange_mol_l_h_pa*(pressure-bio.atmosphere_pa); U=J-e
assert math.isclose(n,record['parts']['needed'],rel_tol=1e-12)
windows=[]
for row in record['windows']:
    f,b=row['f'],row['biomass_recycled']
    ym=m+b*(1-m); ya=f*a+b*(1-a)
    lo=.3*(e+n/ym)/J; hi=math.inf if ya==0 else .3*(e+n/ya)/J
    assert math.isclose(lo,row['low'],rel_tol=1e-12)
    if row['high'] is not None:
        assert math.isclose(hi,row['high'],rel_tol=1e-12)
    else: assert math.isinf(hi)
    windows.append({'f':f,'b':b,'low':lo,'high':None if math.isinf(hi) else hi,'Q':None if math.isinf(hi) else hi/lo})
sinks=[]
for f in (0.,.5,.7,.9,1.):
    ua=(m*U-n)/(m-f*a); um=U-ua
    acetate=(1-f)*a*ua*K
    biomass=((1-a)*ua+(1-m)*um)*K
    np.testing.assert_allclose(acetate+biomass,(U-n)*K,rtol=1e-12)
    sinks.append(dict(f=f,feasible=bool(0<=ua<=U),acetogen_uptake_share=ua/U,
                      acetate_tmol_yr=acetate,biomass_ch4_equivalent_tmol_yr=biomass,
                      total_nonmethane_tmol_ch4_equivalent_yr=acetate+biomass))
full_recovery=[]
for tk in (277.15,t_c+273.15,286.):
    rs=[g.rstar(bio.loss_h) for g in pair(tk-273.15)]
    capture=[J-bio.exchange_mol_l_h_pa*(r-bio.atmosphere_pa) for r in rs]
    full_recovery.append(dict(temperature_k=tk,rstar_pa=rs,captured_h2_mol_l_h=capture,
                              methane_tmol_yr=[q*K for q in capture]))
burial=[]
for b in (.98,.998):
    ym=m+b*(1-m);ya=a+b*(1-a);Q=(e+n/ya)/(e+n/ym)
    burial.append(dict(b=b,Q=Q,Q_minus_1=Q-1,approx_warming_width_k=140.7*math.log(Q)))
out=dict(input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),t_star_k=t_c+273.15,pressure_star_pa=pressure,
         eta_a=a,eta_m=m,methane_total_tmol_yr=methane_total,biotic_methane_tmol_yr=biotic,
         local_h2_to_global_ch4_equivalent=K,windows=windows,reference_sinks=sinks,
         reference_largest_feasible_f=(n/U)/a,
         reference_total_nonmethane_tmol_ch4_equivalent_yr=(U-n)*K,
         same_supply_same_T_all_methanogen_biomass_tmol_ch4_equivalent_yr=(1-m)*U*K,
         additional_sink_relative_same_supply_same_T_methanogen=(m*U-n)*K,
         lower_supply_methanogen_baseline_biomass_tmol_ch4_equivalent_yr=(n/m-n)*K,
         extra_h2_supply_above_lower_methanogen_endpoint_tmol_ch4_equivalent_yr=(U-n/m)*K,
         full_recovery_capture=full_recovery,near_complete_biomass_recycling=burial,
         max_fable_estimate_relative_error=max((row['fable_estimate']/row['ratio']-1) for row in record['windows'] if row['biomass_recycled']==0 and row['fable_estimate'] is not None))
args.output.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ('windows',)},indent=2))
