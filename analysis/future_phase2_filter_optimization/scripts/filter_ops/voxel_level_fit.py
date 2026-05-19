"""voxel_level_fit.py — Voxel-level direct fit (Phase 4 preview).

Per user request 2026-05-18: instead of aggregating voxel prediction to per-color
voxel_corr (current LOCO loss), compute voxel-level MSE directly between
HC-pool-encoder-predicted Y and CVD-observed Y at shifted stimulus angles.

Pre-committed criteria (BEFORE running):
  (1) argmin interior (|β_s|<48, |β_c|<48)
  (2) landscape ratio > 0.30 BOTH subjects
  (3) L@id ordering CVD > HC mean
  (4) β_c sign consistent with LOCO-canonical (both negative)
  (5) P2a >= LOCO-canonical (sub-08 ≥ 0.750, sub-09 ≥ 0.975)

PASS all 5 → Phase 4 candidate worth full investigation
FAIL any → log result, confirm 2-comp standalone LOCO-canonical

Loss form: L_vox = mean over (color, voxel) of (R_cvd_obs - R_hc_pred)^2
  R_hc_pred = mean_HC[C_shifted @ W_HC]  — voxel-level prediction at shifted angles
  R_cvd_obs = CVD observed amplitude (mean over runs)
"""
from __future__ import annotations
import argparse
import json
import time
import sys
from pathlib import Path
import numpy as np

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE / 'forward_models'))
for _base in [_HERE.parent.parent, _HERE.parent.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from utils_forward_model import (
    create_basis_full, N_CHANNELS, HUE_ANGLES, gcv_select_alpha, fit_W_ridge,
)
from forward_models.two_component import dt_2comp_8colors

C010_LOCAL = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/'
                  'colorBlind_analysis/analysis/phase1_procrustes_decoding/results/'
                  'visualization/full_dataset_C010_with_residuals')
C010_SERVER = Path('/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')

HC_SUBJ = ['01', '02', '03', '04', '05', '06', '07']
HUE_ANGLES_FLOAT = np.array(HUE_ANGLES, dtype=float)
N_RUNS_DEFAULT = 6
N_COLORS = 8


def get_c010_root():
    if C010_LOCAL.exists():
        return C010_LOCAL
    return C010_SERVER


def load_amps(sid, roi='V4'):
    root = get_c010_root()
    p = root / f'sub-{sid}' / roi / 'amplitudes_procrustes.npy'
    return np.load(p) if p.exists() else None


def precompute_hc_W_pool(hc_amps_dict, C_original, n_vox):
    """Precompute W_HC per subject, restricted to common n_vox."""
    W_dict = {}
    C_pooled = np.tile(C_original, (N_RUNS_DEFAULT, 1))
    for sid, amp in hc_amps_dict.items():
        if amp is None: continue
        V_s = amp.shape[2]
        v_use = min(n_vox, V_s)
        X_all = amp[:, :, :v_use].reshape(-1, v_use)
        alpha, _ = gcv_select_alpha(C_pooled, X_all)
        W = fit_W_ridge(C_pooled, X_all, alpha)
        W_dict[sid] = W
    return W_dict


def compute_voxel_loss(beta_s, beta_c, cvd_type, axis, basis_full,
                        hc_W_dict, cvd_Y_obs, n_vox):
    """Voxel-level MSE loss at one (β_s, β_c) cell."""
    dt = dt_2comp_8colors(cvd_type, float(beta_s), float(beta_c))
    hue_shifted = (HUE_ANGLES_FLOAT + dt) % 360
    idx = np.round(hue_shifted).astype(int) % 360
    C_shifted = basis_full[idx]
    Y_pred_per_hc = []
    for W in hc_W_dict.values():
        Y_pred = C_shifted @ W[:, :n_vox]
        Y_pred_per_hc.append(Y_pred)
    Y_pred_mean = np.mean(Y_pred_per_hc, axis=0)
    diff = Y_pred_mean - cvd_Y_obs
    mse = float(np.mean(diff ** 2))
    return mse, Y_pred_mean


