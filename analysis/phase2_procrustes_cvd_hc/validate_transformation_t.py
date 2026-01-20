#!/usr/bin/env python3
"""
Validate Transformation T: CVD Correction Effectiveness
======================================================

Goal: Test if T = CVD_mean - HC_mean can correct individual CVD subjects

Strategy:
    1. Load HC_mean and T (CVD common difference) from Option 2D results
    2. For each individual CVD subject:
       - Load original pattern
       - Apply correction: CVD_corrected = CVD_original - T
       - Measure distance to HC_mean before and after
    3. Calculate improvement metrics:
       - Distance reduction (%)
       - Correlation improvement
       - Color-specific improvements

Expected Result:
    - If T is valid: >80% distance reduction
    - If T works: CVD_corrected patterns should cluster near HC_mean
    - Color-specific: Largest improvement for colors with largest T
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from scipy.stats import spearmanr
from scipy.spatial import procrustes

# Paths (auto-detect local vs server)
import os
import sys

if os.path.exists('/scratch/connectome'):
    # Server environment
    BASE_DIR = Path('/scratch/connectome/haba6030/colorBlind')
    BASELINE_DIR = BASE_DIR / 'results' / 'baseline_individual_results' / 'baseline81_deob_determin'
else:
    # Local environment
    BASE_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
    BASELINE_DIR = None  # Will need to download data first

RESULTS_DIR = BASE_DIR / 'analysis' / 'comprehensive' / 'results' / 'baseline81_deob_determin'
OUTPUT_DIR = BASE_DIR / 'analysis' / 'comprehensive' / 'results' / 'transformation_validation'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Subject info (matching Option 2D analysis)
HC_SUBJECTS = ['02', '03', '05', '06', '07']  # 5 HC subjects used in Option 2D
CVD_SUBJECTS = ['08', '09', '10']  # 3 CVD subjects
ROIS = ['V1', 'V2']

def load_subject_pattern(subject_id, roi):
    """Load individual subject's pattern from baseline analysis"""
    if BASELINE_DIR is None:
        print(f"❌ Error: BASELINE_DIR not set. Run this script on the server.")
        return None

    # Path pattern: baseline81_deob_determin/sub-{ID}/{ROI}/amplitudes_z.npy
    amplitudes_file = BASELINE_DIR / f'sub-{subject_id}' / roi / 'amplitudes_z.npy'

    if not amplitudes_file.exists():
        print(f"⚠️  File not found: {amplitudes_file}")
        return None

    # Load and average across runs
    amplitudes = np.load(amplitudes_file)  # (n_runs, 8, n_voxels)
    pattern = amplitudes.mean(axis=0)  # (8, n_voxels)

    return pattern

def align_to_reference(pattern, reference):
    """Align pattern to reference using Procrustes"""
    if pattern is None or reference is None:
        return None

    # Ensure same voxel count
    n_voxels = min(pattern.shape[1], reference.shape[1])
    pattern = pattern[:, :n_voxels]
    reference = reference[:, :n_voxels]

    mtx1, mtx2, disparity = procrustes(reference.T, pattern.T)
    return mtx2.T, disparity

def compute_distance_metrics(pattern1, pattern2):
    """Compute multiple distance metrics between two patterns"""
    # RMS distance
    rms = np.sqrt(np.mean((pattern1 - pattern2) ** 2))

    # Correlation
    corr_per_color = []
    for c in range(8):
        r, _ = spearmanr(pattern1[c], pattern2[c])
        corr_per_color.append(r)
    mean_corr = np.mean(corr_per_color)

    # Color-specific RMS
    color_rms = []
    for c in range(8):
        rms_c = np.sqrt(np.mean((pattern1[c] - pattern2[c]) ** 2))
        color_rms.append(rms_c)

    return {
        'rms': rms,
        'correlation': mean_corr,
        'color_rms': np.array(color_rms),
        'color_correlations': np.array(corr_per_color)
    }

