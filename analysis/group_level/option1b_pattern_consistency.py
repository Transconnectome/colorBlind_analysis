#!/usr/bin/env python3
"""
Option 1B: Pattern-Based Consistency Analysis
==============================================

목적: Voxel 간의 관계(pattern geometry)를 보존한 consistency 측정

배경:
- 색 정보는 individual voxels가 아니라 voxel 간 관계에 존재
- RDM correlation은 이미 pattern-based이지만 충분하지 않을 수 있음
- Pattern geometry (shape, structure)의 stability를 직접 측정 필요

접근:
1. Multivariate pattern distance (not just correlation)
2. Procrustes alignment (pattern shape matching)
3. Cross-validated pattern prediction

저자: Claude Code
날짜: 2025-12-17
"""

import numpy as np
import argparse
from pathlib import Path
from scipy.stats import spearmanr
from scipy.spatial import procrustes
from scipy.spatial.distance import euclidean
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

# ============================================================================
# Pattern Consistency Metrics
# ============================================================================

def compute_pattern_stability(amplitudes, metric='procrustes'):
    """
    Multivariate pattern의 test-retest stability

    **방법**:
    1. Procrustes distance: Pattern geometry 비교
       - Rotation/scaling 보정 후 차이
       - 낮을수록 pattern shape가 유사

    2. Pattern correlation: Direct correlation
       - 각 color pattern (n_voxels,)의 correlation
       - 평균 correlation

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        metric: 'procrustes' or 'correlation'

    Returns:
        stability: Scalar stability measure
        details: Dict with additional info
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Split runs
    half1_indices = list(range(n_runs // 2))
    half2_indices = list(range(n_runs // 2, n_runs))

    half1 = amplitudes[half1_indices].mean(axis=0)  # (n_colors, n_voxels)
    half2 = amplitudes[half2_indices].mean(axis=0)  # (n_colors, n_voxels)

    if metric == 'procrustes':
        # Procrustes analysis: pattern geometry matching
        mtx1, mtx2, disparity = procrustes(half1, half2)

        # Disparity: 낮을수록 좋음 → convert to similarity
        stability = 1 - disparity  # 0~1 scale

        details = {
            'disparity': disparity,
            'mtx1_shape': mtx1.shape,
            'mtx2_shape': mtx2.shape
        }

    elif metric == 'correlation':
        # Color-wise pattern correlation
        correlations = []
        for c in range(n_colors):
            corr, _ = spearmanr(half1[c, :], half2[c, :])
            correlations.append(corr)

        stability = np.mean(correlations)
        details = {
            'per_color_corr': correlations,
            'min_corr': np.min(correlations),
            'max_corr': np.max(correlations)
        }

    else:
        raise ValueError(f"Unknown metric: {metric}")

    return stability, details

def compute_rdm(amplitudes):
    """RDM 계산"""
    n_runs, n_colors, n_voxels = amplitudes.shape
    mean_pattern = amplitudes.mean(axis=0)  # (n_colors, n_voxels)
    rdm = 1 - np.corrcoef(mean_pattern)
    return rdm

def compute_rdm_similarity(rdm1, rdm2):
    """RDM correlation"""
    triu_indices = np.triu_indices(rdm1.shape[0], k=1)
    vec1 = rdm1[triu_indices]
    vec2 = rdm2[triu_indices]
    corr, pval = spearmanr(vec1, vec2)
    return corr, pval

# ============================================================================
# Multi-Metric Analysis
# ============================================================================

def compute_all_metrics(amplitudes):
    """
    여러 consistency metrics를 동시에 계산

    **Metrics**:
    1. RDM correlation (기존 방법)
    2. Pattern geometry (Procrustes)
    3. Pattern correlation (Color-wise)

    Returns:
        results: Dict with all metrics
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Split runs
    half1_indices = list(range(n_runs // 2))
    half2_indices = list(range(n_runs // 2, n_runs))

    amplitudes_half1 = amplitudes[half1_indices]
    amplitudes_half2 = amplitudes[half2_indices]

    # Metric 1: RDM correlation
    rdm_half1 = compute_rdm(amplitudes_half1)
    rdm_half2 = compute_rdm(amplitudes_half2)
    rdm_corr, rdm_pval = compute_rdm_similarity(rdm_half1, rdm_half2)

    # Metric 2: Procrustes (pattern geometry)
    procrustes_stab, procrustes_details = compute_pattern_stability(
        amplitudes, metric='procrustes'
    )

    # Metric 3: Pattern correlation (color-wise)
    pattern_corr, pattern_details = compute_pattern_stability(
        amplitudes, metric='correlation'
    )

    return {
        'rdm_correlation': rdm_corr,
        'rdm_pvalue': rdm_pval,
        'procrustes_stability': procrustes_stab,
        'procrustes_disparity': procrustes_details['disparity'],
        'pattern_correlation': pattern_corr,
        'pattern_corr_min': pattern_details['min_corr'],
        'pattern_corr_max': pattern_details['max_corr'],
        'n_voxels': n_voxels,
    }

# ============================================================================
# Load Data
# ============================================================================

def load_subject_amplitudes(subject_id, roi, timestamp, dataset='deoblique_v2'):
    """
    개별 피험자 amplitudes 로드

    **Actual path structure:**
    derivatives/BH2009_{dataset}/{timestamp}/sm*_sub-{ID}_{roi}_*/amplitudes_z.npy

    Example:
    derivatives/BH2009_deoblique_v2/baseline81_deob_determin/sm6.0_hpYe_moCo_ccNo_drNo_stTr_sub-02_hV4_None/
    """
    base_dir = Path('/scratch/connectome/haba6030/colorBlind')

    # Path: derivatives/BH2009_{dataset}/{timestamp}/
    dataset_dir = base_dir / 'derivatives' / f'BH2009_{dataset}' / timestamp

    if not dataset_dir.exists():
        raise FileNotFoundError(
            f"Dataset directory not found: {dataset_dir}\n"
            f"  Expected: derivatives/BH2009_{dataset}/{timestamp}/"
        )

    # Pattern: sm*_sub-{ID}_{roi}_*
    pattern = f'*_sub-{subject_id}_{roi}_*'
    matches = sorted(dataset_dir.glob(pattern))

    if not matches:
        raise FileNotFoundError(
            f"No results for sub-{subject_id} {roi}\n"
            f"  Searched: {dataset_dir}/{pattern}\n"
            f"  Available: {list(dataset_dir.glob(f'*_sub-{subject_id}_*'))[:5]}"
        )

    # Use first match (should only be one)
    result_dir = matches[0]

    amp_file = result_dir / 'amplitudes_z.npy'
    if not amp_file.exists():
        raise FileNotFoundError(
            f"amplitudes_z.npy not found in {result_dir}\n"
            f"  Available: {list(result_dir.glob('*.npy'))}"
        )

    amplitudes = np.load(amp_file)
    return amplitudes, result_dir

# ============================================================================
# Main Analysis
# ============================================================================

def analyze_subject(subject_id, roi, timestamp, dataset):
    """단일 피험자 multi-metric 분석"""
    try:
        amplitudes, result_dir = load_subject_amplitudes(
            subject_id, roi, timestamp, dataset
        )

        results = compute_all_metrics(amplitudes)

        print(f"  sub-{subject_id}:")
        print(f"    RDM correlation: {results['rdm_correlation']:.3f}")
        print(f"    Procrustes stability: {results['procrustes_stability']:.3f}")
        print(f"    Pattern correlation: {results['pattern_correlation']:.3f}")

        return results

    except FileNotFoundError as e:
        print(f"  sub-{subject_id}: ⚠️  {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Option 1B: Pattern Consistency')
    parser.add_argument('--timestamp', type=str, required=True)
    parser.add_argument('--dataset', type=str, default='deoblique_v2')
    parser.add_argument('--hc-subjects', nargs='+', required=True)
    parser.add_argument('--rois', nargs='+', required=True)
    args = parser.parse_args()

    print("="*80)
    print("Option 1B: Pattern-Based Consistency Analysis")
    print("="*80)
    print(f"Timestamp: {args.timestamp}")
    print(f"Dataset: {args.dataset}")
    print(f"Subjects: {args.hc_subjects}")
    print(f"ROIs: {args.rois}")
    print("")

    # Results storage
    all_results = []

    # Analyze each ROI
    for roi in args.rois:
        print(f"\n{'='*80}")
        print(f"ROI: {roi}")
        print(f"{'='*80}")

        roi_results = []

        for subject_id in args.hc_subjects:
            result = analyze_subject(subject_id, roi, args.timestamp, args.dataset)

            if result is not None:
                roi_results.append({
                    'subject': subject_id,
                    'roi': roi,
                    **result
                })

        # ROI summary
        if len(roi_results) > 0:
            rdm_corrs = [r['rdm_correlation'] for r in roi_results]
            procrustes = [r['procrustes_stability'] for r in roi_results]
            patterns = [r['pattern_correlation'] for r in roi_results]

            print(f"\n  {roi} Summary:")
            print(f"    RDM correlation: {np.mean(rdm_corrs):.3f} ± {np.std(rdm_corrs):.3f}")
            print(f"    Procrustes stability: {np.mean(procrustes):.3f} ± {np.std(procrustes):.3f}")
            print(f"    Pattern correlation: {np.mean(patterns):.3f} ± {np.std(patterns):.3f}")

        all_results.extend(roi_results)

    # Save results
    output_dir = Path('/scratch/connectome/haba6030/colorBlind/results/group_level/option1b_pattern_consistency')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Summary CSV
    df = pd.DataFrame(all_results)
    df.to_csv(output_dir / 'summary_results.csv', index=False)

    print(f"\n{'='*80}")
    print("Results saved to:")
    print(f"  {output_dir / 'summary_results.csv'}")
    print("="*80)

    # Diagnostic insights (check if DataFrame is not empty)
    if len(df) == 0:
        print("\n⚠️  No results to analyze")
        return

    print(f"\n{'='*80}")
    print("Diagnostic Insights:")
    print("="*80)

    mean_rdm = df['rdm_correlation'].mean()
    mean_procrustes = df['procrustes_stability'].mean()
    mean_pattern = df['pattern_correlation'].mean()

    if mean_rdm > 0.5 and mean_procrustes > 0.8:
        print("✅ Both RDM and pattern geometry are stable")
        print("   → Individual representations are consistent")
        print("   → Proceed to group analysis")

    elif mean_rdm > 0.5 and mean_procrustes < 0.8:
        print("⚠️  RDM stable but pattern geometry unstable")
        print("   → Color distances preserved, but not exact patterns")
        print("   → May indicate rotation/scaling differences")
        print("   → SRM may help (finds shared geometry)")

    elif mean_rdm < 0.5 and mean_pattern > 0.5:
        print("⚠️  Individual patterns stable, but RDM unstable")
        print("   → Voxels respond consistently, but color structure varies")
        print("   → May need voxel selection refinement")

    else:
        print("❌ Low consistency across all metrics")
        print("   → Individual representations unstable")
        print("   → Re-evaluate preprocessing or feature selection")

if __name__ == '__main__':
    main()
