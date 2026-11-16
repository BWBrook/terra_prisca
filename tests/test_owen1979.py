from pathlib import Path

import pytest

from terra_prisca.walker_hays_kasting import owen1979 as o


def test_eq5_is_an_endpoint_fit_to_owen_shifted_to_285K():
    fits = {r["owen_temperatures"]: r for r in o.fits()}
    shifted = fits["shifted to 285 K"]
    assert shifted["tg_co2_today"] == pytest.approx(2.3, abs=1e-9)       # eq. (3) closes today
    assert shifted["endpoint_exponent"] == pytest.approx(0.364, abs=0.005)  # printed 0.364
    assert shifted["lsq_exponent"] == pytest.approx(0.314, abs=0.002)     # a full fit differs
    assert 2.5 < shifted["eq5_resid_max"] < 2.8
    assert fits["as printed (290 K today)"]["tg_co2_today"] == pytest.approx(4.8, abs=1e-9)
    for other in ("as printed (290 K today)", "shifted, weak bands deleted"):
        assert abs(fits[other]["endpoint_exponent"] - 0.364) > 0.08


def test_outputs_are_reproducible(tmp_path):
    o.main(tmp_path)
    for name in ("whk1981_eq5_owen_rows.csv", "whk1981_eq5_owen_fits.csv"):
        committed = Path("models/walker_hays_kasting/fidelity") / name
        assert (tmp_path / name).read_bytes() == committed.read_bytes()
