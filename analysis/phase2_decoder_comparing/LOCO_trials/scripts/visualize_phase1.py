#!/usr/bin/env python3
"""
Phase 1 MDS Diagnostic — Comprehensive Visualization

Generates publication-quality summary figures:
  1. Dashboard: 4-panel summary (stress, circular order, Shepard R2, Mantel)
  2. Per-ROI 2D MDS: all 4 ROIs × 3 alignments with color wheel overlay
  3. Stress elbow plot: annotated with threshold
  4. Circular order polar plot: MDS angular positions vs true hue positions
  5. Procrustes cross-alignment heatmap

Usage:
    conda activate srm
    python scripts/visualize_phase1.py
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
from scipy.spatial.distance import squareform, pdist
from scipy.stats import spearmanr
from sklearn.manifold import MDS

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR.parent / 'results' / 'mds_diagnostic'
DATA_DIR = SCRIPT_DIR.parents[2] / 'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

# Load summary
with open(RESULTS_DIR / 'mds_summary.json') as f:
    summary = json.load(f)

# Constants
ROIS = ['V1', 'V2', 'V3', 'hV4']
ALIGNMENTS = ['raw', 'procrustes', 'srm']
ALIGN_COLORS = {'raw': '#e74c3c', 'procrustes': '#3498db', 'srm': '#2ecc71'}
ALIGN_LABELS = {'raw': 'Raw', 'procrustes': 'Procrustes', 'srm': 'SRM'}
HUE_ANGLES = np.array([i * 45 for i in range(8)])
ROI_DIRS = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}
HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]

COLOR_RGBS = [
    (0.85, 0.25, 0.30),  # red
    (0.90, 0.55, 0.20),  # orange
    (0.70, 0.55, 0.15),  # yellow
    (0.15, 0.70, 0.30),  # green
    (0.20, 0.72, 0.65),  # cyan
    (0.30, 0.55, 0.80),  # blue
    (0.40, 0.30, 0.75),  # purple
    (0.70, 0.30, 0.65),  # magenta
]
COLOR_NAMES = ['0 (Red)', '45 (Org)', '90 (Yel)', '135 (Grn)',
               '180 (Cyn)', '225 (Blu)', '270 (Pur)', '315 (Mag)']


def load_amplitudes(subject, roi, alignment):
    roi_dir = ROI_DIRS[roi]
    return np.load(DATA_DIR / f'sub-{subject}' / roi_dir / f'amplitudes_{alignment}.npy')


def compute_rdm(patterns):
    return squareform(pdist(patterns, metric='correlation'))


def normalized_stress(rdm, coords):
    dists_orig = squareform(rdm)
    dists_mds = pdist(coords, metric='euclidean')
    return np.sqrt(np.sum((dists_orig - dists_mds)**2) / np.sum(dists_orig**2))


# ============================================================================
# Figure 1: 4-Panel Dashboard
# ============================================================================
def plot_dashboard():
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))

    x_pos = np.arange(len(ROIS))
    width = 0.25

    # Panel A: 2D Stress
    ax = axes[0, 0]
    for i, align in enumerate(ALIGNMENTS):
        vals = [summary['stress_2d'].get(f'{roi}_{align}', np.nan) for roi in ROIS]
        bars = ax.bar(x_pos + i * width, vals, width, color=ALIGN_COLORS[align],
                      label=ALIGN_LABELS[align], edgecolor='white', linewidth=0.5)
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                    f'{v:.3f}', ha='center', va='bottom', fontsize=7, rotation=45)
    ax.axhline(0.1, color='gray', ls='--', lw=1, alpha=0.7)
    ax.text(3.8, 0.105, 'threshold=0.1', fontsize=8, color='gray', ha='right')
    ax.set_xticks(x_pos + width)
    ax.set_xticklabels(ROIS)
    ax.set_ylabel('Kruskal Normalized Stress')
    ax.set_title('A. 2D MDS Stress', fontweight='bold', fontsize=12)
    ax.legend(fontsize=8)
    ax.set_ylim(0, 0.35)

    # Panel B: Circular Order (Spearman rho)
    ax = axes[0, 1]
    for i, align in enumerate(ALIGNMENTS):
        vals = [summary['circular_order'].get(f'{roi}_{align}', {}).get('rho', np.nan)
                for roi in ROIS]
        pvals = [summary['circular_order'].get(f'{roi}_{align}', {}).get('p', 1.0)
                 for roi in ROIS]
        bars = ax.bar(x_pos + i * width, vals, width, color=ALIGN_COLORS[align],
                      label=ALIGN_LABELS[align], edgecolor='white', linewidth=0.5)
        # Mark significant
        for bar, v, p in zip(bars, vals, pvals):
            marker = '*' if p < 0.05 else ''
            ax.text(bar.get_x() + bar.get_width()/2,
                    max(v, 0) + 0.02 if v >= 0 else v - 0.08,
                    f'{v:.2f}{marker}', ha='center', va='bottom', fontsize=6.5, rotation=45)
    ax.axhline(0.8, color='gray', ls='--', lw=1, alpha=0.7)
    ax.axhline(-0.8, color='gray', ls='--', lw=1, alpha=0.7)
    ax.axhline(0, color='black', lw=0.5, alpha=0.3)
    ax.text(3.8, 0.83, 'threshold=|0.8|', fontsize=8, color='gray', ha='right')
    ax.set_xticks(x_pos + width)
    ax.set_xticklabels(ROIS)
    ax.set_ylabel('Spearman rho')
    ax.set_title('B. Circular Order Preservation', fontweight='bold', fontsize=12)
    ax.set_ylim(-1.0, 1.1)
    ax.legend(fontsize=8)

    # Panel C: Shepard R2
    ax = axes[1, 0]
    for i, align in enumerate(ALIGNMENTS):
        vals = [summary['shepard_r2'].get(f'{roi}_{align}', np.nan) for roi in ROIS]
        # Clip for display (negative R2 are extremely bad)
        vals_clipped = [max(v, -1.5) for v in vals]
        bars = ax.bar(x_pos + i * width, vals_clipped, width, color=ALIGN_COLORS[align],
                      label=ALIGN_LABELS[align], edgecolor='white', linewidth=0.5)
        for bar, v, vc in zip(bars, vals, vals_clipped):
            text = f'{v:.2f}' if v >= -1.5 else f'{v:.1f}'
            y_pos = max(vc, 0) + 0.02 if vc >= 0 else vc - 0.08
            ax.text(bar.get_x() + bar.get_width()/2, y_pos,
                    text, ha='center', va='bottom', fontsize=6.5, rotation=45)
    ax.axhline(0.8, color='gray', ls='--', lw=1, alpha=0.7)
    ax.axhline(0, color='black', lw=0.5, alpha=0.3)
    ax.text(3.8, 0.85, 'threshold=0.80', fontsize=8, color='gray', ha='right')
    ax.set_xticks(x_pos + width)
    ax.set_xticklabels(ROIS)
    ax.set_ylabel('R-squared')
    ax.set_title('C. Shepard Plot R-squared (MDS fit quality)', fontweight='bold', fontsize=12)
    ax.set_ylim(-1.6, 1.2)
    ax.legend(fontsize=8)

    # Panel D: Mantel Test
    ax = axes[1, 1]
    for i, align in enumerate(ALIGNMENTS):
        vals = [summary['mantel'].get(f'{roi}_{align}', {}).get('r', np.nan)
                for roi in ROIS]
        pvals = [summary['mantel'].get(f'{roi}_{align}', {}).get('p', 1.0)
                 for roi in ROIS]
        bars = ax.bar(x_pos + i * width, vals, width, color=ALIGN_COLORS[align],
                      label=ALIGN_LABELS[align], edgecolor='white', linewidth=0.5)
        for bar, v, p in zip(bars, vals, pvals):
            marker = '*' if p < 0.05 else ''
            marker = '(+)' if p < 0.10 and p >= 0.05 else marker
            y_pos = max(v, 0) + 0.02 if v >= 0 else v - 0.05
            ax.text(bar.get_x() + bar.get_width()/2, y_pos,
                    f'{v:.2f}{marker}', ha='center', va='bottom', fontsize=6.5, rotation=45)
    ax.axhline(0.5, color='gray', ls='--', lw=1, alpha=0.7)
    ax.axhline(0, color='black', lw=0.5, alpha=0.3)
    ax.text(3.8, 0.53, 'threshold=0.5', fontsize=8, color='gray', ha='right')
    ax.set_xticks(x_pos + width)
    ax.set_xticklabels(ROIS)
    ax.set_ylabel('Spearman r (vs ideal circular RDM)')
    ax.set_title('D. Mantel Test (neural vs circular RDM)', fontweight='bold', fontsize=12)
    ax.set_ylim(-0.5, 0.7)
    ax.legend(fontsize=8)

    fig.suptitle('Phase 1: MDS Diagnostic Summary — HC Group Mean RDM',
                 fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    out = RESULTS_DIR / 'fig5_dashboard.png'
    plt.savefig(out, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'Saved: {out}')


# ============================================================================
# Figure 2: Per-ROI 2D MDS (all ROIs × all alignments)
# ============================================================================
def plot_all_roi_mds():
    fig, axes = plt.subplots(4, 3, figsize=(15, 20))

    for row, roi in enumerate(ROIS):
        for col, align in enumerate(ALIGNMENTS):
            ax = axes[row, col]

            # Load HC group mean RDM
            rdms = []
            for subj in HC_SUBJECTS:
                try:
                    amp = load_amplitudes(subj, roi, align)
                    rdms.append(compute_rdm(amp.mean(axis=0)))
                except FileNotFoundError:
                    pass

            if not rdms:
                ax.text(0.5, 0.5, 'No data', transform=ax.transAxes,
                        ha='center', va='center')
                continue

            rdm_mean = np.mean(rdms, axis=0)
            mds = MDS(n_components=2, metric=True, n_init=10, max_iter=500,
                      random_state=42, dissimilarity='precomputed')
            coords = mds.fit_transform(rdm_mean)
            stress = normalized_stress(rdm_mean, coords)

            # Plot connecting lines (circular order)
            order = list(range(8)) + [0]
            ax.plot(coords[order, 0], coords[order, 1],
                    'k-', alpha=0.2, linewidth=1)

            # Plot ideal circle for reference
            theta_ideal = np.linspace(0, 2*np.pi, 100)
            r_ideal = np.max(np.abs(coords)) * 0.9
            ax.plot(r_ideal * np.cos(theta_ideal), r_ideal * np.sin(theta_ideal),
                    ':', color='gray', alpha=0.15, linewidth=1)

            # Plot color points
            for i in range(8):
                ax.scatter(coords[i, 0], coords[i, 1],
                          c=[COLOR_RGBS[i]], s=120, edgecolors='k',
                          linewidths=0.8, zorder=5)
                ax.annotate(f'{HUE_ANGLES[i]}',
                           (coords[i, 0], coords[i, 1]),
                           textcoords='offset points', xytext=(8, 8),
                           fontsize=8, fontweight='bold',
                           color=COLOR_RGBS[i])

            ax.set_aspect('equal')
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(f'stress={stress:.3f}', fontsize=10, color='dimgray')

            if row == 0:
                ax.set_title(f'{ALIGN_LABELS[align]}\nstress={stress:.3f}',
                            fontsize=11, fontweight='bold')
            if col == 0:
                ax.set_ylabel(roi, fontsize=13, fontweight='bold', rotation=0,
                             labelpad=30, va='center')

            # Color border based on stress
            border_color = '#2ecc71' if stress < 0.1 else '#f39c12' if stress < 0.2 else '#e74c3c'
            for spine in ax.spines.values():
                spine.set_edgecolor(border_color)
                spine.set_linewidth(2)

    fig.suptitle('2D MDS Embeddings — HC Group Mean (8 colors)',
                 fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    out = RESULTS_DIR / 'fig6_all_roi_mds.png'
    plt.savefig(out, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'Saved: {out}')


# ============================================================================
# Figure 3: Stress Elbow Plot (annotated)
# ============================================================================
def plot_stress_elbow():
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.5), sharey=True)
    dims = list(range(1, 7))

    for col, roi in enumerate(ROIS):
        ax = axes[col]

        for align in ALIGNMENTS:
            # Recompute stress curve
            rdms = []
            for subj in HC_SUBJECTS:
                try:
                    amp = load_amplitudes(subj, roi, align)
                    rdms.append(compute_rdm(amp.mean(axis=0)))
                except FileNotFoundError:
                    pass
            if not rdms:
                continue
            rdm_mean = np.mean(rdms, axis=0)

            stresses = []
            for n_dim in range(1, 7):
                mds = MDS(n_components=n_dim, metric=True, n_init=10,
                          max_iter=500, random_state=42, dissimilarity='precomputed')
                coords = mds.fit_transform(rdm_mean)
                stresses.append(normalized_stress(rdm_mean, coords))

            ax.plot(dims, stresses, 'o-', color=ALIGN_COLORS[align],
                    label=ALIGN_LABELS[align], linewidth=2, markersize=6)

            # Annotate 2D stress value
            ax.annotate(f'{stresses[1]:.3f}',
                       (2, stresses[1]),
                       textcoords='offset points',
                       xytext=(10, 5 if align != 'raw' else -15),
                       fontsize=8, color=ALIGN_COLORS[align],
                       fontweight='bold')

        ax.axhline(0.1, color='dimgray', ls='--', lw=1.5, alpha=0.6)
        ax.fill_between([0.5, 6.5], 0, 0.1, alpha=0.05, color='green')
        ax.text(6.3, 0.07, 'Good fit\n(< 0.1)', fontsize=7, color='green',
                ha='right', va='top', style='italic')

        ax.axhline(0.2, color='orange', ls=':', lw=1, alpha=0.4)
        ax.text(6.3, 0.21, 'Fair (0.2)', fontsize=7, color='orange',
                ha='right', va='bottom', alpha=0.6)

        ax.set_xlabel('Dimensions', fontsize=10)
        ax.set_title(roi, fontsize=13, fontweight='bold')
        ax.set_xticks(dims)
        ax.set_xlim(0.5, 6.5)

        if col == 0:
            ax.set_ylabel('Kruskal Normalized Stress', fontsize=10)
            ax.legend(fontsize=9, loc='upper right')

    fig.suptitle('MDS Stress by Dimensionality (HC Group Mean RDM)',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    out = RESULTS_DIR / 'fig7_stress_elbow.png'
    plt.savefig(out, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'Saved: {out}')


# ============================================================================
# Figure 4: Circular Order — Polar MDS Angle vs True Hue
# ============================================================================
def plot_circular_order_polar():
    fig, axes = plt.subplots(4, 3, figsize=(14, 18),
                              subplot_kw={'projection': 'polar'})

    for row, roi in enumerate(ROIS):
        for col, align in enumerate(ALIGNMENTS):
            ax = axes[row, col]

            rdms = []
            for subj in HC_SUBJECTS:
                try:
                    amp = load_amplitudes(subj, roi, align)
                    rdms.append(compute_rdm(amp.mean(axis=0)))
                except FileNotFoundError:
                    pass
            if not rdms:
                continue

            rdm_mean = np.mean(rdms, axis=0)
            mds = MDS(n_components=2, metric=True, n_init=10, max_iter=500,
                      random_state=42, dissimilarity='precomputed')
            coords = mds.fit_transform(rdm_mean)

            # True hue angles on outer ring
            true_rad = np.deg2rad(HUE_ANGLES)
            ax.scatter(true_rad, np.ones(8) * 1.0, s=100,
                      c=COLOR_RGBS, edgecolors='k', linewidths=0.8, zorder=5,
                      label='True hue')

            # MDS-derived angles on inner ring
            mds_angles = np.arctan2(coords[:, 1], coords[:, 0])
            ax.scatter(mds_angles, np.ones(8) * 0.65, s=60,
                      c=COLOR_RGBS, edgecolors='dimgray', linewidths=0.5,
                      marker='D', alpha=0.8, zorder=5, label='MDS angle')

            # Connect true to MDS with lines
            for i in range(8):
                ax.plot([true_rad[i], mds_angles[i]], [1.0, 0.65],
                       '-', color=COLOR_RGBS[i], alpha=0.3, linewidth=1)

            # Spearman rho annotation
            key = f'{roi}_{align}'
            circ = summary['circular_order'].get(key, {})
            rho = circ.get('rho', 0)
            p = circ.get('p', 1)
            sig = '*' if p < 0.05 else '(+)' if p < 0.10 else ''
            ax.set_title(f'rho={rho:.2f}{sig}', fontsize=9,
                        color='green' if abs(rho) > 0.8 else 'orange' if abs(rho) > 0.5 else 'red',
                        pad=10)

            ax.set_rticks([])
            ax.set_theta_zero_location('E')
            ax.set_theta_direction(1)

            if row == 0 and col == 1:
                ax.set_title(f'{ALIGN_LABELS[align]}\nrho={rho:.2f}{sig}',
                            fontsize=10, fontweight='bold', pad=15)
            elif row == 0:
                ax.set_title(f'{ALIGN_LABELS[align]}\nrho={rho:.2f}{sig}',
                            fontsize=10, fontweight='bold', pad=15)

            # ROI label on left
            if col == 0:
                ax.text(-0.15, 0.5, roi, transform=ax.transAxes,
                       fontsize=13, fontweight='bold', rotation=0,
                       va='center', ha='right')

    # Legend
    fig.legend(['True hue (outer)', 'MDS angle (inner)'],
              loc='lower center', ncol=2, fontsize=10,
              bbox_to_anchor=(0.5, -0.01))

    fig.suptitle('Circular Order Test: MDS Angular Positions vs True Hue Angles',
                 fontsize=14, fontweight='bold', y=1.01)
    plt.tight_layout(rect=[0, 0.02, 1, 0.98])
    out = RESULTS_DIR / 'fig8_circular_order_polar.png'
    plt.savefig(out, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'Saved: {out}')


# ============================================================================
# Figure 5: Procrustes Cross-Alignment Heatmap
# ============================================================================
def plot_procrustes_heatmap():
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))

    pairs = [('raw', 'procrustes'), ('raw', 'srm'), ('procrustes', 'srm')]
    pair_labels = ['Raw vs Proc', 'Raw vs SRM', 'Proc vs SRM']

    for col, roi in enumerate(ROIS):
        ax = axes[col]
        vals = []
        for a1, a2 in pairs:
            key = f'{roi}_{a1}_vs_{a2}'
            vals.append(summary['procrustes_disparity'].get(key, np.nan))

        colors = ['#e74c3c' if v > 1.0 else '#f39c12' if v > 0.5 else '#2ecc71'
                  for v in vals]
        bars = ax.barh(range(len(pairs)), vals, color=colors, edgecolor='white')

        for bar, v in zip(bars, vals):
            ax.text(v + 0.02, bar.get_y() + bar.get_height()/2,
                    f'{v:.3f}', va='center', fontsize=9, fontweight='bold')

        ax.set_yticks(range(len(pairs)))
        ax.set_yticklabels(pair_labels if col == 0 else [''] * 3)
        ax.set_xlabel('Procrustes Disparity')
        ax.set_title(roi, fontsize=12, fontweight='bold')
        ax.set_xlim(0, 2.0)
        ax.axvline(0.5, color='gray', ls=':', alpha=0.4)

    fig.suptitle('Cross-Alignment MDS Disparity (Procrustes)',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    out = RESULTS_DIR / 'fig9_procrustes_heatmap.png'
    plt.savefig(out, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'Saved: {out}')


# ============================================================================
# Figure 6: Pass/Fail Summary Heatmap
# ============================================================================
def plot_pass_fail():
    criteria = ['2d_stress_pass', 'circular_order_pass', 'shepard_pass', 'mantel_pass']
    criteria_labels = ['2D Stress\n< 0.10', 'Circular Order\n|r| > 0.80',
                       'Shepard R2\n> 0.80', 'Mantel\nr>0.5, p<0.05']

    fig, ax = plt.subplots(figsize=(14, 5))

    # Build matrix: rows = ROI x Align, cols = criteria
    row_labels = []
    matrix = []
    for roi in ROIS:
        for align in ALIGNMENTS:
            row_labels.append(f'{roi} / {ALIGN_LABELS[align]}')
            row_data = []
            for c in criteria:
                val = summary['decisions'].get(roi, {}).get(align, {}).get(c, False)
                row_data.append(1 if val else 0)
            matrix.append(row_data)

    matrix = np.array(matrix)

    # Plot
    im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)

    ax.set_xticks(range(len(criteria)))
    ax.set_xticklabels(criteria_labels, fontsize=10)
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=9)

    # Annotate cells
    for i in range(len(row_labels)):
        for j in range(len(criteria)):
            text = 'PASS' if matrix[i, j] else 'FAIL'
            color = 'white' if matrix[i, j] else 'black'
            ax.text(j, i, text, ha='center', va='center',
                   fontsize=8, fontweight='bold', color=color)

    # Add pass count on right
    for i, row_label in enumerate(row_labels):
        total = int(matrix[i].sum())
        ax.text(len(criteria) + 0.3, i, f'{total}/4',
               ha='left', va='center', fontsize=9,
               fontweight='bold',
               color='green' if total >= 3 else 'orange' if total >= 2 else 'red')

    ax.set_title('Phase 1 MDS Diagnostic — Pass/Fail Summary',
                fontsize=14, fontweight='bold')
    plt.tight_layout()
    out = RESULTS_DIR / 'fig10_pass_fail.png'
    plt.savefig(out, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'Saved: {out}')


# ============================================================================
# Main
# ============================================================================
if __name__ == '__main__':
    print('Generating Phase 1 visualizations...')
    print()

    plot_dashboard()
    plot_all_roi_mds()
    plot_stress_elbow()
    plot_circular_order_polar()
    plot_procrustes_heatmap()
    plot_pass_fail()

    print('\nAll visualizations complete.')
