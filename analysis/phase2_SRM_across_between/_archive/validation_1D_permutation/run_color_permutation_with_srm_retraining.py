"""
Test 1D (RIGOROUS): Color Label Permutation with SRM Retraining

Purpose: Strongest test of color label dependency - retrain SRM for each permutation

Critical Difference from Previous Version:
- PREVIOUS: Shuffle labels AFTER SRM alignment (biased - SRM space encodes true colors)
- THIS: Shuffle labels BEFORE SRM training → retrain SRM → compute metrics
         (unbiased - each permutation has its own SRM space)

Method:
1. Load ORIGINAL amplitude data (before SRM, 6 runs × 8 colors × n_voxels)
2. Average across runs → (8 colors × n_voxels)
3. For each permutation:
   - Shuffle color labels (permute rows 0-7) in ORIGINAL data
   - Train SRM on shuffled data
   - Compute metrics in newly learned SRM space
4. Compare observed metrics to null distribution

Computational Cost:
- 1000 permutations × 4 ROIs = 4000 SRM trainings
- Each SRM: ~1-2 min on server
- Total: ~50-100 hours compute (MUST run on server with array jobs!)

Expected Results:
- If patterns truly depend on color labels:
  * Observed (true labels) should be significantly higher than null
  * p < 0.05 for RDM correlations
  * Disparity difference may or may not be significant (depends on color-specificity)
"""

import numpy as np
import json
import sys
from pathlib import Path
from datetime import datetime
from scipy.linalg import orthogonal_procrustes
from scipy.spatial.distance import squareform, pdist
from scipy.stats import spearmanr

# Add parent directories to path
script_dir = Path(__file__).parent
sys.path.append(str(script_dir.parent))
sys.path.append(str(script_dir.parent.parent))

# BrainIAK SRM will be imported when needed (in run_single_permutation)

HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
ROIS = ['V1', 'V2', 'V3', 'hV4']

# SRM k values (from original analysis)
SRM_K_VALUES = {'V1': 4, 'V2': 4, 'V3': 3, 'hV4': 4}


def load_baseline_amplitudes(baseline_dir: Path, subject: str, roi: str) -> np.ndarray:
    """
    Load baseline amplitude data (before SRM).

    Returns
    -------
    amplitudes : np.ndarray
        Shape (6 runs, 8 colors, n_voxels)
    """
    roi_mapped = 'V4' if roi == 'hV4' else roi

    amp_file_options = [
        baseline_dir / subject / roi_mapped / 'amplitudes_procrustes.npy',
        baseline_dir / subject / roi_mapped / 'amplitudes_raw.npy'
    ]

    for amp_file in amp_file_options:
        if amp_file.exists():
            amplitudes = np.load(amp_file)
            if amplitudes.shape[0] != 6 or amplitudes.shape[1] != 8:
                raise ValueError(f"Unexpected amplitude shape: {amplitudes.shape}")
            return amplitudes

    raise FileNotFoundError(f"Amplitude file not found for {subject}/{roi_mapped}")


def permute_color_labels(amplitudes: np.ndarray, seed: int = None) -> np.ndarray:
    """
    Randomly permute color labels in ORIGINAL amplitude data.

    Parameters
    ----------
    amplitudes : np.ndarray
        Shape (6 runs, 8 colors, n_voxels) OR (8 colors, n_voxels)
    seed : int
        Random seed

    Returns
    -------
    permuted : np.ndarray
        Same shape with color dimension permuted
    """
    if seed is not None:
        np.random.seed(seed)

    perm_idx = np.random.permutation(8)

    if amplitudes.ndim == 3:  # (6, 8, n_voxels)
        return amplitudes[:, perm_idx, :]
    elif amplitudes.ndim == 2:  # (8, n_voxels)
        return amplitudes[perm_idx, :]
    else:
        raise ValueError(f"Unexpected amplitude shape: {amplitudes.shape}")


def compute_procrustes_disparity(X: np.ndarray, Y: np.ndarray) -> float:
    """Compute Procrustes disparity."""
    X_centered = X - X.mean(axis=0)
    Y_centered = Y - Y.mean(axis=0)
    X_norm = X_centered / np.linalg.norm(X_centered, 'fro')
    Y_norm = Y_centered / np.linalg.norm(Y_centered, 'fro')
    R, _ = orthogonal_procrustes(X_norm, Y_norm)
    disparity = np.linalg.norm(X_norm @ R - Y_norm, 'fro')
    return disparity


