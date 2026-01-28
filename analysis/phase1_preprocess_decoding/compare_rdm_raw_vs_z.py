#!/usr/bin/env python3
"""
Compare RDM Reliability: amplitudes_raw vs amplitudes_z

Purpose: Test if z-scoring is causing the low RDM reliability (0.001)
         while run correlation using raw amplitudes is high (0.80)

Key Question:
  - Run correlation (0.80) uses amplitudes_raw
  - RDM reliability (0.001) uses amplitudes_z
  - Is this inconsistency causing the problem?
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import spearmanr
from itertools import combinations
import sys

plt.rcParams['figure.dpi'] = 150


def compute_rdm(amplitudes):
    """
    Compute RDM from amplitudes (n_colors, n_voxels)
    """
    corr_matrix = np.corrcoef(amplitudes)
    rdm = 1 - corr_matrix
    return rdm


def remove_constant_voxels(amplitudes):
    """
    Remove voxels with zero variance in any run
    Returns: cleaned amplitudes, valid voxel mask
    """
    n_runs, n_colors, n_voxels = amplitudes.shape
    invalid_voxels = set()

    for run_idx in range(n_runs):
        pattern = amplitudes[run_idx]  # (n_colors, n_voxels)
        voxel_stds = np.std(pattern, axis=0)  # Std across colors
        constant_voxels = np.where(voxel_stds < 1e-10)[0]
        invalid_voxels.update(constant_voxels)

    valid_mask = np.ones(n_voxels, dtype=bool)
    if len(invalid_voxels) > 0:
        valid_mask[list(invalid_voxels)] = False

    cleaned_amplitudes = amplitudes[:, :, valid_mask]
    return cleaned_amplitudes, valid_mask


def compute_rdm_reliability(amplitudes, name=""):
    """
    Compute run-pair RDM correlation
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    print(f"\n  [{name}] Input shape: {amplitudes.shape}")
    print(f"  [{name}] Amplitude range: [{np.min(amplitudes):.2f}, {np.max(amplitudes):.2f}]")

    # Remove constant voxels
    cleaned_amplitudes, valid_mask = remove_constant_voxels(amplitudes)
    n_valid = cleaned_amplitudes.shape[2]

    print(f"  [{name}] Valid voxels: {n_valid}/{n_voxels}")

    if n_valid < 5:
        print(f"  [{name}] ⚠️  Too few valid voxels!")
        return None

    # Compute RDM for each run
    run_rdms = []
    for run_idx in range(n_runs):
        rdm = compute_rdm(cleaned_amplitudes[run_idx])
        run_rdms.append(rdm)

    # Pairwise correlations between runs
    pairwise_correlations = []

    for run_i, run_j in combinations(range(n_runs), 2):
        rdm_i = run_rdms[run_i]
        rdm_j = run_rdms[run_j]

        # Upper triangle
        triu_indices = np.triu_indices(n_colors, k=1)
        vec_i = rdm_i[triu_indices]
        vec_j = rdm_j[triu_indices]

        r, p = spearmanr(vec_i, vec_j)
        pairwise_correlations.append(r)

    return {
        'pairwise_correlations': pairwise_correlations,
        'mean_correlation': float(np.mean(pairwise_correlations)),
        'std_correlation': float(np.std(pairwise_correlations)),
        'median_correlation': float(np.median(pairwise_correlations)),
        'min_correlation': float(np.min(pairwise_correlations)),
        'max_correlation': float(np.max(pairwise_correlations)),
        'run_rdms': run_rdms,
        'n_valid_voxels': n_valid
    }


def compute_run_correlation(amplitudes, name=""):
    """
    Compute run-pair amplitude correlation (same as main pipeline)
    """
    n_runs = amplitudes.shape[0]

    run_correlations = []
    for run_i, run_j in combinations(range(n_runs), 2):
        # Flatten all color × voxel patterns
        pattern_i = amplitudes[run_i].flatten()
        pattern_j = amplitudes[run_j].flatten()
        r = np.corrcoef(pattern_i, pattern_j)[0, 1]
        run_correlations.append(r)

    print(f"  [{name}] Run-pair correlations: {[f'{r:.3f}' for r in run_correlations]}")
    print(f"  [{name}] Mean run correlation: {np.mean(run_correlations):.4f}")

    return run_correlations


