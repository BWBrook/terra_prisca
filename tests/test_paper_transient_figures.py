from pathlib import Path

import matplotlib.pyplot as plt
import pytest

from terra_prisca.haze_world.paper_figures import fig4


def test_fig4_default_replots_exports_without_native_archives(monkeypatch):
    def forbidden(_):
        raise AssertionError("Default figure build must not read ignored native archives")

    def save(fig, name):
        plt.close(fig)
        return name

    monkeypatch.setattr(fig4, "census_record", forbidden)
    monkeypatch.setattr(fig4, "write", lambda *args: None)
    monkeypatch.setattr(fig4.style, "save", save)
    assert fig4.main() == "fig4"


def test_fig4_replot_rejects_export_source_mismatch(monkeypatch):
    read = fig4.read

    def wrong_source(path):
        rows = read(path)
        if Path(path).name == "fig4_trajectories.csv":
            rows[0]["census_sha256"] = "0" * 64
        return rows

    monkeypatch.setattr(fig4, "read", wrong_source)
    with pytest.raises(AssertionError):
        fig4.load_exports()
