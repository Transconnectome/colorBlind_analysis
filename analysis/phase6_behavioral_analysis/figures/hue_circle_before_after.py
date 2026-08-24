"""
Two-panel figure: CVD hue-circle shift (left) + JND ratio vs HC (right).

Left:  original hue positions (ghost) vs CVD-perceived (h + δθ).
Right: JND ratio (sub-08 / HC-mean) with per-pair δθ values and Δarc.

δθ(h) = 38·cos(h−90°) + (−14)·cos(h−150°)  [sub-08, LOCO-canonical]
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── Sub-08 LOCO-canonical parameters ──────────────────────────────────────────
bs, bc, tc = 38.0, -14.0, 150.0

hue_labels_circ = ['c1\nred', 'c2\norange', 'c3\nyellow', 'c4\ngreen',
                   'c5\ncyan',  'c6\nblue',   'c7\npurple', 'c8\nmagenta']
hue_angles_norm = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
hue_colors      = ['#E05050', '#E08020', '#C8C000', '#30B060',
                   '#00B8C8', '#4060E0', '#8040C8', '#D050A0']


def delta_theta(h_deg):
    h = np.deg2rad(h_deg)
    return bs * np.cos(h - np.pi/2) + bc * np.cos(h - np.deg2rad(tc))

dtheta         = np.array([delta_theta(h) for h in hue_angles_norm])
hue_angles_cvd = hue_angles_norm + dtheta

# Circular arc distance helper (returns value in [0, 180])
def arc_dist(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)


# ── JND data ──────────────────────────────────────────────────────────────────
# (pair_name, i, j, jnd_ratio, jnd_cat)
jnd_pairs = [
    ('red–orange',    0, 1, 0.50, 'HYPER'),
    ('orange–yellow', 1, 2, 3.02, 'HYPO'),
    ('yellow–green',  2, 3, 3.10, 'HYPO'),
    ('yellow–purple', 2, 6, 2.87, 'HYPO'),
    ('cyan–magenta',  4, 7, 0.95, 'borderline'),
    ('blue–purple',   5, 6, 0.73, 'HYPER'),
]
pair_names = [p[0] for p in jnd_pairs]
pair_i     = [p[1] for p in jnd_pairs]
pair_j     = [p[2] for p in jnd_pairs]
jnd_ratios = [p[3] for p in jnd_pairs]
jnd_cats   = [p[4] for p in jnd_pairs]

# Compute per-pair δθ values and Δarc
hue_short = ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8']

def fmt_dtheta(idx):
    v = dtheta[idx]
    return f'{hue_short[idx]} {v:+.0f}°'

def fmt_darc(i, j):
    d_norm = arc_dist(hue_angles_norm[i], hue_angles_norm[j])
    d_cvd  = arc_dist(hue_angles_cvd[i],  hue_angles_cvd[j])
    delta  = d_cvd - d_norm
    if abs(delta) < 2:
        arrow = '→'
    elif delta > 0:
        arrow = '↑'
    else:
        arrow = '↓'
    return f'Δarc {delta:+.0f}° {arrow}', d_norm, d_cvd

# Build multi-line x-tick labels
xtick_labels = []
darc_info    = []
for name, i, j, _, _ in jnd_pairs:
    darc_str, d_norm, d_cvd = fmt_darc(i, j)
    label = f'{name}\n{fmt_dtheta(i)}  {fmt_dtheta(j)}\n{darc_str}'
    xtick_labels.append(label)
    darc_info.append((d_norm, d_cvd))

# LOCO significance per hue — unified ★ (LOCO-sig at V1 and/or V2)
loco_sig_set = {1, 2, 6}   # c2 orange, c3 yellow, c7 purple

def bar_color(cat):
    return {'HYPO': '#E06060', 'HYPER': '#6090E0', 'borderline': '#888888'}[cat]


# ═══════════════════════════════════════════════════════════════════════════════
# Figure layout — taller right-panel bottom for 3-line x labels
# ═══════════════════════════════════════════════════════════════════════════════
fig = plt.figure(figsize=(15, 7.2))
fig.patch.set_facecolor('white')

ax_circ = fig.add_axes([0.01, 0.07, 0.46, 0.88])
ax_jnd  = fig.add_axes([0.53, 0.22, 0.45, 0.68])

for ax in [ax_circ, ax_jnd]:
    ax.set_facecolor('white')


# ── LEFT: hue circle ──────────────────────────────────────────────────────────
ax = ax_circ
ax.set_aspect('equal')
ax.set_xlim(-1.72, 1.72)
ax.set_ylim(-1.72, 1.72)
ax.axis('off')

# Guide circle
th = np.linspace(0, 2*np.pi, 360)
ax.plot(np.cos(th), np.sin(th), color='#BBBBBB', lw=0.9, zorder=1)

# Tick marks
for angle in range(0, 360, 45):
    a = np.deg2rad(angle)
    ax.plot([0.93*np.cos(a), 1.02*np.cos(a)],
            [0.93*np.sin(a), 1.02*np.sin(a)],
            color='#AAAAAA', lw=0.7)

r_dot   = 1.15
r_label = 1.43

for i, (h_n, h_c, color) in enumerate(zip(hue_angles_norm, hue_angles_cvd, hue_colors)):
    a_n = np.deg2rad(h_n)
    a_c = np.deg2rad(h_c)
    x_n, y_n = r_dot * np.cos(a_n), r_dot * np.sin(a_n)
    x_c, y_c = r_dot * np.cos(a_c), r_dot * np.sin(a_c)

    # Ghost dot (normal position)
    ax.plot(x_n, y_n, 'o', color=color, ms=9, alpha=0.22, zorder=4,
            markeredgecolor='none')

    # Arrow normal → CVD
    if abs(dtheta[i]) > 3:
        ax.annotate('', xy=(x_c, y_c), xytext=(x_n, y_n),
                    arrowprops=dict(arrowstyle='->', color='#333333',
                                   lw=1.1, mutation_scale=9),
                    zorder=5)

    # Filled CVD dot
    ax.plot(x_c, y_c, 'o', color=color, ms=12, zorder=6,
            markeredgecolor='#333333', markeredgewidth=0.5)

    # δθ annotation
    if abs(dtheta[i]) > 5:
        a_mid = np.deg2rad((h_n + h_c) / 2)
        mx, my = 0.83 * np.cos(a_mid), 0.83 * np.sin(a_mid)
        sign = '+' if dtheta[i] >= 0 else ''
        ax.text(mx, my, f'{sign}{dtheta[i]:.0f}°', color='#444444',
                fontsize=6.5, ha='center', va='center')

    # Hue label
    lx = r_label * np.cos(a_c)
    ly = r_label * np.sin(a_c)
    ha = 'center'
    if lx > 0.35:  ha = 'left'
    elif lx < -0.35:  ha = 'right'
    ax.text(lx, ly, hue_labels_circ[i], color=color, fontsize=8,
            ha=ha, va='center', fontweight='bold', fontfamily='monospace')

# Normal-position tiny dots on guide circle
for i, h_n in enumerate(hue_angles_norm):
    a = np.deg2rad(h_n)
    ax.plot(0.99*np.cos(a), 0.99*np.sin(a), 'o',
            color=hue_colors[i], ms=4.5, alpha=0.22, zorder=3)

# Title
ax.text(0, 1.65, 'Hue-circle shift  (sub-08 deutan)',
        color='black', fontsize=11, ha='center', va='bottom', fontweight='bold')

# Legend
legend_els = [
    mpatches.Patch(facecolor='#AAAAAA', alpha=0.5, label='Normal position (ghost)'),
    mpatches.Patch(facecolor='#555555', alpha=0.8, label='CVD position (filled)'),
    plt.Line2D([0], [0], color='#333333', lw=1.1, marker='>',
               label='Shift direction (δθ)'),
]
ax.legend(handles=legend_els, loc='lower center', fontsize=7,
          facecolor='white', edgecolor='#AAAAAA', labelcolor='black',
          bbox_to_anchor=(0.5, 0.01), ncol=3)


# ── RIGHT: JND bar chart ──────────────────────────────────────────────────────
ax = ax_jnd
n = len(jnd_pairs)
x = np.arange(n)
w = 0.55

# HC reference band & line
ax.axhspan(0.90, 1.10, color='#EEEEEE', alpha=0.8, zorder=0)
ax.axhline(1.0, color='#888888', lw=1.2, ls='--', zorder=1)
ax.text(n - 0.5, 1.02, 'HC = 1.0×', color='#888888', fontsize=7, va='bottom')

for k, (ratio, cat) in enumerate(zip(jnd_ratios, jnd_cats)):
    col = bar_color(cat)
    ax.bar(k, ratio, width=w, color=col, alpha=0.75, zorder=2,
           edgecolor='white', linewidth=0.5)

    # Ratio value label
    y_off = 0.07
    ax.text(k, ratio + y_off, f'{ratio:.2f}×', color='#111111',
            ha='center', va='bottom', fontsize=9.5, fontweight='bold')

    # HYPO/HYPER tag inside bar bottom
    tag = {'HYPO': 'HYPO', 'HYPER': 'HYPER', 'borderline': '~'}[cat]
    ax.text(k, 0.05, tag, color=bar_color(cat), ha='center', va='bottom',
            fontsize=8, fontweight='bold', zorder=3)

# Multi-line x-tick labels (pair name / δθ values / Δarc)
ax.set_xticks(x)
ax.set_xticklabels(xtick_labels, rotation=0, ha='center',
                   fontsize=7.5, color='#222222', linespacing=1.4)

# Axes styling
ax.set_ylim(0, 4.3)
ax.set_ylabel('JND ratio  (sub-08 / HC mean)', color='#222222', fontsize=10)
ax.tick_params(axis='x', colors='#222222', length=0)
ax.tick_params(axis='y', colors='#444444')
ax.spines['bottom'].set_color('#AAAAAA')
ax.spines['left'].set_color('#AAAAAA')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Y-axis grid
for ytick in [1, 2, 3, 4]:
    ax.axhline(ytick, color='#DDDDDD', lw=0.5, zorder=0)

ax.set_title('JND threshold ratio vs HC  (sub-08, no filter)',
             color='black', fontsize=10.5, pad=10, fontweight='bold')

# Legend
legend_els = [
    mpatches.Patch(facecolor='#E06060', alpha=0.75, label='HYPO  (ratio > 1, harder)'),
    mpatches.Patch(facecolor='#6090E0', alpha=0.75, label='HYPER  (ratio < 1, easier)'),
    mpatches.Patch(facecolor='#888888', alpha=0.75, label='Borderline'),
]
ax.legend(handles=legend_els, fontsize=7.5, facecolor='white',
          edgecolor='#AAAAAA', labelcolor='#222222', loc='upper right')


# ── Save ──────────────────────────────────────────────────────────────────────
outpath = ('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/'
           'colorBlind_analysis/analysis/phase6_behavioral_analysis/'
           'figures/hue_circle_before_after.png')
plt.savefig(outpath, dpi=150, bbox_inches='tight', facecolor='white')
print(f'Saved: {outpath}')
plt.close()
