#!/usr/bin/env python3
"""
phase1_rsa.py
=============

Phase 1B: Representational Similarity Analysis (RSA)
표상 유사성 분석 (Representational Similarity Analysis)

**목적**: HC 피험자들 간 표상 기하학(representational geometry)의 일관성 평가

**주요 지표**: **RDM Similarity (Spearman correlation)**

**RDM (Representational Dissimilarity Matrix)란?**
- **정의**: 8가지 색상 간의 neural distance를 나타내는 8×8 행렬
- **계산**: RDM[i,j] = 1 - Spearman_corr(beta_color_i, beta_color_j)
  - beta_color_i: i번째 색상의 모든 복셀 활성화 패턴
  - beta_color_j: j번째 색상의 모든 복셀 활성화 패턴
  - Spearman: 순위 기반 상관계수 (outlier에 robust)
- **범위**: 0 (완전히 같음) ~ 2 (완전히 반대)

**왜 Spearman correlation을 사용하나?**
1. **비선형 관계 포착**: Pearson보다 더 robust
2. **Outlier에 덜 민감**: 극단값의 영향 감소
3. **RSA 표준**: Kriegeskorte et al. (2008) 방법론
4. **순위만 고려**: 절대값보다 상대적 크기 관계가 중요

**RDM Similarity**:
- **의미**: 두 피험자의 RDM 간 Spearman correlation
- **범위**: -1 ~ 1 (일반적으로 양수)
- **해석 기준**:
  - **> 0.7**: ✅ 높은 일관성 (매우 유사한 표상 구조)
  - **0.5 ~ 0.7**: ⚠️ 보통 일관성 (부분적으로 유사)
  - **< 0.5**: ❌ 낮은 일관성 (다른 표상 구조)

**Mantel Test**:
- **목적**: RDM 간 유사성의 통계적 유의성 검정
- **방법**: Permutation test (행/열 동시 permutation)
- **귀무가설**: 두 RDM이 독립적 (상관 없음)
- **해석**: p < 0.05 → 유의미한 유사성 존재

**Phase 1A (Voxel Overlap)와의 차이**:
- **Phase 1A**: 어떤 복셀이 선택되었는가? (Anatomical consistency)
- **Phase 1B**: 복셀 활성화 패턴이 얼마나 비슷한가? (Representational consistency)
- **보완 관계**: Voxel overlap이 높아도 RDM이 다를 수 있음 (역도 성립)

**결과 해석 가이드**:
1. **High RDM similarity + High voxel overlap**:
   - ✅ 이상적 상황: 해부학적으로도, 기능적으로도 일관됨
   - → HC group-level decoder feasible

2. **High RDM similarity + Low voxel overlap**:
   - ⚠️ 다른 복셀 위치지만 비슷한 표상 구조
   - → 개별 복셀 위치는 중요하지 않을 수 있음

3. **Low RDM similarity + High voxel overlap**:
   - ⚠️ 같은 복셀 위치지만 다른 neural coding
   - → Common voxel 사용해도 generalization 어려울 수 있음

4. **Low RDM similarity + Low voxel overlap**:
   - ❌ 해부학적으로도, 기능적으로도 inconsistent
   - → Group-level decoder 어려움, 개별 분석 필요

Usage:
    python analysis/group_level/phase1_rsa.py \
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
from scipy.stats import spearmanr
from scipy.spatial.distance import squareform

# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='Phase 1B: RSA')
    parser.add_argument('--roi', type=str, required=True)
    parser.add_argument('--timestamp', type=str, default='baseline32_deob_determin')
    parser.add_argument('--dataset', type=str, default='deoblique_v2')
    parser.add_argument('--subjects', type=str, nargs='+',
                        default=['01', '02', '03', '05', '06', '07'])
    parser.add_argument('--use-common-voxels', action='store_true',
                        help='Use common voxels from Phase 1A (if available)')
    parser.add_argument('--scenario', type=str, default=None,
                        choices=['A_all_subjects', 'B_sufficient_voxels', 'RDM_guided', 'no_selection'],
                        help='Voxel selection scenario: A/B (Jaccard), RDM_guided, or no_selection (all voxels)')
    parser.add_argument('--output-dir', type=str, default=None)
    return parser.parse_args()

# ============================================================================
# Data Loading
# ============================================================================

def load_subject_amplitudes(subject_id, roi, timestamp, dataset='deoblique_v2'):
    """
    피험자의 amplitudes_z 로드

    **반환값**: (n_runs, n_colors, n_voxels) 형태의 z-scored channel amplitudes

    **Note**:
    - Phase 1B는 개별 최적 K 복셀 사용 (baseline 분석과 동일)
    - amplitudes_z: z-scored channel response (각 run별로 표준화됨)
    """
    # Priority 1: New structure - analysis/phase1_preprocess_decoding/{dataset}/results/baseline_decoding/{timestamp}/sub-{subject}/{roi}/
    new_result_dir = Path(f'analysis/phase1_preprocess_decoding/{dataset}/results/baseline_decoding/{timestamp}/sub-{subject_id}/{roi}')

    if new_result_dir.exists():
        result_dir = new_result_dir
    else:
        # Priority 2: Legacy structure - derivatives/V3_Comprehensive/BH2009_{dataset}/{timestamp}/sub-{subject}/{roi}
        legacy_result_dir = Path(f'derivatives/V3_Comprehensive/BH2009_{dataset}/{timestamp}/sub-{subject_id}/{roi}')

        if legacy_result_dir.exists():
            result_dir = legacy_result_dir
        else:
            raise FileNotFoundError(
                f"No results for sub-{subject_id} {roi}\n"
                f"  Tried new: {new_result_dir}\n"
                f"  Tried legacy: {legacy_result_dir}"
            )

    amp_file = result_dir / 'amplitudes_z.npy'

    if not amp_file.exists():
        raise FileNotFoundError(f"Amplitudes file not found: {amp_file}")

    amplitudes = np.load(amp_file)  # (n_runs, n_colors, n_voxels)
    print(f"  sub-{subject_id}: {amplitudes.shape}")

    return amplitudes, result_dir

def load_common_voxels(roi, timestamp, scenario='B_sufficient_voxels'):
    """
    Phase 1A에서 계산된 common voxels (교집합) 로드 (Optional)

    **목적**: 모든 HC가 공통으로 선택한 복셀만 사용하여 RDM 계산 가능
    - 장점: 더 robust한 비교 (모든 피험자가 동의하는 복셀)
    - 단점: 복셀 수 감소로 인한 signal 감소 가능

    **Note**: Phase 1A가 먼저 실행되어야 함

    Args:
        roi: ROI name
        timestamp: Analysis timestamp
        scenario: 'A_all_subjects' or 'B_sufficient_voxels'

    Returns:
        common_voxels array or None
    """
    voxel_file = Path(f'derivatives/V3_Comprehensive/group_level/{timestamp}/{roi}/voxel_overlap/{scenario}/common_voxels_indices.npy')

    if not voxel_file.exists():
        return None

    common_voxels = np.load(voxel_file)
    print(f"  ✓ Loaded {len(common_voxels)} common voxels from Phase 1A ({scenario})")
    return common_voxels

def detect_phase1a_scenarios(roi, timestamp):
    """
    Phase 1A에서 생성된 시나리오 탐지

    Returns:
        list of scenario names (e.g., ['A_all_subjects', 'B_sufficient_voxels'])
    """
    base_dir = Path(f'derivatives/V3_Comprehensive/group_level/{timestamp}/{roi}/voxel_overlap')

    if not base_dir.exists():
        return []

    scenarios = []
    for scenario_name in ['A_all_subjects', 'B_sufficient_voxels']:
        scenario_dir = base_dir / scenario_name
        if scenario_dir.exists():
            # Check if common voxels file exists
            common_voxels_file = scenario_dir / 'common_voxels_indices.npy'
            if common_voxels_file.exists():
                scenarios.append(scenario_name)

    return scenarios

# ============================================================================
# RDM Computation
# ============================================================================

def compute_rdm(amplitudes, voxel_indices=None):
    """
    Representational Dissimilarity Matrix (RDM) 계산

    **핵심 원리**:
    RDM은 8가지 색상 간의 neural distance를 나타내는 8×8 행렬입니다.

    **계산 과정**:
    1. 각 색상의 복셀 활성화 패턴을 run 평균
       - Color i: [v1, v2, v3, ..., vK] (K개 복셀의 활성화)
       - Color j: [v1, v2, v3, ..., vK]

    2. 두 색상 간 Spearman correlation 계산
       - Spearman_corr(Color_i, Color_j) across voxels
       - 범위: -1 (완전히 반대) ~ +1 (완전히 같음)

    3. Dissimilarity로 변환
       - RDM[i, j] = 1 - Spearman_corr(i, j)
       - 범위: 0 (완전히 같음) ~ 2 (완전히 반대)

    **왜 Spearman을 사용하나?**
    - Pearson은 선형 관계만 포착, outlier에 민감
    - Spearman은 순위 기반 → 비선형 관계 포착, robust
    - RSA 표준 방법론 (Kriegeskorte et al., 2008)

    **예시**:
    - Color 1: [0.5, 1.2, 0.8, 1.5, ...]  # Voxel 활성화
    - Color 2: [0.4, 1.1, 0.9, 1.4, ...]  # 매우 비슷
    - Spearman_corr = 0.95 → RDM[1,2] = 0.05 (매우 가까움)

    - Color 1: [0.5, 1.2, 0.8, 1.5, ...]
    - Color 5: [1.5, 0.3, 1.8, 0.2, ...]  # 완전히 다름
    - Spearman_corr = -0.2 → RDM[1,5] = 1.2 (매우 멈)

    **해석**:
    - RDM[i,j] ≈ 0: Color i와 j가 neural space에서 매우 가까움
    - RDM[i,j] ≈ 1: Color i와 j가 uncorrelated (독립적)
    - RDM[i,j] ≈ 2: Color i와 j가 완전히 반대 패턴

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) z-scored channel amplitudes
        voxel_indices: Optional voxel subset (e.g., common voxels)

    Returns:
        rdm: (n_colors, n_colors) dissimilarity matrix
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # 특정 복셀만 선택 (e.g., common voxels)
    if voxel_indices is not None:
        amplitudes = amplitudes[:, :, voxel_indices]

    # Run 평균: (n_runs, n_colors, n_voxels) → (n_colors, n_voxels)
    # 각 색상의 평균 복셀 활성화 패턴 계산
    amplitudes_avg = amplitudes.mean(axis=0)  # (n_colors, n_voxels)

    # RDM 초기화 (8×8 행렬)
    rdm = np.zeros((n_colors, n_colors))

    # 모든 색상 쌍에 대해 dissimilarity 계산
    for i in range(n_colors):
        for j in range(n_colors):
            if i == j:
                # 대각선: 자기 자신과의 거리는 0
                rdm[i, j] = 0.0
            else:
                # Spearman correlation: 복셀 간 순위 기반 상관계수
                # amplitudes_avg[i, :]: i번째 색상의 K개 복셀 활성화
                # amplitudes_avg[j, :]: j번째 색상의 K개 복셀 활성화
                corr, _ = spearmanr(amplitudes_avg[i, :], amplitudes_avg[j, :])

                # Dissimilarity = 1 - correlation
                # corr = 1 → rdm = 0 (완전히 같음)
                # corr = 0 → rdm = 1 (독립적)
                # corr = -1 → rdm = 2 (완전히 반대)
                rdm[i, j] = 1 - corr

    return rdm

