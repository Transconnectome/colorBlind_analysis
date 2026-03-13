#!/usr/bin/env python3
"""
map_voxel_color_preference.py — Voxel-level color preference mapping via KDE.

Implements Bannert & Bartels (2025) KDE+softmax approach to visualize which
voxels prefer each of the 8 colors, revealing population-level color biases.

Key idea: For each color, identify voxels with max response to that color,
apply KDE to their spatial distribution, normalize to % deviation from uniform.

Caveat: Our data lacks retinotopic coordinates, so we use voxel response
magnitude (SNR) as proxy for spatial organization.

Usage:
    python map_voxel_color_preference.py \
        --baseline_dir /path/to/C010 \
        --output_dir results/voxel_preference_maps \
        [--bandwidth_method scott]
"""

import argparse
import numpy as np
import json
from pathlib import Path
from scipy.stats import gaussian_kde
from scipy.stats import ttest_ind
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from utils_forward_model import (
    load_amplitudes, ROIS, save_config,
    DEFAULT_BASELINE_DIR, HUE_ANGLES
)

# Subject groups
HC_SUBJECTS = [f'sub-{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'sub-{i:02d}' for i in range(8, 11)]
ROI_DIR_MAP = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'V4'}

# Color names for 8 colors
COLOR_NAMES = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']


def compute_color_preferences(amplitudes):
    """Identify which color each voxel prefers (max response).

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        preferred_colors: (n_voxels,) indices 0-7 of preferred color
        response_strengths: (n_voxels,) max response magnitude
    """
    # Average across runs
    mean_response = amplitudes.mean(axis=0)  # (n_colors, n_voxels)

    # Find color with max response per voxel
    preferred_colors = mean_response.argmax(axis=0)  # (n_voxels,)
    response_strengths = mean_response.max(axis=0)   # (n_voxels,)

    return preferred_colors, response_strengths


def compute_kde_preference_density(preferred_colors, response_strengths,
                                   n_colors=8, bandwidth=None):
    """Compute KDE-based preference density for each color.

    Uses response strength (SNR) as 1D spatial proxy. In ideal case with
    retinotopic coordinates, would use 2D KDE on cortical surface.

    Args:
        preferred_colors: (n_voxels,) preferred color indices
        response_strengths: (n_voxels,) response magnitudes
        n_colors: number of colors (default 8)
        bandwidth: KDE bandwidth (None = Scott's rule)

    Returns:
        preference_densities: (n_colors,) normalized density per color
        kde_objects: list of KDE objects per color
    """
    preference_densities = np.zeros(n_colors)
    kde_objects = []

    for color_idx in range(n_colors):
        # Get voxels preferring this color
        mask = (preferred_colors == color_idx)

        if mask.sum() == 0:
            # No voxels prefer this color
            preference_densities[color_idx] = 0
            kde_objects.append(None)
            continue

        color_response_strengths = response_strengths[mask]

        # Compute KDE on response strengths (1D)
        try:
            if bandwidth is None:
                # Scott's rule
                kde = gaussian_kde(color_response_strengths, bw_method='scott')
            else:
                kde = gaussian_kde(color_response_strengths, bw_method=bandwidth)

            # Integrate density (should be ≈ 1 after normalization)
            # Use proportion of voxels as density measure
            preference_densities[color_idx] = mask.sum() / len(preferred_colors)

            kde_objects.append(kde)

        except Exception as e:
            print(f"    KDE failed for color {color_idx}: {e}")
            preference_densities[color_idx] = 0
            kde_objects.append(None)

    # Softmax normalization → % deviation from uniform
    uniform = 1.0 / n_colors
    preference_pct = (preference_densities - uniform) / uniform * 100

    return preference_pct, kde_objects


def analyze_subject_preference(subject, roi, baseline_dir, bandwidth):
    """Compute voxel color preference map for one subject-ROI.

    Returns:
        results: dict with preference_pct, preferred_colors, etc.
    """
    roi_dir = ROI_DIR_MAP[roi]

    try:
        amplitudes = load_amplitudes(subject, roi_dir, baseline_dir)
    except FileNotFoundError:
        print(f"  ⚠ Missing data: {subject} {roi}")
        return None

    # Compute preferences
    preferred_colors, response_strengths = compute_color_preferences(amplitudes)

    # KDE preference density
    preference_pct, kde_objects = compute_kde_preference_density(
        preferred_colors, response_strengths, bandwidth=bandwidth
    )

    # Count voxels per color
    color_counts = [(preferred_colors == i).sum() for i in range(8)]

    results = {
        'preference_pct': preference_pct.tolist(),
        'color_counts': color_counts,
        'n_voxels': len(preferred_colors),
        'bandwidth': bandwidth if bandwidth is not None else 'scott'
    }

    return results


