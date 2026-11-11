"""Residual-checked real polynomial roots on a bounded dense-output interval."""

import numpy as np
from numpy.polynomial import Polynomial
from scipy.optimize import brentq


def real_roots(poly, lo, hi):
    if not np.isfinite([lo, hi]).all() or lo > hi:
        raise ValueError("Root bounds must be finite and ordered")
    if not np.isfinite(poly.coef).all():
        raise ValueError("Polynomial coefficients must be finite")
    if lo == hi or not np.any(poly.coef):
        return []
    midpoint, radius = (lo + hi) / 2, (hi - lo) / 2
    scaled = poly(Polynomial([midpoint, radius]))
    norm = float(np.max(np.abs(scaled.coef)))
    if norm == 0:
        return []
    scaled = (scaled / norm).trim(tol=32 * np.finfo(float).eps)
    tolerance = 128 * np.finfo(float).eps * float(np.sum(np.abs(scaled.coef)))
    candidates = []
    for value in scaled.roots():
        if abs(value.imag) <= 1e-8 and -1 <= value.real <= 1:
            x = float(value.real)
            if abs(scaled(x)) <= tolerance:
                candidates.append(x)
    # A sign change is independently bracketed even if the companion solve
    # loses a bounded root beside a much larger, irrelevant root.
    if scaled(-1) * scaled(1) < 0 and not candidates:
        candidates.append(brentq(scaled, -1., 1., xtol=1e-14))
    result = []
    for x in sorted(candidates):
        root = float(midpoint + radius * x)
        bound = float(Polynomial(np.abs(poly.coef))(abs(root)))
        if abs(poly(root)) <= 256 * np.finfo(float).eps * bound:
            if not result or abs(root - result[-1]) > 32 * np.finfo(float).eps * max(1., abs(root)):
                result.append(root)
    return result


def exit_time(dense, left, right, interval, ratio_index):
    lo, hi = (left - dense.t) / dense.h, (right - dense.t) / dense.h
    ratio = Polynomial(dense.yh[ratio_index])
    points = [lo, hi]
    for boundary in interval:
        if np.isfinite(boundary):
            points.extend(real_roots(ratio - boundary, lo, hi))
    for a, b in zip(np.unique(points)[:-1], np.unique(points)[1:]):
        if not interval[0] <= ratio((a + b) / 2) <= interval[1]:
            if a != lo:
                value = float(ratio(a))
                scale = max(1., abs(value), *(abs(v) for v in interval if np.isfinite(v)))
                if min(abs(value - v) for v in interval if np.isfinite(v)) > 1e-10 * scale:
                    raise RuntimeError("Dense domain-exit root does not meet a boundary")
            elif interval[0] < ratio(lo) < interval[1]:
                raise RuntimeError("Dense domain exit lacks a validated boundary root")
            return float(dense.t + dense.h * a)
    return None
