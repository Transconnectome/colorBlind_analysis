#!/usr/bin/env python3
"""
Compare Dice coefficients across different registration methods

Usage:
    python compare_methods.py --base_dir /path/to/prep_trials
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np


def load_dice_results(base_dir):
    """Load all Dice results from CSVs"""
    results_dir = Path(base_dir) / 'results'

    all_results = []

    # Method names
    methods = {
        'method1_flirt_bbr': 'Method 1: FLIRT → BBR',
        'method2_header_bbr': 'Method 2: Header → BBR',
        'method3_header_mi': 'Method 3: Header → MI',
        'method4_header_bbr1pass': 'Method 4: Header → BBR 1-pass',
    }

    for method_key, method_name in methods.items():
        csv_file = results_dir / f'dice_{method_key}.csv'

        if csv_file.exists():
            df = pd.read_csv(csv_file)
            df['method_name'] = method_name
            df['method_key'] = method_key
            all_results.append(df)
        else:
            print(f"⚠️  WARNING: {csv_file.name} not found, skipping")

    if not all_results:
        print("❌ ERROR: No results found")
        return None

    df_all = pd.concat(all_results, ignore_index=True)
    return df_all


def plot_dice_comparison(df, output_file):
    """Create comparison plot"""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Plot 1: Dice by subject and method
    ax1 = axes[0]
    df_pivot = df.pivot(index='subject', columns='method_name', values='dice')

    df_pivot.plot(kind='bar', ax=ax1, width=0.8, colormap='Set2')
    ax1.set_xlabel('Subject', fontsize=12)
    ax1.set_ylabel('Dice Coefficient', fontsize=12)
    ax1.set_title('Dice Coefficient by Subject and Method', fontsize=14, fontweight='bold')
    ax1.axhline(y=0.90, color='green', linestyle='--', label='Excellent (≥0.90)', alpha=0.5)
    ax1.axhline(y=0.80, color='orange', linestyle='--', label='Good (≥0.80)', alpha=0.5)
    ax1.axhline(y=0.70, color='red', linestyle='--', label='Fair (≥0.70)', alpha=0.5)
    ax1.legend(loc='lower right', fontsize=9)
    ax1.set_ylim(0.5, 1.0)
    ax1.grid(axis='y', alpha=0.3)

    # Plot 2: Mean Dice by method
    ax2 = axes[1]
    df_mean = df.groupby('method_name')['dice'].agg(['mean', 'std']).reset_index()
    df_mean = df_mean.sort_values('mean', ascending=False)

    x_pos = np.arange(len(df_mean))
    bars = ax2.bar(x_pos, df_mean['mean'], yerr=df_mean['std'],
                    capsize=5, alpha=0.7, color='steelblue')

    # Color bars by performance
    for i, (idx, row) in enumerate(df_mean.iterrows()):
        if row['mean'] >= 0.90:
            bars[i].set_color('green')
        elif row['mean'] >= 0.80:
            bars[i].set_color('orange')
        else:
            bars[i].set_color('red')

    ax2.set_xticks(x_pos)
    ax2.set_xticklabels([m.replace('Method ', 'M') for m in df_mean['method_name']],
                         rotation=15, ha='right')
    ax2.set_ylabel('Mean Dice Coefficient', fontsize=12)
    ax2.set_title('Mean Dice by Method (± SD)', fontsize=14, fontweight='bold')
    ax2.axhline(y=0.90, color='green', linestyle='--', alpha=0.5)
    ax2.axhline(y=0.80, color='orange', linestyle='--', alpha=0.5)
    ax2.set_ylim(0.5, 1.0)
    ax2.grid(axis='y', alpha=0.3)

    # Add value labels on bars
    for i, (idx, row) in enumerate(df_mean.iterrows()):
        ax2.text(i, row['mean'] + 0.02, f"{row['mean']:.3f}",
                 ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Plot saved: {output_file}")

    plt.close()


def generate_report(df, output_file):
    """Generate markdown comparison report"""

    with open(output_file, 'w') as f:
        f.write("# Preprocessing Methods Comparison Report\n\n")
        f.write(f"**Date**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("---\n\n")

        # Overall summary
        f.write("## Overall Summary\n\n")
        df_mean = df.groupby('method_name')['dice'].agg(['mean', 'std', 'min', 'max']).reset_index()
        df_mean = df_mean.sort_values('mean', ascending=False)
        df_mean['rank'] = range(1, len(df_mean) + 1)

        f.write("| Rank | Method | Mean Dice | SD | Min | Max | Assessment |\n")
        f.write("|------|--------|-----------|----|----|-----|------------|\n")

        for idx, row in df_mean.iterrows():
            if row['mean'] >= 0.90:
                assessment = "✅ Excellent"
            elif row['mean'] >= 0.80:
                assessment = "✓ Good"
            elif row['mean'] >= 0.70:
                assessment = "⚠️ Fair"
            else:
                assessment = "❌ Poor"

            f.write(f"| {row['rank']} | {row['method_name']} | "
                    f"{row['mean']:.4f} | {row['std']:.4f} | "
                    f"{row['min']:.4f} | {row['max']:.4f} | {assessment} |\n")

        f.write("\n---\n\n")

        # Subject-specific results
        f.write("## Subject-Specific Results\n\n")

        for subject in sorted(df['subject'].unique()):
            df_sub = df[df['subject'] == subject].sort_values('dice', ascending=False)

            f.write(f"### Sub-{subject}\n\n")
            f.write("| Rank | Method | Dice | Assessment |\n")
            f.write("|------|--------|------|------------|\n")

            for rank, (idx, row) in enumerate(df_sub.iterrows(), 1):
                if row['dice'] >= 0.90:
                    assessment = "✅ Excellent"
                elif row['dice'] >= 0.80:
                    assessment = "✓ Good"
                elif row['dice'] >= 0.70:
                    assessment = "⚠️ Fair"
                else:
                    assessment = "❌ Poor"

                f.write(f"| {rank} | {row['method_name']} | {row['dice']:.4f} | {assessment} |\n")

            # Best method for this subject
            best_method = df_sub.iloc[0]['method_name']
            best_dice = df_sub.iloc[0]['dice']
            f.write(f"\n**Best method**: {best_method} (Dice: {best_dice:.4f})\n\n")

        f.write("---\n\n")

        # Recommendations
        f.write("## Recommendations\n\n")

        best_overall = df_mean.iloc[0]
        f.write(f"### Overall Best Method: {best_overall['method_name']}\n\n")
        f.write(f"- Mean Dice: {best_overall['mean']:.4f} ± {best_overall['std']:.4f}\n")
        f.write(f"- Range: {best_overall['min']:.4f} - {best_overall['max']:.4f}\n\n")

        # Check if improvement over baseline
        baseline = df_mean[df_mean['method_name'].str.contains('Method 1')]
        if not baseline.empty:
            baseline_dice = baseline.iloc[0]['mean']
            improvement = best_overall['mean'] - baseline_dice
            improvement_pct = (improvement / baseline_dice) * 100

            if improvement > 0.01:
                f.write(f"### Improvement over Baseline\n\n")
                f.write(f"- Baseline (Method 1): {baseline_dice:.4f}\n")
                f.write(f"- Best method: {best_overall['mean']:.4f}\n")
                f.write(f"- Improvement: +{improvement:.4f} ({improvement_pct:.1f}%)\n\n")
            else:
                f.write(f"### No Significant Improvement\n\n")
                f.write(f"- Baseline performs similarly to alternatives\n")
                f.write(f"- Recommend staying with Method 1 (simplest)\n\n")

        # Subject-specific recommendations
        f.write("### Subject-Specific Recommendations\n\n")

        for subject in sorted(df['subject'].unique()):
            df_sub = df[df['subject'] == subject].sort_values('dice', ascending=False)
            best = df_sub.iloc[0]

            # Check baseline for this subject
            baseline_sub = df_sub[df_sub['method_name'].str.contains('Method 1')]
            if not baseline_sub.empty:
                baseline_dice_sub = baseline_sub.iloc[0]['dice']
                improvement_sub = best['dice'] - baseline_dice_sub

                if improvement_sub > 0.02:  # 2% threshold
                    f.write(f"- **Sub-{subject}**: Switch to {best['method_name']} "
                            f"(Dice: {baseline_dice_sub:.4f} → {best['dice']:.4f}, "
                            f"+{improvement_sub:.4f})\n")
                else:
                    f.write(f"- **Sub-{subject}**: Stay with baseline "
                            f"(Dice: {baseline_dice_sub:.4f}, no significant improvement)\n")

        f.write("\n---\n\n")
        f.write("**Report generated by**: compare_methods.py\n")

    print(f"✅ Report saved: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='Compare registration methods')
    parser.add_argument('--base_dir', type=str,
                        default='/scratch/connectome/haba6030/colorBlind/analysis/prep_trials',
                        help='Base directory for prep_trials')

    args = parser.parse_args()

    base_dir = Path(args.base_dir)
    results_dir = base_dir / 'results'
    results_dir.mkdir(exist_ok=True)

    print("===============================================================================")
    print("Preprocessing Methods Comparison")
    print("===============================================================================")
    print("")

    # Load results
    print("Loading Dice results...")
    df = load_dice_results(base_dir)

    if df is None:
        return

    print(f"✅ Loaded {len(df)} results from {len(df['method_name'].unique())} methods")
    print("")

    # Display summary
    print("Summary:")
    print(df.groupby('method_name')['dice'].agg(['count', 'mean', 'std', 'min', 'max']))
    print("")

    # Generate plot
    print("Generating comparison plot...")
    plot_file = results_dir / 'dice_comparison.png'
    plot_dice_comparison(df, plot_file)
    print("")

    # Generate report
    print("Generating comparison report...")
    report_file = results_dir / 'comparison_report.md'
    generate_report(df, report_file)
    print("")

    print("===============================================================================")
    print("Comparison Complete!")
    print("===============================================================================")
    print("")
    print("Output files:")
    print(f"  Plot:   {plot_file}")
    print(f"  Report: {report_file}")
    print("")


if __name__ == '__main__':
    main()
