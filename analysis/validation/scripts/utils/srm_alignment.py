"""
Shared Response Model (SRM) for Functional Alignment

Implements SRM from BrainIAK for dimensionality reduction and inter-subject alignment.
SRM learns a shared low-dimensional space (k << v features) that captures common
representational structure across subjects while filtering subject-specific noise.

References:
- Chen et al. (2015). A Reduced-Dimension fMRI Shared Response Model. NIPS.
- Nastase et al. (2019). Keep it real: rethinking the primacy of experimental control in cognitive neuroscience. NeuroImage.

Key advantages over Procrustes:
1. Dimensionality reduction: k << v reduces noise
2. Shared response: Extracts common signal across subjects
3. Denoising: Low-rank approximation filters noise

When to use SRM vs Procrustes:
- SRM: Low SNR data, high dimensionality, need denoising
- Procrustes: High SNR, preserve all variance, full-rank needed
"""

import numpy as np
from typing import Dict, Tuple, List, Optional
from scipy.stats import spearmanr
from scipy.spatial.distance import squareform, pdist
import json

try:
    from brainiak.funcalign.srm import SRM
    BRAINIAK_AVAILABLE = True
except ImportError:
    BRAINIAK_AVAILABLE = False
    print("Warning: brainiak not available. SRM functionality disabled.")


def apply_srm_alignment(amplitudes_dict: Dict[str, np.ndarray],
                       n_features: int = 50,
                       n_iter: int = 10,
                       features_axis: int = 1) -> Dict:
    """
    Apply SRM to align subjects in shared response space.

    Args:
        amplitudes_dict: {subject: (n_runs, n_colors, n_voxels)}
        n_features: Number of shared features (k << v)
        n_iter: Number of SRM iterations
        features_axis: Axis for features in BrainIAK (default=1 for voxels)

    Returns:
        results: Dict with keys:
            - 'aligned_amplitudes': {subject: (n_runs, n_colors, n_features)}
            - 'srm_model': Trained SRM object
            - 'transformations': {subject: W_i} transformation matrices
            - 'shared_response': (n_features, n_timepoints) - Common patterns
    """
    if not BRAINIAK_AVAILABLE:
        raise ImportError("brainiak is required for SRM. Install: pip install brainiak")

    subjects = list(amplitudes_dict.keys())
    n_subjects = len(subjects)

    if n_subjects < 2:
        raise ValueError(f"SRM requires at least 2 subjects, got {n_subjects}")

    # Get dimensions (use first subject for runs/colors, but voxels can vary)
    first_subj_data = amplitudes_dict[subjects[0]]
    n_runs, n_colors = first_subj_data.shape[0], first_subj_data.shape[1]

    # Prepare data for BrainIAK SRM
    # SRM expects list of (n_features, n_samples) arrays
    #
    # IMPORTANT: Use Beta-based SRM approach (not time-series)
    # - Average across runs to get stable pattern estimates
    # - Input: (n_voxels, n_colors) per subject
    # - This allows k ≤ n_colors (typically k ≤ 8)
    # - Reduces noise and prevents overfitting with limited samples

    srm_input = []
    voxel_counts = []

    print(f"  Using Beta-based SRM: averaging {n_runs} runs per subject")

    for subj in subjects:
        subj_data = amplitudes_dict[subj]  # (n_runs, n_colors, n_voxels_i)
        n_voxels_i = subj_data.shape[2]
        voxel_counts.append(n_voxels_i)

        # Average across runs to get stable beta estimates
        # (n_runs, n_colors, n_voxels) -> (n_colors, n_voxels)
        subj_beta = np.mean(subj_data, axis=0)  # (n_colors, n_voxels)

        # Transpose to (n_voxels, n_colors) for BrainIAK
        subj_data_reshaped = subj_beta.T  # (n_voxels_i, n_colors)
        srm_input.append(subj_data_reshaped)

    print(f"  Subject voxel counts: min={min(voxel_counts)}, max={max(voxel_counts)}, mean={np.mean(voxel_counts):.1f}")
    print(f"  Input shape per subject: ({voxel_counts[0]}, {n_colors}) - {n_colors} samples (colors)")

    # Fit SRM
    print(f"Fitting SRM with {n_features} features on {n_subjects} subjects...")
    srm = SRM(n_iter=n_iter, features=n_features)
    srm.fit(srm_input)

    # Get shared response
    shared_response = srm.s_

    # Transform each subject's data
    aligned_amplitudes = {}
    transformations = {}

    for i, subj in enumerate(subjects):
        # Get transformation matrix W_i: (n_voxels, n_features)
        W_i = srm.w_[i]
        transformations[subj] = W_i

        # Transform original amplitudes (all runs)
        # (n_runs, n_colors, n_voxels) @ (n_voxels, n_features)
        # -> (n_runs, n_colors, n_features)
        aligned = amplitudes_dict[subj] @ W_i
        aligned_amplitudes[subj] = aligned

    print(f"SRM alignment completed. Reduced from {min(voxel_counts)}-{max(voxel_counts)} voxels to {n_features} features.")

    return {
        'aligned_amplitudes': aligned_amplitudes,
        'srm_model': srm,
        'transformations': transformations,
        'shared_response': shared_response,
        'n_features': n_features,
        'n_voxels_original': voxel_counts  # List of voxel counts per subject
    }


