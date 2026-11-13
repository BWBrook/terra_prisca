"""Figure 4. Arrival order decides the survivor.

(a) Global cell counts during one invasion in each direction (fixed products,
f = 0.5, tau = 3 yr). (b) Outcome of all 24 invasion runs, with the settings
whose reference mixed state is locally stable. Exports: data/fig4_*.csv.
Paths and endpoints use the archived finite-census runs, which remove a guild
below one cell at the next 10-year census. No uncensored continuation is drawn.
The default build uses committed CSV exports and verifies their source identities
against the manifest. --refresh regenerates those exports from local native NPZs.
"""

import csv
from dataclasses import replace
from hashlib import sha256
import json
import sys

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

from terra_prisca.haze_world import dynamic_realisation as dr
from terra_prisca.haze_world import dynamic_transients as dt
from terra_prisca.haze_world.finite_populations import CellProcess

from . import style

DYN = style.ROOT / "models" / "haze_world" / "figures" / "dynamic_realisation"
TMAX = 40.0
DIRS = ("A_into_M", "M_into_A")
DIR_TEXT = {"A_into_M": "acetogens invade methanogens", "M_into_A": "methanogens invade acetogens"}
RESIDENT = {"A_into_M": "methanogen", "M_into_A": "acetogen"}
SURVIVOR = {"acetogen_only": "acetogen", "methanogen_only": "methanogen"}


