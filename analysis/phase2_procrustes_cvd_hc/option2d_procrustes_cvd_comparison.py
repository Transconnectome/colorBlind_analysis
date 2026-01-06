#!/usr/bin/env python3
"""
option2d_procrustes_cvd_comparison.py
====================================

Option 2D: Procrustes-based CVD vs HC Comparison

**목표**:
HC와 CVD의 systematic difference 찾기 → Color filter 제작

**배경**:
- HC group template 실패 (RDM < 0.3)
- 하지만 Procrustes stability 0.91! (geometric alignment 성공)
- CVD도 뇌에서는 색 구분 가능 (classification > chance)

**전략**:
1. **Option A**: Reference-based (sub-02)
   - Sub-02를 reference로 모든 HC 정렬
   - HC mean pattern 계산
   - CVD를 같은 reference로 정렬
   - Systematic difference 분석

2. **Option B**: Iterative alignment (Reference-independent)
   - 초기 HC mean 계산
   - 반복적으로 HC를 mean으로 정렬
   - Converge할 때까지
   - CVD를 converged mean으로 정렬

3. **Option C**: Voxel weighting
   - HC 내에서 reliable voxel 찾기
   - Weighted Procrustes alignment
   - 또는 reliable voxel만 사용

**기대**:
CVD → HC transformation 찾기 → Color filter 제작
"""

import argparse
import numpy as np
from pathlib import Path
from scipy.spatial import procrustes
from scipy.stats import spearmanr
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ============================================================================
# Data Loading
# ============================================================================

def load_subject_amplitudes(subject_id, roi, timestamp, dataset='deoblique_v2'):
    """피험자 데이터 로드"""
    base_dir = Path('/scratch/connectome/haba6030/colorBlind')
    # New structure: derivatives/V3_Comprehensive/BH2009_{dataset}/{timestamp}/sub-{subject}/{roi}
    result_dir = base_dir / 'derivatives' / 'V3_Comprehensive' / f'BH2009_{dataset}' / timestamp / f'sub-{subject_id}' / roi

    if not result_dir.exists():
        raise FileNotFoundError(f"No data found for sub-{subject_id}, ROI {roi} at {result_dir}")
    amp_file = result_dir / 'amplitudes_z.npy'
    amplitudes = np.load(amp_file)

    return amplitudes, result_dir

def load_all_subjects(subjects, roi, timestamp, dataset):
    """모든 피험자 데이터 로드"""
    print(f"Loading {roi} data for {len(subjects)} subjects...")

    amplitudes_all = []
    subjects_info = []

    for subject_id in subjects:
        try:
            amplitudes, _ = load_subject_amplitudes(
                subject_id, roi, timestamp, dataset
            )
            n_runs, n_colors, n_voxels = amplitudes.shape

            # Run 평균 → (n_colors, n_voxels)
            pattern = amplitudes.mean(axis=0)

            amplitudes_all.append(pattern)
            subjects_info.append({
                'subject': subject_id,
                'n_colors': n_colors,
                'n_voxels': n_voxels
            })

            print(f"  sub-{subject_id}: {pattern.shape}")

        except FileNotFoundError as e:
            print(f"  sub-{subject_id}: ⚠️ {e}")
            continue

    # Voxel 수 통일
    n_voxels_min = min([info['n_voxels'] for info in subjects_info])
    amplitudes_all = [amp[:, :n_voxels_min] for amp in amplitudes_all]
    for info in subjects_info:
        info['n_voxels'] = n_voxels_min

    return amplitudes_all, subjects_info

# ============================================================================
# Option A: Reference-based Alignment
# ============================================================================