def compute_rdm_similarity_matrix(rdm_dict, subjects):
    """
    피험자 간 RDM 유사도 행렬 계산 (Spearman correlation)

    **핵심 질문**: "두 피험자의 표상 구조(representational geometry)가 얼마나 비슷한가?"

    **계산 과정**:
    1. 각 피험자의 RDM을 1차원 벡터로 flatten
       - RDM은 대칭 행렬 → upper triangle만 사용 (중복 제거)
       - 8×8 행렬 → 28개 unique 값 (8C2 = 28)
       - 예: [RDM[0,1], RDM[0,2], ..., RDM[6,7]]

    2. 두 피험자의 flattened RDM 간 Spearman correlation 계산
       - Subject A의 RDM: [d1, d2, ..., d28]
       - Subject B의 RDM: [d1', d2', ..., d28']
       - Similarity = Spearman_corr(A, B)

    3. N×N 유사도 행렬 생성 (N = 피험자 수)

    **해석**:
    - Similarity ≈ 1: 두 피험자의 색상 간 neural distance가 매우 유사
    - Similarity ≈ 0: 독립적인 표상 구조
    - Similarity < 0: 반대 패턴 (드묾)

    **왜 upper triangle만 사용하나?**
    - RDM은 대칭: RDM[i,j] = RDM[j,i]
    - 대각선은 항상 0: RDM[i,i] = 0
    - 중복 제거로 통계적으로 더 적절

    **예시**:
    - Subject A: Red-Orange 거리 = 0.2, Red-Blue 거리 = 1.5
    - Subject B: Red-Orange 거리 = 0.3, Red-Blue 거리 = 1.6
    - → 비슷한 패턴 → High similarity

    Args:
        rdm_dict: Dict[subject_id -> RDM (8, 8)]
        subjects: List of subject IDs

    Returns:
        similarity_matrix: (n_subjects, n_subjects) correlation matrix
    """
    n_subjects = len(subjects)
    similarity_matrix = np.zeros((n_subjects, n_subjects))

    for i, sub_i in enumerate(subjects):
        for j, sub_j in enumerate(subjects):
            if i == j:
                # 대각선: 자기 자신과의 유사도는 1
                similarity_matrix[i, j] = 1.0
            else:
                # RDM의 upper triangle만 추출 (k=1: 대각선 제외)
                # 8×8 행렬 → 28개 unique 값
                rdm_i_flat = rdm_dict[sub_i][np.triu_indices(8, k=1)]
                rdm_j_flat = rdm_dict[sub_j][np.triu_indices(8, k=1)]

                # Spearman correlation: 28개 distance 값 간 순위 상관
                # 두 피험자의 색상 간 거리 패턴이 얼마나 비슷한지 측정
                corr, _ = spearmanr(rdm_i_flat, rdm_j_flat)
                similarity_matrix[i, j] = corr

    return similarity_matrix

