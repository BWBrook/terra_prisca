import pytest

from terra_prisca.haze_world.paper_figures import table_s1


def test_reported_literal_guard_rejects_changed_setting(tmp_path, monkeypatch):
    monkeypatch.setattr(table_s1, "PKG", tmp_path)
    source = tmp_path / "producer.py"
    source.write_text("def roots(f, a, b):\n    return brentq(f,a,b,xtol = .0000000000001)\n")
    location = table_s1.checked_loc("producer.py", "brentq(f, a, b, xtol=1e-13)")
    assert location.endswith(":2 (parsed setting checked)")

    source.write_text("old_tolerance = 1e-13\ndef roots(f,a,b):\n    return brentq(f,a,b,xtol=1e-8)\n")
    with pytest.raises(ValueError, match="Reported Table S1 setting changed"):
        table_s1.checked_loc("producer.py", "brentq(f, a, b, xtol=1e-13)")
