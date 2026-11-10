"""Maintained Radau with a certified tiny positive dense extension.

The frozen physical RHS, accepted driver, charts, censuses and tolerances are
unchanged. A present linear allocation may replace its native cubic by the
native-endpoint chord only under an outward-rounded interpolation certificate.
The certificate is not an exact-ODE, future-trajectory or lineage error bound.
"""

from fractions import Fraction
from math import comb, isfinite, nextafter

import numpy as np
from numpy.polynomial import Polynomial
from scipy.integrate import Radau

from . import dormancy_face_integration as face

Census=face.Census
stage=face.stage
_EPS=Fraction.from_float(np.finfo(float).eps)
_UNIT=_EPS/2
_ETA=Fraction.from_float(np.nextafter(0.,1.))


def _f(value):return Fraction.from_float(float(value))
def _l1(coefficients):return sum(map(abs,coefficients),Fraction(0))
def _gamma(operations):return operations*_UNIT/(1-operations*_UNIT)
def _upper(value):return nextafter(float(value),np.inf)
def _lower(value):return nextafter(float(value),-np.inf)
def _ratio(value):return dict(n=hex(value.numerator),d=hex(value.denominator))


def _add(a,b):
    return tuple((a[i] if i<len(a) else 0)+(b[i] if i<len(b) else 0)
                 for i in range(max(len(a),len(b))))


def _multiply(a,b):
    result=[Fraction(0)]*(len(a)+len(b)-1)
    for i,x in enumerate(a):
        for j,y in enumerate(b):result[i+j]+=x*y
    return tuple(result)


def _theta_coefficients(unit_coefficients):
    result=[Fraction(0)]*len(unit_coefficients)
    for power,value in enumerate(unit_coefficients):
        for k in range(power+1):result[k]+=comb(power,k)*value
    return tuple(result)


def _evaluation_error(unit_coefficients,theta_floats,native_end):
    exact_theta=_theta_coefficients(unit_coefficients)
    conversion=sum((abs(value-_f(rounded)) for value,rounded in zip(exact_theta,theta_floats)),Fraction(0))
    operations=16*len(unit_coefficients)+16
    anchor=abs(_f(native_end)-sum(unit_coefficients,Fraction(0)))
    return (conversion+anchor+_gamma(operations)*(_l1(unit_coefficients)+sum((_f(abs(x)) for x in theta_floats),Fraction(0)))
            +operations*_ETA)


def _allocation_error(coefficients,error,root):
    if not root:return error
    size=_l1(coefficients)
    return 2*size*error+error*error+_gamma(2)*(size+error)**2+2*_ETA


def _constrained_indices(coords):
    indices=[*range(0,coords.m-1,6),coords.m-1]
    indices += [6*j+3 for j,w in enumerate(coords.p.weights) if w and not coords.acetate_positive[j]]
    indices += [int(i) for g in coords.groups if g['present'] for i in g['indices'] if not coords.stage_positive[i]]
    return tuple(dict.fromkeys(indices))


def _statistics():
    return dict(native_dense_pieces=0,extended_pieces=0,extended_components=0,
        negative_native_endpoint_pieces=0,negative_native_endpoint_rejections=0,
        declined_defect=0,declined_normalizer=0,maximum_defect_upper=0.,
        maximum_cell_curve_redistribution_upper=0.,sum_local_cell_curve_bounds=0.,
        minimum_normalizer_lower=None,extensions=[])


class _Coordinates(face._Coordinates):
    def __init__(self,initial,p):
        super().__init__(initial,p)
        self.positive_dense_stats=_statistics()
        self.dense_census=Census()
        self.radau_work=dict(rhs_evaluations=0,jacobian_attempts=0,constructor_jacobian_attempts=0,constructors=0,constructor_failures=0,factorizations=0)


