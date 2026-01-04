#!/usr/bin/env python3
"""
option1_within_subject_reliability.py
======================================

Option 1: Within-Subject Reliability Analysis (피험자 내 신뢰도 분석)
⭐⭐⭐ 최우선 진단 분석 (다른 모든 분석 전에 필수)

**목적**:
개별 피험자의 RDM이 얼마나 안정적인가를 평가하여, 피험자 간 낮은 일관성이
실제 신호인지 노이즈인지 판단

**핵심 질문**:
"각 피험자의 색상 표상이 자기 자신 내에서도 일관적인가?"

**방법**: Split-Half Reliability
- 8 run을 두 그룹으로 분할 (first half vs. second half)
- 각 half에서 RDM 계산
- 두 RDM 간 상관계수 측정 (Spearman correlation)

**해석 기준**:
┌─────────────────┬──────────────┬────────────────────────────────────────┐
│ 신뢰도 범위      │ 해석         │ 다음 단계                               │
├─────────────────┼──────────────┼────────────────────────────────────────┤
│ r > 0.7         │ ✅ 높은 신뢰도│ 개별 RDM이 안정적                       │
│                 │              │ → 피험자 간 변동성은 실제 신호          │
│                 │              │ → SRM/Supersubject로 진행 가능          │
├─────────────────┼──────────────┼────────────────────────────────────────┤
│ 0.5 < r < 0.7   │ ⚠️ 보통 신뢰도│ 일부 안정성 있지만 노이즈 많음          │
│                 │              │ → 더 많은 스무딩/평균 고려              │
│                 │              │ → 신중하게 진행                         │
├─────────────────┼──────────────┼────────────────────────────────────────┤
│ r < 0.5         │ ❌ 낮은 신뢰도│ 개별 RDM이 신뢰할 수 없음               │
│                 │              │ → 데이터 품질 문제 (전처리, SNR, 등록) │
│                 │              │ → 그룹 분석 전에 수정 필요              │
└─────────────────┴──────────────┴────────────────────────────────────────┘

**왜 이것이 중요한가?**
┌──────────────────────────────────────────────────────────────────┐
│ 만약 피험자 내 신뢰도가 낮다면:                                   │
│ - 피험자 간 낮은 일관성 = 노이즈 때문 (전처리 문제)              │
│ - SRM/Supersubject 적용해도 의미 없음                            │
│ - 먼저 데이터 품질을 개선해야 함                                 │
│                                                                  │
│ 만약 피험자 내 신뢰도가 높다면:                                   │
│ - 피험자 간 낮은 일관성 = 실제 개인차 (생물학적 변동성)          │
│ - SRM/Supersubject로 공통 구조 찾기 시도 가능                    │
│ - "개인차" 서사로 논문 작성 가능                                 │
└──────────────────────────────────────────────────────────────────┘

**Spearman-Brown Correction** (선택적):
- Split-half reliability는 절반 데이터만 사용하므로 과소평가될 수 있음
- Spearman-Brown formula: r_full = (2 * r_half) / (1 + r_half)
- 전체 데이터 사용 시 예상 신뢰도 추정

**출력**:
1. 피험자별, ROI별 split-half reliability
2. 요약 통계 (평균, 범위)
3. 시각화:
   - Reliability by subject and ROI
   - RDM comparison (first half vs. second half)
4. 해석 가이드

Usage:
    python analysis/group_level/option1_within_subject_reliability.py \\
        --timestamp baseline81_deob_determin \\
        --subjects 01 02 03 05 06 07 \\
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
        description='Option 1: Within-Subject Reliability Analysis'
    )
    parser.add_argument('--timestamp', type=str, default='baseline81_deob_determin',
                        help='분석 timestamp (예: baseline81_deob_determin)')
    parser.add_argument('--dataset', type=str, default='deoblique_v2',
                        help='데이터셋 (deoblique_v2 or original)')
    parser.add_argument('--subjects', type=str, nargs='+',
                        default=['01', '02', '03', '05', '06', '07'],
                        help='피험자 ID 리스트')
    parser.add_argument('--rois', type=str, nargs='+',
                        default=['V1', 'V2', 'V3', 'hV4'],
                        help='ROI 리스트')
    parser.add_argument('--split-method', type=str, default='first-second',
                        choices=['first-second', 'odd-even'],
                        help='Split 방법: first-second (run 1-4 vs 5-8) 또는 odd-even (홀수 vs 짝수 run)')
    parser.add_argument('--output-dir', type=str, default=None,
                        help='출력 디렉토리 (기본값: analysis/group_level/option1_results/{timestamp})')
    return parser.parse_args()

# ============================================================================
# Data Loading
# ============================================================================

def load_subject_amplitudes(subject_id, roi, timestamp, dataset='deoblique_v2'):
    """
    피험자의 amplitudes_z 로드

    Args:
        subject_id: 피험자 ID (예: '01')
        roi: ROI 이름 (예: 'V1')
        timestamp: 분석 timestamp
        dataset: 데이터셋 이름

    Returns:
        amplitudes: (n_runs, n_colors, n_voxels) z-scored channel amplitudes
        result_dir: 결과 디렉토리 경로

    **Note**:
    - amplitudes_z: 각 run별로 z-scored된 channel response
    - n_runs = 8 (일반적으로)
    - n_colors = 8
    - n_voxels = 선택된 복셀 수 (개별 최적화)
    """
    base_path = Path(f'derivatives/BH2009_{dataset}/{timestamp}')
    pattern = str(base_path / f'sm*_sub-{subject_id}_{roi}_*')

    matches = glob.glob(pattern)
    if not matches:
        raise FileNotFoundError(
            f"No results for sub-{subject_id} {roi} in {base_path}"
        )

    result_dir = Path(matches[0])
    amp_file = result_dir / 'amplitudes_z.npy'

    if not amp_file.exists():
        raise FileNotFoundError(f"amplitudes_z.npy not found in {result_dir}")

    amplitudes = np.load(amp_file)  # (n_runs, n_colors, n_voxels)

    return amplitudes, result_dir

# ============================================================================
# RDM Computation
# ============================================================================

def compute_rdm(amplitudes):
    """
    Representational Dissimilarity Matrix (RDM) 계산

    **계산 과정**:
    1. Run 평균: (n_runs, 8, n_voxels) → (8, n_voxels)
    2. 각 색상 쌍에 대해:
       - Spearman correlation 계산 (across voxels)
       - Dissimilarity = 1 - correlation
    3. 8×8 RDM 생성

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) 배열

    Returns:
        rdm: (n_colors, n_colors) dissimilarity matrix

    **Note**:
    - 대각선 = 0 (자기 자신과의 거리)
    - 대칭 행렬 (RDM[i,j] = RDM[j,i])
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Run 평균: 각 색상의 평균 복셀 활성화 패턴
    amplitudes_avg = amplitudes.mean(axis=0)  # (n_colors, n_voxels)

    # RDM 초기화
    rdm = np.zeros((n_colors, n_colors))

    # 모든 색상 쌍에 대해 dissimilarity 계산
    for i in range(n_colors):
        for j in range(n_colors):
            if i == j:
                rdm[i, j] = 0.0  # 자기 자신과의 거리 = 0
            else:
                # Spearman correlation (복셀 간 순위 기반 상관)
                corr, _ = spearmanr(amplitudes_avg[i, :], amplitudes_avg[j, :])

                # Dissimilarity로 변환
                # corr = 1 → rdm = 0 (완전히 같음)
                # corr = 0 → rdm = 1 (독립적)
                # corr = -1 → rdm = 2 (완전히 반대)
                rdm[i, j] = 1 - corr

    return rdm

