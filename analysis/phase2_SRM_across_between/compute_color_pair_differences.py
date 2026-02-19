#!/usr/bin/env python3
"""
Compute color-pair-specific RDM differences between HC and CVD subjects

Analyzes which of the 28 unique color pairs (from 8×8 RDM) show robust
HC-CVD divergence using bootstrap confidence intervals.

Output: Figures showing per-pair differences, CI, and significance
"""

import numpy as np
import json
from pathlib import Path
from scipy import stats
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Configuration
BASE_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')

# Data source: SRM-aligned amplitudes from LOO-consistent analysis (HC-only SRM, Feb 9 2026)
ALIGNED_DATA_DIR = BASE_DIR / 'analysis' / 'phase2_SRM_across_between' / 'results' / 'c010' / 'combined_with_aligned'

# Output directories
OUTPUT_FIG_DIR = BASE_DIR / 'analysis' / 'phase2_SRM_across_between' / 'visualization'
OUTPUT_JSON_DIR = BASE_DIR / 'analysis' / 'phase2_SRM_across_between' / 'results' / 'color_pair_analysis'
OUTPUT_FIG_DIR.mkdir(exist_ok=True, parents=True)
OUTPUT_JSON_DIR.mkdir(exist_ok=True, parents=True)

# Subject configuration
HC_SUBJECTS = [f'sub-{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
CVD_TYPES = {'sub-08': 'Deutan', 'sub-09': 'Protan', 'sub-10': 'Deutan'}

# Color names (8 colors)
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']

ROIS = ['V1', 'V2', 'V3', 'V4']


def extract_color_pairs(rdm_matrix):
    """
    Extract upper triangle of 8×8 RDM (28 unique pairs)

    Args:
        rdm_matrix: (8, 8) dissimilarity matrix

    Returns:
        pairs: List of 28 (i, j) tuples
        values: Array of 28 dissimilarity values
    """
    mask = np.triu(np.ones((8, 8), dtype=bool), k=1)
    pairs = list(zip(*np.where(mask)))
    values = rdm_matrix[mask]
    return pairs, values


def get_pair_labels(pairs):
    """
    Convert pair indices to color names

    Args:
        pairs: List of (i, j) tuples

    Returns:
        List of strings like "Red-Orange"
    """
    return [f"{COLOR_NAMES[i]}-{COLOR_NAMES[j]}" for i, j in pairs]


def compute_pair_differences(rdm_hc, rdm_cvd):
    """
    Compute difference for each of 28 color pairs

    Args:
        rdm_hc: (8, 8) HC mean RDM
        rdm_cvd: (8, 8) CVD RDM

    Returns:
        pair_diffs: (28,) array of signed differences (CVD - HC)
        pair_labels: List of 28 strings
        pairs: List of 28 (i, j) tuples
    """
    pairs, hc_vals = extract_color_pairs(rdm_hc)
    _, cvd_vals = extract_color_pairs(rdm_cvd)

    pair_diffs = cvd_vals - hc_vals  # Signed difference
    pair_labels = get_pair_labels(pairs)

    return pair_diffs, pair_labels, pairs


def bootstrap_pair_ci(rdm_hc_subjects, rdm_cvd, n_bootstrap=1000, seed=42):
    """
    Compute bootstrap CI for each pair difference

    Args:
        rdm_hc_subjects: List of 7 HC RDM matrices (8×8 each)
        rdm_cvd: Single CVD RDM matrix (8×8)
        n_bootstrap: Number of bootstrap iterations
        seed: Random seed for reproducibility

    Returns:
        pair_diffs: (28,) mean differences
        ci_lower: (28,) lower 95% CI
        ci_upper: (28,) upper 95% CI
        bootstrap_diffs: (n_bootstrap, 28) full bootstrap distribution
    """
    np.random.seed(seed)

    n_pairs = 28
    bootstrap_diffs = np.zeros((n_bootstrap, n_pairs))

    for b in range(n_bootstrap):
        # Resample HC subjects with replacement
        sample_idx = np.random.choice(len(rdm_hc_subjects), size=len(rdm_hc_subjects), replace=True)
        rdm_hc_boot = np.mean([rdm_hc_subjects[i] for i in sample_idx], axis=0)

        # Compute differences
        _, hc_vals = extract_color_pairs(rdm_hc_boot)
        _, cvd_vals = extract_color_pairs(rdm_cvd)
        bootstrap_diffs[b] = cvd_vals - hc_vals

    # Compute statistics
    pair_diffs = np.mean(bootstrap_diffs, axis=0)
    ci_lower = np.percentile(bootstrap_diffs, 2.5, axis=0)
    ci_upper = np.percentile(bootstrap_diffs, 97.5, axis=0)

    return pair_diffs, ci_lower, ci_upper, bootstrap_diffs


def identify_significant_pairs(pair_diffs, ci_lower, ci_upper):
    """
    Identify color pairs with CI excluding zero

    Args:
        pair_diffs: (28,) mean differences
        ci_lower: (28,) lower 95% CI
        ci_upper: (28,) upper 95% CI

    Returns:
        sig_idx: Indices of significant pairs
        effect_sizes: Standardized effect sizes (difference / CI width)
    """
    # Pairs where CI doesn't include zero
    sig_positive = ci_lower > 0  # CVD > HC
    sig_negative = ci_upper < 0  # CVD < HC
    sig_idx = np.where(sig_positive | sig_negative)[0]

    # Compute effect size (normalized by CI width)
    ci_width = ci_upper - ci_lower
    # Avoid division by zero for degenerate bootstrap (all same HC RDM)
    ci_width = np.where(ci_width == 0, 1e-10, ci_width)
    effect_sizes = np.abs(pair_diffs) / ci_width

    return sig_idx, effect_sizes


def compute_rdm_from_pattern(pattern):
    """
    Compute RDM (8×8 correlation distance matrix) from aligned pattern

    Args:
        pattern: (8, k) array - 8 colors × k SRM components

    Returns:
        rdm: (8, 8) dissimilarity matrix (correlation distance)
    """
    from scipy.spatial.distance import squareform, pdist
    return squareform(pdist(pattern, metric='correlation'))


def load_rdm_matrices(aligned_data_dir, roi):
    """
    Load aligned amplitudes and compute RDM matrices for HC and CVD subjects

    Args:
        aligned_data_dir: Path to aligned amplitudes directory
        roi: ROI name ('V1', 'V2', 'V3', 'V4')

    Returns:
        rdm_hc_subjects: List of 7 HC RDM matrices (8×8 each)
        rdm_cvd_dict: Dict of {cvd_id: RDM matrix (8×8)}
    """
    # Load aligned amplitudes (HC-only SRM + Procrustes aligned)
    aligned_file = aligned_data_dir / f'{roi}_procrustes_aligned_amplitudes.npy'

    if not aligned_file.exists():
        raise FileNotFoundError(f"Aligned amplitudes not found: {aligned_file}")

    # Load data (dict with subject IDs as keys)
    aligned_data = np.load(aligned_file, allow_pickle=True).item()

    # Extract HC RDMs
    rdm_hc_subjects = []
    for hc_id in HC_SUBJECTS:
        if hc_id not in aligned_data:
            raise ValueError(f"HC subject {hc_id} not found in aligned data for {roi}")

        pattern = aligned_data[hc_id]  # (8, k)
        rdm = compute_rdm_from_pattern(pattern)
        rdm_hc_subjects.append(rdm)

    print(f"  Loaded {len(rdm_hc_subjects)} HC RDMs from aligned amplitudes")

    # Extract CVD RDMs
    rdm_cvd_dict = {}
    for cvd_id in CVD_SUBJECTS:
        if cvd_id not in aligned_data:
            print(f"  Warning: CVD subject {cvd_id} not found in aligned data for {roi}")
            continue

        pattern = aligned_data[cvd_id]  # (8, k)
        rdm = compute_rdm_from_pattern(pattern)
        rdm_cvd_dict[cvd_id] = rdm

    return rdm_hc_subjects, rdm_cvd_dict


def visualize_color_pair_differences(roi, results_dict, output_dir):
    """
    Create figure showing color-pair differences for all CVD subjects

    Args:
        roi: ROI name
        results_dict: Dictionary with CVD results
        output_dir: Path to save figure
    """
    n_cvd = len(results_dict)

    # Create figure with subplots for each CVD subject
    fig, axes = plt.subplots(n_cvd, 1, figsize=(16, 6 * n_cvd))
    if n_cvd == 1:
        axes = [axes]

    cvd_ids = sorted(results_dict.keys())  # '08', '09', '10'

    for ax_idx, cvd_short_id in enumerate(cvd_ids):
        ax = axes[ax_idx]
        cvd_data = results_dict[cvd_short_id]

        pair_labels = cvd_data['pair_labels']
        diffs = np.array(cvd_data['all_diffs'])
        ci_low = np.array(cvd_data['ci_lower'])
        ci_high = np.array(cvd_data['ci_upper'])

        # Identify significant pairs
        sig_positive = ci_low > 0
        sig_negative = ci_high < 0
        significant = sig_positive | sig_negative

        # Create x positions
        x = np.arange(len(pair_labels))

        # Color bars by significance
        colors = []
        for i in range(len(diffs)):
            if sig_positive[i]:
                colors.append('#D32F2F')  # Red (CVD > HC)
            elif sig_negative[i]:
                colors.append('#1976D2')  # Blue (CVD < HC)
            else:
                colors.append('#BDBDBD')  # Gray (n.s.)

        # Plot bars
        bars = ax.bar(x, diffs, color=colors, alpha=0.7, edgecolor='black', linewidth=1.2)

        # Plot error bars
        yerr_lower = diffs - ci_low
        yerr_upper = ci_high - diffs
        ax.errorbar(x, diffs, yerr=[yerr_lower, yerr_upper],
                   fmt='none', ecolor='black', elinewidth=2, capsize=4, capthick=2)

        # Add horizontal line at 0
        ax.axhline(0, color='black', linestyle='--', linewidth=2, alpha=0.5)

        # Formatting
        cvd_full_id = f'sub-{cvd_short_id}'
        cvd_type = cvd_data['cvd_type']
        n_sig = cvd_data['n_significant']

        ax.set_title(f'{cvd_full_id} ({cvd_type}) - {roi}\n'
                    f'Significant pairs: {n_sig}/28 (CI excludes 0)',
                    fontsize=14, fontweight='bold', pad=15)

        ax.set_xlabel('Color Pair', fontsize=12, fontweight='bold')
        ax.set_ylabel('RDM Difference (CVD - HC)', fontsize=12, fontweight='bold')

        ax.set_xticks(x)
        ax.set_xticklabels(pair_labels, rotation=45, ha='right', fontsize=9)
        ax.grid(axis='y', alpha=0.3, linestyle=':')

        # Add legend
        legend_elements = [
            Rectangle((0, 0), 1, 1, fc='#D32F2F', alpha=0.7, label='CVD > HC (p < 0.05)'),
            Rectangle((0, 0), 1, 1, fc='#1976D2', alpha=0.7, label='CVD < HC (p < 0.05)'),
            Rectangle((0, 0), 1, 1, fc='#BDBDBD', alpha=0.7, label='Not significant')
        ]
        ax.legend(handles=legend_elements, loc='upper right', fontsize=10)

    plt.tight_layout()

    # Save figure
    output_path = output_dir / f'color_pair_differences_{roi}.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved figure: {output_path}")


def analyze_roi(roi, aligned_data_dir, n_bootstrap=1000):
    """
    Analyze color-pair differences for one ROI

    Args:
        roi: ROI name
        aligned_data_dir: Path to aligned amplitudes directory
        n_bootstrap: Number of bootstrap iterations

    Returns:
        Dict with results for each CVD subject
    """
    print(f"\n{'='*60}")
    print(f"Analyzing {roi}")
    print(f"{'='*60}")

    # Load RDM matrices from aligned amplitudes
    rdm_hc_subjects, rdm_cvd_dict = load_rdm_matrices(aligned_data_dir, roi)

    results = {}

    for cvd_id, rdm_cvd in rdm_cvd_dict.items():
        print(f"\n{cvd_id} ({CVD_TYPES[cvd_id]}):")

        # Compute mean HC RDM
        rdm_hc_mean = np.mean(rdm_hc_subjects, axis=0)

        # Compute differences with bootstrap CI
        diffs, ci_low, ci_high, boot_diffs = bootstrap_pair_ci(
            rdm_hc_subjects, rdm_cvd, n_bootstrap=n_bootstrap
        )

        # Identify significant pairs
        sig_idx, effect_sizes = identify_significant_pairs(diffs, ci_low, ci_high)

        # Get pair labels
        _, pair_labels, pairs = compute_pair_differences(rdm_hc_mean, rdm_cvd)

        # Print top differences
        sorted_idx = np.argsort(np.abs(diffs))[::-1]
        print(f"  Top 5 absolute differences:")
        for i in sorted_idx[:5]:
            sig_marker = "***" if i in sig_idx else ""
            print(f"    {pair_labels[i]:20s}: {diffs[i]:+.3f} " +
                  f"[{ci_low[i]:+.3f}, {ci_high[i]:+.3f}] {sig_marker}")

        # Store results (convert numpy types to Python types for JSON)
        results[cvd_id.split('-')[1]] = {  # Store as '08', '09', '10'
            'cvd_type': CVD_TYPES[cvd_id],
            'all_diffs': [float(x) for x in diffs],
            'ci_lower': [float(x) for x in ci_low],
            'ci_upper': [float(x) for x in ci_high],
            'pair_labels': pair_labels,
            'pairs': [[int(i), int(j)] for i, j in pairs],  # Convert tuples to lists
            'significant_pairs': [pair_labels[i] for i in sig_idx],
            'significant_diffs': [float(diffs[i]) for i in sig_idx],
            'significant_ci_lower': [float(ci_low[i]) for i in sig_idx],
            'significant_ci_upper': [float(ci_high[i]) for i in sig_idx],
            'effect_sizes': [float(x) for x in effect_sizes],
            'n_significant': int(len(sig_idx)),
            'n_bootstrap': int(n_bootstrap)
        }

        print(f"  Significant pairs (CI excludes 0): {len(sig_idx)}/28")

    return results


def main():
    """Main execution function"""

    print("=" * 80)
    print("Color-Pair RDM Difference Analysis (Figure + JSON Generation)")
    print("=" * 80)
    print(f"Aligned data directory: {ALIGNED_DATA_DIR}")
    print(f"Output figures: {OUTPUT_FIG_DIR}")
    print(f"Output JSON: {OUTPUT_JSON_DIR}")
    print(f"HC subjects: {len(HC_SUBJECTS)}")
    print(f"CVD subjects: {len(CVD_SUBJECTS)}")
    print(f"Bootstrap iterations: 1000")

    all_results = {}

    for roi in ROIS:
        # Check if aligned amplitude files exist for this ROI
        aligned_file = ALIGNED_DATA_DIR / f'{roi}_procrustes_aligned_amplitudes.npy'

        if not aligned_file.exists():
            print(f"\n⚠ Skipping {roi}: Aligned amplitude file not found")
            continue

        try:
            results = analyze_roi(roi, ALIGNED_DATA_DIR, n_bootstrap=1000)
            all_results[roi] = results

            # Create visualization
            visualize_color_pair_differences(roi, results, OUTPUT_FIG_DIR)

            # Save JSON for this ROI
            json_file = OUTPUT_JSON_DIR / f'color_pair_analysis_{roi}.json'
            with open(json_file, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"  ✓ Saved JSON: {json_file}")

        except Exception as e:
            print(f"\n✗ Error processing {roi}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Save combined results
    if len(all_results) > 0:
        combined_file = OUTPUT_JSON_DIR / 'color_pair_analysis_all_rois.json'
        with open(combined_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"\n✓ Saved combined JSON: {combined_file}")

    print("\n" + "=" * 80)
    print("✓ Color-pair analysis complete!")
    print(f"  Figures: {OUTPUT_FIG_DIR} ({len(all_results)} ROIs)")
    print(f"  JSON: {OUTPUT_JSON_DIR} ({len(all_results)} ROIs + combined)")
    print("=" * 80)


if __name__ == '__main__':
    main()
