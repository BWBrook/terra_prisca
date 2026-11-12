"""First physical rare-episode diagnostics, separate from transient production."""

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from . import branching, bottleneck
from . import dynamic_transients as runs
from . import dynamic_realisation as tables

ROOT=Path(__file__).resolve().parents[3]


def first_episode(log_counts,uptake_fraction,*,cap=1e16):
    log_counts=np.asarray(log_counts,float);uptake_fraction=np.asarray(uptake_fraction,float)
    threshold=float(np.log(cap));windows=bottleneck.excursions(log_counts,threshold)
    if not windows:return dict(status='no_rare_episode',window=None)
    initial_lo,initial_hi,initial_terminal=windows[0]
    if not np.any(np.diff(log_counts[initial_lo:initial_hi+1]) < -1e-12):
        return dict(status='first_rare_episode_not_declining',window=None)
    reductions=0
    while True:
        selected=bottleneck.excursions(log_counts[initial_lo:initial_hi+1],threshold)
        if not selected:
            return dict(status='first_episode_not_locally_linear',window=None,
                        initial_window=[initial_lo,initial_hi,initial_terminal],threshold_reductions=reductions)
        a,b,terminal=selected[0];a+=initial_lo;b+=initial_lo
        maximum=float(max(uptake_fraction[a:b+1]))
        if maximum<=1e-10:
            return dict(status='qualified_first_declining_rare_episode',window=(a,b,bool(initial_terminal and terminal)),
                        initial_window=[initial_lo,initial_hi,initial_terminal],log_threshold=threshold,
                        threshold_reductions=reductions,max_uptake_fraction=maximum)
        threshold-=np.log(10.);reductions+=1
        if reductions>1000:raise ArithmeticError('Rarity refinement did not terminate')


def score_first(result,guild):
    t=result['t'];logs=result['log_biomass'][guild]+result['global_log_cell_conversion']
    result_episode=first_episode(logs,result['uptake_fraction'][guild])
    if result_episode['window'] is None:
        return dict(result_episode,assembly_status='unassessed',survival_probability=None,log_survival_probability=None)
    lo,hi,terminal=result_episode['window'];indices=np.arange(lo,hi+1)
    logu=branching.backward_survival(t[indices],result['birth_yr'][guild,indices,None],
             result['death_yr'][guild,indices,None],np.zeros((1,1)),rtol=1e-10,atol=1e-12,max_step=1.)
    math=branching.lineages(np.array([logs[lo]]),logu)
    own=result['first_below_cell_yr'][guild];other=result['first_below_cell_yr'][1-guild]
    own_prior=bool(own is not None and own<t[lo]);other_start=bool(other is not None and other<t[lo])
    other_end=bool(other is not None and other<=t[hi])
    status=('unassessed_threshold_below_one' if result_episode['log_threshold']<0 else
            'unassessed_prior_own_loss' if own_prior else
            'unassessed_other_guild_loss' if other_end else
            'horizon_censored_conditional' if terminal else 'qualified_first_window_conditional')
    return dict(result_episode,start_yr=float(t[lo]),end_yr=float(t[hi]),terminal=terminal,
                assembly_status=status,own_loss_before_start=own_prior,
                other_loss_before_start=other_start,other_loss_before_end=other_end,
                log_entry_cells=float(logs[lo]),log_type_survival=float(logu[0]),
                minimum_log_cells=float(min(logs[indices])),
                log_survival_probability=bottleneck._log_probability(math['log_lambda']),
                scope='Conditional recorded-environment survival over first declining rare episode; not joint recovery',**math)


