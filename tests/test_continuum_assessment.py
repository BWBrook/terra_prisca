from terra_prisca.haze_world import continuum_assessment as assessment


def row(**overrides):
    value = dict(chemistry='fixed', fraction='0.5', sigma_k='1.0', dispersal_yr='0.0001',
                 nominal_potential='0.3', loss_h='0.001', ratio='0.4', status='converged',
                 gain_status='defined', frozen_fd_agrees='True', G_loc='0.03', Sc='-2', S0='-66.67',
                 critical_lag_status='finite_crossing', critical_lag_yr='100', mixed_width_k='0.1')
    value.update(overrides)
    return value


def test_missing_or_unresolved_evidence_does_not_support_predictions():
    result = assessment.assess([], [], {})
    assert result['PC1']['status'] == 'unresolved'
    for prediction in ('PC2', 'PC4', 'PC5', 'PC6'):
        assert result[prediction]['status'] == 'unassessed'
    result = assessment.assess([], [row(critical_lag_status='spectrum_unresolved', critical_lag_yr='')], {})
    assert not result['PC4']['low_d_finiteness_failures']


def test_already_unstable_state_is_not_a_long_margin_counterexample():
    unstable = row(status='homogeneous', critical_lag_status='already_unstable', critical_lag_yr='')
    result = assessment.assess([unstable], [], {})
    assert result['PC3']['counterexample_count'] == 0
    result = assessment.assess([row(status='homogeneous')], [], {})
    assert result['PC3']['counterexample_count'] == 1


def test_censoring_refutes_finiteness_without_claiming_connectivity_irrelevant():
    result = assessment.assess([], [row(critical_lag_status='not_detected_through_10000', critical_lag_yr='')], {})
    assert result['PC4']['status'] == 'refuted'
    assert len(result['PC4']['low_d_finiteness_failures']) == 1
    assert 'does not establish robustness at every connectivity' in result['PC4']['limit']
