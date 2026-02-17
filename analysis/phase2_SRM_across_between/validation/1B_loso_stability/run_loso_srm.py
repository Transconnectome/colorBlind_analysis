#!/usr/bin/env python3
"""
Test 1B: Leave-One-Subject-Out (LOSO) SRM Stability

Purpose: Test if HC-CVD separation is stable when leaving out individual HC subjects.
Each fold: train SRM on 6 HC, project left-out HC + 3 CVD, compute disparities.

Usage:
    python run_loso_srm.py --fold 0 --roi V1
    python run_loso_srm.py --fold 0  # all ROIs

Arguments:
    --fold: HC subject index to leave out (0-6)
    --roi: Single ROI (V1/V2/V3/hV4) or omit for all
"""

import sys
import argparse
import json
import time
import socket
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr, ttest_ind
from scipy.linalg import orthogonal_procrustes

try:
    from brainiak.funcalign.srm import SRM
except ImportError:
    print("ERROR: brainiak not installed. Run: pip install brainiak")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ROIS = ['V1', 'V2', 'V3', 'hV4']
ROI_DIR_MAP = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}
K_VALUES = {'V1': 4, 'V2': 4, 'V3': 3, 'hV4': 4}

# Auto-detect paths
if socket.gethostname().startswith('node'):
    DATA_DIR = Path("/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010")
    OUTPUT_BASE = Path("/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/1B_loso_stability/results")
else:
    DATA_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/full_dataset_C010")
    OUTPUT_BASE = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase2_SRM_across_between/validation/1B_loso_stability/results")


def load_amplitudes(subject, roi):
    """Load Procrustes-aligned amplitudes: (6, 8, n_voxels)"""
    roi_dir = ROI_DIR_MAP.get(roi, roi)
    path = DATA_DIR / subject / roi_dir / "amplitudes_procrustes.npy"
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")
    amp = np.load(path)
    assert amp.shape[0] == 6 and amp.shape[1] == 8, f"Bad shape: {amp.shape}"
    return amp


def project_new_subject(srm_model, new_data):
    """
    Project new subject into SRM shared space.

    Args:
        srm_model: Fitted SRM with .s_ (shared response)
        new_data: (n_voxels, n_timepoints) for new subject

    Returns:
        W_new: (n_voxels, k) transformation matrix
    """
    S = srm_model.s_  # (k, n_timepoints)
    # W_init = X @ S^+ (pseudo-inverse)
    W_init = new_data @ np.linalg.pinv(S)  # (n_voxels, k)
    # Orthogonalize
    U, _, Vt = np.linalg.svd(W_init, full_matrices=False)
    W_new = U @ Vt
    return W_new


def compute_procrustes_disparity(X, Y):
    """Procrustes disparity between two (n_colors, n_features) matrices."""
    X_c = X - X.mean(axis=0)
    Y_c = Y - Y.mean(axis=0)
    X_n = X_c / np.linalg.norm(X_c, 'fro')
    Y_n = Y_c / np.linalg.norm(Y_c, 'fro')
    R, _ = orthogonal_procrustes(X_n, Y_n)
    return float(np.linalg.norm(X_n @ R - Y_n, 'fro'))


def compute_rdm_correlation(patterns_a, patterns_b):
    """Spearman correlation between RDM upper triangles."""
    rdm_a = 1 - np.corrcoef(patterns_a)
    rdm_b = 1 - np.corrcoef(patterns_b)
    mask = np.triu(np.ones_like(rdm_a, dtype=bool), k=1)
    r, p = spearmanr(rdm_a[mask], rdm_b[mask])
    return float(r), float(p)


