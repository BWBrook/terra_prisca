"""Refine the first 30-year lag-margin crossing on each frozen dial branch."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import shutil

import numpy as np

from . import graded_dials as runs


def lag_value(row):
    if row['lag']['status']=='finite_crossing':return row['lag']['tau_c']
    if row['lag']['status']=='not_detected_through_10000':return np.inf
    return None


def refine(rows,cache,stamp,target=30.):
    candidates=[(a,b) for a,b in zip(rows[:-1],rows[1:])
                if lag_value(a) is not None and lag_value(b) is not None and lag_value(a)<target<=lag_value(b)]
    if not candidates:return dict(branch_id=rows[0]['branch_id'],status='no_qualified_bracket'),[]
    lo,hi=candidates[0]
    initial=dict(low_dial=lo['dial'],high_dial=hi['dial'],low_tau=lag_value(lo),
                 high_tau=None if not np.isfinite(lag_value(hi)) else lag_value(hi),
                 high_status=hi['lag']['status'])
    interpolated=None
    if np.isfinite(lag_value(hi)):
        fraction=(target-lag_value(lo))/(lag_value(hi)-lag_value(lo))
        interpolated=abs(lo['Sc'])+fraction*(abs(hi['Sc'])-abs(lo['Sc']))
    evaluations=[];qualified=False
    for iteration in range(24):
        dial=(lo['dial']+hi['dial'])/2 if lo['dial']==0 else float(np.sqrt(lo['dial']*hi['dial']))
        path=cache/f'{lo["branch_id"]}-{dial:.16g}-{stamp}.json'
        if path.exists():value=json.loads(path.read_text())
        else:
            value=(runs.d1_point(dial,lo['fraction'],lo,kind='threshold_refinement') if lo['stage']=='D1' else
                   runs.d2_point(dial,lo['dispersal_yr'],lo,kind='threshold_refinement'))
            value=runs.numerical.clean(value);path.write_text(json.dumps(value,allow_nan=False)+'\n')
        evaluations.append(value)
        print(lo['branch_id'],'threshold iteration',iteration,'dial',dial,'status',value['status'],
              'tau',value.get('lag',{}).get('tau_c'),flush=True)
        if value['status'] not in ('accepted','converged') or lag_value(value) is None:break
        if lag_value(value)<target:lo=value
        else:hi=value
        price_error=abs(hi['Sc']-lo['Sc'])
        finite=bool(np.isfinite(lag_value(hi)))
        if price_error<=max(.001,.02*abs(hi['Sc'])) and finite and lag_value(hi)-lag_value(lo)<=.02*target:
            qualified=True;break
    price_bounds=sorted([abs(lo['Sc']),abs(hi['Sc'])])
    answer=dict(branch_id=lo['branch_id'],stage=lo['stage'],status='qualified_bracket' if qualified else 'refinement_unresolved',
        initial=initial,initial_finite_interpolated_price=interpolated,
        low_dial=lo['dial'],high_dial=hi['dial'],low_tau=lag_value(lo),
        high_tau=lag_value(hi) if np.isfinite(lag_value(hi)) else None,
        high_status=hi['lag']['status'],price_low=price_bounds[0],price_high=price_bounds[1],
        price_midpoint=float(np.mean(price_bounds)),evaluations=len(evaluations),
        limitation='No interpolation treats a right-censoring bound as a finite margin.')
    return answer,evaluations


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=runs.OUTPUT/'states.json')
    parser.add_argument('--output',type=Path,default=runs.OUTPUT/'threshold_refinement')
    parser.add_argument('--cache',type=Path,default=runs.ROOT/'local/haze/graded_thresholds')
    args=parser.parse_args();args.cache.mkdir(parents=True,exist_ok=True)
    hashes=runs.sources();hashes[str(Path(__file__).relative_to(runs.ROOT))]=runs.numerical.digest(Path(__file__))
    hashes[str(args.input.relative_to(runs.ROOT))]=runs.numerical.digest(args.input)
    stamp=sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()[:20]
    epoch=args.cache/'source_epochs'/stamp
    for name,digest in hashes.items():
        target=epoch/name;target.parent.mkdir(parents=True,exist_ok=True)
        if runs.numerical.digest(runs.ROOT/name)!=digest:raise ArithmeticError('Refinement input changed')
        shutil.copyfile(runs.ROOT/name,target)
    records=json.loads(args.input.read_text());answers=[];extra=[]
    for branch in sorted({r['branch_id'] for r in records}):
        rows=sorted([r for r in records if r['branch_id']==branch],key=lambda r:r['dial'])
        answer,evaluations=refine(rows,args.cache,stamp);answers.append(answer);extra.extend(evaluations)
    if any(runs.numerical.digest(runs.ROOT/name)!=digest for name,digest in hashes.items()):raise ArithmeticError('Refinement source changed')
    runs.write(args.output,extra,hashes)
    summary=dict(branches=answers,source_sha256=hashes,source_epoch=stamp,
                 threshold_states_sha256=runs.numerical.digest(args.output/'states.json'))
    (args.output/'thresholds.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps(answers,indent=2),flush=True)


if __name__=='__main__':main()
