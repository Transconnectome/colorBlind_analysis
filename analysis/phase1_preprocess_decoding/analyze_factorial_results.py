#!/usr/bin/env python3
"""
Analyze 2×2 Factorial Experiment Results

Compares 4 conditions:
  E1+C0 (nzBoth_moNo):  Consistent normalization + No confounds
  E1+C1 (nzBoth_moCo):  Consistent normalization + Cosine confounds
  E2+C0 (nzNone_moNo):  All original + No confounds
  E2+C1 (nzNone_moCo):  All original + Cosine confounds

Key diagnostics:
  1. HRF L2 norm (should be ~700 for success, ~0.02 for scale mismatch failure)
  2. Amplitude std/range (should be ~0.3 for success, ~500 for explosion)
  3. Run-to-run correlation (should be >0.5 for success, ~0 for noise)
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (16, 10)

# Paths
RESULTS_BASE = Path('analysis/phase1_preprocess_decoding/results/factorial_experiment')
OUTPUT_DIR = Path('analysis/phase1_preprocess_decoding/factorial_analysis')
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Configuration
SUBJECT = '01'
ROIS = ['V1', 'V2', 'V3', 'hV4']

# Conditions: {condition_name: (dir_name, normalize_level, motion_type)}
CONDITIONS = {
    'E1+C0 (Consistent+None)': ('nzBoth_moNo', 'both', 'none'),
    'E1+C1 (Consistent+Cosine)': ('nzBoth_moCo', 'both', 'cosine'),
    'E2+C0 (Original+None)': ('nzNone_moNo', 'none', 'none'),
    'E2+C1 (Original+Cosine)': ('nzNone_moCo', 'none', 'cosine'),
}

print("="*80)
print("2×2 Factorial Experiment Analysis")
print("="*80)
print()

# Collect results
results = []
hrf_data = {}

for condition_name, (dir_name, normalize_level, motion_type) in CONDITIONS.items():
    for roi in ROIS:
        result_dir = RESULTS_BASE / dir_name / f'sub-{SUBJECT}' / roi
        result_file = result_dir / 'results.json'
        hrf_file = result_dir / 'roi_hrf.npy'

        if not result_file.exists():
            print(f"⚠️  Missing: {result_file}")
            continue

        # Load results
        with open(result_file) as f:
            data = json.load(f)

        # Load HRF
        if hrf_file.exists():
            hrf = np.load(hrf_file)
            hrf_l2_norm = np.linalg.norm(hrf)
            hrf_max_abs = np.max(np.abs(hrf))
        else:
            hrf_l2_norm = np.nan
            hrf_max_abs = np.nan

        # Extract key metrics
        result = {
            'condition': condition_name,
            'normalize_level': normalize_level,
            'motion_type': motion_type,
            'roi': roi,
            'hrf_l2_norm': hrf_l2_norm,
            'hrf_max_abs': hrf_max_abs,
            'amplitude_mean': data.get('amplitude_mean_raw', np.nan),
            'amplitude_std': data.get('amplitude_std_raw', np.nan),
            'voxel_snr_mean': data.get('voxel_snr_mean', np.nan),
            'run_correlation_mean': data.get('run_correlation_mean', np.nan),
            'classification_accuracy': data.get('classification_accuracy', np.nan),
            'reconstruction_error': data.get('reconstruction_error', np.nan),
            'n_voxels_selected': data.get('n_voxels_selected', 0),
        }

        results.append(result)
        print(f"✅ Loaded: {condition_name} - {roi}")

        # Store HRF for visualization
        if hrf_file.exists():
            hrf_data[(condition_name, roi)] = hrf

print()
print(f"Total results loaded: {len(results)}")
print()

if len(results) == 0:
    print("❌ No results found. Make sure the pipeline has completed.")
    exit(1)

# Create DataFrame
df = pd.DataFrame(results)

# Save raw results
df.to_csv(OUTPUT_DIR / 'factorial_results.csv', index=False)
print(f"✅ Raw results saved: {OUTPUT_DIR / 'factorial_results.csv'}")
print()

# =========================================================================
# Critical Diagnostics
# =========================================================================

print("="*80)
print("CRITICAL DIAGNOSTICS")
print("="*80)
print()

# Group by condition
summary = df.groupby('condition').agg({
    'hrf_l2_norm': ['mean', 'std'],
    'amplitude_std': ['mean', 'std'],
    'run_correlation_mean': ['mean', 'std'],
    'classification_accuracy': ['mean', 'std'],
}).round(4)

print("Summary by Condition:")
print(summary)
print()

# Check for success/failure
print("SUCCESS/FAILURE Diagnosis:")
print("-" * 80)

for condition_name in CONDITIONS.keys():
    cond_data = df[df['condition'] == condition_name]

    if len(cond_data) == 0:
        print(f"{condition_name:35s}: NO DATA")
        continue

    hrf_norm = cond_data['hrf_l2_norm'].mean()
    amp_std = cond_data['amplitude_std'].mean()
    run_corr = cond_data['run_correlation_mean'].mean()

    # Diagnosis
    hrf_success = hrf_norm > 100  # Should be ~700, not ~0.02
    amp_success = amp_std < 10    # Should be ~0.3, not ~500
    corr_success = run_corr > 0.3  # Should be >0.5, not ~0

    overall = "✅ SUCCESS" if (hrf_success and amp_success and corr_success) else "❌ FAILURE"

    print(f"{condition_name:35s}: {overall}")
    print(f"  HRF L2 norm:     {hrf_norm:8.2f}  {'✅' if hrf_success else '❌'} (target: ~700, avoid: ~0.02)")
    print(f"  Amplitude std:   {amp_std:8.2f}  {'✅' if amp_success else '❌'} (target: ~0.3, avoid: ~500)")
    print(f"  Run correlation: {run_corr:8.4f}  {'✅' if corr_success else '❌'} (target: >0.5, avoid: ~0)")
    print()

# =========================================================================
# Detailed Comparison
# =========================================================================

print("="*80)
print("DETAILED COMPARISON")
print("="*80)
print()

metrics = ['hrf_l2_norm', 'amplitude_std', 'run_correlation_mean', 'classification_accuracy']

for metric in metrics:
    print(f"\n{metric.upper().replace('_', ' ')}:")
    print("-" * 60)

    pivot = df.pivot_table(
        values=metric,
        index='roi',
        columns='condition',
        aggfunc='mean'
    )

    print(pivot.round(4))
    print()

# =========================================================================
# Visualizations
# =========================================================================

print("="*80)
print("Generating Visualizations")
print("="*80)
print()

# Figure 1: Critical metrics
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# HRF L2 norm
ax = axes[0, 0]
for condition_name in CONDITIONS.keys():
    cond_data = df[df['condition'] == condition_name]
    ax.bar(range(len(cond_data)), cond_data['hrf_l2_norm'],
           label=condition_name.split()[0], alpha=0.8, width=0.8)
ax.axhline(y=700, color='green', linestyle='--', linewidth=2, label='Target (~700)')
ax.axhline(y=0.02, color='red', linestyle='--', linewidth=2, label='Failure (~0.02)')
ax.set_ylabel('HRF L2 Norm')
ax.set_title('HRF L2 Norm by Condition (Scale Check)')
ax.legend()
ax.grid(axis='y', alpha=0.3)
ax.set_yscale('log')

# Amplitude std
ax = axes[0, 1]
cond_order = list(CONDITIONS.keys())
sns.boxplot(data=df, x='condition', y='amplitude_std', ax=ax, order=cond_order)
ax.axhline(y=0.3, color='green', linestyle='--', linewidth=2, label='Target (~0.3)')
ax.axhline(y=500, color='red', linestyle='--', linewidth=2, label='Explosion (~500)')
ax.set_ylabel('Amplitude Std')
ax.set_title('Amplitude Std by Condition (Stability Check)')
ax.set_xticklabels([c.split()[0] for c in cond_order], rotation=45, ha='right')
ax.legend()
ax.grid(axis='y', alpha=0.3)
ax.set_yscale('log')

# Run correlation
ax = axes[1, 0]
sns.boxplot(data=df, x='condition', y='run_correlation_mean', ax=ax, order=cond_order)
ax.axhline(y=0.5, color='green', linestyle='--', linewidth=2, label='Good (>0.5)')
ax.axhline(y=0.0, color='red', linestyle='--', linewidth=2, label='Failure (~0)')
ax.set_ylabel('Run-to-Run Correlation')
ax.set_title('Run Reliability by Condition')
ax.set_xticklabels([c.split()[0] for c in cond_order], rotation=45, ha='right')
ax.legend()
ax.grid(axis='y', alpha=0.3)

# Classification accuracy
ax = axes[1, 1]
sns.boxplot(data=df, x='condition', y='classification_accuracy', ax=ax, order=cond_order)
ax.axhline(y=1/8, color='gray', linestyle='--', linewidth=2, label='Chance (12.5%)')
ax.set_ylabel('Classification Accuracy')
ax.set_title('Classification Accuracy by Condition')
ax.set_xticklabels([c.split()[0] for c in cond_order], rotation=45, ha='right')
ax.legend()
ax.grid(axis='y', alpha=0.3)

plt.suptitle('2×2 Factorial Experiment: Critical Diagnostics', fontsize=16, fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'factorial_diagnostics.png', dpi=150, bbox_inches='tight')
print(f"✅ Plot saved: {OUTPUT_DIR / 'factorial_diagnostics.png'}")

# Figure 2: HRF shapes
if len(hrf_data) > 0:
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    for idx, roi in enumerate(ROIS):
        ax = axes[idx // 2, idx % 2]

        for condition_name in CONDITIONS.keys():
            key = (condition_name, roi)
            if key in hrf_data:
                hrf = hrf_data[key]
                times = np.arange(len(hrf)) * 1.5  # TR = 1.5s
                ax.plot(times, hrf, marker='o', label=condition_name.split()[0], linewidth=2)

        ax.axhline(y=0, color='black', linestyle=':', alpha=0.5)
        ax.set_xlabel('Time (seconds)')
        ax.set_ylabel('HRF Amplitude')
        ax.set_title(f'{roi}: HRF Shape Comparison')
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.suptitle('HRF Shapes by Condition (Scale Check)', fontsize=16, fontweight='bold')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / 'hrf_shapes.png', dpi=150, bbox_inches='tight')
    print(f"✅ Plot saved: {OUTPUT_DIR / 'hrf_shapes.png'}")

print()
print("="*80)
print("Analysis Complete")
print("="*80)
print()
print(f"Results saved to: {OUTPUT_DIR}")
print()
print("Interpretation Guide:")
print("  ✅ SUCCESS: HRF ~700, Amplitude std ~0.3, Run corr >0.5")
print("  ❌ FAILURE: HRF ~0.02, Amplitude std ~500, Run corr ~0")
print()
