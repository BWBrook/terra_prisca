"""Kotsyurbenko et al. (2001) uptake benchmark, separate from climate coupling.

uv run python -m terra_prisca.haze_world.hydrogen_uptake [output_directory]
Unknown cessation thresholds remain explicit inputs or bounded intervals.
"""

import csv
from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
import sys

import numpy as np

BASE = Path(__file__).resolve().parents[3] / "models/haze_world"
ACETOGEN = "Acetobacterium bakii"
MSB = "methanogenic strain MSB"
MSP = "methanogenic strain MSP"
BIOMASS_MG_ML = {ACETOGEN: 0.18, MSB: 0.35, MSP: 0.33}
VOLUME_ML = 20.0


@dataclass(frozen=True)
class Kinetics:
    strain: str
    temperature_c: float
    vmax_nmol_h: float
    km_pa: float
    vmax_ci: float
    km_ci: float | None

    @property
    def mass_mg(self):
        return VOLUME_ML * BIOMASS_MG_ML[self.strain]


@lru_cache(maxsize=1)
def table() -> tuple[Kinetics, ...]:
    with (BASE / "evidence/kotsyurbenko2001_table2.csv").open() as handle:
        return tuple(Kinetics(r["strain"], float(r["temperature_C"]),
                              float(r["Vmax_nmol_h_for20mL"]), float(r["Km_Pa"]),
                              float(r["Vmax_95CI_halfwidth"]),
                              float(r["Km_95CI_halfwidth"]) if r["Km_95CI_halfwidth"] else None)
                     for r in csv.DictReader(handle))


def parameters(temperature_c: float, strain: str) -> Kinetics:
    for row in table():
        if row.temperature_c == temperature_c and row.strain == strain:
            return row
    raise ValueError("Only published strain/temperature pairs are available; no interpolation is assumed")


def uptake(pressure_pa, kinetics: Kinetics, threshold_pa: float, *, basis: str):
    """Positive H2 consumption: nmol/h per source culture, or nmol/h/mg dry mass.

    The paper shifts both numerator and denominator by the cessation threshold.
    A pool-depletion equation would use minus this positive rate.
    """
    pressure = np.asarray(pressure_pa, dtype=float)
    if np.any(~np.isfinite(pressure)) or np.any(pressure < 0) or not np.isfinite(threshold_pa) or threshold_pa < 0:
        raise ValueError("Pressures and threshold must be finite and nonnegative")
    if basis not in ("culture", "dry_mass"):
        raise ValueError("Specify culture or dry_mass rate basis")
    available = np.maximum(pressure - threshold_pa, 0.0)
    rate = kinetics.vmax_nmol_h * available / (kinetics.km_pa + available)
    return rate if basis == "culture" else rate / kinetics.mass_mg


def threshold_upper_bound(kinetics: Kinetics) -> float | None:
    """Coarse source-wide bounds, not recovered Fig. 1 values or confidence limits."""
    if kinetics.strain == ACETOGEN:
        return 200.0
    if kinetics.strain == MSP and kinetics.temperature_c <= 10:
        return None
    return 2.0


def rate_bounds(pressure_pa, kinetics: Kinetics, *, basis: str):
    upper = uptake(pressure_pa, kinetics, 0.0, basis=basis)
    threshold = threshold_upper_bound(kinetics)
    lower = np.zeros_like(upper) if threshold is None else uptake(pressure_pa, kinetics, threshold, basis=basis)
    return lower, upper


def competitiveness(first, second):
    """Positive favors first; both inactive is undefined, represented by NaN."""
    first, second = np.broadcast_arrays(first, second)
    total = first + second
    return np.divide(first - second, total, out=np.full(total.shape, np.nan), where=total > 0)


def competition_bounds(pressure_pa, first: Kinetics, second: Kinetics, *, basis: str):
    """Threshold-only bounds conditional on some uptake; both may be inactive
    when both rate lower bounds vanish. This does not identify inactive regions."""
    first_lo, first_hi = rate_bounds(pressure_pa, first, basis=basis)
    second_lo, second_hi = rate_bounds(pressure_pa, second, basis=basis)
    inactive = (first_hi == 0) & (second_hi == 0)
    lower = np.where(second_hi == 0, 1.0, competitiveness(first_lo, second_hi))
    upper = np.where(first_hi == 0, -1.0, competitiveness(first_hi, second_lo))
    return np.where(inactive, np.nan, lower), np.where(inactive, np.nan, upper)


