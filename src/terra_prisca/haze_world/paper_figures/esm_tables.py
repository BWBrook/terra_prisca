"""Generated tables of the electronic supplementary material.

Each table is computed from a committed output file or from the model code,
written as CSV beside esm.md, and spliced into esm.md between
<!-- table:NAME --> and <!-- /table:NAME --> markers. Run through table_s1:
uv run python -m terra_prisca.haze_world.paper_figures table_s1
"""

import csv
import json
import math
from dataclasses import replace

from .. import methane_budget as budget
from .. import population_coupling as core
from .. import two_guilds as tg

from .table_s1 import ESM, ROOT, md_table, write_csv

FIG = ROOT / "models/haze_world/figures"
REVIEW = ROOT / "models/haze_world/review"
AUDITS = ROOT / "docs/audits"
CENSOR = 1e4


def read(path):
    with path.open() as handle:
        return list(csv.DictReader(handle))


def fixed(x, sig=4):
    return "" if x in (None, "") else f"{float(x):.{sig}g}"


def tau_text(status, tau):
    if status == "finite_crossing":
        return fixed(tau)
    if status.startswith("not_detected"):
        return f"> {CENSOR:g} (censored)"
    return "0 (unstable at zero lag)" if status == "already_unstable" else status


def splice(name, text):
    path = ESM / "esm.md"
    body = path.read_text()
    start, end = f"<!-- table:{name} -->", f"<!-- /table:{name} -->"
    if start not in body or end not in body:
        raise ValueError(f"esm.md has no marker pair for {name}")
    head, rest = body.split(start, 1)
    _, tail = rest.split(end, 1)
    path.write_text(head + start + "\n\n" + text.strip() + "\n\n" + end + tail)


def s2_continuation():
    ref = core.reference()
    out = []
    for variant in ("constant_shape", "arrhenius_continuation"):
        cfg = replace(ref.biology, low_temperature_variant=variant)
        states = core.equilibrium_states(replace(ref, biology=cfg))
        mixed = next(s for s in states if s["kind"] == "mixed" and s["stable"])
        only = next(s for s in states if s["kind"] == "methanogen")
        out.append(dict(variant=variant, mixed_K=mixed["t_k"], methanogen_only_K=only["t_k"],
                        contrast_K=mixed["t_k"] - only["t_k"],
                        only_stable=only["stable"]))
    physiology = []
    for variant in ("constant_shape", "arrhenius_continuation"):
        cfg = replace(ref.biology, low_temperature_variant=variant)
        for tk in (273., 275., 277.15):
            a, m = tg.guilds(tk - 273.15, cfg)
            physiology.append({"variant": variant, "T (K)": fixed(tk, 5), "s_A": fixed(a.rate_scale),
                               "K_A (Pa)": fixed(a.km_pa), "s_M": fixed(m.rate_scale), "K_M (Pa)": fixed(m.km_pa),
                               "R*_A (Pa)": fixed(a.rstar(cfg.loss_h)), "R*_M (Pa)": fixed(m.rstar(cfg.loss_h))})
    write_csv(ESM / "s2_continuation_contrast.csv", out, list(out[0]))
    write_csv(ESM / "s2_continuation_physiology.csv", physiology, list(physiology[0]))
    contrast = [{"continuation below 277.15 K": r["variant"], "mixed state T* (K)": fixed(r["mixed_K"], 7),
                 "methanogen-only control (K)": fixed(r["methanogen_only_K"], 7),
                 "mixed minus control (K)": fixed(r["contrast_K"], 4)} for r in out]
    splice("s2_continuation", md_table(contrast, list(contrast[0])) + "\n\n" + md_table(physiology, list(physiology[0])))
    return out


