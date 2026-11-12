import importlib.util
from pathlib import Path

import numpy as np
import pytest

from terra_prisca.haze_world import continuum_characteristic as characteristic
from terra_prisca.haze_world import continuum_core as weighted
from terra_prisca.haze_world import dynamic_core as reference
from terra_prisca.haze_world import population_coupling as physical


path = Path(__file__).resolve().parents[1]/'docs/audits/graded-dial-independent-2026-11-12.py'
spec = importlib.util.spec_from_file_location('graded_independent', path)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


@pytest.mark.parametrize('kappa,chemistry', [(0., 'fixed'), (1., 'acetate_only')])
def test_independent_physical_derivatives_recover_analytic_endpoint(kappa, chemistry):
    p = weighted.WeightedParams(physical.reference(), chemistry)
    old = reference.DynamicParams(p.base, chemistry)
    y = next(r['y'] for r in reference.equilibrium_states(old) if r['kind'] == 'mixed')
    separate = audit.assemble(p, y, kappa)
    analytic = characteristic.assemble(p, y)
    np.testing.assert_allclose(audit.instantaneous(separate), audit.instantaneous(analytic), rtol=1e-6, atol=2e-8)
    lhs, rhs = audit.responses(p, y, separate), audit.responses(p, y, analytic)
    assert lhs['Sc'] == pytest.approx(rhs['Sc'], rel=1e-5, abs=1e-7)
    assert lhs['S0'] == pytest.approx(rhs['S0'], rel=1e-5)


def test_c54_recount_retains_unstable_and_censored_groups():
    result = audit.recount()
    assert result['pinned_count'] == 42
    assert result['pinned_already_unstable'] == 6
    assert result['ordinary_count'] == 122
    assert result['ordinary_censored'] == 113
    assert result['excluded_count'] == 6
    assert result['excluded_all_unstable']


def test_censored_transition_preserves_its_ratio_bound():
    records = [dict(branch_id='example', dial=0., critical_lag_status='finite_crossing', critical_lag_yr=1.,
                    Sc=0., weak_mode_tau_yr=1.),
               dict(branch_id='example', dial=.1, critical_lag_status='not_detected_through_10000', critical_lag_yr=None,
                    Sc=-1., weak_mode_tau_yr=None)]
    result = audit.grid_recount(records)['branches'][0]
    assert not result['finite_pairs']
    assert result['first_censored_transition_bounds'][0]['tau_ratio_lower_bound'] == 10000.
