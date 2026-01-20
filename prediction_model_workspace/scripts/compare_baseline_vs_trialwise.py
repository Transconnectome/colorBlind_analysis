#!/usr/bin/env python3
"""
Baseline (Phase 0) vs Trial-wise (Step 1.3) 비교 분석

Phase 0는 run-averaged로 괜찮았는데,
Step 1.3 trial-wise는 왜 reliability가 낮을까?

Usage:
    python compare_baseline_vs_trialwise.py --subject 10 --roi V1
"""

import argparse
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial.distance import procrustes

def parse_args():
    parser = argparse.ArgumentParser(description='Compare Baseline vs Trial-wise results')
    parser.add_argument('--subject', type=str, default='10', help='Subject ID')
    parser.add_argument('--roi', type=str, default='V1', help='ROI name')
    parser.add_argument('--baseline_dir', type=str,
                       default='../derivatives/BH2009_original_v3',
                       help='Baseline results directory')
    parser.add_argument('--trialwise_dir', type=str,
                       default='../results/trial_wise_glm/original_v3',
                       help='Trial-wise results directory')
    parser.add_argument('--output_dir', type=str,
                       default='../results/comparison',
                       help='Output directory')
    return parser.parse_args()


def load_baseline_amplitudes(subject_id, roi, baseline_dir):
    """
    Baseline (Phase 0) amplitudes 로드

    Returns
    -------
    amplitudes : ndarray
        (n_runs=6, n_colors=8, n_voxels)
    """
    base_path = Path(baseline_dir)

    # Find matching directory (e.g., baseline81_*/sm6.0_*_sub-10_V1_*)
    import glob
    pattern = str(base_path / f'*/sm*_sub-{subject_id}_{roi}_*')
    matches = glob.glob(pattern)

    if not matches:
        raise FileNotFoundError(f"No baseline results found for sub-{subject_id} {roi}")

    result_dir = Path(matches[0])
    print(f"Loading baseline from: {result_dir.name}")

    # Load amplitudes_z.npy
    amp_file = result_dir / 'amplitudes_z.npy'
    if not amp_file.exists():
        raise FileNotFoundError(f"amplitudes_z.npy not found in {result_dir}")

    amplitudes = np.load(amp_file)  # (6, 8, n_voxels)

    return amplitudes


def load_trialwise_betas(subject_id, roi, trialwise_dir):
    """
    Trial-wise (Step 1.3) betas 로드

    Returns
    -------
    trial_betas : ndarray
        (n_trials, n_voxels)
    trial_metadata : DataFrame
        Trial metadata (color, run, etc.)
    """
    trial_dir = Path(trialwise_dir) / f'sub-{subject_id}_{roi}'

    if not trial_dir.exists():
        raise FileNotFoundError(f"Trial-wise results not found: {trial_dir}")

    print(f"Loading trial-wise from: {trial_dir.name}")

    # Load betas
    betas_file = trial_dir / 'stimulus_wise_betas.npy'
    trial_betas = np.load(betas_file)

    # Load metadata
    metadata_file = trial_dir / 'trial_metadata.csv'
    trial_metadata = pd.read_csv(metadata_file)

    return trial_betas, trial_metadata


def compute_baseline_reliability(amplitudes):
    """
    Baseline run-to-run reliability (split-half)

    Parameters
    ----------
    amplitudes : ndarray (6, 8, n_voxels)

    Returns
    -------
    reliability : float
        Split-half Procrustes stability
    """
    odd_runs = amplitudes[[0, 2, 4], :, :]  # Runs 1, 3, 5
    even_runs = amplitudes[[1, 3, 5], :, :]  # Runs 2, 4, 6

    # Average across runs
    odd_avg = odd_runs.mean(axis=0)  # (8, n_voxels)
    even_avg = even_runs.mean(axis=0)  # (8, n_voxels)

    # Procrustes
    _, _, disparity = procrustes(odd_avg.T, even_avg.T)
    stability = 1.0 - disparity

    return stability


