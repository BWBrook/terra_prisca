from terra_prisca.haze_world import graded_assessment as assessment
from terra_prisca.haze_world import graded_thresholds as thresholds


def row(dial,tau,sc,branch='D1_f0.5',kind='prescribed'):
    return dict(branch_id=branch,dial=dial,Sc=sc,kind=kind,supply_check_status='passed',
        lag=dict(status='finite_crossing' if tau is not None else 'not_detected_through_10000',tau_c=tau),
        weak_mode_tau_yr=tau,weak_mode_ratio=1. if tau else None)


def test_first_censored_transition_is_a_bound_and_not_a_finite_interpolation():
    rows=[row(.1,13.,-.2),row(.3,None,-.6)]
    result=assessment.assess(rows,{}, {})
    assert result['PD1']['censored_transitions'][0]['lower_ratio_bound']>700
    assert not result['PD1']['finite_adjacent']


def test_power_law_slope_clause_can_fail_despite_high_r_squared():
    rows=[row(x,x**.8,-x) for x in (3.,10.,30.)]
    result=assessment.assess(rows,{}, {})
    assert result['PD2']['status']=='refuted_slope_clause'
    assert result['PD2']['branches'][0]['r_squared']> .999999


def test_unresolved_raw_finite_input_is_not_silently_passed():
    item=row(.1,13.,-.2);item['supply_check_status']='unresolved'
    assert assessment.assess([item],{}, {})['counts']['raw_finite_input_qualified']==0
    receipt=dict(records=[dict(branch_id=item['branch_id'],dial=.1,status='qualified_by_two_steps')])
    assert assessment.assess([item],{},receipt)['counts']['raw_finite_input_qualified']==1


def test_passing_prescribed_formula_does_not_hide_refinement_counterexample():
    primary=row(.1,13.,-.2)
    extra=row(.17,78.,-.3,kind='threshold_refinement')
    extra['weak_mode_ratio']=.26
    result=assessment.assess([primary],{}, {},[extra])
    assert result['PD4']['status']=='refuted_by_authorised_refinement'
    assert result['PD4']['comparisons'][0]['passed']
    assert not result['PD4']['refinement_comparisons'][0]['passed']


def test_a_censored_jump_cannot_become_a_qualified_thirty_year_root(tmp_path,monkeypatch):
    low=dict(row(.1,13.,-.1),stage='D1',fraction=.5,status='accepted')
    high=dict(row(.3,None,-.3),stage='D1',fraction=.5,status='accepted')
    def fake(dial,*args,**kwargs):
        return dict(row(dial,13. if dial<.2 else None,-dial),stage='D1',fraction=.5,status='accepted')
    monkeypatch.setattr(thresholds.runs,'d1_point',fake)
    answer,_=thresholds.refine([low,high],tmp_path,'control')
    assert answer['status']=='refinement_unresolved'
    assert answer['initial_finite_interpolated_price'] is None