def s3_resolution():
    rows = []
    for name in ("habitat_resolution_check.json", "habitat_resolution_check_large_n.json"):
        rows += json.loads((REVIEW / name).read_text())["rows"]
    rows.sort(key=lambda r: (r["dispersal_yr"], r["n"]))
    table = [{"d (yr⁻¹)": f"{r['dispersal_yr']:g}", "N": r["n"],
              "τ_c (yr)": tau_text(r["critical_lag_status"], r["critical_lag_yr"]),
              "S (K per e-fold)": fixed(r["dT_dlog_supply_k"]), "mixed-zone width (K)": fixed(r["mixed_zone_width_k"])}
             for r in rows]
    write_csv(ESM / "s3_equal_weight_resolution.csv", table, list(table[0]))
    splice("s3_resolution", md_table(table, list(table[0])))

    c1 = read(FIG / "continuum_habitats/c1_resolved.csv")
    nodes = [int(r["nodes"]) for r in c1]
    doubling = {"settings": len(c1), "converged": sum(r["status"] == "converged" for r in c1),
                "min nodes": min(nodes), "max nodes": max(nodes)}
    audit = json.loads((AUDITS / "continuum-characteristic-main-map-2026-11-12.json").read_text())
    checks = [{"state": c["case_id"], "nodes": c["nodes"], "route 1 (collocation spectrum)": tau_text(c["primary_status"], c["primary_tau_yr"]),
               "relative difference to characteristic route": "" if c["relative_tau_difference"] is None else f"{c['relative_tau_difference']:.2e}",
               "comparison": c["comparison_kind"].replace("_", " "), "passed": c["passed"]} for c in audit["selected"]]
    write_csv(ESM / "s3_characteristic_checks.csv", checks, list(checks[0]))
    splice("s3_checks", md_table(checks, list(checks[0])))
    return doubling, sum(c["passed"] for c in audit["selected"])


def classify(row):
    s, s0 = float(row["Sc"]), float(row["S0"])
    if abs(s) < 1e-6:
        return "exact, already unstable" if row["critical_lag_status"] == "already_unstable" else "exact, finite first loss"
    return "graded, reversed frozen response" if s0 > 0 else "graded"


def s4_states():
    rows = []
    for name, stage in (("c0_local_gain.csv", "C0"), ("c1_resolved.csv", "C1")):
        for r in read(FIG / "continuum_habitats" / name):
            if r["gain_status"] != "defined":
                raise ValueError("Undefined local gain in the resolved set")
            rows.append(dict(
                stage=stage, chemistry=r["chemistry"], f=r["fraction"], loss_per_h=r.get("loss_h", ""),
                supply_potential=r["nominal_potential"], sigma_K=r["sigma_k"], d_per_yr=r.get("dispersal_yr", ""), nodes=r["nodes"],
                T_star_K=r["temperature_k"], r=r["ratio"], S=r["Sc"], S0=r["S0"], G_loc=r["G_loc"],
                tau_c_status=r["critical_lag_status"], tau_c_yr=r["critical_lag_yr"], class_=classify(r)))
    order = ["exact, already unstable", "exact, finite first loss", "graded, reversed frozen response", "graded"]
    rows.sort(key=lambda r: (order.index(r["class_"]), r["stage"], r["chemistry"], float(r["f"]), r["loss_per_h"] or "", r["supply_potential"],
                             float(r["sigma_K"]), r["d_per_yr"] or ""))
    for r in rows:
        r["class"] = r.pop("class_")
    columns = ["class", "stage", "chemistry", "f", "loss_per_h", "supply_potential", "sigma_K", "d_per_yr", "nodes", "T_star_K", "r",
               "S", "S0", "G_loc", "tau_c_status", "tau_c_yr"]
    write_csv(ESM / "s4_states.csv", rows, columns)
    summary = []
    for cls in order:
        sel = [r for r in rows if r["class"] == cls]
        finite = [float(r["tau_c_yr"]) for r in sel if r["tau_c_status"] == "finite_crossing"]
        absS = [abs(float(r["S"])) for r in sel]
        summary.append({"class": cls, "states": len(sel), "C0": sum(r["stage"] == "C0" for r in sel), "C1": sum(r["stage"] == "C1" for r in sel),
                        "max |S| (K per e-fold)": f"{max(absS):.3g}", "min |S|": f"{min(absS):.3g}",
                        "finite τ_c (n)": len(finite),
                        "finite τ_c range (yr)": f"{min(finite):.3g} to {max(finite):.3g}" if finite else "",
                        "censored at 10⁴ yr (n)": sum(r["tau_c_status"].startswith("not_detected") for r in sel),
                        "unstable at zero lag (n)": sum(r["tau_c_status"] == "already_unstable" for r in sel)})
    write_csv(ESM / "s4_summary.csv", summary, list(summary[0]))
    splice("s4_summary", md_table(summary, list(summary[0])))
    bridge = [r for r in rows if r["class"] == "exact, already unstable"]
    reversed_ = [r for r in rows if r["class"] == "graded, reversed frozen response"]
    cols = ["chemistry", "f", "loss_per_h", "supply_potential", "T_star_K", "r", "S", "S0"]
    def short(rs):
        return [{c: (fixed(r[c], 6) if c in ("T_star_K", "r", "S", "S0") else r[c]) for c in cols} for r in rs]
    splice("s4_bridge", md_table(short(bridge), cols))
    splice("s4_reversed", md_table(short(reversed_), cols))
    return {c: sum(r["class"] == c for r in rows) for c in order}


