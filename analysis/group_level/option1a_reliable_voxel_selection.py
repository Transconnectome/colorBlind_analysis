#!/usr/bin/env python3
"""
Option 1A: Reliability-Guided Voxel Selection
==============================================

목적: Baseline에서 선택된 voxels 중 test-retest reliable한 것만 선택

배경:
- Individual decoding이 잘 되었다면 reliable voxels가 있어야 함
- 하지만 모든 selected voxels가 reliable한 것은 아님
- Noisy voxels이 group analysis의 consistency를 해침

접근:
1. 각 voxel의 split-half reliability 계산
2. Top-k% most reliable voxels만 선택
3. 이 voxels로 RDM 재계산
4. Group consistency 향상 기대

저자: Claude Code
날짜: 2025-12-17
"""

import numpy as np
import argparse
from pathlib import Path
from scipy.stats import spearmanr
from scipy.spatial.distance import pdist, squareform
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

# ============================================================================
# Voxel-wise Reliability
# ============================================================================

def compute_voxel_reliability(amplitudes, method='correlation'):
    """
    각 voxel의 test-retest reliability 계산

    **방법**:
    1. Runs를 두 half로 분할
    2. 각 voxel에 대해 8-color pattern 추출
    3. Half1 vs Half2 pattern correlation 계산

    **해석**:
    - High reliability (>0.7): 매우 stable한 voxel
    - Moderate (0.4-0.7): 적당히 stable
    - Low (<0.4): Noisy voxel → 제거 고려

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        method: 'correlation' or 'icc'

    Returns:
        reliability: (n_voxels,) 각 voxel의 reliability
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Split runs
    half1_indices = list(range(n_runs // 2))
    half2_indices = list(range(n_runs // 2, n_runs))

    # Average across runs for each half
    half1 = amplitudes[half1_indices].mean(axis=0)  # (n_colors, n_voxels)
    half2 = amplitudes[half2_indices].mean(axis=0)  # (n_colors, n_voxels)

    # Voxel-wise correlation
    reliability = np.zeros(n_voxels)
    for v in range(n_voxels):
        pattern1 = half1[:, v]  # (n_colors,)
        pattern2 = half2[:, v]  # (n_colors,)

        if method == 'correlation':
            corr, _ = spearmanr(pattern1, pattern2)
            reliability[v] = corr
        else:
            raise NotImplementedError

    return reliability

def select_reliable_voxels(amplitudes, percentile=50, min_reliability=0.3):
    """
    Test-retest reliable voxels만 선택

    **선택 기준**:
    1. Reliability > min_reliability (기본: 0.3)
    2. Top percentile% (기본: 50% → 상위 절반)

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        percentile: Top k% voxels to keep (0-100)
        min_reliability: Minimum reliability threshold

    Returns:
        selected_indices: Indices of selected voxels
        reliability_scores: All voxel reliability scores
    """
    # Compute reliability
    reliability_scores = compute_voxel_reliability(amplitudes)

    # Filter by minimum reliability
    valid_mask = reliability_scores >= min_reliability

    # Select top percentile among valid voxels
    if valid_mask.sum() == 0:
        print(f"  ⚠️  No voxels with reliability >= {min_reliability}")
        # Fallback: use all voxels
        selected_indices = np.arange(len(reliability_scores))
    else:
        threshold = np.percentile(reliability_scores[valid_mask], 100 - percentile)
        selected_mask = (reliability_scores >= threshold) & valid_mask
        selected_indices = np.where(selected_mask)[0]

    return selected_indices, reliability_scores

# ============================================================================
# RDM Computation
# ============================================================================

def compute_rdm(amplitudes):
    """
    Representational Dissimilarity Matrix (RDM) 계산

    **공식**:
    RDM[i,j] = 1 - correlation(color_i, color_j)

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        rdm: (n_colors, n_colors)
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Average across runs
    mean_pattern = amplitudes.mean(axis=0)  # (n_colors, n_voxels)

    # Compute pairwise correlation
    rdm = 1 - np.corrcoef(mean_pattern)  # (n_colors, n_colors)

    return rdm

