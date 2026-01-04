#!/usr/bin/env python3
"""
Statistical analysis of ACTIVATION PATTERNS (not disparity)

Computes:
1. Within HC variability
2. CVD individual - HC (각 CVD vs HC mean)
3. CVD group - HC (CVD 평균 vs HC 평균)
"""

import numpy as np
from pathlib import Path
import json
from scipy import stats
import matplotlib.pyplot as plt

# Paths
base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
data_dir = base_dir / 'derivatives' / 'BH2009_deoblique_v2' / 'baseline81_deob'
results_dir = base_dir / 'results' / 'group_level' / 'activation_statistics'
results_dir.mkdir(parents=True, exist_ok=True)

# Settings
ROIS = ['V1', 'V2']
HC_SUBJECTS = ['03', '05', '06', '07']
CVD_SUBJECTS = ['08', '09', '10']
CVD_TYPES = {'08': 'Deuteranopia', '09': 'Deuteranopia', '10': 'Protanomaly'}
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse', 'Green', 'Cyan', 'Blue', 'Magenta']

# ============================================================================
# Helper Functions
# ============================================================================

def load_activation_pattern(subject_id, roi):
    """Load activation pattern and compute color-specific RMS"""
    pattern = f'*_sub-{subject_id}_{roi}_*_gmFalse_subjFalse'
    matches = list(data_dir.glob(pattern))

    if not matches:
        raise FileNotFoundError(f"No data found for sub-{subject_id}, {roi}")

    data_file = matches[0]
    amp_file = data_file / 'amplitudes_z.npy'

    if not amp_file.exists():
        raise FileNotFoundError(f"amplitudes_z.npy not found in {data_file}")

    amplitudes_z = np.load(amp_file)  # (n_runs, n_colors, n_voxels)
    pattern_data = amplitudes_z.mean(axis=0)  # (8, n_voxels)

    # Compute activation RMS for each color
    color_activation = []
    for c in range(8):
        activation_rms = np.sqrt(np.mean(pattern_data[c]**2))
        color_activation.append(activation_rms)

    return np.array(color_activation)

# ============================================================================
# Main Analysis
# ============================================================================

