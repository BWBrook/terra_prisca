"""Assess the fixed graded-dial predictions without redefining their thresholds."""

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from . import graded_dials as runs


def finite(row):return row.get('lag',{}).get('status')=='finite_crossing'


def export_frozen(output,records,cache):
    manifest=json.loads((output/'manifest.json').read_text())
    stamp=runs.sha256(json.dumps(manifest['source_sha256'],sort_keys=True).encode()).hexdigest()[:20]
    originals={};input_hashes={}
    for stage,value in runs.BRANCHES:
        path=cache/f'{stage}-{value:g}-{stamp}.json'
        input_hashes[str(path.relative_to(runs.ROOT))]=runs.numerical.digest(path)
        for row in json.loads(path.read_text()):originals[(row['branch_id'],row['dial'])]=row
    rows=[]
    for row in records:
        old=originals[(row['branch_id'],row['dial'])]
        if row['Sc']!=old['Sc'] or row['S0']!=old['S0'] or not np.array_equal(row['y'],old['y']):
            raise ArithmeticError('Frozen cache no longer matches the published state')
        lead=old['gain'].get('frozen_leading_real')
        rows.append(dict(branch_id=row['branch_id'],dial=row['dial'],Sc=row['Sc'],S0=row['S0'],
            G_loc=row['G_loc'],frozen_leading_real_yr=lead,
            frozen_status='stable' if lead is not None and lead < -1e-9 else 'unstable_or_neutral' if lead is not None else 'unresolved',
            Sc_schur_condition=old['gain'].get('Sc_schur_condition'),S0_schur_condition=old['gain'].get('S0_schur_condition')))
    runs.numerical.b1.write_csv(output/'frozen_counterfactuals.csv',rows)
    return rows,input_hashes


