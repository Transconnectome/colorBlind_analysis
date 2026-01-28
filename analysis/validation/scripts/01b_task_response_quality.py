#!/usr/bin/env python3
"""
1B. Task-Evoked Response Quality
=================================
색깔 자극에 대한 실제 신호 반응 품질 검증

이 스크립트는 tSNR이 높더라도 실제로 색깔 자극에 반응하는지 확인합니다.

Input:
- Baseline decoding results: {BASELINE_RESULTS}/sub-{ID}/{ROI}/
  - r2_voxel.npy: 각 복셀의 색깔 자극 설명력 (R²)
  - classification_results.csv: 색깔 분류 정확도
  - reconstruction_results.csv: 색깔 재구성 오차
  - amplitudes_z.npy: 색깔별 BOLD 신호 크기 (z-scored)

Output:
- {VALIDATION_OUT}/task_response/{TIMESTAMP}/
  - task_response_quality.json: 전체 품질 지표
  - r2_distribution.png: R² 분포 시각화
  - classification_performance.png: 분류 성능 시각화
  - color_discriminability.png: 색깔 간 구분력 시각화
  - tsnr_vs_r2_correlation.png: tSNR-R² 상관관계

핵심 질문:
1. 색깔 자극을 설명하는 복셀이 충분한가? (R² analysis)
2. 색깔을 실제로 구분할 수 있는가? (Classification accuracy)
3. 색깔별 신호 차이가 충분한가? (Effect size)
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
from scipy.stats import pearsonr

plt.rcParams['figure.dpi'] = 150
plt.style.use('default')


def load_baseline_results(baseline_dir, subject, roi):
    """
    Load baseline decoding results for a subject-ROI

    Returns:
        dict with keys: r2_voxel, amplitudes_z, classification_df, reconstruction_df
    """
    subj_roi_dir = baseline_dir / subject / roi

    results = {}

    # R² scores (voxel selection quality)
    r2_path = subj_roi_dir / 'r2_voxel.npy'
    if r2_path.exists():
        results['r2_voxel'] = np.load(r2_path)
    else:
        results['r2_voxel'] = None

    # Amplitudes (color-specific responses)
    amp_path = subj_roi_dir / 'amplitudes_z.npy'
    if amp_path.exists():
        results['amplitudes_z'] = np.load(amp_path)
    else:
        results['amplitudes_z'] = None

    # Classification results
    clf_path = subj_roi_dir / 'classification_results.csv'
    if clf_path.exists():
        results['classification_df'] = pd.read_csv(clf_path)
    else:
        results['classification_df'] = None

    # Reconstruction results
    recon_path = subj_roi_dir / 'reconstruction_results.csv'
    if recon_path.exists():
        results['reconstruction_df'] = pd.read_csv(recon_path)
    else:
        results['reconstruction_df'] = None

    return results


def analyze_r2_distribution(r2_voxel, threshold=0.1):
    """
    Analyze R² distribution (voxel selection quality)

    R²의 의미:
    - R² = 색깔 자극이 해당 복셀의 신호를 설명하는 비율
    - R² = 0.1 → 색깔 자극이 신호 변동의 10%를 설명
    - R² > threshold인 복셀만 분석에 사용

    Args:
        r2_voxel: (n_voxels,) R² scores
        threshold: R² cutoff (default: 0.1, same as Baseline32)

    Returns:
        dict with metrics
    """
    if r2_voxel is None:
        return None

    # 전체 복셀 통계
    total_voxels = len(r2_voxel)
    selected_voxels = np.sum(r2_voxel > threshold)
    selection_rate = selected_voxels / total_voxels * 100

    # R² 분포 통계
    all_r2_stats = {
        'mean': float(np.mean(r2_voxel)),
        'median': float(np.median(r2_voxel)),
        'std': float(np.std(r2_voxel)),
        'max': float(np.max(r2_voxel)),
        'min': float(np.min(r2_voxel))
    }

    # Selected voxels only (R² > threshold)
    selected_r2 = r2_voxel[r2_voxel > threshold]
    if len(selected_r2) > 0:
        selected_r2_stats = {
            'mean': float(np.mean(selected_r2)),
            'median': float(np.median(selected_r2)),
            'std': float(np.std(selected_r2)),
            'max': float(np.max(selected_r2)),
            'min': float(np.min(selected_r2))
        }
    else:
        selected_r2_stats = None

    return {
        'total_voxels': int(total_voxels),
        'selected_voxels': int(selected_voxels),
        'selection_rate_pct': float(selection_rate),
        'threshold': float(threshold),
        'all_r2_stats': all_r2_stats,
        'selected_r2_stats': selected_r2_stats
    }


def analyze_classification_performance(classification_df):
    """
    Analyze classification performance

    분류 정확도의 의미:
    - 8개 색깔 분류 → chance level = 12.5% (1/8)
    - accuracy > 30% → 색깔 구분 가능
    - accuracy > 40% → 좋은 구분력

    Args:
        classification_df: DataFrame with columns ['test_run', 'accuracy']

    Returns:
        dict with metrics
    """
    if classification_df is None:
        return None

    accuracies = classification_df['accuracy'].values

    return {
        'mean_accuracy': float(np.mean(accuracies)),
        'std_accuracy': float(np.std(accuracies)),
        'median_accuracy': float(np.median(accuracies)),
        'min_accuracy': float(np.min(accuracies)),
        'max_accuracy': float(np.max(accuracies)),
        'n_runs': len(accuracies),
        'chance_level': 12.5,  # 8 colors
        'above_30pct': int(np.sum(accuracies > 30)),
        'above_40pct': int(np.sum(accuracies > 40))
    }


def analyze_reconstruction_performance(reconstruction_df):
    """
    Analyze reconstruction performance

    재구성 오차의 의미:
    - mean_error (degrees): 실제 색깔과 예측 색깔의 각도 차이
    - 0° = 완벽, 180° = 정반대 색깔
    - mean_error < 45° → 좋은 재구성
    - mean_error < 60° → 허용 가능

    Args:
        reconstruction_df: DataFrame with columns ['test_run', 'mean_error', 'hit_rate_30', etc.]

    Returns:
        dict with metrics
    """
    if reconstruction_df is None:
        return None

    mean_errors = reconstruction_df['mean_error'].values

    metrics = {
        'mean_error_deg': float(np.mean(mean_errors)),
        'std_error_deg': float(np.std(mean_errors)),
        'median_error_deg': float(np.median(mean_errors)),
        'min_error_deg': float(np.min(mean_errors)),
        'max_error_deg': float(np.max(mean_errors)),
        'n_runs': len(mean_errors)
    }

    # Hit rates (if available)
    if 'hit_rate_30' in reconstruction_df.columns:
        metrics['mean_hit_rate_30'] = float(np.mean(reconstruction_df['hit_rate_30']))
    if 'hit_rate_45' in reconstruction_df.columns:
        metrics['mean_hit_rate_45'] = float(np.mean(reconstruction_df['hit_rate_45']))

    return metrics


def compute_color_discriminability(amplitudes_z):
    """
    Compute color discriminability (between-color effect size)

    색깔 구분력의 의미:
    - 색깔 간 신호 차이가 클수록 구분 쉬움
    - Effect size (Cohen's d) 사용
    - d > 0.5 → medium effect (구분 가능)
    - d > 0.8 → large effect (명확한 구분)

    Args:
        amplitudes_z: (n_runs, n_colors, n_voxels) z-scored amplitudes

    Returns:
        dict with discriminability metrics
    """
    if amplitudes_z is None:
        return None

    n_runs, n_colors, n_voxels = amplitudes_z.shape

    # Run-averaged amplitudes (more stable)
    amp_avg = np.mean(amplitudes_z, axis=0)  # (n_colors, n_voxels)

    # Pairwise distances between colors (Euclidean in voxel space)
    from itertools import combinations
    pairwise_distances = []

    for i, j in combinations(range(n_colors), 2):
        # Distance between color i and color j
        dist = np.linalg.norm(amp_avg[i] - amp_avg[j])
        pairwise_distances.append(dist)

    pairwise_distances = np.array(pairwise_distances)

    # Effect size (normalized by within-color variability)
    within_color_std = np.mean([np.std(amplitudes_z[:, c, :]) for c in range(n_colors)])
    effect_sizes = pairwise_distances / within_color_std

    return {
        'mean_pairwise_distance': float(np.mean(pairwise_distances)),
        'std_pairwise_distance': float(np.std(pairwise_distances)),
        'min_pairwise_distance': float(np.min(pairwise_distances)),
        'max_pairwise_distance': float(np.max(pairwise_distances)),
        'mean_effect_size': float(np.mean(effect_sizes)),
        'median_effect_size': float(np.median(effect_sizes)),
        'within_color_std': float(within_color_std),
        'n_color_pairs': len(pairwise_distances)
    }


def main():
    parser = argparse.ArgumentParser(description='Analyze task-evoked response quality')
    parser.add_argument('--baseline-timestamp', type=str, required=True,
                       help='Timestamp of baseline results')
    parser.add_argument('--tsnr-timestamp', type=str, default=None,
                       help='Timestamp of tSNR results (for correlation analysis)')
    parser.add_argument('--subjects', nargs='+',
                       default=[f'sub-{i:02d}' for i in range(1, 11)],
                       help='List of subjects')
    parser.add_argument('--rois', nargs='+',
                       default=['V1', 'V2', 'V3', 'hV4'],
                       help='List of ROIs')
    parser.add_argument('--r2-threshold', type=float, default=0.1,
                       help='R² threshold for voxel selection (default: 0.1)')

    args = parser.parse_args()

    # Paths
    baseline_dir = Path('/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding') / args.baseline_timestamp
    output_dir = Path('/scratch/connectome/haba6030/colorBlind/analysis/validation/results/task_response')

    # Create timestamp for this run
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_dir = output_dir / (args.baseline_timestamp + '_' + timestamp)
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {run_dir}")

    # Storage for results
    task_quality_data = {
        'baseline_timestamp': args.baseline_timestamp,
        'r2_threshold': args.r2_threshold,
        'subjects': args.subjects,
        'rois': args.rois,
        'results': {}
    }

    # Analyze each subject-roi
    print("\nAnalyzing task-evoked response quality...")
    for subject in tqdm(args.subjects, desc='Subjects'):
        task_quality_data['results'][subject] = {}

        for roi in args.rois:
            # Load baseline results
            baseline_res = load_baseline_results(baseline_dir, subject, roi)

            if baseline_res['r2_voxel'] is None:
                print(f"Warning: No data for {subject} {roi}")
                continue

            # Analyze R² distribution
            r2_analysis = analyze_r2_distribution(baseline_res['r2_voxel'],
                                                  args.r2_threshold)

            # Analyze classification performance
            clf_analysis = analyze_classification_performance(baseline_res['classification_df'])

            # Analyze reconstruction performance
            recon_analysis = analyze_reconstruction_performance(baseline_res['reconstruction_df'])

            # Compute color discriminability
            discrim_analysis = compute_color_discriminability(baseline_res['amplitudes_z'])

            # Store results
            task_quality_data['results'][subject][roi] = {
                'r2_analysis': r2_analysis,
                'classification': clf_analysis,
                'reconstruction': recon_analysis,
                'discriminability': discrim_analysis
            }

    # Save detailed results
    json_path = run_dir / 'task_response_quality.json'
    with open(json_path, 'w') as f:
        json.dump(task_quality_data, f, indent=2)
    print(f"\nSaved detailed results to {json_path}")

    # ========================================================================
    # Visualization
    # ========================================================================

    print("\nGenerating visualizations...")

    # Prepare data for plotting
    plot_data = []
    for subject in args.subjects:
        for roi in args.rois:
            if subject not in task_quality_data['results']:
                continue
            if roi not in task_quality_data['results'][subject]:
                continue

            data = task_quality_data['results'][subject][roi]

            if data['r2_analysis'] and data['classification']:
                plot_data.append({
                    'subject': subject,
                    'roi': roi,
                    'median_r2': data['r2_analysis']['selected_r2_stats']['median'] if data['r2_analysis']['selected_r2_stats'] else 0,
                    'selection_rate': data['r2_analysis']['selection_rate_pct'],
                    'mean_accuracy': data['classification']['mean_accuracy'],
                    'mean_error': data['reconstruction']['mean_error_deg'] if data['reconstruction'] else np.nan,
                    'effect_size': data['discriminability']['mean_effect_size'] if data['discriminability'] else np.nan
                })

    df = pd.DataFrame(plot_data)

    # Figure 1: R² Distribution
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # 1A: R² median by ROI
    ax = axes[0, 0]
    roi_positions = {roi: i for i, roi in enumerate(args.rois)}
    for roi in args.rois:
        roi_data = df[df['roi'] == roi]['median_r2'].values
        if len(roi_data) > 0:
            ax.boxplot([roi_data], positions=[roi_positions[roi]], widths=0.5)

    ax.axhline(y=0.15, color='green', linestyle='--', label='Good (R²>0.15)', linewidth=2)
    ax.axhline(y=0.10, color='orange', linestyle='--', label='Threshold (R²>0.10)', linewidth=2)
    ax.set_xticks(list(roi_positions.values()))
    ax.set_xticklabels(list(roi_positions.keys()))
    ax.set_xlabel('ROI', fontsize=12)
    ax.set_ylabel('Median R² (selected voxels)', fontsize=12)
    ax.set_title('R² Distribution by ROI', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # 1B: Voxel selection rate by ROI
    ax = axes[0, 1]
    for roi in args.rois:
        roi_data = df[df['roi'] == roi]['selection_rate'].values
        if len(roi_data) > 0:
            ax.boxplot([roi_data], positions=[roi_positions[roi]], widths=0.5)

    ax.set_xticks(list(roi_positions.values()))
    ax.set_xticklabels(list(roi_positions.keys()))
    ax.set_xlabel('ROI', fontsize=12)
    ax.set_ylabel('Voxel Selection Rate (%)', fontsize=12)
    ax.set_title('Percentage of Task-Responsive Voxels', fontsize=14)
    ax.grid(True, alpha=0.3)

    # 1C: Classification accuracy by ROI
    ax = axes[1, 0]
    for roi in args.rois:
        roi_data = df[df['roi'] == roi]['mean_accuracy'].values
        if len(roi_data) > 0:
            ax.boxplot([roi_data], positions=[roi_positions[roi]], widths=0.5)

    ax.axhline(y=40, color='green', linestyle='--', label='Good (>40%)', linewidth=2)
    ax.axhline(y=30, color='orange', linestyle='--', label='Acceptable (>30%)', linewidth=2)
    ax.axhline(y=12.5, color='red', linestyle='--', label='Chance (12.5%)', linewidth=2)
    ax.set_xticks(list(roi_positions.values()))
    ax.set_xticklabels(list(roi_positions.keys()))
    ax.set_xlabel('ROI', fontsize=12)
    ax.set_ylabel('Classification Accuracy (%)', fontsize=12)
    ax.set_title('Color Classification Performance', fontsize=14)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # 1D: Reconstruction error by ROI
    ax = axes[1, 1]
    for roi in args.rois:
        roi_data = df[df['roi'] == roi]['mean_error'].dropna().values
        if len(roi_data) > 0:
            ax.boxplot([roi_data], positions=[roi_positions[roi]], widths=0.5)

    ax.axhline(y=45, color='green', linestyle='--', label='Good (<45°)', linewidth=2)
    ax.axhline(y=60, color='orange', linestyle='--', label='Acceptable (<60°)', linewidth=2)
    ax.set_xticks(list(roi_positions.values()))
    ax.set_xticklabels(list(roi_positions.keys()))
    ax.set_xlabel('ROI', fontsize=12)
    ax.set_ylabel('Reconstruction Error (degrees)', fontsize=12)
    ax.set_title('Color Reconstruction Accuracy', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig_path1 = run_dir / 'task_response_overview.png'
    plt.savefig(fig_path1)
    print(f"Saved overview plot to {fig_path1}")
    plt.close()

    # Figure 2: Color Discriminability (Effect Size)
    fig, ax = plt.subplots(figsize=(10, 6))
    for roi in args.rois:
        roi_data = df[df['roi'] == roi]['effect_size'].dropna().values
        if len(roi_data) > 0:
            ax.boxplot([roi_data], positions=[roi_positions[roi]], widths=0.5)

    ax.axhline(y=0.8, color='green', linestyle='--', label='Large effect (d>0.8)', linewidth=2)
    ax.axhline(y=0.5, color='orange', linestyle='--', label='Medium effect (d>0.5)', linewidth=2)
    ax.set_xticks(list(roi_positions.values()))
    ax.set_xticklabels(list(roi_positions.keys()))
    ax.set_xlabel('ROI', fontsize=12)
    ax.set_ylabel('Effect Size (Cohen\'s d)', fontsize=12)
    ax.set_title('Color Discriminability (Between-Color Signal Difference)', fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    fig_path2 = run_dir / 'color_discriminability.png'
    plt.savefig(fig_path2)
    print(f"Saved discriminability plot to {fig_path2}")
    plt.close()

    # Figure 3: Correlation between metrics
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # R² vs Classification accuracy
    ax = axes[0]
    valid_data = df.dropna(subset=['median_r2', 'mean_accuracy'])
    if len(valid_data) > 0:
        x = valid_data['median_r2'].values
        y = valid_data['mean_accuracy'].values
        ax.scatter(x, y, alpha=0.6, s=50)

        # Correlation
        r, p = pearsonr(x, y)
        ax.text(0.05, 0.95, f'r = {r:.3f}, p = {p:.3f}',
               transform=ax.transAxes, fontsize=11,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    ax.set_xlabel('Median R² (selected voxels)', fontsize=12)
    ax.set_ylabel('Classification Accuracy (%)', fontsize=12)
    ax.set_title('R² vs Classification Performance', fontsize=14)
    ax.grid(True, alpha=0.3)

    # Effect size vs Classification accuracy
    ax = axes[1]
    valid_data = df.dropna(subset=['effect_size', 'mean_accuracy'])
    if len(valid_data) > 0:
        x = valid_data['effect_size'].values
        y = valid_data['mean_accuracy'].values
        ax.scatter(x, y, alpha=0.6, s=50)

        # Correlation
        r, p = pearsonr(x, y)
        ax.text(0.05, 0.95, f'r = {r:.3f}, p = {p:.3f}',
               transform=ax.transAxes, fontsize=11,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    ax.set_xlabel('Effect Size (Cohen\'s d)', fontsize=12)
    ax.set_ylabel('Classification Accuracy (%)', fontsize=12)
    ax.set_title('Discriminability vs Classification Performance', fontsize=14)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    fig_path3 = run_dir / 'metric_correlations.png'
    plt.savefig(fig_path3)
    print(f"Saved correlation plot to {fig_path3}")
    plt.close()

    # Compute summary statistics
    summary = {
        'overall': {
            'mean_r2': float(df['median_r2'].mean()),
            'mean_selection_rate': float(df['selection_rate'].mean()),
            'mean_accuracy': float(df['mean_accuracy'].mean()),
            'mean_error_deg': float(df['mean_error'].mean()),
            'mean_effect_size': float(df['effect_size'].mean())
        },
        'by_roi': {},
        'quality_check': {
            'good_r2_count': int((df['median_r2'] > 0.15).sum()),
            'good_accuracy_count': int((df['mean_accuracy'] > 40).sum()),
            'acceptable_accuracy_count': int((df['mean_accuracy'] > 30).sum()),
            'total_count': len(df)
        }
    }

    for roi in args.rois:
        roi_data = df[df['roi'] == roi]
        if len(roi_data) > 0:
            summary['by_roi'][roi] = {
                'mean_r2': float(roi_data['median_r2'].mean()),
                'mean_selection_rate': float(roi_data['selection_rate'].mean()),
                'mean_accuracy': float(roi_data['mean_accuracy'].mean()),
                'mean_error_deg': float(roi_data['mean_error'].mean()),
                'mean_effect_size': float(roi_data['effect_size'].mean())
            }

    # Save results summary
    results_path = run_dir / 'results.json'
    with open(results_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Saved summary to {results_path}")

    # Save settings
    settings = {
        'script': '01b_task_response_quality.py',
        'baseline_timestamp': args.baseline_timestamp,
        'r2_threshold': args.r2_threshold,
        'subjects': args.subjects,
        'rois': args.rois,
        'timestamp': timestamp
    }
    settings_path = run_dir / 'settings.json'
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)
    print(f"Saved settings to {settings_path}")

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Overall R²: {summary['overall']['mean_r2']:.3f}")
    print(f"Overall voxel selection rate: {summary['overall']['mean_selection_rate']:.1f}%")
    print(f"Overall classification accuracy: {summary['overall']['mean_accuracy']:.1f}% (chance: 12.5%)")
    print(f"Overall reconstruction error: {summary['overall']['mean_error_deg']:.1f}°")
    print(f"Overall color discriminability (d): {summary['overall']['mean_effect_size']:.2f}")
    print(f"\nGood R² (>0.15): {summary['quality_check']['good_r2_count']}/{summary['quality_check']['total_count']}")
    print(f"Good accuracy (>40%): {summary['quality_check']['good_accuracy_count']}/{summary['quality_check']['total_count']}")
    print(f"Acceptable accuracy (>30%): {summary['quality_check']['acceptable_accuracy_count']}/{summary['quality_check']['total_count']}")
    print("="*70)


if __name__ == '__main__':
    main()
