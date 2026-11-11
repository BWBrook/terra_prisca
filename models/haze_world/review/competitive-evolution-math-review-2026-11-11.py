"""Independent selected checks of the specified evolutionary trait family.

No production best-response or canonical-equation implementation is called.
"""
from dataclasses import replace
from hashlib import sha256
import csv
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, minimize_scalar
from scipy.interpolate import PchipInterpolator

from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world import two_guilds as reference

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).parent
KB=8.617333e-5
NODES=np.array(reference.TEMPERATURES_C)
CFG=core.reference().biology
PAIRS=[reference.guilds(float(t),CFG) for t in NODES]
V=np.array([[p[i].rate_scale for p in PAIRS] for i in (0,1)])
K=np.array([[p[i].km_pa for p in PAIRS] for i in (0,1)])


def digest(path): return sha256(Path(path).read_bytes()).hexdigest()


def guild(t_k,u,i,loss=.001,energy=.65,freeze_h=False,freeze_m=False):
    actual=reference.guilds(t_k-273.15,CFG)[i]
    warm=reference.guilds(30.,CFG)[i]
    v=np.interp(u,NODES,V[i])*np.exp(-energy/KB*(1/t_k-1/(u+273.15)))
    return replace(actual,rate_scale=float(v),km_pa=float(np.interp(u,NODES,K[i])),
                   threshold_pa=warm.threshold_pa if freeze_h else actual.threshold_pa,
                   maintenance=warm.maintenance if freeze_m else actual.maintenance)


def best(t_k,i,loss,energy,low=4.,freeze_h=False,freeze_m=False):
    candidates=[]
    for a,b in zip(np.r_[low,NODES[NODES>low]][:-1],np.r_[low,NODES[NODES>low]][1:]):
        objective=lambda u:guild(t_k,u,i,loss,energy,freeze_h,freeze_m).rstar(loss)
        result=minimize_scalar(lambda u:min(objective(u),1e100),bounds=(a,b),method='bounded',options={'xatol':1e-10})
        candidates.extend([(objective(a),float(a)),(objective(b),float(b)),(objective(float(result.x)),float(result.x))])
    return min(candidates)


def roots(loss,energy,low=4.,freeze_h=False,freeze_m=False):
    def difference(t):
        a,b=[best(t,i,loss,energy,low,freeze_h,freeze_m)[0] for i in (0,1)]
        return a-b
    ts=np.linspace(273.,303.15,303)
    values=[difference(t) for t in ts]
    out=[]
    for a,b,fa,fb in zip(ts[:-1],ts[1:],values[:-1],values[1:]):
        if np.isfinite(fa) and np.isfinite(fb) and fa*fb<0:
            t=brentq(difference,a,b,xtol=1e-10)
            out.append(dict(temperature_k=float(t),positions_c=[best(t,i,loss,energy,low,freeze_h,freeze_m)[1] for i in (0,1)]))
    return out


def slopes(u,i):
    j=int(np.clip(np.searchsorted(NODES,u,side='right')-1,0,len(NODES)-2))
    return (V[i,j+1]-V[i,j])/(NODES[j+1]-NODES[j]),(K[i,j+1]-K[i,j])/(NODES[j+1]-NODES[j])


def gradient(t,p,u,i,energy=.65):
    g=guild(t,u,i,energy=energy)
    v0=np.interp(u,NODES,V[i]);sv,sk=slopes(u,i)
    vu=g.rate_scale*(sv/v0-energy/(KB*(u+273.15)**2))
    available=p-g.threshold_pa
    assert available>0
    return g.yield_g_mol*available*(vu*(g.km_pa+available)-g.rate_scale*sk)/(g.km_pa+available)**2