def assess_receipt(receipt):
    row=receipt['row'];raw=ROOT/row['uncensored_raw']
    if sha256(raw.read_bytes()).hexdigest()!=row['uncensored_sha256']:
        raise ArithmeticError('Uncensored trajectory hash differs from accepted receipt')
    with np.load(raw) as data:result={k:data[k].copy() for k in data.files}
    result.update({k:v for k,v in receipt['uncensored_metadata'].items() if k not in result})
    primary=[score_first(result,g) for g in range(2)]
    for g,value in enumerate(primary):
        other=primary[1-g]
        other_end=other.get('end_yr')
        other_likely=other.get('survival_probability') is not None and other['survival_probability']<.5
        value['other_likely_loss_before_start']=bool(other_likely and other_end is not None and other_end<value.get('start_yr',-np.inf))
        value['other_likely_loss_before_end']=bool(other_likely and other_end is not None and other_end<=value.get('end_yr',-np.inf))
        if value['other_likely_loss_before_end'] and not value['assembly_status'].startswith('unassessed'):
            value['assembly_status']='unassessed_other_guild_likely_loss'
    out=[]
    for g,name in enumerate(('acetogen','methanogen')):
        legacy=receipt['first_windows'][name];value=primary[g]
        common={k:row[k] for k in ('case_id','stage','chemistry','fraction','tau_yr','direction')}
        flat={k:v for k,v in value.items() if not isinstance(v,(dict,list,tuple))}
        out.append(dict(common,guild=name,displaced_resident=bool(row['stage']=='B3' and g==(1 if row['direction']=='A_into_M' else 0)),
            legacy_status=legacy['status'],legacy_start_yr=legacy.get('start_yr'),legacy_end_yr=legacy.get('end_yr'),
            legacy_probability=legacy.get('survival_probability'),legacy_log_probability=legacy.get('log_survival_probability'),
            legacy_prior_own_below_one=bool(result['first_below_cell_yr'][g] is not None and
                  result['first_below_cell_yr'][g]<legacy.get('start_yr',-np.inf)),**flat))
    return out


def run(output,raw):
    manifest=json.loads((output/'transient_manifest.json').read_text())
    records=[];receipt_hashes={}
    for row in manifest['rows']:
        name=Path(row['uncensored_raw']).with_suffix('.json')
        receipt=json.loads((ROOT/name).read_text());receipt_hashes[str(name)]=sha256((ROOT/name).read_bytes()).hexdigest()
        records.extend(assess_receipt(receipt))
    tables.write_csv(output/'transient_first_survival.csv',records)
    displaced=[r for r in records if r['displaced_resident']]
    b2=[r for r in manifest['rows'] if r['stage']=='B2']
    b3=[r for r in manifest['rows'] if r['stage']=='B3']
    result=dict(amendment='Post-diagnostic procedural correction: primary window starts from cap1e16 in the FIRST contiguous rare episode, scored only if declining; never a later global minimum. Original legacy probabilities are retained for comparison.',
        primary_rows=records,receipt_sha256=receipt_hashes,
        recount=dict(total_guild_diagnostics=len(records),legacy_post_own_floor_windows=sum(r['legacy_prior_own_below_one'] for r in records),
            displaced_residents=len(displaced),legacy_displaced_post_own_floor_windows=sum(r['legacy_prior_own_below_one'] for r in displaced),
            qualified_primary=sum(r['assembly_status']=='qualified_first_window_conditional' for r in records),
            other_loss_unassessed=sum(r['assembly_status'].startswith('unassessed_other_guild') for r in records),
            no_rare_episode=sum(r['status']=='no_rare_episode' for r in records),
            first_nondeclining=sum(r['status']=='first_rare_episode_not_declining' for r in records),
            resident_qualified=sum(r['assembly_status']=='qualified_first_window_conditional' for r in displaced)),
        homogeneous_predictions=dict(PB5_fixed_f0_tau1_counterexample=next(r for r in b2 if r['case_id']=='B2_f0_tau1'),
            PB5_scope='The homogeneous below-one prediction fails at tau1 over the full30kyr. Habitat-spread prediction is outside this tranche.',
            PB6_displaced_residents_below_one=sum((r['methanogen_log10_min_cells'] if r['direction']=='A_into_M' else r['acetogen_log10_min_cells'])<0 for r in b3),
            PB6_invasions=len(b3),PB6_scope='Supports all homogeneous settings only; no inference about spread habitats.',
            displaced_first_window_log_probability_range=[min(r['log_survival_probability'] for r in displaced),max(r['log_survival_probability'] for r in displaced)],
            census_direction_dependent_pairs=sum(next(r for r in b3 if r['chemistry']==chem and r['fraction']==f and r['tau_yr']==tau and r['direction']=='A_into_M')['census_endpoint'] !=
                next(r for r in b3 if r['chemistry']==chem and r['fraction']==f and r['tau_yr']==tau and r['direction']=='M_into_A')['census_endpoint']
                for chem in ('fixed','products') for f in (0.,.5) for tau in (0.,3.,30.))),
        assembly_scope='Unassessed if rarity threshold falls below one, earlier own loss or other-guild loss invalidates recorded environment; terminal windows are horizon conditional.',
        source_sha256={str(Path(__file__).relative_to(ROOT)):sha256(Path(__file__).read_bytes()).hexdigest(),
                       str(Path(branching.__file__).relative_to(ROOT)):sha256(Path(branching.__file__).read_bytes()).hexdigest()},
        input_manifest_sha256=sha256((output/'transient_manifest.json').read_bytes()).hexdigest())
    (output/'transient_assessment.json').write_text(json.dumps(runs.clean(result),indent=2,allow_nan=False)+'\n')
    return result


