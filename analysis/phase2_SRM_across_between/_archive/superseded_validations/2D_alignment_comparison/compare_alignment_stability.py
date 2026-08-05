#!/usr/bin/env python3
"""
Test 2D: Alignment Method Comparison (Split-Half Stability)

Purpose: Compare Raw vs Procrustes vs SRM alignment on the same split-half metric.
  - For each method, split runs into halves A (1-3) and B (4-6)
  - Compute per-subject RDM from each half
  - Measure: (1) within-subject RDM correlation across halves
             (2) between-subject RDM agreement within each half
             (3) HC-CVD RDM-based separation (RDM distance to HC mean RDM)

Note: Subjects have different voxel counts per ROI, so pattern-space metrics
(Procrustes disparity) only work for SRM (shared k-dim space).
All methods are compared via RDM-based metrics (always 8x8 = 28 values).

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
from scipy.spatial.distance import euclidean

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
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
ROIS = ['V1', 'V2', 'V3', 'hV4']
ROI_DIR_MAP = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}
K_VALUES = {'V1': 4, 'V2': 4, 'V3': 3, 'hV4': 4}
RDM_MASK = np.triu(np.ones((8, 8), dtype=bool), k=1)

if socket.gethostname().startswith('node'):
    DATA_DIR = Path("/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010")
    OUTPUT_BASE = Path("/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/2D_alignment_comparison/results")
else:
    DATA_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/full_dataset_C010")
    OUTPUT_BASE = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase2_SRM_across_between/validation/2D_alignment_comparison/results")


def load_amplitudes(subject, roi):
    roi_dir = ROI_DIR_MAP.get(roi, roi)
    path = DATA_DIR / subject / roi_dir / "amplitudes_procrustes.npy"
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")
    return np.load(path)


def compute_rdm(patterns):
    """RDM from (n_colors, n_features). Works regardless of n_features."""
    return 1 - np.corrcoef(patterns)


def get_rdm_upper(rdm):
    return rdm[RDM_MASK]


def project_new_subject(srm_model, new_data):
    S = srm_model.s_
    W_init = new_data @ np.linalg.pinv(S)
    U, _, Vt = np.linalg.svd(W_init, full_matrices=False)
    return U @ Vt


def compute_procrustes_disparity(X, Y):
    X_c = X - X.mean(axis=0)
    Y_c = Y - Y.mean(axis=0)
    X_n = X_c / np.linalg.norm(X_c, 'fro')
    Y_n = Y_c / np.linalg.norm(Y_c, 'fro')
    R, _ = orthogonal_procrustes(X_n, Y_n)
    return float(np.linalg.norm(X_n @ R - Y_n, 'fro'))


# ============================================================================
# ALIGNMENT: returns per-subject RDM vectors (28,) — universal across methods
# ============================================================================

def get_rdms_raw(run_indices, roi):
    """Raw: RDM from native voxel space (no cross-subject alignment)."""
    rdms = {}
    for s in ALL_SUBJECTS:
        amp = load_amplitudes(s, roi)
        half_avg = amp[run_indices].mean(axis=0)  # (8, n_voxels)
        rdm = get_rdm_upper(compute_rdm(half_avg))
        if np.all(np.isfinite(rdm)):
            rdms[s] = rdm
    return rdms


def get_rdms_procrustes(run_indices, roi):
    """Procrustes: within-subject Procrustes to run-mean, then RDM.
    (Cross-subject Procrustes impossible with different voxel counts.)"""
    rdms = {}
    for s in ALL_SUBJECTS:
        amp = load_amplitudes(s, roi)  # (6, 8, n_voxels)
        half_runs = amp[run_indices]  # (3, 8, n_voxels)
        # Align each run to the run-mean via Procrustes, then average
        run_mean = half_runs.mean(axis=0)  # (8, n_voxels)
        aligned_runs = []
        for run in half_runs:
            R, _ = orthogonal_procrustes(run, run_mean)
            aligned_runs.append(run @ R)
        aligned_avg = np.mean(aligned_runs, axis=0)  # (8, n_voxels)
        rdm = get_rdm_upper(compute_rdm(aligned_avg))
        if np.all(np.isfinite(rdm)):
            rdms[s] = rdm
    return rdms


def get_rdms_srm(run_indices, roi, k):
    """SRM: HC-only fit, project all subjects, RDM in shared k-dim space."""
    hc_data = []
    for s in HC_SUBJECTS:
        amp = load_amplitudes(s, roi)
        half_avg = amp[run_indices].mean(axis=0)
        hc_data.append(half_avg.T)  # (n_voxels, 8)

    srm = SRM(n_iter=10, features=k)
    srm.fit(hc_data)

    rdms = {}
    patterns = {}  # keep for disparity computation

    # HC
    for i, s in enumerate(HC_SUBJECTS):
        amp = load_amplitudes(s, roi)
        half_avg = amp[run_indices].mean(axis=0)
        aligned = half_avg @ srm.w_[i]  # (8, k)
        patterns[s] = aligned
        rdm = get_rdm_upper(compute_rdm(aligned))
        if np.all(np.isfinite(rdm)):
            rdms[s] = rdm

    # CVD
    for s in CVD_SUBJECTS:
        amp = load_amplitudes(s, roi)
        half_avg = amp[run_indices].mean(axis=0)
        W_cvd = project_new_subject(srm, half_avg.T)
        aligned = half_avg @ W_cvd  # (8, k)
        patterns[s] = aligned
        rdm = get_rdm_upper(compute_rdm(aligned))
        if np.all(np.isfinite(rdm)):
            rdms[s] = rdm

    return rdms, patterns


# ============================================================================
# EVALUATION (all RDM-based, works for any method)
# ============================================================================

def evaluate_rdms(rdms_a, rdms_b, method_name, patterns_a=None):
    """
    Evaluate from two half's RDM dicts {subject: rdm_vector(28,)}.
    Optionally compute pattern-space disparity if patterns_a provided.
    """
    results = {}

    # 1. Within-subject RDM correlation across halves
    within_corrs = {}
    for s in ALL_SUBJECTS:
        if s in rdms_a and s in rdms_b:
            r, _ = spearmanr(rdms_a[s], rdms_b[s])
            within_corrs[s] = float(r) if np.isfinite(r) else None
        else:
            within_corrs[s] = None

    valid = [v for v in within_corrs.values() if v is not None]
    hc_vals = [within_corrs[s] for s in HC_SUBJECTS if within_corrs[s] is not None]
    cvd_vals = [within_corrs[s] for s in CVD_SUBJECTS if within_corrs[s] is not None]

    results['within_subject_rdm_corr'] = within_corrs
    results['within_subject_rdm_corr_mean'] = float(np.mean(valid)) if valid else None
    results['hc_within_mean'] = float(np.mean(hc_vals)) if hc_vals else None
    results['cvd_within_mean'] = float(np.mean(cvd_vals)) if cvd_vals else None

    # 2. Between-subject RDM agreement (within half A)
    subjects_a = [s for s in ALL_SUBJECTS if s in rdms_a]
    between_corrs = []
    for i, s1 in enumerate(subjects_a):
        for s2 in subjects_a[i+1:]:
            r, _ = spearmanr(rdms_a[s1], rdms_a[s2])
            if np.isfinite(r):
                between_corrs.append(float(r))
    results['between_subject_rdm_agreement'] = float(np.mean(between_corrs)) if between_corrs else None

    # 3. HC-CVD separation via RDM distance
    # Mean HC RDM as reference
    hc_rdms_a = [rdms_a[s] for s in HC_SUBJECTS if s in rdms_a]
    if hc_rdms_a:
        mean_hc_rdm = np.mean(hc_rdms_a, axis=0)

        hc_dists = [euclidean(rdms_a[s], mean_hc_rdm) for s in HC_SUBJECTS if s in rdms_a]
        cvd_dists = [euclidean(rdms_a[s], mean_hc_rdm) for s in CVD_SUBJECTS if s in rdms_a]

        results['hc_rdm_dist'] = {s: float(euclidean(rdms_a[s], mean_hc_rdm))
                                  for s in HC_SUBJECTS if s in rdms_a}
        results['cvd_rdm_dist'] = {s: float(euclidean(rdms_a[s], mean_hc_rdm))
                                   for s in CVD_SUBJECTS if s in rdms_a}
        results['hc_mean_rdm_dist'] = float(np.mean(hc_dists))
        results['cvd_mean_rdm_dist'] = float(np.mean(cvd_dists))
        results['separation'] = float(np.mean(cvd_dists) - np.mean(hc_dists))
    else:
        results['separation'] = None

    # 4. Pattern-space disparity (SRM only)
    if patterns_a is not None:
        hc_pats = [patterns_a[s] for s in HC_SUBJECTS if s in patterns_a]
        if hc_pats:
            hc_mean_pat = np.mean(hc_pats, axis=0)
            results['pattern_disp_hc'] = {
                s: compute_procrustes_disparity(patterns_a[s], hc_mean_pat)
                for s in HC_SUBJECTS if s in patterns_a}
            results['pattern_disp_cvd'] = {
                s: compute_procrustes_disparity(patterns_a[s], hc_mean_pat)
                for s in CVD_SUBJECTS if s in patterns_a}
            hd = list(results['pattern_disp_hc'].values())
            cd = list(results['pattern_disp_cvd'].values())
            results['pattern_sep'] = float(np.mean(cd) - np.mean(hd))

    return results


def run_comparison(roi):
    k = K_VALUES[roi]
    print(f"\n{'='*60}")
    print(f"Test 2D: Alignment Comparison — {roi} (SRM k={k})")
    print(f"{'='*60}")

    run_a = [0, 1, 2]
    run_b = [3, 4, 5]
    methods = {}

    # Raw
    print("\n  [1/3] Raw (no alignment)...")
    try:
        rdms_a = get_rdms_raw(run_a, roi)
        rdms_b = get_rdms_raw(run_b, roi)
        methods['raw'] = evaluate_rdms(rdms_a, rdms_b, 'raw')
        m = methods['raw']
        print(f"    Within-subj RDM: {m['within_subject_rdm_corr_mean']:.3f} "
              f"(HC={m['hc_within_mean']:.3f}, CVD={m['cvd_within_mean']:.3f})")
        print(f"    Between-subj RDM: {m['between_subject_rdm_agreement']:.3f}")
        print(f"    RDM separation: {m['separation']:.4f}")
    except Exception as e:
        print(f"    ERROR: {e}")
        methods['raw'] = {'error': str(e)}

    # Procrustes (within-subject run alignment)
    print("\n  [2/3] Procrustes (within-subject run alignment)...")
    try:
        rdms_a = get_rdms_procrustes(run_a, roi)
        rdms_b = get_rdms_procrustes(run_b, roi)
        methods['procrustes'] = evaluate_rdms(rdms_a, rdms_b, 'procrustes')
        m = methods['procrustes']
        print(f"    Within-subj RDM: {m['within_subject_rdm_corr_mean']:.3f} "
              f"(HC={m['hc_within_mean']:.3f}, CVD={m['cvd_within_mean']:.3f})")
        print(f"    Between-subj RDM: {m['between_subject_rdm_agreement']:.3f}")
        print(f"    RDM separation: {m['separation']:.4f}")
    except Exception as e:
        print(f"    ERROR: {e}")
        methods['procrustes'] = {'error': str(e)}

    # SRM
    print(f"\n  [3/3] SRM (k={k})...")
    try:
        rdms_a, pats_a = get_rdms_srm(run_a, roi, k)
        rdms_b, pats_b = get_rdms_srm(run_b, roi, k)
        methods['srm'] = evaluate_rdms(rdms_a, rdms_b, 'srm', patterns_a=pats_a)
        m = methods['srm']
        print(f"    Within-subj RDM: {m['within_subject_rdm_corr_mean']:.3f} "
              f"(HC={m['hc_within_mean']:.3f}, CVD={m['cvd_within_mean']:.3f})")
        print(f"    Between-subj RDM: {m['between_subject_rdm_agreement']:.3f}")
        print(f"    RDM separation: {m['separation']:.4f}")
        if 'pattern_sep' in m:
            print(f"    Pattern disparity sep: {m['pattern_sep']:.4f}")
    except Exception as e:
        print(f"    ERROR: {e}")
        methods['srm'] = {'error': str(e)}

    # Summary
    print(f"\n  --- Summary for {roi} ---")
    for name in ['raw', 'procrustes', 'srm']:
        m = methods.get(name, {})
        if 'error' not in m:
            print(f"  {name:12s}: within={m['within_subject_rdm_corr_mean']:.3f}, "
                  f"between={m['between_subject_rdm_agreement']:.3f}, "
                  f"rdm_sep={m['separation']:.4f}")

    return {'roi': roi, 'k': k, 'methods': methods}


def main():
    parser = argparse.ArgumentParser(description='Test 2D: Alignment Method Comparison')
    parser.add_argument('--roi', type=str, default=None, help='ROI. Omit for all.')
    args = parser.parse_args()

    rois = [args.roi] if args.roi else ROIS
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)

    print(f"{'='*80}")
    print(f"Test 2D: Alignment Comparison (Raw vs Procrustes vs SRM)")
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

    roi_tag = args.roi if args.roi else "all"
    out_file = OUTPUT_BASE / f"alignment_comparison_{roi_tag}_results.json"
    with open(out_file, 'w') as f:
        json.dump({
            'config': {
                'test': '2D_alignment_comparison',
                'data_dir': str(DATA_DIR),
                'dataset': 'full_dataset_C010',
                'input_file': 'amplitudes_procrustes.npy',
                'hc_subjects': HC_SUBJECTS,
                'cvd_subjects': CVD_SUBJECTS,
                'k_values': K_VALUES,
                'srm_n_iter': 10,
                'methods': ['raw', 'procrustes (within-subject run alignment)', 'srm (HC-only fit)'],
                'set_a_runs': [1, 2, 3],
                'set_b_runs': [4, 5, 6],
                'metrics': {
                    'all_methods': ['within_subject_rdm_corr (Spearman)', 'between_subject_rdm_agreement (Spearman)', 'rdm_separation (Euclidean distance to HC mean RDM)'],
                    'srm_only': ['pattern_disparity (Procrustes in shared k-dim space)'],
                },
            },
            'settings': {'rois': rois, 'timestamp': timestamp, 'elapsed': time.time() - start},
            'results': all_results
        }, f, indent=2)

    print(f"\n{'='*80}")
    print("FINAL COMPARISON TABLE")
    print(f"{'ROI':<6} {'Method':<12} {'Within-RDM':>10} {'Between-RDM':>11} {'RDM Sep':>9}")
    print("-" * 52)
    for roi in rois:
        if roi in all_results:
            for name in ['raw', 'procrustes', 'srm']:
                m = all_results[roi].get('methods', {}).get(name, {})
                if 'error' not in m:
                    print(f"{roi:<6} {name:<12} {m['within_subject_rdm_corr_mean']:>10.3f} "
                          f"{m['between_subject_rdm_agreement']:>11.3f} "
                          f"{m['separation']:>9.4f}")

    print(f"\nSaved: {out_file}")
    print(f"Elapsed: {time.time() - start:.1f}s")


if __name__ == '__main__':
    main()