def option_a_reference_based(hc_patterns, cvd_patterns, reference_idx=0):
    """
    Option A: Reference-based Procrustes Alignment

    Args:
        hc_patterns: List of (n_colors, n_voxels) HC patterns
        cvd_patterns: List of (n_colors, n_voxels) CVD patterns
        reference_idx: Index of reference HC (default: 0 = sub-02)

    Returns:
        hc_aligned: List of aligned HC patterns
        hc_mean: Mean HC pattern in aligned space
        cvd_aligned: List of aligned CVD patterns
        disparities: Procrustes disparities
    """
    print("=" * 80)
    print("Option A: Reference-based Alignment")
    print("=" * 80)

    n_hc = len(hc_patterns)
    n_cvd = len(cvd_patterns)

    # Debug: print all shapes
    print("HC pattern shapes:")
    for i, p in enumerate(hc_patterns):
        print(f"  HC {i}: {p.shape}")
    print("\nCVD pattern shapes:")
    for i, p in enumerate(cvd_patterns):
        print(f"  CVD {i}: {p.shape}")
    print()

    reference = hc_patterns[reference_idx]
    print(f"Reference: HC subject {reference_idx} (sub-02)")
    print(f"Reference shape: {reference.shape}")
    print()

    # HC alignment
    print("Aligning HC subjects to reference...")
    hc_aligned = [reference]
    hc_disparities = [0.0]

    for i, pattern in enumerate(hc_patterns):
        if i == reference_idx:
            continue

        mtx1, mtx2, disparity = procrustes(reference, pattern)
        hc_aligned.append(mtx2)
        hc_disparities.append(disparity)

        print(f"  HC {i}: disparity = {disparity:.4f}")

    # HC mean
    hc_mean = np.mean(hc_aligned, axis=0)
    print(f"\nHC mean pattern: {hc_mean.shape}")
    print(f"HC mean disparity: {np.mean(hc_disparities):.4f}")
    print()

    # CVD alignment
    print("Aligning CVD subjects to reference...")
    cvd_aligned = []
    cvd_disparities = []

    for i, pattern in enumerate(cvd_patterns):
        mtx1, mtx2, disparity = procrustes(reference, pattern)
        cvd_aligned.append(mtx2)
        cvd_disparities.append(disparity)

        print(f"  CVD {i}: disparity = {disparity:.4f}")

    print(f"\nCVD mean disparity: {np.mean(cvd_disparities):.4f}")
    print()

    return hc_aligned, hc_mean, cvd_aligned, {
        'hc_disparities': hc_disparities,
        'cvd_disparities': cvd_disparities
    }

# ============================================================================
# Option B: Iterative Alignment
# ============================================================================

def option_b_iterative_alignment(hc_patterns, cvd_patterns, max_iter=10, tol=1e-4):
    """
    Option B: Iterative Alignment (Reference-independent)

    Args:
        hc_patterns: List of (n_colors, n_voxels) HC patterns
        cvd_patterns: List of (n_colors, n_voxels) CVD patterns
        max_iter: Maximum iterations
        tol: Convergence tolerance

    Returns:
        hc_aligned: List of aligned HC patterns
        hc_mean: Converged mean HC pattern
        cvd_aligned: List of aligned CVD patterns
        convergence_info: Convergence history
    """
    print("=" * 80)
    print("Option B: Iterative Alignment (Reference-independent)")
    print("=" * 80)

    n_hc = len(hc_patterns)
    n_cvd = len(cvd_patterns)

    # 초기 mean
    hc_mean = np.mean(hc_patterns, axis=0)
    print(f"Initial HC mean: {hc_mean.shape}")
    print()

    convergence_history = []

    for iter_idx in range(max_iter):
        print(f"Iteration {iter_idx + 1}/{max_iter}")

        # HC alignment to current mean
        hc_aligned = []
        disparities = []

        for i, pattern in enumerate(hc_patterns):
            mtx1, mtx2, disparity = procrustes(hc_mean, pattern)
            hc_aligned.append(mtx2)
            disparities.append(disparity)

        mean_disparity = np.mean(disparities)
        print(f"  Mean disparity: {mean_disparity:.6f}")

        # Update mean
        hc_mean_new = np.mean(hc_aligned, axis=0)

        # Check convergence
        mean_change = np.mean(np.abs(hc_mean_new - hc_mean))
        print(f"  Mean change: {mean_change:.6f}")

        convergence_history.append({
            'iteration': iter_idx + 1,
            'mean_disparity': mean_disparity,
            'mean_change': mean_change
        })

        hc_mean = hc_mean_new

        if mean_change < tol:
            print(f"\n✓ Converged at iteration {iter_idx + 1}")
            break

        print()

    print(f"Final HC mean: {hc_mean.shape}")
    print(f"Final mean disparity: {mean_disparity:.4f}")
    print()

    # CVD alignment to converged mean
    print("Aligning CVD subjects to converged mean...")
    cvd_aligned = []
    cvd_disparities = []

    for i, pattern in enumerate(cvd_patterns):
        mtx1, mtx2, disparity = procrustes(hc_mean, pattern)
        cvd_aligned.append(mtx2)
        cvd_disparities.append(disparity)

        print(f"  CVD {i}: disparity = {disparity:.4f}")

    print(f"\nCVD mean disparity: {np.mean(cvd_disparities):.4f}")
    print()

    return hc_aligned, hc_mean, cvd_aligned, {
        'convergence_history': convergence_history,
        'hc_disparities': disparities,
        'cvd_disparities': cvd_disparities
    }

