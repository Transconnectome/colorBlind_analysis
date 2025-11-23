#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_fir_preprocessing_results.py
----------------------------------
Analyze preprocessing parameter effects on FIR GLM performance

Usage:
    python analyze_fir_preprocessing_results.py --timestamp 20250120_123456

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
parser.add_argument('--timestamp', type=str, required=True)
args = parser.parse_args()

TIMESTAMP = args.timestamp

# ============================================================================
# Configuration
# ============================================================================

SUBJECTS = ["01", "02", "03", "04"]
ROIS = ["V1", "V2", "V3", "hV4"]
STRATEGIES = ["flatten", "average", "delay4"]
CONFIGS = [1, 2, 3, 4, 5, 6]
CONFIG_NAMES = {
    1: "baseline",
    2: "spm_default",
    3: "conservative_mvpa",
    4: "nosmooth_mvpa",
    5: "poly_drift",
    6: "minimal"
}
PCA_VARIANTS = [False, True]

print("="*80)
print("FIR GLM - Preprocessing Parameter Analysis")
print("="*80)
print(f"Timestamp: {TIMESTAMP}")
print()

# ============================================================================
# Collect Results
# ============================================================================

results_data = []

for subject in SUBJECTS:
    for roi in ROIS:
        for strategy in STRATEGIES:
            for config_id in CONFIGS:
                for use_pca in PCA_VARIANTS:
                    pca_suffix = f"_pca6" if use_pca else ""
                    result_dir = Path(f"derivatives/fir_preprocessing/sub-{subject}/{TIMESTAMP}_{roi}_{strategy}_cfg{config_id}{pca_suffix}")
                    summary_file = result_dir / "summary.json"

                    if not summary_file.exists():
                        continue

                    with open(summary_file, 'r') as f:
                        data = json.load(f)

                    results_data.append({
                        'subject': subject,
                        'roi': roi,
                        'strategy': strategy,
                        'config_id': config_id,
                        'config_name': CONFIG_NAMES[config_id],
                        'use_pca': use_pca,
                        'n_voxels': data['n_voxels'],
                        'mean_accuracy': data['mean_accuracy'],
                        'smoothing': data['preprocessing']['smoothing_fwhm'],
                        'high_pass': data['preprocessing']['high_pass'],
                        'drift_model': data['preprocessing']['drift_model'],
                    })

if len(results_data) == 0:
    print("ERROR: No results found!")
    exit(1)

df = pd.DataFrame(results_data)
print(f"Found {len(df)} results")
print()

# ============================================================================
# Analysis 1: Overall Performance by Config
# ============================================================================

print("="*80)
print("Performance by Preprocessing Config")
print("="*80)

config_summary = df.groupby(['config_id', 'config_name', 'use_pca'])['mean_accuracy'].agg([
    ('mean', 'mean'),
    ('std', 'std'),
    ('min', 'min'),
    ('max', 'max')
]).reset_index()

print(config_summary.to_string(index=False))
print()

# ============================================================================
# Analysis 2: Best Config per Strategy
# ============================================================================

print("="*80)
print("Best Config per Strategy")
print("="*80)

for strategy in STRATEGIES:
    df_strategy = df[df['strategy'] == strategy]
    best_idx = df_strategy['mean_accuracy'].idxmax()
    best_row = df_strategy.loc[best_idx]

    print(f"\n{strategy.upper()}:")
    print(f"  Best: Config {best_row['config_id']} ({best_row['config_name']})")
    print(f"  PCA: {best_row['use_pca']}")
    print(f"  Accuracy: {best_row['mean_accuracy']:.3f}")
    print(f"  Smoothing: {best_row['smoothing']} mm")
    print(f"  High-pass: {best_row['high_pass']}")
    print(f"  Drift: {best_row['drift_model']}")

print()

# ============================================================================
# Analysis 3: Effect of Individual Parameters
# ============================================================================

print("="*80)
print("Effect of Individual Preprocessing Parameters")
print("="*80)

# Smoothing effect
print("\n1. Smoothing Effect:")
smoothing_effect = df.groupby('smoothing')['mean_accuracy'].agg(['mean', 'std', 'count'])
print(smoothing_effect)

# High-pass effect
print("\n2. High-pass Filtering Effect:")
highpass_effect = df.groupby('high_pass')['mean_accuracy'].agg(['mean', 'std', 'count'])
print(highpass_effect)

