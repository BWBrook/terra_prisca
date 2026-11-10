"""Independent forward branching simulation in a recorded rare-guild environment.

Input NPZ: times (T,), birth/death (T,H), migration (H,H), log_counts
(T,H), all rates in years. Run with --input PATH. No climate or population
equations are integrated here. Birth/death steps use exact homogeneous
linear-branching transitions; exact CTMC migration half steps give Strang
splitting. Halving the maximum step checks the approximation to the recorded,
linearly interpolated time-varying environment.
"""

from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
from statistics import NormalDist

import numpy as np
from scipy.linalg import expm
from scipy.optimize import brentq
from scipy.special import logsumexp


def transition_parameters(birth, death, years):
    """Single ancestor: survival and positive-geometric parameter."""
    if birth < 0 or death < 0 or years < 0:
        raise ValueError("Rates and duration must be nonnegative")
    if birth == 0:
        return np.exp(-death * years), 1.
    if death == 0:
        return 1., np.exp(-birth * years)
    if birth == death:
        value = 1 / (1 + birth * years)
        return value, value
    growth = birth - death
    increment = np.expm1(growth * years)
    denominator = growth + birth * increment
    geometric = growth / denominator
    survival = geometric * np.exp(growth * years)
    if not (0 <= survival <= 1 and 0 < geometric <= 1):
        raise FloatingPointError("Invalid exact birth/death transition")
    return survival, geometric


def birth_death_step(counts, birth, death, years, rng):
    result = np.zeros_like(counts)
    for j in range(counts.shape[1]):
        survival, geometric = transition_parameters(float(birth[j]), float(death[j]), years)
        lines = rng.binomial(counts[:, j], survival)
        positive = lines > 0
        result[positive, j] = lines[positive] + rng.negative_binomial(lines[positive], geometric)
    return result


def migration_matrix(migration, years):
    migration = np.asarray(migration, dtype=float)
    if migration.ndim != 2 or migration.shape[0] != migration.shape[1]:
        raise ValueError("Migration must be square")
    if np.any(migration < 0) or np.any(np.diag(migration) != 0):
        raise ValueError("Migration has nonnegative off-diagonal rates and zero diagonal")
    matrix = expm((migration - np.diag(migration.sum(axis=1))) * years)
    if np.any(matrix < 0) or not np.allclose(matrix.sum(axis=1), 1, atol=1e-13):
        raise FloatingPointError("Invalid migration transition matrix")
    return matrix


def migration_step(counts, matrix, rng):
    result = np.zeros_like(counts)
    for source, probabilities in enumerate(matrix):
        remaining = counts[:, source].copy()
        remainder_probability = 1.
        for target in range(counts.shape[1] - 1):
            chance = probabilities[target] / remainder_probability if remainder_probability else 0.
            if chance < -1e-14 or chance > 1 + 1e-14:
                raise FloatingPointError("Invalid conditional migration probability")
            # Only floating-point cancellation in conditional probabilities is rounded.
            selected = rng.binomial(remaining, min(1., max(0., chance)))
            result[:, target] += selected
            remaining -= selected
            remainder_probability -= probabilities[target]
        result[:, -1] += remaining
    if not np.array_equal(result.sum(axis=1), counts.sum(axis=1)):
        raise AssertionError("Migration did not conserve cell counts")
    return result


def interpolate(time, times, values):
    return np.array([np.interp(time, times, values[:, j]) for j in range(values.shape[1])])


def simulate(times, birth, death, migration, initial, maximum_step, replicates, seed, poisson=True):
    if maximum_step <= 0 or replicates <= 0:
        raise ValueError("Positive step and replicate count required")
    rng = np.random.default_rng(seed)
    if poisson:
        counts = rng.poisson(np.broadcast_to(initial, (replicates, initial.size)))
    else:
        counts = np.broadcast_to(initial.astype(np.int64), (replicates, initial.size)).copy()
    initial_totals = counts.sum(axis=1)
    intervals = 0
    for left, right in zip(times[:-1], times[1:]):
        subdivisions = int(np.ceil((right - left) / maximum_step))
        dt = (right - left) / subdivisions
        move = migration_matrix(migration, dt / 2)
        for k in range(subdivisions):
            midpoint = left + (k + .5) * dt
            b = interpolate(midpoint, times, birth)
            delta = interpolate(midpoint, times, death)
            counts = migration_step(counts, move, rng)
            counts = birth_death_step(counts, b, delta, dt, rng)
            counts = migration_step(counts, move, rng)
            intervals += 1
    return dict(survivors=int(np.count_nonzero(counts.sum(axis=1))), replicates=replicates,
                seed=seed, maximum_step_yr=maximum_step, time_intervals=intervals,
                initialization="independent Poisson counts" if poisson else "fixed integer counts",
                mean_initial_cells=float(initial_totals.mean()),
                mean_terminal_cells=float(counts.sum(axis=1).mean()))


def wilson(successes, size, confidence=.99):
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    p = successes / size
    denominator = 1 + z * z / size
    middle = (p + z * z / (2 * size)) / denominator
    radius = z * np.sqrt(p * (1 - p) / size + z * z / (4 * size * size)) / denominator
    return [float(middle - radius), float(middle + radius)]


