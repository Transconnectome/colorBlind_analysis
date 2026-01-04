#!/usr/bin/env python3
"""
Comprehensive visualization comparing ACTIVATION and DISPARITY
Shows how they provide complementary information for CVD characterization
"""

import numpy as np
from pathlib import Path
import json
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# Paths
base_dir = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
data_dir = base_dir / 'derivatives' / 'BH2009_deoblique_v2' / 'baseline81_deob'
sig_dir = base_dir / 'results' / 'group_level' / 'significance_tests_no_sub02'
act_dir = base_dir / 'results' / 'group_level' / 'activation_statistics'
results_dir = base_dir / 'results' / 'group_level'

# Settings
ROIS = ['V1', 'V2']
HC_SUBJECTS = ['03', '05', '06', '07']
CVD_SUBJECTS = ['08', '09', '10']
CVD_TYPES = {'08': 'Deuteranopia', '09': 'Deuteranopia', '10': 'Protanomaly'}
CVD_COLORS = {'08': '#FF6B6B', '09': '#FFA07A', '10': '#FFB6C1'}
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Chartreuse', 'Green', 'Cyan', 'Blue', 'Magenta']

# ============================================================================
# Load Data
# ============================================================================

def load_activation_pattern(subject_id, roi):
    """Load activation pattern"""
    pattern = f'*_sub-{subject_id}_{roi}_*_gmFalse_subjFalse'
    matches = list(data_dir.glob(pattern))

    if not matches:
        raise FileNotFoundError(f"No data found for sub-{subject_id}, {roi}")

    data_file = matches[0]
    amp_file = data_file / 'amplitudes_z.npy'
    amplitudes_z = np.load(amp_file)
    pattern_data = amplitudes_z.mean(axis=0)

    color_activation = []
    for c in range(8):
        activation_rms = np.sqrt(np.mean(pattern_data[c]**2))
        color_activation.append(activation_rms)

    return np.array(color_activation)

# ============================================================================
# Main Visualization
# ============================================================================

