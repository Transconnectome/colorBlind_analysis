#!/usr/bin/env python3
"""
Compute RDM reliability from no-drift amplitudes

Purpose: Check if high run correlation (0.80) translates to high RDM reliability

Input:
- No-drift amplitudes: nzNone_moNo/sub-{ID}/{ROI}/amplitude.npy
  - Shape: (6, 8, n_voxels) - raw amplitudes (not z-scored)

Output:
- RDM reliability metrics
- RDM matrices visualization
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.stats import spearmanr
from itertools import combinations
import json

plt.rcParams['figure.dpi'] = 150


def compute_rdm(amplitudes):
    """
    Compute RDM from amplitudes (n_colors, n_voxels)
    """
    corr_matrix = np.corrcoef(amplitudes)
    rdm = 1 - corr_matrix
    return rdm


def compute_rdm_reliability(amplitudes_raw):
    """
    Compute run-pair RDM correlation

    Args:
        amplitudes_raw: (n_runs, n_colors, n_voxels)

    Returns:
        dict with reliability metrics
    """
    n_runs, n_colors, n_voxels = amplitudes_raw.shape

    print(f"  Input shape: {amplitudes_raw.shape}")
    print(f"  Amplitude range: [{np.min(amplitudes_raw):.2f}, {np.max(amplitudes_raw):.2f}]")

    # Z-score per run per voxel (to make comparable across voxels)
    amplitudes_z = np.zeros_like(amplitudes_raw)

    for run_idx in range(n_runs):
        for voxel_idx in range(n_voxels):
            voxel_amps = amplitudes_raw[run_idx, :, voxel_idx]  # (n_colors,)

            # Z-score if variance exists
            if np.std(voxel_amps) > 1e-10:
                amplitudes_z[run_idx, :, voxel_idx] = (voxel_amps - np.mean(voxel_amps)) / np.std(voxel_amps)
            else:
                amplitudes_z[run_idx, :, voxel_idx] = 0

    print(f"  After z-scoring: [{np.min(amplitudes_z):.2f}, {np.max(amplitudes_z):.2f}]")

    # Remove constant voxels (zero std across colors in any run)
    valid_voxels = []
    for voxel_idx in range(n_voxels):
        is_valid = True
        for run_idx in range(n_runs):
            if np.std(amplitudes_z[run_idx, :, voxel_idx]) < 1e-10:
                is_valid = False
                break
        if is_valid:
            valid_voxels.append(voxel_idx)

    n_valid = len(valid_voxels)
    print(f"  Valid voxels: {n_valid}/{n_voxels}")

    if n_valid < 5:
        raise ValueError(f"Too few valid voxels: {n_valid}")

    # Use only valid voxels
    amplitudes_z = amplitudes_z[:, :, valid_voxels]

    # Compute RDM for each run
    run_rdms = []
    for run_idx in range(n_runs):
        rdm = compute_rdm(amplitudes_z[run_idx])
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


def main():
    import sys

    if len(sys.argv) < 3:
        print("Usage: python compute_rdm_nodrift.py <subject> <roi>")
        print("Example: python compute_rdm_nodrift.py 01 V1")
        sys.exit(1)

    subject = f"sub-{sys.argv[1]}"
    roi = sys.argv[2]

    # Path
    results_dir = Path("analysis/phase1_preprocess_decoding/method3_header_mi/results/factorial_experiment/nzNone_moNo")
    amp_file = results_dir / subject / roi / "amplitude.npy"

    if not amp_file.exists():
        print(f"ERROR: Amplitude file not found: {amp_file}")
        sys.exit(1)

    output_dir = Path("analysis/phase1_preprocess_decoding/rdm_nodrift")
    output_dir.mkdir(exist_ok=True, parents=True)

    print("=" * 80)
    print(f"RDM Reliability: {subject} {roi} (No-Drift)")
    print("=" * 80)

    # Load amplitudes
    print(f"\nLoading: {amp_file}")
    amplitudes_raw = np.load(amp_file)  # (n_runs, n_colors, n_voxels)

    # Compute RDM reliability
    print("\nComputing RDM reliability...")
    reliability = compute_rdm_reliability(amplitudes_raw)

    # Results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Mean RDM correlation:   {reliability['mean_correlation']:.4f}")
    print(f"Std:                    {reliability['std_correlation']:.4f}")
    print(f"Median:                 {reliability['median_correlation']:.4f}")
    print(f"Range:                  [{reliability['min_correlation']:.4f}, {reliability['max_correlation']:.4f}]")
    print(f"Valid voxels:           {reliability['n_valid_voxels']}")

    if reliability['mean_correlation'] > 0.6:
        print("\n✅ EXCELLENT: High RDM reliability (r > 0.6)")
    elif reliability['mean_correlation'] > 0.4:
        print("\n⚠️  ACCEPTABLE: Moderate RDM reliability (r > 0.4)")
    else:
        print("\n❌ POOR: Low RDM reliability (r < 0.4)")

    # Visualization
    print("\nGenerating visualizations...")

    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    color_names = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
    run_rdms = reliability['run_rdms']

    for run_idx in range(6):
        ax = axes[run_idx]
        rdm = run_rdms[run_idx]

        im = ax.imshow(rdm, cmap='viridis', vmin=0, vmax=2)
        ax.set_title(f'Run {run_idx+1}', fontsize=12, fontweight='bold')
        ax.set_xticks(range(8))
        ax.set_yticks(range(8))
        ax.set_xticklabels(color_names, rotation=45, ha='right', fontsize=9)
        ax.set_yticklabels(color_names, fontsize=9)

        plt.colorbar(im, ax=ax, fraction=0.046)

    plt.suptitle(f'RDM Matrices per Run: {subject}, {roi} (No-Drift)\n'
                 f'Mean Reliability: {reliability["mean_correlation"]:.3f}',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()

    fig_path = output_dir / f"rdm_matrices_{subject}_{roi}.png"
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {fig_path}")
    plt.close()

    # Pairwise correlation heatmap
    fig, ax = plt.subplots(figsize=(8, 6))

    n_runs = 6
    corr_matrix = np.zeros((n_runs, n_runs))

    pair_idx = 0
    for run_i, run_j in combinations(range(n_runs), 2):
        r = reliability['pairwise_correlations'][pair_idx]
        corr_matrix[run_i, run_j] = r
        corr_matrix[run_j, run_i] = r
        pair_idx += 1

    np.fill_diagonal(corr_matrix, 1.0)

    im = ax.imshow(corr_matrix, cmap='RdYlGn', vmin=0, vmax=1)
    ax.set_xticks(range(n_runs))
    ax.set_yticks(range(n_runs))
    ax.set_xticklabels([f'Run {i+1}' for i in range(n_runs)])
    ax.set_yticklabels([f'Run {i+1}' for i in range(n_runs)])

    # Annotate values
    for i in range(n_runs):
        for j in range(n_runs):
            if i != j:
                text = ax.text(j, i, f'{corr_matrix[i, j]:.2f}',
                             ha="center", va="center", color="black", fontsize=9)

    plt.colorbar(im, ax=ax)
    ax.set_title(f'Run-pair RDM Correlations: {subject} {roi}', fontsize=12, fontweight='bold')
    plt.tight_layout()

    fig_path2 = output_dir / f"rdm_runpair_corr_{subject}_{roi}.png"
    plt.savefig(fig_path2, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {fig_path2}")
    plt.close()

    # Save numerical results
    results = {
        'subject': subject,
        'roi': roi,
        'mean_correlation': reliability['mean_correlation'],
        'std_correlation': reliability['std_correlation'],
        'median_correlation': reliability['median_correlation'],
        'min_correlation': reliability['min_correlation'],
        'max_correlation': reliability['max_correlation'],
        'n_valid_voxels': reliability['n_valid_voxels'],
        'pairwise_correlations': reliability['pairwise_correlations']
    }

    json_path = output_dir / f"rdm_reliability_{subject}_{roi}.json"
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✓ Saved: {json_path}")

    print("\n" + "=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