def write_csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    capacities = [dict(temperature_c=p.temperature_c, strain=p.strain, mass_mg=p.mass_mg,
                       vmax_nmol_h_culture=p.vmax_nmol_h,
                       vmax_nmol_h_mg=p.vmax_nmol_h / p.mass_mg, km_pa=p.km_pa,
                       threshold_upper_pa=threshold_upper_bound(p)) for p in table()]
    write_csv(output / "uptake_capacities.csv", capacities)
    checkpoints = [(4, MSB, 40, -1), (4, MSB, 1000, 1),
                   (30, MSB, 500, -1), (30, MSB, 2000, 1), (15, MSP, 1000, 1)]
    fidelity = []
    for temperature, opponent, pressure, expected in checkpoints:
        for basis in ("culture", "dry_mass"):
            low, high = competition_bounds(pressure, parameters(temperature, ACETOGEN),
                                            parameters(temperature, opponent), basis=basis)
            favorable = low > 0 if expected == 1 else high < 0
            contrary = high < 0 if expected == 1 else low > 0
            fidelity.append(dict(temperature_c=temperature, opponent=opponent, pressure_pa=pressure,
                                 basis=basis, k_comp_lower=float(low), k_comp_upper=float(high),
                                 published_winner="acetogen" if expected == 1 else "methanogen",
                                 verdict="consistent" if favorable else "inconsistent" if contrary else "unresolved"))
    write_csv(output / "uptake_landmarks.csv", fidelity)
    grid = np.geomspace(0.1, 1e5, 201)
    curves = []
    for temperature in (4, 10, 15, 20, 25, 30):
        for opponent in (MSB, MSP):
            for basis in ("culture", "dry_mass"):
                low, high = competition_bounds(grid, parameters(temperature, ACETOGEN),
                                                parameters(temperature, opponent), basis=basis)
                curves.extend(dict(temperature_c=temperature, opponent=opponent, basis=basis,
                                   pressure_pa=float(p), k_comp_lower=float(a), k_comp_upper=float(b))
                              for p, a, b in zip(grid, low, high))
    write_csv(output / "uptake_bounds.csv", curves)
    (output / "uptake_status.json").write_text(json.dumps(dict(
        source_doi="10.1111/j.1574-6941.2001.tb00893.x", source_table_rows=len(table()),
        threshold_scope="Coarse published bounds only; Fig. 1 points unrecovered",
        uncertainty="Conditional on central Vmax, Km and biomass; intervals vary thresholds only, not confidence bands",
        figure_reproduction="Incomplete: thresholds missing and normalization discrepancy unresolved",
        climate_coupling=False), indent=2) + "\n")
    plot(output, grid)


def plot(output, grid):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(13, 4), constrained_layout=True)
    for name, label in ((ACETOGEN, "A. bakii"), (MSB, "MSB"), (MSP, "MSP")):
        points = [p for p in table() if p.strain == name]
        axes[0].plot([p.temperature_c for p in points], [p.vmax_nmol_h / p.mass_mg for p in points], "o-", label=label)
        axes[1].plot([p.temperature_c for p in points], [p.km_pa for p in points], "o-", label=label)
    axes[0].set(xlabel="Assay temperature (°C)", ylabel="Vmax (nmol H₂ h⁻¹ mg⁻¹)", title="Table 2: specific capacities")
    axes[1].set(xlabel="Assay temperature (°C)", ylabel="Km (Pa)", title="Table 2: half-saturation")
    axes[0].legend()
    for basis, color in (("culture", "#326782"), ("dry_mass", "#c37a28")):
        low, high = competition_bounds(grid, parameters(30, ACETOGEN), parameters(30, MSB), basis=basis)
        axes[2].fill_between(grid, low, high, alpha=0.28, color=color, label=basis.replace("_", " "))
    axes[2].axhline(0, color="0.3", linewidth=0.8)
    axes[2].axvline(500, color="0.3", linestyle=":", label="500 Pa audit point")
    axes[2].set(xscale="log", ylim=(-1.05, 1.05), xlabel="Hydrogen pressure (Pa)", ylabel="Kcomp: positive favors acetogen",
                title="30 °C: threshold-only envelopes")
    axes[2].legend(fontsize=8)
    fig.savefig(output / "hydrogen_uptake.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    run(Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "figures/hydrogen_uptake")
