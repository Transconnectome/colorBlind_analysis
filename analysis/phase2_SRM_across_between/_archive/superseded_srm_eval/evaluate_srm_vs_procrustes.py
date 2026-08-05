#!/usr/bin/env python3
"""
SRM vs Procrustes Evaluation (Within-Subject)

Compares SRM with Procrustes alignment using Beta-based SRM approach.
- Treats each run as a "subject" (6 runs → 6 "subjects")
- Uses run-averaged betas: (n_voxels, 8 colors) per run
- Tests k ≤ 8 (constrained by n_colors)
- Leave-one-run-out validation

This implements the Beta-based SRM approach recommended for limited samples.
For between-subject HC-CVD comparison, see evaluate_srm_between_subject.py.

Usage:
    python evaluate_srm_vs_procrustes.py --subject sub-01 --roi V1 --output-dir results/

Expected Input Structure (from Phase 1 Baseline):
    BASELINE_RESULTS_DIR/
    ├── sub-{ID}/
    │   └── {ROI}/
    │       ├── amplitudes_z.npy                # (n_runs, n_colors, n_voxels) - z-scored
    │       ├── amplitudes_procrustes.npy       # Procrustes baseline
    │       └── analysis_summary.json           # Metadata

Output Structure:
    results/srm_evaluation/{TIMESTAMP}/
    ├── sub-{ID}_{ROI}_srm_results.json
    └── sub-{ID}_{ROI}_srm_k_tuning.png
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
from scipy.stats import spearmanr
from scipy.spatial.distance import squareform, pdist
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import LeaveOneOut

# Add utils to path
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / 'utils'))
sys.path.insert(0, str(SCRIPT_DIR.parent / 'utils'))  # For shared utils

try:
    from srm_alignment import apply_srm_alignment, srm_tune_features, BRAINIAK_AVAILABLE
    from rdm_visualization import plot_rdm_matrices
except ImportError as e:
    print(f"Error importing utilities: {e}")
    print("Make sure utils/srm_alignment.py and ../utils/rdm_visualization.py exist")
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

# Feature ranges for Beta-based SRM/PCA
# With 8 color conditions, k must be ≤ 8
# Following B&H(2013) color space: typically 2D-6D
K_RANGES = {
    'V1': [2, 3, 4, 5, 6, 8],   # Beta-based: k ≤ n_colors (8)
    'V2': [2, 3, 4, 5, 6, 8],
    'V3': [2, 3, 4, 5, 6, 8],
    'hV4': [2, 3, 4, 5, 6, 8]
}

# ============================================================================
# DATA LOADING
# ============================================================================

def load_baseline_amplitudes(subject: str, roi: str, use_procrustes: bool = False) -> np.ndarray:
    """
    Load amplitudes from baseline results.

    Args:
        subject: Subject ID (e.g., 'sub-01')
        roi: ROI name (e.g., 'V1')
        use_procrustes: If True, load Procrustes-aligned amplitudes
                       If False, load z-scored amplitudes (pre-alignment)

    Returns:
        amplitudes: (n_runs, n_colors, n_voxels)
    """
    if use_procrustes:
        filename = "amplitudes_procrustes.npy"
    else:
        filename = "amplitudes_z.npy"

    amp_path = BASELINE_RESULTS_DIR / subject / roi / filename

    if not amp_path.exists():
        raise FileNotFoundError(f"Amplitudes not found: {amp_path}")

    amplitudes = np.load(amp_path)
    return amplitudes


# ============================================================================
# METRICS COMPUTATION
# ============================================================================

def compute_rdm_correlation_reliability(amplitudes: np.ndarray) -> Tuple[float, float]:
    """
    Compute RDM reliability via pairwise run correlations.

    Args:
        amplitudes: (n_runs, n_colors, n_features)

    Returns:
        (mean_correlation, std_correlation)
    """
    n_runs, n_colors, n_features = amplitudes.shape

    if n_runs < 2:
        return np.nan, np.nan

    # Compute RDM for each run
    run_rdms = []
    for run in range(n_runs):
        patterns = amplitudes[run]  # (n_colors, n_features)
        rdm = 1 - np.corrcoef(patterns)  # Pearson dissimilarity
        run_rdms.append(rdm)

    # Pairwise run correlations
    correlations = []
    for i in range(n_runs):
        for j in range(i+1, n_runs):
            # Upper triangle only
            mask = np.triu(np.ones((n_colors, n_colors), dtype=bool), k=1)
            vec_i = run_rdms[i][mask]
            vec_j = run_rdms[j][mask]

            r, _ = spearmanr(vec_i, vec_j)
            if np.isfinite(r):
                correlations.append(r)

    if len(correlations) == 0:
        return np.nan, np.nan

    return np.mean(correlations), np.std(correlations)


def compute_decoding_accuracy(amplitudes: np.ndarray) -> float:
    """
    Leave-one-run-out 8-class decoding accuracy.

    Args:
        amplitudes: (n_runs, n_colors, n_features)

    Returns:
        accuracy: Mean accuracy across folds
    """
    n_runs, n_colors, n_features = amplitudes.shape

    if n_runs < 2:
        return np.nan

    # Flatten to (n_runs * n_colors, n_features)
    X = amplitudes.reshape(-1, n_features)
    y = np.tile(np.arange(n_colors), n_runs)

    # Leave-one-run-out CV
    loo = LeaveOneOut()
    correct = 0
    total = 0

    run_indices = np.repeat(np.arange(n_runs), n_colors)

    for train_runs in range(n_runs):
        test_run = train_runs
        train_mask = run_indices != test_run
        test_mask = run_indices == test_run

        X_train, y_train = X[train_mask], y[train_mask]
        X_test, y_test = X[test_mask], y[test_mask]

        # Train LDA
        clf = LinearDiscriminantAnalysis()
        try:
            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
            correct += np.sum(y_pred == y_test)
            total += len(y_test)
        except:
            continue

    return correct / total if total > 0 else np.nan


def compute_reconstruction_quality(original: np.ndarray,
                                   W: np.ndarray) -> Dict[str, float]:
    """
    Compute reconstruction quality after low-rank projection.

    Args:
        original: (n_runs, n_colors, n_voxels)
        W: (n_voxels, n_features) transformation matrix

    Returns:
        metrics: Dict with reconstruction error, variance explained
    """
    # Reconstruct: X @ W @ W^T
    reconstructed = (original @ W) @ W.T

    # MSE
    mse = np.mean((original - reconstructed) ** 2)

    # Variance explained
    var_original = np.var(original)
    var_explained = 1 - (mse / var_original) if var_original > 0 else 0

    return {
        'reconstruction_mse': float(mse),
        'variance_explained': float(var_explained)
    }


# ============================================================================
# MAIN EVALUATION
# ============================================================================

def evaluate_srm_single_subject(subject: str,
                                roi: str,
                                output_dir: Path) -> Dict:
    """
    Evaluate SRM vs Procrustes for a single subject-ROI pair.

    Uses Beta-based SRM: treats each run as a "subject" with averaged patterns.
    This approach is appropriate for limited samples (8 colors).

    Args:
        subject: Subject ID (e.g., 'sub-01')
        roi: ROI name (e.g., 'V1')
        output_dir: Directory to save results

    Returns:
        results: Comprehensive evaluation results
    """
    print(f"\n{'='*80}")
    print(f"Evaluating {subject} {roi}")
    print(f"{'='*80}")

    if not BRAINIAK_AVAILABLE:
        raise ImportError("BrainIAK is required for SRM. Install: pip install brainiak")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # 1. LOAD DATA
    # ========================================================================

    print("\n[1/6] Loading data...")

    # Load PRE-PROCRUSTES data (z-scored) for fair SRM comparison
    amplitudes_raw = load_baseline_amplitudes(subject, roi, use_procrustes=False)
    n_runs, n_colors, n_voxels = amplitudes_raw.shape
    print(f"  Z-scored amplitudes shape: {amplitudes_raw.shape}")

    # Load PROCRUSTES baseline for comparison
    amplitudes_procrustes = load_baseline_amplitudes(subject, roi, use_procrustes=True)
    print(f"  Procrustes baseline shape: {amplitudes_procrustes.shape}")

    # Noise ceiling (compute on-the-fly from Procrustes data if not available)
    noise_ceiling = None
    try:
        # Try to compute from baseline metadata
        metadata_path = BASELINE_RESULTS_DIR / subject / roi / "analysis_summary.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                # Could extract noise ceiling from metadata if available
        print(f"  Noise ceiling: Not available (will compute from data if needed)")
    except Exception as e:
        print(f"  WARNING: Could not load metadata: {e}")

    # ========================================================================
    # 2. PROCRUSTES BASELINE METRICS
    # ========================================================================

    print("\n[2/6] Computing Procrustes baseline metrics...")

    procrustes_rdm_mean, procrustes_rdm_std = compute_rdm_correlation_reliability(amplitudes_procrustes)
    procrustes_accuracy = compute_decoding_accuracy(amplitudes_procrustes)

    print(f"  Procrustes RDM correlation: {procrustes_rdm_mean:.3f} ± {procrustes_rdm_std:.3f}")
    print(f"  Procrustes decoding accuracy: {procrustes_accuracy*100:.1f}%")

    # ========================================================================
    # 3. SRM FEATURE TUNING
    # ========================================================================

    print("\n[3/6] SRM feature tuning (Beta-based: runs as 'subjects')...")

    # Get ROI-specific k range
    k_range = K_RANGES.get(roi, [2, 3, 4, 5, 6, 8])

    # k must be ≤ n_colors (8)
    valid_k = [k for k in k_range if k <= n_colors]
    if len(valid_k) == 0:
        print(f"  WARNING: No valid k values. Using k=[2, 3, 4]")
        valid_k = [2, 3, 4]

    print(f"  Testing k values: {valid_k} (k ≤ {n_colors} colors)")
    print(f"  Using Beta-based SRM: {n_runs} runs as 'subjects', averaged patterns")

    # Prepare data: treat each run as a "subject"
    # Each run: (n_colors, n_voxels) averaged pattern
    run_dict = {f'run-{i+1}': amplitudes_raw[i:i+1] for i in range(n_runs)}

    results_by_k = {}

    for k in valid_k:
        print(f"\n  Testing k={k}...")

        try:
            # Apply SRM (Beta-based: runs as subjects)
            srm_result = apply_srm_alignment(
                run_dict,
                n_features=k,
                n_iter=10
            )

            # Stack aligned runs
            aligned_runs = np.stack([srm_result['aligned_amplitudes'][f'run-{i+1}'][0]
                                    for i in range(n_runs)], axis=0)

            # Average transformation matrices
            W_avg = np.mean([srm_result['transformations'][f'run-{i+1}']
                           for i in range(n_runs)], axis=0)

            # Compute metrics
            rdm_mean, rdm_std = compute_rdm_correlation_reliability(aligned_runs)
            accuracy = compute_decoding_accuracy(aligned_runs)

            # Reconstruction quality
            recon_metrics = compute_reconstruction_quality(amplitudes_raw, W_avg)

            results_by_k[k] = {
                'rdm_correlation_mean': float(rdm_mean),
                'rdm_correlation_std': float(rdm_std),
                'decoding_accuracy': float(accuracy),
                'reconstruction_mse': recon_metrics['reconstruction_mse'],
                'variance_explained': recon_metrics['variance_explained'],
                'n_features': k
            }

            print(f"    RDM correlation: {rdm_mean:.3f}")
            print(f"    Decoding accuracy: {accuracy*100:.1f}%")
            print(f"    Variance explained: {recon_metrics['variance_explained']*100:.1f}%")

        except Exception as e:
            print(f"    ERROR: {str(e)}")
            results_by_k[k] = {
                'rdm_correlation_mean': np.nan,
                'error': str(e)
            }

    # ========================================================================
    # 4. SELECT BEST K
    # ========================================================================

    print("\n[4/6] Selecting best k...")

    # Select k with highest RDM correlation
    valid_results = {k: v for k, v in results_by_k.items()
                    if np.isfinite(v.get('rdm_correlation_mean', np.nan))}

    if len(valid_results) == 0:
        print("  ERROR: No valid SRM results. Falling back to Procrustes.")
        best_k = None
        best_metrics = None
    else:
        best_k = max(valid_results.keys(),
                    key=lambda k: valid_results[k]['rdm_correlation_mean'])
        best_metrics = valid_results[best_k]

        print(f"  Best k: {best_k}")
        print(f"  Best RDM correlation: {best_metrics['rdm_correlation_mean']:.3f}")

    # ========================================================================
    # 5. COMPUTE IMPROVEMENTS
    # ========================================================================

    print("\n[5/6] Computing improvements over Procrustes...")

    if best_k is not None:
        rdm_improvement = best_metrics['rdm_correlation_mean'] - procrustes_rdm_mean
        rdm_improvement_pct = (rdm_improvement / procrustes_rdm_mean * 100) if procrustes_rdm_mean > 0 else 0

        accuracy_improvement = best_metrics['decoding_accuracy'] - procrustes_accuracy
        accuracy_improvement_pct = (accuracy_improvement / procrustes_accuracy * 100) if procrustes_accuracy > 0 else 0

        print(f"  RDM correlation improvement: {rdm_improvement:+.3f} ({rdm_improvement_pct:+.1f}%)")
        print(f"  Decoding accuracy improvement: {accuracy_improvement:+.3f} ({accuracy_improvement_pct:+.1f}%)")

        # Ceiling utilization
        if noise_ceiling:
            procrustes_ceiling_pct = (procrustes_rdm_mean / noise_ceiling * 100) if noise_ceiling > 0 else 0
            srm_ceiling_pct = (best_metrics['rdm_correlation_mean'] / noise_ceiling * 100) if noise_ceiling > 0 else 0

            print(f"  Procrustes ceiling utilization: {procrustes_ceiling_pct:.1f}%")
            print(f"  SRM ceiling utilization: {srm_ceiling_pct:.1f}%")
        else:
            procrustes_ceiling_pct = None
            srm_ceiling_pct = None

        winner = 'SRM' if rdm_improvement > 0.02 else 'Procrustes'  # 2% threshold
        print(f"  Winner: {winner}")
    else:
        rdm_improvement = None
        rdm_improvement_pct = None
        accuracy_improvement = None
        accuracy_improvement_pct = None
        procrustes_ceiling_pct = None
        srm_ceiling_pct = None
        winner = 'Procrustes'

    # ========================================================================
    # 6. SAVE RESULTS
    # ========================================================================

    print("\n[6/6] Saving results...")

    results = {
        'subject': subject,
        'roi': roi,
        'timestamp': datetime.now().isoformat(),
        'data_info': {
            'n_runs': int(n_runs),
            'n_colors': int(n_colors),
            'n_voxels': int(n_voxels),
            'noise_ceiling': float(noise_ceiling) if noise_ceiling else None
        },
        'procrustes_baseline': {
            'rdm_correlation_mean': float(procrustes_rdm_mean),
            'rdm_correlation_std': float(procrustes_rdm_std),
            'decoding_accuracy': float(procrustes_accuracy),
            'ceiling_utilization_pct': float(procrustes_ceiling_pct) if procrustes_ceiling_pct else None,
            'n_features': int(n_voxels)
        },
        'srm_tuning': {
            'k_range_tested': valid_k,
            'results_by_k': {str(k): v for k, v in results_by_k.items()},
            'best_k': int(best_k) if best_k else None,
            'best_metrics': best_metrics
        },
        'comparison': {
            'rdm_improvement_absolute': float(rdm_improvement) if rdm_improvement else None,
            'rdm_improvement_pct': float(rdm_improvement_pct) if rdm_improvement_pct else None,
            'accuracy_improvement_absolute': float(accuracy_improvement) if accuracy_improvement else None,
            'accuracy_improvement_pct': float(accuracy_improvement_pct) if accuracy_improvement_pct else None,
            'srm_ceiling_utilization_pct': float(srm_ceiling_pct) if srm_ceiling_pct else None,
            'winner': winner
        }
    }

    # Save JSON
    output_file = output_dir / f"{subject}_{roi}_srm_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"  Saved results to {output_file}")

    # Visualize feature tuning curve
    try:
        import matplotlib.pyplot as plt

        k_values = sorted(valid_results.keys())
        rdm_values = [valid_results[k]['rdm_correlation_mean'] for k in k_values]

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.plot(k_values, rdm_values, marker='o', linewidth=2, markersize=8, color='steelblue')

        # Procrustes baseline
        ax.axhline(procrustes_rdm_mean, color='red', linestyle='--', linewidth=2,
                  label=f'Procrustes (k={n_voxels})', alpha=0.7)

        # Best k
        if best_k:
            ax.axvline(best_k, color='green', linestyle=':', linewidth=2, alpha=0.5)
            ax.scatter([best_k], [best_metrics['rdm_correlation_mean']],
                      s=200, color='green', marker='*', zorder=10,
                      label=f'Best k={best_k}')

        ax.set_xlabel('Number of Features (k)', fontsize=12, fontweight='bold')
        ax.set_ylabel('RDM Correlation (Spearman r)', fontsize=12, fontweight='bold')
        ax.set_title(f'SRM Feature Tuning (Beta-based): {subject} {roi}', fontsize=14, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(alpha=0.3, linestyle=':')

        plot_file = output_dir / f"{subject}_{roi}_srm_k_tuning.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"  Saved tuning plot to {plot_file}")
    except Exception as e:
        print(f"  WARNING: Could not create plot: {e}")

    return results


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Evaluate SRM vs Procrustes (within-subject, Beta-based)')
    parser.add_argument('--subject', type=str, required=True, help='Subject ID (e.g., sub-01)')
    parser.add_argument('--roi', type=str, required=True, help='ROI name (e.g., V1)')
    parser.add_argument('--output-dir', type=str, required=True, help='Output directory')

    args = parser.parse_args()

    output_dir = Path(args.output_dir)

    print(f"\n{'='*80}")
    print("SRM vs Procrustes Evaluation (Within-Subject, Beta-based)")
    print(f"{'='*80}")
    print(f"Subject: {args.subject}")
    print(f"ROI: {args.roi}")
    print(f"Output: {output_dir}")
    print(f"Baseline results: {BASELINE_RESULTS_DIR}")

    # Check if baseline results exist
    if not BASELINE_RESULTS_DIR.exists():
        print(f"\nERROR: Baseline results directory not found: {BASELINE_RESULTS_DIR}")
        print("Please ensure Phase 1 baseline results are available.")
        sys.exit(1)

    start_time = time.time()

    try:
        results = evaluate_srm_single_subject(args.subject, args.roi, output_dir)

        elapsed = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"Evaluation completed in {elapsed:.1f}s")
        print(f"{'='*80}")

        # Print summary
        print("\n=== SUMMARY ===")
        print(f"Subject: {results['subject']} {results['roi']}")
        print(f"Procrustes: r={results['procrustes_baseline']['rdm_correlation_mean']:.3f}, "
              f"acc={results['procrustes_baseline']['decoding_accuracy']*100:.1f}%")

        if results['srm_tuning']['best_k']:
            best = results['srm_tuning']['best_metrics']
            print(f"SRM (k={results['srm_tuning']['best_k']}): r={best['rdm_correlation_mean']:.3f}, "
                  f"acc={best['decoding_accuracy']*100:.1f}%")
            print(f"Improvement: {results['comparison']['rdm_improvement_pct']:+.1f}% RDM, "
                  f"{results['comparison']['accuracy_improvement_pct']:+.1f}% accuracy")
            print(f"Winner: {results['comparison']['winner']}")

    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