def run_loso_fold(fold_idx, roi):
    """
    Run single LOSO fold.

    Args:
        fold_idx: Index of HC subject to leave out (0-6)
        roi: ROI name

    Returns:
        results: Dict with fold results
    """
    left_out = HC_SUBJECTS[fold_idx]
    train_hc = [s for i, s in enumerate(HC_SUBJECTS) if i != fold_idx]
    k = K_VALUES[roi]

    print(f"\n--- Fold {fold_idx}: Leave out {left_out}, ROI={roi}, k={k} ---")
    print(f"  Train HC: {train_hc}")

    # 1. Load training HC data
    hc_data_srm = []  # For SRM fitting: (n_voxels, 8)
    hc_data_full = {}  # For disparity: (6, 8, n_voxels)
    for s in train_hc:
        amp = load_amplitudes(s, roi)
        hc_data_full[s] = amp
        beta = amp.mean(axis=0)  # (8, n_voxels)
        hc_data_srm.append(beta.T)  # (n_voxels, 8)

    # 2. Fit SRM on 6 HC
    print(f"  Fitting SRM on {len(train_hc)} HC subjects...")
    srm = SRM(n_iter=10, features=k)
    srm.fit(hc_data_srm)

    # 3. Project training HC subjects
    hc_aligned = {}
    for i, s in enumerate(train_hc):
        W_i = srm.w_[i]
        aligned = hc_data_full[s] @ W_i  # (6, 8, k)
        hc_aligned[s] = aligned.mean(axis=0)  # (8, k)

    # 4. Project left-out HC subject
    left_out_amp = load_amplitudes(left_out, roi)
    left_out_beta = left_out_amp.mean(axis=0).T  # (n_voxels, 8)
    W_left = project_new_subject(srm, left_out_beta)
    left_out_aligned = (left_out_amp @ W_left).mean(axis=0)  # (8, k)

    # 5. Project CVD subjects
    cvd_aligned = {}
    for s in CVD_SUBJECTS:
        cvd_amp = load_amplitudes(s, roi)
        cvd_beta = cvd_amp.mean(axis=0).T  # (n_voxels, 8)
        W_cvd = project_new_subject(srm, cvd_beta)
        cvd_aligned[s] = (cvd_amp @ W_cvd).mean(axis=0)  # (8, k)

    # 6. Compute HC reference (from training HC only)
    hc_reference = np.mean(list(hc_aligned.values()), axis=0)  # (8, k)

    # 7. Disparities
    hc_hc_disp = [compute_procrustes_disparity(hc_aligned[s], hc_reference) for s in train_hc]
    left_out_disp = compute_procrustes_disparity(left_out_aligned, hc_reference)
    cvd_hc_disp = [compute_procrustes_disparity(cvd_aligned[s], hc_reference) for s in CVD_SUBJECTS]

    hc_mean = np.mean(hc_hc_disp)
    cvd_mean = np.mean(cvd_hc_disp)

    # 8. t-test
    t_stat, p_value = ttest_ind(cvd_hc_disp, hc_hc_disp)

    # 9. RDM correlations
    rdm_corrs = {}
    for s in train_hc:
        for s2 in CVD_SUBJECTS:
            r, _ = compute_rdm_correlation(hc_aligned[s], cvd_aligned[s2])
            rdm_corrs[f"{s}_vs_{s2}"] = r

    print(f"  HC-HC disp: {hc_mean:.4f} ± {np.std(hc_hc_disp):.4f}")
    print(f"  CVD-HC disp: {cvd_mean:.4f} ± {np.std(cvd_hc_disp):.4f}")
    print(f"  Left-out ({left_out}) disp: {left_out_disp:.4f}")
    print(f"  t-test: t={t_stat:.3f}, p={p_value:.4f}")

    return {
        'fold_idx': fold_idx,
        'left_out': left_out,
        'roi': roi,
        'k': k,
        'n_train_hc': len(train_hc),
        'hc_hc_disparities': hc_hc_disp,
        'hc_hc_mean': float(hc_mean),
        'hc_hc_std': float(np.std(hc_hc_disp)),
        'cvd_hc_disparities': cvd_hc_disp,
        'cvd_hc_mean': float(cvd_mean),
        'cvd_hc_std': float(np.std(cvd_hc_disp)),
        'left_out_disparity': float(left_out_disp),
        'separation': float(cvd_mean - hc_mean),
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'significant': bool(p_value < 0.05),
        'rdm_correlations': rdm_corrs
    }


def main():
    parser = argparse.ArgumentParser(description='Test 1B: LOSO SRM Stability')
    parser.add_argument('--fold', type=int, required=True, help='Fold index (0-6)')
    parser.add_argument('--roi', type=str, default=None, help='ROI (V1/V2/V3/hV4). Omit for all.')
    args = parser.parse_args()

    assert 0 <= args.fold <= 6, f"Fold must be 0-6, got {args.fold}"

    rois = [args.roi] if args.roi else ROIS
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

    print(f"{'='*80}")
    print(f"Test 1B: LOSO SRM Stability — Fold {args.fold}")
    print(f"Left out: {HC_SUBJECTS[args.fold]}")
    print(f"ROIs: {rois}")
    print(f"Data: {DATA_DIR}")
    print(f"Output: {output_dir}")
    print(f"{'='*80}")

    start = time.time()
    all_results = {}

    for roi in rois:
        try:
            result = run_loso_fold(args.fold, roi)
            all_results[roi] = result
        except Exception as e:
            print(f"  ERROR in {roi}: {e}")
            import traceback
            traceback.print_exc()

    # Save
    config = {
        'test': '1B_loso_stability',
        'data_dir': str(DATA_DIR),
        'dataset': 'full_dataset_C010',
        'input_file': 'amplitudes_procrustes.npy',
        'hc_subjects': HC_SUBJECTS,
        'cvd_subjects': CVD_SUBJECTS,
        'k_values': K_VALUES,
        'srm_n_iter': 10,
        'training': 'HC-only LOSO (6 HC train, 1 HC left out, 3 CVD projected)',
    }
    settings = {
        'fold_idx': args.fold,
        'left_out': HC_SUBJECTS[args.fold],
        'rois': rois,
        'timestamp': timestamp,
        'elapsed_seconds': time.time() - start
    }

    out_file = OUTPUT_BASE / f"loso_fold{args.fold}_results.json"
    with open(out_file, 'w') as f:
        json.dump({'config': config, 'settings': settings, 'results': all_results}, f, indent=2)

    print(f"\nResults saved: {out_file}")
    print(f"Elapsed: {time.time() - start:.1f}s")

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    for roi, r in all_results.items():
        sig = "SIG" if r['significant'] else "n.s."
        print(f"  {roi}: CVD-HC={r['cvd_hc_mean']:.4f}, HC-HC={r['hc_hc_mean']:.4f}, "
              f"sep={r['separation']:.4f}, p={r['p_value']:.4f} ({sig})")


if __name__ == '__main__':
    main()