def mixed_state(t,u,loss=.001,energy=.65,fraction=.5):
    p=replace(core.reference(),acetate_fraction=fraction,biology=replace(CFG,loss_h=loss))
    pair=[guild(t,u[i],i,loss,energy) for i in (0,1)]
    pressure=pair[0].rstar(loss)
    response=core.response('B')
    indices=np.flatnonzero((response.temperatures_k[:-1]>t)&(response.temperatures_k[1:]<t))
    assert len(indices)==1
    j=indices[0]
    r=response.ratios[j]+(t-response.temperatures_k[j])*(response.ratios[j+1]-response.ratios[j])/(response.temperatures_k[j+1]-response.temperatures_k[j])
    required=np.array([g.maintenance+loss/g.yield_g_mol for g in pair])
    catabolic=required-loss*np.array([g.assimilation_mol_g for g in pair])
    captured=core.supply_h2(p)-p.biology.exchange_mol_l_h_pa*(pressure-p.biology.atmosphere_pa)
    abiotic=core.atmosphere('B')['flux_to_ratio_per_yr']*p.climate.abiotic_flux
    delivery=4*(p.loss.rate(r)-abiotic)/(core.inventory_to_ratio(p)*core.HOURS_PER_YEAR)
    x=np.linalg.solve(np.array([required,[fraction*catabolic[0],catabolic[1]]]),[captured,delivery])
    assert min(x)>0
    krec,kother=core.recycling_rates(t,p)
    acetate=catabolic[0]*x[0]*core.HOURS_PER_YEAR/(4*(krec+kother))
    return np.r_[pressure,x,acetate,r]


def canonical_control():
    crossing=roots(.001,.65)[0]
    t=crossing['temperature_k'];u=np.array(crossing['positions_c']);state=mixed_state(t,u)
    def environment(v):
        fun=lambda tt:guild(tt,v[0],0).rstar(.001)-guild(tt,v[1],1).rstar(.001)
        tt=brentq(fun,t-.5,t+.5,xtol=1e-12)
        return tt,guild(tt,v[0],0).rstar(.001)
    def selection(v,ratio):
        tt,pressure=environment(v)
        weights=state[1:3]/max(state[1:3])*np.array([1.,ratio])
        return weights*np.array([gradient(tt,pressure,v[i],i) for i in (0,1)])
    matrices=[]
    for ratio in (.1,1.,10.):
        for step in (1e-3,1e-4):
            matrix=np.column_stack([(selection(u+step*np.eye(2)[i],ratio)-selection(u-step*np.eye(2)[i],ratio))/(2*step) for i in (0,1)])
            eigen=np.linalg.eigvals(matrix)
            assert max(eigen.real)<0
            matrices.append(dict(mutation_supply_ratio_m_to_a=ratio,step_c=step,jacobian=matrix.tolist(),eigenvalues=eigen.real.tolist()))
    env_columns=[]
    for i in (0,1):
        delta=1e-4*np.eye(2)[i]
        env_columns.append(((np.array(environment(u+delta))-np.array(environment(u-delta)))/(2e-4)).tolist())
    return dict(temperature_k=t,positions_c=u.tolist(),state=state.tolist(),selection_gradient_h_per_c=[gradient(t,state[0],u[i],i) for i in (0,1)],environment_derivatives=env_columns,
        matrices=matrices,scope='One smooth linear-interpolation ESS; arbitrary evolutionary-time normalization, not calibrated years')


def matched_level_diagnostic():
    t=roots(.001,0.)[0]['temperature_k'];positions=(10.,25.)
    base=[guild(t,positions[i],i,energy=0.) for i in (0,1)]
    contributions=[]
    for i,g in enumerate(base):
        coefficient=((-270700.-CFG.cessation_energy_a_j) if i==0 else (-253000.-CFG.cessation_energy_m_j))/(4*reference.GAS_CONSTANT)
        threshold=-coefficient*g.threshold_pa/t**2
        dm=g.maintenance*CFG.maintenance_energy_j/(reference.GAS_CONSTANT*t**2)
        q=g.maintenance+.001/g.yield_g_mol
        maintenance=g.km_pa*g.rate_scale/(g.rate_scale-q)**2*dm
        contributions.append(dict(threshold_pa_k=float(threshold),maintenance_pa_k=float(maintenance)))
    controls=[]
    for fh,fm in ((False,False),(True,False),(False,True),(True,True)):
        def difference(tt):
            values=[]
            for i in (0,1):
                g=guild(tt,positions[i],i,energy=0.)
                g=replace(g,threshold_pa=base[i].threshold_pa if fh else g.threshold_pa,
                          maintenance=base[i].maintenance if fm else g.maintenance)
                values.append(g.rstar(.001))
            return values[0]-values[1]
        controls.append(dict(freeze_thresholds_at_root=fh,freeze_maintenance_at_root=fm,
            root_residual_pa=float(difference(t)),slope_pa_k=float((difference(t+.001)-difference(t-.001))/.002),
            difference_at_root_minus_point1k=float(difference(t-.1)),difference_at_root_plus_point1k=float(difference(t+.1))))
    return dict(post_prediction=True,temperature_k=t,positions_c=positions,per_guild=contributions,
        threshold_contribution_pa_k=contributions[0]['threshold_pa_k']-contributions[1]['threshold_pa_k'],
        maintenance_contribution_pa_k=contributions[0]['maintenance_pa_k']-contributions[1]['maintenance_pa_k'],
        controls=controls,scope='Local matched-level diagnostic; distinct from prescribed30C freezes and does not redefine KE5')


