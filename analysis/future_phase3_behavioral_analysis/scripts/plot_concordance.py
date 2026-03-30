"""
LOCO-JND & SRM z-JND concordance visualization
(A) SRM z vs JND ratio — scatter + concordance coloring
(B) LOCO vulnerability vs JND direction — bar + HYPO pair labels
(C) 3-way comparison heatmap (SRM z direction / LOCO vuln / JND direction)
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
RESULTS_DIR = SCRIPT_DIR.parent / "results"
FIG_DIR = SCRIPT_DIR.parent / "figures"
FIG_DIR.mkdir(exist_ok=True)

# ── Load HC group metrics JSON ──
with open(RESULTS_DIR / "hc_group_metrics.json", 'r') as f:
    hc_metrics = json.load(f)

# ── Data ──
pairs_short = ['R-O', 'O-Y', 'Y-G', 'G-B', 'Y-P', 'B-P', 'C-M', 'R-C']
pairs_raw = ['red-orange', 'orange-yellow', 'yellow-green', 'green-blue',
             'yellow-purple', 'blue-purple', 'cyan-magenta', 'red-cyan']

n_hc = hc_metrics[pairs_raw[0]]['n_hc']
hc_mean_jnd = np.array([hc_metrics[p]['hc_mean'] for p in pairs_raw])
cvd_jnd = np.array([hc_metrics[p]['cvd'] for p in pairs_raw])
jnd_ratio = cvd_jnd / hc_mean_jnd
jnd_dir = [hc_metrics[p]['direction_hc_group'] for p in pairs_raw]

# SRM z (best ROI)
srm_z = np.array([1.66, 3.29, 4.14, -0.89, 13.87, 6.15, np.nan, np.nan])

# Concordance
srm_concordant = []
for i, z in enumerate(srm_z):
    if np.isnan(z) or jnd_dir[i] == 'borderline':
        srm_concordant.append(None)
    elif (z > 0 and jnd_dir[i] == 'HYPER') or (z < 0 and jnd_dir[i] == 'HYPO'):
        srm_concordant.append(True)
    else:
        srm_concordant.append(False)

n_concordant = sum(1 for c in srm_concordant if c is True)
n_discordant = sum(1 for c in srm_concordant if c is False)

# Pair has LOCO-vulnerable color(s)
pair_has_loco_vuln = [False, True, True, False, True, False, False, False]

# LOCO per-color vulnerability
loco_colors = ['orange', 'yellow', 'purple', 'cyan']
loco_p = [0.0018, 0.0059, 0.020, 0.0053]
loco_hypo_pairs = [['O-Y'], ['O-Y', 'Y-G', 'Y-P'], ['Y-P'], []]

# ── Colors ──
COLOR_MAP = {
    'red': '#E63946', 'orange': '#F4A261', 'yellow': '#E9C46A',
    'green': '#2A9D8F', 'cyan': '#00B4D8', 'blue': '#264653',
    'purple': '#7B2D8E', 'magenta': '#D63384'
}
HYPO_COLOR = '#E74C3C'
HYPER_COLOR = '#2ECC71'
CONCORDANT_COLOR = '#2ECC71'
DISCORDANT_COLOR = '#E74C3C'

# ═══════════════════════════════════════════════════
fig = plt.figure(figsize=(16, 12))
fig.suptitle(f'Phase 3: Neural-Behavioral Cross-Modal Concordance\n[PRELIMINARY: CVD N=1, HC N={n_hc}]',
             fontsize=14, fontweight='bold', y=0.98)

# ── (A) SRM z vs JND ratio scatter ──
ax1 = fig.add_subplot(2, 2, 1)

for i in range(len(pairs_short)):
    if np.isnan(srm_z[i]):
        continue
    conc = srm_concordant[i]
    if conc is None:
        color = '#F39C12'
        marker = 'D'
        size = 90
    elif conc:
        color = CONCORDANT_COLOR
        marker = 'o'
        size = 100
    else:
        color = DISCORDANT_COLOR
        marker = 's'
        size = 120

    ax1.scatter(srm_z[i], jnd_ratio[i], c=color, s=size, marker=marker,
                zorder=5, edgecolors='black', linewidths=0.8)
    offset_x = 10 if srm_z[i] < 10 else -50
    ax1.annotate(pairs_short[i], (srm_z[i], jnd_ratio[i]),
                 textcoords="offset points", xytext=(offset_x, 8),
                 fontsize=9, fontweight='bold')

ax1.axhline(y=1.0, color='gray', linewidth=1, linestyle='--', alpha=0.6)
ax1.axvline(x=0, color='gray', linewidth=1, linestyle='--', alpha=0.6)

# Quadrant shading
ax1.fill_between([0, 15], 1.0, 5.0, alpha=0.06, color=DISCORDANT_COLOR)
ax1.fill_between([-2, 0], 0, 1.0, alpha=0.06, color=DISCORDANT_COLOR)
ax1.fill_between([0, 15], 0, 1.0, alpha=0.06, color=CONCORDANT_COLOR)
ax1.fill_between([-2, 0], 1.0, 5.0, alpha=0.06, color=CONCORDANT_COLOR)

ax1.text(7, max(jnd_ratio)*0.95, 'DISCORDANT\n(over-sep + HYPO)', fontsize=8, ha='center',
         color=DISCORDANT_COLOR, fontweight='bold', alpha=0.8)
ax1.text(7, 0.15, 'CONCORDANT\n(over-sep + HYPER)', fontsize=8, ha='center',
         color=CONCORDANT_COLOR, fontweight='bold', alpha=0.8)
ax1.text(-1.2, max(jnd_ratio)*0.95, 'CONCORDANT\n(compressed + HYPO)', fontsize=8, ha='center',
         color=CONCORDANT_COLOR, fontweight='bold', alpha=0.8)
ax1.text(-1.2, 0.15, 'DISCORDANT\n(compressed + HYPER)', fontsize=8, ha='center',
         color=DISCORDANT_COLOR, fontweight='bold', alpha=0.8)

n_eval = n_concordant + n_discordant
c_patch = mpatches.Patch(color=CONCORDANT_COLOR, label=f'Concordant ({n_concordant}/{n_eval})')
d_patch = mpatches.Patch(color=DISCORDANT_COLOR, label=f'Discordant ({n_discordant}/{n_eval})')
b_patch = mpatches.Patch(color='#F39C12', label='Borderline (excluded)')
ax1.legend(handles=[c_patch, d_patch, b_patch], fontsize=8, loc='upper left', framealpha=0.9)

ax1.set_xlabel('SRM z-score (sub-08, best ROI)', fontsize=10)
ax1.set_ylabel(f'JND Ratio (CVD / HC Group Mean, N={n_hc})', fontsize=10)
ax1.set_title('(A) SRM z vs JND: Global-Local Dissociation', fontweight='bold', fontsize=11)
ax1.set_xlim(-2, 15)
ax1.set_ylim(0, max(jnd_ratio) * 1.15)

# ── (B) LOCO vulnerable colors → JND HYPO ──
ax2 = fig.add_subplot(2, 2, 2)

y_loco = np.arange(len(loco_colors))
neg_log_p = [-np.log10(p) for p in loco_p]
bar_colors = [COLOR_MAP[c] for c in loco_colors]

bars = ax2.barh(y_loco, neg_log_p, height=0.6, color=bar_colors,
                edgecolor='black', linewidth=0.8, alpha=0.85)
ax2.axvline(x=-np.log10(0.05), color='red', linewidth=1, linestyle='--',
            alpha=0.7, label='p=0.05')

pair_map = {'O-Y': 'orange-yellow', 'Y-G': 'yellow-green',
            'Y-P': 'yellow-purple', 'B-P': 'blue-purple'}
n_loco_hypo = 0
n_loco_with_pairs = 0

for i, c in enumerate(loco_colors):
    hypo = loco_hypo_pairs[i]
    if hypo:
        n_loco_with_pairs += 1
        valid_hypo = [h for h in hypo
                      if hc_metrics.get(pair_map.get(h, ''), {}).get('direction_hc_group') == 'HYPO']
        if valid_hypo:
            n_loco_hypo += 1
            label = ', '.join(valid_hypo)
            ax2.text(neg_log_p[i] + 0.08, i, f'  JND HYPO: {label}',
                     va='center', fontsize=9, fontweight='bold', color=HYPO_COLOR)
        else:
            not_hypo = [h for h in hypo]
            label = ', '.join(not_hypo)
            ax2.text(neg_log_p[i] + 0.08, i, f'  {label} (now borderline)',
                     va='center', fontsize=9, style='italic', color='#F39C12')
    else:
        ax2.text(neg_log_p[i] + 0.08, i, '  (no HYPO pair)',
                 va='center', fontsize=9, style='italic', color='gray')

ax2.set_yticks(y_loco)
ax2.set_yticklabels([c.capitalize() for c in loco_colors], fontsize=10, fontweight='bold')
ax2.set_xlabel('-log10(p) Crawford-Howell', fontsize=10)
ax2.set_title(f'(B) LOCO Vulnerability -> JND HYPO ({n_loco_hypo}/{n_loco_with_pairs})',
              fontweight='bold', fontsize=11)
ax2.legend(fontsize=8)
ax2.set_xlim(0, 4.5)

# ── (C) 3-way heatmap ──
ax3 = fig.add_subplot(2, 1, 2)

srm_dir_val = []
for z in srm_z:
    if np.isnan(z):
        srm_dir_val.append(0)
    elif z > 0:
        srm_dir_val.append(1)
    else:
        srm_dir_val.append(-1)

loco_val = [1 if v else -1 for v in pair_has_loco_vuln]
jnd_val = [1 if d == 'HYPO' else (-1 if d == 'HYPER' else 0) for d in jnd_dir]

data = np.array([srm_dir_val, loco_val, jnd_val]).T  # (8, 3)

cmap = ListedColormap([HYPER_COLOR, '#CCCCCC', HYPO_COLOR])
im = ax3.imshow(data, aspect='auto', cmap=cmap, vmin=-1, vmax=1)

ax3.set_xticks([0, 1, 2])
ax3.set_xticklabels(['SRM z direction\n(red=over-sep, green=compressed)',
                      'LOCO vuln. color\n(red=contains, green=none)',
                      'JND direction\n(red=HYPO, green=HYPER)'],
                     fontsize=9)
ax3.set_yticks(range(len(pairs_short)))
ax3.set_yticklabels(pairs_short, fontsize=10, fontweight='bold')

# Cell text
labels_map = {
    0: {1: 'Over-sep', -1: 'Compr.', 0: 'N/A'},
    1: {1: 'Vuln.', -1: 'Intact'},
    2: {1: 'HYPO', -1: 'HYPER', 0: 'Borderline'}
}
for i in range(len(pairs_short)):
    for j in range(3):
        val = int(data[i, j])
        txt = labels_map[j][val]
        text_color = 'white' if val != 0 else 'black'
        ax3.text(j, i, txt, ha='center', va='center', fontsize=9,
                 fontweight='bold', color=text_color)

# Concordance annotations
for i in range(len(pairs_short)):
    srm_v = srm_dir_val[i]
    jnd_v = jnd_val[i]
    loco_v = loco_val[i]

    if srm_v == 0 or jnd_v == 0:
        srm_match = '--'
        srm_color = 'gray'
    elif (srm_v == 1 and jnd_v == -1) or (srm_v == -1 and jnd_v == 1):
        srm_match = 'SRM-JND: O'
        srm_color = CONCORDANT_COLOR
    else:
        srm_match = 'SRM-JND: X'
        srm_color = DISCORDANT_COLOR

    if jnd_v == 0:
        loco_match = 'LOCO-JND: --'
        loco_color = 'gray'
    elif jnd_v == 1:
        if loco_v == 1:
            loco_match = 'LOCO-JND: O'
            loco_color = CONCORDANT_COLOR
        else:
            loco_match = 'LOCO-JND: X'
            loco_color = DISCORDANT_COLOR
    else:
        if loco_v == -1:
            loco_match = 'LOCO-JND: O'
            loco_color = CONCORDANT_COLOR
        else:
            loco_match = 'LOCO-JND: ?'
            loco_color = '#F39C12'

    ax3.text(3.15, i - 0.15, srm_match, fontsize=8, fontweight='bold',
             color=srm_color, va='center')
    ax3.text(3.15, i + 0.15, loco_match, fontsize=8, fontweight='bold',
             color=loco_color, va='center')

ax3.set_xlim(-0.5, 4.5)
ax3.set_title(f'(C) 3-Way Concordance: SRM z / LOCO Vulnerability / JND Direction (HC N={n_hc})',
              fontweight='bold', fontsize=11, pad=15)

legend_elements = [
    mpatches.Patch(facecolor=HYPO_COLOR, edgecolor='black', label='Over-sep / Vuln / HYPO'),
    mpatches.Patch(facecolor=HYPER_COLOR, edgecolor='black', label='Compressed / Intact / HYPER'),
    mpatches.Patch(facecolor='#CCCCCC', edgecolor='black', label='N/A / Borderline'),
]
ax3.legend(handles=legend_elements, loc='lower right', fontsize=8,
           bbox_to_anchor=(0.85, -0.15), ncol=3)

plt.tight_layout(rect=[0, 0.02, 1, 0.95])
out_path = FIG_DIR / 'concordance_analysis.png'
plt.savefig(out_path, dpi=200, bbox_inches='tight')
print(f"Saved: {out_path}")
plt.close()
