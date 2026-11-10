"""Independent product powers, annual budget and equilibrium closure checks.

uv run python models/haze_world/review/product_activity_check.py
"""
from dataclasses import asdict, replace
from hashlib import sha256
import csv
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

from terra_prisca.haze_world import population_coupling as model
from terra_prisca.haze_world.methane_budget import AVOGADRO, atmosphere, temperature_k
from terra_prisca.haze_world.two_guilds import HENRY_30C_MOL_L_PA, guilds

H = 365.25 * 24
CASES = Path('models/haze_response/arney2016/cases.csv')


def independent(y, p):
    pressure, xa, xm, stock, ratio = y
    t = float(temperature_k(ratio, p.climate))
    base = guilds(t - 273.15, p.biology)
    co2 = float(next(r['p_co2_bar'] for r in csv.DictReader(CASES.open()) if r['case'] == p.climate.case)) * 100000
    factors = np.ones(2) if p.activity_feedback == 'fixed' else np.array([
        (max(stock, 0) / p.acetate_reference_mol_l)**.25,
        (max(ratio, 0) * co2 / p.methane_reference_pa)**.25])
    theta = np.array([g.threshold_pa for g in base]) * factors
    excess = np.maximum(pressure - theta, 0)
    q = np.array([g.rate_scale * z / (g.km_pa + z) if g.kinetics == 'saturating' else g.rate_scale * z / g.km_pa
                  for g, z in zip(base, excess)])
    x = np.array([xa, xm]) * p.enabled
    mu = np.array([g.yield_g_mol * (qi - g.maintenance) for g, qi in zip(base, q)])
    a = np.array([g.assimilation_mol_g for g in base])
    cat = H * x * (q - a * np.maximum(mu, 0))
    sigma = 1. if p.recycling_variant == 'constant' else 1 / (1 + np.exp((p.recycling_midpoint_k - t) / p.width_k))
    kr, ko = p.acetate_fraction * sigma / p.acetate_lifetime_yr, (1-p.acetate_fraction)/p.acetate_lifetime_yr
    air = atmosphere(p.climate.case)
    gamma = p.habitat_l_cm2 * AVOGADRO / (air['column'] * air['f_co2'])
    j = 4 * p.climate.donor_flux * H * 3600 / (AVOGADRO * p.habitat_l_cm2)
    outlet = H * p.biology.exchange_mol_l_h_pa * (pressure-p.biology.atmosphere_pa)
    ab = air['flux_to_ratio_per_yr'] * p.climate.abiotic_flux
    loss = float(p.loss.rate(ratio))
    dy = np.r_[(j-H*q@x-outlet)/HENRY_30C_MOL_L_PA,
               H*x*(mu-p.biology.loss_h), cat[0]/4-(kr+ko)*stock,
               gamma*(cat[1]/4+kr*stock)+ab-loss]
    weights = np.r_[HENRY_30C_MOL_L_PA, a, 4., 4/gamma]
    export = H*np.sum(a*x*(p.biology.loss_h+np.maximum(-mu,0)))
    external = j-outlet-4*ko*stock-export+4/gamma*(ab-loss)
    return dy, dict(theta=theta, factors=factors, base=base, q=q, mu=mu, j=j,
                    kr=kr, ko=ko, gamma=gamma, weights=weights, external=external)


def jacobian_check(y, p):
    scales=np.maximum(np.abs(y),[10.,1e-4,1e-4,1e-5,.01]);jf=np.empty((5,5))
    for j in range(5):
        h=scales[j]*1e-4;delta=np.eye(5)[j]*h
        v=[independent(y+k*delta,p)[0] for k in (2,1,-1,-2)]
        jf[:,j]=(-v[0]+8*v[1]-8*v[2]+v[3])/(12*h)*scales[j]/scales
    jm=model.jacobian(y,p)
    err=float(np.linalg.norm(jf-jm)/np.linalg.norm(jf))
    eigen=np.linalg.eigvals(jf)
    assert err<1e-7
    return dict(relative_matrix_difference=err,
                independent_max_real_per_yr=float(max(eigen.real)))


