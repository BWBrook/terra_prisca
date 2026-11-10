"""Analytic chemical Newton rows without changing the frozen physical flow.

Primitive coefficient gradients remain numerical. Chemical source derivatives
use the allocation algebra directly, including exact zero-root and gauge
limits. Unrepresentable real derivatives request accepted-state chart changes.
"""

from hashlib import sha256
from types import FunctionType, SimpleNamespace

import numpy as np
from scipy.special import expit

from . import dormancy_jacobian_integration as frozen
from . import dormancy_progress_integration as progress

Census = frozen.Census


class _Coordinates(frozen._Coordinates):
    def __init__(self, initial, p):
        super().__init__(initial, p)
        self.chemical_conditioning_requests = []
        self._pending_chemical_causes = {}

    def condition_chemicals(self, state, time, indices, kind):
        for patch in indices:
            cause = self._pending_chemical_causes.pop(patch, None)
            size = len(self.chemical_events)
            selected = cause["chart_kind"] if cause is not None else kind
            super().condition_chemicals(state, time, [patch], selected)
            if cause is not None:
                cause["accepted_chart_conversion_applied"] = len(self.chemical_events) > size
                if len(self.chemical_events) > size:
                    self.chemical_events[-1]["conditioning_cause"] = cause.copy()


def _primitive_values(state, coords):
    physical, _ = coords.decode(state)
    flux = frozen.model.fluxes(physical, coords.p, trial_extension=True)
    values = np.r_[frozen.model._rhs_from_fluxes(physical, coords.p, flux),
                   np.zeros(len(coords.groups))]
    for patch, on in enumerate(coords.acetate_positive):
        if on:
            values[6*patch+3] = 0.
    for k, group in enumerate(coords.groups):
        if not group["present"]:
            continue
        h = coords.allocations(state, group)[0]
        growth = np.array([flux["net_growth_yr"][j, group["guild"]]
                           if stage == 0 else -flux["dormant_loss_yr"]
                           for j, stage in group["nodes"]])
        z = state[coords.m+k]
        values[coords.m+k] = float(h@growth/sum(h))*(
            1. if z < -30 else np.logaddexp(0., z)/expit(z))
    return values, flux


def _finite_exp(log_value, time, patch, term):
    if log_value > np.log(np.finfo(float).max) or np.isnan(log_value):
        error = frozen._ChemicalConditioning([patch])
        error.chemical_cause = dict(
            kind="unrepresentable_chemical_newton_term", chart_kind="newton_derivative_chemical_chart", patch=int(patch),
            trial_time_yr=float(time), term=term, log_abs_term=float(log_value))
        raise error
    return float(np.exp(log_value)) if np.isfinite(log_value) else 0.


def _coefficients(flux):
    return np.array([[local["acetate_production_per_gdw_yr"],
                      local["k_rec_yr"]+local["k_other_yr"]]
                     if local is not None else [0., 0.] for local in flux["local"]])


def coordinate_jacobian(time, state, coords):
    """Newton matrix with exact allocation dependence in positive chemical rows."""
    cache = {}

    def primitive_values(value, coordinates):
        result = _primitive_values(value, coordinates)
        cache[value.tobytes()] = result
        return result

    namespace = frozen.coordinate_jacobian.__globals__.copy()
    namespace["_matrix_values"] = primitive_values
    allocation_matrix = FunctionType(frozen.coordinate_jacobian.__code__, namespace)
    matrix = allocation_matrix(time, state, coords)
    _, flux = cache[state.tobytes()]
    center = _coefficients(flux)
    gradients = np.zeros((coords.p.n_patches, 2, len(state)))
    stage_indices = set(int(i) for group in coords.groups for i in group["indices"])
    # These are the frozen matrix's perturbations; reuse its cached fluxes.
    for index in range(len(state)):
        root = index < coords.m and coords.stage_positive[index]
        step = (1e-6*abs(state[index]) if root else
                1e-6*max(abs(state[index]), 1e-8 if index in stage_indices else 1.))
        if step == 0.:
            step = np.nextafter(0., 1.)
        plus, minus = state.copy(), state.copy()
        plus[index] += step
        minus[index] -= step
        if ((index in stage_indices and not root and minus[index] < 0)
                or (root and abs(state[index]) <= step)):
            gradients[..., index] = (_coefficients(cache[plus.tobytes()][1])-center)/(plus[index]-state[index])
        else:
            gradients[..., index] = (_coefficients(cache[plus.tobytes()][1])
                                      - _coefficients(cache[minus.tobytes()][1]))/(plus[index]-minus[index])
    stages = coords.decode(state)[1]
    for patch, on in enumerate(coords.acetate_positive):
        if not on:
            continue
        chemical = 6*patch+3
        zc = state[chemical]
        log_denominator = np.log(frozen.old.ACETATE_SCALE)-np.logaddexp(0., -zc)
        coefficient, loss = center[patch]
        log_biomass = stages[patch, 0, 0]
        log_source = (np.log(coefficient)+log_biomass-log_denominator
                      if coefficient > 0 and np.isfinite(log_biomass) else -np.inf)
        source = _finite_exp(log_source, time, patch, "chemical_source")
        factor = 1. if zc < -30 else np.logaddexp(0., zc)/expit(zc)
        row = -factor*gradients[patch, 1].copy()
        if np.isfinite(log_biomass):
            for index, value in enumerate(gradients[patch, 0]):
                if value:
                    row[index] += np.sign(value)*_finite_exp(
                        log_biomass-log_denominator+np.log(abs(value)),
                        time, patch, f"coefficient_gradient[{index}]")
        for k, group in enumerate(coords.groups):
            if (group["guild"] != 0 or not group["present"]
                    or (patch, 0) not in group["nodes"]):
                continue
            h = coords.allocations(state, group)[0]
            normalizer = float(sum(h))
            position = group["nodes"].index((patch, 0))
            active = int(group["indices"][position])
            for index in group["indices"]:
                if index != active:
                    derivative = 2*state[index] if coords.stage_positive[index] else 1.
                    row[index] -= source*derivative/normalizer
            total = state[coords.m+k]
            total_factor = 1. if total < -30 else np.logaddexp(0., total)/expit(total)
            row[coords.m+k] += source/total_factor
            other = float(sum(h[a] for a in range(len(h)) if a != position))
            if coefficient > 0 and other > 0:
                own = (np.log(coefficient)+frozen.old._log_softplus(total)
                       - np.log(group["weights"][position])-log_denominator
                       + np.log(other)-2*np.log(normalizer))
                if coords.stage_positive[active]:
                    root = state[active]
                    if root:
                        row[active] += np.sign(root)*_finite_exp(
                            own+np.log(2.)+np.log(abs(root)), time, patch, "own_root_gradient")
                else:
                    row[active] += _finite_exp(own, time, patch, "own_linear_gradient")
        row[chemical] -= source*(1-expit(zc))
        factor_derivative = 0. if zc < -30 else 1-factor*(1-expit(zc))
        row[chemical] -= loss*factor_derivative
        if np.any(~np.isfinite(row)):
            error = frozen._ChemicalConditioning([patch])
            error.chemical_cause = dict(kind="unrepresentable_chemical_newton_row", chart_kind="newton_derivative_chemical_chart", patch=int(patch), trial_time_yr=float(time))
            raise error
        matrix[chemical] = row
    return matrix


