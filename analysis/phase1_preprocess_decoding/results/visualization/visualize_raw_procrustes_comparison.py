#!/usr/bin/env python3
"""
Comprehensive Visualization: Raw vs Procrustes Comparison

Creates visualizations matching the reference images:
1. MDS Color Space Embedding (Before vs After Procrustes)
2. Distribution plots for RDM correlation, Crossnobis, Decoding accuracy

Author: Claude Code
Date: 2026-02-09
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from pathlib import Path
import json
from scipy.stats import spearmanr
from scipy.spatial.distance import pdist, squareform
from sklearn.manifold import MDS
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import LeaveOneOut
import sys

# Configuration
DATA_DIR = Path(__file__).parent / "full_dataset_C010_with_residuals"
OUTPUT_DIR = Path(__file__).parent / "visualization"

# Subjects and ROIs
SUBJECTS = ['02', '03', '04', '05', '06', '07', '08', '09', '10', '11']
ROIS = ['V1', 'V2', 'V3', 'V4']

N_COLORS = 8
N_RUNS = 6

# Color names and RGB values for visualization
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
COLOR_RGB = [
    '#FF0000',  # Red
    '#FF8800',  # Orange
    '#FFFF00',  # Yellow
    '#00FF00',  # Green
    '#00FFFF',  # Cyan
    '#0000FF',  # Blue
    '#8800FF',  # Purple
    '#FF00FF',  # Magenta
]


# ============================================================================
# Data Loading
# ============================================================================

def load_subject_roi_data(subject_id, roi_name):
    """Load amplitude data for one subject-ROI"""
    data_path = DATA_DIR / f"sub-{subject_id}" / roi_name

    if not data_path.exists():
        return None

    amplitudes_raw = np.load(data_path / "amplitudes_raw.npy")
    amplitudes_proc = np.load(data_path / "amplitudes_procrustes.npy")
    disparities = np.load(data_path / "procrustes_disparities.npy")

    with open(data_path / "metrics.json", 'r') as f:
        metrics = json.load(f)

    with open(data_path / "config.json", 'r') as f:
        config = json.load(f)

    return {
        'amplitudes_raw': amplitudes_raw,
        'amplitudes_proc': amplitudes_proc,
        'disparities': disparities,
        'metrics': metrics,
        'config': config
    }


def load_all_data():
    """Load data for all subjects and ROIs"""
    all_data = {}

    for subject in SUBJECTS:
        all_data[subject] = {}
        for roi in ROIS:
            data = load_subject_roi_data(subject, roi)
            if data is not None:
                all_data[subject][roi] = data

    return all_data


# ============================================================================
# RDM Computation
# ============================================================================

def compute_rdm_correlation(amplitudes):
    """
    Compute RDM correlation reliability (split-half)

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        Spearman correlation between odd/even RDM
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Split into odd and even runs
    odd_indices = np.arange(0, n_runs, 2)
    even_indices = np.arange(1, n_runs, 2)

    odd_patterns = amplitudes[odd_indices].mean(axis=0)  # (n_colors, n_voxels)
    even_patterns = amplitudes[even_indices].mean(axis=0)

    # Compute RDMs
    rdm_odd = 1 - np.corrcoef(odd_patterns)
    rdm_even = 1 - np.corrcoef(even_patterns)

    # Upper triangle
    mask = np.triu(np.ones_like(rdm_odd, dtype=bool), k=1)
    rdm_odd_vec = rdm_odd[mask]
    rdm_even_vec = rdm_even[mask]

    r, _ = spearmanr(rdm_odd_vec, rdm_even_vec)
    return r


