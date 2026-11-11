from dataclasses import replace
import numpy as np

from terra_prisca.haze_world import competitive_evolution as model
from terra_prisca.haze_world import evolved_kinetics as kinetics
from terra_prisca.haze_world import population_coupling as reference


def test_identity_kinetic_state_preserves_reference_budget_and_redox():
    p=reference.reference();ratio=.195
    temperature=float(reference.temperature_k(ratio,p.climate))
    traits=kinetics.Traits((temperature-273.15,temperature-273.15),0.)
    y=np.array([30.,.0003,.0004,.001,ratio])
    np.testing.assert_allclose(model.rhs(y,p,traits),reference.rhs(y,p),rtol=2e-14,atol=2e-13)
    assert abs(model.redox_residual(y,p,traits))<1e-16
    derivative=model.rhs(y,p,traits)
    y[1]=0.
    assert model.rhs(y,p,traits)[1]==0.
    assert np.isfinite(derivative).all()


def test_mixed_balance_and_full_inventory_agree_at_reference_switch():
    p=reference.reference();temperature=281.534822805
    traits=kinetics.Traits((temperature-273.15,temperature-273.15),0.)
    candidates=[model.mixed_state(r,p,traits) for r in model.ratio_roots(temperature,p)]
    y=next(y for y in candidates if y is not None)
    assert max(abs(model.rhs(y,p,traits)[1:]))<1e-10
    assert abs(model.redox_residual(y,p,traits))<1e-16
    described=model.describe('mixed',y,p,traits)
    assert described['stable']
    assert described['climate_slope_k_per_ratio']<0
    inventory=model.fixed_equilibria(p,traits,301)
    assert {'lifeless','acetogen','methanogen','mixed'} <= {r['kind'] for r in inventory}
    assert any(s['kind']=='mixed' and abs(s['temperature_k']-temperature)<1e-5 for s in inventory)


def test_mutant_grid_and_stationary_root_check_real_fitness():
    p=model.parameters(.001,.5);t=277.960221065
    best=kinetics.best_response(t,p.biology,0.)
    traits=kinetics.Traits(tuple(best['positions_c']),0.)
    y=next(y for r in model.ratio_roots(t,p) if (y:=model.mixed_state(r,p,traits)) is not None)
    records=model.invasion(y,p,traits,'test')
    assert len(records)==2 and all(r['mutants']==2601 for r in records)
    assert all(r['passes'] for r in records)
    convergence=model.convergence(y,p,traits,best)
    assert all(r['convergence']=='attracting' for r in convergence)
    assert all(r['canonical_eigenvalues'] is None for r in convergence)


def test_fast_frozen_trait_pressure_formula_matches_guilds():
    p=model.parameters(.001,.5)
    traits=kinetics.Traits((10.,25.),.45,'smooth_shape')
    for t in (273.4,281.5,297.):
        expected=[g.rstar(p.biology.loss_h) for g in kinetics.guilds(t,p.biology,traits)]
        np.testing.assert_allclose(model.rstars_at_temperature(t,p.biology,traits),expected,rtol=3e-14)


def test_projected_path_stays_in_measured_trait_domain_and_does_not_claim_extinction():
    rows=model.canonical_path(.0003,0.,'linear_shape',.5,max_trait_step=.05,max_steps=10)
    assert rows
    assert all(all(4<=u<=30 for u in r['positions_c']) for r in rows if 'positions_c' in r)
    assert 'extinction' not in rows[-1]['status']


def test_canonical_path_checks_stability_between_saved_steps_and_keeps_last_state(monkeypatch):
    p=model.parameters(.001,.5);t=281.534822805
    traits=kinetics.Traits((t-273.15,t-273.15),0.)
    y=next(y for r in model.ratio_roots(t,p) if (y:=model.mixed_state(r,p,traits)) is not None)
    monkeypatch.setattr(reference,'switch_temperatures',lambda _: [t])
    monkeypatch.setattr(model,'branch_state',lambda *_: y.copy())
    monkeypatch.setattr(model,'canonical_gradient',lambda *_: (np.array([1.,0.]),'test'))
    checks=[]
    def stability(*_):
        checks.append(1)
        return {'stable':len(checks)==1}
    monkeypatch.setattr(model,'describe',stability)
    monkeypatch.setattr(model,'fixed_equilibria',lambda *_: [])
    rows=model.canonical_path(.001,0.,'linear_shape',.5,max_trait_step=.025,max_steps=20)
    assert rows[-1]['status']=='stable_ecological_branch_lost'
    assert rows[-1]['step']==1
    assert rows[-1]['positions_c']==traits.positions_c
    assert rows[-1]['attempted_positions_c'][0]>rows[-1]['positions_c'][0]