def mantel_test(rdm1, rdm2, n_permutations=10000):
    """
    Mantel Test: RDM 간 유사성의 통계적 유의성 검정

    **목적**: "관찰된 RDM correlation이 우연히 나타난 것인가?"를 검정

    **귀무가설 (H0)**:
    - 두 RDM이 독립적 (상관 없음)
    - 관찰된 correlation은 우연의 산물

    **대립가설 (H1)**:
    - 두 RDM이 유의미하게 유사함
    - 공유된 표상 구조 존재

    **검정 방법: Permutation Test**
    1. 관찰값 계산: obs_corr = Spearman_corr(RDM1, RDM2)

    2. Permutation (N회 반복, 예: 10,000회):
       - RDM2의 행/열을 무작위로 섞음 (대칭성 유지!)
       - 섞인 RDM2'와 RDM1 간 correlation 계산
       - Null distribution 생성

    3. P-value 계산:
       - p = (permutation corr ≥ obs_corr인 비율)
       - p < 0.05: 관찰된 유사성이 통계적으로 유의미

    **왜 행/열을 동시에 permute하나?**
    - RDM은 대칭 행렬: RDM[i,j] = RDM[j,i]
    - 행만 섞으면 대칭성 깨짐 → 잘못된 null distribution
    - 행/열 동시 permutation = 색상 label을 무작위로 재배치

    **예시**:
    - obs_corr = 0.85
    - 10,000번 permutation 중 50번만 0.85 이상
    - p-value = 50/10,000 = 0.005
    - → p < 0.05: 유의미한 유사성 존재!

    **해석**:
    - p < 0.001: ✅✅✅ 매우 강한 유의성 (우연일 확률 < 0.1%)
    - p < 0.01:  ✅✅ 강한 유의성
    - p < 0.05:  ✅ 유의미
    - p ≥ 0.05:  ❌ 유의미하지 않음 (우연일 수 있음)

    Args:
        rdm1, rdm2: (n_colors, n_colors) dissimilarity matrices
        n_permutations: Permutation 반복 횟수 (기본 10,000)

    Returns:
        corr: 관찰된 correlation (obs_corr)
        p_value: Permutation test p-value
    """
    # Step 1: RDM flatten (upper triangle만)
    rdm1_flat = rdm1[np.triu_indices(len(rdm1), k=1)]
    rdm2_flat = rdm2[np.triu_indices(len(rdm2), k=1)]

    # Step 2: 관찰된 correlation 계산
    obs_corr, _ = spearmanr(rdm1_flat, rdm2_flat)

    # Step 3: Permutation test - Null distribution 생성
    perm_corrs = []
    for _ in range(n_permutations):
        # RDM2의 행/열을 무작위로 섞음 (대칭성 유지)
        perm_idx = np.random.permutation(len(rdm2))

        # 행 섞기 → 열 섞기 (같은 순서로!)
        # 예: [0,1,2,3] → [2,0,3,1]이면 행2→0, 열2→0 동시에
        rdm2_perm = rdm2[perm_idx, :][:, perm_idx]

        # Permuted RDM과 RDM1 간 correlation
        rdm2_perm_flat = rdm2_perm[np.triu_indices(len(rdm2), k=1)]
        perm_corr, _ = spearmanr(rdm1_flat, rdm2_perm_flat)
        perm_corrs.append(perm_corr)

    # Step 4: P-value 계산
    # Null distribution에서 obs_corr 이상의 값이 나타날 확률
    # abs() 사용: 양/음 방향 모두 고려 (two-tailed test)
    p_value = np.mean(np.abs(perm_corrs) >= np.abs(obs_corr))

    return obs_corr, p_value

