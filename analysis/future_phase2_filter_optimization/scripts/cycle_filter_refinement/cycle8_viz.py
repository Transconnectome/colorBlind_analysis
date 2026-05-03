#!/usr/bin/env python3
"""cycle8_viz.py — Plan 04 Cycle 7~8 핵심 결과 시각화."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization')
RES = ROOT / 'results/cycles'
FIG = RES / 'cycle8_figures'
FIG.mkdir(parents=True, exist_ok=True)

# ---- Figure 1: z_set + z_vox per (subj, ROI) heatmap ----
with open(RES / 'cycle7_dual_criterion.json') as f:
    A = json.load(f)
subs = ['08', '09', '10']
rois = ['V1', 'V2', 'V4']
z_set = np.array([[A['cvd_per_cell'][s][r]['z_set'] for r in rois] for s in subs])
z_vox = np.array([[A['cvd_per_cell'][s][r]['z_vox'] for r in rois] for s in subs])

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
for ax, mat, title in zip(axes, [z_set, z_vox], ['z_set', 'z_vox-axis (family-aware)']):
    vmax = max(abs(mat).max(), 1)
    im = ax.imshow(mat, cmap='RdBu_r', vmin=-vmax, vmax=vmax, aspect='auto')
    ax.set_xticks(range(len(rois))); ax.set_xticklabels(rois)
    ax.set_yticks(range(len(subs))); ax.set_yticklabels([f'sub-{s}' for s in subs])
    for i in range(len(subs)):
        for j in range(len(rois)):
            ax.text(j, i, f'{mat[i,j]:+.1f}', ha='center', va='center',
                    color='white' if abs(mat[i,j]) > vmax*0.5 else 'black', fontsize=11)
    ax.set_title(title)
    plt.colorbar(im, ax=ax, fraction=0.04)
fig.suptitle('Cycle 7 selection rule components (z-score within HC pool, n=6)')
fig.tight_layout()
fig.savefig(FIG / 'fig1_z_components.png', dpi=120)
plt.close(fig)
print(f'Wrote {FIG}/fig1_z_components.png')

# ---- Figure 2: HC FP vs CVD selection rule distribution ----
with open(RES / 'cycle8_hc_fp.json') as f:
    HC_FP = json.load(f)
HC_subs = ['01', '02', '03', '04', '05', '06']
hc_z_deutan = [HC_FP['results'][h]['deutan']['z_V1+V4'] for h in HC_subs]
hc_z_protan = [HC_FP['results'][h]['protan']['z_V1+V4'] for h in HC_subs]
cvd_z = {'sub-08 (deutan)': -19.32, 'sub-09 (protan)': -5.95, 'sub-10 (near-norm)': -0.09}

fig, ax = plt.subplots(figsize=(10, 5))
x_pos = np.arange(len(HC_subs))
ax.bar(x_pos - 0.18, hc_z_deutan, width=0.35, color='#d97757', alpha=0.7, label='HC LOO (deutan family)')
ax.bar(x_pos + 0.18, hc_z_protan, width=0.35, color='#5a8d8d', alpha=0.7, label='HC LOO (protan family)')
for i, h in enumerate(HC_subs):
    if hc_z_deutan[i] < -2:
        ax.text(i - 0.18, hc_z_deutan[i] - 0.3, 'FP', ha='center', color='red', fontweight='bold')
    if hc_z_protan[i] < -2:
        ax.text(i + 0.18, hc_z_protan[i] - 0.3, 'FP', ha='center', color='red', fontweight='bold')
ax.set_xticks(x_pos); ax.set_xticklabels([f'sub-{h}' for h in HC_subs])
ax.axhline(-2, ls='--', color='gray', alpha=0.5, label='specificity threshold (z=-2)')
ax.axhline(0, ls='-', color='black', alpha=0.3)
# CVD reference points
for label, z in cvd_z.items():
    ax.axhline(z, ls=':', color='red' if 'sub-08' in label or 'sub-09' in label else 'green',
               alpha=0.6, label=f'{label}: z={z}')
ax.set_ylabel('z_combined (V1+V4)')
ax.set_title('HC LOO False Positive vs CVD specificity (Cycle 7 selection rule)')
ax.legend(loc='lower left', fontsize=8)
ax.set_ylim(-22, 16)
fig.tight_layout()
fig.savefig(FIG / 'fig2_hc_fp_vs_cvd.png', dpi=120)
plt.close(fig)
print(f'Wrote {FIG}/fig2_hc_fp_vs_cvd.png')

# ---- Figure 3: Preimage hue circle ----
with open(RES / 'cycle8_preimage.json') as f:
    PRE = json.load(f)
fig, axes = plt.subplots(2, 2, figsize=(10, 10), subplot_kw={'projection': 'polar'})
COLOR_RGB = {
    'red': '#e63946', 'orange': '#f4a261', 'yellow': '#e9c46a',
    'green': '#2a9d8f', 'cyan': '#06aed5', 'blue': '#1d3557',
    'purple': '#7209b7', 'magenta': '#c9184a',
}
for col, subj in enumerate(['08', '09']):
    fam = PRE['subjects'][subj]['family']
    for row, key in enumerate(['preimage_V4_only', 'preimage_V1V4_avg']):
        ax = axes[row, col]
        if key not in PRE['subjects'][subj]:
            continue
        p = PRE['subjects'][subj][key]
        rows = p['rows']
        for r in rows:
            theta_obs = np.deg2rad(r['theta_obs'])
            theta_pre = np.deg2rad(r['theta_preimage'])
            color = COLOR_RGB[r['color_name']]
            ax.plot([theta_obs, theta_pre], [1.0, 0.7], '-', color=color, lw=2, alpha=0.5)
            ax.plot(theta_obs, 1.0, 'o', color=color, markersize=10, label=r['color_name'] if row==0 and col==0 else None)
            ax.plot(theta_pre, 0.7, 's', color=color, markersize=8)
        ax.set_ylim(0, 1.1)
        ax.set_yticks([])
        ax.set_title(f'sub-{subj} ({fam}) {key.replace("preimage_","")}\n'
                     f'β_s={p["used_bs"]:.0f}, β_c={p["used_bc"]:.0f}', fontsize=10)
fig.suptitle('Pre-image hue mapping (○ = observed CVD hue, ■ = stimulus pre-image)')
fig.tight_layout()
fig.savefig(FIG / 'fig3_preimage_hue.png', dpi=120)
plt.close(fig)
print(f'Wrote {FIG}/fig3_preimage_hue.png')

# ---- Figure 4: Local bootstrap CI95 comparison ----
boot_files = sorted((RES / 'cycle8_voxel_bootstrap_local').glob('*.json'))
cells = []
ci_low, ci_high, medians = [], [], []
labels = []
for f in boot_files:
    with open(f) as fp: d = json.load(fp)
    s = d['bootstrap_summary']['L_vox']
    cell = f.stem
    cells.append(cell)
    ci_low.append(s['ci95'][0]); ci_high.append(s['ci95'][1]); medians.append(s['median'])
    fam = d['family']; col = d['family_color']
    labels.append(f'{cell}\n({fam}, {col})')

fig, ax = plt.subplots(figsize=(9, 5))
y = np.arange(len(cells))
colors = ['#d97757' if 'sub-04' in c else '#5a8d8d' for c in cells]
for i, (lo, hi, m, c) in enumerate(zip(ci_low, ci_high, medians, colors)):
    ax.plot([lo, hi], [i, i], '-', color=c, lw=4, alpha=0.6)
    ax.plot(m, i, 'o', color=c, markersize=12)
    ax.text(hi + 0.5, i, f'CI95=[{lo:.1f}, {hi:.1f}]', va='center', fontsize=9)
ax.axvline(-2, ls='--', color='gray', alpha=0.5, label='specificity threshold')
ax.axvline(0, ls='-', color='black', alpha=0.3)
ax.set_yticks(y); ax.set_yticklabels(labels)
ax.set_xlabel('L_vox-axis (family-aware signed)')
ax.set_title('Local n_boot=100 — CVD (sub-09) vs HC LOO (sub-04) overlap')
ax.legend()
fig.tight_layout()
fig.savefig(FIG / 'fig4_bootstrap_overlap.png', dpi=120)
plt.close(fig)
print(f'Wrote {FIG}/fig4_bootstrap_overlap.png')

print(f'\nAll 4 figures in: {FIG}')
