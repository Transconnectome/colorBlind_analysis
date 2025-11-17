#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_colorblind_metrics.py
------------------------------
Extract comprehensive metrics to distinguish CVD from Non-CVD individuals.

This script analyzes reconstruction results across all ROIs and extracts:
1. PCA coordinates (PC1-PC3) for each color
2. Novel color reconstruction patterns (mean angles, biases)
3. Red-Green confusion metrics (distances, discriminability)
4. Channel response profiles (6-channel model weights)
5. Color pair discriminability matrix

Usage:
    python extract_colorblind_metrics.py --subject P01
    python extract_colorblind_metrics.py --subject 01 --output-dir results/

Output:
    - {subject}_cvd_metrics_summary.txt: Human-readable summary
    - {subject}_pca_coordinates.csv: PCA coordinates per color per ROI
    - {subject}_novel_color_angles.csv: Novel color reconstruction angles
    - {subject}_channel_responses.csv: 6-channel responses per color per ROI
    - {subject}_color_pair_distances.csv: Pairwise color distances
    - {subject}_red_green_metrics.csv: Red-green specific metrics
"""

import numpy as np
import pandas as pd
import pickle
from pathlib import Path
import argparse
import sys

# ============================================================================
# Configuration
# ============================================================================

LABEL2HUE_DEG_PILOT = {
    'color_1': 182.142053052572436,
    'color_2': 287.979026187069735,
    'color_3': 305.226546308759566,
    'color_4': 330.204721787408289,
    'color_5': 35.269500805260478,
    'color_6': 73.365061454288877,
    'color_7': 125.585145639335096,
    'color_8': 143.909094545652778,
}

LABEL2HUE_DEG_TEST = {
    'color_1': 0.0,
    'color_2': 45.0,
    'color_3': 90.0,
    'color_4': 135.0,
    'color_5': 180.0,
    'color_6': 225.0,
    'color_7': 270.0,
    'color_8': 315.0,
}

# Red-Green color pairs (opposite hues, ~180° apart)
RED_GREEN_PAIRS_PILOT = [
    ('color_5', 'color_1'),   # 35° vs 182° (147° diff)
    ('color_6', 'color_1'),   # 73° vs 182° (109° diff)
]

RED_GREEN_PAIRS_TEST = [
    ('color_1', 'color_5'),   # 0° vs 180° (180° diff)
    ('color_2', 'color_6'),   # 45° vs 225° (180° diff)
]

ROIS = ['V1', 'V2', 'V3', 'hV4']

# ============================================================================
# Helper Functions
# ============================================================================

def circular_diff_deg(a, b):
    """Circular difference in degrees (0-360)"""
    diff = np.abs(a - b)
    return np.minimum(diff, 360 - diff)

def circular_mean_deg(angles_deg):
    """Calculate circular mean of angles in degrees"""
    if len(angles_deg) == 0:
        return np.nan
    ang = np.deg2rad(np.asarray(angles_deg))
    C = np.cos(ang).mean()
    S = np.sin(ang).mean()
    mean_ang = (np.rad2deg(np.arctan2(S, C)) + 360) % 360
    return mean_ang

def load_results(subject_id, roi_name, method='universal_hrf', timestamp=None):
    """
    Load results.pkl from derivatives directory

    New structure: derivatives/{timestamp}/{subject}/fir_reconstruction_uni_hrf/{roi}/results.pkl

    Parameters
    ----------
    subject_id : str
        Subject ID (P01, 01, 02, etc.)
    roi_name : str
        ROI name (V1, V2, V3, hV4)
    method : str
        Method name (universal_hrf, zScore, voxelSelect)
    timestamp : str, optional
        Specific timestamp to load. If None, uses most recent.

    Returns
    -------
    results : dict or None
        Results dict or None if not found
    """
    base_dir = Path("derivatives")

    # Determine subject path
    if subject_id == 'P01':
        subject_path = "pilot/sub-01"
    else:
        subject_path = f"sub-{subject_id}"

    # Build pattern based on method
    if method == 'universal_hrf':
        method_path = f"{roi_name}_universal_hrf"
    elif method == 'zScore':
        method_path = f"zScore/{roi_name}_universal_hrf"
    elif method == 'voxelSelect':
        method_path = f"voxelSelect/{roi_name}_universal_hrf"
    else:
        method_path = f"{roi_name}_universal_hrf"

    # If timestamp specified, use it directly
    if timestamp:
        results_file = base_dir / timestamp / subject_path / "fir_reconstruction_uni_hrf" / method_path / "results.pkl"
        if results_file.exists():
            with open(results_file, 'rb') as f:
                return pickle.load(f)
        return None

    # Otherwise, find most recent timestamp
    # Search pattern: derivatives/*/subject/fir_reconstruction_uni_hrf/method/roi/results.pkl
    pattern = f"*/{subject_path}/fir_reconstruction_uni_hrf/{method_path}/results.pkl"
    results_files = list(base_dir.glob(pattern))

    if not results_files:
        return None

    # Use most recent (sort by timestamp directory name)
    results_file = sorted(results_files)[-1]

    with open(results_file, 'rb') as f:
        results = pickle.load(f)

    return results

# ============================================================================
# Metric Extraction Functions
# ============================================================================

def extract_pca_coordinates(subject_id, rois=ROIS, n_components=3):
    """
    Extract PCA coordinates (PC1-PC3) for each color in each ROI

    Returns DataFrame with columns:
    - Subject, ROI, Color, PC1, PC2, PC3, ...
    """
    rows = []

    for roi in rois:
        results = load_results(subject_id, roi)
        if results is None:
            print(f"  Warning: No results found for {roi}")
            continue

        # Check if PCA was used
        if not results.get('use_pca', False):
            print(f"  Warning: {roi} did not use PCA")
            continue

        # We need to re-compute PCA coordinates from raw data
        # For now, we'll extract from saved PCA matrix if available
        # Otherwise, skip this ROI
        print(f"  Warning: {roi} - PCA coordinates not saved in results.pkl")
        print(f"           Need to extract from all_betas data")
        # TODO: Load all_betas and compute PCA coordinates

    df = pd.DataFrame(rows)
    return df

def extract_novel_color_angles(subject_id, rois=ROIS, timestamp=None):
    """
    Extract novel color reconstruction angles for all colors and ROIs

    Returns DataFrame with columns:
    - Subject, ROI, Color, True_Hue, Mean_Reconstructed_Hue, Mean_Error,
      Run1_Hue, Run2_Hue, ..., Run6_Hue
    """
    is_pilot = (subject_id == 'P01')
    LABEL2HUE = LABEL2HUE_DEG_PILOT if is_pilot else LABEL2HUE_DEG_TEST

    rows = []

    for roi in rois:
        results = load_results(subject_id, roi, timestamp=timestamp)
        if results is None:
            print(f"  Warning: No results found for {roi}")
            continue

        novel_color_results = results['novel_colors']['per_color']

        for result in novel_color_results:
            color_name = result['color']
            true_hue = LABEL2HUE[color_name]
            mean_error = result['mean_error']

            # All reconstructed hues across runs
            reconstructed_hues = result['reconstructed_hues']
            mean_reconstructed = circular_mean_deg(reconstructed_hues)

            row = {
                'Subject': subject_id,
                'ROI': roi,
                'Color': color_name,
                'True_Hue': true_hue,
                'Mean_Reconstructed_Hue': mean_reconstructed,
                'Mean_Error': mean_error,
            }

            # Add individual run reconstructions
            for run_idx, hue in enumerate(reconstructed_hues, 1):
                row[f'Run{run_idx}_Hue'] = hue

            rows.append(row)

    df = pd.DataFrame(rows)
    return df

def extract_channel_responses(subject_id, rois=ROIS):
    """
    Extract 6-channel response profiles for each color in each ROI

    Returns DataFrame with columns:
    - Subject, ROI, Color, True_Hue, Ch0, Ch1, Ch2, Ch3, Ch4, Ch5
    """
    # This requires access to the forward model weights and channel outputs
    # Not directly saved in results.pkl
    # TODO: Implement by loading saved model or re-computing

    print("  Warning: Channel responses not implemented yet")
    print("           Requires access to forward model weights")
    return pd.DataFrame()

def extract_color_pair_distances(subject_id, rois=ROIS, timestamp=None):
    """
    Extract pairwise color distances in reconstruction space

    For each ROI, compute distance between all color pairs based on:
    - Reconstruction angle distance
    - (TODO) PCA space Euclidean distance
    - (TODO) Channel response correlation

    Returns DataFrame with columns:
    - Subject, ROI, Color1, Color2, Angle_Distance, Mean_Error_Color1, Mean_Error_Color2
    """
    is_pilot = (subject_id == 'P01')
    LABEL2HUE = LABEL2HUE_DEG_PILOT if is_pilot else LABEL2HUE_DEG_TEST

    rows = []

    for roi in rois:
        results = load_results(subject_id, roi, timestamp=timestamp)
        if results is None:
            continue

        novel_color_results = results['novel_colors']['per_color']

        # Create lookup dict
        color_to_reconstruction = {}
        for result in novel_color_results:
            color_name = result['color']
            reconstructed_hues = result['reconstructed_hues']
            mean_reconstructed = circular_mean_deg(reconstructed_hues)
            mean_error = result['mean_error']
            color_to_reconstruction[color_name] = {
                'mean_hue': mean_reconstructed,
                'mean_error': mean_error
            }

        # Compute pairwise distances
        colors = list(color_to_reconstruction.keys())
        for i, color1 in enumerate(colors):
            for color2 in colors[i+1:]:
                hue1 = color_to_reconstruction[color1]['mean_hue']
                hue2 = color_to_reconstruction[color2]['mean_hue']

                angle_distance = circular_diff_deg(hue1, hue2)

                row = {
                    'Subject': subject_id,
                    'ROI': roi,
                    'Color1': color1,
                    'Color2': color2,
                    'True_Hue1': LABEL2HUE[color1],
                    'True_Hue2': LABEL2HUE[color2],
                    'True_Angle_Distance': circular_diff_deg(LABEL2HUE[color1], LABEL2HUE[color2]),
                    'Reconstructed_Angle_Distance': angle_distance,
                    'Mean_Error_Color1': color_to_reconstruction[color1]['mean_error'],
                    'Mean_Error_Color2': color_to_reconstruction[color2]['mean_error'],
                }

                rows.append(row)

    df = pd.DataFrame(rows)
    return df

def extract_red_green_metrics(subject_id, rois=ROIS, timestamp=None):
    """
    Extract Red-Green specific confusion metrics

    Returns DataFrame with columns:
    - Subject, ROI, Red_Color, Green_Color, True_Distance,
      Reconstructed_Distance, Compression_Ratio, Mean_Error_Red, Mean_Error_Green
    """
    is_pilot = (subject_id == 'P01')
    LABEL2HUE = LABEL2HUE_DEG_PILOT if is_pilot else LABEL2HUE_DEG_TEST
    RED_GREEN_PAIRS = RED_GREEN_PAIRS_PILOT if is_pilot else RED_GREEN_PAIRS_TEST

    rows = []

    for roi in rois:
        results = load_results(subject_id, roi, timestamp=timestamp)
        if results is None:
            continue

        novel_color_results = results['novel_colors']['per_color']

        # Create lookup dict
        color_to_reconstruction = {}
        for result in novel_color_results:
            color_name = result['color']
            reconstructed_hues = result['reconstructed_hues']
            mean_reconstructed = circular_mean_deg(reconstructed_hues)
            mean_error = result['mean_error']
            color_to_reconstruction[color_name] = {
                'mean_hue': mean_reconstructed,
                'mean_error': mean_error,
                'all_hues': reconstructed_hues
            }

        # Analyze red-green pairs
        for red_color, green_color in RED_GREEN_PAIRS:
            if red_color not in color_to_reconstruction or green_color not in color_to_reconstruction:
                continue

            # True distance
            true_hue_red = LABEL2HUE[red_color]
            true_hue_green = LABEL2HUE[green_color]
            true_distance = circular_diff_deg(true_hue_red, true_hue_green)

            # Reconstructed distance
            recon_hue_red = color_to_reconstruction[red_color]['mean_hue']
            recon_hue_green = color_to_reconstruction[green_color]['mean_hue']
            recon_distance = circular_diff_deg(recon_hue_red, recon_hue_green)

            # Compression ratio (< 1 = compressed, > 1 = expanded)
            compression_ratio = recon_distance / true_distance if true_distance > 0 else np.nan

            row = {
                'Subject': subject_id,
                'ROI': roi,
                'Red_Color': red_color,
                'Green_Color': green_color,
                'True_Hue_Red': true_hue_red,
                'True_Hue_Green': true_hue_green,
                'True_Distance': true_distance,
                'Reconstructed_Hue_Red': recon_hue_red,
                'Reconstructed_Hue_Green': recon_hue_green,
                'Reconstructed_Distance': recon_distance,
                'Compression_Ratio': compression_ratio,
                'Mean_Error_Red': color_to_reconstruction[red_color]['mean_error'],
                'Mean_Error_Green': color_to_reconstruction[green_color]['mean_error'],
            }

            rows.append(row)

    df = pd.DataFrame(rows)
    return df

def extract_classification_confusion(subject_id, rois=ROIS, timestamp=None):
    """
    Extract classification confusion patterns

    Returns DataFrame with confusion matrix entries for each ROI
    """
    is_pilot = (subject_id == 'P01')
    LABEL2HUE = LABEL2HUE_DEG_PILOT if is_pilot else LABEL2HUE_DEG_TEST

    rows = []

    for roi in rois:
        results = load_results(subject_id, roi, timestamp=timestamp)
        if results is None:
            continue

        classification_results = results['classification']['per_run']

        # Build confusion matrix
        N_COLORS = 8
        conf_matrix = np.zeros((N_COLORS, N_COLORS), dtype=int)
        for run_result in classification_results:
            for true_idx, pred_idx in zip(run_result['y_true'], run_result['y_pred']):
                conf_matrix[true_idx, pred_idx] += 1

        # Extract confusion entries
        for i in range(N_COLORS):
            for j in range(N_COLORS):
                if i == j:
                    continue  # Skip diagonal (correct classifications)

                count = conf_matrix[i, j]
                if count == 0:
                    continue  # Skip zero confusions

                color_true = f'color_{i+1}'
                color_pred = f'color_{j+1}'

                row = {
                    'Subject': subject_id,
                    'ROI': roi,
                    'True_Color': color_true,
                    'Predicted_Color': color_pred,
                    'True_Hue': LABEL2HUE[color_true],
                    'Predicted_Hue': LABEL2HUE[color_pred],
                    'Confusion_Count': count,
                    'Hue_Distance': circular_diff_deg(LABEL2HUE[color_true], LABEL2HUE[color_pred]),
                }

                rows.append(row)

    df = pd.DataFrame(rows)
    return df

# ============================================================================
# Summary Generation
# ============================================================================

def generate_summary_report(subject_id, output_dir, timestamp=None):
    """
    Generate human-readable summary report with key CVD indicators
    """
    output_file = output_dir / f"{subject_id}_cvd_metrics_summary.txt"

    with open(output_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write(f"Color Vision Deficiency (CVD) Metrics Summary\n")
        f.write(f"Subject: {subject_id}\n")
        if timestamp:
            f.write(f"Timestamp: {timestamp}\n")
        f.write("="*80 + "\n\n")

        # 1. Novel Color Reconstruction Summary
        f.write("1. NOVEL COLOR RECONSTRUCTION ANGLES (all ROIs)\n")
        f.write("-"*80 + "\n")

        df_novel = extract_novel_color_angles(subject_id, timestamp=timestamp)
        if not df_novel.empty:
            # Pivot to show all ROIs side by side
            pivot = df_novel.pivot_table(
                values='Mean_Reconstructed_Hue',
                index='Color',
                columns='ROI',
                aggfunc='first'
            )
            pivot['True_Hue'] = df_novel.groupby('Color')['True_Hue'].first()

            # Reorder columns: True_Hue first, then ROIs
            cols = ['True_Hue'] + ROIS
            pivot = pivot[[col for col in cols if col in pivot.columns]]

            f.write(pivot.to_string())
            f.write("\n\n")

            # Mean errors per ROI
            f.write("Mean Reconstruction Errors (degrees):\n")
            mean_errors = df_novel.groupby('ROI')['Mean_Error'].mean()
            for roi, error in mean_errors.items():
                f.write(f"  {roi}: {error:.2f}°\n")
        else:
            f.write("  No data available\n")

        f.write("\n\n")

        # 2. Red-Green Confusion Metrics
        f.write("2. RED-GREEN CONFUSION METRICS\n")
        f.write("-"*80 + "\n")

        df_rg = extract_red_green_metrics(subject_id, timestamp=timestamp)
        if not df_rg.empty:
            for _, row in df_rg.iterrows():
                f.write(f"\n{row['ROI']}: {row['Red_Color']} ({row['True_Hue_Red']:.1f}°) vs "
                       f"{row['Green_Color']} ({row['True_Hue_Green']:.1f}°)\n")
                f.write(f"  True distance:          {row['True_Distance']:.1f}°\n")
                f.write(f"  Reconstructed distance: {row['Reconstructed_Distance']:.1f}°\n")
                f.write(f"  Compression ratio:      {row['Compression_Ratio']:.3f} "
                       f"({'COMPRESSED' if row['Compression_Ratio'] < 0.9 else 'NORMAL' if row['Compression_Ratio'] < 1.1 else 'EXPANDED'})\n")
                f.write(f"  Mean error (red):       {row['Mean_Error_Red']:.1f}°\n")
                f.write(f"  Mean error (green):     {row['Mean_Error_Green']:.1f}°\n")
        else:
            f.write("  No data available\n")

        f.write("\n\n")

        # 3. Color Pair Distance Analysis
        f.write("3. COLOR PAIR DISTANCE COMPRESSION (Top 10 most compressed pairs)\n")
        f.write("-"*80 + "\n")

        df_pairs = extract_color_pair_distances(subject_id, timestamp=timestamp)
        if not df_pairs.empty:
            # Compute compression ratio
            df_pairs['Compression_Ratio'] = (
                df_pairs['Reconstructed_Angle_Distance'] / df_pairs['True_Angle_Distance']
            )

            # Find most compressed pairs (ratio < 1)
            compressed = df_pairs[df_pairs['Compression_Ratio'] < 1.0].copy()
            compressed = compressed.sort_values('Compression_Ratio').head(10)

            for _, row in compressed.iterrows():
                f.write(f"\n{row['ROI']}: {row['Color1']} vs {row['Color2']}\n")
                f.write(f"  True distance:    {row['True_Angle_Distance']:.1f}°\n")
                f.write(f"  Recon distance:   {row['Reconstructed_Angle_Distance']:.1f}°\n")
                f.write(f"  Compression:      {row['Compression_Ratio']:.3f}\n")
        else:
            f.write("  No data available\n")

        f.write("\n\n")

        # 4. Classification Confusion Summary
        f.write("4. CLASSIFICATION CONFUSION PATTERNS (Top 10)\n")
        f.write("-"*80 + "\n")

        df_confusion = extract_classification_confusion(subject_id, timestamp=timestamp)
        if not df_confusion.empty:
            # Sort by confusion count
            top_confusions = df_confusion.sort_values('Confusion_Count', ascending=False).head(10)

            for _, row in top_confusions.iterrows():
                f.write(f"\n{row['ROI']}: {row['True_Color']} → {row['Predicted_Color']} "
                       f"({row['Confusion_Count']} times)\n")
                f.write(f"  Hue distance: {row['Hue_Distance']:.1f}°\n")
        else:
            f.write("  No data available\n")

        f.write("\n\n")
        f.write("="*80 + "\n")
        f.write("End of Summary Report\n")
        f.write("="*80 + "\n")

    return output_file

# ============================================================================
# Main Function
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Extract CVD discrimination metrics')
    parser.add_argument('--subject', type=str, required=True,
                       help='Subject ID (P01, 01, 02, 03, 04)')
    parser.add_argument('--output-dir', type=str, default='cvd_metrics',
                       help='Output directory for metrics')
    parser.add_argument('--rois', type=str, nargs='+', default=ROIS,
                       help='ROIs to analyze (default: V1 V2 V3 hV4)')
    parser.add_argument('--timestamp', type=str, default=None,
                       help='Specific timestamp to analyze (e.g., 20250116_143022). If not specified, uses most recent.')

    args = parser.parse_args()

    subject_id = args.subject
    timestamp = args.timestamp
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("Extracting CVD Discrimination Metrics")
    print("="*80)
    print(f"Subject: {subject_id}")
    if timestamp:
        print(f"Timestamp: {timestamp}")
    else:
        print(f"Timestamp: Most recent")
    print(f"Output directory: {output_dir}")
    print()

    # 1. Extract novel color angles
    print("[1/5] Extracting novel color reconstruction angles...")
    df_novel = extract_novel_color_angles(subject_id, args.rois, timestamp=timestamp)
    if not df_novel.empty:
        output_file = output_dir / f"{subject_id}_novel_color_angles.csv"
        df_novel.to_csv(output_file, index=False)
        print(f"  Saved: {output_file}")
        print(f"  Extracted {len(df_novel)} color×ROI combinations")
    else:
        print("  No data found")
    print()

    # 2. Extract color pair distances
    print("[2/5] Extracting color pair distances...")
    df_pairs = extract_color_pair_distances(subject_id, args.rois, timestamp=timestamp)
    if not df_pairs.empty:
        output_file = output_dir / f"{subject_id}_color_pair_distances.csv"
        df_pairs.to_csv(output_file, index=False)
        print(f"  Saved: {output_file}")
        print(f"  Extracted {len(df_pairs)} color pairs")
    else:
        print("  No data found")
    print()

    # 3. Extract red-green metrics
    print("[3/5] Extracting red-green confusion metrics...")
    df_rg = extract_red_green_metrics(subject_id, args.rois, timestamp=timestamp)
    if not df_rg.empty:
        output_file = output_dir / f"{subject_id}_red_green_metrics.csv"
        df_rg.to_csv(output_file, index=False)
        print(f"  Saved: {output_file}")
        print(f"  Extracted {len(df_rg)} red-green pairs")
    else:
        print("  No data found")
    print()

    # 4. Extract classification confusion
    print("[4/5] Extracting classification confusion patterns...")
    df_confusion = extract_classification_confusion(subject_id, args.rois, timestamp=timestamp)
    if not df_confusion.empty:
        output_file = output_dir / f"{subject_id}_classification_confusion.csv"
        df_confusion.to_csv(output_file, index=False)
        print(f"  Saved: {output_file}")
        print(f"  Extracted {len(df_confusion)} confusion entries")
    else:
        print("  No data found")
    print()

    # 5. Generate summary report
    print("[5/5] Generating summary report...")
    summary_file = generate_summary_report(subject_id, output_dir, timestamp=timestamp)
    print(f"  Saved: {summary_file}")
    print()

    print("="*80)
    print("Extraction Complete!")
    print("="*80)
    print()
    print("Output files:")
    print(f"  1. {subject_id}_cvd_metrics_summary.txt - Human-readable summary")
    print(f"  2. {subject_id}_novel_color_angles.csv - Novel color reconstructions")
    print(f"  3. {subject_id}_color_pair_distances.csv - Pairwise color distances")
    print(f"  4. {subject_id}_red_green_metrics.csv - Red-green confusion metrics")
    print(f"  5. {subject_id}_classification_confusion.csv - Classification errors")
    print()

if __name__ == "__main__":
    main()
