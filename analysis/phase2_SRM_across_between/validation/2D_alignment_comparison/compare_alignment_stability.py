#!/usr/bin/env python3
"""
Test 2D: Alignment Method Comparison (Split-Half Stability)

Purpose: Compare Raw vs Procrustes vs SRM alignment on the same split-half metric.
  - For each method, split runs into halves A (1-3) and B (4-6)
  - Compute per-subject RDM from each half
  - Measure: (1) within-subject RDM correlation across halves
             (2) between-subject RDM agreement within each half
             (3) HC-CVD disparity separation

Usage:
    python compare_alignment_stability.py --roi V1
    python compare_alignment_stability.py  # all ROIs
"""

import sys
import argparse
import json
import time
import socket
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr
from scipy.linalg import orthogonal_procrustes

try:
    import mpi4py
    mpi4py.rc.initialize = False
    mpi4py.rc.finalize = False
    from brainiak.funcalign.srm import SRM
except ImportError:
    print("ERROR: brainiak not installed")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
ROIS = ['V1', 'V2', 'V3', 'hV4']
ROI_DIR_MAP = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}
K_VALUES = {'V1': 4, 'V2': 4, 'V3': 3, 'hV4': 4}

if socket.gethostname().startswith('node'):
    DATA_DIR = Path("/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010")
    OUTPUT_BASE = Path("/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/2D_alignment_comparison/results")
else:
    DATA_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/full_dataset_C010")
    OUTPUT_BASE = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase2_SRM_across_between/validation/2D_alignment_comparison/results")


def load_amplitudes(subject, roi):
    """Load Procrustes-aligned amplitudes: (6, 8, n_voxels)"""
    roi_dir = ROI_DIR_MAP.get(roi, roi)
    path = DATA_DIR / subject / roi_dir / "amplitudes_procrustes.npy"
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")
    return np.load(path)


def compute_rdm(patterns):
    """Compute RDM (correlation distance) from (n_colors, n_features) matrix."""
    return 1 - np.corrcoef(patterns)


def get_rdm_upper(rdm):
    """Extract upper triangle of 8x8 RDM (28 values)."""
    mask = np.triu(np.ones((8, 8), dtype=bool), k=1)
    return rdm[mask]


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


# ============================================================================
# ALIGNMENT METHODS
# ============================================================================

def align_raw(run_indices, roi):
    """
    Raw: No alignment. Each subject's voxel patterns used directly.
    RDM computed per subject in native voxel space.
    """
    patterns = {}
    for s in ALL_SUBJECTS:
        amp = load_amplitudes(s, roi)  # (6, 8, n_voxels)
        half_avg = amp[run_indices].mean(axis=0)  # (8, n_voxels)
        patterns[s] = half_avg
    return patterns


def align_procrustes(run_indices, roi):
    """
    Procrustes: Align each subject to HC mean template using orthogonal Procrustes.
    """
    # Compute HC mean as template
    hc_patterns = {}
    for s in HC_SUBJECTS:
        amp = load_amplitudes(s, roi)
        hc_patterns[s] = amp[run_indices].mean(axis=0)  # (8, n_voxels)

    template = np.mean(list(hc_patterns.values()), axis=0)  # (8, n_voxels)

    aligned = {}
    for s in ALL_SUBJECTS:
        amp = load_amplitudes(s, roi)
        half_avg = amp[run_indices].mean(axis=0)  # (8, n_voxels)
        # Procrustes: find R such that half_avg @ R ≈ template
        # Center both
        X_c = half_avg - half_avg.mean(axis=0)
        T_c = template - template.mean(axis=0)
        R, _ = orthogonal_procrustes(X_c, T_c)
        aligned[s] = X_c @ R
    return aligned


def align_srm(run_indices, roi, k):
    """
    SRM: Fit on HC, project CVD. Return patterns in shared k-dimensional space.
    """
    # Fit SRM on HC
    hc_data_srm = []
    for s in HC_SUBJECTS:
        amp = load_amplitudes(s, roi)
        half_avg = amp[run_indices].mean(axis=0)  # (8, n_voxels)
        hc_data_srm.append(half_avg.T)  # (n_voxels, 8)

    srm = SRM(n_iter=10, features=k)
    srm.fit(hc_data_srm)

    # Project HC
    aligned = {}
    for i, s in enumerate(HC_SUBJECTS):
        amp = load_amplitudes(s, roi)
        half_avg = amp[run_indices].mean(axis=0)
        W_i = srm.w_[i]
        aligned[s] = half_avg @ W_i  # (8, k)

    # Project CVD
    for s in CVD_SUBJECTS:
        amp = load_amplitudes(s, roi)
        half_avg = amp[run_indices].mean(axis=0)
        W_cvd = project_new_subject(srm, half_avg.T)
        aligned[s] = half_avg @ W_cvd  # (8, k)

    return aligned


