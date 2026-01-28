#!/usr/bin/env python3
"""
Compare Confound Strategies Metrics

Compares Baseline32 (cosine only) vs Method3+confounds (standard)
"""

import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (16, 10)

# Paths
RESULTS_BASE = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results')
OUTPUT_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/confound_comparison')
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

# Test configuration
TEST_SUBJECTS = ['01', '06', '09']
TEST_ROIS = ['V1', 'V2', 'V3', 'hV4']
MOTION_TYPES = ['cosine', 'standard']

print("="*80)
print("Confound Strategy Comparison")
print("="*80)
print()
print("Test configuration:")
print(f"  Subjects: {', '.join([f'sub-{s}' for s in TEST_SUBJECTS])}")
print(f"  ROIs: {', '.join(TEST_ROIS)}")
print(f"  Strategies: {', '.join(MOTION_TYPES)}")
print()

# Collect results
results = []

for subject in TEST_SUBJECTS:
    for roi in TEST_ROIS:
        for motion_type in MOTION_TYPES:
            # New structure: results/{motion_type}/sub-{subject}/{roi}/results.json
            result_file = RESULTS_BASE / motion_type / f'sub-{subject}' / roi / 'results.json'

            if not result_file.exists():
                print(f"⚠️  Results file not found: {result_file}")
                continue

            # Load results
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)

                # Extract metrics
                result = {
                    'subject': subject,
                    'roi': roi,
                    'motion_type': motion_type,
                    'classification_accuracy': data.get('classification_accuracy', np.nan),
                    'reconstruction_error': data.get('reconstruction_error', np.nan),
                    'voxel_snr_mean': data.get('voxel_snr_mean', np.nan),
                    'run_correlation_mean': data.get('run_correlation_mean', np.nan),
                    'timestamp': data.get('timestamp', ''),
                    'result_file': str(result_file)
                }

                results.append(result)
                print(f"✅ Loaded: sub-{subject} {roi} {motion_type}")

            except Exception as e:
                print(f"❌ Error loading sub-{subject} {roi} {motion_type}: {e}")

print()
print(f"Total results loaded: {len(results)}")
print()

if len(results) == 0:
    print("❌ No results found. Make sure the pipeline has completed.")
    exit(1)

# Create DataFrame
df = pd.DataFrame(results)

# Check for missing data
expected_total = len(TEST_SUBJECTS) * len(TEST_ROIS) * len(MOTION_TYPES)
if len(df) < expected_total:
    print(f"⚠️  Warning: Expected {expected_total} results, got {len(df)}")
    print()
    missing_configs = []
    for subject in TEST_SUBJECTS:
        for roi in TEST_ROIS:
            for motion_type in MOTION_TYPES:
                if not ((df['subject'] == subject) &
                       (df['roi'] == roi) &
                       (df['motion_type'] == motion_type)).any():
                    missing_configs.append(f"sub-{subject} {roi} {motion_type}")

    if missing_configs:
        print("Missing configurations:")
        for cfg in missing_configs:
            print(f"  - {cfg}")
        print()

# Save raw results
df.to_csv(OUTPUT_DIR / 'comparison_results.csv', index=False)
print(f"✅ Raw results saved: {OUTPUT_DIR / 'comparison_results.csv'}")
print()

# =========================================================================
# Statistical Comparison
# =========================================================================

print("="*80)
print("Statistical Comparison")
print("="*80)
print()

