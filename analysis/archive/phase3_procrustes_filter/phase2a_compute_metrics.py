#!/usr/bin/env python3
"""
Phase 2A: 추가 메트릭 계산

1. Procrustes disparity
2. Magnitude ratios
3. Baseline (mean activation)
"""

import numpy as np
from pathlib import Path
import json
import pandas as pd
from scipy.spatial import procrustes

# 경로 설정
BASE_DIR = Path("/scratch/connectome/haba6030/colorBlind")
PATTERN_DIR = BASE_DIR / "results/group_level/phase2a_data/patterns"
OUTPUT_DIR = BASE_DIR / "results/group_level/phase2a_data/metrics"

CVD_SUBJECTS = ['08', '09', '10']
ROIS = ['V1', 'V2', 'V3', 'hV4']
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']


def compute_procrustes_disparity(pattern1, pattern2):
    """
    Procrustes disparity 계산

    Parameters:
    -----------
    pattern1, pattern2 : np.ndarray (8, n_voxels)

    Returns:
    --------
    disparity : float
    rotation_matrix : np.ndarray (8, 8)
    """
    # Procrustes 분석 (translation + rotation, no scaling)
    mtx1, mtx2, disparity = procrustes(pattern1, pattern2)

    # Rotation matrix 추출 (approximate)
    # mtx1 = pattern1 after transformation
    # mtx2 = pattern2 after transformation
    # R ≈ mtx1.T @ mtx2 / ||mtx1||

    return disparity


def compute_magnitude_ratios(cvd_pattern, hc_pattern):
    """
    색별 L2 norm 비율 계산

    Returns:
    --------
    DataFrame with magnitude ratios
    """
    # L2 norm per color
    hc_norms = np.linalg.norm(hc_pattern, axis=1)  # (8,)
    cvd_norms = np.linalg.norm(cvd_pattern, axis=1)  # (8,)

    ratios = cvd_norms / (hc_norms + 1e-10)
    percents = ratios * 100

    df = pd.DataFrame({
        'color': COLOR_NAMES,
        'hc_norm': hc_norms,
        'cvd_norm': cvd_norms,
        'ratio': ratios,
        'percent': percents,
        'difference': cvd_norms - hc_norms
    })

    return df


def compute_baseline_shifts(cvd_pattern, hc_pattern):
    """
    색별 평균 활성 (baseline) 차이 계산

    Returns:
    --------
    DataFrame with baseline shifts
    """
    # Mean per color
    hc_means = hc_pattern.mean(axis=1)  # (8,)
    cvd_means = cvd_pattern.mean(axis=1)  # (8,)

    shifts = cvd_means - hc_means

    df = pd.DataFrame({
        'color': COLOR_NAMES,
        'hc_mean': hc_means,
        'cvd_mean': cvd_means,
        'shift': shifts
    })

    return df