def s5_dials():
    thresholds = json.loads((FIG / "graded_dials/threshold_refinement/thresholds.json").read_text())["branches"]
    brackets = []
    for b in thresholds:
        i = b["initial"]
        brackets.append({
            "branch": b["branch_id"], "initial bracket (dial)": f"{i['low_dial']:.3g} to {i['high_dial']:.3g}",
            "initial τ_c (yr)": f"{i['low_tau']:.4g} to " + (f"{i['high_tau']:.4g}" if i["high_tau"] else "> 10⁴ (censored)"),
            "refined bracket (dial)": f"{b['low_dial']:.6g} to {b['high_dial']:.6g}",
            "τ_c at ends (yr)": f"{b['low_tau']:.4g} and {b['high_tau']:.4g}",
            "|S| at ends (K per e-fold)": f"{b['price_low']:.6f} and {b['price_high']:.6f}", "evaluations": b["evaluations"], "status": b["status"]})
    write_csv(ESM / "s5_brackets.csv", brackets, list(brackets[0]))
    splice("s5_brackets", md_table(brackets, list(brackets[0])))

    states = json.loads((FIG / "graded_dials/threshold_refinement/states.json").read_text())
    pts = [{"branch": s["branch_id"], "dial": s["dial"], "τ_c (yr)": s["lag"]["tau_c"], "|S| (K per e-fold)": abs(s["Sc"]),
            "weak-mode estimate (yr)": s["weak_mode_tau_yr"], "estimate / τ_c": s["weak_mode_ratio"],
            "within factor 2": 0.5 <= s["weak_mode_ratio"] <= 2} for s in states]
    write_csv(ESM / "s5_refinement_points.csv", pts, list(pts[0]))
    failures = [p for p in pts if not p["within factor 2"]]
    counter = [{"branch": p["branch"], "dial": fixed(p["dial"], 6), "τ_c (yr)": fixed(p["τ_c (yr)"], 6), "weak-mode estimate (yr)": fixed(p["weak-mode estimate (yr)"], 6),
                "ratio": fixed(p["estimate / τ_c"], 6)} for p in failures]
    splice("s5_counterexamples", md_table(counter, list(counter[0])))

    assess = json.loads((FIG / "graded_dials/prediction_assessment.json").read_text())
    fits = [{"branch": b["branch_id"], "points": b["n"], "slope": fixed(b["slope"], 4), "R²": fixed(b["r_squared"], 4), "slope in 1 to 2.5": b["slope_in_band"]}
            for b in assess["PD2"]["branches"]]
    write_csv(ESM / "s5_power_law_fits.csv", fits, list(fits[0]))
    splice("s5_fits", md_table(fits, list(fits[0])))

    dial_rows = [r for r in read(FIG / "graded_dials/dials.csv")]
    dial_table = [{"branch": r["branch_id"], "kind": r["kind"], "dial": r["dial"], "T*_K": r["temperature_k"], "S": r["Sc"],
                   "tau_c_status": r["critical_lag_status"], "tau_c_yr": r["critical_lag_yr"], "weak_mode_ratio": r["weak_mode_ratio"]} for r in dial_rows]
    write_csv(ESM / "s5_dial_points.csv", dial_table, list(dial_table[0]))
    return len(dial_rows), len(pts), len(failures)


