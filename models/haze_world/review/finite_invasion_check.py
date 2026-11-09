"""Finite-population reading of the reference acetogen invasion (population coupling).

uv run python models/haze_world/review/finite_invasion_check.py
Global habitat = habitat_l_cm2 x Earth surface; one cell taken as 3e-13 gDW. Reports when each
guild first falls below 1, 1e6 and 1e12 global cells, then removes methanogens at that point
and finds the acetogen-only endpoint for f_ac = 0, 0.5, 0.9, with methanogen invadability.
"""

import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from terra_prisca.haze_world.population_coupling import equilibrium_states, integrate, reference
from terra_prisca.haze_world.methane_budget import temperature_k

HERE = Path(__file__).resolve().parent
EARTH_CM2 = 5.1e18
CELL_GDW = 3e-13


def main():
    p = reference(.3)
    control = next(e for e in equilibrium_states(replace(p, enabled=(False, True)))
                   if e["kind"] == "methanogen" and e["stable"])
    y0 = control["y"].copy()
    y0[1] = 1e-12
    ts = np.linspace(0, 1e5, 20001)
    res = integrate(y0, p, 1e5, ts)
    temps = np.array([float(temperature_k(r, p.climate)) for r in res.y[4]])
    one_cell = float(np.log(CELL_GDW / (p.habitat_l_cm2 * EARTH_CM2)))
    crossings = {}
    for name, series in zip(("acetogen", "methanogen"), res.log_biomass):
        crossings[name] = {f"{n:.0e}_cells": (float(ts[np.argmax(series < one_cell + np.log(n))])
                                              if np.any(series < one_cell + np.log(n)) else None)
                           for n in (1.0, 1e6, 1e12)}
    t_ext = crossings["methanogen"]["1e+00_cells"]
    y = res.y[:, np.searchsorted(ts, t_ext)].copy()
    y[2] = 0.0
    endpoints = []
    for f in (0.0, 0.5, 0.9):
        q = replace(p, enabled=(True, False), acetate_fraction=f)
        end = integrate(y, q, 2e5, np.linspace(0, 2e5, 2001))
        t_end = float(temperature_k(end.y[4, -1], q.climate))
        endpoints.append(dict(acetate_fraction=f, end_t_k=t_end, end_ln_acetogen=float(end.log_biomass[0, -1]),
                              methanogen_could_reinvade=t_end > 281.534823,
                              equilibria=[dict(kind=e["kind"], t_k=e["t_k"], stable=bool(e["stable"]))
                                          for e in equilibrium_states(q)]))
    out = dict(control_t_k=control["t_k"], mixed_t_k=281.534823, ln_one_global_cell=one_cell,
               first_below=crossings, methanogen_extinct_yr=t_ext,
               min_ln_biomass=dict(acetogen=float(res.log_biomass[0].min()), methanogen=float(res.log_biomass[1].min())),
               temperature_range_k=[float(temps.min()), float(temps.max())], acetogen_only_endpoints=endpoints)
    (HERE / "finite_invasion_check.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
