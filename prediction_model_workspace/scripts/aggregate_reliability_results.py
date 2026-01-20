#!/usr/bin/env python3
"""
Aggregate reliability comparison results from all subjects and ROIs

Usage:
    python aggregate_reliability_results.py --input_dir ../results/reliability_check
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns

def parse_args():
    parser = argparse.ArgumentParser(description='Aggregate reliability results')
    parser.add_argument(
        '--input_dir',
        type=str,
        default='../results/reliability_check',
        help='Input directory with individual results'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='../results/reliability_check',
        help='Output directory for aggregated results'
    )
    return parser.parse_args()


def aggregate_results(input_dir):
    """Aggregate all individual subject-ROI results"""
    input_path = Path(input_dir)

    results = []

    # Find all JSON result files
    json_files = list(input_path.glob('sub-*_*_reliability.json'))

    if not json_files:
        print(f"⚠️ No result files found in {input_dir}")
        return None

    print(f"Found {len(json_files)} result files")

    for json_file in sorted(json_files):
        with open(json_file, 'r') as f:
            data = json.load(f)

        # Extract subject and ROI from filename
        # Example: sub-02_V1_reliability.json
        parts = json_file.stem.split('_')
        subject = parts[0].replace('sub-', '')
        roi = parts[1]

        # Flatten nested structure
        row = {
            'subject': subject,
            'roi': roi,
            'procrustes_mean': data['procrustes']['mean'],
            'procrustes_std': data['procrustes']['std'],
            'voxelwise_mean': data['voxelwise']['mean'],
            'voxelwise_std': data['voxelwise']['std'],
            'decision': data['decision']['action'],
            'recommendation': data['decision']['recommendation']
        }

        # Add per-color metrics if available
        if 'by_color' in data['procrustes']:
            for color, value in data['procrustes']['by_color'].items():
                row[f'procrustes_{color}'] = value

        results.append(row)

    df = pd.DataFrame(results)
    return df


def create_visualizations(df, output_dir):
    """Create summary visualizations"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Procrustes reliability by ROI
    ax = axes[0, 0]
    df_pivot = df.pivot(index='subject', columns='roi', values='procrustes_mean')
    df_pivot.plot(kind='bar', ax=ax)
    ax.set_ylabel('Procrustes Stability (1 - disparity)')
    ax.set_xlabel('Subject')
    ax.set_title('(A) Procrustes Stability by ROI')
    ax.axhline(y=0.80, color='green', linestyle='--', label='Target (0.80)')
    ax.axhline(y=0.70, color='orange', linestyle='--', label='Caution (0.70)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. Voxelwise correlation by ROI
    ax = axes[0, 1]
    df_pivot = df.pivot(index='subject', columns='roi', values='voxelwise_mean')
    df_pivot.plot(kind='bar', ax=ax)
    ax.set_ylabel('Voxelwise Correlation')
    ax.set_xlabel('Subject')
    ax.set_title('(B) Voxelwise Correlation by ROI')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. ROI comparison (boxplot)
    ax = axes[1, 0]
    sns.boxplot(data=df, x='roi', y='procrustes_mean', ax=ax)
    ax.set_ylabel('Procrustes Stability')
    ax.set_xlabel('ROI')
    ax.set_title('(C) Procrustes Stability Distribution by ROI')
    ax.axhline(y=0.80, color='green', linestyle='--', alpha=0.5)
    ax.axhline(y=0.70, color='orange', linestyle='--', alpha=0.5)
    ax.grid(True, alpha=0.3)

    # 4. Decision summary (count)
    ax = axes[1, 1]
    decision_counts = df['decision'].value_counts()
    decision_counts.plot(kind='bar', ax=ax)
    ax.set_ylabel('Count')
    ax.set_xlabel('Decision')
    ax.set_title('(D) Decision Summary')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path / 'reliability_summary.png', dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_path / 'reliability_summary.png'}")

    # 5. Procrustes vs Voxelwise scatter
    fig, ax = plt.subplots(figsize=(8, 8))
    for roi in df['roi'].unique():
        df_roi = df[df['roi'] == roi]
        ax.scatter(df_roi['voxelwise_mean'], df_roi['procrustes_mean'],
                  label=roi, s=100, alpha=0.7)

    ax.set_xlabel('Voxelwise Correlation')
    ax.set_ylabel('Procrustes Stability')
    ax.set_title('Procrustes vs Voxelwise Reliability')
    ax.axhline(y=0.80, color='green', linestyle='--', alpha=0.3, label='Procrustes target')
    ax.axhline(y=0.70, color='orange', linestyle='--', alpha=0.3)
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path / 'procrustes_vs_voxelwise.png', dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_path / 'procrustes_vs_voxelwise.png'}")


