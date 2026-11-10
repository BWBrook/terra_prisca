"""A tolerance-scaled dense budget on certified macroscopic terminal faces.

Only canonical one-cell/ten-year census pieces with one active habitat and one
present guild can use the broader interpolation budget. All other pieces use
the frozen Radau constructor exactly. Physical flow, tolerances, native states,
endpoint/domain checks and census rules are unchanged. The local dense-curve
certificate is not a rare-lineage or exact-flow error guarantee.
"""

from fractions import Fraction
from types import FunctionType

import numpy as np

from . import dormancy_conditioned_integration as conditioned

upstream = conditioned.upstream
stage = conditioned.stage
Census = conditioned.Census
ROOT_ABSOLUTE_TOLERANCE = conditioned.ROOT_ABSOLUTE_TOLERANCE
MINIMUM_TOTAL_CELLS = 10**16
MINIMUM_ENCODED_TOTAL = -16
SOFTPLUS_LOWER_DENOMINATOR = 2**25
BUDGET_KIND = 'frozen_root_atol_squared_certified_macro_terminal_face'


class _Coordinates(conditioned._Coordinates):
    def __init__(self, initial, p):
        super().__init__(initial, p)
        self.terminal_census_active = False
        self.terminal_dense_stats = dict(pieces=0, broader_budget_pieces=0,
            strict_budget_pieces=0, broader_budget_extensions=0,
            minimum_encoded_total_lower=None, minimum_total_cells_lower=None,
            fallback_reasons={})


def _terminal_certificate(native, native_end, coords):
    if not coords.terminal_census_active:
        return None, 'actual_census_absent'
    if np.count_nonzero(coords.p.weights > 0) != 1:
        return None, 'multiple_active_habitats'
    present = [(k, group) for k, group in enumerate(coords.groups) if group['present']]
    if len(present) != 1:
        return None, 'present_guild_count'
    process = coords.dense_census
    if process.minimum_cells != 1. or process.census_yr != 10.:
        return None, 'noncanonical_census'
    arrays = (native.y_old, native.Q, native_end)
    if any(np.any(~np.isfinite(value)) for value in arrays):
        return None, 'nonfinite_native_arrays'
    k, group = present[0]
    index = coords.m+k
    polynomial = tuple([upstream._f(native.y_old[index]), *map(upstream._f, native.Q[index])])
    theta = np.zeros(native.Q.shape[1]+1)
    theta[0] = native.y_old[index]
    for power in range(1, native.Q.shape[1]+1):
        for j in range(power+1):
            theta[j] += upstream.comb(power, j)*native.Q[index, power-1]
    error = upstream._evaluation_error(polynomial, theta, native_end[index])
    lower = polynomial[0]-upstream._l1(polynomial[1:])-error
    if lower < MINIMUM_ENCODED_TOTAL:
        return None, 'encoded_total_lower'
    volume_fraction = sum((upstream._f(coords.p.weights[j])
                           for j, s in group['nodes'] if s == 0), Fraction(0))
    conversion = (upstream._f(coords.p.coupled.habitat_l_cm2)*upstream._f(process.surface_cm2)
                  /upstream._f(process.cell_mass_gdw)*volume_fraction)
    mass_lower = upstream._f(stage.SCALE)/SOFTPLUS_LOWER_DENOMINATOR
    cells_lower = mass_lower*conversion
    if cells_lower < MINIMUM_TOTAL_CELLS:
        return None, 'total_cells_lower'
    return dict(total_coordinate_index=index,
        encoded_total_lower=upstream._lower(lower), encoded_total_lower_exact=upstream._ratio(lower),
        encoded_total_polynomial_exact=[upstream._ratio(x) for x in polynomial],
        encoded_total_rounding_margin_exact=upstream._ratio(error),
        biomass_lower_exact=upstream._ratio(mass_lower),
        volume_conversion_exact=upstream._ratio(conversion),
        volume_fraction_exact=upstream._ratio(volume_fraction),
        total_cells_lower=upstream._lower(cells_lower), total_cells_lower_exact=upstream._ratio(cells_lower),
        active_habitats=1, present_guilds=1, minimum_cells=1., census_yr=10.,
        minimum_required_cells=MINIMUM_TOTAL_CELLS,
        softplus_lower_bound='z>=-16 implies softplus(z)>=1/2^25: log(1+x)>=x/2 for0<=x<=1 and exp(16)<2^24.',
        biomass_scale=stage.SCALE, habitat_l_cm2=coords.p.coupled.habitat_l_cm2,
        surface_cm2=process.surface_cm2, cell_mass_gdw=process.cell_mass_gdw), None


_CAP_GLOBALS = upstream._Dense.__init__.__globals__.copy()
_CAP_GLOBALS['_EPS'] = Fraction.from_float(ROOT_ABSOLUTE_TOLERANCE)
_CHANGED_GLOBALS = tuple(key for key in _CAP_GLOBALS
    if _CAP_GLOBALS[key] is not upstream._Dense.__init__.__globals__[key])