def compute_rdm_similarity(rdm1, rdm2):
    """
    두 RDM 간 유사도 계산 (Spearman correlation)

    **방법**:
    1. 각 RDM을 벡터화 (상삼각 부분만 추출)
       - 8×8 RDM → 28개 값 (대각선 제외, 대칭이므로 상삼각만)
    2. 두 벡터 간 Spearman correlation 계산

    Args:
        rdm1: (n_colors, n_colors) 첫 번째 RDM
        rdm2: (n_colors, n_colors) 두 번째 RDM

    Returns:
        similarity: Spearman correlation between RDMs
        p_value: 통계적 유의성

    **해석**:
    - similarity > 0.7: 높은 일관성 (안정적인 표상)
    - 0.5 < similarity < 0.7: 보통 일관성
    - similarity < 0.5: 낮은 일관성 (불안정한 표상)
    """
    n_colors = rdm1.shape[0]

    # 상삼각 부분 추출 (대각선 제외)
    # 예: 8×8 → 28개 값
    triu_indices = np.triu_indices(n_colors, k=1)
    rdm1_vec = rdm1[triu_indices]
    rdm2_vec = rdm2[triu_indices]

    # Spearman correlation
    similarity, p_value = spearmanr(rdm1_vec, rdm2_vec)

    return similarity, p_value

