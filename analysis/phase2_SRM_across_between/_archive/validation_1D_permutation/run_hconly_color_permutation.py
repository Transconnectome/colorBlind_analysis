"""
Test 1D (HC-Only SRM): Color Label Permutation with HC-Only SRM Retraining

Purpose: Re-run the rigorous color permutation test (1D + 1D-ext) using HC-only
SRM training to match the corrected main analysis (RT-2 fix).

Critical Difference from Previous Versions:
- PREVIOUS: SRM trained on ALL 10 subjects (HC + CVD) — circularity
- THIS: SRM trained on 7 HC only; CVD projected via SVD into HC space

Combines both test variants in one pass:
  1D:     Group-difference disparity + within-group RDM correlations
  1D-ext: Per-group LOO disparity + per-subject p-values

Method:
1. Load ORIGINAL amplitude data (6 runs × 8 colors × n_voxels)
2. Average across runs → (8 colors × n_voxels)
3. For observed + each permutation:
   - (Permutations only: shuffle color labels in ORIGINAL data)
   - Train SRM on HC subjects only
   - Project CVD into HC space via SVD: W = U @ Vt from SVD(X @ pinv(S))
   - Compute both metric sets in the resulting space
4. Compare observed metrics to null distributions
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from scipy.linalg import orthogonal_procrustes
from scipy.spatial.distance import squareform, pdist
from scipy.stats import spearmanr

HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ROIS = ['V1', 'V2', 'V3', 'hV4']

# Updated k values (hV4 revised from 4→3 per formal aggregation)
SRM_K_VALUES = {'V1': 4, 'V2': 4, 'V3': 3, 'hV4': 3}


def load_baseline_amplitudes(baseline_dir: Path, subject: str, roi: str) -> np.ndarray:
    """Load baseline amplitude data (6 runs, 8 colors, n_voxels)."""
    roi_mapped = 'V4' if roi == 'hV4' else roi
    for name in ['amplitudes_procrustes.npy', 'amplitudes_raw.npy']:
        amp_file = baseline_dir / subject / roi_mapped / name
        if amp_file.exists():
            amplitudes = np.load(amp_file)
            if amplitudes.shape[0] != 6 or amplitudes.shape[1] != 8:
                raise ValueError(f"Unexpected shape: {amplitudes.shape}")
            return amplitudes
    raise FileNotFoundError(f"Amplitude file not found for {subject}/{roi_mapped}")


def permute_color_labels(amplitudes: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Randomly permute color labels. Uses Generator API (no global state)."""
    perm_idx = rng.permutation(8)
    if amplitudes.ndim == 3:
        return amplitudes[:, perm_idx, :]
    elif amplitudes.ndim == 2:
        return amplitudes[perm_idx, :]
    else:
        raise ValueError(f"Unexpected shape: {amplitudes.shape}")


def compute_procrustes_disparity(X: np.ndarray, Y: np.ndarray) -> float:
    """Procrustes disparity between two pattern matrices."""
    X_c = X - X.mean(axis=0)
    Y_c = Y - Y.mean(axis=0)
    X_n = X_c / np.linalg.norm(X_c, 'fro')
    Y_n = Y_c / np.linalg.norm(Y_c, 'fro')
    R, _ = orthogonal_procrustes(X_n, Y_n)
    return float(np.linalg.norm(X_n @ R - Y_n, 'fro'))


def compute_rdm(patterns: np.ndarray) -> np.ndarray:
    """RDM from patterns (8, k)."""
    return squareform(pdist(patterns, metric='correlation'))


def project_new_subject(srm_model, new_data: np.ndarray) -> np.ndarray:
    """
    Project a new subject into HC-learned SRM space via SVD.

    Parameters
    ----------
    srm_model : brainiak SRM model (fitted on HC)
    new_data : np.ndarray, shape (n_voxels, n_timepoints)

    Returns
    -------
    projected : np.ndarray, shape (k, n_timepoints)
    """
    S = srm_model.s_  # shared response (k, n_timepoints)
    W_init = new_data @ np.linalg.pinv(S)  # (n_voxels, k)
    U, _, Vt = np.linalg.svd(W_init, full_matrices=False)
    W_new = U @ Vt  # orthogonal projection matrix
    return W_new.T @ new_data  # (k, n_timepoints)


