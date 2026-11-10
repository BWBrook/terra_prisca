"""Recover the small E3 environment from its checksummed uncensored record."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.special import logsumexp

from terra_prisca.haze_world import branching as b
from terra_prisca.haze_world import buffered_experiments as e
from terra_prisca.haze_world import bottleneck_runs as runs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--output", type=Path, default=runs.OUTPUT/"main_0010_environment.npz")
    args = parser.parse_args()
    if args.receipt is None:
        candidates = list(runs.RAW.glob("main_0010*t3000-*.receipt.json"))
        if len(candidates) != 1:
            raise RuntimeError("Select the archived E3 pilot receipt explicitly")
        args.receipt = candidates[0]
    record = json.loads(args.receipt.read_text())
    path = args.receipt.parent/record["raw_file"]
    if sha256(path.read_bytes()).hexdigest() != record["raw_sha256"]:
        raise RuntimeError("Changed E3 pilot payload")
    p = e.parameters(e.Case(**record["protocol"]["case"]))
    with np.load(path, allow_pickle=False) as z:
        metadata = json.loads(str(z["metadata"]))
        t, y, biomass = z["t"], z["y"], z["log_biomass"]
    active = np.flatnonzero(p.weights)
    log_counts = biomass[active, 0, :].T+np.log(p.weights[active])+metadata["global_log_cell_conversion"]
    total = logsumexp(log_counts, axis=1); k = int(np.argmin(total))
    threshold = min(np.log(1e16), total[k]+np.log(1e8)); lo = hi = k
    while lo > 0 and total[lo] < threshold: lo -= 1
    while hi < len(t)-1 and total[hi] < threshold: hi += 1
    rates = [b.per_cell_rates(y[:, j], p, 0) for j in range(lo, hi+1)]
    birth, death = np.array([s[1] for s in rates]), np.array([s[2] for s in rates])
    times, migration = t[lo:hi+1], b.migration_matrix(p)
    lu = b.backward_survival(times, birth, death, migration, max_step=1.)
    ll = float(logsumexp(log_counts[lo]+lu))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.output, times=times, birth=birth, death=death, migration=migration,
        log_counts=log_counts[lo:hi+1], reference_log_lambda=ll, source_raw_sha256=record["raw_sha256"])
    print(sha256(args.output.read_bytes()).hexdigest())


if __name__ == "__main__": main()
