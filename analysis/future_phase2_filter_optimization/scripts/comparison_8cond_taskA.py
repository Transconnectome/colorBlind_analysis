"""comparison_8cond_taskA.py — Augment 2-comp wretrained landscapes with vuln_sim.

For each subject (08, 09):
  - Load cached 1326-cell wretrained landscape (4term).
  - For each cell missing 'vuln_sim', recompute via simulate_mean_hc_loco_legacy
    using the same C_shifted / loss formulae. Verifies l_fit matches cache.
  - Saves augmented landscape: sub-{sid}_V4_4term_landscape_with_vuln_sim.json.

Usage:
    python scripts/comparison_8cond_taskA.py 08
    python scripts/comparison_8cond_taskA.py 09
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
_PHASE2 = _THIS_DIR.parent
for _base in [_PHASE2.parent, _PHASE2.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, HUE_ANGLES, create_basis_full, load_amplitudes,
)
from old_formula_refit import LOCAL_DATA, SERVER_DATA, get_shifted_design_old
from step1_fit_loco_v2 import simulate_mean_hc_loco_legacy, precompute_hc_W
from diagnostic_delta_rdm import compute_delta_rdm_obs, compute_delta_rdm_sim
from phase3_wfixed_diagnostic import compute_L_fit_4term

OUTDIR = _PHASE2 / 'results' / 'old_formula'


def main(sid):
    data_dir = SERVER_DATA if SERVER_DATA.exists() else LOCAL_DATA
    print(f'[sub-{sid}] data_dir: {data_dir}')

    hc_amps = {s: load_amplitudes(data_dir, s, 'V4') for s in HC_SUBJECTS}
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_baseline = basis_full[HUE_ANGLES]

    # Load CVD vuln (uses same target as wfixed_summary)
    vc = np.array(
        json.load(open(OUTDIR / f'sub-{sid}_V4_wfixed_summary.json'))['vuln_cvd']
    )

    # Load existing 4term landscape (no vuln_sim)
    src_path = OUTDIR / f'sub-{sid}_V4_4term_landscape.json'
    print(f'[sub-{sid}] loading {src_path.name}')
    landscape = json.load(open(src_path))
    print(f'[sub-{sid}] {len(landscape)} cells, has vuln_sim: {"vuln_sim" in landscape[0]}')

    if 'vuln_sim' in landscape[0]:
        print(f'[sub-{sid}] already has vuln_sim — nothing to do')
        return

    # Precompute single-W for ΔRDM (same as cached) — only used to re-verify l_fit
    print(f'[sub-{sid}] precomputing single-W (for ΔRDM verification)...')
    hc_W_single, _ = precompute_hc_W(hc_amps, C_baseline)
    # Compute ΔRDM_obs (per subject)
    amp_cvd = load_amplitudes(data_dir, sid, 'V4')
    delta_rdm_obs, _, _, _ = compute_delta_rdm_obs(
        amp_cvd, hc_amps, distance='correlation')

    t0 = time.time()
    mismatches = 0
    for i, c in enumerate(landscape):
        C_shifted, dt = get_shifted_design_old(c['bs'], c['bc'])
        vuln_sim, _ = simulate_mean_hc_loco_legacy(hc_amps, C_shifted)
        delta_rdm_sim, _ = compute_delta_rdm_sim(
            hc_W_single, C_shifted, C_baseline, distance='correlation')
        loss = compute_L_fit_4term(vuln_sim, vc, dt, delta_rdm_sim, delta_rdm_obs)

        # Cache vuln_sim and verify
        c['vuln_sim'] = vuln_sim.tolist()
        if abs(loss['l_fit'] - c['l_fit']) > 1e-5:
            mismatches += 1
            if mismatches < 5:
                print(f'  mismatch at ({c["bs"]:.0f},{c["bc"]:+.0f}): '
                      f'recomputed l_fit={loss["l_fit"]:.6f}, cached={c["l_fit"]:.6f}')

        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (len(landscape) - i - 1) / rate
            print(f'[sub-{sid}] {i+1}/{len(landscape)} cells '
                  f'({elapsed:.0f}s elapsed, ETA {eta:.0f}s)')

    elapsed = time.time() - t0
    print(f'[sub-{sid}] done in {elapsed:.0f}s, mismatches={mismatches}/{len(landscape)}')

    # Save augmented file (distinct name to preserve original)
    out_path = OUTDIR / f'sub-{sid}_V4_4term_landscape_with_vuln_sim.json'
    with open(out_path, 'w') as f:
        json.dump(landscape, f)
    print(f'[sub-{sid}] wrote {out_path}')


if __name__ == '__main__':
    sid = sys.argv[1] if len(sys.argv) > 1 else '08'
    main(sid)
