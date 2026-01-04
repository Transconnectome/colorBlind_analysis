#!/usr/bin/env python3
"""
option2b_procrustes_alignment.py
=================================

Option 2B: Procrustes-based Group Alignment
대안: SRM 대신 Procrustes로 피험자 간 정렬

**배경**:
SRM이 실패한 이유는 temporal alignment 가정이 우리 데이터에 맞지 않음.
우리 데이터는 aggregated beta values로 시간적 대응 관계가 없음.

**Procrustes의 장점**:
- Option 1B에서 이미 검증됨: stability 0.83
- 시간 정렬 가정 불필요
- 직접적으로 패턴 geometry 정렬
- 간단하고 해석 쉬움

**방법**:
1. 각 피험자 데이터를 run-averaged pattern으로 변환 (8 colors × n_voxels)
2. 기준 피험자 선택 (sub-02)
3. 모든 피험자를 기준에 Procrustes 정렬
4. 정렬된 패턴들 평균 → 그룹 템플릿
5. 그룹 RDM 계산 및 개인 RDM과 비교

**기대 결과**:
RDM correlation: 0.6-0.8 (SRM보다 훨씬 나을 것)
"""

import argparse
import numpy as np
from pathlib import Path
from scipy.spatial import procrustes
from scipy.stats import spearmanr
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# ============================================================================
# Data Loading (Option 1과 동일)
# ============================================================================

def load_subject_amplitudes(subject_id, roi, timestamp, dataset='deoblique_v2'):
    """피험자 데이터 로드"""
    base_dir = Path('/scratch/connectome/haba6030/colorBlind')
    dataset_dir = base_dir / 'derivatives' / f'BH2009_{dataset}' / timestamp

    pattern = f'*_sub-{subject_id}_{roi}_*'
    matches = sorted(dataset_dir.glob(pattern))

    if len(matches) == 0:
        raise FileNotFoundError(f"No data found for sub-{subject_id}, ROI {roi}")

    result_dir = matches[0]
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
            amplitudes, result_dir = load_subject_amplitudes(
                subject_id, roi, timestamp, dataset
            )
            n_runs, n_colors, n_voxels = amplitudes.shape

            amplitudes_all.append(amplitudes)
            subjects_info.append({
                'subject': subject_id,
                'n_runs': n_runs,
                'n_colors': n_colors,
                'n_voxels': n_voxels
            })

            print(f"  sub-{subject_id}: {amplitudes.shape}")

        except FileNotFoundError as e:
            print(f"  sub-{subject_id}: ⚠️ {e}")
            continue

    if len(amplitudes_all) == 0:
        raise ValueError(f"No data loaded for ROI {roi}")

    # Voxel 수 확인
    n_voxels_min = min([info['n_voxels'] for info in subjects_info])
    n_voxels_max = max([info['n_voxels'] for info in subjects_info])

    print(f"  Voxel count range: {n_voxels_min} - {n_voxels_max}")

    # 모든 피험자가 같은 voxel 수를 가져야 함
    if n_voxels_min != n_voxels_max:
        print(f"  Truncating all subjects to {n_voxels_min} voxels")
        amplitudes_all = [amp[:, :, :n_voxels_min] for amp in amplitudes_all]
        for info in subjects_info:
            info['n_voxels'] = n_voxels_min

    return amplitudes_all, subjects_info

# ============================================================================
# RDM Computation
# ============================================================================

def compute_rdm(pattern):
    """
    RDM 계산

    Args:
        pattern: (n_colors, n_voxels) 또는 (n_runs, n_colors, n_voxels)

    Returns:
        rdm: (n_colors, n_colors)
    """
    if pattern.ndim == 3:
        # (n_runs, n_colors, n_voxels) → (n_colors, n_voxels)
        pattern = pattern.mean(axis=0)

    n_colors = pattern.shape[0]
    rdm = np.zeros((n_colors, n_colors))

    for i in range(n_colors):
        for j in range(n_colors):
            if i == j:
                rdm[i, j] = 0.0
            else:
                corr, _ = spearmanr(pattern[i, :], pattern[j, :])
                rdm[i, j] = 1 - corr

    return rdm

def compute_rdm_similarity(rdm1, rdm2):
    """두 RDM 간 유사도"""
    n_colors = rdm1.shape[0]
    triu_indices = np.triu_indices(n_colors, k=1)
    rdm1_vec = rdm1[triu_indices]
    rdm2_vec = rdm2[triu_indices]
    similarity, p_value = spearmanr(rdm1_vec, rdm2_vec)
    return similarity, p_value

# ============================================================================
# Procrustes Alignment
# ============================================================================

