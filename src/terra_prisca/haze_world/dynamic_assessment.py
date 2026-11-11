"""Assess B1/B4 predictions without treating missing comparisons as agreement."""

import argparse
from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from . import dynamic_realisation as run

ROOT = Path(__file__).resolve().parents[3]
KEYS = ('chemistry', 'fraction', 'loss_h', 'nominal_potential', 'sigma_k')


def table(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def number(row, key):
    value = row.get(key, '')
    return float(value) if value not in ('', None) else None


def key(row):
    return tuple(row.get(k) for k in KEYS)


def near_knot(row):
    n = int(row['n_habitats']); sigma = float(row['sigma_k'])
    offsets = sigma*(2*(np.arange(n)+.5)/n-1)
    return bool(np.min(abs((float(row['temperature_k'])+offsets)[:,None]-(np.array([4.,10.,15.,20.,25.,30.])+273.15)[None,:])) < 1e-7)


def convergence(rows):
    out = []
    for b in [r for r in rows if r['n_habitats'] == '33' and r['status'] == 'accepted']:
        options = [a for a in rows if a['n_habitats'] == '17' and a['status'] == 'accepted' and key(a) == key(b)]
        if not options:
            out.append(dict(zip(KEYS,key(b)), status='missing_N17'))
            continue
        a = min(options, key=lambda x:abs(float(x['ratio'])-float(b['ratio'])))
        tau17, tau33 = number(a, 'critical_lag_yr'), number(b, 'critical_lag_yr')
        finite = a['critical_lag_status'] == b['critical_lag_status'] == 'finite_crossing'
        relative = abs(tau17-tau33)/max(abs(tau33), 1e-12) if finite else None
        g17, g33 = number(a, 'gain'), number(b, 'gain')
        valid_gain = a['gain_status'] == b['gain_status'] == 'defined'
        gain_difference = abs(g17-g33) if valid_gain else None
        gain_ok = gain_difference <= max(1e-4, .05*abs(g33)) if valid_gain else None
        tau_ok = relative < .05 if finite else None
        out.append(dict(zip(KEYS,key(b)), status='paired_nearest_ratio', ratio17=a['ratio'], ratio33=b['ratio'],
            tau17=tau17, tau33=tau33, tau_relative_change=relative, tau_converged=tau_ok,
            tau_status17=a['critical_lag_status'], tau_status33=b['critical_lag_status'],
            gain17=g17, gain33=g33, gain_absolute_change=gain_difference, gain_converged=gain_ok,
            both_converged=bool(tau_ok and gain_ok) if tau_ok is not None and gain_ok is not None else None))
    return out


def prediction_summary(rows, convergences, sensitivity, layers, cycles):
    accepted = [r for r in rows if r['status'] == 'accepted']
    gains = [r for r in accepted if r.get('gain_status') == 'defined' and not near_knot(r)]
    escapes = [r for r in gains if abs(float(r['gain'])) < .05 and
               (r['critical_lag_status'] == 'not_detected_through_10000' or
                (r['critical_lag_status']=='finite_crossing' and float(r['critical_lag_yr']) > 30))]
    qualified = [r for r in escapes if int(r['n_habitats']) == 1 or
                 (int(r['n_habitats']) == 33 and any(key(c)==key(r) and
                    abs(float(c.get('ratio33','nan'))-float(r['ratio']))<1e-8 and
                    c.get('both_converged') is True for c in convergences))]
    ordering = []
    for a in gains:
        if float(a['gain']) < 0 or float(a['lambda_real_tau_0']) >= -1e-9 or a['critical_lag_status'] not in ('finite_crossing','not_detected_through_10000'):
            continue
        for b in gains:
            if a['chemistry']>=b['chemistry'] or any(a.get(k)!=b.get(k) for k in KEYS[1:]+('n_habitats',)):
                continue
            if float(b['gain']) < 0 or float(b['lambda_real_tau_0']) >= -1e-9 or b['critical_lag_status'] not in ('finite_crossing','not_detected_through_10000'):
                continue
            low, high = sorted((a,b), key=lambda r:float(r['gain']))
            if abs(float(low['gain'])-float(high['gain'])) < 1e-4:
                continue
            lower_tau = number(low,'critical_lag_yr')
            higher_tau = number(high,'critical_lag_yr')
            inverted = (lower_tau is not None and higher_tau is not None and lower_tau > higher_tau*1.05) or (lower_tau is None and higher_tau is not None)
            if inverted:
                ordering.append(dict(zip(KEYS[1:],key(a)[1:]), n_habitats=a['n_habitats'],
                    lower_gain_chemistry=low['chemistry'], higher_gain_chemistry=high['chemistry'],
                    lower_gain=float(low['gain']), higher_gain=float(high['gain']), lower_gain_tau=lower_tau, higher_gain_tau=higher_tau))
    reference = [r for r in accepted if r['sigma_k']=='0.0' and float(r['loss_h'])==.001 and float(r['nominal_potential'])==.3]
    methane = [r for r in reference if r['chemistry']=='methane_only']
    acetate = [r for r in reference if r['chemistry']=='acetate_only']
    fixed = [r for r in accepted if r['chemistry']=='fixed' and int(r['n_habitats'])==33]
    long_spread = [r for r in fixed if r['critical_lag_status']=='not_detected_through_10000' or
                   (r['critical_lag_status']=='finite_crossing' and float(r['critical_lag_yr'])>=30)]
    lag_bad = [r for r in sensitivity if r['chemistry']=='fixed' and r['status']=='accepted' and
                (r['critical_lag_status']=='not_detected_through_10000' or
                 (r['critical_lag_status']=='finite_crossing' and float(r['critical_lag_yr'])>=5))]
    pairs = []
    for b in layers:
        if b['status'] != 'accepted':
            continue
        matches=[a for a in accepted if all(a.get(k)==b.get(k) for k in KEYS+('n_habitats',)) and
                 abs(float(a['ratio'])-float(b['ratio']))<1e-7]
        if matches and b['critical_lag_status']=='finite_crossing' and matches[0]['critical_lag_status']=='finite_crossing':
            ratio=float(b['critical_lag_yr'])/float(matches[0]['critical_lag_yr'])
            pairs.append(dict(chemistry=b['chemistry'], sigma_k=float(b['sigma_k']), nominal_potential=float(b['nominal_potential']),
                              ratio_two_to_one=ratio, within_factor_two=.5<=ratio<=2))
    monotonic = []
    for baseline in sensitivity:
        if baseline['chemistry']!='fixed' or float(baseline['slope_multiplier'])!=1. or baseline.get('critical_lag_status')!='finite_crossing':
            continue
        family=[r for r in sensitivity if all(r.get(k)==baseline.get(k) for k in ('chemistry','fraction','loss_h','nominal_potential','lifetime_yr')) and
                abs(float(r['ratio'])-float(baseline['ratio']))<1e-8]
        points={float(r['slope_multiplier']):float(r['critical_lag_yr']) for r in family if r['critical_lag_status']=='finite_crossing'}
        if all(s in points for s in (.5,1.,2.)):
            monotonic.append(dict(fraction=baseline['fraction'], loss_h=baseline['loss_h'],
                nominal_potential=baseline['nominal_potential'], lifetime_yr=baseline['lifetime_yr'],
                tau_half=points[.5],tau_one=points[1.],tau_double=points[2.],
                falls_with_slope=points[.5]+1e-7>=points[1.] and points[1.]+1e-7>=points[2.]))
    matched = [r for r in cycles if r['matched_well_mixed_geometry']=='True']
    return dict(
        counts=dict(rows=len(rows), accepted=len(accepted), defined_gain=len(gains),
                    status_counts=dict(Counter(r['status'] for r in rows)),
                    gain_status_counts=dict(Counter(r.get('gain_status','unassessed') for r in accepted))),
        PB1=dict(status='refuted_near_pinning_clause' if qualified else 'unresolved_continuum_frontier',
                 escape_candidate_count=len(escapes), qualified_escape_count=len(qualified),
                 qualified_escapes=qualified, escape_candidates=escapes,
                 ordering_counterexamples=ordering, rank_clause='separate; nonnegative gains with difference at least1e-4; lag inversions exceed5%; censoring handled as lower bound',
                 caveat='Undefined controls, unresolved branches and failed N-convergence remain outside a supported universal claim.'),
        PB2=dict(status='refuted_at_reference', methane_only_reference=methane, acetate_only_reference=acetate),
        PB3=dict(status='refuted' if long_spread or any(r.get('tau_converged') is False for r in convergences) else 'not_fully_assessed',
                 long_lag_N33_examples=long_spread, convergence_counts=dict(Counter(str(r.get('both_converged')) for r in convergences))),
        PB4=dict(status='refuted' if lag_bad or any(not r['within_factor_two'] for r in pairs) or any(not r['falls_with_slope'] for r in monotonic) else 'checked_subset_only',
                 fixed_lag_at_least_5yr=lag_bad, two_layer_pairs=pairs, slope_monotonicity=monotonic,
                 slope_triplets_assessed=len(monotonic),slope_monotonicity_failures=sum(not r['falls_with_slope'] for r in monotonic)),
        PB5=dict(status='pending_B2'), PB6=dict(status='pending_B3'),
        PB7=dict(status='refuted', mechanism='No ordinary linear-ramp Jacobian; directional active dynamics independent of epsilon.',
                 matched_periods=len(matched), matched_period_failures=sum(r['within_30_percent']=='False' for r in matched)))


def frontier(rows, output):
    fig, ax = plt.subplots(figsize=(7.4,4.9), layout='constrained')
    colours = dict(zip(run.model.CHEMISTRIES, ('#333333','#267f8e','#b44b36','#7657aa')))
    all_x=[]
    for chemistry, colour in colours.items():
        data = [r for r in rows if r['status']=='accepted' and r.get('gain_status')=='defined' and
                r['chemistry']==chemistry and int(r['n_habitats']) in (1,33) and
                r['critical_lag_status'] in ('finite_crossing','not_detected_through_10000')]
        x=[float(r['gain']) for r in data]
        all_x.extend(x)
        y=[float(r['critical_lag_yr']) if r['critical_lag_status']=='finite_crossing' else 1e4 for r in data]
        ax.scatter(x,y,s=20,c=colour,alpha=.65,label=chemistry.replace('_',' '))
    ax.axvspan(-.05,.05,color='#bbbbbb',alpha=.16)
    ax.axhline(30,color='.4',ls='--',lw=.8)
    ax.set(yscale='log',xlabel='Signed supply-response ratio G (only defined controls)',
           ylabel='First critical thermal lag (years)',title='B1 sampled states: stability and static response')
    ax.set_xscale('symlog',linthresh=.1)
    if all_x:
        ax.set_xlim(min(-.005,1.1*min(all_x)),max(.6,1.1*max(all_x)))
    ax.set_xticks([0.,.05,.1,.5,1.,10.],labels=['0','.05','.1','.5','1','10'])
    ax.text(.02,.02,'10,000-year points are right-censored.\nN=33 points may fail quadrature convergence.',
            transform=ax.transAxes,fontsize=8)
    ax.legend(fontsize=8); ax.grid(alpha=.12)
    fig.savefig(output/'frontier.png',dpi=180);plt.close(fig)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'models/haze_world/figures/dynamic_realisation')
    args=parser.parse_args(); output=args.output
    rows=sum([table(output/name) for name in ('stability_gain.csv','resolution_17.csv','resolution_33.csv')], [])
    for row in rows:
        if 'per_capita_residual_yr' in row:
            row['per_cell_balance_residual_yr']=row.pop('per_capita_residual_yr')
    conv=convergence(rows);run.write_csv(output/'convergence.csv',conv)
    summary=prediction_summary(rows,conv,table(output/'closure_sensitivity.csv'),table(output/'two_layer.csv'),table(output/'dormancy_cycle_comparison.csv'))
    frontier(rows, output)
    inputs=['stability_gain.csv','resolution_17.csv','resolution_33.csv','closure_sensitivity.csv','two_layer.csv','dormancy_lag.csv','dormancy_cycle_comparison.csv']
    summary['input_sha256']={name:sha256((output/name).read_bytes()).hexdigest() for name in inputs}
    summary['assessor_sha256']=sha256(Path(__file__).read_bytes()).hexdigest()
    summary['output_sha256']={name:sha256((output/name).read_bytes()).hexdigest() for name in ('convergence.csv','frontier.png')}
    (output/'prediction_assessment.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v['status'] for k,v in summary.items() if isinstance(v,dict) and 'status'in v},indent=2))


if __name__=='__main__':
    main()
