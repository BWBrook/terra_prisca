"""Independent algebra and table recounts for synthesis claims C05-C11."""
from collections import Counter
import csv
from dataclasses import replace
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.optimize import brentq

from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world.two_guilds import guilds

ROOT = Path(__file__).resolve().parents[3]
FIG = ROOT/'models/haze_world/figures'
HERE = Path(__file__).parent
INPUTS = {}


def read(path):
    path = Path(path)
    INPUTS[str(path.relative_to(ROOT))] = sha256(path.read_bytes()).hexdigest()
    return list(csv.DictReader(path.open()))


def need(biology, temperature):
    pair = guilds(temperature-273.15, biology)
    pressures = []
    for g in pair:
        required = g.maintenance+biology.loss_h/g.yield_g_mol
        denominator = g.rate_scale-required if g.kinetics == 'saturating' else g.rate_scale
        pressures.append(g.threshold_pa+g.km_pa*required/denominator)
    return pair, np.asarray(pressures)


def numerical_spectrum(y, p, relative_step):
    scales = np.maximum(abs(y), [10., 1e-4, 1e-4, 1e-5, .01])
    columns = []
    for j in range(5):
        delta = np.eye(5)[j]*scales[j]*relative_step
        derivative = (-core.rhs(y+2*delta,p)+8*core.rhs(y+delta,p)
                      -8*core.rhs(y-delta,p)+core.rhs(y-2*delta,p))/(12*relative_step)
        columns.append(derivative/scales)
    matrix = np.column_stack(columns)
    active = [0, *[j+1 for j, enabled in enumerate(p.enabled) if enabled], 3, 4]
    return np.linalg.eigvals(matrix[np.ix_(active,active)])


def crossing(rows, column, target):
    result = []
    for a,b in zip(rows[:-1],rows[1:]):
        u,v = float(a[column])-target,float(b[column])-target
        if u*v < 0:
            weight = -u/(v-u)
            estimate = np.exp((1-weight)*np.log(float(a['dispersal_yr']))+weight*np.log(float(b['dispersal_yr'])))
            result.append(dict(bracket_yr=[float(a['dispersal_yr']),float(b['dispersal_yr'])],interpolated_yr=float(estimate)))
    return result


