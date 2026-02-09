#!/usr/bin/env python3
"""
SRM Between-Subject Alignment (HC Reference vs CVD)

Learns a shared response space from HC subjects and projects CVD subjects
to measure representational disparity.

This addresses the voxel count heterogeneity problem:
- Different subjects have different voxel counts (V1: 129-429)
- SRM maps different dimensions to common low-dimensional space
- Enables HC-CVD comparison without anatomical correspondence

Usage:
    python evaluate_srm_between_subject.py --roi V1 --n-features 50 --output-dir results/

Expected Input (from Phase 1 Baseline):
    BASELINE_RESULTS_DIR/
    ├── sub-01/{ROI}/amplitudes_z.npy  # HC (z-scored)
    ├── sub-02/{ROI}/amplitudes_z.npy  # HC
    ...
    ├── sub-08/{ROI}/amplitudes_z.npy  # CVD
    └── sub-10/{ROI}/amplitudes_z.npy  # CVD

Output:
    results/srm_between_subject/{TIMESTAMP}/
    ├── {ROI}_srm_between_subject_results.json
    ├── {ROI}_hc_cvd_disparity_comparison.png
    └── {ROI}_rdm_similarity_matrix.png
"""

import sys
import os
import argparse
import json
import time
import socket
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
from scipy.stats import spearmanr, ttest_ind
from scipy.spatial.distance import squareform, pdist
from itertools import combinations

# Add utils to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / 'utils'))
sys.path.insert(0, str(SCRIPT_DIR.parent / 'utils'))  # For shared utils

try:
    from srm_alignment import apply_srm_alignment, BRAINIAK_AVAILABLE
    from rdm_visualization import plot_rdm_matrices
except ImportError as e:
    print(f"Error importing utilities: {e}")
    sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Auto-detect local vs server paths
if socket.gethostname().startswith('node'):
    # Server path
    BASELINE_RESULTS_DIR = Path("/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline")
else:
    # Local path
    BASELINE_RESULTS_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline")

# Subject groups
HC_SUBJECTS = [f'sub-{i:02d}' for i in range(1, 8)]  # sub-01 to sub-07
CVD_SUBJECTS = [f'sub-{i:02d}' for i in range(8, 11)]  # sub-08 to sub-10

# Exclusions (data quality issues)
EXCLUDE_SUBJECTS = ['sub-07']  # Poor tSNR

