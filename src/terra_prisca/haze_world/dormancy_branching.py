"""Two-stage lineage survival in a recorded dormancy-model environment.

Types are interleaved active/dormant within each positive-area habitat.
Transition matrices use origin rows and destination columns. Probabilities
refer to any living descendant at the terminal time, not establishment.
"""

import numpy as np
from scipy.integrate import LSODA
from scipy.special import logsumexp

from . import branching as reference


def per_cell_rates(y, p, guild):
    from . import dormancy as model
    if guild not in (0, 1) or not p.base.base.enabled[guild]:
        raise ValueError("The target guild must be enabled")
    y = np.asarray(y, dtype=float)
    if y.shape != (p.state_size,) or np.any(~np.isfinite(y)) or np.any(y < 0):
        raise ValueError("Rates require finite nonnegative physical stocks")
    active, active_birth, active_death = reference.per_cell_rates(model.active_state(y, p), p.base, guild)
    f = model.fluxes(y, p)
    net = np.asarray(f["net_growth_yr"])[active, guild]
    n = 2*len(active)
    birth, death, transition = np.zeros(n), np.zeros(n), np.zeros((n, n))
    birth[::2], death[::2] = active_birth, active_death
    death[1::2] = f["dormant_loss_yr"]
    if not np.allclose(birth[::2]-death[::2], net, rtol=1e-10, atol=1e-10):
        raise ArithmeticError("Birth minus death differs from active net growth")
    for j, patch in enumerate(active):
        transition[2*j, 2*j+1] = f["sigma_yr"][patch, guild]
        transition[2*j+1, 2*j] = f["rho_yr"][patch, guild]
        for k, destination in enumerate(active):
            if k != j:
                rate = p.base.dispersal_yr*p.base.weights[destination]
                transition[2*j, 2*k] = transition[2*j+1, 2*k+1] = rate
    return active, birth, death, transition


def trajectory_rates(times, y, p, guild):
    times, y = np.asarray(times, dtype=float), np.asarray(y, dtype=float)
    if y.shape != (p.state_size, len(times)):
        raise ValueError("States must have shape (state_size, time)")
    samples = [per_cell_rates(y[:, i], p, guild) for i in range(len(times))]
    return samples[0][0], np.array([s[1] for s in samples]), np.array([s[2] for s in samples]), np.array([s[3] for s in samples])


def _components(transition):
    adjacent = np.any(transition > 0, axis=0)
    adjacent |= adjacent.T
    unseen = set(range(adjacent.shape[0])); groups = []
    while unseen:
        pending = [min(unseen)]; group = []
        while pending:
            j = pending.pop()
            if j not in unseen: continue
            unseen.remove(j); group.append(j)
            pending.extend(k for k in np.flatnonzero(adjacent[j]) if k in unseen)
        groups.append(np.array(sorted(group), dtype=int))
    return groups


class _RatioOverflow(ArithmeticError):
    pass


def _birth_death_step(logu, birth, death, duration):
    """Advance nonnegative extinction odds, then return log survival."""
    growth = birth-death
    z = -growth*duration
    integral = np.full_like(z, np.log(duration))
    positive = z > 1e-7
    negative = z < -1e-7
    small = ~(positive | negative)
    integral[positive] = z[positive]+np.log(-np.expm1(-z[positive]))-np.log(-growth[positive])
    integral[negative] = np.log(-np.expm1(z[negative]))-np.log(growth[negative])
    integral[small] += np.log1p(z[small]/2+z[small]**2/6+z[small]**3/24)
    log_death = np.full_like(death, -np.inf)
    np.log(death, out=log_death, where=death > 0)
    with np.errstate(divide="ignore"):
        log_odds = -logu+np.log(-np.expm1(logu))
    return -np.logaddexp(0., np.logaddexp(log_odds+z, log_death+integral))


def _positive_step(logu, time, duration, interpolate):
    birth, death, _ = interpolate(time-duration/2)
    value = _birth_death_step(logu, birth, death, duration/2)
    kernel = _timevarying_kernel(interpolate(time)[2], interpolate(time-duration)[2], duration)
    log_kernel = np.full_like(kernel, -np.inf)
    np.log(kernel, out=log_kernel, where=kernel > 0)
    deficit = (kernel@(-np.expm1(value)))/kernel.sum(axis=1)
    near_one = deficit < .5
    mixed = np.empty_like(value)
    mixed[near_one] = np.log1p(-deficit[near_one])
    mixed[~near_one] = (logsumexp(log_kernel[~near_one]+value[None, :], axis=1)
                        -logsumexp(log_kernel[~near_one], axis=1))
    value = mixed
    return _birth_death_step(value, birth, death, duration/2)


