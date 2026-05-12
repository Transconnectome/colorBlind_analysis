"""phase3_cache_vulnsim_old.py — cache vuln_sim per cell under OLD formula.

Saves vuln_sim (8-vector) for every (β_s, β_c) grid cell so loss-variant
sub-agents can compute alternative loss functions analytically without
re-running the heavy LOCO simulation.

Output: results/old_formula/sub-XX_V4_vulnsim_cache.json
         containing list of {'bs', 'bc', 'vuln_sim': [..]} entries.
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

import numpy as np

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / 'forward_models'))

from old_formula_refit import (
    HC_SUBJECTS, load_amplitudes, create_basis_full, N_CHANNELS, HUE_ANGLES,
    simulate_mean_hc_loco_legacy, get_shifted_design_old,
    load_cvd_loco_target, LOCAL_DATA, SERVER_DATA,
)

OUTDIR = _THIS_DIR.parent / 'results' / 'old_formula'
OUTDIR.mkdir(parents=True, exist_ok=True)


def cache_subject(subj_id: str, roi: str = 'V4'):
    data_dir = SERVER_DATA if SERVER_DATA.exists() else LOCAL_DATA
    hc_amps = {s: load_amplitudes(data_dir, s, roi) for s in HC_SUBJECTS}
    vuln_cvd = load_cvd_loco_target(subj_id, roi)

    bs_range = np.arange(0, 51, 2, dtype=float)
    bc_range = np.arange(-50, 51, 2, dtype=float)
    cache = []
    t0 = time.time()
    for i, bs in enumerate(bs_range):
        for bc in bc_range:
            C_shifted, dt = get_shifted_design_old(bs, bc)
            vuln_sim, _ = simulate_mean_hc_loco_legacy(hc_amps, C_shifted)
            cache.append({
                'bs': float(bs), 'bc': float(bc),
                'vuln_sim': vuln_sim.tolist(),
                'delta_theta': dt.tolist(),
            })
        if (i + 1) % max(1, len(bs_range) // 5) == 0:
            print(f'  [{i+1}/{len(bs_range)} β_s] elapsed={time.time()-t0:.0f}s')
    elapsed = time.time() - t0
    print(f'Done in {elapsed:.0f}s')

    out = {
        'subject': subj_id, 'roi': roi,
        'formula': 'OLD CIELab-direct',
        'grid_bounds': {'bs': [0, 50, 2], 'bc': [-50, 50, 2]},
        'vuln_cvd': vuln_cvd.tolist(),
        'cells': cache,
    }
    fn = OUTDIR / f'sub-{subj_id}_{roi}_vulnsim_cache.json'
    with open(fn, 'w') as f:
        json.dump(out, f)
    print(f'Wrote {fn} ({fn.stat().st_size / 1024:.0f} KB)')


def main():
    for sid in ['08', '09']:
        print(f'\n=== Caching sub-{sid} V4 ===')
        cache_subject(sid, 'V4')


if __name__ == '__main__':
    main()