def _normalizer_certificate(unit_polys,theta,indices,positive,changes,native_end):
    old_h=[];new_h=[];old_error=[];new_error=[]
    for index,root in zip(indices,positive):
        original=unit_polys[index]
        revised=changes.get(index,original)
        old_h.append(_multiply(original,original) if root else original)
        new_h.append(_multiply(revised,revised) if root else revised)
        old_z_error=_evaluation_error(original,theta[index],native_end[index])
        revised_theta=theta[index] if index not in changes else np.r_[native_end[index],float(revised[1]),np.zeros(len(original)-2)]
        new_z_error=_evaluation_error(revised,revised_theta,native_end[index])
        old_error.append(_allocation_error(original,old_z_error,root))
        new_error.append(_allocation_error(revised,new_z_error,root))
    original_H=(Fraction(0),);regularized_H=(Fraction(0),)
    for value in old_h:original_H=_add(original_H,value)
    for value in new_h:regularized_H=_add(regularized_H,value)
    old_K=sum(map(_l1,old_h),Fraction(0));new_K=sum(map(_l1,new_h),Fraction(0))
    old_errors=sum(old_error,Fraction(0));new_errors=sum(new_error,Fraction(0))
    summation_operations=4*len(indices)+16
    old_margin=old_errors+_gamma(summation_operations)*(old_K+old_errors)+summation_operations*_ETA
    new_margin=new_errors+_gamma(summation_operations)*(new_K+new_errors)+summation_operations*_ETA
    old_lower=original_H[0]-_l1(original_H[1:])-old_margin
    new_lower=regularized_H[0]-_l1(regularized_H[1:])-new_margin
    return dict(lower=min(old_lower,new_lower),K=old_K+old_errors,
        original=original_H,regularized=regularized_H,
        original_component_norm=old_K,regularized_component_norm=new_K,
        original_rounding_margin=old_margin,regularized_rounding_margin=new_margin)