def grid_search_voxel(sid, axis, cvd_type, bs_grid, bc_grid, verbose=True):
    """Voxel-level loss landscape on (β_s, β_c) grid."""
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')

    hc_amps = {h: load_amps(h, 'V4') for h in HC_SUBJ}
    hc_amps = {k: v for k, v in hc_amps.items() if v is not None}
    cvd_amp = load_amps(sid, 'V4')

    # Common n_vox
    all_amps = list(hc_amps.values()) + [cvd_amp]
    n_vox = min(a.shape[2] for a in all_amps)
    if verbose:
        print(f'[sub-{sid}] n_vox = {n_vox} (limited by smallest subject)')

    # Original design matrix for W training
    C_original = basis_full[HUE_ANGLES]
    hc_W_dict = precompute_hc_W_pool(hc_amps, C_original, n_vox)
    cvd_Y_obs = cvd_amp[:, :, :n_vox].mean(axis=0)  # (8, n_vox)

    L_arr = np.full((len(bs_grid), len(bc_grid)), np.nan)
    L_id = None
    total = len(bs_grid) * len(bc_grid)
    t0 = time.time()
    for i, bs in enumerate(bs_grid):
        for j, bc in enumerate(bc_grid):
            mse, _ = compute_voxel_loss(bs, bc, cvd_type, axis, basis_full,
                                         hc_W_dict, cvd_Y_obs, n_vox)
            L_arr[i, j] = mse
            if bs == 0 and bc == 0:
                L_id = mse
        if verbose and (i + 1) % max(1, len(bs_grid) // 5) == 0:
            rate = (i + 1) * len(bc_grid) / (time.time() - t0)
            print(f'  [{(i+1)*len(bc_grid)}/{total}] {rate:.1f} cells/s')
    elapsed = time.time() - t0
    if verbose:
        print(f'  Done in {elapsed:.1f}s ({total/elapsed:.1f} cells/s)')

    return L_arr, L_id, elapsed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--subject', required=True, choices=['08', '09'])
    ap.add_argument('--bs_range', nargs=3, type=float, default=[0, 50, 2],
                    help='start stop step (default 0 50 2)')
    ap.add_argument('--bc_range', nargs=3, type=float, default=[-50, 50, 2],
                    help='start stop step (default -50 50 2)')
    ap.add_argument('--output_dir', default='results/voxel_level_fit')
    ap.add_argument('--timing_only', action='store_true',
                    help='Run small 5x5 grid for ETA estimation only')
    args = ap.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cvd_type = 'deutan' if args.subject == '08' else 'protan'
    axis = 150.0 if args.subject == '08' else 16.0

    if args.timing_only:
        # Small grid for ETA
        bs_grid = np.array([0, 12, 24, 36, 48])
        bc_grid = np.array([-40, -20, 0, 20, 40])
        print(f'\n=== TIMING TEST: 5×5 = 25 cells for sub-{args.subject} ===')
        L_arr, L_id, elapsed = grid_search_voxel(args.subject, axis, cvd_type,
                                                  bs_grid, bc_grid, verbose=True)
        # Extrapolate to full grid
        full_bs = np.arange(args.bs_range[0], args.bs_range[1] + 0.1, args.bs_range[2])
        full_bc = np.arange(args.bc_range[0], args.bc_range[1] + 0.1, args.bc_range[2])
        full_total = len(full_bs) * len(full_bc)
        per_cell = elapsed / 25
        full_eta = per_cell * full_total
        print(f'\n=== ETA EXTRAPOLATION ===')
        print(f'  Per-cell time: {per_cell:.3f} s')
        print(f'  Full grid: {len(full_bs)}×{len(full_bc)} = {full_total} cells/subject')
        print(f'  Per-subject ETA: {full_eta:.0f} s = {full_eta/60:.1f} min')
        print(f'  Both subjects ETA: {2*full_eta:.0f} s = {2*full_eta/60:.1f} min')
        # Save timing info
        out_json = out_dir / f'timing_sub-{args.subject}.json'
        json.dump({
            'subject': args.subject,
            'small_grid_size': [len(bs_grid), len(bc_grid)],
            'small_grid_elapsed_s': elapsed,
            'per_cell_s': per_cell,
            'full_grid_size': [len(full_bs), len(full_bc)],
            'full_grid_eta_s_per_subj': full_eta,
            'full_grid_eta_min_per_subj': full_eta / 60,
        }, open(out_json, 'w'), indent=2)
        print(f'  Saved: {out_json}')
        return

    # Full grid
    bs_grid = np.arange(args.bs_range[0], args.bs_range[1] + 0.1, args.bs_range[2])
    bc_grid = np.arange(args.bc_range[0], args.bc_range[1] + 0.1, args.bc_range[2])
    print(f'\n=== FULL GRID: {len(bs_grid)}×{len(bc_grid)} for sub-{args.subject} ===')
    L_arr, L_id, elapsed = grid_search_voxel(args.subject, axis, cvd_type,
                                              bs_grid, bc_grid, verbose=True)

    idx = np.unravel_index(int(np.nanargmin(L_arr)), L_arr.shape)
    argmin = (float(bs_grid[idx[0]]), float(bc_grid[idx[1]]))
    L_min = float(np.nanmin(L_arr))
    L_max = float(np.nanmax(L_arr))
    delta = L_id - L_min if L_id is not None else None
    ratio = delta / (L_max - L_min) if delta is not None and L_max > L_min else None
    print(f'\nargmin = {argmin}')
    print(f'L_min={L_min:.6f}, L_id={L_id:.6f}, ΔL={delta:.6f}, ratio={ratio:.3f}')

    out_json = out_dir / f'voxel_landscape_sub-{args.subject}.json'
    json.dump({
        'subject': args.subject,
        'cvd_type': cvd_type,
        'axis': axis,
        'bs_grid': bs_grid.tolist(),
        'bc_grid': bc_grid.tolist(),
        'landscape': L_arr.tolist(),
        'argmin': argmin,
        'L_min': L_min,
        'L_id': L_id,
        'L_max': L_max,
        'delta': delta,
        'ratio': ratio,
        'elapsed_s': elapsed,
    }, open(out_json, 'w'), indent=2)
    print(f'Saved: {out_json}')


if __name__ == '__main__':
    main()