def compute_crossnobis_rdm(amplitudes, residuals):
    """
    Compute Crossnobis RDM (Mahalanobis distance with noise covariance)

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        residuals: (total_scans, n_voxels) - noise covariance estimation

    Returns:
        RDM correlation using crossnobis distance
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Estimate noise covariance from residuals (Ledoit-Wolf regularization)
    try:
        from sklearn.covariance import LedoitWolf
        lw = LedoitWolf()
        lw.fit(residuals)
        precision = lw.precision_
    except:
        # Fallback: regularized inverse
        cov = np.cov(residuals.T)
        reg = 0.1 * np.trace(cov) / n_voxels
        precision = np.linalg.inv(cov + reg * np.eye(n_voxels))

    # Compute crossnobis distance for odd/even split
    odd_indices = np.arange(0, n_runs, 2)
    even_indices = np.arange(1, n_runs, 2)

    odd_patterns = amplitudes[odd_indices].mean(axis=0)  # (n_colors, n_voxels)
    even_patterns = amplitudes[even_indices].mean(axis=0)

    # Crossnobis RDM (using precision matrix)
    rdm_crossnobis = np.zeros((n_colors, n_colors))
    for i in range(n_colors):
        for j in range(i+1, n_colors):
            diff = odd_patterns[i] - odd_patterns[j]
            dist = np.sqrt(diff @ precision @ diff.T)
            rdm_crossnobis[i, j] = dist
            rdm_crossnobis[j, i] = dist

    # Compute correlation with even patterns
    rdm_even = np.zeros((n_colors, n_colors))
    for i in range(n_colors):
        for j in range(i+1, n_colors):
            diff = even_patterns[i] - even_patterns[j]
            dist = np.sqrt(diff @ precision @ diff.T)
            rdm_even[i, j] = dist
            rdm_even[j, i] = dist

    # Correlation between RDMs
    mask = np.triu(np.ones_like(rdm_crossnobis, dtype=bool), k=1)
    r, _ = spearmanr(rdm_crossnobis[mask], rdm_even[mask])

    return r


def compute_decoding_accuracy_loro(amplitudes):
    """
    Compute decoding accuracy using Leave-One-Run-Out (LORO) cross-validation
    Uses nearest-centroid classification (correlation-based)

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        Mean decoding accuracy across folds
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    accuracies = []

    # LORO cross-validation
    for test_run in range(n_runs):
        # Training runs
        train_runs = [r for r in range(n_runs) if r != test_run]

        # Average across training runs to get class centroids
        train_centroids = amplitudes[train_runs].mean(axis=0)  # (n_colors, n_voxels)
        test_data = amplitudes[test_run]  # (n_colors, n_voxels)

        # Classify each test pattern using correlation-based distance
        correct = 0
        for true_color in range(n_colors):
            test_pattern = test_data[true_color]  # (n_voxels,)

            # Compute correlation with all centroids
            correlations = np.zeros(n_colors)
            for centroid_idx in range(n_colors):
                centroid = train_centroids[centroid_idx]
                r = np.corrcoef(test_pattern, centroid)[0, 1]
                correlations[centroid_idx] = r if np.isfinite(r) else -1

            # Predict as the most correlated centroid
            predicted_color = np.argmax(correlations)

            if predicted_color == true_color:
                correct += 1

        accuracy = correct / n_colors
        accuracies.append(accuracy)

    return np.mean(accuracies)


# ============================================================================
# MDS Color Space Embedding
# ============================================================================