class _Dense:
    def __init__(self,native,native_end,coords,atol):
        self.t,self.t_old,self.h=float(native.t),float(native.t_old),float(native.h)
        self.native_start=np.asarray(native.y_old).copy()
        self.native_end=np.asarray(native_end).copy()
        self.Q=np.asarray(native.Q).copy()
        if np.any(~np.isfinite(self.Q)) or np.any(~np.isfinite(self.native_start)) or np.any(~np.isfinite(self.native_end)):
            raise stage.guarded._InvalidTrial('nonfinite_native_dense','Radau returned nonfinite dense inputs')
        self.constraints=_constrained_indices(coords)
        self.negative_start=tuple(i for i in self.constraints if self.native_start[i]<0.)
        self.negative_end=tuple(i for i in self.constraints if self.native_end[i]<0.)
        self._endpoint_rejection_recorded=False
        self.repaired=[]
        self._stats=coords.positive_dense_stats
        self._stats['native_dense_pieces']+=1
        if self.negative_start or self.negative_end:self._stats['negative_native_endpoint_pieces']+=1
        unit_polys={}
        def unit(index):
            if index not in unit_polys:unit_polys[index]=tuple([_f(self.native_start[index]),*map(_f,self.Q[index])])
            return unit_polys[index]
        self.yh=np.zeros((len(self.native_start),self.Q.shape[1]+1));self.yh[:,0]=self.native_start
        for power in range(1,self.Q.shape[1]+1):
            for k in range(power+1):self.yh[:,k]+=comb(power,k)*self.Q[:,power-1]
        original_theta=self.yh.copy()
        candidates={}
        for group in coords.groups:
            if not group['present']:continue
            for index in group['indices']:
                index=int(index)
                if coords.stage_positive[index] or self.native_start[index]<0. or self.native_end[index]<0.:continue
                poly=Polynomial(original_theta[index])
                points=[-1.,0.,*stage.old._real_roots(poly.deriv(),-1.,0.)]
                if min(float(poly(x)) for x in points)>=0.:continue
                chord=(_f(self.native_start[index]),_f(self.native_end[index])-_f(self.native_start[index]),*([Fraction(0)]*(self.Q.shape[1]-1)))
                difference=tuple(a-b for a,b in zip(chord,unit(index)))
                chord_theta=np.r_[self.native_end[index],float(chord[1]),np.zeros(self.Q.shape[1]-1)]
                bound=(_l1(difference)+_evaluation_error(unit(index),original_theta[index],self.native_end[index])
                       +_evaluation_error(chord,chord_theta,self.native_end[index]))
                cap=min(float(atol[index]),float(_EPS*_EPS))
                if not isfinite(_upper(bound)) or _upper(bound)>cap:
                    self._stats['declined_defect']+=1;continue
                candidates[index]=dict(chord=chord,difference=difference,bound=bound,cap=cap,
                    native_minimum=min(float(poly(x)) for x in points))
        for group_k,group in enumerate(coords.groups):
            selected={i:row for i,row in candidates.items() if i in group['indices']}
            if not selected:continue
            indices=[int(i) for i in group['indices']]
            positive=[bool(coords.stage_positive[i]) for i in indices]
            for index in indices:unit(index)
            normalizer=_normalizer_certificate(unit_polys,original_theta,indices,positive,
                {i:row['chord'] for i,row in selected.items()},self.native_end)
            H=normalizer['lower']
            if H<=0 or _lower(H)<=0:
                self._stats['declined_normalizer']+=1;continue
            total_poly=unit(coords.m+group_k)
            z_upper=total_poly[0]+_l1(total_poly[1:])+_evaluation_error(total_poly,original_theta[coords.m+group_k],self.native_end[coords.m+group_k])
            mass_upper=_f(stage.SCALE)*(max(z_upper,Fraction(0))+1)
            volume_fraction=Fraction(1) if coords.shared else sum((_f(coords.p.weights[j]) for j,s in group['nodes'] if s==0),Fraction(0))
            process=coords.dense_census
            conversion=(_f(coords.p.coupled.habitat_l_cm2)*_f(process.surface_cm2)/_f(process.cell_mass_gdw)*volume_fraction)
            D=sum((row['bound'] for row in selected.values()),Fraction(0))
            cells=mass_upper*conversion*(D/H+normalizer['K']*D/(H*H))
            event=dict(native_left_yr=self.t_old,native_right_yr=self.t,
                native_y_old=self.native_start.tolist(),native_y_end=self.native_end.tolist(),native_Q=self.Q.tolist(),
                group_indices=indices,group_positive_charts=positive,total_coordinate_index=coords.m+group_k,
                original_H_coefficients_exact=[_ratio(x) for x in normalizer['original']],
                regularized_H_coefficients_exact=[_ratio(x) for x in normalizer['regularized']],
                component_norms_exact=dict(original=_ratio(normalizer['original_component_norm']),regularized=_ratio(normalizer['regularized_component_norm'])),
                normalizer_rounding_margins_exact=dict(original=_ratio(normalizer['original_rounding_margin']),regularized=_ratio(normalizer['regularized_rounding_margin'])),
                H_lower=_lower(H),cell_curve_redistribution_upper=_upper(cells),
                bound_inputs=dict(biomass_scale=stage.SCALE,habitat_l_cm2=coords.p.coupled.habitat_l_cm2,
                    surface_cm2=process.surface_cm2,cell_mass_gdw=process.cell_mass_gdw,
                    volume_fraction_exact=_ratio(volume_fraction),unit_roundoff=float(_UNIT),minimum_subnormal=float(_ETA),
                    biomass_upper='SCALE*(max(encoded_total_upper,0)+1)'),components=[])
            for index,row in selected.items():
                self.yh[index]=np.r_[self.native_end[index],float(row['chord'][1]),np.zeros(self.Q.shape[1]-1)]
                self.repaired.append(index)
                event['components'].append(dict(index=index,original_atol=float(atol[index]),epsilon_squared=float(_EPS*_EPS),
                    cap=row['cap'],difference_coefficients_exact=[_ratio(x) for x in row['difference']],
                    defect_upper=_upper(row['bound']),detected_native_minimum=row['native_minimum']))
                self._stats['extended_components']+=1
                self._stats['maximum_defect_upper']=max(self._stats['maximum_defect_upper'],_upper(row['bound']))
            self._stats['extensions'].append(event)
            self._stats['maximum_cell_curve_redistribution_upper']=max(self._stats['maximum_cell_curve_redistribution_upper'],_upper(cells))
            self._stats['sum_local_cell_curve_bounds']+=_upper(cells)
            lower=_lower(H)
            self._stats['minimum_normalizer_lower']=lower if self._stats['minimum_normalizer_lower'] is None else min(lower,self._stats['minimum_normalizer_lower'])
        if self.repaired:self._stats['extended_pieces']+=1

    def __call__(self,time):
        time=np.asarray(time);theta=(time-self.t)/self.h
        result=self.yh@np.array([theta**k for k in range(self.yh.shape[1])])
        unit=(time-self.t_old)/self.h
        for index in self.repaired:result[index]=(1-unit)*self.native_start[index]+unit*self.native_end[index]
        if time.ndim==0:
            if time==self.t_old:return self.native_start.copy()
            if time==self.t:return self.native_end.copy()
        else:
            result[:,time==self.t_old]=self.native_start[:,None]
            result[:,time==self.t]=self.native_end[:,None]
        return result


def _positive_piece(dense,left,right,coords,start):
    negative=(left==dense.t_old and bool(dense.negative_start)) or (right==dense.t and bool(dense.negative_end))
    if negative:
        if not dense._endpoint_rejection_recorded:
            dense._stats['negative_native_endpoint_rejections']+=1;dense._endpoint_rejection_recorded=True
        return False
    if right==left:return all(start[i]>=0. for i in dense.constraints)
    return stage._positive_piece(dense,left,right,coords,start)


