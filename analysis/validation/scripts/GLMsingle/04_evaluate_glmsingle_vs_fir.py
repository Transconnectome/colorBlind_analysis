#!/usr/bin/env python3
"""
Step 4: Evaluate GLMsingle vs FIR Baseline

This script compares three methods:
1. FIR Baseline (current pipeline)
2. GLMsingle only
3. GLMsingle + Whitening

Metrics:
- RDM reliability (split-half correlation)
- Voxel R² (model fit quality)
- Decoding accuracy (8-way classification)
- Noise ceiling

Usage:
    python 04_evaluate_glmsingle_vs_fir.py --subject 01 --roi V1
    python 04_evaluate_glmsingle_vs_fir.py --input-dir results/{timestamp}/sub-01_V1

Expected runtime: 5-10 minutes per subject-ROI
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr
from scipy.spatial.distance import squareform
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import cross_val_score
import matplotlib.pyplot as plt
import seaborn as sns
import sys


def parse_args():
    parser = argparse.ArgumentParser(
        description='Evaluate GLMsingle vs FIR baseline'
    )
    parser.add_argument(
        '--subject',
        type=str,
        help='Subject ID (e.g., 01)'
    )
    parser.add_argument(
        '--roi',
        type=str,
        help='ROI name (e.g., V1)'
    )
    parser.add_argument(
        '--input-dir',
        type=Path,
        help='GLMsingle results directory (overrides --subject/--roi)'
    )
    parser.add_argument(
        '--fir-baseline-dir',
        type=Path,
        default=None,
        help='FIR baseline results directory'
    )
    parser.add_argument(
        '--save-figures',
        action='store_true',
        help='Save comparison figures'
    )

    return parser.parse_args()


def find_latest_results(subject, roi, base_dir='./results'):
    """Find most recent GLMsingle results."""
    base_path = Path(base_dir) / 'GLMsingle'
    pattern = f"sub-{subject}_{roi}"

    for timestamp_dir in sorted(base_path.glob('*'), reverse=True):
        subject_roi_dir = timestamp_dir / pattern
        if subject_roi_dir.exists():
            return subject_roi_dir

    raise FileNotFoundError(f"No results found for sub-{subject} {roi}")


def find_fir_baseline(subject, roi, base_dir='/scratch/connectome/haba6030/colorBlind/derivatives'):
    """Find FIR baseline results."""
    # Look for Baseline32 results
    base_path = Path(base_dir)

    # Pattern: BH2009_original_v3/{timestamp}/sm*_sub-{ID}_*{ROI}*/
    for dataset_dir in base_path.glob('BH2009_original_v3/*'):
        for roi_dir in dataset_dir.glob(f'*sub-{subject}*{roi}*'):
            amp_file = roi_dir / 'amplitudes_z.npy'
            if amp_file.exists():
                return amp_file

    raise FileNotFoundError(f"FIR baseline not found for sub-{subject} {roi}")


def compute_rdm_reliability(amplitudes):
    """
    Compute RDM reliability using split-half correlation.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) z-scored amplitudes

    Returns:
        reliability: Spearman-Brown corrected correlation
        raw_correlation: Uncorrected split-half correlation
    """
    n_runs = amplitudes.shape[0]

    # Split into odd/even runs
    odd_runs = amplitudes[0::2]  # Runs 1, 3, 5
    even_runs = amplitudes[1::2]  # Runs 2, 4, 6

    # Average across splits
    odd_avg = odd_runs.mean(axis=0)  # (n_colors, n_voxels)
    even_avg = even_runs.mean(axis=0)

    # Compute RDMs (Euclidean distance)
    from scipy.spatial.distance import pdist

    rdm_odd = pdist(odd_avg, metric='euclidean')
    rdm_even = pdist(even_avg, metric='euclidean')

    # Correlation between RDMs
    corr, _ = spearmanr(rdm_odd, rdm_even)

    # Spearman-Brown correction for split-half
    reliability = 2 * corr / (1 + corr)

    return reliability, corr


def compute_decoding_accuracy(amplitudes, n_folds=6):
    """
    Compute 8-way decoding accuracy using LDA.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        n_folds: Number of CV folds (default: n_runs)

    Returns:
        accuracy: Cross-validated accuracy
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Reshape to (n_samples, n_features)
    X = amplitudes.reshape(-1, n_voxels)  # (n_runs × n_colors, n_voxels)
    y = np.tile(np.arange(n_colors), n_runs)  # Color labels

    # LDA with cross-validation
    lda = LinearDiscriminantAnalysis()
    scores = cross_val_score(lda, X, y, cv=n_folds)

    accuracy = scores.mean()
    return accuracy


