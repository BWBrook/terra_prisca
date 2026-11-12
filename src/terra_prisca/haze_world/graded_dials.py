"""D1/D2 continued equilibria, raw supply slopes and thermal delay margins."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import shutil

import numpy as np
from scipy.linalg import eig

from . import continuum_core as weighted
from . import continuum_experiments as numerical
from . import dynamic_core as reference
from . import graded_acetate as acetate
from . import graded_spread as spread

ROOT=Path(__file__).resolve().parents[3]
OUTPUT=ROOT/'models/haze_world/figures/graded_dials'
KAPPAS=(0.,1e-4,3e-4,.001,.003,.01,.03,.1,.3,1.)
SIGMAS=(.003,.01,.03,.1,.3,1.)
BRANCHES=(('D1',0.),('D1',.5),('D2',1e-4),('D2',1e-3))


def sources():
    values=numerical.sources()
    paths=[Path(__file__),Path(acetate.__file__),Path(spread.__file__),
           ROOT/'models/haze_world/graded-dial-spec.md',ROOT/'models/haze_world/graded-dial-methods.md']
    paths+=list((ROOT/'src/terra_prisca/haze_response').glob('*.py'))
    values.update({str(p.relative_to(ROOT)):numerical.digest(p) for p in paths})
    return values


def reconstruct(record):
    if record['stage']=='D1':return acetate.parameters(record['kappa'],record['fraction'])
    return spread.parameters_from_record(record)


def blocks(y,p,stage):
    return acetate.blocks(y,p) if stage=='D1' else weighted.local_blocks(y,p)


def modal_record(y,p,b,tau=0.):
    scale=weighted.operator_scales(y,p,b,tau)
    matrix=weighted.dense_matrix(y,p,tau,blocks=b)*scale[None,:]/scale[:,None]
    values,vectors=eig(matrix,check_finite=True)
    order=np.argsort(values.real)[::-1]
    norm=np.linalg.norm(matrix)
    rows=[]
    for index in order:
        value=values[index];vector=vectors[:,index]
        residual=float(np.linalg.norm(matrix@vector-value*vector)/
                       (max(norm,abs(value))*np.linalg.norm(vector)))
        if value.imag>1e-8*max(1.,abs(value.real)):
            rows.append(dict(real_yr=float(value.real),omega_yr=float(value.imag),
                period_yr=float(2*np.pi/value.imag),
                damping_time_yr=float(-1/value.real) if value.real<0 else None,
                eigenpair_residual=residual))
    leading=values[order[0]]
    return dict(leading_real_yr=float(leading.real),leading_imag_yr=float(abs(leading.imag)),
                complex_pairs=rows,selected_pair=rows[0] if rows else None)


def raw_supply_check(y,p,stage,expected,step=1e-3):
    values=[]
    for offset in (-step,step):
        q=replace(p,base=replace(p.base,climate=replace(p.base.climate,
            donor_flux=p.base.climate.donor_flux*np.exp(offset))))
        found=(acetate.equilibrium(y,q) if stage=='D1' else weighted.equilibrium(y,q,tolerance=1e-10))
        if found is None:return dict(status='unresolved',step=step)
        values.append(found['t_k'])
    value=float((values[1]-values[0])/(2*step))
    return dict(status='passed' if abs(value-expected)<=max(1e-7,.02*abs(expected)) else 'disagrees',
                step=step,Sc_finite_difference=value)


def enrich(record):
    if 'y' not in record:return record
    stage=record['stage'];p=reconstruct(record);y=np.asarray(record['y'])
    b=blocks(y,p,stage)
    modes=modal_record(y,p,b)
    record['zero_lag_modes']=modes
    tau=record['lag']['tau_c']
    if record['lag']['status']=='finite_crossing':
        crossing=modal_record(y,p,b,tau)
        pair=crossing['selected_pair']
        record['critical_modes']=crossing
        record['critical_omega_yr']=pair['omega_yr'] if pair else None
    else:record['critical_omega_yr']=None
    pair=modes['selected_pair']
    estimate=None if pair is None or pair['damping_time_yr'] is None else 2*(-pair['real_yr'])/pair['omega_yr']**2
    record['weak_mode_tau_yr']=estimate
    record['weak_mode_ratio']=estimate/tau if estimate is not None and tau is not None and tau>0 else None
    record['supply_check']=raw_supply_check(y,p,stage,record['Sc'])
    if record['supply_check']['status']=='disagrees':
        record['supply_check_fine']=raw_supply_check(y,p,stage,record['Sc'],step=1e-4)
    return record


def d1_advance(previous,kappa,fraction,history,depth=0):
    p=acetate.parameters(kappa,fraction)
    seed=np.asarray(previous['y'])
    found=acetate.equilibrium(seed,p)
    history.append(dict(from_kappa=previous.get('kappa',0.),to_kappa=kappa,depth=depth,
                        accepted=found is not None,residual=found['residual'] if found else None))
    if found is not None:return found
    old=previous.get('kappa',0.)
    if depth>=16 or kappa-old<=1e-10:return None
    midpoint=(old+kappa)/2
    middle=d1_advance(previous,midpoint,fraction,history,depth+1)
    return None if middle is None else d1_advance(dict(middle,kappa=midpoint),kappa,fraction,history,depth+1)


def d1_point(kappa,fraction,previous=None,kind='prescribed'):
    p=acetate.parameters(kappa,fraction)
    if previous is None:
        initial=reference.DynamicParams(p.base,'fixed')
        roots=[r for r in reference.equilibrium_states(initial) if r['kind']=='mixed' and r['status']=='accepted']
        if len(roots)!=1:raise ArithmeticError('D1 needs one supported initial mixed branch')
        previous=dict(roots[0],kappa=0.)
    history=[];found=d1_advance(previous,kappa,fraction,history)
    common=dict(stage='D1',branch_id=f'D1_f{fraction:g}',kind=kind,dial=kappa,kappa=kappa,
        chemistry='graded_acetate',fraction=fraction,sigma_k=0.,dispersal_yr=p.dispersal_yr,nominal_potential=.3)
    if found is None:return dict(common,status='continuation_unresolved',continuation_history=history)
    y=found['y'];b=acetate.blocks(y,p);slopes=acetate.slopes(y,p)
    finite=acetate.frozen_supply_check(y,p)
    accepted=finite['status']=='passed' and abs(finite['S0_finite_difference']-slopes['S0'])<=max(.001,.02*abs(slopes['S0']))
    if not accepted:
        finite=acetate.frozen_supply_check(y,p,step=1e-5)
        accepted=finite['status']=='passed' and abs(finite['S0_finite_difference']-slopes['S0'])<=max(.001,.02*abs(slopes['S0']))
    frozen=numerical.spectrum(y,p,blocks=weighted.frozen_blocks(y,p,b))
    slopes.update(frozen_fd_agrees=accepted,frozen_finite_input=finite,frozen_leading_real=frozen['leading_real'])
    value=dict(common,status='accepted' if accepted else 'frozen_response_unresolved',
        y=y,nodes=1,offsets=[0.],weights=[1.],panels=[],temperature_k=found['t_k'],ratio=float(y[-1]),
        Sc=slopes.get('Sc'),S0=slopes.get('S0'),G_loc=slopes.get('G_loc'),gain_status=slopes['status'],gain=slopes,
        lag=numerical.lag_check(y,p,blocks=b),per_cell_balance_residual_yr=found['residual'],continuation_history=history)
    return enrich(value)


def d2_point(sigma,d,previous=None,kind='prescribed'):
    value=spread.solve_sigma(sigma,d,previous)
    value.update(branch_id=f'D2_d{d:g}',kind=kind,dial=sigma,kappa=0.)
    return enrich(value)


def run_branch(stage,value,cache,stamp):
    path=cache/f'{stage}-{value:g}-{stamp}.json'
    if path.exists():return json.loads(path.read_text())
    rows=[];previous=None
    values=KAPPAS if stage=='D1' else (0.,)+SIGMAS
    for dial in values:
        record=d1_point(dial,value,previous) if stage=='D1' else d2_point(dial,value,previous,kind='baseline' if dial==0 else 'prescribed')
        rows.append(numerical.clean(record))
        path.with_suffix('.partial.json').write_text(json.dumps(rows,allow_nan=False)+'\n')
        print(f'{stage} branch={value:g} dial={dial:g}: {record["status"]}',flush=True)
        if record['status'] not in ('accepted','converged','homogeneous_control'):break
        previous=record
    path.write_text(json.dumps(rows,allow_nan=False)+'\n')
    return rows


def flattened(record):
    row={k:v for k,v in record.items() if not isinstance(v,(dict,list,tuple,np.ndarray))}
    row.update(critical_lag_status=record.get('lag',{}).get('status'),critical_lag_yr=record.get('lag',{}).get('tau_c'),
        frozen_fd_agrees=record.get('gain',{}).get('frozen_fd_agrees'),
        supply_check_status=record.get('supply_check_fine',record.get('supply_check',{})).get('status'))
    modes=record.get('zero_lag_modes',{});pair=modes.get('selected_pair') or {}
    row.update(leading_real_zero=modes.get('leading_real_yr'),leading_imag_zero=modes.get('leading_imag_yr'),
               pair_real_zero=pair.get('real_yr'),pair_omega_zero=pair.get('omega_yr'),
               pair_period_zero=pair.get('period_yr'),pair_damping_time_zero=pair.get('damping_time_yr'))
    return row


def write(output,records,hashes):
    output.mkdir(parents=True,exist_ok=True)
    numerical.b1.write_csv(output/'dials.csv',[flattened(r) for r in records])
    states=[]
    for record in records:
        value=flattened(record)
        for key in ('y','offsets','weights','panels','zero_lag_modes','critical_modes','continuation_history'):
            if key in record:value[key]=record[key]
        value['lag']={key:record.get('lag',{}).get(key) for key in ('status','tau_c','crossings')}
        value['doubling_checks']=[dict(iteration=r['iteration'],nodes_before=r['nodes_before'],nodes_after=r['nodes_after'],
            slopes_agree=r['slopes_agree'],lag_agrees=r['lag_agrees'],
            before={k:r['before'].get(k) for k in ('Sc','S0')},after={k:r['after'].get(k) for k in ('Sc','S0')},
            before_lag=r['before']['lag']['tau_c'],after_lag=r['after']['lag']['tau_c']) for r in record.get('doubling_history',[])]
        states.append(value)
    (output/'states.json').write_text(json.dumps(numerical.clean(states),indent=1,allow_nan=False)+'\n')
    manifest=dict(method_freeze_commit='9b63b47',source_sha256=hashes,
        prescribed_count=sum(r['kind']=='prescribed' for r in records),baseline_count=sum(r['kind']=='baseline' for r in records),
        output_sha256={name:numerical.digest(output/name) for name in ('dials.csv','states.json')})
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUTPUT)
    parser.add_argument('--cache',type=Path,default=ROOT/'local/haze/graded_dials')
    parser.add_argument('--workers',type=int,default=2)
    args=parser.parse_args();args.cache.mkdir(parents=True,exist_ok=True)
    hashes=sources();stamp=sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()[:20]
    epoch=args.cache/'source_epochs'/stamp
    for name,digest in hashes.items():
        target=epoch/name;target.parent.mkdir(parents=True,exist_ok=True)
        if numerical.digest(ROOT/name)!=digest:raise ArithmeticError('Source changed while freezing')
        shutil.copyfile(ROOT/name,target)
    records=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs=[pool.submit(run_branch,stage,value,args.cache,stamp) for stage,value in BRANCHES]
        for future in as_completed(jobs):records.extend(future.result())
    if sources()!=hashes:raise ArithmeticError('Numerical source changed during production; epoch retained')
    records.sort(key=lambda r:(r['branch_id'],r['dial']))
    write(args.output,records,hashes)
    print('Saved',len(records),'continued equilibria',flush=True)


if __name__=='__main__':main()
