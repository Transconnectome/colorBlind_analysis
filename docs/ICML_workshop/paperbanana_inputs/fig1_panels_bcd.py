#!/usr/bin/env python3
"""
ICML Figure 1, panels (b)-(d): LOCO vulnerability profiles with model fits.
Single-column figure: 3.25 x 1.8 inches, 300 DPI.

Usage:
    conda activate srm
    python fig1_panels_bcd.py
    # -> fig1_panels_bcd.pdf
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

# ── Data from phase_a_v2 results (ICML draft values) ──

# Observed CVD vulnerability profiles (vuln_cvd from manifest JSONs)
vuln_obs = {
    'sub-08': np.array([0.573, -0.637, -0.733, -0.306, 0.250, -0.251, -0.759, -0.334]),
    'sub-09': np.array([0.023,  0.596,  0.322,  0.147, -0.451, -0.256, -0.090, -0.575]),
    'sub-10': np.array([-0.006, 0.160,  0.069,  0.293,  0.508,  0.183, -0.028, -0.085]),
}

# Best-fit simulated vulnerability (vuln_sim from phase_a_v2 JSONs)
vuln_sim = {
    'sub-08': np.array([0.276, 0.100, 0.089, 0.141, 0.110, 0.214, -0.062, 0.119]),  # R+C
    'sub-09': np.array([0.278, 0.119, 0.134, 0.078, 0.058, 0.066, -0.080, -0.101]),  # Machado
    'sub-10': np.array([0.369, 0.137, 0.094, 0.130, 0.058, 0.055, -0.053,  0.110]),  # baseline~
}

# Colors
color_rgb = ['#E74C3C', '#E67E22', '#F1C40F', '#2ECC71', '#1ABC9C', '#3498DB', '#9B59B6', '#E91E9B']

# Panel configs
panels = [
    {'title': 'Sub-08 (deutan)', 'obs': vuln_obs['sub-08'], 'sim': vuln_sim['sub-08'],
     'line_color': '#E67E22', 'annot': r'R+C: $\rho$=.857'+'\np=.005**', 'model': 'R+C'},
    {'title': 'Sub-09 (protan)', 'obs': vuln_obs['sub-09'], 'sim': vuln_sim['sub-09'],
     'line_color': '#E74C3C', 'annot': r'Machado: $\rho$=.762'+'\np=.018*', 'model': 'Machado'},
    {'title': 'Sub-10 (control)', 'obs': vuln_obs['sub-10'], 'sim': vuln_sim['sub-10'],
     'line_color': '#7F8C8D', 'annot': 'n.s.\np=.559', 'model': None},
]

# ── Plot ──

fig, axes = plt.subplots(1, 3, figsize=(3.25, 1.8), dpi=300, sharey=True)
fig.subplots_adjust(wspace=0.08, left=0.14, right=0.97, bottom=0.18, top=0.80)

x = np.arange(8)
bar_w = 0.6

for i, (ax, p) in enumerate(zip(axes, panels)):
    # Gray bars: observed
    ax.bar(x, p['obs'], width=bar_w, color='#BDC3C7', edgecolor='#95A5A6',
           linewidth=0.4, zorder=2)

    # Colored line: model fit
    if p['model']:
        ax.plot(x, p['sim'], color=p['line_color'], linewidth=1.2,
                marker='o', markersize=2.5, zorder=3)
    else:
        ax.axhline(0, color='#95A5A6', linewidth=0.8, linestyle='--', zorder=3)

    # Annotation — top-right, inside plot area
    ax.text(0.95, 0.95, p['annot'], transform=ax.transAxes,
            fontsize=4.5, ha='right', va='top', linespacing=1.3,
            fontweight='bold' if p['model'] else 'normal',
            color=p['line_color'] if p['model'] else '#555555')

    # Panel title
    ax.set_title(p['title'], fontsize=5.5, fontweight='bold', pad=3)

    # Panel label — above title
    label = chr(ord('b') + i)
    ax.text(-0.02, 1.18, f'({label})', transform=ax.transAxes,
            fontsize=7, fontweight='bold', va='bottom')

    # X-axis: color squares below axis
    ax.set_xticks(x)
    ax.set_xticklabels([])
    for j, c in enumerate(color_rgb):
        ax.add_patch(Rectangle((j - 0.25, -0.14), 0.5, 0.06,
                               facecolor=c, edgecolor='none', clip_on=False,
                               transform=ax.get_xaxis_transform()))

    # Styling
    ax.set_xlim(-0.5, 7.5)
    ax.axhline(0, color='black', linewidth=0.3, zorder=1)
    ax.tick_params(axis='both', labelsize=5, length=2, width=0.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    for spine in ax.spines.values():
        spine.set_linewidth(0.4)

# Y-axis label
axes[0].set_ylabel('LOCO vuln.', fontsize=5.5, labelpad=2)
axes[0].set_ylim(-0.9, 0.7)

# Shared legend at bottom
legend_elements = [
    Rectangle((0, 0), 1, 1, facecolor='#BDC3C7', edgecolor='#95A5A6', linewidth=0.4, label='Observed CVD'),
    Line2D([0], [0], color='#E67E22', linewidth=1.2, marker='o', markersize=2.5, label='Model fit'),
]
fig.legend(handles=legend_elements, loc='lower center', ncol=2, fontsize=5,
           frameon=False, bbox_to_anchor=(0.55, -0.01))

# Save
fig.savefig('fig1_panels_bcd.pdf', bbox_inches='tight', facecolor='white')
fig.savefig('fig1_panels_bcd.png', bbox_inches='tight', facecolor='white', dpi=300)
print("Saved: fig1_panels_bcd.pdf / .png")
