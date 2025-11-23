#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_fir_simple_results.py
----------------------------------
Analyze and compare results from different FIR-only strategies

Usage:
    python analyze_fir_simple_results.py --timestamp 20250120_123456

Created: 2025-01-20
"""

import argparse
import json
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns

# ============================================================================
# Parse Arguments
# ============================================================================

parser = argparse.ArgumentParser()
parser.add_argument('--timestamp', type=str, required=True,
                    help='Timestamp of the analysis run')
args = parser.parse_args()

TIMESTAMP = args.timestamp

# ============================================================================
# Collect Results
# ============================================================================

SUBJECTS = ["01", "02", "03", "04"]
ROIS = ["V1", "V2", "V3", "hV4"]
STRATEGIES = ["flatten", "average", "delay3", "delay4", "delay5"]
PCA_VARIANTS = ["", "_pca6"]

print("="*70)
print("FIR-Only Strategy Comparison")
print("="*70)
print(f"Timestamp: {TIMESTAMP}")
print()

results_data = []

for subject in SUBJECTS:
    subject_prefix = f"sub-{subject}"

    for roi in ROIS:
        for strategy in STRATEGIES:
            for pca_var in PCA_VARIANTS:
                # Build path
                result_dir = Path(f"derivatives/fir_simple/{subject_prefix}/{TIMESTAMP}_{roi}_{strategy}{pca_var}")
                summary_file = result_dir / "summary.json"

                if not summary_file.exists():
                    continue

                # Load results
                with open(summary_file, 'r') as f:
                    data = json.load(f)

                results_data.append({
                    'subject': subject,
                    'roi': roi,
                    'strategy': strategy,
                    'use_pca': (pca_var != ""),
                    'n_voxels': data['n_voxels'],
                    'mean_accuracy': data['mean_accuracy'],
                })

if len(results_data) == 0:
    print("ERROR: No results found!")
    print(f"Looking for: derivatives/fir_simple/{{subject}}/{TIMESTAMP}_{{roi}}_{{strategy}}_{{pca}}/summary.json")
    exit(1)

df = pd.DataFrame(results_data)

print(f"Found {len(df)} results")
print()

# ============================================================================
# Analysis
# ============================================================================

# 1. Overall summary
print("="*70)
print("Overall Performance Summary")
print("="*70)

summary_stats = df.groupby(['strategy', 'use_pca'])['mean_accuracy'].agg([
    ('mean', 'mean'),
    ('std', 'std'),
    ('min', 'min'),
    ('max', 'max'),
    ('count', 'count')
]).reset_index()

print(summary_stats.to_string(index=False))
print()

# 2. Best strategy per subject/ROI
print("="*70)
print("Best Strategy Per Subject × ROI")
print("="*70)

best_results = df.loc[df.groupby(['subject', 'roi'])['mean_accuracy'].idxmax()]
print(best_results[['subject', 'roi', 'strategy', 'use_pca', 'mean_accuracy']].to_string(index=False))
print()

# 3. Strategy comparison (average across subjects/ROIs)
print("="*70)
print("Strategy Comparison (Average Across All)")
print("="*70)

strategy_avg = df.groupby(['strategy', 'use_pca'])['mean_accuracy'].mean().unstack(fill_value=0)
print(strategy_avg)
print()

# ============================================================================
# Visualization
# ============================================================================

output_dir = Path(f"derivatives/fir_simple/summary/{TIMESTAMP}")
output_dir.mkdir(parents=True, exist_ok=True)

print("Creating visualizations...")

# Plot 1: Strategy comparison heatmap
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

for idx, use_pca in enumerate([False, True]):
    df_subset = df[df['use_pca'] == use_pca]
    pivot = df_subset.pivot_table(values='mean_accuracy',
                                   index='roi',
                                   columns='strategy',
                                   aggfunc='mean')

    sns.heatmap(pivot, annot=True, fmt='.3f', cmap='RdYlGn',
                vmin=0.125, vmax=1.0, ax=axes[idx],
                cbar_kws={'label': 'Accuracy'})
    axes[idx].set_title(f'{"With PCA (n=6)" if use_pca else "Without PCA"}',
                        fontsize=14, fontweight='bold')
    axes[idx].set_xlabel('Strategy')
    axes[idx].set_ylabel('ROI')

plt.suptitle('FIR-Only Strategy Comparison: Mean Accuracy Across Subjects',
             fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(output_dir / 'strategy_comparison_heatmap.png', dpi=300)
plt.close()

# Plot 2: Bar plot comparison
fig, ax = plt.subplots(figsize=(14, 7))

df_plot = df.copy()
df_plot['strategy_pca'] = df_plot['strategy'] + df_plot['use_pca'].apply(lambda x: ' (PCA)' if x else '')

grouped = df_plot.groupby('strategy_pca')['mean_accuracy'].agg(['mean', 'std']).reset_index()
grouped = grouped.sort_values('mean', ascending=False)

bars = ax.bar(range(len(grouped)), grouped['mean'],
              yerr=grouped['std'], capsize=5,
              edgecolor='black', alpha=0.7)

# Color code by strategy
colors = plt.cm.Set3(np.linspace(0, 1, len(STRATEGIES)))
color_map = {s: colors[i] for i, s in enumerate(STRATEGIES)}

for i, (_, row) in enumerate(grouped.iterrows()):
    strategy_base = row['strategy_pca'].replace(' (PCA)', '')
    bars[i].set_color(color_map[strategy_base])

ax.axhline(0.125, color='red', linestyle=':', linewidth=2, label='Chance (12.5%)')
ax.set_xticks(range(len(grouped)))
ax.set_xticklabels(grouped['strategy_pca'], rotation=45, ha='right')
ax.set_ylabel('Mean Classification Accuracy', fontsize=12)
ax.set_title('FIR-Only Strategy Performance (Mean ± Std Across All Subjects × ROIs)',
             fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')
ax.set_ylim([0, 1])

plt.tight_layout()
plt.savefig(output_dir / 'strategy_comparison_bars.png', dpi=300)
plt.close()

# Plot 3: Subject-wise comparison
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
axes = axes.ravel()

for idx, subject in enumerate(SUBJECTS):
    df_sub = df[df['subject'] == subject]

    # Pivot for heatmap
    pivot = df_sub.pivot_table(values='mean_accuracy',
                               index='roi',
                               columns=['strategy', 'use_pca'])

    # Create grouped bar plot instead of heatmap
    strategies_ordered = []
    means = []

    for strategy in STRATEGIES:
        for use_pca in [False, True]:
            row = df_sub[(df_sub['strategy'] == strategy) & (df_sub['use_pca'] == use_pca)]
            if len(row) > 0:
                mean_val = row.groupby('roi')['mean_accuracy'].mean().mean()
                strategies_ordered.append(f"{strategy}{' (PCA)' if use_pca else ''}")
                means.append(mean_val)

    axes[idx].bar(range(len(means)), means, edgecolor='black', alpha=0.7)
    axes[idx].axhline(0.125, color='red', linestyle=':', linewidth=2, alpha=0.5)
    axes[idx].set_xticks(range(len(strategies_ordered)))
    axes[idx].set_xticklabels(strategies_ordered, rotation=45, ha='right', fontsize=8)
    axes[idx].set_ylabel('Mean Accuracy')
    axes[idx].set_title(f'Subject {subject}', fontweight='bold')
    axes[idx].set_ylim([0, 1])
    axes[idx].grid(True, alpha=0.3, axis='y')

plt.suptitle('FIR-Only Strategy Performance by Subject', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(output_dir / 'strategy_comparison_by_subject.png', dpi=300)
plt.close()

# Plot 4: ROI comparison
fig, axes = plt.subplots(2, 2, figsize=(16, 12))
axes = axes.ravel()

for idx, roi in enumerate(ROIS):
    df_roi = df[df['roi'] == roi]

    grouped_roi = df_roi.groupby(['strategy', 'use_pca'])['mean_accuracy'].mean().unstack(fill_value=0)

    x = np.arange(len(grouped_roi))
    width = 0.35

    bars1 = axes[idx].bar(x - width/2, grouped_roi[False], width,
                          label='No PCA', alpha=0.8, edgecolor='black')
    bars2 = axes[idx].bar(x + width/2, grouped_roi[True], width,
                          label='PCA (n=6)', alpha=0.8, edgecolor='black')

    axes[idx].axhline(0.125, color='red', linestyle=':', linewidth=2, alpha=0.5)
    axes[idx].set_xticks(x)
    axes[idx].set_xticklabels(grouped_roi.index, rotation=45, ha='right')
    axes[idx].set_ylabel('Mean Accuracy')
    axes[idx].set_title(f'{roi}', fontweight='bold')
    axes[idx].legend()
    axes[idx].set_ylim([0, 1])
    axes[idx].grid(True, alpha=0.3, axis='y')

plt.suptitle('FIR-Only Strategy Performance by ROI', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(output_dir / 'strategy_comparison_by_roi.png', dpi=300)
plt.close()

print(f"  Saved to: {output_dir}")
print()

# ============================================================================
# Save Summary
# ============================================================================

print("Saving summary...")

# Save full results table
df.to_csv(output_dir / 'all_results.csv', index=False)

# Save best results
best_results.to_csv(output_dir / 'best_per_subject_roi.csv', index=False)

# Save strategy averages
strategy_avg.to_csv(output_dir / 'strategy_averages.csv')

print()
print("="*70)
print("Complete!")
print("="*70)
print(f"Results saved to: {output_dir}")
print()

# Final recommendations
print("="*70)
print("Recommendations:")
print("="*70)

best_overall = summary_stats.loc[summary_stats['mean'].idxmax()]
print(f"\nBest overall strategy: {best_overall['strategy']} " +
      f"{'with PCA' if best_overall['use_pca'] else 'without PCA'}")
print(f"  Mean accuracy: {best_overall['mean']:.3f} ± {best_overall['std']:.3f}")
print(f"  Range: [{best_overall['min']:.3f}, {best_overall['max']:.3f}]")
print()