def srm_tune_features(amplitudes_dict: Dict[str, np.ndarray],
                     feature_range: List[int] = [10, 30, 50, 100, 200],
                     metric: str = 'correlation',
                     n_iter: int = 10) -> Dict:
    """
    Grid search for optimal number of SRM features.

    Evaluates RDM reliability and reconstruction quality for different k values.

    Args:
        amplitudes_dict: {subject: (n_runs, n_colors, n_voxels)}
        feature_range: List of k values to test
        metric: Distance metric for RDM
        n_iter: SRM iterations per k value

    Returns:
        results: Dict with keys:
            - 'results_by_k': {k: {'rdm_reliability': float, 'reconstruction_error': float}}
            - 'best_k': Optimal feature count
            - 'best_k_criterion': Criterion used for selection
    """
    if not BRAINIAK_AVAILABLE:
        raise ImportError("brainiak is required for SRM")

    subjects = list(amplitudes_dict.keys())
    first_subj_data = amplitudes_dict[subjects[0]]
    n_runs, n_colors = first_subj_data.shape[0], first_subj_data.shape[1]

    # Get min voxels across subjects for k validation
    min_voxels = min(data.shape[2] for data in amplitudes_dict.values())

    # Filter invalid k values (k must be <= minimum voxel count)
    valid_features = [k for k in feature_range if k <= min_voxels and k >= 2]
    if len(valid_features) == 0:
        raise ValueError(f"No valid feature counts. Max allowed: {min_voxels}")

    print(f"Testing SRM with k = {valid_features}")

    results_by_k = {}

    for k in valid_features:
        print(f"\n=== Testing k = {k} ===")

        # Apply SRM
        srm_results = apply_srm_alignment(amplitudes_dict, n_features=k, n_iter=n_iter)
        aligned_amplitudes = srm_results['aligned_amplitudes']

        # Evaluate: RDM reliability (inter-run correlation)
        rdm_reliabilities = []

        for subj in subjects:
            subj_data = aligned_amplitudes[subj]  # (n_runs, n_colors, n_features)

            if n_runs < 2:
                continue

            # Compute RDMs for each run
            run_rdms = []
            for run in range(n_runs):
                run_patterns = subj_data[run]  # (n_colors, n_features)
                if metric == 'correlation':
                    rdm = 1 - np.corrcoef(run_patterns)
                else:
                    rdm = squareform(pdist(run_patterns, metric=metric))
                run_rdms.append(rdm)

            # Pairwise run correlations
            for i in range(n_runs):
                for j in range(i+1, n_runs):
                    mask = np.triu(np.ones_like(run_rdms[i], dtype=bool), k=1)
                    vec_i = run_rdms[i][mask]
                    vec_j = run_rdms[j][mask]
                    r, _ = spearmanr(vec_i, vec_j)
                    if np.isfinite(r):
                        rdm_reliabilities.append(r)

        mean_rdm_reliability = np.mean(rdm_reliabilities) if rdm_reliabilities else 0.0

        # Compute reconstruction error (how much variance lost)
        reconstruction_errors = []
        for subj in subjects:
            original = amplitudes_dict[subj]  # (n_runs, n_colors, n_voxels)
            W_i = srm_results['transformations'][subj]  # (n_voxels, n_features)

            # Reconstruct: X @ W @ W^T
            reconstructed = (original @ W_i) @ W_i.T  # (n_runs, n_colors, n_voxels)

            # MSE
            mse = np.mean((original - reconstructed) ** 2)
            reconstruction_errors.append(mse)

        mean_reconstruction_error = np.mean(reconstruction_errors)

        results_by_k[k] = {
            'rdm_reliability': mean_rdm_reliability,
            'reconstruction_error': mean_reconstruction_error,
            'variance_explained': 1 - mean_reconstruction_error / np.var(list(amplitudes_dict.values()))
        }

        print(f"k={k}: RDM reliability = {mean_rdm_reliability:.3f}, "
              f"Reconstruction error = {mean_reconstruction_error:.4f}")

    # Select best k (maximize RDM reliability)
    best_k = max(results_by_k.keys(), key=lambda k: results_by_k[k]['rdm_reliability'])

    return {
        'results_by_k': results_by_k,
        'best_k': best_k,
        'best_k_criterion': 'rdm_reliability'
    }


