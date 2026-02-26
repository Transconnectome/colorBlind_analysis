#!/usr/bin/env python3
"""
Visualize LOCO Ensemble Results
Creates comparison plots for FE_Ensemble vs Baseline
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Load data
data_file = Path(__file__).parent / 'loco_decoding_comparison' / 'decoding_comparison.json'
with open(data_file, 'r') as f:
    data = json.load(f)

# Subject groups
subjects_hc = [f'{i:02d}' for i in range(1, 8)]
subjects_cvd = [f'{i:02d}' for i in range(8, 11)]
rois = ['V1', 'V2', 'V3', 'V4']
roi_names = ['V1', 'V2', 'V3', 'hV4']

# Extract data
baseline_hc = {roi: [] for roi in rois}
ensemble_hc = {roi: [] for roi in rois}
baseline_cvd = {roi: [] for roi in rois}
ensemble_cvd = {roi: [] for roi in rois}

for roi in rois:
    for subj_id in subjects_hc:
        if subj_id in data['per_subject'] and roi in data['per_subject'][subj_id]:
            if 'ForwardEncoding' in data['per_subject'][subj_id][roi]:
                baseline_hc[roi].append(data['per_subject'][subj_id][roi]['ForwardEncoding']['mae'])
            if 'FE_Ensemble' in data['per_subject'][subj_id][roi]:
                ensemble_hc[roi].append(data['per_subject'][subj_id][roi]['FE_Ensemble']['mae'])

    for subj_id in subjects_cvd:
        if subj_id in data['per_subject'] and roi in data['per_subject'][subj_id]:
            if 'ForwardEncoding' in data['per_subject'][subj_id][roi]:
                baseline_cvd[roi].append(data['per_subject'][subj_id][roi]['ForwardEncoding']['mae'])
            if 'FE_Ensemble' in data['per_subject'][subj_id][roi]:
                ensemble_cvd[roi].append(data['per_subject'][subj_id][roi]['FE_Ensemble']['mae'])

# Create figure
fig, axes = plt.subplots(1, 4, figsize=(16, 4), sharey=True)
fig.suptitle('LOCO Decoding: FE_Ensemble vs Baseline (Procrustes)', fontsize=14, fontweight='bold')

colors_hc = {'baseline': '#4477AA', 'ensemble': '#228833'}
colors_cvd = {'baseline': '#EE6677', 'ensemble': '#CC3311'}

for idx, (roi, roi_name) in enumerate(zip(rois, roi_names)):
    ax = axes[idx]

    # HC group
    x_hc = [1, 2]
    means_hc = [np.mean(baseline_hc[roi]), np.mean(ensemble_hc[roi])]
    stds_hc = [np.std(baseline_hc[roi], ddof=1), np.std(ensemble_hc[roi], ddof=1)]

    ax.bar(x_hc, means_hc, yerr=stds_hc, capsize=5, alpha=0.7,
           color=[colors_hc['baseline'], colors_hc['ensemble']],
           label=['Baseline (HC)', 'Ensemble (HC)'], edgecolor='black', linewidth=1.5)

    # CVD group
    x_cvd = [3.5, 4.5]
    means_cvd = [np.mean(baseline_cvd[roi]), np.mean(ensemble_cvd[roi])]
    stds_cvd = [np.std(baseline_cvd[roi], ddof=1), np.std(ensemble_cvd[roi], ddof=1)]

    ax.bar(x_cvd, means_cvd, yerr=stds_cvd, capsize=5, alpha=0.7,
           color=[colors_cvd['baseline'], colors_cvd['ensemble']],
           label=['Baseline (CVD)', 'Ensemble (CVD)'], edgecolor='black', linewidth=1.5)

    # Add delta annotation for HC
    delta_hc = means_hc[1] - means_hc[0]
    y_pos = max(means_hc) + max(stds_hc) + 5
    arrow_y = y_pos - 3
    ax.annotate('', xy=(2, arrow_y), xytext=(1, arrow_y),
                arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(1.5, y_pos, f'Δ={delta_hc:.1f}°',
            ha='center', va='bottom', fontsize=10, fontweight='bold',
            color='green' if delta_hc < 0 else 'red')

    # Add delta annotation for CVD
    delta_cvd = means_cvd[1] - means_cvd[0]
    y_pos_cvd = max(means_cvd) + max(stds_cvd) + 5
    arrow_y_cvd = y_pos_cvd - 3
    ax.annotate('', xy=(4.5, arrow_y_cvd), xytext=(3.5, arrow_y_cvd),
                arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(4, y_pos_cvd, f'Δ={delta_cvd:.1f}°',
            ha='center', va='bottom', fontsize=10,
            color='green' if delta_cvd < 0 else 'red')

    # Formatting
    ax.set_xticks([1.5, 4])
    ax.set_xticklabels(['HC', 'CVD'])
    ax.set_title(roi_name, fontsize=12, fontweight='bold')
    ax.set_ylim(0, 130)
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(90, color='gray', linestyle='--', alpha=0.5, label='Chance')

    if idx == 0:
        ax.set_ylabel('Mean Angular Error (°)', fontsize=11)

# Add legend
handles = [
    plt.Rectangle((0,0),1,1, fc=colors_hc['baseline'], ec='black', alpha=0.7),
    plt.Rectangle((0,0),1,1, fc=colors_hc['ensemble'], ec='black', alpha=0.7),
    plt.Rectangle((0,0),1,1, fc=colors_cvd['baseline'], ec='black', alpha=0.7),
    plt.Rectangle((0,0),1,1, fc=colors_cvd['ensemble'], ec='black', alpha=0.7),
    plt.Line2D([0], [0], color='gray', linestyle='--', alpha=0.5)
]
labels = ['Baseline (HC)', 'Ensemble (HC)', 'Baseline (CVD)', 'Ensemble (CVD)', 'Chance (90°)']
fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=5, frameon=False)

plt.tight_layout()
plt.savefig(Path(__file__).parent / 'ensemble_comparison_barplot.png', dpi=300, bbox_inches='tight')
print(f"✓ Saved: ensemble_comparison_barplot.png")

# ============================================================================
# Figure 2: Individual Subject Scatter
# ============================================================================

fig2, axes2 = plt.subplots(1, 4, figsize=(16, 4))
fig2.suptitle('Individual Subject Improvements (FE_Ensemble vs Baseline)', fontsize=14, fontweight='bold')

for idx, (roi, roi_name) in enumerate(zip(rois, roi_names)):
    ax = axes2[idx]

    # HC subjects
    x_hc = baseline_hc[roi]
    y_hc = ensemble_hc[roi]

    # CVD subjects
    x_cvd = baseline_cvd[roi]
    y_cvd = ensemble_cvd[roi]

    # Plot
    ax.scatter(x_hc, y_hc, s=100, alpha=0.7, color=colors_hc['ensemble'],
               edgecolor='black', linewidth=1.5, label='HC', marker='o')
    ax.scatter(x_cvd, y_cvd, s=100, alpha=0.7, color=colors_cvd['ensemble'],
               edgecolor='black', linewidth=1.5, label='CVD', marker='s')

    # Identity line
    lim = [0, 130]
    ax.plot(lim, lim, 'k--', alpha=0.5, lw=2, label='No change')

    # Add improvement/worsening regions
    ax.fill_between(lim, 0, lim, alpha=0.1, color='green', label='Improvement')
    ax.fill_between(lim, lim, 130, alpha=0.1, color='red', label='Worsening')

    # Formatting
    ax.set_xlabel('Baseline MAE (°)', fontsize=10)
    if idx == 0:
        ax.set_ylabel('FE_Ensemble MAE (°)', fontsize=10)
    ax.set_title(roi_name, fontsize=12, fontweight='bold')
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.grid(alpha=0.3)
    ax.set_aspect('equal')

    if idx == 3:
        ax.legend(loc='upper left', frameon=True, fontsize=9)

plt.tight_layout()
plt.savefig(Path(__file__).parent / 'ensemble_comparison_scatter.png', dpi=300, bbox_inches='tight')
print(f"✓ Saved: ensemble_comparison_scatter.png")

# ============================================================================
# Figure 3: Ensemble Variant Comparison
# ============================================================================

models = ['ForwardEncoding', 'FE_Ensemble', 'FE_EnsembleRidge', 'FE_EnsembleGaussML']
model_names = ['Baseline', 'Ensemble', 'Ensemble+Ridge', 'Ensemble+GaussML']
model_colors = ['#4477AA', '#228833', '#CCBB44', '#EE6677']

fig3, axes3 = plt.subplots(1, 4, figsize=(16, 4), sharey=True)
fig3.suptitle('Ensemble Variant Comparison (HC Group)', fontsize=14, fontweight='bold')

for idx, (roi, roi_name) in enumerate(zip(rois, roi_names)):
    ax = axes3[idx]

    means = []
    stds = []

    for model in models:
        values = []
        for subj_id in subjects_hc:
            if subj_id in data['per_subject'] and roi in data['per_subject'][subj_id]:
                if model in data['per_subject'][subj_id][roi]:
                    values.append(data['per_subject'][subj_id][roi][model]['mae'])

        means.append(np.mean(values) if values else np.nan)
        stds.append(np.std(values, ddof=1) if values else np.nan)

    x = np.arange(len(models))
    bars = ax.bar(x, means, yerr=stds, capsize=5, alpha=0.7,
                  color=model_colors, edgecolor='black', linewidth=1.5)

    # Highlight baseline vs ensemble improvement
    if not np.isnan(means[0]) and not np.isnan(means[1]):
        delta = means[1] - means[0]
        y_pos = max(means[:2]) + max(stds[:2]) + 5
        arrow_y = y_pos - 3
        ax.annotate('', xy=(1, arrow_y), xytext=(0, arrow_y),
                    arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
        ax.text(0.5, y_pos, f'{delta:.1f}°',
                ha='center', va='bottom', fontsize=9, fontweight='bold',
                color='green' if delta < 0 else 'red')

    # Formatting
    ax.set_xticks(x)
    ax.set_xticklabels(model_names, rotation=15, ha='right')
    ax.set_title(roi_name, fontsize=12, fontweight='bold')
    ax.set_ylim(0, 150)
    ax.grid(axis='y', alpha=0.3)
    ax.axhline(90, color='gray', linestyle='--', alpha=0.5)

    if idx == 0:
        ax.set_ylabel('Mean Angular Error (°)', fontsize=11)

plt.tight_layout()
plt.savefig(Path(__file__).parent / 'ensemble_variants_comparison.png', dpi=300, bbox_inches='tight')
print(f"✓ Saved: ensemble_variants_comparison.png")

print("\n✓ All figures saved successfully!")
