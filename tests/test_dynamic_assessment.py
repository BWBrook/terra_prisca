from terra_prisca.haze_world.dynamic_assessment import convergence, prediction_summary


def pair(status17, status33, tau17='', tau33='', gain17='', gain33=''):
    common = dict(chemistry='fixed', fraction='0.5', loss_h='0.001',
                  nominal_potential='0.3', sigma_k='1.0', status='accepted', ratio='0.195')
    return [dict(common, n_habitats=str(n), critical_lag_status=status,
                 critical_lag_yr=str(tau), gain=str(gain),
                 gain_status='defined' if gain != '' else 'no_admissible_control')
            for n,status,tau,gain in ((17,status17,tau17,gain17),(33,status33,tau33,gain33))]


def test_missing_control_does_not_establish_gain_or_joint_convergence():
    result = convergence(pair('finite_crossing','finite_crossing',16.,102.))[0]
    assert result['tau_converged'] is False
    assert result['gain_converged'] is None
    assert result['both_converged'] is None


def test_matching_right_censoring_is_not_numeric_convergence_of_a_margin():
    rows = pair('not_detected_through_10000','not_detected_through_10000',gain17=0.,gain33=0.)
    result = convergence(rows)[0]
    assert result['gain_converged'] is True
    assert result['tau_converged'] is None
    assert result['both_converged'] is None


def test_convergence_of_another_branch_cannot_qualify_a_candidate_escape():
    row=pair('finite_crossing','finite_crossing',40.,40.,.01,.01)[1]
    row.update(temperature_k='281.5', ratio='0.195', lambda_real_tau_0='-0.001')
    other=dict(row,ratio33='0.205',both_converged=True)
    summary=prediction_summary([row],[other],[],[],[])
    assert summary['PB1']['escape_candidate_count']==1
    assert summary['PB1']['qualified_escape_count']==0
