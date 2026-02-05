"""
Noise Ceiling Computation for RDM Reliability Analysis

Implements two methods for estimating theoretical upper bounds on model performance:
1. Split-half reliability with Spearman-Brown correction
2. Leave-one-subject-out (LOSO) inter-subject reliability

References:
- Nili et al. (2014). A Toolbox for Representational Similarity Analysis. PLoS Computational Biology.
- Spearman (1910). Correlation calculated from faulty data. British Journal of Psychology.
"""

import numpy as np
from scipy.stats import spearmanr
from scipy.spatial.distance import squareform, pdist
from typing import Dict, Tuple, List
import matplotlib.pyplot as plt


def compute_rdm_from_amplitudes(amplitudes: np.ndarray, metric='correlation') -> np.ndarray:
    """
    Compute RDM from amplitude patterns.

    Args:
        amplitudes: (n_conditions, n_voxels) - Neural patterns
        metric: Distance metric ('correlation', 'euclidean', 'mahalanobis')

    Returns:
        rdm: (n_conditions, n_conditions) - Representational dissimilarity matrix
    """
    if metric == 'correlation':
        # 1 - Pearson correlation
        rdm = 1 - np.corrcoef(amplitudes)
    else:
        # Use scipy's pdist and squareform
        rdm_vector = pdist(amplitudes, metric=metric)
        rdm = squareform(rdm_vector)

    return rdm


def compute_split_half_reliability(amplitudes: np.ndarray,
                                   n_iterations: int = 1000,
                                   metric: str = 'correlation',
                                   random_seed: int = 42) -> Dict[str, float]:
    """
    Compute split-half reliability with Spearman-Brown correction.

    Randomly splits runs into two halves, computes RDMs for each half,
    correlates them, and applies Spearman-Brown correction to estimate
    full-data reliability.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) - Neural response patterns
        n_iterations: Number of random splits to average over
        metric: Distance metric for RDM computation
        random_seed: Random seed for reproducibility

    Returns:
        results: Dict with keys:
            - 'corrected': Spearman-Brown corrected reliability
            - 'raw': Mean uncorrected split-half correlation
            - 'ci_lower': 95% CI lower bound
            - 'ci_upper': 95% CI upper bound
            - 'all_correlations': List of all split-half correlations
    """
    np.random.seed(random_seed)
    n_runs, n_colors, n_voxels = amplitudes.shape

    if n_runs < 4:
        raise ValueError(f"Need at least 4 runs for split-half, got {n_runs}")

    correlations = []

    for _ in range(n_iterations):
        # Random split of runs
        run_indices = np.random.permutation(n_runs)
        split_point = n_runs // 2

        half1_runs = run_indices[:split_point]
        half2_runs = run_indices[split_point:2*split_point]  # Equal sizes

        # Average patterns within each half
        half1_patterns = amplitudes[half1_runs].mean(axis=0)  # (n_colors, n_voxels)
        half2_patterns = amplitudes[half2_runs].mean(axis=0)

        # Compute RDMs
        rdm1 = compute_rdm_from_amplitudes(half1_patterns, metric=metric)
        rdm2 = compute_rdm_from_amplitudes(half2_patterns, metric=metric)

        # Vectorize upper triangle (excluding diagonal)
        mask = np.triu(np.ones_like(rdm1, dtype=bool), k=1)
        rdm1_vec = rdm1[mask]
        rdm2_vec = rdm2[mask]

        # Spearman correlation
        r, _ = spearmanr(rdm1_vec, rdm2_vec)
        correlations.append(r)

    correlations = np.array(correlations)

    # Remove NaN/Inf values
    correlations = correlations[np.isfinite(correlations)]

    # Mean uncorrected reliability
    r_half = np.mean(correlations)

    # Spearman-Brown correction: r_full = 2*r_half / (1 + r_half)
    r_corrected = 2 * r_half / (1 + r_half) if r_half < 1 else 1.0

    # 95% Confidence intervals
    ci_lower = np.percentile(correlations, 2.5)
    ci_upper = np.percentile(correlations, 97.5)

    # Apply correction to CIs as well
    ci_lower_corrected = 2 * ci_lower / (1 + ci_lower) if ci_lower < 1 else 1.0
    ci_upper_corrected = 2 * ci_upper / (1 + ci_upper) if ci_upper < 1 else 1.0

    return {
        'corrected': r_corrected,
        'raw': r_half,
        'ci_lower': ci_lower_corrected,
        'ci_upper': ci_upper_corrected,
        'ci_lower_raw': ci_lower,
        'ci_upper_raw': ci_upper,
        'all_correlations': correlations.tolist()
    }


