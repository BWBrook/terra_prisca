"""Diagnose five original 100kyr census profiles without changing status.

Run from the repository with
    uv run python models/haze_world/review/check_dormancy_late_stocks.py

No trajectories are integrated. Static active-reference roots are auxiliary
comparisons, not replacements for the dormancy stationarity criteria.
"""

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from terra_prisca.haze_world import dormancy as model
from terra_prisca.haze_world import dormancy_experiments as runner
from terra_prisca.haze_world import dormancy_starts
from terra_prisca.haze_world import habitat_equilibria
from terra_prisca.haze_world import turnover_survival


ROOT = Path(__file__).resolve().parents[3]
STEMS = (
    "dormancy_0052_census_t100000-8e362bac2ebab71b",
    "dormancy_0004_census_t100000-01678b047d5c4872",
    "dormancy_0000_census_t100000-8c482482983f6113",
    "dormancy_0008_census_t100000-99a293ad5c5f18c5",
    "dormancy_0016_census_t100000-b7f381a56a6733d8",
)


def diagnose(record, data):
    case = runner.Case(**record["protocol"]["case"])
    p = runner.parameters(case)
    t, ys = data["t"], data["y"]
    y = ys[:, -1]
    f, dy = model.fluxes(y, p), model.rhs(y, p)
    conversion = np.exp(data["metadata"]["global_log_cell_conversion"])
    cell_mass = runner.Census().cell_mass_gdw
    active = p.weights > 0
    floors = np.divide(1., conversion*p.weights, out=np.zeros(p.n_patches), where=active)
    minimum = np.r_[np.array([[1., v, v, 1e-9, v, v] for v in floors]).ravel(), .001]
    late = t >= case.years-20000.
    sample = ys[:, late]
    scale = np.maximum(np.mean(abs(sample), axis=1), minimum)
    spans = np.divide(np.ptp(sample, axis=1), scale, out=np.zeros(p.state_size), where=scale > 0)
    if not np.isclose(max(spans), record["summary"]["late_max_relative_span"], rtol=1e-10, atol=1e-14):
        raise RuntimeError("The reproduced late-stock statistic differs")
    names = [f"{name}:{q}" for name in p.patch_names
             for q in ("hydrogen_pa", "active_a", "active_m", "acetate_mol_l", "dormant_a", "dormant_m")]+["methane_ratio"]
    late_fluxes = [model.fluxes(ys[:, k], p) for k in np.flatnonzero(late)[::10]]
    stocks = []
    for k in np.argsort(spans)[::-1][:6]:
        j, component = divmod(int(k), 6)
        stock = dict(name=names[k], late_relative_span=float(spans[k]), final_value=float(y[k]),
            late_min=float(min(sample[k])), late_max=float(max(sample[k])), instantaneous_rhs=float(dy[k]))
        if k < p.state_size-1 and component in (1, 2, 4, 5):
            guild = component-1 if component < 3 else component-4
            total = y[p.biomass_indices[:, guild]]+y[p.dormant_indices[:, guild]]
            cells = float(y[k]*conversion*p.weights[j])
            stock.update(value_units="gDW/L", global_cells=cells, global_mass_gdw=cells*cell_mass,
                fraction_of_global_guild=float(p.weights[j]*y[k]/(p.weights@total)) if p.weights@total else 0.)
            if component >= 4:
                stock.update(entry_gdw_l_yr=float(f["sigma_yr"][j, guild]*y[p.biomass_indices[j, guild]]),
                    waking_gdw_l_yr=float(f["rho_yr"][j, guild]*y[k]),
                    dormant_death_gdw_l_yr=float(f["dormant_loss_yr"]*y[k]),
                    migration_gdw_l_yr=float(f["dormant_exchange_gdw_l_yr"][j, guild]),
                    active_net_growth_yr=float(f["net_growth_yr"][j, guild]),
                    sigma_yr=float(f["sigma_yr"][j, guild]), rho_yr=float(f["rho_yr"][j, guild]),
                    dormant_loss_yr=float(f["dormant_loss_yr"]),
                    instantaneous_relative_rhs=float(dy[k]/y[k]) if y[k] else None,
                    late_growth_range_yr=[float(min(v["net_growth_yr"][j, guild] for v in late_fluxes)),
                                          float(max(v["net_growth_yr"][j, guild] for v in late_fluxes))])
        stocks.append(stock)
    details = dict(native_summary=record["summary"], largest_stock_spans=stocks,
                   dormant_death_e_fold_yr=float(1/f["dormant_loss_yr"]))
    if case.case_id in ("dormancy_0052", "dormancy_0004"):
        details["shorter_windows"] = {}
        for width in (10000., 5000., 1000.):
            mask = t >= case.years-width
            details["shorter_windows"][str(int(width))] = {
                names[k]: dict(relative_span=float(np.ptp(ys[k, mask])/np.mean(ys[k, mask])),
                    sampled_endpoint_relative_trend_yr=float((y[k]-ys[k, np.flatnonzero(mask)[0]])/width/y[k]))
                for k in (5, 11)}
        details["fixed_environment_pressure_probes"] = []
        for shift in (0., 1e-9, -1e-9, 1e-8, -1e-8, 1e-7, -1e-7):
            probe = y.copy(); probe[0] += shift
            flux = model.fluxes(probe, p)
            details["fixed_environment_pressure_probes"].append(dict(delta_bulk_pressure_pa=shift,
                bulk_m_growth_yr=float(flux["net_growth_yr"][0, 1]), bulk_m_sigma_yr=float(flux["sigma_yr"][0, 1])))
    fit = habitat_equilibria.refine(model.active_state(y, p), p.base)
    if fit is not None:
        auxiliary = model.reference_state(np.asarray(fit["y"]), p)
        dormancy_starts.dormant_balance(auxiliary, p)
        residual = model.rhs(auxiliary, p)
        details["auxiliary_active_reference_root"] = dict(
            scope="Static reference active root with stationary dormant bank imposed; not a full new dormancy root or a stationarity reclassification",
            max_scaled_active_reference_residual=fit["max_scaled_residual"],
            reference_full_community_stability=fit["stability"],
            reference_full_community_stability_scope="Includes the absent guild's invasion mode; an absorbing census boundary need not resist invasion",
            temperature_k=fit["global_temperature_k"], methane_ratio=float(auxiliary[-1]),
            bulk_pressure_pa=float(auxiliary[0]), endpoint_minus_root_pressure_pa=float(y[0]-auxiliary[0]),
            dormant_m_bulk_gdw_l=float(auxiliary[5]), dormant_m_warm_gdw_l=float(auxiliary[11]),
            maximum_dormant_rhs_gdw_l_yr=float(max(abs(residual[p.dormant_indices]).ravel())))
        if case.case_id != "dormancy_0052" and dy[-1]:
            details["methane_endpoint_offset_over_rhs_yr"] = float(abs((y[-1]-auxiliary[-1])/dy[-1]))
    return details


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=runner.RAW)
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).with_name("dormancy-late-stock-check-2026-11-10.json"))
    args = parser.parse_args()
    rows = []
    for stem in STEMS:
        path = args.raw_dir/(stem+".receipt.json")
        record = json.loads(path.read_text())
        protocol = record["protocol"]
        if (record["execution_status"] != "complete" or protocol["mode"] != "census"
                or protocol["case"]["years"] != 100000.
                or sha256(runner.e.dumps(protocol).encode()).hexdigest() != record["fingerprint"]):
            raise RuntimeError("Invalid original census receipt")
        for name, digest in protocol["source_sha256"].items():
            if sha256((ROOT/name).read_bytes()).hexdigest() != digest:
                raise RuntimeError("Physical source differs: "+name)
        data = turnover_survival.load(record, args.raw_dir)
        rows.append(dict(case_id=protocol["case"]["case_id"], protocol=protocol,
            receipt_file=path.name, receipt_sha256=sha256(path.read_bytes()).hexdigest(),
            **{k: record[k] for k in ("fingerprint", "raw_file", "raw_sha256")}, **diagnose(record, data)))
    result = dict(scope="Five original 100kyr census profiles, partial-grid late-stock diagnostic only; no new trajectories or changed statuses",
        interpretation={
            "0052": "Warm dormant M drives the 20kyr span. Its transient diminishes, but final 1kyr bulk-bank variation remains near the strict threshold. A longer hold does not guarantee microscopic precision.",
            "0004": "Banks are rapidly slaved to a still-relaxing atmospheric/H2 state; the physical tail is approximately the reference methane lifetime.",
            "0000_0008_0016": "The methane tail is approximately 10000yr; a 200kyr hold is a motivated extension, not a computed pass.",
            "precision": "Fixed pressure and stage absolute tolerances can limit tiny-bank resolution. Tighter rtol alone is not a guaranteed precision control. No criterion is weakened.",
            "rates": "Instantaneous relative RHS of a small slaved bank is not its relaxation eigenvalue and can differ from sampled drift."},
        source_sha256={str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in
                       (Path(__file__), Path(turnover_survival.__file__))}, cases=rows)
    args.output.write_text(runner.e.dumps(result)+"\n")
    print(args.output, args.output.stat().st_size, "bytes")


if __name__ == "__main__":
    main()
