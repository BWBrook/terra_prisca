"""Count/grid sensitivity and longer follow-up of the reported H stranding case.

Run from the repo root: uv run python models/haze_world/review/strain_robustness.py OUTDIR
Three workers; common starting genotype and explicit mutation/cutoff rescaling.
The strict runs change only solver tolerances in the worker, not model equations.
"""

import csv,json,sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
from terra_prisca.haze_world.darwinian import reference,Constraint
from terra_prisca.haze_world.experiments import flux_for_potential
from terra_prisca.haze_world.strains import Grid,Run,StrainModel,supply_schedule

OUT=Path(sys.argv[1])

def job(args):
    step,check,base_mutation,scale,years,strict=args
    import terra_prisca.haze_world.strains as module
    from scipy.integrate import solve_ivp as standard_solver
    module.solve_ivp=standard_solver
    if strict:
        original_solver=standard_solver
        def accurate(*positional,**keywords):
            keywords["rtol"]=1e-9
            keywords["atol"]=np.asarray(keywords["atol"])*.01
            return original_solver(*positional,**keywords)
        module.solve_ivp=accurate
    p,losses=reference()
    mutation=base_mutation*(.5/step)**2 if scale else base_mutation
    relative_floor=1e-6*step/.5 if scale else 1e-6
    run=Run(Constraint(energy_ev=.65),losses[2],mutation=mutation,b_min_rel=relative_floor,t_zero_k=265.,check_yr=check)
    # All lattices include 285.5K, the default experiment's initial clone.
    grid=Grid(theta_min_k=245.5,theta_max_k=310.5,step_k=step)
    model=StrainModel(p,run,grid)
    original_snapshot=model.snapshot
    def snapshot(t,y,phi):
        row=original_snapshot(t,y,phi)
        total=float(y[2:].sum())
        row['boundary_biomass_fraction']=float((y[2]+y[-1])/total) if total>0 else 0.
        return row
    model.snapshot=snapshot
    phi0=float(flux_for_potential(.22,p)); phi1=float(flux_for_potential(.02,p))
    y0,e=model.resident_state(phi0)
    initial=np.zeros_like(y0[2:]); i=int(np.argmin(abs(model.theta-285.5)))
    assert abs(model.theta[i]-285.5)<1e-12
    rho=float(model.rho(e['t_k'])[i])
    d=model.half_sat/(rho-1)
    initial[i]=(model.c*phi0-run.k_donor*d)/run.death
    y0=np.r_[d,e['r'],initial]
    b_star=float(initial.sum()); threshold=relative_floor*b_star
    schedule=supply_schedule(phi0,phi1,2000.,1000.)
    out=model.integrate(y0,schedule,years,threshold,record_every_yr=100.)
    series=out['series']; last=series[-1]
    result=dict(horizon_yr=years,strict_solver=strict,grid_step_k=step,census_yr=check,base_mutation=base_mutation,scaled=scale,mutation=mutation,
        mutational_variance_per_birth_k2=2*mutation*step*step,b_min_rel=relative_floor,
        floor_density_rel_per_k=relative_floor/step,initial_theta_k=float(model.theta[i]),
        survived=out['extinct_at_yr'] is None,extinct_after_decline_start_yr=(out['extinct_at_yr']-2000 if out['extinct_at_yr'] is not None else ''),
        final_temperature_k=last['t_k'],final_mean_theta_k=last['mean_theta_k'],final_biomass_rel=float(out['y'][2:].sum()/b_star),
        minimum_biomass_rel=out['min_total_biomass']/b_star,
        maximum_mean_theta_k=max(s['mean_theta_k'] for s in series if np.isfinite(s['mean_theta_k'])),
        maximum_boundary_biomass_fraction=max(s['boundary_biomass_fraction'] for s in series))
    print(json.dumps(result),flush=True)
    return result

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    jobs=[]
    for years in (63000.,203000.):
        jobs += [(.5,dt,m,False,years,False) for dt in (1.,3.,10.,30.,100.) for m in (1e-8,1e-6)]
        jobs += [(h,10.,m,scaled,years,False) for h in (.25,1.) for m in (1e-8,1e-6) for scaled in (False,True)]
    jobs += [(.125,10.,1e-6,True,203000.,False)]
    jobs += [(.5,10.,1e-6,False,63000.,True),(.25,10.,1e-6,True,63000.,True)]
    with Pool(3,maxtasksperchild=1) as pool:
        rows=list(pool.imap_unordered(job,jobs))
    rows.sort(key=lambda r:(r['horizon_yr'],r['strict_solver'],r['grid_step_k'],r['census_yr'],r['base_mutation'],r['scaled']))
    with (OUT/'strain_robustness.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    metadata=dict(reviewed_commit='85041a0',constraint='H E=0.65',loss='linear',bridge_T0_K=265.,
        initial_potential=.22,final_potential=.02,spinup_yr=2000.,decline_yr=1000.,
        trait_domain_K=[245.5,310.5],common_initial_theta_K=285.5,
        scaling='m=m0*(0.5/h)^2, B_min_rel=1e-6*h/0.5; raw cases hold both fixed',
        census_note='Counts are model interventions, not integration timesteps',
        long_runs=sum(r['horizon_yr']==203000. for r in rows),
        long_run_extinctions=sum(r['horizon_yr']==203000. and not r['survived'] for r in rows),
        max_recorded_boundary_biomass_fraction=max(r['maximum_boundary_biomass_fraction'] for r in rows))
    (OUT/'strain_robustness_metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
