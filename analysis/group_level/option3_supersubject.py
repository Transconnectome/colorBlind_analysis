#!/usr/bin/env python3
"""
option3_supersubject.py
=======================

Option 3: "Supersubject" Method (Brouwer & Heeger 2009, 2013)
⭐⭐ 고전적 기준선

**목적**:
모든 HC 피험자의 데이터를 하나의 "supersubject"로 결합하여
그룹 수준 색상 표상 분석

**Brouwer & Heeger의 방법**:
"Measurements were combined across subjects and scanning sessions to increase sensitivity"
- Journal of Neuroscience, 2009, 2013

**핵심 아이디어**:
┌────────────────────────────────────────────────────────────────┐
│ 개별 피험자: n_runs × 8_colors × n_voxels                      │
│ Supersubject: (n_subjects * n_runs) × 8_colors × n_voxels     │
│                                                                │
│ 예시:                                                          │
│ - 6명 HC × 8 runs = 48 runs                                   │
│ - 48 runs × 8 colors × n_voxels                               │
│ → 거대한 데이터셋으로 BH2009 모델 학습                         │
└────────────────────────────────────────────────────────────────┘

**가정**:
⚠️ **중요**: 이 방법은 모든 피험자가 유사한 voxel-to-color 매핑을 가진다고 가정
- 즉, 해부학적으로 정렬된 복셀이 기능적으로도 대응된다고 가정
- Phase 1 결과에서 이 가정이 약하다는 것을 확인했지만, 고전적 기준선으로 유용

**장점**:
- ✅ 매우 간단한 구현
- ✅ 통계적 검정력 증가 (더 많은 데이터)
- ✅ Brouwer & Heeger 원본 논문에서 사용 (인용 용이)
- ✅ 그룹 수준 채널 모델 파라미터 도출 가능

**단점**:
- ❌ 개인차를 명시적으로 모델링하지 않음
- ❌ 강한 가정: 모든 피험자가 비슷한 복셀-채널 매핑
- ❌ 데이터 풀링이 개별 신호를 희석할 수 있음
- ❌ 명시적 정렬 없음 (해부학적 정규화에만 의존)

**이 방법을 사용하는 이유**:
1. **고전적 기준선**: Brouwer & Heeger가 사용한 방법과 직접 비교
2. **간단한 구현**: SRM/Hyperalignment보다 훨씬 간단
3. **그룹 수준 파라미터**: 도출된 채널 특성 (bandwidth, gain) 분석 가능

**Output**:
1. Supersubject 채널 모델 (8 color channels)
2. 그룹 수준 채널 파라미터
   - Bandwidth: 채널 선택성 (좁을수록 → 특정 색상에 selective)
   - Gain: 채널 반응 강도
3. 개별 CVD와 supersubject 비교
4. RDM: Supersubject vs. 개별 피험자

Usage:
    python analysis/group_level/option3_supersubject.py \\
        --timestamp baseline81_deob_determin \\
        --hc-subjects 01 02 03 05 06 07 \\
        --cvd-subjects 08 09 10 \\
        --rois V1 V2 V3 hV4

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

# ============================================================================
# Configuration
# ============================================================================

def parse_args():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(
        description='Option 3: Supersubject Analysis (Brouwer & Heeger method)'
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

def create_supersubject(subject_ids, roi, timestamp, dataset='deoblique_v2'):
    """
    Supersubject 생성: 모든 HC 피험자의 데이터를 run 차원으로 연결

    **Brouwer & Heeger 방법**:
    "Measurements were combined across subjects and scanning sessions"

    **절차**:
    1. 각 피험자의 amplitudes 로드
    2. 복셀 수가 가장 적은 피험자에 맞춰 모든 피험자 복셀 수 통일
       (또는 공통 복셀만 사용)
    3. Run 차원으로 concatenate

    **중요**: 복셀 수가 피험자마다 다를 수 있음!
    - 옵션 1: 최소 복셀 수에 맞춰 자르기
    - 옵션 2: 공통 복셀만 사용 (Phase 1A에서 계산된 경우)
    - 여기서는 옵션 1 사용 (간단)

    Args:
        subject_ids: HC 피험자 ID 리스트
        roi: ROI 이름
        timestamp: 분석 timestamp
        dataset: 데이터셋 이름

    Returns:
        supersubject_amplitudes: (n_subjects*n_runs, n_colors, n_voxels_min)
        subjects_info: 각 피험자 정보 딕셔너리
        n_voxels_used: 사용된 복셀 수
    """
    print(f"Creating supersubject for {roi}...")
    print(f"  HC subjects: {subject_ids}")

    amplitudes_list = []
    subjects_info = []
    n_voxels_list = []

    # 각 피험자 데이터 로드
    for subject_id in subject_ids:
        try:
            amplitudes, result_dir = load_subject_amplitudes(
                subject_id, roi, timestamp, dataset
            )
            n_runs, n_colors, n_voxels = amplitudes.shape

            amplitudes_list.append(amplitudes)
            n_voxels_list.append(n_voxels)

            subjects_info.append({
                'subject': subject_id,
                'n_runs': n_runs,
                'n_colors': n_colors,
                'n_voxels': n_voxels
            })

            print(f"    sub-{subject_id}: {amplitudes.shape}")

        except FileNotFoundError as e:
            print(f"    sub-{subject_id}: ⚠️ {e}")
            continue

    if len(amplitudes_list) == 0:
        raise ValueError(f"No HC data loaded for {roi}")

    # 최소 복셀 수 찾기
    n_voxels_min = min(n_voxels_list)
    print(f"  Minimum voxels across subjects: {n_voxels_min}")
    print(f"  Truncating all subjects to {n_voxels_min} voxels")

    # 모든 피험자를 최소 복셀 수에 맞춰 자르기
    amplitudes_truncated = []
    for amplitudes in amplitudes_list:
        amplitudes_truncated.append(amplitudes[:, :, :n_voxels_min])

    # Run 차원으로 concatenate
    # 예: 6 subjects × 8 runs → 48 runs
    supersubject_amplitudes = np.concatenate(amplitudes_truncated, axis=0)

    print(f"  Supersubject shape: {supersubject_amplitudes.shape}")
    print(f"    Total runs: {supersubject_amplitudes.shape[0]} ({len(subject_ids)} subjects × {subjects_info[0]['n_runs']} runs)")
    print(f"    Colors: {supersubject_amplitudes.shape[1]}")
    print(f"    Voxels: {supersubject_amplitudes.shape[2]}")
    print()

    return supersubject_amplitudes, subjects_info, n_voxels_min

# ============================================================================
# RDM Computation
# ============================================================================

def compute_rdm(amplitudes):
    """
    RDM 계산

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
# Channel Model Analysis
# ============================================================================