def compute_trialwise_reliability(trial_betas, trial_metadata):
    """
    Trial-wise split-half reliability

    Returns
    -------
    reliability : float
    """
    odd_runs = trial_metadata['run'].isin([1, 3, 5])
    even_runs = trial_metadata['run'].isin([2, 4, 6])

    # Per-color average
    color_reliabilities = []
    for color in trial_metadata['color'].unique():
        color_mask = trial_metadata['color'] == color

        odd_trials = trial_betas[color_mask & odd_runs]
        even_trials = trial_betas[color_mask & even_runs]

        if len(odd_trials) > 0 and len(even_trials) > 0:
            odd_avg = odd_trials.mean(axis=0)
            even_avg = even_trials.mean(axis=0)

            _, _, disparity = procrustes(
                odd_avg.reshape(-1, 1),
                even_avg.reshape(-1, 1)
            )
            stability = 1.0 - disparity
            color_reliabilities.append(stability)

    return np.mean(color_reliabilities)


def color_average_trialwise(trial_betas, trial_metadata):
    """
    Trial-wise를 color-averaged로 변환
    (Baseline과 동일한 구조)

    Returns
    -------
    color_averaged : ndarray (6, 8, n_voxels)
    """
    n_voxels = trial_betas.shape[1]
    color_averaged = np.zeros((6, 8, n_voxels))

    colors = sorted(trial_metadata['color'].unique())

    for run_idx, run_id in enumerate(range(1, 7)):
        run_mask = trial_metadata['run'] == run_id

        for color_idx, color in enumerate(colors):
            color_mask = trial_metadata['color'] == color

            trials = trial_betas[run_mask & color_mask]

            if len(trials) > 0:
                color_averaged[run_idx, color_idx, :] = trials.mean(axis=0)

    return color_averaged


def compare_snr(baseline_amps, trial_betas, trial_metadata):
    """
    SNR 비교: Baseline vs Trial-wise

    Returns
    -------
    baseline_snr : float
    trialwise_snr : float
    averaged_trialwise_snr : float
    """
    # Baseline SNR (per color, across runs)
    baseline_snr = []
    for color_idx in range(baseline_amps.shape[1]):  # 8 colors
        color_pattern = baseline_amps[:, color_idx, :]  # (6, n_voxels)
        snr = color_pattern.mean(axis=0) / (color_pattern.std(axis=0) + 1e-10)
        baseline_snr.append(snr.mean())
    baseline_snr = np.mean(baseline_snr)

    # Trial-wise SNR (per color, across trials)
    trialwise_snr = []
    for color in trial_metadata['color'].unique():
        color_mask = trial_metadata['color'] == color
        color_trials = trial_betas[color_mask]

        if len(color_trials) > 1:
            snr = color_trials.mean(axis=0) / (color_trials.std(axis=0) + 1e-10)
            trialwise_snr.append(snr.mean())
    trialwise_snr = np.mean(trialwise_snr)

    # Color-averaged trial-wise SNR
    color_avg = color_average_trialwise(trial_betas, trial_metadata)
    averaged_snr = []
    for color_idx in range(color_avg.shape[1]):
        color_pattern = color_avg[:, color_idx, :]
        snr = color_pattern.mean(axis=0) / (color_pattern.std(axis=0) + 1e-10)
        averaged_snr.append(snr.mean())
    averaged_snr = np.mean(averaged_snr)

    return baseline_snr, trialwise_snr, averaged_snr


