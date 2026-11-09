from pathlib import Path
import csv

import numpy as np
import pytest

from terra_prisca.haze_response.arney2016 import Response
from terra_prisca.haze_response.extract_arney2016 import main

DATA = Path(__file__).resolve().parents[1] / "models/haze_response/arney2016"


def test_extracted_pressures_and_ratios_use_each_atmospheres_co2():
    with (DATA / "cases.csv").open() as fh:
        co2 = {r["case"]: float(r["p_co2_bar"]) for r in csv.DictReader(fh)}
    with (DATA / "figure4.csv").open() as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 38
    for row in rows:
        assert float(row["ch4_co2_ratio"]) == pytest.approx(
            float(row["p_ch4_bar"]) / co2[row["case"]], abs=2e-8
        )


def test_curve_and_table_checkpoints_are_preserved_as_separate_targets():
    response = Response.from_csv(DATA / "figure4.csv", "B")
    assert response.temperatures_k.max() == pytest.approx(297.01, abs=0.02)
    with (DATA / "cases.csv").open() as fh:
        case = next(r for r in csv.DictReader(fh) if r["case"] == "B")
    assert float(case["table_max_clear_k"]) == 299


@pytest.mark.parametrize("case", ["A", "B", "C", "D"])
def test_interpolation_preserves_vertices_and_has_no_between_vertex_overshoot(case):
    response = Response.from_csv(DATA / "figure4.csv", case)
    np.testing.assert_array_equal(response.temperature_k(response.ratios), response.temperatures_k)
    midpoint = response.temperature_k((response.ratios[:-1] + response.ratios[1:]) / 2)
    np.testing.assert_allclose(midpoint, (response.temperatures_k[:-1] + response.temperatures_k[1:]) / 2)
    assert isinstance(response.temperature_k(float(response.ratios[0])), float)


@pytest.mark.parametrize("query", [0.0, 0.3, np.nan, np.inf, [0.18, 0.0]])
def test_missing_climate_domains_are_rejected(query):
    response = Response.from_csv(DATA / "figure4.csv", "A")
    with pytest.raises(ValueError, match="extrapolation is undefined"):
        response.temperature_k(query)


def test_missing_case_is_rejected():
    with pytest.raises(ValueError, match="No response curve"):
        Response.from_csv(DATA / "figure4.csv", "E")


def test_extractor_rejects_unidentified_source_before_writing(tmp_path):
    source = tmp_path / "different.pdf"
    source.write_bytes(b"different source")
    with pytest.raises(ValueError, match="checksum-identified"):
        main(source, tmp_path / "output")
    assert not (tmp_path / "output").exists()
