#!/usr/bin/env python3
"""
Analyze Drift Comparison Experiment Results

Purpose: Compare 4 drift processing strategies to identify optimal approach
Critical question: Does D0+M0 (no drift) match Baseline32 performance?

Conditions:
  D0+M0: No highpass, No drift regressors (Baseline32 재현)
  D1+M0: Highpass only (0.01 Hz)
  D2+M0: Cosine regressors only
  D2+M1: Full confounds (standard)

Key Metrics:
  - run_correlation_mean: Run-to-run reliability (MOST IMPORTANT)
  - classification_accuracy: Decoding performance
  - reconstruction_error: Reconstruction quality
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Configuration
RESULTS_DIR = Path("analysis/phase1_preprocess_decoding/method3_header_mi/results/factorial_experiment")
OUTPUT_DIR = Path("analysis/phase1_preprocess_decoding/drift_analysis")
OUTPUT_DIR.mkdir(exist_ok=True)

SUBJECT = "sub-01"
ROIS = ["V1", "V2", "V3", "hV4"]

# Drift conditions with their directory mappings
DRIFT_CONDITIONS = {
    'D0+M0': {'highpass': 'None', 'motion': 'none', 'label': 'D0: No Drift'},
    'D1+M0': {'highpass': '0.01', 'motion': 'none', 'label': 'D1: HPF Only'},
    'D2+M0': {'highpass': 'None', 'motion': 'cosine', 'label': 'D2: Cosine Only'},
    'D2+M1': {'highpass': 'None', 'motion': 'standard', 'label': 'D2+M1: Full Confounds'}
}

# Directory naming logic
def get_directory_suffix(motion):
    """Get directory suffix based on motion type"""
    if motion == 'none':
        return 'moNo'
    elif motion == 'cosine':
        return 'moCo'
    elif motion == 'standard':
        return 'moSt'
    else:
        raise ValueError(f"Unknown motion type: {motion}")

def load_result(roi, highpass, motion):
    """
    Load results.json for a specific condition

    Critical: D0 and D1 both have motion='none', so they're in the same directory!
    We must check config.highpass_hz to distinguish them.
    """
    # Determine directory
    motion_suffix = get_directory_suffix(motion)
    result_dir = RESULTS_DIR / f"nzNone_{motion_suffix}" / SUBJECT / roi

    result_file = result_dir / "results.json"

    if not result_file.exists():
        print(f"⚠️  Missing: {result_file}")
        return None

    with open(result_file, 'r') as f:
        data = json.load(f)

    # CRITICAL: Check if this is the right condition
    # D0 and D1 are both in nzNone_moNo/, so we need to check config
    config_highpass = data.get('config', {}).get('highpass_hz')

    # Verify this matches what we're looking for
    if highpass == 'None' and config_highpass is not None:
        print(f"⚠️  Skipping {roi} - Expected no highpass, found {config_highpass} Hz")
        return None
    elif highpass == '0.01' and config_highpass != 0.01:
        print(f"⚠️  Skipping {roi} - Expected 0.01 Hz, found {config_highpass} Hz")
        return None

    return data

def main():
    print("=" * 80)
    print("Drift Comparison Analysis")
    print("=" * 80)
    print(f"Results directory: {RESULTS_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Collect all results
    results = []

    for roi in ROIS:
        for cond_name, cond_config in DRIFT_CONDITIONS.items():
            highpass = cond_config['highpass']
            motion = cond_config['motion']
            label = cond_config['label']

            print(f"Loading {cond_name} ({roi})...")
            data = load_result(roi, highpass, motion)

            if data is None:
                continue

            # Extract key metrics
            result = {
                'condition': cond_name,
                'condition_label': label,
                'roi': roi,
                'highpass': highpass,
                'motion': motion,
                'run_correlation_mean': data.get('run_correlation_mean'),
                'run_correlation_std': data.get('run_correlation_std'),
                'classification_accuracy': data.get('classification_accuracy'),
                'reconstruction_error': data.get('reconstruction_error'),
                'amplitude_std': data.get('amplitude_std'),
                'hrf_peak_delay': data.get('hrf_peak_delay'),
                'hrf_l2_norm': data.get('hrf_l2_norm')
            }

            results.append(result)

            # Print if this is D0 (critical condition)
            if cond_name == 'D0+M0':
                r = result['run_correlation_mean']
                print(f"  🎯 D0+M0 ({roi}): run_correlation = {r:.4f}")
                if r is not None and r > 0.5:
                    print(f"     ✅ SUCCESS! Matches Baseline32 level")
                elif r is not None and r > 0.3:
                    print(f"     ⚠️  PARTIAL - Better than current but not Baseline32")
                else:
                    print(f"     ❌ FAILED - Problem is not drift-related")

    if not results:
        print("\n❌ No results found! Check if jobs completed successfully.")
        return

    # Create DataFrame
    df = pd.DataFrame(results)

    # Save CSV
    csv_path = OUTPUT_DIR / "drift_results.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n✅ Saved results to: {csv_path}")

    # Print summary
    print("\n" + "=" * 80)
    print("Summary Statistics")
    print("=" * 80)

    summary = df.groupby('condition_label')['run_correlation_mean'].agg(['mean', 'std', 'min', 'max'])
    summary = summary.sort_values('mean', ascending=False)
    print("\nRun-to-Run Correlation by Condition:")
    print(summary)

    # Check D0 specifically
    d0_results = df[df['condition'] == 'D0+M0']
    if len(d0_results) > 0:
        d0_mean = d0_results['run_correlation_mean'].mean()
        print(f"\n🎯 D0+M0 (No Drift) Mean: {d0_mean:.4f}")
        print(f"   Target (Baseline32): 0.775")

        if d0_mean > 0.5:
            print("   ✅ SUCCESS: Drift processing is the problem!")
            print("   → Recommendation: Use no-drift strategy for full analysis")
        elif d0_mean > 0.3:
            print("   ⚠️  PARTIAL: Drift improves but doesn't fully explain")
            print("   → Recommendation: Test D0 on sub-07, investigate other factors")
        else:
            print("   ❌ FAILED: Problem is not drift-related")
            print("   → Recommendation: Deep dive into Baseline32 vs current code differences")

    # Visualization 1: Overall comparison
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Bar plot - run correlation
    ax = axes[0]
    # Group by condition and compute mean/std
    grouped = df.groupby('condition_label')['run_correlation_mean'].agg(['mean', 'std'])
    conditions = grouped.index
    means = grouped['mean']
    stds = grouped['std']

    x_pos = np.arange(len(conditions))
    ax.bar(x_pos, means, yerr=stds, capsize=5, alpha=0.7)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(conditions, rotation=45, ha='right')
    ax.axhline(0.775, color='red', linestyle='--', label='Baseline32 (target)')
    ax.axhline(0.5, color='orange', linestyle='--', alpha=0.5, label='Success threshold')
    ax.set_xlabel('Drift Processing Strategy')
    ax.set_ylabel('Run-to-Run Correlation')
    ax.set_title('Reliability Comparison Across Drift Strategies')
    ax.legend()

    # Classification accuracy
    ax = axes[1]
    grouped_acc = df.groupby('condition_label')['classification_accuracy'].agg(['mean', 'std'])
    means_acc = grouped_acc['mean']
    stds_acc = grouped_acc['std']

    ax.bar(x_pos, means_acc, yerr=stds_acc, capsize=5, alpha=0.7)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(conditions, rotation=45, ha='right')
    ax.axhline(0.125, color='gray', linestyle='--', label='Chance (12.5%)')
    ax.set_xlabel('Drift Processing Strategy')
    ax.set_ylabel('Classification Accuracy')
    ax.set_title('Decoding Performance')
    ax.legend()

    plt.tight_layout()
    plot_path = OUTPUT_DIR / "drift_comparison.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"✅ Saved plot: {plot_path}")

    # Visualization 2: By ROI
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()

    for idx, roi in enumerate(ROIS):
        ax = axes[idx]
        roi_data = df[df['roi'] == roi]

        # Sort by condition order
        condition_order = ['D0: No Drift', 'D1: HPF Only', 'D2: Cosine Only', 'D2+M1: Full Confounds']
        roi_data['condition_label'] = pd.Categorical(
            roi_data['condition_label'],
            categories=condition_order,
            ordered=True
        )
        roi_data = roi_data.sort_values('condition_label')

        ax.bar(range(len(roi_data)), roi_data['run_correlation_mean'])
        ax.axhline(0.775, color='red', linestyle='--', label='Baseline32', alpha=0.7)
        ax.axhline(0.5, color='orange', linestyle='--', alpha=0.5)
        ax.set_xticks(range(len(roi_data)))
        ax.set_xticklabels([c.split(':')[0] for c in roi_data['condition_label']],
                          rotation=45, ha='right')
        ax.set_ylabel('Run Correlation')
        ax.set_title(f'{roi}')
        ax.set_ylim(0, 1)
        if idx == 0:
            ax.legend()

    plt.tight_layout()
    plot_path = OUTPUT_DIR / "drift_by_roi.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"✅ Saved plot: {plot_path}")

    print("\n" + "=" * 80)
    print("Analysis Complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
