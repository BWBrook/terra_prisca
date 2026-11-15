"""Issue 3: recount immigration-assembled endpoints from the finite-population stage.

Reads the stored 144 census-stationary endpoints (C07 design) and counts, by
acetate fraction and immigration (zero or positive), endpoints where both
guilds supply at least 1% of catabolic hydrogen use, and any
immigration-supported sinks.

Run: uv run python models/haze_world/review/issue3_immigration.py
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'models/haze_world/figures/finite_populations/attained_endpoints.csv'
OUT = Path(__file__).with_suffix('.json')


def main():
    rows = list(csv.DictReader(SOURCE.open()))
    groups = {}
    for r in rows:
        key = f"f={r['fraction']}, immigration={'positive' if float(r['relative_immigration_yr']) > 0 else 'zero'}"
        g = groups.setdefault(key, dict(n=0, both_material=0, sinks=0, temperatures_k=[], min_relative_immigration_yr=None))
        g['n'] += 1
        g['both_material'] += float(r['catabolic_share_a']) >= .01 and float(r['catabolic_share_m']) >= .01
        g['sinks'] += r['immigration_supported_sink_a'] == 'True' or r['immigration_supported_sink_m'] == 'True'
        g['temperatures_k'].append(round(float(r['temperature_k']), 3))
        rate = float(r['relative_immigration_yr'])
        if rate > 0:
            g['min_relative_immigration_yr'] = min(rate, g['min_relative_immigration_yr'] or rate)
    for g in groups.values():
        g['temperature_range_k'] = [min(g['temperatures_k']), max(g['temperatures_k'])]
        del g['temperatures_k']
    out = dict(source=str(SOURCE.relative_to(ROOT)), endpoints=len(rows),
               settling=sorted({r['settling_status'] for r in rows}), groups=groups)
    OUT.write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
