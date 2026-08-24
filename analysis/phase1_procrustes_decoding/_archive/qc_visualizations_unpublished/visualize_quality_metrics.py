#!/usr/bin/env python3
"""
Visualize Quality Metrics for C010+Procrustes Pipeline

Creates comprehensive visualizations including:
1. Voxel-wise SNR distribution
2. Run-to-run amplitude correlation heatmap
3. Mean amplitude per color
4. HRF variability analysis (if individual voxel HRFs available)

Author: Claude Code
Date: 2026-02-09
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from scipy.stats import spearmanr
import sys

# Configuration
DATA_DIR = Path(__file__).parent / "full_dataset_C010_with_residuals"
OUTPUT_DIR = Path(__file__).parent / "visualization" / "quality_metrics"

# Subject and ROI to visualize
SUBJECT_ID = "02"
ROI_NAME = "V2"

N_COLORS = 8
N_RUNS = 6
TR = 1.5
FIR_DELAYS = np.arange(8) * TR

# Color names for plotting
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']


def load_data(subject_id, roi_name):
    """Load amplitude and HRF data"""
    data_path = DATA_DIR / f"sub-{subject_id}" / roi_name

    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_path}")

    # Load amplitudes
    amplitudes_raw = np.load(data_path / "amplitudes_raw.npy")  # (6, 8, n_voxels)
    amplitudes_proc = np.load(data_path / "amplitudes_procrustes.npy")

    # Load HRF
    roi_hrf = np.load(data_path / "roi_hrf.npy")  # (8,)
    roi_hrf_deriv = np.load(data_path / "roi_hrf_deriv.npy")

    # Load residuals (for SNR calculation)
    residuals = np.load(data_path / "residuals_2nd_level.npy")  # (total_scans, n_voxels)

    # Load config
    with open(data_path / "config.json", 'r') as f:
        config = json.load(f)

    return {
        'amplitudes_raw': amplitudes_raw,
        'amplitudes_proc': amplitudes_proc,
        'roi_hrf': roi_hrf,
        'roi_hrf_deriv': roi_hrf_deriv,
        'residuals': residuals,
        'config': config
    }


def compute_voxelwise_snr(amplitudes_raw):
    """
    Compute voxel-wise SNR (color discrimination)

    For each voxel:
    - Signal = std(mean_amplitude_per_color)
    - Noise = mean(std_amplitude_per_color_across_runs)
    - SNR = Signal / Noise
    """
    n_runs, n_colors, n_voxels = amplitudes_raw.shape
    voxel_snr = np.zeros(n_voxels)

    for voxel_idx in range(n_voxels):
        # Mean amplitude per color (across runs)
        mean_per_color = np.mean(amplitudes_raw[:, :, voxel_idx], axis=0)  # (8,)

        # Std amplitude per color (across runs)
        std_per_color = np.std(amplitudes_raw[:, :, voxel_idx], axis=0)  # (8,)

        # Signal = variability across colors
        signal = np.std(mean_per_color)

        # Noise = mean variability within colors
        noise = np.mean(std_per_color)

        voxel_snr[voxel_idx] = signal / (noise + 1e-8)

    return voxel_snr


def compute_run_to_run_correlation(amplitudes_raw):
    """
    Compute run-to-run amplitude pattern correlation

    Returns correlation matrix (6x6)
    """
    n_runs, n_colors, n_voxels = amplitudes_raw.shape
    corr_matrix = np.zeros((n_runs, n_runs))

    for i in range(n_runs):
        for j in range(n_runs):
            # Flatten amplitude patterns (colors × voxels)
            pattern_i = amplitudes_raw[i].flatten()
            pattern_j = amplitudes_raw[j].flatten()

            # Spearman correlation
            r, _ = spearmanr(pattern_i, pattern_j)
            corr_matrix[i, j] = r

    return corr_matrix


def plot_snr_distribution(voxel_snr, output_dir):
    """Plot voxel-wise SNR distribution"""
    fig, ax = plt.subplots(figsize=(10, 7))

    # Histogram
    ax.hist(voxel_snr, bins=40, edgecolor='black', alpha=0.7, color='steelblue')

    # Statistics lines
    mean_snr = np.mean(voxel_snr)
    median_snr = np.median(voxel_snr)

    ax.axvline(mean_snr, color='red', linestyle='--', linewidth=2.5,
               label=f'Mean = {mean_snr:.3f}')
    ax.axvline(median_snr, color='orange', linestyle='--', linewidth=2.5,
               label=f'Median = {median_snr:.3f}')
    ax.axvline(1.0, color='black', linestyle=':', linewidth=2,
               label='SNR = 1.0 (signal = noise)')

    # Labels and title
    ax.set_xlabel('SNR (color discrimination)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Number of voxels', fontsize=13, fontweight='bold')
    ax.set_title(f'{ROI_NAME}: Voxel-wise SNR Distribution',
                 fontsize=15, fontweight='bold')
    ax.legend(fontsize=11, loc='upper right')
    ax.grid(True, alpha=0.3)

    # Add text box with statistics
    high_snr = np.sum(voxel_snr > 1.0)
    very_high_snr = np.sum(voxel_snr > 2.0)
    n_voxels = len(voxel_snr)

    stats_text = f'Voxels with SNR > 1.0: {high_snr}/{n_voxels} ({100*high_snr/n_voxels:.1f}%)\n'
    stats_text += f'Voxels with SNR > 2.0: {very_high_snr}/{n_voxels} ({100*very_high_snr/n_voxels:.1f}%)'

    ax.text(0.98, 0.97, stats_text,
            transform=ax.transAxes, ha='right', va='top',
            fontsize=10, family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat',
                     edgecolor='black', alpha=0.8))

    plt.tight_layout()
    plt.savefig(output_dir / 'voxelwise_snr_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved: voxelwise_snr_distribution.png")


def plot_run_correlation_heatmap(corr_matrix, output_dir):
    """Plot run-to-run amplitude correlation heatmap"""
    fig, ax = plt.subplots(figsize=(10, 8))

    # Heatmap
    im = ax.imshow(corr_matrix, cmap='RdYlGn', aspect='auto',
                   vmin=0.0, vmax=1.0, interpolation='nearest')

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Spearman Correlation', rotation=270, labelpad=20,
                   fontsize=12, fontweight='bold')

    # Add text annotations
    for i in range(N_RUNS):
        for j in range(N_RUNS):
            text_color = 'white' if corr_matrix[i, j] < 0.5 else 'black'
            ax.text(j, i, f'{corr_matrix[i, j]:.3f}',
                   ha='center', va='center', color=text_color,
                   fontsize=11, fontweight='bold')

    # Labels and title
    ax.set_xticks(np.arange(N_RUNS))
    ax.set_yticks(np.arange(N_RUNS))
    ax.set_xticklabels([f'Run {i+1}' for i in range(N_RUNS)], fontsize=11)
    ax.set_yticklabels([f'Run {i+1}' for i in range(N_RUNS)], fontsize=11)
    ax.set_xlabel('Run', fontsize=13, fontweight='bold')
    ax.set_ylabel('Run', fontsize=13, fontweight='bold')
    ax.set_title(f'{ROI_NAME}: Run-to-Run Amplitude Pattern Correlation',
                 fontsize=15, fontweight='bold', pad=15)

    # Add grid
    ax.set_xticks(np.arange(N_RUNS) - 0.5, minor=True)
    ax.set_yticks(np.arange(N_RUNS) - 0.5, minor=True)
    ax.grid(which='minor', color='black', linestyle='-', linewidth=1.5)

    # Compute off-diagonal mean
    mask = ~np.eye(N_RUNS, dtype=bool)
    off_diag_mean = np.mean(corr_matrix[mask])

    # Add text box
    stats_text = f'Off-diagonal mean: {off_diag_mean:.3f}\n'
    stats_text += f'(Average run-to-run reliability)'

    ax.text(0.02, 0.98, stats_text,
            transform=ax.transAxes, ha='left', va='top',
            fontsize=10, family='monospace',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='wheat',
                     edgecolor='black', alpha=0.8))

    plt.tight_layout()
    plt.savefig(output_dir / 'run_to_run_correlation_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved: run_to_run_correlation_heatmap.png")


def plot_mean_amplitude_per_color(amplitudes_raw, amplitudes_proc, output_dir):
    """Plot mean amplitude per color (raw and Procrustes)"""
    n_runs, n_colors, n_voxels = amplitudes_raw.shape

    # Compute mean and SEM across runs and voxels
    mean_raw = np.mean(amplitudes_raw, axis=(0, 2))  # (8,)
    sem_raw = np.std(amplitudes_raw, axis=(0, 2)) / np.sqrt(n_runs * n_voxels)

    mean_proc = np.mean(amplitudes_proc, axis=(0, 2))
    sem_proc = np.std(amplitudes_proc, axis=(0, 2)) / np.sqrt(n_runs * n_voxels)

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Raw amplitudes
    ax = axes[0]
    x = np.arange(N_COLORS)
    bars = ax.bar(x, mean_raw, yerr=sem_raw, capsize=5, alpha=0.7,
                  color='steelblue', edgecolor='black', linewidth=1.5,
                  error_kw={'linewidth': 2})

    ax.axhline(0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=11)
    ax.set_xlabel('Color', fontsize=13, fontweight='bold')
    ax.set_ylabel('Mean Amplitude (±SEM)', fontsize=13, fontweight='bold')
    ax.set_title(f'{ROI_NAME}: Raw Amplitudes', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, mean_raw)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.3f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Procrustes amplitudes
    ax = axes[1]
    bars = ax.bar(x, mean_proc, yerr=sem_proc, capsize=5, alpha=0.7,
                  color='coral', edgecolor='black', linewidth=1.5,
                  error_kw={'linewidth': 2})

    ax.axhline(0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=11)
    ax.set_xlabel('Color', fontsize=13, fontweight='bold')
    ax.set_ylabel('Mean Amplitude (±SEM)', fontsize=13, fontweight='bold')
    ax.set_title(f'{ROI_NAME}: Procrustes-Aligned Amplitudes', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # Add value labels on bars
    for i, (bar, val) in enumerate(zip(bars, mean_proc)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.3f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_dir / 'mean_amplitude_per_color.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved: mean_amplitude_per_color.png")


def plot_roi_hrf(roi_hrf, roi_hrf_deriv, output_dir):
    """Plot ROI mean HRF and derivative"""
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # HRF
    ax = axes[0]
    ax.plot(FIR_DELAYS, roi_hrf, 'o-', color='steelblue', linewidth=2.5,
            markersize=8, markerfacecolor='white', markeredgewidth=2,
            markeredgecolor='steelblue', label='ROI Mean HRF')
    ax.axhline(0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.set_xlabel('Time (seconds)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Response Amplitude', fontsize=13, fontweight='bold')
    ax.set_title(f'{ROI_NAME}: ROI Mean HRF', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    # Find peak
    peak_idx = np.argmax(roi_hrf)
    peak_time = FIR_DELAYS[peak_idx]
    peak_amp = roi_hrf[peak_idx]
    ax.plot(peak_time, peak_amp, 'r*', markersize=20, label=f'Peak at {peak_time:.1f}s')
    ax.legend(fontsize=11)

    # Derivative
    ax = axes[1]
    ax.plot(FIR_DELAYS, roi_hrf_deriv, 'o-', color='coral', linewidth=2.5,
            markersize=8, markerfacecolor='white', markeredgewidth=2,
            markeredgecolor='coral', label='HRF Derivative')
    ax.axhline(0, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
    ax.set_xlabel('Time (seconds)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Derivative Amplitude', fontsize=13, fontweight='bold')
    ax.set_title(f'{ROI_NAME}: HRF Derivative', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / 'roi_mean_hrf.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved: roi_mean_hrf.png")


def plot_summary_figure(data, voxel_snr, corr_matrix, output_dir):
    """Create comprehensive summary figure"""
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    amplitudes_raw = data['amplitudes_raw']
    amplitudes_proc = data['amplitudes_proc']
    roi_hrf = data['roi_hrf']
    n_runs, n_colors, n_voxels = amplitudes_raw.shape

    # Title
    fig.suptitle(f'{ROI_NAME}: Quality Metrics Summary (sub-{SUBJECT_ID})',
                 fontsize=18, fontweight='bold')

    # 1. SNR Distribution (top-left)
    ax = fig.add_subplot(gs[0, 0])
    ax.hist(voxel_snr, bins=30, edgecolor='black', alpha=0.7, color='steelblue')
    mean_snr = np.mean(voxel_snr)
    ax.axvline(mean_snr, color='red', linestyle='--', linewidth=2,
               label=f'Mean = {mean_snr:.3f}')
    ax.axvline(1.0, color='black', linestyle=':', linewidth=1.5)
    ax.set_xlabel('SNR', fontsize=11, fontweight='bold')
    ax.set_ylabel('Number of voxels', fontsize=11, fontweight='bold')
    ax.set_title('Voxel-wise SNR', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # 2. Run Correlation Heatmap (top-middle)
    ax = fig.add_subplot(gs[0, 1])
    im = ax.imshow(corr_matrix, cmap='RdYlGn', vmin=0, vmax=1, aspect='auto')
    ax.set_xticks(np.arange(N_RUNS))
    ax.set_yticks(np.arange(N_RUNS))
    ax.set_xticklabels([f'R{i+1}' for i in range(N_RUNS)], fontsize=9)
    ax.set_yticklabels([f'R{i+1}' for i in range(N_RUNS)], fontsize=9)
    ax.set_title('Run-to-Run Correlation', fontsize=12, fontweight='bold')
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    # 3. ROI HRF (top-right)
    ax = fig.add_subplot(gs[0, 2])
    ax.plot(FIR_DELAYS, roi_hrf, 'o-', color='steelblue', linewidth=2,
            markersize=6, markerfacecolor='white', markeredgewidth=1.5)
    ax.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_xlabel('Time (s)', fontsize=11, fontweight='bold')
    ax.set_ylabel('Amplitude', fontsize=11, fontweight='bold')
    ax.set_title('ROI Mean HRF', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)

    # 4. Raw Amplitudes per Color (middle-left)
    ax = fig.add_subplot(gs[1, 0])
    mean_raw = np.mean(amplitudes_raw, axis=(0, 2))
    sem_raw = np.std(amplitudes_raw, axis=(0, 2)) / np.sqrt(n_runs * n_voxels)
    x = np.arange(N_COLORS)
    ax.bar(x, mean_raw, yerr=sem_raw, capsize=4, alpha=0.7,
           color='steelblue', edgecolor='black', linewidth=1)
    ax.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels([c[:3] for c in COLOR_NAMES], fontsize=9)
    ax.set_xlabel('Color', fontsize=11, fontweight='bold')
    ax.set_ylabel('Amplitude', fontsize=11, fontweight='bold')
    ax.set_title('Raw Amplitudes', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # 5. Procrustes Amplitudes per Color (middle-middle)
    ax = fig.add_subplot(gs[1, 1])
    mean_proc = np.mean(amplitudes_proc, axis=(0, 2))
    sem_proc = np.std(amplitudes_proc, axis=(0, 2)) / np.sqrt(n_runs * n_voxels)
    ax.bar(x, mean_proc, yerr=sem_proc, capsize=4, alpha=0.7,
           color='coral', edgecolor='black', linewidth=1)
    ax.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels([c[:3] for c in COLOR_NAMES], fontsize=9)
    ax.set_xlabel('Color', fontsize=11, fontweight='bold')
    ax.set_ylabel('Amplitude', fontsize=11, fontweight='bold')
    ax.set_title('Procrustes Amplitudes', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # 6. Amplitude comparison (middle-right)
    ax = fig.add_subplot(gs[1, 2])
    ax.plot(mean_raw, 'o-', color='steelblue', linewidth=2, markersize=8,
            label='Raw', alpha=0.7)
    ax.plot(mean_proc, 's-', color='coral', linewidth=2, markersize=8,
            label='Procrustes', alpha=0.7)
    ax.axhline(0, color='red', linestyle='--', linewidth=1, alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels([c[:3] for c in COLOR_NAMES], fontsize=9)
    ax.set_xlabel('Color', fontsize=11, fontweight='bold')
    ax.set_ylabel('Mean Amplitude', fontsize=11, fontweight='bold')
    ax.set_title('Raw vs Procrustes', fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # 7. Metrics Table (bottom span all)
    ax = fig.add_subplot(gs[2, :])
    ax.axis('off')

    # Load metrics
    with open(DATA_DIR / f"sub-{SUBJECT_ID}" / ROI_NAME / "metrics.json", 'r') as f:
        metrics = json.load(f)

    # Create table data
    table_data = [
        ['Metric', 'Raw', 'Procrustes', 'Improvement'],
        ['RDM Reliability', f"{metrics['raw_rdm_reliability']:.4f}",
         f"{metrics['procrustes_rdm_reliability']:.4f}",
         f"+{(metrics['procrustes_rdm_reliability'] - metrics['raw_rdm_reliability']):.4f}"],
        ['Noise Ceiling (Random)', f"{metrics['raw_noise_ceiling']['random']:.4f}",
         f"{metrics['procrustes_noise_ceiling']['random']:.4f}",
         f"+{(metrics['procrustes_noise_ceiling']['random'] - metrics['raw_noise_ceiling']['random']):.4f}"],
        ['Noise Ceiling (Odd/Even)', f"{metrics['raw_noise_ceiling']['oddeven']:.4f}",
         f"{metrics['procrustes_noise_ceiling']['oddeven']:.4f}",
         f"+{(metrics['procrustes_noise_ceiling']['oddeven'] - metrics['raw_noise_ceiling']['oddeven']):.4f}"],
        ['Method Difference', f"{metrics['raw_noise_ceiling']['method_diff']:.4f}",
         f"{metrics['procrustes_noise_ceiling']['method_diff']:.4f}",
         f"{(metrics['procrustes_noise_ceiling']['method_diff'] - metrics['raw_noise_ceiling']['method_diff']):+.4f}"],
        ['', '', '', ''],
        ['SNR (mean)', f"{mean_snr:.3f}", '-', '-'],
        ['Procrustes Disparity', '-', f"{metrics['procrustes_disparity']:.6f}", '-'],
        ['Temporal Autocorrelation', f"{metrics['temporal_autocorrelation']:.4f}", '-', '-'],
        ['Drift Magnitude', f"{metrics['drift_magnitude']:.6f}", '-', '-'],
    ]

    table = ax.table(cellText=table_data, cellLoc='center', loc='center',
                    bbox=[0.1, 0.1, 0.8, 0.8])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    # Style header row
    for i in range(4):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # Style data rows
    for i in range(1, len(table_data)):
        for j in range(4):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#f0f0f0')

    plt.savefig(output_dir / 'summary_quality_metrics.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved: summary_quality_metrics.png")


def main():
    """Main execution"""
    print(f"\n{'='*80}")
    print(f"Visualizing Quality Metrics: sub-{SUBJECT_ID} {ROI_NAME}")
    print(f"{'='*80}\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    print("Loading data...")
    data = load_data(SUBJECT_ID, ROI_NAME)
    print(f"  ✓ Amplitudes: {data['amplitudes_raw'].shape}")
    print(f"  ✓ Residuals: {data['residuals'].shape}")
    print(f"  ✓ ROI HRF: {data['roi_hrf'].shape}")

    # Compute SNR
    print("\nComputing voxel-wise SNR...")
    voxel_snr = compute_voxelwise_snr(data['amplitudes_raw'])
    print(f"  ✓ Mean SNR: {np.mean(voxel_snr):.3f}")

    # Compute run-to-run correlation
    print("\nComputing run-to-run correlation...")
    corr_matrix = compute_run_to_run_correlation(data['amplitudes_raw'])
    mask = ~np.eye(N_RUNS, dtype=bool)
    off_diag_mean = np.mean(corr_matrix[mask])
    print(f"  ✓ Off-diagonal mean: {off_diag_mean:.3f}")

    # Generate visualizations
    print("\nGenerating visualizations...")
    plot_snr_distribution(voxel_snr, OUTPUT_DIR)
    plot_run_correlation_heatmap(corr_matrix, OUTPUT_DIR)
    plot_mean_amplitude_per_color(data['amplitudes_raw'], data['amplitudes_proc'], OUTPUT_DIR)
    plot_roi_hrf(data['roi_hrf'], data['roi_hrf_deriv'], OUTPUT_DIR)
    plot_summary_figure(data, voxel_snr, corr_matrix, OUTPUT_DIR)

    print(f"\n{'='*80}")
    print(f"✓ All visualizations saved to: {OUTPUT_DIR}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
