#!/usr/bin/env python3
"""
SRM Analysis Summary Visualization
Generates a 4-panel figure summarizing the LOO-consistent + LOSO results.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from pathlib import Path

# --- Load results ---
RESULT_PATH = Path(__file__).resolve().parent / "results" / "loo_consistent" / "20260218_163819" / "loo_consistent_results.json"
with open(RESULT_PATH) as f:
    data = json.load(f)

ROIS = ['V1', 'V2', 'V3', 'hV4']
HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
CVD_MARKERS = {'sub-08': 's', 'sub-09': '^', 'sub-10': 'D'}
CVD_COLORS_MAP = {'sub-08': '#e74c3c', 'sub-09': '#3498db', 'sub-10': '#2ecc71'}

results = data['results']

fig = plt.figure(figsize=(16, 14))
fig.suptitle('SRM Between-Subject Analysis: LOO-Consistent + LOSO Color-Dependency',
             fontsize=14, fontweight='bold', y=0.98)

# ============================================================
# Panel A: Group Disparity Comparison (LOO-consistent)
# ============================================================
ax1 = fig.add_subplot(2, 2, 1)

x_pos = np.arange(len(ROIS))
width = 0.35

hc_means = [results[r]['summary']['hc_mean'] for r in ROIS]
cvd_means = [results[r]['summary']['cvd_mean'] for r in ROIS]
hc_cis = [results[r]['summary']['hc_ci'] for r in ROIS]
cvd_cis = [results[r]['summary']['cvd_ci'] for r in ROIS]

hc_errs = [[m - ci[0] for m, ci in zip(hc_means, hc_cis)],
            [ci[1] - m for m, ci in zip(hc_means, hc_cis)]]
cvd_errs = [[m - ci[0] for m, ci in zip(cvd_means, cvd_cis)],
             [ci[1] - m for m, ci in zip(cvd_means, cvd_cis)]]

bars_hc = ax1.bar(x_pos - width/2, hc_means, width, yerr=hc_errs,
                   label='HC (n=7)', color='#3498db', alpha=0.7, capsize=4, edgecolor='black', linewidth=0.5)
bars_cvd = ax1.bar(x_pos + width/2, cvd_means, width, yerr=cvd_errs,
                    label='CVD (n=3)', color='#e74c3c', alpha=0.7, capsize=4, edgecolor='black', linewidth=0.5)

# Add individual CVD dots
for j, s in enumerate(CVD_SUBJECTS):
    for i, r in enumerate(ROIS):
        score = results[r]['individual_cvd'][s]['cvd_score']
        ax1.scatter(i + width/2 + (j-1)*0.08, score, marker=CVD_MARKERS[s],
                    color=CVD_COLORS_MAP[s], s=40, zorder=5, edgecolors='black', linewidth=0.5)

# Add p-values
p_vals = [results[r]['summary']['group_perm_p'] for r in ROIS]
for i, p in enumerate(p_vals):
    y_max = max(hc_means[i] + hc_errs[1][i], cvd_means[i] + cvd_errs[1][i]) + 0.02
    sig = '†' if p < 0.1 else 'n.s.'
    ax1.text(i, y_max + 0.01, f'p={p:.3f}{" " + sig if sig != "n.s." else ""}',
             ha='center', fontsize=8, fontstyle='italic')

ax1.set_xticks(x_pos)
ax1.set_xticklabels(ROIS)
ax1.set_ylabel('Procrustes Disparity')
ax1.set_title('A. Group Disparity (LOO-consistent)', fontweight='bold')
ax1.legend(loc='upper left', fontsize=8)
ax1.set_ylim(0, 1.05)

# ============================================================
# Panel B: Individual CVD Tests (Crawford & Howell)
# ============================================================
ax2 = fig.add_subplot(2, 2, 2)

for j, s in enumerate(CVD_SUBJECTS):
    p_vals_subj = []
    for r in ROIS:
        p = results[r]['individual_cvd'][s]['p_value']
        p_vals_subj.append(p)
    ax2.plot(range(len(ROIS)), p_vals_subj, marker=CVD_MARKERS[s],
             color=CVD_COLORS_MAP[s], label=f'{s} ({"protan" if s == "sub-09" else "deutan"})',
             linewidth=2, markersize=10, zorder=5)

ax2.axhline(y=0.05, color='black', linestyle='--', linewidth=1, alpha=0.5, label='p=0.05')
ax2.axhline(y=0.01, color='gray', linestyle=':', linewidth=1, alpha=0.5, label='p=0.01')

# Annotate significant results
for j, s in enumerate(CVD_SUBJECTS):
    for i, r in enumerate(ROIS):
        p = results[r]['individual_cvd'][s]['p_value']
        if p < 0.05:
            ax2.annotate(f'p={p:.3f}*', (i, p), textcoords='offset points',
                         xytext=(10, -5 if j == 0 else 10), fontsize=8, fontweight='bold',
                         color=CVD_COLORS_MAP[s])

ax2.set_xticks(range(len(ROIS)))
ax2.set_xticklabels(ROIS)
ax2.set_ylabel('p-value (one-tailed)')
ax2.set_title('B. Individual CVD Tests (Crawford & Howell)', fontweight='bold')
ax2.legend(loc='upper right', fontsize=7)
ax2.set_ylim(-0.02, 1.0)
ax2.invert_yaxis()

# ============================================================
# Panel C: LOSO Color-Dependency (observed vs null)
# ============================================================
ax3 = fig.add_subplot(2, 2, 3)

x_pos = np.arange(len(ROIS))
width = 0.2

hc_obs = [results[r]['loso_analysis']['color_label_permutation']['observed']['hc_held_out_mean'] for r in ROIS]
hc_null = [results[r]['loso_analysis']['color_label_permutation']['null_means']['hc_held_out_mean'] for r in ROIS]
cvd_obs = [results[r]['loso_analysis']['color_label_permutation']['observed']['cvd_score_mean'] for r in ROIS]
cvd_null = [results[r]['loso_analysis']['color_label_permutation']['null_means']['cvd_score_mean'] for r in ROIS]

ax3.bar(x_pos - 1.5*width, hc_obs, width, label='HC observed', color='#3498db', alpha=0.8, edgecolor='black', linewidth=0.5)
ax3.bar(x_pos - 0.5*width, hc_null, width, label='HC null (shuffled)', color='#3498db', alpha=0.3, edgecolor='black', linewidth=0.5, hatch='//')
ax3.bar(x_pos + 0.5*width, cvd_obs, width, label='CVD observed', color='#e74c3c', alpha=0.8, edgecolor='black', linewidth=0.5)
ax3.bar(x_pos + 1.5*width, cvd_null, width, label='CVD null (shuffled)', color='#e74c3c', alpha=0.3, edgecolor='black', linewidth=0.5, hatch='//')

# Add p-values
for i, r in enumerate(ROIS):
    loso_p = results[r]['loso_analysis']['color_label_permutation']['p_values']
    hc_p = loso_p['hc_held_out_disp']
    cvd_p = loso_p['cvd_score_disp']

    # HC p-value
    y_hc = max(hc_obs[i], hc_null[i]) + 0.01
    ax3.text(i - width, y_hc, f'p={hc_p:.2f}', ha='center', fontsize=7, color='#2980b9')

    # CVD p-value
    y_cvd = max(cvd_obs[i], cvd_null[i]) + 0.01
    sig = '*' if cvd_p < 0.05 else ''
    fontw = 'bold' if cvd_p < 0.05 else 'normal'
    ax3.text(i + width, y_cvd, f'p={cvd_p:.3f}{sig}', ha='center', fontsize=7, color='#c0392b', fontweight=fontw)

ax3.set_xticks(x_pos)
ax3.set_xticklabels(ROIS)
ax3.set_ylabel('Mean Disparity')
ax3.set_title('C. LOSO Color-Dependency (true vs shuffled labels)', fontweight='bold')
ax3.legend(loc='upper left', fontsize=7, ncol=2)
ax3.set_ylim(0, 0.95)

# ============================================================
# Panel D: Validation Suite Summary (heatmap)
# ============================================================
ax4 = fig.add_subplot(2, 2, 4)

tests = [
    'Group perm\n(LOO)',
    'Crawford\n(any CVD)',
    'LOSO\nstability',
    'Split-half',
    'CVD color\n(single-SRM)',
    'CVD color\n(LOSO)',
    'HC color\n(LOSO)',
]

# Manual data from results
validation_data = {
    'V1': [0.062, 0.007, 6/7, 1/2, 0.427, 0.412, 0.364],
    'V2': [0.075, 0.040, 7/7, 2/2, 0.033, 0.010, 0.227],
    'V3': [0.395, 0.052, 0/7, 0/2, 0.009, 0.000, 0.207],
    'hV4': [0.559, 0.411, 0/7, 0/2, 0.028, 0.016, 0.330],
}

# Color scheme: green = significant/pass, yellow = trending, red = n.s.
def p_to_color(p, is_rate=False):
    if is_rate:
        if p >= 0.8:
            return '#27ae60'  # green
        elif p >= 0.5:
            return '#f39c12'  # yellow
        else:
            return '#e74c3c'  # red
    else:
        if p < 0.01:
            return '#1a7a3a'  # dark green
        elif p < 0.05:
            return '#27ae60'  # green
        elif p < 0.1:
            return '#f39c12'  # yellow
        else:
            return '#e74c3c'  # red

cell_w = 1.0
cell_h = 1.0

for i, r in enumerate(ROIS):
    for j, (test_name, val) in enumerate(zip(tests, validation_data[r])):
        is_rate = j in [2, 3]  # LOSO stability and split-half are rates
        # For HC color test, lower p means HC IS color-dependent (bad for our argument)
        # So we want high p = good (green)
        if j == 6:  # HC color LOSO
            color = '#27ae60' if val > 0.1 else '#f39c12' if val > 0.05 else '#e74c3c'
        else:
            color = p_to_color(val, is_rate)

        rect = FancyBboxPatch((i * cell_w, (len(tests) - 1 - j) * cell_h),
                               cell_w * 0.9, cell_h * 0.8,
                               boxstyle="round,pad=0.05",
                               facecolor=color, alpha=0.7, edgecolor='black', linewidth=0.5)
        ax4.add_patch(rect)

        if is_rate:
            txt = f'{val:.0%}'
        elif j == 6:
            txt = f'p={val:.2f}\n(n.s.=good)'
        else:
            sig = '*' if val < 0.05 else '†' if val < 0.1 else ''
            txt = f'p={val:.3f}{sig}' if not is_rate else f'{val:.0%}'
        ax4.text(i * cell_w + cell_w * 0.45, (len(tests) - 1 - j) * cell_h + cell_h * 0.4,
                 txt, ha='center', va='center', fontsize=7, fontweight='bold' if val < 0.05 and not is_rate and j != 6 else 'normal')

# Labels
for i, r in enumerate(ROIS):
    ax4.text(i * cell_w + cell_w * 0.45, len(tests) * cell_h + 0.1, r,
             ha='center', va='bottom', fontsize=10, fontweight='bold')

for j, test_name in enumerate(tests):
    ax4.text(-0.15, (len(tests) - 1 - j) * cell_h + cell_h * 0.4, test_name,
             ha='right', va='center', fontsize=8)

ax4.set_xlim(-0.1, len(ROIS) * cell_w)
ax4.set_ylim(-0.2, len(tests) * cell_h + 0.5)
ax4.axis('off')
ax4.set_title('D. Validation Suite Summary', fontweight='bold', pad=15)

plt.tight_layout(rect=[0, 0, 1, 0.96])

# Save
out_dir = Path(__file__).resolve().parent / "results" / "loo_consistent" / "20260218_163819"
out_path = out_dir / "srm_summary_figure.png"
plt.savefig(out_path, dpi=200, bbox_inches='tight', facecolor='white')
print(f"Saved to: {out_path}")

# Also save to a common location
common_path = Path(__file__).resolve().parent / "results" / "srm_summary_figure.png"
plt.savefig(common_path, dpi=200, bbox_inches='tight', facecolor='white')
print(f"Saved to: {common_path}")

plt.close()
