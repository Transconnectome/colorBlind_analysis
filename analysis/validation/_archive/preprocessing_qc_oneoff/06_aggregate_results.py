#!/usr/bin/env python3
"""
Aggregate decoder comparison results across all subjects

Creates group-level summary statistics and publication-ready tables
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_style('whitegrid')
plt.rcParams['figure.dpi'] = 150


def load_all_results(results_dir, subjects, alignment='before'):
    """
    Load results for all subjects

    Returns:
        all_data: Dict[subject][roi][model] = [fold_scores]
    """
    all_data = {}

    for subject in subjects:
        results_file = Path(results_dir) / f"sub-{subject}_performance_raw.json"

        if not results_file.exists():
            print(f"WARNING: Results not found for sub-{subject}: {results_file}")
            continue

        with open(results_file, 'r') as f:
            data = json.load(f)

        # Extract results
        subject_data = {}
        for roi, roi_results in data['results'].items():
            subject_data[roi] = {}

            for model, fold_results in roi_results.items():
                # Store all fold scores for each metric
                subject_data[roi][model] = {
                    'acc_45': [f['acc_45'] for f in fold_results],
                    'acc_90': [f['acc_90'] for f in fold_results],
                    'mae': [f['mae'] for f in fold_results],
                    'medae': [f['medae'] for f in fold_results]
                }

        all_data[subject] = subject_data

    return all_data


def compute_group_statistics(before_data, after_data, subjects, rois, models, metric='acc_45'):
    """
    Compute group-level statistics

    Returns:
        stats_df: DataFrame with mean, SEM, CI for each condition
    """
    rows = []

    for model in models:
        for roi in rois:
            # Collect subject-level means
            before_subject_means = []
            after_subject_means = []

            for subject in subjects:
                if subject not in before_data or subject not in after_data:
                    continue

                if roi not in before_data[subject] or roi not in after_data[subject]:
                    continue

                if model not in before_data[subject][roi] or model not in after_data[subject][roi]:
                    continue

                # Get fold scores
                before_folds = before_data[subject][roi][model][metric]
                after_folds = after_data[subject][roi][model][metric]

                # Subject-level mean
                before_subject_means.append(np.mean(before_folds))
                after_subject_means.append(np.mean(after_folds))

            if len(before_subject_means) == 0:
                continue

            # Compute statistics
            before_mean = np.mean(before_subject_means)
            before_sem = np.std(before_subject_means) / np.sqrt(len(before_subject_means))
            before_ci = 1.96 * before_sem  # 95% CI

            after_mean = np.mean(after_subject_means)
            after_sem = np.std(after_subject_means) / np.sqrt(len(after_subject_means))
            after_ci = 1.96 * after_sem

            # Improvement
            improvement = after_mean - before_mean
            improvement_sem = np.std(np.array(after_subject_means) - np.array(before_subject_means)) / np.sqrt(len(before_subject_means))

            # Paired t-test
            t_stat, p_value = stats.ttest_rel(after_subject_means, before_subject_means)

            # Effect size (Cohen's d)
            diff = np.array(after_subject_means) - np.array(before_subject_means)
            cohens_d = np.mean(diff) / np.std(diff)

            rows.append({
                'Model': model,
                'ROI': roi,
                'Metric': metric,
                'N_subjects': len(before_subject_means),
                'Before_Mean': before_mean,
                'Before_SEM': before_sem,
                'Before_CI': before_ci,
                'After_Mean': after_mean,
                'After_SEM': after_sem,
                'After_CI': after_ci,
                'Improvement': improvement,
                'Improvement_SEM': improvement_sem,
                'T_stat': t_stat,
                'P_value': p_value,
                'Cohens_d': cohens_d
            })

    return pd.DataFrame(rows)


def create_group_summary_table(stats_df, output_dir):
    """
    Create publication-ready summary table

    Saves to CSV and LaTeX format
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Format for publication
    summary_rows = []

    for _, row in stats_df.iterrows():
        # Format with mean ± SEM
        before_str = f"{row['Before_Mean']:.3f} ± {row['Before_SEM']:.3f}"
        after_str = f"{row['After_Mean']:.3f} ± {row['After_SEM']:.3f}"

        # Format improvement with significance
        if row['P_value'] < 0.001:
            sig_str = '***'
        elif row['P_value'] < 0.01:
            sig_str = '**'
        elif row['P_value'] < 0.05:
            sig_str = '*'
        else:
            sig_str = 'ns'

        improvement_str = f"{row['Improvement']:+.3f} ± {row['Improvement_SEM']:.3f} ({sig_str})"

        summary_rows.append({
            'Model': row['Model'],
            'ROI': row['ROI'],
            'Metric': row['Metric'],
            'N': row['N_subjects'],
            'Before': before_str,
            'After': after_str,
            'Improvement': improvement_str,
            "Cohen's d": f"{row['Cohens_d']:.2f}",
            'P-value': f"{row['P_value']:.4f}"
        })

    summary_df = pd.DataFrame(summary_rows)

    # Save to CSV
    csv_file = output_path / 'group_summary_table.csv'
    summary_df.to_csv(csv_file, index=False)
    print(f"\nSaved summary table: {csv_file}")

    # Save raw statistics
    raw_csv = output_path / 'group_statistics_raw.csv'
    stats_df.to_csv(raw_csv, index=False)
    print(f"Saved raw statistics: {raw_csv}")

    # Print to console
    print("\n" + "="*100)
    print("Group Summary Table")
    print("="*100)
    print(summary_df.to_string(index=False))
    print("="*100)
    print("\nSignificance levels: *** p<0.001, ** p<0.01, * p<0.05, ns p>=0.05")


