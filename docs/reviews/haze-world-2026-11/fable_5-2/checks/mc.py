"""Reviewer check: propagate Kotsyurbenko Table 2 95% CIs into the switch temperature."""
import csv
from dataclasses import replace
import numpy as np
from terra_prisca.haze_world import population_coupling as pc, two_guilds as tg
from terra_prisca.haze_world import hydrogen_uptake as hu

rows = list(csv.DictReader(open("models/haze_world/evidence/kotsyurbenko2001_table2.csv")))
T = np.array(tg.TEMPERATURES_C)
def table(strain):
    r = [x for x in rows if x["strain"] == strain]
    f = lambda k, d=None: np.array([float(x[k]) if x[k] else d for x in r])
    return f("Vmax_nmol_h_for20mL"), f("Vmax_95CI_halfwidth"), f("Km_Pa"), f("Km_95CI_halfwidth", np.nan)
tabs = {s: table(s) for s in (hu.ACETOGEN, hu.MSB, hu.MSP)}
# MSP 10C Km halfwidth missing: use the mean relative halfwidth of that strain
v, dv, k, dk = tabs[hu.MSP]; dk[np.isnan(dk)] = np.nanmean(dk / k) * k[np.isnan(dk)]

rng = np.random.default_rng(20261111)
current = {}
def shape(temperature_c, strain, low_temperature_variant="none"):
    v, k = current[strain]
    rel = np.interp(temperature_c, T, v) / v[-1]
    km = np.interp(temperature_c, T, k)
    if temperature_c < 4 and low_temperature_variant == "arrhenius_continuation":
        raise NotImplementedError
    return float(rel), float(km)
tg.shape = shape

def draw():
    for s, (v, dv, k, dk) in tabs.items():
        current[s] = (np.maximum(rng.normal(v, dv / 1.96), 1.), np.maximum(rng.normal(k, dk / 1.96), 1.))

ref = pc.reference().biology
LO, HI = 273.39, 297.008
for strain in (hu.MSB, hu.MSP):
    b = replace(ref, methanogen=strain)
    for s in tabs: current[s] = (tabs[s][0], tabs[s][2])
    pc.switch_temperatures.cache_clear()
    print(strain, "central", pc.switch_temperatures(b))
    res, none, multi, off = [], 0, 0, 0
    N = 4000
    for _ in range(N):
        draw(); pc.switch_temperatures.cache_clear()
        s = pc.switch_temperatures(b)
        if not s: none += 1; continue
        if len(s) > 1: multi += 1
        res.append(s[-1])
        off += not (LO < s[-1] < HI)
    res = np.array(res)
    q = np.percentile(res, [2.5, 16, 50, 84, 97.5])
    print(f"  N={N} no crossing in 273–303 K: {none/N:.3f}; multiple: {multi/N:.3f}; crossing off cooling branch: {off/N:.3f}")
    print("  switch T percentiles 2.5/16/50/84/97.5:", np.round(q, 2), " sd", round(res.std(), 2))