def compute_mds_embedding(amplitudes):
    """
    Compute MDS embedding for color space visualization

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)

    Returns:
        embedding: (n_runs, n_colors, 2) - 2D MDS coordinates
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # Compute MDS for each run separately
    embeddings = []

    for run_idx in range(n_runs):
        patterns = amplitudes[run_idx]  # (n_colors, n_voxels)

        # Compute pairwise distances (correlation distance)
        rdm = 1 - np.corrcoef(patterns)

        # MDS
        mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
        embedding = mds.fit_transform(rdm)

        embeddings.append(embedding)

    embeddings = np.array(embeddings)  # (n_runs, n_colors, 2)

    return embeddings


def plot_mds_color_space(subject_id, roi_name, data, output_dir):
    """
    Plot MDS color space embedding (Before vs After Procrustes)

    Matches the reference image format
    """
    amplitudes_raw = data['amplitudes_raw']
    amplitudes_proc = data['amplitudes_proc']

    # Compute MDS embeddings
    print(f"  Computing MDS embeddings...")
    embedding_raw = compute_mds_embedding(amplitudes_raw)
    embedding_proc = compute_mds_embedding(amplitudes_proc)

    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(20, 9))

    titles = ['A. Before Procrustes', 'B. After Procrustes']
    embeddings = [embedding_raw, embedding_proc]

    for ax, title, embedding in zip(axes, titles, embeddings):
        # Plot each run's colors
        for run_idx in range(N_RUNS):
            for color_idx in range(N_COLORS):
                x = embedding[run_idx, color_idx, 0]
                y = embedding[run_idx, color_idx, 1]

                ax.scatter(x, y, c=COLOR_RGB[color_idx], s=200,
                          alpha=0.6, edgecolors='black', linewidths=1.5)

        # Add color labels (positioned at the mean of all runs)
        for color_idx in range(N_COLORS):
            mean_x = embedding[:, color_idx, 0].mean()
            mean_y = embedding[:, color_idx, 1].mean()

            ax.annotate(COLOR_NAMES[color_idx],
                       xy=(mean_x, mean_y),
                       xytext=(10, 10), textcoords='offset points',
                       fontsize=11, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                                edgecolor='black', alpha=0.9))

        ax.axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.axvline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.set_xlabel('MDS Dimension 1', fontsize=13, fontweight='bold')
        ax.set_ylabel('MDS Dimension 2', fontsize=13, fontweight='bold')
        ax.set_title(f'{title}\n{subject_id} {roi_name} (6 runs overlaid)',
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_dir / f'color_space_embedding_{subject_id}_{roi_name}.png',
                dpi=300, bbox_inches='tight')
    plt.close()

    print(f"  ✓ Saved: color_space_embedding_{subject_id}_{roi_name}.png")


# ============================================================================
# Distribution Plots
# ============================================================================

def compute_all_metrics(all_data):
    """
    Compute all metrics for all subjects and ROIs

    Returns:
        Dictionary with arrays of metrics
    """
    metrics = {
        'rdm_corr_raw': [],
        'rdm_corr_proc': [],
        'crossnobis_raw': [],
        'crossnobis_proc': [],
        'decoding_raw': [],
        'decoding_proc': [],
        'procrustes_disparity': [],
        'subjects': [],
        'rois': []
    }

    print("\nComputing metrics for all subjects and ROIs...")

    for subject in SUBJECTS:
        for roi in ROIS:
            if subject not in all_data or roi not in all_data[subject]:
                continue

            data = all_data[subject][roi]
            amplitudes_raw = data['amplitudes_raw']
            amplitudes_proc = data['amplitudes_proc']
            disparities = data['disparities']

            # Check if residuals exist
            data_path = DATA_DIR / f"sub-{subject}" / roi
            if (data_path / "residuals_2nd_level.npy").exists():
                residuals = np.load(data_path / "residuals_2nd_level.npy")
            else:
                residuals = None

            print(f"  Processing {subject} {roi}...")

            # RDM correlation
            rdm_corr_raw = compute_rdm_correlation(amplitudes_raw)
            rdm_corr_proc = compute_rdm_correlation(amplitudes_proc)

            # Crossnobis (if residuals available)
            if residuals is not None:
                try:
                    crossnobis_raw = compute_crossnobis_rdm(amplitudes_raw, residuals)
                    crossnobis_proc = compute_crossnobis_rdm(amplitudes_proc, residuals)
                except:
                    crossnobis_raw = np.nan
                    crossnobis_proc = np.nan
            else:
                crossnobis_raw = np.nan
                crossnobis_proc = np.nan

            # Decoding accuracy (LORO)
            decoding_raw = compute_decoding_accuracy_loro(amplitudes_raw)
            decoding_proc = compute_decoding_accuracy_loro(amplitudes_proc)

            # Procrustes disparity
            disparity = disparities.mean()

            # Store metrics
            metrics['rdm_corr_raw'].append(rdm_corr_raw)
            metrics['rdm_corr_proc'].append(rdm_corr_proc)
            metrics['crossnobis_raw'].append(crossnobis_raw)
            metrics['crossnobis_proc'].append(crossnobis_proc)
            metrics['decoding_raw'].append(decoding_raw)
            metrics['decoding_proc'].append(decoding_proc)
            metrics['procrustes_disparity'].append(disparity)
            metrics['subjects'].append(subject)
            metrics['rois'].append(roi)

    # Convert to arrays
    for key in ['rdm_corr_raw', 'rdm_corr_proc', 'crossnobis_raw', 'crossnobis_proc',
                'decoding_raw', 'decoding_proc', 'procrustes_disparity']:
        metrics[key] = np.array(metrics[key])

    return metrics


def plot_distribution_comparison(metrics, output_dir):
    """
    Plot distribution comparison (Before vs After Procrustes)

    Matches the reference image format with violin plots
    """
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3)

    fig.suptitle('Raw vs Procrustes Pipeline: Distribution and Confidence Intervals',
                 fontsize=18, fontweight='bold')

    # Remove NaN values
    rdm_raw = metrics['rdm_corr_raw'][np.isfinite(metrics['rdm_corr_raw'])]
    rdm_proc = metrics['rdm_corr_proc'][np.isfinite(metrics['rdm_corr_proc'])]

    crossnobis_raw = metrics['crossnobis_raw'][np.isfinite(metrics['crossnobis_raw'])]
    crossnobis_proc = metrics['crossnobis_proc'][np.isfinite(metrics['crossnobis_proc'])]

    decoding_raw = metrics['decoding_raw'][np.isfinite(metrics['decoding_raw'])]
    decoding_proc = metrics['decoding_proc'][np.isfinite(metrics['decoding_proc'])]

    # A. RDM Correlation (Within-Subject)
    ax = fig.add_subplot(gs[0, 0])

    parts = ax.violinplot([rdm_raw, rdm_proc],
                         positions=[0, 1],
                         showmeans=True, showmedians=True,
                         widths=0.7)

    # Color the violins
    for i, pc in enumerate(parts['bodies']):
        if i == 0:
            pc.set_facecolor('#FFB6C1')  # Light red
            pc.set_alpha(0.7)
        else:
            pc.set_facecolor('#ADD8E6')  # Light blue
            pc.set_alpha(0.7)

    # Add mean and confidence interval
    mean_raw = np.mean(rdm_raw)
    mean_proc = np.mean(rdm_proc)
    ci_raw = 1.96 * np.std(rdm_raw) / np.sqrt(len(rdm_raw))
    ci_proc = 1.96 * np.std(rdm_proc) / np.sqrt(len(rdm_proc))

    ax.errorbar([0, 1], [mean_raw, mean_proc],
                yerr=[ci_raw, ci_proc],
                fmt='ko', markersize=8, capsize=10, capthick=2,
                linewidth=2, zorder=10)

    ax.axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Before\nProcrustes', 'After\nProcrustes'], fontsize=11)
    ax.set_ylabel('RDM Correlation Reliability', fontsize=12, fontweight='bold')
    ax.set_title('A. RDM Correlation (Within-Subject)', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # Add statistics text
    from scipy.stats import wilcoxon
    stat, pval = wilcoxon(rdm_raw, rdm_proc)
    pval_text = f'p={pval:.2e}' if pval < 0.001 else f'p={pval:.3f}'
    ax.text(0.5, 0.95, f'Mean ± 95% CI | Wilcoxon: {pval_text}',
            transform=ax.transAxes, ha='center', va='top',
            fontsize=9, style='italic',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='wheat',
                     edgecolor='black', alpha=0.7))

    # B. RDM Crossnobis (Mahalanobis)
    ax = fig.add_subplot(gs[0, 1])

    if len(crossnobis_raw) > 0 and len(crossnobis_proc) > 0:
        parts = ax.violinplot([crossnobis_raw, crossnobis_proc],
                             positions=[0, 1],
                             showmeans=True, showmedians=True,
                             widths=0.7)

        for i, pc in enumerate(parts['bodies']):
            if i == 0:
                pc.set_facecolor('#FFB6C1')
                pc.set_alpha(0.7)
            else:
                pc.set_facecolor('#ADD8E6')
                pc.set_alpha(0.7)

        mean_raw = np.mean(crossnobis_raw)
        mean_proc = np.mean(crossnobis_proc)
        ci_raw = 1.96 * np.std(crossnobis_raw) / np.sqrt(len(crossnobis_raw))
        ci_proc = 1.96 * np.std(crossnobis_proc) / np.sqrt(len(crossnobis_proc))

        ax.errorbar([0, 1], [mean_raw, mean_proc],
                    yerr=[ci_raw, ci_proc],
                    fmt='ko', markersize=8, capsize=10, capthick=2,
                    linewidth=2, zorder=10)

        stat, pval = wilcoxon(crossnobis_raw, crossnobis_proc)
        pval_text = f'p={pval:.2e}' if pval < 0.001 else f'p={pval:.3f}'
        ax.text(0.5, 0.95, f'Wilcoxon: {pval_text}',
                transform=ax.transAxes, ha='center', va='top',
                fontsize=9, style='italic',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='wheat',
                         edgecolor='black', alpha=0.7))

    ax.axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Before\nProcrustes', 'After\nProcrustes'], fontsize=11)
    ax.set_ylabel('RDM Crossnobis Reliability', fontsize=12, fontweight='bold')
    ax.set_title('B. RDM Crossnobis (Mahalanobis)', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # C. Decoding Accuracy (LORO)
    ax = fig.add_subplot(gs[0, 2])

    parts = ax.violinplot([decoding_raw, decoding_proc],
                         positions=[0, 1],
                         showmeans=True, showmedians=True,
                         widths=0.7)

    for i, pc in enumerate(parts['bodies']):
        if i == 0:
            pc.set_facecolor('#FFB6C1')
            pc.set_alpha(0.7)
        else:
            pc.set_facecolor('#ADD8E6')
            pc.set_alpha(0.7)

    mean_raw = np.mean(decoding_raw)
    mean_proc = np.mean(decoding_proc)
    ci_raw = 1.96 * np.std(decoding_raw) / np.sqrt(len(decoding_raw))
    ci_proc = 1.96 * np.std(decoding_proc) / np.sqrt(len(decoding_proc))

    ax.errorbar([0, 1], [mean_raw, mean_proc],
                yerr=[ci_raw, ci_proc],
                fmt='ko', markersize=8, capsize=10, capthick=2,
                linewidth=2, zorder=10)

    # Chance level
    chance = 1.0 / N_COLORS
    ax.axhline(chance, color='red', linestyle='--', linewidth=2,
               alpha=0.7, label=f'Chance ({chance*100:.1f}%)')

    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Before\nProcrustes', 'After\nProcrustes'], fontsize=11)
    ax.set_ylabel('Decoding Accuracy', fontsize=12, fontweight='bold')
    ax.set_title('C. Decoding Accuracy (LORO)', fontsize=13, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')

    stat, pval = wilcoxon(decoding_raw, decoding_proc)
    pval_text = f'p={pval:.2e}' if pval < 0.001 else f'p={pval:.3f}'
    ax.text(0.5, 0.95, f'Mean ± 95% CI | Wilcoxon: {pval_text}',
            transform=ax.transAxes, ha='center', va='top',
            fontsize=9, style='italic',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='wheat',
                     edgecolor='black', alpha=0.7))

    # D. Procrustes Effect Size
    ax = fig.add_subplot(gs[1, 0])

    # Compute effect sizes
    improvement_rdm = rdm_proc - rdm_raw
    improvement_crossnobis = crossnobis_proc - crossnobis_raw if len(crossnobis_raw) > 0 else np.array([0])
    improvement_decoding = decoding_proc - decoding_raw

    effect_sizes = [
        np.mean(improvement_rdm),
        np.mean(improvement_crossnobis),
        np.mean(improvement_decoding)
    ]

    effect_stds = [
        np.std(improvement_rdm) / np.sqrt(len(improvement_rdm)),
        np.std(improvement_crossnobis) / np.sqrt(len(improvement_crossnobis)) if len(improvement_crossnobis) > 0 else 0,
        np.std(improvement_decoding) / np.sqrt(len(improvement_decoding))
    ]

    labels = ['RDM Corr', 'RDM Xnobis', 'Decoding']
    colors = ['#ADD8E6', '#90EE90', '#DDA0DD']

    bars = ax.bar(range(3), effect_sizes, yerr=effect_stds,
                  capsize=10, color=colors, edgecolor='black',
                  linewidth=1.5, alpha=0.7)

    # Add value labels
    for i, (bar, val, std) in enumerate(zip(bars, effect_sizes, effect_stds)):
        height = bar.get_height()
        pct_improvement = (val / abs(np.mean(rdm_raw if i == 0 else (crossnobis_raw if i == 1 else decoding_raw)))) * 100
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.3f}\n({pct_improvement:.0f}%)',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.axhline(0, color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_xticks(range(3))
    ax.set_xticklabels(labels, fontsize=11)
    ax.set_ylabel('Improvement (After - Before)', fontsize=12, fontweight='bold')
    ax.set_title('D. Procrustes Effect Size', fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')

    # E. Performance by ROI
    ax = fig.add_subplot(gs[1, 1])

    roi_means_raw = []
    roi_means_proc = []
    roi_stds_raw = []
    roi_stds_proc = []

    for roi in ROIS:
        roi_mask = np.array([r == roi for r in metrics['rois']])
        roi_rdm_raw = rdm_raw[roi_mask[:len(rdm_raw)]]
        roi_rdm_proc = rdm_proc[roi_mask[:len(rdm_proc)]]

        if len(roi_rdm_raw) > 0:
            roi_means_raw.append(np.mean(roi_rdm_raw))
            roi_stds_raw.append(np.std(roi_rdm_raw) / np.sqrt(len(roi_rdm_raw)))
        else:
            roi_means_raw.append(0)
            roi_stds_raw.append(0)

        if len(roi_rdm_proc) > 0:
            roi_means_proc.append(np.mean(roi_rdm_proc))
            roi_stds_proc.append(np.std(roi_rdm_proc) / np.sqrt(len(roi_rdm_proc)))
        else:
            roi_means_proc.append(0)
            roi_stds_proc.append(0)

    x = np.arange(len(ROIS))
    width = 0.35

    ax.bar(x - width/2, roi_means_raw, width, yerr=roi_stds_raw,
           capsize=5, label='Before', color='#FFB6C1', edgecolor='black',
           linewidth=1.5, alpha=0.7)
    ax.bar(x + width/2, roi_means_proc, width, yerr=roi_stds_proc,
           capsize=5, label='After', color='#ADD8E6', edgecolor='black',
           linewidth=1.5, alpha=0.7)

    ax.set_xticks(x)
    ax.set_xticklabels(ROIS, fontsize=11)
    ax.set_ylabel('RDM Correlation', fontsize=12, fontweight='bold')
    ax.set_title('E. Performance by ROI', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')

    # F. Procrustes Disparity Distribution
    ax = fig.add_subplot(gs[1, 2])

    disparity = metrics['procrustes_disparity'][np.isfinite(metrics['procrustes_disparity'])]

    ax.hist(disparity, bins=30, edgecolor='black', alpha=0.7, color='orange')

    mean_disp = np.mean(disparity)
    median_disp = np.median(disparity)

    ax.axvline(mean_disp, color='red', linestyle='--', linewidth=2,
               label=f'Mean: {mean_disp:.1f}')
    ax.axvline(median_disp, color='blue', linestyle='--', linewidth=2,
               label=f'Median: {median_disp:.1f}')

    ax.set_xlabel('Procrustes Disparity', fontsize=12, fontweight='bold')
    ax.set_ylabel('Count', fontsize=12, fontweight='bold')
    ax.set_title('F. Anatomical Misalignment', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    iqr = np.percentile(disparity, 75) - np.percentile(disparity, 25)
    ax.text(0.98, 0.97, f'IQR: [{np.percentile(disparity, 25):.1f}, {np.percentile(disparity, 75):.1f}]',
            transform=ax.transAxes, ha='right', va='top',
            fontsize=9, style='italic',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='wheat',
                     edgecolor='black', alpha=0.7))

    plt.savefig(output_dir / 'raw_procrustes_distributions.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Saved: raw_procrustes_distributions.png")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main execution"""
    print(f"\n{'='*80}")
    print(f"Comprehensive Visualization: Raw vs Procrustes Comparison")
    print(f"{'='*80}\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load all data
    print("Loading data for all subjects and ROIs...")
    all_data = load_all_data()

    n_loaded = sum(len(rois) for rois in all_data.values())
    print(f"✓ Loaded {n_loaded} subject-ROI pairs")

    # Generate MDS color space embeddings for one example subject
    print("\n" + "="*80)
    print("Generating MDS Color Space Embeddings (Example: sub-02 V2)")
    print("="*80)

    if '02' in all_data and 'V2' in all_data['02']:
        plot_mds_color_space('02', 'V2', all_data['02']['V2'], OUTPUT_DIR)

    # Compute all metrics
    print("\n" + "="*80)
    print("Computing Metrics for Distribution Plots")
    print("="*80)

    metrics = compute_all_metrics(all_data)

    print(f"\n✓ Computed metrics for {len(metrics['rdm_corr_raw'])} subject-ROI pairs")
    print(f"  RDM Correlation (Raw): {np.nanmean(metrics['rdm_corr_raw']):.3f} ± {np.nanstd(metrics['rdm_corr_raw']):.3f}")
    print(f"  RDM Correlation (Proc): {np.nanmean(metrics['rdm_corr_proc']):.3f} ± {np.nanstd(metrics['rdm_corr_proc']):.3f}")
    print(f"  Decoding Accuracy (Raw): {np.nanmean(metrics['decoding_raw']):.3f} ± {np.nanstd(metrics['decoding_raw']):.3f}")
    print(f"  Decoding Accuracy (Proc): {np.nanmean(metrics['decoding_proc']):.3f} ± {np.nanstd(metrics['decoding_proc']):.3f}")

    # Generate distribution plots
    print("\n" + "="*80)
    print("Generating Distribution Comparison Plots")
    print("="*80)

    plot_distribution_comparison(metrics, OUTPUT_DIR)

    print(f"\n{'='*80}")
    print(f"✓ All visualizations saved to: {OUTPUT_DIR}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