# ROI-specific k values for Beta-based SRM (k ≤ n_colors = 8)
# Following B&H(2013): color space typically 2D-6D
DEFAULT_K_VALUES = {
    'V1': 4,   # Mid-range: good balance between denoising and information
    'V2': 4,
    'V3': 3,   # Fewer voxels, use lower k
    'hV4': 4
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def load_subject_amplitudes(subject: str, roi: str) -> np.ndarray:
    """Load z-scored amplitudes for a subject-ROI pair (pre-Procrustes)."""
    amp_path = BASELINE_RESULTS_DIR / subject / roi / "amplitudes_z.npy"

    if not amp_path.exists():
        raise FileNotFoundError(f"Amplitudes not found: {amp_path}")

    amplitudes = np.load(amp_path)
    return amplitudes


def compute_rdm_from_amplitudes(amplitudes: np.ndarray) -> np.ndarray:
    """
    Compute RDM from amplitudes (averaged across runs).

    Args:
        amplitudes: (n_runs, n_colors, n_features)

    Returns:
        rdm: (n_colors, n_colors) dissimilarity matrix
    """
    # Average across runs
    mean_patterns = np.mean(amplitudes, axis=0)  # (n_colors, n_features)

    # Pearson dissimilarity
    rdm = 1 - np.corrcoef(mean_patterns)

    return rdm


def compute_procrustes_disparity(X: np.ndarray, Y: np.ndarray) -> float:
    """
    Compute Procrustes disparity between two pattern sets.

    Args:
        X, Y: (n_colors, n_features) pattern matrices

    Returns:
        disparity: Frobenius norm of residual
    """
    from scipy.linalg import orthogonal_procrustes

    # Center and scale
    X_centered = X - X.mean(axis=0)
    Y_centered = Y - Y.mean(axis=0)

    X_scaled = X_centered / np.linalg.norm(X_centered, 'fro')
    Y_scaled = Y_centered / np.linalg.norm(Y_centered, 'fro')

    # Find optimal rotation
    R, scale = orthogonal_procrustes(X_scaled, Y_scaled)

    # Compute disparity
    Y_aligned = X_scaled @ R
    disparity = np.linalg.norm(Y_aligned - Y_scaled, 'fro')

    return disparity


# ============================================================================
# MAIN EVALUATION
# ============================================================================

def evaluate_srm_between_subject(roi: str,
                                 n_features: int,
                                 output_dir: Path) -> Dict:
    """
    Evaluate SRM between-subject alignment for HC vs CVD.

    Args:
        roi: ROI name
        n_features: Number of SRM features (k)
        output_dir: Output directory

    Returns:
        results: Comprehensive evaluation results
    """
    print(f"\n{'='*80}")
    print(f"Between-Subject SRM Evaluation: {roi}")
    print(f"{'='*80}")
    print(f"SRM features: {n_features}")

    if not BRAINIAK_AVAILABLE:
        raise ImportError("BrainIAK required for SRM")

    output_dir.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # 1. LOAD DATA
    # ========================================================================

    print("\n[1/6] Loading data...")

    # Filter valid subjects
    hc_valid = [s for s in HC_SUBJECTS if s not in EXCLUDE_SUBJECTS]
    cvd_valid = CVD_SUBJECTS

    print(f"  HC subjects: {hc_valid} (n={len(hc_valid)})")
    print(f"  CVD subjects: {cvd_valid} (n={len(cvd_valid)})")

    # Load HC amplitudes
    hc_amplitudes = {}
    for subj in hc_valid:
        try:
            amp = load_subject_amplitudes(subj, roi)
            hc_amplitudes[subj] = amp
            print(f"    Loaded {subj}: {amp.shape}")
        except FileNotFoundError as e:
            print(f"    WARNING: {e}")

    # Load CVD amplitudes
    cvd_amplitudes = {}
    for subj in cvd_valid:
        try:
            amp = load_subject_amplitudes(subj, roi)
            cvd_amplitudes[subj] = amp
            print(f"    Loaded {subj}: {amp.shape}")
        except FileNotFoundError as e:
            print(f"    WARNING: {e}")

    if len(hc_amplitudes) < 2:
        raise ValueError(f"Insufficient HC subjects: {len(hc_amplitudes)} (need >=2)")

    if len(cvd_amplitudes) == 0:
        raise ValueError("No CVD subjects found")

    print(f"\n  Total: {len(hc_amplitudes)} HC + {len(cvd_amplitudes)} CVD")

    # ========================================================================
    # 2. LEARN HC SHARED SPACE
    # ========================================================================

    print("\n[2/6] Learning HC shared response space...")

    hc_srm_result = apply_srm_alignment(
        hc_amplitudes,
        n_features=n_features,
        n_iter=10
    )

    hc_aligned = hc_srm_result['aligned_amplitudes']
    hc_transformations = hc_srm_result['transformations']

    print(f"  HC shared space learned: {n_features} features")
    print(f"  Original voxel counts: {[amp.shape[2] for amp in hc_amplitudes.values()]}")

    # ========================================================================
    # 3. PROJECT CVD TO HC SPACE
    # ========================================================================

    print("\n[3/6] Projecting CVD subjects to HC space...")

    # Combine HC + CVD for joint SRM (alternative: project CVD to learned HC space)
    all_amplitudes = {**hc_amplitudes, **cvd_amplitudes}

    all_srm_result = apply_srm_alignment(
        all_amplitudes,
        n_features=n_features,
        n_iter=10
    )

    all_aligned = all_srm_result['aligned_amplitudes']

    print(f"  CVD subjects projected to {n_features}-D space")

    # ========================================================================
    # 4. COMPUTE DISPARITIES
    # ========================================================================

    print("\n[4/6] Computing Procrustes disparities...")

    # HC reference (mean of HC subjects in aligned space)
    hc_subjects_list = list(hc_aligned.keys())
    hc_reference = np.mean([np.mean(hc_aligned[s], axis=0) for s in hc_subjects_list], axis=0)  # (n_colors, n_features)

    print(f"  HC reference shape: {hc_reference.shape}")

    # Compute disparities
    hc_disparities = []
    cvd_disparities = []

    # HC-to-HC disparities
    for subj in hc_subjects_list:
        subj_pattern = np.mean(all_aligned[subj], axis=0)  # (n_colors, n_features)
        disparity = compute_procrustes_disparity(subj_pattern, hc_reference)
        hc_disparities.append(disparity)

    # CVD-to-HC disparities
    cvd_subjects_list = list(cvd_amplitudes.keys())
    for subj in cvd_subjects_list:
        subj_pattern = np.mean(all_aligned[subj], axis=0)
        disparity = compute_procrustes_disparity(subj_pattern, hc_reference)
        cvd_disparities.append(disparity)

    # CVD-to-CVD pairwise disparities (internal consistency)
    cvd_cvd_disparities = []
    for i, subj_i in enumerate(cvd_subjects_list):
        for j, subj_j in enumerate(cvd_subjects_list):
            if i < j:  # Unique pairs only
                pattern_i = np.mean(all_aligned[subj_i], axis=0)
                pattern_j = np.mean(all_aligned[subj_j], axis=0)
                disparity = compute_procrustes_disparity(pattern_i, pattern_j)
                cvd_cvd_disparities.append(disparity)

    hc_disparities = np.array(hc_disparities)
    cvd_disparities = np.array(cvd_disparities)
    cvd_cvd_disparities = np.array(cvd_cvd_disparities) if cvd_cvd_disparities else np.array([np.nan])

    print(f"\n  HC-to-HC disparities: {hc_disparities.mean():.2f} ± {hc_disparities.std():.2f} (n={len(hc_disparities)})")
    print(f"  CVD-to-HC disparities: {cvd_disparities.mean():.2f} ± {cvd_disparities.std():.2f} (n={len(cvd_disparities)})")
    print(f"  CVD-to-CVD disparities: {cvd_cvd_disparities.mean():.2f} ± {cvd_cvd_disparities.std():.2f} (n={len(cvd_cvd_disparities)})")

    # Statistical test (HC vs CVD)
    t_stat, p_value = ttest_ind(hc_disparities, cvd_disparities)
    print(f"  HC vs CVD t-test: t={t_stat:.3f}, p={p_value:.4f}")

    # Statistical test (CVD-CVD vs CVD-HC)
    t_stat_cvd, p_value_cvd = None, None
    if len(cvd_cvd_disparities) > 1 and not np.isnan(cvd_cvd_disparities).all():
        t_stat_cvd, p_value_cvd = ttest_ind(cvd_cvd_disparities, cvd_disparities)
        print(f"  CVD-CVD vs CVD-HC t-test: t={t_stat_cvd:.3f}, p={p_value_cvd:.4f}")

    # ========================================================================
    # 5. COMPUTE RDM SIMILARITIES
    # ========================================================================

    print("\n[5/6] Computing inter-subject RDM similarities...")

    # Compute RDMs for all subjects in aligned space
    rdms = {}
    for subj in all_aligned.keys():
        rdms[subj] = compute_rdm_from_amplitudes(all_aligned[subj])

    # Pairwise RDM correlations
    hc_hc_correlations = []
    cvd_cvd_correlations = []
    hc_cvd_correlations = []

    for subj_i, subj_j in combinations(all_aligned.keys(), 2):
        mask = np.triu(np.ones_like(rdms[subj_i], dtype=bool), k=1)
        vec_i = rdms[subj_i][mask]
        vec_j = rdms[subj_j][mask]

        r, _ = spearmanr(vec_i, vec_j)

        if subj_i in hc_amplitudes and subj_j in hc_amplitudes:
            hc_hc_correlations.append(r)
        elif subj_i in cvd_amplitudes and subj_j in cvd_amplitudes:
            cvd_cvd_correlations.append(r)
        else:
            hc_cvd_correlations.append(r)

    print(f"\n  HC-HC RDM correlation: {np.mean(hc_hc_correlations):.3f} ± {np.std(hc_hc_correlations):.3f} (n={len(hc_hc_correlations)})")
    print(f"  CVD-CVD RDM correlation: {np.mean(cvd_cvd_correlations):.3f} ± {np.std(cvd_cvd_correlations):.3f} (n={len(cvd_cvd_correlations)})")
    print(f"  HC-CVD RDM correlation: {np.mean(hc_cvd_correlations):.3f} ± {np.std(hc_cvd_correlations):.3f} (n={len(hc_cvd_correlations)})")

    # ========================================================================
    # 6. SAVE RESULTS
    # ========================================================================

    print("\n[6/6] Saving results...")

    results = {
        'roi': roi,
        'n_features': int(n_features),
        'timestamp': datetime.now().isoformat(),
        'subjects': {
            'hc': hc_subjects_list,
            'cvd': list(cvd_amplitudes.keys()),
            'excluded': EXCLUDE_SUBJECTS
        },
        'disparities': {
            'hc_to_hc_reference': {
                'mean': float(hc_disparities.mean()),
                'std': float(hc_disparities.std()),
                'values': hc_disparities.tolist()
            },
            'cvd_to_hc_reference': {
                'mean': float(cvd_disparities.mean()),
                'std': float(cvd_disparities.std()),
                'values': cvd_disparities.tolist()
            },
            'cvd_to_cvd_pairwise': {
                'mean': float(cvd_cvd_disparities.mean()) if len(cvd_cvd_disparities) > 0 and not np.isnan(cvd_cvd_disparities).all() else None,
                'std': float(cvd_cvd_disparities.std()) if len(cvd_cvd_disparities) > 0 and not np.isnan(cvd_cvd_disparities).all() else None,
                'values': cvd_cvd_disparities.tolist() if len(cvd_cvd_disparities) > 0 else [],
                'n_pairs': len(cvd_cvd_disparities) if len(cvd_cvd_disparities) > 0 else 0
            },
            'statistical_test_hc_vs_cvd': {
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'significant': bool(p_value < 0.05)
            },
            'statistical_test_cvd_cvd_vs_cvd_hc': {
                't_statistic': float(t_stat_cvd) if len(cvd_cvd_disparities) > 1 and not np.isnan(cvd_cvd_disparities).all() else None,
                'p_value': float(p_value_cvd) if len(cvd_cvd_disparities) > 1 and not np.isnan(cvd_cvd_disparities).all() else None,
                'significant': bool(p_value_cvd < 0.05) if len(cvd_cvd_disparities) > 1 and not np.isnan(cvd_cvd_disparities).all() else None
            }
        },
        'rdm_similarities': {
            'hc_hc': {
                'mean': float(np.mean(hc_hc_correlations)),
                'std': float(np.std(hc_hc_correlations)),
                'n_pairs': len(hc_hc_correlations)
            },
            'cvd_cvd': {
                'mean': float(np.mean(cvd_cvd_correlations)) if cvd_cvd_correlations else None,
                'std': float(np.std(cvd_cvd_correlations)) if cvd_cvd_correlations else None,
                'n_pairs': len(cvd_cvd_correlations)
            },
            'hc_cvd': {
                'mean': float(np.mean(hc_cvd_correlations)),
                'std': float(np.std(hc_cvd_correlations)),
                'n_pairs': len(hc_cvd_correlations)
            }
        },
        'interpretation': {
            'cvd_differs_from_hc': bool(p_value < 0.05 and cvd_disparities.mean() > hc_disparities.mean()),
            'effect_size_cohens_d': float((cvd_disparities.mean() - hc_disparities.mean()) /
                                         np.sqrt((hc_disparities.std()**2 + cvd_disparities.std()**2) / 2))
        }
    }

    # Save JSON
    output_file = output_dir / f"{roi}_srm_between_subject_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"  Saved results to {output_file}")

    # Save aligned amplitudes for visualization
    aligned_file = output_dir / f"{roi}_aligned_amplitudes.npy"
    np.save(aligned_file, all_aligned, allow_pickle=True)
    print(f"  Saved aligned amplitudes to {aligned_file}")

    # ========================================================================
    # VISUALIZATIONS
    # ========================================================================

    print("\n[Visualizations]")

    try:
        import matplotlib.pyplot as plt
        import seaborn as sns

        # 1. Disparity comparison (now with CVD-to-CVD)
        fig, ax = plt.subplots(figsize=(10, 6))

        # Include CVD-to-CVD if available
        if len(cvd_cvd_disparities) > 0 and not np.isnan(cvd_cvd_disparities).all():
            positions = [1, 2, 3]
            data_to_plot = [hc_disparities, cvd_disparities, cvd_cvd_disparities]
            labels = ['HC-to-HC\nReference', 'CVD-to-HC\nReference', 'CVD-to-CVD\nPairwise']
            colors = ['skyblue', 'salmon', 'orchid']
        else:
            positions = [1, 2]
            data_to_plot = [hc_disparities, cvd_disparities]
            labels = ['HC-to-HC\nReference', 'CVD-to-HC\nReference']
            colors = ['skyblue', 'salmon']

        bp = ax.boxplot(data_to_plot, positions=positions, widths=0.5,
                       patch_artist=True, showfliers=True)

        # Color boxes
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax.set_xticks(positions)
        ax.set_xticklabels(labels, fontsize=11)
        ax.set_ylabel('Procrustes Disparity', fontsize=12, fontweight='bold')
        # Fix title overlap by adding padding
        title_text = f'Between-Subject Disparity Comparison: {roi}\nSRM k={n_features}, p={p_value:.4f}'
        ax.set_title(title_text, fontsize=14, fontweight='bold', pad=20)
        ax.grid(alpha=0.3, axis='y', linestyle=':')

        # Add significance annotation
        if p_value < 0.05:
            y_max = max(hc_disparities.max(), cvd_disparities.max())
            y_annotation = y_max * 1.1
            ax.plot([1, 2], [y_annotation, y_annotation], 'k-', linewidth=2)
            ax.text(1.5, y_annotation * 1.05, f'p={p_value:.4f}*',
                   ha='center', fontsize=11, fontweight='bold')

        plot_file = output_dir / f"{roi}_hc_cvd_disparity_comparison.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  Saved disparity plot to {plot_file}")

        # 2. RDM similarity matrix
        subjects_ordered = hc_subjects_list + list(cvd_amplitudes.keys())
        n_subjects = len(subjects_ordered)

        similarity_matrix = np.zeros((n_subjects, n_subjects))

        for i, subj_i in enumerate(subjects_ordered):
            for j, subj_j in enumerate(subjects_ordered):
                if i == j:
                    similarity_matrix[i, j] = 1.0
                else:
                    mask = np.triu(np.ones_like(rdms[subj_i], dtype=bool), k=1)
                    r, _ = spearmanr(rdms[subj_i][mask], rdms[subj_j][mask])
                    similarity_matrix[i, j] = r

        fig, ax = plt.subplots(figsize=(10, 8))

        sns.heatmap(similarity_matrix, annot=True, fmt='.2f', cmap='RdYlGn',
                   center=0, vmin=-0.5, vmax=1.0,
                   xticklabels=subjects_ordered, yticklabels=subjects_ordered,
                   cbar_kws={'label': 'RDM Correlation (Spearman r)'},
                   ax=ax)

        # Add group separators
        n_hc = len(hc_subjects_list)
        ax.axhline(n_hc, color='black', linewidth=3)
        ax.axvline(n_hc, color='black', linewidth=3)

        ax.set_title(f'Inter-Subject RDM Similarity: {roi} (SRM k={n_features})',
                    fontsize=14, fontweight='bold')

        plot_file = output_dir / f"{roi}_rdm_similarity_matrix.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  Saved RDM similarity matrix to {plot_file}")

    except Exception as e:
        print(f"  WARNING: Could not create plots: {e}")

    return results


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='SRM Between-Subject Alignment')
    parser.add_argument('--roi', type=str, required=True, help='ROI name (e.g., V1)')
    parser.add_argument('--n-features', type=int, help='Number of SRM features (default: ROI-specific)')
    parser.add_argument('--output-dir', type=str, required=True, help='Output directory')

    args = parser.parse_args()

    # Use ROI-specific default k if not specified
    if args.n_features is None:
        args.n_features = DEFAULT_K_VALUES.get(args.roi, 50)
        print(f"Using default k={args.n_features} for {args.roi}")

    output_dir = Path(args.output_dir)

    print(f"\n{'='*80}")
    print("SRM Between-Subject Alignment (HC vs CVD)")
    print(f"{'='*80}")
    print(f"ROI: {args.roi}")
    print(f"SRM features: {args.n_features}")
    print(f"Output: {output_dir}")
    print(f"Baseline results: {BASELINE_RESULTS_DIR}")

    # Check baseline results
    if not BASELINE_RESULTS_DIR.exists():
        print(f"\nERROR: Baseline results not found: {BASELINE_RESULTS_DIR}")
        print("Please ensure Phase 1 baseline results are available.")
        sys.exit(1)

    start_time = time.time()

    try:
        results = evaluate_srm_between_subject(args.roi, args.n_features, output_dir)

        elapsed = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"Evaluation completed in {elapsed:.1f}s")
        print(f"{'='*80}")

        # Print summary
        print("\n=== SUMMARY ===")
        print(f"ROI: {results['roi']}, k={results['n_features']}")
        print(f"HC disparity: {results['disparities']['hc_to_hc_reference']['mean']:.2f} ± "
              f"{results['disparities']['hc_to_hc_reference']['std']:.2f}")
        print(f"CVD disparity: {results['disparities']['cvd_to_hc_reference']['mean']:.2f} ± "
              f"{results['disparities']['cvd_to_hc_reference']['std']:.2f}")
        print(f"Difference significant: {results['disparities']['statistical_test']['significant']}")
        print(f"CVD differs from HC: {results['interpretation']['cvd_differs_from_hc']}")

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
