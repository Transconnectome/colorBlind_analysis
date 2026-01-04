#!/usr/bin/env python3
"""
Phase 2A: RDM (Representational Dissimilarity Matrix) 계산

패턴 행렬에서 RDM 계산 및 색-쌍 비교
"""

import numpy as np
from pathlib import Path
import json
import pandas as pd
from scipy import stats

# 경로 설정
BASE_DIR = Path("/scratch/connectome/haba6030/colorBlind")
PATTERN_DIR = BASE_DIR / "results/group_level/phase2a_data/patterns"
OUTPUT_DIR = BASE_DIR / "results/group_level/phase2a_data/rdm"

HC_SUBJECTS = ['03', '05', '06', '07']
CVD_SUBJECTS = ['08', '09', '10']
ROIS = ['V1', 'V2', 'V3', 'hV4']
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse',
               'Green', 'Cyan', 'Blue', 'Magenta']


def compute_rdm(pattern):
    """
    RDM 계산 (평균-중심화 Pearson correlation 기반)

    Parameters:
    -----------
    pattern : np.ndarray (8, n_voxels)
        fMRI 패턴 행렬

    Returns:
    --------
    rdm : np.ndarray (8, 8)
        Representational Dissimilarity Matrix
    """
    n_colors = pattern.shape[0]
    rdm = np.zeros((n_colors, n_colors))

    # 평균 중심화
    pattern_centered = pattern - pattern.mean(axis=1, keepdims=True)

    for i in range(n_colors):
        for j in range(n_colors):
            if i == j:
                rdm[i, j] = 0.0
            else:
                vi = pattern_centered[i]
                vj = pattern_centered[j]

                # Pearson correlation
                corr = np.corrcoef(vi, vj)[0, 1]

                # Dissimilarity = 1 - correlation
                rdm[i, j] = 1 - corr

    return rdm


def save_rdm(rdm, subject_id, roi):
    """RDM 저장 (.npy 및 .csv)"""
    # 디렉토리 생성
    if subject_id == 'HC_mean':
        output_dir = OUTPUT_DIR / "matrices" / "HC_mean"
    else:
        output_dir = OUTPUT_DIR / "matrices" / f"sub-{subject_id}"

    output_dir.mkdir(parents=True, exist_ok=True)

    # .npy 저장
    npy_file = output_dir / f"{roi}_rdm.npy"
    np.save(npy_file, rdm)

    # .csv 저장 (가독성)
    csv_file = output_dir / f"{roi}_rdm.csv"
    df = pd.DataFrame(rdm, index=COLOR_NAMES, columns=COLOR_NAMES)
    df.to_csv(csv_file)

    print(f"  Saved: {npy_file}")

    return rdm


def compute_rdm_zscores(cvd_rdm, hc_rdms, subject_id, roi):
    """
    CVD와 HC의 RDM 비교 (z-score)

    Parameters:
    -----------
    cvd_rdm : np.ndarray (8, 8)
    hc_rdms : list of np.ndarray
        각 HC 피험자의 RDM
    """
    results = []

    # Upper triangle만 (대칭 행렬)
    for i in range(8):
        for j in range(i+1, 8):
            cvd_val = cvd_rdm[i, j]

            # HC 분포
            hc_vals = [rdm[i, j] for rdm in hc_rdms]
            hc_mean = np.mean(hc_vals)
            hc_std = np.std(hc_vals, ddof=1)  # Sample std

            # Z-score
            if hc_std > 0:
                z = (cvd_val - hc_mean) / hc_std
            else:
                z = 0.0

            # P-value (two-tailed)
            p = stats.norm.sf(abs(z)) * 2

            # Significance
            if p < 0.001:
                sig = '***'
            elif p < 0.01:
                sig = '**'
            elif p < 0.05:
                sig = '*'
            else:
                sig = 'n.s.'

            results.append({
                'color_pair': f'{COLOR_NAMES[i]}-{COLOR_NAMES[j]}',
                'color_i': COLOR_NAMES[i],
                'color_j': COLOR_NAMES[j],
                'hc_mean': hc_mean,
                'hc_std': hc_std,
                'cvd_value': cvd_val,
                'z_score': z,
                'p_value': p,
                'significance': sig
            })

    # DataFrame 생성
    df = pd.DataFrame(results)

    # Z-score로 정렬 (절댓값 큰 순서)
    df['abs_z'] = df['z_score'].abs()
    df = df.sort_values('abs_z', ascending=False)
    df = df.drop('abs_z', axis=1)

    # 저장
    output_dir = OUTPUT_DIR / "comparisons"
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_file = output_dir / f"sub-{subject_id}_{roi}_rdm_zscore.csv"
    df.to_csv(csv_file, index=False, float_format='%.4f')

    print(f"  RDM comparison saved: {csv_file}")

    # 유의한 차이 출력
    sig_df = df[df['significance'].isin(['*', '**', '***'])]
    if len(sig_df) > 0:
        print(f"  Significant differences: {len(sig_df)}")
        for _, row in sig_df.head(5).iterrows():
            print(f"    {row['color_pair']}: z={row['z_score']:.2f} {row['significance']}")

    return df