def subwindow(times, birth, death, log_counts, scale, target=1e5):
    log_total = logsumexp(log_counts, axis=1) + np.log(scale)
    crossing = np.flatnonzero((log_total[:-1] >= np.log(target)) & (log_total[1:] < np.log(target)))
    if not crossing.size:
        raise RuntimeError("Recorded window has no descending 1e5-cell crossing")
    index = int(crossing[0])
    start = brentq(lambda time: logsumexp(interpolate(time, times, log_counts)) + np.log(scale) - np.log(target),
                   times[index], times[index + 1], xtol=1e-10)
    new_times = np.r_[start, times[index + 1:]]
    new_birth = np.vstack([interpolate(start, times, birth), birth[index + 1:]])
    new_death = np.vstack([interpolate(start, times, death), death[index + 1:]])
    initial = np.exp(interpolate(start, times, log_counts) + np.log(scale))
    return new_times, new_birth, new_death, initial


def run(path, replicates=10000, steps=(.5, .25), seed=20261110):
    from terra_prisca.haze_world import branching
    from terra_prisca.haze_world.branching import backward_survival

    with np.load(path) as data:
        times, birth, death, migration, log_counts = (data[k] for k in ("times", "birth", "death", "migration", "log_counts"))
        raw_hash = str(data["source_raw_sha256"]) if "source_raw_sha256" in data else None
    if np.any(np.diff(times) <= 0) or birth.shape != death.shape or birth.shape != log_counts.shape:
        raise ValueError("Malformed recorded environment")
    full_logu = backward_survival(times, birth, death, migration)
    full_loglambda = float(logsumexp(log_counts[0] + full_logu))
    scale = float(np.exp(-full_loglambda))
    later_times, later_birth, later_death, initial = subwindow(times, birth, death, log_counts, scale)
    logu = backward_survival(later_times, later_birth, later_death, migration)
    loglambda = float(logsumexp(np.log(initial) + logu))
    poisson_probability = float(-np.expm1(-np.exp(loglambda)))
    integer = np.floor(initial).astype(np.int64)
    for j in np.argsort(initial - integer)[::-1][:int(round(initial.sum()) - integer.sum())]:
        integer[j] += 1
    u = np.exp(logu)
    occupied = integer > 0
    fixed_probability = float(-np.expm1(np.sum(integer[occupied] * np.log1p(-u[occupied]))))
    results = []
    for i, dt in enumerate(steps):
        observed = simulate(later_times, later_birth, later_death, migration, initial, dt,
                            replicates, seed + i, poisson=True)
        observed["predicted_probability"] = poisson_probability
        results.append(observed)
    observed = simulate(later_times, later_birth, later_death, migration, integer, min(steps),
                        replicates, seed + len(steps), poisson=False)
    observed["predicted_probability"] = fixed_probability
    results.append(observed)
    for observed in results:
        observed["observed_probability"] = observed["survivors"] / observed["replicates"]
        observed["wilson_99_interval"] = wilson(observed["survivors"], observed["replicates"])
        observed["prediction_in_interval"] = observed["wilson_99_interval"][0] <= observed["predicted_probability"] <= observed["wilson_99_interval"][1]
        observed["binomial_z"] = (observed["observed_probability"] - observed["predicted_probability"]) / np.sqrt(
            observed["predicted_probability"] * (1 - observed["predicted_probability"]) / replicates)
    convergence = []
    for a, b in zip(results[:-2], results[1:-1]):
        error = np.sqrt(sum(x["predicted_probability"] * (1 - x["predicted_probability"]) / x["replicates"] for x in (a, b)))
        convergence.append(dict(steps_yr=[a["maximum_step_yr"], b["maximum_step_yr"]],
            probability_difference=b["observed_probability"] - a["observed_probability"],
            monte_carlo_standard_error=error,
            difference_in_standard_errors=(b["observed_probability"] - a["observed_probability"]) / error))
    return dict(scope="Independent forward demographic process in the recorded deterministic environment; finite-time survival, not establishment or coupled stochastic climate",
        method="Exact homogeneous birth/death transitions with midpoint rates; Strang split exact CTMC migration; two step sizes and fixed/Poisson initial counts",
        input_sha256=sha256(path.read_bytes()).hexdigest(), checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        source_raw_sha256=raw_hash,
        backward_source_sha256=sha256(Path(branching.__file__).read_bytes()).hexdigest(), numpy_version=np.__version__,
        full_window_yr=[float(times[0]), float(times[-1])], full_window_log_lambda_reference=full_loglambda,
        scale_for_full_window_lambda_one=scale, full_window_scaled_probability=float(-np.expm1(-1.)),
        simulation_window_yr=[float(later_times[0]), float(later_times[-1])],
        initial_expected_cells_by_habitat=initial.tolist(), initial_integer_cells_by_habitat=integer.tolist(),
        later_window_poisson_probability=poisson_probability, later_window_fixed_probability=fixed_probability,
        change_from_later_poisson_initialization=poisson_probability - float(-np.expm1(-1.)),
        results=results, convergence=convergence,
        all_predictions_within_99_intervals=all(x["prediction_in_interval"] for x in results))


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_suffix(".json"))
    parser.add_argument("--replicates", type=int, default=10000)
    args = parser.parse_args()
    report = run(args.input, args.replicates)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: report[k] for k in ("scale_for_full_window_lambda_one", "later_window_poisson_probability", "all_predictions_within_99_intervals")}, indent=2))
    if not report["all_predictions_within_99_intervals"]:
        raise SystemExit("Monte Carlo mismatch: examine rates, discretization and sampling error")


if __name__ == "__main__":
    main()