def compute_rdm_similarity(rdm1, rdm2):
    """RDM 간 Spearman correlation"""
    triu_indices = np.triu_indices(rdm1.shape[0], k=1)
    vec1 = rdm1[triu_indices]
    vec2 = rdm2[triu_indices]

    corr, pval = spearmanr(vec1, vec2)
    return corr, pval

# ============================================================================
# Split-Half Analysis with Voxel Selection
# ============================================================================

def compute_split_half_with_selection(amplitudes, percentile=50, min_reliability=0.3):
    """
    Reliable voxels만 사용한 split-half reliability

    **절차**:
    1. 전체 voxels에서 reliable ones 선택
    2. 선택된 voxels로 RDM 계산
    3. Split-half correlation

    Returns:
        results: Dict with:
            - reliability_all: 모든 voxels 사용한 경우
            - reliability_selected: Reliable voxels만 사용한 경우
            - n_voxels_original: 원래 voxel 수
            - n_voxels_selected: 선택된 voxel 수
            - voxel_reliability_scores: 각 voxel의 reliability
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Step 1: Select reliable voxels (전체 데이터로)
    selected_indices, reliability_scores = select_reliable_voxels(
        amplitudes, percentile=percentile, min_reliability=min_reliability
    )

    # Step 2: Split runs
    half1_indices = list(range(n_runs // 2))
    half2_indices = list(range(n_runs // 2, n_runs))

    amplitudes_half1 = amplitudes[half1_indices]
    amplitudes_half2 = amplitudes[half2_indices]

    # Step 3a: RDM with ALL voxels
    rdm_half1_all = compute_rdm(amplitudes_half1)
    rdm_half2_all = compute_rdm(amplitudes_half2)
    reliability_all, pval_all = compute_rdm_similarity(rdm_half1_all, rdm_half2_all)

    # Step 3b: RDM with SELECTED voxels only
    amplitudes_half1_selected = amplitudes_half1[:, :, selected_indices]
    amplitudes_half2_selected = amplitudes_half2[:, :, selected_indices]

    rdm_half1_sel = compute_rdm(amplitudes_half1_selected)
    rdm_half2_sel = compute_rdm(amplitudes_half2_selected)
    reliability_selected, pval_sel = compute_rdm_similarity(rdm_half1_sel, rdm_half2_sel)

    return {
        'reliability_all': reliability_all,
        'pval_all': pval_all,
        'reliability_selected': reliability_selected,
        'pval_selected': pval_sel,
        'n_voxels_original': n_voxels,
        'n_voxels_selected': len(selected_indices),
        'voxel_reliability_scores': reliability_scores,
        'selected_voxel_indices': selected_indices,
        'rdm_half1_all': rdm_half1_all,
        'rdm_half2_all': rdm_half2_all,
        'rdm_half1_selected': rdm_half1_sel,
        'rdm_half2_selected': rdm_half2_sel,
    }

# ============================================================================
# Load Data
# ============================================================================

def load_subject_amplitudes(subject_id, roi, timestamp, dataset='deoblique_v2'):
    """
    개별 피험자의 amplitudes 로드

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
# Analysis
# ============================================================================

