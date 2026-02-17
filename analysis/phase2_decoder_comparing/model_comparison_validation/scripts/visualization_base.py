#!/usr/bin/env python3
"""
Visualization for Decoder Model Comparison

Creates plots to answer:
1. Which linear model is better? (Ridge vs Forward Encoding)
2. Does alignment help linear models more? (Linear vs Non-linear × Before vs After)
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.dpi'] = 150
plt.rcParams['font.size'] = 10


def load_results(results_dir, subject):
    """Load results from JSON file"""
    results_file = Path(results_dir) / f"sub-{subject}_performance_raw.json"

    if not results_file.exists():
        raise FileNotFoundError(f"Results not found: {results_file}")

    with open(results_file, 'r') as f:
        data = json.load(f)

    return data


def aggregate_metrics(results_data, metric_name='acc_45'):
    """
    Aggregate metrics across folds and ROIs

    Returns:
        aggregated: Dict[roi][model] = [fold_scores]
    """
    results = results_data['results']
    aggregated = {}

    for roi, roi_results in results.items():
        aggregated[roi] = {}

        for model, fold_results in roi_results.items():
            # Extract metric values from each fold
            values = [fold[metric_name] for fold in fold_results]
            aggregated[roi][model] = values

    return aggregated


def plot_performance_comparison(before_data, after_data, output_dir, subject):
    """
    Create performance comparison plot

    2×2 subplot:
    - Top left: Classification (acc_45)
    - Top right: Reconstruction (MAE)
    - Bottom: Combined bar plot with before/after
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Decoder Model Comparison: sub-{subject}', fontsize=14, fontweight='bold')

    # Get ROIs and models
    rois = before_data['rois']
    models = before_data['models']

    model_labels = {
        'ridge': 'Ridge',
        'forward_encoding': 'Forward Enc.',
        'mlp': 'MLP'
    }

    model_colors = {
        'ridge': '#1f77b4',
        'forward_encoding': '#ff7f0e',
        'mlp': '#2ca02c'
    }

    # ========================================================================
    # Panel A: Classification Accuracy (acc_45)
    # ========================================================================
    ax = axes[0, 0]

    # Aggregate across ROIs
    acc_before = aggregate_metrics(before_data, 'acc_45')
    acc_after = aggregate_metrics(after_data, 'acc_45')

    # Compute means and SEMs across ROIs
    means_before = []
    sems_before = []
    means_after = []
    sems_after = []

    for model in models:
        # Collect values across all ROIs
        values_before = []
        values_after = []

        for roi in rois:
            if model in acc_before[roi]:
                values_before.extend(acc_before[roi][model])
            if model in acc_after[roi]:
                values_after.extend(acc_after[roi][model])

        means_before.append(np.mean(values_before))
        sems_before.append(np.std(values_before) / np.sqrt(len(values_before)))

        means_after.append(np.mean(values_after))
        sems_after.append(np.std(values_after) / np.sqrt(len(values_after)))

    # Plot grouped bars
    x = np.arange(len(models))
    width = 0.35

    bars1 = ax.bar(x - width/2, means_before, width, yerr=sems_before,
                   label='Before Alignment', color='lightgray', edgecolor='black')
    bars2 = ax.bar(x + width/2, means_after, width, yerr=sems_after,
                   label='After Alignment', color=[model_colors[m] for m in models],
                   edgecolor='black')

    # Chance level
    ax.axhline(1/8, color='red', linestyle='--', linewidth=1, label='Chance (12.5%)')

    ax.set_ylabel('Accuracy (within 45°)', fontweight='bold')
    ax.set_title('Classification Performance', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([model_labels[m] for m in models])
    ax.legend(loc='upper left')
    ax.set_ylim([0, 1])

    # Add percentage labels on bars
    for i, (bar, val) in enumerate(zip(bars1, means_before)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
               f'{val:.1%}', ha='center', va='bottom', fontsize=8)

    for i, (bar, val) in enumerate(zip(bars2, means_after)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
               f'{val:.1%}', ha='center', va='bottom', fontsize=8)

    # ========================================================================
    # Panel B: Reconstruction Error (MAE)
    # ========================================================================
    ax = axes[0, 1]

    # Aggregate MAE
    mae_before = aggregate_metrics(before_data, 'mae')
    mae_after = aggregate_metrics(after_data, 'mae')

    # Compute means and SEMs
    means_before = []
    sems_before = []
    means_after = []
    sems_after = []

    for model in models:
        values_before = []
        values_after = []

        for roi in rois:
            if model in mae_before[roi]:
                values_before.extend(mae_before[roi][model])
            if model in mae_after[roi]:
                values_after.extend(mae_after[roi][model])

        means_before.append(np.mean(values_before))
        sems_before.append(np.std(values_before) / np.sqrt(len(values_before)))

        means_after.append(np.mean(values_after))
        sems_after.append(np.std(values_after) / np.sqrt(len(values_after)))

    # Plot grouped bars (lower is better)
    bars1 = ax.bar(x - width/2, means_before, width, yerr=sems_before,
                   label='Before Alignment', color='lightgray', edgecolor='black')
    bars2 = ax.bar(x + width/2, means_after, width, yerr=sems_after,
                   label='After Alignment', color=[model_colors[m] for m in models],
                   edgecolor='black')

    # Random guess baseline (90 degrees)
    ax.axhline(90, color='red', linestyle='--', linewidth=1, label='Random (90°)')

    ax.set_ylabel('Mean Absolute Error (degrees)', fontweight='bold')
    ax.set_title('Reconstruction Error', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([model_labels[m] for m in models])
    ax.legend(loc='upper right')
    ax.set_ylim([0, 100])

    # Add value labels
    for bar, val in zip(bars1, means_before):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
               f'{val:.1f}°', ha='center', va='bottom', fontsize=8)

    for bar, val in zip(bars2, means_after):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
               f'{val:.1f}°', ha='center', va='bottom', fontsize=8)

    # ========================================================================
    # Panel C: Improvement by Alignment (Delta)
    # ========================================================================
    ax = axes[1, 0]

    # Compute improvement (after - before)
    acc_before_agg = aggregate_metrics(before_data, 'acc_45')
    acc_after_agg = aggregate_metrics(after_data, 'acc_45')

    improvements = []
    improvement_sems = []

    for model in models:
        deltas = []

        for roi in rois:
            if model in acc_before_agg[roi] and model in acc_after_agg[roi]:
                before_vals = np.array(acc_before_agg[roi][model])
                after_vals = np.array(acc_after_agg[roi][model])

                # Compute paired differences
                delta = after_vals - before_vals
                deltas.extend(delta)

        improvements.append(np.mean(deltas))
        improvement_sems.append(np.std(deltas) / np.sqrt(len(deltas)))

    # Plot
    bars = ax.bar(x, improvements, width=0.6, yerr=improvement_sems,
                  color=[model_colors[m] for m in models], edgecolor='black')

    ax.axhline(0, color='black', linestyle='-', linewidth=0.5)
    ax.set_ylabel('Improvement in Accuracy\n(After - Before)', fontweight='bold')
    ax.set_title('Alignment Effect', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([model_labels[m] for m in models])

    # Add value labels
    for bar, val in zip(bars, improvements):
        y_pos = val + (improvement_sems[bars.index(bar)] if val > 0 else -improvement_sems[bars.index(bar)])
        ax.text(bar.get_x() + bar.get_width()/2, y_pos,
               f'{val:+.1%}', ha='center', va='bottom' if val > 0 else 'top', fontsize=8)

    # ========================================================================
    # Panel D: Linear vs Non-linear Interaction
    # ========================================================================
    ax = axes[1, 1]

    # Group models
    linear_models = ['ridge', 'forward_encoding']
    nonlinear_models = ['mlp']

    # Compute group averages
    def compute_group_mean(models_list, data, metric='acc_45'):
        values = []
        for model in models_list:
            if model in data['models']:
                agg = aggregate_metrics(data, metric)
                for roi in data['rois']:
                    if model in agg[roi]:
                        values.extend(agg[roi][model])
        return np.mean(values), np.std(values) / np.sqrt(len(values))

    linear_before, linear_before_sem = compute_group_mean(linear_models, before_data)
    linear_after, linear_after_sem = compute_group_mean(linear_models, after_data)

    nonlinear_before, nonlinear_before_sem = compute_group_mean(nonlinear_models, before_data)
    nonlinear_after, nonlinear_after_sem = compute_group_mean(nonlinear_models, after_data)

    # Plot
    x_align = ['Before', 'After']
    x_pos = np.arange(len(x_align))

    width = 0.35

    ax.bar(x_pos - width/2, [linear_before, linear_after], width,
           yerr=[linear_before_sem, linear_after_sem],
           label='Linear Models', color='steelblue', edgecolor='black')

    ax.bar(x_pos + width/2, [nonlinear_before, nonlinear_after], width,
           yerr=[nonlinear_before_sem, nonlinear_after_sem],
           label='Non-linear Models', color='coral', edgecolor='black')

    ax.set_ylabel('Accuracy (within 45°)', fontweight='bold')
    ax.set_title('Linear vs Non-linear Models', fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(x_align)
    ax.legend()
    ax.set_ylim([0, 1])

    # Add interaction annotation
    delta_linear = linear_after - linear_before
    delta_nonlinear = nonlinear_after - nonlinear_before

    interaction_text = f'Δ Linear: {delta_linear:+.1%}\nΔ Non-linear: {delta_nonlinear:+.1%}'

    if delta_linear > delta_nonlinear:
        interaction_text += '\n\nAlignment helps\nlinear models more!'

    ax.text(0.98, 0.98, interaction_text,
            transform=ax.transAxes, ha='right', va='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7),
            fontsize=9)

    # ========================================================================
    # Save figure
    # ========================================================================
    plt.tight_layout()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    output_file = output_path / f'sub-{subject}_performance_comparison.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_file}")

    plt.close()


def plot_roi_comparison(before_data, after_data, output_dir, subject):
    """
    Plot performance by ROI

    Shows how alignment effect varies across visual areas
    """
    fig, axes = plt.subplots(1, len(before_data['rois']), figsize=(16, 4))
    fig.suptitle(f'ROI Comparison: sub-{subject}', fontsize=14, fontweight='bold')

    rois = before_data['rois']
    models = before_data['models']

    model_labels = {
        'ridge': 'Ridge',
        'forward_encoding': 'Forward',
        'mlp': 'MLP'
    }

    for roi_idx, roi in enumerate(rois):
        ax = axes[roi_idx]

        # Get data for this ROI
        acc_before = aggregate_metrics(before_data, 'acc_45')[roi]
        acc_after = aggregate_metrics(after_data, 'acc_45')[roi]

        # Compute means
        means_before = [np.mean(acc_before[m]) if m in acc_before else 0 for m in models]
        means_after = [np.mean(acc_after[m]) if m in acc_after else 0 for m in models]

        sems_before = [np.std(acc_before[m])/np.sqrt(len(acc_before[m])) if m in acc_before else 0 for m in models]
        sems_after = [np.std(acc_after[m])/np.sqrt(len(acc_after[m])) if m in acc_after else 0 for m in models]

        # Plot
        x = np.arange(len(models))
        width = 0.35

        ax.bar(x - width/2, means_before, width, yerr=sems_before,
               label='Before', color='lightgray', edgecolor='black')
        ax.bar(x + width/2, means_after, width, yerr=sems_after,
               label='After', color='steelblue', edgecolor='black')

        ax.axhline(1/8, color='red', linestyle='--', linewidth=1, alpha=0.5)

        ax.set_title(roi, fontweight='bold')
        ax.set_ylabel('Accuracy' if roi_idx == 0 else '')
        ax.set_xticks(x)
        ax.set_xticklabels([model_labels[m] for m in models], rotation=45, ha='right')
        ax.set_ylim([0, 1])

        if roi_idx == 0:
            ax.legend()

    plt.tight_layout()

    output_path = Path(output_dir)
    output_file = output_path / f'sub-{subject}_roi_comparison.png'
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_file}")

    plt.close()


def create_summary_table(before_data, after_data, output_dir, subject):
    """
    Create summary table with mean ± SEM for each model

    Saves to CSV and prints to console
    """
    import pandas as pd

    rois = before_data['rois']
    models = before_data['models']

    # Collect data
    summary_rows = []

    for model in models:
        for metric in ['acc_45', 'acc_90', 'mae', 'medae']:
            # Before alignment
            before_values = []
            for roi in rois:
                agg = aggregate_metrics(before_data, metric)[roi]
                if model in agg:
                    before_values.extend(agg[model])

            before_mean = np.mean(before_values)
            before_sem = np.std(before_values) / np.sqrt(len(before_values))

            # After alignment
            after_values = []
            for roi in rois:
                agg = aggregate_metrics(after_data, metric)[roi]
                if model in agg:
                    after_values.extend(agg[model])

            after_mean = np.mean(after_values)
            after_sem = np.std(after_values) / np.sqrt(len(after_values))

            # Improvement
            improvement = after_mean - before_mean

            # Statistical test (paired t-test)
            if len(before_values) == len(after_values):
                t_stat, p_value = stats.ttest_rel(after_values, before_values)
            else:
                t_stat, p_value = np.nan, np.nan

            summary_rows.append({
                'Model': model,
                'Metric': metric,
                'Before_Mean': before_mean,
                'Before_SEM': before_sem,
                'After_Mean': after_mean,
                'After_SEM': after_sem,
                'Improvement': improvement,
                'T_stat': t_stat,
                'P_value': p_value
            })

    df = pd.DataFrame(summary_rows)

    # Save to CSV
    output_path = Path(output_dir)
    csv_file = output_path / f'sub-{subject}_summary_table.csv'
    df.to_csv(csv_file, index=False)
    print(f"\nSaved summary table: {csv_file}")

    # Print to console
    print("\n" + "="*80)
    print(f"Summary Table: sub-{subject}")
    print("="*80)
    print(df.to_string(index=False))
    print("="*80)


def main():
    parser = argparse.ArgumentParser(
        description="Visualize decoder model comparison results"
    )
    parser.add_argument('--before_dir', type=str, required=True,
                       help='Directory with before alignment results')
    parser.add_argument('--after_dir', type=str, required=True,
                       help='Directory with after alignment results')
    parser.add_argument('--subject', type=str, required=True,
                       help='Subject ID (e.g., 01)')
    parser.add_argument('--output_dir', type=str, required=True,
                       help='Output directory for figures')

    args = parser.parse_args()

    # Load results
    print(f"\nLoading results for sub-{args.subject}...")
    before_data = load_results(args.before_dir, args.subject)
    after_data = load_results(args.after_dir, args.subject)

    # Create visualizations
    print("\nGenerating visualizations...")

    # Main performance comparison
    plot_performance_comparison(before_data, after_data, args.output_dir, args.subject)

    # ROI comparison
    plot_roi_comparison(before_data, after_data, args.output_dir, args.subject)

    # Summary table
    create_summary_table(before_data, after_data, args.output_dir, args.subject)

    print(f"\nVisualization complete! Figures saved to: {args.output_dir}\n")


if __name__ == '__main__':
    main()
