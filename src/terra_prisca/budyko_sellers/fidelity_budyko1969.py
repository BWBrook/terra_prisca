"""Score the Budyko (1969) reconstruction against the published figures and text.

    uv run python -m terra_prisca.budyko_sellers.fidelity_budyko1969 [PDF] [outdir]

Needs the Tellus A PDF identified in scan_budyko1969.py. For every printed
curve, traced separately from the scan, two scores are reported:
- column error: where the printed curve is single-valued, the printed value in
  each pixel column against the model at the same abscissa, in data units
  (deg C, or degrees of latitude for the ice edge);
- two-way distance: from model samples to the traced ink and from the traced
  ink to the model, in pixels (about 0.09 deg C and 0.17-0.19 deg of latitude
  per pixel; see the fidelity table for each figure's scale).
The faithful reading is scored with the controls that the score must reject:
no ice-albedo feedback, no change from the present, and the readings of
eqs (5)-(7) that the faithful one was chosen over.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .budyko1969 import LAT as GRID
from .budyko1969 import Budyko1969, hemispheric_mean, model
from .digitise import chamfer, column_median
from .scan_budyko1969 import DEFAULT_PDF, FRAMES, fig2_points, load

LAT = np.linspace(0.0, 90.0, 1801)
EPS_FIG4 = {"T0": 0.0, "T1.0": -0.010, "T1.5": -0.015}
PHI0_OFFSET = 50.0  # Fig. 5 shares one vertical scale: phi_0 = T_p + 50


def fig5_curves(m: Budyko1969, eps_range=(0.0, -0.0175)) -> dict[str, np.ndarray]:
    """T_p and phi_0 against eps on the stable branch, then the vertical runaway."""
    b = m.branch(np.arange(m.p.edge_now, 5.0, -0.02))
    i = int(np.argmin(b["eps"]))
    eps, tp, edge = b["eps"][: i + 1], b["tp"][: i + 1], b["edge"][: i + 1]
    keep = eps >= eps_range[1]
    eps, tp, edge = eps[keep], tp[keep], edge[keep]
    drop = np.linspace(0, 1, 50)
    tp_curve = np.column_stack([np.r_[eps, np.full(50, eps[-1])], np.r_[tp, tp[-1] + drop * (-30 - tp[-1])]])
    phi_curve = np.column_stack([np.r_[eps, np.full(50, eps[-1])],
                                 np.r_[edge, edge[-1] + drop * (25 - edge[-1])] - PHI0_OFFSET])
    return {"Tp": tp_curve, "phi0": phi_curve}


def model_curves(m: Budyko1969 | None, control: str | None = None) -> dict[tuple[str, str], np.ndarray]:
    """Model counterparts of the printed curves, in each figure's data units.

    control: None (the model as given), "no feedback" (ice edge held at 72 deg)
    or "no change" (the present state offered for every perturbed curve)."""
    m = m or model()
    out = {}
    t0 = m.profile(LAT)
    out[("fig3", "T0")] = np.column_stack([LAT, t0])
    for name, eps in EPS_FIG4.items():
        if eps == 0.0 or control == "no change":
            y = t0
        elif control == "no feedback":
            y = m.zonal_temperature(m.insolation(LAT), m.present_albedo(LAT), m.tp_now + m.delta_tp(eps, m.p.edge_now), eps)
        else:
            y = m.profile(LAT, eps)
        out[("fig4", name)] = np.column_stack([LAT, y])
    out[("fig6", "T0")] = np.column_stack([LAT, t0])
    out[("fig6", "Tq")] = np.column_stack([LAT, t0 if control else m.ice_free(LAT)])
    if control is None:
        out[("fig3", "T observed")] = np.column_stack([LAT, t0])
    if control is None:
        out.update({("fig5", k): v for k, v in fig5_curves(m).items()})
    else:
        eps = np.linspace(0.0, -0.0175, 200)
        tp = m.tp_now + (0 if control == "no change" else np.array([m.delta_tp(e, m.p.edge_now) for e in eps]))
        out[("fig5", "Tp")] = np.column_stack([eps, np.broadcast_to(tp, eps.shape)])
        out[("fig5", "phi0")] = np.column_stack([eps, np.full_like(eps, m.p.edge_now - PHI0_OFFSET)])
    return out


PRESENT = {("fig3", "T0"), ("fig3", "T observed"), ("fig4", "T0"), ("fig6", "T0")}


def score(scan, curves: dict, label: str, skip=frozenset()) -> list[dict]:
    rows = []
    for key, mc in curves.items():
        if key not in scan.curves or key in skip:
            continue
        fr = scan.frames[key[0]]
        ink = scan.curves[key]
        printed = column_median(ink, fr)
        xlo, xhi = np.sort(fr.x.value([ink[:, 0].min(), ink[:, 0].max()]))
        mc = mc[(mc[:, 0] >= xlo) & (mc[:, 0] <= xhi)] if key[0] != "fig5" else mc[mc[:, 0] >= xlo]
        o = np.argsort(mc[:, 0], kind="stable")
        xs, ys = mc[o, 0], mc[o, 1]
        single = np.r_[True, np.diff(xs) > 0]
        err = np.interp(printed[:, 0], xs[single], ys[single]) - printed[:, 1]
        to_ink, to_model = chamfer(fr.to_px(mc), ink)
        rows.append({"reading": label, "figure": key[0], "curve": key[1], "columns": len(printed),
                     "rmse": round(float(np.sqrt(np.mean(err ** 2))), 2),
                     "median_abs": round(float(np.median(np.abs(err))), 2),
                     "max_abs": round(float(np.abs(err).max()), 2),
                     "model_to_ink_median_px": round(float(np.median(to_ink)), 1),
                     "model_to_ink_p95_px": round(float(np.percentile(to_ink, 95)), 1),
                     "ink_to_model_median_px": round(float(np.median(to_model)), 1),
                     "ink_to_model_p95_px": round(float(np.percentile(to_model, 95)), 1),
                     "within_3px": round(float(np.mean(np.r_[to_ink, to_model] <= 3)), 3)})
    return rows


def printed_vs_printed(scan) -> list[dict]:
    """The paper's own curves against each other: Fig. 3 observed T against the
    computed T0 (Budyko's 'good agreement'), and T0 as drawn in Figs 3, 4 and 6."""
    rows = []
    med = {k: column_median(v, scan.frames[k[0]]) for k, v in scan.curves.items()}
    pairs = [(("fig3", "T observed"), ("fig3", "T0")), (("fig4", "T0"), ("fig3", "T0")),
             (("fig6", "T0"), ("fig3", "T0")), (("fig6", "T0"), ("fig4", "T0")),
             (("fig3", "T observed"), ("fig4", "T0"))]
    for ref, other in pairs:
        a, b = med[ref], med[other]
        lo, hi = max(a[:, 0].min(), b[:, 0].min()), min(a[:, 0].max(), b[:, 0].max())
        x = np.linspace(lo, hi, 200)
        d = np.interp(x, *a[np.argsort(a[:, 0])].T) - np.interp(x, *b[np.argsort(b[:, 0])].T)
        rows.append({"reading": "printed vs printed", "figure": f"{ref[0]} {ref[1]}", "curve": f"{other[0]} {other[1]}",
                     "columns": len(x), "rmse": round(float(np.sqrt(np.mean(d ** 2))), 2),
                     "median_abs": round(float(np.median(np.abs(d))), 2), "max_abs": round(float(np.abs(d).max()), 2)})
    return rows


def key_numbers(scan, m: Budyko1969) -> list[dict]:
    """Stated and printed numbers against the reconstruction."""
    med = {k: column_median(v, scan.frames[k[0]]) for k, v in scan.curves.items() if k[1] != "vertical"}
    tp_ink, phi_ink = med[("fig5", "Tp")], med[("fig5", "phi0")]

    def printed_at(c, eps, offset=0.0):
        o = np.argsort(-c[:, 0])
        return float(np.interp(-eps, -c[o, 0], c[o, 1])) + offset

    vert = scan.curves[("fig5", "vertical")]
    crit = m.critical()
    pts = fig2_points(scan)
    rows = [
        ("beta from Fig. 2 points (kcal cm-2 month-1 K-1)", "0.235 (text)", float(np.polyfit(*pts.T, 1)[0]), m.p.beta),
        ("dT_p per 1% radiation, fixed albedo 0.33 (deg C)", "1.5 (text)", None, m.fixed_albedo_sensitivity(0.33)),
        ("present T_p (deg C)", "Fig. 5", printed_at(tp_ink, -0.0002), m.tp_now),
        ("present ice edge (deg)", "72 (text)", printed_at(phi_ink, -0.0002, PHI0_OFFSET), m.p.edge_now),
    ]
    for eps, text_dtp in ((-0.010, "-5 (text)"), (-0.015, "-9 (text)")):
        edge = m.stable_edge(eps)
        rows.append((f"dT_p at {eps:.1%} (deg C)", text_dtp, printed_at(tp_ink, eps) - printed_at(tp_ink, -0.0002),
                     m.delta_tp(eps, edge)))
        rows.append((f"ice edge at {eps:.1%} (deg)", "shift 10-18 deg from 72 (text)",
                     printed_at(phi_ink, eps, PHI0_OFFSET), edge))
    branch = m.branch(np.arange(m.p.edge_now, 50.0, -0.01))
    for edge in (65.0, 60.0, 55.0):
        o = np.argsort(phi_ink[:, 1])
        printed_eps = float(np.interp(edge - PHI0_OFFSET, phi_ink[o, 1], phi_ink[o, 0]))
        rows.append((f"dQ_p/Q_p holding the ice edge at {edge:.0f} deg", "Fig. 5", printed_eps,
                     float(np.interp(edge, branch["edge"][::-1], branch["eps"][::-1]))))
    rows += [
        ("critical dQ_p/Q_p (runaway)", "-1.6% (text)", float(scan.frames["fig5"].x.value(np.median(vert[:, 0]))), crit["eps"]),
        ("ice edge at the critical point (deg)", "about 50 (text)", None, crit["edge"]),
        ("ice-free polar mean, 80-90 deg (deg C)", "several degrees below zero (text)",
         float(np.mean(np.interp(np.linspace(80, 85, 6), *med[("fig6", "Tq")][np.argsort(med[("fig6", "Tq")][:, 0])].T))),
         float(m.ice_free(np.linspace(80, 90, 101)).mean())),
    ]
    return [{"quantity": q, "stated": s, "printed": None if p is None else round(p, 4), "reconstruction": round(r, 4)}
            for q, s, p, r in rows]


READINGS = {
    "faithful": {},
    "alt: area-mean planetary albedo": {"planetary_albedo": "area"},
    "alt: 365.25/12-day month": {"month_days": 365.25 / 12},
    "alt: 365.25/12-day month, area-mean planetary albedo": {"month_days": 365.25 / 12, "planetary_albedo": "area"},
    "alt: stepped present-day albedo": {"present_albedo": "step"},
    "alt: albedo profile translated with the edge": {"ice_albedo": "translate"},
    "alt: S counted over the whole globe": {"s_area_factor": 0.5},
}


def threshold_readings(scan) -> dict[str, dict]:
    """Ice-onset temperature: the present T0 profile at 72 deg, or the observed curve of Fig. 3 there."""
    obs = column_median(scan.curves[("fig3", "T observed")], scan.frames["fig3"])
    o = np.argsort(obs[:, 0])
    return {
        "alt: ice threshold from the model's present T0 at 72 deg": {"t_edge": float(model().profile(72.0))},
        "alt: ice threshold from the observed T at 72 deg (Fig. 3)": {"t_edge": float(np.interp(72.0, *obs[o].T))},
    }


def reading_summary(readings: dict[str, dict]) -> list[dict]:
    """For each reading: present T_p, global closure of the present state, ice threshold and runaway point."""
    rows = []
    for label, kw in readings.items():
        m = model(**kw)
        c = m.critical()
        rows.append({"reading": label, "alpha_p": round(m.alpha_p_now, 5), "Tp": round(m.tp_now, 4),
                     "mean_T0_minus_Tp": round(hemispheric_mean(m.profile(GRID)) - m.tp_now, 4),
                     "t_edge": round(float(m.t_edge), 4), "critical_eps": round(c["eps"], 5),
                     "critical_edge": round(c["edge"], 2)})
    return rows


def overlay(scan, curves: dict, path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(12, 11))
    for ax, fig_name in zip(axes.flat, ("fig3", "fig4", "fig5", "fig6")):
        fr = scan.frames[fig_name]
        x0, x1, y0, y1 = fr.box
        page = scan.pages[FRAMES[fig_name][0]]
        ax.imshow(page[y0 - 40:y1 + 20, x0 - 90:x1 + 20], cmap="gray_r", alpha=0.45,
                  extent=(x0 - 90, x1 + 20, y1 + 20, y0 - 40))
        for (f, name), mc in curves.items():
            if f == fig_name:
                px = fr.to_px(mc)
                ax.plot(px[:, 0], px[:, 1], "-", color="red", lw=1.0, alpha=0.8)
        ax.set_title(f"Budyko (1969) {fig_name.replace('fig', 'Fig. ')}: scan (grey), reconstruction (red)", fontsize=9)
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main(pdf: Path, outdir: Path) -> None:
    scan = load(pdf)
    outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    readings = READINGS | threshold_readings(scan)
    for label, kw in readings.items():
        rows += score(scan, model_curves(model(**kw)), label)
    m = model()
    for control in ("no feedback", "no change"):
        rows += score(scan, model_curves(m, control), f"null: {control}", skip=PRESENT)
    rows += score(scan, {("fig3", "T0"): column_median(scan.curves[("fig3", "T observed")], scan.frames["fig3"])},
                  "null: observed T offered as T0")
    rows += printed_vs_printed(scan)
    fields = list(rows[0])
    with (outdir / "budyko1969_fidelity.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    summary = reading_summary(readings)
    with (outdir / "budyko1969_readings.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(summary)
    keys = key_numbers(scan, m)
    with (outdir / "budyko1969_numbers.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(keys[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(keys)
    with (outdir / "budyko1969_printed_curves.csv").open("w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["figure", "curve", "x", "y"])
        for (f, name), ink in scan.curves.items():
            if name != "vertical":
                for x, y in column_median(ink, scan.frames[f]):
                    w.writerow([f, name, round(float(x), 5), round(float(y), 3)])
    overlay(scan, model_curves(m), outdir / "budyko1969_overlay.png")
    for r in rows:
        print(r)
    for k in keys + summary:
        print(k)


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PDF,
         Path(sys.argv[2]) if len(sys.argv) > 2 else Path("models/budyko_sellers/fidelity"))
