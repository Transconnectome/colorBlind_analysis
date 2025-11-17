#!/usr/bin/env python3
"""
Detailed CVD analysis: Red-Green spectrum analysis
Focuses on color spacing preservation, PCA clustering, and angular confusion patterns
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pickle
from scipy.spatial.distance import pdist, squareform
from scipy.stats import ttest_ind, mannwhitneyu
from sklearn.metrics import pairwise_distances
import warnings
warnings.filterwarnings('ignore')

# Configuration
LOGS_DIR = Path("logs_1117")
OUTPUT_DIR = LOGS_DIR / "cvd_detailed_analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

ZSCORE_DIR = "20251118_010419"
VOXELSELECT_DIR = "20251118_012145"
SUBJECTS = ["sub-01", "sub-02", "sub-03", "sub-04"]
ROIS = ["V1", "V2", "V3", "hV4"]

NON_CVD = ["sub-01", "sub-02"]
CVD = ["sub-03", "sub-04"]

# Color mapping (TEST subjects: regular 45° spacing)
LABEL2HUE_DEG = {
    'color_1': 0.0,      # Red
    'color_2': 45.0,     # Orange
    'color_3': 90.0,     # Yellow
    'color_4': 135.0,    # Yellow-green
    'color_5': 180.0,    # Cyan (blue-green)
    'color_6': 225.0,    # Blue
    'color_7': 270.0,    # Purple
    'color_8': 315.0,    # Magenta
}

# Red-Green spectrum colors (most affected by CVD)
RED_GREEN_COLORS = ['color_1', 'color_2', 'color_3', 'color_4', 'color_5']
BLUE_YELLOW_COLORS = ['color_6', 'color_7', 'color_8']

def angular_distance(angle1, angle2):
    """Calculate minimum angular distance between two angles in degrees"""
    diff = np.abs(angle1 - angle2)
    return np.minimum(diff, 360 - diff)

def load_pickle_results(subject, roi, method):
    """Load detailed results from pickle file"""
    method_folder = "zScore" if method == "zScore" else "voxelSelect"
    timestamp = ZSCORE_DIR if method == "zScore" else VOXELSELECT_DIR

    pkl_path = (LOGS_DIR / timestamp / subject / "fir_reconstruction_uni_hrf" /
                method_folder / f"{roi}_universal_hrf" / "results.pkl")

    if pkl_path.exists():
        with open(pkl_path, 'rb') as f:
            return pickle.load(f)
    return None

def extract_color_predictions(results):
    """Extract predicted hues for each color from results"""
    if results is None or 'reconstruction' not in results:
        return None

    recon = results['reconstruction']

    # Collect predictions for training colors from all runs
    predictions = {}
    true_hues = {}

    # Initialize storage for each color
    for color_idx in range(8):
        color_name = f'color_{color_idx + 1}'
        true_hues[color_name] = LABEL2HUE_DEG[color_name]
        predictions[color_name] = []

    # Extract from per_run data
    if 'per_run' in recon:
        for run_data in recon['per_run']:
            if 'reconstructed_hues' in run_data:
                recon_hues = run_data['reconstructed_hues']
                for color_idx, pred_hue in enumerate(recon_hues):
                    if color_idx < 8:
                        color_name = f'color_{color_idx + 1}'
                        predictions[color_name].append(pred_hue)

    # Convert to numpy arrays
    for color_name in predictions:
        if predictions[color_name]:
            predictions[color_name] = np.array(predictions[color_name])
        else:
            predictions[color_name] = None

    # Extract novel color predictions if available
    novel_predictions = {}
    if 'novel_colors' in results and 'per_color' in results['novel_colors']:
        for color_data in results['novel_colors']['per_color']:
            color_name = color_data['color']
            if 'reconstructed_hues' in color_data:
                novel_predictions[color_name] = np.array(color_data['reconstructed_hues'])
            elif 'reconstructed_hue' in color_data:
                novel_predictions[color_name] = np.array([color_data['reconstructed_hue']])

    return {
        'predictions': predictions,
        'true_hues': true_hues,
        'novel_predictions': novel_predictions
    }

def analyze_color_spacing(predictions, true_hues, color_list):
    """Analyze whether color spacing is preserved"""
    if not predictions:
        return None

    # True spacing between consecutive colors
    true_spacing = []
    for i in range(len(color_list) - 1):
        c1, c2 = color_list[i], color_list[i+1]
        if c1 in true_hues and c2 in true_hues:
            spacing = angular_distance(true_hues[c1], true_hues[c2])
            true_spacing.append(spacing)

    # Predicted spacing (mean across runs)
    pred_spacing = []
    for i in range(len(color_list) - 1):
        c1, c2 = color_list[i], color_list[i+1]
        if c1 in predictions and c2 in predictions:
            mean_pred1 = np.mean(predictions[c1])
            mean_pred2 = np.mean(predictions[c2])
            spacing = angular_distance(mean_pred1, mean_pred2)
            pred_spacing.append(spacing)

    if not pred_spacing:
        return None

    # Calculate spacing preservation metric
    spacing_error = np.abs(np.array(pred_spacing) - np.array(true_spacing))

    return {
        'true_spacing': np.array(true_spacing),
        'pred_spacing': np.array(pred_spacing),
        'spacing_error': spacing_error,
        'mean_error': np.mean(spacing_error),
        'std_error': np.std(spacing_error)
    }

def extract_pca_components(results, subject, roi, method):
    """Extract or compute PCA components for each color from zmaps"""
    if results is None:
        return None

    # Try to load z-score maps and compute PCA ourselves
    method_folder = "zScore" if method == "zScore" else "voxelSelect"
    timestamp = ZSCORE_DIR if method == "zScore" else VOXELSELECT_DIR

    zmaps_dir = (LOGS_DIR / timestamp / subject / "fir_reconstruction_uni_hrf" /
                 method_folder / f"{roi}_universal_hrf" / "zmaps")

    if not zmaps_dir.exists():
        return None

    # Load z-score maps for all colors
    from sklearn.decomposition import PCA
    import nibabel as nib

    color_zscores = {}
    for color_idx in range(1, 9):
        color_name = f'color_{color_idx}'
        zmap_file = zmaps_dir / f"{color_name}_zmap.nii.gz"

        if zmap_file.exists():
            img = nib.load(zmap_file)
            data = img.get_fdata()
            # Flatten and remove zeros/nans
            flat_data = data.flatten()
            flat_data = flat_data[~np.isnan(flat_data)]
            flat_data = flat_data[flat_data != 0]

            if len(flat_data) > 0:
                color_zscores[color_name] = flat_data

    # If we have z-scores for all colors, apply PCA
    if len(color_zscores) == 8:
        # Stack into matrix (8 colors x n_voxels)
        zmat = np.array([color_zscores[f'color_{i}'] for i in range(1, 9)])

        # Ensure same number of voxels
        min_voxels = min([len(z) for z in zmat])
        zmat = np.array([z[:min_voxels] for z in zmat])

        # Apply PCA
        pca = PCA(n_components=min(6, len(zmat)))
        pca_features = pca.fit_transform(zmat)

        # Return as dict
        color_pca_features = {}
        for color_idx in range(8):
            color_name = f'color_{color_idx + 1}'
            if color_idx < len(pca_features):
                color_pca_features[color_name] = pca_features[color_idx]

        return color_pca_features

    return None

def analyze_pca_clustering(pca_features, color_groups):
    """Analyze PCA space clustering for color groups"""
    if not pca_features:
        return None

    # Separate colors by group
    group_features = {group: [] for group in color_groups.keys()}
    group_colors = {group: [] for group in color_groups.keys()}

    for group_name, colors in color_groups.items():
        for color in colors:
            if color in pca_features:
                group_features[group_name].append(pca_features[color])
                group_colors[group_name].append(color)

    # Calculate within-group and between-group distances
    results = {}

    for group_name, features in group_features.items():
        if len(features) > 1:
            features_array = np.array(features)
            # Within-group distances
            within_dist = pdist(features_array, metric='euclidean')
            results[f'{group_name}_within_mean'] = np.mean(within_dist)
            results[f'{group_name}_within_std'] = np.std(within_dist)

    # Between-group distances
    all_groups = list(group_features.keys())
    for i, group1 in enumerate(all_groups):
        for group2 in all_groups[i+1:]:
            if group_features[group1] and group_features[group2]:
                feat1 = np.array(group_features[group1])
                feat2 = np.array(group_features[group2])
                between_dist = pairwise_distances(feat1, feat2, metric='euclidean')
                results[f'{group1}_vs_{group2}_mean'] = np.mean(between_dist)
                results[f'{group1}_vs_{group2}_std'] = np.std(between_dist)

    return results

def create_color_spacing_visualization(all_data, output_file):
    """Visualize color spacing preservation for CVD vs Non-CVD"""
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('Red-Green Spectrum Color Spacing Analysis: CVD vs Non-CVD',
                 fontsize=20, fontweight='bold')

    # Organize data by group
    non_cvd_data = {roi: [] for roi in ROIS}
    cvd_data = {roi: [] for roi in ROIS}

    for key, spacing_data in all_data.items():
        if spacing_data is None:
            continue
        subject, roi, method = key

        if subject in NON_CVD:
            non_cvd_data[roi].append(spacing_data)
        else:
            cvd_data[roi].append(spacing_data)

    # Plot 1: Red-Green spacing errors by ROI
    ax1 = axes[0, 0]
    roi_positions = np.arange(len(ROIS))
    width = 0.35

    non_cvd_means = []
    cvd_means = []
    non_cvd_stds = []
    cvd_stds = []

    for roi in ROIS:
        if non_cvd_data[roi]:
            errors = [d['mean_error'] for d in non_cvd_data[roi]]
            non_cvd_means.append(np.mean(errors))
            non_cvd_stds.append(np.std(errors))
        else:
            non_cvd_means.append(0)
            non_cvd_stds.append(0)

        if cvd_data[roi]:
            errors = [d['mean_error'] for d in cvd_data[roi]]
            cvd_means.append(np.mean(errors))
            cvd_stds.append(np.std(errors))
        else:
            cvd_means.append(0)
            cvd_stds.append(0)

    ax1.bar(roi_positions - width/2, non_cvd_means, width,
            yerr=non_cvd_stds, label='Non-CVD', alpha=0.8, color='steelblue',
            capsize=5)
    ax1.bar(roi_positions + width/2, cvd_means, width,
            yerr=cvd_stds, label='CVD', alpha=0.8, color='coral',
            capsize=5)

    ax1.set_xlabel('ROI', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Mean Spacing Error (degrees)', fontsize=12, fontweight='bold')
    ax1.set_title('Red-Green Color Spacing Preservation Error', fontsize=14, fontweight='bold')
    ax1.set_xticks(roi_positions)
    ax1.set_xticklabels(ROIS)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)

    # Plot 2: Individual color pair spacing errors
    ax2 = axes[0, 1]

    # Aggregate all spacing errors by color pair
    color_pairs = [f'{RED_GREEN_COLORS[i]}-{RED_GREEN_COLORS[i+1]}'
                   for i in range(len(RED_GREEN_COLORS)-1)]

    non_cvd_pair_errors = {pair: [] for pair in color_pairs}
    cvd_pair_errors = {pair: [] for pair in color_pairs}

    for key, spacing_data in all_data.items():
        if spacing_data is None or 'spacing_error' not in spacing_data:
            continue
        subject, roi, method = key

        for i, pair in enumerate(color_pairs):
            if i < len(spacing_data['spacing_error']):
                error = spacing_data['spacing_error'][i]
                if subject in NON_CVD:
                    non_cvd_pair_errors[pair].append(error)
                else:
                    cvd_pair_errors[pair].append(error)

    pair_positions = np.arange(len(color_pairs))
    non_cvd_pair_means = [np.mean(non_cvd_pair_errors[p]) if non_cvd_pair_errors[p] else 0
                           for p in color_pairs]
    cvd_pair_means = [np.mean(cvd_pair_errors[p]) if cvd_pair_errors[p] else 0
                      for p in color_pairs]

    ax2.bar(pair_positions - width/2, non_cvd_pair_means, width,
            label='Non-CVD', alpha=0.8, color='steelblue')
    ax2.bar(pair_positions + width/2, cvd_pair_means, width,
            label='CVD', alpha=0.8, color='coral')

    ax2.set_xlabel('Color Pair', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Mean Spacing Error (degrees)', fontsize=12, fontweight='bold')
    ax2.set_title('Spacing Error by Color Pair', fontsize=14, fontweight='bold')
    ax2.set_xticks(pair_positions)
    ax2.set_xticklabels([f'C{i+1}-{i+2}' for i in range(len(color_pairs))], rotation=45)
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)

    # Plot 3: Distribution of spacing errors
    ax3 = axes[1, 0]

    all_non_cvd_errors = []
    all_cvd_errors = []

    for key, spacing_data in all_data.items():
        if spacing_data is None or 'spacing_error' not in spacing_data:
            continue
        subject, roi, method = key

        if subject in NON_CVD:
            all_non_cvd_errors.extend(spacing_data['spacing_error'])
        else:
            all_cvd_errors.extend(spacing_data['spacing_error'])

    if all_non_cvd_errors:
        ax3.hist(all_non_cvd_errors, bins=30, alpha=0.6, label='Non-CVD',
                 color='steelblue', edgecolor='black')
    if all_cvd_errors:
        ax3.hist(all_cvd_errors, bins=30, alpha=0.6, label='CVD',
                 color='coral', edgecolor='black')

    ax3.set_xlabel('Spacing Error (degrees)', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax3.set_title('Distribution of Spacing Errors', fontsize=14, fontweight='bold')
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)

    # Plot 4: True vs Predicted spacing
    ax4 = axes[1, 1]

    true_spacings_non_cvd = []
    pred_spacings_non_cvd = []
    true_spacings_cvd = []
    pred_spacings_cvd = []

    for key, spacing_data in all_data.items():
        if spacing_data is None:
            continue
        subject, roi, method = key

        if 'true_spacing' in spacing_data and 'pred_spacing' in spacing_data:
            if subject in NON_CVD:
                true_spacings_non_cvd.extend(spacing_data['true_spacing'])
                pred_spacings_non_cvd.extend(spacing_data['pred_spacing'])
            else:
                true_spacings_cvd.extend(spacing_data['true_spacing'])
                pred_spacings_cvd.extend(spacing_data['pred_spacing'])

    if true_spacings_non_cvd:
        ax4.scatter(true_spacings_non_cvd, pred_spacings_non_cvd,
                   alpha=0.6, s=100, label='Non-CVD', color='steelblue', edgecolors='black')
    if true_spacings_cvd:
        ax4.scatter(true_spacings_cvd, pred_spacings_cvd,
                   alpha=0.6, s=100, label='CVD', color='coral', edgecolors='black', marker='s')

    # Add diagonal line (perfect prediction)
    max_val = max(max(true_spacings_non_cvd + true_spacings_cvd, default=45),
                  max(pred_spacings_non_cvd + pred_spacings_cvd, default=45))
    ax4.plot([0, max_val], [0, max_val], 'k--', alpha=0.5, linewidth=2, label='Perfect prediction')

    ax4.set_xlabel('True Spacing (degrees)', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Predicted Spacing (degrees)', fontsize=12, fontweight='bold')
    ax4.set_title('True vs Predicted Color Spacing', fontsize=14, fontweight='bold')
    ax4.legend()
    ax4.grid(alpha=0.3)
    ax4.set_aspect('equal')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

def create_pca_clustering_visualization(all_pca_data, output_file):
    """Visualize PCA space clustering for CVD vs Non-CVD"""
    fig = plt.figure(figsize=(24, 18))
    gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)

    fig.suptitle('PCA Space Analysis: Red-Green vs Blue-Yellow Clustering',
                 fontsize=24, fontweight='bold')

    # For each ROI, plot PCA space for Non-CVD and CVD
    for roi_idx, roi in enumerate(ROIS):
        # Non-CVD subplot
        ax_non_cvd = fig.add_subplot(gs[roi_idx // 2, (roi_idx % 2) * 2])
        ax_cvd = fig.add_subplot(gs[roi_idx // 2, (roi_idx % 2) * 2 + 1])

        # Collect data for this ROI
        for subject in SUBJECTS:
            group = 'Non-CVD' if subject in NON_CVD else 'CVD'
            ax = ax_non_cvd if group == 'Non-CVD' else ax_cvd

            for method in ['zScore', 'voxelSelect']:
                key = (subject, roi, method)
                if key not in all_pca_data or all_pca_data[key] is None:
                    continue

                pca_features = all_pca_data[key]

                # Plot red-green colors
                rg_colors = []
                rg_features = []
                for color in RED_GREEN_COLORS:
                    if color in pca_features:
                        rg_colors.append(color)
                        rg_features.append(pca_features[color])

                if rg_features:
                    rg_features = np.array(rg_features)
                    # Plot PC1 vs PC2
                    marker = 'o' if method == 'zScore' else 's'
                    alpha = 0.7 if subject == SUBJECTS[0] or subject == SUBJECTS[2] else 0.4
                    ax.scatter(rg_features[:, 0], rg_features[:, 1],
                             c='red', marker=marker, s=150, alpha=alpha,
                             edgecolors='black', linewidths=1.5,
                             label=f'{subject}-{method}-RG' if roi_idx == 0 else '')

                # Plot blue-yellow colors
                by_colors = []
                by_features = []
                for color in BLUE_YELLOW_COLORS:
                    if color in pca_features:
                        by_colors.append(color)
                        by_features.append(pca_features[color])

                if by_features:
                    by_features = np.array(by_features)
                    marker = 'o' if method == 'zScore' else 's'
                    alpha = 0.7 if subject == SUBJECTS[0] or subject == SUBJECTS[2] else 0.4
                    ax.scatter(by_features[:, 0], by_features[:, 1],
                             c='blue', marker=marker, s=150, alpha=alpha,
                             edgecolors='black', linewidths=1.5,
                             label=f'{subject}-{method}-BY' if roi_idx == 0 else '')

        ax_non_cvd.set_xlabel('PC1', fontsize=11, fontweight='bold')
        ax_non_cvd.set_ylabel('PC2', fontsize=11, fontweight='bold')
        ax_non_cvd.set_title(f'{roi} - Non-CVD', fontsize=13, fontweight='bold')
        ax_non_cvd.grid(alpha=0.3)

        ax_cvd.set_xlabel('PC1', fontsize=11, fontweight='bold')
        ax_cvd.set_ylabel('PC2', fontsize=11, fontweight='bold')
        ax_cvd.set_title(f'{roi} - CVD', fontsize=13, fontweight='bold')
        ax_cvd.grid(alpha=0.3)

    # Add distance comparison subplot
    ax_dist = fig.add_subplot(gs[2, :])

    # Calculate clustering metrics for all conditions
    metrics_data = []

    for key, pca_features in all_pca_data.items():
        if pca_features is None:
            continue

        subject, roi, method = key
        group = 'Non-CVD' if subject in NON_CVD else 'CVD'

        color_groups = {
            'red_green': RED_GREEN_COLORS,
            'blue_yellow': BLUE_YELLOW_COLORS
        }

        clustering_metrics = analyze_pca_clustering(pca_features, color_groups)

        if clustering_metrics:
            # Extract within-group distances
            rg_within = clustering_metrics.get('red_green_within_mean', np.nan)
            by_within = clustering_metrics.get('blue_yellow_within_mean', np.nan)
            between = clustering_metrics.get('red_green_vs_blue_yellow_mean', np.nan)

            metrics_data.append({
                'Subject': subject,
                'ROI': roi,
                'Method': method,
                'Group': group,
                'RG_within': rg_within,
                'BY_within': by_within,
                'Between': between,
                'Separation_ratio': between / ((rg_within + by_within) / 2) if not np.isnan(rg_within) and not np.isnan(by_within) else np.nan
            })

    if metrics_data:
        df_metrics = pd.DataFrame(metrics_data)

        # Plot separation ratios
        non_cvd_ratios = df_metrics[df_metrics['Group'] == 'Non-CVD']['Separation_ratio'].dropna()
        cvd_ratios = df_metrics[df_metrics['Group'] == 'CVD']['Separation_ratio'].dropna()

        positions = [1, 2]
        bp = ax_dist.boxplot([non_cvd_ratios, cvd_ratios],
                             positions=positions,
                             widths=0.6,
                             patch_artist=True,
                             labels=['Non-CVD', 'CVD'])

        bp['boxes'][0].set_facecolor('steelblue')
        bp['boxes'][1].set_facecolor('coral')

        ax_dist.set_ylabel('Separation Ratio\n(Between / Within distance)',
                          fontsize=12, fontweight='bold')
        ax_dist.set_title('PCA Space Clustering Quality: Red-Green vs Blue-Yellow Separation',
                         fontsize=14, fontweight='bold')
        ax_dist.grid(axis='y', alpha=0.3)

        # Add statistical test
        if len(non_cvd_ratios) > 0 and len(cvd_ratios) > 0:
            stat, pval = mannwhitneyu(non_cvd_ratios, cvd_ratios, alternative='two-sided')
            ax_dist.text(0.5, 0.95, f'Mann-Whitney U test: p = {pval:.4f}',
                        transform=ax_dist.transAxes, ha='center', va='top',
                        fontsize=11, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

def create_angular_confusion_analysis(all_predictions, output_file):
    """Analyze red-green angular confusion patterns"""
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('Red-Green Angular Confusion Analysis',
                 fontsize=20, fontweight='bold')

    # Collect all prediction errors
    non_cvd_rg_errors = {color: [] for color in RED_GREEN_COLORS}
    cvd_rg_errors = {color: [] for color in RED_GREEN_COLORS}

    for key, pred_data in all_predictions.items():
        if pred_data is None or 'predictions' not in pred_data:
            continue

        subject, roi, method = key
        predictions = pred_data['predictions']
        true_hues = pred_data['true_hues']

        for color in RED_GREEN_COLORS:
            if color not in predictions or color not in true_hues:
                continue

            # Calculate errors
            pred_hues = predictions[color]
            true_hue = true_hues[color]
            errors = [angular_distance(p, true_hue) for p in pred_hues]

            if subject in NON_CVD:
                non_cvd_rg_errors[color].extend(errors)
            else:
                cvd_rg_errors[color].extend(errors)

    # Plot 1: Error by color
    ax1 = axes[0, 0]
    color_positions = np.arange(len(RED_GREEN_COLORS))
    width = 0.35

    non_cvd_means = [np.mean(non_cvd_rg_errors[c]) if non_cvd_rg_errors[c] else 0
                     for c in RED_GREEN_COLORS]
    cvd_means = [np.mean(cvd_rg_errors[c]) if cvd_rg_errors[c] else 0
                 for c in RED_GREEN_COLORS]

    ax1.bar(color_positions - width/2, non_cvd_means, width,
            label='Non-CVD', alpha=0.8, color='steelblue')
    ax1.bar(color_positions + width/2, cvd_means, width,
            label='CVD', alpha=0.8, color='coral')

    ax1.set_xlabel('Color', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Mean Angular Error (degrees)', fontsize=12, fontweight='bold')
    ax1.set_title('Reconstruction Error: Red-Green Spectrum', fontsize=14, fontweight='bold')
    ax1.set_xticks(color_positions)
    ax1.set_xticklabels([f'C{i+1}\n{int(LABEL2HUE_DEG[c])}°' for i, c in enumerate(RED_GREEN_COLORS)])
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)

    # Plot 2: Confusion matrix (which colors are confused with which)
    ax2 = axes[0, 1]

    # Create confusion matrix for CVD subjects
    confusion_matrix = np.zeros((len(RED_GREEN_COLORS), len(RED_GREEN_COLORS)))

    for key, pred_data in all_predictions.items():
        if pred_data is None or 'predictions' not in pred_data:
            continue

        subject, roi, method = key
        if subject not in CVD:
            continue

        predictions = pred_data['predictions']
        true_hues = pred_data['true_hues']

        for i, true_color in enumerate(RED_GREEN_COLORS):
            if true_color not in predictions:
                continue

            pred_hues = predictions[true_color]

            # For each prediction, find closest color
            for pred_hue in pred_hues:
                closest_idx = 0
                min_dist = float('inf')

                for j, target_color in enumerate(RED_GREEN_COLORS):
                    target_hue = LABEL2HUE_DEG[target_color]
                    dist = angular_distance(pred_hue, target_hue)
                    if dist < min_dist:
                        min_dist = dist
                        closest_idx = j

                confusion_matrix[i, closest_idx] += 1

    # Normalize by row
    row_sums = confusion_matrix.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1  # Avoid division by zero
    confusion_matrix_norm = confusion_matrix / row_sums

    sns.heatmap(confusion_matrix_norm, annot=True, fmt='.2f', cmap='RdYlGn_r',
                ax=ax2, cbar_kws={'label': 'Confusion Probability'},
                xticklabels=[f'C{i+1}' for i in range(len(RED_GREEN_COLORS))],
                yticklabels=[f'C{i+1}' for i in range(len(RED_GREEN_COLORS))])
    ax2.set_xlabel('Predicted Color', fontsize=12, fontweight='bold')
    ax2.set_ylabel('True Color', fontsize=12, fontweight='bold')
    ax2.set_title('CVD Red-Green Confusion Matrix', fontsize=14, fontweight='bold')

    # Plot 3: Error distribution comparison
    ax3 = axes[1, 0]

    all_non_cvd = []
    all_cvd = []
    for color in RED_GREEN_COLORS:
        all_non_cvd.extend(non_cvd_rg_errors[color])
        all_cvd.extend(cvd_rg_errors[color])

    if all_non_cvd:
        ax3.hist(all_non_cvd, bins=40, alpha=0.6, label='Non-CVD',
                 color='steelblue', edgecolor='black', density=True)
    if all_cvd:
        ax3.hist(all_cvd, bins=40, alpha=0.6, label='CVD',
                 color='coral', edgecolor='black', density=True)

    ax3.set_xlabel('Angular Error (degrees)', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Density', fontsize=12, fontweight='bold')
    ax3.set_title('Error Distribution: Red-Green Colors', fontsize=14, fontweight='bold')
    ax3.legend()
    ax3.grid(axis='y', alpha=0.3)

    # Plot 4: Per-color violin plots
    ax4 = axes[1, 1]

    plot_data = []
    for color in RED_GREEN_COLORS:
        for error in non_cvd_rg_errors[color]:
            plot_data.append({
                'Color': color.replace('color_', 'C'),
                'Error': error,
                'Group': 'Non-CVD'
            })
        for error in cvd_rg_errors[color]:
            plot_data.append({
                'Color': color.replace('color_', 'C'),
                'Error': error,
                'Group': 'CVD'
            })

    if plot_data:
        df_plot = pd.DataFrame(plot_data)
        sns.violinplot(data=df_plot, x='Color', y='Error', hue='Group',
                      palette={'Non-CVD': 'steelblue', 'CVD': 'coral'},
                      ax=ax4, split=True, inner='quartile')
        ax4.set_xlabel('Color', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Angular Error (degrees)', fontsize=12, fontweight='bold')
        ax4.set_title('Error Distribution by Color', fontsize=14, fontweight='bold')
        ax4.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

def generate_detailed_statistics(spacing_data, pca_data, prediction_data):
    """Generate detailed statistical comparison"""

    print("\n" + "="*80)
    print("DETAILED CVD ANALYSIS: RED-GREEN SPECTRUM")
    print("="*80)

    # 1. Color Spacing Analysis
    print("\n1. COLOR SPACING PRESERVATION")
    print("-" * 80)

    non_cvd_spacing_errors = []
    cvd_spacing_errors = []

    for key, data in spacing_data.items():
        if data is None:
            continue
        subject, roi, method = key

        if subject in NON_CVD:
            non_cvd_spacing_errors.append(data['mean_error'])
        else:
            cvd_spacing_errors.append(data['mean_error'])

    if non_cvd_spacing_errors and cvd_spacing_errors:
        print(f"Non-CVD spacing error: {np.mean(non_cvd_spacing_errors):.2f} ± {np.std(non_cvd_spacing_errors):.2f}°")
        print(f"CVD spacing error: {np.mean(cvd_spacing_errors):.2f} ± {np.std(cvd_spacing_errors):.2f}°")

        stat, pval = mannwhitneyu(non_cvd_spacing_errors, cvd_spacing_errors)
        print(f"Mann-Whitney U test: U = {stat:.2f}, p = {pval:.4f}")

        effect_size = (np.mean(cvd_spacing_errors) - np.mean(non_cvd_spacing_errors)) / np.std(non_cvd_spacing_errors + cvd_spacing_errors)
        print(f"Effect size (Cohen's d): {effect_size:.3f}")

    # 2. PCA Clustering Analysis
    print("\n2. PCA CLUSTERING ANALYSIS")
    print("-" * 80)

    non_cvd_sep_ratios = []
    cvd_sep_ratios = []

    for key, pca_features in pca_data.items():
        if pca_features is None:
            continue

        subject, roi, method = key

        color_groups = {
            'red_green': RED_GREEN_COLORS,
            'blue_yellow': BLUE_YELLOW_COLORS
        }

        clustering_metrics = analyze_pca_clustering(pca_features, color_groups)

        if clustering_metrics:
            rg_within = clustering_metrics.get('red_green_within_mean', np.nan)
            by_within = clustering_metrics.get('blue_yellow_within_mean', np.nan)
            between = clustering_metrics.get('red_green_vs_blue_yellow_mean', np.nan)

            if not np.isnan(rg_within) and not np.isnan(by_within) and not np.isnan(between):
                sep_ratio = between / ((rg_within + by_within) / 2)

                if subject in NON_CVD:
                    non_cvd_sep_ratios.append(sep_ratio)
                else:
                    cvd_sep_ratios.append(sep_ratio)

    if non_cvd_sep_ratios and cvd_sep_ratios:
        print(f"Non-CVD separation ratio: {np.mean(non_cvd_sep_ratios):.3f} ± {np.std(non_cvd_sep_ratios):.3f}")
        print(f"CVD separation ratio: {np.mean(cvd_sep_ratios):.3f} ± {np.std(cvd_sep_ratios):.3f}")
        print(f"(Higher ratio = better separation between red-green and blue-yellow clusters)")

        stat, pval = mannwhitneyu(non_cvd_sep_ratios, cvd_sep_ratios)
        print(f"Mann-Whitney U test: U = {stat:.2f}, p = {pval:.4f}")

    # 3. Angular Error Analysis
    print("\n3. RED-GREEN ANGULAR ERROR ANALYSIS")
    print("-" * 80)

    for color in RED_GREEN_COLORS:
        non_cvd_errors = []
        cvd_errors = []

        for key, pred_data in prediction_data.items():
            if pred_data is None or 'predictions' not in pred_data:
                continue

            subject, roi, method = key
            predictions = pred_data['predictions']
            true_hues = pred_data['true_hues']

            if color not in predictions or color not in true_hues:
                continue

            pred_hues = predictions[color]
            true_hue = true_hues[color]
            errors = [angular_distance(p, true_hue) for p in pred_hues]

            if subject in NON_CVD:
                non_cvd_errors.extend(errors)
            else:
                cvd_errors.extend(errors)

        if non_cvd_errors and cvd_errors:
            hue = int(LABEL2HUE_DEG[color])
            print(f"\n{color} ({hue}°):")
            print(f"  Non-CVD: {np.mean(non_cvd_errors):.2f} ± {np.std(non_cvd_errors):.2f}°")
            print(f"  CVD: {np.mean(cvd_errors):.2f} ± {np.std(cvd_errors):.2f}°")

            stat, pval = mannwhitneyu(non_cvd_errors, cvd_errors)
            print(f"  Mann-Whitney U: p = {pval:.4f}")

    print("\n" + "="*80)

def main():
    """Main analysis pipeline"""

    print("\n" + "="*80)
    print("DETAILED CVD ANALYSIS: RED-GREEN SPECTRUM")
    print("="*80 + "\n")

    # Collect all data
    all_spacing_data = {}
    all_pca_data = {}
    all_prediction_data = {}

    print("Loading detailed results from pickle files...")
    for subject in SUBJECTS:
        for roi in ROIS:
            for method in ['zScore', 'voxelSelect']:
                results = load_pickle_results(subject, roi, method)

                if results is None:
                    continue

                key = (subject, roi, method)

                # Extract prediction data
                pred_data = extract_color_predictions(results)
                if pred_data and pred_data['predictions']:
                    all_prediction_data[key] = pred_data

                    # Analyze spacing
                    spacing_analysis = analyze_color_spacing(
                        pred_data['predictions'],
                        pred_data['true_hues'],
                        RED_GREEN_COLORS
                    )
                    all_spacing_data[key] = spacing_analysis

                # Extract PCA features
                pca_features = extract_pca_components(results, subject, roi, method)
                if pca_features:
                    all_pca_data[key] = pca_features

                print(f"✓ Loaded: {subject} - {roi} - {method}")

    print(f"\n✓ Loaded {len(all_prediction_data)} complete datasets\n")

    # Create visualizations
    print("Creating visualizations...")

    print("1. Color spacing analysis...")
    create_color_spacing_visualization(
        all_spacing_data,
        OUTPUT_DIR / "cvd_color_spacing_analysis.png"
    )

    print("2. PCA clustering analysis...")
    create_pca_clustering_visualization(
        all_pca_data,
        OUTPUT_DIR / "cvd_pca_clustering_analysis.png"
    )

    print("3. Angular confusion analysis...")
    create_angular_confusion_analysis(
        all_prediction_data,
        OUTPUT_DIR / "cvd_angular_confusion_analysis.png"
    )

    # Generate statistics
    print("\nGenerating detailed statistics...")
    generate_detailed_statistics(all_spacing_data, all_pca_data, all_prediction_data)

    print("\n" + "="*80)
    print(f"✓ DETAILED CVD ANALYSIS COMPLETE!")
    print(f"Results saved to: {OUTPUT_DIR}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