def main():
    """메인 실행"""
    print("=" * 70)
    print("Phase 2A: Computing Additional Metrics")
    print("=" * 70)

    # 출력 디렉토리 생성
    (OUTPUT_DIR / "procrustes").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "magnitude").mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "baseline").mkdir(parents=True, exist_ok=True)

    all_procrustes = []
    all_magnitude = []
    all_baseline = []

    for roi in ROIS:
        print(f"\n{'='*70}")
        print(f"Processing ROI: {roi}")
        print(f"{'='*70}")

        # HC mean pattern 로드
        hc_mean_file = PATTERN_DIR / "HC_mean" / f"{roi}_pattern.npy"
        if not hc_mean_file.exists():
            print(f"  Warning: HC mean pattern not found for {roi}")
            continue

        hc_pattern = np.load(hc_mean_file)
        print(f"  HC pattern shape: {hc_pattern.shape}")

        # CVD 피험자 처리
        for subj in CVD_SUBJECTS:
            pattern_file = PATTERN_DIR / f"sub-{subj}" / f"{roi}_pattern.npy"
            if not pattern_file.exists():
                print(f"  Warning: Pattern not found for sub-{subj} {roi}")
                continue

            cvd_pattern = np.load(pattern_file)
            print(f"\n  Processing sub-{subj} {roi}...")
            print(f"    CVD pattern shape: {cvd_pattern.shape}")

            # Align voxel counts (use minimum)
            n_voxels_hc = hc_pattern.shape[1]
            n_voxels_cvd = cvd_pattern.shape[1]
            min_voxels = min(n_voxels_hc, n_voxels_cvd)

            if n_voxels_hc != n_voxels_cvd:
                print(f"    Aligning voxel counts: HC={n_voxels_hc}, CVD={n_voxels_cvd} → using {min_voxels}")
                hc_aligned = hc_pattern[:, :min_voxels]
                cvd_aligned = cvd_pattern[:, :min_voxels]
            else:
                hc_aligned = hc_pattern
                cvd_aligned = cvd_pattern

            # 1. Procrustes disparity
            disparity = compute_procrustes_disparity(cvd_aligned, hc_aligned)
            print(f"    Procrustes disparity: {disparity:.4f}")

            procrustes_result = {
                'subject': subj,
                'roi': roi,
                'disparity': disparity
            }
            all_procrustes.append(procrustes_result)

            # JSON 저장
            json_file = OUTPUT_DIR / "procrustes" / f"sub-{subj}_{roi}_disparity.json"
            with open(json_file, 'w') as f:
                json.dump(procrustes_result, f, indent=2)

            # 2. Magnitude ratios
            mag_df = compute_magnitude_ratios(cvd_aligned, hc_aligned)
            print(f"    Magnitude ratios:")
            print(f"      Mean: {mag_df['percent'].mean():.1f}%")
            print(f"      Range: {mag_df['percent'].min():.1f}% - {mag_df['percent'].max():.1f}%")

            # Top/bottom 3
            top3 = mag_df.nlargest(3, 'percent')
            bottom3 = mag_df.nsmallest(3, 'percent')
            print(f"      Highest: {top3.iloc[0]['color']} {top3.iloc[0]['percent']:.1f}%")
            print(f"      Lowest: {bottom3.iloc[0]['color']} {bottom3.iloc[0]['percent']:.1f}%")

            # CSV 저장
            csv_file = OUTPUT_DIR / "magnitude" / f"sub-{subj}_{roi}_magnitude.csv"
            mag_df.to_csv(csv_file, index=False, float_format='%.4f')

            # 전체 결과에 추가
            for _, row in mag_df.iterrows():
                all_magnitude.append({
                    'subject': subj,
                    'roi': roi,
                    'color': row['color'],
                    'hc_norm': row['hc_norm'],
                    'cvd_norm': row['cvd_norm'],
                    'ratio': row['ratio'],
                    'percent': row['percent']
                })

            # 3. Baseline shifts
            base_df = compute_baseline_shifts(cvd_aligned, hc_aligned)
            print(f"    Baseline shifts:")
            print(f"      Mean shift: {base_df['shift'].mean():.4f}")
            print(f"      Max shift: {base_df['shift'].max():.4f} ({base_df.loc[base_df['shift'].idxmax(), 'color']})")
            print(f"      Min shift: {base_df['shift'].min():.4f} ({base_df.loc[base_df['shift'].idxmin(), 'color']})")

            # CSV 저장
            csv_file = OUTPUT_DIR / "baseline" / f"sub-{subj}_{roi}_baseline.csv"
            base_df.to_csv(csv_file, index=False, float_format='%.4f')

            # 전체 결과에 추가
            for _, row in base_df.iterrows():
                all_baseline.append({
                    'subject': subj,
                    'roi': roi,
                    'color': row['color'],
                    'hc_mean': row['hc_mean'],
                    'cvd_mean': row['cvd_mean'],
                    'shift': row['shift']
                })

    # 전체 요약 저장
    print("\n" + "="*70)
    print("Saving summary files...")
    print("="*70)

    # Procrustes summary
    procrustes_df = pd.DataFrame(all_procrustes)
    procrustes_file = OUTPUT_DIR / "procrustes_summary.csv"
    procrustes_df.to_csv(procrustes_file, index=False, float_format='%.4f')
    print(f"  Procrustes summary: {procrustes_file}")

    # Magnitude summary
    magnitude_df = pd.DataFrame(all_magnitude)
    magnitude_file = OUTPUT_DIR / "magnitude_summary.csv"
    magnitude_df.to_csv(magnitude_file, index=False, float_format='%.4f')
    print(f"  Magnitude summary: {magnitude_file}")

    # Baseline summary
    baseline_df = pd.DataFrame(all_baseline)
    baseline_file = OUTPUT_DIR / "baseline_summary.csv"
    baseline_df.to_csv(baseline_file, index=False, float_format='%.4f')
    print(f"  Baseline summary: {baseline_file}")

    print("\n" + "="*70)
    print("Metric computation complete!")
    print("="*70)
    print(f"\nOutput directory: {OUTPUT_DIR}")

    # 요약 통계
    print("\n" + "="*70)
    print("Summary Statistics")
    print("="*70)

    print("\nProcrustes Disparity by Subject:")
    for subj in CVD_SUBJECTS:
        subj_data = procrustes_df[procrustes_df['subject'] == subj]
        mean_disp = subj_data['disparity'].mean()
        print(f"  sub-{subj}: {mean_disp:.4f} (mean across {len(subj_data)} ROIs)")

    print("\nMagnitude Ratio by Subject:")
    for subj in CVD_SUBJECTS:
        subj_data = magnitude_df[magnitude_df['subject'] == subj]
        mean_ratio = subj_data['percent'].mean()
        print(f"  sub-{subj}: {mean_ratio:.1f}% (mean across all colors/ROIs)")


if __name__ == "__main__":
    main()
