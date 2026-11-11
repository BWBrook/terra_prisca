"""Export a compact, checksum-pinned C07 census trajectory without interpolation."""
import csv
import gzip
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from . import methane_budget as climate

ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT/'models/haze_world/figures/finite_populations'
SOURCE = ROOT/'local/haze/finite_populations/final_raw/main_0024_t100000-ce9c0899cdf042d0.json.gz'
TABLE = OUTPUT/'attained_endpoints.csv'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def main():
    with TABLE.open() as f:
        matches=[r for r in csv.DictReader(f) if r['base_case_id']=='main_0024_t100000']
    if len(matches)!=1 or digest(SOURCE)!=matches[0]['selected_raw_sha256']:
        raise ValueError('C07 source identity does not match the selected endpoint')
    record=json.loads(gzip.decompress(SOURCE.read_bytes()))
    used_sources={}
    for name in ('src/terra_prisca/haze_world/methane_budget.py',
                 'src/terra_prisca/haze_response/arney2016.py',
                 'models/haze_response/arney2016/figure4.csv',
                 'models/haze_response/arney2016/cases.csv'):
        actual=digest(ROOT/name)
        if actual!=record['protocol']['source_sha256'][name]:
            raise ValueError('Changed climate source: '+name)
        used_sources[name]=actual
    case=record['protocol']['case']
    assert case['fraction']==.5 and case['direction']=='A_into_M'
    assert case['relative_immigration_yr']==0. and case['minimum_cells']==1. and case['census_yr']==10.
    result=record['result'];time=np.asarray(result['t']);state=np.asarray(result['y'])
    assert state.shape==(5,len(time)) and time[0]==0. and time[-1]==100000.
    selected=(time<=200)|((time>200)&(time<=5000)&(time%100==0))|((time>5000)&(time<=20000)&(time%250==0))|((time>20000)&(time%1000==0))
    events=result['extinction_events']
    for event in events:
        selected|=abs(time-event['time_yr'])<=case['census_yr']
    indices=np.flatnonzero(selected)
    p=climate.Params(**record['protocol']['parameters']['climate'])
    temperatures=np.asarray(climate.temperature_k(state[-1,indices],p))
    conversion=result['metadata']['total_habitat_l']/result['metadata']['cell_mass_gdw']
    removed={(event['time_yr'],event['guild']):event['removed_cells'] for event in events}
    target=OUTPUT/'c07_transient.csv'
    with target.open('w',newline='') as f:
        writer=csv.writer(f,lineterminator='\n')
        writer.writerow(['time_yr','hydrogen_pa','acetogens_gdw_l','methanogens_gdw_l',
            'acetate_mol_l','methane_ratio','global_temperature_k','global_acetogen_cells',
            'global_methanogen_cells','acetogen_cells_removed_at_census','methanogen_cells_removed_at_census'])
        for k,temp in zip(indices,temperatures):
            writer.writerow([float(time[k]),*state[:,k].tolist(),float(temp),
                float(conversion*state[1,k]),float(conversion*state[2,k]),
                removed.get((time[k],'acetogen'),0.),removed.get((time[k],'methanogen'),0.)])
    position=int(np.flatnonzero(time[indices]==20.)[0])
    assert state[2,indices[position]]==0. and removed[(20.,'methanogen')]>0
    assert abs(temperatures[0]-273.516744039)<1e-8
    assert abs(temperatures[position]-273.525251377)<1e-8
    manifest=dict(case=case,source_raw_file=str(SOURCE.relative_to(ROOT)),source_raw_sha256=digest(SOURCE),
        selected_table_sha256=digest(TABLE),climate_sources_sha256=used_sources,
        exporter_sha256=digest(Path(__file__)),output_file=str(target.relative_to(ROOT)),output_sha256=digest(target),
        rows=len(indices),source_rows=len(time),actual_horizon_yr=float(time[-1]),
        sampling='All censuses through200yr; every100yr through5000; every250yr through20000; every1000yr thereafter; preserve events and adjacent censuses. No interpolation.',
        initial_temperature_k=float(temperatures[0]),temperature_at_first_m_removal_k=float(temperatures[position]),
        first_methanogen_removal_yr=20.,extinction_events=events,
        counts_from='Original source total_habitat_l / cell_mass_gdw metadata',
        scope='Post-census deterministic stocks and separate pre-removal counts; not continuous minima or stochastic survival. Only the temperature evaluation is recomputed, with verified original climate sources. No physical trajectory is rerun.')
    OUTPUT.joinpath('c07_transient_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(rows=len(indices),bytes=target.stat().st_size,output=str(target.relative_to(ROOT)))))


if __name__=='__main__': main()