# ============================================================================
# Visualization
# ============================================================================

def plot_rdms(rdm_dict, subjects, output_dir):
    """
    모든 피험자의 RDM을 grid로 시각화

    **목적**: 각 피험자의 색상 간 neural distance 패턴 비교
    **해석**: 비슷한 패턴 → 일관된 표상 구조
    """
    n_subjects = len(subjects)
    n_cols = 3
    n_rows = (n_subjects + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 4 * n_rows))
    axes = axes.flatten()

    color_labels = [f'C{i+1}' for i in range(8)]

    for idx, subject_id in enumerate(subjects):
        ax = axes[idx]
        rdm = rdm_dict[subject_id]

        im = ax.imshow(rdm, cmap='viridis', vmin=0, vmax=2, aspect='auto')
        ax.set_xticks(range(8))
        ax.set_yticks(range(8))
        ax.set_xticklabels(color_labels, fontsize=8)
        ax.set_yticklabels(color_labels, fontsize=8)
        ax.set_title(f'sub-{subject_id}', fontweight='bold')

        # Colorbar
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    # Hide empty subplots
    for idx in range(n_subjects, len(axes)):
        axes[idx].axis('off')

    plt.suptitle('Representational Dissimilarity Matrices (RDMs)\n1 - Spearman correlation',
                 fontsize=14, fontweight='bold', y=1.00)
    plt.tight_layout()

    fig_path = output_dir / 'rdm_grid.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ RDM grid: {fig_path}")