# ============================================================================
# Option C: Voxel Weighting
# ============================================================================

def compute_voxel_reliability(patterns):
    """
    HC 내에서 voxel-wise reliability 계산

    Args:
        patterns: List of (n_colors, n_voxels) patterns

    Returns:
        reliability: (n_voxels,) reliability scores
    """
    n_patterns = len(patterns)
    n_voxels = patterns[0].shape[1]

    reliability = np.zeros(n_voxels)

    for v in range(n_voxels):
        # 이 voxel의 color pattern correlation (모든 HC 쌍)
        correlations = []
        for i in range(n_patterns):
            for j in range(i + 1, n_patterns):
                r, _ = spearmanr(patterns[i][:, v], patterns[j][:, v])
                if not np.isnan(r):
                    correlations.append(r)

        if len(correlations) > 0:
            reliability[v] = np.mean(correlations)

    return reliability

def option_c_voxel_weighting(hc_patterns, cvd_patterns, reliability_threshold=0.3):
    """
    Option C: Voxel Weighting

    Reliable voxel만 사용해서 Procrustes alignment

    Args:
        hc_patterns: List of (n_colors, n_voxels) HC patterns
        cvd_patterns: List of (n_colors, n_voxels) CVD patterns
        reliability_threshold: Threshold for reliable voxels

    Returns:
        hc_aligned: List of aligned HC patterns (reliable voxels only)
        hc_mean: Mean HC pattern
        cvd_aligned: List of aligned CVD patterns
        voxel_info: Voxel reliability info
    """
    print("=" * 80)
    print("Option C: Voxel Weighting")
    print("=" * 80)

    # Compute voxel reliability
    print("Computing voxel reliability across HC subjects...")
    reliability = compute_voxel_reliability(hc_patterns)

    reliable_mask = reliability > reliability_threshold
    n_reliable = reliable_mask.sum()
    n_total = len(reliability)

    print(f"Reliable voxels (r > {reliability_threshold}): {n_reliable}/{n_total} ({100*n_reliable/n_total:.1f}%)")
    print(f"Mean reliability (all): {reliability.mean():.3f}")
    print(f"Mean reliability (reliable): {reliability[reliable_mask].mean():.3f}")
    print()

    # Select reliable voxels
    hc_reliable = [pattern[:, reliable_mask] for pattern in hc_patterns]
    cvd_reliable = [pattern[:, reliable_mask] for pattern in cvd_patterns]

    print(f"HC pattern shape (reliable): {hc_reliable[0].shape}")
    print(f"CVD pattern shape (reliable): {cvd_reliable[0].shape}")
    print()

    # Iterative alignment on reliable voxels
    print("Iterative alignment on reliable voxels...")
    hc_aligned, hc_mean, cvd_aligned, info = option_b_iterative_alignment(
        hc_reliable, cvd_reliable, max_iter=10
    )

    return hc_aligned, hc_mean, cvd_aligned, {
        'reliability': reliability,
        'reliable_mask': reliable_mask,
        'n_reliable': n_reliable,
        **info
    }

# ============================================================================
# CVD vs HC Difference Analysis
# ============================================================================

