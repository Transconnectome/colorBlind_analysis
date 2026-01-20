#!/usr/bin/env python3
"""
Aggregate trial-wise GLM results from all subjects and ROIs

Usage:
    python aggregate_trial_glm_results.py --input_dir ../results/trial_wise_glm/original_v3
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
import json
import matplotlib.pyplot as plt
import seaborn as sns

def parse_args():
    parser = argparse.ArgumentParser(description='Aggregate trial-wise GLM results')
    parser.add_argument(
        '--input_dir',
        type=str,
        default='../results/trial_wise_glm/original_v3',
        help='Input directory with individual results'
    )
    parser.add_argument(
        '--output_dir',
        type=str,
        default='../results/trial_wise_glm',
        help='Output directory for aggregated results'
    )
    return parser.parse_args()


def aggregate_results(input_dir):
    """Aggregate all subject-ROI results"""
    input_path = Path(input_dir)

    results = []

    # Find all quality_metrics.json files
    json_files = list(input_path.glob('sub-*_*/quality_metrics.json'))

    if not json_files:
        print(f"⚠️ No result files found in {input_dir}")
        return None

    print(f"Found {len(json_files)} result files")

    for json_file in sorted(json_files):
        with open(json_file, 'r') as f:
            data = json.load(f)

        # Extract subject and ROI from path
        # Example: sub-02_V1/quality_metrics.json
        parts = json_file.parent.name.split('_')
        subject = parts[0].replace('sub-', '')
        roi = parts[1]

        # Flatten structure
        row = {
            'subject': subject,
            'roi': roi,
            'n_voxels': data['n_voxels'],
            'total_trials': data['total_trials'],
            'reliability_mean': data['split_half_reliability']['mean'],
            'tsnr_mean': data['temporal_snr']['mean'],
            'tsnr_median': data['temporal_snr']['median'],
            'smoothing_fwhm': data['smoothing_fwhm'],
            'confounds': data['confounds_strategy']
        }

        # Add per-color reliability
        for color, value in data['split_half_reliability']['by_color'].items():
            row[f'reliability_{color}'] = value

        # Add trial counts
        for color, count in data['trial_counts'].items():
            row[f'count_{color}'] = count

        results.append(row)

    df = pd.DataFrame(results)
    return df


def create_visualizations(df, output_dir):
    """Create summary visualizations"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    # 1. Reliability by ROI
    ax = axes[0, 0]
    df_pivot = df.pivot(index='subject', columns='roi', values='reliability_mean')
    df_pivot.plot(kind='bar', ax=ax)
    ax.set_ylabel('Split-half Reliability (Procrustes)')
    ax.set_xlabel('Subject')
    ax.set_title('(A) Trial-wise Reliability by ROI')
    ax.axhline(y=0.50, color='green', linestyle='--', label='Target (0.50)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 2. tSNR by ROI
    ax = axes[0, 1]
    df_pivot = df.pivot(index='subject', columns='roi', values='tsnr_mean')
    df_pivot.plot(kind='bar', ax=ax)
    ax.set_ylabel('Temporal SNR')
    ax.set_xlabel('Subject')
    ax.set_title('(B) Temporal SNR by ROI')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. Trial counts
    ax = axes[0, 2]
    trial_counts = df.groupby('roi')['total_trials'].mean()
    trial_counts.plot(kind='bar', ax=ax)
    ax.set_ylabel('Mean Trial Count')
    ax.set_xlabel('ROI')
    ax.set_title('(C) Average Trial Count per ROI')
    ax.grid(True, alpha=0.3)

    # 4. Reliability distribution
    ax = axes[1, 0]
    sns.boxplot(data=df, x='roi', y='reliability_mean', ax=ax)
    ax.set_ylabel('Reliability')
    ax.set_xlabel('ROI')
    ax.set_title('(D) Reliability Distribution by ROI')
    ax.axhline(y=0.50, color='green', linestyle='--', alpha=0.5)
    ax.grid(True, alpha=0.3)

    # 5. tSNR distribution
    ax = axes[1, 1]
    sns.boxplot(data=df, x='roi', y='tsnr_mean', ax=ax)
    ax.set_ylabel('Temporal SNR')
    ax.set_xlabel('ROI')
    ax.set_title('(E) tSNR Distribution by ROI')
    ax.grid(True, alpha=0.3)

    # 6. Reliability vs tSNR scatter
    ax = axes[1, 2]
    for roi in df['roi'].unique():
        df_roi = df[df['roi'] == roi]
        ax.scatter(df_roi['tsnr_mean'], df_roi['reliability_mean'],
                  label=roi, s=100, alpha=0.7)
    ax.set_xlabel('Temporal SNR')
    ax.set_ylabel('Reliability')
    ax.set_title('(F) Reliability vs tSNR')
    ax.axhline(y=0.50, color='green', linestyle='--', alpha=0.3, label='Reliability target')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path / 'trial_glm_summary.png', dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_path / 'trial_glm_summary.png'}")