def compute_rdm(patterns: np.ndarray) -> np.ndarray:
    """Compute RDM from patterns (8, k)."""
    rdm = squareform(pdist(patterns, metric='correlation'))
    return rdm


def compute_metrics_from_aligned_patterns(hc_patterns: list, cvd_patterns: list) -> dict:
    """
    Compute validation metrics from SRM-aligned patterns.

    Parameters
    ----------
    hc_patterns : list
        List of HC patterns, each (8, k)
    cvd_patterns : list
        List of CVD patterns, each (8, k)

    Returns
    -------
    metrics : dict
    """
    # HC reference
    hc_reference = np.mean(hc_patterns, axis=0)  # (8, k)

    # Compute disparities
    hc_disparities = [compute_procrustes_disparity(p, hc_reference) for p in hc_patterns]
    cvd_disparities = [compute_procrustes_disparity(p, hc_reference) for p in cvd_patterns]

    hc_disparity_mean = np.mean(hc_disparities)
    cvd_disparity_mean = np.mean(cvd_disparities)
    disparity_difference = cvd_disparity_mean - hc_disparity_mean

    # Compute RDMs
    hc_rdms = [compute_rdm(p) for p in hc_patterns]
    cvd_rdms = [compute_rdm(p) for p in cvd_patterns]

    # Within-HC RDM correlations
    hc_rdm_correlations = []
    for i in range(len(hc_rdms)):
        for j in range(i+1, len(hc_rdms)):
            mask = np.triu(np.ones_like(hc_rdms[i], dtype=bool), k=1)
            r, _ = spearmanr(hc_rdms[i][mask], hc_rdms[j][mask])
            if np.isfinite(r):
                hc_rdm_correlations.append(r)

    # Within-CVD RDM correlations
    cvd_rdm_correlations = []
    for i in range(len(cvd_rdms)):
        for j in range(i+1, len(cvd_rdms)):
            mask = np.triu(np.ones_like(cvd_rdms[i], dtype=bool), k=1)
            r, _ = spearmanr(cvd_rdms[i][mask], cvd_rdms[j][mask])
            if np.isfinite(r):
                cvd_rdm_correlations.append(r)

    return {
        'hc_disparity_mean': float(hc_disparity_mean),
        'cvd_disparity_mean': float(cvd_disparity_mean),
        'disparity_difference': float(disparity_difference),
        'hc_rdm_correlation_mean': float(np.mean(hc_rdm_correlations)) if hc_rdm_correlations else 0.0,
        'cvd_rdm_correlation_mean': float(np.mean(cvd_rdm_correlations)) if cvd_rdm_correlations else 0.0
    }


