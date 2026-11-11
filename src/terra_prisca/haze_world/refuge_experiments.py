"""Frozen, resumable two-habitat equilibrium and invasion experiments.

uv run python -m terra_prisca.haze_world.refuge_experiments --stage pilot --workers 2
"""

import argparse
from collections import Counter
import csv
from dataclasses import asdict, dataclass, replace
from functools import lru_cache
import gzip
from hashlib import sha256
import importlib.metadata
import io
import itertools
import json
from multiprocessing import Pool
from pathlib import Path
import platform
import sys
from time import perf_counter

import numpy as np

from . import population_coupling as core
from . import refuge_coupling as model
from . import refuge_equilibria as equilibria
from .finite_experiments import clean, dumps
from .refuge_integration import Census, integrate_finite

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "models/haze_world/figures/refuge_coupling"
RAW = ROOT / "local/haze/refuge_coupling"
FRACTIONS = (0., .5, .9)
PATCHES = ("cold", "warm")
GUILDS = ("a", "m")
MINIMUM_SHARE = .01


@dataclass(frozen=True)
class Case:
    case_id: str
    fraction: float
    warm_fraction: float
    contrast_k: float
    dispersal_yr: float
    direction: str
    activity: str = "fixed"
    seed_origin: str = "both"
    census_yr: float = 10.
    years: float = 100000.


@dataclass(frozen=True)
class EquilibriumCase:
    case_id: str
    fraction: float
    warm_fraction: float
    contrast_k: float
    dispersal_yr: float
    activity: str = "fixed"


def parameters(case):
    base = replace(core.reference(.3), acetate_fraction=case.fraction, activity_feedback=case.activity)
    return model.Refuge(base, case.warm_fraction, case.contrast_k, case.dispersal_yr)


def design(stage="main", years=None):
    duration = (1000. if stage == "pilot" else 100000.) if years is None else float(years)
    rows = []

    def add(f, w, contrast, dispersal, direction, activity="fixed", origin="both", census=10.):
        rows.append(Case("", f, w, contrast, dispersal, direction, activity, origin, census, duration))

    if stage == "main":
        for values in itertools.product(FRACTIONS, (.1, .5, .9), (0., 5., 10., 15., 20., 30.),
                                        (0., 1e-6, 1e-3, 1.), ("A_into_M", "M_into_A")):
            add(*values)
    elif stage == "subsets":
        for values in itertools.product(FRACTIONS, (.05,), (8.4, 8.6, 9.), (0., 1e-3), ("A_into_M", "M_into_A")):
            add(*values)
        for f, direction in itertools.product(FRACTIONS, ("A_into_M", "M_into_A")):
            for origin in ("cold", "warm"):
                add(f, .05, 8.6, 1e-3, direction, origin=origin)
            add(f, .05, 8.6, 1e-3, direction, activity="products")
            add(f, .05, 8.6, 1e-3, direction, census=1.)
            add(f, .01, 8.8, 1e-3, direction)
        for (f, w, contrast), dispersal, direction in itertools.product(
                ((0., .74, 1.), (.5, .51, 8.), (.5, .99, 15.)), (0., 1e-3), ("A_into_M", "M_into_A")):
            add(f, w, contrast, dispersal, direction)
    elif stage == "pilot":
        for values in ((.5, .5, 0., 0., "A_into_M"), (.5, .05, 8.6, 1e-3, "A_into_M"),
                       (.5, .05, 8.6, 1e-3, "M_into_A"), (.9, .01, 8.8, 1e-3, "A_into_M")):
            add(*values)
    else:
        raise ValueError("Unknown invasion stage")
    unique = list(dict.fromkeys(rows))
    return [replace(case, case_id=f"{stage}_{i:04d}_t{duration:g}") for i, case in enumerate(unique)]


def equilibrium_design():
    values = itertools.product(FRACTIONS, (.01, .05, .1, .5, .51, .7, .74, .9, .99),
                               (0., 1., 5., 8., 10., 15., 20., 30.), (0., 1e-3))
    return [EquilibriumCase(f"equilibria_{i:04d}", *row) for i, row in enumerate(values)]