def coexistence_budget():
    """Supply potentials at which one group alone would balance the methane budget at T* (reference, fixed products)."""
    ref = core.reference()
    bio = ref.biology
    state = next(s for s in core.equilibrium_states(ref) if s["kind"] == "mixed" and s["stable"])
    r, tk, p = state["r"], state["t_k"], state["y"][0]
    a, m = tg.guilds(tk - 273.15, bio)
    eta = [1 - g.assimilation_mol_g * bio.loss_h / (g.maintenance + bio.loss_h / g.yield_g_mol) for g in (a, m)]
    abiotic = budget.atmosphere("B")["flux_to_ratio_per_yr"] * ref.climate.abiotic_flux
    needed = 4 * (r / ref.climate.lifetime_yr - abiotic) / (core.inventory_to_ratio(ref) * core.HOURS_PER_YEAR)
    j_ref = core.supply_h2(ref)
    outlet = bio.exchange_mol_l_h_pa * (p - bio.atmosphere_pa)
    low = .3 * (outlet + needed / eta[1]) / j_ref
    high = lambda f: float("inf") if f == 0 else .3 * (outlet + needed / (f * eta[0])) / j_ref
    return dict(low=low, high=high, j_ref=j_ref, k_ex=bio.exchange_mol_l_h_pa, p_star=p, t_star=tk)


def s7_hydrogen():
    rows = json.loads((REVIEW / "atmospheric_h2_check.json").read_text())["rows"]
    bud = coexistence_budget()
    pressure_limit = (bud["high"](.5) - .3) * bud["j_ref"] / (.3 * bud["k_ex"])
    independent = json.loads((AUDITS / "readiness-h2-2026-11-12.json").read_text())["fixed_independent"]
    recorded_limit = next(r["upper_reference_branch_pressure_pa"] for r in independent if r["fraction"] == .5)
    if not math.isclose(pressure_limit, recorded_limit, rel_tol=1e-8, abs_tol=1e-6):
        raise ValueError("Atmospheric-hydrogen endpoint disagrees with the independent budget audit")
    for pressure, expected in ((pressure_limit - 1., True), (pressure_limit + 1., False)):
        p = core.reference()
        p = replace(p, biology=replace(p.biology, atmosphere_pa=pressure))
        on_reference_branch = any(s["kind"] == "mixed" and abs(s["t_k"] - bud["t_star"]) < 1e-6
                                  for s in core.equilibrium_states(p))
        if on_reference_branch != expected:
            raise ValueError("Reference mixed-state search disagrees across the atmospheric-hydrogen endpoint")
    table = []
    for r in rows:
        mixed = r["status"] == "mixed"
        entry = {"chemistry": r["chemistry"], "f": r["fraction"], "p_atm (Pa)": f"{r['atmosphere_pa']:g}",
                 "mixed state": "yes" if mixed else "none found (other states: " + ", ".join(x["kind"] for x in r["found"]) + ")",
                 "T* (K)": fixed(r.get("temperature_k"), 7), "local H₂ (Pa)": fixed(r.get("local_h2_pa"), 6),
                 "S (K per e-fold)": "" if "dT_dlog_supply_k" not in r else f"{r['dT_dlog_supply_k']:.2e}",
                 "τ_c (yr)": "" if "critical_lag_status" not in r else tau_text(r["critical_lag_status"], r["critical_lag_yr"]),
                 "equivalent zero-reservoir supply potential": ""}
        if r["chemistry"] == "fixed":
            equivalent = .3 * (bud["j_ref"] + bud["k_ex"] * r["atmosphere_pa"]) / bud["j_ref"]
            if (bud["low"] < equivalent < bud["high"](float(r["fraction"]))) != mixed:
                raise ValueError("Equivalent-input interval disagrees with the recorded mixed-state search")
            entry["equivalent zero-reservoir supply potential"] = f"{equivalent:.4f}"
        table.append(entry)
    write_csv(ESM / "s7_atmospheric_h2.csv", table, list(table[0]))
    fixed_rows = [t for t in table if t["chemistry"] == "fixed"]
    splice("s7_h2", md_table(fixed_rows, list(fixed_rows[0])))
    products = [t for t in table if t["chemistry"] == "products"]
    return len(table), products