def validate_transformation(roi):
    """Validate transformation T for a given ROI"""
    print(f"\n{'='*60}")
    print(f"Validating Transformation T for {roi}")
    print(f"{'='*60}\n")

    # Load HC mean and T from Option 2D results
    roi_dir = RESULTS_DIR / roi
    hc_mean = np.load(roi_dir / 'hc_mean_option_a.npy')
    T = np.load(roi_dir / 'cvd_common_diff_option_a.npy')

    print(f"✓ Loaded HC mean: {hc_mean.shape}")
    print(f"✓ Loaded T (CVD systematic difference): {T.shape}")
    print(f"✓ T magnitude (RMS): {np.sqrt(np.mean(T**2)):.4f}")

    # Load reference subject (sub-02) for alignment
    reference = load_subject_pattern('02', roi)
    if reference is None:
        print(f"❌ Failed to load reference subject")
        return None

    n_voxels = hc_mean.shape[1]
    reference = reference[:, :n_voxels]
    print(f"✓ Reference (sub-02): {reference.shape}\n")

    # Validate for each CVD subject
    results = []

    for cvd_id in CVD_SUBJECTS:
        print(f"\n--- CVD Subject {cvd_id} ---")

        # Load original CVD pattern
        cvd_original = load_subject_pattern(cvd_id, roi)
        if cvd_original is None:
            print(f"⚠️  Skipping subject {cvd_id}")
            continue

        # Align to reference
        cvd_aligned, disparity = align_to_reference(cvd_original, reference)
        print(f"✓ Loaded and aligned: {cvd_aligned.shape}")
        print(f"  Procrustes disparity: {disparity:.4f}")

        # Measure distance BEFORE correction
        metrics_before = compute_distance_metrics(cvd_aligned, hc_mean)
        print(f"\n📊 Before Correction:")
        print(f"  RMS distance to HC: {metrics_before['rms']:.4f}")
        print(f"  Mean correlation: {metrics_before['correlation']:.4f}")

        # Apply correction: CVD_corrected = CVD_original - T
        cvd_corrected = cvd_aligned - T

        # Measure distance AFTER correction
        metrics_after = compute_distance_metrics(cvd_corrected, hc_mean)
        print(f"\n📊 After Correction:")
        print(f"  RMS distance to HC: {metrics_after['rms']:.4f}")
        print(f"  Mean correlation: {metrics_after['correlation']:.4f}")

        # Calculate improvement
        rms_reduction = (metrics_before['rms'] - metrics_after['rms']) / metrics_before['rms'] * 100
        corr_improvement = metrics_after['correlation'] - metrics_before['correlation']

        print(f"\n✅ Improvement:")
        print(f"  RMS reduction: {rms_reduction:.1f}%")
        print(f"  Correlation gain: {corr_improvement:+.4f}")

        # Store results
        results.append({
            'subject': cvd_id,
            'roi': roi,
            'rms_before': metrics_before['rms'],
            'rms_after': metrics_after['rms'],
            'rms_reduction_%': rms_reduction,
            'corr_before': metrics_before['correlation'],
            'corr_after': metrics_after['correlation'],
            'corr_improvement': corr_improvement,
            'color_rms_before': metrics_before['color_rms'],
            'color_rms_after': metrics_after['color_rms'],
            'color_corr_before': metrics_before['color_correlations'],
            'color_corr_after': metrics_after['color_correlations']
        })

    return results, hc_mean, T

def visualize_validation_results(results, roi):
    """Create comprehensive visualization of validation results"""
    n_subjects = len(results)

    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f'Transformation T Validation - {roi}', fontsize=16, fontweight='bold')

    subjects = [r['subject'] for r in results]

    # 1. RMS Distance Comparison
    ax = axes[0, 0]
    x = np.arange(n_subjects)
    width = 0.35

    rms_before = [r['rms_before'] for r in results]
    rms_after = [r['rms_after'] for r in results]

    bars1 = ax.bar(x - width/2, rms_before, width, label='Before Correction', color='#e74c3c')
    bars2 = ax.bar(x + width/2, rms_after, width, label='After Correction', color='#27ae60')

    ax.set_xlabel('CVD Subject')
    ax.set_ylabel('RMS Distance to HC Mean')
    ax.set_title('RMS Distance Reduction')
    ax.set_xticks(x)
    ax.set_xticklabels([f'sub-{s}' for s in subjects])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # 2. RMS Reduction Percentage
    ax = axes[0, 1]
    reductions = [r['rms_reduction_%'] for r in results]
    bars = ax.bar(x, reductions, color='#3498db')
    ax.axhline(y=80, color='green', linestyle='--', linewidth=2, label='Target (80%)')
    ax.axhline(y=50, color='orange', linestyle='--', linewidth=2, label='Moderate (50%)')

    ax.set_xlabel('CVD Subject')
    ax.set_ylabel('RMS Reduction (%)')
    ax.set_title('Correction Effectiveness')
    ax.set_xticks(x)
    ax.set_xticklabels([f'sub-{s}' for s in subjects])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, reductions)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')

    # 3. Correlation Improvement
    ax = axes[0, 2]
    corr_before = [r['corr_before'] for r in results]
    corr_after = [r['corr_after'] for r in results]

    bars1 = ax.bar(x - width/2, corr_before, width, label='Before', color='#e74c3c')
    bars2 = ax.bar(x + width/2, corr_after, width, label='After', color='#27ae60')

    ax.set_xlabel('CVD Subject')
    ax.set_ylabel('Mean Correlation with HC')
    ax.set_title('Correlation Improvement')
    ax.set_xticks(x)
    ax.set_xticklabels([f'sub-{s}' for s in subjects])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # 4. Color-specific RMS (Heatmap Before)
    ax = axes[1, 0]
    color_rms_before = np.array([r['color_rms_before'] for r in results])
    sns.heatmap(color_rms_before.T, annot=True, fmt='.3f', cmap='Reds',
                xticklabels=[f'sub-{s}' for s in subjects],
                yticklabels=[f'Color {i}' for i in range(8)],
                ax=ax, cbar_kws={'label': 'RMS Distance'})
    ax.set_title('Color-specific RMS (Before Correction)')
    ax.set_xlabel('CVD Subject')
    ax.set_ylabel('Color')

    # 5. Color-specific RMS (Heatmap After)
    ax = axes[1, 1]
    color_rms_after = np.array([r['color_rms_after'] for r in results])
    sns.heatmap(color_rms_after.T, annot=True, fmt='.3f', cmap='Greens',
                xticklabels=[f'sub-{s}' for s in subjects],
                yticklabels=[f'Color {i}' for i in range(8)],
                ax=ax, cbar_kws={'label': 'RMS Distance'})
    ax.set_title('Color-specific RMS (After Correction)')
    ax.set_xlabel('CVD Subject')
    ax.set_ylabel('Color')

    # 6. Color-specific Reduction
    ax = axes[1, 2]
    color_reduction = (color_rms_before - color_rms_after) / color_rms_before * 100
    color_reduction_mean = color_reduction.mean(axis=0)

    bars = ax.bar(range(8), color_reduction_mean, color='#9b59b6')
    ax.axhline(y=80, color='green', linestyle='--', linewidth=2, alpha=0.5)
    ax.set_xlabel('Color')
    ax.set_ylabel('Mean RMS Reduction (%)')
    ax.set_title('Color-specific Correction Effectiveness')
    ax.set_xticks(range(8))
    ax.set_xticklabels([f'C{i}' for i in range(8)])
    ax.grid(axis='y', alpha=0.3)

    # Add value labels
    for bar, val in zip(bars, color_reduction_mean):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.0f}%', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()

    # Save figure
    output_file = OUTPUT_DIR / f'transformation_validation_{roi}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Saved visualization: {output_file}")
    plt.close()

