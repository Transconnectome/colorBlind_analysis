#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
summarize_all_subjects.py
-------------------------
Summarize FIR reconstruction results across all subjects and ROIs

Usage:
    python summarize_all_subjects.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration
SUBJECTS = ['01', '02', '03', '04']
ROIS = ['V1', 'V2', 'V3', 'hV4']
BASE_DIR = Path('logs')

def load_results():
    """Load all CSV results"""
    results = []

    for subject in SUBJECTS:
        for roi in ROIS:
            # Try different path patterns (sub-01 has different structure)
            path1 = BASE_DIR / f'sub-{subject}' / '1112_23' / 'fir_reconstruction_uni_hrf' / f'{roi}_universal_hrf' / 'summary.csv'
            path2 = BASE_DIR / f'sub-{subject}' / '1112_23' / f'{roi}_universal_hrf' / 'summary.csv'

            csv_path = path1 if path1.exists() else (path2 if path2.exists() else None)

            if csv_path and csv_path.exists():
                df = pd.read_csv(csv_path)
                df['Subject'] = subject
                results.append(df)
                print(f"✓ Loaded: sub-{subject} {roi}")
            else:
                print(f"✗ Missing: sub-{subject} {roi}")

    if not results:
        print("ERROR: No results found!")
        return None

    return pd.concat(results, ignore_index=True)

def create_summary_table(df):
    """Create summary statistics table"""
    summary = df.groupby(['ROI', 'Subject']).agg({
        'N_voxels': 'first',
        'Optimal_delay_TRs': 'first',
        'Classification_accuracy': 'mean',
        'Reconstruction_error_deg': 'mean',
        'Novel_color_error_deg': 'mean'
    }).reset_index()

    return summary

def create_visualizations(df, output_dir):
    """Create comparison plots"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Novel Color Error by ROI and Subject
    fig, ax = plt.subplots(figsize=(12, 6))

    pivot_data = df.pivot(index='Subject', columns='ROI', values='Novel_color_error_deg')
    pivot_data.plot(kind='bar', ax=ax, width=0.8)

    ax.axhline(y=90, color='red', linestyle='--', linewidth=2, label='Chance (90°)', alpha=0.7)
    ax.set_xlabel('Subject', fontsize=12, fontweight='bold')
    ax.set_ylabel('Novel Color Error (degrees)', fontsize=12, fontweight='bold')
    ax.set_title('Novel Color Reconstruction Error\nAcross Subjects and ROIs', fontsize=14, fontweight='bold')
    ax.legend(title='ROI', fontsize=10)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_dir / 'novel_error_by_subject_roi.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 2. Heatmap of Novel Errors
    fig, ax = plt.subplots(figsize=(10, 6))

    pivot_data = df.pivot(index='ROI', columns='Subject', values='Novel_color_error_deg')
    sns.heatmap(pivot_data, annot=True, fmt='.1f', cmap='RdYlGn_r',
                center=90, vmin=40, vmax=140, ax=ax, cbar_kws={'label': 'Error (degrees)'})

    ax.set_title('Novel Color Error Heatmap\n(Green=Better, Red=Worse)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Subject', fontsize=12, fontweight='bold')
    ax.set_ylabel('ROI', fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_dir / 'novel_error_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()

    # 3. Training vs Novel Error
    fig, axes = plt.subplots(1, len(SUBJECTS), figsize=(16, 4), sharey=True)
    fig.suptitle('Training vs Novel Color Error by Subject', fontsize=14, fontweight='bold')

    for idx, subject in enumerate(SUBJECTS):
        ax = axes[idx]
        sub_data = df[df['Subject'] == subject]

        x = np.arange(len(sub_data))
        width = 0.35

        ax.bar(x - width/2, sub_data['Reconstruction_error_deg'], width,
               label='Training', color='skyblue', alpha=0.8)
        ax.bar(x + width/2, sub_data['Novel_color_error_deg'], width,
               label='Novel', color='salmon', alpha=0.8)

        ax.axhline(y=90, color='red', linestyle='--', linewidth=1, alpha=0.5)
        ax.set_xlabel('ROI', fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(sub_data['ROI'])
        ax.set_title(f'Subject {subject}', fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

        if idx == 0:
            ax.set_ylabel('Error (degrees)', fontweight='bold')
            ax.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(output_dir / 'training_vs_novel_by_subject.png', dpi=150, bbox_inches='tight')
    plt.close()

    print(f"\n✓ Saved visualizations to: {output_dir}")

def main():
    print("=" * 60)
    print("FIR Reconstruction Results Summary")
    print("=" * 60)
    print()

    # Load results
    print("Loading results...")
    df = load_results()

    if df is None:
        return

    print(f"\nTotal records: {len(df)}")
    print()

    # Create summary
    print("Creating summary table...")
    summary = create_summary_table(df)

    # Save summary
    output_dir = Path('logs/all_subjects_summary')
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / 'all_subjects_summary.csv'
    summary.to_csv(summary_path, index=False)
    print(f"✓ Saved summary to: {summary_path}")

    # Display summary
    print("\n" + "=" * 60)
    print("SUMMARY TABLE")
    print("=" * 60)
    print(summary.to_string(index=False))
    print()

    # Aggregate statistics
    print("=" * 60)
    print("AGGREGATE STATISTICS BY ROI")
    print("=" * 60)
    agg_stats = df.groupby('ROI').agg({
        'Novel_color_error_deg': ['mean', 'std', 'min', 'max'],
        'Classification_accuracy': ['mean', 'std'],
        'N_voxels': 'mean'
    }).round(2)
    print(agg_stats)
    print()

    # Best performing
    print("=" * 60)
    print("BEST PERFORMING CONFIGURATIONS")
    print("=" * 60)
    best_overall = df.loc[df['Novel_color_error_deg'].idxmin()]
    print(f"Best Overall:")
    print(f"  Subject: {best_overall['Subject']}, ROI: {best_overall['ROI']}")
    print(f"  Novel Error: {best_overall['Novel_color_error_deg']:.1f}°")
    print()

    for roi in ROIS:
        roi_data = df[df['ROI'] == roi]
        if not roi_data.empty:
            best_roi = roi_data.loc[roi_data['Novel_color_error_deg'].idxmin()]
            print(f"Best {roi}: Subject {best_roi['Subject']} ({best_roi['Novel_color_error_deg']:.1f}°)")

    print()

    # Create visualizations
    print("=" * 60)
    print("Creating visualizations...")
    print("=" * 60)
    create_visualizations(df, output_dir)

    print()
    print("=" * 60)
    print("SUMMARY COMPLETE!")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print()

if __name__ == '__main__':
    main()