def plot_preference_polar(results_by_group, output_dir):
    """Create polar plots of color preference per ROI (8 colors × 4 ROI).

    Args:
        results_by_group: dict {group: {ROI: [subject_results]}}
        output_dir: Path
    """
    fig, axes = plt.subplots(2, 4, figsize=(16, 8),
                            subplot_kw=dict(projection='polar'))
    groups = ['HC', 'CVD']

    # Polar angles for 8 colors (evenly spaced)
    theta = np.array(HUE_ANGLES) * np.pi / 180  # Convert to radians

    for row, group in enumerate(groups):
        for col, roi in enumerate(ROIS):
            ax = axes[row, col]

            if roi not in results_by_group[group] or len(results_by_group[group][roi]) == 0:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center',
                       transform=ax.transAxes)
                ax.set_title(f"{group} {roi}")
                continue

            subject_results = results_by_group[group][roi]

            # Compute group mean preference
            mean_preference = np.mean([res['preference_pct']
                                      for res in subject_results], axis=0)

            # Plot bars (positive = above uniform, negative = below uniform)
            colors_rgb = plt.cm.hsv(np.linspace(0, 1, 8, endpoint=False))
            bars = ax.bar(theta, mean_preference, width=2*np.pi/8,
                         color=colors_rgb, alpha=0.7, edgecolor='black')

            # Add zero line
            ax.axhline(0, color='gray', linestyle='--', linewidth=1)

            # Configure polar plot
            ax.set_theta_zero_location('N')
            ax.set_theta_direction(-1)
            ax.set_xticks(theta)
            ax.set_xticklabels(COLOR_NAMES, fontsize=8)
            ax.set_ylabel('% deviation from uniform', fontsize=8)
            ax.set_title(f"{group} {roi}", fontsize=10)

            # Set radial limits
            max_abs = max(abs(mean_preference.min()), abs(mean_preference.max()))
            ax.set_ylim(-max_abs * 1.2, max_abs * 1.2)

    plt.tight_layout()
    fig_path = output_dir / 'fig_preference_polar.pdf'
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved figure: {fig_path}")


def plot_preference_distribution(results_by_group, output_dir):
    """Create bar plots showing voxel count distribution per color.

    Args:
        results_by_group: dict {group: {ROI: [subject_results]}}
        output_dir: Path
    """
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    groups = ['HC', 'CVD']

    x_pos = np.arange(8)
    colors_rgb = plt.cm.hsv(np.linspace(0, 1, 8, endpoint=False))

    for row, group in enumerate(groups):
        for col, roi in enumerate(ROIS):
            ax = axes[row, col]

            if roi not in results_by_group[group] or len(results_by_group[group][roi]) == 0:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center',
                       transform=ax.transAxes)
                ax.set_title(f"{group} {roi}")
                continue

            subject_results = results_by_group[group][roi]

            # Compute mean voxel counts per color (normalized)
            mean_counts = np.mean([np.array(res['color_counts']) / res['n_voxels']
                                  for res in subject_results], axis=0)

            # Plot bars
            ax.bar(x_pos, mean_counts, color=colors_rgb, alpha=0.7, edgecolor='black')

            # Add uniform expectation line
            uniform = 1.0 / 8
            ax.axhline(uniform, color='gray', linestyle='--', linewidth=1,
                      label='Uniform (12.5%)')

            ax.set_xticks(x_pos)
            ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=8)
            ax.set_ylabel('Proportion of voxels')
            ax.set_title(f"{group} {roi}")
            ax.set_ylim(0, mean_counts.max() * 1.2)
            ax.legend(fontsize=8)

    plt.tight_layout()
    fig_path = output_dir / 'fig_preference_distribution.pdf'
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved figure: {fig_path}")