def _timevarying_kernel(start, end, duration):
    """Positive time-ordered CTMC kernel for an affine rate matrix.

    Uniformization jump matrices are affine Bernstein polynomials. Their
    ordered integrals retain nonnegative Bernstein coefficients, including
    the leading coefficients of newly opened multi-hop paths. The simple-path
    floor preserves reachability; absolute tail truncation is not an
    entrywise relative-error bound.
    """
    if np.array_equal(start, end): return _conversion_kernel(start, duration)
    exit_start, exit_end = start.sum(axis=1), end.sum(axis=1)
    rate = float(max(max(exit_start), max(exit_end)))
    identity = np.eye(len(start))
    if rate == 0: return identity
    mean = rate*duration
    if mean > 1+8*np.finfo(float).eps:
        raise ArithmeticError("Time-ordered conversion bootstrap requires a shorter interval")
    first, last = start/rate, end/rate
    np.fill_diagonal(first, 1-exit_start/rate)
    np.fill_diagonal(last, 1-exit_end/rate)
    coefficients = identity[None, :, :]
    weight = np.exp(-mean); kernel = weight*identity
    for k in range(1, 101):
        degree = len(coefficients)-1
        product = np.zeros((degree+2, len(start), len(start)))
        for j in range(degree+2):
            if j <= degree: product[j] += (degree+1-j)/(degree+1)*(first@coefficients[j])
            if j: product[j] += j/(degree+1)*(last@coefficients[j-1])
        coefficients = np.concatenate((np.zeros_like(identity)[None, :, :],
                                        k/(degree+2)*np.cumsum(product, axis=0)))
        weight *= mean/k
        kernel += weight*coefficients[-1]
        if k >= len(start)-1 and weight < np.finfo(float).eps*1e-3: break
    else: raise ArithmeticError("Time-ordered conversion uniformization failed")
    kernel /= kernel.sum(axis=1, keepdims=True)
    return kernel


def _conversion_kernel(transition, duration):
    """Positive CTMC exponential by scaled uniformization and squaring."""
    exit_rate = transition.sum(axis=1)
    rate = float(max(exit_rate))
    identity = np.eye(len(exit_rate))
    if rate == 0: return identity
    product = rate*duration
    if not np.isfinite(product): raise ArithmeticError("Conversion time scale exceeds floating range")
    squares = max(0, int(np.ceil(np.log2(product)))) if product else 0
    mean = np.ldexp(product, -squares)
    jump = transition/rate
    np.fill_diagonal(jump, 1-exit_rate/rate)
    power = identity.copy(); weight = np.exp(-mean); kernel = weight*identity
    target = np.ldexp(np.finfo(float).eps*1e-3, -squares)
    for k in range(1, 101):
        power = power@jump; weight *= mean/k; kernel += weight*power
        if k >= len(transition)-1 and weight < target: break
    else: raise ArithmeticError("Conversion uniformization failed to converge")
    # Row normalization enforces the known stochastic invariant after roundoff;
    # the Poisson truncation tail is below scaled machine precision.
    kernel /= kernel.sum(axis=1, keepdims=True)
    for _ in range(squares):
        kernel = kernel@kernel
        kernel /= kernel.sum(axis=1, keepdims=True)
    return kernel


def _backward_interval(start, duration):
    endpoint = float(start-duration)
    if start-endpoint > duration:
        endpoint = float(np.nextafter(endpoint, start))
    actual = start-endpoint
    if actual <= 0:
        raise ArithmeticError("Conversion probability refinement lost time resolution")
    return endpoint, actual


def _local_rates(times, arrays, knot, start):
    width = times[knot+1]-times[knot]
    distance_left, distance_right = start-times[knot], times[knot+1]-start

    def interpolate(offset):
        left_weight = (distance_right-offset)/width
        right_weight = (distance_left+offset)/width
        return tuple(left_weight*a[knot]+right_weight*a[knot+1] for a in arrays)

    return interpolate