def write_summary_report(df, output_dir):
    """Write text summary report"""
    output_path = Path(output_dir)

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("RELIABILITY COMPARISON SUMMARY")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Overall statistics
    report_lines.append("## Overall Statistics")
    report_lines.append("")
    report_lines.append(f"Total combinations: {len(df)}")
    report_lines.append(f"Subjects: {df['subject'].nunique()}")
    report_lines.append(f"ROIs: {df['roi'].nunique()}")
    report_lines.append("")

    # Procrustes stability summary
    report_lines.append("## Procrustes Stability (Primary Metric)")
    report_lines.append("")
    report_lines.append(f"Overall mean: {df['procrustes_mean'].mean():.3f} ± {df['procrustes_mean'].std():.3f}")
    report_lines.append("")
    report_lines.append("By ROI:")
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        df_roi = df[df['roi'] == roi]
        if len(df_roi) > 0:
            mean_val = df_roi['procrustes_mean'].mean()
            std_val = df_roi['procrustes_mean'].std()
            report_lines.append(f"  {roi}: {mean_val:.3f} ± {std_val:.3f}")
    report_lines.append("")

    # Voxelwise correlation summary
    report_lines.append("## Voxelwise Correlation (Reference Metric)")
    report_lines.append("")
    report_lines.append(f"Overall mean: {df['voxelwise_mean'].mean():.3f} ± {df['voxelwise_mean'].std():.3f}")
    report_lines.append("")
    report_lines.append("By ROI:")
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        df_roi = df[df['roi'] == roi]
        if len(df_roi) > 0:
            mean_val = df_roi['voxelwise_mean'].mean()
            std_val = df_roi['voxelwise_mean'].std()
            report_lines.append(f"  {roi}: {mean_val:.3f} ± {std_val:.3f}")
    report_lines.append("")

    # Decision summary
    report_lines.append("## Decision Summary")
    report_lines.append("")
    decision_counts = df['decision'].value_counts()
    for decision, count in decision_counts.items():
        pct = count / len(df) * 100
        report_lines.append(f"  {decision}: {count} ({pct:.1f}%)")
    report_lines.append("")

    # Cases requiring attention
    report_lines.append("## Cases Requiring Attention")
    report_lines.append("")

    needs_attention = df[df['decision'].isin(['IMPROVE_GLM', 'PROCEED_WITH_CAUTION'])]
    if len(needs_attention) > 0:
        report_lines.append("Subject-ROI pairs needing improvement or caution:")
        for _, row in needs_attention.iterrows():
            report_lines.append(f"  sub-{row['subject']} {row['roi']}: {row['decision']}")
            report_lines.append(f"    Procrustes: {row['procrustes_mean']:.3f}")
            report_lines.append(f"    Recommendation: {row['recommendation']}")
        report_lines.append("")
    else:
        report_lines.append("✅ All combinations passed with PROCEED status!")
        report_lines.append("")

    # Next steps
    report_lines.append("## Next Steps")
    report_lines.append("")

    proceed_count = len(df[df['decision'] == 'PROCEED'])
    total_count = len(df)

    if proceed_count == total_count:
        report_lines.append("✅ ALL SUBJECTS AND ROIS READY FOR STEP 1.3 (LS-S GLM)")
        report_lines.append("")
        report_lines.append("Proceed with:")
        report_lines.append("  - Step 1.3: LS-S GLM extraction (trial-wise betas)")
        report_lines.append("  - No preprocessing modifications needed")
    elif proceed_count >= total_count * 0.8:
        report_lines.append("⚠️ MOST SUBJECTS READY, SOME NEED CAUTION")
        report_lines.append("")
        report_lines.append("Recommendation:")
        report_lines.append("  - Proceed with good subjects/ROIs")
        report_lines.append("  - Monitor quality closely for caution cases")
    else:
        report_lines.append("❌ MAJOR ISSUES DETECTED")
        report_lines.append("")
        report_lines.append("Recommendation:")
        report_lines.append("  - Review preprocessing parameters")
        report_lines.append("  - Consider increasing smoothing or adjusting confounds")
        report_lines.append("  - Consult with team before proceeding to Step 1.3")

    report_lines.append("")
    report_lines.append("=" * 80)

    # Write to file
    report_path = output_path / 'reliability_summary.txt'
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))

    print(f"✅ Saved: {report_path}")

    # Print to console
    print("")
    print('\n'.join(report_lines))


def main():
    args = parse_args()

    print("Aggregating reliability comparison results...")
    print("")

    # Aggregate results
    df = aggregate_results(args.input_dir)

    if df is None:
        print("❌ No results to aggregate")
        return

    # Save detailed CSV
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_path = output_path / 'reliability_detailed.csv'
    df.to_csv(csv_path, index=False)
    print(f"✅ Saved: {csv_path}")
    print("")

    # Create visualizations
    create_visualizations(df, args.output_dir)
    print("")

    # Write summary report
    write_summary_report(df, args.output_dir)


if __name__ == '__main__':
    main()
