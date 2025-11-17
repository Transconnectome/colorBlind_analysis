#!/usr/bin/env python3
"""
Comprehensive analysis of fMRI color decoding results
Comparing zScore vs voxelSelect methods across subjects and ROIs
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import pickle
from PIL import Image

# Configuration
LOGS_DIR = Path("logs_1117")
OUTPUT_DIR = LOGS_DIR / "comprehensive_analysis"
OUTPUT_DIR.mkdir(exist_ok=True)

# Analysis configurations
ZSCORE_DIR = "20251118_010419"
VOXELSELECT_DIR = "20251118_012145"
SUBJECTS = ["sub-01", "sub-02", "sub-03", "sub-04"]
ROIS = ["V1", "V2", "V3", "hV4"]

# Subject groups
NON_CVD = ["sub-01", "sub-02"]
CVD = ["sub-03", "sub-04"]

def collect_all_summaries():
    """Collect all summary.csv files into a single DataFrame"""
    all_results = []

    for method, method_dir in [("zScore", ZSCORE_DIR), ("voxelSelect", VOXELSELECT_DIR)]:
        method_path = LOGS_DIR / method_dir

        for subject in SUBJECTS:
            # Determine folder name based on method
            if method == "zScore":
                base_path = method_path / subject / "fir_reconstruction_uni_hrf" / "zScore"
            else:
                base_path = method_path / subject / "fir_reconstruction_uni_hrf" / "voxelSelect"

            for roi in ROIS:
                roi_path = base_path / f"{roi}_universal_hrf"
                summary_file = roi_path / "summary.csv"

                if summary_file.exists():
                    df = pd.read_csv(summary_file)
                    df['Subject'] = subject
                    df['ROI'] = roi
                    df['Method'] = method
                    df['Group'] = 'Non-CVD' if subject in NON_CVD else 'CVD'
                    all_results.append(df)
                    print(f"✓ Loaded: {subject} - {roi} - {method}")
                else:
                    print(f"✗ Missing: {summary_file}")

    if not all_results:
        raise ValueError("No summary files found!")

    return pd.concat(all_results, ignore_index=True)

def create_accuracy_comparison_plot(df):
    """Create comprehensive accuracy comparison plots"""
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    fig.suptitle('Classification and Reconstruction Performance Comparison',
                 fontsize=20, fontweight='bold', y=0.995)

    # 1. Classification accuracy by subject and ROI
    ax1 = axes[0, 0]
    data_class = df.pivot_table(values='Classification_accuracy',
                                 index=['Subject', 'ROI'],
                                 columns='Method')
    x = np.arange(len(data_class))
    width = 0.35

    ax1.bar(x - width/2, data_class['zScore'], width,
            label='zScore (All voxels)', alpha=0.8, color='steelblue')
    ax1.bar(x + width/2, data_class['voxelSelect'], width,
            label='voxelSelect (Selected voxels)', alpha=0.8, color='coral')

    ax1.set_xlabel('Subject - ROI', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Classification Accuracy', fontsize=12, fontweight='bold')
    ax1.set_title('Classification Accuracy Comparison', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"{s}\n{r}" for s, r in data_class.index],
                        rotation=45, ha='right', fontsize=9)
    ax1.legend(fontsize=11)
    ax1.grid(axis='y', alpha=0.3)
    ax1.set_ylim([0, 1])

    # Add chance level line
    ax1.axhline(y=1/8, color='red', linestyle='--', alpha=0.5, label='Chance (12.5%)')

    # 2. Reconstruction error by subject and ROI (lower is better)
    ax2 = axes[0, 1]
    data_recon = df.pivot_table(values='Reconstruction_error_deg',
                                index=['Subject', 'ROI'],
                                columns='Method')

    ax2.bar(x - width/2, data_recon['zScore'], width,
            label='zScore', alpha=0.8, color='steelblue')
    ax2.bar(x + width/2, data_recon['voxelSelect'], width,
            label='voxelSelect', alpha=0.8, color='coral')

    ax2.set_xlabel('Subject - ROI', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Reconstruction Error (degrees)', fontsize=12, fontweight='bold')
    ax2.set_title('Reconstruction Error Comparison (lower is better)', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"{s}\n{r}" for s, r in data_recon.index],
                        rotation=45, ha='right', fontsize=9)
    ax2.legend(fontsize=11)
    ax2.grid(axis='y', alpha=0.3)
    ax2.set_ylim([0, max(180, data_recon.max().max() * 1.1)])

    # 3. Group comparison (Non-CVD vs CVD)
    ax3 = axes[1, 0]
    group_data = df.groupby(['Group', 'ROI', 'Method'])[
        ['Classification_accuracy', 'Reconstruction_error_deg']].mean().reset_index()

    x_group = np.arange(len(ROIS))
    width_group = 0.2

    for i, group in enumerate(['Non-CVD', 'CVD']):
        for j, method in enumerate(['zScore', 'voxelSelect']):
            data_subset = group_data[(group_data['Group'] == group) &
                                     (group_data['Method'] == method)]
            offset = (i * 2 + j - 1.5) * width_group
            color = 'steelblue' if method == 'zScore' else 'coral'
            alpha = 0.9 if group == 'Non-CVD' else 0.5
            ax3.bar(x_group + offset,
                   data_subset['Classification_accuracy'].values,
                   width_group,
                   label=f'{group} - {method}',
                   alpha=alpha,
                   color=color,
                   edgecolor='black' if group == 'CVD' else 'none',
                   linewidth=1.5 if group == 'CVD' else 0)

    ax3.set_xlabel('ROI', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Classification Accuracy', fontsize=12, fontweight='bold')
    ax3.set_title('Group Comparison: Non-CVD vs CVD', fontsize=14, fontweight='bold')
    ax3.set_xticks(x_group)
    ax3.set_xticklabels(ROIS, fontsize=11)
    ax3.legend(fontsize=9, ncol=2)
    ax3.grid(axis='y', alpha=0.3)
    ax3.set_ylim([0, 1])
    ax3.axhline(y=1/8, color='red', linestyle='--', alpha=0.5)

    # 4. ROI hierarchy analysis
    ax4 = axes[1, 1]
    roi_data = df.groupby(['ROI', 'Method'])[
        ['Classification_accuracy', 'Reconstruction_error_deg']].mean().reset_index()

    x_roi = np.arange(len(ROIS))
    for i, method in enumerate(['zScore', 'voxelSelect']):
        data_subset = roi_data[roi_data['Method'] == method]
        offset = (i - 0.5) * width
        color = 'steelblue' if method == 'zScore' else 'coral'
        ax4.bar(x_roi + offset,
               data_subset['Classification_accuracy'].values,
               width,
               label=f'{method}',
               alpha=0.8,
               color=color)

    ax4.set_xlabel('ROI (Visual Hierarchy)', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Average Classification Accuracy', fontsize=12, fontweight='bold')
    ax4.set_title('ROI Hierarchy Analysis (All Subjects)', fontsize=14, fontweight='bold')
    ax4.set_xticks(x_roi)
    ax4.set_xticklabels(ROIS, fontsize=11)
    ax4.legend(fontsize=11)
    ax4.grid(axis='y', alpha=0.3)
    ax4.set_ylim([0, 1])
    ax4.axhline(y=1/8, color='red', linestyle='--', alpha=0.5)

    plt.tight_layout()
    output_file = OUTPUT_DIR / "comprehensive_accuracy_comparison.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    return output_file

def create_hrf_grid(method, method_dir):
    """Create comprehensive HRF visualization grid"""
    fig, axes = plt.subplots(len(SUBJECTS), len(ROIS),
                            figsize=(24, 6*len(SUBJECTS)))

    folder_name = "zScore" if method == "zScore" else "voxelSelect"
    fig.suptitle(f'Universal HRF Across All Subjects and ROIs ({method})',
                 fontsize=24, fontweight='bold', y=0.995)

    for i, subject in enumerate(SUBJECTS):
        for j, roi in enumerate(ROIS):
            ax = axes[i, j]

            # Construct path
            base_path = LOGS_DIR / method_dir / subject / "fir_reconstruction_uni_hrf" / folder_name
            hrf_file = base_path / f"{roi}_universal_hrf" / "figures" / f"{roi}_universal_hrf.png"

            if hrf_file.exists():
                img = Image.open(hrf_file)
                ax.imshow(img)
                ax.axis('off')

                # Add title
                group = "Non-CVD" if subject in NON_CVD else "CVD"
                ax.set_title(f"{subject} ({group}) - {roi}",
                           fontsize=14, fontweight='bold', pad=10)
            else:
                ax.text(0.5, 0.5, f"Missing:\n{subject} - {roi}",
                       ha='center', va='center', fontsize=12)
                ax.axis('off')

    plt.tight_layout()
    output_file = OUTPUT_DIR / f"comprehensive_hrf_{method}.png"
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    return output_file

def create_color_wheel_grid(method, method_dir):
    """Create comprehensive color preference wheel visualization grid"""
    fig, axes = plt.subplots(len(SUBJECTS), len(ROIS),
                            figsize=(24, 6*len(SUBJECTS)))

    folder_name = "zScore" if method == "zScore" else "voxelSelect"
    fig.suptitle(f'Color Preference Wheel Across All Subjects and ROIs ({method})',
                 fontsize=24, fontweight='bold', y=0.995)

    for i, subject in enumerate(SUBJECTS):
        for j, roi in enumerate(ROIS):
            ax = axes[i, j]

            # Construct path
            base_path = LOGS_DIR / method_dir / subject / "fir_reconstruction_uni_hrf" / folder_name
            wheel_file = base_path / f"{roi}_universal_hrf" / "figures" / f"{roi}_color_preference_wheel.png"

            if wheel_file.exists():
                img = Image.open(wheel_file)
                ax.imshow(img)
                ax.axis('off')

                # Add title
                group = "Non-CVD" if subject in NON_CVD else "CVD"
                ax.set_title(f"{subject} ({group}) - {roi}",
                           fontsize=14, fontweight='bold', pad=10)
            else:
                ax.text(0.5, 0.5, f"Missing:\n{subject} - {roi}",
                       ha='center', va='center', fontsize=12)
                ax.axis('off')

    plt.tight_layout()
    output_file = OUTPUT_DIR / f"comprehensive_color_wheel_{method}.png"
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    return output_file

def create_circular_space_grid(method, method_dir):
    """Create comprehensive circular color space visualization grid"""
    fig, axes = plt.subplots(len(SUBJECTS), len(ROIS),
                            figsize=(24, 6*len(SUBJECTS)))

    folder_name = "zScore" if method == "zScore" else "voxelSelect"
    fig.suptitle(f'Circular Color Space Reconstruction ({method})',
                 fontsize=24, fontweight='bold', y=0.995)

    for i, subject in enumerate(SUBJECTS):
        for j, roi in enumerate(ROIS):
            ax = axes[i, j]

            # Construct path
            base_path = LOGS_DIR / method_dir / subject / "fir_reconstruction_uni_hrf" / folder_name
            space_file = base_path / f"{roi}_universal_hrf" / "figures" / f"{roi}_circular_color_space.png"

            if space_file.exists():
                img = Image.open(space_file)
                ax.imshow(img)
                ax.axis('off')

                # Add title
                group = "Non-CVD" if subject in NON_CVD else "CVD"
                ax.set_title(f"{subject} ({group}) - {roi}",
                           fontsize=14, fontweight='bold', pad=10)
            else:
                ax.text(0.5, 0.5, f"Missing:\n{subject} - {roi}",
                       ha='center', va='center', fontsize=12)
                ax.axis('off')

    plt.tight_layout()
    output_file = OUTPUT_DIR / f"comprehensive_circular_space_{method}.png"
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    return output_file

def create_confusion_matrix_grid(method, method_dir):
    """Create comprehensive confusion matrix visualization grid"""
    fig, axes = plt.subplots(len(SUBJECTS), len(ROIS),
                            figsize=(24, 6*len(SUBJECTS)))

    folder_name = "zScore" if method == "zScore" else "voxelSelect"
    fig.suptitle(f'Confusion Matrix Across All Subjects and ROIs ({method})',
                 fontsize=24, fontweight='bold', y=0.995)

    for i, subject in enumerate(SUBJECTS):
        for j, roi in enumerate(ROIS):
            ax = axes[i, j]

            # Construct path
            base_path = LOGS_DIR / method_dir / subject / "fir_reconstruction_uni_hrf" / folder_name
            conf_file = base_path / f"{roi}_universal_hrf" / "figures" / f"{roi}_confusion_matrix.png"

            if conf_file.exists():
                img = Image.open(conf_file)
                ax.imshow(img)
                ax.axis('off')

                # Add title
                group = "Non-CVD" if subject in NON_CVD else "CVD"
                ax.set_title(f"{subject} ({group}) - {roi}",
                           fontsize=14, fontweight='bold', pad=10)
            else:
                ax.text(0.5, 0.5, f"Missing:\n{subject} - {roi}",
                       ha='center', va='center', fontsize=12)
                ax.axis('off')

    plt.tight_layout()
    output_file = OUTPUT_DIR / f"comprehensive_confusion_matrix_{method}.png"
    plt.savefig(output_file, dpi=200, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

    return output_file

def generate_statistical_summary(df):
    """Generate statistical summary tables"""

    # Overall summary
    print("\n" + "="*80)
    print("OVERALL SUMMARY STATISTICS")
    print("="*80)

    summary_stats = df.groupby(['Method', 'Group'])[
        ['Classification_accuracy', 'Reconstruction_error_deg', 'Novel_color_error_deg']
    ].agg(['mean', 'std', 'min', 'max'])

    print(summary_stats.round(4))

    # By ROI
    print("\n" + "="*80)
    print("SUMMARY BY ROI")
    print("="*80)

    roi_stats = df.groupby(['ROI', 'Method'])[
        ['Classification_accuracy', 'Reconstruction_error_deg']
    ].mean().round(4)

    print(roi_stats)

    # By Subject
    print("\n" + "="*80)
    print("SUMMARY BY SUBJECT")
    print("="*80)

    subject_stats = df.groupby(['Subject', 'Method'])[
        ['Classification_accuracy', 'Reconstruction_error_deg']
    ].mean().round(4)

    print(subject_stats)

    # Save to CSV
    summary_stats.to_csv(OUTPUT_DIR / "statistical_summary_overall.csv")
    roi_stats.to_csv(OUTPUT_DIR / "statistical_summary_roi.csv")
    subject_stats.to_csv(OUTPUT_DIR / "statistical_summary_subject.csv")

    return summary_stats, roi_stats, subject_stats

def create_detailed_comparison_table(df):
    """Create detailed comparison table for the report"""

    # Pivot table for easy comparison
    comparison = df.pivot_table(
        values=['Classification_accuracy', 'Reconstruction_error_deg', 'Novel_color_error_deg'],
        index=['Subject', 'ROI'],
        columns='Method',
        aggfunc='mean'
    ).round(4)

    # Calculate improvement (for classification, higher is better; for errors, lower is better)
    comparison[('Classification_accuracy', 'Improvement')] = (
        comparison[('Classification_accuracy', 'voxelSelect')] -
        comparison[('Classification_accuracy', 'zScore')]
    )

    comparison[('Reconstruction_error_deg', 'Improvement')] = (
        comparison[('Reconstruction_error_deg', 'zScore')] -
        comparison[('Reconstruction_error_deg', 'voxelSelect')]  # Reversed: lower error is better
    )

    comparison[('Novel_color_error_deg', 'Improvement')] = (
        comparison[('Novel_color_error_deg', 'zScore')] -
        comparison[('Novel_color_error_deg', 'voxelSelect')]  # Reversed: lower error is better
    )

    # Save
    comparison.to_csv(OUTPUT_DIR / "detailed_comparison.csv")
    print(f"\n✓ Saved detailed comparison table")

    return comparison

def main():
    """Main analysis pipeline"""

    print("\n" + "="*80)
    print("COMPREHENSIVE ANALYSIS OF fMRI COLOR DECODING RESULTS")
    print("="*80 + "\n")

    # Step 1: Collect all summaries
    print("Step 1: Collecting all summary data...")
    df = collect_all_summaries()
    print(f"✓ Collected {len(df)} result entries\n")

    # Step 2: Create accuracy comparison plots
    print("Step 2: Creating accuracy comparison plots...")
    create_accuracy_comparison_plot(df)
    print()

    # Step 3: Create HRF grids
    print("Step 3: Creating HRF visualization grids...")
    create_hrf_grid("zScore", ZSCORE_DIR)
    create_hrf_grid("voxelSelect", VOXELSELECT_DIR)
    print()

    # Step 4: Create color wheel grids
    print("Step 4: Creating color preference wheel grids...")
    create_color_wheel_grid("zScore", ZSCORE_DIR)
    create_color_wheel_grid("voxelSelect", VOXELSELECT_DIR)
    print()

    # Step 5: Create circular space grids
    print("Step 5: Creating circular color space grids...")
    create_circular_space_grid("zScore", ZSCORE_DIR)
    create_circular_space_grid("voxelSelect", VOXELSELECT_DIR)
    print()

    # Step 6: Create confusion matrix grids
    print("Step 6: Creating confusion matrix grids...")
    create_confusion_matrix_grid("zScore", ZSCORE_DIR)
    create_confusion_matrix_grid("voxelSelect", VOXELSELECT_DIR)
    print()

    # Step 7: Generate statistical summaries
    print("Step 7: Generating statistical summaries...")
    generate_statistical_summary(df)
    print()

    # Step 8: Create detailed comparison table
    print("Step 8: Creating detailed comparison table...")
    create_detailed_comparison_table(df)
    print()

    print("="*80)
    print(f"✓ ANALYSIS COMPLETE! All results saved to: {OUTPUT_DIR}")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
