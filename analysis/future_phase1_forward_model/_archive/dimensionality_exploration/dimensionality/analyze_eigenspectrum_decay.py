#!/usr/bin/env python3
"""
analyze_eigenspectrum_decay.py — Broken power law eigenspectrum analysis.

Implements Pospisil & Pillow (2024) eigenspectrum geometry analysis to test:
1. Whether signal eigenvalues follow broken power law (α_early ≠ α_late)
2. HC vs CVD dimensionality comparison (steeper decay in CVD?)
3. Validation that SRM k=3-4 captures dominant modes

Key insight from Pospisil: V1 eigenspectrum shows α≈0.5 for first ~10 modes,
α≈1.2 for later modes, NOT simple power law (α≈1). This suggests ~10 dominant
modes shape sensory encoding, while hundreds of additional modes contribute
minimally to signal.

Usage:
    python analyze_eigenspectrum_decay.py \
        --baseline_dir /path/to/C010 \
        --output_dir results/eigenspectrum_decay \
        [--n_early 10] [--n_late 50]
"""

import argparse
import numpy as np
import json
from pathlib import Path
from scipy.stats import linregress, ttest_ind
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from utils_forward_model import (
    load_amplitudes, ROIS, save_config,
    DEFAULT_BASELINE_DIR
)

# Subject groups
HC_SUBJECTS = [f'sub-{i:02d}' for i in range(1, 8)]  # sub-01 to sub-07
CVD_SUBJECTS = [f'sub-{i:02d}' for i in range(8, 11)]  # sub-08 to sub-10

# ROI directory mapping (hV4 → V4 on disk)
ROI_DIR_MAP = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'V4'}