# ============================================================================
# EVALUATION METRICS
# ============================================================================

def evaluate_method(patterns_a, patterns_b, method_name):
    """
    Evaluate alignment quality from two split-half pattern sets.

    Returns dict with:
      - within_subject_rdm_corr: per-subject RDM correlation across halves
      - between_subject_rdm_agreement: mean RDM correlation between subjects (within half)
      - hc_cvd_separation: mean CVD disparity - mean HC disparity
    """
    results = {}

    # 1. Within-subject RDM correlation across halves
    within_corrs = {}
    for s in ALL_SUBJECTS:
        if s in patterns_a and s in patterns_b:
            rdm_a = get_rdm_upper(compute_rdm(patterns_a[s]))
            rdm_b = get_rdm_upper(compute_rdm(patterns_b[s]))
            if np.all(np.isfinite(rdm_a)) and np.all(np.isfinite(rdm_b)):
                r, _ = spearmanr(rdm_a, rdm_b)
                within_corrs[s] = float(r) if np.isfinite(r) else None
            else:
                within_corrs[s] = None

    valid_within = [v for v in within_corrs.values() if v is not None]
    results['within_subject_rdm_corr'] = within_corrs
    results['within_subject_rdm_corr_mean'] = float(np.mean(valid_within)) if valid_within else None

    hc_within = [within_corrs[s] for s in HC_SUBJECTS if within_corrs.get(s) is not None]
    cvd_within = [within_corrs[s] for s in CVD_SUBJECTS if within_corrs.get(s) is not None]
    results['hc_within_mean'] = float(np.mean(hc_within)) if hc_within else None
    results['cvd_within_mean'] = float(np.mean(cvd_within)) if cvd_within else None

    # 2. Between-subject RDM agreement (within half A)
    between_corrs_a = []
    rdms_a = {}
    for s in ALL_SUBJECTS:
        if s in patterns_a:
            rdm = get_rdm_upper(compute_rdm(patterns_a[s]))
            if np.all(np.isfinite(rdm)):
                rdms_a[s] = rdm

    for i, s1 in enumerate(list(rdms_a.keys())):
        for s2 in list(rdms_a.keys())[i+1:]:
            r, _ = spearmanr(rdms_a[s1], rdms_a[s2])
            if np.isfinite(r):
                between_corrs_a.append(float(r))

    results['between_subject_rdm_agreement_a'] = float(np.mean(between_corrs_a)) if between_corrs_a else None

    # 3. HC-CVD disparity separation (using half A patterns)
    # HC reference = mean HC pattern
    hc_refs = [patterns_a[s] for s in HC_SUBJECTS if s in patterns_a]
    if hc_refs:
        hc_mean = np.mean(hc_refs, axis=0)

        hc_disps = []
        for s in HC_SUBJECTS:
            if s in patterns_a:
                d = compute_procrustes_disparity(patterns_a[s], hc_mean)
                hc_disps.append(d)

        cvd_disps = []
        for s in CVD_SUBJECTS:
            if s in patterns_a:
                d = compute_procrustes_disparity(patterns_a[s], hc_mean)
                cvd_disps.append(d)

        results['hc_disparities_a'] = {s: compute_procrustes_disparity(patterns_a[s], hc_mean)
                                       for s in HC_SUBJECTS if s in patterns_a}
        results['cvd_disparities_a'] = {s: compute_procrustes_disparity(patterns_a[s], hc_mean)
                                        for s in CVD_SUBJECTS if s in patterns_a}
        results['hc_mean_disp'] = float(np.mean(hc_disps)) if hc_disps else None
        results['cvd_mean_disp'] = float(np.mean(cvd_disps)) if cvd_disps else None
        results['separation'] = float(np.mean(cvd_disps) - np.mean(hc_disps)) if hc_disps and cvd_disps else None
    else:
        results['separation'] = None

    return results


