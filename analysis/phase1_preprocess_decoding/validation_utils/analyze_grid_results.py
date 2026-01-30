#!/usr/bin/env python3
"""
Analyze grid factorial experiment results.

Usage:
    python analyze_grid_results.py
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.dpi'] = 150

def load_results(results_file='results/grid_factorial/evaluation_summary.json'):
    """Load evaluation results."""
    with open(results_file) as f:
        results = json.load(f)
    return results

def prepare_dataframe(results):
    """Convert results to DataFrame with proper factor parsing."""
    records = []

    for condition_name, metrics in results.items():
        record = metrics.copy()
        record['condition_name'] = condition_name

        # Parse factors from stored values (already parsed in evaluate script)
        # But verify by parsing name as backup
        if 'grid_resample' not in record or pd.isna(record['grid_resample']):
            # Fallback parsing
            parts = condition_name.split('_')
            if len(parts) >= 5:
                record['grid_resample'] = parts[1]  # no or yes
                record['highpass'] = parts[2]  # hp0 or hp001
                record['motion'] = parts[3]  # none, standard, cosine
                record['drift'] = '_'.join(parts[4:])  # rest is drift

        records.append(record)

    df = pd.DataFrame(records)

    # Convert highpass to numeric
    df['highpass_hz'] = df['highpass'].map({'hp0': 0.0, 'hp001': 0.01})

    return df

def plot_factor_effects(df, output_dir='results/grid_factorial'):
    """Plot factor effects on RDM correlation (AFTER Procrustes)."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # Use AFTER Procrustes metrics
    metric = 'rdm_correlation_after'

    # Factor 1: Grid resampling
    sns.boxplot(x='grid_resample', y=metric, data=df, ax=axes[0,0])
    axes[0,0].set_title('Effect of Grid Resampling', fontsize=12, fontweight='bold')
    axes[0,0].set_ylabel('RDM Correlation (After Procrustes)')
    axes[0,0].set_xlabel('Grid Resample')

    # Factor 2: Highpass
    sns.boxplot(x='highpass', y=metric, data=df, ax=axes[0,1])
    axes[0,1].set_title('Effect of Highpass Filter', fontsize=12, fontweight='bold')
    axes[0,1].set_ylabel('RDM Correlation (After Procrustes)')
    axes[0,1].set_xlabel('Highpass')

    # Factor 3: Motion
    sns.boxplot(x='motion', y=metric, data=df, ax=axes[1,0])
    axes[1,0].set_title('Effect of Motion Confounds', fontsize=12, fontweight='bold')
    axes[1,0].set_ylabel('RDM Correlation (After Procrustes)')
    axes[1,0].set_xlabel('Motion')

    # Factor 4: Drift
    sns.boxplot(x='drift', y=metric, data=df, ax=axes[1,1])
    axes[1,1].set_title('Effect of Drift Modeling', fontsize=12, fontweight='bold')
    axes[1,1].set_ylabel('RDM Correlation (After Procrustes)')
    axes[1,1].set_xlabel('Drift')
    axes[1,1].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    output_path = Path(output_dir) / 'factor_effects_rdm_correlation.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")

