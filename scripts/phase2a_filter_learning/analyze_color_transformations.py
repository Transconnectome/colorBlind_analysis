#!/usr/bin/env python3
"""
8개 Circular 색상의 필터링 변화 분석

방법 1: Brain Pattern Space에서 변화량 분석
- L2 norm 변화
- 방향(각도) 변화
- HC와의 유사도 변화
"""

import numpy as np
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 경로 설정
BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
PATTERN_DIR = BASE_DIR / "results/group_level/phase2a_data/patterns"
MODEL_DIR = BASE_DIR / "results/filters/models/optionD/20251219_122240"
OUTPUT_DIR = BASE_DIR / "results/filters/analysis/color_transformations"

# 색상 정의 (8개 circular colors)
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']

# CVD 피험자
CVD_SUBJECTS = ['08', '09', '10']
ROIS = ['V1', 'V2']


def apply_filter(cvd_pattern, A, b):
    """필터 적용: F = Y @ A + b"""
    return cvd_pattern @ A + b[np.newaxis, :]


def analyze_single_color(before, after, hc_target, color_name):
    """단일 색상의 변화 분석"""

    # 1. L2 norm 변화
    norm_before = np.linalg.norm(before)
    norm_after = np.linalg.norm(after)
    norm_hc = np.linalg.norm(hc_target)

    norm_change = norm_after - norm_before
    norm_change_pct = (norm_change / norm_before) * 100

    # 2. 방향(각도) 변화
    if norm_before > 1e-10 and norm_after > 1e-10:
        cos_sim = np.dot(before, after) / (norm_before * norm_after)
        cos_sim = np.clip(cos_sim, -1.0, 1.0)
        angle_change = np.arccos(cos_sim) * 180 / np.pi
    else:
        angle_change = np.nan

    # 3. HC와의 거리 변화
    dist_before_hc = np.linalg.norm(before - hc_target)
    dist_after_hc = np.linalg.norm(after - hc_target)
    dist_reduction = dist_before_hc - dist_after_hc
    dist_reduction_pct = (dist_reduction / dist_before_hc) * 100

    # 4. HC와의 각도
    if norm_before > 1e-10 and norm_hc > 1e-10:
        cos_sim_hc_before = np.dot(before, hc_target) / (norm_before * norm_hc)
        cos_sim_hc_before = np.clip(cos_sim_hc_before, -1.0, 1.0)
        angle_hc_before = np.arccos(cos_sim_hc_before) * 180 / np.pi
    else:
        angle_hc_before = np.nan

    if norm_after > 1e-10 and norm_hc > 1e-10:
        cos_sim_hc_after = np.dot(after, hc_target) / (norm_after * norm_hc)
        cos_sim_hc_after = np.clip(cos_sim_hc_after, -1.0, 1.0)
        angle_hc_after = np.arccos(cos_sim_hc_after) * 180 / np.pi
    else:
        angle_hc_after = np.nan

    return {
        'color': color_name,
        'norm_before': norm_before,
        'norm_after': norm_after,
        'norm_hc': norm_hc,
        'norm_change': norm_change,
        'norm_change_pct': norm_change_pct,
        'angle_change': angle_change,
        'dist_before_hc': dist_before_hc,
        'dist_after_hc': dist_after_hc,
        'dist_reduction': dist_reduction,
        'dist_reduction_pct': dist_reduction_pct,
        'angle_hc_before': angle_hc_before,
        'angle_hc_after': angle_hc_after,
        'angle_hc_improvement': angle_hc_before - angle_hc_after
    }


def analyze_subject_roi(subject_id, roi):
    """피험자-ROI별 8개 색상 변화 분석"""

    print(f"\n{'='*70}")
    print(f"Analyzing: sub-{subject_id} {roi}")
    print(f"{'='*70}")

    # 1. 데이터 로드
    hc_pattern = np.load(PATTERN_DIR / "HC_mean" / f"{roi}_pattern.npy")
    cvd_pattern = np.load(PATTERN_DIR / f"sub-{subject_id}" / f"{roi}_pattern.npy")

    # 2. 필터 로드
    model_dir = MODEL_DIR / f"sub-{subject_id}" / roi
    A = np.load(model_dir / "A_matrix.npy")
    b = np.load(model_dir / "b_vector.npy")

    # 3. Voxel alignment
    n_voxels = min(hc_pattern.shape[1], cvd_pattern.shape[1])
    hc_pattern = hc_pattern[:, :n_voxels]
    cvd_pattern = cvd_pattern[:, :n_voxels]

    # 4. 필터 적용
    filtered_pattern = apply_filter(cvd_pattern, A, b)

    print(f"\nPattern shapes:")
    print(f"  CVD before: {cvd_pattern.shape}")
    print(f"  CVD after:  {filtered_pattern.shape}")
    print(f"  HC target:  {hc_pattern.shape}")

    # 5. 색상별 분석
    results = []
    for i, color_name in enumerate(COLOR_NAMES):
        analysis = analyze_single_color(
            before=cvd_pattern[i],
            after=filtered_pattern[i],
            hc_target=hc_pattern[i],
            color_name=color_name
        )
        results.append(analysis)

    df = pd.DataFrame(results)

    # 6. 요약 출력
    print(f"\n{'Color':<12} {'Norm Before':>12} {'Norm After':>12} {'Change %':>10} {'Angle°':>8} {'Dist Reduc%':>12}")
    print("-" * 80)
    for _, row in df.iterrows():
        print(f"{row['color']:<12} {row['norm_before']:>12.2f} {row['norm_after']:>12.2f} "
              f"{row['norm_change_pct']:>10.1f}% {row['angle_change']:>8.1f}° {row['dist_reduction_pct']:>12.1f}%")

    print(f"\n{'='*70}")
    print(f"Summary Statistics:")
    print(f"  Mean norm change: {df['norm_change_pct'].mean():+.1f}%")
    print(f"  Mean angle change: {df['angle_change'].mean():.1f}°")
    print(f"  Mean distance reduction: {df['dist_reduction_pct'].mean():.1f}%")
    print(f"  Mean angle to HC improvement: {df['angle_hc_improvement'].mean():.1f}°")

    return df


