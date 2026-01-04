#!/usr/bin/env python3
"""
phase1a_rdm_guided.py
=====================

Phase 1A-alt: RDM-guided Voxel Selection

**목적**: RDM consistency를 **직접 최대화**하는 voxel subset 선택

**Jaccard-based와의 차이**:
- Jaccard: 해부학적 일치 (같은 위치 복셀 선택했나?)
- RDM-guided: 기능적 일치 (inter-subject RDM similarity 높은 복셀)

**방법**: Per-voxel RDM Contribution
1. 각 복셀에 대해 단일 복셀 RDM 계산 (8×8, 색상 간 distance)
2. 피험자 간 RDM similarity (Spearman correlation) 계산
3. High consistency voxels를 Top K로 선택

**예상 결과**:
- Jaccard ≈ RDM-guided: 해부학/기능 일치 (이상적)
- Jaccard ≠ RDM-guided: Distributed coding, functional importance > location

Usage:
    python analysis/group_level/phase1a_rdm_guided.py \
        --roi V1 \
        --timestamp baseline32_deob_determin \
        --k-voxels 50

Author: Claude Code
Date: 2025-12-17
"""

import sys
from pathlib import Path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import glob
from scipy.stats import spearmanr
from sklearn.feature_selection import f_classif

# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='Phase 1A-alt: RDM-guided Voxel Selection')
    parser.add_argument('--roi', type=str, required=True)
    parser.add_argument('--timestamp', type=str, default='baseline32_deob_determin')
    parser.add_argument('--dataset', type=str, default='deoblique_v2')
    parser.add_argument('--subjects', type=str, nargs='+',
                        default=['01', '02', '03', '05', '06', '07'])
    parser.add_argument('--k-voxels', type=int, default=50,
                        help='Number of voxels to select')
    parser.add_argument('--output-dir', type=str, default=None)
    return parser.parse_args()

# ============================================================================
# Data Loading
# ============================================================================

def load_subject_amplitudes(subject_id, roi, timestamp, dataset='deoblique_v2'):
    """
    피험자의 amplitudes_z 로드

    Returns:
        amplitudes: (n_runs, n_colors, n_voxels)
    """
    base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
    pattern = str(base_path / f'sm*_sub-{subject_id}_{roi}_*')

    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"No results for sub-{subject_id} {roi}")

    result_dir = Path(matches[0])
    amp_file = result_dir / 'amplitudes_z.npy'

    if not amp_file.exists():
        raise FileNotFoundError(f"No amplitudes_z.npy in {result_dir}")

    amplitudes = np.load(amp_file)  # (n_runs, n_colors, n_voxels)
    print(f"  sub-{subject_id}: {amplitudes.shape}")

    return amplitudes

# ============================================================================
# RDM Computation (Single Voxel)
# ============================================================================

def compute_single_voxel_rdm(amplitudes, voxel_idx):
    """
    단일 복셀에 대한 RDM 계산

    **핵심 아이디어**:
    이 복셀이 8가지 색상을 얼마나 잘 구별하는가?

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        voxel_idx: 단일 복셀 인덱스

    Returns:
        rdm: (8, 8) dissimilarity matrix for this voxel
    """
    # 단일 복셀 추출: (n_runs, n_colors, 1)
    amp_v = amplitudes[:, :, voxel_idx]

    # Run 평균: (n_colors, 1) → (n_colors,)
    amp_v_avg = amp_v.mean(axis=0).squeeze()

    # RDM 계산: 8×8 행렬
    n_colors = amp_v_avg.shape[0]
    rdm = np.zeros((n_colors, n_colors))

    for i in range(n_colors):
        for j in range(n_colors):
            if i == j:
                rdm[i, j] = 0.0
            else:
                # 단일 값이므로 absolute difference 사용
                # (Spearman은 2개 이상 필요하므로 불가능)
                rdm[i, j] = np.abs(amp_v_avg[i] - amp_v_avg[j])

    return rdm

