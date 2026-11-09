"""Matched H2/CO2 chemostat/Pirt benchmark for Peters et al. (1998).

    uv run python -m terra_prisca.haze_world.woodii1998 [output_directory]

This benchmark fits no hydrogen affinity or saturation function. Source
parameters, a fit to rounded means, and the inferred rate anchor stay separate.
"""

import csv
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

BASE = Path(__file__).resolve().parents[3] / "models/haze_world"
SOURCE = BASE / "evidence/peters1998_chemostat.csv"
SOURCE_DOI = "10.1111/j.1574-6941.1998.tb00516.x"

Y_ACETATE_REPORTED = 7.7  # gDW per mol acetate produced
Y_H2_REPORTED = 1.7  # gDW per mol H2 consumed
MAINTENANCE_ACETATE = 0.40e-3  # mol acetate per gDW per h
MAINTENANCE_H2 = 4 * MAINTENANCE_ACETATE  # mol H2 per gDW per h
BIOMASS_ACETATE_EQUIVALENT = 0.0206  # mol acetate-equivalent per gDW
MU_MAX = 0.024  # h^-1, net biomass synthesis before external demographic loss


@dataclass(frozen=True)
class Observation:
    growth_h: float
    residual_h2_pa: float
    acetate_umol_l: float
    biomass_mgdw_l: float
    observed_yield_acetate: float

    @property
    def q_acetate(self):
        """Acetate production, mol gDW^-1 h^-1, from reported observed yield."""
        return self.growth_h / self.observed_yield_acetate

    @property
    def yield_from_concentrations(self):
        return self.biomass_mgdw_l * 1e-3 / (self.acetate_umol_l * 1e-6)


@dataclass(frozen=True)
class PirtFit:
    true_yield_acetate: float
    maintenance_acetate: float
    production_rmse: float


def observations() -> tuple[Observation, ...]:
    with SOURCE.open() as handle:
        return tuple(Observation(
            float(r["dilution_h^-1"]), float(r["residual_H2_Pa"]),
            float(r["acetate_uM"]), float(r["biomass_mgDW_L"]),
            float(r["observed_Y_acetate_gDW_mol"]),
        ) for r in csv.DictReader(handle))


def _growth_rates(growth_h):
    growth = np.asarray(growth_h, dtype=float)
    if np.any(~np.isfinite(growth)) or np.any(growth < 0):
        raise ValueError("Growth rates must be finite and nonnegative")
    return growth


def acetate_production(growth_h, *, true_yield=Y_ACETATE_REPORTED,
                       maintenance=MAINTENANCE_ACETATE):
    """Pirt production q_ac = mu/Y_ac,true + m_ac, mol gDW^-1 h^-1."""
    if not np.isfinite(true_yield) or true_yield <= 0 or not np.isfinite(maintenance) or maintenance < 0:
        raise ValueError("True yield must be positive and maintenance nonnegative")
    return _growth_rates(growth_h) / true_yield + maintenance


def observed_yield(growth_h, *, true_yield=Y_ACETATE_REPORTED,
                   maintenance=MAINTENANCE_ACETATE):
    """Observed gDW/mol acetate; undefined at mu = m = 0 (NaN)."""
    growth = _growth_rates(growth_h)
    production = acetate_production(growth, true_yield=true_yield, maintenance=maintenance)
    return np.divide(growth, production, out=np.full(growth.shape, np.nan), where=production > 0)


def hydrogen_yield_from_assimilation():
    """Derived H2 yield; it does not replace the source's rounded reported 1.7."""
    return 1 / (4 * (1 / Y_ACETATE_REPORTED + BIOMASS_ACETATE_EQUIVALENT))


def inferred_reference_uptake():
    """Inferred H2 rate scale, mol gDW^-1 h^-1, not a measured uptake qmax."""
    return MU_MAX / Y_H2_REPORTED + MAINTENANCE_H2


def fit_rounded_means() -> PirtFit:
    """OLS q_ac against mu, using four rounded source yields as reported.

    Equal weights in q space are a reconstruction choice. No measurement
    errors, confidence interval, or original fitting procedure are inferred.
    """
    rows = observations()
    growth = np.array([r.growth_h for r in rows])
    production = np.array([r.q_acetate for r in rows])
    slope, intercept = np.polyfit(growth, production, 1)
    residual = slope * growth + intercept - production
    return PirtFit(float(1 / slope), float(intercept), float(np.sqrt(np.mean(residual ** 2))))


def fidelity_rows():
    fit = fit_rounded_means()
    result = []
    for row in observations():
        source_q = float(acetate_production(row.growth_h))
        fit_q = float(acetate_production(row.growth_h, true_yield=fit.true_yield_acetate,
                                         maintenance=fit.maintenance_acetate))
        source_y = row.growth_h / source_q
        result.append(dict(
            growth_h=row.growth_h, residual_h2_pa=row.residual_h2_pa,
            reported_yield_acetate_gdw_mol=row.observed_yield_acetate,
            concentration_yield_acetate_gdw_mol=row.yield_from_concentrations,
            reported_yield_derived_q_acetate_mol_gdw_h=row.q_acetate,
            table2_q_acetate_mol_gdw_h=source_q,
            table2_q_residual_mol_gdw_h=source_q - row.q_acetate,
            table2_observed_yield_acetate_gdw_mol=source_y,
            table2_yield_residual_gdw_mol=source_y - row.observed_yield_acetate,
            rounded_fit_q_acetate_mol_gdw_h=fit_q,
            rounded_fit_q_residual_mol_gdw_h=fit_q - row.q_acetate,
        ))
    return result


