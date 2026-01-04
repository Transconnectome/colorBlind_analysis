#!/usr/bin/env python3
"""
option2c_advanced_voxel_selection.py
====================================

Option 2C: Advanced Voxel Selection + Procrustes Alignment

**배경**:
Procrustes stability가 0.83으로 높지만 cross-subject RDM이 0.26으로 낮음.
→ Voxel selection이 문제일 수 있음

**전략**:
1. **ANOVA Color-Significant**: 색상 간 차이가 유의한 voxel (Brouwer & Heeger 2009)
2. **Group-Consistent**: 모든 피험자에서 reliable한 voxel
3. **Combined**: 두 조건을 모두 만족하는 voxel

**이론적 근거**:
- Brouwer & Heeger (2009): "voxels that showed significant color selectivity"
- Haxby et al (2001): "most reliable and informative voxels"
- Bannert & Bartels (2025): "feature selection critical for cross-subject alignment"

**예상 효과**:
현재 RDM 0.26 → 0.5-0.6 가능
"""

import argparse
import numpy as np
from pathlib import Path
from scipy.spatial import procrustes
from scipy.stats import spearmanr, f_oneway
from sklearn.model_selection import KFold
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# ============================================================================
# Data Loading
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
            amplitudes, _ = load_subject_amplitudes(
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

    # Voxel 수 통일
    n_voxels_min = min([info['n_voxels'] for info in subjects_info])
    amplitudes_all = [amp[:, :, :n_voxels_min] for amp in amplitudes_all]
    for info in subjects_info:
        info['n_voxels'] = n_voxels_min

    return amplitudes_all, subjects_info

# ============================================================================
# Voxel Selection Methods
# ============================================================================

def select_anova_voxels(amplitudes_list, p_threshold=0.01, min_consensus_subjects=2):
    """
    Method 1: ANOVA Color-Significant Voxels

    각 voxel에서 8 colors 간 one-way ANOVA 수행
    p < threshold인 voxel만 선택

    **이론적 근거**:
    Brouwer & Heeger (2009): "voxels that showed significant differences
    across the eight color directions (one-way ANOVA, p < 0.05)"

    Args:
        amplitudes_list: List of (n_runs, n_colors, n_voxels)
        p_threshold: p-value threshold (default 0.01)
        min_consensus_subjects: Minimum number of subjects required (default 2)

    Returns:
        anova_mask: Boolean mask (n_voxels,)
        f_values: F-statistics (n_voxels,)
        p_values: p-values (n_voxels,)
    """
    print(f"Method 1: ANOVA color-significant voxels (p < {p_threshold})...")

    n_subjects = len(amplitudes_list)
    n_voxels = amplitudes_list[0].shape[2]
    n_colors = amplitudes_list[0].shape[1]

    # 각 피험자에서 ANOVA
    subject_masks = []
    all_f_values = []
    all_p_values = []

    for i, amplitudes in enumerate(amplitudes_list):
        # (n_runs, n_colors, n_voxels) → run 평균 → (n_colors, n_voxels)
        pattern = amplitudes.mean(axis=0)

        f_values = np.zeros(n_voxels)
        p_values = np.zeros(n_voxels)

        for v in range(n_voxels):
            # 각 voxel에서 8 colors에 대한 one-way ANOVA
            color_responses = [pattern[c, v] for c in range(n_colors)]
            # 각 color를 여러 observation으로 만들기 위해 runs 사용
            color_groups = []
            for c in range(n_colors):
                # 해당 color의 모든 run 값들
                color_groups.append(amplitudes[:, c, v])

            try:
                f_stat, p_val = f_oneway(*color_groups)
                f_values[v] = f_stat
                p_values[v] = p_val
            except:
                f_values[v] = 0
                p_values[v] = 1.0

        mask = p_values < p_threshold
        subject_masks.append(mask)
        all_f_values.append(f_values)
        all_p_values.append(p_values)

        print(f"  sub-{i}: {mask.sum()}/{n_voxels} voxels significant")

    # Group consensus: 적어도 min_consensus_subjects명에서 유의한 voxel
    vote_counts = np.sum(subject_masks, axis=0)
    anova_mask = vote_counts >= min_consensus_subjects

    # 평균 F-value, p-value
    mean_f_values = np.mean(all_f_values, axis=0)
    mean_p_values = np.mean(all_p_values, axis=0)

    print(f"  Group consensus (≥{min_consensus_subjects}/{n_subjects} subjects): {anova_mask.sum()}/{n_voxels} voxels")

    return anova_mask, mean_f_values, mean_p_values


def select_group_consistent_voxels(amplitudes_list, reliability_threshold=0.3, min_consensus_subjects=2):
    """
    Method 2: Group-Consistent Reliable Voxels

    각 피험자에서 split-half reliability 계산
    최소 min_consensus_subjects명에서 reliable한 voxel 선택

    **이론적 근거**:
    Haxby et al (2001): "most reliable voxels across runs"

    Args:
        amplitudes_list: List of (n_runs, n_colors, n_voxels)
        reliability_threshold: correlation threshold (default 0.3)
        min_consensus_subjects: Minimum number of subjects required (default 2)

    Returns:
        consistent_mask: Boolean mask (n_voxels,)
        reliabilities: Per-subject reliabilities (n_subjects, n_voxels)
    """
    print(f"Method 2: Group-consistent reliable voxels (r > {reliability_threshold})...")

    n_subjects = len(amplitudes_list)
    n_voxels = amplitudes_list[0].shape[2]
    n_runs = amplitudes_list[0].shape[0]

    # Split-half indices
    half1_idx = list(range(0, n_runs, 2))  # 0, 2, 4
    half2_idx = list(range(1, n_runs, 2))  # 1, 3, 5

    # 각 피험자에서 reliability 계산
    all_reliabilities = []
    subject_masks = []

    for i, amplitudes in enumerate(amplitudes_list):
        # (n_runs, n_colors, n_voxels)
        half1 = amplitudes[half1_idx].mean(axis=0)  # (n_colors, n_voxels)
        half2 = amplitudes[half2_idx].mean(axis=0)

        reliabilities = np.zeros(n_voxels)

        for v in range(n_voxels):
            # 각 voxel의 8-color pattern correlation
            r, _ = spearmanr(half1[:, v], half2[:, v])
            reliabilities[v] = r if not np.isnan(r) else 0

        mask = reliabilities > reliability_threshold
        subject_masks.append(mask)
        all_reliabilities.append(reliabilities)

        print(f"  sub-{i}: {mask.sum()}/{n_voxels} voxels reliable (mean r={reliabilities[mask].mean():.3f})")

    # At least min_consensus_subjects must be reliable
    vote_counts = np.sum(subject_masks, axis=0)
    consistent_mask = vote_counts >= min_consensus_subjects

    print(f"  Consensus (≥{min_consensus_subjects}/{n_subjects} subjects): {consistent_mask.sum()}/{n_voxels} voxels")

    return consistent_mask, np.array(all_reliabilities)


def select_combined_voxels(anova_mask, consistent_mask):
    """
    Method 3: Combined Selection

    ANOVA significant AND group-consistent

    **이론적 근거**:
    - Color information present (ANOVA)
    - Cross-subject consistent (reliability)
    - Double filtering for robustness
    """
    print("Method 3: Combined (ANOVA AND consistent)...")

    combined_mask = anova_mask & consistent_mask

    print(f"  ANOVA: {anova_mask.sum()} voxels")
    print(f"  Consistent: {consistent_mask.sum()} voxels")
    print(f"  Combined: {combined_mask.sum()} voxels")

    return combined_mask


def select_cross_validated_voxels(amplitudes_list, n_splits=3, top_k=100):
    """
    Method 4: Cross-Validated Feature Selection

    K-fold cross-validation으로 stable features 선택

    **이론적 근거**:
    Kriegeskorte et al (2009): Cross-validated feature selection
    prevents overfitting in MVPA
    """
    print(f"Method 4: Cross-validated selection (k={n_splits}, top_k={top_k})...")

    n_subjects = len(amplitudes_list)
    n_voxels = amplitudes_list[0].shape[2]
    n_runs = amplitudes_list[0].shape[0]

    # 각 피험자에서 CV
    cv_scores_all = []

    for i, amplitudes in enumerate(amplitudes_list):
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        voxel_scores = np.zeros(n_voxels)

        for train_idx, test_idx in kf.split(range(n_runs)):
            train_data = amplitudes[train_idx].mean(axis=0)  # (n_colors, n_voxels)
            test_data = amplitudes[test_idx].mean(axis=0)

            # 각 voxel의 train-test correlation
            for v in range(n_voxels):
                r, _ = spearmanr(train_data[:, v], test_data[:, v])
                voxel_scores[v] += r if not np.isnan(r) else 0

        voxel_scores /= n_splits
        cv_scores_all.append(voxel_scores)

    # Group average CV scores
    mean_cv_scores = np.mean(cv_scores_all, axis=0)

    # Top k voxels
    top_k_actual = min(top_k, n_voxels)
    top_indices = np.argsort(mean_cv_scores)[-top_k_actual:]
    cv_mask = np.zeros(n_voxels, dtype=bool)
    cv_mask[top_indices] = True

    print(f"  Selected top {cv_mask.sum()} voxels (mean CV score: {mean_cv_scores[cv_mask].mean():.3f})")

    return cv_mask, mean_cv_scores

# ============================================================================
# Procrustes Alignment (from option2b)
# ============================================================================

def compute_rdm(pattern):
    """RDM 계산"""
    if pattern.ndim == 3:
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

def procrustes_align_and_evaluate(amplitudes_list, subjects_info, voxel_mask):
    """
    선택된 voxel에 대해 Procrustes 정렬 및 평가
    """
    n_voxels_selected = voxel_mask.sum()
    print(f"  Using {n_voxels_selected} selected voxels")

    # Voxel selection 적용
    amplitudes_selected = [amp[:, :, voxel_mask] for amp in amplitudes_list]

    # Run-averaged patterns
    patterns = []
    for amplitudes in amplitudes_selected:
        pattern = amplitudes.mean(axis=0)
        patterns.append(pattern)

    # Procrustes alignment
    reference = patterns[0]
    aligned_patterns = [reference]
    disparities = [0.0]

    for i in range(1, len(patterns)):
        mtx1, mtx2, disparity = procrustes(reference, patterns[i])
        aligned_patterns.append(mtx2)
        disparities.append(disparity)

    # Group template
    group_template = np.mean(aligned_patterns, axis=0)

    # Evaluate
    group_rdm = compute_rdm(group_template)
    rdm_similarities = []

    for i, pattern in enumerate(aligned_patterns):
        individual_rdm = compute_rdm(pattern)
        similarity, _ = compute_rdm_similarity(individual_rdm, group_rdm)
        rdm_similarities.append(similarity)

        subj_id = subjects_info[i]['subject']
        disp = disparities[i]
        print(f"    sub-{subj_id}: disparity={disp:.4f}, RDM_sim={similarity:.3f}")

    mean_similarity = np.mean(rdm_similarities)
    mean_disparity = np.mean(disparities)

    return {
        'n_voxels': n_voxels_selected,
        'mean_rdm_similarity': mean_similarity,
        'mean_procrustes_disparity': mean_disparity,
        'mean_procrustes_stability': 1 - mean_disparity,
        'rdm_similarities': rdm_similarities,
        'disparities': disparities
    }

# ============================================================================
# Main Analysis
# ============================================================================

def run_advanced_voxel_selection(args):
    """Advanced voxel selection 분석 실행"""
    print("=" * 80)
    print("Option 2C: Advanced Voxel Selection + Procrustes")
    print("=" * 80)
    print(f"Timestamp: {args.timestamp}")
    print(f"HC subjects: {args.hc_subjects}")
    print(f"ROIs: {args.rois}")
    print()

    output_base = Path('results/group_level') / args.timestamp
    output_base.mkdir(parents=True, exist_ok=True)

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

            n_voxels_original = subjects_info[0]['n_voxels']
            print(f"Original voxels: {n_voxels_original}")
            print()

            # Method 1: ANOVA
            anova_mask, f_values, p_values = select_anova_voxels(
                amplitudes_list,
                p_threshold=args.anova_p,
                min_consensus_subjects=args.anova_consensus
            )
            print()

            # Method 2: Group-consistent
            consistent_mask, reliabilities = select_group_consistent_voxels(
                amplitudes_list,
                reliability_threshold=args.reliability_threshold,
                min_consensus_subjects=args.reliability_consensus
            )
            print()

            # Method 3: Combined
            combined_mask = select_combined_voxels(anova_mask, consistent_mask)
            print()

            # Method 4: Cross-validated (optional)
            if args.use_cv:
                cv_mask, cv_scores = select_cross_validated_voxels(
                    amplitudes_list, n_splits=3, top_k=args.cv_top_k
                )
                print()
            else:
                cv_mask = None

            # Evaluate each method
            results = {}

            print("-" * 80)
            print("Evaluating voxel selection methods:")
            print("-" * 80)

            # Baseline (all voxels)
            print("\nBaseline (all voxels):")
            all_mask = np.ones(n_voxels_original, dtype=bool)
            results['baseline'] = procrustes_align_and_evaluate(
                amplitudes_list, subjects_info, all_mask
            )

            # ANOVA
            if anova_mask.sum() > 0:
                print("\nMethod 1 (ANOVA):")
                results['anova'] = procrustes_align_and_evaluate(
                    amplitudes_list, subjects_info, anova_mask
                )

            # Group-consistent
            if consistent_mask.sum() > 0:
                print("\nMethod 2 (Group-consistent):")
                results['consistent'] = procrustes_align_and_evaluate(
                    amplitudes_list, subjects_info, consistent_mask
                )

            # Combined
            if combined_mask.sum() > 0:
                print("\nMethod 3 (Combined):")
                results['combined'] = procrustes_align_and_evaluate(
                    amplitudes_list, subjects_info, combined_mask
                )

            # Cross-validated
            if cv_mask is not None and cv_mask.sum() > 0:
                print("\nMethod 4 (Cross-validated):")
                results['cv'] = procrustes_align_and_evaluate(
                    amplitudes_list, subjects_info, cv_mask
                )

            # Save results
            output_dir = output_base / roi
            output_dir.mkdir(parents=True, exist_ok=True)

            np.savez(
                output_dir / 'advanced_voxel_selection_results.npz',
                anova_mask=anova_mask,
                consistent_mask=consistent_mask,
                combined_mask=combined_mask,
                cv_mask=cv_mask if cv_mask is not None else np.array([]),
                f_values=f_values,
                p_values=p_values,
                reliabilities=reliabilities,
                results=results,
                subjects=[info['subject'] for info in subjects_info]
            )

            # Summary
            summary_results.append({
                'roi': roi,
                'n_voxels_original': n_voxels_original,
                'n_anova': anova_mask.sum(),
                'n_consistent': consistent_mask.sum(),
                'n_combined': combined_mask.sum(),
                'n_cv': cv_mask.sum() if cv_mask is not None else 0,
                'baseline_rdm': results['baseline']['mean_rdm_similarity'],
                'anova_rdm': results.get('anova', {}).get('mean_rdm_similarity', np.nan),
                'consistent_rdm': results.get('consistent', {}).get('mean_rdm_similarity', np.nan),
                'combined_rdm': results.get('combined', {}).get('mean_rdm_similarity', np.nan),
                'cv_rdm': results.get('cv', {}).get('mean_rdm_similarity', np.nan)
            })

            print(f"\n✓ Results saved to {output_dir}")
            print()

        except Exception as e:
            print(f"❌ Error processing {roi}: {e}")
            import traceback
            traceback.print_exc()
            print()

    # Save summary
    print("=" * 80)
    print("Summary Report")
    print("=" * 80)
    summary_file = output_base / 'advanced_voxel_selection_summary.txt'
    with open(summary_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("Option 2C: Advanced Voxel Selection + Procrustes - Summary\n")
        f.write("=" * 80 + "\n\n")

        for result in summary_results:
            f.write(f"{result['roi']}:\n")
            f.write(f"  Original voxels: {result['n_voxels_original']}\n")
            f.write(f"  ANOVA selected: {result['n_anova']} ({result['n_anova']/result['n_voxels_original']*100:.1f}%)\n")
            f.write(f"  Consistent selected: {result['n_consistent']} ({result['n_consistent']/result['n_voxels_original']*100:.1f}%)\n")
            f.write(f"  Combined selected: {result['n_combined']} ({result['n_combined']/result['n_voxels_original']*100:.1f}%)\n")
            if result['n_cv'] > 0:
                f.write(f"  CV selected: {result['n_cv']}\n")
            f.write("\n")
            f.write(f"  RDM Similarity Results:\n")
            f.write(f"    Baseline (all): {result['baseline_rdm']:.3f}\n")
            if not np.isnan(result['anova_rdm']):
                f.write(f"    ANOVA: {result['anova_rdm']:.3f}\n")
            if not np.isnan(result['consistent_rdm']):
                f.write(f"    Consistent: {result['consistent_rdm']:.3f}\n")
            if not np.isnan(result['combined_rdm']):
                f.write(f"    Combined: {result['combined_rdm']:.3f}\n")
            if not np.isnan(result['cv_rdm']):
                f.write(f"    CV: {result['cv_rdm']:.3f}\n")
            f.write("\n")

    print(f"✓ Summary saved to {summary_file}")
    print("\nAdvanced Voxel Selection Analysis complete!")

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Advanced Voxel Selection + Procrustes')
    parser.add_argument('--timestamp', type=str, required=True)
    parser.add_argument('--dataset', type=str, default='deoblique_v2')
    parser.add_argument('--hc-subjects', nargs='+', required=True)
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2', 'V3', 'hV4'])
    parser.add_argument('--anova-p', type=float, default=0.01,
                       help='ANOVA p-value threshold')
    parser.add_argument('--anova-consensus', type=int, default=2,
                       help='Minimum subjects for ANOVA consensus (1-5)')
    parser.add_argument('--reliability-threshold', type=float, default=0.3,
                       help='Reliability threshold for consistent voxels')
    parser.add_argument('--reliability-consensus', type=int, default=2,
                       help='Minimum subjects for reliability consensus (1-5)')
    parser.add_argument('--use-cv', action='store_true',
                       help='Use cross-validated selection')
    parser.add_argument('--cv-top-k', type=int, default=100,
                       help='Top K voxels for CV selection')

    args = parser.parse_args()
    run_advanced_voxel_selection(args)