def compute_multi_voxel_rdm(amplitudes, voxel_indices):
    """
    여러 복셀에 대한 RDM 계산 (Spearman correlation 사용)

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        voxel_indices: List of voxel indices

    Returns:
        rdm: (8, 8) dissimilarity matrix
    """
    # 복셀 선택
    amp_selected = amplitudes[:, :, voxel_indices]

    # Run 평균: (n_colors, n_voxels)
    amp_avg = amp_selected.mean(axis=0)

    # RDM 계산
    n_colors = amp_avg.shape[0]
    rdm = np.zeros((n_colors, n_colors))

    for i in range(n_colors):
        for j in range(n_colors):
            if i == j:
                rdm[i, j] = 0.0
            else:
                # Spearman correlation across voxels
                if len(voxel_indices) > 1:
                    corr, _ = spearmanr(amp_avg[i, :], amp_avg[j, :])
                else:
                    # Single voxel: use absolute difference
                    corr = -np.abs(amp_avg[i, 0] - amp_avg[j, 0])
                rdm[i, j] = 1 - corr

    return rdm

# ============================================================================
# Per-voxel RDM Contribution
# ============================================================================

def compute_voxel_rdm_contributions(amplitudes_dict, subjects, n_voxels):
    """
    각 복셀의 inter-subject RDM consistency 기여도 계산

    **핵심 질문**: "이 복셀이 피험자 간 일관된 색상 표상을 제공하는가?"

    **방법**:
    1. 각 복셀에 대해, 모든 피험자의 single-voxel RDM 계산
    2. 피험자 간 RDM similarity (Spearman correlation) 계산
    3. 평균 similarity = 이 복셀의 consistency score

    **해석**:
    - High score (>0.5): 피험자 간 일관된 색상 구별 패턴
    - Low score (<0.3): 개인차 큼, 일관되지 않은 표상

    Args:
        amplitudes_dict: Dict[subject_id -> (n_runs, n_colors, n_voxels)]
        subjects: List of subject IDs
        n_voxels: Total number of voxels

    Returns:
        voxel_scores: (n_voxels,) - RDM consistency score per voxel
        voxel_details: List of dicts with detailed statistics
    """
    print(f"\nComputing per-voxel RDM contributions ({n_voxels} voxels)...")

    voxel_scores = np.zeros(n_voxels)
    voxel_details = []

    # Progress tracking
    report_interval = max(1, n_voxels // 20)  # Report every 5%

    for v in range(n_voxels):
        if v % report_interval == 0:
            print(f"  Progress: {v}/{n_voxels} ({100*v/n_voxels:.0f}%)")

        # Step 1: 각 피험자의 single-voxel RDM 계산
        rdms_v = []
        for sub in subjects:
            rdm_v = compute_single_voxel_rdm(amplitudes_dict[sub], v)
            rdms_v.append(rdm_v)

        # Step 2: Inter-subject RDM similarity 계산
        similarities = []
        for i in range(len(subjects)):
            for j in range(i+1, len(subjects)):
                # RDM flatten (upper triangle)
                rdm_i_flat = rdms_v[i][np.triu_indices(8, k=1)]
                rdm_j_flat = rdms_v[j][np.triu_indices(8, k=1)]

                # Spearman correlation
                if len(rdm_i_flat) > 1:
                    corr, _ = spearmanr(rdm_i_flat, rdm_j_flat)
                    if not np.isnan(corr):
                        similarities.append(corr)

        # Step 3: 평균 similarity = voxel score
        if len(similarities) > 0:
            voxel_scores[v] = np.mean(similarities)
        else:
            voxel_scores[v] = 0.0

        # 상세 정보 저장
        voxel_details.append({
            'voxel_idx': v,
            'rdm_consistency': voxel_scores[v],
            'n_comparisons': len(similarities),
            'std': np.std(similarities) if len(similarities) > 0 else 0.0
        })

    print(f"  Completed: {n_voxels}/{n_voxels} (100%)\n")

    return voxel_scores, voxel_details

# ============================================================================
# Voxel Selection
# ============================================================================

def select_top_k_voxels(voxel_scores, k):
    """
    Top K voxels by RDM consistency

    Returns:
        selected_indices: (k,) Top K voxel indices
    """
    selected_indices = np.argsort(voxel_scores)[::-1][:k]
    return selected_indices

# ============================================================================
# Comparison with Jaccard-based
# ============================================================================

def compare_with_jaccard(rdm_guided_voxels, roi, timestamp):
    """
    Jaccard-based selection과 비교

    Returns:
        comparison_results: Dict with overlap statistics
    """
    results = {
        'jaccard_A_overlap': 0,
        'jaccard_B_overlap': 0,
        'jaccard_A_voxels': None,
        'jaccard_B_voxels': None
    }

    # Try to load Jaccard-based voxels
    for scenario_name in ['A_all_subjects', 'B_sufficient_voxels']:
        voxel_file = Path(f'derivatives/group_level/{timestamp}/{roi}/voxel_overlap/{scenario_name}/common_voxels_indices.npy')

        if voxel_file.exists():
            jaccard_voxels = np.load(voxel_file)

            if len(jaccard_voxels) > 0:
                # Compute overlap
                overlap = len(set(rdm_guided_voxels) & set(jaccard_voxels))
                overlap_ratio = overlap / len(rdm_guided_voxels) if len(rdm_guided_voxels) > 0 else 0

                if scenario_name == 'A_all_subjects':
                    results['jaccard_A_overlap'] = overlap_ratio
                    results['jaccard_A_voxels'] = jaccard_voxels
                else:
                    results['jaccard_B_overlap'] = overlap_ratio
                    results['jaccard_B_voxels'] = jaccard_voxels

    return results

# ============================================================================
# Visualization
# ============================================================================

def plot_voxel_score_distribution(voxel_scores, selected_indices, output_dir):
    """RDM consistency score 분포"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Histogram
    ax = axes[0]
    ax.hist(voxel_scores, bins=50, alpha=0.7, edgecolor='black')
    ax.axvline(voxel_scores[selected_indices].min(),
               color='red', linestyle='--', linewidth=2,
               label=f'Selection threshold')
    ax.set_xlabel('RDM Consistency Score', fontsize=12)
    ax.set_ylabel('Number of Voxels', fontsize=12)
    ax.set_title('Distribution of Voxel RDM Consistency', fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)

    # Ranked plot
    ax = axes[1]
    sorted_scores = np.sort(voxel_scores)[::-1]
    ax.plot(sorted_scores, linewidth=2)
    ax.axvline(len(selected_indices), color='red', linestyle='--', linewidth=2,
               label=f'Top {len(selected_indices)} selected')
    ax.axhline(sorted_scores[len(selected_indices)-1],
               color='red', linestyle=':', alpha=0.5)
    ax.set_xlabel('Voxel Rank', fontsize=12)
    ax.set_ylabel('RDM Consistency Score', fontsize=12)
    ax.set_title('Ranked Voxel Scores', fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3)

    plt.tight_layout()
    fig_path = output_dir / 'voxel_score_distribution.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Score distribution: {fig_path}")

def plot_comparison_venn(rdm_guided, comparison_results, output_dir):
    """Jaccard vs RDM-guided Venn diagram"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for idx, scenario in enumerate(['A', 'B']):
        ax = axes[idx]

        jaccard_key = f'jaccard_{scenario}_voxels'
        overlap_key = f'jaccard_{scenario}_overlap'

        if comparison_results[jaccard_key] is not None:
            jaccard_voxels = set(comparison_results[jaccard_key])
            rdm_voxels = set(rdm_guided)

            only_jaccard = len(jaccard_voxels - rdm_voxels)
            only_rdm = len(rdm_voxels - jaccard_voxels)
            both = len(jaccard_voxels & rdm_voxels)

            # Simple bar plot instead of venn
            categories = ['Jaccard\nonly', 'Both', 'RDM\nonly']
            values = [only_jaccard, both, only_rdm]
            colors = ['skyblue', 'lightgreen', 'coral']

            bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=1.5)

            # Add percentage labels
            for bar, val in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{val}\n({val/len(rdm_voxels)*100:.1f}%)',
                       ha='center', va='bottom', fontsize=11, fontweight='bold')

            ax.set_ylabel('Number of Voxels', fontsize=12)
            ax.set_title(f'Scenario {scenario}: Jaccard vs RDM-guided\nOverlap: {comparison_results[overlap_key]:.1%}',
                        fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
        else:
            ax.text(0.5, 0.5, f'Scenario {scenario}\nNo Jaccard data',
                   ha='center', va='center', fontsize=14)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')

    plt.tight_layout()
    fig_path = output_dir / 'comparison_venn.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Comparison plot: {fig_path}")

# ============================================================================
# Main
# ============================================================================

def main():
    args = parse_args()

    print(f"\n{'='*80}")
    print(f"Phase 1A-alt: RDM-guided Voxel Selection")
    print(f"{'='*80}")
    print(f"ROI: {args.roi}")
    print(f"Timestamp: {args.timestamp}")
    print(f"Subjects: {', '.join(args.subjects)}")
    print(f"Target K: {args.k_voxels}")
    print()

    # Output directory
    if args.output_dir is None:
        output_dir = Path(f"derivatives/group_level/{args.timestamp}/{args.roi}/voxel_overlap/RDM_guided")
    else:
        output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output: {output_dir}\n")

    # ========================================================================
    # Load amplitudes
    # ========================================================================
    print(f"Loading amplitudes...")
    amplitudes_dict = {}
    n_voxels = None

    for subject_id in args.subjects:
        try:
            amplitudes = load_subject_amplitudes(
                subject_id, args.roi, args.timestamp, args.dataset
            )
            amplitudes_dict[subject_id] = amplitudes

            if n_voxels is None:
                n_voxels = amplitudes.shape[2]
        except Exception as e:
            print(f"  ✗ sub-{subject_id}: {e}")

    if len(amplitudes_dict) == 0:
        raise RuntimeError("No subjects loaded!")

    subjects = list(amplitudes_dict.keys())
    print(f"\n✅ Loaded {len(subjects)} subjects ({n_voxels} voxels per subject)\n")

    # ========================================================================
    # Compute per-voxel RDM contributions
    # ========================================================================
    voxel_scores, voxel_details = compute_voxel_rdm_contributions(
        amplitudes_dict, subjects, n_voxels
    )

    # Statistics
    print(f"RDM Consistency Scores:")
    print(f"  Mean: {voxel_scores.mean():.3f} ± {voxel_scores.std():.3f}")
    print(f"  Range: [{voxel_scores.min():.3f}, {voxel_scores.max():.3f}]")
    print(f"  Median: {np.median(voxel_scores):.3f}\n")

    # ========================================================================
    # Select Top K voxels
    # ========================================================================
    k_actual = min(args.k_voxels, n_voxels)
    print(f"Selecting top {k_actual} voxels by RDM consistency...")

    selected_indices = select_top_k_voxels(voxel_scores, k_actual)
    selected_scores = voxel_scores[selected_indices]

    print(f"  Selected voxels: {len(selected_indices)}")
    print(f"  Score range: [{selected_scores.min():.3f}, {selected_scores.max():.3f}]")
    print(f"  Mean score: {selected_scores.mean():.3f}\n")

    # ========================================================================
    # Compare with Jaccard-based
    # ========================================================================
    print(f"Comparing with Jaccard-based selection...")
    comparison_results = compare_with_jaccard(selected_indices, args.roi, args.timestamp)

    if comparison_results['jaccard_A_voxels'] is not None:
        print(f"  Scenario A overlap: {comparison_results['jaccard_A_overlap']:.1%}")
    if comparison_results['jaccard_B_voxels'] is not None:
        print(f"  Scenario B overlap: {comparison_results['jaccard_B_overlap']:.1%}")
    print()

    # ========================================================================
    # Save results
    # ========================================================================
    print(f"Saving results...")

    # Selected voxels
    np.save(output_dir / 'rdm_guided_voxels_indices.npy', selected_indices)

    # All scores
    np.save(output_dir / 'voxel_rdm_scores.npy', voxel_scores)

    # Details
    details_df = pd.DataFrame(voxel_details)
    details_df = details_df.sort_values('rdm_consistency', ascending=False)
    details_df.to_csv(output_dir / 'voxel_rdm_details.csv', index=False)

    # Statistics
    with open(output_dir / 'rdm_guided_statistics.txt', 'w') as f:
        f.write(f"Phase 1A-alt: RDM-guided Voxel Selection\n")
        f.write(f"{'='*80}\n\n")
        f.write(f"ROI: {args.roi}\n")
        f.write(f"Timestamp: {args.timestamp}\n")
        f.write(f"Subjects: {', '.join(subjects)}\n")
        f.write(f"Total voxels: {n_voxels}\n")
        f.write(f"Selected: {len(selected_indices)}\n\n")
        f.write(f"RDM Consistency Scores (all voxels):\n")
        f.write(f"  Mean: {voxel_scores.mean():.3f} ± {voxel_scores.std():.3f}\n")
        f.write(f"  Range: [{voxel_scores.min():.3f}, {voxel_scores.max():.3f}]\n")
        f.write(f"  Median: {np.median(voxel_scores):.3f}\n\n")
        f.write(f"Selected Voxels:\n")
        f.write(f"  Mean score: {selected_scores.mean():.3f}\n")
        f.write(f"  Score range: [{selected_scores.min():.3f}, {selected_scores.max():.3f}]\n\n")
        f.write(f"Comparison with Jaccard-based:\n")
        if comparison_results['jaccard_A_voxels'] is not None:
            f.write(f"  Scenario A overlap: {comparison_results['jaccard_A_overlap']:.1%}\n")
        if comparison_results['jaccard_B_voxels'] is not None:
            f.write(f"  Scenario B overlap: {comparison_results['jaccard_B_overlap']:.1%}\n")

    print(f"  ✓ rdm_guided_voxels_indices.npy ({len(selected_indices)} voxels)")
    print(f"  ✓ voxel_rdm_scores.npy ({n_voxels} scores)")
    print(f"  ✓ voxel_rdm_details.csv")
    print(f"  ✓ rdm_guided_statistics.txt\n")

    # ========================================================================
    # Visualization
    # ========================================================================
    print(f"Creating visualizations...")
    plot_voxel_score_distribution(voxel_scores, selected_indices, output_dir)
    plot_comparison_venn(selected_indices, comparison_results, output_dir)

    # ========================================================================
    # Summary
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Phase 1A-alt Complete!")
    print(f"{'='*80}")
    print(f"Results: {output_dir}")
    print(f"\nKey findings:")
    print(f"  Selected: {len(selected_indices)} voxels (RDM consistency: {selected_scores.mean():.3f})")

    if comparison_results['jaccard_B_overlap'] > 0:
        overlap = comparison_results['jaccard_B_overlap']
        if overlap > 0.7:
            print(f"\n✅ HIGH overlap with Jaccard ({overlap:.1%}) - Anatomical/Functional alignment")
        elif overlap > 0.4:
            print(f"\n⚠️  MODERATE overlap with Jaccard ({overlap:.1%}) - Partial agreement")
        else:
            print(f"\n🔬 LOW overlap with Jaccard ({overlap:.1%}) - Functional ≠ Anatomical")
            print(f"   → Evidence for distributed/functional coding!")
    print()

if __name__ == '__main__':
    main()