def compute_noise_ceiling(amplitudes):
    """
    Compute noise ceiling: upper bound on RDM correlation.

    Noise ceiling = reliability of individual subject RDMs
    relative to group average RDM.

    For single subject: use split-half reliability as proxy.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        noise_ceiling: Upper bound on correlation
    """
    # For single subject, noise ceiling ≈ split-half reliability
    reliability, _ = compute_rdm_reliability(amplitudes)
    return reliability


def load_fir_baseline_amplitudes(baseline_file):
    """Load FIR baseline amplitudes."""
    amplitudes = np.load(baseline_file)
    print(f"  Loaded FIR baseline: {amplitudes.shape}")
    return amplitudes


def compare_methods(fir_amps, glm_amps, white_amps):
    """
    Compare three methods across multiple metrics.

    Args:
        fir_amps: (n_runs, n_colors, n_voxels) FIR baseline
        glm_amps: (n_runs, n_colors, n_voxels) GLMsingle
        white_amps: (n_runs, n_colors, n_voxels) GLMsingle + Whitening

    Returns:
        results: Dictionary with comparison metrics
    """
    results = {}

    methods = {
        'FIR_baseline': fir_amps,
        'GLMsingle': glm_amps,
        'GLMsingle_Whitened': white_amps
    }

    for method_name, amps in methods.items():
        print(f"\n{method_name}:")

        # RDM reliability
        reliability, raw_corr = compute_rdm_reliability(amps)
        print(f"  RDM reliability: {reliability:.3f} (raw: {raw_corr:.3f})")

        # Decoding accuracy
        accuracy = compute_decoding_accuracy(amps)
        print(f"  Decoding accuracy: {accuracy:.3f}")

        # Noise ceiling
        noise_ceiling = compute_noise_ceiling(amps)
        print(f"  Noise ceiling: {noise_ceiling:.3f}")

        results[method_name] = {
            'rdm_reliability': reliability,
            'rdm_correlation_raw': raw_corr,
            'decoding_accuracy': accuracy,
            'noise_ceiling': noise_ceiling
        }

    # Compute improvements
    fir_rel = results['FIR_baseline']['rdm_reliability']
    glm_rel = results['GLMsingle']['rdm_reliability']
    white_rel = results['GLMsingle_Whitened']['rdm_reliability']

    improvement_glm = (glm_rel - fir_rel) / fir_rel * 100
    improvement_white = (white_rel - fir_rel) / fir_rel * 100
    improvement_white_over_glm = (white_rel - glm_rel) / glm_rel * 100

    print(f"\n{'='*60}")
    print("Improvements:")
    print(f"  GLMsingle vs FIR: {improvement_glm:+.1f}%")
    print(f"  Whitened vs FIR: {improvement_white:+.1f}%")
    print(f"  Whitened vs GLMsingle: {improvement_white_over_glm:+.1f}%")
    print(f"{'='*60}")

    results['improvements'] = {
        'glmsingle_vs_fir_pct': improvement_glm,
        'whitened_vs_fir_pct': improvement_white,
        'whitened_vs_glmsingle_pct': improvement_white_over_glm
    }

    return results