# Drift model effect
print("\n3. Drift Model Effect:")
drift_effect = df.groupby('drift_model')['mean_accuracy'].agg(['mean', 'std', 'count'])
print(drift_effect)

# PCA effect
print("\n4. PCA Effect:")
pca_effect = df.groupby('use_pca')['mean_accuracy'].agg(['mean', 'std'])
print(pca_effect)

print()

# ============================================================================
# Visualization
# ============================================================================

output_dir = Path(f"derivatives/fir_preprocessing/summary/{TIMESTAMP}")
output_dir.mkdir(parents=True, exist_ok=True)

print("Creating visualizations...")

# Plot 1: Config comparison heatmap
fig, axes = plt.subplots(3, 2, figsize=(16, 18))

for strat_idx, strategy in enumerate(STRATEGIES):
    for pca_idx, use_pca in enumerate([False, True]):
        ax = axes[strat_idx, pca_idx]

        df_subset = df[(df['strategy'] == strategy) & (df['use_pca'] == use_pca)]
        pivot = df_subset.pivot_table(
            values='mean_accuracy',
            index='roi',
            columns='config_name',
            aggfunc='mean'
        )

        # Reorder columns
        col_order = ['baseline', 'spm_default', 'conservative_mvpa',
                     'nosmooth_mvpa', 'poly_drift', 'minimal']
        pivot = pivot[[c for c in col_order if c in pivot.columns]]

        sns.heatmap(pivot, annot=True, fmt='.3f', cmap='RdYlGn',
                    vmin=0.125, vmax=1.0, ax=ax,
                    cbar_kws={'label': 'Accuracy'})

        title = f"{strategy.upper()}"
        if use_pca:
            title += " + PCA"
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.set_xlabel('Preprocessing Config')
        ax.set_ylabel('ROI')