def source_hashes():
    names = ("refuge_experiments.py", "refuge_coupling.py", "refuge_equilibria.py", "refuge_integration.py", "dense_roots.py",
             "population_coupling.py", "methane_budget.py", "darwinian.py", "two_guilds.py",
             "hydrogen_uptake.py", "woodii1998.py", "finite_experiments.py")
    paths = [Path(__file__).with_name(name) for name in names]
    paths += [ROOT / name for name in ("src/terra_prisca/haze_response/arney2016.py",
              "models/haze_response/arney2016/cases.csv", "models/haze_response/arney2016/figure4.csv",
              "models/haze_world/evidence/kotsyurbenko2001_table2.csv", "models/haze_world/evidence/peters1998_chemostat.csv",
              "uv.lock")]
    return {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest() for path in paths}


def identity(case, n_grid=201):
    p = parameters(case)
    record = dict(case=asdict(case), parameters=asdict(p), equilibrium_n_grid=n_grid,
                  source_sha256=source_hashes(), packages={name: importlib.metadata.version(name) for name in ("numpy", "scipy")},
                  python=dict(version=platform.python_version(), implementation=platform.python_implementation()))
    if isinstance(case, Case):
        record.update(census=asdict(Census(census_yr=case.census_yr)),
                      initial_protocol="Stable conditional resident positive in every active patch; highest-r root if multiple; invader added at matched total global dose; no external immigration",
                      initial_total_seed_gdw_l=1e-12,
                      start_selection="Highest r among qualifying roots; candidate ambiguity retained")
    return sha256(dumps(record).encode()).hexdigest(), record


def select_start(candidates, p, resident_index):
    qualifying = [e for e in candidates if e.get("stability") == "stable"
                  and all(e["y"][4*j+1+resident_index] > 0 for j, w in enumerate(p.weights) if w)]
    selected = max(qualifying, key=lambda e: e["r"]) if qualifying else None
    return selected, qualifying


@lru_cache(maxsize=None)
def conditional_start(p, resident_index, n_grid):
    enabled = (resident_index == 0, resident_index == 1)
    conditional = replace(p, base=replace(p.base, enabled=enabled))
    candidates = equilibria.equilibrium_states(conditional, n_grid=n_grid, stability=True)
    selected, qualifying = select_start(candidates, conditional, resident_index)
    return selected, dict(candidate_count=len(candidates), qualifying_count=len(qualifying),
                         qualifying_ratios=[e["r"] for e in qualifying], ambiguous=len(qualifying) > 1,
                         selected_ratio=selected["r"] if selected else None,
                         candidates=candidates, coverage=equilibria.search_coverage(conditional, n_grid))


def seed_state(case, resident):
    p = parameters(case)
    if case.direction not in ("A_into_M", "M_into_A") or case.seed_origin not in ("both", *PATCHES):
        raise ValueError("Unknown invasion direction or seed origin")
    invader = 0 if case.direction == "A_into_M" else 1
    y = np.asarray(resident, dtype=float).copy()
    if case.seed_origin == "both":
        for j, w in enumerate(p.weights):
            y[4*j+1+invader] = 1e-12 if w else 0.
    else:
        patch = PATCHES.index(case.seed_origin)
        if not p.weights[patch]:
            raise ValueError("Cannot inoculate an inactive habitat")
        y[model.BIOMASS_INDICES[:, invader]] = 0.
        y[4*patch+1+invader] = 1e-12 / p.weights[patch]
    dose = float(p.weights @ y[model.BIOMASS_INDICES[:, invader]])
    assert np.isclose(dose, 1e-12, rtol=1e-12, atol=0.)
    return y, dict(invader=GUILDS[invader], seed_origin=case.seed_origin, weighted_seed_gdw_l=dose,
                   global_seed_gdw=dose*p.base.habitat_l_cm2*Census().surface_cm2,
                   global_seed_cells=dose*p.base.habitat_l_cm2*Census().surface_cm2/Census().cell_mass_gdw)