for ROI in ROIS:
    print(f"\n{'='*70}")
    print(f"ACTIVATION vs DISPARITY ANALYSIS: {ROI}")
    print(f"{'='*70}\n")

    # Load significance test results (disparity)
    sig_file = sig_dir / f'significance_tests_{ROI}.json'
    with open(sig_file, 'r') as f:
        sig_results = json.load(f)

    # Load activation statistics
    act_file = act_dir / f'activation_statistics_{ROI}.json'
    with open(act_file, 'r') as f:
        act_results = json.load(f)

    # Load activation patterns
    hc_activations = []
    for hc_id in HC_SUBJECTS:
        activation = load_activation_pattern(hc_id, ROI)
        hc_activations.append(activation)

    hc_activations = np.array(hc_activations)
    hc_mean_activation = hc_activations.mean(axis=0)

    cvd_activations = {}
    for cvd_id in CVD_SUBJECTS:
        activation = load_activation_pattern(cvd_id, ROI)
        cvd_activations[cvd_id] = activation

    # Get disparity data
    cvd_disparities = {}
    for cvd_id in CVD_SUBJECTS:
        disparity = np.array(sig_results['individual_level'][cvd_id]['color_rms'])
        cvd_disparities[cvd_id] = disparity

    # ========================================================================
    # Create comprehensive figure
    # ========================================================================

    fig = plt.figure(figsize=(22, 20))
    gs = GridSpec(4, 3, figure=fig, hspace=0.45, wspace=0.35,
                  left=0.05, right=0.95, top=0.96, bottom=0.04)

    # ========================================================================
    # Row 1: Activation vs Disparity for each CVD
    # ========================================================================

    for cvd_idx, cvd_id in enumerate(CVD_SUBJECTS):
        ax = fig.add_subplot(gs[0, cvd_idx])

        x_pos = np.arange(8)
        width = 0.35

        # Activation (actual values)
        activation = cvd_activations[cvd_id]
        activation_diff_pct = ((activation - hc_mean_activation) / hc_mean_activation) * 100

        # Disparity (difference from HC)
        disparity = cvd_disparities[cvd_id]

        # Normalize for comparison
        activation_norm = (activation_diff_pct - activation_diff_pct.min()) / (activation_diff_pct.max() - activation_diff_pct.min())
        disparity_norm = (disparity - disparity.min()) / (disparity.max() - disparity.min())

        ax.bar(x_pos - width/2, activation_norm, width,
               label='Activation\n(% diff from HC)', color='steelblue', alpha=0.7, edgecolor='black')
        ax.bar(x_pos + width/2, disparity_norm, width,
               label='Disparity\n(after alignment)', color='coral', alpha=0.7, edgecolor='black')

        ax.set_xticks(x_pos)
        ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=9)
        ax.set_ylabel('Normalized Value', fontweight='bold', fontsize=10)
        ax.set_title(f'Sub-{cvd_id} ({CVD_TYPES[cvd_id]})\nActivation vs Disparity',
                    fontweight='bold', fontsize=11, pad=10)
        ax.legend(fontsize=9, loc='upper left')
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_ylim([0, 1.05])

    # ========================================================================
    # Row 2: Correlation between Activation and Disparity
    # ========================================================================

    for cvd_idx, cvd_id in enumerate(CVD_SUBJECTS):
        ax = fig.add_subplot(gs[1, cvd_idx])

        activation = cvd_activations[cvd_id]
        activation_diff_pct = ((activation - hc_mean_activation) / hc_mean_activation) * 100
        disparity = cvd_disparities[cvd_id]

        # Scatter plot
        ax.scatter(activation_diff_pct, disparity, s=100, alpha=0.7,
                  c=range(8), cmap='tab10', edgecolor='black', linewidth=1.5)

        # Add color labels
        for i, color in enumerate(COLOR_NAMES):
            ax.annotate(color[:3], (activation_diff_pct[i], disparity[i]),
                       fontsize=8, ha='center', va='bottom')

        # Correlation
        corr = np.corrcoef(activation_diff_pct, disparity)[0, 1]

        ax.set_xlabel('Activation Diff (%)', fontweight='bold', fontsize=10)
        ax.set_ylabel('Disparity (RMS)', fontweight='bold', fontsize=10)
        ax.set_title(f'Sub-{cvd_id}\nCorrelation: r={corr:.3f}',
                    fontweight='bold', fontsize=11, pad=10)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)

    # ========================================================================
    # Row 3: CVD Signature Profiles (Radar plots)
    # ========================================================================

    for cvd_idx, cvd_id in enumerate(CVD_SUBJECTS):
        ax = fig.add_subplot(gs[2, cvd_idx], projection='polar')

        activation = cvd_activations[cvd_id]
        activation_diff_pct = ((activation - hc_mean_activation) / hc_mean_activation) * 100
        disparity = cvd_disparities[cvd_id]

        angles = np.linspace(0, 2*np.pi, 8, endpoint=False)
        angles_plot = np.concatenate([angles, [angles[0]]])

        # Normalize
        activation_norm = (activation_diff_pct - activation_diff_pct.min()) / (activation_diff_pct.max() - activation_diff_pct.min())
        disparity_norm = (disparity - disparity.min()) / (disparity.max() - disparity.min())

        activation_plot = np.concatenate([activation_norm, [activation_norm[0]]])
        disparity_plot = np.concatenate([disparity_norm, [disparity_norm[0]]])

        ax.plot(angles_plot, activation_plot, 'o-', linewidth=2,
               label='Activation', color='steelblue', markersize=8)
        ax.fill(angles_plot, activation_plot, alpha=0.2, color='steelblue')

        ax.plot(angles_plot, disparity_plot, 's--', linewidth=2,
               label='Disparity', color='coral', markersize=8)
        ax.fill(angles_plot, disparity_plot, alpha=0.2, color='coral')

        ax.set_xticks(angles)
        ax.set_xticklabels(COLOR_NAMES, fontsize=9)
        ax.set_ylim([0, 1.1])
        ax.set_title(f'Sub-{cvd_id} Signature\n(Normalized)',
                    fontweight='bold', fontsize=11, pad=25)
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True)

    # ========================================================================
    # Row 4: Key Differences Summary
    # ========================================================================

    # Panel A: Color-specific differences heatmap
    ax = fig.add_subplot(gs[3, 0])

    # Create data matrix: CVD x Colors
    activation_matrix = []
    for cvd_id in CVD_SUBJECTS:
        activation = cvd_activations[cvd_id]
        activation_diff_pct = ((activation - hc_mean_activation) / hc_mean_activation) * 100
        activation_matrix.append(activation_diff_pct)

    activation_matrix = np.array(activation_matrix)

    im = ax.imshow(activation_matrix, cmap='RdBu_r', aspect='auto', vmin=-30, vmax=30)
    ax.set_xticks(np.arange(8))
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=9)
    ax.set_yticks(np.arange(3))
    ax.set_yticklabels([f'Sub-{cid}\n({CVD_TYPES[cid][:5]})' for cid in CVD_SUBJECTS], fontsize=10)
    ax.set_title('Activation Difference (%)\nfrom HC Mean', fontweight='bold', fontsize=11, pad=10)

    # Add text annotations
    for i in range(3):
        for j in range(8):
            text = ax.text(j, i, f'{activation_matrix[i, j]:.0f}',
                          ha="center", va="center", color="black", fontsize=8, fontweight='bold')

    plt.colorbar(im, ax=ax, label='% Difference', shrink=0.7)

    # Panel B: Disparity heatmap
    ax = fig.add_subplot(gs[3, 1])

    disparity_matrix = []
    for cvd_id in CVD_SUBJECTS:
        disparity = cvd_disparities[cvd_id]
        disparity_matrix.append(disparity)

    disparity_matrix = np.array(disparity_matrix)

    im = ax.imshow(disparity_matrix, cmap='YlOrRd', aspect='auto', vmin=0, vmax=0.3)
    ax.set_xticks(np.arange(8))
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=9)
    ax.set_yticks(np.arange(3))
    ax.set_yticklabels([f'Sub-{cid}\n({CVD_TYPES[cid][:5]})' for cid in CVD_SUBJECTS], fontsize=10)
    ax.set_title('Disparity (RMS)\nafter Procrustes', fontweight='bold', fontsize=11, pad=10)

    # Add text annotations
    for i in range(3):
        for j in range(8):
            text = ax.text(j, i, f'{disparity_matrix[i, j]:.2f}',
                          ha="center", va="center", color="black", fontsize=8, fontweight='bold')

    plt.colorbar(im, ax=ax, label='RMS', shrink=0.7)

    # Panel C: Summary statistics
    ax = fig.add_subplot(gs[3, 2])
    ax.axis('off')

    summary_text = f"""
    ╔═══════════════════════════════════════════════╗
    ║   ACTIVATION vs DISPARITY SUMMARY ({ROI})        ║
    ╚═══════════════════════════════════════════════╝

    KEY DIFFERENCES:

    1. ACTIVATION (Absolute magnitude)
       • Measures: How much brain responds
       • Independent of HC alignment
       • Shows over/under activation

    2. DISPARITY (Relative difference)
       • Measures: How different from HC
       • After Procrustes alignment
       • Shows geometric distance

    ────────────────────────────────────────────────

    CVD-SPECIFIC PATTERNS:

    Sub-08 (Deuteranopia):
    """

    # Calculate key metrics for each CVD
    for cvd_id in CVD_SUBJECTS:
        activation = cvd_activations[cvd_id]
        activation_diff_pct = ((activation - hc_mean_activation) / hc_mean_activation) * 100
        disparity = cvd_disparities[cvd_id]

        # Find max over/under activation
        max_over_idx = np.argmax(activation_diff_pct)
        max_under_idx = np.argmin(activation_diff_pct)

        # Find max disparity
        max_disp_idx = np.argmax(disparity)

        # Correlation
        corr = np.corrcoef(activation_diff_pct, disparity)[0, 1]

        cvd_summary = f"""
      • Max over: {COLOR_NAMES[max_over_idx]} ({activation_diff_pct[max_over_idx]:+.1f}%)
      • Max under: {COLOR_NAMES[max_under_idx]} ({activation_diff_pct[max_under_idx]:+.1f}%)
      • Max disparity: {COLOR_NAMES[max_disp_idx]} ({disparity[max_disp_idx]:.3f})
      • Act-Disp corr: r={corr:.3f}
        """

        if cvd_id == '08':
            summary_text += cvd_summary
        else:
            summary_text += f"\n    Sub-{cvd_id} ({CVD_TYPES[cvd_id]}):{cvd_summary}"

    summary_text += """
    ────────────────────────────────────────────────

    FOR DEEP LEARNING LOSS:

    L_total = α·L_activation + β·L_disparity

    • L_activation: Match absolute response
    • L_disparity: Match geometric difference

    → Both provide complementary constraints!

    ╚═══════════════════════════════════════════════╝
    """

    ax.text(0.02, 0.98, summary_text, transform=ax.transAxes,
           fontsize=7.5, va='top', ha='left', family='monospace',
           bbox=dict(boxstyle='round', facecolor='lightyellow',
                    alpha=0.3, edgecolor='black', linewidth=1))

    # Overall title
    fig.suptitle(f'Activation vs Disparity: Comprehensive Analysis ({ROI})\n' +
                f'Understanding Complementary Information for CVD Characterization',
                fontsize=17, fontweight='bold', y=0.99)

    # Save
    output_file = results_dir / f'activation_vs_disparity_{ROI}.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")

    plt.close()

    # ========================================================================
    # Save detailed comparison data
    # ========================================================================

    comparison_results = {
        'roi': ROI,
        'cvd_subjects': CVD_SUBJECTS,
        'color_names': COLOR_NAMES,
        'hc_mean_activation': hc_mean_activation.tolist(),
        'cvd_profiles': {}
    }

    for cvd_id in CVD_SUBJECTS:
        activation = cvd_activations[cvd_id]
        activation_diff_pct = ((activation - hc_mean_activation) / hc_mean_activation) * 100
        disparity = cvd_disparities[cvd_id]

        corr = np.corrcoef(activation_diff_pct, disparity)[0, 1]

        comparison_results['cvd_profiles'][cvd_id] = {
            'activation': activation.tolist(),
            'activation_diff_percent': activation_diff_pct.tolist(),
            'disparity': disparity.tolist(),
            'correlation': float(corr),
            'max_over_activation': {
                'color': COLOR_NAMES[np.argmax(activation_diff_pct)],
                'percent': float(activation_diff_pct.max())
            },
            'max_under_activation': {
                'color': COLOR_NAMES[np.argmin(activation_diff_pct)],
                'percent': float(activation_diff_pct.min())
            },
            'max_disparity': {
                'color': COLOR_NAMES[np.argmax(disparity)],
                'value': float(disparity.max())
            }
        }

    output_json = results_dir / f'activation_vs_disparity_{ROI}.json'
    with open(output_json, 'w') as f:
        json.dump(comparison_results, f, indent=2)

    print(f"✅ Saved: {output_json}")

print("\n" + "="*70)
print("ACTIVATION vs DISPARITY ANALYSIS COMPLETE!")
print("="*70)
print("\nGenerated files:")
print("  - activation_vs_disparity_V1.png")
print("  - activation_vs_disparity_V2.png")
print("  - activation_vs_disparity_V1.json")
print("  - activation_vs_disparity_V2.json")
print("\nKey insight:")
print("  Activation and Disparity provide COMPLEMENTARY information")
print("  → Both should be used in deep learning loss function!")