# Pivot for comparison
for metric in ['classification_accuracy', 'reconstruction_error', 'voxel_snr_mean', 'run_correlation_mean']:
    if metric not in df.columns or df[metric].isna().all():
        continue

    print(f"\n{metric.upper().replace('_', ' ')}:")
    print("-" * 40)

    pivot = df.pivot_table(
        values=metric,
        index=['subject', 'roi'],
        columns='motion_type',
        aggfunc='first'
    )

    if 'cosine' in pivot.columns and 'standard' in pivot.columns:
        pivot['difference'] = pivot['standard'] - pivot['cosine']
        pivot['pct_change'] = (pivot['difference'] / pivot['cosine'] * 100)

        print(pivot.round(4))
        print()

        # Summary statistics
        print(f"Mean difference (standard - cosine): {pivot['difference'].mean():.4f}")
        print(f"Std difference: {pivot['difference'].std():.4f}")

        # Determine if higher is better (accuracy, snr, correlation) or lower is better (error)
        better_count = (pivot['difference'] > 0).sum() if metric != 'reconstruction_error' else (pivot['difference'] < 0).sum()
        total_count = len(pivot)
        print(f"Standard better in: {better_count}/{total_count} cases ({better_count/total_count*100:.1f}%)")
        print()

# =========================================================================
# Visualization
# =========================================================================

print("="*80)
print("Generating Visualizations")
print("="*80)
print()

# Figure 1: Accuracy comparison
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