class _ChemicalLSODA(progress._ProgressLSODA):
    def _initialize(self, time, state, bound, options):
        selected = options | {"jac": self._chemical_jacobian}
        return super()._initialize(time, state, bound, selected)

    def _record_request(self, error, accepted_time, accepted):
        cause = error.chemical_cause
        cause.update(accepted_time_yr=float(accepted_time),
                     accepted_coordinate_sha256=sha256(accepted.tobytes()).hexdigest())
        self.coordinates.chemical_conditioning_requests.append(cause)
        for patch in error.indices:
            self.coordinates._pending_chemical_causes[patch] = cause

    def _chemical_jacobian(self, time, state):
        try:
            return coordinate_jacobian(time, state, self.coordinates)
        except frozen._ChemicalConditioning as error:
            if hasattr(error, "chemical_cause"):
                self._record_request(error, getattr(self, "_guard_left", time),
                                     getattr(self, "_guard_start", state))
            raise

    def step(self):
        coords = self.coordinates
        candidates = [j for j, on in enumerate(coords.acetate_positive)
                      if on and not coords.stage_positive[6*j+1] and self.y[6*j+1] == 0.
                      and any(g["guild"] == 0 and g["present"] and (j, 0) in g["nodes"]
                              for g in coords.groups)]
        if candidates:
            physical, _ = coords.decode(self.y)
            flux = frozen.model.fluxes(physical, coords.p, trial_extension=True)
            for patch in candidates:
                for group in coords.groups:
                    if group["guild"] != 0 or not group["present"] or (patch, 0) not in group["nodes"]:
                        continue
                    h = coords.allocations(self.y, group)[0]
                    position = group["nodes"].index((patch, 0))
                    arrival = float(group["migration"][:, position]@h)
                    arrival += sum(flux["rho_yr"][patch, 0]*h[a]
                                   for a, node in enumerate(group["nodes"]) if node == (patch, 1))
                    if arrival > 0:
                        error = frozen._ChemicalConditioning([patch])
                        error.chemical_cause = dict(
                            kind="linear_producer_arrival", chart_kind="linear_producer_arrival_chemical_chart",
                            patch=int(patch), incoming_allocation_rate_yr=arrival)
                        self._record_request(error, self.t, self.y)
                        raise error
        return super().step()


def _copied(function, namespace):
    result = FunctionType(function.__code__, namespace, function.__name__,
                          function.__defaults__, function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


def integrate(y0, p, years, **kwargs):
    instances = []

    def coordinates(initial, parameters):
        value = _Coordinates(initial, parameters)
        instances.append(value)
        return value

    namespace = frozen.integrate.__globals__.copy()
    namespace["_Coordinates"] = coordinates
    accepted_driver = _copied(frozen.integrate, namespace)
    namespace = progress.integrate.__globals__.copy()
    namespace.update(qualified=SimpleNamespace(integrate=accepted_driver),
                     _ProgressLSODA=_ChemicalLSODA)
    function = _copied(progress.integrate, namespace)
    try:
        result = function(y0, p, years, **kwargs)
    except RuntimeError as error:
        error.chemical_conditioning_requests = [event for instance in instances
                                         for event in instance.chemical_conditioning_requests]
        raise
    result.metadata.update(
        base_numerical_variant=result.metadata["numerical_variant"],
        numerical_variant="analytic_dormancy_chemical_jacobian",
        chemical_conditioning_requests=[event for instance in instances
                                 for event in instance.chemical_conditioning_requests])
    return result


def integrate_finite(y0, p, years, process=Census(), **kwargs):
    return integrate(y0, p, years, census=process, **kwargs)