plt.suptitle('Preprocessing Config Comparison Across Strategies',
             fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(output_dir / 'config_comparison_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: Parameter effects
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Smoothing effect
ax = axes[0, 0]
smoothing_data = df.groupby(['smoothing', 'use_pca'])['mean_accuracy'].mean().unstack()
smoothing_data.plot(kind='bar', ax=ax, rot=0)
ax.axhline(0.125, color='red', linestyle=':', linewidth=2, alpha=0.5)
ax.set_xlabel('Smoothing FWHM (mm)')
ax.set_ylabel('Mean Accuracy')
ax.set_title('Effect of Smoothing', fontweight='bold')
ax.legend(['No PCA', 'PCA (n=6)'])
ax.grid(True, alpha=0.3, axis='y')

# High-pass effect
ax = axes[0, 1]
highpass_data = df.copy()
highpass_data['high_pass_str'] = highpass_data['high_pass'].apply(
    lambda x: 'None' if x is None else f'{x:.6f}'
)
hp_grouped = highpass_data.groupby(['high_pass_str', 'use_pca'])['mean_accuracy'].mean().unstack()
hp_grouped.plot(kind='bar', ax=ax, rot=45)
ax.axhline(0.125, color='red', linestyle=':', linewidth=2, alpha=0.5)
ax.set_xlabel('High-pass Filter (Hz)')
ax.set_ylabel('Mean Accuracy')
ax.set_title('Effect of High-pass Filtering', fontweight='bold')
ax.legend(['No PCA', 'PCA (n=6)'])
ax.grid(True, alpha=0.3, axis='y')

# Drift model effect
ax = axes[1, 0]
drift_data = df.groupby(['drift_model', 'use_pca'])['mean_accuracy'].mean().unstack()
drift_data.plot(kind='bar', ax=ax, rot=0)
ax.axhline(0.125, color='red', linestyle=':', linewidth=2, alpha=0.5)
ax.set_xlabel('Drift Model')
ax.set_ylabel('Mean Accuracy')
ax.set_title('Effect of Drift Modeling', fontweight='bold')
ax.legend(['No PCA', 'PCA (n=6)'])
ax.grid(True, alpha=0.3, axis='y')

# Config comparison
ax = axes[1, 1]
config_data = df.groupby(['config_name', 'use_pca'])['mean_accuracy'].mean().unstack()
# Reorder
config_order = ['baseline', 'spm_default', 'conservative_mvpa',
                'nosmooth_mvpa', 'poly_drift', 'minimal']
config_data = config_data.reindex([c for c in config_order if c in config_data.index])
config_data.plot(kind='bar', ax=ax, rot=45)
ax.axhline(0.125, color='red', linestyle=':', linewidth=2, alpha=0.5)
ax.set_xlabel('Preprocessing Config')
ax.set_ylabel('Mean Accuracy')
ax.set_title('Overall Config Comparison', fontweight='bold')
ax.legend(['No PCA', 'PCA (n=6)'])
ax.grid(True, alpha=0.3, axis='y')

plt.suptitle('Preprocessing Parameter Effects on Classification Performance',
             fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(output_dir / 'parameter_effects.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 3: Strategy × Config interaction
fig, ax = plt.subplots(figsize=(14, 7))

for strategy in STRATEGIES:
    df_strat = df[df['use_pca'] == False]  # Without PCA for clarity
    strat_data = df_strat[df_strat['strategy'] == strategy].groupby('config_name')['mean_accuracy'].mean()
    # Reorder
    strat_data = strat_data.reindex([c for c in config_order if c in strat_data.index])
    ax.plot(range(len(strat_data)), strat_data.values, 'o-', linewidth=2,
            markersize=8, label=strategy.upper())

ax.axhline(0.125, color='red', linestyle=':', linewidth=2, alpha=0.5, label='Chance')
ax.set_xticks(range(len(config_order)))
ax.set_xticklabels(config_order, rotation=45, ha='right')
ax.set_xlabel('Preprocessing Config')
ax.set_ylabel('Mean Accuracy')
ax.set_title('Strategy × Preprocessing Config Interaction (Without PCA)',
             fontsize=14, fontweight='bold')
ax.legend()
ax.grid(True, alpha=0.3)
ax.set_ylim([0, 1])

plt.tight_layout()
plt.savefig(output_dir / 'strategy_config_interaction.png', dpi=300, bbox_inches='tight')
plt.close()

print(f"  Saved to: {output_dir}")
print()

# ============================================================================
# Save Results
# ============================================================================

print("Saving summary tables...")

df.to_csv(output_dir / 'all_results.csv', index=False)

# Best per strategy
best_per_strategy = []
for strategy in STRATEGIES:
    df_strat = df[df['strategy'] == strategy]
    best_idx = df_strat['mean_accuracy'].idxmax()
    best_per_strategy.append(df_strat.loc[best_idx])

pd.DataFrame(best_per_strategy).to_csv(output_dir / 'best_per_strategy.csv', index=False)

# Parameter effects
with open(output_dir / 'parameter_effects.txt', 'w') as f:
    f.write("SMOOTHING EFFECT\n")
    f.write("=" * 50 + "\n")
    f.write(smoothing_effect.to_string())
    f.write("\n\n")

    f.write("HIGH-PASS FILTERING EFFECT\n")
    f.write("=" * 50 + "\n")
    f.write(highpass_effect.to_string())
    f.write("\n\n")

    f.write("DRIFT MODEL EFFECT\n")
    f.write("=" * 50 + "\n")
    f.write(drift_effect.to_string())
    f.write("\n\n")

    f.write("PCA EFFECT\n")
    f.write("=" * 50 + "\n")
    f.write(pca_effect.to_string())
    f.write("\n")

print()
print("="*80)
print("Complete!")
print("="*80)
print(f"\nResults saved to: {output_dir}")

# Final recommendation
print()
print("="*80)
print("RECOMMENDATIONS")
print("="*80)

best_overall = df.loc[df['mean_accuracy'].idxmax()]
print(f"\nBest overall:")
print(f"  Config: {best_overall['config_id']} ({best_overall['config_name']})")
print(f"  Strategy: {best_overall['strategy']}")
print(f"  PCA: {best_overall['use_pca']}")
print(f"  Accuracy: {best_overall['mean_accuracy']:.3f}")
print(f"  Subject: {best_overall['subject']}, ROI: {best_overall['roi']}")

print(f"\nPreprocessing settings:")
print(f"  Smoothing: {best_overall['smoothing']} mm")
print(f"  High-pass: {best_overall['high_pass']}")
print(f"  Drift model: {best_overall['drift_model']}")
print()