def plot_similarity_heatmap(similarity_matrix, subjects, output_dir):
    """
    RDM 유사도 행렬 heatmap

    **해석**:
    - 녹색 (1에 가까움): 매우 유사한 표상 구조
    - 노란색 (0 근처): 독립적
    - 빨간색 (음수): 반대 패턴 (드묾)
    """
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(similarity_matrix, cmap='RdYlGn', vmin=-1, vmax=1, aspect='auto')

    ax.set_xticks(range(len(subjects)))
    ax.set_yticks(range(len(subjects)))
    ax.set_xticklabels([f'sub-{s}' for s in subjects], rotation=45, ha='right')
    ax.set_yticklabels([f'sub-{s}' for s in subjects])

    # Annotate
    for i in range(len(subjects)):
        for j in range(len(subjects)):
            if i != j:
                ax.text(j, i, f'{similarity_matrix[i, j]:.2f}',
                       ha="center", va="center",
                       color="white" if abs(similarity_matrix[i, j]) > 0.5 else "black",
                       fontsize=10)

    plt.colorbar(im, ax=ax, label='RDM Correlation')
    ax.set_title('RDM Similarity Matrix\n(Spearman correlation between RDMs)',
                 fontweight='bold', pad=15)
    plt.tight_layout()

    fig_path = output_dir / 'rdm_similarity_heatmap.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Similarity heatmap: {fig_path}")

