#!/usr/bin/env python3
"""
phase1_voxel_overlap.py
=======================

Phase 1A: Voxel Overlap Analysis

HC 피험자들이 해부학적으로 일관된 복셀을 사용하는지 평가합니다.

**핵심 질문**: HC 피험자들이 color encoding에 같은 뇌 영역(복셀)을 사용하는가?

**방법**:
1. 각 HC 피험자의 선택된 복셀 로드
   - Baseline feature selection 결과 사용
   - 없으면 SNR 기반 top 50% 사용
2. Pairwise Jaccard index 계산
   - 모든 피험자 쌍 간 복셀 겹침 정도
3. Common voxels (교집합) 및 Union voxels (합집합) 계산
4. 시각화 및 통계

**주요 지표**: **Jaccard Index**
- **공식**: J(A, B) = |A ∩ B| / |A ∪ B|
  - A ∩ B: 두 피험자가 모두 선택한 복셀 (교집합)
  - A ∪ B: 둘 중 하나라도 선택한 복셀 (합집합)
- **범위**: 0 (완전히 다름) ~ 1 (완전히 같음)
- **의미**: 두 피험자가 얼마나 유사한 위치의 복셀을 사용하는가?

**해석 기준**:
- **> 0.5**: ✅ 높은 일관성 - HC가 해부학적으로 유사한 복셀 사용
  - 예: V1에서 0.6 → 60%의 복셀이 겹침
- **0.3 ~ 0.5**: ⚠️ 보통 일관성 - 어느 정도 겹치지만 개인차 존재
- **< 0.3**: ❌ 낮은 일관성 - 개인차가 크고 복셀 선택이 매우 다름

**추가 지표**:
- **Common voxels (교집합)**: 모든 HC가 공통으로 선택한 복셀
  - 가장 일관된 복셀 위치
  - Phase 1B, 1C, 2B에서 사용 가능
- **Union voxels (합집합)**: HC 중 한 명이라도 선택한 모든 복셀
- **Overlap ratio**: Common / Union (전체 대비 공통 비율)

Usage:
    python analysis/group_level/phase1_voxel_overlap.py \
        --roi V1 \
        --timestamp baseline32_deob_determin \
        --subjects 01 02 03 05 06 07

Author: Claude Code
Date: 2025-12-16
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
import argparse
import glob
from sklearn.feature_selection import f_classif

# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='Phase 1A: Voxel Overlap')
    parser.add_argument('--roi', type=str, required=True)
    parser.add_argument('--timestamp', type=str, default='baseline32_deob_determin')
    parser.add_argument('--dataset', type=str, default='deoblique_v2')
    parser.add_argument('--subjects', type=str, nargs='+',
                        default=['01', '02', '03', '05', '06', '07'])
    parser.add_argument('--k-voxels', type=int, default=50,
                        help='Number of voxels to select (via ANOVA if selection file missing)')
    parser.add_argument('--output-dir', type=str, default=None)
    return parser.parse_args()

# ============================================================================
# Data Loading
# ============================================================================

def load_subject_voxels(subject_id, roi, timestamp, dataset='deoblique_v2', k_voxels=50):
    """
    피험자의 선택된 복셀 인덱스 로드

    **로딩 전략** (Fallback chain):
    1. **우선**: selected_voxel_indices.npy (baseline feature selection 결과)
       - ANOVA, RFE 등으로 선택된 복셀
    2. **대안1**: ANOVA F-score 계산하여 top K 선택 (NEW!)
       - GLM betas 로드 → One-way ANOVA → Top K
       - 모든 피험자에 동일한 K 사용 → 공정한 비교
    3. **대안2**: voxel_snr.npy 있으면 top K by SNR
       - SNR: Signal-to-Noise Ratio (신호 대 잡음비)
    4. **대안3**: 모든 복셀 사용

    **Path structure**:
    derivatives/BH2009_{dataset}/{timestamp}/sm*_sub-{ID}_{ROI}_*/amplitudes_z.npy

    Args:
        subject_id: Subject ID (e.g., '01')
        roi: ROI name (e.g., 'V1')
        timestamp: Baseline timestamp
        dataset: Dataset name
        k_voxels: Number of voxels to select (if ANOVA/SNR used)

    Returns:
        selected_indices: (n_selected,) array - 선택된 복셀의 인덱스
        n_voxels: Total number of voxels in ROI
    """
    base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
    pattern = str(base_path / f'sm*_sub-{subject_id}_{roi}_*')

    # Baseline 결과 디렉토리 찾기
    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(f"No results for sub-{subject_id} {roi}")

    # 첫 번째 매치 사용 (config가 맞으면 하나만 있어야 함)
    result_dir = Path(matches[0])
    print(f"  sub-{subject_id}: {result_dir.name}")

    # Amplitudes 로드 (복셀 수 확인용)
    amp_file = result_dir / 'amplitudes_z.npy'
    if not amp_file.exists():
        raise FileNotFoundError(f"No amplitudes_z.npy in {result_dir}")

    amplitudes = np.load(amp_file)
    n_runs, n_colors, n_voxels = amplitudes.shape

    # 선택된 복셀 인덱스 로드 (4-tier fallback)
    selected_file = result_dir / 'selected_voxel_indices.npy'

    if selected_file.exists():
        # Strategy 1: Baseline feature selection 결과 사용 (가장 선호)
        selected_indices = np.load(selected_file)
        print(f"    ✓ {len(selected_indices)} selected voxels (from baseline)")
    else:
        # Strategy 2: ANOVA 기반 선택 (NEW!)
        # amplitudes_z를 사용하여 ANOVA F-score 계산
        try:
            # amplitudes: (n_runs, n_colors, n_voxels) - 이미 위에서 로드됨

            # ANOVA를 위해 reshape: (n_samples, n_voxels)
            # n_samples = n_runs × n_colors
            X = amplitudes.reshape(-1, n_voxels)  # (n_runs*n_colors, n_voxels)

            # Color labels: [0,1,2,3,4,5,6,7, 0,1,2,3,4,5,6,7, ...]
            # 각 run마다 8개 색상 반복
            y = np.tile(np.arange(n_colors), n_runs)

            # ANOVA F-score 계산
            # f_classif: One-way ANOVA, 각 복셀에 대해 색상 간 차이 검정
            # 높은 F-score = 색상 간 차이가 큰 복셀 = 색상 정보가 풍부
            f_scores, _ = f_classif(X, y)

            # NaN 처리 (분산이 0인 복셀)
            f_scores = np.nan_to_num(f_scores, nan=0.0)

            # Top K 선택
            k = min(k_voxels, n_voxels)
            selected_indices = np.argsort(f_scores)[::-1][:k]
            print(f"    ✓ Top-{k} voxels by ANOVA (F-score)")
        except Exception as e:
            print(f"    ⚠️  ANOVA failed ({e}), trying SNR...")
            selected_indices = None

        # Strategy 3: SNR 기반 (ANOVA 실패 시)
        if selected_indices is None:
            snr_file = result_dir / 'voxel_snr.npy'
            if snr_file.exists():
                voxel_snr = np.load(snr_file)
                k = min(k_voxels, n_voxels)
                # argsort[::-1] = 내림차순 정렬 (높은 SNR부터)
                selected_indices = np.argsort(voxel_snr)[::-1][:k]
                print(f"    ⚠️  No selection/ANOVA, using top-{k} by SNR")
            else:
                # Strategy 4: 모든 복셀 사용 (최후의 수단)
                selected_indices = np.arange(n_voxels)
                print(f"    ⚠️  Using all {n_voxels} voxels (no selection available)")

    return selected_indices, n_voxels

# ============================================================================
# Jaccard Index
# ============================================================================

def compute_jaccard(set_a, set_b):
    """
    Jaccard Index (자카드 지수) 계산

    **공식**: J(A, B) = |A ∩ B| / |A ∪ B|

    **의미**:
    - A ∩ B (교집합): 두 피험자가 **모두** 선택한 복셀
    - A ∪ B (합집합): 둘 중 **하나라도** 선택한 복셀
    - 분자/분모 = 전체 중 겹치는 비율

    **예시**:
    - A = {1, 2, 3, 4, 5}, B = {3, 4, 5, 6, 7}
    - Intersection = {3, 4, 5} → size = 3
    - Union = {1, 2, 3, 4, 5, 6, 7} → size = 7
    - J(A, B) = 3/7 = 0.43 (43% 겹침)

    **해석**:
    - J = 1.0: 완전히 같은 복셀 (100% 일치)
    - J = 0.5: 절반 겹침
    - J = 0.0: 전혀 겹치지 않음

    Args:
        set_a, set_b: Array-like of voxel indices

    Returns:
        jaccard: Float in [0, 1]
    """
    # NumPy array → Python set 변환 (집합 연산용)
    set_a = set(set_a)
    set_b = set(set_b)

    # 교집합: A와 B 모두에 있는 원소
    intersection = set_a & set_b

    # 합집합: A 또는 B에 있는 모든 원소
    union = set_a | set_b

    # Jaccard = |교집합| / |합집합|
    return len(intersection) / len(union) if len(union) > 0 else 0.0

def compute_jaccard_matrix(voxel_dict, subjects):
    """
    Pairwise Jaccard index matrix 계산

    모든 피험자 쌍에 대해 Jaccard index를 계산합니다.

    **결과 행렬**:
    - 크기: (n_subjects, n_subjects)
    - 대각선: 1.0 (자기 자신과는 100% 일치)
    - 대칭 행렬: J(A, B) = J(B, A)

    Args:
        voxel_dict: Dict[subject_id -> voxel_indices]
        subjects: List of subject IDs

    Returns:
        matrix: (n_subjects, n_subjects) Jaccard index matrix
    """
    n = len(subjects)
    matrix = np.zeros((n, n))

    # 모든 피험자 쌍에 대해
    for i, sub_i in enumerate(subjects):
        for j, sub_j in enumerate(subjects):
            if i == j:
                # 자기 자신: 항상 1.0
                matrix[i, j] = 1.0
            else:
                # 다른 피험자: Jaccard 계산
                matrix[i, j] = compute_jaccard(voxel_dict[sub_i], voxel_dict[sub_j])

    return matrix

def compute_common_union(voxel_dict, subjects):
    """
    Common voxels (교집합) 및 Union voxels (합집합) 계산

    **Common voxels (교집합)**:
    - **의미**: 모든 HC 피험자가 공통으로 선택한 복셀
    - **중요**: 가장 일관되고 신뢰할 수 있는 복셀
    - **사용**: Phase 1B (RSA), 1C (LOSO), 2B (HC→CVD) 에서 사용 가능
    - **예시**: 6명 모두 선택 → 매우 robust한 복셀

    **Union voxels (합집합)**:
    - **의미**: HC 중 한 명이라도 선택한 모든 복셀
    - **중요**: 전체 탐색 공간
    - **Overlap ratio**: Common / Union = 전체 중 일관된 비율

    Args:
        voxel_dict: Dict[subject_id -> voxel_indices]
        subjects: List of subject IDs

    Returns:
        common_voxels: (n_common,) array - 교집합
        union_voxels: (n_union,) array - 합집합
    """
    # 각 피험자의 복셀을 set으로 변환
    voxel_sets = [set(voxel_dict[sub]) for sub in subjects]

    # 교집합: 모든 set의 교집합
    # A ∩ B ∩ C ∩ D ∩ E ∩ F
    common = voxel_sets[0]  # 첫 번째로 초기화
    for vset in voxel_sets[1:]:
        common = common & vset  # 순차적으로 교집합

    # 합집합: 모든 set의 합집합
    # A ∪ B ∪ C ∪ D ∪ E ∪ F
    union = set()
    for vset in voxel_sets:
        union = union | vset  # 순차적으로 합집합

    # Set → sorted NumPy array 변환
    return np.array(sorted(common)), np.array(sorted(union))

# ============================================================================
# Visualization
# ============================================================================

def plot_jaccard_heatmap(jaccard_matrix, subjects, output_dir):
    """
    Jaccard index heatmap 시각화

    **Heatmap 해석**:
    - **색상**: 노란색(0) → 주황색 → 빨간색(1)
    - **대각선**: 항상 1.0 (자기 자신)
    - **Off-diagonal**: 피험자 간 복셀 겹침
    - **숫자**: Jaccard index 값 (0.XX)

    **패턴 해석**:
    - 전체적으로 빨간색: ✅ 높은 일관성 (J > 0.5)
    - 주황색 섞임: ⚠️ 보통 일관성 (J = 0.3-0.5)
    - 노란색 많음: ❌ 낮은 일관성 (J < 0.3)
    """
    fig, ax = plt.subplots(figsize=(8, 7))

    # Heatmap: 0 (노란색) ~ 1 (빨간색)
    im = ax.imshow(jaccard_matrix, cmap='YlOrRd', vmin=0, vmax=1, aspect='auto')

    # Axis 설정
    ax.set_xticks(range(len(subjects)))
    ax.set_yticks(range(len(subjects)))
    ax.set_xticklabels([f'sub-{s}' for s in subjects], rotation=45, ha='right')
    ax.set_yticklabels([f'sub-{s}' for s in subjects])

    # 각 칸에 숫자 표시 (대각선 제외)
    for i in range(len(subjects)):
        for j in range(len(subjects)):
            if i != j:  # 대각선 아닌 경우만
                # 텍스트 색상: 밝은 배경(J > 0.5)은 흰색, 어두운 배경은 검은색
                ax.text(j, i, f'{jaccard_matrix[i, j]:.2f}',
                       ha="center", va="center",
                       color="white" if jaccard_matrix[i, j] > 0.5 else "black",
                       fontsize=10)

    # Colorbar
    plt.colorbar(im, ax=ax, label='Jaccard Index')

    # Title
    ax.set_title('Pairwise Voxel Overlap (Jaccard Index)', fontweight='bold', pad=15)
    plt.tight_layout()

    # Save
    fig_path = output_dir / 'jaccard_heatmap.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Heatmap: {fig_path}")

# ============================================================================
# Main
# ============================================================================

def main():
    args = parse_args()

    print(f"\n{'='*80}")
    print(f"Phase 1A: Voxel Overlap Analysis")
    print(f"{'='*80}")
    print(f"ROI: {args.roi}")
    print(f"Timestamp: {args.timestamp}")
    print(f"Subjects: {', '.join(args.subjects)}")
    print(f"K voxels: {args.k_voxels} (for ANOVA/SNR selection)")

    # Output directory
    if args.output_dir is None:
        output_dir = Path(f"derivatives/group_level/{args.timestamp}/{args.roi}/voxel_overlap")
    else:
        output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output: {output_dir}\n")

    # ========================================================================
    # Load voxels - Step 1: Check voxel counts
    # ========================================================================
    print(f"Step 1: Checking ROI voxel counts...")
    total_voxels_dict = {}

    for subject_id in args.subjects:
        try:
            base_path = Path(f'derivatives/BH2009_{args.dataset}/{args.timestamp}')
            pattern = str(base_path / f'sm*_sub-{subject_id}_{args.roi}_*')
            matches = glob.glob(pattern)
            if matches:
                result_dir = Path(matches[0])
                amp_file = result_dir / 'amplitudes_z.npy'
                if amp_file.exists():
                    amplitudes = np.load(amp_file)
                    n_voxels = amplitudes.shape[2]
                    total_voxels_dict[subject_id] = n_voxels
                    print(f"  sub-{subject_id}: {n_voxels} voxels")
        except Exception as e:
            print(f"  ✗ sub-{subject_id}: {e}")

    # 최소/최대 복셀 수
    min_voxels = min(total_voxels_dict.values())
    max_voxels = max(total_voxels_dict.values())

    print(f"\nVoxel count range: {min_voxels} ~ {max_voxels}")

    # Scenario 분석 결정
    scenarios = []

    # Scenario A: K=최소값, 모든 피험자 포함
    scenarios.append({
        'name': 'A_all_subjects',
        'description': f'K={min_voxels} (all {len(args.subjects)} subjects)',
        'k': min_voxels,
        'subjects': args.subjects
    })

    # Scenario B: K=지정값, 충분한 복셀 있는 피험자만
    if min_voxels < args.k_voxels:
        # K 이상의 복셀을 가진 피험자만
        subjects_sufficient = [s for s, n in total_voxels_dict.items() if n >= args.k_voxels]
        excluded = [s for s in args.subjects if s not in subjects_sufficient]

        scenarios.append({
            'name': 'B_sufficient_voxels',
            'description': f'K={args.k_voxels} ({len(subjects_sufficient)} subjects, excluded: {", ".join(excluded)})',
            'k': args.k_voxels,
            'subjects': subjects_sufficient
        })
        print(f"⚠️  Some subjects have < {args.k_voxels} voxels")
        print(f"   Will run 2 scenarios:\n")
    else:
        print(f"✓ All subjects have ≥ {args.k_voxels} voxels")
        print(f"   Will run 1 scenario:\n")

    # ========================================================================
    # Run both scenarios
    # ========================================================================
    for scenario in scenarios:
        print(f"\n{'='*80}")
        print(f"Scenario {scenario['name']}: {scenario['description']}")
        print(f"{'='*80}\n")

        # 시나리오별 출력 디렉토리
        scenario_output_dir = output_dir / scenario['name']
        scenario_output_dir.mkdir(parents=True, exist_ok=True)

        # 복셀 로드
        print(f"Loading {scenario['k']} voxels per subject...")
        voxel_dict = {}
        voxel_counts = {}

        for subject_id in scenario['subjects']:
            try:
                selected_indices, n_total = load_subject_voxels(
                    subject_id, args.roi, args.timestamp, args.dataset, scenario['k']
                )
                voxel_dict[subject_id] = selected_indices
                voxel_counts[subject_id] = len(selected_indices)
            except Exception as e:
                print(f"  ✗ sub-{subject_id}: {e}")

        if len(voxel_dict) == 0:
            print(f"  ⚠️  No subjects loaded for this scenario, skipping...\n")
            continue

        subjects = list(voxel_dict.keys())
        print(f"\n✅ Loaded {len(subjects)} subjects (all with {scenario['k']} voxels)\n")

        # Jaccard 계산 및 저장 (기존 로직 재사용)
        run_overlap_analysis(voxel_dict, voxel_counts, subjects, scenario_output_dir,
                            args.roi, args.timestamp, total_voxels_dict)

    # ========================================================================
    # Final Summary
    # ========================================================================
    print(f"\n{'='*80}")
    print(f"Phase 1A Complete! ({len(scenarios)} scenario(s) analyzed)")
    print(f"{'='*80}")
    print(f"Results saved in: {output_dir}")
    for scenario in scenarios:
        print(f"  - {scenario['name']}: {scenario['description']}")
    print()

def run_overlap_analysis(voxel_dict, voxel_counts, subjects, output_dir, roi, timestamp, total_voxels_dict):
    """
    Voxel overlap 분석 실행 (Jaccard, common/union, 시각화)

    이 함수는 기존 main()의 분석 로직을 분리한 것입니다.
    """

    # ========================================================================
    # Compute Jaccard
    # ========================================================================
    print(f"Computing pairwise Jaccard index...")
    jaccard_matrix = compute_jaccard_matrix(voxel_dict, subjects)

    # Statistics (upper triangle only - 대각선 제외, 중복 제거)
    # 예: 6명이면 6×5/2 = 15개 쌍
    upper_tri = np.triu_indices(len(subjects), k=1)
    jaccard_values = jaccard_matrix[upper_tri]

    # 통계량 계산
    mean_jac = jaccard_values.mean()  # 평균 Jaccard
    std_jac = jaccard_values.std()    # 표준편차 (variability)
    min_jac = jaccard_values.min()    # 최소값 (가장 다른 쌍)
    max_jac = jaccard_values.max()    # 최대값 (가장 비슷한 쌍)

    print(f"  Mean: {mean_jac:.3f} ± {std_jac:.3f}")
    print(f"  Range: [{min_jac:.3f}, {max_jac:.3f}]\n")

    # ========================================================================
    # Common and union voxels
    # ========================================================================
    print(f"Computing common (intersection) and union voxels...")
    common_voxels, union_voxels = compute_common_union(voxel_dict, subjects)

    # 결과 출력
    print(f"  Common: {len(common_voxels)}")  # 모든 HC가 선택 (가장 일관됨)
    print(f"  Union: {len(union_voxels)}")    # 한 명이라도 선택 (전체 탐색 공간)

    # Overlap ratio: 전체 중 일관된 비율
    # 높을수록 피험자 간 복셀 선택이 일치
    overlap_ratio = len(common_voxels) / len(union_voxels) if len(union_voxels) > 0 else 0
    print(f"  Overlap ratio: {overlap_ratio:.3f}\n")

    # Overlap ratio 해석
    # - > 0.5: 절반 이상이 공통 → 매우 일관됨
    # - 0.2-0.5: 일부 공통
    # - < 0.2: 소수만 공통 → 개인차 큼

    # ========================================================================
    # Save results
    # ========================================================================
    print(f"Saving results...")

    # Jaccard matrix
    jaccard_df = pd.DataFrame(jaccard_matrix,
                              index=[f'sub-{s}' for s in subjects],
                              columns=[f'sub-{s}' for s in subjects])
    jaccard_df.to_csv(output_dir / 'jaccard_matrix.csv')

    # Voxel indices
    np.save(output_dir / 'common_voxels_indices.npy', common_voxels)
    np.save(output_dir / 'union_voxels_indices.npy', union_voxels)

    # Summary
    voxel_summary = pd.DataFrame({
        'subject': [f'sub-{s}' for s in subjects],
        'n_selected': [voxel_counts[s] for s in subjects],
        'n_total': [total_voxels_dict[s] for s in subjects],
        'selection_ratio': [voxel_counts[s] / total_voxels_dict[s] for s in subjects]
    })
    voxel_summary.to_csv(output_dir / 'voxel_count_summary.csv', index=False)

    # Statistics
    with open(output_dir / 'overlap_statistics.txt', 'w') as f:
        f.write(f"Phase 1A: Voxel Overlap Analysis\n")
        f.write(f"{'='*80}\n\n")
        f.write(f"ROI: {roi}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Subjects: {', '.join(subjects)}\n\n")
        f.write(f"Pairwise Jaccard Index:\n")
        f.write(f"  Mean: {mean_jac:.3f} ± {std_jac:.3f}\n")
        f.write(f"  Range: [{min_jac:.3f}, {max_jac:.3f}]\n\n")
        f.write(f"Group Voxel Overlap:\n")
        f.write(f"  Common voxels: {len(common_voxels)}\n")
        f.write(f"  Union voxels: {len(union_voxels)}\n")
        f.write(f"  Overlap ratio: {len(common_voxels) / len(union_voxels):.3f}\n\n")
        f.write(f"Per-subject:\n")
        for s in subjects:
            f.write(f"  sub-{s}: {voxel_counts[s]} selected\n")

    print(f"  ✓ jaccard_matrix.csv")
    print(f"  ✓ common_voxels_indices.npy ({len(common_voxels)} voxels)")
    print(f"  ✓ union_voxels_indices.npy ({len(union_voxels)} voxels)")
    print(f"  ✓ voxel_count_summary.csv")
    print(f"  ✓ overlap_statistics.txt\n")

    # ========================================================================
    # Visualization
    # ========================================================================
    print(f"Creating visualization...")
    plot_jaccard_heatmap(jaccard_matrix, subjects, output_dir)

    # ========================================================================
    # Summary (per scenario)
    # ========================================================================
    print(f"\nScenario Summary:")
    print(f"  Mean Jaccard: {mean_jac:.3f} ± {std_jac:.3f}")
    print(f"  Common voxels: {len(common_voxels)} ({100*len(common_voxels)/len(union_voxels):.1f}% of union)")

    if mean_jac > 0.5:
        print(f"  ✅ HIGH consistency - HC subjects use similar voxels")
    elif mean_jac > 0.3:
        print(f"  ⚠️  MODERATE consistency - Some overlap but variability")
    else:
        print(f"  ❌ LOW consistency - High inter-subject variability")
    print()

if __name__ == '__main__':
    main()
