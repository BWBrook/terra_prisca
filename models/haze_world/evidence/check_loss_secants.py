"""Recompute the finite read-off elasticities from published Akahori2024 Fig. 6a.

uv run python models/haze_world/evidence/check_loss_secants.py
Original source image and PDF remain in ignored local storage.
"""

import csv
import json
import math
from pathlib import Path

root = Path(__file__).resolve().parent
metadata = json.loads((root / "akahori2024_secants.json").read_text())
with (root / "akahori2024_figure6a_points.csv").open() as handle:
    points = list(csv.DictReader(handle))
calibration = metadata["calibration"]
x_step = calibration["flux10_x"] - calibration["flux1_x"]
y_step = (calibration["pCH4_1e_minus6_y"] - calibration["pCH4_1e_minus2_y"]) / 4
assert len(points) == 6
for result in metadata["secants"]:
    pair = [p for p in points if float(p["co2_bar"]) == result["co2_bar"]]
    first, last = pair
    dx = float(last["x_native_px"]) - float(first["x_native_px"])
    dy = float(first["y_native_px"]) - float(last["y_native_px"])
    slope = math.log(float(last["flux_tmol_c_yr"]) / float(first["flux_tmol_c_yr"])) / math.log(
        float(last["p_ch4_bar"]) / float(first["p_ch4_bar"])
    )
    lower = (dx - 10) * (y_step - 1) / ((x_step + 4) * (dy + 10))
    upper = (dx + 10) * (y_step + 1) / ((x_step - 4) * (dy - 10))
    assert abs(slope - result["elasticity_secant"]) < 1e-12
    assert abs(lower - result["lower_digitization_envelope"]) < 1e-12
    assert abs(upper - result["upper_digitization_envelope"]) < 1e-12
    assert 0 < lower < slope < upper < 0.5
    assert all(float(p["ch4_co2_ratio"]) < 0.03 for p in pair)
    print(f"CO2 {result['co2_bar']:.2f} bar: secant {slope:.3f}, read-off envelope {lower:.3f}–{upper:.3f}")
