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

def load_all_subjects(subjects, roi, timestamp, dataset, min_voxels=10):
    """
    모든 피험자 데이터 로드

    Args:
        subjects: 피험자 ID 리스트
        roi: ROI 이름
        timestamp: 타임스탬프
        dataset: 데이터셋 이름
        min_voxels: 최소 복셀 수 임계값 (기본값: 10)
                    이보다 적은 복셀을 가진 피험자-ROI 쌍은 제외

    Returns:
        amplitudes_all: 패턴 리스트
        subjects_info: 피험자 정보 리스트
        excluded_subjects: 제외된 피험자 정보 리스트
    """
    print(f"Loading {roi} data for {len(subjects)} subjects...")
    print(f"Minimum voxel count threshold: {min_voxels}")

    amplitudes_all = []
    subjects_info = []
    excluded_subjects = []

    for subject_id in subjects:
        try:
            amplitudes, _ = load_subject_amplitudes(
                subject_id, roi, timestamp, dataset
            )
            n_runs, n_colors, n_voxels = amplitudes.shape

            # ✅ 복셀 수 체크 - 최소 임계값 미달 시 제외
            if n_voxels < min_voxels:
                print(f"  sub-{subject_id}: ⚠️ EXCLUDED - Only {n_voxels} voxels (< {min_voxels} threshold)")
                excluded_subjects.append({
                    'subject': subject_id,
                    'n_voxels': n_voxels,
                    'reason': f'Insufficient voxels ({n_voxels} < {min_voxels})'
                })
                continue

            # Run 평균 → (n_colors, n_voxels)
            pattern = amplitudes.mean(axis=0)

            amplitudes_all.append(pattern)
            subjects_info.append({
                'subject': subject_id,
                'n_colors': n_colors,
                'n_voxels': n_voxels
            })

            print(f"  sub-{subject_id}: {pattern.shape} ✓")

        except FileNotFoundError as e:
            print(f"  sub-{subject_id}: ⚠️ {e}")
            excluded_subjects.append({
                'subject': subject_id,
                'n_voxels': 0,
                'reason': 'Data not found'
            })
            continue

    # 제외된 피험자 요약
    if excluded_subjects:
        print(f"\n⚠️  Excluded {len(excluded_subjects)} subject(s) from {roi} analysis:")
        for exc in excluded_subjects:
            print(f"    sub-{exc['subject']}: {exc['reason']}")

    # Voxel 수 통일
    if len(amplitudes_all) == 0:
        raise ValueError(f"No valid subjects remaining for {roi} after exclusion")

    n_voxels_min = min([info['n_voxels'] for info in subjects_info])
    amplitudes_all = [amp[:, :n_voxels_min] for amp in amplitudes_all]
    for info in subjects_info:
        info['n_voxels'] = n_voxels_min

    print(f"\n✓ {len(amplitudes_all)} subjects included, final voxel count: {n_voxels_min}\n")

    return amplitudes_all, subjects_info, excluded_subjects

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

    # Validate reference dimensions
    if reference.shape[0] == 0 or reference.shape[1] == 0:
        print(f"⚠️  ERROR: Reference has zero dimension: {reference.shape}")
        print(f"  Cannot perform Procrustes alignment")
        return [], reference, [], {'hc_disparities': [], 'cvd_disparities': []}

    print()

    # HC alignment
    print("Aligning HC subjects to reference...")
    hc_aligned = [reference]
    hc_disparities = [0.0]

    for i, pattern in enumerate(hc_patterns):
        if i == reference_idx:
            continue

        # Validate pattern dimensions before Procrustes
        if pattern.shape[0] == 0 or pattern.shape[1] == 0:
            print(f"  ⚠️  Skipping HC {i} - zero dimension: {pattern.shape}")
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
        # Validate pattern dimensions before Procrustes
        if pattern.shape[0] == 0 or pattern.shape[1] == 0:
            print(f"  ⚠️  Skipping CVD {i} - zero dimension: {pattern.shape}")
            continue

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

    # Validate matrix dimensions
    if hc_mean.shape[0] == 0 or hc_mean.shape[1] == 0:
        print(f"⚠️  ERROR: HC mean has zero dimension: {hc_mean.shape}")
        print(f"  Cannot perform Procrustes alignment")
        return [], hc_mean, [], {'convergence_history': [], 'hc_disparities': [], 'cvd_disparities': []}

    print()

    convergence_history = []

    for iter_idx in range(max_iter):
        print(f"Iteration {iter_idx + 1}/{max_iter}")

        # HC alignment to current mean
        hc_aligned = []
        disparities = []

        for i, pattern in enumerate(hc_patterns):
            # Validate pattern dimensions before Procrustes
            if pattern.shape[0] == 0 or pattern.shape[1] == 0:
                print(f"  ⚠️  Skipping HC {i} - zero dimension: {pattern.shape}")
                continue

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
        # Validate pattern dimensions before Procrustes
        if pattern.shape[0] == 0 or pattern.shape[1] == 0:
            print(f"  ⚠️  Skipping CVD {i} - zero dimension: {pattern.shape}")
            continue

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

    # Validate sufficient voxels
    if n_reliable == 0:
        print(f"⚠️  WARNING: No reliable voxels found (threshold={reliability_threshold})")
        print(f"  Cannot perform Procrustes alignment - returning empty results")
        return [], np.array([]), [], {
            'reliability': reliability,
            'reliable_mask': reliable_mask,
            'n_reliable': n_reliable,
            'convergence_history': [],
            'hc_disparities': [],
            'cvd_disparities': []
        }

    if n_reliable < 10:
        print(f"⚠️  WARNING: Very few reliable voxels ({n_reliable}), results may be unreliable")

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

    # Validate input dimensions
    if hc_mean.ndim != 2:
        print(f"⚠️  ERROR: hc_mean has {hc_mean.ndim} dimensions (expected 2)")
        print(f"  Shape: {hc_mean.shape}")
        print(f"  Likely cause: No reliable voxels after selection")
        return {
            'error': 'Invalid hc_mean dimensions',
            'hc_mean_shape': hc_mean.shape,
            'hc_mean_ndim': hc_mean.ndim
        }

    if hc_mean.shape[1] == 0:
        print(f"⚠️  ERROR: hc_mean has 0 voxels")
        print(f"  Shape: {hc_mean.shape}")
        return {
            'error': 'No voxels in hc_mean',
            'hc_mean_shape': hc_mean.shape
        }

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

    # Skip if analysis failed (due to insufficient voxels)
    if 'error' in analysis_results:
        print(f"⚠️  Skipping visualization due to analysis error: {analysis_results['error']}")
        return

    # Validate input dimensions
    if hc_mean.ndim != 2:
        print(f"⚠️  Skipping visualization: hc_mean has {hc_mean.ndim} dimensions (expected 2)")
        return

    if hc_mean.shape[1] == 0:
        print(f"⚠️  Skipping visualization: hc_mean has 0 voxels")
        return

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
    import datetime

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
    output_base = base_dir / 'analysis' / 'comprehensive' / 'results' / args.timestamp
    output_base.mkdir(parents=True, exist_ok=True)

    # Save settings.json (configuration)
    settings = {
        'analysis_type': 'procrustes_cvd_comparison',
        'method': 'option_a_reference_based',
        'timestamp': args.timestamp,
        'dataset': args.dataset,
        'hc_subjects': args.hc_subjects,
        'cvd_subjects': args.cvd_subjects,
        'rois': args.rois,
        'min_voxels_threshold': 10,
        'procrustes_config': {
            'method': 'ordinary',
            'scaling': False,
            'reference': 'first_hc_subject'
        },
        'run_time': datetime.datetime.now().isoformat()
    }

    with open(output_base / 'settings.json', 'w') as f:
        json.dump(settings, f, indent=2)

    print(f"✓ Settings saved to {output_base / 'settings.json'}")
    print()

    all_results = {}

    for roi in args.rois:
        print("\n" + "=" * 80)
        print(f"ROI: {roi}")
        print("=" * 80)

        try:
            # Load HC data (with min_voxels=10 threshold)
            hc_patterns, hc_info, hc_excluded = load_all_subjects(
                args.hc_subjects, roi, args.timestamp, args.dataset, min_voxels=10
            )
            print()

            # Load CVD data (with min_voxels=10 threshold)
            cvd_patterns, cvd_info, cvd_excluded = load_all_subjects(
                args.cvd_subjects, roi, args.timestamp, args.dataset, min_voxels=10
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

            # ============================================================================
            # Option A: Reference-based Alignment (ONLY)
            # ============================================================================
            # 논문에서 사용한 방법: Ordinary Procrustes (translation + rotation, no scaling)
            # Option B (iterative) and Option C (voxel weighting) are experimental methods
            # not used in the published paper
            print("\n")
            hc_a, hc_mean_a, cvd_a, info_a = option_a_reference_based(
                hc_patterns, cvd_patterns, reference_idx=0
            )
            analysis_a = analyze_cvd_differences(hc_mean_a, cvd_a, cvd_info)

            # ============================================================================
            # Option B & C: DISABLED
            # ============================================================================
            # Option B (Iterative alignment): Not used in paper
            # Option C (Voxel weighting with reliability threshold=0.3): Not applicable
            #   - Current data: Mean reliability = -0.022 ~ 0.022 (far below 0.3)
            #   - Result: 0 voxels pass threshold → all analyses fail
            #   - Paper method: Use all voxels without reliability filtering
            # print("\n")
            # hc_b, hc_mean_b, cvd_b, info_b = option_b_iterative_alignment(
            #     hc_patterns, cvd_patterns, max_iter=10
            # )
            # analysis_b = analyze_cvd_differences(hc_mean_b, cvd_b, cvd_info)
            #
            # print("\n")
            # hc_c, hc_mean_c, cvd_c, info_c = option_c_voxel_weighting(
            #     hc_patterns, cvd_patterns, reliability_threshold=0.3
            # )
            # analysis_c = analyze_cvd_differences(hc_mean_c, cvd_c, cvd_info)

            print("\n" + "=" * 80)
            print("Option B & C: SKIPPED")
            print("Reason: Paper uses Option A (reference-based Procrustes) only")
            print("  - Option B (iterative): Experimental, not validated in paper")
            print("  - Option C (reliability filtering): Inappropriate for current data")
            print("    * Mean cross-subject reliability: -0.022 to 0.022")
            print("    * Threshold 0.3 filters out ALL voxels")
            print("    * Paper method: No reliability filtering")
            print("=" * 80)

            # Save results
            roi_dir = output_base / roi
            roi_dir.mkdir(parents=True, exist_ok=True)

            # Option A figures (ONLY)
            plot_difference_maps(hc_mean_a, cvd_a, analysis_a, roi_dir / 'option_a', roi)

            # Save numerical results (Option A only)
            np.save(roi_dir / 'hc_mean_option_a.npy', hc_mean_a)
            np.save(roi_dir / 'cvd_common_diff_option_a.npy', analysis_a['cvd_common_diff'])

            # Results (Option A only)
            roi_results = {
                'roi': roi,
                'n_hc': len(hc_patterns),
                'n_cvd': len(cvd_patterns),
                'n_voxels': hc_patterns[0].shape[1],
                'hc_excluded': hc_excluded,
                'cvd_excluded': cvd_excluded,
                'hc_mean_disparity': float(np.mean(info_a['hc_disparities'])),
                'cvd_mean_disparity': float(np.mean(info_a['cvd_disparities'])),
                'cvd_common_magnitude': float(analysis_a['cvd_common_magnitude'])
            }

            with open(roi_dir / 'results.json', 'w') as f:
                json.dump(roi_results, f, indent=2)

            all_results[roi] = roi_results

            print(f"\n✓ Results saved to {roi_dir}/")

        except Exception as e:
            print(f"❌ Error processing {roi}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Save overall results summary
    overall_results = {
        'analysis': 'procrustes_cvd_comparison',
        'timestamp': args.timestamp,
        'rois': all_results
    }

    with open(output_base / 'results.json', 'w') as f:
        json.dump(overall_results, f, indent=2)

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
