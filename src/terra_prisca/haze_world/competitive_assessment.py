"""Score the fixed KE predictions and draw compact scientific response figures."""
import csv
from hashlib import sha256
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter
import numpy as np
from . import competitive_evolution as model

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'models/haze_world/figures/competitive_evolution'


def table(name):
    with (OUT/name).open() as f:return list(csv.DictReader(f))


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    maps=table('best_response.csv');anchors=table('anchors.csv');communities=table('communities.csv')
    mutants=table('invasions.csv');paths=table('paths.csv');singles=table('adapted_single.csv')
    mixed=[r for r in communities if r['status']=='joint_community']
    cooling=[r for r in mixed if r['cooling_branch']=='True']
    missing=[r for r in communities if r['status']=='no_feasible_joint_community']
    crossings=[r for r in maps if r['status']=='crossing']
    one=next(r for r in crossings if float(r['loss_h'])==.001 and float(r['energy_ev'])==0 and r['interpolation']=='linear_shape')
    selected=[r for r in cooling if float(r['loss_h'])==.001 and float(r['energy_ev'])==0 and r['interpolation']=='linear_shape']
    ke1=abs(float(one['temperature_k'])-277.96)<.5 and {float(r['fraction']) for r in selected}=={0.,.5} and all(r['stable']=='True' for r in selected)
    slopes=[]
    for r in mixed:
        p=model.parameters(float(r['loss_h']),float(r['fraction']))
        traits=model.kinetics.Traits(tuple(json.loads(r['positions_c'])),float(r['energy_ev']),r['interpolation'])
        t=float(r['temperature_k']);h=.001
        high=model.rstars_at_temperature(t+h,p.biology,traits);low=model.rstars_at_temperature(t-h,p.biology,traits)
        slopes.append(float(((high[0]-high[1])-(low[0]-low[1]))/(2*h)))
    low_map=[r for r in maps if float(r['loss_h'])==.0003 and float(r['energy_ev'])<=.2]
    low_m=[r for r in singles if float(r['setting_id'].split('_')[0][1:])==.0003 and r['kind']=='methanogen' and r['stable']=='True']
    constrained=[r for r in crossings if float(r['loss_h'])==.001 and float(r['energy_ev'])>=.45]
    margins=[abs(float(r['temperature_k'])-281.535) for r in constrained]
    controls=[r for r in anchors if float(r['loss_h'])==.001 and float(r['energy_ev'])==0]
    counts={variant:sum(r['status']=='crossing' for r in controls if r['variant']==variant) for variant in sorted({r['variant'] for r in controls})}
    threshold_clause=all(r['status']=='no_crossing' or abs(float(r['nearest_baseline_shift_k']))>2 for r in controls if r['variant']=='thresholds_30c')
    maintenance_clause=all(r['status']=='crossing' and abs(float(r['nearest_baseline_shift_k']))<=2 for r in controls if r['variant']=='maintenance_30c')
    q=[float(r['quality_factor']) for r in cooling]
    convergences=[c for r in cooling for c in json.loads(r['convergence'])]
    comparisons=[]
    for loss in (.001,.003):
        for energy in model.ENERGIES:
            pair=[next(r for r in crossings if float(r['loss_h'])==loss and float(r['energy_ev'])==energy and r['interpolation']==interp) for interp in model.kinetics.INTERPOLATIONS]
            comparisons.append(dict(loss_h=loss,energy_ev=energy,shift_k=abs(float(pair[0]['temperature_k'])-float(pair[1]['temperature_k'])),
                linear_on_branch=pair[0]['on_cooling_branch']=='True',smooth_on_branch=pair[1]['on_cooling_branch']=='True'))
    terminal=[r for r in paths if r['status']!='mixed_branch']
    paired=[]
    for setting in sorted({r['setting_id'] for r in terminal}):
        rows=sorted([r for r in terminal if r['setting_id']==setting],key=lambda r:float(r['max_trait_step_c']))
        assert len(rows)==2
        paired.append(dict(setting_id=setting,statuses=[r['status'] for r in rows],
            temperature_difference_k=abs(float(rows[0]['temperature_k'])-float(rows[1]['temperature_k'])),
            trait_difference_c=float(max(abs(np.array(json.loads(rows[0]['positions_c']))-np.array(json.loads(rows[1]['positions_c'])))))))
    predictions={
        'KE1':dict(status='supported' if ke1 else 'refuted',linear_reference_temperature_k=float(one['temperature_k']),feasible_reference_communities=len(selected)),
        'KE2':dict(status='supported' if all(r['orientation']=='acetogen_cold' for r in crossings) and min(slopes)>0 else 'refuted',detected_crossings=len(crossings),minimum_joint_frozen_trait_slope_pa_k=min(slopes),scope='Detected crossings within the searched domain, not an interval proof'),
        'KE3':dict(status='qualified_support' if all(r['status']=='no_crossing' for r in low_map) and low_m else 'refuted',no_crossing_low_energy=all(r['status']=='no_crossing' for r in low_map),stable_low_loss_methanogen_endpoints=len(low_m),
            endpoint_temperatures_k=sorted({float(r['temperature_k']) for r in low_m}),climate_domains=sorted({r['climate_domain'] for r in low_m}),
            qualification="No numerical tolerance for 'near273.5K' was prescribed. Actual endpoint274.002K is on the imposed high-methane plateau; S5 does not prove arrival there."),
        'KE4':dict(status='supported' if max(margins)<2.5 else 'refuted',maximum_reference_shift_k=max(margins)),
        'KE5':dict(status='supported' if threshold_clause and maintenance_clause else 'refuted',reference_control_crossing_counts=counts,threshold_clause=threshold_clause,maintenance_clause=maintenance_clause,
            mechanism='At30C freezes both threshold and maintenance level/slope; both individually remove the crossing. The matched-level diagnostic is separate.'),
        'KE6':dict(status='supported' if all(r['stable']=='True' for r in cooling) and all(c['convergence']=='attracting' for c in convergences) and min(q)>10 else 'refuted',
            stable_cooling_communities=len(cooling),convergence_checks=len(convergences),quality_factor_range=[min(q),max(q)],
            scope='Smooth canonical matrices where defined; one-sided/projected attraction at nodes. Other greenhouse roots are not adiabatic convergence states.'),
        'KE7':dict(status='supported' if max(r['shift_k'] for r in comparisons)<2 else 'refuted',maximum_interpolation_shift_k=max(r['shift_k'] for r in comparisons),
            comparisons=comparisons,qualification='A small shift can change feasibility at the climate peak.')}
    result=dict(static_settings=len({(r['loss_h'],r['energy_ev'],r['interpolation']) for r in maps}),static_no_crossing=sum(r['status']=='no_crossing' for r in maps),predictions=predictions,settings=len({r['setting_id'] for r in communities}),joint_roots=len(mixed),cooling_joint_roots=len(cooling),
        unstable_greenhouse_roots=sum(r['cooling_branch']=='False' and r['stable']=='False' for r in mixed),missing_settings=len(missing),
        mutant_assays=len(mutants),mutants_per_assay=sorted({int(r['mutants']) for r in mutants}),all_mutant_assays_pass=all(r['passes']=='True' for r in mutants),
        maximum_mutant_growth_h=max(float(r['maximum_mutant_growth_h']) for r in mutants),
        path_terminal_rows=len(terminal),path_pair_comparison=paired,
        maximum_path_terminal_temperature_difference_k=max(r['temperature_difference_k'] for r in paired),
        maximum_path_terminal_trait_difference_c=max(r['trait_difference_c'] for r in paired),
        input_sha256={name:digest(OUT/name) for name in ('best_response.csv','anchors.csv','communities.csv','equilibria.csv','invasions.csv','paths.csv','adapted_single.csv','best_response_manifest.json','communities_manifest.json')},
        assessor_sha256=digest(Path(__file__)),spec_sha256=digest(ROOT/'models/haze_world/competitive-evolution-spec.md'),
        scope='Fixed predictions preserved; KE3 structurally supported with unresolved numerical meaning of near. Finite root/trait searches and uncalibrated canonical branch paths, not evolutionary or geological time forecasts.')
    OUT.joinpath('prediction_assessment.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained',sharey=True)
    for ax,interp in zip(axes,model.kinetics.INTERPOLATIONS):
        for energy in model.ENERGIES:
            points=sorted([r for r in maps if r['interpolation']==interp and float(r['energy_ev'])==energy],key=lambda r:float(r['loss_h']))
            ax.plot([float(r['loss_h']) for r in points],[float(r['temperature_k']) if r['temperature_k'] else np.nan for r in points],'o-',ms=3,label=f'E={energy:g} eV')
        ax.axhspan(273.39,297.008,color='.7',alpha=.15);ax.axhline(297.008,color='.5',lw=.7)
        ax.set(xscale='log',xlim=(.0002,.005),xlabel='Shared cell loss (/hour)',title=interp.replace('_',' '))
        ax.set_xticks([.0002,.0005,.001,.002,.005],labels=['2e−4','5e−4','1e−3','2e−3','5e−3'])
        ax.xaxis.set_minor_formatter(NullFormatter());ax.grid(alpha=.15)
    axes[0].set_ylabel('Best-response crossing (K)');axes[1].legend(fontsize=7,ncol=2)
    fig.savefig(OUT/'crossings.png',dpi=170);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    for interp,style in zip(model.kinetics.INTERPOLATIONS,('o-','s--')):
        rows=sorted([r for r in cooling if float(r['loss_h'])==.001 and float(r['fraction'])==.5 and r['interpolation']==interp],key=lambda r:float(r['energy_ev']))
        axes[0].plot([float(r['energy_ev']) for r in rows],[float(r['temperature_k']) for r in rows],style,label=interp.replace('_',' '))
    axes[0].axhline(281.535,color='.5',ls=':',label='Frozen reference');axes[0].set(xlabel='Arrhenius parameter E (eV)',ylabel='Joint equilibrium temperature (K)');axes[0].legend(fontsize=8)
    for interp,marker in zip(model.kinetics.INTERPOLATIONS,('o','s')):
        rows=[r for r in cooling if r['interpolation']==interp]
        axes[1].scatter([float(r['complex_period_yr']) for r in rows],[float(r['quality_factor']) for r in rows],marker=marker,s=20,label=interp.replace('_',' '))
    axes[1].set(xlabel='Frozen-trait ecological period (yr)',ylabel='Quality factor Q',yscale='log');axes[1].legend(fontsize=8)
    for ax in axes:ax.grid(alpha=.15)
    fig.savefig(OUT/'joint_communities.png',dpi=170);plt.close(fig)
    result['figure_sha256']={name:digest(OUT/name) for name in ('crossings.png','joint_communities.png')}
    OUT.joinpath('prediction_assessment.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v['status'] for k,v in predictions.items()}))


if __name__=='__main__': main()