class _Radau(face._FaceLSODA):
    def _initialize(self,time,state,bound,options):
        self._radau=None
        self._native_options=options|{'jac':self._native_jacobian}
        self._constructing_native=False
        self._dense_atol=np.asarray(options['atol']).copy()
        self.t=float(time);self.y=np.asarray(state).copy();self.t_old=None;self.t_bound=float(bound)
        self.direction=float(np.sign(bound-time)) or 1.;self.n=len(state);self.status='running'
        self.nfev=self.njev=self.nlu=0
        self._dense_token=self._dense_cache=None
        def observed(t,y):
            self._last_trial_time=float(t);self.nfev+=1
            self.coordinates.radau_work['rhs_evaluations']+=1
            return self._physical_rhs(t,y)
        self.fun=observed

    def _native_jacobian(self,time,state):
        self.coordinates.radau_work['jacobian_attempts']+=1
        self.coordinates.radau_work['constructor_jacobian_attempts']+=int(self._constructing_native)
        return self._chemical_jacobian(time,state)

    def _step_impl(self):
        lu_before=0 if self._radau is None else self._radau.nlu
        offset=self.nfev if self._radau is None else self.nfev-self._radau.nfev
        try:
            if self._radau is None:
                self._constructing_native=True;self.coordinates.radau_work['constructors']+=1
                try:self._radau=Radau(self.fun,self.t,self.y.copy(),self.t_bound,**self._native_options)
                finally:
                    self._constructing_native=False
                    self.coordinates.radau_work['constructor_failures']+=int(self._radau is None)
            success,message=self._radau._step_impl()
        finally:
            if self._radau is not None:
                self.nfev=offset+self._radau.nfev;self.njev=self._radau.njev;self.nlu=self._radau.nlu
                self.coordinates.radau_work['factorizations']+=self._radau.nlu-lu_before
        if success:self.t=float(self._radau.t);self.y=self._radau.y.copy()
        return success,message

    def _dense_output_impl(self):
        if self._dense_token is not self._radau.sol:
            self._dense_token=self._radau.sol
            self._dense_cache=_Dense(self._radau.sol,self._radau.y,self.coordinates,self._dense_atol)
        return self._dense_cache


def integrate(y0,p,years,**kwargs):
    instances=[];process=kwargs.get('census') or Census()
    def coordinates(initial,parameters):
        value=_Coordinates(initial,parameters);value.dense_census=process;instances.append(value);return value
    namespace=stage._accepted_integrate.__globals__.copy();namespace['_positive_piece']=_positive_piece
    accepted_driver=stage.chemical._copied(stage._accepted_integrate,namespace)
    namespace=stage.integrate.__globals__.copy()
    namespace.update(_accepted_integrate=accepted_driver,_Coordinates=coordinates,_StageLSODA=_Radau)
    function=stage.chemical._copied(stage.integrate,namespace)
    try:result=function(y0,p,years,**kwargs)
    except RuntimeError as error:
        error.positive_dense_stats=[c.positive_dense_stats for c in instances]
        error.zero_face_newton_stats=[c.zero_face_newton_stats for c in instances]
        error.radau_work=[c.radau_work for c in instances];raise
    result.metadata.update(numerical_variant='radau_dormancy_positive_dense',
        upstream_numerical_variant='analytic_dormancy_zero_face_newton',
        positive_dense_stats=[c.positive_dense_stats for c in instances],
        radau_work=[c.radau_work for c in instances],
        radau_work_scope='Native RHS/Jacobian/factorization attempts across all backends, including failed trials and constructor Jacobian attempts. Accepted-driver preliminary RHS checks are outside these native counters.',
        zero_face_newton_stats=[c.zero_face_newton_stats for c in instances],
        zero_face_newton_scope='Approximate Newton couplings only for present linear allocation coordinate0 and unchanged returned float RHS0; retained log sources may exist below float range. No physical source or stock changes.',
        positive_dense_scope='Maintained Radau; unchanged frozen RHS/driver/charts/census/tolerances. Present linear allocation dense chords only, nonnegative native endpoints, outward defect<=min(component_atol,epsilon**2), positive interval normalizer certificate. Counts include constructed pieces later rejected or truncated. Cell bounds describe local real-arithmetic normalized-curve redistribution, not decoded-float, exact-ODE, future-trajectory, lineage or log-probability bounds. Native endpoint arrays are retained per piece; census-interior restarts may alter later trajectories. Barycentric calls and polynomial metadata represent one chord up to recorded rounding bounds.')
    return result


def integrate_finite(y0,p,years,process=Census(),**kwargs):
    return integrate(y0,p,years,census=process,**kwargs)