def _dynamic_survival(times, birth, death, transition, rtol, atol, max_step):
    n = birth.shape[1]

    def interpolate(time):
        k = min(max(int(np.searchsorted(times, time))-1, 0), len(times)-2)
        fraction = min(max((time-times[k])/(times[k+1]-times[k]), 0.), 1.)
        return tuple(a[k]+fraction*(a[k+1]-a[k]) for a in (birth, death, transition))

    def rhs(time, logu):
        b, delta, q = interpolate(time)
        differences = logu[None, :]-logu[:, None]
        positive = q > 0
        if np.any(differences[positive] > 700.) or np.any(logu > 700.):
            raise _RatioOverflow("A conversion-opening trial exceeds log-ratio range")
        coupled = np.zeros_like(q)
        coupled[positive] = -q[positive]*np.expm1(differences[positive])
        return b*np.expm1(logu)+delta+coupled.sum(axis=1)

    t0, terminal = float(times[0]), float(times[-1])
    state = np.zeros(n)
    solver = LSODA(rhs, terminal, state, t0, rtol=rtol, atol=atol, max_step=max_step)
    recorded_t, recorded_y = [terminal], [state.copy()]
    evaluations, repairs = 0, 0
    while solver.status == "running":
        start, accepted = float(solver.t), solver.y.copy()
        try:
            message = solver.step()
        except _RatioOverflow:
            evaluations += solver.nfev
            knot = max(int(np.searchsorted(times, start, side="left"))-1, 0)
            duration = min(max_step, start-times[knot], start-t0)
            endpoint_rates = (interpolate(start)[2], interpolate(times[knot])[2])
            rate = max(float(max(q.sum(axis=1))) for q in endpoint_rates)
            if rate: duration = min(duration, 1/rate)
            local = _local_rates(times, (birth, death, transition), knot, start)
            for attempt in range(30):
                next_time, duration = _backward_interval(start, duration)
                coarse = _positive_step(accepted, 0., duration, local)
                half = _positive_step(accepted, 0., duration/2, local)
                fine = _positive_step(half, -duration/2, duration/2, local)
                error = np.max(abs(fine-coarse)/(atol+rtol*np.maximum(1., abs(fine))))
                if error <= 1. and np.all(fine <= 0): break
                duration /= 2
            else:
                raise ArithmeticError("Cannot resolve conversion-opening probability step")
            repairs += 1
            recorded_t.append(next_time); recorded_y.append(fine.copy())
            if next_time <= t0:
                solver = None
                break
            solver = LSODA(rhs, next_time, fine, t0, rtol=rtol, atol=atol,
                           max_step=max_step, first_step=min(duration, next_time-t0))
            continue
        if solver.status == "failed":
            raise ArithmeticError("Dormancy branching integration failed: "+str(message))
        if np.any(~np.isfinite(solver.y)) or np.any(solver.y > 0):
            raise ArithmeticError("Accepted survival probability left [0,1]")
        recorded_t.append(float(solver.t)); recorded_y.append(solver.y.copy())
    evaluations += 0 if solver is None else solver.nfev
    result = reference.SurvivalSolution(np.array(recorded_t), np.array(recorded_y).T, evaluations)
    result.conversion_opening_steps = repairs
    return result


def backward_survival(times, birth, death, transitions, *, rtol=1e-9, atol=1e-11,
                      max_step=np.inf, return_solution=False):
    """Log survival through linearly interpolated rates and conversions.

    Birth/death shape is (time,type); transitions are (time,type,type), or a
    constant (type,type) origin-row matrix with zero diagonal. Disconnected
    constant blocks use the frozen reference solver. This makes zero-switch
    active probabilities exactly reproduce that solver, without inactive
    dormant dimensions altering adaptive error control.
    """
    times, birth, death = (np.asarray(v, dtype=float) for v in (times, birth, death))
    if times.ndim != 1 or len(times) < 2 or np.any(~np.isfinite(times)) or np.any(np.diff(times) <= 0):
        raise ValueError("Provide finite strictly increasing times")
    if birth.ndim != 2 or birth.shape[0] != len(times) or death.shape != birth.shape or birth.shape[1] < 1:
        raise ValueError("Birth/death arrays must have shape (time,type)")
    n = birth.shape[1]
    transitions = np.asarray(transitions, dtype=float)
    if transitions.shape == (n, n): transitions = np.broadcast_to(transitions, (len(times), n, n))
    if transitions.shape != (len(times), n, n) or np.any(np.diagonal(transitions, axis1=1, axis2=2) != 0):
        raise ValueError("Transitions require matching type dimensions and a zero diagonal")
    if any(np.any(~np.isfinite(a)) or np.any(a < 0) for a in (birth, death, transitions)):
        raise ValueError("Rates must be finite and nonnegative")
    if np.isnan(max_step) or max_step <= 0 or min(rtol, atol) <= 0:
        raise ValueError("Integration tolerances and maximum step must be positive")
    solutions = []
    for group in _components(transitions):
        q = transitions[:, group[:, None], group]
        b, d = birth[:, group], death[:, group]
        if np.all(d == 0):
            result = reference.SurvivalSolution(times[::-1].copy(), np.zeros((len(group), len(times))), 0)
        elif np.all(q == q[0]):
            result = reference.backward_survival(times, b, d, q[0], rtol=rtol, atol=atol,
                max_step=max_step, return_solution=True)
        else:
            result = _dynamic_survival(times, b, d, q, rtol, atol, max_step)
        solutions.append((group, result))
    if not return_solution:
        initial = np.empty(n)
        for group, result in solutions: initial[group] = result.initial_log_survival
        return initial
    combined_times = np.unique(np.concatenate([r.times for g, r in solutions]))[::-1]
    logs = np.empty((n, len(combined_times)))
    for group, result in solutions:
        for i, target in enumerate(group):
            logs[target] = np.interp(combined_times[::-1], result.times[::-1], result.log_survival[i, ::-1])[::-1]
    output = reference.SurvivalSolution(combined_times, logs, sum(r.evaluations for g, r in solutions))
    output.conversion_opening_steps = sum(getattr(r, "conversion_opening_steps", 0) for g, r in solutions)
    return output