def compute_rdm_correlation(rdm1, rdm2):
    """두 RDM 간 상관 (Spearman)"""
    # Upper triangle vectorize
    n = rdm1.shape[0]
    vec1 = []
    vec2 = []

    for i in range(n):
        for j in range(i+1, n):
            vec1.append(rdm1[i, j])
            vec2.append(rdm2[i, j])

    corr, pval = stats.spearmanr(vec1, vec2)

    return corr, pval


def main():
    """메인 실행"""
    print("=" * 70)
    print("Phase 2A: Computing RDMs")
    print("=" * 70)

    # 출력 디렉토리 생성
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results = []

    for roi in ROIS:
        print(f"\n{'='*70}")
        print(f"Processing ROI: {roi}")
        print(f"{'='*70}")

        # HC mean RDM
        hc_mean_file = PATTERN_DIR / "HC_mean" / f"{roi}_pattern.npy"
        if not hc_mean_file.exists():
            print(f"  Warning: HC mean pattern not found for {roi}")
            continue

        hc_mean_pattern = np.load(hc_mean_file)
        hc_mean_rdm = compute_rdm(hc_mean_pattern)
        save_rdm(hc_mean_rdm, 'HC_mean', roi)

        # Individual HC RDMs (for z-score)
        print(f"\nComputing individual HC RDMs for {roi}...")
        hc_rdms = []
        for subj in HC_SUBJECTS:
            pattern_file = PATTERN_DIR / f"sub-{subj}" / f"{roi}_pattern.npy"
            if pattern_file.exists():
                pattern = np.load(pattern_file)
                rdm = compute_rdm(pattern)
                hc_rdms.append(rdm)
                save_rdm(rdm, subj, roi)
            else:
                print(f"  Warning: Pattern not found for sub-{subj} {roi}")

        if len(hc_rdms) == 0:
            print(f"  Error: No HC RDMs for {roi}")
            continue

        # CVD RDMs
        print(f"\nComputing CVD RDMs for {roi}...")
        for subj in CVD_SUBJECTS:
            pattern_file = PATTERN_DIR / f"sub-{subj}" / f"{roi}_pattern.npy"
            if not pattern_file.exists():
                print(f"  Warning: Pattern not found for sub-{subj} {roi}")
                continue

            pattern = np.load(pattern_file)
            cvd_rdm = compute_rdm(pattern)
            save_rdm(cvd_rdm, subj, roi)

            # RDM correlation with HC mean
            corr, pval = compute_rdm_correlation(cvd_rdm, hc_mean_rdm)
            print(f"  sub-{subj} {roi} RDM correlation: r={corr:.3f}, p={pval:.4f}")

            # Z-score comparison
            print(f"\n  Computing z-scores for sub-{subj} {roi}...")
            zscore_df = compute_rdm_zscores(cvd_rdm, hc_rdms, subj, roi)

            # 결과 저장
            all_results.append({
                'subject': subj,
                'roi': roi,
                'rdm_correlation': corr,
                'rdm_pvalue': pval,
                'n_significant': len(zscore_df[zscore_df['significance'].isin(['*', '**', '***'])])
            })

    # 전체 요약 저장
    summary_df = pd.DataFrame(all_results)
    summary_file = OUTPUT_DIR / "rdm_summary.csv"
    summary_df.to_csv(summary_file, index=False, float_format='%.4f')

    print("\n" + "="*70)
    print("RDM computation complete!")
    print("="*70)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"Summary: {summary_file}")

    print("\nRDM Correlation Summary:")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