def plot_group_comparison(stats_df, output_dir, metric='acc_45'):
    """
    Create group-level comparison plot
    """
    # Filter for specific metric
    df = stats_df[stats_df['Metric'] == metric].copy()

    models = df['Model'].unique()
    rois = df['ROI'].unique()

    # Create figure
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('Group-Level Decoder Comparison (N=7 HC subjects)', fontsize=14, fontweight='bold')

    # ========================================================================
    # Panel A: Performance by model (averaged across ROIs)
    # ========================================================================
    ax = axes[0]

    # Aggregate across ROIs
    model_stats = df.groupby('Model').agg({
        'Before_Mean': 'mean',
        'Before_SEM': lambda x: np.sqrt(np.sum(x**2)) / len(x),  # Combined SEM
        'After_Mean': 'mean',
        'After_SEM': lambda x: np.sqrt(np.sum(x**2)) / len(x)
    }).reset_index()

    x = np.arange(len(models))
    width = 0.35

    before_means = [model_stats[model_stats['Model'] == m]['Before_Mean'].values[0] for m in models]
    before_sems = [model_stats[model_stats['Model'] == m]['Before_SEM'].values[0] for m in models]

    after_means = [model_stats[model_stats['Model'] == m]['After_Mean'].values[0] for m in models]
    after_sems = [model_stats[model_stats['Model'] == m]['After_SEM'].values[0] for m in models]

    ax.bar(x - width/2, before_means, width, yerr=before_sems,
           label='Before Alignment', color='lightgray', edgecolor='black')
    ax.bar(x + width/2, after_means, width, yerr=after_sems,
           label='After Alignment', color='steelblue', edgecolor='black')

    ax.axhline(1/8, color='red', linestyle='--', linewidth=1, label='Chance (12.5%)')

    ax.set_ylabel('Accuracy (within 45°)', fontweight='bold')
    ax.set_title('Performance by Model', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.legend()
    ax.set_ylim([0, 1])

    # ========================================================================
    # Panel B: Improvement by model
    # ========================================================================
    ax = axes[1]

    improvement_means = [model_stats[model_stats['Model'] == m]['After_Mean'].values[0] -
                        model_stats[model_stats['Model'] == m]['Before_Mean'].values[0]
                        for m in models]

    # Get significance from original data
    significance = []
    for model in models:
        model_df = df[df['Model'] == model]
        # Average p-value across ROIs (conservative)
        p_avg = model_df['P_value'].mean()
        if p_avg < 0.001:
            significance.append('***')
        elif p_avg < 0.01:
            significance.append('**')
        elif p_avg < 0.05:
            significance.append('*')
        else:
            significance.append('ns')

    colors = ['steelblue' if imp > 0 else 'lightgray' for imp in improvement_means]
    bars = ax.bar(x, improvement_means, width=0.6, color=colors, edgecolor='black')

    ax.axhline(0, color='black', linestyle='-', linewidth=0.5)
    ax.set_ylabel('Improvement (After - Before)', fontweight='bold')
    ax.set_title('Alignment Effect', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(models)

    # Add significance annotations
    for i, (bar, sig) in enumerate(zip(bars, significance)):
        y_pos = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2,
               y_pos + 0.02 if y_pos > 0 else y_pos - 0.02,
               sig, ha='center', va='bottom' if y_pos > 0 else 'top',
               fontsize=12, fontweight='bold')

    plt.tight_layout()

    # Save
    output_path = Path(output_dir)
    output_file = output_path / f'group_comparison_{metric}.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_file}")

    plt.close()


def plot_roi_gradient(stats_df, output_dir, metric='acc_45'):
    """
    Plot ROI gradient effect
    """
    df = stats_df[stats_df['Metric'] == metric].copy()

    models = df['Model'].unique()
    rois = ['V1', 'V2', 'V3', 'hV4']  # In order

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    for model in models:
        model_df = df[df['Model'] == model]

        improvements = []
        for roi in rois:
            roi_df = model_df[model_df['ROI'] == roi]
            if len(roi_df) > 0:
                improvements.append(roi_df['Improvement'].values[0])
            else:
                improvements.append(np.nan)

        ax.plot(rois, improvements, marker='o', linewidth=2, markersize=8, label=model)

    ax.axhline(0, color='gray', linestyle='--', linewidth=1)
    ax.set_xlabel('Visual Area', fontweight='bold')
    ax.set_ylabel('Improvement (After - Before)', fontweight='bold')
    ax.set_title('ROI Gradient: Alignment Effect by Visual Area', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = Path(output_dir)
    output_file = output_path / f'roi_gradient_{metric}.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_file}")

    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate decoder comparison results across subjects"
    )
    parser.add_argument('--before_dir', type=str, required=True,
                       help='Directory with before alignment results')
    parser.add_argument('--after_dir', type=str, required=True,
                       help='Directory with after alignment results')
    parser.add_argument('--subjects', nargs='+', default=['01', '02', '03', '05', '06', '07'],
                       help='Subject IDs')
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2', 'V3', 'hV4'],
                       help='ROI names')
    parser.add_argument('--models', nargs='+', default=['ridge', 'forward_encoding', 'mlp'],
                       help='Model names')
    parser.add_argument('--output_dir', type=str, required=True,
                       help='Output directory')

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print("Aggregating Results Across Subjects")
    print(f"{'='*80}")
    print(f"Subjects: {args.subjects}")
    print(f"ROIs: {args.rois}")
    print(f"Models: {args.models}")
    print(f"{'='*80}\n")

    # Load all results
    print("Loading results...")
    before_data = load_all_results(args.before_dir, args.subjects, 'before')
    after_data = load_all_results(args.after_dir, args.subjects, 'after')

    print(f"Loaded {len(before_data)} subjects (before)")
    print(f"Loaded {len(after_data)} subjects (after)")

    # Compute statistics for each metric
    for metric in ['acc_45', 'acc_90', 'mae', 'medae']:
        print(f"\n{'='*80}")
        print(f"Computing statistics for {metric}...")
        print(f"{'='*80}")

        stats_df = compute_group_statistics(
            before_data, after_data,
            args.subjects, args.rois, args.models,
            metric=metric
        )

        # Save and display summary
        create_group_summary_table(stats_df, args.output_dir)

        # Create plots (for main metrics only)
        if metric in ['acc_45', 'mae']:
            print(f"\nGenerating plots for {metric}...")
            plot_group_comparison(stats_df, args.output_dir, metric)
            plot_roi_gradient(stats_df, args.output_dir, metric)

    print(f"\n{'='*80}")
    print(f"Aggregation complete! Results saved to: {args.output_dir}")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