def train_hconly_srm_and_align(hc_data_list, cvd_data_list, k):
    """
    Train SRM on HC only, project CVD into HC space.

    Parameters
    ----------
    hc_data_list : list of (8, n_voxels) arrays
    cvd_data_list : list of (8, n_voxels) arrays
    k : int

    Returns
    -------
    hc_aligned : list of (8, k) arrays
    cvd_aligned : list of (8, k) arrays
    """
    from brainiak.funcalign.srm import SRM

    # Train on HC only (n_voxels, 8) format for BrainIAK
    hc_srm_input = [amp.T for amp in hc_data_list]
    srm = SRM(n_iter=10, features=k)
    srm.fit(hc_srm_input)

    # Transform HC
    hc_transformed = srm.transform(hc_srm_input)  # list of (k, 8)
    hc_aligned = [arr.T for arr in hc_transformed]  # list of (8, k)

    # Project CVD via SVD
    cvd_aligned = []
    for cvd_amp in cvd_data_list:
        projected = project_new_subject(srm, cvd_amp.T)  # (k, 8)
        cvd_aligned.append(projected.T)  # (8, k)

    return hc_aligned, cvd_aligned


def compute_all_metrics(hc_patterns, cvd_patterns):
    """
    Compute both 1D and 1D-ext metrics in one call.

    Returns dict with keys for both metric sets.
    """
    n_hc = len(hc_patterns)
    mask_8x8 = np.triu(np.ones((8, 8), dtype=bool), k=1)

    # --- 1D metrics: group-difference (HC uses LOO to avoid group-mean leakage) ---
    hc_arr = np.array(hc_patterns)  # (n_hc, 8, k)
    hc_reference_full = hc_arr.mean(axis=0)  # (8, k) — for CVD only

    # HC: Leave-One-Out disparity (sub-i vs mean of other n-1)
    hc_disparities = []
    for i in range(n_hc):
        others = np.delete(hc_arr, i, axis=0)
        loo_ref = others.mean(axis=0)
        hc_disparities.append(compute_procrustes_disparity(hc_patterns[i], loo_ref))

    # CVD: vs full HC mean (no leakage)
    cvd_disparities = [compute_procrustes_disparity(p, hc_reference_full) for p in cvd_patterns]

    hc_disp_mean = np.mean(hc_disparities)
    cvd_disp_mean = np.mean(cvd_disparities)
    disparity_difference = cvd_disp_mean - hc_disp_mean

    # RDMs
    hc_rdms = [compute_rdm(p) for p in hc_patterns]
    cvd_rdms = [compute_rdm(p) for p in cvd_patterns]

    hc_rdm_corrs = []
    for i in range(len(hc_rdms)):
        for j in range(i + 1, len(hc_rdms)):
            r, _ = spearmanr(hc_rdms[i][mask_8x8], hc_rdms[j][mask_8x8])
            if np.isfinite(r):
                hc_rdm_corrs.append(r)

    cvd_rdm_corrs = []
    for i in range(len(cvd_rdms)):
        for j in range(i + 1, len(cvd_rdms)):
            r, _ = spearmanr(cvd_rdms[i][mask_8x8], cvd_rdms[j][mask_8x8])
            if np.isfinite(r):
                cvd_rdm_corrs.append(r)

    # --- 1D-ext metrics: per-group LOO ---
    # hc_arr already computed above
    hc_loo_disps = []
    for i in range(n_hc):
        others = np.delete(hc_arr, i, axis=0)
        loo_ref = others.mean(axis=0)
        hc_loo_disps.append(compute_procrustes_disparity(hc_patterns[i], loo_ref))

    cvd_loo_disps = []
    if len(cvd_patterns) > 1:
        cvd_arr = np.array(cvd_patterns)
        for i in range(len(cvd_patterns)):
            others = np.delete(cvd_arr, i, axis=0)
            loo_ref = others.mean(axis=0)
            cvd_loo_disps.append(compute_procrustes_disparity(cvd_patterns[i], loo_ref))

    cvd_pairwise_disps = []
    for i in range(len(cvd_patterns)):
        for j in range(i + 1, len(cvd_patterns)):
            cvd_pairwise_disps.append(
                compute_procrustes_disparity(cvd_patterns[i], cvd_patterns[j]))

    return {
        # 1D
        'disparity_difference': float(disparity_difference),
        'hc_disp_mean': float(hc_disp_mean),
        'cvd_disp_mean': float(cvd_disp_mean),
        'hc_rdm_corr_mean': float(np.mean(hc_rdm_corrs)) if hc_rdm_corrs else 0.0,
        'cvd_rdm_corr_mean': float(np.mean(cvd_rdm_corrs)) if cvd_rdm_corrs else 0.0,
        # 1D-ext
        'hc_loo_disp_mean': float(np.mean(hc_loo_disps)),
        'cvd_loo_disp_mean': float(np.mean(cvd_loo_disps)) if cvd_loo_disps else float('nan'),
        'cvd_pairwise_disp_mean': float(np.mean(cvd_pairwise_disps)) if cvd_pairwise_disps else float('nan'),
        'per_subject_hc_loo_disp': [float(d) for d in hc_loo_disps],
        'per_subject_cvd_loo_disp': [float(d) for d in cvd_loo_disps],
        # Individual disparities (for per-subject analysis)
        'hc_disparities': [float(d) for d in hc_disparities],
        'cvd_disparities': [float(d) for d in cvd_disparities],
    }


