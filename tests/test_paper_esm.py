import json

import numpy as np

from terra_prisca.haze_world import population_coupling as core
from terra_prisca.haze_world import two_guilds
from terra_prisca.haze_world.paper_figures import esm_tables as esm


def test_atmospheric_input_matches_independent_mixture_boundary(tmp_path, monkeypatch):
    audit = json.loads((esm.AUDITS / "readiness-h2-2026-11-12.json").read_text())
    reference = next(r for r in audit["fixed_independent"]
                     if r["fraction"] == .5 and r["atmosphere_pa"] == 0)
    boundary = reference["upper_reference_branch_pressure_pa"]
    assert np.isclose(boundary, 157.326965402655, rtol=0, atol=1e-6)
    bud = esm.coexistence_budget()
    inferred = (bud["high"](.5) - .3) * bud["j_ref"] / (.3 * bud["k_ex"])
    assert np.isclose(inferred, boundary, rtol=0, atol=1e-6)

    p = core.reference()
    pair = two_guilds.guilds(reference["temperature_k"] - 273.15, p.biology)
    uptake = np.array([g.maintenance + p.biology.loss_h / g.yield_g_mol for g in pair])
    methane_equivalents = uptake - p.biology.loss_h * np.array([g.assimilation_mol_g for g in pair])
    methane_equivalents[0] *= .5
    needed = methane_equivalents @ np.array([reference["XA"], reference["XM"]])
    records = []
    for pressure, expected in ((boundary - 1, True), (boundary + 1, False), (160., False)):
        captured = bud["j_ref"] + bud["k_ex"] * (pressure - reference["local_h2_pa"])
        biomasses = np.linalg.solve(np.stack([uptake, methane_equivalents]), [captured, needed])
        positive = bool(np.all(biomasses > 0))
        assert positive == expected
        records.append(dict(chemistry="fixed", fraction=.5, atmosphere_pa=pressure,
                            status="mixed" if positive else "none", found=[]))
    (tmp_path / "atmospheric_h2_check.json").write_text(json.dumps(dict(rows=records)))
    table = []
    monkeypatch.setattr(esm, "REVIEW", tmp_path)
    monkeypatch.setattr(esm, "write_csv", lambda path, rows, columns: table.extend(rows))
    monkeypatch.setattr(esm, "splice", lambda *args: None)
    esm.s7_hydrogen()
    assert table[-1]["equivalent zero-reservoir supply potential"] == "0.4600"
    assert table[-1]["mixed state"].startswith("none found")