def s8_acetate():
    c0 = read(FIG / "continuum_habitats/c0_local_gain.csv")
    table = []
    for potential in (.24, .30, .36):
        for f in (0., .5, .9):
            p = replace(core.reference(potential), acetate_fraction=f)
            mixed = [s for s in core.equilibrium_states(p) if s["kind"] == "mixed" and s["stable"]]
            rec = [r for r in c0 if r["chemistry"] == "fixed" and float(r["fraction"]) == f and float(r["loss_h"]) == .001
                   and abs(float(r["nominal_potential"]) - potential) < 1e-9]
            if bool(mixed) != bool(rec):
                raise ValueError("Live mixed-state existence disagrees with c0_local_gain.csv")
            table.append({"supply potential": f"{potential:.2f}", "f": f"{f:g}",
                          "stable mixed state": "yes" if mixed else "none",
                          "T* (K)": fixed(mixed[0]["t_k"], 7) if mixed else "",
                          "τ_c (yr)": tau_text(rec[0]["critical_lag_status"], rec[0]["critical_lag_yr"]) if rec else ""})
    write_csv(ESM / "s8_matched_margins.csv", table, list(table[0]))
    splice("s8_margins", md_table(table, list(table[0])))

    bud = coexistence_budget()
    low = bud["low"]
    interval = []
    for f in (0., .5, .9, 1.):
        high = bud["high"](f)
        interval.append({"f": f"{f:g}", "lower end, methanogens alone": f"{low:.6f}",
                         "upper end, acetogens alone": "no upper end" if f == 0 else f"{high:.6f}",
                         "ratio upper/lower": "" if f == 0 else f"{high / low:.4f}"})
    write_csv(ESM / "s8_coexistence_interval.csv", interval, list(interval[0]))
    splice("s8_interval", md_table(interval, list(interval[0])))
    return interval


CLAIM_USE = {"C05": "S2", "C06": "S2", "C44": "S3", "C45": "S3, S4", "C52": "S3, S6", "C54": "S4", "C55": "S5, S6", "C56": "S5, S6",
             "C57": "S5", "C58": "S5, S6", "C59": "S7", "C38": "S6", "C39": "S6", "C40": "S6", "C41": "S6", "C42": "S6", "C43": "S6",
             "C46": "S6", "C47": "S6", "C48": "S6", "C49": "S6", "C50": "S6", "C51": "S6"}


def s9_claims():
    ledger = {r["id"]: r for r in read(ROOT / "models/haze_world/synthesis/claims.csv")}
    table = [{"claim": i, "status": ledger[i]["status"], "commit": ledger[i]["commit"], "used in": CLAIM_USE[i],
              "claim text": ledger[i]["claim"]} for i in sorted(CLAIM_USE)]
    write_csv(ESM / "s9_claims.csv", table, list(table[0]))
    splice("s9_claims", md_table(table, list(table[0])))
    return len(table)


def main():
    s2_continuation()
    doubling, passed = s3_resolution()
    classes = s4_states()
    n_dial, n_ref, n_fail = s5_dials()
    n_h2, _ = s7_hydrogen()
    s8_acetate()
    n_claims = s9_claims()
    return (f"S4 classes {classes}; S3 {doubling}, {passed} independent checks passed; S5 {n_dial} dial points, "
            f"{n_ref} refinement points ({n_fail} outside factor 2); S7 {n_h2} rows; S9 {n_claims} claims")