def assess(records,thresholds,qualification,refinements=()):
    repaired={(r['branch_id'],float(r['dial'])) for r in qualification.get('records',[])
              if r['status']=='qualified_by_two_steps'}
    raw_checks=[]
    for row in records:
        original=row.get('supply_check_status')
        raw_checks.append(dict(branch_id=row['branch_id'],dial=row['dial'],original_status=original,
            effective_status='passed' if original=='passed' or (row['branch_id'],row['dial']) in repaired else 'unresolved'))
    adjacent=[];censored=[];fits=[]
    for branch in sorted({r['branch_id'] for r in records}):
        rows=sorted([r for r in records if r['branch_id']==branch],key=lambda r:r['dial'])
        for a,b in zip(rows[:-1],rows[1:]):
            if finite(a) and finite(b):
                ratio=b['lag']['tau_c']/a['lag']['tau_c']
                adjacent.append(dict(branch_id=branch,low_dial=a['dial'],high_dial=b['dial'],
                    ratio=ratio,nondecreasing=ratio>=.98,within_factor_ten=.1<ratio<10))
            elif finite(a) and b['lag']['status']=='not_detected_through_10000':
                censored.append(dict(branch_id=branch,low_dial=a['dial'],high_dial=b['dial'],
                    lower_ratio_bound=1e4/a['lag']['tau_c'],
                    scope='First censored transition excluded from finite-pair criterion; not evidence of a mathematical discontinuity.'))
        chosen=[r for r in rows if finite(r) and 2<r['lag']['tau_c']<1e3 and abs(r['Sc'])>0]
        if len(chosen)>=2:
            x=np.log([abs(r['Sc']) for r in chosen]);y=np.log([r['lag']['tau_c'] for r in chosen])
            slope,intercept=np.polyfit(x,y,1);residual=y-(slope*x+intercept)
            total=float(np.sum((y-y.mean())**2));sse=float(residual@residual)
            fits.append(dict(branch_id=branch,n=len(chosen),slope=float(slope),intercept=float(intercept),
                r_squared=1-sse/total if total else None,residuals=residual.tolist(),
                slope_in_band=bool(1<=slope<=2.5),
                linearity_status='two_point_identity_unassessed' if len(chosen)==2 else 'descriptive_no_prespecified_tolerance'))
        else:fits.append(dict(branch_id=branch,n=len(chosen),slope=None,slope_in_band=None,linearity_status='too_few_points'))
    prices=[]
    for r in thresholds.get('branches',[]):
        qualified=r['status']=='qualified_bracket'
        status=('within_predicted_band' if r['price_low']>=.05 and r['price_high']<=.5 else
                'outside_predicted_band' if r['price_high']<.05 or r['price_low']>.5 else 'boundary_unresolved') if qualified else 'unresolved'
        prices.append(dict(r,price_status=status))
    formula=[];refined_formula=[];outside=[]
    for row in list(records)+list(refinements):
        ratio=row.get('weak_mode_ratio')
        common=dict(branch_id=row['branch_id'],dial=row['dial'],kind=row['kind'],
                    computed_tau=row['lag']['tau_c'],estimated_tau=row.get('weak_mode_tau_yr'),ratio=ratio)
        if finite(row) and row['lag']['tau_c']<100:
            selected=refined_formula if row['kind']=='threshold_refinement' else formula
            selected.append(dict(common,passed=ratio is not None and .5<=ratio<=2))
        elif row.get('weak_mode_tau_yr') is not None:outside.append(common)
    return dict(
        counts=dict(prescribed=sum(r['kind']=='prescribed' for r in records),baseline_controls=sum(r['kind']=='baseline' for r in records),
                    raw_finite_input_qualified=sum(r['effective_status']=='passed' for r in raw_checks)),
        raw_supply_checks=raw_checks,
        PD1=dict(status='sampled_finite_criteria_supported' if adjacent and all(r['nondecreasing'] and r['within_factor_ten'] for r in adjacent) else 'refuted_or_unassessed',
                 finite_adjacent=adjacent,censored_transitions=censored,
                 continuity_limit='Finite spacing does not prove continuity or a jump. Local regularity and simple-Hopf checks are reported independently.'),
        PD2=dict(status='refuted_slope_clause' if any(r['slope_in_band'] is False for r in fits) else 'slope_band_not_refuted_linearity_unassessed',
                 branches=fits,limitation='No post-hoc R-squared cutoff; a two-point fit cannot test linearity.'),
        PD3=dict(status='supported_in_all_refined_brackets' if len(prices)==4 and all(r['price_status']=='within_predicted_band' for r in prices) else 'refuted' if any(r['price_status']=='outside_predicted_band' for r in prices) else 'unresolved',branches=prices),
        PD4=dict(status='refuted_by_authorised_refinement' if any(not r['passed'] for r in refined_formula) else
                 'supported_on_eligible_points' if formula and all(r['passed'] for r in formula) else 'refuted_or_unassessed',
                 prescribed_count=sum(r['kind']=='prescribed' for r in formula),baseline_count=sum(r['kind']=='baseline' for r in formula),
                 comparisons=formula,refinement_comparisons=refined_formula,outside_prediction_domain=outside,
                 limitation='Conditional on computed tau below100yr; not a general formula for censored or overdamped states.'))