def compute_loso_noise_ceiling(amplitudes_dict: Dict[str, np.ndarray],
                               metric: str = 'correlation') -> Dict[str, float]:
    """
    Compute leave-one-subject-out (LOSO) noise ceiling.

    This provides a conservative estimate of inter-subject reliability by
    correlating each subject's RDM to the group-mean RDM (excluding that subject).

    Args:
        amplitudes_dict: {subject_id: (n_runs, n_colors, n_voxels)}
        metric: Distance metric for RDM computation

    Returns:
        results: Dict with keys:
            - 'lower_bound': Mean LOSO correlation (conservative)
            - 'upper_bound': Mean correlation including self (optimistic)
            - 'per_subject': Dict {subject: loso_score}
            - 'per_subject_upper': Dict {subject: upper_score}
    """
    subjects = list(amplitudes_dict.keys())
    n_subjects = len(subjects)

    if n_subjects < 3:
        raise ValueError(f"Need at least 3 subjects for LOSO, got {n_subjects}")

    # Compute RDM for each subject (averaged across runs)
    subject_rdms = {}
    for subj in subjects:
        avg_patterns = amplitudes_dict[subj].mean(axis=0)  # (n_colors, n_voxels)
        rdm = compute_rdm_from_amplitudes(avg_patterns, metric=metric)
        subject_rdms[subj] = rdm

    # LOSO correlations
    loso_scores = {}
    upper_scores = {}

    for held_out_subj in subjects:
        # Group mean RDM excluding held-out subject
        other_subjects = [s for s in subjects if s != held_out_subj]
        other_rdms = [subject_rdms[s] for s in other_subjects]
        group_mean_rdm = np.mean(other_rdms, axis=0)

        # Correlation: held-out RDM vs group mean
        mask = np.triu(np.ones_like(group_mean_rdm, dtype=bool), k=1)
        held_out_vec = subject_rdms[held_out_subj][mask]
        group_vec = group_mean_rdm[mask]

        r_loso, _ = spearmanr(held_out_vec, group_vec)
        loso_scores[held_out_subj] = r_loso

        # Upper bound: include self in group mean
        all_rdms = [subject_rdms[s] for s in subjects]
        full_group_mean = np.mean(all_rdms, axis=0)
        full_group_vec = full_group_mean[mask]
        r_upper, _ = spearmanr(held_out_vec, full_group_vec)
        upper_scores[held_out_subj] = r_upper

    # Average across subjects
    lower_bound = np.mean(list(loso_scores.values()))
    upper_bound = np.mean(list(upper_scores.values()))

    return {
        'lower_bound': lower_bound,
        'upper_bound': upper_bound,
        'per_subject': loso_scores,
        'per_subject_upper': upper_scores
    }


