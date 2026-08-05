#!/usr/bin/env python3
"""
Test 1C: Split-Half SRM Reliability

Purpose: Test if SRM learned from different run subsets produces consistent CVD patterns.
  - Set A: Average runs 1-3 -> train SRM (HC only) -> project CVD -> compute disparities
  - Set B: Average runs 4-6 -> train SRM (HC only) -> project CVD -> compute disparities
  - Spearman correlation between Set A and Set B disparities

Usage:
    python run_split_half_srm.py --roi V1
    python run_split_half_srm.py  # all ROIs
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
    print("ERROR: brainiak not installed")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ROIS = ['V1', 'V2', 'V3', 'hV4']
ROI_DIR_MAP = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}
K_VALUES = {'V1': 4, 'V2': 4, 'V3': 3, 'hV4': 4}

if socket.gethostname().startswith('node'):
    DATA_DIR = Path("/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010")
    OUTPUT_BASE = Path("/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/1C_split_half/results")
else:
    DATA_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/full_dataset_C010")
    OUTPUT_BASE = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase2_SRM_across_between/validation/1C_split_half/results")


def load_amplitudes(subject, roi):
    """Load Procrustes-aligned amplitudes: (6, 8, n_voxels)"""
    roi_dir = ROI_DIR_MAP.get(roi, roi)
    path = DATA_DIR / subject / roi_dir / "amplitudes_procrustes.npy"
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")
    return np.load(path)


def project_new_subject(srm_model, new_data):
    """Project new subject using learned shared response."""
    S = srm_model.s_
    W_init = new_data @ np.linalg.pinv(S)
    U, _, Vt = np.linalg.svd(W_init, full_matrices=False)
    return U @ Vt


def compute_procrustes_disparity(X, Y):
    """Procrustes disparity between (n_colors, k) matrices."""
    X_c = X - X.mean(axis=0)
    Y_c = Y - Y.mean(axis=0)
    X_n = X_c / np.linalg.norm(X_c, 'fro')
    Y_n = Y_c / np.linalg.norm(Y_c, 'fro')
    R, _ = orthogonal_procrustes(X_n, Y_n)
    return float(np.linalg.norm(X_n @ R - Y_n, 'fro'))


def fit_half_and_compute(run_indices, roi, k, label):
    """
    Fit SRM on one run-half and compute disparities.

    Args:
        run_indices: List of run indices (e.g., [0,1,2] for runs 1-3)
        roi: ROI name
        k: Number of SRM features
        label: 'A' or 'B'

    Returns:
        Dict with disparities and aligned patterns
    """
    print(f"\n  [{label}] Runs {[i+1 for i in run_indices]}, k={k}")

    # 1. Load and average selected runs for HC
    hc_data_srm = []
    for s in HC_SUBJECTS:
        amp = load_amplitudes(s, roi)  # (6, 8, n_voxels)
        half_avg = amp[run_indices].mean(axis=0)  # (8, n_voxels)
        hc_data_srm.append(half_avg.T)  # (n_voxels, 8)

    # 2. Fit SRM on HC
    srm = SRM(n_iter=10, features=k)
    srm.fit(hc_data_srm)

    # 3. Project HC into shared space
    hc_aligned = {}
    for i, s in enumerate(HC_SUBJECTS):
        W_i = srm.w_[i]
        amp = load_amplitudes(s, roi)
        half_avg = amp[run_indices].mean(axis=0)  # (8, n_voxels)
        hc_aligned[s] = half_avg @ W_i  # (8, k)

    # 4. Project CVD
    cvd_aligned = {}
    for s in CVD_SUBJECTS:
        amp = load_amplitudes(s, roi)
        half_avg = amp[run_indices].mean(axis=0)  # (8, n_voxels)
        W_cvd = project_new_subject(srm, half_avg.T)  # (n_voxels, k)
        cvd_aligned[s] = half_avg @ W_cvd  # (8, k)

    # 5. Compute HC reference and disparities
    hc_ref = np.mean(list(hc_aligned.values()), axis=0)

    hc_disp = {s: compute_procrustes_disparity(hc_aligned[s], hc_ref) for s in HC_SUBJECTS}
    cvd_disp = {s: compute_procrustes_disparity(cvd_aligned[s], hc_ref) for s in CVD_SUBJECTS}

    hc_vals = list(hc_disp.values())
    cvd_vals = list(cvd_disp.values())
    t_stat, p_value = ttest_ind(cvd_vals, hc_vals)

    # 6. CVD-CVD RDM correlations
    cvd_rdm_corrs = []
    for i, s1 in enumerate(CVD_SUBJECTS):
        for s2 in CVD_SUBJECTS[i+1:]:
            rdm1 = 1 - np.corrcoef(cvd_aligned[s1])
            rdm2 = 1 - np.corrcoef(cvd_aligned[s2])
            mask = np.triu(np.ones_like(rdm1, dtype=bool), k=1)
            r, _ = spearmanr(rdm1[mask], rdm2[mask])
            cvd_rdm_corrs.append(float(r))

    print(f"    HC-HC: {np.mean(hc_vals):.4f}, CVD-HC: {np.mean(cvd_vals):.4f}, "
          f"p={p_value:.4f}, CVD-CVD RDM r={np.mean(cvd_rdm_corrs):.3f}")

    return {
        'hc_disparities': hc_disp,
        'cvd_disparities': cvd_disp,
        'hc_mean': float(np.mean(hc_vals)),
        'cvd_mean': float(np.mean(cvd_vals)),
        'separation': float(np.mean(cvd_vals) - np.mean(hc_vals)),
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'significant': bool(p_value < 0.05),
        'cvd_cvd_rdm_correlation': float(np.mean(cvd_rdm_corrs)),
    }


def run_split_half(roi):
    """Run split-half analysis for one ROI."""
    k = K_VALUES[roi]
    print(f"\n{'='*60}")
    print(f"Split-Half SRM: {roi} (k={k})")
    print(f"{'='*60}")

    # Set A: runs 1-3, Set B: runs 4-6
    result_a = fit_half_and_compute([0, 1, 2], roi, k, 'A (runs 1-3)')
    result_b = fit_half_and_compute([3, 4, 5], roi, k, 'B (runs 4-6)')

    # Cross-half consistency: correlate disparity patterns
    # Per-subject disparities from A vs B
    all_subjects = HC_SUBJECTS + CVD_SUBJECTS
    disp_a = [result_a['hc_disparities'].get(s, result_a['cvd_disparities'].get(s, np.nan)) for s in all_subjects]
    disp_b = [result_b['hc_disparities'].get(s, result_b['cvd_disparities'].get(s, np.nan)) for s in all_subjects]

    valid = [(a, b) for a, b in zip(disp_a, disp_b) if np.isfinite(a) and np.isfinite(b)]
    if len(valid) >= 3:
        va, vb = zip(*valid)
        cross_r, cross_p = spearmanr(va, vb)
    else:
        cross_r, cross_p = np.nan, np.nan

    print(f"\n  Cross-half disparity correlation: r={cross_r:.3f}, p={cross_p:.4f}")
    print(f"  Set A CVD-CVD RDM: {result_a['cvd_cvd_rdm_correlation']:.3f}")
    print(f"  Set B CVD-CVD RDM: {result_b['cvd_cvd_rdm_correlation']:.3f}")

    return {
        'roi': roi,
        'k': k,
        'set_a': result_a,
        'set_b': result_b,
        'cross_half_correlation': float(cross_r) if np.isfinite(cross_r) else None,
        'cross_half_p_value': float(cross_p) if np.isfinite(cross_p) else None,
        'both_significant': result_a['significant'] and result_b['significant'],
        'both_cvd_rdm_above_05': (
            result_a['cvd_cvd_rdm_correlation'] > 0.5 and
            result_b['cvd_cvd_rdm_correlation'] > 0.5
        )
    }


def main():
    parser = argparse.ArgumentParser(description='Test 1C: Split-Half SRM Reliability')
    parser.add_argument('--roi', type=str, default=None, help='ROI (V1/V2/V3/hV4). Omit for all.')
    args = parser.parse_args()

    rois = [args.roi] if args.roi else ROIS
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

    print(f"{'='*80}")
    print(f"Test 1C: Split-Half SRM Reliability")
    print(f"ROIs: {rois}")
    print(f"{'='*80}")

    start = time.time()
    all_results = {}

    for roi in rois:
        try:
            all_results[roi] = run_split_half(roi)
        except Exception as e:
            print(f"ERROR in {roi}: {e}")
            import traceback
            traceback.print_exc()

    roi_tag = args.roi if args.roi else "all"
    out_file = OUTPUT_BASE / f"split_half_{roi_tag}_results.json"
    with open(out_file, 'w') as f:
        json.dump({
            'config': {
                'test': '1C_split_half',
                'data_dir': str(DATA_DIR),
                'dataset': 'full_dataset_C010',
                'input_file': 'amplitudes_procrustes.npy',
                'hc_subjects': HC_SUBJECTS,
                'cvd_subjects': CVD_SUBJECTS,
                'k_values': K_VALUES,
                'srm_n_iter': 10,
                'set_a_runs': [1, 2, 3],
                'set_b_runs': [4, 5, 6],
                'training': 'HC-only (CVD projected via pseudo-inverse)',
            },
            'settings': {'rois': rois, 'timestamp': timestamp, 'elapsed': time.time() - start},
            'results': all_results
        }, f, indent=2)

    print(f"\n{'='*80}")
    print("SUMMARY")
    for roi, r in all_results.items():
        print(f"  {roi}: cross-half r={r['cross_half_correlation']}, "
              f"A sig={r['set_a']['significant']}, B sig={r['set_b']['significant']}, "
              f"A CVD-RDM={r['set_a']['cvd_cvd_rdm_correlation']:.3f}, "
              f"B CVD-RDM={r['set_b']['cvd_cvd_rdm_correlation']:.3f}")
    print(f"Saved: {out_file}")


if __name__ == '__main__':
    main()