def run_hconly_permutation_test(baseline_dir: Path, output_dir: Path,
                                 n_permutations: int = 1000, seed: int = 42):
    """
    Run HC-only SRM color permutation test for all ROIs.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = output_dir / f"hconly_{timestamp}"
    results_dir.mkdir(parents=True, exist_ok=True)

    all_results = {}

    for roi in ROIS:
        k = SRM_K_VALUES[roi]

        print(f"\n{'=' * 80}")
        print(f"HC-Only Color Permutation Test — {roi} (k={k})")
        print(f"{'=' * 80}")
        print(f"Permutations: {n_permutations}")
        print(f"Method: Shuffle → HC-only SRM → CVD projection → metrics")

        # Load baseline amplitudes
        print("\nLoading data...")
        hc_amp_list = []
        cvd_amp_list = []

        for subject in HC_SUBJECTS:
            amp = load_baseline_amplitudes(baseline_dir, subject, roi)
            hc_amp_list.append(amp.mean(axis=0))  # (8, n_voxels)
            print(f"  {subject}: {hc_amp_list[-1].shape}")

        for subject in CVD_SUBJECTS:
            amp = load_baseline_amplitudes(baseline_dir, subject, roi)
            cvd_amp_list.append(amp.mean(axis=0))
            print(f"  {subject}: {cvd_amp_list[-1].shape}")

        # Observed (true labels)
        print("\nObserved (true labels)...")
        hc_aligned, cvd_aligned = train_hconly_srm_and_align(hc_amp_list, cvd_amp_list, k)
        observed = compute_all_metrics(hc_aligned, cvd_aligned)

        print(f"  Disparity diff (CVD-HC): {observed['disparity_difference']:.4f}")
        print(f"  HC RDM corr: {observed['hc_rdm_corr_mean']:.3f}")
        print(f"  CVD RDM corr: {observed['cvd_rdm_corr_mean']:.3f}")
        print(f"  HC LOO disp: {observed['hc_loo_disp_mean']:.4f}")
        print(f"  CVD LOO disp: {observed['cvd_loo_disp_mean']:.4f}")

        # Permutation null distribution
        print(f"\nRunning {n_permutations} permutations...")
        rng = np.random.default_rng(seed)
        null_metrics = {key: [] for key in [
            'disparity_difference', 'hc_rdm_corr_mean', 'cvd_rdm_corr_mean',
            'hc_loo_disp_mean', 'cvd_loo_disp_mean', 'cvd_pairwise_disp_mean',
        ]}
        null_per_subject_hc = {i: [] for i in range(len(hc_amp_list))}
        null_per_subject_cvd = {i: [] for i in range(len(cvd_amp_list))}
        n_failed = 0

        for perm_i in range(n_permutations):
            if (perm_i + 1) % 50 == 0:
                print(f"  Permutation {perm_i + 1}/{n_permutations}")

            try:
                # Shuffle color labels for each subject independently
                hc_shuffled = [permute_color_labels(amp, rng) for amp in hc_amp_list]
                cvd_shuffled = [permute_color_labels(amp, rng) for amp in cvd_amp_list]

                # HC-only SRM + CVD projection
                hc_al, cvd_al = train_hconly_srm_and_align(hc_shuffled, cvd_shuffled, k)
                m = compute_all_metrics(hc_al, cvd_al)

                for key in null_metrics:
                    null_metrics[key].append(m[key])
                for i, d in enumerate(m['per_subject_hc_loo_disp']):
                    null_per_subject_hc[i].append(d)
                for i, d in enumerate(m['per_subject_cvd_loo_disp']):
                    null_per_subject_cvd[i].append(d)

            except Exception as e:
                n_failed += 1
                if n_failed <= 3:
                    print(f"  WARNING: Permutation {perm_i} failed: {e}")

        n_success = n_permutations - n_failed
        print(f"  Successful: {n_success}/{n_permutations}")

        # Convert to arrays
        for key in null_metrics:
            null_metrics[key] = np.array(null_metrics[key])

        # --- P-values ---
        # 1D: disparity difference (higher observed = CVD more dispersed)
        p_disp_diff = float(np.mean(null_metrics['disparity_difference'] >= observed['disparity_difference']))
        # 1D: RDM correlations (higher observed = more color structure)
        p_hc_rdm = float(np.mean(null_metrics['hc_rdm_corr_mean'] >= observed['hc_rdm_corr_mean']))
        p_cvd_rdm = float(np.mean(null_metrics['cvd_rdm_corr_mean'] >= observed['cvd_rdm_corr_mean']))
        # 1D-ext: LOO disparity (lower observed = more color-consistent)
        p_hc_loo = float(np.mean(null_metrics['hc_loo_disp_mean'] <= observed['hc_loo_disp_mean']))
        p_cvd_loo = float(np.mean(null_metrics['cvd_loo_disp_mean'] <= observed['cvd_loo_disp_mean']))
        p_cvd_pair = float(np.mean(null_metrics['cvd_pairwise_disp_mean'] <= observed['cvd_pairwise_disp_mean']))

        # Per-subject p-values
        per_subject_hc_pvals = []
        for i, obs_d in enumerate(observed['per_subject_hc_loo_disp']):
            arr = np.array(null_per_subject_hc[i])
            per_subject_hc_pvals.append(float(np.mean(arr <= obs_d)) if len(arr) > 0 else float('nan'))

        per_subject_cvd_pvals = []
        for i, obs_d in enumerate(observed['per_subject_cvd_loo_disp']):
            arr = np.array(null_per_subject_cvd[i])
            per_subject_cvd_pvals.append(float(np.mean(arr <= obs_d)) if len(arr) > 0 else float('nan'))

        # Store results
        roi_results = {
            'roi': roi,
            'k': k,
            'method': 'hc_only_srm_with_cvd_projection',
            'n_permutations': n_permutations,
            'n_successful': n_success,
            'observed': observed,
            'p_values': {
                # 1D
                'disparity_difference': p_disp_diff,
                'hc_rdm_correlation': p_hc_rdm,
                'cvd_rdm_correlation': p_cvd_rdm,
                # 1D-ext
                'hc_loo_disp': p_hc_loo,
                'cvd_loo_disp': p_cvd_loo,
                'cvd_pairwise_disp': p_cvd_pair,
                # Per-subject
                'per_subject_hc_loo': per_subject_hc_pvals,
                'per_subject_cvd_loo': per_subject_cvd_pvals,
            },
            'null_means': {
                'disparity_difference': float(np.mean(null_metrics['disparity_difference'])),
                'hc_rdm_corr_mean': float(np.mean(null_metrics['hc_rdm_corr_mean'])),
                'cvd_rdm_corr_mean': float(np.mean(null_metrics['cvd_rdm_corr_mean'])),
                'hc_loo_disp_mean': float(np.mean(null_metrics['hc_loo_disp_mean'])),
                'cvd_loo_disp_mean': float(np.mean(null_metrics['cvd_loo_disp_mean'])),
                'cvd_pairwise_disp_mean': float(np.mean(null_metrics['cvd_pairwise_disp_mean'])),
            },
        }

        all_results[roi] = roi_results

        # Print summary
        print(f"\n--- {roi} Summary ---")
        print(f"  1D  Disparity diff:  obs={observed['disparity_difference']:.4f}  null={roi_results['null_means']['disparity_difference']:.4f}  p={p_disp_diff:.4f}")
        print(f"  1D  HC RDM corr:     obs={observed['hc_rdm_corr_mean']:.3f}  null={roi_results['null_means']['hc_rdm_corr_mean']:.3f}  p={p_hc_rdm:.4f}")
        print(f"  1D  CVD RDM corr:    obs={observed['cvd_rdm_corr_mean']:.3f}  null={roi_results['null_means']['cvd_rdm_corr_mean']:.3f}  p={p_cvd_rdm:.4f}")
        print(f"  EXT HC LOO disp:     obs={observed['hc_loo_disp_mean']:.4f}  null={roi_results['null_means']['hc_loo_disp_mean']:.4f}  p={p_hc_loo:.4f}")
        print(f"  EXT CVD LOO disp:    obs={observed['cvd_loo_disp_mean']:.4f}  null={roi_results['null_means']['cvd_loo_disp_mean']:.4f}  p={p_cvd_loo:.4f}")
        print(f"  EXT CVD pairwise:    obs={observed['cvd_pairwise_disp_mean']:.4f}  null={roi_results['null_means']['cvd_pairwise_disp_mean']:.4f}  p={p_cvd_pair:.4f}")

        print(f"\n  Per-subject HC LOO p-values:")
        for subj, p in zip(HC_SUBJECTS, per_subject_hc_pvals):
            print(f"    {subj}: p={p:.4f}")
        print(f"  Per-subject CVD LOO p-values:")
        for subj, p in zip(CVD_SUBJECTS, per_subject_cvd_pvals):
            print(f"    {subj}: p={p:.4f}")

    # Save combined results
    output = {
        'config': {
            'method': 'hc_only_srm_color_permutation',
            'fix': 'RT-2: HC-only SRM training; CVD projected via SVD',
            'k_values': SRM_K_VALUES,
            'n_permutations': n_permutations,
            'seed': seed,
            'timestamp': timestamp,
        },
        'results': all_results,
    }

    out_file = results_dir / 'hconly_color_permutation_results.json'
    with open(out_file, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n{'=' * 80}")
    print(f"All results saved to: {out_file}")
    print(f"{'=' * 80}")

    return output


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='HC-only SRM color permutation test (1D + 1D-ext)')
    parser.add_argument('--n_permutations', type=int, default=1000,
                        help='Number of permutations (default: 1000)')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
    baseline_dir = base_dir / 'analysis' / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'
    output_dir = base_dir / 'analysis' / 'phase2_SRM_across_between' / 'validation' / '1D_permutation' / 'results_hconly'

    results = run_hconly_permutation_test(baseline_dir, output_dir,
                                           n_permutations=args.n_permutations,
                                           seed=args.seed)

    print("\nDone!")