def refinements(output,raw,workers=2):
    requested={'B2_f0_tau1','B2_f0_tau100','B3_fixed_f0.5_tau3_A_into_M','B3_products_f0.5_tau3_M_into_A'}
    cases=[c for c in runs.design() if c.case_id in requested]
    manifest=json.loads((output/'transient_manifest.json').read_text())
    main={r['case_id']:r for r in manifest['rows']};rows=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        jobs={pool.submit(runs.run_case,c,raw,2e-9,2.,.5):c for c in cases}
        for future in as_completed(jobs):
            result=future.result();c=jobs[future];control=result['row'];original=main[c.case_id]
            rows.append(dict(case_id=c.case_id,rtol=2e-9,max_step_yr=2.,sample_step_yr=.5,
                delta_acetogen_log10_min_cells=control['acetogen_log10_min_cells']-original['acetogen_log10_min_cells'],
                delta_methanogen_log10_min_cells=control['methanogen_log10_min_cells']-original['methanogen_log10_min_cells'],
                delta_peak_temperature_k=control['peak_temperature_k']-original['peak_temperature_k'],
                min_below_one_class_same=(min(control['acetogen_log10_min_cells'],control['methanogen_log10_min_cells'])<0)==
                                        (min(original['acetogen_log10_min_cells'],original['methanogen_log10_min_cells'])<0),
                census_endpoint_same=control.get('census_endpoint')==original.get('census_endpoint'),
                main_census_events=original.get('census_events'),control_census_events=control.get('census_events'),
                control_uncensored_raw=control['uncensored_raw'],control_uncensored_sha256=control['uncensored_sha256'],
                control_census_raw=control.get('census_raw'),control_census_sha256=control.get('census_sha256'),
                maximum_accepted_source_log=result['uncensored_metadata']['maximum_accepted_source_log'],
                maximum_interval_source_bound=result['uncensored_metadata']['maximum_interval_source_bound'],
                rejected_trial_source_extensions=result['uncensored_metadata']['rejected_trial_source_extensions']))
            print(c.case_id,'refinement complete',flush=True)
    tables.write_csv(output/'transient_refinement_controls.csv',rows)
    return rows