def status():
    fit = fit_rounded_means()
    fidelity = fidelity_rows()
    q_residual = np.array([r["table2_q_residual_mol_gdw_h"] for r in fidelity])
    y_residual = np.array([r["table2_yield_residual_gdw_mol"] for r in fidelity])
    return dict(
        source_doi=SOURCE_DOI, source_csv_sha256=sha256(SOURCE.read_bytes()).hexdigest(),
        organism="Acetobacterium woodii DSM1030", temperature_c=30,
        substrate="H2/CO2", pH=7, source_observations=len(fidelity),
        table2_reported=dict(
            true_yield_acetate_gdw_mol=Y_ACETATE_REPORTED,
            true_yield_h2_gdw_mol=Y_H2_REPORTED,
            maintenance_acetate_mol_gdw_h=MAINTENANCE_ACETATE,
            maximum_growth_h=MU_MAX,
        ),
        derived=dict(
            maintenance_h2_mol_gdw_h=MAINTENANCE_H2,
            assimilation_acetate_equivalent_mol_gdw=BIOMASS_ACETATE_EQUIVALENT,
            assimilation_corrected_yield_h2_gdw_mol=hydrogen_yield_from_assimilation(),
            inferred_reference_h2_uptake_mol_gdw_h=inferred_reference_uptake(),
            reference_uptake_status="Inferred mu_max/Y_H2,reported + m_H2; not a directly measured qmax",
            exact_assimilation_reference_h2_uptake_mol_gdw_h=(
                MU_MAX / hydrogen_yield_from_assimilation() + MAINTENANCE_H2),
        ),
        rounded_means_fit=dict(
            procedure="Equal-weight OLS q_ac=mu/Y_ac,observed against mu; not the original fit",
            true_yield_acetate_gdw_mol=fit.true_yield_acetate,
            maintenance_acetate_mol_gdw_h=fit.maintenance_acetate,
            q_acetate_rmse_mol_gdw_h=fit.production_rmse,
            relative_yield_difference=fit.true_yield_acetate / Y_ACETATE_REPORTED - 1,
            relative_maintenance_difference=fit.maintenance_acetate / MAINTENANCE_ACETATE - 1,
        ),
        table2_fidelity=dict(
            q_acetate_rmse_mol_gdw_h=float(np.sqrt(np.mean(q_residual ** 2))),
            observed_yield_rmse_gdw_mol=float(np.sqrt(np.mean(y_residual ** 2))),
            observed_yield_max_abs_residual_gdw_mol=float(np.max(np.abs(y_residual))),
            residual_direction="prediction minus reported rounded mean",
        ),
        limitations=[
            "Four rounded means cannot reproduce the original unrounded fit or establish confidence limits",
            "Residual H2 is retained as source data; no Monod or cessation-pressure model is fitted",
            "The uptake reference is inferred from growth and Pirt parameters, not measured uptake saturation",
            "Mesophilic A.woodii parameters do not calibrate cold A.bakii physiology",
        ],
    )


def plot(output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = observations()
    fit = fit_rounded_means()
    growth = np.array([r.growth_h for r in rows])
    grid = np.linspace(0, MU_MAX, 240)
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 4.1), layout="constrained")
    axes[0].scatter(growth, [r.q_acetate * 1000 for r in rows],
                    color="black", zorder=3, label="Table 1 rounded means")
    axes[0].plot(grid, acetate_production(grid) * 1000, color="#28766c", label="Table 2 Pirt parameters")
    axes[0].plot(grid, acetate_production(grid, true_yield=fit.true_yield_acetate,
                                        maintenance=fit.maintenance_acetate) * 1000,
                 "--", color="#c27825", label="Refit of four rounded means")
    axes[0].set(xlabel="Growth rate μ (h⁻¹)", ylabel="Acetate production (mmol gDW⁻¹ h⁻¹)",
                title="a  Maintenance and growth demand", xlim=(0, MU_MAX))
    axes[0].legend(fontsize=8, loc="upper left")
    axes[1].scatter(growth, [r.observed_yield_acetate for r in rows], color="black", zorder=3)
    axes[1].plot(grid, observed_yield(grid), color="#28766c")
    axes[1].plot(grid, observed_yield(grid, true_yield=fit.true_yield_acetate,
                                    maintenance=fit.maintenance_acetate), "--", color="#c27825")
    axes[1].set(xlabel="Growth rate μ (h⁻¹)", ylabel="Observed yield (gDW mol⁻¹ acetate)",
                title="b  Observed yield approaches true yield", xlim=(0, MU_MAX), ylim=(0, 8.2))
    axes[1].axhline(Y_ACETATE_REPORTED, color="#28766c", linewidth=0.8, alpha=0.5)
    axes[1].text(0.001, 7.35, "True yield = 7.7", color="#28766c", fontsize=9)
    fig.suptitle("A. woodii, 30 °C: matched H₂/CO₂ chemostat benchmark", fontsize=12)
    fig.savefig(output / "woodii1998.png", dpi=180)
    plt.close(fig)


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    rows = fidelity_rows()
    with (output / "fidelity.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (output / "status.json").write_text(json.dumps(status(), indent=2) + "\n")
    plot(output)


if __name__ == "__main__":
    run(Path(sys.argv[1]) if len(sys.argv) > 1 else BASE / "figures/woodii1998")