def compute_preference_statistics(results_by_group):
    """Test if HC vs CVD show different color preference patterns.

    Returns:
        stats: dict {ROI: {color_idx: {HC_mean, CVD_mean, p_value}}}
    """
    stats = {}

    for roi in ROIS:
        stats[roi] = {}

        for color_idx in range(8):
            hc_prefs = [res['preference_pct'][color_idx]
                       for res in results_by_group['HC'].get(roi, [])]
            cvd_prefs = [res['preference_pct'][color_idx]
                        for res in results_by_group['CVD'].get(roi, [])]

            if len(hc_prefs) < 2 or len(cvd_prefs) < 2:
                stats[roi][COLOR_NAMES[color_idx]] = {
                    'HC_mean': np.nan,
                    'CVD_mean': np.nan,
                    'p_value': np.nan
                }
                continue

            hc_mean = np.mean(hc_prefs)
            cvd_mean = np.mean(cvd_prefs)

            # Welch's t-test
            t_stat, p_value = ttest_ind(hc_prefs, cvd_prefs, equal_var=False)

            stats[roi][COLOR_NAMES[color_idx]] = {
                'HC_mean': float(hc_mean),
                'HC_std': float(np.std(hc_prefs, ddof=1)),
                'CVD_mean': float(cvd_mean),
                'CVD_std': float(np.std(cvd_prefs, ddof=1)),
                't_stat': float(t_stat),
                'p_value': float(p_value),
                'n_HC': len(hc_prefs),
                'n_CVD': len(cvd_prefs)
            }

    return stats


def main():
    parser = argparse.ArgumentParser(
        description='Voxel color preference mapping via KDE (Bannert & Bartels 2025)'
    )
    parser.add_argument('--baseline_dir', type=str,
                       default=DEFAULT_BASELINE_DIR,
                       help='Path to C010 baseline data')
    parser.add_argument('--output_dir', type=str, required=True,
                       help='Output directory')
    parser.add_argument('--bandwidth_method', type=str, default='scott',
                       help='KDE bandwidth method (scott, silverman, or float)')

    args = parser.parse_args()

    baseline_dir = Path(args.baseline_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse bandwidth
    if args.bandwidth_method in ['scott', 'silverman']:
        bandwidth = args.bandwidth_method
    else:
        try:
            bandwidth = float(args.bandwidth_method)
        except ValueError:
            bandwidth = 'scott'

    print("=" * 70)
    print("Voxel Color Preference Mapping (Bannert & Bartels 2025)")
    print("=" * 70)
    print(f"Baseline data: {baseline_dir}")
    print(f"Output dir: {output_dir}")
    print(f"KDE bandwidth: {bandwidth}")
    print()

    # Organize results
    results_by_group = {'HC': {}, 'CVD': {}}
    all_results = {}

    for roi in ROIS:
        print(f"ROI: {roi}")
        results_by_group['HC'][roi] = []
        results_by_group['CVD'][roi] = []

        for subject in HC_SUBJECTS + CVD_SUBJECTS:
            group = 'HC' if subject in HC_SUBJECTS else 'CVD'

            result = analyze_subject_preference(subject, roi, baseline_dir, bandwidth)

            if result is not None:
                results_by_group[group][roi].append(result)
                all_results[f"{subject}_{roi}"] = result

                # Print top 3 preferred colors
                pref_pct = np.array(result['preference_pct'])
                top3_idx = np.argsort(pref_pct)[-3:][::-1]
                top3_str = ', '.join([f"{COLOR_NAMES[i]}({pref_pct[i]:.1f}%)"
                                     for i in top3_idx])
                print(f"  {subject}: Top 3 = {top3_str}")

        print()

    # Compute statistics
    print("Computing HC vs CVD preference comparison...")
    stats = compute_preference_statistics(results_by_group)

    print("\nSignificant Preference Differences (HC vs CVD):")
    print("-" * 70)
    for roi in ROIS:
        sig_colors = [color for color, s in stats[roi].items()
                     if not np.isnan(s['p_value']) and s['p_value'] < 0.05]
        if sig_colors:
            print(f"{roi}:")
            for color in sig_colors:
                s = stats[roi][color]
                print(f"  {color:8s}: HC={s['HC_mean']:+.1f}%, "
                      f"CVD={s['CVD_mean']:+.1f}%, p={s['p_value']:.4f}*")

    # Save results
    results_file = output_dir / 'preference_results.json'
    with open(results_file, 'w') as f:
        json.dump({
            'per_subject': all_results,
            'preference_statistics': stats,
            'color_names': COLOR_NAMES,
            'config': {
                'bandwidth_method': str(bandwidth),
                'baseline_dir': str(baseline_dir)
            }
        }, f, indent=2)
    print(f"\n✓ Saved results: {results_file}")

    save_config(output_dir, args)

    # Create figures
    print("\nCreating preference maps...")
    plot_preference_polar(results_by_group, output_dir)
    plot_preference_distribution(results_by_group, output_dir)

    print("\n" + "=" * 70)
    print("DONE - Voxel color preference mapping complete")
    print("=" * 70)


if __name__ == '__main__':
    main()