def main():
    climate = [r for r in read(ROOT/'models/haze_response/arney2016/figure4.csv') if r['case']=='B']
    ratios = np.array([float(r['ch4_co2_ratio']) for r in climate])
    temperatures = np.array([float(r['temperature_k']) for r in climate])
    p = core.reference(.3)
    switches = []
    for kinetics in ('saturating','first_order'):
        biology = replace(p.biology,kinetics=kinetics)
        ts = brentq(lambda t: np.diff(need(biology,t)[1])[0],280.,285.,xtol=1e-11)
        segments = np.flatnonzero((temperatures[:-1] > ts)&(temperatures[1:] < ts))
        assert len(segments)==1
        j = segments[0]
        slope = (temperatures[j+1]-temperatures[j])/(ratios[j+1]-ratios[j])
        rs = ratios[j]+(ts-temperatures[j])/slope
        before = need(biology,ts-.01)[1]
        after = need(biology,ts+.01)[1]
        assert before[0] < before[1] and after[0] > after[1] and slope < 0
        switches.append(dict(kinetics=kinetics,switch_temperature_k=ts,methane_ratio=rs,
                             local_climate_slope_k_per_ratio=slope,pressure_pa=need(biology,ts)[1][0]))
    ts,rs = switches[0]['switch_temperature_k'],switches[0]['methane_ratio']
    pair,pressures = need(p.biology,ts)
    pressure = pressures[0]
    q = np.array([g.maintenance+p.biology.loss_h/g.yield_g_mol for g in pair])
    catabolic = q-p.biology.loss_h*np.array([g.assimilation_mol_g for g in pair])
    capture = core.supply_h2(p)-p.biology.exchange_mol_l_h_pa*(pressure-p.biology.atmosphere_pa)
    delivery = -core.rhs(np.array([pressure,0.,0.,0.,rs]),p)[-1]*4/(core.inventory_to_ratio(p)*core.HOURS_PER_YEAR)
    x = np.linalg.solve(np.array([q,[p.acetate_fraction*catabolic[0],catabolic[1]]]),[capture,delivery])
    krec,kother = core.recycling_rates(ts,p)
    acetate = catabolic[0]*x[0]*core.HOURS_PER_YEAR/(4*(krec+kother))
    mixed = np.r_[pressure,x,acetate,rs]
    spectra = [numerical_spectrum(mixed,p,h) for h in (1e-4,3e-5)]
    assert all(max(v.real)<0 for v in spectra)
    controls = []
    for variant in ('constant_shape','arrhenius_continuation'):
        pp = replace(p,biology=replace(p.biology,low_temperature_variant=variant),enabled=(False,True))
        def state(r):
            t = float(core.temperature_k(r,pp.climate))
            gs,pressures = need(pp.biology,t)
            pm = pressures[1]
            qm = gs[1].maintenance+pp.biology.loss_h/gs[1].yield_g_mol
            biomass = (core.supply_h2(pp)-pp.biology.exchange_mol_l_h_pa*(pm-pp.biology.atmosphere_pa))/qm
            return np.array([pm,0.,biomass,0.,r])
        rm = brentq(lambda r:core.rhs(state(r),pp)[-1],.2,.23,xtol=1e-13)
        ym = state(rm)
        controls.append(dict(variant=variant,temperature_k=float(core.temperature_k(rm,p.climate)),
            contrast_k=ts-float(core.temperature_k(rm,p.climate)),y=ym.tolist(),
            max_real_yr=float(max(numerical_spectrum(ym,pp,1e-4).real))))
    conversion = p.habitat_l_cm2*5.1e18/3e-13
    c06 = dict(mixed_temperature_k=ts,mixed_y=mixed.tolist(),
        maximum_absolute_rhs_by_stock=abs(core.rhs(mixed,p)).tolist(),
        mixed_max_real_yr=[float(max(e.real)) for e in spectra],controls=controls,
        no_special_memory_counterexample=dict(acetogen_cells=float(x[0]*conversion),methanogen_cells=float(x[1]*conversion),
            setting='No refuges, dormancy or external immigration; a stable positive mixed equilibrium is unchanged by the one-cell census. This does not establish joint stochastic permanence.'))
    finite = read(FIG/'finite_populations/attained_endpoints.csv')
    assert len(finite)==144 and all(r['settling_status']=='census_stationary' for r in finite)
    zero = [r for r in finite if float(r['relative_immigration_yr'])==0]
    outcomes = Counter((r['fraction'],r['direction'],r['occupancy']) for r in zero)
    raw = ROOT/'local/haze/finite_populations/final_raw/main_0024_t100000-ce9c0899cdf042d0.json.gz'
    digest = sha256(raw.read_bytes()).hexdigest()
    target = next(r for r in finite if r['base_case_id']=='main_0024_t100000')
    assert digest==target['selected_raw_sha256']
    record = json.loads(gzip.decompress(raw.read_bytes()))
    times = np.array(record['result']['t']); yy=np.array(record['result']['y'])
    use = np.flatnonzero(times==20.)
    assert len(use)==1
    c07 = dict(stationary_selected_endpoints=len(finite),zero_immigration_cases=len(zero),
        zero_immigration_outcomes=[dict(fraction=k[0],direction=k[1],occupancy=k[2],runs=v) for k,v in sorted(outcomes.items())],
        focal_raw_file=str(raw.relative_to(ROOT)),focal_raw_sha256=digest,
        first_extinction=record['result']['extinction_events'][0],initial_temperature_k=float(core.temperature_k(yy[-1,0],p.climate)),
        temperature_at_20yr_k=float(core.temperature_k(yy[-1,use[0]],p.climate)))
    tracking = []
    for name in ('selected_main.csv','selected_subsets.csv'):
        tracking += read(FIG/'refuge_coupling'/name)
    protected=[]
    for r in tracking:
        if r['attempt_status']=='no_supported_conditional_start_found' or float(r['contrast_k'])==0:continue
        loser = 'm' if r['direction']=='A_into_M' else 'a'
        margin = float(r['path_min_temperature_warm_k'])-ts if loser=='m' else ts-float(r['path_max_temperature_cold_k'])
        if margin>0:
            protected.append(dict(case_id=r['case_id'],status=r['attempt_status'],margin_k=margin,
                                  losing_guild_present=None if r['attempt_status']!='completed' else r['global_present_'+loser]=='True'))
    tracking_pairs=read(FIG/'refuge_coupling/direction_comparisons.csv')
    exceptions=[r for r in tracking_pairs if float(r['contrast_k'])>0 and r['matching_endpoint']=='True'
                and r['class_a'] in ('pure_partition','spatial_coexistence') and r['class_m'] in ('pure_partition','spatial_coexistence')]
    c08=dict(protected_path_counts=dict(Counter(r['status'] for r in protected)),
        protected_completed_missing_guild=sum(r['losing_guild_present'] is False for r in protected),
        matching_coexisting_nonzero_contrast_pairs=len(exceptions),
        counterexamples=[{k:r[k] for k in ('case_a','case_m','fraction','warm_fraction','contrast_k','dispersal_yr','class_a','class_m')} for r in exceptions],
        f_le_half_matching_coexisting_nonzero_contrast_pairs=sum(float(r['fraction'])<=.5 for r in exceptions),
        greenhouse_peak_k=float(max(temperatures)),
        scope='No paired supported rescue in the tested f=0/0.5 geometry; f=0.9 exceptions refute a universal tracking-refuge failure claim.')
    buffered=[]
    for name in ('selected_main.csv','selected_controls.csv','selected_sensitivity.csv'):
        buffered+=read(FIG/'buffered_refuges'/name)
    main=read(FIG/'buffered_refuges/selected_main.csv')
    keyruns=[r for r in main if r['configuration']=='both' and float(r['fraction'])<=.5 and float(r['dispersal_yr'])<=.001]
    assert len(keyruns)==12
    pairs=read(FIG/'buffered_refuges/direction_comparisons.csv')
    keypairs=[r for r in pairs if r['configuration']=='both' and float(r['fraction'])<=.5
              and 0<float(r['dispersal_yr'])<=.001 and float(r['refuge_fraction'])==.02
              and float(r['warm_k'])==286 and float(r['cold_k'])==278 and r['activity']=='fixed']
    assert len(keypairs)==6 and all(r['matching_endpoint']=='True' and r['both_coexist']=='True' for r in keypairs)
    lookup = {r['case_id']:r for r in buffered}
    direct_errors=[]
    stock_fields=['methane_ratio']+[name for name in keyruns[0] if name.startswith(('pressure_','cells_','acetate_'))]
    for comparison in keypairs:
        a,b=lookup[comparison['case_a']],lookup[comparison['case_m']]
        errors=[]
        for name in stock_fields:
            if a[name]==b[name]=='':continue
            u,v=float(a[name]),float(b[name])
            errors.append(0. if u==v==0 else 2*abs(u-v)/(abs(u)+abs(v)))
        direct_errors.append(max(errors))
    assert max(direct_errors)<.001
    c09=dict(total_stationary=sum(r['settling_status']=='census_stationary' for r in buffered),
        selected_total=len(buffered),extended_to_200000=sum(float(r['selected_horizon_yr'])==200000 for r in buffered),
        global_endpoint_classes=dict(Counter(r['endpoint_class'] for r in buffered)),
        paired_histories=len(pairs),matching_pairs=sum(r['matching_endpoint']=='True' for r in pairs),
        matching_mixed_pairs=sum(r['matching_endpoint']=='True' and r['both_coexist']=='True' for r in pairs),
        key_rescue_runs=len(keyruns),key_rescue_pairs=len(keypairs),
        key_temperature_range_k=[min(float(r['global_temperature_k']) for r in keyruns),max(float(r['global_temperature_k']) for r in keyruns)],
        key_pair_maximum_reported_relative_stock_difference=max(float(r['maximum_relative_stock_difference']) for r in keypairs),
        key_pair_maximum_direct_relative_stock_difference=max(direct_errors))
    exchange = read(FIG/'bottleneck/exchange_continuation.csv')
    target = sorted([r for r in exchange if float(r['fraction'])==0 and float(r['refuge_fraction'])==.02],key=lambda r:float(r['dispersal_yr']))
    selected=[r for r in target if float(r['dispersal_yr'])<=1.0000001e-4]
    xx=np.log10([float(r['dispersal_yr']) for r in selected]);zz=np.array([float(r['log10_min_cells']) for r in selected])
    centered=xx-np.mean(xx);slope=float(np.sum(centered*(zz-np.mean(zz)))/sum(centered**2))
    intercept=float(np.mean(zz)-slope*np.mean(xx))
    half=crossing(target,'log_lambda',np.log(np.log(2.)))[0]
    floor=crossing(target,'posthoc_global_floor_1yr_min_log_cells',0.)[0]
    floor10=crossing(target,'posthoc_global_floor_10yr_min_log_cells',0.)[0]
    c10=dict(fit_points=len(selected),fit_log10_exchange_range=[float(min(xx)),float(max(xx))],
        slope=slope,max_fit_residual_decades=float(max(abs(zz-(slope*xx+intercept)))),
        half_survival=half,annual_one_cell=floor,ten_year_one_cell=floor10,
        half_over_annual=half['interpolated_yr']/floor['interpolated_yr'],
        half_over_ten_year=half['interpolated_yr']/floor10['interpolated_yr'],
        gaussian_approximation_cells=float(np.log(2.)*8.766*37.9),
        exact_table_minimum_threshold_cell_range=[min(float(r['first_window_cells_for_half_survival_at_min']) for r in target),max(float(r['first_window_cells_for_half_survival_at_min']) for r in target)],
        scope='First rare-window conditional diagnostic, f=0/2% warm refuge; count crossings are posthoc global counts, not local-census counterfactual reruns.')
    recycled=[r for r in exchange if float(r['fraction'])==.5]
    smallest=min(recycled,key=lambda r:float(r['min_cells']))
    c11=dict(cases=len(recycled),all_robust_first_window_persistence=all(r['classification']=='robust_persistence' for r in recycled),
        minimum_global_acetogen_cells=float(smallest['min_cells']),refuge_area_fraction=float(smallest['refuge_fraction']),
        exchange_yr=float(smallest['dispersal_yr']),case_id=smallest['case_id'])
    result=dict(C05=switches,C06=c06,C07=c07,C08=c08,C09=c09,C10=c10,C11=c11,inputs=INPUTS,
        source_sha256={str(Path(m.__file__).relative_to(ROOT)):sha256(Path(m.__file__).read_bytes()).hexdigest() for m in (core,)},
        checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='Independent algebra/finite-difference controls and table/raw recounts, with shared empirical inputs. No new trajectory or empirical validation.')
    HERE.joinpath('synthesis-communities-audit-2026-11-11.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(C05=switches,C06=c06,C08=c08['protected_path_counts'],C09=c09,C10=c10,C11=c11),indent=2))

if __name__=='__main__':main()