def visualize_transformations(df, subject_id, roi, output_dir):
    """변화 시각화"""

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Norm 변화
    ax = axes[0, 0]
    x = np.arange(len(COLOR_NAMES))
    ax.plot(x, df['norm_before'], 'o-', label='Before', linewidth=2, markersize=8)
    ax.plot(x, df['norm_after'], 's-', label='After', linewidth=2, markersize=8)
    ax.plot(x, df['norm_hc'], '^--', label='HC Target', linewidth=2, markersize=8, alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_ylabel('L2 Norm')
    ax.set_title(f'Activation Strength (L2 Norm)\nsub-{subject_id} {roi}')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Distance to HC
    ax = axes[0, 1]
    ax.bar(x, df['dist_before_hc'], alpha=0.5, label='Before', width=0.4, align='edge')
    ax.bar(x + 0.4, df['dist_after_hc'], alpha=0.5, label='After', width=0.4, align='edge')
    ax.set_xticks(x + 0.2)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_ylabel('Euclidean Distance')
    ax.set_title('Distance to HC Target')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # 3. Angle to HC
    ax = axes[1, 0]
    ax.plot(x, df['angle_hc_before'], 'o-', label='Before', linewidth=2, markersize=8)
    ax.plot(x, df['angle_hc_after'], 's-', label='After', linewidth=2, markersize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_ylabel('Angle (degrees)')
    ax.set_title('Angular Distance to HC')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 4. Reduction percentages
    ax = axes[1, 1]
    ax.bar(x, df['dist_reduction_pct'], alpha=0.7, color='green')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_ylabel('Reduction (%)')
    ax.set_title('Distance Reduction to HC')
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    # 저장
    output_file = output_dir / f"sub-{subject_id}_{roi}_color_transformations.png"
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\nVisualization saved: {output_file}")
    plt.close()


def main():
    """메인 실행"""

    print("=" * 70)
    print("8-Color Transformation Analysis")
    print("Method 1: Brain Pattern Space Analysis")
    print("=" * 70)

    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 모든 피험자-ROI 조합 분석
    all_results = []

    for subject in CVD_SUBJECTS:
        for roi in ROIS:
            # 분석
            df = analyze_subject_roi(subject, roi)
            df['subject'] = subject
            df['roi'] = roi
            all_results.append(df)

            # 시각화
            subject_output_dir = OUTPUT_DIR / f"sub-{subject}"
            subject_output_dir.mkdir(exist_ok=True)
            visualize_transformations(df, subject, roi, subject_output_dir)

            # CSV 저장
            csv_file = subject_output_dir / f"sub-{subject}_{roi}_color_analysis.csv"
            df.to_csv(csv_file, index=False)
            print(f"CSV saved: {csv_file}")

    # 전체 결과 통합
    all_df = pd.concat(all_results, ignore_index=True)
    all_csv = OUTPUT_DIR / "all_color_transformations.csv"
    all_df.to_csv(all_csv, index=False)

    # 전체 요약
    print("\n" + "=" * 70)
    print("Overall Summary (all subjects, all ROIs)")
    print("=" * 70)
    print(f"\nMean distance reduction: {all_df['dist_reduction_pct'].mean():.1f}%")
    print(f"Mean angle improvement to HC: {all_df['angle_hc_improvement'].mean():.1f}°")

    # 색상별 평균
    print("\nPer-color average distance reduction:")
    color_summary = all_df.groupby('color')['dist_reduction_pct'].mean().sort_values(ascending=False)
    for color, reduction in color_summary.items():
        print(f"  {color:<12}: {reduction:>6.1f}%")

    print(f"\nAll results saved to: {OUTPUT_DIR}")
    print("=" * 70)


if __name__ == "__main__":
    main()