def visualize_noise_ceiling(results: Dict[str, float],
                            output_path: str,
                            figsize: Tuple[int, int] = (10, 6)) -> None:
    """
    Visualize model performance relative to noise ceiling.

    Creates bar plot showing:
    - Baseline model performance
    - Procrustes-aligned performance
    - Optional: SRM, whitening, etc.
    - Noise ceiling bounds (horizontal lines)

    Args:
        results: Dict with keys like:
            - 'baseline': float
            - 'procrustes': float
            - 'srm': float (optional)
            - 'whitening': float (optional)
            - 'noise_ceiling_lower': float
            - 'noise_ceiling_upper': float
        output_path: Path to save figure
        figsize: Figure size (width, height)
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Extract model results
    models = []
    scores = []
    colors_map = {
        'baseline': '#d62728',  # Red
        'procrustes': '#2ca02c',  # Green
        'srm': '#ff7f0e',  # Orange
        'whitening': '#1f77b4',  # Blue
        'srm+procrustes': '#9467bd',  # Purple
        'whitening+procrustes': '#8c564b'  # Brown
    }

    for key in ['baseline', 'procrustes', 'srm', 'whitening',
                'srm+procrustes', 'whitening+procrustes']:
        if key in results:
            models.append(key.replace('_', '+').title())
            scores.append(results[key])

    # Create bars
    x_pos = np.arange(len(models))
    bars = ax.bar(x_pos, scores,
                  color=[colors_map.get(m.lower().replace(' ', '_').replace('+', '_'), '#7f7f7f')
                         for m in [m.lower() for m in models]],
                  alpha=0.7, edgecolor='black', linewidth=1.5)

    # Add noise ceiling bounds
    if 'noise_ceiling_lower' in results:
        ax.axhline(results['noise_ceiling_lower'],
                  color='red', linestyle='--', linewidth=2,
                  label=f"Lower Bound (LOSO): {results['noise_ceiling_lower']:.3f}")

    if 'noise_ceiling_upper' in results:
        ax.axhline(results['noise_ceiling_upper'],
                  color='darkred', linestyle='--', linewidth=2,
                  label=f"Upper Bound (Split-half): {results['noise_ceiling_upper']:.3f}")

    # Annotate bars with values and % of ceiling
    for i, (bar, score) in enumerate(zip(bars, scores)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
               f'{score:.3f}',
               ha='center', va='bottom', fontsize=10, fontweight='bold')

        if 'noise_ceiling_upper' in results and results['noise_ceiling_upper'] > 0:
            pct = (score / results['noise_ceiling_upper']) * 100
            ax.text(bar.get_x() + bar.get_width()/2., height/2,
                   f'{pct:.1f}%',
                   ha='center', va='center', fontsize=9,
                   color='white', fontweight='bold')

    # Formatting
    ax.set_xlabel('Method', fontsize=12, fontweight='bold')
    ax.set_ylabel('RDM Reliability (Spearman r)', fontsize=12, fontweight='bold')
    ax.set_title('Model Performance vs Noise Ceiling', fontsize=14, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle=':')
    ax.set_ylim(0, min(1.0, max(scores + [results.get('noise_ceiling_upper', 0.8)]) * 1.15))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved noise ceiling visualization to {output_path}")


def visualize_split_half_distribution(correlations: List[float],
                                      corrected_value: float,
                                      output_path: str,
                                      figsize: Tuple[int, int] = (8, 5)) -> None:
    """
    Visualize distribution of split-half correlations.

    Args:
        correlations: List of split-half correlation values
        corrected_value: Spearman-Brown corrected reliability
        output_path: Path to save figure
        figsize: Figure size
    """
    fig, ax = plt.subplots(figsize=figsize)

    # Histogram
    ax.hist(correlations, bins=30, color='steelblue', alpha=0.7, edgecolor='black')

    # Mean line
    mean_val = np.mean(correlations)
    ax.axvline(mean_val, color='red', linestyle='--', linewidth=2,
              label=f'Mean (uncorrected): {mean_val:.3f}')

    # Corrected value (dashed line at different height)
    ax.axvline(corrected_value, color='darkred', linestyle=':', linewidth=2.5,
              label=f'Corrected (full data): {corrected_value:.3f}')

    # Formatting
    ax.set_xlabel('Split-Half Correlation (Spearman r)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax.set_title('Split-Half Reliability Distribution', fontsize=14, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(axis='y', alpha=0.3, linestyle=':')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Saved split-half distribution to {output_path}")


def compute_noise_ceiling_comprehensive(amplitudes: np.ndarray,
                                       amplitudes_dict: Dict[str, np.ndarray] = None,
                                       metric: str = 'correlation',
                                       n_iterations: int = 1000) -> Dict:
    """
    Comprehensive noise ceiling computation (both split-half and LOSO).

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) - Single subject data for split-half
        amplitudes_dict: {subject: (n_runs, n_colors, n_voxels)} - Multi-subject for LOSO
        metric: Distance metric
        n_iterations: Number of split-half iterations

    Returns:
        comprehensive_results: Dict with both split-half and LOSO results
    """
    results = {}

    # Split-half (within-subject)
    if amplitudes is not None:
        split_half = compute_split_half_reliability(amplitudes, n_iterations, metric)
        results['split_half'] = split_half
        results['noise_ceiling_upper'] = split_half['corrected']  # Optimistic

    # LOSO (inter-subject)
    if amplitudes_dict is not None and len(amplitudes_dict) >= 3:
        loso = compute_loso_noise_ceiling(amplitudes_dict, metric)
        results['loso'] = loso
        results['noise_ceiling_lower'] = loso['lower_bound']  # Conservative

        # If both available, use LOSO lower as conservative, split-half as optimistic
        if 'split_half' in results:
            results['noise_ceiling_range'] = (loso['lower_bound'], split_half['corrected'])

    return results


if __name__ == '__main__':
    # Test with synthetic data
    print("Testing noise ceiling computation with synthetic data...")

    # Synthetic data: 6 runs, 8 colors, 100 voxels
    np.random.seed(42)
    n_runs, n_colors, n_voxels = 6, 8, 100

    # Create ground truth patterns with some noise
    true_patterns = np.random.randn(n_colors, n_voxels)
    amplitudes = true_patterns[np.newaxis, :, :] + np.random.randn(n_runs, n_colors, n_voxels) * 0.3

    # Split-half reliability
    split_half_results = compute_split_half_reliability(amplitudes, n_iterations=100)
    print("\n=== Split-Half Reliability ===")
    print(f"Raw (uncorrected): {split_half_results['raw']:.3f}")
    print(f"Corrected (Spearman-Brown): {split_half_results['corrected']:.3f}")
    print(f"95% CI: [{split_half_results['ci_lower']:.3f}, {split_half_results['ci_upper']:.3f}]")

    # Multi-subject LOSO
    n_subjects = 5
    amplitudes_dict = {}
    for i in range(n_subjects):
        # Each subject has shared + unique patterns
        subject_patterns = true_patterns + np.random.randn(n_colors, n_voxels) * 0.5
        subject_amplitudes = subject_patterns[np.newaxis, :, :] + np.random.randn(n_runs, n_colors, n_voxels) * 0.3
        amplitudes_dict[f'sub-{i+1:02d}'] = subject_amplitudes

    loso_results = compute_loso_noise_ceiling(amplitudes_dict)
    print("\n=== LOSO Noise Ceiling ===")
    print(f"Lower bound (LOSO): {loso_results['lower_bound']:.3f}")
    print(f"Upper bound (including self): {loso_results['upper_bound']:.3f}")
    print(f"Per-subject LOSO scores: {loso_results['per_subject']}")

    # Comprehensive
    comprehensive = compute_noise_ceiling_comprehensive(amplitudes, amplitudes_dict, n_iterations=100)
    print("\n=== Comprehensive Results ===")
    print(f"Noise ceiling range: [{comprehensive['noise_ceiling_lower']:.3f}, {comprehensive['noise_ceiling_upper']:.3f}]")

    print("\nTest completed successfully!")