def plot(output,records,refinements=()):
    fig,axes=plt.subplots(1,2,figsize=(10.5,4.4),layout='constrained')
    colours=('#156e91','#38a1b8','#b45d28','#d8a43b')
    branches=sorted({r['branch_id'] for r in records})
    for branch,colour in zip(branches,colours):
        rows=sorted([r for r in records if r['branch_id']==branch],key=lambda r:r['dial'])
        points=[r for r in rows if finite(r)]
        axes[0].plot([abs(r['Sc']) for r in points],[r['lag']['tau_c'] for r in points],'o-',ms=4,color=colour,label=branch)
        censored=[r for r in rows if r['lag']['status']=='not_detected_through_10000']
        axes[0].scatter([abs(r['Sc']) for r in censored],[1e4]*len(censored),marker='^',color=colour,s=35)
        for row in rows:
            estimate=row.get('weak_mode_tau_yr')
            if estimate is None:continue
            x=row['lag']['tau_c'] if finite(row) else 1e4
            marker='o' if finite(row) else '>'
            fill=colour if finite(row) and x<100 else 'none'
            axes[1].scatter(x,estimate,marker=marker,s=25,facecolors=fill,edgecolors=colour,zorder=3)
    for row in refinements:
        if finite(row) and row['lag']['tau_c']<100 and row.get('weak_mode_tau_yr') is not None:
            axes[1].scatter(row['lag']['tau_c'],row['weak_mode_tau_yr'],marker='x',s=22,color='.25',zorder=4)
    axes[0].set(xscale='symlog',yscale='log',xlabel='Residual |Sc| (K per e-fold of supply)',
        ylabel='First thermal delay margin (years)',title='Gradual departure from exact pinning')
    axes[0].set_xscale('symlog',linthresh=1e-4);axes[0].set_xlim(left=0)
    axes[0].axhline(30,color='.4',ls='--',lw=.8)
    axes[0].legend(fontsize=8);axes[0].text(.02,.98,'Triangles: no crossing through 10,000 years',
        transform=axes[0].transAxes,va='top',fontsize=7.5)
    x=np.geomspace(.1,1e4,100)
    axes[1].fill_between(x,x/2,x*2,color='.9',zorder=0);axes[1].plot(x,x,color='.5',lw=.8,zorder=1)
    axes[1].set(xscale='log',yscale='log',xlabel='Computed margin (years; arrows are bounds)',
        ylabel='Weak-mode estimate (years)',title='Weak-mode estimate and finite-margin controls')
    axes[1].text(.02,.98,'Filled: prescribed margin <100 years\nOpen: outside prediction domain; crosses: refinement',
        transform=axes[1].transAxes,va='top',fontsize=8)
    for ax in axes:ax.grid(alpha=.15)
    fig.savefig(output/'graded_response.png',dpi=180);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=runs.OUTPUT)
    parser.add_argument('--qualification',type=Path,default=runs.ROOT/'docs/audits/graded-dial-numerics-2026-11-12.json')
    parser.add_argument('--cache',type=Path,default=runs.ROOT/'local/haze/graded_dials')
    args=parser.parse_args();out=args.output
    state=out/'states.json';threshold=out/'threshold_refinement/thresholds.json'
    qualification=json.loads(args.qualification.read_text())
    for field in ('source_sha256','input_sha256'):
        for name,digest in qualification.get(field,{}).items():
            if runs.numerical.digest(runs.ROOT/name)!=digest:raise ArithmeticError('Qualification source/input changed: '+name)
    records=json.loads(state.read_text())
    refinement_path=threshold.with_name('states.json')
    refinements=json.loads(refinement_path.read_text())
    expected={(f'D1_f{f:g}',k) for f in (0.,.5) for k in runs.KAPPAS}
    expected|={(f'D2_d{d:g}',s) for d in (1e-4,1e-3) for s in (0.,)+runs.SIGMAS}
    identities=[(r['branch_id'],r['dial']) for r in records]
    if len(identities)!=len(expected) or set(identities)!=expected:raise ArithmeticError('Missing or duplicated prescribed dial/control')
    result=assess(records,json.loads(threshold.read_text()),qualification,refinements)
    frozen,cache_hashes=export_frozen(out,records,args.cache)
    result['frozen_counterfactuals']=dict(stable=sum(r['frozen_status']=='stable' for r in frozen),
        total=len(frozen),table_sha256=runs.numerical.digest(out/'frozen_counterfactuals.csv'),cache_sha256=cache_hashes)
    plot(out,records,refinements)
    result['source_sha256']={str(Path(__file__).relative_to(runs.ROOT)):runs.numerical.digest(Path(__file__))}
    result['input_sha256']={str(p.relative_to(runs.ROOT)):runs.numerical.digest(p) for p in (state,threshold,refinement_path,args.qualification)}
    result['figure_sha256']=runs.numerical.digest(out/'graded_response.png')
    (out/'prediction_assessment.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v['status'] for k,v in result.items() if k.startswith('PD')},indent=2))


if __name__=='__main__':main()