def main():
    """Main validation workflow"""
    print("\n" + "="*60)
    print("TRANSFORMATION T VALIDATION")
    print("="*60)
    print("\nGoal: Validate that T = CVD_mean - HC_mean can correct CVD patterns")
    print("\nSuccess Criteria:")
    print("  ✓ RMS reduction > 80%: Excellent")
    print("  ✓ RMS reduction > 50%: Moderate")
    print("  ✗ RMS reduction < 50%: Insufficient")

    all_results = []

    for roi in ROIS:
        results, hc_mean, T = validate_transformation(roi)

        if results:
            # Create visualizations
            visualize_validation_results(results, roi)

            # Save numerical results
            df = pd.DataFrame([{
                'subject': r['subject'],
                'roi': r['roi'],
                'rms_before': r['rms_before'],
                'rms_after': r['rms_after'],
                'rms_reduction_%': r['rms_reduction_%'],
                'corr_before': r['corr_before'],
                'corr_after': r['corr_after'],
                'corr_improvement': r['corr_improvement']
            } for r in results])

            output_file = OUTPUT_DIR / f'validation_results_{roi}.csv'
            df.to_csv(output_file, index=False)
            print(f"✓ Saved results: {output_file}")

            all_results.extend(results)

    # Summary across all ROIs
    if all_results:
        print("\n" + "="*60)
        print("SUMMARY ACROSS ALL ROIS")
        print("="*60)

        mean_reduction = np.mean([r['rms_reduction_%'] for r in all_results])
        mean_corr_gain = np.mean([r['corr_improvement'] for r in all_results])

        print(f"\nMean RMS reduction: {mean_reduction:.1f}%")
        print(f"Mean correlation gain: {mean_corr_gain:+.4f}")

        if mean_reduction > 80:
            print("\n✅ SUCCESS: Transformation T is highly effective!")
        elif mean_reduction > 50:
            print("\n⚠️  MODERATE: Transformation T shows partial effectiveness")
        else:
            print("\n❌ INSUFFICIENT: Transformation T needs revision")

        # Save combined summary
        df_all = pd.DataFrame([{
            'subject': r['subject'],
            'roi': r['roi'],
            'rms_before': r['rms_before'],
            'rms_after': r['rms_after'],
            'rms_reduction_%': r['rms_reduction_%'],
            'corr_before': r['corr_before'],
            'corr_after': r['corr_after'],
            'corr_improvement': r['corr_improvement']
        } for r in all_results])

        output_file = OUTPUT_DIR / 'validation_results_all.csv'
        df_all.to_csv(output_file, index=False)
        print(f"\n✓ Saved combined results: {output_file}")

if __name__ == '__main__':
    main()
