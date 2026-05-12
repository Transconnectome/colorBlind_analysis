"""comparison_8cond_taskB.py — Machado 1way wfixed landscape (W trained on UNSHIFTED C).

Same architecture as `phase3_wfixed_diagnostic.fit_wfixed_for_subject`:
  - W_k trained ONCE per (HC, held-out color) on UNSHIFTED C_baseline.
  - Test-time prediction uses C(θ + Machado-shifted-δθ).
Grid: Δλ ∈ [0, 20] step 0.5 nm (41 cells — matches existing wretrained Machado).

Loss family identical to phase_a Machado 1way (4-term L_fit), enabling
like-for-like comparison with `results/fits/phase_a/sub-XX_V4_machado_1way_landscape.json`.

Outputs (results/fits/phase_a/):
    sub-{sid}_V4_machado_1way_wfixed_landscape.json
    sub-{sid}_V4_machado_1way_wfixed_summary.json

Usage:
    python scripts/comparison_8cond_taskB.py 08
    python scripts/comparison_8cond_taskB.py 09
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
from utils_distortion_models import get_design_matrix
from machado_simulator import machado_shifted_hue
from old_formula_refit import LOCAL_DATA, SERVER_DATA
from step1_fit_loco_v2 import precompute_hc_W
from diagnostic_delta_rdm import compute_delta_rdm_obs, compute_delta_rdm_sim
from phase3_wfixed_diagnostic import (
    compute_L_fit_4term,
    precompute_hc_W_loco_unshifted,
    simulate_mean_hc_loco_wfixed,
)

OUTDIR = _PHASE2 / 'results' / 'fits' / 'phase_a'
OUTDIR.mkdir(parents=True, exist_ok=True)

CVD_FAMILY = {'08': 'deutan', '09': 'protan', '10': 'normal'}


def main(sid):
    family = CVD_FAMILY[sid]
    print(f'[sub-{sid}] family={family}, wfixed Machado 1way')

    data_dir = SERVER_DATA if SERVER_DATA.exists() else LOCAL_DATA
    print(f'[sub-{sid}] data_dir: {data_dir}')

    hc_amps = {s: load_amplitudes(data_dir, s, 'V4') for s in HC_SUBJECTS}
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_baseline = basis_full[HUE_ANGLES]

    # CVD target vuln from wfixed summary
    src_summary = (_PHASE2 / 'results' / 'old_formula' /
                   f'sub-{sid}_V4_wfixed_summary.json')
    vuln_cvd = np.array(json.load(open(src_summary))['vuln_cvd'])
    print(f'[sub-{sid}] vuln_cvd: {np.round(vuln_cvd, 3).tolist()}')

    # ΔRDM_obs (per-subject) and single-W for ΔRDM_sim (same as cached pipeline)
    print(f'[sub-{sid}] computing ΔRDM_obs and HC single-W...')
    amp_cvd = load_amplitudes(data_dir, sid, 'V4')
    delta_rdm_obs, _, _, _ = compute_delta_rdm_obs(
        amp_cvd, hc_amps, distance='correlation')
    hc_W_single, _ = precompute_hc_W(hc_amps, C_baseline)

    # LOCO W_k precompute on UNSHIFTED C_baseline (independent of Δλ)
    print(f'[sub-{sid}] precomputing W_k (LOCO, UNSHIFTED C, 7 HC × 8 colors)...')
    t0 = time.time()
    W_loco, alpha_loco = precompute_hc_W_loco_unshifted(hc_amps, C_baseline)
    print(f'[sub-{sid}] W_k precompute done in {time.time()-t0:.1f}s')

    # Δλ grid [0, 20] step 0.5 — matches existing wretrained Machado file
    dlam_grid = np.arange(0.0, 20.0 + 1e-9, 0.5)
    n_cells = len(dlam_grid)
    print(f'[sub-{sid}] Δλ grid: {n_cells} cells [0, 20] step 0.5')

    landscape = []
    t0 = time.time()
    for i, dl in enumerate(dlam_grid):
        # Shifted design via Machado (family-specific direction)
        C_shifted = get_design_matrix('machado_1way', [float(dl)],
                                      cvd_type=family,
                                      n_channels=N_CHANNELS)
        # delta_theta from machado_shifted_hue (already used in phase_a)
        _, _, dt = machado_shifted_hue(float(dl), family)
        dt = np.asarray(dt)

        # wfixed: W_k trained on UNSHIFTED C, predict held-out with C_shifted
        vuln_sim, _ = simulate_mean_hc_loco_wfixed(W_loco, hc_amps, C_shifted)
        delta_rdm_sim, _ = compute_delta_rdm_sim(
            hc_W_single, C_shifted, C_baseline, distance='correlation')

        loss = compute_L_fit_4term(vuln_sim, vuln_cvd, dt,
                                   delta_rdm_sim, delta_rdm_obs)
        entry = {
            'params': [float(dl)],
            'delta_lambda_nm': float(dl),
            'vuln_sim': vuln_sim.tolist(),
            'delta_theta': dt.tolist(),
            **loss,
        }
        landscape.append(entry)
        if (i + 1) % 10 == 0:
            print(f'  [{i+1}/{n_cells}] Δλ={dl:.1f} ρ={loss["spearman_r"]:+.3f} '
                  f'l_fit={loss["l_fit"]:.4f}')
    elapsed = time.time() - t0
    print(f'[sub-{sid}] grid sweep done in {elapsed:.1f}s')

    by_lfit = sorted(landscape, key=lambda r: r['l_fit'])
    by_rho = sorted(landscape, key=lambda r: -r['spearman_r'])
    summary = {
        'subject': sid,
        'roi': 'V4',
        'model': 'machado_1way',
        'cvd_family': family,
        'simulator': 'wfixed_loco_unshifted',
        'description': ('Machado 1way wfixed: W_k trained ONCE per (HC, held-out color) '
                        'on UNSHIFTED C_baseline; held-out test uses Machado-shifted '
                        'design C(θ + δθ(Δλ, family)).'),
        'formula': 'machado_1way + 4-term L_fit (matches phase_a)',
        'grid_bounds': {'delta_lambda_nm': [0.0, 20.0], 'step_nm': 0.5},
        'n_cells': n_cells,
        'elapsed_s': elapsed,
        'vuln_cvd': vuln_cvd.tolist(),
        'delta_rdm_obs': delta_rdm_obs.tolist(),
        'hc_subjects': list(hc_amps.keys()),
        'alpha_loco': {k: list(map(float, v)) for k, v in alpha_loco.items()},
        'best_by_l_fit': by_lfit[0],
        'best_by_rho': by_rho[0],
        'top_10_by_l_fit': by_lfit[:10],
        'top_10_by_rho': by_rho[:10],
    }

    out_summary = OUTDIR / f'sub-{sid}_V4_machado_1way_wfixed_summary.json'
    out_landscape = OUTDIR / f'sub-{sid}_V4_machado_1way_wfixed_landscape.json'
    with open(out_summary, 'w') as f:
        json.dump(summary, f, indent=2)
    with open(out_landscape, 'w') as f:
        json.dump(landscape, f, indent=2)
    print(f'[sub-{sid}] wrote {out_summary.name}')
    print(f'[sub-{sid}] wrote {out_landscape.name}')


if __name__ == '__main__':
    sid = sys.argv[1] if len(sys.argv) > 1 else '08'
    main(sid)
