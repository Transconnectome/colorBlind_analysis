#!/usr/bin/env python3
"""
LOCO (Leave-One-Color-Out) summary visualization for phase3_decoder_comparing.

Produces three figures from Procrustes-aligned ForwardEncoding LOCO results:
  1. fig_loco_hc_vs_cvd.png   — HC vs CVD MAE strip+box across 4 ROIs
  2. fig_loco_per_color_polar.png — 2×2 polar grid per-color MAE
  3. fig_loco_individual_heatmap.png — Subject × Color heatmap for hV4

Data: analysis/phase3_decoder_comparing/results/loco/procrustes/sub-{ID}_loco.json
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from scipy import stats

# ============================================================================
# Configuration
# ============================================================================
BASE_DIR = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis')
LOCO_DIR = BASE_DIR / 'analysis' / 'phase3_decoder_comparing' / 'results' / 'loco' / 'procrustes'
OUTPUT_DIR = BASE_DIR / 'analysis' / 'phase3_decoder_comparing' / 'figures'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

HC_IDS = [f'{i:02d}' for i in range(1, 8)]
CVD_IDS = ['08', '09', '10']
ALL_IDS = HC_IDS + CVD_IDS

CVD_META = {
    '08': {'type': 'Deutan', 'color': '#E74C3C', 'marker': 's'},
    '09': {'type': 'Protan', 'color': '#E67E22', 'marker': '^'},
    '10': {'type': 'Deutan', 'color': '#9B59B6', 'marker': 'D'},
}

ROIS = ['V1', 'V2', 'V3', 'V4']
ROI_LABELS = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}
N_COLORS = 8
MODEL = 'ForwardEncoding'

COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
COLOR_ANGLES_DEG = np.array([0, 45, 90, 135, 180, 225, 270, 315])
COLOR_RGB = ['#E74C3C', '#E67E22', '#F1C40F', '#2ECC71',
             '#1ABC9C', '#3498DB', '#9B59B6', '#E91E90']

# Crawford & Howell p-values from notion.md
CRAWFORD_P = {'V1': 0.237, 'V2': 0.072, 'V3': 0.642, 'V4': 0.017}


# ============================================================================
# Data Loading
# ============================================================================

def load_loco_mae(loco_dir, subject_ids, model=MODEL):
    """Load per-subject, per-ROI mean MAE from LOCO JSON files.

    Returns
    -------
    mae : dict[roi] -> dict[subj_id] -> float (mean MAE across 8 folds)
    per_color : dict[roi] -> dict[subj_id] -> np.array(8,) per-color MAE
    """
    mae = {r: {} for r in ROIS}
    per_color = {r: {} for r in ROIS}

    for sid in subject_ids:
        fpath = loco_dir / f'sub-{sid}_loco.json'
        if not fpath.exists():
            print(f"  [WARN] Missing: {fpath.name}")
            continue
        with open(fpath) as f:
            data = json.load(f)

        for roi in ROIS:
            if roi not in data['results']:
                continue
            if model not in data['results'][roi]:
                continue

            folds = data['results'][roi][model]['fold_results']
            color_maes = np.array([fold['mae'] for fold in folds])
            mae[roi][sid] = float(np.mean(color_maes))
            per_color[roi][sid] = color_maes

    return mae, per_color


# ============================================================================
# Figure 1: HC vs CVD MAE strip + box (4 ROIs)
# ============================================================================

def fig_hc_vs_cvd(mae, output_path):
    """Strip + box plot of LOCO MAE: HC distribution vs CVD individuals."""
    fig, ax = plt.subplots(figsize=(8, 5.5))

    x_positions = np.arange(len(ROIS))
    box_width = 0.35
    rng = np.random.default_rng(42)

    for i, roi in enumerate(ROIS):
        hc_vals = [mae[roi][s] for s in HC_IDS if s in mae[roi]]
        # HC box
        bp = ax.boxplot([hc_vals], positions=[i - 0.18], widths=box_width,
                        patch_artist=True, showfliers=False,
                        medianprops=dict(color='white', linewidth=1.5),
                        whiskerprops=dict(color='#2C3E50'),
                        capprops=dict(color='#2C3E50'))
        bp['boxes'][0].set(facecolor='#3498DB', alpha=0.5, edgecolor='#2C3E50')

        # HC individual points
        for val in hc_vals:
            jitter = rng.uniform(-0.06, 0.06)
            ax.scatter(i - 0.18 + jitter, val, color='#2980B9',
                       s=28, alpha=0.7, zorder=3, edgecolor='white', linewidth=0.3)

        # CVD individual points
        for j, cvd_id in enumerate(CVD_IDS):
            if cvd_id not in mae[roi]:
                continue
            meta = CVD_META[cvd_id]
            x_cvd = i + 0.22 + (j - 1) * 0.12
            ax.scatter(x_cvd, mae[roi][cvd_id],
                       color=meta['color'], marker=meta['marker'],
                       s=70, edgecolor='black', linewidth=0.8, zorder=4)

        # Crawford & Howell p annotation
        p = CRAWFORD_P[roi]
        ymax = max(hc_vals + [mae[roi].get(s, 0) for s in CVD_IDS])
        if p < 0.05:
            ax.annotate(f'p={p:.3f}*', xy=(i, ymax + 3), fontsize=8,
                        fontweight='bold', color='#C0392B', ha='center')
        elif p < 0.1:
            ax.annotate(f'p={p:.3f}†', xy=(i, ymax + 3), fontsize=8,
                        fontstyle='italic', color='#7F8C8D', ha='center')

    # Chance line
    ax.axhline(90, color='gray', linestyle='--', linewidth=1, alpha=0.5, zorder=1)
    ax.text(len(ROIS) - 0.5, 91.5, 'Chance (90°)', fontsize=7, color='gray',
            ha='right')

    # Legend
    hc_patch = mpatches.Patch(facecolor='#3498DB', alpha=0.5, edgecolor='#2C3E50',
                              label='HC (n=7)')
    cvd_handles = [
        plt.Line2D([], [], color=CVD_META[c]['color'], marker=CVD_META[c]['marker'],
                   linestyle='', markersize=7, markeredgecolor='black',
                   label=f'sub-{c} ({CVD_META[c]["type"]})')
        for c in CVD_IDS
    ]
    ax.legend(handles=[hc_patch] + cvd_handles, loc='upper left', fontsize=8,
              framealpha=0.9)

    ax.set_xticks(x_positions)
    ax.set_xticklabels([ROI_LABELS[r] for r in ROIS], fontsize=11)
    ax.set_ylabel('LOCO MAE (degrees)', fontsize=11)
    ax.set_title('LOCO Interpolation: HC vs CVD (FE + Procrustes)', fontsize=12,
                 fontweight='bold')
    ax.set_xlim(-0.6, len(ROIS) - 0.4)
    ax.grid(axis='y', alpha=0.2)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path.name}")


# ============================================================================
# Figure 2: Per-color polar 2×2 grid
# ============================================================================

def fig_per_color_polar(per_color, output_path):
    """2×2 polar grid: per-color MAE for HC mean ± SD vs CVD individuals."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 13),
                             subplot_kw=dict(projection='polar'))

    for idx, roi in enumerate(ROIS):
        ax = axes[idx // 2][idx % 2]

        # HC statistics
        hc_matrix = np.array([per_color[roi][s] for s in HC_IDS if s in per_color[roi]])
        hc_mean = hc_matrix.mean(axis=0)
        hc_std = hc_matrix.std(axis=0)

        angles_rad = np.deg2rad(COLOR_ANGLES_DEG)
        # Close the polygon
        ang_c = np.concatenate([angles_rad, [angles_rad[0]]])
        mean_c = np.concatenate([hc_mean, [hc_mean[0]]])
        lo_c = np.concatenate([hc_mean - hc_std, [hc_mean[0] - hc_std[0]]])
        hi_c = np.concatenate([hc_mean + hc_std, [hc_mean[0] + hc_std[0]]])

        # HC shaded
        ax.fill_between(ang_c, np.maximum(lo_c, 0), hi_c,
                        color='#3498DB', alpha=0.2, zorder=1)
        ax.plot(ang_c, mean_c, 'o-', color='#2980B9', linewidth=2, markersize=6,
                label='HC mean', zorder=3)

        # CVD lines
        for cvd_id in CVD_IDS:
            if cvd_id not in per_color[roi]:
                continue
            vals = per_color[roi][cvd_id]
            vals_c = np.concatenate([vals, [vals[0]]])
            meta = CVD_META[cvd_id]
            ax.plot(ang_c, vals_c, marker=meta['marker'], linestyle='--',
                    linewidth=1.8, markersize=6, color=meta['color'], alpha=0.85,
                    label=f'sub-{cvd_id}', zorder=4)

        # Color labels at perimeter
        all_vals = list(hc_mean) + [v for c in CVD_IDS if c in per_color[roi]
                                     for v in per_color[roi][c]]
        r_label = max(all_vals) * 1.2
        for angle, name, rgb in zip(angles_rad, COLOR_NAMES, COLOR_RGB):
            ax.text(angle, r_label, name, ha='center', va='center', fontsize=7,
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor=rgb,
                              edgecolor='#2C3E50', linewidth=1, alpha=0.6))

        ax.set_theta_zero_location('N')
        ax.set_theta_direction(-1)
        ax.set_yticklabels([])
        ax.set_xticks(angles_rad)
        ax.set_xticklabels([])
        ax.grid(True, linestyle=':', alpha=0.3)

        # p-value in title
        p = CRAWFORD_P[roi]
        p_str = f'  p={p:.3f}*' if p < 0.05 else (f'  p={p:.3f}†' if p < 0.1 else '')
        title_str = f'{ROI_LABELS[roi]}  (HC mean={hc_mean.mean():.1f}°){p_str}'
        ax.set_title(title_str, fontsize=11, fontweight='bold', pad=25)

        if idx == 0:
            ax.legend(loc='upper left', bbox_to_anchor=(1.15, 1.05), fontsize=8)

    fig.suptitle('LOCO Per-Color Interpolation Error (FE + Procrustes)',
                 fontsize=14, fontweight='bold', y=1.02)
    plt.subplots_adjust(hspace=0.35, wspace=0.3)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path.name}")