def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_rdm_raw_vs_z.py <subject> <roi>")
        print("Example: python compare_rdm_raw_vs_z.py 01 V1")
        sys.exit(1)

    subject = sys.argv[1]
    roi = sys.argv[2]

    # Paths
    results_dir = Path("analysis/phase1_preprocess_decoding/method3_header_mi/results/factorial_experiment/nzNone_moNo")
    subject_dir = results_dir / f"sub-{subject}" / roi

    amp_raw_file = subject_dir / "amplitude.npy"
    amp_z_file = subject_dir / "amplitudes_z.npy"

    # Check files
    if not amp_raw_file.exists():
        print(f"ERROR: Raw amplitude file not found: {amp_raw_file}")
        sys.exit(1)

    if not amp_z_file.exists():
        print(f"ERROR: Z-scored amplitude file not found: {amp_z_file}")
        sys.exit(1)

    output_dir = Path("analysis/phase1_preprocess_decoding/rdm_raw_vs_z_comparison")
    output_dir.mkdir(exist_ok=True, parents=True)

    print("=" * 80)
    print(f"RDM Reliability Comparison: sub-{subject} {roi}")
    print("=" * 80)
    print("\nTesting hypothesis:")
    print("  - Run correlation (0.80) uses amplitudes_raw")
    print("  - RDM reliability (0.001) uses amplitudes_z")
    print("  - Is z-scoring causing the discrepancy?")

    # Load amplitudes
    print("\n[1/4] Loading amplitudes...")
    amplitudes_raw = np.load(amp_raw_file)  # (n_runs, n_colors, n_voxels)
    amplitudes_z = np.load(amp_z_file)

    print(f"  Raw shape: {amplitudes_raw.shape}")
    print(f"  Z-scored shape: {amplitudes_z.shape}")

    # Compute run correlation (for reference)
    print("\n[2/4] Computing run-pair amplitude correlations...")
    print("  (This is what the main pipeline reports as 'run correlation')")

    run_corr_raw = compute_run_correlation(amplitudes_raw, name="RAW")
    run_corr_z = compute_run_correlation(amplitudes_z, name="Z-SCORED")

    # Compute RDM reliability with RAW amplitudes
    print("\n[3/4] Computing RDM reliability with RAW amplitudes...")
    reliability_raw = compute_rdm_reliability(amplitudes_raw, name="RAW")

    # Compute RDM reliability with Z-SCORED amplitudes
    print("\n[4/4] Computing RDM reliability with Z-SCORED amplitudes...")
    reliability_z = compute_rdm_reliability(amplitudes_z, name="Z-SCORED")

    # Results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    print("\n1. Run-pair Amplitude Correlation (entire pattern):")
    print(f"   RAW:       {np.mean(run_corr_raw):.4f} ± {np.std(run_corr_raw):.4f}")
    print(f"   Z-SCORED:  {np.mean(run_corr_z):.4f} ± {np.std(run_corr_z):.4f}")

    print("\n2. RDM Reliability (color dissimilarity structure):")
    if reliability_raw:
        print(f"   RAW:       {reliability_raw['mean_correlation']:.4f} ± {reliability_raw['std_correlation']:.4f}")
        print(f"              Valid voxels: {reliability_raw['n_valid_voxels']}")
    else:
        print(f"   RAW:       Failed (too few valid voxels)")

    if reliability_z:
        print(f"   Z-SCORED:  {reliability_z['mean_correlation']:.4f} ± {reliability_z['std_correlation']:.4f}")
        print(f"              Valid voxels: {reliability_z['n_valid_voxels']}")
    else:
        print(f"   Z-SCORED:  Failed (too few valid voxels)")

    # Visualization
    print("\n[5/5] Creating comparison visualizations...")

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))

    # Row 1: RAW amplitudes
    if reliability_raw:
        # Run correlation (RAW)
        ax = axes[0, 0]
        ax.bar(range(len(run_corr_raw)), run_corr_raw, edgecolor='black', alpha=0.7)
        ax.set_xlabel('Run Pair', fontsize=12)
        ax.set_ylabel('Pearson r', fontsize=12)
        ax.set_title(f'Run Correlation (RAW)\nMean: {np.mean(run_corr_raw):.3f}',
                     fontsize=12, fontweight='bold')
        ax.set_ylim([0, 1])
        ax.grid(alpha=0.3, axis='y')

        # RDM reliability (RAW)
        ax = axes[0, 1]
        rdm_corr_raw = reliability_raw['pairwise_correlations']
        ax.bar(range(len(rdm_corr_raw)), rdm_corr_raw, edgecolor='black', alpha=0.7)
        ax.axhline(0, color='red', linestyle='--', linewidth=1)
        ax.set_xlabel('Run Pair', fontsize=12)
        ax.set_ylabel('Spearman r', fontsize=12)
        ax.set_title(f'RDM Reliability (RAW)\nMean: {reliability_raw["mean_correlation"]:.3f}',
                     fontsize=12, fontweight='bold')
        ax.set_ylim([-1, 1])
        ax.grid(alpha=0.3, axis='y')

        # RDM example (RAW, run 1)
        ax = axes[0, 2]
        rdm = reliability_raw['run_rdms'][0]
        im = ax.imshow(rdm, cmap='viridis', vmin=0, vmax=2)
        ax.set_title('RDM Example (RAW, Run 1)', fontsize=12, fontweight='bold')
        color_names = ['Red', 'Ora', 'Yel', 'Grn', 'Cya', 'Blu', 'Pur', 'Mag']
        ax.set_xticks(range(8))
        ax.set_yticks(range(8))
        ax.set_xticklabels(color_names, rotation=45, ha='right', fontsize=9)
        ax.set_yticklabels(color_names, fontsize=9)
        plt.colorbar(im, ax=ax, fraction=0.046)

    # Row 2: Z-SCORED amplitudes
    if reliability_z:
        # Run correlation (Z-SCORED)
        ax = axes[1, 0]
        ax.bar(range(len(run_corr_z)), run_corr_z, edgecolor='black', alpha=0.7, color='orange')
        ax.set_xlabel('Run Pair', fontsize=12)
        ax.set_ylabel('Pearson r', fontsize=12)
        ax.set_title(f'Run Correlation (Z-SCORED)\nMean: {np.mean(run_corr_z):.3f}',
                     fontsize=12, fontweight='bold')
        ax.set_ylim([0, 1])
        ax.grid(alpha=0.3, axis='y')

        # RDM reliability (Z-SCORED)
        ax = axes[1, 1]
        rdm_corr_z = reliability_z['pairwise_correlations']
        ax.bar(range(len(rdm_corr_z)), rdm_corr_z, edgecolor='black', alpha=0.7, color='orange')
        ax.axhline(0, color='red', linestyle='--', linewidth=1)
        ax.set_xlabel('Run Pair', fontsize=12)
        ax.set_ylabel('Spearman r', fontsize=12)
        ax.set_title(f'RDM Reliability (Z-SCORED)\nMean: {reliability_z["mean_correlation"]:.3f}',
                     fontsize=12, fontweight='bold')
        ax.set_ylim([-1, 1])
        ax.grid(alpha=0.3, axis='y')

        # RDM example (Z-SCORED, run 1)
        ax = axes[1, 2]
        rdm = reliability_z['run_rdms'][0]
        im = ax.imshow(rdm, cmap='viridis', vmin=0, vmax=2)
        ax.set_title('RDM Example (Z-SCORED, Run 1)', fontsize=12, fontweight='bold')
        color_names = ['Red', 'Ora', 'Yel', 'Grn', 'Cya', 'Blu', 'Pur', 'Mag']
        ax.set_xticks(range(8))
        ax.set_yticks(range(8))
        ax.set_xticklabels(color_names, rotation=45, ha='right', fontsize=9)
        ax.set_yticklabels(color_names, fontsize=9)
        plt.colorbar(im, ax=ax, fraction=0.046)

    plt.suptitle(f'RAW vs Z-SCORED Amplitude Comparison: sub-{subject} {roi}',
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()

    fig_path = output_dir / f"rdm_raw_vs_z_sub-{subject}_{roi}.png"
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"  ✓ Saved: {fig_path}")
    plt.close()

    # Interpretation
    print("\n" + "=" * 80)
    print("INTERPRETATION")
    print("=" * 80)

    if reliability_raw and reliability_z:
        rdm_raw_mean = reliability_raw['mean_correlation']
        rdm_z_mean = reliability_z['mean_correlation']

        print(f"\nRDM reliability difference: {abs(rdm_raw_mean - rdm_z_mean):.4f}")

        if abs(rdm_raw_mean - rdm_z_mean) > 0.1:
            if rdm_raw_mean > rdm_z_mean:
                print("\n🔍 FINDING: RAW amplitudes produce HIGHER RDM reliability!")
                print("   → Z-scoring may be removing signal or adding noise")
                print("   → Consider using RAW amplitudes for RDM analysis")
            else:
                print("\n🔍 FINDING: Z-SCORED amplitudes produce HIGHER RDM reliability!")
                print("   → Z-scoring helps by normalizing voxel scales")
        else:
            print("\n🔍 FINDING: RAW and Z-SCORED produce similar RDM reliability")
            print("   → The problem is NOT z-scoring")
            print("   → Low RDM reliability has a different cause")

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
