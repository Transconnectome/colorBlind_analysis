"""
Behavioral Pilot Data Visualization — Phase 3
Generates 4-panel figure:
  (A) JND comparison bar chart (HC vs CVD)
  (B) RSVP per-color accuracy
  (C) SRM z vs JND ratio concordance
  (D) LOCO vulnerability vs JND direction alignment
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

# ── Paths ──
SCRIPT_DIR = Path(__file__).parent
FIG_DIR = SCRIPT_DIR.parent / "figures"
FIG_DIR.mkdir(exist_ok=True)

# ── Color palette matching fMRI stimuli ──
COLOR_MAP = {
    'red': '#E63946', 'orange': '#F4A261', 'yellow': '#E9C46A',
    'green': '#2A9D8F', 'cyan': '#00B4D8', 'blue': '#264653',
    'purple': '#7B2D8E', 'magenta': '#D63384'
}

# ── Data ──
pairs = ['red-\norange', 'orange-\nyellow', 'yellow-\ngreen', 'green-\nblue',
         'yellow-\npurple', 'blue-\npurple', 'cyan-\nmagenta', 'red-\ncyan']
pairs_short = ['R-O', 'O-Y', 'Y-G', 'G-B', 'Y-P', 'B-P', 'C-M', 'R-C']

hc_jnd = [0.235, 0.443, 0.103, 0.103, 0.025, 0.165, 0.048, 0.048]
cvd_jnd = [0.062, 0.840, 0.278, 0.077, 0.062, 0.120, 0.040, 0.015]
jnd_dir = ['HYPER', 'HYPO', 'HYPO', 'HYPER', 'HYPO', 'HYPER', 'HYPER', 'HYPER']

# SRM z (best ROI, sub-08)
srm_z = [1.66, 3.29, 4.14, -0.89, 13.87, 6.15, np.nan, np.nan]
srm_concordant = [True, False, False, False, False, True, None, None]

# RSVP per-color
colors_order = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
cvd_acc = [1.0, 0.875, 0.625, 0.75, 1.0, 1.0, 0.5, 0.75]
loco_vuln = [False, True, True, False, True, False, True, False]  # p<0.05 in any ROI

# ── Figure ──
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Phase 3: Behavioral Pilot — sub-08 (Deutan CVD) vs HC\n[PRELIMINARY: N=1 per group]',
             fontsize=13, fontweight='bold', y=0.98)

# ── Panel A: JND Comparison ──
ax = axes[0, 0]
x = np.arange(len(pairs))
w = 0.35
bars_hc = ax.bar(x - w/2, hc_jnd, w, label='HC', color='#4A90D9', alpha=0.8, edgecolor='black', linewidth=0.5)
bars_cvd = ax.bar(x + w/2, cvd_jnd, w, label='CVD (sub-08)', color='#E74C3C', alpha=0.8, edgecolor='black', linewidth=0.5)

# Mark HYPO/HYPER
for i, d in enumerate(jnd_dir):
    y_max = max(hc_jnd[i], cvd_jnd[i])
    color = '#E74C3C' if d == 'HYPO' else '#2ECC71'
    ax.text(x[i], y_max + 0.02, d, ha='center', va='bottom', fontsize=7,
            fontweight='bold', color=color)

ax.set_ylabel('JND (interpolation step)')
ax.set_xticks(x)
ax.set_xticklabels(pairs_short, fontsize=8)
ax.legend(fontsize=8, loc='upper left')
ax.set_title('(A) JND: HC vs CVD', fontweight='bold', fontsize=10)
ax.set_ylim(0, 1.0)
ax.axhline(y=0, color='black', linewidth=0.5)

# ── Panel B: RSVP Per-Color Accuracy ──
ax = axes[0, 1]
bar_colors = [COLOR_MAP[c] for c in colors_order]
bars = ax.bar(colors_order, cvd_acc, color=bar_colors, edgecolor='black', linewidth=0.5, alpha=0.85)

# Mark LOCO-vulnerable colors
for i, (v, acc) in enumerate(zip(loco_vuln, cvd_acc)):
    if v:
        ax.bar(colors_order[i], acc, color=bar_colors[i], edgecolor='red',
               linewidth=2.5, alpha=0.85, linestyle='--')
        ax.text(i, acc + 0.02, 'LOCO\nvuln', ha='center', va='bottom', fontsize=6,
                color='red', fontweight='bold')

ax.axhline(y=1.0, color='#4A90D9', linewidth=1.5, linestyle='--', label='HC (100%)', alpha=0.7)
ax.set_ylabel('CVD Accuracy')
ax.set_title('(B) RSVP 8AFC: CVD Per-Color Accuracy', fontweight='bold', fontsize=10)
ax.set_ylim(0, 1.25)
ax.legend(fontsize=8)
ax.set_xticklabels(colors_order, fontsize=8)

# ── Panel C: SRM z vs JND Ratio ──
ax = axes[1, 0]
jnd_ratio = [c / h if h > 0 else 0 for c, h in zip(cvd_jnd, hc_jnd)]

for i in range(len(pairs_short)):
    if np.isnan(srm_z[i]):
        continue
    color = '#2ECC71' if srm_concordant[i] else '#E74C3C'
    marker = 'o' if srm_concordant[i] else 'x'
    ax.scatter(srm_z[i], jnd_ratio[i], c=color, s=80, marker=marker, zorder=5,
               edgecolors='black', linewidths=0.5)
    ax.annotate(pairs_short[i], (srm_z[i], jnd_ratio[i]),
                textcoords="offset points", xytext=(8, 5), fontsize=7)

ax.axhline(y=1.0, color='gray', linewidth=0.8, linestyle='--', alpha=0.7)
ax.axvline(x=0, color='gray', linewidth=0.8, linestyle='--', alpha=0.7)

# Quadrant labels
ax.text(10, 0.3, 'CONCORDANT\n(over-sep + HYPER)', fontsize=7, color='#2ECC71',
        ha='center', style='italic', alpha=0.7)
ax.text(10, 2.5, 'DISCORDANT\n(over-sep + HYPO)', fontsize=7, color='#E74C3C',
        ha='center', style='italic', alpha=0.7)
ax.text(-0.5, 0.3, 'CONCORDANT\n(compressed + HYPO)', fontsize=7, color='#2ECC71',
        ha='center', style='italic', alpha=0.7)

concordant_patch = mpatches.Patch(color='#2ECC71', label='Concordant (2/6)')
discordant_patch = mpatches.Patch(color='#E74C3C', label='Discordant (4/6)')
ax.legend(handles=[concordant_patch, discordant_patch], fontsize=7, loc='upper left')

ax.set_xlabel('SRM z-score (sub-08, best ROI)')
ax.set_ylabel('JND Ratio (CVD / HC)')
ax.set_title('(C) SRM z vs JND Ratio: 5/7 Discordance', fontweight='bold', fontsize=10)

# ── Panel D: LOCO Vulnerability → JND Alignment ──
ax = axes[1, 1]

# LOCO vulnerable colors and their JND pair involvement
loco_data = {
    'orange': {'p_V1': 0.0018, 'p_V2': 0.023, 'hypo_pairs': ['O-Y']},
    'yellow': {'p_V1': 0.0059, 'p_V2': 0.0077, 'hypo_pairs': ['O-Y', 'Y-G', 'Y-P']},
    'purple': {'p_V1': 0.020, 'p_V2': None, 'hypo_pairs': ['Y-P']},
    'cyan': {'p_V2': 0.0053, 'p_V1': None, 'hypo_pairs': []},
}

y_pos = np.arange(len(loco_data))
colors_loco = list(loco_data.keys())
p_vals = []
for c in colors_loco:
    ps = [v for v in [loco_data[c].get('p_V1'), loco_data[c].get('p_V2')] if v is not None]
    p_vals.append(min(ps))

# Plot -log10(p)
neg_log_p = [-np.log10(p) for p in p_vals]
bar_colors_loco = [COLOR_MAP[c] for c in colors_loco]
bars = ax.barh(y_pos, neg_log_p, color=bar_colors_loco, edgecolor='black', linewidth=0.5, alpha=0.85)

# Add pair annotations
for i, c in enumerate(colors_loco):
    hypo = loco_data[c]['hypo_pairs']
    label = ', '.join(hypo) if hypo else '(no HYPO pair)'
    style = 'normal' if hypo else 'italic'
    color = 'black' if hypo else 'gray'
    ax.text(neg_log_p[i] + 0.05, i, f' JND HYPO: {label}', va='center', fontsize=8,
            style=style, color=color)

ax.axvline(x=-np.log10(0.05), color='red', linewidth=1, linestyle='--', alpha=0.7,
           label='p=0.05')
ax.set_yticks(y_pos)
ax.set_yticklabels([c.capitalize() for c in colors_loco], fontsize=9)
ax.set_xlabel('-log10(p) Crawford-Howell')
ax.set_title('(D) LOCO Vulnerability → JND HYPO (3/3 = 100%)', fontweight='bold', fontsize=10)
ax.legend(fontsize=8)
ax.set_xlim(0, 4.0)

plt.tight_layout(rect=[0, 0, 1, 0.95])
out_path = FIG_DIR / 'behavioral_pilot_summary.png'
plt.savefig(out_path, dpi=200, bbox_inches='tight')
print(f"Saved: {out_path}")
plt.close()
