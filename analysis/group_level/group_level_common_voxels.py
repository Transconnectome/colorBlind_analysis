#!/usr/bin/env python3
"""
group_level_common_voxels.py
============================

Group-level analysis to identify voxels with significant color-encoding across subjects.

Approach:
---------
1. Load amplitudes_z.npy from all non-CVD subjects
2. For each voxel:
   - Compute group-level statistics (one-sample t-test per color)
   - Test if color activation is significantly different from baseline
3. Apply multiple comparison correction (FDR)
4. Select voxels with significant group-level contrast
5. Visualize common voxels in brain space

이러한 significant common voxels를 basis로 하여 ANOVA, RFE, PCA를 적용합니다.

Non-CVD subjects: 01, 02, 03, 05, 06, 07 (6 subjects)
Excluded: sub-04 (no BOLD signal at V1)

Usage:
    python group_level_common_voxels.py --roi V1 --timestamp baseline32_deob \
        --dataset deoblique_v2 --fdr-alpha 0.05

Output:
    derivatives/group_level/{timestamp}/{roi}/
    ├── common_voxels/
    │   ├── group_amplitudes_z.npy           # (n_subjects, n_runs, n_colors, n_voxels)
    │   ├── group_statistics.npz             # t-values, p-values per voxel-color
    │   ├── significant_voxels.npy           # Boolean mask of significant voxels
    │   ├── significant_voxel_indices.npy    # Indices of significant voxels
    │   ├── group_statistics_summary.csv     # Summary statistics
    │   └── figures/
    │       ├── common_voxels_brain.png      # Brain visualization
    │       ├── significance_distribution.png
    │       └── per_color_activation.png

Author: Claude Code
Date: 2025-12-13
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from scipy import stats
from statsmodels.stats.multitest import multipletests
import nibabel as nib
from nilearn import plotting as niplot
import argparse
import sys
import glob
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Group-level common voxel identification'
    )

    # Required arguments
    parser.add_argument('--roi', type=str, required=True,
                        help='ROI name (V1, V2, V3, hV4)')
    parser.add_argument('--timestamp', type=str, required=True,
                        help='Baseline timestamp (e.g., baseline32_deob, baseline81_deob)')
    parser.add_argument('--dataset', type=str, default='deoblique_v2',
                        help='Dataset name (default: deoblique_v2)')

    # Non-CVD subjects (default)
    parser.add_argument('--subjects', type=str, nargs='+',
                        default=['01', '02', '03', '05', '06', '07'],
                        help='Subject IDs (default: non-CVD subjects)')

    # Statistical parameters
    parser.add_argument('--fdr-alpha', type=float, default=0.05,
                        help='FDR alpha level (default: 0.05)')
    parser.add_argument('--min-colors', type=int, default=1,
                        help='Minimum number of colors with significant activation (default: 1)')

    # Output directory
    parser.add_argument('--output-dir', type=str, default=None,
                        help='Output directory (default: derivatives/group_level/{timestamp}/{roi}/common_voxels)')

    return parser.parse_args()


# ============================================================================
# Data Loading
# ============================================================================

def load_subject_amplitudes(subject_id, roi, timestamp, dataset='deoblique_v2'):
    """
    Load amplitudes_z.npy and voxel SNR for a single subject

    Args:
        subject_id: Subject ID (e.g., '01')
        roi: ROI name (e.g., 'V1')
        timestamp: Baseline timestamp
        dataset: Dataset name

    Returns:
        amplitudes_z: (n_runs, n_colors, n_voxels) array
        voxel_snr: (n_voxels,) array - SNR for each voxel (for quality-based selection)
        result_dir: Path to baseline result directory
    """
    base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
    pattern = str(base_path / f'sm*_sub-{subject_id}_{roi}_*')

    matches = glob.glob(pattern)

    if len(matches) == 0:
        raise FileNotFoundError(
            f"Baseline result not found for sub-{subject_id} {roi}!\n"
            f"  Pattern: {pattern}"
        )

    # Filter by directories that contain amplitudes_z.npy
    valid_matches = [m for m in matches if Path(m).joinpath('amplitudes_z.npy').exists()]

    if not valid_matches:
        raise FileNotFoundError(
            f"No valid baseline results with amplitudes_z.npy found!\n"
            f"  Subject: {subject_id}, ROI: {roi}\n"
            f"  Pattern: {pattern}"
        )

    # Prefer directories ending with '_None' (auto-detected config)
    none_matches = [m for m in valid_matches if m.endswith('_None')]

    if len(none_matches) > 0:
        none_matches_sorted = sorted(none_matches, key=lambda x: Path(x).stat().st_mtime, reverse=True)
        result_dir = Path(none_matches_sorted[0])
    else:
        result_dir = Path(valid_matches[0])

    # Load amplitudes
    amplitudes_path = result_dir / 'amplitudes_z.npy'
    amplitudes_z = np.load(amplitudes_path)

    # Try to load voxel quality metric (SNR or R2)
    voxel_snr = None
    quality_candidates = [
        result_dir / 'voxel_snr.npy',
        result_dir / 'r2_voxel.npy',
    ]

    for quality_path in quality_candidates:
        if quality_path.exists():
            voxel_snr = np.load(quality_path)
            break

    if voxel_snr is None:
        # If no quality metric, use uniform (all voxels equally important)
        voxel_snr = np.ones(amplitudes_z.shape[2])
        print(f"      Warning: No voxel quality metric found, using uniform weights")

    return amplitudes_z, voxel_snr, str(result_dir)


def select_top_k_voxels_by_snr(amplitudes_z, voxel_snr, k):
    """
    Select top-k voxels by SNR (or R2)

    Args:
        amplitudes_z: (n_runs, n_colors, n_voxels) array
        voxel_snr: (n_voxels,) array - quality metric
        k: Number of voxels to select

    Returns:
        amplitudes_selected: (n_runs, n_colors, k) array
        selected_indices: (k,) array - indices of selected voxels
    """
    n_voxels = amplitudes_z.shape[2]

    if k > n_voxels:
        # If k is larger than available voxels, use all voxels
        k = n_voxels

    # Sort by SNR and select top-k
    sorted_indices = np.argsort(voxel_snr)[::-1]  # Descending order
    selected_indices = sorted_indices[:k]

    # Extract amplitudes
    amplitudes_selected = amplitudes_z[:, :, selected_indices]

    return amplitudes_selected, selected_indices


def validate_group_data_consistency(amplitudes_list, subjects):
    """
    Validate that all subjects have consistent data dimensions

    This is CRITICAL because np.array(amplitudes_list) requires identical shapes.

    Args:
        amplitudes_list: List of (n_runs, n_colors, n_voxels) arrays
        subjects: List of subject IDs

    Raises:
        ValueError: If dimensions are inconsistent
    """
    print(f"\n{'='*80}")
    print(f"Validating data consistency...")
    print(f"{'='*80}")

    # Extract shapes
    shapes = [amp.shape for amp in amplitudes_list]
    n_runs_list = [s[0] for s in shapes]
    n_colors_list = [s[1] for s in shapes]
    n_voxels_list = [s[2] for s in shapes]

    # Check consistency
    issues = []

    # Check n_runs
    if len(set(n_runs_list)) > 1:
        issues.append(f"  ❌ INCONSISTENT n_runs across subjects: {dict(zip(subjects, n_runs_list))}")
    else:
        print(f"  ✓ n_runs consistent: {n_runs_list[0]}")

    # Check n_colors
    if len(set(n_colors_list)) > 1:
        issues.append(f"  ❌ INCONSISTENT n_colors across subjects: {dict(zip(subjects, n_colors_list))}")
    else:
        print(f"  ✓ n_colors consistent: {n_colors_list[0]}")

    # Check n_voxels (CRITICAL)
    if len(set(n_voxels_list)) > 1:
        issues.append(f"  ❌ INCONSISTENT n_voxels across subjects:")
        for subj, n_vox in zip(subjects, n_voxels_list):
            issues.append(f"       sub-{subj}: {n_vox} voxels")
        issues.append("")
        issues.append("  This is a CRITICAL error - cannot proceed with group analysis!")
        issues.append("  See docs/grouplevel_execution.md for solutions:")
        issues.append("    - Option 1 (Recommended): MNI coordinate intersection")
        issues.append("    - Option 2: Zero padding (not recommended)")
        issues.append("")
    else:
        print(f"  ✓ n_voxels consistent: {n_voxels_list[0]}")

    # Raise error if issues found
    if issues:
        error_msg = "\n".join(issues)
        raise ValueError(
            f"\n{'='*80}\n"
            f"DATA CONSISTENCY VALIDATION FAILED\n"
            f"{'='*80}\n"
            f"{error_msg}\n"
            f"{'='*80}\n"
        )

    print(f"  ✅ All dimensions consistent - safe to proceed!")


def load_all_subjects(subjects, roi, timestamp, dataset='deoblique_v2'):
    """
    Load amplitudes_z.npy from all subjects with SNR-based voxel selection

    This function handles dimension inconsistencies by selecting the top-K voxels
    from each subject based on SNR, where K = minimum voxel count across subjects.

    Returns:
        group_amplitudes: (n_subjects, n_runs, n_colors, k_voxels) array
        subject_info: List of dicts with subject info
    """
    print(f"\n{'='*80}")
    print(f"Loading data from {len(subjects)} subjects...")
    print(f"{'='*80}")

    amplitudes_raw_list = []
    voxel_snr_list = []
    subject_info = []

    # Step 1: Load all data
    for subject_id in subjects:
        try:
            amplitudes_z, voxel_snr, result_dir = load_subject_amplitudes(
                subject_id, roi, timestamp, dataset
            )

            amplitudes_raw_list.append(amplitudes_z)
            voxel_snr_list.append(voxel_snr)

            subject_info.append({
                'subject_id': subject_id,
                'result_dir': result_dir,
                'shape_raw': amplitudes_z.shape,
                'mean_snr': voxel_snr.mean()
            })
            print(f"  ✓ sub-{subject_id}: {amplitudes_z.shape}, mean_SNR={voxel_snr.mean():.2f}")
        except FileNotFoundError as e:
            print(f"  ✗ sub-{subject_id}: {e}")
            continue

    if len(amplitudes_raw_list) == 0:
        raise RuntimeError("No subject data loaded!")

    # Step 2: Determine K (minimum voxel count)
    voxel_counts = [amp.shape[2] for amp in amplitudes_raw_list]
    k = min(voxel_counts)

    print(f"\n{'='*80}")
    print(f"Voxel Selection Strategy: Top-{k} by SNR")
    print(f"{'='*80}")
    print(f"  Voxel counts: {dict(zip([info['subject_id'] for info in subject_info], voxel_counts))}")
    print(f"  Selecting top-{k} voxels from each subject based on SNR/R2")

    # Step 3: Select top-k voxels from each subject
    amplitudes_list = []
    for i, info in enumerate(subject_info):
        subject_id = info['subject_id']
        amplitudes_z = amplitudes_raw_list[i]
        voxel_snr = voxel_snr_list[i]

        amplitudes_selected, selected_indices = select_top_k_voxels_by_snr(
            amplitudes_z, voxel_snr, k
        )

        amplitudes_list.append(amplitudes_selected)

        # Update subject info
        info['shape_selected'] = amplitudes_selected.shape
        info['selected_indices'] = selected_indices
        info['selected_snr_mean'] = voxel_snr[selected_indices].mean()

        print(f"  sub-{subject_id}: {info['shape_raw']} -> {amplitudes_selected.shape}, "
              f"selected_SNR={info['selected_snr_mean']:.2f}")

    # Step 4: Validate consistency (should pass now!)
    validate_group_data_consistency(amplitudes_list, [info['subject_id'] for info in subject_info])

    # Step 5: Stack into group array
    group_amplitudes = np.array(amplitudes_list)  # (n_subjects, n_runs, n_colors, k)

    print(f"\n✅ Loaded {len(amplitudes_list)} subjects with top-{k} voxels")
    print(f"   Group shape: {group_amplitudes.shape}")
    print(f"   (subjects={group_amplitudes.shape[0]}, runs={group_amplitudes.shape[1]}, "
          f"colors={group_amplitudes.shape[2]}, voxels={group_amplitudes.shape[3]})")

    return group_amplitudes, subject_info


# ============================================================================
# Group-level Statistics
# ============================================================================

def compute_group_statistics(group_amplitudes):
    """
    Compute group-level statistics for each voxel and color

    Performs THREE types of statistical tests:
    1. Option A: One-sample t-test vs 0 (activation exists?)
    2. Option B-1: Each color vs other colors (color selectivity)
    3. Option B-2: Pairwise color contrasts (color discrimination)

    Args:
        group_amplitudes: (n_subjects, n_runs, n_colors, n_voxels) array

    Returns:
        stats_dict: Dictionary containing all test results
    """
    n_subjects, n_runs, n_colors, n_voxels = group_amplitudes.shape

    print(f"\n{'='*80}")
    print(f"Computing group-level statistics (3 types of tests)...")
    print(f"{'='*80}")

    # Average across runs for each subject
    amplitudes_avg = group_amplitudes.mean(axis=1)  # (n_subjects, n_colors, n_voxels)

    stats_dict = {}

    # ========================================================================
    # Option A: One-sample t-test vs 0
    # ========================================================================
    print(f"\n[Option A] One-sample t-test vs 0 (activation exists?)")

    t_values_vs0 = np.zeros((n_colors, n_voxels))
    p_values_vs0 = np.zeros((n_colors, n_voxels))

    for color_idx in range(n_colors):
        color_data = amplitudes_avg[:, color_idx, :]
        t_vals, p_vals = stats.ttest_1samp(color_data, 0, axis=0)
        t_values_vs0[color_idx, :] = t_vals
        p_values_vs0[color_idx, :] = p_vals

    stats_dict['vs_zero'] = {
        't_values': t_values_vs0,
        'p_values': p_values_vs0
    }

    print(f"  t-values range: [{t_values_vs0.min():.2f}, {t_values_vs0.max():.2f}]")

    # ========================================================================
    # Option B-1: Each color vs other colors (Color Selectivity)
    # ========================================================================
    print(f"\n[Option B-1] Each color vs others (color selectivity)")

    t_values_selectivity = np.zeros((n_colors, n_voxels))
    p_values_selectivity = np.zeros((n_colors, n_voxels))

    for color_idx in range(n_colors):
        # This color
        this_color = amplitudes_avg[:, color_idx, :]  # (n_subjects, n_voxels)

        # Other colors (average)
        other_colors_mask = np.ones(n_colors, dtype=bool)
        other_colors_mask[color_idx] = False
        other_colors = amplitudes_avg[:, other_colors_mask, :].mean(axis=1)  # (n_subjects, n_voxels)

        # Paired t-test
        t_vals, p_vals = stats.ttest_rel(this_color, other_colors, axis=0)

        t_values_selectivity[color_idx, :] = t_vals
        p_values_selectivity[color_idx, :] = p_vals

    stats_dict['selectivity'] = {
        't_values': t_values_selectivity,
        'p_values': p_values_selectivity
    }

    print(f"  t-values range: [{t_values_selectivity.min():.2f}, {t_values_selectivity.max():.2f}]")
    print(f"  Positive t-value = this color > others (selective)")

    # ========================================================================
    # Option B-2: Pairwise color contrasts (Color Discrimination)
    # ========================================================================
    print(f"\n[Option B-2] Pairwise color contrasts (color discrimination)")
    print(f"  Total comparisons: {n_colors}C2 = {n_colors * (n_colors - 1) // 2}")

    pairwise_contrasts = []

    for color1_idx in range(n_colors):
        for color2_idx in range(color1_idx + 1, n_colors):
            # Color 1 vs Color 2
            color1_data = amplitudes_avg[:, color1_idx, :]
            color2_data = amplitudes_avg[:, color2_idx, :]

            # Paired t-test
            t_vals, p_vals = stats.ttest_rel(color1_data, color2_data, axis=0)

            pairwise_contrasts.append({
                'color1': color1_idx,
                'color2': color2_idx,
                'pair_name': f'C{color1_idx+1}_vs_C{color2_idx+1}',
                't_values': t_vals,
                'p_values': p_vals
            })

    stats_dict['pairwise'] = pairwise_contrasts

    print(f"  Computed {len(pairwise_contrasts)} pairwise contrasts")
    print(f"  Example: C1 vs C2, C1 vs C3, ..., C7 vs C8")

    # ========================================================================
    # Summary
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Statistics Summary:")
    print(f"  Option A (vs 0): {n_colors} colors × {n_voxels} voxels = {n_colors * n_voxels} tests")
    print(f"  Option B-1 (selectivity): {n_colors} colors × {n_voxels} voxels = {n_colors * n_voxels} tests")
    print(f"  Option B-2 (pairwise): {len(pairwise_contrasts)} pairs × {n_voxels} voxels = {len(pairwise_contrasts) * n_voxels} tests")
    print(f"{'='*80}")

    return stats_dict


def apply_fdr_correction_to_stats(stats_dict, alpha=0.05):
    """
    Apply FDR correction to all statistical tests

    Args:
        stats_dict: Dictionary from compute_group_statistics()
        alpha: FDR alpha level

    Returns:
        corrected_stats: Dictionary with FDR-corrected results
    """
    corrected_stats = {}

    print(f"\n{'='*80}")
    print(f"FDR Correction (alpha={alpha})")
    print(f"{'='*80}")

    # Option A: vs zero
    print(f"\n[Option A] vs 0:")
    p_values = stats_dict['vs_zero']['p_values']
    n_colors, n_voxels = p_values.shape

    p_flat = p_values.flatten()
    reject, p_corrected_flat, _, _ = multipletests(p_flat, alpha=alpha, method='fdr_bh')

    significant_mask = reject.reshape((n_colors, n_voxels))
    p_corrected = p_corrected_flat.reshape((n_colors, n_voxels))

    corrected_stats['vs_zero'] = {
        't_values': stats_dict['vs_zero']['t_values'],
        'p_values': p_values,
        'p_corrected': p_corrected,
        'significant_mask': significant_mask
    }

    print(f"  Significant: {significant_mask.sum():,}/{n_colors * n_voxels:,} ({100*significant_mask.sum()/(n_colors*n_voxels):.2f}%)")

    # Option B-1: selectivity
    print(f"\n[Option B-1] Selectivity:")
    p_values = stats_dict['selectivity']['p_values']

    p_flat = p_values.flatten()
    reject, p_corrected_flat, _, _ = multipletests(p_flat, alpha=alpha, method='fdr_bh')

    significant_mask = reject.reshape((n_colors, n_voxels))
    p_corrected = p_corrected_flat.reshape((n_colors, n_voxels))

    corrected_stats['selectivity'] = {
        't_values': stats_dict['selectivity']['t_values'],
        'p_values': p_values,
        'p_corrected': p_corrected,
        'significant_mask': significant_mask
    }

    print(f"  Significant: {significant_mask.sum():,}/{n_colors * n_voxels:,} ({100*significant_mask.sum()/(n_colors*n_voxels):.2f}%)")

    # Option B-2: pairwise
    print(f"\n[Option B-2] Pairwise contrasts:")
    pairwise_corrected = []

    for contrast in stats_dict['pairwise']:
        p_values = contrast['p_values']

        reject, p_corrected, _, _ = multipletests(p_values, alpha=alpha, method='fdr_bh')

        pairwise_corrected.append({
            'color1': contrast['color1'],
            'color2': contrast['color2'],
            'pair_name': contrast['pair_name'],
            't_values': contrast['t_values'],
            'p_values': p_values,
            'p_corrected': p_corrected,
            'significant_mask': reject
        })

    corrected_stats['pairwise'] = pairwise_corrected

    # Summary for pairwise
    total_sig = sum([c['significant_mask'].sum() for c in pairwise_corrected])
    total_tests = len(pairwise_corrected) * n_voxels
    print(f"  Significant: {total_sig:,}/{total_tests:,} ({100*total_sig/total_tests:.2f}%)")

    return corrected_stats


def create_union_voxel_mask(corrected_stats, n_voxels):
    """
    Create union of significant voxels from all three test types

    Args:
        corrected_stats: Dictionary from apply_fdr_correction_to_stats()
        n_voxels: Total number of voxels

    Returns:
        union_mask: (n_voxels,) boolean array - union of all significant voxels
        breakdown: Dictionary with per-test-type masks
    """
    print(f"\n{'='*80}")
    print(f"Creating Union of Significant Voxels")
    print(f"{'='*80}")

    breakdown = {}

    # Option A: vs zero
    mask_vs_zero = corrected_stats['vs_zero']['significant_mask'].any(axis=0)  # (n_voxels,)
    breakdown['vs_zero'] = mask_vs_zero
    print(f"  Option A (vs 0): {mask_vs_zero.sum():,}/{n_voxels:,} voxels")

    # Option B-1: selectivity
    mask_selectivity = corrected_stats['selectivity']['significant_mask'].any(axis=0)
    breakdown['selectivity'] = mask_selectivity
    print(f"  Option B-1 (selectivity): {mask_selectivity.sum():,}/{n_voxels:,} voxels")

    # Option B-2: pairwise (union across all pairs)
    mask_pairwise = np.zeros(n_voxels, dtype=bool)
    for contrast in corrected_stats['pairwise']:
        mask_pairwise |= contrast['significant_mask']

    breakdown['pairwise'] = mask_pairwise
    print(f"  Option B-2 (pairwise): {mask_pairwise.sum():,}/{n_voxels:,} voxels")

    # Union
    union_mask = mask_vs_zero | mask_selectivity | mask_pairwise
    breakdown['union'] = union_mask

    print(f"\n  ✅ UNION: {union_mask.sum():,}/{n_voxels:,} voxels ({100*union_mask.sum()/n_voxels:.1f}%)")

    # Overlap analysis
    print(f"\n  Overlap analysis:")
    all_three = mask_vs_zero & mask_selectivity & mask_pairwise
    print(f"    All 3 methods: {all_three.sum():,} voxels")

    vs_zero_only = mask_vs_zero & ~mask_selectivity & ~mask_pairwise
    selectivity_only = ~mask_vs_zero & mask_selectivity & ~mask_pairwise
    pairwise_only = ~mask_vs_zero & ~mask_selectivity & mask_pairwise

    print(f"    vs_zero only: {vs_zero_only.sum():,} voxels")
    print(f"    selectivity only: {selectivity_only.sum():,} voxels")
    print(f"    pairwise only: {pairwise_only.sum():,} voxels")

    return union_mask, breakdown


# ============================================================================
# Visualization
# ============================================================================

def visualize_common_voxels_brain(common_voxel_mask, roi, roi_mask_path, output_dir):
    """
    Visualize common voxels in brain space

    Args:
        common_voxel_mask: (n_voxels,) boolean array
        roi: ROI name
        roi_mask_path: Path to ROI mask file
        output_dir: Output directory
    """
    try:
        # Load ROI mask
        if not Path(roi_mask_path).exists():
            print(f"  ⚠️  ROI mask not found: {roi_mask_path}")
            print(f"     Skipping brain visualization...")
            return None

        mask_img = nib.load(roi_mask_path)
        mask_data = mask_img.get_fdata()

        # Get voxel coordinates
        voxel_coords = np.argwhere(mask_data > 0)  # All voxels in mask

        # Create a new volume with selected voxels highlighted
        highlight_data = np.zeros_like(mask_data)

        for idx, is_selected in enumerate(common_voxel_mask):
            if is_selected and idx < len(voxel_coords):
                coord = voxel_coords[idx]
                highlight_data[coord[0], coord[1], coord[2]] = 1.0

        highlight_img = nib.Nifti1Image(highlight_data, mask_img.affine, mask_img.header)

        # Plot brain slices
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))

        # Axial view
        niplot.plot_stat_map(highlight_img, display_mode='z', cut_coords=5,
                            title=f'Common Voxels - Axial View',
                            axes=axes[0, 0], colorbar=True, cmap='hot',
                            threshold=0.1)

        # Sagittal view
        niplot.plot_stat_map(highlight_img, display_mode='x', cut_coords=5,
                            title=f'Common Voxels - Sagittal View',
                            axes=axes[0, 1], colorbar=True, cmap='hot',
                            threshold=0.1)

        # Coronal view
        niplot.plot_stat_map(highlight_img, display_mode='y', cut_coords=5,
                            title=f'Common Voxels - Coronal View',
                            axes=axes[1, 0], colorbar=True, cmap='hot',
                            threshold=0.1)

        # Glass brain
        niplot.plot_glass_brain(highlight_img,
                               title=f'Common Voxels - Glass Brain',
                               axes=axes[1, 1], colorbar=True, cmap='hot',
                               threshold=0.1)

        plt.suptitle(f'{roi}: Group-level Common Voxels (Significant Color Encoding)',
                     fontsize=16, fontweight='bold')
        plt.tight_layout()

        fig_path = output_dir / 'figures' / 'common_voxels_brain.png'
        plt.savefig(fig_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"  ✓ Brain visualization saved: {fig_path}")
        return fig_path

    except Exception as e:
        print(f"  ⚠️  Brain visualization failed: {e}")
        return None


def visualize_significance_distribution(p_values, significant_mask, fdr_alpha, output_dir):
    """
    Visualize p-value distribution and significance

    Args:
        p_values: (n_colors, n_voxels) array
        significant_mask: (n_colors, n_voxels) boolean array
        fdr_alpha: FDR alpha level
        output_dir: Output directory
    """
    n_colors, n_voxels = p_values.shape

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. P-value histogram (all)
    ax = axes[0, 0]
    p_flat = p_values.flatten()
    ax.hist(p_flat, bins=50, alpha=0.7, edgecolor='black')
    ax.axvline(fdr_alpha, color='r', linestyle='--', label=f'α={fdr_alpha}')
    ax.set_xlabel('P-value')
    ax.set_ylabel('Count')
    ax.set_title('P-value Distribution (All Tests)')
    ax.legend()

    # 2. -log10(p-value) histogram
    ax = axes[0, 1]
    log_p = -np.log10(p_flat + 1e-300)  # Avoid log(0)
    ax.hist(log_p, bins=50, alpha=0.7, edgecolor='black', color='orange')
    ax.axvline(-np.log10(fdr_alpha), color='r', linestyle='--', label=f'-log10({fdr_alpha})')
    ax.set_xlabel('-log10(P-value)')
    ax.set_ylabel('Count')
    ax.set_title('Significance Distribution')
    ax.legend()

    # 3. Per-color significance
    ax = axes[1, 0]
    n_sig_per_color = significant_mask.sum(axis=1)
    colors_names = [f'C{i+1}' for i in range(n_colors)]
    ax.bar(colors_names, n_sig_per_color, alpha=0.7, edgecolor='black')
    ax.set_xlabel('Color')
    ax.set_ylabel('Number of Significant Voxels')
    ax.set_title(f'Significant Voxels per Color (FDR α={fdr_alpha})')
    ax.grid(axis='y', alpha=0.3)

    # 4. Number of colors per voxel
    ax = axes[1, 1]
    n_colors_per_voxel = significant_mask.sum(axis=0)
    ax.hist(n_colors_per_voxel, bins=np.arange(0, n_colors+2)-0.5,
            alpha=0.7, edgecolor='black', color='green')
    ax.set_xlabel('Number of Colors with Significant Activation')
    ax.set_ylabel('Number of Voxels')
    ax.set_title('Distribution of Significance Across Colors')
    ax.set_xticks(range(n_colors+1))
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()

    fig_path = output_dir / 'figures' / 'significance_distribution.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Significance distribution saved: {fig_path}")
    return fig_path


def visualize_per_color_activation(group_amplitudes, common_voxel_mask, output_dir):
    """
    Visualize mean activation per color for common voxels

    Args:
        group_amplitudes: (n_subjects, n_runs, n_colors, n_voxels) array
        common_voxel_mask: (n_voxels,) boolean array
        output_dir: Output directory
    """
    n_subjects, n_runs, n_colors, n_voxels = group_amplitudes.shape

    # Extract common voxels
    amplitudes_common = group_amplitudes[:, :, :, common_voxel_mask]
    n_common_voxels = amplitudes_common.shape[3]

    # Average across runs and voxels
    amplitudes_avg = amplitudes_common.mean(axis=(1, 3))  # (n_subjects, n_colors)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 1. Mean activation per color (across subjects)
    ax = axes[0]
    mean_activation = amplitudes_avg.mean(axis=0)
    std_activation = amplitudes_avg.std(axis=0)
    colors_names = [f'C{i+1}' for i in range(n_colors)]

    ax.bar(colors_names, mean_activation, yerr=std_activation,
           alpha=0.7, edgecolor='black', capsize=5)
    ax.set_xlabel('Color')
    ax.set_ylabel('Mean Activation (z-scored)')
    ax.set_title(f'Mean Activation per Color\n(Common Voxels, N={n_common_voxels})')
    ax.axhline(0, color='gray', linestyle='--', linewidth=0.5)
    ax.grid(axis='y', alpha=0.3)

    # 2. Heatmap: subjects × colors
    ax = axes[1]
    im = ax.imshow(amplitudes_avg, aspect='auto', cmap='RdBu_r',
                   vmin=-1, vmax=1, interpolation='nearest')
    ax.set_xlabel('Color')
    ax.set_ylabel('Subject')
    ax.set_title('Activation Heatmap (Subjects × Colors)')
    ax.set_xticks(range(n_colors))
    ax.set_xticklabels(colors_names)
    ax.set_yticks(range(n_subjects))
    ax.set_yticklabels([f'S{i+1}' for i in range(n_subjects)])
    plt.colorbar(im, ax=ax, label='Z-scored Activation')

    plt.tight_layout()

    fig_path = output_dir / 'figures' / 'per_color_activation.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Per-color activation saved: {fig_path}")
    return fig_path


def visualize_voxel_color_heatmap(group_amplitudes, t_values, p_values, fdr_alpha, output_dir):
    """
    Visualize Voxel × Color activation heatmap with significance overlay

    이 함수는 FDR correction 결과와 무관하게 모든 voxel의 색별 activation을 보여줍니다.

    Args:
        group_amplitudes: (n_subjects, n_runs, n_colors, n_voxels) array
        t_values: (n_colors, n_voxels) array
        p_values: (n_colors, n_voxels) array (corrected)
        fdr_alpha: FDR alpha level
        output_dir: Output directory
    """
    n_subjects, n_runs, n_colors, n_voxels = group_amplitudes.shape

    # Compute group mean activation (average across subjects and runs)
    mean_activation = group_amplitudes.mean(axis=(0, 1))  # (n_colors, n_voxels)

    # Significance mask
    significant_mask = p_values < fdr_alpha

    print(f"\n  Creating Voxel × Color heatmap...")
    print(f"    Data shape: {n_colors} colors × {n_voxels} voxels")
    print(f"    Significant pairs: {significant_mask.sum()}/{n_colors * n_voxels}")

    # Create figure with two subplots
    fig, axes = plt.subplots(2, 1, figsize=(max(12, n_voxels * 0.3), 10))

    # 1. Mean activation heatmap
    ax = axes[0]
    im1 = ax.imshow(mean_activation, aspect='auto', cmap='RdBu_r',
                    vmin=-2, vmax=2, interpolation='nearest')
    ax.set_xlabel('Voxel Index')
    ax.set_ylabel('Color')
    ax.set_title(f'Group Mean Activation (Voxels × Colors)\n'
                 f'Averaged across {n_subjects} subjects, {n_runs} runs')
    ax.set_yticks(range(n_colors))
    ax.set_yticklabels([f'C{i+1}' for i in range(n_colors)])

    # Add grid
    ax.set_xticks(np.arange(n_voxels) - 0.5, minor=True)
    ax.set_yticks(np.arange(n_colors) - 0.5, minor=True)
    ax.grid(which='minor', color='gray', linestyle='-', linewidth=0.5, alpha=0.3)

    # Add significance markers
    for color_idx in range(n_colors):
        for voxel_idx in range(n_voxels):
            if significant_mask[color_idx, voxel_idx]:
                ax.plot(voxel_idx, color_idx, 'k*', markersize=4, alpha=0.6)

    plt.colorbar(im1, ax=ax, label='Z-scored Activation')

    # 2. T-values heatmap
    ax = axes[1]
    im2 = ax.imshow(t_values, aspect='auto', cmap='RdBu_r',
                    vmin=-5, vmax=5, interpolation='nearest')
    ax.set_xlabel('Voxel Index')
    ax.set_ylabel('Color')
    ax.set_title(f'T-values (One-sample t-test vs 0)\n'
                 f'Stars (*) indicate FDR-corrected significance (α={fdr_alpha})')
    ax.set_yticks(range(n_colors))
    ax.set_yticklabels([f'C{i+1}' for i in range(n_colors)])

    # Add grid
    ax.set_xticks(np.arange(n_voxels) - 0.5, minor=True)
    ax.set_yticks(np.arange(n_colors) - 0.5, minor=True)
    ax.grid(which='minor', color='gray', linestyle='-', linewidth=0.5, alpha=0.3)

    # Add significance markers
    for color_idx in range(n_colors):
        for voxel_idx in range(n_voxels):
            if significant_mask[color_idx, voxel_idx]:
                ax.plot(voxel_idx, color_idx, 'k*', markersize=4, alpha=0.6)

    plt.colorbar(im2, ax=ax, label='T-value')

    plt.tight_layout()

    fig_path = output_dir / 'figures' / 'voxel_color_heatmap.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Voxel × Color heatmap saved: {fig_path}")

    # Save numerical data
    np.savez(
        output_dir / 'voxel_color_activation.npz',
        mean_activation=mean_activation,
        t_values=t_values,
        significant_mask=significant_mask,
        color_labels=[f'C{i+1}' for i in range(n_colors)]
    )

    return fig_path


# ============================================================================
# Main
# ============================================================================

def main():
    args = parse_args()

    print(f"\n{'='*80}")
    print(f"Group-level Common Voxel Identification")
    print(f"{'='*80}")
    print(f"ROI: {args.roi}")
    print(f"Dataset: {args.dataset}")
    print(f"Timestamp: {args.timestamp}")
    print(f"Subjects: {', '.join(args.subjects)} ({len(args.subjects)} subjects)")
    print(f"FDR alpha: {args.fdr_alpha}")
    print(f"Min colors: {args.min_colors}")

    # Output directory
    if args.output_dir is None:
        output_dir = Path(f"derivatives/group_level/{args.timestamp}/{args.roi}/common_voxels")
    else:
        output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'figures').mkdir(exist_ok=True)

    print(f"Output directory: {output_dir}")

    # ========================================================================
    # Load data
    # ========================================================================
    group_amplitudes, subject_info = load_all_subjects(
        args.subjects, args.roi, args.timestamp, args.dataset
    )

    # ========================================================================
    # Compute group-level statistics
    # ========================================================================
    t_values, p_values = compute_group_statistics(group_amplitudes)

    # ========================================================================
    # Apply FDR correction
    # ========================================================================
    significant_mask, p_values_corrected = apply_fdr_correction(
        p_values, alpha=args.fdr_alpha
    )

    # ========================================================================
    # Select common voxels
    # ========================================================================
    common_voxel_mask, n_colors_per_voxel = select_common_voxels(
        significant_mask, min_colors=args.min_colors
    )

    common_voxel_indices = np.where(common_voxel_mask)[0]

    # ========================================================================
    # Save results
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Saving results...")
    print(f"{'='*80}")

    # Save arrays
    np.save(output_dir / 'group_amplitudes_z.npy', group_amplitudes)
    np.savez(output_dir / 'group_statistics.npz',
             t_values=t_values,
             p_values=p_values,
             p_values_corrected=p_values_corrected,
             significant_mask=significant_mask)
    np.save(output_dir / 'significant_voxels.npy', common_voxel_mask)
    np.save(output_dir / 'significant_voxel_indices.npy', common_voxel_indices)
    np.save(output_dir / 'n_colors_per_voxel.npy', n_colors_per_voxel)

    print(f"  ✓ Arrays saved")

    # Save summary CSV
    n_colors, n_voxels = t_values.shape
    summary_data = []

    for color_idx in range(n_colors):
        n_sig = significant_mask[color_idx, :].sum()
        mean_t = t_values[color_idx, common_voxel_mask].mean() if n_sig > 0 else 0

        summary_data.append({
            'color': f'color_{color_idx+1}',
            'n_significant_voxels': n_sig,
            'percent_significant': 100 * n_sig / n_voxels,
            'mean_t_value': mean_t
        })

    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(output_dir / 'group_statistics_summary.csv', index=False)

    print(f"  ✓ Summary CSV saved")
    print(f"\n{summary_df.to_string(index=False)}")

    # ========================================================================
    # Visualizations
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Creating visualizations...")
    print(f"{'='*80}")

    # Get ROI mask path (from first subject)
    first_subject = args.subjects[0]
    roi_mask_candidates = [
        f'derivatives/sub-{first_subject}/roi_pipeline/{args.roi}_mask_thr50_intnearest_binTrue_masknone_gmTrue_subjFalse.nii.gz',
        f'derivatives/BH2009_{args.dataset}/{args.timestamp}/sub-{first_subject}_{args.roi}_mask.nii.gz',
        f'derivatives/roi_masks/sub-{first_subject}_{args.roi}_mask.nii.gz'
    ]

    roi_mask_path = None
    for candidate in roi_mask_candidates:
        if Path(candidate).exists():
            roi_mask_path = candidate
            break

    if roi_mask_path:
        visualize_common_voxels_brain(
            common_voxel_mask, args.roi, roi_mask_path, output_dir
        )
    else:
        print(f"  ⚠️  ROI mask not found, skipping brain visualization")

    visualize_significance_distribution(
        p_values, significant_mask, args.fdr_alpha, output_dir
    )

    # NEW: Voxel × Color heatmap (shows ALL voxels, even if not significant)
    visualize_voxel_color_heatmap(
        group_amplitudes, t_values, p_values_corrected, args.fdr_alpha, output_dir
    )

    # Per-color activation (only for common voxels)
    if common_voxel_mask.sum() > 0:
        visualize_per_color_activation(
            group_amplitudes, common_voxel_mask, output_dir
        )
    else:
        print(f"  ⚠️  No common voxels selected, skipping per-color activation plot")

    # ========================================================================
    # Final summary
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Group-level Common Voxel Analysis Complete!")
    print(f"{'='*80}")
    print(f"Results saved to: {output_dir}")
    print(f"\nKey results:")
    print(f"  - Total voxels: {n_voxels:,}")
    print(f"  - Common voxels: {len(common_voxel_indices):,} "
          f"({100*len(common_voxel_indices)/n_voxels:.2f}%)")
    print(f"  - Subjects: {len(args.subjects)}")
    print(f"  - FDR alpha: {args.fdr_alpha}")
    print(f"  - Min colors: {args.min_colors}")
    print(f"\nNext steps:")
    print(f"  1. Run ANOVA feature selection on common voxels:")
    print(f"     python group_level_anova_selection.py --roi {args.roi} --timestamp {args.timestamp}")
    print(f"  2. Run RFE feature selection on common voxels:")
    print(f"     python group_level_rfe_selection.py --roi {args.roi} --timestamp {args.timestamp}")
    print(f"  3. Run PCA with high-loading voxel visualization:")
    print(f"     python group_level_pca_analysis.py --roi {args.roi} --timestamp {args.timestamp}")


if __name__ == '__main__':
    main()
