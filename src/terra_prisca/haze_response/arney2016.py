"""Interpolate the digitised Fig. 4 curves without extrapolating their domain."""

from dataclasses import dataclass
from pathlib import Path
import csv

import numpy as np


@dataclass(frozen=True)
class Response:
    case: str
    ratios: np.ndarray
    temperatures_k: np.ndarray

    @classmethod
    def from_csv(cls, path: Path | str, case: str) -> "Response":
        with Path(path).open(newline="") as fh:
            rows = [r for r in csv.DictReader(fh) if r["case"] == case]
        if len(rows) < 2:
            raise ValueError(f"No response curve for case {case!r}")
        ratios = np.array([float(r["ch4_co2_ratio"]) for r in rows])
        temps = np.array([float(r["temperature_k"]) for r in rows])
        if not np.all(np.isfinite(ratios)) or not np.all(np.diff(ratios) > 0):
            raise ValueError("Response ratios must be finite and strictly increasing")
        if not np.all(np.isfinite(temps)):
            raise ValueError("Response temperatures must be finite")
        ratios.setflags(write=False)
        temps.setflags(write=False)
        return cls(case, ratios, temps)

    def temperature_k(self, ch4_co2_ratio: float | np.ndarray) -> float | np.ndarray:
        ratio = np.asarray(ch4_co2_ratio, dtype=float)
        if np.any(~np.isfinite(ratio)) or np.any((ratio < self.ratios[0]) | (ratio > self.ratios[-1])):
            raise ValueError(
                f"Case {self.case} supports only CH4/CO2 in "
                f"[{self.ratios[0]}, {self.ratios[-1]}]; extrapolation is undefined"
            )
        result = np.interp(ratio, self.ratios, self.temperatures_k)
        return float(result) if result.ndim == 0 else result
