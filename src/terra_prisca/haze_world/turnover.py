"""Well-mixed turnover regimes, rooted boundaries and deterministic basins.

    uv run python -m terra_prisca.haze_world.turnover --stage map --workers 4
    uv run python -m terra_prisca.haze_world.turnover --stage basins --workers 4

The environmental and physiological source curves remain unchanged. A switch
of resource requirements need not be reachable by a planetary equilibrium.
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
import csv
from dataclasses import asdict, replace
from hashlib import sha256
from functools import lru_cache
import importlib.metadata
import json
from pathlib import Path
import platform
from time import perf_counter
from types import FunctionType

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

from . import buffered_experiments as e
from . import population_coupling as core
from .two_guilds import guilds

OUTPUT = e.ROOT / "models/haze_world/figures/turnover"
RAW = e.ROOT / "local/haze/turnover/basins"
FRACTIONS = (0., .25, .5, .75, .9)
LOSSES = np.logspace(-4, -2, 49)


def params(fraction, loss_h):
    ref = core.reference()
    return replace(ref, acetate_fraction=float(fraction), biology=replace(ref.biology, loss_h=float(loss_h)))


def switches(loss_h):
    return core.switch_temperatures(params(0., loss_h).biology)


def switch_at(loss_h):
    values = switches(loss_h)
    return float(values[0]) if values else float("nan")


def sources():
    return e.source_hashes() | {str(Path(__file__).relative_to(e.ROOT)): sha256(Path(__file__).read_bytes()).hexdigest()}


def equilibria(fraction, loss_h, verify=False):
    p = params(fraction, loss_h)
    def inventory(n):
        result=core.equilibrium_states(p,n_grid=n)
        grid=np.unique(np.r_[core._ratio_grid(p,n),nonsmooth_ratios(p.climate)])
        for index,kind in enumerate(("acetogen","methanogen")):
            for ratio in core._roots(lambda r:_pure_balance(r,loss_h,fraction,index),grid,1e-14):
                state=core._resident(ratio,p,index)
                if state is not None and not any(s["kind"]==kind and abs(s["r"]-ratio)<1e-8 for s in result):
                    result.append(core._describe(kind,state,p))
        return sorted(result,key=lambda s:(s["r"],s["kind"]))
    states = inventory(501)
    if verify:
        fine = inventory(1001)
        if len(states) != len(fine) or any(a["kind"] != b["kind"] or abs(a["r"]-b["r"]) > 1e-8
                                            for a, b in zip(states, fine)):
            raise RuntimeError("Equilibrium inventory changes on grid refinement")
    for state in states:
        eigenvalues,stencil=stability_spectrum(state["y"],p)
        maximum=float(max(eigenvalues.real))
        state.update(eigenvalues=eigenvalues,max_real_yr=maximum,
            stability="stable" if maximum < -1e-9 else "unstable" if maximum > 1e-9 else "marginal",
            stable=maximum < -1e-9,stability_stencil=stencil)
    return states


@lru_cache(maxsize=8)
def nonsmooth_ratios(climate):
    p=replace(core.reference(),climate=climate)
    grid=core._ratio_grid(p,1001)
    result=list(core.response(climate.case).ratios)
    for temperature in (277.15,283.15,288.15,293.15,298.15,303.15):
        result.extend(core._roots(lambda ratio:float(core.temperature_k(ratio,climate))-temperature,grid,1e-10))
    return np.array(sorted(set(result)))


def stability_spectrum(y,p,fractional_step=1e-5):
    y=np.asarray(y,dtype=float);scales=np.maximum(abs(y),[10.,1e-4,1e-4,1e-5,.01])
    cuts=nonsmooth_ratios(p.climate);distance=float(min(abs(cuts-y[4])))
    corner=distance<1e-11
    h=scales[4]*fractional_step
    if not corner:h=min(h,distance*.25)
    spectra=[]
    for side in ((-1,1) if corner else (0,)):
        jac=np.empty((5,5));center=core.rhs(y,p)
        for j in range(5):
            step=h if j==4 else scales[j]*fractional_step
            delta=np.eye(5)[j]*step
            derivative=(core.rhs(y+side*delta,p)-center)/(side*step) if j==4 and side else (core.rhs(y+delta,p)-core.rhs(y-delta,p))/(2*step)
            jac[:,j]=derivative*scales[j]/scales
        active=[0,*[i+1 for i,enabled in enumerate(p.enabled) if enabled],3,4]
        spectra.extend(np.linalg.eigvals(jac[np.ix_(active,active)]))
    return np.array(spectra),"both_one_sided_at_corner" if corner else "central_stencil_inside_one_segment"


def regime(states):
    stable = [s for s in states if s["stable"]]
    labels = sorted(s["kind"] for s in stable)
    if not labels:
        return "no_stable_equilibrium_found"
    if len(labels) > 1:
        return "multistable:"+"+".join(labels)
    return labels[0]+"_only" if labels[0] != "mixed" else "mixed"


def map_case(item):
    i, fraction, loss_h = item
    p = params(fraction, loss_h); states = equilibria(fraction, loss_h, verify=True)
    summary = dict(profile_id=f"regime_{i:04d}" if isinstance(i,int) else i, fraction=fraction, loss_h=loss_h,
        turnover_days=1/(24*loss_h), switch_temperatures_k="|".join(map(str, switches(loss_h))),
        regime=regime(states), equilibria=len(states), stable_equilibria=sum(s["stable"] for s in states))
    rows = []
    for j, s in enumerate(states):
        flow = core.rhs(s["y"], p)
        rows.append(dict(**summary, equilibrium_id=f"{summary['profile_id']}_{j}", kind=s["kind"],
            stability=s["stability"], stable=s["stable"], temperature_k=s["t_k"], methane_ratio=s["r"],
            pressure_pa=s["y"][0], biomass_a_gdw_l=s["y"][1], biomass_m_gdw_l=s["y"][2], acetate_mol_l=s["y"][3],
            max_real_eigenvalue_yr=s["max_real_yr"], eigenvalues=e.dumps([[z.real, z.imag] for z in s["eigenvalues"]]),
            stability_stencil=s["stability_stencil"],
            climate_domain=s["domain"], physiology_domain="measured" if s["t_k"] >= 277.15 else "cold_continuation",
            redox_residual=s["redox_residual"], methane_balance_residual_yr=flow[-1],
            grid_refinement_verified=True,
            radiative_vertex=bool(np.any(np.isclose(s["r"], core.response(p.climate.case).ratios, rtol=0, atol=1e-10)))))
    return summary, rows


def _difference(temperature_k, loss_h):
    values = [g.rstar(loss_h) for g in guilds(temperature_k-273.15, params(0., loss_h).biology)]
    return values[0]-values[1]


def _log_roots(function, low=1e-4, high=1e-2, n=301):
    grid = np.linspace(np.log(low), np.log(high), n)
    values = np.array([function(float(np.exp(v))) for v in grid])
    result = []
    for x, y, a, b in zip(grid[:-1], grid[1:], values[:-1], values[1:]):
        if np.isfinite(a) and abs(a) < 1e-10:
            result.append(float(np.exp(x)))
        elif np.isfinite(a) and np.isfinite(b) and a*b < 0:
            result.append(float(np.exp(brentq(lambda q:function(float(np.exp(q))), x, y, xtol=1e-12))))
    return sorted({round(v, 15) for v in result})


def _pure_balance(ratio, loss_h, fraction, index):
    p = params(fraction, loss_h)
    temperature = float(core.temperature_k(ratio, p.climate))
    g = guilds(temperature-273.15, p.biology)[index]
    q = g.maintenance+loss_h/g.yield_g_mol
    if q >= g.rate_scale:
        return float("nan")
    pressure = g.threshold_pa+g.km_pa*q/(g.rate_scale-q)
    capture = core.supply_h2(p)-p.biology.exchange_mol_l_h_pa*(pressure-p.biology.atmosphere_pa)
    factor = fraction if index == 0 else 1.
    source = core.inventory_to_ratio(p)*core.HOURS_PER_YEAR*capture*(1-g.assimilation_mol_g*loss_h/q)*factor/4
    return source+core.atmosphere(p.climate.case)["flux_to_ratio_per_yr"]*p.climate.abiotic_flux-float(p.loss.rate(ratio))


def _resident_loss(ratio, fraction, index):
    p = params(fraction, 1e-3)
    temperature = float(core.temperature_k(ratio, p.climate))
    g = guilds(temperature-273.15, p.biology)[index]
    p0 = p.biology.atmosphere_pa+core.supply_h2(p)/p.biology.exchange_mol_l_h_pa
    upper = min(.01, g.yield_g_mol*(g.uptake(p0)-g.maintenance))
    if upper <= 1e-4:
        return np.nan
    left, right = _pure_balance(ratio, 1e-4, fraction, index), _pure_balance(ratio, upper, fraction, index)
    if not np.isfinite(left) or not np.isfinite(right) or left*right > 0:
        return np.nan
    return float(brentq(lambda loss:_pure_balance(ratio, loss, fraction, index), 1e-4, upper, xtol=1e-14))


def _ratio_breaks(p):
    grid = core._ratio_grid(p, 1001)
    for temperature in (273., 277.15, 283.15, 288.15, 293.15, 298.15, 303.15):
        for a, b in zip(grid[:-1], grid[1:]):
            fa, fb = float(core.temperature_k(a, p.climate))-temperature, float(core.temperature_k(b, p.climate))-temperature
            if fa*fb < 0:
                grid = np.r_[grid, brentq(lambda r:float(core.temperature_k(r, p.climate))-temperature, a, b)]
    return np.unique(grid)


def plateau_family(fraction, loss_h):
    p=params(fraction,loss_h);curve=core.response(p.climate.case)
    temperature=float(curve.temperatures_k[-1]);pair=guilds(temperature-273.15,p.biology)
    if abs(pair[0].rstar(loss_h)-pair[1].rstar(loss_h))>1e-5:return None
    pressure=pair[0].rstar(loss_h)
    capture=core.supply_h2(p)-p.biology.exchange_mol_l_h_pa*(pressure-p.biology.atmosphere_pa)
    if capture<=0:return None
    abiotic=core.atmosphere(p.climate.case)["flux_to_ratio_per_yr"]*p.climate.abiotic_flux
    endpoints=[]
    for index,g in enumerate(pair):
        q=g.maintenance+loss_h/g.yield_g_mol
        source=core.inventory_to_ratio(p)*core.HOURS_PER_YEAR*capture*(1-g.assimilation_mol_g*loss_h/q)*(fraction if index==0 else 1.)/4+abiotic
        endpoints.append(float(p.loss.inverse(source)))
    low=max(float(curve.ratios[-1]),min(endpoints));high=max(endpoints)
    return dict(ratio_interval=[low,high],temperature_k=temperature,
                meaning="Neutral mixed equilibrium continuum on the imposed flat high-methane temperature extension") if high>low else None


def boundaries():
    results = []
    ref = params(0., 1e-3)
    curve = core.response(ref.climate.case)
    r0 = float(ref.loss.inverse(core.atmosphere(ref.climate.case)["flux_to_ratio_per_yr"]*ref.climate.abiotic_flux))
    special = {"physiology_floor":273., "climate_minimum":float(min(curve.temperatures_k)),
               "methane_plateau":float(curve.temperatures_k[-1]), "climate_maximum":float(max(curve.temperatures_k)),
               "cold_refuge":278., "warm_refuge":286.}
    for name, temperature in special.items():
        for loss in _log_roots(lambda L:_difference(temperature, L)):
            results.append(dict(event="switch_crosses_"+name, loss_h=loss, temperature_k=temperature,
                                interpretation="Thermal R* equality; planetary feasibility must be checked separately"))
            if name in ("climate_minimum","methane_plateau","climate_maximum"):
                for fraction in FRACTIONS:
                    below=equilibria(fraction,loss*(1-1e-5));above=equilibria(fraction,loss*(1+1e-5))
                    signature=lambda ss:sorted((s["kind"],s["stability"]) for s in ss)
                    if signature(below)!=signature(above):
                        record=dict(event="mixed_geometry_"+name,fraction=fraction,loss_h=loss,temperature_k=temperature)
                        if name=="methane_plateau":record["plateau_family"]=plateau_family(fraction,loss)
                        results.append(record)
    for temperature in sorted(set(curve.temperatures_k)|{277.15,283.15,288.15,293.15,298.15,303.15}):
        if any(abs(temperature-value)<1e-8 for value in special.values()):continue
        for loss in _log_roots(lambda L:_difference(float(temperature),L)):
            for fraction in FRACTIONS:
                below=equilibria(fraction,loss*(1-1e-5));above=equilibria(fraction,loss*(1+1e-5))
                signature=lambda ss:sorted((s["kind"],s["stability"]) for s in ss)
                if signature(below)!=signature(above):
                    results.append(dict(event="mixed_nonsmooth_transition",fraction=fraction,loss_h=loss,temperature_k=float(temperature),
                        interpretation="Stability or inventory changes as the thermal switch crosses a radiative or physiological corner"))
    p0 = ref.biology.atmosphere_pa+core.supply_h2(ref)/ref.biology.exchange_mol_l_h_pa
    t0 = float(core.temperature_k(r0, ref.climate))
    for index, label in enumerate(("acetogen", "methanogen")):
        g = guilds(t0-273.15, ref.biology)[index]
        loss = float(g.yield_g_mol*(g.uptake(p0)-g.maintenance))
        results.append(dict(event="lifeless_invasion_"+label, loss_h=loss, temperature_k=t0,
                            interpretation="Exact growth=loss at the unconsumed donor pressure"))
    for fraction in FRACTIONS:
        for index, kind in enumerate(("acetogen", "methanogen")):
            if index == 0 and fraction == 0:
                for loss in _log_roots(lambda L:core.fluxes(core._resident(r0, params(0., L), 0), params(0., L))["net_growth_yr"][1]
                                         if core._resident(r0, params(0., L), 0) is not None else np.nan):
                    results.append(dict(event="acetogen_invaded", fraction=fraction, loss_h=loss, methane_ratio=r0, temperature_k=t0))
                continue
            breaks = _ratio_breaks(params(fraction, 1e-3)); grid = breaks[breaks > r0+1e-10]
            losses = np.array([_resident_loss(float(r), fraction, index) for r in grid])

            def invasion(r):
                loss = _resident_loss(r, fraction, index)
                if not np.isfinite(loss): return np.nan
                state = core._resident(r, params(fraction, loss), index)
                return core.fluxes(state, params(fraction, loss))["net_growth_yr"][1-index] if state is not None else np.nan

            roots = core._roots(invasion, grid, 1e-9)
            for ratio in roots:
                loss = _resident_loss(ratio, fraction, index)
                results.append(dict(event=kind+"_invaded", fraction=fraction, loss_h=loss, methane_ratio=ratio,
                                    temperature_k=float(core.temperature_k(ratio, ref.climate))))

            vertices = nonsmooth_ratios(ref.climate)
            def derivative(r):
                loss = _resident_loss(r, fraction, index)
                if not np.isfinite(loss): return np.nan
                distance = np.min(abs(vertices-r))
                h = min(1e-6, max(distance*.1, 1e-10))
                return (_pure_balance(r+h, loss, fraction, index)-_pure_balance(r-h, loss, fraction, index))/(2*h)

            for a,b,la,lb in zip(grid[:-1],grid[1:],losses[:-1],losses[1:]):
                if not np.isfinite(la+lb) or np.any((vertices >= a)&(vertices <= b)):
                    continue
                fa, fb = derivative(float(a)), derivative(float(b))
                if np.isfinite(fa+fb) and fa*fb < 0:
                    ratio = float(brentq(derivative,a,b,xtol=1e-11));loss=_resident_loss(ratio,fraction,index)
                    results.append(dict(event=kind+"_resident_fold",fraction=fraction,loss_h=loss,methane_ratio=ratio,
                                        temperature_k=float(core.temperature_k(ratio,ref.climate))))
            for ratio in vertices:
                loss = _resident_loss(float(ratio),fraction,index)
                if not np.isfinite(loss): continue
                h=1e-8
                center=_pure_balance(float(ratio),loss,fraction,index)
                left=(center-_pure_balance(float(ratio-h),loss,fraction,index))/h
                right=(_pure_balance(float(ratio+h),loss,fraction,index)-center)/h
                if left*right < 0:
                    results.append(dict(event=kind+"_resident_corner_fold",fraction=fraction,loss_h=loss,methane_ratio=float(ratio),
                                        temperature_k=float(core.temperature_k(ratio,ref.climate))))
    results.extend(_stability_boundaries(results))
    for result in results:
        if "fraction" in result:
            f=result["fraction"]; L=result["loss_h"]
            result["regime_below"]=regime(equilibria(f,L*(1-1e-5)))
            result["regime_above"]=regime(equilibria(f,L*(1+1e-5)))
    unique=[]
    for result in sorted(results,key=lambda r:(r["loss_h"],r.get("fraction",-1),r["event"])):
        if not any(result["event"]==r["event"] and result.get("fraction")==r.get("fraction")
                   and abs(np.log(result["loss_h"]/r["loss_h"]))<1e-7 for r in unique):unique.append(result)
    return unique


def _stability_boundaries(events):
    results=[]
    for fraction in FRACTIONS:
        edges=_event_edges(events,fraction)
        for left,right in zip(edges[:-1],edges[1:]):
            grid=np.exp(np.linspace(np.log(left),np.log(right),9)[1:-1])
            states=[equilibria(fraction,float(L)) for L in grid]
            for la,lb,sa,sb in zip(grid[:-1],grid[1:],states[:-1],states[1:]):
                for kind in ("acetogen","methanogen","mixed"):
                    aa=[s for s in sa if s["kind"]==kind];bb=[s for s in sb if s["kind"]==kind]
                    if len(aa)!=len(bb):continue
                    for branch,(a,b) in enumerate(zip(aa,bb)):
                        if a["max_real_yr"]*b["max_real_yr"]>=0:continue
                        def maximum(logloss):
                            current=[s for s in equilibria(fraction,float(np.exp(logloss))) if s["kind"]==kind]
                            if len(current)!=len(aa):raise ValueError("Unresolved root inventory inside stability bracket")
                            return current[branch]["max_real_yr"]
                        try:loss=float(np.exp(brentq(maximum,np.log(la),np.log(lb),xtol=1e-12)))
                        except ValueError:continue
                        state=[s for s in equilibria(fraction,loss) if s["kind"]==kind][branch]
                        z=state["eigenvalues"][np.argmax(state["eigenvalues"].real)]
                        results.append(dict(event=kind+"_"+("hopf_candidate" if abs(z.imag)>1e-5 else "stability_crossing"),
                            fraction=fraction,loss_h=loss,methane_ratio=state["r"],temperature_k=state["t_k"],
                            critical_eigenvalue=[float(z.real),float(z.imag)],
                            interpretation="Root of full spectral abscissa; complex crossing is a Hopf candidate, not a nonlinear cycle proof"))
    return results


def _event_edges(events,fraction):
    values=sorted({1e-4,.01,*[r["loss_h"] for r in events
        if (r.get("fraction")==fraction or r["event"].startswith("lifeless_invasion_")) and 1e-4<r["loss_h"]<.01]})
    result=[]
    for value in values:
        if not result or abs(np.log(value/result[-1]))>1e-7:result.append(value)
    return result


def resolved_points(events):
    points=[dict(profile_id=f"regime_{i:04d}",fraction=f,loss_h=float(L),sampling="planned_grid")
            for i,(f,L) in enumerate((f,L) for f in FRACTIONS for L in LOSSES)]
    for fraction in FRACTIONS:
        edges=_event_edges(events,fraction)
        for j,(left,right) in enumerate(zip(edges[:-1],edges[1:])):
            if any(left<L<right for L in LOSSES):continue
            loss=float(np.sqrt(left*right))
            points.append(dict(profile_id=f"resolved_f{fraction:g}_{j:02d}",fraction=fraction,loss_h=loss,
                               sampling="root_delimited_interval",interval_low=left,interval_high=right))
    return points


def basin_tasks(events=None):
    tasks=[]
    if events is None:
        path=OUTPUT/"boundaries.json"
        if not path.exists():raise RuntimeError("Run the rooted T1 map before enumerating basins")
        events=json.loads(path.read_text())["boundaries"]
    for point in resolved_points(events):
        fraction,loss,profile=point["fraction"],point["loss_h"],point["profile_id"]
        states=equilibria(fraction,loss); stable=[s for s in states if s["stable"]]
        if len(stable)<2:continue
        for resident,index,direction in (("methanogen",0,"A_into_M"),("acetogen",1,"M_into_A")):
            candidates=[s for s in states if s["kind"]==resident]
            p_cond=replace(params(fraction,loss),enabled=(index==1,index==0))
            candidates=[s for s in candidates if max(stability_spectrum(s["y"],p_cond)[0].real)<-1e-9]
            for branch,candidate in enumerate(candidates):
                start=candidate["y"].copy();start[index+1]=1e-12
                tasks.append(dict(case_id=f"basin_{profile}_{direction}_res{branch}",fraction=fraction,loss_h=loss,
                                  trigger=direction,initial=start.tolist(),sampling=point["sampling"],resident_branch=branch))
        for j,s in enumerate(stable):
            if s["kind"]=="lifeless":
                for guild in (0,1):
                    start=s["y"].copy();start[guild+1]=1e-12
                    tasks.append(dict(case_id=f"basin_{profile}_lifeless_seed{guild}",fraction=fraction,loss_h=loss,
                        trigger=f"lifeless_seed{guild}",initial=start.tolist(),sampling=point["sampling"]))
                continue
            if s["kind"]!="mixed" and any(q["kind"]=="mixed" for q in stable):continue
            for guild in (g for g in (0,1) if s["y"][g+1]>0):
                for factor in (.99,1.01):
                    start=s["y"].copy();start[guild+1]*=factor
                    tasks.append(dict(case_id=f"basin_{profile}_{s['kind']}{j}_g{guild}_{factor:g}",fraction=fraction,loss_h=loss,
                        trigger=f"{s['kind']}_g{guild}_x{factor:g}",initial=start.tolist(),sampling=point["sampling"]))
    return tasks


def basin_case(item, years=100000., raw=RAW, expected_sources=None):
    protocol=dict(**item,years=years,source_sha256=sources(),python=platform.python_version(),
                  packages={name:importlib.metadata.version(name) for name in ("numpy","scipy")},
                  method="Radau, scaled numerical Jacobian, invariant initial face, acetate atol1e-13, max_step1000yr; frozen positive-biomass equations; uncensored; 1001 full-span samples plus10yr late-window samples")
    if expected_sources is not None and protocol["source_sha256"]!=expected_sources:raise RuntimeError("T1 source changed")
    fingerprint=sha256(e.dumps(protocol).encode()).hexdigest();stem=f"{item['case_id']}_t{years:g}-{fingerprint[:16]}"
    data,receipt=raw/(stem+".npz"),raw/(stem+".receipt.json")
    if receipt.exists():
        record=json.loads(receipt.read_text())
        if sha256(data.read_bytes()).hexdigest()!=record["raw_sha256"]:raise RuntimeError("Changed T1 basin record")
        return record
    p=params(item["fraction"],item["loss_h"]);initial=np.array(item["initial"])
    sample_times=np.unique(np.r_[np.linspace(0,years,1001),np.arange(max(0.,years-20000.),years+1.,10.),years])
    started=perf_counter(); result=integrate_basin(initial,p,years,sample_times=sample_times)
    if np.any(~np.isfinite(result.y)) or np.any(result.y[1:3]<0):raise RuntimeError("Invalid basin stocks")
    if np.min(result.y[[0,3,4]]) < -1e-10:raise RuntimeError("Material negative donor/product stock")
    final=result.y[:,-1]; states=equilibria(item["fraction"],item["loss_h"])
    floor=np.array([1.,1e-20,1e-20,1e-10,.001])
    distances=[float(max(abs(final-s["y"])/np.maximum((abs(final)+abs(s["y"]))/2,floor))) for s in states]
    nearest=states[int(np.argmin(distances))];distance=min(distances)
    late=result.t>=years-20000; span=max(np.ptp(result.y[:,late],axis=1)/np.maximum(np.mean(abs(result.y[:,late]),axis=1),floor))
    f=core.fluxes(final,p);hydraulic=core.HENRY_30C_MOL_L_PA/(p.biology.exchange_mol_l_h_pa*core.HOURS_PER_YEAR)
    dy=core.rhs(final,p)
    derivative=max(abs(dy[0])*hydraulic/max(final[0],1.),abs(dy[3])*p.acetate_lifetime_yr/max(abs(final[3]),1e-10),
        abs(dy[4])*p.loss.lifetime_yr/max(final[4],.001),
        *[abs(f["net_growth_yr"][g])/(p.biology.loss_h*core.HOURS_PER_YEAR) for g in (0,1) if final[g+1]>1e-20])
    invasion_ok=all(not (nearest["y"][g+1]==0 and f["net_growth_yr"][g]>1e-8) for g in (0,1))
    converged=bool(nearest["stable"] and distance<.001 and span<.001 and derivative<.001 and invasion_ok)
    summary=dict(case_id=item["case_id"],fraction=item["fraction"],loss_h=item["loss_h"],trigger=item["trigger"],years=years,
        converged=converged,nearest_kind=nearest["kind"],nearest_stability=nearest["stability"],nearest_ratio=nearest["r"],
        nearest_stock_distance=distance,late_max_relative_span=float(span),scaled_derivative=float(derivative),invasion_ok=invasion_ok,
        final_temperature_k=float(core.temperature_k(final[4],p.climate)),final_ratio=float(final[4]),
        minimum_sampled_chemical_stock=float(np.min(result.y[[0,3,4]])),wall_seconds=perf_counter()-started,nfev=result.nfev,
        sampling=item.get("sampling","planned_grid"))
    raw.mkdir(parents=True,exist_ok=True);temporary=data.with_suffix(".tmp")
    with temporary.open("wb") as stream:np.savez_compressed(stream,t=result.t,y=result.y,log_biomass=result.log_biomass,initial=initial)
    temporary.replace(data)
    if sources()!=protocol["source_sha256"]:raise RuntimeError("T1 source changed while integrating")
    record=dict(protocol=protocol,fingerprint=fingerprint,summary=summary,raw_file=data.name,raw_sha256=sha256(data.read_bytes()).hexdigest())
    temporary=receipt.with_suffix(".tmp");temporary.write_text(e.dumps(record)+"\n");temporary.replace(receipt)
    return record


def _basin_worker(arg):
    item,years,raw,frozen=arg
    return basin_case(item,years,raw,frozen)


def integrate_basin(initial,p,years,sample_times=None):
    """Use the frozen positive coordinates with a bounded stiff endpoint solver.

    The private namespace changes only solve_ivp's numerical backend. The scaled
    Newton matrix avoids pathological automatic differencing of rare stocks.
    Exactly absent guilds stay on their invariant face; every initially present
    guild retains its coordinate even below floating-point biomass underflow.
    """
    active=np.array([0,*[i for i in (1,2) if initial[i]>0],3,4])
    def solver(fun,span,state,**kwargs):
        def reduced(time,z):
            full=np.zeros(5);full[active]=z
            return fun(time,full)[active]
        def jacobian(time,z):
            steps=1e-5*np.maximum(abs(z),np.array([10.,1.,1.,1e-3,.01])[active])
            matrix=np.empty((len(active),len(active)))
            for i,step in enumerate(steps):
                a=z.copy();b=z.copy();a[i]+=step;b[i]-=step
                matrix[:,i]=(reduced(time,a)-reduced(time,b))/(2*step)
            return matrix
        tolerance=np.asarray(kwargs["atol"]).copy();tolerance[3]=1e-13
        kwargs.update(method="Radau",max_step=1000.,jac=jacobian,atol=tolerance[active])
        result=solve_ivp(reduced,span,state[active],**kwargs)
        expanded=np.zeros((5,len(result.t)));expanded[active]=result.y;result.y=expanded
        return result
    namespace=core.integrate.__globals__.copy();namespace["solve_ivp"]=solver
    function=FunctionType(core.integrate.__code__,namespace,core.integrate.__name__,core.integrate.__defaults__,core.integrate.__closure__)
    function.__kwdefaults__=core.integrate.__kwdefaults__
    return function(initial,p,years,sample_times=sample_times)


def mechanism(output):
    components=[];slopes=[]
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(12,3.5),constrained_layout=True)
    for ax,loss in zip(axes,(3e-4,1e-3,3e-3)):
        p=params(0.,loss);ts=switch_at(loss);grid=np.linspace(273.,303.15,400)
        for index,name in enumerate(("acetogen","methanogen")):
            ax.plot(grid,[guilds(t-273.15,p.biology)[index].rstar(loss) for t in grid],label=name)
        ax.axvline(ts,color=".5",ls=":");ax.set_ylim(0,350);ax.axhline(300.,color=".6",ls="--",lw=.8)
        ax.set_title(f"L={loss:g}/hour; switch={ts:.2f} K")
        ax.set_xlabel("Temperature (K)");ax.grid(alpha=.2)
        pair=guilds(ts-273.15,p.biology);temperature_components=[];loss_derivatives=[]
        for index,(name,g) in enumerate(zip(("acetogen","methanogen"),pair)):
            q=g.maintenance+loss/g.yield_g_mol;h=1e-4
            minus=guilds(ts-273.15-h,p.biology)[index];plus=guilds(ts-273.15+h,p.biology)[index]
            d=lambda key:(getattr(plus,key)-getattr(minus,key))/(2*h)
            terms=dict(threshold=d("threshold_pa"),affinity=d("km_pa")*q/(g.rate_scale-q),
                maintenance=g.km_pa*g.rate_scale*d("maintenance")/(g.rate_scale-q)**2,
                capacity=-g.km_pa*q*d("rate_scale")/(g.rate_scale-q)**2)
            temperature_components.append(terms)
            derivative=g.km_pa*g.rate_scale/(g.yield_g_mol*(g.rate_scale-q)**2);loss_derivatives.append(derivative)
            components.append(dict(loss_h=loss,switch_temperature_k=ts,guild=name,threshold_pa=g.threshold_pa,
                affinity_pa=g.km_pa,capacity_mol_g_h=g.rate_scale,maintenance_mol_g_h=g.maintenance,yield_g_mol=g.yield_g_mol,
                turnover_requirement_mol_g_h=loss/g.yield_g_mol,required_uptake_mol_g_h=q,rstar_pa=g.rstar(loss),
                direct_drstar_dloss=derivative,**{f"drstar_dtemperature_{k}":v for k,v in terms.items()}))
        dtemp=sum(temperature_components[0].values())-sum(temperature_components[1].values())
        dloss=loss_derivatives[0]-loss_derivatives[1]
        h=loss*1e-4;observed=(switch_at(loss+h)-switch_at(loss-h))/(2*h)
        slopes.append(dict(loss_h=loss,switch_temperature_k=ts,analytic_dtemperature_dloss=-dloss/dtemp,
            finite_difference_dtemperature_dloss=observed,difference_temperature_derivative=dtemp,
            difference_loss_derivative=dloss,yield_ratio_a_over_m=pair[0].yield_g_mol/pair[1].yield_g_mol,
            direct_threshold_loss_derivative=0.))
    axes[0].set_ylabel("Required H₂ pressure R* (Pa)");axes[0].legend(frameon=False)
    fig.savefig(output/"mechanism.png",dpi=160);plt.close(fig)
    e.table(output/"mechanism.csv",components);e.table(output/"mechanism_slopes.csv",slopes)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage",choices=("map","basins","collect","mechanism"),default="map")
    parser.add_argument("--workers",type=int,default=4);parser.add_argument("--years",type=float,default=100000.)
    parser.add_argument("--case-id",action="append");parser.add_argument("--raw-dir",type=Path,default=RAW)
    parser.add_argument("--output",type=Path,default=OUTPUT)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True);frozen=sources()
    if args.stage=="map":
        tasks=[(i,f,float(L)) for i,(f,L) in enumerate((f,L) for f in FRACTIONS for L in LOSSES)]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:results=list(pool.map(map_case,tasks))
        e.table(args.output/"regimes_summary.csv",[r[0] for r in results]);e.table(args.output/"regimes.csv",[s for r in results for s in r[1]])
        events=boundaries()
        (args.output/"boundaries.json").write_text(e.dumps(dict(source_sha256=frozen,boundaries=events,
            qualification="All thermal crossings are separate from planetary feasibility; the 274.002K plateau supports neutral mixed continua at exact equality"))+"\n")
        points=resolved_points(events)
        e.table(args.output/"regimes_resolved_points.csv",points)
        extra=[map_case((p["profile_id"],p["fraction"],p["loss_h"])) for p in points if p["sampling"]!="planned_grid"]
        e.table(args.output/"regimes_resolved.csv",[s for r in extra for s in r[1]])
        _regime_plot([r[0] for r in results]+[dict(r[0],sampling="root_delimited_interval") for r in extra],args.output)
        (args.output/"regimes_manifest.json").write_text(e.dumps(dict(source_sha256=frozen,profiles=len(results),equilibria=sum(len(r[1]) for r in results),
            fractions=FRACTIONS,losses=LOSSES,grid_refinement="Every501-point inventory agrees with1001 points",
            bistable_profiles=sum(r[0]["stable_equilibria"]>1 for r in results),additional_resolved_profiles=len(extra),
            additional_bistable_profiles=sum(r[0]["stable_equilibria"]>1 for r in extra)))+"\n")
    elif args.stage=="mechanism":mechanism(args.output)
    else:
        tasks=basin_tasks()
        if args.case_id:
            tasks=[t for t in tasks if t["case_id"] in args.case_id]
            if len(tasks)!=len(args.case_id):raise ValueError("Unknown basin selection")
        if args.stage=="basins":
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                for i,r in enumerate(pool.map(_basin_worker,[(t,args.years,args.raw_dir,frozen) for t in tasks]),1):print(i,len(tasks),r["summary"]["case_id"],r["summary"]["converged"],flush=True)
        records=[]
        for item in tasks:
            candidates=[]
            for path in args.raw_dir.glob(item["case_id"]+"_t*.receipt.json"):
                record=json.loads(path.read_text())
                if record["protocol"]["source_sha256"]!=frozen:continue
                if sha256((args.raw_dir/record["raw_file"]).read_bytes()).hexdigest()!=record["raw_sha256"]:raise RuntimeError("Changed basin payload")
                candidates.append(record)
            if not candidates:raise RuntimeError("Incomplete basin batch")
            records.append(max(candidates,key=lambda r:r["protocol"]["years"]))
        suffix="_selection" if args.case_id else ""
        e.table(args.output/("basins"+suffix+".csv"),[r["summary"] for r in records])
        (args.output/("basins"+suffix+"_manifest.json")).write_text(e.dumps(dict(source_sha256=frozen,profiles=len(records),
            unresolved=[r["summary"]["case_id"] for r in records if not r["summary"]["converged"]],
            receipts=[{k:r[k] for k in ("fingerprint","raw_file","raw_sha256")} for r in records]))+"\n")


def _regime_plot(rows,output):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    labels=sorted(set(r["regime"] for r in rows));colors=plt.cm.tab10(np.arange(len(labels)))
    fig,ax=plt.subplots(figsize=(9,4),constrained_layout=True)
    for label,color in zip(labels,colors):
        group=[r for r in rows if r["regime"]==label]
        ax.scatter([r["loss_h"] for r in group],[r["fraction"] for r in group],c=[color],label=label,s=30)
        extra=[r for r in group if r.get("sampling")=="root_delimited_interval"]
        ax.scatter([r["loss_h"] for r in extra],[r["fraction"] for r in extra],facecolors="none",edgecolors=[color],s=80,marker="s")
    ax.set_xscale("log");ax.set_xlabel("Cell loss L (per hour)");ax.set_ylabel("Acetate converted to methane")
    ax.legend(frameon=False,fontsize=8,bbox_to_anchor=(1.02,1),loc="upper left");ax.grid(alpha=.15)
    fig.savefig(output/"regimes.png",dpi=160);plt.close(fig)


if __name__=="__main__":main()
