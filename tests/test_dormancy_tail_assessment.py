from dataclasses import asdict
import json

import numpy as np
import pytest

from terra_prisca.haze_world import dormancy_experiments as runner
from terra_prisca.haze_world import dormancy_tail_assessment as tail


def example(monkeypatch):
    case = runner.Case("tail_test", "main", 0., .001, "none", 0., "A_into_M")
    p = runner.parameters(case)
    y = np.zeros((p.state_size, 3))
    y[:6] = np.array([30., 1e-3, 2e-3, 1e-4, 1e-12, 1e-12])[:, None]
    y[-1] = .2
    y[4] *= [1., .8, .6]
    data = dict(t=np.array([80000., 90000., 100000.]), y=y,
        metadata=dict(global_log_cell_conversion=np.log(1e29)),
        temperatures_k=np.full((p.n_patches, 3), 281.5), extinction_events=json.dumps([]))
    record = dict(summary=dict(settling_status="unsettled", temperature_k=281.5),
                  protocol=dict(parameters=asdict(p)))
    monkeypatch.setattr(tail.model, "rhs", lambda y, p: np.zeros_like(y))
    return record, data, p


def test_exact_affine_bank_forecast_on_irregular_saved_times():
    t = np.array([0., .3, 2., 7.])
    observed = 3.+5.*np.exp(-.4*t)
    forecast = tail.bank_forecast(t, np.array([8.]), np.array([[-.4]]), np.array([1.2]))
    assert np.allclose(forecast[0], observed, rtol=2e-15)
    assert np.allclose(tail.fit_bank(observed[None], forecast, np.array([1e-30])), 0., atol=3e-15)


def test_source_free_patch_exchange_preserves_weighted_bank_before_death():
    w = np.array([.98, .02])
    matrix = .3*(np.ones((2, 1))*w[None]-np.eye(2))-.1*np.eye(2)
    t = np.array([0., 1., 4.])
    forecast = tail.bank_forecast(t, np.array([1., 0.]), matrix, np.zeros(2))
    assert np.all(forecast >= 0)
    assert np.allclose(w@forecast, .98*np.exp(-.1*t), rtol=3e-15)
    assert forecast[1, -1] > 0


def test_bank_fit_does_not_accept_tiny_noise_as_explained_decay():
    observed = 1e-25*np.array([[1., 1.1, 1.]])
    predicted = 1e-25*np.array([[1., .9, .8]])
    normalized, range_error = tail.fit_bank(observed, predicted, np.array([1e-20]))
    assert normalized[0] < tail.STOCK_TOLERANCE
    assert range_error[0] > 1


def test_retained_source_is_not_declared_absent_after_decoded_underflow(monkeypatch):
    record, data, p = example(monkeypatch)
    data["log_active"] = np.log(data["y"][p.biomass_indices],
        out=np.full((p.n_patches, 2, 3), -np.inf), where=data["y"][p.biomass_indices] > 0)
    sigma = np.zeros((p.n_patches, 2))
    sigma[0, 0] = np.nextafter(0., 1.)
    assert sigma[0, 0]*data["y"][1, -1] == 0
    monkeypatch.setattr(tail.model, "fluxes", lambda y, p:
        dict(sigma_yr=sigma, rho_yr=np.zeros_like(sigma), dormant_loss_yr=.01))
    evidence = tail.bank_evidence(data, data["y"][:, -1], p, [4])
    bank = next(row for row in evidence["stocks"] if row["index"] == 4)
    assert bank["sampled_retained_entry_source_present"]
    assert not bank["sampled_entry_source_free"]
    assert not evidence["passed"]


def test_macro_class_preserves_total_stocks_and_occupancy(monkeypatch):
    record, data, p = example(monkeypatch)
    evidence = tail.macro_evidence(record, data, p)
    assert evidence["passed"]
    assert evidence["failing_indices"] == [4]
    assert evidence["maximum_total_guild_relative_span"] < tail.STOCK_TOLERANCE
    assert evidence["occupancy_changes"] == 0
    assert np.isinf(tail.stock_floors(p, np.log(1e29))[1][p.weights == 0]).all()


@pytest.mark.parametrize("change,failed", [
    ("total", "total_guild_stock_spans"),
    ("chemistry", "macro_stock_spans"),
    ("temperature", "temperature_span"),
    ("cull", "no_late_culls"),
    ("derivative", "macro_terminal_derivatives"),
])
def test_macro_class_retains_original_nonbank_requirements(monkeypatch, change, failed):
    record, data, p = example(monkeypatch)
    if change == "total": data["y"][4] = [1e-3, 2e-3, 3e-3]
    if change == "chemistry": data["y"][0] = [30., 31., 32.]
    if change == "temperature": data["temperatures_k"][0, -1] += .02
    if change == "cull": data["extinction_events"] = json.dumps([dict(time_yr=90000.)])
    if change == "derivative":
        def rhs(y, p):
            result = np.zeros_like(y)
            result[-1] = .001
            return result
        monkeypatch.setattr(tail.model, "rhs", rhs)
    evidence = tail.macro_evidence(record, data, p)
    assert not evidence["tests"][failed]
    assert not evidence["passed"]


def test_macro_pair_agreement_does_not_overwrite_strict_status(monkeypatch):
    record, data, p = example(monkeypatch)
    other = {key: (value.copy() if isinstance(value, np.ndarray) else value) for key, value in data.items()}
    other["y"][4] *= 2
    comparison = tail.compare_macro(record, record, data, other, p)
    assert comparison["same_macro_state"]
    assert not comparison["both_stationary"]
    assert not comparison["same_endpoint"]
    other["y"][4, -1] = 1e-3
    assert not tail.compare_macro(record, record, data, other, p)["same_macro_state"]