def procrustes_align_subjects(amplitudes_list, subjects_info):
    """
    Procrustes를 사용하여 모든 피험자를 정렬

    Args:
        amplitudes_list: List of (n_runs, n_colors, n_voxels)
        subjects_info: 피험자 정보

    Returns:
        aligned_patterns: List of (n_colors, n_voxels) - 정렬된 패턴
        disparities: List of disparities
    """
    print("Aligning subjects with Procrustes...")

    # 1. 각 피험자를 run-averaged pattern으로 변환
    patterns = []
    for i, amplitudes in enumerate(amplitudes_list):
        # (n_runs, n_colors, n_voxels) → (n_colors, n_voxels)
        pattern = amplitudes.mean(axis=0)
        patterns.append(pattern)
        print(f"  sub-{subjects_info[i]['subject']}: {pattern.shape}")

    # 2. 기준 피험자 선택 (첫 번째 피험자)
    reference = patterns[0]
    reference_id = subjects_info[0]['subject']
    print(f"  Reference subject: sub-{reference_id}")

    # 3. Procrustes 정렬
    aligned_patterns = [reference]  # 기준은 그대로
    disparities = [0.0]  # 기준의 disparity는 0

    for i in range(1, len(patterns)):
        mtx1, mtx2, disparity = procrustes(reference, patterns[i])
        aligned_patterns.append(mtx2)
        disparities.append(disparity)

        stability = 1 - disparity
        subj_id = subjects_info[i]['subject']
        print(f"  sub-{subj_id}: disparity={disparity:.4f}, stability={stability:.4f}")

    return aligned_patterns, disparities

def compute_group_template(aligned_patterns):
    """정렬된 패턴들의 평균 계산"""
    group_template = np.mean(aligned_patterns, axis=0)
    print(f"  Group template shape: {group_template.shape}")
    return group_template

# ============================================================================
# Cross-Subject Consistency Evaluation
# ============================================================================

def evaluate_cross_subject_consistency(aligned_patterns, group_template, subjects_info):
    """
    피험자 간 일관성 평가

    Returns:
        individual_rdms: 개인별 RDM
        group_rdm: 그룹 RDM
        rdm_similarities: 개인 vs 그룹 RDM 유사도
    """
    print("Evaluating cross-subject consistency...")

    # 그룹 RDM
    group_rdm = compute_rdm(group_template)

    # 개인 RDM 및 유사도
    individual_rdms = []
    rdm_similarities = []

    for i, pattern in enumerate(aligned_patterns):
        individual_rdm = compute_rdm(pattern)
        similarity, p_value = compute_rdm_similarity(individual_rdm, group_rdm)

        individual_rdms.append(individual_rdm)
        rdm_similarities.append(similarity)

        subj_id = subjects_info[i]['subject']
        print(f"  sub-{subj_id}: RDM similarity to group = {similarity:.3f} (p={p_value:.4f})")

    mean_similarity = np.mean(rdm_similarities)
    print(f"  Mean RDM similarity: {mean_similarity:.3f}")

    return individual_rdms, group_rdm, rdm_similarities

# ============================================================================
# Visualization
# ============================================================================

def visualize_results(individual_rdms, group_rdm, rdm_similarities, subjects_info, output_dir):
    """결과 시각화"""
    print("Creating visualizations...")

    n_subjects = len(individual_rdms)
    n_colors = group_rdm.shape[0]

    # 1. RDM Grid
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    axes = axes.flatten()

    # 개인 RDMs
    for i in range(n_subjects):
        ax = axes[i]
        im = ax.imshow(individual_rdms[i], cmap='viridis', vmin=0, vmax=2)
        subj_id = subjects_info[i]['subject']
        sim = rdm_similarities[i]
        ax.set_title(f'sub-{subj_id}\n(sim={sim:.3f})')
        ax.set_xlabel('Color')
        ax.set_ylabel('Color')
        plt.colorbar(im, ax=ax)

    # 그룹 RDM
    ax = axes[-1]
    im = ax.imshow(group_rdm, cmap='viridis', vmin=0, vmax=2)
    ax.set_title('Group Template\n(Procrustes aligned)')
    ax.set_xlabel('Color')
    ax.set_ylabel('Color')
    plt.colorbar(im, ax=ax)

    plt.tight_layout()
    plt.savefig(output_dir / 'procrustes_rdms_grid.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 2. RDM Similarity Bar Plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    x = np.arange(n_subjects)
    bars = ax.bar(x, rdm_similarities)

    # Color bars by value
    for i, bar in enumerate(bars):
        if rdm_similarities[i] > 0.6:
            bar.set_color('green')
        elif rdm_similarities[i] > 0.4:
            bar.set_color('orange')
        else:
            bar.set_color('red')

    ax.axhline(y=0.5, color='gray', linestyle='--', label='Target (0.5)')
    ax.set_xlabel('Subject')
    ax.set_ylabel('RDM Similarity to Group')
    ax.set_title('Cross-Subject Consistency (Procrustes Aligned)')
    ax.set_xticks(x)
    ax.set_xticklabels([f"sub-{info['subject']}" for info in subjects_info])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / 'procrustes_rdm_similarity.png', dpi=150, bbox_inches='tight')
    plt.close()

    print("  ✓ Visualizations complete")

