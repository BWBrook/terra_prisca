import csv
from pathlib import Path

import pytest

DATA = Path(__file__).resolve().parents[1] / "models/haze_response/eager_nash2023/figure5.csv"


def test_source_grid_and_absolute_temperature_reconstruction():
    with DATA.open() as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 36
    for case in ("EN100", "EN300", "EN1000", "EN3000"):
        subset = [r for r in rows if r["case"] == case]
        assert [int(r["p_ch4_pa"]) for r in subset] == [0, 1, 3, 10, 30, 100, 300, 1000, 3500]
        for r in subset:
            assert float(r["ch4_co2_ratio"]) == pytest.approx(float(r["p_ch4_pa"]) / float(r["p_co2_pa"]))
            assert float(r["temperature_k"]) == pytest.approx(float(r["baseline_k"]) + float(r["warming_k"]), abs=0.0002)


def test_recovered_zero_methane_checkpoint_is_not_the_assumed_265k_bridge():
    with DATA.open() as fh:
        row = next(r for r in csv.DictReader(fh) if r["case"] == "EN1000" and r["p_ch4_pa"] == "0")
    assert float(row["temperature_k"]) == pytest.approx(278.67, abs=0.02)
