#!/usr/bin/env python3
"""
Phase 2A: 결과 분석 및 비교

3가지 옵션(A, B, D)의 학습 결과를 비교 분석
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# 경로 설정
BASE_DIR = Path("/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis")
RESULTS_DIR = BASE_DIR / "results/group_level/phase2a_data"
OUTPUT_DIR = BASE_DIR / "results/group_level/phase2a_analysis"

SUBJECTS = ['08', '09', '10']
ROIS = ['V1', 'V2']
OPTIONS = ['D', 'A', 'B']
OPTION_NAMES = {
    'D': 'RDM-Based',
    'A': 'Angular',
    'B': 'Variance'
}

def load_metadata(option, subject, roi):
    """메타데이터 로드"""
    if option == 'D':
        model_dir = RESULTS_DIR / "models"
    else:
        model_dir = RESULTS_DIR / f"models_option{option}"

    metadata_file = model_dir / f"sub-{subject}" / roi / "metadata.json"

    if not metadata_file.exists():
        return None

    with open(metadata_file, 'r') as f:
        return json.load(f)

def load_A_matrix(option, subject, roi):
    """A 행렬 로드"""
    if option == 'D':
        model_dir = RESULTS_DIR / "models"
    else:
        model_dir = RESULTS_DIR / f"models_option{option}"

    A_file = model_dir / f"sub-{subject}" / roi / "A_matrix.npy"

    if not A_file.exists():
        return None

    return np.load(A_file)

def load_b_vector(option, subject, roi):
    """b 벡터 로드"""
    if option == 'D':
        model_dir = RESULTS_DIR / "models"
    else:
        model_dir = RESULTS_DIR / f"models_option{option}"

    b_file = model_dir / f"sub-{subject}" / roi / "b_vector.npy"

    if not b_file.exists():
        return None

    return np.load(b_file)

def compare_options():
    """3가지 옵션 비교"""
    print("=" * 80)
    print("Phase 2A: 옵션별 결과 비교")
    print("=" * 80)

    results = []

    for subject in SUBJECTS:
        for roi in ROIS:
            print(f"\n{'='*80}")
            print(f"Sub-{subject} {roi}")
            print(f"{'='*80}")

            for option in OPTIONS:
                metadata = load_metadata(option, subject, roi)

                if metadata is None:
                    print(f"  Option {option}: NOT FOUND")
                    continue

                final_loss = metadata['final_loss']
                n_iter = metadata['n_iterations']

                # A 행렬 통계
                A = load_A_matrix(option, subject, roi)
                b = load_b_vector(option, subject, roi)

                diag_A = np.diag(A)
                A_mean = diag_A.mean()
                A_std = diag_A.std()

                b_mean = b.mean()
                b_std = b.std()

                print(f"\n  Option {option} ({OPTION_NAMES[option]}):")
                print(f"    Total Loss:     {final_loss['total']:.6f}")
                print(f"    - Magnitude:    {final_loss['magnitude']:.6f}")
                print(f"    - Baseline:     {final_loss['baseline']:.6f}")
                print(f"    - Structure:    {final_loss['structure']:.6f}")
                print(f"    Iterations:     {n_iter}")
                print(f"    A diagonal:     mean={A_mean:.3f}, std={A_std:.3f}")
                print(f"    b vector:       mean={b_mean:.4f}, std={b_std:.4f}")

                results.append({
                    'subject': subject,
                    'roi': roi,
                    'option': option,
                    'option_name': OPTION_NAMES[option],
                    'total_loss': final_loss['total'],
                    'magnitude_loss': final_loss['magnitude'],
                    'baseline_loss': final_loss['baseline'],
                    'structure_loss': final_loss['structure'],
                    'n_iterations': n_iter,
                    'A_mean': A_mean,
                    'A_std': A_std,
                    'b_mean': b_mean,
                    'b_std': b_std
                })

    return pd.DataFrame(results)

def analyze_best_options(df):
    """피험자별 최적 옵션 분석"""
    print("\n" + "=" * 80)
    print("피험자별 최적 옵션")
    print("=" * 80)

    for subject in SUBJECTS:
        print(f"\nSub-{subject}:")
        subject_df = df[df['subject'] == subject]

        for roi in ROIS:
            roi_df = subject_df[subject_df['roi'] == roi]

            if len(roi_df) == 0:
                continue

            best_idx = roi_df['total_loss'].idxmin()
            best = roi_df.loc[best_idx]

            print(f"  {roi}: Option {best['option']} ({best['option_name']})")
            print(f"    Total Loss: {best['total_loss']:.6f}")
            print(f"    Structure:  {best['structure_loss']:.6f}")

            # 다른 옵션과 비교
            for _, row in roi_df.iterrows():
                if row['option'] != best['option']:
                    diff = row['total_loss'] - best['total_loss']
                    pct = (diff / best['total_loss']) * 100
                    print(f"    vs Option {row['option']}: +{diff:.6f} ({pct:+.1f}%)")

def plot_comparison(df):
    """시각화"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Total Loss 비교
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for idx, roi in enumerate(ROIS):
        roi_df = df[df['roi'] == roi]

        pivot = roi_df.pivot(index='subject', columns='option_name', values='total_loss')
        pivot.plot(kind='bar', ax=axes[idx], width=0.8)

        axes[idx].set_xlabel('Subject', fontsize=12)
        axes[idx].set_ylabel('Total Loss', fontsize=12)
        axes[idx].set_title(f'{roi}: Total Loss by Option', fontsize=14, fontweight='bold')
        axes[idx].legend(title='Option', fontsize=10)
        axes[idx].grid(True, alpha=0.3, axis='y')
        axes[idx].set_xticklabels(axes[idx].get_xticklabels(), rotation=0)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "option_comparison_total_loss.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\nSaved: {OUTPUT_DIR / 'option_comparison_total_loss.png'}")

    # 2. Loss Components 비교
    fig, axes = plt.subplots(3, 1, figsize=(12, 12))

    loss_types = ['magnitude_loss', 'baseline_loss', 'structure_loss']
    loss_names = ['Magnitude', 'Baseline', 'Structure']
    colors = ['red', 'green', 'blue']

    for idx, (loss_type, loss_name, color) in enumerate(zip(loss_types, loss_names, colors)):
        df_plot = df.copy()
        df_plot['subject_roi'] = 'Sub-' + df_plot['subject'] + ' ' + df_plot['roi']

        pivot = df_plot.pivot(index='subject_roi', columns='option_name', values=loss_type)
        pivot.plot(kind='bar', ax=axes[idx], width=0.8, color=[color]*3, alpha=0.7)

        axes[idx].set_xlabel('Subject - ROI', fontsize=11)
        axes[idx].set_ylabel(f'{loss_name} Loss', fontsize=11)
        axes[idx].set_title(f'{loss_name} Loss Comparison', fontsize=13, fontweight='bold')
        axes[idx].legend(title='Option', fontsize=9)
        axes[idx].grid(True, alpha=0.3, axis='y')
        axes[idx].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "option_comparison_components.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {OUTPUT_DIR / 'option_comparison_components.png'}")

    # 3. A 행렬 통계 비교
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    df_plot = df.copy()
    df_plot['subject_roi'] = 'Sub-' + df_plot['subject'] + ' ' + df_plot['roi']

    # A mean
    pivot_mean = df_plot.pivot(index='subject_roi', columns='option_name', values='A_mean')
    pivot_mean.plot(kind='bar', ax=axes[0], width=0.8)
    axes[0].axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='Identity (1.0)')
    axes[0].set_xlabel('Subject - ROI', fontsize=11)
    axes[0].set_ylabel('Mean(diag(A))', fontsize=11)
    axes[0].set_title('A Matrix Diagonal Mean', fontsize=13, fontweight='bold')
    axes[0].legend(fontsize=9)
    axes[0].grid(True, alpha=0.3, axis='y')
    axes[0].tick_params(axis='x', rotation=45)

    # A std
    pivot_std = df_plot.pivot(index='subject_roi', columns='option_name', values='A_std')
    pivot_std.plot(kind='bar', ax=axes[1], width=0.8)
    axes[1].set_xlabel('Subject - ROI', fontsize=11)
    axes[1].set_ylabel('Std(diag(A))', fontsize=11)
    axes[1].set_title('A Matrix Diagonal Std (Lower is better)', fontsize=13, fontweight='bold')
    axes[1].legend(fontsize=9)
    axes[1].grid(True, alpha=0.3, axis='y')
    axes[1].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "option_comparison_A_matrix.png", dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved: {OUTPUT_DIR / 'option_comparison_A_matrix.png'}")

def main():
    """메인 실행"""
    # 결과 비교
    df = compare_options()

    # CSV 저장
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_file = OUTPUT_DIR / "option_comparison.csv"
    df.to_csv(csv_file, index=False, float_format='%.6f')
    print(f"\n\nSaved summary: {csv_file}")

    # 최적 옵션 분석
    analyze_best_options(df)

    # 시각화
    print("\n" + "=" * 80)
    print("시각화 생성 중...")
    print("=" * 80)
    plot_comparison(df)

    print("\n" + "=" * 80)
    print("분석 완료!")
    print("=" * 80)
    print(f"\n결과 디렉토리: {OUTPUT_DIR}")
    print(f"  - option_comparison.csv")
    print(f"  - option_comparison_total_loss.png")
    print(f"  - option_comparison_components.png")
    print(f"  - option_comparison_A_matrix.png")

if __name__ == "__main__":
    main()
