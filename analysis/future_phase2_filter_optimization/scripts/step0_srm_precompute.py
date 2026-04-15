#!/usr/bin/env python3
"""
step0_srm_precompute.py — Train HC-only SRM for V1/V2, compute W_combined and
SRM-space ΔRDM_obs for use in srm_integrated_loco.py.

Architecture:
  For each ROI in {V1, V2}:
    1. Load HC amplitudes (6 runs x 8 colors x V_s voxels)
    2. Train HC-only SRM (K=4 for V1/V2)
    3. Compute W_ridge for each HC (pooled 48 samples, ridge_gcv)
    4. W_combined = W_ridge @ W_srm  →  (K_basis, K_srm) per HC
    5. Project CVD into SRM space via SVD
    6. Compute SRM-space ΔRDM_obs = RDM(CVD_aligned) - RDM(mean HC_aligned)

Output: results/srm_precompute/
  - srm_{roi}.npz: W_combined per HC, shared_space (s_), CVD aligned patterns
  - delta_rdm_obs_srm_{roi}.npz: per-CVD ΔRDM_obs in SRM space
  - manifest.json: config, K values, alpha values

Usage (requires mpirun for BrainIAK):
    mpirun -np 1 python scripts/step0_srm_precompute.py \
        --output_dir results/srm_precompute
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr

# ── Path resolution (fallback: tries analysis/ then parent of analysis/) ──
_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _SCRIPT_DIR.parent
sys.path.insert(0, str(_SCRIPT_DIR))

for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from utils_forward_model import (  # noqa: E402
    HC_SUBJECTS, CVD_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS,
    HUE_ANGLES, load_amplitudes, create_basis_full,
    gcv_select_alpha, fit_W_ridge,
)

# SRM + rerun_loo_consistent imports: only needed when running as main script.
# Deferred to avoid BrainIAK MPI hang when importing just compute_delta_rdm_sim_srm.
SRM = None
project_new_subject = None

def _lazy_import_srm():
    global SRM, project_new_subject
    if SRM is not None:
        return
    try:
        from brainiak.funcalign.srm import SRM as _SRM
        SRM = _SRM
    except ImportError:
        print("ERROR: brainiak not available. Run with: mpirun -np 1 python ...")
        sys.exit(1)
    for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
        _srm = _base / 'phase2_SRM_across_between'
        if _srm.exists() and str(_srm) not in sys.path:
            sys.path.insert(0, str(_srm))
            break
    from rerun_loo_consistent import project_new_subject as _pns  # noqa: E402
    project_new_subject = _pns

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
K_SRM = {'V1': 4, 'V2': 4}
ROIS = ['V1', 'V2']

LOCAL_DATA = (Path(__file__).resolve().parent.parent.parent.parent
              / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')
SERVER_DATA = Path(
    '/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010')


def auto_detect_data_dir(override=None):
    if override:
        return Path(override)
    if SERVER_DATA.exists():
        return SERVER_DATA
    if LOCAL_DATA.exists():
        return LOCAL_DATA
    raise FileNotFoundError('No data dir found')


def precompute_hc_W_ridge(hc_amps_dict, C_original):
    """Precompute ridge encoding weights (K_basis, V_s) for each HC.

    Same as step1_fit_loco_v2.precompute_hc_W but kept local to avoid
    circular import issues with step1's other imports.
    """
    hc_W_dict = {}
    hc_alpha_dict = {}
    C_pooled = np.tile(C_original, (N_RUNS, 1))  # (48, K_basis)

    for subj, amp in hc_amps_dict.items():
        V_s = amp.shape[2]
        X_all = amp.reshape(-1, V_s)  # (48, V_s)
        alpha, _ = gcv_select_alpha(C_pooled, X_all)
        W = fit_W_ridge(C_pooled, X_all, alpha)  # (K_basis, V_s)
        hc_W_dict[subj] = W
        hc_alpha_dict[subj] = float(alpha)

    return hc_W_dict, hc_alpha_dict


def compute_delta_rdm_sim_srm(W_combined_dict, C_shifted, C_baseline):
    """Compute ΔRDM in SRM space: RDM(C_shifted @ W_combined) - RDM(C_baseline @ W_combined).

    Averaged over HC subjects.

    Args:
        W_combined_dict: {subj: (K_basis, K_srm)} combined weight matrices
        C_shifted: (8, K_basis) shifted design matrix
        C_baseline: (8, K_basis) original design matrix

    Returns:
        delta_rdm_mean: (28,) mean ΔRDM across HCs
        delta_rdm_per_hc: {subj: (28,)}
    """
    delta_rdm_per_hc = {}
    for subj, W_comb in W_combined_dict.items():
        Y_shifted = C_shifted @ W_comb     # (8, K_srm)
        Y_baseline = C_baseline @ W_comb   # (8, K_srm)
        rdm_shifted = pdist(Y_shifted, metric='correlation')   # (28,)
        rdm_baseline = pdist(Y_baseline, metric='correlation')  # (28,)
        delta_rdm_per_hc[subj] = rdm_shifted - rdm_baseline

    delta_rdm_mean = np.mean(list(delta_rdm_per_hc.values()), axis=0)
    return delta_rdm_mean, delta_rdm_per_hc


def train_srm_for_roi(roi, k, hc_amps_dict, cvd_amps_dict, C_original,
                       verbose=True):
    """Train HC-only SRM, compute W_combined, project CVD, compute ΔRDM_obs.

    Returns:
        artifacts: dict with all precomputed data for this ROI
    """
    _lazy_import_srm()
    if verbose:
        print(f'\n=== Training SRM for {roi} (K={k}) ===')

    # --- HC betas: mean across runs → (8, V_s) per subject ---
    hc_betas = {}
    for subj, amp in hc_amps_dict.items():
        hc_betas[subj] = amp.mean(axis=0)  # (8, V_s)

    # --- Train HC-only SRM ---
    hc_list = sorted(hc_amps_dict.keys())
    # SRM expects list of (V_s, T) arrays where T=8 (conditions as time)
    srm_input = [hc_betas[s].T for s in hc_list]  # list of (V_s, 8)

    t0 = time.time()
    srm = SRM(n_iter=10, features=k)
    srm.fit(srm_input)
    if verbose:
        print(f'  SRM trained in {time.time() - t0:.1f}s')

    # srm.w_[i]: (V_s_i, K_srm) for each HC
    # srm.s_: (K_srm, 8) shared space

    # --- HC aligned patterns ---
    hc_aligned = {}
    for i, subj in enumerate(hc_list):
        # W_srm[i].T @ beta.T → (K_srm, 8) → transpose → (8, K_srm)
        hc_aligned[subj] = (srm.w_[i].T @ srm_input[i]).T  # (8, K_srm)

    if verbose:
        print(f'  HC aligned: {len(hc_aligned)} subjects, '
              f'shape={(8, k)}')

    # --- W_ridge for each HC ---
    hc_W_ridge, hc_alphas = precompute_hc_W_ridge(hc_amps_dict, C_original)
    if verbose:
        for subj, alpha in hc_alphas.items():
            print(f'  sub-{subj}: W_ridge shape={hc_W_ridge[subj].shape}, '
                  f'alpha={alpha:.1f}')

    # --- W_combined = W_ridge @ W_srm → (K_basis, K_srm) per HC ---
    W_combined = {}
    for i, subj in enumerate(hc_list):
        # W_ridge: (K_basis, V_s), W_srm: (V_s, K_srm)
        W_combined[subj] = hc_W_ridge[subj] @ srm.w_[i]  # (K_basis, K_srm)

    if verbose:
        subj0 = hc_list[0]
        print(f'  W_combined: {len(W_combined)} HCs, '
              f'shape={W_combined[subj0].shape}')

    # --- CVD SRM projection via SVD ---
    cvd_aligned = {}
    for cvd_s, amp in cvd_amps_dict.items():
        cvd_beta = amp.mean(axis=0)  # (8, V_s)
        # project_new_subject expects (V_s, 8), returns (V_s, K_srm)
        W_cvd_srm = project_new_subject(srm, cvd_beta.T)
        cvd_aligned[cvd_s] = cvd_beta @ W_cvd_srm  # (8, K_srm)

    if verbose:
        for cvd_s in cvd_aligned:
            print(f'  CVD sub-{cvd_s}: aligned shape='
                  f'{cvd_aligned[cvd_s].shape}')

    # --- SRM-space ΔRDM_obs = RDM(CVD_aligned) - RDM(mean HC_aligned) ---
    hc_rdms = {}
    for subj, pattern in hc_aligned.items():
        hc_rdms[subj] = pdist(pattern, metric='correlation')  # (28,)
    rdm_hc_mean = np.mean(list(hc_rdms.values()), axis=0)  # (28,)

    delta_rdm_obs = {}
    for cvd_s, pattern in cvd_aligned.items():
        rdm_cvd = pdist(pattern, metric='correlation')  # (28,)
        delta_rdm_obs[cvd_s] = rdm_cvd - rdm_hc_mean

    if verbose:
        for cvd_s, drdm in delta_rdm_obs.items():
            print(f'  ΔRDM_obs sub-{cvd_s}: norm={np.linalg.norm(drdm):.4f}')

    # --- Sanity check: cross-validate with HC LOO ---
    hc_loo_rdm_corr = {}
    for i, subj in enumerate(hc_list):
        others = [hc_rdms[s] for s in hc_list if s != subj]
        rdm_others_mean = np.mean(others, axis=0)
        rho, _ = spearmanr(hc_rdms[subj], rdm_others_mean)
        hc_loo_rdm_corr[subj] = float(rho) if np.isfinite(rho) else 0.0

    if verbose:
        print(f'  HC LOO RDM correlation: '
              f'mean={np.mean(list(hc_loo_rdm_corr.values())):.3f}')

    return {
        'roi': roi,
        'k': k,
        'hc_list': hc_list,
        'W_combined': W_combined,
        'hc_aligned': hc_aligned,
        'cvd_aligned': cvd_aligned,
        'delta_rdm_obs': delta_rdm_obs,
        'rdm_hc_mean': rdm_hc_mean,
        'hc_rdms': hc_rdms,
        'hc_alphas': hc_alphas,
        'hc_loo_rdm_corr': hc_loo_rdm_corr,
        'shared_space': srm.s_,
    }


def main():
    parser = argparse.ArgumentParser(
        description='Step 0: SRM precompute for V1/V2 (cross-ROI LOCO pipeline)')
    parser.add_argument('--rois', nargs='+', default=ROIS,
                        help='ROIs to process (default: V1 V2)')
    parser.add_argument('--data_dir', type=str, default=None)
    parser.add_argument('--output_dir', type=str,
                        default='results/srm_precompute')
    args = parser.parse_args()

    data_dir = auto_detect_data_dir(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('STEP 0: SRM Precompute (V1/V2)')
    print('=' * 60)
    print(f'Data:     {data_dir}')
    print(f'ROIs:     {args.rois}')
    print(f'K values: {K_SRM}')
    print(f'Output:   {output_dir}')

    # Build basis
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_original = basis_full[HUE_ANGLES]  # (8, K_basis)

    manifest = {
        'date': datetime.now().isoformat(),
        'rois': args.rois,
        'k_values': K_SRM,
        'hc_subjects': HC_SUBJECTS,
        'cvd_subjects': CVD_SUBJECTS,
        'data_dir': str(data_dir),
        'C_original_shape': list(C_original.shape),
        'roi_details': {},
    }

    t_total = time.time()

    for roi in args.rois:
        k = K_SRM.get(roi)
        if k is None:
            print(f'\nWARNING: No K defined for {roi}, skipping')
            continue

        # Load amplitudes
        print(f'\n--- Loading {roi} amplitudes ---')
        hc_amps = {}
        for subj in HC_SUBJECTS:
            hc_amps[subj] = load_amplitudes(data_dir, subj, roi)
        cvd_amps = {}
        for subj in CVD_SUBJECTS:
            cvd_amps[subj] = load_amplitudes(data_dir, subj, roi)
        print(f'  HC: {len(hc_amps)} subjects, '
              f'V_s={hc_amps[HC_SUBJECTS[0]].shape[2]}')
        print(f'  CVD: {len(cvd_amps)} subjects')

        # Train and precompute
        artifacts = train_srm_for_roi(roi, k, hc_amps, cvd_amps, C_original)

        # Save SRM artifacts
        srm_path = output_dir / f'srm_{roi}.npz'
        save_dict = {
            'shared_space': artifacts['shared_space'],
            'rdm_hc_mean': artifacts['rdm_hc_mean'],
        }
        # Save W_combined per HC
        for subj, W_comb in artifacts['W_combined'].items():
            save_dict[f'W_combined_{subj}'] = W_comb
        # Save HC aligned patterns
        for subj, pattern in artifacts['hc_aligned'].items():
            save_dict[f'hc_aligned_{subj}'] = pattern
        # Save CVD aligned patterns
        for subj, pattern in artifacts['cvd_aligned'].items():
            save_dict[f'cvd_aligned_{subj}'] = pattern
        # Save HC RDMs
        for subj, rdm in artifacts['hc_rdms'].items():
            save_dict[f'hc_rdm_{subj}'] = rdm

        np.savez_compressed(srm_path, **save_dict)
        print(f'\n  Saved: {srm_path}')

        # Save ΔRDM_obs per CVD
        drdm_path = output_dir / f'delta_rdm_obs_srm_{roi}.npz'
        drdm_dict = {}
        for cvd_s, drdm in artifacts['delta_rdm_obs'].items():
            drdm_dict[f'sub_{cvd_s}'] = drdm
        np.savez_compressed(drdm_path, **drdm_dict)
        print(f'  Saved: {drdm_path}')

        # Update manifest
        manifest['roi_details'][roi] = {
            'k': k,
            'hc_alphas': artifacts['hc_alphas'],
            'W_combined_shape': list(artifacts['W_combined']
                                     [HC_SUBJECTS[0]].shape),
            'hc_loo_rdm_corr': artifacts['hc_loo_rdm_corr'],
            'delta_rdm_obs_norms': {
                s: float(np.linalg.norm(d))
                for s, d in artifacts['delta_rdm_obs'].items()
            },
        }

    elapsed = time.time() - t_total
    manifest['total_elapsed_s'] = round(elapsed, 1)

    with open(output_dir / 'manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f'\n  Saved: {output_dir}/manifest.json')
    print(f'\nTotal: {elapsed:.1f}s')
    print('Step 0 complete.')


if __name__ == '__main__':
    main()