if _CHANGED_GLOBALS != ('_EPS',):
    raise RuntimeError('Terminal dense budget must change only the private cap constant')
_CAP_CONSTRUCTOR = FunctionType(upstream._Dense.__init__.__code__, _CAP_GLOBALS,
    upstream._Dense.__init__.__name__, upstream._Dense.__init__.__defaults__,
    upstream._Dense.__init__.__closure__)


class _Dense(upstream._Dense):
    def __init__(self, native, native_end, coords, atol):
        certificate, reason = _terminal_certificate(native, native_end, coords)
        stats = coords.terminal_dense_stats
        stats['pieces'] += 1
        if certificate is None:
            stats['strict_budget_pieces'] += 1
            stats['fallback_reasons'][reason] = stats['fallback_reasons'].get(reason, 0)+1
            super().__init__(native, native_end, coords, atol)
            return
        stats['broader_budget_pieces'] += 1
        for key, value in [('minimum_encoded_total_lower', certificate['encoded_total_lower']),
                           ('minimum_total_cells_lower', certificate['total_cells_lower'])]:
            prior = stats[key]
            stats[key] = value if prior is None else min(prior, value)
        before = len(coords.positive_dense_stats['extensions'])
        _CAP_CONSTRUCTOR(self, native, native_end, coords, atol)
        for event in coords.positive_dense_stats['extensions'][before:]:
            event['dense_budget_kind'] = BUDGET_KIND
            event['terminal_macro_certificate'] = certificate
            for component in event['components']:
                component['root_atol_squared_budget'] = component.pop('epsilon_squared')
                component['machine_epsilon_squared'] = float(upstream._EPS*upstream._EPS)
                component['dense_budget_kind'] = BUDGET_KIND
            stats['broader_budget_extensions'] += 1


_BACKEND_GLOBALS = upstream._Radau._dense_output_impl.__globals__.copy()
_BACKEND_GLOBALS['_Dense'] = _Dense


class _Radau(conditioned._Radau):
    _dense_output_impl = FunctionType(upstream._Radau._dense_output_impl.__code__, _BACKEND_GLOBALS,
        upstream._Radau._dense_output_impl.__name__, upstream._Radau._dense_output_impl.__defaults__,
        upstream._Radau._dense_output_impl.__closure__)


def integrate(y0, p, years, **kwargs):
    instances = []

    def coordinates(initial, parameters):
        value = _Coordinates(initial, parameters)
        value.terminal_census_active = kwargs.get('census') is not None
        instances.append(value)
        return value

    namespace = conditioned.integrate.__globals__.copy()
    namespace.update(_Coordinates=coordinates, _Radau=_Radau)
    function = stage.chemical._copied(conditioned.integrate, namespace)
    try:
        result = function(y0, p, years, **kwargs)
    except RuntimeError as error:
        error.terminal_dense_stats = [c.terminal_dense_stats for c in instances]
        raise
    original_scope = result.metadata['positive_dense_scope']
    marker = 'defect<=min(component_atol,epsilon**2)'
    if original_scope.count(marker) != 1:
        raise RuntimeError('Frozen positive-dense scope changed')
    scope = original_scope.replace(marker,
        'defect<=min(component_atol,root_atol**2) on certified macro terminal pieces; otherwise min(component_atol,machine_epsilon**2)')
    result.metadata.update(numerical_variant='radau_dormancy_terminal_dense_budget',
        upstream_numerical_variant='radau_dormancy_tolerance_conditioning',
        terminal_dense_stats=[c.terminal_dense_stats for c in instances],
        terminal_dense_constants=dict(frozen_root_absolute_tolerance=ROOT_ABSOLUTE_TOLERANCE,
            broader_dense_budget=float(_CAP_GLOBALS['_EPS']**2),
            original_machine_epsilon_squared=float(upstream._EPS**2),
            unchanged_unit_roundoff=float(upstream._UNIT),
            minimum_encoded_total=MINIMUM_ENCODED_TOTAL,
            softplus_lower_denominator=SOFTPLUS_LOWER_DENOMINATOR,
            minimum_total_cells=MINIMUM_TOTAL_CELLS,
            changed_private_constructor_globals=list(_CHANGED_GLOBALS)),
        terminal_dense_scope='Declared interpolation budget on canonical1-cell/10-year census pieces only: exactly one active habitat, exactly one present guild, finite native arrays and a whole-piece encoded-total/volume certificate>=1e16 cells. Every other piece invokes the original09be dense constructor exactly, including all uncensored, two-guild and uncertified rare pieces. Actual machine roundoff bounds, physical RHS, tolerances, native endpoints, domain prefix and census remain unchanged. No rare-lineage, exact-flow or global trajectory error guarantee.',
        upstream_terminal_positive_dense_scope=original_scope,
        positive_dense_scope=scope)
    return result


def integrate_finite(y0, p, years, process=Census(), **kwargs):
    return integrate(y0, p, years, census=process, **kwargs)