def analyze_cvd_differences(hc_mean, cvd_aligned, subjects_info):
    """
    CVD vs HC systematic difference 분석

    Args:
        hc_mean: (n_colors, n_voxels) HC mean pattern
        cvd_aligned: List of (n_colors, n_voxels) CVD patterns
        subjects_info: CVD subject info

    Returns:
        analysis_results: Dict with analysis results
    """
    print("=" * 80)
    print("CVD vs HC Difference Analysis")
    print("=" * 80)

    n_colors, n_voxels = hc_mean.shape
    n_cvd = len(cvd_aligned)

    # 1. Per-CVD difference
    print("Computing per-CVD differences...")
    cvd_diffs = []
    for i, cvd_pattern in enumerate(cvd_aligned):
        diff = cvd_pattern - hc_mean  # (n_colors, n_voxels)
        cvd_diffs.append(diff)

        # Overall magnitude
        diff_magnitude = np.sqrt(np.mean(diff ** 2))
        print(f"  CVD {i}: RMS difference = {diff_magnitude:.4f}")

    print()

    # 2. Common CVD pattern
    print("Computing common CVD pattern...")
    cvd_common_diff = np.mean(cvd_diffs, axis=0)  # (n_colors, n_voxels)
    cvd_common_magnitude = np.sqrt(np.mean(cvd_common_diff ** 2))
    print(f"Common CVD difference (RMS): {cvd_common_magnitude:.4f}")
    print()

    # 3. Color-specific difference
    print("Color-specific analysis:")
    color_diffs = []
    for c in range(n_colors):
        # 각 색상에서 CVD 평균 차이
        color_diff = np.mean([diff[c] for diff in cvd_diffs], axis=0)  # (n_voxels,)
        color_magnitude = np.sqrt(np.mean(color_diff ** 2))
        color_diffs.append(color_magnitude)

        print(f"  Color {c+1}: RMS = {color_magnitude:.4f}")

    print()

    # 4. Voxel-specific difference
    print("Voxel-specific analysis:")
    voxel_diffs = []
    for v in range(n_voxels):
        # 각 voxel에서 CVD 평균 차이 (across colors)
        voxel_diff = np.mean([diff[:, v] for diff in cvd_diffs], axis=0)  # (n_colors,)
        voxel_magnitude = np.sqrt(np.mean(voxel_diff ** 2))
        voxel_diffs.append(voxel_magnitude)

    voxel_diffs = np.array(voxel_diffs)
    print(f"  Mean voxel difference: {voxel_diffs.mean():.4f}")
    print(f"  Max voxel difference: {voxel_diffs.max():.4f}")
    print(f"  Top 10% voxels (mean): {voxel_diffs[voxel_diffs > np.percentile(voxel_diffs, 90)].mean():.4f}")
    print()

    # 5. Consistency across CVDs
    print("Consistency across CVD subjects:")
    # 각 voxel에서 CVD들이 같은 방향으로 차이나는지
    consistency_scores = []
    for v in range(n_voxels):
        # 각 voxel, 각 color에서의 차이 방향
        diffs_at_voxel = np.array([diff[:, v] for diff in cvd_diffs])  # (n_cvd, n_colors)

        # 부호 일치도
        signs = np.sign(diffs_at_voxel)
        consistency = np.abs(signs.mean(axis=0)).mean()  # 평균 부호 일치도
        consistency_scores.append(consistency)

    consistency_scores = np.array(consistency_scores)
    print(f"  Mean consistency: {consistency_scores.mean():.3f}")
    print(f"  High consistency voxels (>0.7): {(consistency_scores > 0.7).sum()}/{n_voxels}")
    print()

    return {
        'cvd_diffs': cvd_diffs,
        'cvd_common_diff': cvd_common_diff,
        'cvd_common_magnitude': cvd_common_magnitude,
        'color_diffs': color_diffs,
        'voxel_diffs': voxel_diffs,
        'consistency_scores': consistency_scores
    }

# ============================================================================
# Visualization
# ============================================================================

