"""Preview: well-mixed haze-world regimes across cell turnover.

uv run python models/haze_world/review/turnover_regime_preview.py

Single-habitat equilibria (population_coupling.equilibrium_states, full local
stability) for the reference physiology with the loss rate L replaced, on 43
log-spaced values from 2e-4 to 5e-3 per hour and acetate recycling
f in {0, 0.5, 0.9}. Also locates by root-finding the L at which the switch
temperature T_sw(L) crosses the temperatures that bound the regimes. A
preview for the turnover stage, not a planned-grid result: no basin checks,
no refuges, no transients.
"""

from concurrent.futures import ProcessPoolExecutor
import dataclasses
import json
from pathlib import Path
import warnings

import numpy as np
from scipy.optimize import brentq

from terra_prisca.haze_world import population_coupling as core

OUT = Path(__file__).with_suffix(".json")
FRACTIONS = (0., .5, .9)
LOSSES = np.geomspace(2e-4, 5e-3, 43)


def params(f, loss):
    ref = core.reference()
    return dataclasses.replace(ref, acetate_fraction=f, biology=dataclasses.replace(ref.biology, loss_h=loss))


def states(arg):
    f, loss = arg
    warnings.filterwarnings("ignore")
    p = params(f, loss)
    eq = core.equilibrium_states(p)
    return dict(fraction=f, loss_h=float(loss), turnover_days=float(1 / loss / 24),
                switch_k=[float(t) for t in core.switch_temperatures(p.biology)],
                states=[dict(kind=e["kind"], temperature_k=float(e["t_k"]), r=float(e["r"]), stable=bool(e["stable"]))
                        for e in eq if e["kind"] != "lifeless"])


def switch_at(loss):
    ts = core.switch_temperatures(params(0., loss).biology)
    return ts[0] if ts else np.nan


def crossing(target, lo, hi):
    return float(np.exp(brentq(lambda x: switch_at(np.exp(x)) - target, np.log(lo), np.log(hi), xtol=1e-6)))


def main():
    with ProcessPoolExecutor(max_workers=8) as pool:
        rows = list(pool.map(states, [(f, x) for f in FRACTIONS for x in LOSSES]))
    targets = {"methanogen_haze_274.0K": (274.0, 2.4e-4, 2.6e-4), "cold_refuge_278K": (278., 3.5e-4, 6e-4),
               "f0_acetogen_world_283.2K": (283.199, 1.1e-3, 1.4e-3), "warm_refuge_286K": (286., 1.6e-3, 2.2e-3)}
    crossings = {k: crossing(*v) for k, v in targets.items()}
    OUT.write_text(json.dumps(dict(
        scope="Preview. Well-mixed equilibria with full local stability across loss rate; no basins, refuges or transients",
        loss_rate_at_switch_temperature=crossings, rows=rows), indent=1) + "\n")
    for k, v in crossings.items():
        print(f"T_sw = {k}: L = {v:.4g} /h")
    for r in rows:
        stable = ", ".join(f"{s['kind']}@{s['temperature_k']:.2f}" for s in r["states"] if s["stable"])
        print(f"f={r['fraction']} L={r['loss_h']:.2e} T_sw={[round(t, 2) for t in r['switch_k']]} stable: {stable}")


if __name__ == "__main__":
    main()