def read(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def write(name, rows):
    style.DATA.mkdir(parents=True, exist_ok=True)
    with open(style.DATA / name, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def mixed_stability():
    """Reference mixed state (one habitat, loss 1e-3, potential 0.3): leading real part of the
    linearisation at tau = 0, 3, 30 yr, from stability_gain.csv."""
    out = {}
    for r in read(DYN / "stability_gain.csv"):
        if (r["status"] == "accepted" and r["kind"] == "mixed" and r["sigma_k"] == "0.0" and r["n_habitats"] == "1"
                and r["nominal_potential"] == "0.3" and r["loss_h"] == "0.001" and r["branch"] == "0"
                and r["two_layer"] == "False" and r["slope_multiplier"] == "1.0" and r["lifetime_yr"] == "10000.0"
                and r["chemistry"] in ("fixed", "products")):
            for tau in ("0", "3", "30"):
                out[(r["chemistry"], float(r["fraction"]), float(tau))] = float(r[f"lambda_real_tau_{tau}"])
    assert len(out) == 12, len(out)
    return out


def census_record(record):
    path = style.ROOT / record["census_raw"]
    assert sha256(path.read_bytes()).hexdigest() == record["census_sha256"], path
    with np.load(path) as data:
        return {key: data[key] for key in ("t", "y", "log_biomass")}


def reference_inputs():
    inv = read(DYN / "invasions.csv")
    assert len(inv) == 24
    lam = mixed_stability()
    records = {r["case_id"]: r for r in json.loads((DYN / "transient_manifest.json").read_text())["rows"]}
    cases = {c.case_id: c for c in dt.design() if c.stage == "B3"}
    return inv, lam, records, cases


def refresh():
    inv, lam, records, cases = reference_inputs()
    outcomes = []
    trajectories = []
    for r in inv:
        key = (r["chemistry"], float(r["fraction"]), float(r["tau_yr"]))
        case = cases[r["case_id"]]
        assert key == (case.chemistry, case.fraction, case.tau_yr)
        assert replace(dt.parameters(case), activity_feedback="fixed") == dr.parameters(
            case.chemistry, case.fraction, 0.001, 0.30).base
        record = records[case.case_id]
        data = census_record(record)
        present = np.isfinite(data["log_biomass"][:, -1])
        endpoint = "both" if all(present) else "acetogen_only" if present[0] else "methanogen_only" if present[1] else "empty"
        assert endpoint == r["census_endpoint"] == record["census_endpoint"]
        l = lam[key]
        outcomes.append(dict(case_id=r["case_id"], chemistry=r["chemistry"], fraction=float(r["fraction"]),
                             tau_yr=float(r["tau_yr"]), direction=r["direction"],
                             census_endpoint=r["census_endpoint"], survivor=SURVIVOR[r["census_endpoint"]],
                             first_resident_below_one_cell_yr=float(r["first_%s_below_cell_yr" % RESIDENT[r["direction"]]]),
                             mixed_state_leading_real_part_per_yr=l, mixed_state_locally_stable=l < 0,
                             census_raw=record["census_raw"], census_sha256=record["census_sha256"]))
        if case.case_id in (f"B3_fixed_f0.5_tau3_{d}" for d in DIRS):
            mask = data["t"] <= TMAX
            p = dt.parameters(case)
            cells = CellProcess()
            conversion = np.log(p.habitat_l_cm2 * cells.surface_cm2 / cells.cell_mass_gdw)
            logs = (data["log_biomass"][:, mask] + conversion) / np.log(10.)
            for guild, values in zip(("acetogen", "methanogen"), logs):
                for time, value in zip(data["t"][mask], values):
                    trajectories.append(dict(case_id=case.case_id, direction=case.direction, guild=guild,
                        time_yr=time, log10_cells=float(value) if np.isfinite(value) else "",
                        present=bool(np.isfinite(value)), trace="finite_census",
                        census_raw=record["census_raw"], census_sha256=record["census_sha256"]))
    write("fig4_outcomes.csv", outcomes)
    write("fig4_trajectories.csv", trajectories)


def load_exports():
    inv, lam, records, cases = reference_inputs()
    inputs = {r["case_id"]: r for r in inv}
    outcomes = read(style.DATA / "fig4_outcomes.csv")
    assert len(outcomes) == len({o["case_id"] for o in outcomes}) == 24
    for row in outcomes:
        case = cases[row["case_id"]]
        record, source = records[case.case_id], inputs[case.case_id]
        for name in ("fraction", "tau_yr", "first_resident_below_one_cell_yr", "mixed_state_leading_real_part_per_yr"):
            row[name] = float(row[name])
        assert row["mixed_state_locally_stable"] in ("True", "False")
        row["mixed_state_locally_stable"] = row["mixed_state_locally_stable"] == "True"
        key = row["chemistry"], row["fraction"], row["tau_yr"]
        assert key == (case.chemistry, case.fraction, case.tau_yr)
        assert key == (record["chemistry"], float(record["fraction"]), float(record["tau_yr"]))
        assert key == (source["chemistry"], float(source["fraction"]), float(source["tau_yr"]))
        assert row["direction"] == case.direction == source["direction"]
        assert replace(dt.parameters(case), activity_feedback="fixed") == dr.parameters(
            case.chemistry, case.fraction, 0.001, 0.30).base
        assert row["census_endpoint"] == record["census_endpoint"] == source["census_endpoint"]
        assert row["survivor"] == SURVIVOR[row["census_endpoint"]]
        assert row["census_raw"] == record["census_raw"] and row["census_sha256"] == record["census_sha256"]
        crossing = f"first_{RESIDENT[case.direction]}_below_cell_yr"
        assert row["first_resident_below_one_cell_yr"] == float(record[crossing]) == float(source[crossing])
        assert row["mixed_state_leading_real_part_per_yr"] == lam[key]
        assert row["mixed_state_locally_stable"] == (lam[key] < 0)
    trajectories = read(style.DATA / "fig4_trajectories.csv")
    plotted = {f"B3_fixed_f0.5_tau3_{d}" for d in DIRS}
    assert {r["case_id"] for r in trajectories} == plotted
    for row in trajectories:
        record = records[row["case_id"]]
        assert row["trace"] == "finite_census" and row["direction"] == cases[row["case_id"]].direction
        assert row["census_raw"] == record["census_raw"] and row["census_sha256"] == record["census_sha256"]
        assert row["present"] in ("True", "False")
        guild = ("acetogen", "methanogen").index(row["guild"])
        removed = [event["time_yr"] for event in json.loads(record["census_events"]) if event["guild"] == guild]
        expected_present = not removed or float(row["time_yr"]) < min(removed)
        assert (row["present"] == "True") == expected_present
        if row["present"] == "True":
            assert np.isfinite(float(row["log10_cells"]))
        else:
            assert row["log10_cells"] == ""
    for case_id in plotted:
        for guild in ("acetogen", "methanogen"):
            rows = [r for r in trajectories if r["case_id"] == case_id and r["guild"] == guild]
            assert [float(r["time_yr"]) for r in rows] == list(np.arange(TMAX + 1))
    return outcomes, trajectories, lam, records


def main(do_refresh=False):
    style.apply()
    if do_refresh:
        refresh()
    outcomes, trajectories, lam, records = load_exports()
    n_a = sum(o["survivor"] == "acetogen" for o in outcomes if o["direction"] == "A_into_M")
    n_m = sum(o["survivor"] == "methanogen" for o in outcomes if o["direction"] == "M_into_A")
    assert (n_a, n_m) == (12, 12)
    assert all(o["first_resident_below_one_cell_yr"] > 0 for o in outcomes)

    fig = plt.figure(figsize=(style.DOUBLE, 80 * style.MM))
    gs = GridSpec(1, 2, figure=fig, width_ratios=[1.0, 0.82], wspace=0.34, left=0.07, right=0.995, bottom=0.14, top=0.97)
    sub = gs[0, 0].subgridspec(1, 2, wspace=0.08)
    axa = [fig.add_subplot(sub[0, 0])]
    axa.append(fig.add_subplot(sub[0, 1], sharey=axa[0]))
    axb = fig.add_subplot(gs[0, 1])

    for ax, d in zip(axa, DIRS):
        case_id = f"B3_fixed_f0.5_tau3_{d}"
        record = records[case_id]
        y = {}
        for guild in ("acetogen", "methanogen"):
            rows = [r for r in trajectories if r["case_id"] == case_id and r["guild"] == guild]
            t = np.array([float(r["time_yr"]) for r in rows])
            y[guild] = np.array([float(r["log10_cells"]) if r["present"] == "True" else np.nan for r in rows])
        t_cross = next(float(o["first_resident_below_one_cell_yr"]) for o in outcomes
                       if o["case_id"] == f"B3_fixed_f0.5_tau3_{d}")
        for g in ("acetogen", "methanogen"):
            e = style.ENTITY[g]
            solid = np.isfinite(y[g])
            ax.plot(t[solid], y[g][solid], color=e["color"], ls="-", lw=1.2, marker=e["marker"], ms=2.6,
                    markevery=4, mfc=e["color"], mec=e["color"], zorder=4)
        style.one_cell_line(ax)
        ax.plot([t_cross], [0], marker="x", color=style.INK, ms=4.5, mew=0.9, zorder=6)
        ax.annotate(f"first crossing\n{t_cross:.1f} yr", (t_cross, 0), xytext=(t_cross + 5, 14), fontsize=6, color=style.INK_2,
                    arrowprops=dict(arrowstyle="-", lw=0.4, color=style.INK_2), va="center")
        event = json.loads(record["census_events"])[0]
        ax.text(0.97, 0.27, f"resident removed\nat {event['time_yr']:g}-yr census", transform=ax.transAxes,
                fontsize=5.8, color=style.INK_2, ha="right", va="top")
        ax.text(0.5, 1.0, DIR_TEXT[d], transform=ax.transAxes, fontsize=6.3, color=style.INK_2, ha="center", va="top")
        ax.set_xlim(0, TMAX)
        ax.set_xlabel("Time after invasion (yr)")
    axa[0].set_ylim(-15, 32)
    axa[0].set_ylabel("Global cell count, log$_{10}$ (cells)")
    axa[1].tick_params(labelleft=False)
    axa[1].spines["left"].set_visible(False)
    axa[1].tick_params(axis="y", left=False)
    handles = [
        Line2D([], [], color=style.ACETOGEN, marker="o", ms=2.6, lw=1.2, label="acetogens"),
        Line2D([], [], color=style.METHANOGEN, marker="s", ms=2.6, lw=1.2, label="methanogens"),
        Line2D([], [], color=style.INK_2, ls=":", lw=0.7, label="one cell"),
    ]
    axa[0].legend(handles=handles, loc="lower left", bbox_to_anchor=(0.0, 0.0), fontsize=5.8, labelspacing=0.3, handlelength=2.2)
    style.panel_label(axa[0], "a", x=-0.28, y=0.985)

    # (b) outcome grid
    settings = [(c, f, tau) for c in ("fixed", "products") for f in (0.0, 0.5) for tau in (0.0, 3.0, 30.0)]
    cols = {"A_into_M": 0, "M_into_A": 1, "mix": 2.25}
    n = len(settings)
    byk = {(o["chemistry"], o["fraction"], o["tau_yr"], o["direction"]): o for o in outcomes}
    rows_out = []
    for i, (c, f, tau) in enumerate(settings):
        y = n - 1 - i - (0.6 if c == "products" else 0)
        for d in DIRS:
            o = byk[(c, f, tau, d)]
            e = style.ENTITY[o["survivor"]]
            axb.plot(cols[d], y, marker=e["marker"], ms=5.2, color=e["color"], ls="none", mec=e["color"])
            rows_out.append(dict(setting=f"{c}, f={f:g}, tau={tau:g}", direction=d, survivor=o["survivor"], x=cols[d], y=y))
        stable = lam[(c, f, tau)] < 0
        if stable:
            axb.plot(cols["mix"], y, marker="D", ms=4.6, color=style.INK, ls="none")
        else:
            axb.plot(cols["mix"], y, marker="_", ms=5, color=style.MUTED, ls="none", mew=1.0)
        rows_out.append(dict(setting=f"{c}, f={f:g}, tau={tau:g}", direction="mixed_state_locally_stable",
                             survivor="stable" if stable else "unstable", x=cols["mix"], y=y))
    ylabels, yt = [], []
    for i, (c, f, tau) in enumerate(settings):
        yt.append(n - 1 - i - (0.6 if c == "products" else 0))
        ylabels.append(f"f = {f:g}, τ = {tau:g}")
    axb.set_yticks(yt)
    axb.set_yticklabels(ylabels, fontsize=6)
    axb.set_xticks([0, 1, 2.25])
    axb.set_xticklabels(["acetogens\ninvade", "methanogens\ninvade", "mixture\nlocally stable"], fontsize=6.3)
    axb.set_xlim(-0.55, 2.8)
    axb.set_ylabel("")
    axb.set_ylim(-0.8, n - 0.2 + 0.2)
    axb.spines["left"].set_visible(False)
    axb.tick_params(axis="y", length=0)
    axb.tick_params(axis="x", length=0)
    axb.xaxis.set_ticks_position("top")
    axb.xaxis.set_label_position("top")
    for c, ytxt in (("fixed products", 11.55), ("products from both", 5.15)):
        pass
    axb.text(-0.55, n - 0.15, "", fontsize=1)
    axb.spines["bottom"].set_visible(False)
    axb.text(-0.30, 0.75, "fixed products", transform=axb.transAxes, fontsize=6.3, color=style.INK, ha="center", va="center", rotation=90)
    axb.text(-0.30, 0.25, "feedback from both products", transform=axb.transAxes, fontsize=6.3, color=style.INK, ha="center", va="center", rotation=90)
    axb.axhline(5.7 - 0.2, color=style.GRID, lw=0.6, xmin=0, xmax=1)
    axb.text(0.5, -0.75, "12/12 acetogen-only   |   12/12 methanogen-only", fontsize=6, color=style.INK_2, ha="center", va="top", transform=axb.transData) if False else None
    hb = [
        Line2D([], [], marker="o", color=style.ACETOGEN, ls="none", ms=5, label="acetogen only"),
        Line2D([], [], marker="s", color=style.METHANOGEN, ls="none", ms=5, label="methanogen only"),
        Line2D([], [], marker="D", color=style.INK, ls="none", ms=4.6, label="mixture stable"),
        Line2D([], [], marker="_", color=style.MUTED, ls="none", ms=5, mew=1.0, label="mixture unstable"),
    ]
    axb.legend(handles=hb, loc="upper center", bbox_to_anchor=(0.42, -0.04), ncol=2, fontsize=6, columnspacing=1.0, handletextpad=0.3)
    style.panel_label(axb, "b", x=-0.34, y=1.1)
    write("fig4_grid.csv", rows_out)
    stable_n = sum(lam[(c, f, tau)] < 0 for c, f, tau in settings)
    write("fig4_checks.csv", [dict(quantity="acetogen_invasions_ending_acetogen_only", reproduced=n_a, expected=12),
                              dict(quantity="methanogen_invasions_ending_methanogen_only", reproduced=n_m, expected=12),
                              dict(quantity="settings_with_locally_stable_mixture", reproduced=stable_n, expected="recorded, no prior count")])
    return style.save(fig, "fig4")


if __name__ == "__main__":
    print(main("--refresh" in sys.argv))