def plot_procrustes_before_after(df, output_dir='results/grid_factorial'):
    """Plot metrics before and after Procrustes alignment."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    metrics = [
        ('rdm_correlation', 'RDM Correlation'),
        ('rdm_crossnobis', 'RDM Crossnobis'),
        ('decoding_accuracy', 'Decoding Accuracy')
    ]

    for ax, (metric_base, label) in zip(axes, metrics):
        before_col = f'{metric_base}_before'
        after_col = f'{metric_base}_after'

        # Before vs After scatter
        ax.scatter(df[before_col], df[after_col], alpha=0.6, s=80,
                  c=df['grid_resample'].map({'no': 'red', 'yes': 'blue'}))
        ax.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='No change')

        # Add diagonal reference for improvement
        ax.axhline(y=df[after_col].mean(), color='gray', linestyle=':', alpha=0.5)
        ax.axvline(x=df[before_col].mean(), color='gray', linestyle=':', alpha=0.5)

        ax.set_xlabel(f'{label} (Before Procrustes)', fontsize=11)
        ax.set_ylabel(f'{label} (After Procrustes)', fontsize=11)
        ax.set_title(f'Procrustes Effect on {label}', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='red', alpha=0.6, label='Grid resample: no'),
            Patch(facecolor='blue', alpha=0.6, label='Grid resample: yes')
        ]
        ax.legend(handles=legend_elements, loc='lower right', fontsize=9)

    plt.tight_layout()
    output_path = Path(output_dir) / 'procrustes_before_after.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")


def plot_procrustes_improvements(df, output_dir='results/grid_factorial'):
    """Plot distribution of Procrustes improvements."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    improvements = [
        ('rdm_correlation_improvement', 'RDM Correlation Δ'),
        ('rdm_crossnobis_improvement', 'RDM Crossnobis Δ'),
        ('decoding_improvement', 'Decoding Accuracy Δ')
    ]

    for ax, (metric, label) in zip(axes, improvements):
        # Boxplot by grid resampling
        sns.boxplot(x='grid_resample', y=metric, data=df, ax=ax)
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5, label='No change')

        ax.set_xlabel('Grid Resample', fontsize=11)
        ax.set_ylabel(f'{label}', fontsize=11)
        ax.set_title(f'Procrustes Improvement: {label}', fontsize=12, fontweight='bold')
        ax.legend()

        # Add mean text
        for i, resample in enumerate(['no', 'yes']):
            subset = df[df['grid_resample'] == resample][metric]
            mean_val = subset.mean()
            positive_pct = 100 * (subset > 0).sum() / len(subset)
            ax.text(i, ax.get_ylim()[1] * 0.9,
                   f'Mean: {mean_val:+.4f}\n{positive_pct:.0f}% positive',
                   ha='center', va='top', fontsize=9, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    output_path = Path(output_dir) / 'procrustes_improvements.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")


def plot_crossnobis_comparison(df, output_dir='results/grid_factorial'):
    """Compare correlation vs crossnobis RDMs (AFTER Procrustes)."""
    fig, ax = plt.subplots(figsize=(8, 8))

    ax.scatter(df['rdm_correlation_after'], df['rdm_crossnobis_after'], alpha=0.6, s=80)
    ax.plot([0, 1], [0, 1], 'k--', alpha=0.3, label='Identity')

    ax.set_xlabel('RDM Correlation Reliability (After)', fontsize=12)
    ax.set_ylabel('RDM Crossnobis Reliability (After)', fontsize=12)
    ax.set_title('Correlation vs Crossnobis RDM Reliability', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    output_path = Path(output_dir) / 'correlation_vs_crossnobis.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")

def plot_procrustes_effect(df, output_dir='results/grid_factorial'):
    """Plot Procrustes disparity by grid resampling."""
    fig, ax = plt.subplots(figsize=(10, 6))

    # Log scale for disparity
    df_plot = df.copy()
    df_plot['log_disparity'] = np.log10(df_plot['procrustes_disparity'])

    sns.boxplot(x='grid_resample', y='log_disparity', data=df_plot, ax=ax)
    ax.set_title('Procrustes Disparity: Grid Resampling Effect', fontsize=14, fontweight='bold')
    ax.set_ylabel('Log10(Procrustes Disparity)', fontsize=12)
    ax.set_xlabel('Grid Resample', fontsize=12)

    # Add actual values as text
    for i, resample in enumerate(['no', 'yes']):
        subset = df[df['grid_resample'] == resample]
        median_disp = subset['procrustes_disparity'].median()
        ax.text(i, ax.get_ylim()[1] * 0.95, f'Median: {median_disp:.2f}',
                ha='center', va='top', fontsize=10, fontweight='bold')

    plt.tight_layout()
    output_path = Path(output_dir) / 'procrustes_disparity.png'
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")

def print_factor_effects(df):
    """Print statistical comparison of factor effects."""
    print("\n" + "="*80)
    print("Factor Effects Summary (AFTER Procrustes)")
    print("="*80)

    metrics = ['rdm_correlation_after', 'rdm_crossnobis_after', 'decoding_accuracy_after', 'procrustes_disparity']

    for metric in metrics:
        print(f"\n{metric.upper()}:")
        print("-" * 80)

        # Grid resampling effect
        print("\nGrid Resampling:")
        for value in ['no', 'yes']:
            subset = df[df['grid_resample'] == value][metric]
            print(f"  {value:6s}: mean={subset.mean():.4f}, std={subset.std():.4f}, "
                  f"median={subset.median():.4f}, n={len(subset)}")

        # Motion effect
        print("\nMotion:")
        for value in ['none', 'standard', 'cosine']:
            subset = df[df['motion'] == value][metric]
            if len(subset) > 0:
                print(f"  {value:8s}: mean={subset.mean():.4f}, std={subset.std():.4f}, "
                      f"median={subset.median():.4f}, n={len(subset)}")

        # Highpass effect
        print("\nHighpass:")
        for value in ['hp0', 'hp001']:
            subset = df[df['highpass'] == value][metric]
            print(f"  {value:6s}: mean={subset.mean():.4f}, std={subset.std():.4f}, "
                  f"median={subset.median():.4f}, n={len(subset)}")

        # Drift effect
        print("\nDrift:")
        for value in df['drift'].unique():
            subset = df[df['drift'] == value][metric]
            if len(subset) > 0:
                print(f"  {value:12s}: mean={subset.mean():.4f}, std={subset.std():.4f}, "
                      f"median={subset.median():.4f}, n={len(subset)}")

def find_best_conditions(df):
    """Find best performing conditions."""
    print("\n" + "="*80)
    print("Best Performing Conditions")
    print("="*80)

    # Best by each metric (AFTER Procrustes)
    metrics = {
        'rdm_correlation_after': 'max',
        'rdm_crossnobis_after': 'max',
        'decoding_accuracy_after': 'max',
        'procrustes_disparity': 'min',
        'shrinkage': 'optimal'  # Around 0.2-0.4
    }

    for metric, criterion in metrics.items():
        print(f"\n{metric.upper()}:")

        if criterion == 'max':
            best_idx = df[metric].idxmax()
            best_val = df[metric].max()
        elif criterion == 'min':
            best_idx = df[metric].idxmin()
            best_val = df[metric].min()
        else:  # optimal shrinkage
            # Find closest to 0.3
            best_idx = (df[metric] - 0.3).abs().idxmin()
            best_val = df.loc[best_idx, metric]

        best_row = df.loc[best_idx]

        print(f"  Best condition: {best_row['condition_name']}")
        print(f"  Value: {best_val:.4f}")
        print(f"  Factors:")
        print(f"    Grid resample: {best_row['grid_resample']}")
        print(f"    Highpass: {best_row['highpass']}")
        print(f"    Motion: {best_row['motion']}")
        print(f"    Drift: {best_row['drift']}")
        print(f"  All metrics (AFTER Procrustes):")
        print(f"    RDM correlation: {best_row['rdm_correlation_after']:.4f}")
        print(f"    RDM crossnobis: {best_row['rdm_crossnobis_after']:.4f}")
        print(f"    Decoding: {best_row['decoding_accuracy_after']:.4f}")
        print(f"    Procrustes: {best_row['procrustes_disparity']:.4f}")

    # Best improvements
    print(f"\nBEST IMPROVEMENTS (from Procrustes):")
    improvement_metrics = {
        'rdm_correlation_improvement': ('rdm_correlation_before', 'rdm_correlation_after'),
        'rdm_crossnobis_improvement': ('rdm_crossnobis_before', 'rdm_crossnobis_after'),
        'decoding_improvement': ('decoding_accuracy_before', 'decoding_accuracy_after')
    }

    for metric, (before_col, after_col) in improvement_metrics.items():
        best_idx = df[metric].idxmax()
        best_row = df.loc[best_idx]
        print(f"\n  {metric}:")
        print(f"    Best condition: {best_row['condition_name']}")
        print(f"    Improvement: {best_row[metric]:+.4f}")
        print(f"    Before: {best_row[before_col]:.4f}")
        print(f"    After:  {best_row[after_col]:.4f}")

    # Overall best (composite score using AFTER metrics)
    print(f"\nOVERALL BEST (composite score AFTER Procrustes):")
    print("  Ranking by: (rdm_crossnobis_after + decoding_accuracy_after) / (procrustes_disparity + 1)")

    df['composite_score'] = (df['rdm_crossnobis_after'] + df['decoding_accuracy_after']) / (df['procrustes_disparity'] + 1)
    best_overall_idx = df['composite_score'].idxmax()
    best_overall = df.loc[best_overall_idx]

    print(f"  Best condition: {best_overall['condition_name']}")
    print(f"  Composite score: {best_overall['composite_score']:.6f}")
    print(f"  Factors:")
    print(f"    Grid resample: {best_overall['grid_resample']}")
    print(f"    Highpass: {best_overall['highpass']}")
    print(f"    Motion: {best_overall['motion']}")
    print(f"    Drift: {best_overall['drift']}")
    print(f"  Metrics (AFTER Procrustes):")
    print(f"    RDM crossnobis: {best_overall['rdm_crossnobis_after']:.4f}")
    print(f"    Decoding: {best_overall['decoding_accuracy_after']:.4f}")
    print(f"    Procrustes: {best_overall['procrustes_disparity']:.4f}")
    print(f"    Shrinkage: {best_overall['shrinkage']:.4f}")
    print(f"  Improvements:")
    print(f"    RDM crossnobis: {best_overall['rdm_crossnobis_improvement']:+.4f}")
    print(f"    Decoding: {best_overall['decoding_improvement']:+.4f}")

def main():
    """Main analysis pipeline."""
    print("="*80)
    print("Grid Factorial Results Analysis")
    print("="*80)

    # Load results
    results = load_results()
    print(f"\nLoaded {len(results)} conditions")

    # Prepare DataFrame
    df = prepare_dataframe(results)
    print(f"DataFrame shape: {df.shape}")

    # Check for NaN
    nan_counts = df.isna().sum()
    if nan_counts.any():
        print("\nWarning: NaN values found:")
        print(nan_counts[nan_counts > 0])

    # Summary statistics
    print("\n" + "="*80)
    print("Summary Statistics")
    print("="*80)

    print("\nBEFORE Procrustes:")
    metrics_before = ['rdm_correlation_before', 'rdm_crossnobis_before', 'decoding_accuracy_before']
    for metric in metrics_before:
        values = df[metric].dropna()
        if len(values) > 0:
            print(f"  {metric}:")
            print(f"    Mean:   {values.mean():.4f}")
            print(f"    Median: {values.median():.4f}")
            print(f"    Min:    {values.min():.4f}")
            print(f"    Max:    {values.max():.4f}")

    print("\nAFTER Procrustes:")
    metrics_after = ['rdm_correlation_after', 'rdm_crossnobis_after', 'decoding_accuracy_after']
    for metric in metrics_after:
        values = df[metric].dropna()
        if len(values) > 0:
            print(f"  {metric}:")
            print(f"    Mean:   {values.mean():.4f}")
            print(f"    Median: {values.median():.4f}")
            print(f"    Min:    {values.min():.4f}")
            print(f"    Max:    {values.max():.4f}")

    print("\nProcrustes IMPROVEMENTS:")
    metrics_improvement = ['rdm_correlation_improvement', 'rdm_crossnobis_improvement', 'decoding_improvement']
    for metric in metrics_improvement:
        values = df[metric].dropna()
        if len(values) > 0:
            positive_count = (values > 0).sum()
            print(f"  {metric}:")
            print(f"    Mean:     {values.mean():+.4f}")
            print(f"    Median:   {values.median():+.4f}")
            print(f"    Positive: {positive_count}/{len(values)} ({100*positive_count/len(values):.1f}%)")

    print("\nOther Metrics:")
    other_metrics = ['procrustes_disparity', 'shrinkage']
    for metric in other_metrics:
        values = df[metric].dropna()
        if len(values) > 0:
            print(f"  {metric}:")
            print(f"    Mean:   {values.mean():.4f}")
            print(f"    Median: {values.median():.4f}")

    # Factor effects
    print_factor_effects(df)

    # Best conditions
    find_best_conditions(df)

    # Plots
    print("\n" + "="*80)
    print("Generating Plots")
    print("="*80)

    plot_factor_effects(df)  # Factor effects on RDM (after Procrustes)
    plot_procrustes_before_after(df)  # Before/After scatter plots
    plot_procrustes_improvements(df)  # Improvement distributions
    plot_crossnobis_comparison(df)  # Correlation vs Crossnobis
    plot_procrustes_effect(df)  # Procrustes disparity

    # Save processed DataFrame
    output_file = 'results/grid_factorial/results_dataframe.csv'
    df.to_csv(output_file, index=False)
    print(f"\nSaved DataFrame: {output_file}")

    print("\n" + "="*80)
    print("✅ Analysis complete!")
    print("="*80)

if __name__ == '__main__':
    main()