# ============================================================================
# Figure 3: Subject × Color heatmap for hV4
# ============================================================================

def fig_individual_heatmap(per_color, output_path):
    """Heatmap of per-subject per-color MAE in hV4 (the significant ROI)."""
    roi = 'V4'
    subjects_order = HC_IDS + CVD_IDS
    labels = [f'sub-{s}' for s in subjects_order]

    matrix = []
    for sid in subjects_order:
        if sid in per_color[roi]:
            matrix.append(per_color[roi][sid])
        else:
            matrix.append(np.full(N_COLORS, np.nan))
    matrix = np.array(matrix)  # (10, 8)

    fig, ax = plt.subplots(figsize=(10, 5.5))
    im = ax.imshow(matrix, aspect='auto', cmap='RdYlGn_r', vmin=0, vmax=180)

    # Annotate cells
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            val = matrix[i, j]
            if np.isnan(val):
                continue
            txt_color = 'white' if val > 120 else 'black'
            ax.text(j, i, f'{val:.0f}', ha='center', va='center',
                    fontsize=8, color=txt_color, fontweight='bold')

    ax.set_xticks(range(N_COLORS))
    ax.set_xticklabels(COLOR_NAMES, fontsize=9, rotation=30, ha='right')
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=9)

    # Group separator and bracket
    ax.axhline(6.5, color='white', linewidth=2.5)
    # Use axes transform for group labels so they don't overlap ytick labels
    ax.annotate('HC', xy=(-0.08, 0.65), xycoords='axes fraction',
                fontsize=10, fontweight='bold', color='#2980B9', ha='center',
                va='center', rotation=90)
    ax.annotate('CVD', xy=(-0.08, 0.17), xycoords='axes fraction',
                fontsize=10, fontweight='bold', color='#E74C3C', ha='center',
                va='center', rotation=90)

    # Subject-level mean on right
    for i, sid in enumerate(subjects_order):
        if sid in per_color[roi]:
            m = per_color[roi][sid].mean()
            ax.text(N_COLORS + 0.15, i, f'{m:.1f}°', va='center', fontsize=8,
                    fontweight='bold',
                    color='#E74C3C' if sid in CVD_IDS else '#2C3E50')

    ax.text(N_COLORS + 0.15, -0.8, 'Mean', ha='left', fontsize=8,
            fontweight='bold', color='#7F8C8D')

    cbar = plt.colorbar(im, ax=ax, fraction=0.025, pad=0.12)
    cbar.set_label('MAE (degrees)', fontsize=10)

    ax.set_title('hV4 LOCO Per-Color Error by Subject (FE + Procrustes)',
                 fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {output_path.name}")


# ============================================================================
# Main
# ============================================================================

def main():
    print("=" * 60)
    print("LOCO Summary Visualization")
    print("=" * 60)
    print(f"Data: {LOCO_DIR}")
    print(f"Output: {OUTPUT_DIR}\n")

    mae, per_color = load_loco_mae(LOCO_DIR, ALL_IDS)

    # Quick sanity check
    for roi in ROIS:
        hc_vals = [mae[roi][s] for s in HC_IDS if s in mae[roi]]
        cvd_vals = [mae[roi].get(s, np.nan) for s in CVD_IDS]
        print(f"  {ROI_LABELS[roi]:>4s}: HC={np.mean(hc_vals):.1f}° ± {np.std(hc_vals):.1f}°  "
              f"CVD=[{', '.join(f'{v:.1f}' for v in cvd_vals)}]")

    print()
    fig_hc_vs_cvd(mae, OUTPUT_DIR / 'fig_loco_hc_vs_cvd.png')
    fig_per_color_polar(per_color, OUTPUT_DIR / 'fig_loco_per_color_polar.png')
    fig_individual_heatmap(per_color, OUTPUT_DIR / 'fig_loco_individual_heatmap.png')

    print("\nDone.")


if __name__ == '__main__':
    main()