def plot_difference_maps(hc_mean, cvd_aligned, analysis_results, output_dir, roi):
    """차이 맵 시각화"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    n_colors, n_voxels = hc_mean.shape

    # 1. Color-specific differences
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    fig.suptitle(f'{roi}: Color-specific CVD vs HC Difference', fontsize=16)

    for c in range(n_colors):
        ax = axes[c // 4, c % 4]

        # CVD 평균 차이
        color_diff = np.mean([diff[c] for diff in analysis_results['cvd_diffs']], axis=0)

        ax.hist(color_diff, bins=50, alpha=0.7, edgecolor='black')
        ax.axvline(0, color='red', linestyle='--', linewidth=2)
        ax.set_title(f'Color {c+1}')
        ax.set_xlabel('Difference (CVD - HC)')
        ax.set_ylabel('Voxel Count')
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / f'{roi}_color_specific_differences.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 2. Voxel-specific differences
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))

    voxel_diffs = analysis_results['voxel_diffs']
    voxel_indices = np.arange(n_voxels)

    ax.bar(voxel_indices, voxel_diffs, alpha=0.7, edgecolor='black')
    ax.axhline(voxel_diffs.mean(), color='red', linestyle='--', linewidth=2, label='Mean')
    ax.axhline(np.percentile(voxel_diffs, 90), color='orange', linestyle='--', linewidth=2, label='90th percentile')
    ax.set_title(f'{roi}: Voxel-specific CVD vs HC Difference (RMS)')
    ax.set_xlabel('Voxel Index')
    ax.set_ylabel('RMS Difference')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / f'{roi}_voxel_specific_differences.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 3. Consistency scores
    fig, ax = plt.subplots(1, 1, figsize=(12, 6))

    consistency = analysis_results['consistency_scores']

    ax.bar(voxel_indices, consistency, alpha=0.7, edgecolor='black')
    ax.axhline(0.7, color='red', linestyle='--', linewidth=2, label='High consistency (0.7)')
    ax.set_title(f'{roi}: CVD Consistency Across Subjects')
    ax.set_xlabel('Voxel Index')
    ax.set_ylabel('Consistency Score')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / f'{roi}_consistency_scores.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"✓ Figures saved to {output_dir}/")

# ============================================================================
# Main Analysis
# ============================================================================

def run_procrustes_cvd_comparison(args):
    """Procrustes + CVD comparison 실행"""
    print("=" * 80)
    print("Option 2D: Procrustes + CVD Comparison")
    print("=" * 80)
    print(f"Timestamp: {args.timestamp}")
    print(f"HC subjects: {args.hc_subjects}")
    print(f"CVD subjects: {args.cvd_subjects}")
    print(f"ROIs: {args.rois}")
    print()

    # Output directory
    base_dir = Path('/scratch/connectome/haba6030/colorBlind')
    output_base = base_dir / 'results' / 'group_level' / args.timestamp

    all_results = {}

    for roi in args.rois:
        print("\n" + "=" * 80)
        print(f"ROI: {roi}")
        print("=" * 80)

        try:
            # Load HC data
            hc_patterns, hc_info = load_all_subjects(
                args.hc_subjects, roi, args.timestamp, args.dataset
            )
            print()

            # Load CVD data
            cvd_patterns, cvd_info = load_all_subjects(
                args.cvd_subjects, roi, args.timestamp, args.dataset
            )
            print()

            # Unify voxel count between HC and CVD
            n_voxels_hc = hc_patterns[0].shape[1]
            n_voxels_cvd = cvd_patterns[0].shape[1]
            n_voxels_min = min(n_voxels_hc, n_voxels_cvd)

            if n_voxels_hc != n_voxels_cvd:
                print(f"⚠️  Unifying voxels: HC {n_voxels_hc}, CVD {n_voxels_cvd} → {n_voxels_min}")
                hc_patterns = [pattern[:, :n_voxels_min] for pattern in hc_patterns]
                cvd_patterns = [pattern[:, :n_voxels_min] for pattern in cvd_patterns]
                print()

            # Option A
            print("\n")
            hc_a, hc_mean_a, cvd_a, info_a = option_a_reference_based(
                hc_patterns, cvd_patterns, reference_idx=0
            )
            analysis_a = analyze_cvd_differences(hc_mean_a, cvd_a, cvd_info)

            # Option B
            print("\n")
            hc_b, hc_mean_b, cvd_b, info_b = option_b_iterative_alignment(
                hc_patterns, cvd_patterns, max_iter=10
            )
            analysis_b = analyze_cvd_differences(hc_mean_b, cvd_b, cvd_info)

            # Option C
            print("\n")
            hc_c, hc_mean_c, cvd_c, info_c = option_c_voxel_weighting(
                hc_patterns, cvd_patterns, reliability_threshold=0.3
            )
            analysis_c = analyze_cvd_differences(hc_mean_c, cvd_c, cvd_info)

            # Save results
            roi_dir = output_base / roi
            roi_dir.mkdir(parents=True, exist_ok=True)

            # Option A figures
            plot_difference_maps(hc_mean_a, cvd_a, analysis_a, roi_dir / 'option_a', roi)

            # Option B figures
            plot_difference_maps(hc_mean_b, cvd_b, analysis_b, roi_dir / 'option_b', roi)

            # Option C figures
            plot_difference_maps(hc_mean_c, cvd_c, analysis_c, roi_dir / 'option_c', roi)

            # Save numerical results
            np.save(roi_dir / 'hc_mean_option_a.npy', hc_mean_a)
            np.save(roi_dir / 'hc_mean_option_b.npy', hc_mean_b)
            np.save(roi_dir / 'hc_mean_option_c.npy', hc_mean_c)

            np.save(roi_dir / 'cvd_common_diff_option_a.npy', analysis_a['cvd_common_diff'])
            np.save(roi_dir / 'cvd_common_diff_option_b.npy', analysis_b['cvd_common_diff'])
            np.save(roi_dir / 'cvd_common_diff_option_c.npy', analysis_c['cvd_common_diff'])

            # Summary
            summary = {
                'roi': roi,
                'n_hc': len(hc_patterns),
                'n_cvd': len(cvd_patterns),
                'n_voxels': hc_patterns[0].shape[1],
                'option_a': {
                    'hc_mean_disparity': float(np.mean(info_a['hc_disparities'])),
                    'cvd_mean_disparity': float(np.mean(info_a['cvd_disparities'])),
                    'cvd_common_magnitude': float(analysis_a['cvd_common_magnitude'])
                },
                'option_b': {
                    'hc_mean_disparity': float(np.mean(info_b['hc_disparities'])),
                    'cvd_mean_disparity': float(np.mean(info_b['cvd_disparities'])),
                    'cvd_common_magnitude': float(analysis_b['cvd_common_magnitude']),
                    'n_iterations': len(info_b['convergence_history'])
                },
                'option_c': {
                    'n_reliable_voxels': int(info_c['n_reliable']),
                    'reliability_threshold': 0.3,
                    'hc_mean_disparity': float(np.mean(info_c['hc_disparities'])),
                    'cvd_mean_disparity': float(np.mean(info_c['cvd_disparities'])),
                    'cvd_common_magnitude': float(analysis_c['cvd_common_magnitude'])
                }
            }

            with open(roi_dir / 'summary.json', 'w') as f:
                json.dump(summary, f, indent=2)

            all_results[roi] = summary

            print(f"\n✓ Results saved to {roi_dir}/")

        except Exception as e:
            print(f"❌ Error processing {roi}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Save overall summary
    with open(output_base / 'procrustes_cvd_comparison_summary.json', 'w') as f:
        json.dump(all_results, f, indent=2)

    print("\n" + "=" * 80)
    print("Procrustes + CVD Comparison Analysis complete!")
    print("=" * 80)

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Procrustes + CVD Comparison')
    parser.add_argument('--timestamp', type=str, required=True)
    parser.add_argument('--dataset', type=str, default='deoblique_v2')
    parser.add_argument('--hc-subjects', nargs='+', required=True,
                       help='HC subject IDs')
    parser.add_argument('--cvd-subjects', nargs='+', required=True,
                       help='CVD subject IDs')
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2', 'V3', 'hV4'])

    args = parser.parse_args()
    run_procrustes_cvd_comparison(args)
