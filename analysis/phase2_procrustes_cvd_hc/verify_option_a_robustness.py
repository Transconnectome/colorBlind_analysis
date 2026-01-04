#!/usr/bin/env python3
"""
Option A 방법론 검증: Reference Robustness & Statistical Tests
============================================================

목적:
1. Reference subject 선택이 결과에 영향 주는지 확인
2. Permutation test로 HC vs CVD 차이가 real인지 검증
3. Systematic difference 시각화

검증 항목:
- Reference bias: 5명의 HC를 각각 reference로 사용했을 때 일관성
- Statistical significance: Permutation test로 p-value 계산
- Consistency: CVD 3명이 정말 일관된 패턴을 보이는지
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.spatial import procrustes
from scipy.stats import spearmanr
import matplotlib.gridspec as gridspec
import json

# Paths (auto-detect server vs local)
import os
if os.path.exists('/scratch/connectome'):
    # Server
    BASE_DIR = Path('/scratch/connectome/haba6030/colorBlind')
    DATASET_DIR = BASE_DIR / 'derivatives'
else:
    # Local
    BASE_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
    DATASET_DIR = None

RESULTS_DIR = BASE_DIR / 'results/group_level/baseline81_deob_determin'
OUTPUT_DIR = BASE_DIR / 'results/group_level/option_a_verification'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Subject info
HC_SUBJECTS = ['02', '03', '05', '06', '07']
CVD_SUBJECTS = ['08', '09', '10']
ROIS = ['V1', 'V2']

# 8 colors used in the experiment (0-315° in 45° steps)
COLOR_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Lime', 'Cyan', 'Blue', 'Purple', 'Magenta']


def load_subject_amplitudes(subject_id, roi, timestamp='baseline81_deob_determin', dataset='deoblique_v2'):
    """피험자 데이터 로드 (Option 2D와 동일한 방식)"""
    if not os.path.exists('/scratch/connectome'):
        raise RuntimeError("Run this script on the server!")

    base_dir = Path('/scratch/connectome/haba6030/colorBlind')
    dataset_dir = base_dir / 'derivatives' / f'BH2009_{dataset}' / timestamp

    # Use glob pattern to find subject directory
    pattern = f'*_sub-{subject_id}_{roi}_*'
    matches = sorted(dataset_dir.glob(pattern))

    if len(matches) == 0:
        raise FileNotFoundError(f"No data found for sub-{subject_id}, ROI {roi} at {dataset_dir}")

    result_dir = matches[0]
    amp_file = result_dir / 'amplitudes_z.npy'

    if not amp_file.exists():
        raise FileNotFoundError(f"amplitudes_z.npy not found in {result_dir}")

    amplitudes = np.load(amp_file)  # (n_runs, 8, n_voxels)

    # Average across runs
    pattern = amplitudes.mean(axis=0)  # (8, n_voxels)

    return pattern


def load_all_subjects(subjects, roi, timestamp='baseline81_deob_determin', dataset='deoblique_v2'):
    """모든 피험자 데이터 로드 (Option 2D와 동일한 방식)"""
    print(f"Loading {roi} data for {len(subjects)} subjects...")

    patterns = []

    for subject_id in subjects:
        try:
            pattern = load_subject_amplitudes(subject_id, roi, timestamp, dataset)
            patterns.append(pattern)
            print(f"  sub-{subject_id}: {pattern.shape}")
        except FileNotFoundError as e:
            print(f"  sub-{subject_id}: ⚠️ {e}")
            continue

    if len(patterns) == 0:
        raise RuntimeError(f"No subjects loaded for {roi}")

    # Unify voxel count
    n_voxels_min = min([p.shape[1] for p in patterns])
    patterns = [p[:, :n_voxels_min] for p in patterns]

    patterns = np.array(patterns)  # (n_subjects, 8, n_voxels)
    print(f"✓ Loaded {patterns.shape[0]} subjects, unified to {n_voxels_min} voxels")

    return patterns


def option_a_with_custom_reference(hc_patterns, cvd_patterns, ref_idx):
    """
    Run Option A with specific reference subject

    Args:
        hc_patterns: (n_hc, 8, n_voxels) HC patterns
        cvd_patterns: (n_cvd, 8, n_voxels) CVD patterns
        ref_idx: Index of reference subject (0-4)

    Returns:
        T: Systematic difference (8, n_voxels)
        hc_mean: HC mean pattern (8, n_voxels)
        cvd_mean: CVD mean pattern (8, n_voxels)
        hc_disparities: Procrustes disparities for HC subjects
        cvd_disparities: Procrustes disparities for CVD subjects
    """
    n_hc, n_colors, n_voxels = hc_patterns.shape
    n_cvd = cvd_patterns.shape[0]

    reference = hc_patterns[ref_idx]

    # Align HC subjects to reference
    hc_aligned = [reference]
    hc_disparities = [0.0]  # Reference has 0 disparity

    for i, pattern in enumerate(hc_patterns):
        if i == ref_idx:
            continue
        mtx1, mtx2, disparity = procrustes(reference.T, pattern.T)
        hc_aligned.append(mtx2.T)
        hc_disparities.append(disparity)

    hc_mean = np.mean(hc_aligned, axis=0)

    # Align CVD subjects to reference
    cvd_aligned = []
    cvd_disparities = []

    for pattern in cvd_patterns:
        mtx1, mtx2, disparity = procrustes(reference.T, pattern.T)
        cvd_aligned.append(mtx2.T)
        cvd_disparities.append(disparity)

    cvd_mean = np.mean(cvd_aligned, axis=0)

    # Calculate systematic difference
    T = cvd_mean - hc_mean

    return T, hc_mean, cvd_mean, np.array(hc_disparities), np.array(cvd_disparities)


def test_reference_robustness(hc_patterns, cvd_patterns, roi):
    """Test if reference choice affects results"""
    print(f"\n{'='*60}")
    print(f"Testing Reference Robustness - {roi}")
    print(f"{'='*60}\n")

    n_hc = len(HC_SUBJECTS)
    results = []

    T_all = []

    for ref_idx in range(n_hc):
        ref_subj = HC_SUBJECTS[ref_idx]
        print(f"\n--- Reference: sub-{ref_subj} (index {ref_idx}) ---")

        T, hc_mean, cvd_mean, hc_disp, cvd_disp = option_a_with_custom_reference(
            hc_patterns, cvd_patterns, ref_idx
        )

        # Calculate metrics
        T_rms = np.sqrt(np.mean(T ** 2))
        hc_disp_mean = np.mean(hc_disp[hc_disp > 0])  # Exclude reference (0)
        cvd_disp_mean = np.mean(cvd_disp)

        # Color-specific RMS
        color_rms = np.sqrt(np.mean(T ** 2, axis=1))

        print(f"  T magnitude (RMS): {T_rms:.4f}")
        print(f"  HC mean disparity: {hc_disp_mean:.4f}")
        print(f"  CVD mean disparity: {cvd_disp_mean:.4f}")
        print(f"  Color RMS range: {color_rms.min():.4f} - {color_rms.max():.4f}")

        results.append({
            'reference': ref_subj,
            'ref_idx': ref_idx,
            'T_rms': T_rms,
            'hc_disparity_mean': hc_disp_mean,
            'cvd_disparity_mean': cvd_disp_mean,
            'color_rms': color_rms
        })

        T_all.append(T)

    # Analyze consistency across references
    T_all = np.array(T_all)  # (5_refs, 8_colors, n_voxels)
    T_std = np.std(T_all, axis=0)  # (8, n_voxels)
    T_mean = np.mean(T_all, axis=0)

    T_rms_all = [r['T_rms'] for r in results]
    T_rms_mean = np.mean(T_rms_all)
    T_rms_std = np.std(T_rms_all)

    print(f"\n{'='*60}")
    print(f"Reference Robustness Summary")
    print(f"{'='*60}")
    print(f"T RMS across references:")
    print(f"  Mean: {T_rms_mean:.4f}")
    print(f"  Std:  {T_rms_std:.4f}")
    print(f"  CV:   {T_rms_std/T_rms_mean*100:.1f}%")

    if T_rms_std / T_rms_mean < 0.15:
        print(f"\n✅ ROBUST: Reference choice는 결과에 큰 영향 없음 (CV < 15%)")
    elif T_rms_std / T_rms_mean < 0.30:
        print(f"\n⚠️  MODERATE: Reference choice가 약간 영향 줌 (15% < CV < 30%)")
    else:
        print(f"\n🚨 SENSITIVE: Reference choice가 결과에 큰 영향 (CV > 30%)")

    return results, T_all, T_mean, T_std


def permutation_test(hc_patterns, cvd_patterns, roi, n_perm=10000):
    """
    Permutation test: HC vs CVD 차이가 우연인지 검증

    Null hypothesis: HC와 CVD에 차이 없음 (라벨만 다름)
    """
    print(f"\n{'='*60}")
    print(f"Permutation Test - {roi}")
    print(f"{'='*60}\n")

    n_hc = hc_patterns.shape[0]
    n_cvd = cvd_patterns.shape[0]
    n_total = n_hc + n_cvd

    # Observed T (using sub-02 as reference, index 0)
    T_obs, _, _, _, _ = option_a_with_custom_reference(hc_patterns, cvd_patterns, ref_idx=0)
    T_obs_rms = np.sqrt(np.mean(T_obs ** 2))

    print(f"Observed T RMS: {T_obs_rms:.4f}")
    print(f"Running {n_perm} permutations...")

    # Combine all subjects
    all_patterns = np.concatenate([hc_patterns, cvd_patterns], axis=0)

    T_null_rms = []

    for i in range(n_perm):
        if (i + 1) % 1000 == 0:
            print(f"  Progress: {i+1}/{n_perm}")

        # Shuffle labels
        shuffled_idx = np.random.permutation(n_total)
        pseudo_hc = all_patterns[shuffled_idx[:n_hc]]
        pseudo_cvd = all_patterns[shuffled_idx[n_hc:]]

        # Calculate pseudo T
        T_null, _, _, _, _ = option_a_with_custom_reference(pseudo_hc, pseudo_cvd, ref_idx=0)
        T_null_rms.append(np.sqrt(np.mean(T_null ** 2)))

    T_null_rms = np.array(T_null_rms)

    # Calculate p-value
    p_value = np.sum(T_null_rms >= T_obs_rms) / n_perm

    print(f"\n{'='*60}")
    print(f"Permutation Test Results")
    print(f"{'='*60}")
    print(f"Observed T RMS: {T_obs_rms:.4f}")
    print(f"Null mean: {T_null_rms.mean():.4f}")
    print(f"Null std:  {T_null_rms.std():.4f}")
    print(f"p-value: {p_value:.4f}")

    if p_value < 0.001:
        print(f"\n✅ HIGHLY SIGNIFICANT: HC vs CVD 차이는 real (p < 0.001)")
    elif p_value < 0.05:
        print(f"\n✅ SIGNIFICANT: HC vs CVD 차이는 real (p < 0.05)")
    else:
        print(f"\n⚠️  NOT SIGNIFICANT: 우연일 수 있음 (p >= 0.05)")

    return T_obs_rms, T_null_rms, p_value


def visualize_reference_robustness(results, T_all, T_mean, T_std, roi):
    """Visualize reference robustness results"""
    fig = plt.figure(figsize=(20, 12))
    gs = gridspec.GridSpec(3, 4, hspace=0.3, wspace=0.3)

    fig.suptitle(f'Reference Robustness Analysis - {roi}',
                 fontsize=16, fontweight='bold', y=0.995)

    # 1. T RMS across references (Bar plot)
    ax1 = fig.add_subplot(gs[0, :2])
    refs = [r['reference'] for r in results]
    T_rms_vals = [r['T_rms'] for r in results]

    bars = ax1.bar(range(len(refs)), T_rms_vals, color='steelblue', alpha=0.7)
    ax1.axhline(y=np.mean(T_rms_vals), color='red', linestyle='--',
                linewidth=2, label=f'Mean: {np.mean(T_rms_vals):.4f}')
    ax1.set_xlabel('Reference Subject', fontsize=12)
    ax1.set_ylabel('T Magnitude (RMS)', fontsize=12)
    ax1.set_title('T Magnitude across Different References', fontsize=13, fontweight='bold')
    ax1.set_xticks(range(len(refs)))
    ax1.set_xticklabels([f'sub-{r}' for r in refs])
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)

    # Add value labels
    for bar, val in zip(bars, T_rms_vals):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.4f}', ha='center', va='bottom', fontsize=10)

    # 2. HC vs CVD disparity (Grouped bar)
    ax2 = fig.add_subplot(gs[0, 2:])
    x = np.arange(len(refs))
    width = 0.35

    hc_disp = [r['hc_disparity_mean'] for r in results]
    cvd_disp = [r['cvd_disparity_mean'] for r in results]

    bars1 = ax2.bar(x - width/2, hc_disp, width, label='HC', color='#3498db')
    bars2 = ax2.bar(x + width/2, cvd_disp, width, label='CVD', color='#e74c3c')

    ax2.set_xlabel('Reference Subject', fontsize=12)
    ax2.set_ylabel('Mean Procrustes Disparity', fontsize=12)
    ax2.set_title('Alignment Quality by Reference', fontsize=13, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'sub-{r}' for r in refs])
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)

    # 3. Color-specific RMS (Heatmap)
    ax3 = fig.add_subplot(gs[1, :2])
    color_rms_matrix = np.array([r['color_rms'] for r in results])

    # Use imshow instead of seaborn
    im = ax3.imshow(color_rms_matrix.T, aspect='auto', cmap='YlOrRd', interpolation='nearest')

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax3)
    cbar.set_label('RMS Distance', fontsize=11)

    # Add text annotations
    for i in range(len(COLOR_NAMES)):
        for j in range(len(refs)):
            text = ax3.text(j, i, f'{color_rms_matrix[j, i]:.3f}',
                          ha="center", va="center", color="black", fontsize=9)

    # Set ticks and labels
    ax3.set_xticks(range(len(refs)))
    ax3.set_xticklabels([f'sub-{r}' for r in refs])
    ax3.set_yticks(range(len(COLOR_NAMES)))
    ax3.set_yticklabels(COLOR_NAMES)

    ax3.set_title('Color-specific T Magnitude by Reference',
                  fontsize=13, fontweight='bold')
    ax3.set_xlabel('Reference Subject', fontsize=12)
    ax3.set_ylabel('Color', fontsize=12)

    # 4. T Variability (Heatmap of Std)
    ax4 = fig.add_subplot(gs[1, 2:])
    T_std_per_color = np.mean(T_std, axis=1)  # Average std across voxels for each color
    T_mean_per_color = np.mean(T_mean, axis=1)
    CV_per_color = T_std_per_color / (np.abs(T_mean_per_color) + 1e-10) * 100

    bars = ax4.barh(range(8), CV_per_color, color='coral')
    ax4.axvline(x=15, color='green', linestyle='--', linewidth=2, label='15% threshold')
    ax4.set_yticks(range(8))
    ax4.set_yticklabels(COLOR_NAMES)
    ax4.set_xlabel('Coefficient of Variation (%)', fontsize=12)
    ax4.set_title('T Variability across References (by Color)',
                  fontsize=13, fontweight='bold')
    ax4.legend()
    ax4.grid(axis='x', alpha=0.3)

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, CV_per_color)):
        width = bar.get_width()
        ax4.text(width, bar.get_y() + bar.get_height()/2.,
                f'{val:.1f}%', ha='left', va='center', fontsize=9)

    # 5. Consistency Score (Box plot)
    ax5 = fig.add_subplot(gs[2, :2])

    # Calculate pairwise correlations of T between references
    n_refs = len(results)
    correlations = []
    for i in range(n_refs):
        for j in range(i+1, n_refs):
            T_i = T_all[i].flatten()
            T_j = T_all[j].flatten()
            r, _ = spearmanr(T_i, T_j)
            correlations.append(r)

    bp = ax5.boxplot([correlations], vert=True, patch_artist=True,
                     labels=['T Pairwise Correlations'])
    bp['boxes'][0].set_facecolor('lightblue')
    bp['boxes'][0].set_alpha(0.7)

    ax5.axhline(y=0.9, color='green', linestyle='--', linewidth=2, label='High consistency (0.9)')
    ax5.set_ylabel('Spearman Correlation', fontsize=12)
    ax5.set_title('Consistency of T across Reference Choices',
                  fontsize=13, fontweight='bold')
    ax5.legend()
    ax5.grid(axis='y', alpha=0.3)

    # Add statistics text
    corr_mean = np.mean(correlations)
    corr_min = np.min(correlations)
    ax5.text(1.15, 0.5, f'Mean: {corr_mean:.3f}\nMin: {corr_min:.3f}',
            transform=ax5.transAxes, fontsize=11,
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 6. Summary Statistics Table
    ax6 = fig.add_subplot(gs[2, 2:])
    ax6.axis('off')

    T_rms_mean = np.mean(T_rms_vals)
    T_rms_std = np.std(T_rms_vals)
    T_rms_cv = T_rms_std / T_rms_mean * 100

    summary_text = f"""
    📊 Reference Robustness Summary

    T Magnitude (RMS):
      • Mean: {T_rms_mean:.4f}
      • Std:  {T_rms_std:.4f}
      • CV:   {T_rms_cv:.1f}%

    T Consistency:
      • Mean Correlation: {corr_mean:.3f}
      • Min Correlation:  {corr_min:.3f}

    Assessment:
    """

    if T_rms_cv < 15 and corr_mean > 0.9:
        assessment = "  ✅ ROBUST\n  Reference choice는 결과에\n  큰 영향 없음"
        color = 'green'
    elif T_rms_cv < 30 and corr_mean > 0.7:
        assessment = "  ⚠️  MODERATE\n  Reference choice가\n  약간 영향 줌"
        color = 'orange'
    else:
        assessment = "  🚨 SENSITIVE\n  Reference choice가\n  결과에 큰 영향"
        color = 'red'

    ax6.text(0.1, 0.95, summary_text, transform=ax6.transAxes,
            fontsize=11, verticalalignment='top', family='monospace')
    ax6.text(0.1, 0.20, assessment, transform=ax6.transAxes,
            fontsize=13, verticalalignment='top', fontweight='bold',
            color=color)

    # Save figure
    output_file = OUTPUT_DIR / f'reference_robustness_{roi}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Saved: {output_file}")
    plt.close()


def visualize_permutation_test(T_obs_rms, T_null_rms, p_value, roi):
    """Visualize permutation test results"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle(f'Permutation Test - {roi}', fontsize=16, fontweight='bold')

    # 1. Histogram of null distribution
    ax = axes[0]
    ax.hist(T_null_rms, bins=50, color='gray', alpha=0.7, edgecolor='black',
            label='Null Distribution')
    ax.axvline(T_obs_rms, color='red', linestyle='--', linewidth=3,
              label=f'Observed: {T_obs_rms:.4f}')
    ax.axvline(np.mean(T_null_rms), color='blue', linestyle='--', linewidth=2,
              label=f'Null Mean: {np.mean(T_null_rms):.4f}')

    ax.set_xlabel('T Magnitude (RMS)', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title('Null Distribution vs Observed', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)

    # Add p-value text
    ax.text(0.95, 0.95, f'p-value = {p_value:.4f}',
            transform=ax.transAxes, fontsize=14, fontweight='bold',
            verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))

    # 2. Cumulative distribution
    ax = axes[1]
    sorted_null = np.sort(T_null_rms)
    cumulative = np.arange(1, len(sorted_null) + 1) / len(sorted_null)

    ax.plot(sorted_null, cumulative, 'b-', linewidth=2, label='Null CDF')
    ax.axvline(T_obs_rms, color='red', linestyle='--', linewidth=3,
              label=f'Observed: {T_obs_rms:.4f}')
    ax.axhline(1 - p_value, color='orange', linestyle='--', linewidth=2,
              label=f'Percentile: {(1-p_value)*100:.2f}%')

    ax.set_xlabel('T Magnitude (RMS)', fontsize=12)
    ax.set_ylabel('Cumulative Probability', fontsize=12)
    ax.set_title('Cumulative Distribution', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)

    # Add significance assessment
    if p_value < 0.001:
        sig_text = "✅ HIGHLY SIGNIFICANT\n(p < 0.001)"
        color = 'green'
    elif p_value < 0.05:
        sig_text = "✅ SIGNIFICANT\n(p < 0.05)"
        color = 'green'
    else:
        sig_text = "⚠️  NOT SIGNIFICANT\n(p >= 0.05)"
        color = 'orange'

    ax.text(0.05, 0.95, sig_text,
            transform=ax.transAxes, fontsize=12, fontweight='bold',
            verticalalignment='top', color=color,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()

    # Save
    output_file = OUTPUT_DIR / f'permutation_test_{roi}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Saved: {output_file}")
    plt.close()


def visualize_systematic_difference(T_mean, T_std, roi):
    """Visualize the systematic CVD difference pattern"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle(f'Systematic CVD Difference (T) - {roi}',
                 fontsize=16, fontweight='bold')

    n_voxels = T_mean.shape[1]

    # 1. Color-specific T magnitude
    ax = axes[0, 0]
    color_rms = np.sqrt(np.mean(T_mean ** 2, axis=1))

    bars = ax.bar(range(8), color_rms, color=plt.cm.hsv(np.linspace(0, 1, 8)),
                  alpha=0.7, edgecolor='black')
    ax.set_xticks(range(8))
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_ylabel('T Magnitude (RMS)', fontsize=12)
    ax.set_title('Color-specific Systematic Difference', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)

    # Add value labels
    for bar, val in zip(bars, color_rms):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.3f}', ha='center', va='bottom', fontsize=9)

    # 2. T pattern heatmap (average across voxels)
    ax = axes[0, 1]
    # Show T for each color (averaged in bins of voxels)
    n_bins = 50
    voxels_per_bin = max(1, n_voxels // n_bins)
    T_binned = np.array([T_mean[:, i*voxels_per_bin:(i+1)*voxels_per_bin].mean(axis=1)
                        for i in range(n_bins)]).T

    im = ax.imshow(T_binned, aspect='auto', cmap='RdBu_r',
                   vmin=-np.abs(T_mean).max(), vmax=np.abs(T_mean).max())
    ax.set_yticks(range(8))
    ax.set_yticklabels(COLOR_NAMES)
    ax.set_xlabel('Voxel Bins', fontsize=12)
    ax.set_title('T Pattern across Voxels', fontsize=13, fontweight='bold')
    plt.colorbar(im, ax=ax, label='T Magnitude')

    # 3. Uncertainty (Std) by color
    ax = axes[1, 0]
    color_std = np.mean(T_std, axis=1)  # Average std across voxels

    bars = ax.bar(range(8), color_std, color='coral', alpha=0.7, edgecolor='black')
    ax.set_xticks(range(8))
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_ylabel('T Variability (Std)', fontsize=12)
    ax.set_title('Uncertainty in T by Color', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)

    # 4. Signal-to-noise ratio
    ax = axes[1, 1]
    snr = color_rms / color_std

    bars = ax.bar(range(8), snr, color='seagreen', alpha=0.7, edgecolor='black')
    ax.set_xticks(range(8))
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_ylabel('Signal-to-Noise Ratio', fontsize=12)
    ax.set_title('T Robustness (Mean/Std)', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)

    # Add value labels
    for bar, val in zip(bars, snr):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.1f}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()

    # Save
    output_file = OUTPUT_DIR / f'systematic_difference_{roi}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Saved: {output_file}")
    plt.close()


def main():
    """Main workflow"""
    import argparse

    parser = argparse.ArgumentParser(description='Option A Robustness Verification')
    parser.add_argument('--roi', type=str, default='all', choices=['V1', 'V2', 'all'],
                       help='ROI to analyze')
    parser.add_argument('--test', type=str, default='all',
                       choices=['reference', 'permutation', 'all'],
                       help='Which test to run')
    parser.add_argument('--n-perm', type=int, default=10000,
                       help='Number of permutations')
    parser.add_argument('--timestamp', type=str, default='baseline81_deob_determin',
                       help='Timestamp/baseline directory name')
    parser.add_argument('--dataset', type=str, default='deoblique_v2',
                       help='Dataset version')

    args = parser.parse_args()

    print("\n" + "="*60)
    print("OPTION A ROBUSTNESS VERIFICATION")
    print("="*60)

    # Check environment
    if DATASET_DIR is None:
        print("\n⚠️  Running in LOCAL mode - cannot load subject data")
        print("This script must be run on the server to access subject data.")
        print("\nTo run on server:")
        print("  1. Upload: scp verify_option_a_robustness.py haba6030@node2:...")
        print("  2. SSH: ssh haba6030@node2")
        print("  3. Run: python verify_option_a_robustness.py --test all")
        return

    print(f"\n✓ Running in SERVER mode")
    print(f"  Timestamp: {args.timestamp}")
    print(f"  Dataset: {args.dataset}")
    print(f"  Test: {args.test}")

    # Determine ROIs to analyze
    rois_to_analyze = ROIS if args.roi == 'all' else [args.roi]

    for roi in rois_to_analyze:
        print(f"\n{'='*60}")
        print(f"Analyzing {roi}")
        print(f"{'='*60}")

        # Load data
        try:
            hc_patterns = load_all_subjects(HC_SUBJECTS, roi, args.timestamp, args.dataset)
            cvd_patterns = load_all_subjects(CVD_SUBJECTS, roi, args.timestamp, args.dataset)
        except Exception as e:
            print(f"❌ Failed to load data for {roi}: {e}")
            import traceback
            traceback.print_exc()
            continue

        # Ensure same voxel count
        n_voxels = min(hc_patterns.shape[2], cvd_patterns.shape[2])
        hc_patterns = hc_patterns[:, :, :n_voxels]
        cvd_patterns = cvd_patterns[:, :, :n_voxels]

        print(f"\n✓ Data loaded:")
        print(f"  HC: {hc_patterns.shape}")
        print(f"  CVD: {cvd_patterns.shape}")

        # Run tests
        if args.test in ['reference', 'all']:
            print(f"\n{'─'*60}")
            print("Running Reference Robustness Test...")
            print(f"{'─'*60}")

            try:
                results, T_all, T_mean, T_std = test_reference_robustness(
                    hc_patterns, cvd_patterns, roi
                )

                # Visualize
                visualize_reference_robustness(results, T_all, T_mean, T_std, roi)

                # Save numerical results
                df = pd.DataFrame(results)
                output_file = OUTPUT_DIR / f'reference_robustness_{roi}.csv'
                df.to_csv(output_file, index=False)
                print(f"\n✓ Saved: {output_file}")

                # Visualize systematic difference
                visualize_systematic_difference(T_mean, T_std, roi)

            except Exception as e:
                print(f"\n❌ Reference test failed: {e}")
                import traceback
                traceback.print_exc()

        if args.test in ['permutation', 'all']:
            print(f"\n{'─'*60}")
            print("Running Permutation Test...")
            print(f"{'─'*60}")

            try:
                T_obs_rms, T_null_rms, p_value = permutation_test(
                    hc_patterns, cvd_patterns, roi, n_perm=args.n_perm
                )

                # Visualize
                visualize_permutation_test(T_obs_rms, T_null_rms, p_value, roi)

                # Save results
                results_dict = {
                    'roi': roi,
                    'T_observed_rms': T_obs_rms,
                    'T_null_mean': T_null_rms.mean(),
                    'T_null_std': T_null_rms.std(),
                    'p_value': p_value,
                    'n_permutations': args.n_perm
                }

                output_file = OUTPUT_DIR / f'permutation_test_{roi}.json'
                with open(output_file, 'w') as f:
                    json.dump(results_dict, f, indent=2)
                print(f"\n✓ Saved: {output_file}")

            except Exception as e:
                print(f"\n❌ Permutation test failed: {e}")
                import traceback
                traceback.print_exc()

    print(f"\n{'='*60}")
    print("✓ VERIFICATION COMPLETE")
    print(f"{'='*60}")
    print(f"\nResults saved to: {OUTPUT_DIR}")
    print("\nDownload results with:")
    print(f"  scp -r haba6030@node2:{OUTPUT_DIR} results/group_level/")


if __name__ == '__main__':
    main()