def analyze_subject(subject_id, roi, timestamp, dataset, percentile=50):
    """단일 피험자 분석"""
    try:
        amplitudes, result_dir = load_subject_amplitudes(
            subject_id, roi, timestamp, dataset
        )

        results = compute_split_half_with_selection(
            amplitudes, percentile=percentile
        )

        print(f"  sub-{subject_id}:")
        print(f"    All voxels ({results['n_voxels_original']}): r={results['reliability_all']:.3f}")
        print(f"    Selected voxels ({results['n_voxels_selected']}): r={results['reliability_selected']:.3f}")
        print(f"    Improvement: {results['reliability_selected'] - results['reliability_all']:+.3f}")

        return results

    except FileNotFoundError as e:
        print(f"  sub-{subject_id}: ⚠️  {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Option 1A: Reliability-Guided Voxel Selection')
    parser.add_argument('--timestamp', type=str, required=True)
    parser.add_argument('--dataset', type=str, default='deoblique_v2')
    parser.add_argument('--hc-subjects', nargs='+', required=True)
    parser.add_argument('--rois', nargs='+', required=True)
    parser.add_argument('--percentile', type=int, default=50,
                       help='Top k%% reliable voxels to keep (default: 50)')
    args = parser.parse_args()

    print("="*80)
    print("Option 1A: Reliability-Guided Voxel Selection")
    print("="*80)
    print(f"Timestamp: {args.timestamp}")
    print(f"Dataset: {args.dataset}")
    print(f"Subjects: {args.hc_subjects}")
    print(f"ROIs: {args.rois}")
    print(f"Voxel selection: Top {args.percentile}% most reliable")
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
            result = analyze_subject(
                subject_id, roi, args.timestamp, args.dataset,
                percentile=args.percentile
            )

            if result is not None:
                roi_results.append({
                    'subject': subject_id,
                    'roi': roi,
                    **result
                })

        # ROI summary
        if len(roi_results) > 0:
            reliability_all = [r['reliability_all'] for r in roi_results]
            reliability_sel = [r['reliability_selected'] for r in roi_results]

            print(f"\n  {roi} Summary:")
            print(f"    All voxels: {np.mean(reliability_all):.3f} ± {np.std(reliability_all):.3f}")
            print(f"    Selected voxels: {np.mean(reliability_sel):.3f} ± {np.std(reliability_sel):.3f}")
            print(f"    Mean improvement: {np.mean(reliability_sel) - np.mean(reliability_all):+.3f}")

        all_results.extend(roi_results)

    # Save results
    output_dir = Path('/scratch/connectome/haba6030/colorBlind/results/group_level/option1a_reliable_voxels')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Summary CSV
    summary_data = []
    for r in all_results:
        summary_data.append({
            'subject': r['subject'],
            'roi': r['roi'],
            'reliability_all_voxels': r['reliability_all'],
            'reliability_selected_voxels': r['reliability_selected'],
            'improvement': r['reliability_selected'] - r['reliability_all'],
            'n_voxels_original': r['n_voxels_original'],
            'n_voxels_selected': r['n_voxels_selected'],
            'selection_ratio': r['n_voxels_selected'] / r['n_voxels_original']
        })

    df = pd.DataFrame(summary_data)
    df.to_csv(output_dir / 'summary_results.csv', index=False)

    # Save selected voxel indices for each subject/ROI (for use in Option 2/3)
    indices_dir = output_dir / 'selected_voxel_indices'
    indices_dir.mkdir(exist_ok=True)

    for r in all_results:
        subject_id = r['subject']
        roi = r['roi']
        indices = r['selected_voxel_indices']
        reliability_scores = r['voxel_reliability_scores']

        # Save indices
        np.save(
            indices_dir / f'sub-{subject_id}_{roi}_indices.npy',
            indices
        )
        # Save all voxel reliability scores
        np.save(
            indices_dir / f'sub-{subject_id}_{roi}_reliability_scores.npy',
            reliability_scores
        )

    print(f"\n{'='*80}")
    print("Results saved to:")
    print(f"  {output_dir / 'summary_results.csv'}")
    print(f"  {indices_dir}/ (voxel indices)")
    print("="*80)

    # Key insight (check if DataFrame is not empty)
    if len(df) == 0:
        print("\n⚠️  No results to analyze")
        return

    mean_improvement = df['improvement'].mean()
    if mean_improvement > 0.1:
        print(f"\n✅ Voxel selection improves reliability by {mean_improvement:.3f}")
        print("   → Many non-reliable voxels in baseline selection")
        print("   → Use selected voxels for group analysis")
    elif mean_improvement > 0:
        print(f"\n⚠️  Modest improvement ({mean_improvement:.3f})")
        print("   → Most baseline voxels are already reliable")
    else:
        print(f"\n❌ No improvement ({mean_improvement:.3f})")
        print("   → Voxel reliability not the issue")
        print("   → Consider pattern-level analysis instead")

if __name__ == '__main__':
    main()