def estimate_channel_parameters(amplitudes):
    """
    채널 모델 파라미터 추정

    **Brouwer & Heeger 채널 모델**:
    - 8가지 색상에 대해 8개의 채널 (color-selective neurons)
    - 각 채널은 선호 색상(preferred color)에 대해 bell-shaped tuning curve

    **파라미터**:
    1. **Bandwidth (대역폭)**:
       - 채널의 선택성 (selectivity)
       - 좁은 bandwidth → 특정 색상에 매우 selective
       - 넓은 bandwidth → 여러 색상에 반응

    2. **Gain (이득)**:
       - 채널의 반응 강도
       - 높은 gain → 강한 반응
       - 낮은 gain → 약한 반응

    3. **Peak response (최대 반응)**:
       - 각 채널이 가장 강하게 반응하는 색상

    **여기서는 간단한 추정 방법 사용**:
    - Bandwidth: 각 색상에 대한 반응 변동성 (std dev)
    - Gain: 평균 반응 강도
    - Peak: 최대 반응 색상

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        params: 채널 파라미터 딕셔너리
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Run 평균
    amplitudes_avg = amplitudes.mean(axis=0)  # (n_colors, n_voxels)

    # 각 색상에 대한 평균 반응 (복셀 평균)
    mean_response_per_color = amplitudes_avg.mean(axis=1)  # (n_colors,)

    # 각 색상에 대한 반응 변동성 (복셀 간 std)
    std_response_per_color = amplitudes_avg.std(axis=1)  # (n_colors,)

    # 전체 평균
    overall_mean = mean_response_per_color.mean()
    overall_std = mean_response_per_color.std()

    # 가장 강하게 반응하는 색상
    peak_color = np.argmax(mean_response_per_color)

    # Bandwidth 추정 (간단하게 std의 평균)
    bandwidth = std_response_per_color.mean()

    # Gain 추정 (평균 반응 강도)
    gain = overall_mean

    params = {
        'mean_response_per_color': mean_response_per_color,
        'std_response_per_color': std_response_per_color,
        'overall_mean': overall_mean,
        'overall_std': overall_std,
        'peak_color': peak_color,
        'bandwidth': bandwidth,
        'gain': gain
    }

    return params

# ============================================================================
# Main Analysis
# ============================================================================

def run_supersubject_analysis(args):
    """Supersubject 분석 실행"""
    print("=" * 80)
    print("Option 3: Supersubject Analysis (Brouwer & Heeger 2009)")
    print("=" * 80)
    print(f"Timestamp: {args.timestamp}")
    print(f"Dataset: {args.dataset}")
    print(f"HC subjects: {args.hc_subjects}")
    print(f"CVD subjects: {args.cvd_subjects}")
    print(f"ROIs: {args.rois}")
    print()

    # 출력 디렉토리
    if args.output_dir is None:
        output_dir = Path(f'analysis/group_level/option3_results/{args.timestamp}')
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
            # Supersubject 생성
            supersubject_amplitudes, hc_subjects_info, n_voxels_used = create_supersubject(
                args.hc_subjects, roi, args.timestamp, args.dataset
            )

            # Supersubject RDM 계산
            supersubject_rdm = compute_rdm(supersubject_amplitudes)
            print(f"Supersubject RDM computed")

            # Supersubject 채널 파라미터 추정
            supersubject_params = estimate_channel_parameters(supersubject_amplitudes)
            print(f"Supersubject parameters:")
            print(f"  Bandwidth: {supersubject_params['bandwidth']:.3f}")
            print(f"  Gain: {supersubject_params['gain']:.3f}")
            print(f"  Peak color: {supersubject_params['peak_color']}")
            print()

            # 개별 HC 피험자 RDM 계산 및 supersubject와 비교
            hc_rdms = []
            hc_similarities = []

            print("Comparing individual HC subjects to supersubject...")
            for subject_id in args.hc_subjects:
                try:
                    amplitudes, _ = load_subject_amplitudes(
                        subject_id, roi, args.timestamp, args.dataset
                    )
                    # 복셀 수 맞추기
                    amplitudes_truncated = amplitudes[:, :, :n_voxels_used]

                    # RDM 계산
                    rdm = compute_rdm(amplitudes_truncated)
                    hc_rdms.append(rdm)

                    # Supersubject RDM과 비교
                    similarity, p_value = compute_rdm_similarity(rdm, supersubject_rdm)
                    hc_similarities.append(similarity)

                    print(f"  sub-{subject_id}: similarity = {similarity:.3f} (p = {p_value:.4f})")

                except FileNotFoundError:
                    continue

            mean_hc_similarity = np.mean(hc_similarities)
            std_hc_similarity = np.std(hc_similarities)
            print(f"  Mean HC-Supersubject similarity: {mean_hc_similarity:.3f} ± {std_hc_similarity:.3f}")
            print()

            # 결과 저장
            roi_results = {
                'roi': roi,
                'n_hc': len(args.hc_subjects),
                'n_voxels_used': n_voxels_used,
                'supersubject_amplitudes': supersubject_amplitudes,
                'supersubject_rdm': supersubject_rdm,
                'supersubject_params': supersubject_params,
                'hc_subjects_info': hc_subjects_info,
                'hc_rdms': hc_rdms,
                'hc_similarities': hc_similarities,
                'mean_hc_similarity': mean_hc_similarity,
                'std_hc_similarity': std_hc_similarity
            }

            # CVD 분석 (있다면)
            if len(args.cvd_subjects) > 0:
                cvd_results = analyze_cvd_subjects(
                    args.cvd_subjects, roi, args.timestamp, args.dataset,
                    supersubject_rdm, supersubject_params,
                    n_voxels_used, hc_similarities
                )
                roi_results['cvd_results'] = cvd_results

            all_results[roi] = roi_results

            # 시각화
            create_supersubject_visualizations(roi_results, roi_output_dir, args)

            # 결과 저장
            np.savez(
                roi_output_dir / 'supersubject_results.npz',
                supersubject_rdm=supersubject_rdm,
                hc_similarities=hc_similarities,
                mean_similarity=mean_hc_similarity
            )

            print(f"  ✓ Results saved to {roi_output_dir}")
            print()

        except Exception as e:
            print(f"  ❌ Error processing {roi}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # 전체 요약
    create_summary_report(all_results, output_dir, args)

    print()
    print("=" * 80)
    print("Supersubject Analysis complete!")
    print(f"Results saved to: {output_dir}")
    print("=" * 80)

# ============================================================================
# CVD Analysis
# ============================================================================

def analyze_cvd_subjects(cvd_subjects, roi, timestamp, dataset,
                          supersubject_rdm, supersubject_params,
                          n_voxels_used, hc_similarities):
    """
    CVD 피험자를 supersubject와 비교

    **비교 항목**:
    1. RDM 유사도: CVD RDM vs. Supersubject RDM
    2. 채널 파라미터: CVD bandwidth/gain vs. Supersubject
    3. Z-score: HC 분포 대비 CVD 위치

    Returns:
        cvd_results: CVD 분석 결과 리스트
    """
    print("Analyzing CVD subjects...")

    hc_mean_similarity = np.mean(hc_similarities)
    hc_std_similarity = np.std(hc_similarities)

    cvd_results = []

    for cvd_id in cvd_subjects:
        try:
            # CVD 데이터 로드
            amplitudes, _ = load_subject_amplitudes(
                cvd_id, roi, timestamp, dataset
            )
            amplitudes_truncated = amplitudes[:, :, :n_voxels_used]

            # RDM 계산
            cvd_rdm = compute_rdm(amplitudes_truncated)

            # Supersubject와 비교
            similarity, p_value = compute_rdm_similarity(cvd_rdm, supersubject_rdm)

            # Z-score
            z_score = (similarity - hc_mean_similarity) / hc_std_similarity

            # 채널 파라미터
            cvd_params = estimate_channel_parameters(amplitudes_truncated)

            # Bandwidth/Gain 차이
            bandwidth_diff = cvd_params['bandwidth'] - supersubject_params['bandwidth']
            gain_diff = cvd_params['gain'] - supersubject_params['gain']

            cvd_results.append({
                'subject': cvd_id,
                'rdm_similarity': similarity,
                'p_value': p_value,
                'z_score': z_score,
                'bandwidth': cvd_params['bandwidth'],
                'bandwidth_diff': bandwidth_diff,
                'gain': cvd_params['gain'],
                'gain_diff': gain_diff,
                'rdm': cvd_rdm
            })

            print(f"  sub-{cvd_id}:")
            print(f"    RDM similarity: {similarity:.3f} (z = {z_score:.2f})")
            print(f"    Bandwidth: {cvd_params['bandwidth']:.3f} (diff = {bandwidth_diff:+.3f})")
            print(f"    Gain: {cvd_params['gain']:.3f} (diff = {gain_diff:+.3f})")

        except FileNotFoundError as e:
            print(f"  sub-{cvd_id}: ⚠️ {e}")
            continue

    print()
    return cvd_results

# ============================================================================
# Visualizations
# ============================================================================

def create_supersubject_visualizations(roi_results, output_dir, args):
    """시각화 생성"""
    print("  Creating visualizations...")

    # 1. Supersubject RDM
    create_supersubject_rdm_plot(roi_results, output_dir)

    # 2. HC similarities bar plot
    create_hc_similarities_plot(roi_results, output_dir, args)

    # 3. RDM comparison grid (Supersubject + individual HCs)
    create_rdm_comparison_grid(roi_results, output_dir, args)

    # 4. CVD comparison (if available)
    if 'cvd_results' in roi_results:
        create_cvd_comparison_plots(roi_results, output_dir, args)

    print("  ✓ Visualizations complete")

def create_supersubject_rdm_plot(roi_results, output_dir):
    """Supersubject RDM"""
    rdm = roi_results['supersubject_rdm']

    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(rdm, cmap='viridis', vmin=0, vmax=2)
    ax.set_title(f'{roi_results["roi"]}: Supersubject RDM', fontsize=14, fontweight='bold')
    ax.set_xlabel('Color', fontsize=12)
    ax.set_ylabel('Color', fontsize=12)
    plt.colorbar(im, ax=ax, label='Dissimilarity')
    plt.tight_layout()

    save_path = output_dir / 'supersubject_rdm.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

def create_hc_similarities_plot(roi_results, output_dir, args):
    """HC-Supersubject similarities bar plot"""
    similarities = roi_results['hc_similarities']
    subjects = args.hc_subjects[:len(similarities)]

    fig, ax = plt.subplots(figsize=(10, 6))
    x_pos = range(len(subjects))

    bars = ax.bar(x_pos, similarities, color='skyblue', edgecolor='black', linewidth=1.5)

    # Mean line
    mean_sim = roi_results['mean_hc_similarity']
    ax.axhline(mean_sim, color='red', linestyle='--', linewidth=2, label=f'Mean = {mean_sim:.3f}')

    ax.set_xticks(x_pos)
    ax.set_xticklabels([f'sub-{s}' for s in subjects], rotation=45, ha='right')
    ax.set_xlabel('HC Subjects', fontsize=12)
    ax.set_ylabel('RDM Similarity with Supersubject', fontsize=12)
    ax.set_title(f'{roi_results["roi"]}: HC-Supersubject Similarity', fontsize=14, fontweight='bold')
    ax.set_ylim(-0.5, 1.0)
    ax.legend(loc='lower right')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    save_path = output_dir / 'hc_supersubject_similarities.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

def create_rdm_comparison_grid(roi_results, output_dir, args):
    """RDM comparison grid"""
    hc_rdms = roi_results['hc_rdms']
    supersubject_rdm = roi_results['supersubject_rdm']
    subjects = args.hc_subjects[:len(hc_rdms)]

    n_subjects = len(hc_rdms)
    n_cols = 3
    n_rows = (n_subjects + 2) // n_cols  # +1 for supersubject

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 4*n_rows))
    axes = axes.flatten()

    # Supersubject RDM (first)
    im0 = axes[0].imshow(supersubject_rdm, cmap='viridis', vmin=0, vmax=2)
    axes[0].set_title('Supersubject', fontsize=10, fontweight='bold')
    axes[0].set_xlabel('Color')
    axes[0].set_ylabel('Color')
    plt.colorbar(im0, ax=axes[0], fraction=0.046)

    # Individual HC RDMs
    for i, (rdm, subject_id) in enumerate(zip(hc_rdms, subjects), start=1):
        im = axes[i].imshow(rdm, cmap='viridis', vmin=0, vmax=2)
        axes[i].set_title(f'sub-{subject_id}', fontsize=10)
        axes[i].set_xlabel('Color')
        axes[i].set_ylabel('Color')
        plt.colorbar(im, ax=axes[i], fraction=0.046)

    # Hide extra subplots
    for i in range(n_subjects + 1, len(axes)):
        axes[i].axis('off')

    fig.suptitle(f'{roi_results["roi"]}: RDM Comparison', fontsize=14, fontweight='bold')
    plt.tight_layout()
    save_path = output_dir / 'rdm_comparison_grid.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

def create_cvd_comparison_plots(roi_results, output_dir, args):
    """CVD vs. Supersubject comparison"""
    cvd_results = roi_results['cvd_results']
    hc_similarities = roi_results['hc_similarities']
    hc_mean = roi_results['mean_hc_similarity']
    hc_std = roi_results['std_hc_similarity']

    # 1. RDM similarity comparison
    fig, ax = plt.subplots(figsize=(10, 6))

    # HC distribution
    ax.axhspan(hc_mean - 2*hc_std, hc_mean + 2*hc_std,
               alpha=0.2, color='blue', label='HC ± 2 SD')
    ax.axhline(hc_mean, color='blue', linestyle='--', linewidth=2, label='HC mean')

    # HC individual points
    x_hc = [-1] * len(hc_similarities)
    ax.scatter(x_hc, hc_similarities, s=80, color='blue', alpha=0.5, marker='o')

    # CVD points
    cvd_sims = [r['rdm_similarity'] for r in cvd_results]
    cvd_subjects = [r['subject'] for r in cvd_results]
    x_cvd = range(len(cvd_subjects))

    ax.scatter(x_cvd, cvd_sims, s=150, color='red', marker='o', zorder=3, label='CVD')

    for i, (subj, sim, z) in enumerate(zip(cvd_subjects, cvd_sims,
                                             [r['z_score'] for r in cvd_results])):
        ax.text(i, sim + 0.03, f'sub-{subj}\nz={z:.2f}',
                ha='center', va='bottom', fontsize=9)

    ax.set_xticks([-1] + list(x_cvd))
    ax.set_xticklabels(['HC'] + [f'sub-{s}' for s in cvd_subjects])
    ax.set_xlabel('Subjects', fontsize=12)
    ax.set_ylabel('RDM Similarity with Supersubject', fontsize=12)
    ax.set_title(f'{roi_results["roi"]}: CVD vs. HC Comparison', fontsize=14, fontweight='bold')
    ax.set_ylim(-0.5, 1.0)
    ax.legend(loc='lower right')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    save_path = output_dir / 'cvd_comparison.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

# ============================================================================
# Summary Report
# ============================================================================

def create_summary_report(all_results, output_dir, args):
    """전체 요약 리포트"""
    print()
    print("Creating summary report...")

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("Option 3: Supersubject Analysis - Summary")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("Brouwer & Heeger (2009) Method:")
    report_lines.append("\"Measurements were combined across subjects and scanning sessions\"")
    report_lines.append("")
    report_lines.append(f"Timestamp: {args.timestamp}")
    report_lines.append(f"HC subjects: {', '.join(args.hc_subjects)}")
    report_lines.append(f"CVD subjects: {', '.join(args.cvd_subjects) if args.cvd_subjects else 'None'}")
    report_lines.append("")
    report_lines.append("-" * 80)
    report_lines.append("Results by ROI:")
    report_lines.append("-" * 80)

    for roi, results in all_results.items():
        report_lines.append(f"\n{roi}:")
        report_lines.append(f"  Voxels used: {results['n_voxels_used']}")
        report_lines.append(f"  Total runs in supersubject: {results['supersubject_amplitudes'].shape[0]}")
        report_lines.append(f"  Mean HC-Supersubject similarity: {results['mean_hc_similarity']:.3f} ± {results['std_hc_similarity']:.3f}")

        report_lines.append(f"\n  Supersubject parameters:")
        params = results['supersubject_params']
        report_lines.append(f"    Bandwidth: {params['bandwidth']:.3f}")
        report_lines.append(f"    Gain: {params['gain']:.3f}")

        if 'cvd_results' in results:
            report_lines.append(f"\n  CVD results:")
            for cvd in results['cvd_results']:
                report_lines.append(f"    sub-{cvd['subject']}:")
                report_lines.append(f"      RDM similarity: {cvd['rdm_similarity']:.3f} (z={cvd['z_score']:.2f})")
                report_lines.append(f"      Bandwidth: {cvd['bandwidth']:.3f} (diff={cvd['bandwidth_diff']:+.3f})")
                report_lines.append(f"      Gain: {cvd['gain']:.3f} (diff={cvd['gain_diff']:+.3f})")

    report_lines.append("")
    report_lines.append("=" * 80)
    report_lines.append("Interpretation:")
    report_lines.append("=" * 80)
    report_lines.append("")
    report_lines.append("높은 HC-Supersubject similarity (> 0.5):")
    report_lines.append("  → 개별 피험자가 그룹 평균과 유사")
    report_lines.append("  → Supersubject 방법이 합리적")
    report_lines.append("")
    report_lines.append("낮은 HC-Supersubject similarity (< 0.3):")
    report_lines.append("  → 개별 피험자가 그룹 평균과 다름")
    report_lines.append("  → 개인차가 크고, pooling이 신호를 희석")
    report_lines.append("  → SRM 같은 명시적 정렬 방법 필요")
    report_lines.append("")
    report_lines.append("CVD z-score < -2:")
    report_lines.append("  → CVD가 HC supersubject와 유의미하게 다름")
    report_lines.append("  → 색각 결핍이 그룹 수준 표상에서 벗어남")
    report_lines.append("")

    report_text = '\n'.join(report_lines)
    print(report_text)

    report_path = output_dir / 'supersubject_summary.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_text)

    print(f"✓ Summary report saved to {report_path}")

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    args = parse_args()
    run_supersubject_analysis(args)