def create_comparison_figure(results, output_dir):
    """
    비교 시각화
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Panel A: Reliability comparison
    ax = axes[0, 0]
    reliabilities = [
        results['baseline_reliability'],
        results['trialwise_reliability'],
        results['averaged_trialwise_reliability']
    ]
    labels = ['Baseline\n(run-averaged)', 'Trial-wise\n(individual)', 'Trial-wise\n(color-averaged)']
    colors_bar = ['green', 'red', 'orange']

    bars = ax.bar(labels, reliabilities, color=colors_bar, alpha=0.7)
    ax.axhline(0.50, color='green', linestyle='--', label='Target (0.50)')
    ax.set_ylabel('Split-half Reliability (Procrustes)', fontsize=12)
    ax.set_title('(A) Reliability Comparison', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Add value labels
    for bar, val in zip(bars, reliabilities):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.3f}', ha='center', va='bottom', fontsize=10)

    # Panel B: SNR comparison
    ax = axes[0, 1]
    snrs = [
        results['baseline_snr'],
        results['trialwise_snr'],
        results['averaged_snr']
    ]

    bars = ax.bar(labels, snrs, color=colors_bar, alpha=0.7)
    ax.set_ylabel('Signal-to-Noise Ratio', fontsize=12)
    ax.set_title('(B) SNR Comparison', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    for bar, val in zip(bars, snrs):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.2f}', ha='center', va='bottom', fontsize=10)

    # Panel C: Trial counts
    ax = axes[1, 0]
    n_patterns = [
        48,  # Baseline: 6 runs × 8 colors
        results['n_trials'],  # Trial-wise individual
        48  # Trial-wise color-averaged (same as baseline)
    ]

    bars = ax.bar(labels, n_patterns, color=colors_bar, alpha=0.7)
    ax.set_ylabel('Number of Patterns', fontsize=12)
    ax.set_title('(C) Pattern Count', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)

    for bar, val in zip(bars, n_patterns):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val}', ha='center', va='bottom', fontsize=10)

    # Panel D: Averaging benefit
    ax = axes[1, 1]

    # Calculate averaging benefit
    reliability_gain = results['averaged_trialwise_reliability'] - results['trialwise_reliability']
    snr_gain = results['averaged_snr'] / results['trialwise_snr']

    metrics = ['Reliability\nGain', 'SNR\nRatio']
    values = [reliability_gain, snr_gain]
    colors_gain = ['blue', 'purple']

    bars = ax.bar(metrics, values, color=colors_gain, alpha=0.7)
    ax.set_ylabel('Gain / Ratio', fontsize=12)
    ax.set_title('(D) Averaging Benefit', fontsize=14, fontweight='bold')
    ax.axhline(1.0, color='gray', linestyle='--', alpha=0.5)
    ax.grid(True, alpha=0.3)

    for bar, val in zip(bars, values):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.2f}', ha='center', va='bottom', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path / 'baseline_vs_trialwise_comparison.png', dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_path / 'baseline_vs_trialwise_comparison.png'}")
    plt.close()


def write_comparison_report(results, output_dir):
    """
    비교 리포트 작성
    """
    output_path = Path(output_dir)
    report_path = output_path / 'comparison_report.txt'

    lines = []
    lines.append("=" * 80)
    lines.append("BASELINE (Phase 0) vs TRIAL-WISE (Step 1.3) COMPARISON")
    lines.append("=" * 80)
    lines.append(f"\nSubject: sub-{results['subject']}")
    lines.append(f"ROI: {results['roi']}")
    lines.append("")

    lines.append("## 1. Reliability Comparison")
    lines.append("")
    lines.append(f"Baseline (run-averaged):          {results['baseline_reliability']:.3f}")
    lines.append(f"Trial-wise (individual):          {results['trialwise_reliability']:.3f}")
    lines.append(f"Trial-wise (color-averaged):      {results['averaged_trialwise_reliability']:.3f}")
    lines.append("")

    reliability_drop = results['baseline_reliability'] - results['trialwise_reliability']
    lines.append(f"📉 Reliability drop (baseline → trial-wise): {reliability_drop:.3f}")

    recovery = results['averaged_trialwise_reliability'] - results['trialwise_reliability']
    lines.append(f"📈 Recovery by averaging: {recovery:.3f}")
    lines.append("")

    lines.append("## 2. SNR Comparison")
    lines.append("")
    lines.append(f"Baseline SNR:                     {results['baseline_snr']:.2f}")
    lines.append(f"Trial-wise SNR:                   {results['trialwise_snr']:.2f}")
    lines.append(f"Trial-wise (color-averaged) SNR:  {results['averaged_snr']:.2f}")
    lines.append("")

    snr_ratio = results['averaged_snr'] / results['trialwise_snr']
    lines.append(f"📊 SNR improvement by averaging: {snr_ratio:.2f}x")
    lines.append("")

    lines.append("## 3. Pattern Count")
    lines.append("")
    lines.append(f"Baseline: 48 patterns (6 runs × 8 colors)")
    lines.append(f"Trial-wise: {results['n_trials']} trials")
    lines.append(f"Trial-wise color-averaged: 48 patterns (same as baseline)")
    lines.append("")

    lines.append("## 4. 왜 Phase 0 Baseline은 괜찮았을까?")
    lines.append("")
    lines.append("**Averaging 효과**:")
    lines.append(f"  - Reliability gain: +{recovery:.3f}")
    lines.append(f"  - SNR improvement: {snr_ratio:.2f}x")
    lines.append("")

    sqrt_n = np.sqrt(results['n_trials'] / 48)
    lines.append(f"**이론적 SNR 증가** (√n): {sqrt_n:.2f}x")
    lines.append(f"**실제 SNR 증가**: {snr_ratio:.2f}x")
    lines.append("")

    if results['baseline_reliability'] >= 0.50 and results['trialwise_reliability'] < 0.30:
        lines.append("## 5. 결론")
        lines.append("")
        lines.append("✅ Phase 0 Baseline이 괜찮았던 이유:")
        lines.append("   → Run-averaging이 noise를 효과적으로 감소시킴")
        lines.append("")
        lines.append("❌ Step 1.3 Trial-wise가 낮은 이유:")
        lines.append("   → Individual trials는 noise가 많음")
        lines.append("   → Averaging 없이는 낮은 SNR")
        lines.append("")
        lines.append("💡 해결 방안:")
        lines.append("   1. Trial-wise 결과를 color-averaged로 변환")
        lines.append(f"      → Reliability 향상: {results['trialwise_reliability']:.3f} → {results['averaged_trialwise_reliability']:.3f}")
        lines.append("   2. Smoothing 증가 (6mm → 8mm → 10mm)")
        lines.append("   3. HRF model 개선 (spm → spm+derivative)")
        lines.append("   4. 더 많은 trials 사용 (현재 ~330, 목표 432)")

    lines.append("")
    lines.append("=" * 80)

    with open(report_path, 'w') as f:
        f.write('\n'.join(lines))

    print(f"✅ Saved: {report_path}")

    # Print to console
    print("\n" + '\n'.join(lines))


def main():
    args = parse_args()

    print("=" * 80)
    print("Baseline vs Trial-wise Comparison")
    print("=" * 80)
    print(f"Subject: sub-{args.subject}")
    print(f"ROI: {args.roi}")
    print("")

    # Load data
    print("Loading data...")
    baseline_amps = load_baseline_amplitudes(args.subject, args.roi, args.baseline_dir)
    trial_betas, trial_metadata = load_trialwise_betas(args.subject, args.roi, args.trialwise_dir)

    print(f"  Baseline shape: {baseline_amps.shape}")
    print(f"  Trial-wise shape: {trial_betas.shape}")
    print("")

    # Compute metrics
    print("Computing metrics...")

    # Reliability
    baseline_reliability = compute_baseline_reliability(baseline_amps)
    trialwise_reliability = compute_trialwise_reliability(trial_betas, trial_metadata)

    # Color-averaged trial-wise
    color_avg_betas = color_average_trialwise(trial_betas, trial_metadata)
    averaged_trialwise_reliability = compute_baseline_reliability(color_avg_betas)

    # SNR
    baseline_snr, trialwise_snr, averaged_snr = compare_snr(
        baseline_amps, trial_betas, trial_metadata
    )

    print(f"  Baseline reliability: {baseline_reliability:.3f}")
    print(f"  Trial-wise reliability: {trialwise_reliability:.3f}")
    print(f"  Color-averaged trial-wise reliability: {averaged_trialwise_reliability:.3f}")
    print("")

    # Store results
    results = {
        'subject': args.subject,
        'roi': args.roi,
        'baseline_reliability': baseline_reliability,
        'trialwise_reliability': trialwise_reliability,
        'averaged_trialwise_reliability': averaged_trialwise_reliability,
        'baseline_snr': baseline_snr,
        'trialwise_snr': trialwise_snr,
        'averaged_snr': averaged_snr,
        'n_trials': len(trial_betas)
    }

    # Create figure
    print("Creating visualization...")
    create_comparison_figure(results, args.output_dir)

    # Write report
    print("\nWriting report...")
    write_comparison_report(results, args.output_dir)

    print("\n✅ Comparison complete!")


if __name__ == '__main__':
    main()