def compare_procrustes_vs_srm(amplitudes_dict: Dict[str, np.ndarray],
                              procrustes_results: Dict,
                              k_srm: int = 50,
                              metric: str = 'correlation') -> Dict:
    """
    Head-to-head comparison of Procrustes (full-rank) vs SRM (low-rank).

    Args:
        amplitudes_dict: {subject: (n_runs, n_colors, n_voxels)} - Raw amplitudes
        procrustes_results: Pre-computed Procrustes results
        k_srm: Number of SRM features
        metric: Distance metric

    Returns:
        comparison: Dict with metrics for both methods
    """
    if not BRAINIAK_AVAILABLE:
        raise ImportError("brainiak is required for SRM")

    # Apply SRM
    srm_results = apply_srm_alignment(amplitudes_dict, n_features=k_srm)

    # Compute RDM reliability for both methods
    def compute_rdm_reliability(amp_dict):
        reliabilities = []
        for subj, data in amp_dict.items():
            n_runs = data.shape[0]
            if n_runs < 2:
                continue

            # RDMs per run
            run_rdms = []
            for run in range(n_runs):
                patterns = data[run]
                if metric == 'correlation':
                    rdm = 1 - np.corrcoef(patterns)
                else:
                    rdm = squareform(pdist(patterns, metric=metric))
                run_rdms.append(rdm)

            # Pairwise correlations
            for i in range(n_runs):
                for j in range(i+1, n_runs):
                    mask = np.triu(np.ones_like(run_rdms[i], dtype=bool), k=1)
                    r, _ = spearmanr(run_rdms[i][mask], run_rdms[j][mask])
                    if np.isfinite(r):
                        reliabilities.append(r)

        return np.mean(reliabilities) if reliabilities else 0.0

    # Procrustes reliability
    procrustes_reliability = compute_rdm_reliability(procrustes_results['aligned_amplitudes'])

    # SRM reliability
    srm_reliability = compute_rdm_reliability(srm_results['aligned_amplitudes'])

    # Dimensionality comparison (use mean voxel count)
    voxel_counts = [data.shape[2] for data in amplitudes_dict.values()]
    n_voxels_original = int(np.mean(voxel_counts))

    comparison = {
        'procrustes': {
            'rdm_reliability': procrustes_reliability,
            'n_features': n_voxels_original,
            'method': 'full_rank'
        },
        'srm': {
            'rdm_reliability': srm_reliability,
            'n_features': k_srm,
            'method': 'low_rank',
            'dimensionality_reduction': f"{n_voxels_original} -> {k_srm}"
        },
        'improvement': {
            'absolute': srm_reliability - procrustes_reliability,
            'relative_pct': ((srm_reliability - procrustes_reliability) / procrustes_reliability * 100)
                            if procrustes_reliability > 0 else 0
        },
        'winner': 'SRM' if srm_reliability > procrustes_reliability else 'Procrustes'
    }

    print("\n=== Procrustes vs SRM Comparison ===")
    print(f"Procrustes (k={n_voxels_original}): r = {procrustes_reliability:.3f}")
    print(f"SRM (k={k_srm}): r = {srm_reliability:.3f}")
    print(f"Improvement: {comparison['improvement']['absolute']:+.3f} ({comparison['improvement']['relative_pct']:+.1f}%)")
    print(f"Winner: {comparison['winner']}")

    return comparison


