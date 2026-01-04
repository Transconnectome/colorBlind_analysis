#!/usr/bin/env python3
"""
option2_srm_analysis.py
=======================

Option 2: Shared Response Model (SRM) Analysis
⭐⭐⭐ 최우선 권장 (Bannert & Bartels 2025에서 검증)

**목적**:
피험자 간 공유된 신경 표상 구조(shared neural representation)를 찾아내고,
이를 통해 HC 피험자들의 공통 색상 표상 공간을 구성

**핵심 아이디어**:
해부학적으로 정렬된 복셀(MNI space)이 기능적으로 대응되지 않을 수 있음.
SRM은 각 피험자의 개별 복셀 공간을 공유 잠재 공간(shared latent space)으로 변환하는
변환 행렬을 학습합니다.

**수학적 모델**:
┌────────────────────────────────────────────────────────────────┐
│ X_i = W_i @ S + noise                                          │
│                                                                │
│ X_i: 피험자 i의 복셀 활성화 (n_voxels_i × n_conditions)        │
│ W_i: 피험자 i의 변환 행렬 (n_voxels_i × k_features)            │
│ S: 공유 잠재 공간 (k_features × n_conditions)                  │
│ k_features: 공유 차원 수 (하이퍼파라미터, 보통 10-50)           │
└────────────────────────────────────────────────────────────────┘

**SRM이 하는 일**:
1. 모든 피험자의 데이터를 동시에 보고
2. 공유 구조 S를 찾아냄 (모든 피험자가 공유하는 표상)
3. 각 피험자별 변환 행렬 W_i를 학습 (개별 복셀 → 공유 공간)

**장점**:
- ✅ 색상 fMRI에 대해 검증됨 (Bannert & Bartels 2025, J. Neurosci.)
- ✅ 복셀 수가 달라도 OK (각 피험자 W_i 크기 다를 수 있음)
- ✅ 개별 해부학적 변동성 처리
- ✅ BrainIAK 패키지로 구현 용이
- ✅ 게재에 가장 안전 (검증된 방법)

**단점**:
- ❌ 선형 변환 가정 (비선형 구조 놓칠 수 있음)
- ❌ k_features 하이퍼파라미터 튜닝 필요
- ❌ 해석 가능성 낮음 (MDS보다)

**Output**:
1. 공유 잠재 공간 표상 (k_features × 8_colors)
2. 피험자별 변환 행렬 (n_voxels × k_features)
3. HC 합의 공간에서 CVD 재구성 오류
4. 통계 테스트: CVD가 HC 분포 밖인가?

**Bannert & Bartels (2025) 방법**:
1. HC 피험자들의 fMRI 데이터로 SRM 학습
2. 공유 공간에서 색상 디코더 학습
3. 새로운 피험자(CVD)를 공유 공간으로 투영
4. 공유 공간 디코더로 CVD 색상 디코딩

Usage:
    # HC만 분석 (공유 구조 찾기)
    python analysis/group_level/option2_srm_analysis.py \\
        --timestamp baseline81_deob_determin \\
        --hc-subjects 01 02 03 05 06 07 \\
        --rois V1 V2 V3 hV4 \\
        --k-features 20

    # CVD 포함 분석
    python analysis/group_level/option2_srm_analysis.py \\
        --timestamp baseline81_deob_determin \\
        --hc-subjects 01 02 03 05 06 07 \\
        --cvd-subjects 08 09 10 \\
        --rois V1 V2 V3 hV4 \\
        --k-features 20

Requirements:
    pip install brainiak

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
import argparse
import glob
from scipy.stats import spearmanr
from scipy.spatial.distance import cdist

# BrainIAK 임포트 (설치 필요: pip install brainiak)
try:
    from brainiak.funcalign.srm import SRM
    BRAINIAK_AVAILABLE = True
except ImportError:
    BRAINIAK_AVAILABLE = False
    print("⚠️ Warning: BrainIAK not found. Please install: pip install brainiak")

# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='Option 2: Shared Response Model (SRM) Analysis'
    )
    parser.add_argument('--timestamp', type=str, default='baseline81_deob_determin',
                        help='분석 timestamp')
    parser.add_argument('--dataset', type=str, default='deoblique_v2',
                        help='데이터셋 이름')
    parser.add_argument('--hc-subjects', type=str, nargs='+',
                        default=['01', '02', '03', '05', '06', '07'],
                        help='HC 피험자 ID 리스트')
    parser.add_argument('--cvd-subjects', type=str, nargs='*',
                        default=[],
                        help='CVD 피험자 ID 리스트 (선택적)')
    parser.add_argument('--rois', type=str, nargs='+',
                        default=['V1', 'V2', 'V3', 'hV4'],
                        help='ROI 리스트')
    parser.add_argument('--k-features', type=int, default=20,
                        help='공유 잠재 차원 수 (10-50 권장)')
    parser.add_argument('--n-iter', type=int, default=10,
                        help='SRM 최적화 iteration 수')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='출력 디렉토리')
    return parser.parse_args()

# ============================================================================
# Data Loading
# ============================================================================

def load_subject_amplitudes(subject_id, roi, timestamp, dataset='deoblique_v2'):
    """
    피험자의 amplitudes_z 로드

    Returns:
        amplitudes: (n_runs, n_colors, n_voxels)
        result_dir: 결과 디렉토리 경로
    """
    base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
    pattern = str(base_path / f'sm*_sub-{subject_id}_{roi}_*')

    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(
            f"No results for sub-{subject_id} {roi}"
        )

    result_dir = Path(matches[0])
    amp_file = result_dir / 'amplitudes_z.npy'

    if not amp_file.exists():
        raise FileNotFoundError(f"amplitudes_z.npy not found")

    amplitudes = np.load(amp_file)  # (n_runs, n_colors, n_voxels)
    return amplitudes, result_dir

def load_all_subjects_amplitudes(subject_ids, roi, timestamp, dataset='deoblique_v2'):
    """
    여러 피험자의 amplitudes 로드

    **SRM 입력 형식**:
    SRM은 리스트 형식을 요구합니다:
    - List of (n_timepoints, n_voxels) 배열
    - 여기서 n_timepoints = n_runs * n_colors = 8 runs * 8 colors = 64

    **변환**:
    1. 원본: (n_runs, n_colors, n_voxels)
    2. Reshape: (n_runs * n_colors, n_voxels)
    3. 각 피험자가 하나의 배열 → 리스트로 묶음

    **중요**: 모든 피험자의 복셀 수를 최소값으로 통일
    - BrainIAK SRM은 복셀 수가 달라도 되지만, 안정성을 위해 통일
    - 최소 복셀 수에 맞춰 truncate

    Returns:
        data_list: List of (n_timepoints, n_voxels_min) for each subject
        subjects_info: 피험자 정보 (ID, 복셀 수 등)
        n_voxels_min: 사용된 최소 복셀 수
    """
    # First pass: load all data and find minimum voxels
    amplitudes_all = []
    subjects_info_temp = []

    print(f"Loading {roi} data for {len(subject_ids)} subjects...")

    for subject_id in subject_ids:
        try:
            amplitudes, result_dir = load_subject_amplitudes(
                subject_id, roi, timestamp, dataset
            )
            n_runs, n_colors, n_voxels = amplitudes.shape

            amplitudes_all.append(amplitudes)
            subjects_info_temp.append({
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

    # Find minimum voxels across all subjects
    n_voxels_min = min([info['n_voxels'] for info in subjects_info_temp])
    n_voxels_max = max([info['n_voxels'] for info in subjects_info_temp])
    n_voxels_median = np.median([info['n_voxels'] for info in subjects_info_temp])

    print(f"  Minimum voxels across subjects: {n_voxels_min}")
    print(f"  Maximum voxels across subjects: {n_voxels_max}")
    print(f"  Median voxels across subjects: {n_voxels_median:.0f}")

    # Outlier detection: warn if min is much smaller than median
    outlier_ratio = n_voxels_min / n_voxels_median
    if outlier_ratio < 0.5:
        outlier_subject = [info['subject'] for info in subjects_info_temp
                          if info['n_voxels'] == n_voxels_min][0]
        data_loss_pct = (1 - outlier_ratio) * 100
        print(f"  ⚠️  WARNING: sub-{outlier_subject} has {n_voxels_min} voxels")
        print(f"  ⚠️  This is {outlier_ratio:.1%} of median ({n_voxels_median:.0f})")
        print(f"  ⚠️  Truncation will discard {data_loss_pct:.0f}% of data from other subjects")
        print(f"  ⚠️  Consider excluding sub-{outlier_subject} from this ROI analysis")

    print(f"  Truncating all subjects to {n_voxels_min} voxels")

    # Second pass: truncate and reshape
    data_list = []
    subjects_info = []

    for amplitudes, info in zip(amplitudes_all, subjects_info_temp):
        # Truncate to minimum voxels
        amplitudes_truncated = amplitudes[:, :, :n_voxels_min]
        n_runs, n_colors, _ = amplitudes_truncated.shape

        # Reshape: (n_runs, n_colors, n_voxels) → (n_runs*n_colors, n_voxels)
        amplitudes_reshaped = amplitudes_truncated.reshape(n_runs * n_colors, n_voxels_min)

        data_list.append(amplitudes_reshaped)

        subjects_info.append({
            'subject': info['subject'],
            'n_runs': n_runs,
            'n_colors': n_colors,
            'n_voxels': n_voxels_min,
            'n_timepoints': n_runs * n_colors
        })

        print(f"  sub-{info['subject']}: → {amplitudes_reshaped.shape}")

    return data_list, subjects_info, n_voxels_min

# ============================================================================
# RDM Computation (from Option 1)
# ============================================================================

def compute_rdm(amplitudes):
    """
    RDM 계산 (Option 1과 동일)

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        rdm: (n_colors, n_colors) dissimilarity matrix
    """
    n_runs, n_colors, n_voxels = amplitudes.shape
    amplitudes_avg = amplitudes.mean(axis=0)  # (n_colors, n_voxels)

    rdm = np.zeros((n_colors, n_colors))
    for i in range(n_colors):
        for j in range(n_colors):
            if i == j:
                rdm[i, j] = 0.0
            else:
                corr, _ = spearmanr(amplitudes_avg[i, :], amplitudes_avg[j, :])
                rdm[i, j] = 1 - corr

    return rdm

def compute_rdm_similarity(rdm1, rdm2):
    """두 RDM 간 유사도 계산"""
    n_colors = rdm1.shape[0]
    triu_indices = np.triu_indices(n_colors, k=1)
    rdm1_vec = rdm1[triu_indices]
    rdm2_vec = rdm2[triu_indices]
    similarity, p_value = spearmanr(rdm1_vec, rdm2_vec)
    return similarity, p_value

# ============================================================================
# SRM Analysis
# ============================================================================

def fit_srm(data_list, k_features=20, n_iter=10):
    """
    Shared Response Model 학습

    **SRM 알고리즘**:
    1. 초기화: 무작위 W_i, S
    2. Iteration:
       a. S 고정, W_i 업데이트 (각 피험자별로)
       b. W_i 고정, S 업데이트 (모든 피험자 데이터 사용)
    3. 수렴할 때까지 반복

    Args:
        data_list: List of (n_timepoints, n_voxels) 배열
        k_features: 공유 잠재 차원 수
        n_iter: 최적화 iteration 수

    Returns:
        srm: 학습된 SRM 모델
        shared_response: 공유 잠재 표상 (k_features, n_timepoints)
        transformations: 피험자별 변환 행렬 리스트

    **k_features 선택 가이드**:
    - 너무 작으면 (< 10): 표상력 부족, 과소적합
    - 적절하면 (10-50): 공유 구조 포착
    - 너무 크면 (> 100): 노이즈 포함, 과적합
    - Bannert & Bartels는 20-30 사용
    """
    if not BRAINIAK_AVAILABLE:
        raise ImportError("BrainIAK is required for SRM. Install: pip install brainiak")

    print(f"Fitting SRM with k={k_features} features, n_iter={n_iter}...")
    print(f"  n_subjects: {len(data_list)}")
    print(f"  n_timepoints: {data_list[0].shape[0]}")
    print(f"  n_voxels: {[d.shape[1] for d in data_list]}")

    # SRM 초기화 및 학습
    srm = SRM(n_iter=n_iter, features=k_features)
    srm.fit(data_list)

    # 공유 반응 추출
    # shared_response: (k_features, n_timepoints)
    # 각 timepoint에서 k개 잠재 차원의 활성화
    shared_response = srm.s_

    # 변환 행렬 추출
    # transformations: List of (n_voxels_i, k_features)
    # W_i: 피험자 i의 복셀을 공유 공간으로 변환
    transformations = srm.w_

    print(f"  ✓ SRM fitted successfully")
    print(f"    Shared response shape: {shared_response.shape}")
    print(f"    Transformation matrices: {len(transformations)} subjects")

    # DEBUG: Print shapes of transformation matrices
    print(f"  DEBUG: Transformation matrix shapes:")
    for i, W in enumerate(transformations):
        print(f"    Subject {i}: {W.shape}")
    print(f"  DEBUG: Data list shapes:")
    for i, data in enumerate(data_list):
        print(f"    Subject {i}: {data.shape}")

    return srm, shared_response, transformations

def transform_to_shared_space(amplitudes, transformation_matrix):
    """
    개별 피험자 데이터를 공유 공간으로 변환

    **수학**:
    X_shared = X @ W
    - X: (n_timepoints, n_voxels) 원본 데이터
    - W: (n_voxels, k_features) 변환 행렬
    - X_shared: (n_timepoints, k_features) 공유 공간 표상

    Args:
        amplitudes: (n_runs * n_colors, n_voxels)
        transformation_matrix: (n_voxels, k_features)

    Returns:
        shared_amplitudes: (n_runs * n_colors, k_features)
    """
    shared_amplitudes = amplitudes @ transformation_matrix
    return shared_amplitudes

def compute_reconstruction_error(original, transformation_matrix, shared_response):
    """
    재구성 오류 계산

    **개념**:
    원본 데이터 X를 공유 공간으로 변환한 뒤 다시 복원했을 때의 오류

    **수학**:
    1. Forward: X_shared = X @ W
    2. Backward: X_reconstructed = X_shared @ W^T = (X @ W) @ W^T
    3. Error: ||X - X_reconstructed||_F (Frobenius norm)

    **해석**:
    - 낮은 오류: 피험자가 공유 구조에 잘 맞음 (HC 같음)
    - 높은 오류: 피험자가 공유 구조에서 벗어남 (CVD 다를 수 있음)

    Args:
        original: (n_timepoints, n_voxels) 원본 데이터
        transformation_matrix: (n_voxels, k_features)
        shared_response: (k_features, n_timepoints) 공유 반응

    Returns:
        error: 재구성 오류 (normalized by data size)
    """
    # Forward transform
    shared = original @ transformation_matrix  # (n_timepoints, k_features)

    # Backward transform
    reconstructed = shared @ transformation_matrix.T  # (n_timepoints, n_voxels)

    # Frobenius norm
    error = np.linalg.norm(original - reconstructed, 'fro')

    # Normalize by data size
    error_normalized = error / (original.shape[0] * original.shape[1])

    return error_normalized

# ============================================================================
# Cross-Subject Consistency in Shared Space
# ============================================================================

def evaluate_consistency_in_shared_space(data_list, transformations, subjects_info, n_colors=8):
    """
    공유 공간에서 피험자 간 RDM 일관성 평가

    **목적**:
    SRM이 실제로 일관성을 개선했는지 확인

    **방법**:
    1. 각 피험자 데이터를 공유 공간으로 변환
    2. 공유 공간에서 RDM 계산
    3. 피험자 간 RDM 유사도 계산
    4. 원본 공간 결과와 비교

    **BrainIAK SRM 출력**:
    - transformations[i]: (n_voxels, k_features) - transformation matrix
    - shared_response: (k_features, n_timepoints) - 공유 템플릿

    Args:
        data_list: List of original data (n_timepoints, n_voxels)
        transformations: List of transformation matrices (n_voxels, k_features)
        subjects_info: 피험자 정보
        n_colors: 색상 개수

    Returns:
        rdm_similarities: 피험자 쌍별 RDM 유사도
        mean_similarity: 평균 유사도
    """
    n_subjects = len(data_list)
    n_runs = subjects_info[0]['n_runs']

    print(f"DEBUG: evaluate_consistency_in_shared_space")
    print(f"  n_subjects: {n_subjects}")
    print(f"  n_runs: {n_runs}")

    # 각 피험자의 공유 공간 RDM 계산
    shared_rdms = []
    for i in range(n_subjects):
        # BrainIAK SRM returns transformations as ALREADY transformed data!
        # transformations[i] shape: (n_timepoints, k_features)
        # This is NOT a transformation matrix, but shared space coefficients
        shared_data = transformations[i]  # Already in shared space!

        print(f"  Subject {i}:")
        print(f"    shared_data.shape: {shared_data.shape}")

        # Reshape to (n_runs, n_colors, k_features)
        shared_data_reshaped = shared_data.reshape(n_runs, n_colors, -1)

        # RDM 계산
        rdm = compute_rdm(shared_data_reshaped)
        shared_rdms.append(rdm)

    # 피험자 쌍별 RDM 유사도
    rdm_similarities = np.zeros((n_subjects, n_subjects))
    for i in range(n_subjects):
        for j in range(i+1, n_subjects):
            similarity, _ = compute_rdm_similarity(shared_rdms[i], shared_rdms[j])
            rdm_similarities[i, j] = similarity
            rdm_similarities[j, i] = similarity

    # 대각선 = 1
    np.fill_diagonal(rdm_similarities, 1.0)

    # 평균 유사도 (상삼각만)
    triu_indices = np.triu_indices(n_subjects, k=1)
    mean_similarity = rdm_similarities[triu_indices].mean()

    return rdm_similarities, mean_similarity, shared_rdms

# ============================================================================
# CVD Analysis
# ============================================================================

def analyze_cvd_in_shared_space(cvd_data_list, cvd_subjects_info, srm_model,
                                  hc_transformations, hc_data_list, n_colors=8):
    """
    CVD 피험자를 HC 공유 공간에 투영하고 분석

    **방법**:
    1. CVD 데이터에 대한 변환 행렬 학습 (SRM transform)
    2. CVD를 공유 공간으로 투영
    3. 재구성 오류 계산: CVD vs. HC 평균
    4. 공유 공간에서 RDM 계산
    5. CVD RDM vs. HC RDMs 비교

    Args:
        cvd_data_list: CVD 데이터 리스트
        cvd_subjects_info: CVD 정보
        srm_model: 학습된 SRM 모델
        hc_transformations: HC 변환 행렬 리스트
        hc_data_list: HC 원본 데이터 리스트
        n_colors: 색상 개수

    Returns:
        cvd_results: CVD 분석 결과 딕셔너리
    """
    print("Analyzing CVD subjects in shared space...")

    cvd_results = []

    # HC 재구성 오류 계산 (reference)
    hc_errors = []
    for i, hc_data in enumerate(hc_data_list):
        error = compute_reconstruction_error(
            hc_data, hc_transformations[i], srm_model.s_
        )
        hc_errors.append(error)

    hc_error_mean = np.mean(hc_errors)
    hc_error_std = np.std(hc_errors)

    print(f"  HC reconstruction error: {hc_error_mean:.4f} ± {hc_error_std:.4f}")

    # 각 CVD 피험자 분석
    for i, cvd_data in enumerate(cvd_data_list):
        cvd_id = cvd_subjects_info[i]['subject']
        print(f"  Analyzing sub-{cvd_id}...")

        # CVD 변환 행렬 학습 (SRM transform)
        # 공유 구조 S는 고정, CVD에 대한 W만 학습
        cvd_transformation = srm_model.transform_subject(cvd_data)

        # 재구성 오류
        cvd_error = compute_reconstruction_error(
            cvd_data, cvd_transformation, srm_model.s_
        )

        # Z-score: HC 분포 대비 CVD 위치
        z_score = (cvd_error - hc_error_mean) / hc_error_std

        print(f"    Reconstruction error: {cvd_error:.4f} (z = {z_score:.2f})")

        # 공유 공간에서 RDM
        cvd_shared = cvd_data @ cvd_transformation
        n_runs = cvd_subjects_info[i]['n_runs']
        cvd_shared_reshaped = cvd_shared.reshape(n_runs, n_colors, -1)
        cvd_rdm = compute_rdm(cvd_shared_reshaped)

        cvd_results.append({
            'subject': cvd_id,
            'reconstruction_error': cvd_error,
            'z_score': z_score,
            'transformation': cvd_transformation,
            'rdm': cvd_rdm
        })

    return cvd_results, hc_error_mean, hc_error_std

# ============================================================================
# Main Analysis
# ============================================================================

def run_srm_analysis(args):
    """SRM 분석 실행"""
    print("=" * 80)
    print("Option 2: Shared Response Model (SRM) Analysis")
    print("=" * 80)
    print(f"Timestamp: {args.timestamp}")
    print(f"Dataset: {args.dataset}")
    print(f"HC subjects: {args.hc_subjects}")
    print(f"CVD subjects: {args.cvd_subjects}")
    print(f"ROIs: {args.rois}")
    print(f"k_features: {args.k_features}")
    print(f"n_iter: {args.n_iter}")
    print()

    if not BRAINIAK_AVAILABLE:
        print("❌ BrainIAK not available. Please install: pip install brainiak")
        return

    # 출력 디렉토리
    if args.output_dir is None:
        output_dir = Path(f'analysis/group_level/option2_results/{args.timestamp}')
    else:
        output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()

    # 각 ROI에 대해 분석
    all_results = {}

    for roi in args.rois:
        print("=" * 80)
        print(f"ROI: {roi}")
        print("=" * 80)

        roi_output_dir = output_dir / roi
        roi_output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # HC 데이터 로드
            hc_data_list, hc_subjects_info, n_voxels_min = load_all_subjects_amplitudes(
                args.hc_subjects, roi, args.timestamp, args.dataset
            )

            # k_features 자동 조정 (복셀 수보다 클 수 없음)
            k_features_adjusted = min(n_voxels_min, args.k_features)
            if k_features_adjusted < args.k_features:
                print(f"  ⚠️ k_features adjusted: {args.k_features} → {k_features_adjusted} (limited by n_voxels={n_voxels_min})")

            # SRM 학습
            srm_model, shared_response, hc_transformations = fit_srm(
                hc_data_list, k_features=k_features_adjusted, n_iter=args.n_iter
            )

            # 공유 공간에서 일관성 평가
            rdm_similarities, mean_similarity, shared_rdms = evaluate_consistency_in_shared_space(
                hc_data_list, hc_transformations, hc_subjects_info
            )

            print(f"  Mean RDM similarity in shared space: {mean_similarity:.3f}")

            # 결과 저장
            roi_results = {
                'roi': roi,
                'n_hc': len(hc_data_list),
                'k_features': k_features_adjusted,
                'n_voxels_used': n_voxels_min,
                'shared_response': shared_response,
                'hc_transformations': hc_transformations,
                'hc_subjects_info': hc_subjects_info,
                'rdm_similarities': rdm_similarities,
                'mean_rdm_similarity': mean_similarity,
                'shared_rdms': shared_rdms,
                'srm_model': srm_model
            }

            # CVD 분석 (있다면)
            if len(args.cvd_subjects) > 0:
                cvd_data_list, cvd_subjects_info, _ = load_all_subjects_amplitudes(
                    args.cvd_subjects, roi, args.timestamp, args.dataset
                )

                cvd_results, hc_error_mean, hc_error_std = analyze_cvd_in_shared_space(
                    cvd_data_list, cvd_subjects_info, srm_model,
                    hc_transformations, hc_data_list
                )

                roi_results['cvd_results'] = cvd_results
                roi_results['hc_error_mean'] = hc_error_mean
                roi_results['hc_error_std'] = hc_error_std

            all_results[roi] = roi_results

            # 시각화 생성
            create_srm_visualizations(roi_results, roi_output_dir, args)

            # 결과 저장 (numpy arrays)
            np.savez(
                roi_output_dir / 'srm_results.npz',
                shared_response=shared_response,
                rdm_similarities=rdm_similarities,
                mean_similarity=mean_similarity
            )

            print(f"  ✓ Results saved to {roi_output_dir}")
            print()

        except Exception as e:
            print(f"  ❌ Error processing {roi}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # 전체 요약 생성
    create_summary_report(all_results, output_dir, args)

    print()
    print("=" * 80)
    print("SRM Analysis complete!")
    print(f"Results saved to: {output_dir}")
    print("=" * 80)

# ============================================================================
# Visualizations
# ============================================================================

def create_srm_visualizations(roi_results, output_dir, args):
    """SRM 결과 시각화"""
    print("  Creating visualizations...")

    # 1. RDM similarity matrix (HC subjects in shared space)
    create_rdm_similarity_heatmap(roi_results, output_dir)

    # 2. Shared RDMs (각 HC 피험자)
    create_shared_rdm_grid(roi_results, output_dir, args)

    # 3. CVD comparison (if available)
    if 'cvd_results' in roi_results:
        create_cvd_comparison_plots(roi_results, output_dir, args)

    print("  ✓ Visualizations complete")

def create_rdm_similarity_heatmap(roi_results, output_dir):
    """공유 공간에서 RDM 유사도 히트맵"""
    rdm_similarities = roi_results['rdm_similarities']
    subjects = [info['subject'] for info in roi_results['hc_subjects_info']]

    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(rdm_similarities, cmap='RdYlGn', vmin=-0.5, vmax=1.0)

    # Annotations
    for i in range(len(subjects)):
        for j in range(len(subjects)):
            text = ax.text(j, i, f'{rdm_similarities[i, j]:.2f}',
                          ha="center", va="center", color="black", fontsize=9)

    ax.set_xticks(range(len(subjects)))
    ax.set_yticks(range(len(subjects)))
    ax.set_xticklabels([f'sub-{s}' for s in subjects], rotation=45, ha='right')
    ax.set_yticklabels([f'sub-{s}' for s in subjects])
    ax.set_title(f'{roi_results["roi"]}: RDM Similarity in Shared Space', fontsize=12, fontweight='bold')

    plt.colorbar(im, ax=ax, label='Spearman Correlation')
    plt.tight_layout()
    save_path = output_dir / 'rdm_similarity_shared_space.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

def create_shared_rdm_grid(roi_results, output_dir, args):
    """공유 공간에서 각 피험자의 RDM"""
    shared_rdms = roi_results['shared_rdms']
    subjects = [info['subject'] for info in roi_results['hc_subjects_info']]
    n_subjects = len(subjects)

    fig, axes = plt.subplots(2, (n_subjects + 1) // 2, figsize=(12, 8))
    axes = axes.flatten()

    for i, (rdm, subject_id) in enumerate(zip(shared_rdms, subjects)):
        im = axes[i].imshow(rdm, cmap='viridis', vmin=0, vmax=2)
        axes[i].set_title(f'sub-{subject_id}', fontsize=10)
        axes[i].set_xlabel('Color')
        axes[i].set_ylabel('Color')
        plt.colorbar(im, ax=axes[i], fraction=0.046)

    # Hide extra subplots
    for i in range(n_subjects, len(axes)):
        axes[i].axis('off')

    fig.suptitle(f'{roi_results["roi"]}: RDMs in Shared Space (HC)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    save_path = output_dir / 'shared_rdms_grid.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

def create_cvd_comparison_plots(roi_results, output_dir, args):
    """CVD vs. HC 비교 플롯"""
    cvd_results = roi_results['cvd_results']
    hc_error_mean = roi_results['hc_error_mean']
    hc_error_std = roi_results['hc_error_std']

    # Reconstruction error comparison
    fig, ax = plt.subplots(figsize=(10, 6))

    # HC distribution
    ax.axhspan(hc_error_mean - 2*hc_error_std, hc_error_mean + 2*hc_error_std,
               alpha=0.2, color='blue', label='HC ± 2 SD')
    ax.axhline(hc_error_mean, color='blue', linestyle='--', linewidth=2, label='HC mean')

    # CVD points
    cvd_errors = [r['reconstruction_error'] for r in cvd_results]
    cvd_subjects = [r['subject'] for r in cvd_results]
    x_pos = range(len(cvd_subjects))

    ax.scatter(x_pos, cvd_errors, s=150, color='red', marker='o', zorder=3, label='CVD')

    for i, (subj, err, z) in enumerate(zip(cvd_subjects, cvd_errors,
                                             [r['z_score'] for r in cvd_results])):
        ax.text(i, err + 0.01, f'sub-{subj}\nz={z:.2f}',
                ha='center', va='bottom', fontsize=9)

    ax.set_xticks(x_pos)
    ax.set_xticklabels([f'sub-{s}' for s in cvd_subjects])
    ax.set_xlabel('CVD Subjects', fontsize=12)
    ax.set_ylabel('Reconstruction Error', fontsize=12)
    ax.set_title(f'{roi_results["roi"]}: CVD vs. HC Reconstruction Error', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    save_path = output_dir / 'cvd_reconstruction_error.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

# ============================================================================
# Summary Report
# ============================================================================

def create_summary_report(all_results, output_dir, args):
    """전체 요약 리포트 생성"""
    print()
    print("Creating summary report...")

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("Option 2: Shared Response Model (SRM) Analysis - Summary")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append(f"Timestamp: {args.timestamp}")
    report_lines.append(f"k_features: {args.k_features}")
    report_lines.append(f"n_iter: {args.n_iter}")
    report_lines.append(f"HC subjects: {', '.join(args.hc_subjects)}")
    report_lines.append(f"CVD subjects: {', '.join(args.cvd_subjects) if args.cvd_subjects else 'None'}")
    report_lines.append("")
    report_lines.append("-" * 80)
    report_lines.append("Results by ROI:")
    report_lines.append("-" * 80)

    for roi, results in all_results.items():
        report_lines.append(f"\n{roi}:")
        report_lines.append(f"  Voxels used: {results['n_voxels_used']}")
        report_lines.append(f"  k_features used: {results['k_features']} (requested: {args.k_features})")
        report_lines.append(f"  Mean RDM similarity (shared space): {results['mean_rdm_similarity']:.3f}")

        if 'cvd_results' in results:
            report_lines.append(f"  HC reconstruction error: {results['hc_error_mean']:.4f} ± {results['hc_error_std']:.4f}")
            report_lines.append("  CVD reconstruction errors:")
            for cvd_res in results['cvd_results']:
                report_lines.append(f"    sub-{cvd_res['subject']}: {cvd_res['reconstruction_error']:.4f} (z={cvd_res['z_score']:.2f})")

    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("Interpretation:")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("SRM은 개별 피험자의 복셀 공간을 공유 잠재 공간으로 변환하여")
    report_lines.append("해부학적 차이를 넘어 기능적 대응을 찾습니다.")
    report_lines.append("")
    report_lines.append("높은 RDM similarity (> 0.5):")
    report_lines.append("  → SRM이 공유 구조를 성공적으로 찾음")
    report_lines.append("  → HC 피험자들이 기능적으로 유사한 색상 표상 공유")
    report_lines.append("")
    report_lines.append("낮은 RDM similarity (< 0.3):")
    report_lines.append("  → 공유 구조가 약하거나 없음")
    report_lines.append("  → k_features 조정 또는 다른 방법 고려")
    report_lines.append("")
    report_lines.append("CVD z-score > 2:")
    report_lines.append("  → CVD가 HC 공유 구조에서 유의미하게 벗어남")
    report_lines.append("  → 색각 결핍이 신경 표상에 영향을 미침")
    report_lines.append("")

    report_text = '\n'.join(report_lines)
    print(report_text)

    # 파일 저장
    report_path = output_dir / 'srm_analysis_summary.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"✓ Summary report saved to {report_path}")

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    args = parse_args()
    run_srm_analysis(args)