def base_summary(case, start_info):
    return dict(**asdict(case), attempt_status="no_supported_conditional_start_found", settling_status="no_physical_endpoint",
                endpoint_class=None, global_temperature_k=None, methane_ratio=None, climate_domain=None,
                conditional_candidates=start_info["candidate_count"], conditional_qualifying=start_info["qualifying_count"],
                conditional_ambiguous=start_info["ambiguous"], conditional_selected_ratio=start_info["selected_ratio"],
                start_coverage_status=start_info["coverage"]["status"])


def summarize(case, p, process, result, start_info):
    row = base_summary(case, start_info)
    row.update(attempt_status=result.status, terminal_time_yr=float(result.t[-1]),
               terminal_global_temperature_k=float(core.temperature_k(result.y[8, -1], p.base.climate)),
               terminal_cold_temperature_k=float(result.temperatures_k[0, -1]),
               terminal_warm_temperature_k=float(result.temperatures_k[1, -1]),
               domain_exit_time_yr=result.domain_exit["time_yr"] if result.domain_exit else None,
               solver_nfev=result.metadata["nfev"], solver_resets=result.metadata["solver_resets"],
               accepted_steps=result.metadata["accepted_steps"], wall_seconds=result.metadata["wall_seconds"])
    volume = p.base.habitat_l_cm2 * process.surface_cm2 * p.weights
    global_log_conversion = float(result.metadata["global_log_cell_conversion"])
    for name, values, times in (
            ("global_continuous",result.global_continuous_min_log_biomass,result.global_continuous_min_times_yr),
            ("global_pre_extinction",result.global_pre_extinction_min_log_biomass,result.global_pre_extinction_min_times_yr),
            ("global_after_census",result.global_after_census_min_log_biomass,None)):
        for i,guild in enumerate(GUILDS):
            value=float(values[i])
            row[f"{name}_min_log_biomass_{guild}"]=value
            row[f"{name}_min_log_cells_{guild}"]=value+global_log_conversion
            row[f"{name}_min_zero_{guild}"]=bool(np.isneginf(value))
            if times is not None:
                row[f"{name}_min_time_{guild}_yr"]=float(times[i])
    row["sampled_path_climate_domains"]="|".join(sorted(set(result.climate_domains)))
    row["path_min_global_temperature_k"]=result.metadata["global_min_temperature_k"]
    row["path_max_global_temperature_k"]=result.metadata["global_max_temperature_k"]
    for j, patch in enumerate(PATCHES):
        row[f"path_min_temperature_{patch}_k"]=result.metadata["patch_min_temperature_k"][j]
        row[f"path_max_temperature_{patch}_k"]=result.metadata["patch_max_temperature_k"][j]
        row[f"path_cold_continuation_{patch}"]=bool(result.metadata["patch_min_temperature_k"][j]<277.15-1e-8)
        row[f"sampled_path_cold_continuation_{patch}"]=bool(np.any(result.physiology_domains[j]=="cold_continuation"))
        row[f"sampled_path_unsupported_{patch}"]=bool(np.any(result.physiology_domains[j]=="unsupported"))
        log_conversion = np.log(volume[j]/process.cell_mass_gdw) if volume[j] else -np.inf
        for i, guild in enumerate(GUILDS):
            label = f"{patch}_{guild}"
            for name, values in (("continuous", result.continuous_min_log_biomass),
                                 ("pre_removal", result.pre_removal_min_log_biomass),
                                 ("after_census", result.after_census_min_log_biomass)):
                value = float(values[j, i])
                row[f"{name}_min_log_biomass_{label}"] = value
                row[f"{name}_min_log_cells_{label}"] = value + log_conversion
                row[f"{name}_min_zero_{label}"] = bool(np.isneginf(value))
            events = [e for e in result.extinction_events if e["patch"] == patch and e["guild"] == ("acetogen" if i == 0 else "methanogen")]
            row[f"culls_{label}"] = len(events)
            row[f"first_cull_{label}_yr"] = events[0]["time_yr"] if events else None
    if result.status != "completed":
        return clean(row)
    analysis_time = float(result.census_times[-1]) if len(result.census_times) else float(result.t[-1])
    end = int(np.flatnonzero(result.t <= analysis_time + 1e-8)[-1])
    y = result.y[:, end]
    sample = result.y[:, (result.t <= analysis_time + 1e-8) & (result.t >= max(0., analysis_time-20000.))]
    density_floor = np.divide(process.minimum_cells*process.cell_mass_gdw, volume,
                              out=np.zeros(2), where=volume > 0)
    minimum = [1., density_floor[0], density_floor[0], 1e-9,
               1., density_floor[1], density_floor[1], 1e-9, .001]
    scales = np.maximum(np.mean(abs(sample), axis=1), minimum)
    spans = np.divide(np.ptp(sample, axis=1),scales,out=np.zeros(9),where=scales>0)
    temperatures = np.array([model.temperatures(state, p) for state in sample.T])
    temperature_span = float(np.max(np.ptp(temperatures[:, p.weights > 0], axis=0)))
    local = model.fluxes(y, p)
    rates = model.rhs(y, p)
    derivative = [abs(rates[8])*p.base.loss.lifetime_yr/max(y[8], .001)]
    hydraulic = core.HENRY_30C_MOL_L_PA/(p.base.biology.exchange_mol_l_h_pa*core.HOURS_PER_YEAR)
    global_catabolic = np.zeros(2)
    occupancy = []
    for j, (patch, weight, detail) in enumerate(zip(PATCHES, p.weights, local["local"])):
        if not weight:
            occupancy.append(0)
            row[f"occupancy_{patch}"] = "inactive"
            continue
        stocks = y[4*j:4*j+4]
        cells = stocks[1:3]*volume[j]/process.cell_mass_gdw
        mask = int(cells[0] >= process.minimum_cells*(1-1e-10)) + 2*int(cells[1] >= process.minimum_cells*(1-1e-10))
        occupancy.append(mask)
        row[f"occupancy_{patch}"] = ("empty", "acetogen", "methanogen", "both")[mask]
        catabolic = np.asarray(detail["catabolic_h2_mol_l_yr"])
        global_catabolic += weight*catabolic
        shares = catabolic/sum(catabolic) if sum(catabolic) > 0 else np.zeros(2)
        row.update({f"temperature_{patch}_k":float(local["temperatures_k"][j]),
                    f"physiology_{patch}":local["physiology_domains"][j],
                    f"pressure_{patch}_pa":float(stocks[0]), f"acetate_{patch}_mol_l":float(stocks[3])})
        derivative.extend((abs(rates[4*j])*hydraulic/max(stocks[0],1.),
                           abs(rates[4*j+3])*p.base.acetate_lifetime_yr/max(stocks[3],1e-9)))
        for i, guild in enumerate(GUILDS):
            label = f"{patch}_{guild}"
            row.update({f"cells_{label}":float(cells[i]), f"catabolic_share_{label}":float(shares[i]),
                        f"biological_growth_{label}_yr":float(detail["net_growth_yr"][i]),
                        f"exchange_{label}_gdw_l_yr":float(local["exchange_gdw_l_yr"][j,i]),
                        f"source_sink_{label}":bool(cells[i]>0 and detail["net_growth_yr"][i]<-1e-4 and local["exchange_gdw_l_yr"][j,i]>0)})
            if mask & (1 << i):
                derivative.append(abs(rates[4*j+1+i])/max(stocks[1+i],density_floor[j])/(p.base.biology.loss_h*core.HOURS_PER_YEAR))
    late_activity = result.census_activity[result.census_times >= max(0., analysis_time-20000.)]
    changes = int(np.sum(late_activity[1:] != late_activity[:-1]))
    stationary = (case.years >= 100000 and max(spans)<.001 and temperature_span<.01
                  and max(derivative)<.001 and changes==0)
    global_presence = [any(mask & (1 << i) for mask in occupancy) for i in range(2)]
    if not any(global_presence):
        kind = "empty"
    elif not all(global_presence):
        kind = "single_acetogen" if global_presence[0] else "single_methanogen"
    elif p.dispersal_yr == 0 and occupancy == [1,2]:
        kind = "pure_partition"
    elif p.dispersal_yr == 0 and occupancy == [2,1]:
        kind = "reverse_partition"
    elif p.dispersal_yr == 0 and p.base.activity_feedback == "fixed" and any(
            mask == 3 and any(abs(local["temperatures_k"][j]-t)<.01 for t in core.switch_temperatures(p.base.biology))
            for j, mask in enumerate(occupancy)):
        kind = "locally_pinned_within_0.01K"
    else:
        kind = "spatial_coexistence"
    global_shares = global_catabolic/sum(global_catabolic) if sum(global_catabolic)>0 else np.zeros(2)
    row.update(analysis_time_yr=analysis_time, settling_status="census_stationary" if stationary else
               "unsettled" if case.years>=100000 else "pilot_only",
               endpoint_class=kind if stationary else None, instantaneous_class=kind,
               global_temperature_k=float(local["global_temperature_k"]), methane_ratio=float(y[8]),
               climate_domain=local["climate_domain"], global_catabolic_share_a=float(global_shares[0]),
               global_catabolic_share_m=float(global_shares[1]), both_material=bool(np.all(global_shares>=MINIMUM_SHARE)),
               max_late_relative_span=float(max(spans)), late_temperature_span_k=temperature_span,
               max_scaled_derivative=float(max(derivative)), late_occupancy_changes=changes)
    return clean(row)