for idx, roi in enumerate(TEST_ROIS):
    ax = axes[idx // 2, idx % 2]

    roi_data = df[df['roi'] == roi]

    if len(roi_data) == 0:
        ax.text(0.5, 0.5, f'No data for {roi}', ha='center', va='center')
        ax.set_title(f'{roi}')
        continue

    # Grouped bar plot
    subjects = roi_data['subject'].unique()
    x = np.arange(len(subjects))
    width = 0.35

    cosine_acc = []
    standard_acc = []

    for subj in subjects:
        cosine_val = roi_data[(roi_data['subject'] == subj) &
                              (roi_data['motion_type'] == 'cosine')]['classification_accuracy'].values
        standard_val = roi_data[(roi_data['subject'] == subj) &
                                (roi_data['motion_type'] == 'standard')]['classification_accuracy'].values

        cosine_acc.append(cosine_val[0] if len(cosine_val) > 0 else np.nan)
        standard_acc.append(standard_val[0] if len(standard_val) > 0 else np.nan)

    ax.bar(x - width/2, cosine_acc, width, label='Cosine (Baseline32)',
           color='steelblue', alpha=0.8)
    ax.bar(x + width/2, standard_acc, width, label='Standard (Method3+confounds)',
           color='coral', alpha=0.8)

    ax.set_xlabel('Subject')
    ax.set_ylabel('Decoding Accuracy')
    ax.set_title(f'{roi}')
    ax.set_xticks(x)
    ax.set_xticklabels([f'sub-{s}' for s in subjects])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim([0, 1])

plt.suptitle('Decoding Accuracy: Baseline32 (cosine) vs Method3+confounds (standard)',
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'accuracy_comparison.png', dpi=150, bbox_inches='tight')
print(f"✅ Plot saved: {OUTPUT_DIR / 'accuracy_comparison.png'}")

# Figure 2: Error comparison
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

for idx, roi in enumerate(TEST_ROIS):
    ax = axes[idx // 2, idx % 2]

    roi_data = df[df['roi'] == roi]

    if len(roi_data) == 0:
        continue

    subjects = roi_data['subject'].unique()
    x = np.arange(len(subjects))
    width = 0.35

    cosine_err = []
    standard_err = []

    for subj in subjects:
        cosine_val = roi_data[(roi_data['subject'] == subj) &
                              (roi_data['motion_type'] == 'cosine')]['reconstruction_error'].values
        standard_val = roi_data[(roi_data['subject'] == subj) &
                                (roi_data['motion_type'] == 'standard')]['reconstruction_error'].values

        cosine_err.append(cosine_val[0] if len(cosine_val) > 0 else np.nan)
        standard_err.append(standard_val[0] if len(standard_val) > 0 else np.nan)

    ax.bar(x - width/2, cosine_err, width, label='Cosine',
           color='steelblue', alpha=0.8)
    ax.bar(x + width/2, standard_err, width, label='Standard',
           color='coral', alpha=0.8)

    ax.set_xlabel('Subject')
    ax.set_ylabel('Mean Error (degrees)')
    ax.set_title(f'{roi}')
    ax.set_xticks(x)
    ax.set_xticklabels([f'sub-{s}' for s in subjects])
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

plt.suptitle('Reconstruction Error: Baseline32 vs Method3+confounds',
             fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'error_comparison.png', dpi=150, bbox_inches='tight')
print(f"✅ Plot saved: {OUTPUT_DIR / 'error_comparison.png'}")

# =========================================================================
# Recommendations
# =========================================================================

print()
print("="*80)
print("Recommendations")
print("="*80)
print()

# Calculate overall metrics
cosine_results = df[df['motion_type'] == 'cosine']
standard_results = df[df['motion_type'] == 'standard']

mean_acc_cosine = cosine_results['classification_accuracy'].mean()
mean_acc_standard = standard_results['classification_accuracy'].mean()

mean_err_cosine = cosine_results['reconstruction_error'].mean()
mean_err_standard = standard_results['reconstruction_error'].mean()

mean_snr_cosine = cosine_results['voxel_snr_mean'].mean()
mean_snr_standard = standard_results['voxel_snr_mean'].mean()

mean_rel_cosine = cosine_results['run_correlation_mean'].mean()
mean_rel_standard = standard_results['run_correlation_mean'].mean()

print(f"Overall Performance:")
print(f"  Baseline32 (cosine):")
print(f"    Accuracy: {mean_acc_cosine:.4f}, Error: {mean_err_cosine:.2f}°")
print(f"    SNR: {mean_snr_cosine:.4f}, Reliability: {mean_rel_cosine:.4f}")
print(f"  Method3+confounds (standard):")
print(f"    Accuracy: {mean_acc_standard:.4f}, Error: {mean_err_standard:.2f}°")
print(f"    SNR: {mean_snr_standard:.4f}, Reliability: {mean_rel_standard:.4f}")
print()

acc_change = mean_acc_standard - mean_acc_cosine
err_change = mean_err_standard - mean_err_cosine
snr_change = mean_snr_standard - mean_snr_cosine
rel_change = mean_rel_standard - mean_rel_cosine

print(f"Change with confound regression:")
print(f"  Accuracy: {acc_change:+.4f} ({acc_change/mean_acc_cosine*100:+.2f}%)")
print(f"  Error: {err_change:+.2f}° ({err_change/mean_err_cosine*100:+.2f}%)")
print(f"  SNR: {snr_change:+.4f} ({snr_change/mean_snr_cosine*100:+.2f}%)")
print(f"  Reliability: {rel_change:+.4f}")
print()

# Decision
if acc_change > 0.01 or (acc_change > 0 and err_change < -5):
    print("✅ RECOMMENDATION: Use 'standard' (Method3+confounds)")
    print()
    print("   Reasoning:")
    print("   - Improved decoding accuracy")
    print("   - Motion artifact properly controlled")
    print("   - Better tSNR expected")
    print()
    print("   Action: Use --motion standard for full dataset")

elif acc_change < -0.01 or err_change > 5:
    print("❌ RECOMMENDATION: Keep 'cosine' (Baseline32)")
    print()
    print("   Reasoning:")
    print("   - Standard confound regression degraded performance")
    print("   - Possible over-regression of neural signal")
    print("   - Baseline32 was optimal for a reason")
    print()
    print("   Action: Use --motion cosine for full dataset")

else:
    print("⚠️  RECOMMENDATION: Marginal difference - Consider trade-offs")
    print()
    print("   Reasoning:")
    print("   - Minimal performance difference")
    print("   - Standard provides better noise control")
    print("   - Cosine preserves more signal variance")
    print()
    print("   Suggested action:")
    print("   - If tSNR is critical: Use --motion standard")
    print("   - If decoding is critical: Use --motion cosine")
    print("   - Or run both for final analysis")

print()
print("="*80)
print("Comparison Complete")
print("="*80)
print()
print(f"Results saved to: {OUTPUT_DIR}")
print()