def archive_manifest(output):
    main=json.loads((output/'transient_manifest.json').read_text())
    controls=[]
    control_path=output/'transient_refinement_controls.csv'
    if control_path.exists():
        import csv
        controls=list(csv.DictReader(control_path.open()))
    receipt_paths=[Path(r['uncensored_raw']).with_suffix('.json') for r in main['rows']]
    receipt_paths += [Path(r['control_uncensored_raw']).with_suffix('.json') for r in controls]
    entries={};receipts=[]
    def include(path,role):
        path=Path(path);data=(ROOT/path).read_bytes();digest=sha256(data).hexdigest()
        entries[str(path)]=dict(path=str(path),sha256=digest,bytes=len(data),role=role)
        return digest
    for path in receipt_paths:
        include(path,'raw_receipt');receipt=json.loads((ROOT/path).read_text())
        protocol=receipt['protocol'];row=receipt['row']
        epoch=Path('local/haze/dynamic_transients/source_epochs')/sha256(json.dumps(protocol['source_sha256'],sort_keys=True).encode()).hexdigest()[:20]
        for name,digest in protocol['source_sha256'].items():
            if include(epoch/name,'producer_epoch')!=digest:raise ArithmeticError('Archived producer epoch differs')
        for name in ('uncensored','census'):
            rawpath=row.get(name+'_raw')
            if rawpath and include(rawpath,name+'_trajectory')!=row[name+'_sha256']:raise ArithmeticError('Raw hash differs')
        receipts.append(dict(case_id=row['case_id'],receipt=str(path),source_epoch=str(epoch),
            producer_sha256=protocol['source_sha256']['src/terra_prisca/haze_world/dynamic_transients.py'],
            rtol=protocol['rtol'],max_step_yr=protocol['max_step'],sample_step_yr=protocol['sample_step']))
    public=[]
    for path in sorted(output.glob('transient*'))+ [output/'oscillations.csv',output/'invasions.csv']:
        if path.is_file() and path.name!='transient_archive_manifest.json':
            data=path.read_bytes();public.append(dict(path=str(path.relative_to(ROOT)),sha256=sha256(data).hexdigest(),bytes=len(data)))
    value=dict(scope='Canonical29-case main epoch plus four tighter controls only; failed preliminary epochs remain retained but are not canonical evidence.',
        receipts=receipts,canonical_raw=list(entries.values()),canonical_bytes=sum(r['bytes'] for r in entries.values()),public_files=public,
        archive_publication_status='Prepared local evidence index; not deposited or released')
    (output/'transient_archive_manifest.json').write_text(json.dumps(value,indent=2)+'\n')
    return value


def refinement_survival(output):
    import csv
    path=output/'transient_refinement_controls.csv'
    if not path.exists():return []
    primary=json.loads((output/'transient_assessment.json').read_text())['primary_rows']
    rows=[]
    for control in csv.DictReader(path.open()):
        receipt=json.loads((ROOT/Path(control['control_uncensored_raw']).with_suffix('.json')).read_text())
        for r in assess_receipt(receipt):
            main=next(m for m in primary if m['case_id']==r['case_id'] and m['guild']==r['guild'])
            rows.append(dict(case_id=r['case_id'],guild=r['guild'],
                main_status=main['assembly_status'],control_status=r['assembly_status'],
                main_log_survival_probability=main.get('log_survival_probability'),
                control_log_survival_probability=r.get('log_survival_probability'),
                main_start_yr=main.get('start_yr'),control_start_yr=r.get('start_yr'),
                main_end_yr=main.get('end_yr'),control_end_yr=r.get('end_yr'),
                main_log_threshold=main.get('log_threshold'),control_log_threshold=r.get('log_threshold'),
                main_survival_probability=main.get('survival_probability'),control_survival_probability=r.get('survival_probability')))
    tables.write_csv(output/'transient_refinement_first_survival.csv',rows)
    return rows


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'models/haze_world/figures/dynamic_realisation')
    parser.add_argument('--raw',type=Path,default=ROOT/'local/haze/dynamic_transients')
    parser.add_argument('--refine',action='store_true')
    args=parser.parse_args();result=run(args.output,args.raw)
    if args.refine:refinements(args.output,args.raw)
    refinement_survival(args.output)
    archive_manifest(args.output)
    print('Scored',len(result['primary_rows']),'first-episode diagnostics')


if __name__=='__main__':main()
