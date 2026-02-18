#!/usr/bin/env python3
"""
SRM Analysis Detailed Visualization
8-panel figure showing each validation test individually with data distributions.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path

# --- Load results ---
RESULT_PATH = Path(__file__).resolve().parent / "results" / "loo_consistent" / "20260218_163819" / "loo_consistent_results.json"
with open(RESULT_PATH) as f:
    data = json.load(f)

ROIS = ['V1', 'V2', 'V3', 'hV4']
HC_SUBJECTS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
CVD_SUBJECTS = ['sub-08', 'sub-09', 'sub-10']
CVD_MARKERS = {'sub-08': 's', 'sub-09': '^', 'sub-10': 'D'}
CVD_LABELS = {'sub-08': 'sub-08 (deutan)', 'sub-09': 'sub-09 (protan)', 'sub-10': 'sub-10 (deutan)'}
HC_COLOR = '#3498db'
CVD_COLOR = '#e74c3c'
CVD_INDIV_COLORS = {'sub-08': '#e74c3c', 'sub-09': '#2980b9', 'sub-10': '#27ae60'}

results = data['results']

fig = plt.figure(figsize=(18, 24))
gs = gridspec.GridSpec(4, 2, hspace=0.35, wspace=0.3)
fig.suptitle('SRM Between-Subject Analysis: Detailed Validation Results',
             fontsize=16, fontweight='bold', y=0.995)

# ============================================================
# Panel A: Group Disparity Strip Plot (LOO-consistent)
# ============================================================
ax_a = fig.add_subplot(gs[0, 0])

for i, r in enumerate(ROIS):
    # HC individual dots
    hc_vals = [results[r]['hc_loo_disparities'][s] for s in HC_SUBJECTS]
    jitter_hc = np.random.default_rng(42).uniform(-0.12, 0.12, len(hc_vals))
    ax_a.scatter(np.full(len(hc_vals), i) - 0.2 + jitter_hc, hc_vals,
                 color=HC_COLOR, alpha=0.6, s=30, zorder=3, edgecolors='white', linewidth=0.5)

    # CVD individual dots with distinct markers
    for j, s in enumerate(CVD_SUBJECTS):
        score = results[r]['individual_cvd'][s]['cvd_score']
        ax_a.scatter(i + 0.2 + (j-1)*0.08, score, marker=CVD_MARKERS[s],
                     color=CVD_INDIV_COLORS[s], s=80, zorder=5, edgecolors='black', linewidth=0.8,
                     label=CVD_LABELS[s] if i == 0 else None)

    # Group means + CI
    hc_m = results[r]['summary']['hc_mean']
    cvd_m = results[r]['summary']['cvd_mean']
    hc_ci = results[r]['summary']['hc_ci']
    cvd_ci = results[r]['summary']['cvd_ci']

    ax_a.plot([i-0.32, i-0.08], [hc_m, hc_m], color=HC_COLOR, linewidth=2.5, zorder=4)
    ax_a.plot([i-0.2, i-0.2], hc_ci, color=HC_COLOR, linewidth=1.5, zorder=4)
    ax_a.plot([i+0.08, i+0.32], [cvd_m, cvd_m], color=CVD_COLOR, linewidth=2.5, zorder=4)
    ax_a.plot([i+0.2, i+0.2], cvd_ci, color=CVD_COLOR, linewidth=1.5, zorder=4)

    # p-value annotation
    p = results[r]['summary']['group_perm_p']
    y_top = max(max(hc_vals), max(results[r]['individual_cvd'][s]['cvd_score'] for s in CVD_SUBJECTS)) + 0.04
    sig = '*' if p < 0.05 else '~' if p < 0.1 else ''
    ax_a.text(i, y_top, f'p={p:.3f}{sig}', ha='center', fontsize=8, fontstyle='italic')

ax_a.set_xticks(range(len(ROIS)))
ax_a.set_xticklabels(ROIS)
ax_a.set_ylabel('Procrustes Disparity')
ax_a.set_title('A. Group Disparity (LOO-consistent)', fontweight='bold')

# Manual legend for HC
from matplotlib.lines import Line2D
handles = [Line2D([0], [0], marker='o', color='w', markerfacecolor=HC_COLOR, markersize=8, label='HC (n=7)')]
for s in CVD_SUBJECTS:
    handles.append(Line2D([0], [0], marker=CVD_MARKERS[s], color='w',
                          markerfacecolor=CVD_INDIV_COLORS[s], markersize=8,
                          markeredgecolor='black', label=CVD_LABELS[s]))
ax_a.legend(handles=handles, loc='upper left', fontsize=7, framealpha=0.9)
ax_a.set_ylim(0.2, 1.05)

# ============================================================
# Panel B: Crawford & Howell — HC distribution + CVD scores
# ============================================================
ax_b = fig.add_subplot(gs[0, 1])

for i, r in enumerate(ROIS):
    # HC individual LOO disparities as box-like strip
    hc_vals = [results[r]['hc_loo_disparities'][s] for s in HC_SUBJECTS]
    hc_arr = np.array(hc_vals)
    hc_m = hc_arr.mean()
    hc_s = hc_arr.std(ddof=1)

    # Draw HC range (mean +/- 2SD) as shaded region
    ax_b.fill_between([i-0.3, i+0.3], hc_m - 2*hc_s, hc_m + 2*hc_s,
                       color=HC_COLOR, alpha=0.1, zorder=1)
    ax_b.fill_between([i-0.3, i+0.3], hc_m - hc_s, hc_m + hc_s,
                       color=HC_COLOR, alpha=0.2, zorder=1)
    ax_b.plot([i-0.3, i+0.3], [hc_m, hc_m], color=HC_COLOR, linewidth=2, zorder=2)

    # HC individual dots
    jitter = np.random.default_rng(42).uniform(-0.08, 0.08, len(hc_vals))
    ax_b.scatter(np.full(len(hc_vals), i) + jitter, hc_vals,
                 color=HC_COLOR, alpha=0.5, s=25, zorder=3, edgecolors='white', linewidth=0.5)

    # CVD individual scores with p-value labels
    for j, s in enumerate(CVD_SUBJECTS):
        score = results[r]['individual_cvd'][s]['cvd_score']
        p = results[r]['individual_cvd'][s]['p_value']
        ax_b.scatter(i + 0.15 + j*0.06, score, marker=CVD_MARKERS[s],
                     color=CVD_INDIV_COLORS[s], s=100, zorder=5, edgecolors='black', linewidth=1)
        if p < 0.05:
            ax_b.annotate(f'p={p:.3f}*', (i + 0.15 + j*0.06, score),
                         textcoords='offset points', xytext=(8, -3 if j != 1 else 8),
                         fontsize=7, fontweight='bold', color=CVD_INDIV_COLORS[s])

ax_b.set_xticks(range(len(ROIS)))
ax_b.set_xticklabels(ROIS)
ax_b.set_ylabel('Procrustes Disparity')
ax_b.set_title('B. Crawford & Howell: CVD vs HC Distribution', fontweight='bold')

# Legend
handles_b = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor=HC_COLOR, markersize=8, label='HC (mean +/- 1,2 SD)'),
]
for s in CVD_SUBJECTS:
    handles_b.append(Line2D([0], [0], marker=CVD_MARKERS[s], color='w',
                           markerfacecolor=CVD_INDIV_COLORS[s], markersize=8,
                           markeredgecolor='black', label=CVD_LABELS[s]))
ax_b.legend(handles=handles_b, loc='upper left', fontsize=7, framealpha=0.9)
ax_b.set_ylim(0.2, 1.05)

# ============================================================
# Panel C: Bootstrap CIs for Separation (forest plot)
# ============================================================
ax_c = fig.add_subplot(gs[1, 0])

for i, r in enumerate(ROIS):
    sep = results[r]['summary']['separation']
    sep_ci = results[r]['summary']['separation_ci']
    g = results[r]['summary']['hedges_g']

    color = '#27ae60' if sep_ci[0] > 0 else '#e74c3c' if sep_ci[1] < 0 else '#f39c12'

    ax_c.errorbar(sep, i, xerr=[[sep - sep_ci[0]], [sep_ci[1] - sep]],
                  fmt='o', color=color, markersize=10, capsize=6, capthick=2, linewidth=2,
                  markeredgecolor='black', markeredgewidth=0.5)
    ax_c.text(sep_ci[1] + 0.01, i + 0.15, f'g={g:.2f}', fontsize=8, color='gray')
    # CI text
    ax_c.text(sep_ci[1] + 0.01, i - 0.2, f'[{sep_ci[0]:.3f}, {sep_ci[1]:.3f}]', fontsize=7, color='gray')

ax_c.axvline(x=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
ax_c.set_yticks(range(len(ROIS)))
ax_c.set_yticklabels(ROIS)
ax_c.set_xlabel('CVD - HC Separation (Procrustes Disparity)')
ax_c.set_title('C. Bootstrap 95% CIs for Group Separation', fontweight='bold')
ax_c.invert_yaxis()

# Color legend
from matplotlib.patches import Patch
handles_c = [
    Patch(facecolor='#27ae60', label='CI excludes 0'),
    Patch(facecolor='#f39c12', label='CI includes 0'),
]
ax_c.legend(handles=handles_c, loc='lower right', fontsize=8)

# ============================================================
# Panel D: LOSO Disparity Strip Plot
# ============================================================
ax_d = fig.add_subplot(gs[1, 1])

for i, r in enumerate(ROIS):
    loso = results[r]['loso_analysis']

    # HC held-out disparities
    hc_ho_vals = [loso['hc_held_out_disparities'][s] for s in HC_SUBJECTS]
    jitter_hc = np.random.default_rng(42).uniform(-0.12, 0.12, len(hc_ho_vals))
    ax_d.scatter(np.full(len(hc_ho_vals), i) - 0.2 + jitter_hc, hc_ho_vals,
                 color=HC_COLOR, alpha=0.6, s=30, zorder=3, edgecolors='white', linewidth=0.5)

    # CVD LOSO scores (mean across folds)
    for j, s in enumerate(CVD_SUBJECTS):
        score = loso['individual_cvd'][s]['cvd_score']
        ax_d.scatter(i + 0.2 + (j-1)*0.08, score, marker=CVD_MARKERS[s],
                     color=CVD_INDIV_COLORS[s], s=80, zorder=5, edgecolors='black', linewidth=0.8)

    # Group means
    hc_m = loso['summary']['hc_mean']
    cvd_m = loso['summary']['cvd_mean']
    ax_d.plot([i-0.32, i-0.08], [hc_m, hc_m], color=HC_COLOR, linewidth=2.5, zorder=4)
    ax_d.plot([i+0.08, i+0.32], [cvd_m, cvd_m], color=CVD_COLOR, linewidth=2.5, zorder=4)

    # p-value
    p = loso['summary']['group_perm_p']
    y_top = max(max(hc_ho_vals), max(loso['individual_cvd'][s]['cvd_score'] for s in CVD_SUBJECTS)) + 0.04
    ax_d.text(i, y_top, f'p={p:.3f}', ha='center', fontsize=8, fontstyle='italic')

ax_d.set_xticks(range(len(ROIS)))
ax_d.set_xticklabels(ROIS)
ax_d.set_ylabel('Procrustes Disparity')
ax_d.set_title('D. LOSO Disparity (HC projected via SVD, same as CVD)', fontweight='bold')
ax_d.set_ylim(0.2, 1.1)

# ============================================================
# Panel E: Single-SRM Color Permutation — CVD metrics
# ============================================================
ax_e = fig.add_subplot(gs[2, 0])

x_pos = np.arange(len(ROIS))
width = 0.25

# CVD score: observed vs null
cvd_obs = [results[r]['color_label_permutation']['observed']['cvd_score_mean'] for r in ROIS]
cvd_null = [results[r]['color_label_permutation']['null_means']['cvd_score_mean'] for r in ROIS]
cvd_p = [results[r]['color_label_permutation']['p_values']['cvd_score_disp'] for r in ROIS]

# CVD pairwise: observed vs null
cvd_pw_obs = [results[r]['color_label_permutation']['observed']['cvd_pairwise_mean'] for r in ROIS]
cvd_pw_null = [results[r]['color_label_permutation']['null_means']['cvd_pairwise_mean'] for r in ROIS]
cvd_pw_p = [results[r]['color_label_permutation']['p_values']['cvd_pairwise_disp'] for r in ROIS]

bars1 = ax_e.bar(x_pos - width, cvd_obs, width, label='CVD score (observed)',
                  color=CVD_COLOR, alpha=0.8, edgecolor='black', linewidth=0.5)
bars2 = ax_e.bar(x_pos, cvd_null, width, label='CVD score (null)',
                  color=CVD_COLOR, alpha=0.3, edgecolor='black', linewidth=0.5, hatch='//')
bars3 = ax_e.bar(x_pos + width, cvd_pw_obs, width, label='CVD pairwise (observed)',
                  color='#8e44ad', alpha=0.8, edgecolor='black', linewidth=0.5)

# p-value annotations
for i in range(len(ROIS)):
    y = max(cvd_obs[i], cvd_null[i]) + 0.01
    sig = '*' if cvd_p[i] < 0.05 else ''
    fw = 'bold' if cvd_p[i] < 0.05 else 'normal'
    ax_e.text(i - width/2, y, f'p={cvd_p[i]:.3f}{sig}', ha='center', fontsize=7, fontweight=fw, color='#c0392b')

    # Pairwise p
    y2 = cvd_pw_obs[i] + 0.01
    sig2 = '*' if cvd_pw_p[i] < 0.05 else ''
    fw2 = 'bold' if cvd_pw_p[i] < 0.05 else 'normal'
    ax_e.text(i + width, y2, f'p={cvd_pw_p[i]:.3f}{sig2}', ha='center', fontsize=7, fontweight=fw2, color='#7d3c98')

    # Arrow showing direction: if observed < null, color helps (lower disparity)
    if cvd_obs[i] < cvd_null[i]:
        ax_e.annotate('', xy=(i - width, cvd_obs[i]), xytext=(i, cvd_null[i]),
                      arrowprops=dict(arrowstyle='->', color='green', lw=1.5, alpha=0.5))

ax_e.set_xticks(x_pos)
ax_e.set_xticklabels(ROIS)
ax_e.set_ylabel('Mean Disparity')
ax_e.set_title('E. Single-SRM Color Permutation (CVD)', fontweight='bold')
ax_e.legend(loc='upper left', fontsize=7)
ax_e.set_ylim(0, 1.1)

# ============================================================
# Panel F: LOSO Color Permutation — HC vs CVD comparison
# ============================================================
ax_f = fig.add_subplot(gs[2, 1])

x_pos = np.arange(len(ROIS))
width = 0.18

hc_obs_loso = [results[r]['loso_analysis']['color_label_permutation']['observed']['hc_held_out_mean'] for r in ROIS]
hc_null_loso = [results[r]['loso_analysis']['color_label_permutation']['null_means']['hc_held_out_mean'] for r in ROIS]
hc_p_loso = [results[r]['loso_analysis']['color_label_permutation']['p_values']['hc_held_out_disp'] for r in ROIS]

cvd_obs_loso = [results[r]['loso_analysis']['color_label_permutation']['observed']['cvd_score_mean'] for r in ROIS]
cvd_null_loso = [results[r]['loso_analysis']['color_label_permutation']['null_means']['cvd_score_mean'] for r in ROIS]
cvd_p_loso = [results[r]['loso_analysis']['color_label_permutation']['p_values']['cvd_score_disp'] for r in ROIS]

ax_f.bar(x_pos - 1.5*width, hc_obs_loso, width, label='HC obs', color=HC_COLOR, alpha=0.8, edgecolor='black', linewidth=0.5)
ax_f.bar(x_pos - 0.5*width, hc_null_loso, width, label='HC null', color=HC_COLOR, alpha=0.3, edgecolor='black', linewidth=0.5, hatch='//')
ax_f.bar(x_pos + 0.5*width, cvd_obs_loso, width, label='CVD obs', color=CVD_COLOR, alpha=0.8, edgecolor='black', linewidth=0.5)
ax_f.bar(x_pos + 1.5*width, cvd_null_loso, width, label='CVD null', color=CVD_COLOR, alpha=0.3, edgecolor='black', linewidth=0.5, hatch='//')

for i in range(len(ROIS)):
    # HC p
    y_hc = max(hc_obs_loso[i], hc_null_loso[i]) + 0.01
    ax_f.text(i - width, y_hc, f'p={hc_p_loso[i]:.2f}', ha='center', fontsize=7, color='#2980b9')

    # CVD p
    y_cvd = max(cvd_obs_loso[i], cvd_null_loso[i]) + 0.01
    sig = '*' if cvd_p_loso[i] < 0.05 else '**' if cvd_p_loso[i] < 0.01 else ''
    if cvd_p_loso[i] == 0.0:
        sig = '***'
    fw = 'bold' if cvd_p_loso[i] < 0.05 else 'normal'
    ax_f.text(i + width, y_cvd, f'p={cvd_p_loso[i]:.3f}{sig}', ha='center', fontsize=7,
              fontweight=fw, color='#c0392b')

ax_f.set_xticks(x_pos)
ax_f.set_xticklabels(ROIS)
ax_f.set_ylabel('Mean Disparity')
ax_f.set_title('F. LOSO Color Permutation (symmetric HC & CVD)', fontweight='bold')
ax_f.legend(loc='upper left', fontsize=7, ncol=2)
ax_f.set_ylim(0, 0.95)

# ============================================================
# Panel G: RDM Correlations
# ============================================================
ax_g = fig.add_subplot(gs[3, 0])

x_pos = np.arange(len(ROIS))
width = 0.25

hh = [results[r]['rdm_correlations']['hc_hc']['mean'] for r in ROIS]
hc = [results[r]['rdm_correlations']['hc_cvd']['mean'] for r in ROIS]
cc = [results[r]['rdm_correlations']['cvd_cvd']['mean'] for r in ROIS]

ax_g.bar(x_pos - width, hh, width, label='HC-HC (n=21 pairs)', color=HC_COLOR, alpha=0.8,
         edgecolor='black', linewidth=0.5)
ax_g.bar(x_pos, hc, width, label='HC-CVD (n=21 pairs)', color='#9b59b6', alpha=0.7,
         edgecolor='black', linewidth=0.5)
ax_g.bar(x_pos + width, cc, width, label='CVD-CVD (n=3 pairs)', color=CVD_COLOR, alpha=0.8,
         edgecolor='black', linewidth=0.5)

# Value labels
for i in range(len(ROIS)):
    ax_g.text(i - width, hh[i] + 0.01, f'{hh[i]:.2f}', ha='center', fontsize=7, color='#2980b9')
    ax_g.text(i, hc[i] + 0.01, f'{hc[i]:.2f}', ha='center', fontsize=7, color='#7d3c98')
    ax_g.text(i + width, cc[i] + 0.01, f'{cc[i]:.2f}', ha='center', fontsize=7, color='#c0392b')

ax_g.set_xticks(x_pos)
ax_g.set_xticklabels(ROIS)
ax_g.set_ylabel('Mean RDM Correlation')
ax_g.set_title('G. RDM Correlations in SRM Space', fontweight='bold')
ax_g.legend(loc='upper right', fontsize=7)
ax_g.set_ylim(0, 0.65)

# ============================================================
# Panel H: LOSO Crawford & Howell — comparison with single-SRM
# ============================================================
ax_h = fig.add_subplot(gs[3, 1])

# For each CVD subject, show single-SRM p vs LOSO p across ROIs
bar_width = 0.12
roi_positions = np.arange(len(ROIS))

for j, s in enumerate(CVD_SUBJECTS):
    single_p = [results[r]['individual_cvd'][s]['p_value'] for r in ROIS]
    loso_p = [results[r]['loso_analysis']['individual_cvd'][s]['p_value'] for r in ROIS]

    offset = (j - 1) * 0.28
    ax_h.bar(roi_positions + offset - bar_width/2, single_p, bar_width,
             color=CVD_INDIV_COLORS[s], alpha=0.8, edgecolor='black', linewidth=0.5,
             label=f'{CVD_LABELS[s]} (single)' if True else None)
    ax_h.bar(roi_positions + offset + bar_width/2, loso_p, bar_width,
             color=CVD_INDIV_COLORS[s], alpha=0.35, edgecolor='black', linewidth=0.5, hatch='//',
             label=f'{CVD_LABELS[s]} (LOSO)' if True else None)

    # Mark significant
    for i in range(len(ROIS)):
        if single_p[i] < 0.05:
            ax_h.scatter(i + offset - bar_width/2, single_p[i] + 0.02, marker='*',
                        color=CVD_INDIV_COLORS[s], s=60, zorder=5)
        if loso_p[i] < 0.05:
            ax_h.scatter(i + offset + bar_width/2, loso_p[i] + 0.02, marker='*',
                        color=CVD_INDIV_COLORS[s], s=60, zorder=5)

ax_h.axhline(y=0.05, color='black', linestyle='--', linewidth=1, alpha=0.5, label='p=0.05')
ax_h.set_xticks(roi_positions)
ax_h.set_xticklabels(ROIS)
ax_h.set_ylabel('p-value (one-tailed)')
ax_h.set_title('H. Crawford & Howell: Single-SRM vs LOSO', fontweight='bold')
ax_h.legend(loc='upper right', fontsize=6, ncol=2)
ax_h.set_ylim(0, 1.05)

# ============================================================
# Save
# ============================================================
out_dir = Path(__file__).resolve().parent / "results" / "loo_consistent" / "20260218_163819"
out_path = out_dir / "srm_detailed_figure.png"
plt.savefig(out_path, dpi=200, bbox_inches='tight', facecolor='white')
print(f"Saved to: {out_path}")

common_path = Path(__file__).resolve().parent / "results" / "srm_detailed_figure.png"
plt.savefig(common_path, dpi=200, bbox_inches='tight', facecolor='white')
print(f"Saved to: {common_path}")

plt.close()
