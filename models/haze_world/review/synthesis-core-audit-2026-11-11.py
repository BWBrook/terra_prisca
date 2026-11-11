"""Independent short algebra/recount controls for the synthesis's supported rows."""
from dataclasses import replace
from hashlib import sha256
import csv
import json
from pathlib import Path

import numpy as np
from scipy.integrate import quad, solve_ivp
from terra_prisca.haze_world import population_coupling as core

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent

def read(name):
    return json.loads((ROOT/name).read_text())

def digest(p):
    return sha256(p.read_bytes()).hexdigest()

def main():
    inputs = ['models/haze_world/figures/dormancy/prediction_assessment.json',
              'models/haze_world/figures/dormancy/first_survival.csv',
              'models/haze_world/figures/bottleneck/survival.csv',
              'models/haze_world/review/check_turnover_gaussian.json',
              'models/haze_world/review/cycle-closure-results-2026-11-11.json']
    a = read(inputs[0])
    half = []
    approximations = {('m', 0.): .006, ('m', .5): .00247,
                      ('a', 0.): .00046, ('a', .5): .00082}
    for row in a['KD3']['curves']:
        if row['switching_factor'] != 10: continue
        assert len(row['brackets']) == 1
        bracket = row['brackets'][0]
        low, high = bracket['low'], bracket['high']
        guess = approximations[(row['displaced_guild'], row['fraction'])]
        half.append(dict(guild=row['displaced_guild'], fraction=row['fraction'],
            epsilon=[low, high], half_life_yr=[np.log(2)/(8.766*high), np.log(2)/(8.766*low)],
            measured_over_approximation=[low/guess, high/guess],
            evidence=bracket['evidence'], cases=bracket['cases']))
    assert len(half) == 4 and all(r['evidence']=='resolved_first_bottlenecks' for r in half)
    comparison = read(inputs[3])['shape_diagnostic']
    relative_percent = 100*abs(comparison['scalar_hazard_cells_for_half_survival']/comparison['exact_multitype_cells_for_half_survival']-1)
    # Separate scalar backward equation and quadrature on a time-varying environment.
    birth = lambda t: 2.+np.sin(t)
    death = lambda t: 1.5+.2*np.cos(t)
    log_mean = lambda t: .5*t+1.-np.cos(t)-.2*np.sin(t)
    inv_u = 1+quad(lambda t: death(t)*np.exp(-log_mean(t)), 0., 4., epsabs=1e-12)[0]
    flow = solve_ivp(lambda t,u: [-(birth(t)-death(t))*u[0]+birth(t)*u[0]**2],
                     (4.,0.), [1.], rtol=1e-11, atol=1e-13)
    assert abs(flow.y[0,-1]-1/inv_u)<1e-10
    modes = []
    for fraction in (0.,.5):
        for loss in (.001,.002):
            base = core.reference()
            p = replace(base, acetate_fraction=fraction, biology=replace(base.biology,loss_h=loss))
            state = next(r for r in core.equilibrium_states(p) if r['kind']=='mixed' and r['stable'])
            y = np.array(state['y']);scale=np.maximum(abs(y),[10.,1e-4,1e-4,1e-5,.01])
            spectra=[]
            for step in (1e-4,1e-5):
                matrix=np.column_stack([(core.rhs(y+step*scale[j]*np.eye(5)[j],p)
                    -core.rhs(y-step*scale[j]*np.eye(5)[j],p))/(2*step*scale[j]) for j in range(5)])
                eigenvalues=np.linalg.eigvals(matrix*scale[None,:]/scale[:,None])
                value=max((v for v in eigenvalues if v.imag>0),key=lambda v:v.real)
                assert max(eigenvalues.real)<0
                spectra.append(dict(real_yr=float(value.real),imaginary_yr=float(value.imag),
                    period_yr=float(2*np.pi/value.imag), damping_yr=float(-1/value.real),
                    quality_factor=float(value.imag/(-2*value.real))))
            assert abs(spectra[0]['damping_yr']/spectra[1]['damping_yr']-1)<.001
            modes.append(dict(fraction=fraction,loss_h=loss,stencils=spectra))
    with (ROOT/inputs[1]).open() as f: table=list(csv.DictReader(f))
    selected=[r for r in table if r['configuration']=='warm' and float(r['fraction'])==0
              and r['direction']=='A_into_M' and r['guild']=='a' and float(r['epsilon'])==.1]
    with (ROOT/inputs[2]).open() as f: baseline=list(csv.DictReader(f))
    minima=[]
    for row in selected:
        d=float(row['dispersal_yr'])
        old=next(r for r in baseline if r['guild']=='a' and r['case_id']==('main_0008_t100000' if d==1e-9 else 'main_0010_t100000'))
        minima.append(dict(dispersal_yr=d, dormant_log10_min=float(row['log10_min_cells']),
                          no_dormancy_log10_min=float(old['log10_min_cells'])))
    repetitions=[dict(cycles=n,extinction=float(np.exp(-14500/(1+99*n)))) for n in (1,100,1000000)]
    kicks=read(inputs[4])['amplitude']
    kick_damping=[r['mode']['damping_time_yr']/1000 for r in kicks]
    result=dict(kick_damping_kyr=[min(kick_damping),max(kick_damping)],source_sha256={str(Path(core.__file__).relative_to(ROOT)):digest(Path(core.__file__))},
        inputs={name:digest(ROOT/name) for name in inputs}, checker_sha256=digest(Path(__file__)),
        C16=dict(scalar_n50=comparison['scalar_hazard_cells_for_half_survival'],
            multitype_n50=comparison['exact_multitype_cells_for_half_survival'],relative_difference_percent=relative_percent,
            independent_scalar_survival_ode=float(flow.y[0,-1]),independent_scalar_survival_quadrature=1/inv_u,
            scope='Exact single-type linear process with Poisson entry; multitype reduction separately checked in one recorded example'),
        C17=half,C18=dict(log_population_ratio=8.766*6.2,half_life_fraction=np.log(2)/(8.766*6.2),half_life_percent=100*np.log(2)/(8.766*6.2)),
        C19=minima,C20=modes,C24=repetitions,
        scope='Algebra, independent finite differences and frozen-table recounts; no new long trajectories or empirical calibration')
    HERE.joinpath('synthesis-core-audit-2026-11-11.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(half_lives=len(half),scalar_error=abs(flow.y[0,-1]-1/inv_u),modes=modes,minima=minima),indent=2))

if __name__=='__main__': main()