def implementation_control(comparison,canonical):
    from terra_prisca.haze_world import competitive_evolution as evolved
    from terra_prisca.haze_world import evolved_kinetics as kinetics
    table=ROOT/'models/haze_world/figures/competitive_evolution/best_response.csv'
    rows=list(csv.DictReader(table.open()));errors=[]
    for record in comparison:
        selected=[row for row in rows if row['interpolation']=='linear_shape'
            and float(row['loss_h'])==record['loss_h'] and float(row['energy_ev'])==record['energy_ev'] and row['status']=='crossing']
        assert len(selected)==len(record['explicit_measured_trait_range'])
        errors.extend(abs(float(row['temperature_k'])-own['temperature_k']) for row,own in zip(selected,record['explicit_measured_trait_range']))
    assert max(errors)<1e-7
    y=np.array(canonical['state']);p=evolved.parameters(.001,.5)
    traits=kinetics.Traits(tuple(canonical['positions_c']),.65)
    scale=np.maximum(abs(y),[10.,1e-4,1e-4,1e-5,.01]);spectra=[]
    for step in (1e-4,1e-5):
        columns=[]
        for j in range(5):
            delta=step*scale[j]*np.eye(5)[j]
            derivative=(-evolved.rhs(y+2*delta,p,traits)+8*evolved.rhs(y+delta,p,traits)
                        -8*evolved.rhs(y-delta,p,traits)+evolved.rhs(y-2*delta,p,traits))/(12*step)
            columns.append(derivative/scale)
        values=np.linalg.eigvals(np.column_stack(columns));assert max(values.real)<0
        spectra.append(dict(step=step,eigenvalues=[[float(v.real),float(v.imag)] for v in values]))
    return dict(selected_crossings=len(errors),maximum_temperature_difference_k=max(errors),
        rhs=evolved.rhs(y,p,traits).tolist(),redox_residual=float(evolved.redox_residual(y,p,traits)),
        ecological_five_point_spectra=spectra,
        inputs_sha256={str(path.relative_to(ROOT)):digest(path) for path in (table,Path(evolved.__file__),Path(kinetics.__file__))},
        scope='Selected independent roots and one ecological state, not a full production inventory audit')