# ============================================================================
# Main Analysis
# ============================================================================

def run_procrustes_analysis(args):
    """Procrustes 기반 분석 실행"""
    print("=" * 80)
    print("Option 2B: Procrustes-based Group Alignment")
    print("=" * 80)
    print(f"Timestamp: {args.timestamp}")
    print(f"Dataset: {args.dataset}")
    print(f"HC subjects: {args.hc_subjects}")
    print(f"ROIs: {args.rois}")
    print()

    # Output directory
    output_base = Path('results/group_level') / args.timestamp
    output_base.mkdir(parents=True, exist_ok=True)

    # Summary results
    summary_results = []

    for roi in args.rois:
        print("=" * 80)
        print(f"ROI: {roi}")
        print("=" * 80)

        try:
            # Load data
            amplitudes_list, subjects_info = load_all_subjects(
                args.hc_subjects, roi, args.timestamp, args.dataset
            )

            # Procrustes alignment
            aligned_patterns, disparities = procrustes_align_subjects(
                amplitudes_list, subjects_info
            )

            # Group template
            group_template = compute_group_template(aligned_patterns)

            # Evaluate consistency
            individual_rdms, group_rdm, rdm_similarities = evaluate_cross_subject_consistency(
                aligned_patterns, group_template, subjects_info
            )

            # Visualization
            output_dir = output_base / roi
            output_dir.mkdir(parents=True, exist_ok=True)
            visualize_results(individual_rdms, group_rdm, rdm_similarities,
                            subjects_info, output_dir)

            # Save results
            np.savez(
                output_dir / 'procrustes_results.npz',
                aligned_patterns=aligned_patterns,
                group_template=group_template,
                group_rdm=group_rdm,
                individual_rdms=individual_rdms,
                rdm_similarities=rdm_similarities,
                disparities=disparities,
                subjects=[info['subject'] for info in subjects_info]
            )

            # Summary
            summary_results.append({
                'roi': roi,
                'n_subjects': len(subjects_info),
                'n_voxels': subjects_info[0]['n_voxels'],
                'mean_disparity': np.mean(disparities),
                'mean_stability': 1 - np.mean(disparities),
                'mean_rdm_similarity': np.mean(rdm_similarities),
                'min_rdm_similarity': np.min(rdm_similarities),
                'max_rdm_similarity': np.max(rdm_similarities)
            })

            print(f"  ✓ Results saved to {output_dir}")
            print()

        except Exception as e:
            print(f"  ❌ Error processing {roi}: {e}")
            import traceback
            traceback.print_exc()
            print()

    # Save summary
    print("Creating summary report...")
    summary_file = output_base / 'procrustes_analysis_summary.txt'
    with open(summary_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("Option 2B: Procrustes-based Group Alignment - Summary\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Timestamp: {args.timestamp}\n")
        f.write(f"HC subjects: {', '.join(args.hc_subjects)}\n\n")
        f.write("-" * 80 + "\n")
        f.write("Results by ROI:\n")
        f.write("-" * 80 + "\n\n")

        for result in summary_results:
            f.write(f"{result['roi']}:\n")
            f.write(f"  Subjects: {result['n_subjects']}\n")
            f.write(f"  Voxels: {result['n_voxels']}\n")
            f.write(f"  Mean Procrustes disparity: {result['mean_disparity']:.4f}\n")
            f.write(f"  Mean Procrustes stability: {result['mean_stability']:.4f}\n")
            f.write(f"  Mean RDM similarity: {result['mean_rdm_similarity']:.3f}\n")
            f.write(f"  RDM similarity range: [{result['min_rdm_similarity']:.3f}, {result['max_rdm_similarity']:.3f}]\n\n")

    print(f"✓ Summary report saved to {summary_file}")
    print()
    print("=" * 80)
    print("Procrustes Analysis complete!")
    print(f"Results saved to: {output_base}")
    print("=" * 80)

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Procrustes-based Group Alignment')
    parser.add_argument('--timestamp', type=str, required=True,
                       help='Timestamp directory name')
    parser.add_argument('--dataset', type=str, default='deoblique_v2',
                       help='Dataset name')
    parser.add_argument('--hc-subjects', nargs='+', required=True,
                       help='HC subject IDs')
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2', 'V3', 'hV4'],
                       help='ROIs to analyze')

    args = parser.parse_args()
    run_procrustes_analysis(args)
