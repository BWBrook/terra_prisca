"""Approximate Newton faces for exactly zero linear allocation float rates.

Only Newton row/column couplings change. The physical RHS, accepted driver,
charts, stocks, censuses and tolerances remain those of the stage variant.
A retained incoming log source may exist below floating range, so a frozen
Newton face is not an algebraically invariant or extinct population.
"""

import numpy as np
from scipy.special import logsumexp

from . import dormancy_stage_integration as stage

Census=stage.Census


class _Coordinates(stage._Coordinates):
    def __init__(self,initial,p):
        super().__init__(initial,p)
        self.zero_face_newton_stats={}


def coordinate_jacobian(time,state,coords):
    matrix=stage.coordinate_jacobian(time,state,coords)
    physical,_=coords.decode(state)
    flux=stage.model.fluxes(physical,coords.p,trial_extension=True)
    for group in coords.groups:
        if not group['present']:continue
        indices=group['indices']
        candidates=[a for a,index in enumerate(indices)
                    if not coords.stage_positive[index] and state[index]==0.]
        if not candidates:continue
        h,log_h=coords.allocations(state,group)
        growth=np.array([flux['net_growth_yr'][j,group['guild']] if s==0
                         else -flux['dormant_loss_yr'] for j,s in group['nodes']])
        mean=float(h@growth/sum(h));q=group['migration'].copy()
        for a,(j,s) in enumerate(group['nodes']):
            for b,(k,other) in enumerate(group['nodes']):
                if j==k and s!=other:
                    q[a,b]=flux['sigma_yr'][j,group['guild']] if s==0 else flux['rho_yr'][j,group['guild']]
        # This is exactly the frozen linear-allocation RHS expression. Calling
        # coords.derivative here could consume accepted chemical-chart requests.
        rates=h*(growth-mean)+q.T@h-q.sum(axis=1)*h
        for a in candidates:
            if rates[a]!=0.:continue
            index=int(indices[a]);diagonal=matrix[index,index]
            matrix[index,:]=0.;matrix[:,index]=0.;matrix[index,index]=diagonal
            incoming=q[:,a]>0
            log_source=float(logsumexp(np.log(q[incoming,a])+log_h[incoming])) if np.any(incoming) else -np.inf
            entry=coords.zero_face_newton_stats.setdefault(index,dict(
                calls=0,first_time_yr=float(time),first_log_incoming_allocation_rate_yr=log_source,
                first_retained_incoming_log_source=bool(np.isfinite(log_source))))
            entry.update(calls=entry['calls']+1,last_time_yr=float(time),
                last_log_incoming_allocation_rate_yr=log_source,
                last_retained_incoming_log_source=bool(np.isfinite(log_source)))
    return matrix


class _FaceLSODA(stage._StageLSODA):
    def _chemical_jacobian(self,time,state):
        try:return coordinate_jacobian(time,state,self.coordinates)
        except stage._ChemicalConditioning as error:
            if hasattr(error,'chemical_cause'):
                self._record_request(error,getattr(self,'_guard_left',time),getattr(self,'_guard_start',state))
            raise


def integrate(y0,p,years,**kwargs):
    instances=[]
    def coordinates(initial,parameters):
        value=_Coordinates(initial,parameters);instances.append(value);return value
    namespace=stage.integrate.__globals__.copy()
    namespace.update(_Coordinates=coordinates,_StageLSODA=_FaceLSODA)
    function=stage.chemical._copied(stage.integrate,namespace)
    try:result=function(y0,p,years,**kwargs)
    except RuntimeError as error:
        error.zero_face_newton_stats=[c.zero_face_newton_stats for c in instances]
        raise
    result.metadata.update(upstream_numerical_variant=result.metadata['numerical_variant'],
        numerical_variant='analytic_dormancy_zero_face_newton',
        zero_face_newton_stats=[c.zero_face_newton_stats for c in instances],
        zero_face_newton_scope='Approximate Newton row/column couplings only; own diagonal retained. Gate rechecked at each matrix evaluation: present linear allocation coordinate equals0 and the unchanged returned float RHS equals0 exactly. Positive coordinates or representable positive source are never selected for the approximation. A retained log source may exist below floating range; no algebraic-invariance, extinction, clipping or physical-source removal claim.')
    return result


def integrate_finite(y0,p,years,process=Census(),**kwargs):
    return integrate(y0,p,years,census=process,**kwargs)