def final_table_control():
    from terra_prisca.haze_world import competitive_evolution as evolved
    from terra_prisca.haze_world import evolved_kinetics as kinetics
    folder=ROOT/'models/haze_world/figures/competitive_evolution'
    manifest=json.loads((folder/'communities_manifest.json').read_text())
    for name,expected in manifest['outputs'].items():assert digest(folder/name)==expected
    for name,expected in manifest['source_sha256'].items():assert digest(ROOT/name)==expected
    rows=list(csv.DictReader((folder/'communities.csv').open()))
    joint=[r for r in rows if r['status']=='joint_community']
    cooling=[r for r in joint if r['cooling_branch']=='True']
    warm=[r for r in joint if r['cooling_branch']!='True']
    assert all(r['stable']=='True' for r in cooling)
    assert all(r['stable']=='False' for r in warm)
    assert all(all(x['convergence']=='attracting' for x in json.loads(r['convergence'])) for r in cooling)
    mutant_max=[]
    grid=np.linspace(4.,30.,2601)
    for row in joint:
        loss,energy,t=float(row['loss_h']),float(row['energy_ev']),float(row['temperature_k'])
        pressure=json.loads(row['y'])[0]
        for i in (0,1):
            if row['interpolation']=='linear_shape':
                v=np.interp(grid,NODES,V[i]);k=np.interp(grid,NODES,K[i])
            else:
                v=np.exp(PchipInterpolator(NODES,np.log(V[i]))(grid))
                k=np.exp(PchipInterpolator(NODES,np.log(K[i]))(grid))
            local=reference.guilds(t-273.15,replace(CFG,loss_h=loss))[i]
            v=v*np.exp(-energy/KB*(1/t-1/(grid+273.15)))
            available=max(pressure-local.threshold_pa,0.)
            fitness=local.yield_g_mol*(v*available/(k+available)-local.maintenance)-loss
            mutant_max.append(float(max(fitness)))
    assert max(mutant_max)<=1e-8
    spectral=[]
    selected=[r for r in joint if r['loss_h']=='0.003' and r['energy_ev']=='0.0' and r['interpolation']=='linear_shape' and r['fraction']=='0.5']
    assert len(selected)==2
    for row in selected:
        y=np.array(json.loads(row['y']));p=evolved.parameters(.003,.5)
        traits=kinetics.Traits(tuple(json.loads(row['positions_c'])),0.)
        scales=np.maximum(abs(y),[10.,1e-4,1e-4,1e-5,.01]);spectra=[]
        for step in (1e-4,1e-5):
            columns=[]
            for j in range(5):
                delta=step*scales[j]*np.eye(5)[j]
                derivative=(-evolved.rhs(y+2*delta,p,traits)+8*evolved.rhs(y+delta,p,traits)-8*evolved.rhs(y-delta,p,traits)+evolved.rhs(y-2*delta,p,traits))/(12*step)
                columns.append(derivative/scales)
            values=np.linalg.eigvals(np.column_stack(columns));maximum=float(max(values.real))
            assert (maximum<0)==(row['stable']=='True')
            spectra.append(dict(step=step,max_real_yr=maximum,eigenvalues=[[float(v.real),float(v.imag)] for v in values]))
        spectral.append(dict(community_id=row['community_id'],cooling=row['cooling_branch']=='True',spectra=spectra))
    return dict(input_sha256={name:digest(folder/name) for name in ('communities.csv','communities_manifest.json')},
        joint_rows=len(joint),stable_cooling_rows=len(cooling),unstable_greenhouse_rows=len(warm),
        no_joint_settings=sum(r['status']!='joint_community' for r in rows),
        independent_mutant_assays=len(mutant_max),maximum_mutant_growth_h=max(mutant_max),
        selected_branch_spectra=spectral,inventory_refinement_disagreements=manifest['inventory_refinement_disagreements'],
        scope='Independent all-grid mutant growth; two selected high-turnover spectra; class and manifest recount')


def main():
    comparison=[]
    for loss in (.001,.003):
        for energy in (0.,.2,.45,.65):
            comparison.append(dict(loss_h=loss,energy_ev=energy,
                explicit_measured_trait_range=roots(loss,energy),preview_trait_range=roots(loss,energy,-.15)))
    anchors=[]
    for fh,fm in ((False,False),(True,False),(False,True),(True,True)):
        anchors.append(dict(freeze_thresholds=fh,freeze_maintenance=fm,roots=roots(.001,0.,freeze_h=fh,freeze_m=fm)))
    canonical=canonical_control()
    result=dict(inputs_sha256={str(path.relative_to(ROOT)):digest(path) for path in (
        HERE.parent/'competitive-evolution-spec.md',HERE/'competitive_evolution_preview.py',Path(core.__file__),Path(reference.__file__))},
        checker_sha256=digest(Path(__file__)),trait_bound_comparison=comparison,anchors_reference_loss_zero_energy=anchors,
        canonical_smooth_control=canonical,matched_level_diagnostic=matched_level_diagnostic(),
        implementation_control=implementation_control(comparison,canonical),final_table_control=final_table_control(),
        scope='Independent selected linear-shape algebra and finite differences, not a repeat of the full experiment or a general evolutionary theorem')
    HERE.joinpath('competitive-evolution-math-review-2026-11-11.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(bound_controls=len(comparison),anchors=anchors,canonical_temperature=result['canonical_smooth_control']['temperature_k'])))

if __name__=='__main__': main()