def write_summary_report(df, output_dir):
    """Write text summary report"""
    output_path = Path(output_dir)

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("TRIAL-WISE GLM (LS-S) SUMMARY")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Overall statistics
    report_lines.append("## Overall Statistics")
    report_lines.append("")
    report_lines.append(f"Total subject-ROI combinations: {len(df)}")
    report_lines.append(f"Subjects: {df['subject'].nunique()}")
    report_lines.append(f"ROIs: {df['roi'].nunique()}")
    report_lines.append("")

    # Reliability summary
    report_lines.append("## Split-half Reliability (Procrustes)")
    report_lines.append("")
    report_lines.append(f"Overall mean: {df['reliability_mean'].mean():.3f} ± {df['reliability_mean'].std():.3f}")
    report_lines.append("")
    report_lines.append("By ROI:")
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        df_roi = df[df['roi'] == roi]
        if len(df_roi) > 0:
            mean_val = df_roi['reliability_mean'].mean()
            std_val = df_roi['reliability_mean'].std()
            report_lines.append(f"  {roi}: {mean_val:.3f} ± {std_val:.3f}")
    report_lines.append("")

    # tSNR summary
    report_lines.append("## Temporal SNR")
    report_lines.append("")
    report_lines.append(f"Overall mean: {df['tsnr_mean'].mean():.2f} ± {df['tsnr_mean'].std():.2f}")
    report_lines.append("")
    report_lines.append("By ROI:")
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        df_roi = df[df['roi'] == roi]
        if len(df_roi) > 0:
            mean_val = df_roi['tsnr_mean'].mean()
            std_val = df_roi['tsnr_mean'].std()
            report_lines.append(f"  {roi}: {mean_val:.2f} ± {std_val:.2f}")
    report_lines.append("")

    # Trial counts
    report_lines.append("## Trial Counts")
    report_lines.append("")
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        df_roi = df[df['roi'] == roi]
        if len(df_roi) > 0:
            mean_count = df_roi['total_trials'].mean()
            report_lines.append(f"  {roi}: {mean_count:.0f} trials (average)")
    report_lines.append("")

    # Quality assessment
    report_lines.append("## Quality Assessment")
    report_lines.append("")

    pass_count = len(df[df['reliability_mean'] >= 0.50])
    total_count = len(df)

    report_lines.append(f"Combinations meeting reliability target (≥0.50): {pass_count}/{total_count} ({pass_count/total_count*100:.1f}%)")
    report_lines.append("")

    # Cases needing attention
    low_reliability = df[df['reliability_mean'] < 0.50]
    if len(low_reliability) > 0:
        report_lines.append("⚠️ Cases with low reliability:")
        for _, row in low_reliability.iterrows():
            report_lines.append(f"  sub-{row['subject']} {row['roi']}: {row['reliability_mean']:.3f}")
        report_lines.append("")
    else:
        report_lines.append("✅ All combinations passed reliability check!")
        report_lines.append("")

    # Next steps
    report_lines.append("## Next Steps")
    report_lines.append("")

    if pass_count >= total_count * 0.8:
        report_lines.append("✅ PROCEED TO STEP 1.4 (HYPERALIGNMENT)")
        report_lines.append("")
        report_lines.append("Most combinations have sufficient reliability.")
        report_lines.append("Ready for trial-aligned GPA (Generalized Procrustes Analysis).")
    else:
        report_lines.append("⚠️ REVIEW NEEDED")
        report_lines.append("")
        report_lines.append("Many combinations have low reliability.")
        report_lines.append("Consider:")
        report_lines.append("  - Increasing smoothing (6mm → 8mm)")
        report_lines.append("  - Adding more confounds (motion_compcor)")
        report_lines.append("  - Reviewing preprocessing quality")

    report_lines.append("")
    report_lines.append("=" * 80)

    # Write to file
    report_path = output_path / 'trial_glm_summary.txt'
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))

    print(f"✅ Saved: {report_path}")

    # Print to console
    print("")
    print('\n'.join(report_lines))


def main():
    args = parse_args()

    print("Aggregating trial-wise GLM results...")
    print("")

    # Aggregate results
    df = aggregate_results(args.input_dir)

    if df is None:
        print("❌ No results to aggregate")
        return

    # Save detailed CSV
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    csv_path = output_path / 'trial_glm_detailed.csv'
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
