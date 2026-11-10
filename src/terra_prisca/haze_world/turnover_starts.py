"""Conditional resident starts, including migration-maintained sink habitats."""

from dataclasses import replace

import numpy as np

from . import habitat_equilibria as eq
from . import population_coupling as core


def conditional_states(p, guild):
    conditional = replace(p, base=replace(p.base, enabled=(guild == 0, guild == 1)))
    candidates = list(eq.conditional_states(p, guild))
    qualifying = [v for v in candidates if v["stability"] == "stable"
                  and all(v["y"][4*j+1+guild] > 0 for j, w in enumerate(p.weights) if w)]
    if qualifying:
        return dict(candidates=candidates,qualifying=qualifying,attempted_refinements=0,
            search_scope="Finite zero-d branches followed into migration; not a proof of global uniqueness",
            selected=max(qualifying,key=lambda v:v["r"]))
    seeds = []
    reference = replace(conditional, base=replace(conditional.base,
                        biology=replace(conditional.base.biology, loss_h=1e-3)))
    for item in eq.conditional_states(reference, guild):
        seeds.append((item["y"], 1e-3))
    for item in core.equilibrium_states(conditional.base):
        if item["kind"] != ("acetogen" if guild == 0 else "methanogen"):
            continue
        y = np.zeros(p.state_size); y[-1] = item["r"]
        for j, w in enumerate(p.weights):
            if w:
                y[4*j:4*j+4] = item["y"][:4]
        seeds.append((y, p.base.biology.loss_h))
    attempted = 0
    for seed, start_loss in seeds:
        current = np.asarray(seed).copy()
        losses = (np.array([start_loss]) if start_loss == p.base.biology.loss_h
                  else np.linspace(start_loss,p.base.biology.loss_h,41))
        result = None
        for loss in losses:
            target = replace(conditional, base=replace(conditional.base,
                             biology=replace(conditional.base.biology, loss_h=float(loss))))
            attempted += 1
            result = eq.refine(current, target)
            if result is None:
                break
            current = result["y"]
        if result is not None and not any(abs(result["r"]-v["r"]) < 1e-8 for v in candidates):
            candidates.append(result)
    qualifying = [v for v in candidates if v["stability"] == "stable"
                  and all(v["y"][4*j+1+guild] > 0 for j, w in enumerate(p.weights) if w)]
    return dict(candidates=candidates, qualifying=qualifying, attempted_refinements=attempted,
                search_scope="Finite zero-d root search plus loss continuation and homogeneous branch seeds; not a proof of global uniqueness",
                selected=max(qualifying, key=lambda v:v["r"]) if qualifying else None)