def run_single_permutation(hc_amplitudes_list: list, cvd_amplitudes_list: list,
                           roi: str, k: int, seed: int) -> dict:
    """
    Run a single permutation: shuffle labels → train SRM → compute metrics.

    Parameters
    ----------
    hc_amplitudes_list : list
        List of HC amplitudes, each (8, n_voxels)
    cvd_amplitudes_list : list
        List of CVD amplitudes, each (8, n_voxels)
    roi : str
    k : int
        SRM dimensionality
    seed : int
        Random seed for permutation

    Returns
    -------
    metrics : dict
    """
    # Shuffle color labels for all subjects
    hc_shuffled = [permute_color_labels(amp, seed=seed + i) for i, amp in enumerate(hc_amplitudes_list)]
    cvd_shuffled = [permute_color_labels(amp, seed=seed + 100 + i) for i, amp in enumerate(cvd_amplitudes_list)]

    # Prepare data for BrainIAK SRM (expects list of (n_voxels, n_colors))
    try:
        # Create input dictionary with dummy run dimension for compatibility
        # apply_srm_alignment expects (n_runs, n_colors, n_voxels) but will average runs
        # So we add dummy run dimension: (8, n_voxels) → (1, 8, n_voxels)
        hc_dict = {f'hc_{i}': amp[np.newaxis, :, :] for i, amp in enumerate(hc_shuffled)}
        cvd_dict = {f'cvd_{i}': amp[np.newaxis, :, :] for i, amp in enumerate(cvd_shuffled)}
        all_dict = {**hc_dict, **cvd_dict}

        # Define training subjects (HC only)
        hc_keys = [f'hc_{i}' for i in range(len(hc_shuffled))]

        # Apply SRM using existing utilities
        # Need to use the proper SRM function from evaluate script
        from brainiak.funcalign.srm import SRM

        # Prepare SRM input (transpose to (n_voxels, n_colors))
        all_srm_input = [amp.T for amp in (hc_shuffled + cvd_shuffled)]  # List of (n_voxels, 8)

        # Train SRM on all subjects
        # Note: For rigorous null test, we fit on ALL shuffled subjects
        # This ensures each permutation has independent SRM space
        srm = SRM(n_iter=10, features=k)
        srm.fit(all_srm_input)

        # Transform all subjects
        all_aligned_srm = srm.transform(all_srm_input)  # List of (k, 8)

        # Split back into HC and CVD
        n_hc = len(hc_shuffled)
        hc_aligned = [arr.T for arr in all_aligned_srm[:n_hc]]  # List of (8, k)
        cvd_aligned = [arr.T for arr in all_aligned_srm[n_hc:]]  # List of (8, k)

        # Compute metrics
        metrics = compute_metrics_from_aligned_patterns(hc_aligned, cvd_aligned)

        return metrics

    except Exception as e:
        print(f"  WARNING: Permutation {seed} failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_rigorous_color_permutation_test(baseline_dir: Path, output_dir: Path,
                                        roi: str, n_permutations: int = 100):
    """
    Run rigorous color permutation test for a single ROI.

    CRITICAL: This retrains SRM for each permutation!

    Parameters
    ----------
    baseline_dir : Path
        Directory containing baseline amplitudes
    output_dir : Path
        Output directory
    roi : str
        ROI name
    n_permutations : int
        Number of permutations (default 100 for testing, use 1000 for final)
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_dir = output_dir / f"{roi}_{timestamp}"
    results_dir.mkdir(parents=True, exist_ok=True)

    k = SRM_K_VALUES[roi]

    print(f"\n{'='*80}")
    print(f"Rigorous Color Permutation Test - {roi} (k={k})")
    print(f"{'='*80}")
    print(f"Permutations: {n_permutations}")
    print(f"Method: Shuffle labels → Retrain SRM → Compute metrics")
    print(f"WARNING: This is computationally expensive!")
    print()

    # Load baseline amplitudes for all subjects
    print("Loading baseline amplitudes...")
    hc_amplitudes_list = []
    cvd_amplitudes_list = []

    for subject in HC_SUBJECTS:
        try:
            amp = load_baseline_amplitudes(baseline_dir, subject, roi)
            # Average across runs
            amp_mean = amp.mean(axis=0)  # (8, n_voxels)
            hc_amplitudes_list.append(amp_mean)
            print(f"  Loaded {subject}: {amp_mean.shape}")
        except Exception as e:
            print(f"  WARNING: Could not load {subject}: {e}")

    for subject in CVD_SUBJECTS:
        try:
            amp = load_baseline_amplitudes(baseline_dir, subject, roi)
            amp_mean = amp.mean(axis=0)  # (8, n_voxels)
            cvd_amplitudes_list.append(amp_mean)
            print(f"  Loaded {subject}: {amp_mean.shape}")
        except Exception as e:
            print(f"  WARNING: Could not load {subject}: {e}")

    if len(hc_amplitudes_list) < 6 or len(cvd_amplitudes_list) < 2:
        raise ValueError(f"Insufficient data: HC={len(hc_amplitudes_list)}, CVD={len(cvd_amplitudes_list)}")

    # Compute observed metrics (with true labels)
    print("\nComputing observed metrics (true labels)...")

    # Train SRM on original (non-shuffled) data
    from brainiak.funcalign.srm import SRM

    # Prepare SRM input (transpose to (n_voxels, n_colors))
    all_srm_input_obs = [amp.T for amp in (hc_amplitudes_list + cvd_amplitudes_list)]

    # Train SRM on all subjects (BrainIAK requires all subjects for transform)
    # Note: The shared space will be learned from all subjects, but this is for observed only
    srm_obs = SRM(n_iter=10, features=k)
    srm_obs.fit(all_srm_input_obs)

    # Transform all subjects
    all_aligned_srm_obs = srm_obs.transform(all_srm_input_obs)

    # Split back into HC and CVD
    n_hc = len(hc_amplitudes_list)
    hc_aligned_obs = [arr.T for arr in all_aligned_srm_obs[:n_hc]]
    cvd_aligned_obs = [arr.T for arr in all_aligned_srm_obs[n_hc:]]

    observed = compute_metrics_from_aligned_patterns(hc_aligned_obs, cvd_aligned_obs)

    print(f"  Observed disparity difference: {observed['disparity_difference']:.4f}")
    print(f"  Observed HC RDM correlation: {observed['hc_rdm_correlation_mean']:.3f}")
    print(f"  Observed CVD RDM correlation: {observed['cvd_rdm_correlation_mean']:.3f}")

    # Run permutation test
    print(f"\nRunning {n_permutations} permutations...")
    print("  (Each permutation retrains SRM - this will take a while!)")

    null_disparity_diff = []
    null_hc_rdm_corr = []
    null_cvd_rdm_corr = []

    for perm_i in range(n_permutations):
        if (perm_i + 1) % 10 == 0:
            print(f"  Permutation {perm_i + 1}/{n_permutations}")

        seed = 42 + perm_i * 1000
        metrics = run_single_permutation(hc_amplitudes_list, cvd_amplitudes_list,
                                        roi, k, seed)

        if metrics is not None:
            null_disparity_diff.append(metrics['disparity_difference'])
            null_hc_rdm_corr.append(metrics['hc_rdm_correlation_mean'])
            null_cvd_rdm_corr.append(metrics['cvd_rdm_correlation_mean'])

    null_disparity_diff = np.array(null_disparity_diff)
    null_hc_rdm_corr = np.array(null_hc_rdm_corr)
    null_cvd_rdm_corr = np.array(null_cvd_rdm_corr)

    # Compute p-values
    p_disparity = np.mean(null_disparity_diff >= observed['disparity_difference'])
    p_hc_rdm = np.mean(null_hc_rdm_corr >= observed['hc_rdm_correlation_mean'])
    p_cvd_rdm = np.mean(null_cvd_rdm_corr >= observed['cvd_rdm_correlation_mean'])

    # Store results
    results = {
        'roi': roi,
        'k': k,
        'n_permutations': n_permutations,
        'n_successful': len(null_disparity_diff),
        'observed': observed,
        'null_distributions': {
            'disparity_difference': null_disparity_diff.tolist(),
            'hc_rdm_correlation': null_hc_rdm_corr.tolist(),
            'cvd_rdm_correlation': null_cvd_rdm_corr.tolist()
        },
        'p_values': {
            'disparity_difference': float(p_disparity),
            'hc_rdm_correlation': float(p_hc_rdm),
            'cvd_rdm_correlation': float(p_cvd_rdm)
        },
        'null_means': {
            'disparity_difference': float(np.mean(null_disparity_diff)),
            'hc_rdm_correlation': float(np.mean(null_hc_rdm_corr)),
            'cvd_rdm_correlation': float(np.mean(null_cvd_rdm_corr))
        }
    }

    # Save results
    with open(results_dir / 'rigorous_permutation_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print(f"\n{'='*80}")
    print(f"RESULTS SUMMARY - {roi}")
    print(f"{'='*80}")
    print(f"Successful permutations: {len(null_disparity_diff)}/{n_permutations}")
    print(f"\nObserved vs Null:")
    print(f"  Disparity diff: {observed['disparity_difference']:.4f} vs {np.mean(null_disparity_diff):.4f} (p={p_disparity:.4f})")
    print(f"  HC RDM corr:    {observed['hc_rdm_correlation_mean']:.3f} vs {np.mean(null_hc_rdm_corr):.3f} (p={p_hc_rdm:.4f})")
    print(f"  CVD RDM corr:   {observed['cvd_rdm_correlation_mean']:.3f} vs {np.mean(null_cvd_rdm_corr):.3f} (p={p_cvd_rdm:.4f})")

    if p_hc_rdm < 0.05 and p_cvd_rdm < 0.05:
        print(f"\n✅ PASS: RDM patterns depend on true color labels")
    else:
        print(f"\n⚠️  WARNING: RDM patterns may not depend on color labels")

    print(f"\nResults saved to: {results_dir}")

    return results


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Rigorous color permutation test with SRM retraining')
    parser.add_argument('--roi', type=str, required=True, choices=ROIS,
                       help='ROI to analyze')
    parser.add_argument('--n_permutations', type=int, default=100,
                       help='Number of permutations (default: 100 for testing)')
    parser.add_argument('--output_dir', type=str, default=None,
                       help='Output directory')

    args = parser.parse_args()

    # Paths
    base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
    baseline_dir = base_dir / 'analysis' / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

    if args.output_dir is None:
        output_dir = base_dir / 'analysis' / 'phase2_SRM_across_between' / 'validation' / '1D_permutation' / 'results_rigorous'
    else:
        output_dir = Path(args.output_dir)

    # Run test
    results = run_rigorous_color_permutation_test(baseline_dir, output_dir,
                                                  args.roi, args.n_permutations)

    print("\n✅ Rigorous color permutation test completed!")