for ROI in ROIS:
    print(f"\n{'='*70}")
    print(f"ACTIVATION PATTERN STATISTICS: {ROI}")
    print(f"{'='*70}\n")

    # Load all patterns
    hc_activations = []
    for hc_id in HC_SUBJECTS:
        activation = load_activation_pattern(hc_id, ROI)
        hc_activations.append(activation)
        print(f"  HC sub-{hc_id}: {activation}")

    hc_activations = np.array(hc_activations)  # (n_hc, 8)

    cvd_activations = []
    cvd_ids = []
    for cvd_id in CVD_SUBJECTS:
        activation = load_activation_pattern(cvd_id, ROI)
        cvd_activations.append(activation)
        cvd_ids.append(cvd_id)
        print(f"  CVD sub-{cvd_id}: {activation}")

    cvd_activations = np.array(cvd_activations)  # (n_cvd, 8)

    # ========================================================================
    # 1. Within HC Statistics
    # ========================================================================

    print(f"\n{'-'*70}")
    print("1. WITHIN HC VARIABILITY")
    print(f"{'-'*70}\n")

    hc_mean = hc_activations.mean(axis=0)  # (8,)
    hc_std = hc_activations.std(axis=0)  # (8,)
    hc_cv = (hc_std / hc_mean) * 100  # Coefficient of Variation (%)

    within_hc_stats = {
        'mean': hc_mean.tolist(),
        'std': hc_std.tolist(),
        'cv_percent': hc_cv.tolist(),
        'color_names': COLOR_NAMES
    }

    print("Color-specific HC statistics:")
    for i, color in enumerate(COLOR_NAMES):
        print(f"  {color:12s}: mean={hc_mean[i]:.4f}, std={hc_std[i]:.4f}, CV={hc_cv[i]:.2f}%")

    # Overall HC consistency
    overall_hc_mean = hc_mean.mean()
    overall_hc_cv = hc_cv.mean()
    print(f"\nOverall HC:")
    print(f"  Mean activation: {overall_hc_mean:.4f}")
    print(f"  Mean CV: {overall_hc_cv:.2f}%")

    # ========================================================================
    # 2. CVD Individual - HC (각 CVD vs HC mean)
    # ========================================================================

    print(f"\n{'-'*70}")
    print("2. CVD INDIVIDUAL vs HC MEAN")
    print(f"{'-'*70}\n")

    cvd_individual_results = {}

    for cvd_idx, cvd_id in enumerate(CVD_SUBJECTS):
        cvd_pattern = cvd_activations[cvd_idx]

        print(f"\n--- Sub-{cvd_id} ({CVD_TYPES[cvd_id]}) ---")

        # Color-specific differences
        differences = cvd_pattern - hc_mean
        percent_diff = (differences / hc_mean) * 100

        # t-test for each color (comparing CVD value to HC distribution)
        p_values = []
        t_stats = []
        cohens_d = []

        for c in range(8):
            # One-sample t-test: is CVD different from HC mean?
            hc_color_values = hc_activations[:, c]
            cvd_value = cvd_pattern[c]

            # Calculate t-statistic and p-value
            t, p = stats.ttest_1samp(hc_color_values, cvd_value)
            t_stats.append(t)
            p_values.append(p)

            # Cohen's d effect size
            d = (cvd_value - hc_mean[c]) / hc_std[c]
            cohens_d.append(d)

        p_values = np.array(p_values)
        t_stats = np.array(t_stats)
        cohens_d = np.array(cohens_d)

        # FDR correction (Benjamini-Hochberg)
        from scipy.stats import false_discovery_control
        reject_fdr = false_discovery_control(p_values, method='bh')

        print(f"\nColor-specific analysis:")
        for i, color in enumerate(COLOR_NAMES):
            sig_marker = "***" if reject_fdr[i] else ""
            direction = "↑" if differences[i] > 0 else "↓"

            print(f"  {color:12s}: {direction} {percent_diff[i]:+6.2f}% "
                  f"(d={cohens_d[i]:+.3f}, p={p_values[i]:.4f}) {sig_marker}")

        # Overall difference
        overall_diff = cvd_pattern.mean() - hc_mean.mean()
        overall_pct = (overall_diff / hc_mean.mean()) * 100

        print(f"\nOverall:")
        print(f"  Mean activation: {cvd_pattern.mean():.4f} vs HC {hc_mean.mean():.4f}")
        print(f"  Difference: {overall_pct:+.2f}%")
        print(f"  Significant colors (FDR<0.05): {np.sum(reject_fdr)}/8")

        cvd_individual_results[cvd_id] = {
            'activation': cvd_pattern.tolist(),
            'differences': differences.tolist(),
            'percent_diff': percent_diff.tolist(),
            't_stats': t_stats.tolist(),
            'p_values': p_values.tolist(),
            'cohens_d': cohens_d.tolist(),
            'fdr_significant': reject_fdr.tolist(),
            'overall_diff_percent': float(overall_pct),
            'n_significant_colors': int(np.sum(reject_fdr))
        }

    # ========================================================================
    # 3. CVD Group - HC (CVD 평균 vs HC 평균)
    # ========================================================================

    print(f"\n{'-'*70}")
    print("3. CVD GROUP vs HC GROUP")
    print(f"{'-'*70}\n")

    cvd_mean = cvd_activations.mean(axis=0)  # (8,)
    cvd_std = cvd_activations.std(axis=0)  # (8,)

    # Color-specific t-tests (independent samples)
    group_t_stats = []
    group_p_values = []
    group_cohens_d = []

    for c in range(8):
        hc_color_values = hc_activations[:, c]
        cvd_color_values = cvd_activations[:, c]

        # Independent samples t-test
        t, p = stats.ttest_ind(hc_color_values, cvd_color_values)
        group_t_stats.append(t)
        group_p_values.append(p)

        # Cohen's d (pooled)
        pooled_std = np.sqrt(((len(hc_color_values)-1)*hc_std[c]**2 +
                               (len(cvd_color_values)-1)*cvd_std[c]**2) /
                              (len(hc_color_values) + len(cvd_color_values) - 2))
        d = (cvd_mean[c] - hc_mean[c]) / pooled_std
        group_cohens_d.append(d)

    group_p_values = np.array(group_p_values)
    group_t_stats = np.array(group_t_stats)
    group_cohens_d = np.array(group_cohens_d)

    # FDR correction
    group_reject_fdr = false_discovery_control(group_p_values, method='bh')

    group_differences = cvd_mean - hc_mean
    group_percent_diff = (group_differences / hc_mean) * 100

    print("Color-specific group comparison:")
    for i, color in enumerate(COLOR_NAMES):
        sig_marker = "***" if group_reject_fdr[i] else ""
        direction = "↑" if group_differences[i] > 0 else "↓"

        print(f"  {color:12s}: {direction} {group_percent_diff[i]:+6.2f}% "
              f"(d={group_cohens_d[i]:+.3f}, p={group_p_values[i]:.4f}) {sig_marker}")

    print(f"\nOverall group comparison:")
    print(f"  HC mean: {hc_mean.mean():.4f} ± {hc_std.mean():.4f}")
    print(f"  CVD mean: {cvd_mean.mean():.4f} ± {cvd_std.mean():.4f}")
    print(f"  Difference: {group_percent_diff.mean():+.2f}%")
    print(f"  Significant colors (FDR<0.05): {np.sum(group_reject_fdr)}/8")

    cvd_group_results = {
        'cvd_mean': cvd_mean.tolist(),
        'cvd_std': cvd_std.tolist(),
        'differences': group_differences.tolist(),
        'percent_diff': group_percent_diff.tolist(),
        't_stats': group_t_stats.tolist(),
        'p_values': group_p_values.tolist(),
        'cohens_d': group_cohens_d.tolist(),
        'fdr_significant': group_reject_fdr.tolist(),
        'n_significant_colors': int(np.sum(group_reject_fdr))
    }

    # ========================================================================
    # Save Results
    # ========================================================================

    results = {
        'roi': ROI,
        'hc_subjects': HC_SUBJECTS,
        'cvd_subjects': CVD_SUBJECTS,
        'color_names': COLOR_NAMES,
        'within_hc': within_hc_stats,
        'cvd_individual_vs_hc': cvd_individual_results,
        'cvd_group_vs_hc': cvd_group_results
    }

    output_json = results_dir / f'activation_statistics_{ROI}.json'
    with open(output_json, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Saved: {output_json}")

    # ========================================================================
    # Visualization
    # ========================================================================

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))

    # Panel A: Within HC variability (CV)
    ax = axes[0, 0]
    x_pos = np.arange(8)

    bars = ax.bar(x_pos, hc_cv, color='steelblue', alpha=0.7, edgecolor='black')
    ax.axhline(y=hc_cv.mean(), color='red', linestyle='--', linewidth=2,
               label=f'Mean CV = {hc_cv.mean():.1f}%')

    ax.set_xticks(x_pos)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_ylabel('Coefficient of Variation (%)', fontweight='bold')
    ax.set_title('A. Within HC Variability', fontweight='bold', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Panel B: CVD Individual - HC (percent difference)
    ax = axes[0, 1]
    x_pos = np.arange(8)
    width = 0.25

    for i, cvd_id in enumerate(CVD_SUBJECTS):
        pct_diff = cvd_individual_results[cvd_id]['percent_diff']
        fdr_sig = cvd_individual_results[cvd_id]['fdr_significant']

        colors = ['red' if sig else 'lightcoral' for sig in fdr_sig]

        ax.bar(x_pos + i*width, pct_diff, width, label=f'Sub-{cvd_id}',
               color=colors, alpha=0.7, edgecolor='black')

    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_xticks(x_pos + width)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_ylabel('% Difference from HC', fontweight='bold')
    ax.set_title('B. CVD Individual vs HC Mean\n(Dark red = FDR<0.05)',
                 fontweight='bold', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Panel C: CVD Group - HC
    ax = axes[1, 0]
    x_pos = np.arange(8)

    colors = ['red' if sig else 'lightgray' for sig in group_reject_fdr]
    bars = ax.bar(x_pos, group_percent_diff, color=colors, alpha=0.7, edgecolor='black')

    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_ylabel('% Difference', fontweight='bold')
    ax.set_title('C. CVD Group vs HC Group\n(Red = FDR<0.05)',
                 fontweight='bold', fontsize=12)
    ax.grid(True, alpha=0.3, axis='y')

    # Panel D: Effect sizes (Cohen's d)
    ax = axes[1, 1]
    x_pos = np.arange(8)
    width = 0.35

    ax.bar(x_pos - width/2, group_cohens_d, width, label='Group',
           color='steelblue', alpha=0.7, edgecolor='black')

    # Average individual effect size
    avg_individual_d = np.mean([cvd_individual_results[cid]['cohens_d']
                                 for cid in CVD_SUBJECTS], axis=0)
    ax.bar(x_pos + width/2, avg_individual_d, width, label='Individual (avg)',
           color='coral', alpha=0.7, edgecolor='black')

    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.axhline(y=0.2, color='green', linestyle=':', linewidth=1, alpha=0.5, label='Small (0.2)')
    ax.axhline(y=0.5, color='orange', linestyle=':', linewidth=1, alpha=0.5, label='Medium (0.5)')
    ax.axhline(y=0.8, color='red', linestyle=':', linewidth=1, alpha=0.5, label='Large (0.8)')

    ax.set_xticks(x_pos)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right')
    ax.set_ylabel("Cohen's d", fontweight='bold')
    ax.set_title('D. Effect Sizes', fontweight='bold', fontsize=12)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    plt.suptitle(f'Activation Pattern Statistics: {ROI}',
                 fontsize=16, fontweight='bold')
    plt.tight_layout()

    output_fig = results_dir / f'activation_statistics_{ROI}.png'
    plt.savefig(output_fig, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_fig}")

    plt.close()

print("\n" + "="*70)
print("ACTIVATION PATTERN STATISTICS COMPLETE!")
print("="*70)