def _paths(case, fingerprint, raw_dir):
    stem = f"{case.case_id}-{fingerprint[:16]}"
    return raw_dir/(stem+".json.gz"), raw_dir/(stem+".receipt.json")


def _reuse(case, fingerprint, raw_dir):
    data, receipt = _paths(case, fingerprint, raw_dir)
    if not receipt.exists():
        return None
    record = json.loads(receipt.read_text())
    if (record["execution_status"] != "complete" or record["fingerprint"] != fingerprint
            or sha256(data.read_bytes()).hexdigest() != record["raw_sha256"]):
        raise RuntimeError(f"Receipt/data mismatch for {case.case_id}")
    return record


def _save(case, fingerprint, protocol, raw_dir, payload, summary):
    data, receipt = _paths(case, fingerprint, raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    temporary = data.with_suffix(".tmp")
    with temporary.open("wb") as binary, gzip.GzipFile(filename="",mode="wb",fileobj=binary,mtime=0) as compressed, io.TextIOWrapper(compressed) as handle:
        handle.write(dumps(dict(protocol=protocol, summary=summary, **payload)))
    temporary.replace(data)
    record = dict(execution_status="complete", fingerprint=fingerprint, protocol=protocol, summary=summary,
                  raw_file=data.name, raw_sha256=sha256(data.read_bytes()).hexdigest())
    temporary = receipt.with_suffix(".tmp")
    temporary.write_text(dumps(record)+"\n")
    temporary.replace(receipt)
    return record


def run_case(case, raw_dir, n_grid=201, expected_sources=None):
    try:
        fingerprint, protocol = identity(case, n_grid)
        if expected_sources is not None and protocol["source_sha256"] != expected_sources:
            raise RuntimeError("Source changed after the batch freeze")
        reused = _reuse(case, fingerprint, raw_dir)
        if reused is not None:
            return reused
        p = parameters(case)
        selected, start_info = conditional_start(p, 1 if case.direction=="A_into_M" else 0, n_grid)
        if selected is None:
            summary = base_summary(case, start_info)
            payload = dict(start_info=start_info, initial_y=None, seed=None, result=None)
        else:
            y0, seed = seed_state(case, selected["y"])
            process = Census(census_yr=case.census_yr)
            result = integrate_finite(y0, p, case.years, process, sample_every_censuses=1)
            if result.status not in ("completed","initial_unsupported","domain_exit"):
                raise RuntimeError(f"Unexpected integration status {result.status}")
            if np.any(~np.isfinite(result.y)) or np.any(result.y < 0) or np.any(np.isnan(result.log_biomass)):
                raise RuntimeError("Accepted trajectory contains invalid physical stocks or log diagnostics")
            summary = summarize(case,p,process,result,start_info)
            payload = dict(start_info=start_info, initial_y=y0, seed=seed, result=asdict(result))
        if identity(case,n_grid)[0] != fingerprint:
            raise RuntimeError("Source/environment changed during the case")
        return _save(case,fingerprint,protocol,raw_dir,payload,summary)
    except Exception as error:
        raise RuntimeError(f"Refuge case {case.case_id} failed: {type(error).__name__}: {error}") from error


def run_equilibrium_case(case, raw_dir, n_grid=201, expected_sources=None):
    try:
        fingerprint, protocol = identity(case,n_grid)
        if expected_sources is not None and protocol["source_sha256"] != expected_sources:
            raise RuntimeError("Source changed after the batch freeze")
        reused = _reuse(case,fingerprint,raw_dir)
        if reused is not None:
            return reused
        p = parameters(case)
        started = perf_counter()
        candidates = equilibria.equilibrium_states(p,n_grid=n_grid,stability=True)
        coverage = equilibria.search_coverage(p,n_grid)
        summary = dict(**asdict(case),attempt_status="candidates_found" if candidates else "no_supported_equilibrium_found",
                       candidates=len(candidates), measured_candidates=sum(e["measured"] for e in candidates),
                       stable_candidates=sum(e["stability"]=="stable" for e in candidates),
                       coverage_status=coverage["status"],wall_seconds=perf_counter()-started)
        if identity(case,n_grid)[0] != fingerprint:
            raise RuntimeError("Source/environment changed during equilibrium search")
        return _save(case,fingerprint,protocol,raw_dir,dict(candidates=candidates,coverage=coverage),summary)
    except Exception as error:
        raise RuntimeError(f"Refuge equilibrium case {case.case_id} failed: {type(error).__name__}: {error}") from error


def _worker(task):
    kind,case,raw_dir,n_grid,sources = task
    try:
        return (run_equilibrium_case if kind=="equilibria" else run_case)(case,raw_dir,n_grid,sources)
    except Exception:
        print(f"ERROR: {case.case_id} failed; batch collection is aborted",file=sys.stderr,flush=True)
        raise


def run_many(cases,raw_dir,n_grid,workers,kind):
    sources=source_hashes()
    tasks=[(kind,case,raw_dir,n_grid,sources) for case in cases]
    if workers==1:
        for task in tasks:
            _worker(task)
    else:
        # Pool's public context terminates other workers on an exception.
        with Pool(processes=workers) as pool:
            for _ in pool.imap_unordered(_worker,tasks,chunksize=1):
                pass


def _csv_text(rows):
    names=list(dict.fromkeys(k for row in rows for k in row))
    handle=io.StringIO(newline="")
    writer=csv.DictWriter(handle,fieldnames=names,lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue()


def public_table(output,name,rows):
    text=_csv_text(rows)
    if len(text.encode())<900000:
        (output/name).write_text(text)
        return [name]
    names=[]
    for i,start in enumerate(range(0,len(rows),128)):
        filename=f"{Path(name).stem}_{i:03d}.csv"
        text=_csv_text(rows[start:start+128])
        if len(text.encode())>=1000000:
            raise RuntimeError("Public row batch exceeds1MB; detailed data stay in raw storage")
        (output/filename).write_text(text)
        names.append(filename)
    return names


def collect(cases,raw_dir,output,stage,n_grid=201):
    if not cases:
        raise ValueError("Collect at least one requested case")
    records=[]
    for case in cases:
        fingerprint,_=identity(case,n_grid)
        record=_reuse(case,fingerprint,raw_dir)
        if record is None:
            raise RuntimeError(f"Missing qualified completion receipt: {case.case_id}")
        records.append(record)
    output.mkdir(parents=True,exist_ok=True)
    rows=[record["summary"] for record in records]
    tables=public_table(output,f"{stage}_summary.csv",rows)
    if all(isinstance(case,EquilibriumCase) for case in cases):
        states=[]
        for record in records:
            with gzip.open(raw_dir/record["raw_file"],"rt") as handle:
                payload=json.load(handle)
            for i,e in enumerate(payload["candidates"]):
                y=e["y"]
                states.append(dict(**record["protocol"]["case"],candidate=i,kind=e["kind"],stability=e["stability"],
                    global_temperature_k=e["global_temperature_k"],cold_temperature_k=e["temperatures_k"][0],
                    warm_temperature_k=e["temperatures_k"][1],cold_domain=e["physiology_domains"][0],
                    warm_domain=e["physiology_domains"][1],climate_domain=e["climate_domain"],measured=e["measured"],
                    ratio=e["r"],max_real_yr=e["max_real_yr"],max_scaled_residual=e["max_scaled_residual"],
                    cold_pressure_pa=y[0],cold_a_gdw_l=y[1],cold_m_gdw_l=y[2],cold_acetate_mol_l=y[3],
                    warm_pressure_pa=y[4],warm_a_gdw_l=y[5],warm_m_gdw_l=y[6],warm_acetate_mol_l=y[7]))
        tables += public_table(output,f"{stage}_candidates.csv",states)
    manifest=dict(stage=stage,cases=len(cases),tables=tables,source_sha256=source_hashes(),
                  packages=records[0]["protocol"]["packages"],python=records[0]["protocol"]["python"],
                  attempt_counts=dict(Counter(r["attempt_status"] for r in rows)),
                  settling_counts=dict(Counter(r.get("settling_status","not_applicable") for r in rows)),
                  receipts=[dict(case_id=r["protocol"]["case"]["case_id"],fingerprint=r["fingerprint"],
                                 raw_file=r["raw_file"],raw_sha256=r["raw_sha256"]) for r in records],
                  physical_endpoint_rule="Only completed integrations may supply endpoint fields; stationarity separately requires100kyr, last20kyr spans<0.001, temperature span<0.01K, scaled derivatives<0.001 and unchanged census occupancy",
                  unsupported_scope="No conditional start/root found is a finite-search outcome, not extinction or global nonexistence",
                  external_immigration="none",minimum_scope="Accepted dense-flow extrema and explicit census jumps; censored minima depend on the census protocol; global minima use simultaneous area-weighted biomass rather than sums of separate minima",
                  infinity_encoding="Negative-infinite log minima are JSON null/CSV blank with explicit min_zero=true; they mean zero stock, not missing diagnostics",
                  path_flags_scope="Sampled climate domains use returned census/removal/terminal states; temperature extrema and physiological continuation use accepted dense pieces with r-polynomial extrema and radiative vertices; supported-domain exits are located on those pieces",
                  material_share_threshold=MINIMUM_SHARE,seed_dose="Weighted total1e-12gDW/L, matched across seed-origin comparisons")
    path=output/f"{stage}_manifest.json"
    path.write_text(dumps(manifest)+"\n")
    for file in [path,*[output/name for name in tables]]:
        if file.stat().st_size>=1000000:
            raise RuntimeError(f"Public output exceeds1MB: {file.name}")
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage",choices=("pilot","main","subsets","equilibria"),default="pilot")
    parser.add_argument("--workers",type=int,default=1)
    parser.add_argument("--years",type=float)
    parser.add_argument("--n-grid",type=int,default=201)
    parser.add_argument("--raw-dir",type=Path,default=RAW)
    parser.add_argument("--output",type=Path,default=OUTPUT)
    parser.add_argument("--case-id",action="append")
    parser.add_argument("--collect-only",action="store_true")
    parser.add_argument("--list-cases",action="store_true")
    args=parser.parse_args()
    if args.workers<1 or args.n_grid<21 or (args.years is not None and (not np.isfinite(args.years) or args.years<=0)):
        parser.error("Use positive workers/duration and at least21 ratio-grid points")
    cases=equilibrium_design() if args.stage=="equilibria" else design(args.stage,args.years)
    selected=set(args.case_id or ())
    if selected:
        cases=[case for case in cases if case.case_id in selected]
        if len(cases)!=len(selected):
            parser.error("One or more requested case IDs are absent from this stage/duration")
    if args.list_cases:
        print(dumps([asdict(case) for case in cases]));return
    if not args.collect_only:
        run_many(cases,args.raw_dir,args.n_grid,args.workers,args.stage)
    stage=args.stage+("_selection_"+sha256(dumps(sorted(selected)).encode()).hexdigest()[:8] if selected else "")
    print(dumps(collect(cases,args.raw_dir,args.output,stage,args.n_grid)))


if __name__=="__main__":
    main()