def main():
    p = replace(model.reference(), activity_feedback='products')
    rref = 350/1800
    powers = []
    for af, mf in [(0,0), (1,1), (16,1), (1,16), (1/16,1/16)]:
        y = np.array([25., 5e-4, 3e-4, p.acetate_reference_mol_l*af, rref*mf])
        expected, terms = independent(y,p)
        actual_guilds = model.activity_guilds(y,p)
        assert np.allclose([g.threshold_pa for g in actual_guilds], terms['theta'],rtol=1e-14,atol=0)
        for actual, base in zip(actual_guilds,terms['base']):
            aa,bb=asdict(actual),asdict(base);aa.pop('threshold_pa');bb.pop('threshold_pa');assert aa==bb
        dy = model.rhs(y,p)
        residual = float(terms['weights']@dy-terms['external'])
        assert np.allclose(dy,expected,rtol=1e-12,atol=1e-11) and abs(residual)<1e-13
        powers.append(dict(acetate_reference_multiple=af,methane_pressure_reference_multiple=mf,
                           threshold_factors=terms['factors'].tolist(),redox_residual=residual))
    initial=np.array([23.,5.7e-4,3.4e-4,.00087,.1955])
    def residual_log(z):
        y=np.exp(z);dy,terms=independent(y,p)
        return np.r_[dy[0]*HENRY_30C_MOL_L_PA/terms['j'],
                     dy[1:3]/(y[1:3]*H*p.biology.loss_h),
                     dy[3]/(terms['j']/4),dy[4]/3e-5]
    fit=least_squares(residual_log,np.log(initial),xtol=1e-12,ftol=1e-12,gtol=1e-12,max_nfev=500)
    solved=np.exp(fit.x);assert fit.success and np.max(np.abs(fit.fun))<1e-8
    parent=next(e for e in model.equilibrium_states(p) if e['kind']=='mixed')
    relative=float(np.max(np.abs(solved-parent['y'])/np.maximum(np.abs(solved),1e-10)))
    assert relative<1e-7
    scenarios=[]
    for label,fraction,variant,old_stock in [('old_37M_case',.5,'constant',36.70992652),('old_773M_case',1.,'cold_limited',773.311541)]:
        pp=replace(model.reference(.6),activity_feedback='products',acetate_fraction=fraction,
                   recycling_variant=variant,acetate_lifetime_yr=10000.)
        states=model.equilibrium_states(pp,n_grid=1001)
        records=[]
        for e in states:
            yy=np.asarray(e['y']);dy,terms=independent(yy,pp)
            rr=float(terms['weights']@dy-terms['external'])
            flow_residual=float(abs(dy[0])*HENRY_30C_MOL_L_PA/terms['j'])
            assert abs(rr)<1e-11 and flow_residual<1e-8 and np.max(np.abs(dy[1:]))<1e-8
            records.append(dict(kind=e['kind'],stable=bool(e['stable']),temperature_k=float(e['t_k']),
                                acetate_mol_l=float(yy[3]),pressure_pa=float(yy[0]),ratio=float(yy[4]),
                                independent_rhs_max_other=float(np.max(np.abs(dy[1:]))),redox_residual=rr,
                                independent_jacobian_check=jacobian_check(yy,pp) if e['stable'] else None))
        scenarios.append(dict(label=label,former_fixed_activity_stock_mol_l=old_stock,
                              scenario='potential.6,tau10000yr,originalfractionandvariant',returned_states=records))
    result=dict(scope='Conditional product-law and numerical root audit; not an exhaustive root census or chemical plausibility bound',
                source_sha256=sha256(Path(model.__file__).read_bytes()).hexdigest(),methane_reference_ratio_case_B=rref,
                reference_multiplier_checks=powers,independent_reference_state=solved.tolist(),
                independent_reference_temperature_k=float(temperature_k(solved[4],p.climate)),
                maximum_scaled_root_residual=float(np.max(np.abs(fit.fun))),
                maximum_relative_difference_from_model_reference=relative,long_lag_scenarios=scenarios)
    result['independent_reference_jacobian_check']=jacobian_check(solved,p)
    Path(__file__).with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()