# ============================================================================
# Split-Half Reliability Analysis
# ============================================================================

def compute_split_half_reliability(amplitudes, split_method='first-second'):
    """
    Split-half reliability 계산

    **개념**:
    - 데이터를 두 그룹으로 나누고 각각 RDM 계산
    - 두 RDM 간 상관계수 = reliability
    - 높을수록 → 표상이 안정적

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        split_method: 'first-second' 또는 'odd-even'

    Returns:
        reliability: Split-half reliability (Spearman correlation)
        p_value: 통계적 유의성
        rdm_half1: 첫 번째 half의 RDM
        rdm_half2: 두 번째 half의 RDM

    **Split Methods**:
    1. first-second: run 1-4 vs run 5-8
       - 장점: 시간에 따른 drift 평가 가능
       - 단점: 순서 효과 포함될 수 있음

    2. odd-even: 홀수 run vs 짝수 run
       - 장점: 순서 효과 제거
       - 단점: 더 balanced
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Split 방법에 따라 run 인덱스 분할
    if split_method == 'first-second':
        # 첫 절반 vs 두 번째 절반
        half1_indices = list(range(n_runs // 2))
        half2_indices = list(range(n_runs // 2, n_runs))
    elif split_method == 'odd-even':
        # 홀수 run vs 짝수 run
        half1_indices = list(range(0, n_runs, 2))  # 0, 2, 4, 6
        half2_indices = list(range(1, n_runs, 2))  # 1, 3, 5, 7
    else:
        raise ValueError(f"Unknown split method: {split_method}")

    # 각 half에서 RDM 계산
    amplitudes_half1 = amplitudes[half1_indices, :, :]
    amplitudes_half2 = amplitudes[half2_indices, :, :]

    rdm_half1 = compute_rdm(amplitudes_half1)
    rdm_half2 = compute_rdm(amplitudes_half2)

    # 두 RDM 간 유사도 = reliability
    reliability, p_value = compute_rdm_similarity(rdm_half1, rdm_half2)

    return reliability, p_value, rdm_half1, rdm_half2

def spearman_brown_correction(reliability):
    """
    Spearman-Brown Correction 적용

    **개념**:
    - Split-half는 절반 데이터만 사용하므로 신뢰도를 과소평가
    - 전체 데이터 사용 시 예상 신뢰도 추정

    **공식**:
    r_full = (2 * r_half) / (1 + r_half)

    Args:
        reliability: Split-half reliability

    Returns:
        corrected_reliability: 보정된 reliability (전체 데이터 사용 시 예상)

    **예시**:
    - r_half = 0.6 → r_full = 0.75
    - r_half = 0.4 → r_full = 0.57
    """
    if reliability >= 1.0:
        # 이미 완벽한 신뢰도
        return 1.0
    elif reliability <= -1.0:
        # 완전히 반대 (매우 드묾)
        return -1.0
    else:
        corrected = (2 * reliability) / (1 + reliability)
        return corrected

# ============================================================================
# Main Analysis
# ============================================================================

def run_within_subject_reliability(args):
    """
    모든 피험자와 ROI에 대해 within-subject reliability 계산

    **절차**:
    1. 각 피험자, 각 ROI에 대해:
       a. amplitudes 로드
       b. Split-half reliability 계산
       c. Spearman-Brown correction 적용
    2. 결과 정리 및 요약
    3. 시각화 생성
    4. 해석 가이드 출력
    """
    print("=" * 80)
    print("Option 1: Within-Subject Reliability Analysis")
    print("=" * 80)
    print(f"Timestamp: {args.timestamp}")
    print(f"Dataset: {args.dataset}")
    print(f"Subjects: {args.subjects}")
    print(f"ROIs: {args.rois}")
    print(f"Split method: {args.split_method}")
    print()

    # 출력 디렉토리 설정
    if args.output_dir is None:
        output_dir = Path(f'analysis/group_level/option1_results/{args.timestamp}')
    else:
        output_dir = Path(args.output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()

    # 결과 저장용 리스트
    results = []

    # 각 피험자, 각 ROI에 대해 분석
    for subject_id in args.subjects:
        print(f"Processing sub-{subject_id}...")

        for roi in args.rois:
            try:
                # 데이터 로드
                amplitudes, result_dir = load_subject_amplitudes(
                    subject_id, roi, args.timestamp, args.dataset
                )
                n_runs, n_colors, n_voxels = amplitudes.shape
                print(f"  {roi}: {amplitudes.shape} (runs={n_runs}, colors={n_colors}, voxels={n_voxels})")

                # Split-half reliability 계산
                reliability, p_value, rdm_half1, rdm_half2 = compute_split_half_reliability(
                    amplitudes, split_method=args.split_method
                )

                # Spearman-Brown correction
                corrected_reliability = spearman_brown_correction(reliability)

                # 결과 저장
                results.append({
                    'subject': subject_id,
                    'roi': roi,
                    'reliability': reliability,
                    'p_value': p_value,
                    'corrected_reliability': corrected_reliability,
                    'n_runs': n_runs,
                    'n_voxels': n_voxels
                })

                print(f"    Reliability: {reliability:.3f} (p={p_value:.4f})")
                print(f"    Corrected: {corrected_reliability:.3f}")

                # RDM 저장 (나중에 시각화용)
                rdm_save_dir = output_dir / f'sub-{subject_id}' / roi
                rdm_save_dir.mkdir(parents=True, exist_ok=True)
                np.save(rdm_save_dir / 'rdm_half1.npy', rdm_half1)
                np.save(rdm_save_dir / 'rdm_half2.npy', rdm_half2)

            except FileNotFoundError as e:
                print(f"  {roi}: ⚠️ {e}")
                continue

        print()

    # 결과를 DataFrame으로 변환
    df_results = pd.DataFrame(results)

    # CSV 저장
    csv_path = output_dir / 'reliability_results.csv'
    df_results.to_csv(csv_path, index=False)
    print(f"✓ Results saved to {csv_path}")

    # 요약 통계 출력
    print_summary_statistics(df_results, output_dir)

    # 시각화 생성
    create_visualizations(df_results, output_dir, args)

    # 해석 가이드 출력
    print_interpretation_guide(df_results, output_dir)

    print()
    print("=" * 80)
    print("Analysis complete!")
    print(f"Results saved to: {output_dir}")
    print("=" * 80)

# ============================================================================
# Summary Statistics
# ============================================================================

def print_summary_statistics(df_results, output_dir):
    """요약 통계 출력 및 저장"""
    print()
    print("=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)
    print()

    # ROI별 요약
    print("By ROI:")
    print("-" * 80)
    summary_by_roi = df_results.groupby('roi').agg({
        'reliability': ['mean', 'std', 'min', 'max'],
        'corrected_reliability': ['mean', 'std', 'min', 'max']
    }).round(3)
    print(summary_by_roi)
    print()

    # 피험자별 요약
    print("By Subject:")
    print("-" * 80)
    summary_by_subject = df_results.groupby('subject').agg({
        'reliability': ['mean', 'std', 'min', 'max'],
        'corrected_reliability': ['mean', 'std', 'min', 'max']
    }).round(3)
    print(summary_by_subject)
    print()

    # 전체 요약
    print("Overall:")
    print("-" * 80)
    print(f"Mean reliability: {df_results['reliability'].mean():.3f} ± {df_results['reliability'].std():.3f}")
    print(f"Range: [{df_results['reliability'].min():.3f}, {df_results['reliability'].max():.3f}]")
    print(f"Corrected mean: {df_results['corrected_reliability'].mean():.3f} ± {df_results['corrected_reliability'].std():.3f}")
    print()

    # 통계적 유의성
    n_significant = (df_results['p_value'] < 0.05).sum()
    n_total = len(df_results)
    print(f"Significant pairs (p < 0.05): {n_significant}/{n_total} ({100*n_significant/n_total:.1f}%)")
    print()

    # 요약 통계 저장
    summary_path = output_dir / 'summary_statistics.txt'
    with open(summary_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("Within-Subject Reliability Analysis - Summary\n")
        f.write("=" * 80 + "\n\n")
        f.write("By ROI:\n")
        f.write("-" * 80 + "\n")
        f.write(summary_by_roi.to_string() + "\n\n")
        f.write("By Subject:\n")
        f.write("-" * 80 + "\n")
        f.write(summary_by_subject.to_string() + "\n\n")
        f.write("Overall:\n")
        f.write("-" * 80 + "\n")
        f.write(f"Mean reliability: {df_results['reliability'].mean():.3f} ± {df_results['reliability'].std():.3f}\n")
        f.write(f"Range: [{df_results['reliability'].min():.3f}, {df_results['reliability'].max():.3f}]\n")
        f.write(f"Corrected mean: {df_results['corrected_reliability'].mean():.3f} ± {df_results['corrected_reliability'].std():.3f}\n")
        f.write(f"\nSignificant pairs (p < 0.05): {n_significant}/{n_total} ({100*n_significant/n_total:.1f}%)\n")

    print(f"✓ Summary saved to {summary_path}")

# ============================================================================
# Visualizations
# ============================================================================

def create_visualizations(df_results, output_dir, args):
    """시각화 생성"""
    print()
    print("Creating visualizations...")

    # 1. Reliability by subject and ROI (heatmap)
    create_reliability_heatmap(df_results, output_dir)

    # 2. Reliability distribution by ROI (box plot)
    create_reliability_boxplot(df_results, output_dir)

    # 3. Scatter: raw vs. corrected reliability
    create_raw_vs_corrected_plot(df_results, output_dir)

    # 4. Example RDM comparison (first subject, first ROI)
    create_rdm_comparison_examples(df_results, output_dir, args)

    print("✓ Visualizations complete")

def create_reliability_heatmap(df_results, output_dir):
    """Reliability heatmap (subject × ROI)"""
    # Pivot table: subject × ROI
    pivot = df_results.pivot(index='subject', columns='roi', values='reliability')

    fig, ax = plt.subplots(figsize=(8, 6))

    # Manual heatmap using imshow
    im = ax.imshow(pivot.values, cmap='RdYlGn', vmin=-0.2, vmax=1.0, aspect='auto')

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Split-Half Reliability', fontsize=10)

    # Add annotations
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            text = ax.text(j, i, f'{pivot.values[i, j]:.3f}',
                          ha="center", va="center", color="black", fontsize=9)

    # Set ticks and labels
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticklabels(pivot.index)

    ax.set_title('Within-Subject Reliability (Split-Half)', fontsize=14, fontweight='bold')
    ax.set_xlabel('ROI', fontsize=12)
    ax.set_ylabel('Subject', fontsize=12)

    plt.tight_layout()
    save_path = output_dir / 'reliability_heatmap.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {save_path}")

def create_reliability_boxplot(df_results, output_dir):
    """Reliability distribution by ROI (box plot)"""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Prepare data for boxplot
    rois = df_results['roi'].unique()
    data_by_roi = [df_results[df_results['roi'] == roi]['reliability'].values for roi in rois]

    # Box plot
    bp = ax.boxplot(data_by_roi, labels=rois, patch_artist=True, widths=0.6)

    # Color the boxes
    colors = ['lightblue', 'lightgreen', 'lightyellow', 'lightcoral']
    for patch, color in zip(bp['boxes'], colors[:len(rois)]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)

    # Add individual points
    for i, roi in enumerate(rois):
        y = df_results[df_results['roi'] == roi]['reliability'].values
        x = np.random.normal(i+1, 0.04, size=len(y))  # Add jitter
        ax.scatter(x, y, color='black', s=40, alpha=0.6, zorder=3)

    # Reference lines
    ax.axhline(y=0.7, color='green', linestyle='--', linewidth=1, alpha=0.7, label='High reliability (r > 0.7)')
    ax.axhline(y=0.5, color='orange', linestyle='--', linewidth=1, alpha=0.7, label='Moderate reliability (r = 0.5)')

    ax.set_title('Within-Subject Reliability by ROI', fontsize=14, fontweight='bold')
    ax.set_xlabel('ROI', fontsize=12)
    ax.set_ylabel('Split-Half Reliability', fontsize=12)
    ax.set_ylim(-0.2, 1.0)
    ax.legend(loc='lower right', fontsize=9)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    save_path = output_dir / 'reliability_boxplot.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {save_path}")

def create_raw_vs_corrected_plot(df_results, output_dir):
    """Raw vs. Spearman-Brown corrected reliability"""
    fig, ax = plt.subplots(figsize=(8, 8))

    # Scatter plot
    for roi in df_results['roi'].unique():
        subset = df_results[df_results['roi'] == roi]
        ax.scatter(subset['reliability'], subset['corrected_reliability'],
                   label=roi, s=100, alpha=0.7)

    # Identity line
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, alpha=0.5, label='Identity')

    ax.set_xlabel('Raw Split-Half Reliability', fontsize=12)
    ax.set_ylabel('Spearman-Brown Corrected Reliability', fontsize=12)
    ax.set_title('Raw vs. Corrected Reliability', fontsize=14, fontweight='bold')
    ax.set_xlim(-0.2, 1.0)
    ax.set_ylim(-0.2, 1.0)
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    save_path = output_dir / 'raw_vs_corrected.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {save_path}")

def create_rdm_comparison_examples(df_results, output_dir, args):
    """Example RDM comparisons (first subject, all ROIs)"""
    # 첫 번째 피험자 선택
    first_subject = df_results['subject'].iloc[0]

    n_rois = len(args.rois)
    fig, axes = plt.subplots(n_rois, 3, figsize=(12, 4*n_rois))

    if n_rois == 1:
        axes = axes.reshape(1, -1)

    for i, roi in enumerate(args.rois):
        # RDM 로드
        rdm_dir = output_dir / f'sub-{first_subject}' / roi
        if not rdm_dir.exists():
            continue

        rdm_half1 = np.load(rdm_dir / 'rdm_half1.npy')
        rdm_half2 = np.load(rdm_dir / 'rdm_half2.npy')

        # Reliability 가져오기
        reliability = df_results[
            (df_results['subject'] == first_subject) &
            (df_results['roi'] == roi)
        ]['reliability'].values[0]

        # Plot RDM half 1
        im1 = axes[i, 0].imshow(rdm_half1, cmap='viridis', vmin=0, vmax=2)
        axes[i, 0].set_title(f'{roi} - First Half', fontsize=10)
        axes[i, 0].set_xlabel('Color')
        axes[i, 0].set_ylabel('Color')
        plt.colorbar(im1, ax=axes[i, 0], fraction=0.046)

        # Plot RDM half 2
        im2 = axes[i, 1].imshow(rdm_half2, cmap='viridis', vmin=0, vmax=2)
        axes[i, 1].set_title(f'{roi} - Second Half', fontsize=10)
        axes[i, 1].set_xlabel('Color')
        axes[i, 1].set_ylabel('Color')
        plt.colorbar(im2, ax=axes[i, 1], fraction=0.046)

        # Scatter plot: half1 vs. half2
        triu_indices = np.triu_indices(8, k=1)
        half1_vec = rdm_half1[triu_indices]
        half2_vec = rdm_half2[triu_indices]

        axes[i, 2].scatter(half1_vec, half2_vec, alpha=0.6, s=40)
        axes[i, 2].plot([0, 2], [0, 2], 'r--', linewidth=1, alpha=0.7)
        axes[i, 2].set_xlabel('First Half RDM', fontsize=9)
        axes[i, 2].set_ylabel('Second Half RDM', fontsize=9)
        axes[i, 2].set_title(f'{roi} - r = {reliability:.3f}', fontsize=10)
        axes[i, 2].set_xlim(0, 2)
        axes[i, 2].set_ylim(0, 2)
        axes[i, 2].grid(alpha=0.3)

    fig.suptitle(f'RDM Split-Half Comparison: sub-{first_subject}',
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    save_path = output_dir / f'rdm_comparison_sub-{first_subject}.png'
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  ✓ {save_path}")

# ============================================================================
# Interpretation Guide
# ============================================================================

def print_interpretation_guide(df_results, output_dir):
    """해석 가이드 출력 및 저장"""
    print()
    print("=" * 80)
    print("INTERPRETATION GUIDE")
    print("=" * 80)
    print()

    # ROI별 평균 reliability
    mean_by_roi = df_results.groupby('roi')['reliability'].mean()

    # 전체 평균
    overall_mean = df_results['reliability'].mean()

    # 해석
    interpretation = []
    interpretation.append("=" * 80)
    interpretation.append("결과 해석 및 다음 단계 권장사항")
    interpretation.append("=" * 80)
    interpretation.append("")

    # Overall assessment
    if overall_mean > 0.7:
        interpretation.append("✅ 전체 평가: 높은 피험자 내 신뢰도 (r > 0.7)")
        interpretation.append("")
        interpretation.append("의미:")
        interpretation.append("- 개별 피험자의 RDM이 매우 안정적입니다")
        interpretation.append("- 피험자 간 낮은 일관성은 실제 개인차를 반영합니다 (노이즈 아님)")
        interpretation.append("- 데이터 품질이 우수합니다")
        interpretation.append("")
        interpretation.append("다음 단계:")
        interpretation.append("✅ Option 2 (SRM) 진행 가능 - 공유 구조 찾기")
        interpretation.append("✅ Option 3 (Supersubject) 진행 가능 - 그룹 수준 모델")
        interpretation.append("✅ '개인차' 서사로 논문 작성 가능")

    elif overall_mean > 0.5:
        interpretation.append("⚠️ 전체 평가: 보통 피험자 내 신뢰도 (0.5 < r < 0.7)")
        interpretation.append("")
        interpretation.append("의미:")
        interpretation.append("- 개별 RDM이 부분적으로 안정적입니다")
        interpretation.append("- 일부 노이즈가 존재하지만 신호도 있습니다")
        interpretation.append("- 개선의 여지가 있습니다")
        interpretation.append("")
        interpretation.append("다음 단계:")
        interpretation.append("⚠️ 더 많은 스무딩 고려 (예: 8mm)")
        interpretation.append("⚠️ 더 많은 run 평균 사용")
        interpretation.append("⚠️ Option 2/3 진행 가능하지만 신중하게")

    else:
        interpretation.append("❌ 전체 평가: 낮은 피험자 내 신뢰도 (r < 0.5)")
        interpretation.append("")
        interpretation.append("의미:")
        interpretation.append("- 개별 RDM이 불안정합니다")
        interpretation.append("- 노이즈가 신호를 압도합니다")
        interpretation.append("- 데이터 품질 문제가 있습니다")
        interpretation.append("")
        interpretation.append("다음 단계:")
        interpretation.append("❌ 그룹 분석 전에 데이터 품질 개선 필요")
        interpretation.append("  - 전처리 재검토 (더 많은 스무딩, 다른 confound regression)")
        interpretation.append("  - SNR 확인")
        interpretation.append("  - 등록 품질 확인")
        interpretation.append("❌ Option 2/3 진행 시 의미 있는 결과 기대하기 어려움")

    interpretation.append("")
    interpretation.append("-" * 80)
    interpretation.append("ROI별 상세 평가:")
    interpretation.append("-" * 80)

    for roi in mean_by_roi.index:
        mean_rel = mean_by_roi[roi]
        if mean_rel > 0.7:
            status = "✅ 우수"
        elif mean_rel > 0.5:
            status = "⚠️ 보통"
        else:
            status = "❌ 낮음"

        interpretation.append(f"{roi}: {mean_rel:.3f} - {status}")

    interpretation.append("")
    interpretation.append("=" * 80)
    interpretation.append("참고 문헌:")
    interpretation.append("=" * 80)
    interpretation.append("- Nunnally, J. C., & Bernstein, I. H. (1994). Psychometric theory.")
    interpretation.append("  → 일반적으로 r > 0.7을 '수용 가능한 신뢰도'로 간주")
    interpretation.append("- Guntupalli, J. S., et al. (2016). A model of representational spaces.")
    interpretation.append("  → 높은 피험자 내 신뢰도가 피험자 간 정렬의 전제조건")
    interpretation.append("")

    # 출력
    for line in interpretation:
        print(line)

    # 저장
    guide_path = output_dir / 'interpretation_guide.txt'
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(interpretation))

    print(f"✓ Interpretation guide saved to {guide_path}")

# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    args = parse_args()
    run_within_subject_reliability(args)