def compute_eigenspectrum(amplitudes):
    """Compute PCA eigenvalues from neural data.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) array

    Returns:
        eigenvalues: (n_voxels,) sorted in descending order
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Concatenate across runs and colors → (n_samples, n_voxels)
    X = amplitudes.reshape(-1, n_voxels)
    n_samples = X.shape[0]

    # Center columns (voxel-wise mean subtraction)
    X_centered = X - X.mean(axis=0, keepdims=True)

    # Compute sample covariance: Σ̂ = (1/n) X^T X
    cov_matrix = (X_centered.T @ X_centered) / n_samples

    # SVD to get eigenvalues
    eigenvalues = np.linalg.eigvalsh(cov_matrix)

    # Sort descending
    eigenvalues = np.sort(eigenvalues)[::-1]

    return eigenvalues


def fit_power_law(eigenvalues, indices):
    """Fit power law λ_i = c · i^(-α) via log-log regression.

    Args:
        eigenvalues: (n,) eigenvalue array
        indices: array of indices to fit (e.g., 0-9 for early modes)

    Returns:
        alpha: fitted power law exponent
        intercept: log(c)
        r_squared: goodness of fit
    """
    log_i = np.log(indices + 1)  # i=1,2,3,... (avoid log(0))
    log_lambda = np.log(eigenvalues[indices] + 1e-10)  # avoid log(0)

    # Filter out invalid values (negative eigenvalues or zeros)
    valid = np.isfinite(log_lambda) & (log_lambda > -20)

    if valid.sum() < 2:
        return np.nan, np.nan, np.nan

    slope, intercept, r_value, _, _ = linregress(log_i[valid], log_lambda[valid])

    # slope = -α in λ = c · i^(-α)
    alpha = -slope
    r_squared = r_value ** 2

    return alpha, intercept, r_squared


def analyze_subject_eigenspectrum(subject, roi, baseline_dir, n_early, n_late):
    """Compute eigenspectrum and fit broken power law for one subject-ROI.

    Returns:
        results: dict with eigenvalues, alpha_early, alpha_late, etc.
    """
    try:
        # load_amplitudes expects subject='01' not 'sub-01', and handles ROI mapping internally
        sub_id = subject.replace('sub-', '')
        amplitudes = load_amplitudes(baseline_dir, sub_id, roi)
    except FileNotFoundError:
        print(f"  ⚠ Missing data: {subject} {roi}")
        return None

    # Compute eigenvalues
    eigenvalues = compute_eigenspectrum(amplitudes)
    n_voxels = len(eigenvalues)

    # Ensure we have enough modes to fit
    if n_voxels < n_late:
        print(f"  ⚠ {subject} {roi}: only {n_voxels} voxels (< {n_late})")
        # Adjust n_late if needed
        n_late_actual = min(n_late, n_voxels - 1)
    else:
        n_late_actual = n_late

    # Fit early modes (shallow decay)
    early_indices = np.arange(n_early)
    alpha_early, c_early, r2_early = fit_power_law(eigenvalues, early_indices)

    # Fit late modes (steeper decay)
    # Use modes [n_early, n_late_actual)
    late_indices = np.arange(n_early, n_late_actual)
    alpha_late, c_late, r2_late = fit_power_law(eigenvalues, late_indices)

    # Compute explained variance ratio
    total_var = eigenvalues.sum()
    explained_var_early = eigenvalues[:n_early].sum() / total_var
    explained_var_late = eigenvalues[n_early:n_late_actual].sum() / total_var

    results = {
        'eigenvalues': eigenvalues.tolist(),
        'n_voxels': n_voxels,
        'alpha_early': float(alpha_early),
        'alpha_late': float(alpha_late),
        'c_early': float(c_early),
        'c_late': float(c_late),
        'r2_early': float(r2_early),
        'r2_late': float(r2_late),
        'explained_var_early': float(explained_var_early),
        'explained_var_late': float(explained_var_late),
        'n_early': n_early,
        'n_late': n_late_actual
    }

    return results


def plot_eigenspectrum_decay(results_by_group, output_dir, n_early, n_late):
    """Create 2×4 subplot: HC/CVD × V1/V2/V3/hV4 log-log eigenvalue plots.

    Args:
        results_by_group: dict {group: {ROI: [subject_results]}}
        output_dir: Path to save figure
        n_early, n_late: indices for early/late regime
    """
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    groups = ['HC', 'CVD']

    for row, group in enumerate(groups):
        for col, roi in enumerate(ROIS):
            ax = axes[row, col]

            if roi not in results_by_group[group]:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center',
                       transform=ax.transAxes)
                ax.set_title(f"{group} {roi}")
                continue

            subject_results = results_by_group[group][roi]

            # Plot individual subjects (gray)
            for res in subject_results:
                eigenvals = np.array(res['eigenvalues'])
                n_modes = min(n_late, len(eigenvals))
                indices = np.arange(1, n_modes + 1)

                ax.loglog(indices, eigenvals[:n_modes],
                         color='gray', alpha=0.3, linewidth=0.5)

            # Compute group mean eigenspectrum
            min_voxels = min(len(res['eigenvalues']) for res in subject_results)
            mean_eigenvals = np.mean([res['eigenvalues'][:min_voxels]
                                     for res in subject_results], axis=0)

            indices = np.arange(1, len(mean_eigenvals) + 1)
            ax.loglog(indices, mean_eigenvals, 'k-', linewidth=2, label='Mean')

            # Fit and plot power laws
            early_idx = np.arange(n_early)
            late_idx = np.arange(n_early, min(n_late, len(mean_eigenvals)))

            alpha_early, c_early, _ = fit_power_law(mean_eigenvals, early_idx)
            alpha_late, c_late, _ = fit_power_law(mean_eigenvals, late_idx)

            # Plot fitted lines
            if not np.isnan(alpha_early):
                fit_early = np.exp(c_early) * (early_idx + 1) ** (-alpha_early)
                ax.loglog(early_idx + 1, fit_early, 'r--', linewidth=2,
                         label=f'Early: α={alpha_early:.2f}')

            if not np.isnan(alpha_late):
                fit_late = np.exp(c_late) * (late_idx + 1) ** (-alpha_late)
                ax.loglog(late_idx + 1, fit_late, 'b--', linewidth=2,
                         label=f'Late: α={alpha_late:.2f}')

            # Mark transition point
            ax.axvline(n_early, color='green', linestyle=':', alpha=0.5,
                      label=f'Transition (i={n_early})')

            ax.set_xlabel('Mode index i')
            ax.set_ylabel('Eigenvalue λᵢ')
            ax.set_title(f"{group} {roi}")
            ax.legend(fontsize=8, loc='upper right')
            ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig_path = output_dir / 'fig_eigenspectrum_decay.pdf'
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved figure: {fig_path}")


def compute_group_statistics(results_by_group):
    """Compare HC vs CVD eigenspectrum parameters.

    Returns:
        stats: dict {ROI: {param: {HC_mean, CVD_mean, t_stat, p_value}}}
    """
    stats = {}

    for roi in ROIS:
        stats[roi] = {}

        # Extract alpha values
        for param in ['alpha_early', 'alpha_late', 'explained_var_early']:
            hc_vals = [res[param] for res in results_by_group['HC'].get(roi, [])
                      if not np.isnan(res[param])]
            cvd_vals = [res[param] for res in results_by_group['CVD'].get(roi, [])
                       if not np.isnan(res[param])]

            if len(hc_vals) < 2 or len(cvd_vals) < 2:
                stats[roi][param] = {
                    'HC_mean': np.nan,
                    'CVD_mean': np.nan,
                    't_stat': np.nan,
                    'p_value': np.nan
                }
                continue

            hc_mean = np.mean(hc_vals)
            cvd_mean = np.mean(cvd_vals)

            # Welch's t-test (unequal variances)
            t_stat, p_value = ttest_ind(hc_vals, cvd_vals, equal_var=False)

            stats[roi][param] = {
                'HC_mean': float(hc_mean),
                'HC_std': float(np.std(hc_vals, ddof=1)),
                'CVD_mean': float(cvd_mean),
                'CVD_std': float(np.std(cvd_vals, ddof=1)),
                't_stat': float(t_stat),
                'p_value': float(p_value),
                'n_HC': len(hc_vals),
                'n_CVD': len(cvd_vals)
            }

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Analyze eigenspectrum decay (Pospisil & Pillow 2024 framework)'
    )
    parser.add_argument('--baseline_dir', type=str,
                       default=DEFAULT_BASELINE_DIR,
                       help='Path to C010 baseline data')
    parser.add_argument('--output_dir', type=str, required=True,
                       help='Output directory for results')
    parser.add_argument('--n_early', type=int, default=10,
                       help='Number of early modes to fit (default: 10)')
    parser.add_argument('--n_late', type=int, default=50,
                       help='Max index for late modes (default: 50)')

    args = parser.parse_args()

    baseline_dir = Path(args.baseline_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Eigenspectrum Decay Analysis (Pospisil & Pillow 2024)")
    print("=" * 70)
    print(f"Baseline data: {baseline_dir}")
    print(f"Output dir: {output_dir}")
    print(f"Early modes: 0-{args.n_early}, Late modes: {args.n_early}-{args.n_late}")
    print()

    # Organize results by group and ROI
    results_by_group = {'HC': {}, 'CVD': {}}
    all_results = {}

    for roi in ROIS:
        print(f"ROI: {roi}")
        results_by_group['HC'][roi] = []
        results_by_group['CVD'][roi] = []

        for subject in HC_SUBJECTS + CVD_SUBJECTS:
            group = 'HC' if subject in HC_SUBJECTS else 'CVD'

            result = analyze_subject_eigenspectrum(
                subject, roi, baseline_dir, args.n_early, args.n_late
            )

            if result is not None:
                results_by_group[group][roi].append(result)
                all_results[f"{subject}_{roi}"] = result

                print(f"  {subject}: α_early={result['alpha_early']:.3f}, "
                      f"α_late={result['alpha_late']:.3f}, "
                      f"R²_early={result['r2_early']:.3f}")

        print()

    # Compute group statistics
    print("Computing HC vs CVD statistics...")
    stats = compute_group_statistics(results_by_group)

    # Print summary
    print("\nGroup Comparison (HC vs CVD):")
    print("-" * 70)
    for roi in ROIS:
        print(f"\n{roi}:")
        for param in ['alpha_early', 'alpha_late', 'explained_var_early']:
            s = stats[roi][param]
            if not np.isnan(s['p_value']):
                sig = '*' if s['p_value'] < 0.05 else ''
                print(f"  {param:20s}: HC={s['HC_mean']:.3f}±{s['HC_std']:.3f}, "
                      f"CVD={s['CVD_mean']:.3f}±{s['CVD_std']:.3f}, "
                      f"p={s['p_value']:.4f}{sig}")

    # Save results
    results_file = output_dir / 'eigenspectrum_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'per_subject': all_results,
            'group_statistics': stats,
            'config': {
                'n_early': args.n_early,
                'n_late': args.n_late,
                'baseline_dir': str(baseline_dir)
            }
        }, f, indent=2)
    print(f"\n✓ Saved results: {results_file}")

    # Save config
    cfg = {k: v for k, v in vars(args).items() if k != 'output_dir'}
    save_config(output_dir, **cfg)

    # Create figure
    print("\nCreating eigenspectrum decay plots...")
    plot_eigenspectrum_decay(results_by_group, output_dir, args.n_early, args.n_late)

    print("\n" + "=" * 70)
    print("DONE - Eigenspectrum decay analysis complete")
    print("=" * 70)


if __name__ == '__main__':
    main()
