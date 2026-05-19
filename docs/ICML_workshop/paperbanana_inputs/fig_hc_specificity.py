#!/usr/bin/env python3
"""
ICML Appendix: HC Specificity Calibration figure.
Full-width: 6.75 x 2.8 inches, 300 DPI.

Usage:
    conda activate srm
    python fig_hc_specificity.py
    # -> fig_hc_specificity.pdf
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Data from HC specificity test (Job 96600/96664) ──
subjects = ['Sub-01', 'Sub-02', 'Sub-03', 'Sub-04', 'Sub-05', 'Sub-06', 'Sub-07']

# p-values (from hc_specificity results)
p_machado  = [0.085, 0.042, 0.001, 0.065, 0.001, 0.001, 0.072]
p_rc       = [0.023, 0.005, 0.001, 0.018, 0.001, 0.001, 0.023]
p_2comp    = [0.023, 0.005, 0.001, 0.018, 0.001, 0.001, 0.023]

# FP counts (override with known values)
fp_machado, fp_rc, fp_2comp = 3, 5, 7

# ── Plot ──

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.75, 2.4), dpi=300,
                                gridspec_kw={'width_ratios': [1.8, 1]})
fig.subplots_adjust(wspace=0.30, left=0.08, right=0.92, bottom=0.16, top=0.88)

# --- Panel (a): Forest plot ---
y_pos = np.arange(len(subjects))

markers = [
    (p_machado, 'o', '#3498DB', 'Machado (1 DOF)'),
    (p_rc,      's', '#E67E22', 'R+C (2 DOF)'),
    (p_2comp,   '^', '#2ECC71', '2-Comp (2 DOF)'),
]

offsets = [-0.15, 0, 0.15]
for (pvals, marker, color, label), off in zip(markers, offsets):
    ax1.scatter(pvals, y_pos + off, marker=marker, c=color, s=30,
                edgecolors='black', linewidths=0.3, zorder=3, label=label)

# p = 0.05 line
ax1.axvline(0.05, color='#E74C3C', linewidth=1.0, linestyle='--', zorder=2)

# FP zone shading
ax1.axvspan(0, 0.05, alpha=0.08, color='#E74C3C', zorder=1)
ax1.text(0.025, len(subjects) - 0.3, 'FP zone', fontsize=6, color='#E74C3C',
         ha='center', style='italic')

ax1.set_xscale('log')
ax1.set_xlim(0.0005, 1.2)
ax1.set_xticks([0.001, 0.01, 0.05, 0.1, 0.5, 1.0])
ax1.set_xticklabels(['0.001', '0.01', '0.05', '0.1', '0.5', '1.0'], fontsize=7)
ax1.set_yticks(y_pos)
ax1.set_yticklabels(subjects, fontsize=7)
ax1.set_xlabel('p-value (log scale)', fontsize=8)
ax1.legend(fontsize=5, loc='upper right', framealpha=0.9, edgecolor='#CCCCCC',
           markerscale=0.7, handletextpad=0.3, borderpad=0.3, labelspacing=0.3)

ax1.text(-0.08, 1.06, '(a)', transform=ax1.transAxes, fontsize=9, fontweight='bold')
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# --- Panel (b): FP rate bar chart ---
models = ['Machado', 'R+C', '2-Comp']
fp_rates = [fp_machado / 7 * 100, fp_rc / 7 * 100, fp_2comp / 7 * 100]
colors = ['#3498DB', '#E67E22', '#2ECC71']

bars = ax2.bar(models, fp_rates, color=colors, edgecolor='black', linewidth=0.5, width=0.55)

# Fraction labels above bars
for bar, fp in zip(bars, [fp_machado, fp_rc, fp_2comp]):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 2,
             f'{fp}/7', ha='center', fontsize=7, fontweight='bold')

# Reference lines (labels in caption)
ax2.axhline(5, color='#CCCCCC', linewidth=0.7, linestyle='--')
ax2.axhline(100 / 7, color='#CCCCCC', linewidth=0.5, linestyle=':')

ax2.set_ylabel('False Positive Rate (%)', fontsize=8)
ax2.set_ylim(0, 115)
ax2.tick_params(labelsize=7)
ax2.text(-0.12, 1.06, '(b)', transform=ax2.transAxes, fontsize=9, fontweight='bold')
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

# Save
fig.savefig('fig_hc_specificity.pdf', bbox_inches='tight', facecolor='white')
fig.savefig('fig_hc_specificity.png', bbox_inches='tight', facecolor='white', dpi=300)
print("Saved: fig_hc_specificity.pdf / .png")