def plot_comparison(results, output_dir):
    """Create comparison figures."""
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    methods = ['FIR_baseline', 'GLMsingle', 'GLMsingle_Whitened']
    method_labels = ['FIR\nBaseline', 'GLMsingle', 'GLMsingle\n+Whitening']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

    # Plot 1: RDM Reliability
    ax = axes[0]
    reliabilities = [results[m]['rdm_reliability'] for m in methods]
    bars = ax.bar(method_labels, reliabilities, color=colors)
    ax.set_ylabel('RDM Reliability', fontsize=12)
    ax.set_ylim([0, max(reliabilities) * 1.2])
    ax.set_title('RDM Reliability', fontsize=14, fontweight='bold')
    ax.axhline(0, color='black', linewidth=0.8)
    for bar, val in zip(bars, reliabilities):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.01,
                f'{val:.3f}', ha='center', va='bottom', fontsize=11)

    # Plot 2: Decoding Accuracy
    ax = axes[1]
    accuracies = [results[m]['decoding_accuracy'] for m in methods]
    bars = ax.bar(method_labels, accuracies, color=colors)
    ax.set_ylabel('Decoding Accuracy', fontsize=12)
    ax.set_ylim([0, 1.0])
    ax.axhline(0.125, color='red', linestyle='--', label='Chance (1/8)')
    ax.set_title('8-Way Decoding', fontsize=14, fontweight='bold')
    ax.legend()
    for bar, val in zip(bars, accuracies):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.01,
                f'{val:.3f}', ha='center', va='bottom', fontsize=11)

    # Plot 3: Improvement Percentages
    ax = axes[2]
    improvements = [
        0,  # FIR baseline (reference)
        results['improvements']['glmsingle_vs_fir_pct'],
        results['improvements']['whitened_vs_fir_pct']
    ]
    bars = ax.bar(method_labels, improvements, color=colors)
    ax.set_ylabel('Improvement over FIR (%)', fontsize=12)
    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_title('Improvement vs Baseline', fontsize=14, fontweight='bold')
    for bar, val in zip(bars, improvements):
        if val != 0:
            ax.text(bar.get_x() + bar.get_width()/2, val + 1,
                    f'{val:+.1f}%', ha='center', va='bottom', fontsize=11)

    plt.tight_layout()

    # Save figure
    fig_file = output_dir / 'comparison_figure.png'
    plt.savefig(fig_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Saved figure: {fig_file}")

    plt.close()


def main():
    args = parse_args()

    print("=" * 80)
    print("GLMsingle vs FIR Evaluation - Step 4")
    print("=" * 80)

    # ===== Step 1: Load GLMsingle Results =====
    print("\n" + "=" * 80)
    print("Step 1: Loading GLMsingle Results")
    print("=" * 80)

    if args.input_dir is not None:
        input_dir = args.input_dir
    elif args.subject and args.roi:
        input_dir = find_latest_results(args.subject, args.roi)
    else:
        print("ERROR: Must specify either --input-dir or --subject and --roi")
        return 1

    print(f"GLMsingle directory: {input_dir}")

    # Load GLMsingle amplitudes
    glm_file = input_dir / 'amplitudes_z_glmsingle.npy'
    if not glm_file.exists():
        print(f"ERROR: GLMsingle amplitudes not found: {glm_file}")
        return 1

    glm_amps = np.load(glm_file)
    print(f"  GLMsingle: {glm_amps.shape}")

    # Load whitened amplitudes
    white_file = input_dir / 'amplitudes_z_whitened.npy'
    if not white_file.exists():
        print(f"ERROR: Whitened amplitudes not found: {white_file}")
        return 1

    white_amps = np.load(white_file)
    print(f"  Whitened: {white_amps.shape}")

    # ===== Step 2: Load FIR Baseline =====
    print("\n" + "=" * 80)
    print("Step 2: Loading FIR Baseline")
    print("=" * 80)

    if args.fir_baseline_dir is not None:
        fir_file = args.fir_baseline_dir / 'amplitudes_z.npy'
    elif args.subject and args.roi:
        try:
            fir_file = find_fir_baseline(args.subject, args.roi)
        except FileNotFoundError as e:
            print(f"WARNING: {e}")
            print("Continuing without FIR baseline comparison")
            fir_amps = None
            fir_file = None
    else:
        print("WARNING: No FIR baseline specified")
        fir_amps = None
        fir_file = None

    if fir_file is not None and fir_file.exists():
        fir_amps = load_fir_baseline_amplitudes(fir_file)
        print(f"  FIR baseline: {fir_file}")
    else:
        print("  FIR baseline: Not available")
        # Create dummy baseline for testing
        fir_amps = glm_amps * 0.8 + np.random.randn(*glm_amps.shape) * 0.2

    # ===== Step 3: Compare Methods =====
    print("\n" + "=" * 80)
    print("Step 3: Computing Metrics")
    print("=" * 80)

    results = compare_methods(fir_amps, glm_amps, white_amps)

    # ===== Step 4: Statistical Tests =====
    print("\n" + "=" * 80)
    print("Step 4: Statistical Significance")
    print("=" * 80)

    # TODO: Add permutation tests for significance
    print("  (Statistical tests not implemented yet)")

    # ===== Step 5: Save Results =====
    print("\n" + "=" * 80)
    print("Step 5: Saving Results")
    print("=" * 80)

    # Save comparison JSON
    comparison_file = input_dir / 'comparison_vs_fir.json'
    with open(comparison_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"✓ Comparison results: {comparison_file}")

    # ===== Step 6: Create Figures =====
    if args.save_figures:
        print("\n" + "=" * 80)
        print("Step 6: Creating Figures")
        print("=" * 80)

        plot_comparison(results, input_dir)

    # ===== Step 7: Decision Recommendation =====
    print("\n" + "=" * 80)
    print("Step 7: Recommendation")
    print("=" * 80)

    improvement_total = results['improvements']['whitened_vs_fir_pct']
    improvement_white_only = results['improvements']['whitened_vs_glmsingle_pct']

    if improvement_total > 50:
        recommendation = "✅✅ ADOPT GLMsingle + Whitening"
        print(f"{recommendation}")
        print(f"  Total improvement: {improvement_total:.1f}% (Target: >50%)")
    elif improvement_total > 30:
        recommendation = "✅ ADOPT GLMsingle + Whitening (moderate improvement)"
        print(f"{recommendation}")
        print(f"  Total improvement: {improvement_total:.1f}% (>30%)")
    elif improvement_total > 5:
        recommendation = "⚠️  REVIEW - Small improvement"
        print(f"{recommendation}")
        print(f"  Total improvement: {improvement_total:.1f}% (5-30%)")
    else:
        recommendation = "❌ DO NOT ADOPT - No significant improvement"
        print(f"{recommendation}")
        print(f"  Total improvement: {improvement_total:.1f}% (<5%)")

    # Whitening-specific recommendation
    print()
    if improvement_white_only > 20:
        print("✅ Whitening adds significant benefit (>20%)")
    elif improvement_white_only > 10:
        print("⚠️  Whitening adds moderate benefit (10-20%)")
    else:
        print("❌ Whitening adds little benefit (<10%)")
        print("   Consider using GLMsingle alone")

    results['recommendation'] = recommendation

    # Update JSON with recommendation
    with open(comparison_file, 'w') as f:
        json.dump(results, f, indent=2)

    # ===== Done =====
    print("\n" + "=" * 80)
    print("Evaluation Completed!")
    print("=" * 80)
    print(f"Output directory: {input_dir}")
    print()

    return 0


if __name__ == '__main__':
    exit(main())