def plot_average_rdm(rdm_dict, subjects, output_dir):
    """
    HC 평균 RDM 및 변동성(std) 시각화

    **Average RDM**:
    - HC group의 대표적인 색상 간 neural distance
    - Group-level decoder 설계 시 참고할 표상 구조

    **Std RDM**:
    - 피험자 간 변동성이 큰 색상 쌍 확인
    - 높은 std → 개인차 큼, 낮은 std → 일관됨
    """
    rdms = np.array([rdm_dict[sub] for sub in subjects])
    avg_rdm = rdms.mean(axis=0)
    std_rdm = rdms.std(axis=0)

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    color_labels = [f'C{i+1}' for i in range(8)]

    # Average RDM
    ax = axes[0]
    im = ax.imshow(avg_rdm, cmap='viridis', vmin=0, vmax=2, aspect='auto')
    ax.set_xticks(range(8))
    ax.set_yticks(range(8))
    ax.set_xticklabels(color_labels)
    ax.set_yticklabels(color_labels)
    ax.set_title('Average RDM (across HC subjects)', fontweight='bold')
    plt.colorbar(im, ax=ax, label='Dissimilarity')

    # Std RDM
    ax = axes[1]
    im = ax.imshow(std_rdm, cmap='plasma', vmin=0, aspect='auto')
    ax.set_xticks(range(8))
    ax.set_yticks(range(8))
    ax.set_xticklabels(color_labels)
    ax.set_yticklabels(color_labels)
    ax.set_title('RDM Variability (std across subjects)', fontweight='bold')
    plt.colorbar(im, ax=ax, label='Std')

    plt.tight_layout()

    fig_path = output_dir / 'average_rdm.png'
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  ✓ Average RDM: {fig_path}")

# ============================================================================
# Main
# ============================================================================