def visualize_srm_tuning(results_by_k: Dict,
                        output_path: str,
                        figsize: Tuple[int, int] = (10, 6)) -> None:
    """
    Visualize SRM performance vs feature count.

    Args:
        results_by_k: Dict from srm_tune_features()
        output_path: Path to save figure
        figsize: Figure size
    """
    import matplotlib.pyplot as plt

    k_values = sorted(results_by_k.keys())
    rdm_reliabilities = [results_by_k[k]['rdm_reliability'] for k in k_values]
    reconstruction_errors = [results_by_k[k]['reconstruction_error'] for k in k_values]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    # RDM Reliability vs k
    ax1.plot(k_values, rdm_reliabilities, marker='o', linewidth=2, markersize=8, color='steelblue')
    ax1.set_xlabel('Number of Features (k)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('RDM Reliability (Spearman r)', fontsize=12, fontweight='bold')
    ax1.set_title('SRM Performance vs Feature Count', fontsize=14, fontweight='bold')
    ax1.grid(alpha=0.3, linestyle=':')

    # Highlight best k
    best_k = k_values[np.argmax(rdm_reliabilities)]
    best_r = max(rdm_reliabilities)
    ax1.axvline(best_k, color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax1.text(best_k, best_r, f'  Best k={best_k}\n  r={best_r:.3f}',
            fontsize=10, ha='left', va='top', color='red', fontweight='bold')

    # Reconstruction Error vs k
    ax2.plot(k_values, reconstruction_errors, marker='s', linewidth=2, markersize=8, color='coral')
    ax2.set_xlabel('Number of Features (k)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Reconstruction Error (MSE)', fontsize=12, fontweight='bold')
    ax2.set_title('Signal Preservation vs Dimensionality', fontsize=14, fontweight='bold')
    ax2.grid(alpha=0.3, linestyle=':')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved SRM tuning visualization to {output_path}")


if __name__ == '__main__':
    if not BRAINIAK_AVAILABLE:
        print("Skipping tests: brainiak not installed")
        exit(0)

    # Test with synthetic data
    print("Testing SRM alignment with synthetic data...")

    np.random.seed(42)
    n_subjects = 5
    n_runs = 6
    n_colors = 8
    n_voxels = 100
    k_shared = 30  # True shared dimensionality

    # Generate shared + subject-specific patterns
    shared_patterns = np.random.randn(n_colors, k_shared)

    amplitudes_dict = {}
    for i in range(n_subjects):
        # Random transformation to voxel space
        W_true = np.random.randn(k_shared, n_voxels)

        # Subject patterns in voxel space
        subject_patterns = shared_patterns @ W_true

        # Add subject-specific noise
        subject_patterns += np.random.randn(n_colors, n_voxels) * 0.5

        # Add run-wise variation
        subject_amplitudes = subject_patterns[np.newaxis, :, :] + \
                           np.random.randn(n_runs, n_colors, n_voxels) * 0.2

        amplitudes_dict[f'sub-{i+1:02d}'] = subject_amplitudes

    print(f"\nGenerated synthetic data: {n_subjects} subjects, {n_runs} runs, {n_colors} colors, {n_voxels} voxels")
    print(f"True shared dimensionality: {k_shared}")

    # Test SRM with different k values
    feature_range = [10, 20, 30, 50, 80]
    tuning_results = srm_tune_features(amplitudes_dict, feature_range=feature_range, n_iter=5)

    print("\n=== SRM Tuning Results ===")
    for k, metrics in tuning_results['results_by_k'].items():
        print(f"k={k}: RDM reliability = {metrics['rdm_reliability']:.3f}, "
              f"Reconstruction error = {metrics['reconstruction_error']:.4f}")

    print(f"\nBest k: {tuning_results['best_k']} (criterion: {tuning_results['best_k_criterion']})")

    print("\nTest completed successfully!")