def run_comparison(roi):
    """Run all three alignment methods for one ROI."""
    k = K_VALUES[roi]
    print(f"\n{'='*60}")
    print(f"Test 2D: Alignment Comparison — {roi} (SRM k={k})")
    print(f"{'='*60}")

    run_a = [0, 1, 2]  # runs 1-3
    run_b = [3, 4, 5]  # runs 4-6

    methods = {}

    # Raw alignment
    print("\n  [1/3] Raw (no alignment)...")
    try:
        pat_a = align_raw(run_a, roi)
        pat_b = align_raw(run_b, roi)
        methods['raw'] = evaluate_method(pat_a, pat_b, 'raw')
        print(f"    Within-subj RDM corr: {methods['raw']['within_subject_rdm_corr_mean']:.3f}")
        print(f"    Between-subj agreement: {methods['raw']['between_subject_rdm_agreement_a']:.3f}")
        print(f"    HC-CVD separation: {methods['raw']['separation']:.4f}")
    except Exception as e:
        print(f"    ERROR: {e}")
        methods['raw'] = {'error': str(e)}

    # Procrustes alignment
    print("\n  [2/3] Procrustes alignment...")
    try:
        pat_a = align_procrustes(run_a, roi)
        pat_b = align_procrustes(run_b, roi)
        methods['procrustes'] = evaluate_method(pat_a, pat_b, 'procrustes')
        print(f"    Within-subj RDM corr: {methods['procrustes']['within_subject_rdm_corr_mean']:.3f}")
        print(f"    Between-subj agreement: {methods['procrustes']['between_subject_rdm_agreement_a']:.3f}")
        print(f"    HC-CVD separation: {methods['procrustes']['separation']:.4f}")
    except Exception as e:
        print(f"    ERROR: {e}")
        methods['procrustes'] = {'error': str(e)}

    # SRM alignment
    print(f"\n  [3/3] SRM alignment (k={k})...")
    try:
        pat_a = align_srm(run_a, roi, k)
        pat_b = align_srm(run_b, roi, k)
        methods['srm'] = evaluate_method(pat_a, pat_b, 'srm')
        print(f"    Within-subj RDM corr: {methods['srm']['within_subject_rdm_corr_mean']:.3f}")
        print(f"    Between-subj agreement: {methods['srm']['between_subject_rdm_agreement_a']:.3f}")
        print(f"    HC-CVD separation: {methods['srm']['separation']:.4f}")
    except Exception as e:
        print(f"    ERROR: {e}")
        methods['srm'] = {'error': str(e)}

    # Summary comparison
    print(f"\n  --- Summary for {roi} ---")
    for name in ['raw', 'procrustes', 'srm']:
        m = methods.get(name, {})
        if 'error' not in m:
            print(f"  {name:12s}: within={m['within_subject_rdm_corr_mean']:.3f}, "
                  f"between={m['between_subject_rdm_agreement_a']:.3f}, "
                  f"sep={m['separation']:.4f}")

    return {
        'roi': roi,
        'k': k,
        'methods': methods
    }


def main():
    parser = argparse.ArgumentParser(description='Test 2D: Alignment Method Comparison')
    parser.add_argument('--roi', type=str, default=None, help='ROI. Omit for all.')
    args = parser.parse_args()

    rois = [args.roi] if args.roi else ROIS
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = OUTPUT_BASE / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'='*80}")
    print(f"Test 2D: Alignment Method Comparison (Raw vs Procrustes vs SRM)")
    print(f"ROIs: {rois}")
    print(f"{'='*80}")

    start = time.time()
    all_results = {}

    for roi in rois:
        try:
            all_results[roi] = run_comparison(roi)
        except Exception as e:
            print(f"ERROR in {roi}: {e}")
            import traceback
            traceback.print_exc()

    out_file = output_dir / "alignment_comparison_results.json"
    with open(out_file, 'w') as f:
        json.dump({
            'settings': {'rois': rois, 'timestamp': timestamp, 'elapsed': time.time() - start},
            'results': all_results
        }, f, indent=2)

    # Print final comparison table
    print(f"\n{'='*80}")
    print("FINAL COMPARISON TABLE")
    print(f"{'ROI':<6} {'Method':<12} {'Within-Subj':>11} {'Between-Subj':>12} {'HC-CVD Sep':>10}")
    print("-" * 55)
    for roi in rois:
        if roi in all_results:
            for name in ['raw', 'procrustes', 'srm']:
                m = all_results[roi].get('methods', {}).get(name, {})
                if 'error' not in m:
                    print(f"{roi:<6} {name:<12} {m['within_subject_rdm_corr_mean']:>11.3f} "
                          f"{m['between_subject_rdm_agreement_a']:>12.3f} "
                          f"{m['separation']:>10.4f}")

    print(f"\nSaved: {out_file}")
    print(f"Elapsed: {time.time() - start:.1f}s")


if __name__ == '__main__':
    main()