def main():
    args = parse_args()

    print(f"\n{'='*80}")
    print(f"Phase 1B: Representational Similarity Analysis (RSA)")
    print(f"{'='*80}")
    print(f"ROI: {args.roi}")
    print(f"Timestamp: {args.timestamp}")
    print(f"Subjects: {', '.join(args.subjects)}")
    if args.scenario:
        print(f"Scenario: {args.scenario}")
    print()

    # Output directory
    if args.output_dir is None:
        base_dir = Path(f"derivatives/V3_Comprehensive/group_level/{args.timestamp}/{args.roi}/rsa")
        if args.scenario:
            output_dir = base_dir / args.scenario
        else:
            output_dir = base_dir
    else:
        output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output: {output_dir}\n")

    # ========================================================================
    # Load voxels (based on scenario)
    # ========================================================================
    common_voxels = None

    if args.scenario == 'no_selection':
        print(f"Scenario: No selection - using all voxels\n")
        common_voxels = None

    elif args.scenario == 'RDM_guided':
        print(f"Loading RDM-guided voxels from Phase 1A-alt...")
        voxel_file = Path(f'derivatives/V3_Comprehensive/group_level/{args.timestamp}/{args.roi}/voxel_overlap/RDM_guided/rdm_guided_voxels_indices.npy')
        if voxel_file.exists():
            common_voxels = np.load(voxel_file)
            print(f"  ✓ Loaded {len(common_voxels)} RDM-guided voxels\n")
        else:
            print(f"  ⚠️  RDM-guided voxels not found, using all voxels\n")
            common_voxels = None

    elif args.scenario in ['A_all_subjects', 'B_sufficient_voxels']:
        print(f"Loading Jaccard-based voxels from Phase 1A ({args.scenario})...")
        common_voxels = load_common_voxels(args.roi, args.timestamp, args.scenario)
        if common_voxels is None:
            print(f"  ⚠️  Jaccard voxels not found, using all voxels\n")
        elif len(common_voxels) == 0:
            print(f"  ⚠️  Empty common voxels, using all voxels\n")
            common_voxels = None
        else:
            print()

    elif args.use_common_voxels:
        # Legacy: no scenario specified, try B then A
        print(f"Loading common voxels from Phase 1A...")
        common_voxels = load_common_voxels(args.roi, args.timestamp, 'B_sufficient_voxels')
        if common_voxels is None:
            common_voxels = load_common_voxels(args.roi, args.timestamp, 'A_all_subjects')

        if common_voxels is None or len(common_voxels) == 0:
            print(f"  ⚠️  No common voxels found, using all voxels\n")
            common_voxels = None
        else:
            print()

    # ========================================================================
    # Load amplitudes and compute RDMs
    # ========================================================================
    # 각 피험자의 channel amplitudes를 로드하고 RDM 계산
    # - amplitudes_z: (n_runs, 8_colors, n_voxels)
    # - RDM: 8×8 행렬 (색상 간 neural distance)
    print(f"Loading amplitudes and computing RDMs...")
    rdm_dict = {}

    for subject_id in args.subjects:
        try:
            # 1. Amplitudes 로드 (개별 최적 K 복셀 사용)
            amplitudes, _ = load_subject_amplitudes(
                subject_id, args.roi, args.timestamp, args.dataset
            )

            # 2. RDM 계산
            # - Common voxels 사용 시: 교집합 복셀만
            # - 그렇지 않으면: 모든 복셀 사용
            rdm = compute_rdm(amplitudes, common_voxels)
            rdm_dict[subject_id] = rdm

        except Exception as e:
            print(f"  ✗ sub-{subject_id}: {e}")

    if len(rdm_dict) == 0:
        raise RuntimeError("No subjects loaded!")

    subjects = list(rdm_dict.keys())
    print(f"\n✅ Computed RDMs for {len(subjects)} subjects\n")

    # ========================================================================
    # Compute RDM similarity matrix
    # ========================================================================
    # 피험자 간 RDM 유사도 계산 (Spearman correlation)
    # - N×N 행렬 (N = 피험자 수)
    # - 각 cell: 두 피험자의 RDM 간 correlation
    print(f"Computing RDM similarity matrix...")
    similarity_matrix = compute_rdm_similarity_matrix(rdm_dict, subjects)

    # Upper triangle만 추출하여 통계량 계산 (대각선 제외)
    # 대각선 = 1 (자기 자신)은 통계에서 제외
    upper_tri = np.triu_indices(len(subjects), k=1)
    sim_values = similarity_matrix[upper_tri]

    mean_sim = sim_values.mean()
    std_sim = sim_values.std()
    min_sim = sim_values.min()
    max_sim = sim_values.max()

    print(f"  Mean: {mean_sim:.3f} ± {std_sim:.3f}")
    print(f"  Range: [{min_sim:.3f}, {max_sim:.3f}]")
    print(f"  해석: >0.7=높음, 0.5-0.7=보통, <0.5=낮음\n")

    # ========================================================================
    # Mantel test (pairwise)
    # ========================================================================
    # 모든 피험자 쌍에 대해 Mantel test 수행
    # - 목적: 관찰된 RDM similarity가 통계적으로 유의미한지 검정
    # - 방법: Permutation test (1000회)
    # - 해석: p < 0.05 → 유의미한 표상 구조 공유
    print(f"Running Mantel tests (pairwise)...")
    mantel_results = []

    for i, sub_i in enumerate(subjects):
        for j, sub_j in enumerate(subjects):
            if i < j:  # Upper triangle만 (중복 제거)
                # Mantel test: RDM 간 correlation의 통계적 유의성
                # n_permutations=1000: 계산 시간 단축 (10000이 이상적)
                corr, p_val = mantel_test(rdm_dict[sub_i], rdm_dict[sub_j], n_permutations=1000)
                mantel_results.append({
                    'subject_i': sub_i,
                    'subject_j': sub_j,
                    'correlation': corr,
                    'p_value': p_val
                })

    mantel_df = pd.DataFrame(mantel_results)
    n_significant = (mantel_df['p_value'] < 0.05).sum()
    print(f"  {n_significant}/{len(mantel_df)} pairs significant (p < 0.05)")
    print(f"  해석: 높을수록 많은 피험자 쌍이 유의미한 표상 구조를 공유\n")

    # ========================================================================
    # Save results
    # ========================================================================
    print(f"Saving results...")

    # RDMs
    rdm_array = np.array([rdm_dict[sub] for sub in subjects])
    np.savez(output_dir / 'rdm_per_subject.npz',
             rdms=rdm_array,
             subjects=subjects,
             color_labels=[f'color_{i+1}' for i in range(8)])

    # Similarity matrix
    similarity_df = pd.DataFrame(similarity_matrix,
                                 index=[f'sub-{s}' for s in subjects],
                                 columns=[f'sub-{s}' for s in subjects])
    similarity_df.to_csv(output_dir / 'rdm_similarity_matrix.csv')

    # Mantel results
    mantel_df.to_csv(output_dir / 'mantel_test_results.csv', index=False)

    # Statistics
    with open(output_dir / 'rsa_statistics.txt', 'w') as f:
        f.write(f"Phase 1B: Representational Similarity Analysis\n")
        f.write(f"{'='*80}\n\n")
        f.write(f"ROI: {args.roi}\n")
        f.write(f"Timestamp: {args.timestamp}\n")
        f.write(f"Subjects: {', '.join(subjects)}\n")
        if common_voxels is not None:
            f.write(f"Common voxels: {len(common_voxels)}\n\n")
        else:
            f.write(f"Using all voxels (no Phase 1A common voxels)\n\n")
        f.write(f"RDM Similarity (Spearman correlation):\n")
        f.write(f"  Mean: {mean_sim:.3f} ± {std_sim:.3f}\n")
        f.write(f"  Range: [{min_sim:.3f}, {max_sim:.3f}]\n\n")
        f.write(f"Mantel Test Results:\n")
        f.write(f"  Significant pairs: {n_significant}/{len(mantel_df)} (p < 0.05)\n")

    print(f"  ✓ rdm_per_subject.npz")
    print(f"  ✓ rdm_similarity_matrix.csv")
    print(f"  ✓ mantel_test_results.csv")
    print(f"  ✓ rsa_statistics.txt\n")

    # ========================================================================
    # Visualization
    # ========================================================================
    print(f"Creating visualizations...")
    plot_rdms(rdm_dict, subjects, output_dir)
    plot_similarity_heatmap(similarity_matrix, subjects, output_dir)
    plot_average_rdm(rdm_dict, subjects, output_dir)

    # ========================================================================
    # Summary
    # ========================================================================
    # 결과 요약 및 해석 가이드 제공
    print(f"\n{'='*80}")
    print(f"Phase 1B Complete!")
    print(f"{'='*80}")
    print(f"Results: {output_dir}")
    print(f"\nKey findings:")
    print(f"  Mean RDM correlation: {mean_sim:.3f} ± {std_sim:.3f}")
    print(f"  Significant Mantel pairs: {n_significant}/{len(mantel_df)}")

    # 해석 기준에 따른 자동 판정
    if mean_sim > 0.7:
        print(f"\n✅ HIGH similarity - HC subjects share representational geometry")
        print(f"   → 해석: HC group의 색상 표상 구조가 매우 일관됨")
        print(f"   → 의미: Group-level decoder 설계 feasible")
    elif mean_sim > 0.5:
        print(f"\n⚠️  MODERATE similarity - Some shared structure")
        print(f"   → 해석: 부분적으로 유사한 표상 구조")
        print(f"   → 의미: Common voxels 사용 시 개선 가능성 있음")
    else:
        print(f"\n❌ LOW similarity - Different representational structures")
        print(f"   → 해석: HC 간에도 표상 구조가 다름")
        print(f"   → 의미: Individual decoder 사용 권장, group-level 어려움")

if __name__ == '__main__':
    main()
