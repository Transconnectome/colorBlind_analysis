#!/usr/bin/env python3
"""
visualize_filter_comparison.py — Compare CVD distortion and filter correction across models.

Layout (2×2):
  Row 1: Sub-08 (deutan)  — R+C vs 2-Component
  Row 2: Sub-09 (protan)  — Machado vs 2-Component

Each panel: 8 color swatches in 5 rows:
  (A) Original stimulus (CIELab)
  (B) CVD perceived (distorted) — rendered as CIELab-equivalent via normal inverse
  (C) Modified stimulus (pre-image filter, CIELab)
  (D) CVD perceived after filter — rendered as CIELab-equivalent
  (E) Healthy target (= identical to A for normal vision)

IMPORTANT: Rows B, D, E are in opponent color space (from Stockman cone model).
Opponent ≠ CIELab, so we invert through the normal-vision forward model to get the
CIELab angle that a normal observer would associate with each opponent percept.
This ensures:  E = A (correct),  D ≈ A when filter is exact (correct).

Usage:
    conda activate srm
    python scripts/visualize_filter_comparison.py
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from pathlib import Path
import shutil

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PIPELINE_DIR = _SCRIPT_DIR.parent

# ---------------------------------------------------------------------------
# CIELab → sRGB conversion
# ---------------------------------------------------------------------------
_M_XYZ_TO_SRGB = np.array([
    [3.2406, -1.5372, -0.4986],
    [-0.9689,  1.8758,  0.0415],
    [0.0557, -0.2040,  1.0570],
])

# Screenshot-derived CIELab values (actual experimental stimuli)
STIM_LAB = {
    'color_1': [59.90, 62.69, 3.78],    # 0°  Red
    'color_2': [64.20, 49.20, 45.58],   # 45° Orange
    'color_3': [57.27, 13.06, 41.69],   # 90° Yellow
    'color_4': [69.08, -55.02, 47.38],  # 135° Green
    'color_5': [74.61, -41.33, -4.89],  # 180° Cyan
    'color_6': [69.14, -11.45, -40.91], # 225° Blue
    'color_7': [60.68, 19.18, -54.13],  # 270° Purple
    'color_8': [60.17, 46.82, -40.31],  # 315° Magenta
}

CIELAB_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
COLOR_LABELS = [f'c{i+1}' for i in range(8)]

# Pre-compute stimulus properties
STIM_LAB_ARR = np.array([STIM_LAB[f'color_{i+1}'] for i in range(8)])
STIM_L = STIM_LAB_ARR[:, 0]
STIM_A = STIM_LAB_ARR[:, 1]
STIM_B = STIM_LAB_ARR[:, 2]
STIM_CHROMA = np.sqrt(STIM_A**2 + STIM_B**2)


def lab2rgb(L, a, b):
    """CIELab → sRGB [0,1]."""
    L, a, b = np.asarray(L, float), np.asarray(a, float), np.asarray(b, float)
    y = (L + 16) / 116
    x = a / 500 + y
    z = y - b / 200
    xyz = np.stack([x, y, z], axis=-1)
    mask = xyz > 0.206893
    xyz = np.where(mask, xyz**3, (xyz - 16/116) / 7.787)
    xyz *= np.array([0.95047, 1.0, 1.08883])
    rgb = xyz @ _M_XYZ_TO_SRGB.T
    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb,
                   1.055 * np.power(np.maximum(rgb, 0), 1/2.4) - 0.055)
    return np.clip(rgb, 0, 1)


# ---------------------------------------------------------------------------
# Opponent → CIELab inverse mapping
# ---------------------------------------------------------------------------
def build_opponent_to_cielab(target_opponent_angles, cielab_angles):
    """Build an inverse mapping: opponent angle → CIELab-equivalent angle.

    Uses the 8-point normal-vision forward model (CIELab → Opponent) and
    piecewise linear interpolation on the circular domain.

    Parameters
    ----------
    target_opponent_angles : (8,) opponent angles for the 8 stimuli under normal vision
    cielab_angles : (8,) CIELab angles [0, 45, 90, ..., 315]

    Returns
    -------
    callable : opponent_angle → CIELab-equivalent angle
    """
    opp = np.array(target_opponent_angles)
    lab = np.array(cielab_angles)

    # Sort by opponent angle (ascending)
    idx = np.argsort(opp)
    opp_sorted = opp[idx]
    lab_sorted = lab[idx]

    # Unwrap CIELab to make monotonically decreasing
    # (opponent increases ~87→348, CIELab goes ~270→225→...→0→315)
    lab_unwrap = lab_sorted.copy()
    for i in range(1, len(lab_unwrap)):
        while lab_unwrap[i] > lab_unwrap[i - 1]:
            lab_unwrap[i] -= 360

    # Extend periodically for circular interpolation
    opp_ext = np.concatenate([opp_sorted - 360, opp_sorted, opp_sorted + 360])
    lab_ext = np.concatenate([lab_unwrap + 360, lab_unwrap, lab_unwrap - 360])

    def inverse(opp_query):
        """Map opponent angle(s) → CIELab-equivalent angle(s)."""
        result = np.interp(np.asarray(opp_query), opp_ext, lab_ext)
        return result % 360

    return inverse


# ---------------------------------------------------------------------------
# Color rendering
# ---------------------------------------------------------------------------
def render_colors(cielab_angles_per_color):
    """Render 8 colors at given CIELab angles, using per-color L* and chroma
    from the actual experimental stimuli for vivid, consistent rendering.

    Each color c_i keeps its original L* and chroma but shifts to the
    specified CIELab hue angle.
    """
    angles = np.asarray(cielab_angles_per_color)
    hue_rad = np.deg2rad(angles)
    new_a = STIM_CHROMA * np.cos(hue_rad)
    new_b = STIM_CHROMA * np.sin(hue_rad)
    return lab2rgb(STIM_L, new_a, new_b)


# ---------------------------------------------------------------------------
# Load pre-image data
# ---------------------------------------------------------------------------
def load_preimage(filename):
    path = _PIPELINE_DIR / 'results' / 'loco_filter' / filename
    if not path.exists():
        path = _PIPELINE_DIR / 'results' / 'loco_filter' / 'preimage_2component' / Path(filename).name
    if not path.exists():
        path = _PIPELINE_DIR / 'results' / 'loco_filter' / 'preimage' / filename
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Swatch drawing
# ---------------------------------------------------------------------------
def draw_swatch_row(ax, rgbs, y, swatch_w=0.085, swatch_h=0.12, spacing=0.098,
                    label=None, label_color='black', edgecolor='#333',
                    linewidth=1.0, fail_indices=None):
    """Draw a row of 8 color swatches at vertical position y."""
    x_start = 0.16
    for i in range(8):
        x = x_start + i * spacing
        rect = FancyBboxPatch(
            (x, y), swatch_w, swatch_h,
            boxstyle="round,pad=0.01",
            facecolor=rgbs[i],
            edgecolor=edgecolor,
            linewidth=linewidth,
            transform=ax.transAxes,
            zorder=3,
        )
        ax.add_patch(rect)

        # Color label
        brightness = 0.299 * rgbs[i][0] + 0.587 * rgbs[i][1] + 0.114 * rgbs[i][2]
        txt_color = 'white' if brightness < 0.45 else 'black'
        ax.text(x + swatch_w / 2, y + swatch_h / 2, COLOR_LABELS[i],
                transform=ax.transAxes, fontsize=6.5, ha='center', va='center',
                color=txt_color, fontweight='bold', zorder=5)

        # Fail marker — red X over the swatch
        if fail_indices and i in fail_indices:
            ax.plot([x, x + swatch_w], [y, y + swatch_h],
                    color='red', linewidth=2.5, transform=ax.transAxes, zorder=6)
            ax.plot([x, x + swatch_w], [y + swatch_h, y],
                    color='red', linewidth=2.5, transform=ax.transAxes, zorder=6)

    if label:
        ax.text(0.14, y + swatch_h / 2, label, transform=ax.transAxes,
                fontsize=7.5, ha='right', va='center', color=label_color,
                fontweight='bold')


def draw_arrows(ax, y_from, y_to, x_start=0.16, spacing=0.098, swatch_w=0.085,
                color='gray', alpha=0.4):
    """Draw downward arrows between swatch rows."""
    for i in range(8):
        x = x_start + i * spacing + swatch_w / 2
        ax.annotate('', xy=(x, y_to + 0.005), xytext=(x, y_from - 0.005),
                    xycoords='axes fraction', textcoords='axes fraction',
                    arrowprops=dict(arrowstyle='->', color=color, alpha=alpha,
                                    lw=1.0),
                    zorder=1)


# ---------------------------------------------------------------------------
# Panel drawing
# ---------------------------------------------------------------------------
def draw_panel(ax, original_rgb, perceived_rgb, modified_rgb, restored_rgb,
               target_rgb, title, model_info, fail_indices=None):
    """Draw a single panel with 5 swatch rows + arrows."""
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    y_pos = {
        'original': 0.82,
        'perceived': 0.65,
        'modified': 0.44,
        'restored': 0.27,
        'target': 0.08,
    }
    labels = {
        'original': '(A) Stimulus',
        'perceived': '(B) CVD sees',
        'modified': '(C) Filtered\n     stimulus',
        'restored': '(D) CVD sees\n     after filter',
        'target': '(E) HC target',
    }

    draw_swatch_row(ax, original_rgb, y_pos['original'],
                    label=labels['original'], edgecolor='#333', linewidth=1.5)
    draw_swatch_row(ax, perceived_rgb, y_pos['perceived'],
                    label=labels['perceived'], edgecolor='#C62828', linewidth=1.5)
    draw_swatch_row(ax, modified_rgb, y_pos['modified'],
                    label=labels['modified'], edgecolor='#1565C0', linewidth=1.5)
    draw_swatch_row(ax, restored_rgb, y_pos['restored'],
                    label=labels['restored'], edgecolor='#2E7D32', linewidth=1.5,
                    fail_indices=fail_indices)
    draw_swatch_row(ax, target_rgb, y_pos['target'],
                    label=labels['target'], edgecolor='#555', linewidth=1.0)

    # Arrows
    draw_arrows(ax, y_pos['original'], y_pos['perceived'] + 0.12,
                color='#C62828', alpha=0.3)
    draw_arrows(ax, y_pos['perceived'], y_pos['modified'] + 0.12,
                color='#1565C0', alpha=0.3)
    draw_arrows(ax, y_pos['modified'], y_pos['restored'] + 0.12,
                color='#2E7D32', alpha=0.3)

    # Match quality between (D) and (E)
    n_fail = len(fail_indices) if fail_indices else 0
    n_pass = 8 - n_fail
    if n_fail == 0:
        match_text = 'D = E: 8/8 exact match'
        match_color = '#2E7D32'
    else:
        match_text = f'D vs E: {n_pass}/8 match, {n_fail}/8 FAIL'
        match_color = '#C62828'
    ax.text(0.55, y_pos['target'] + 0.155, match_text,
            transform=ax.transAxes, fontsize=7, ha='center', va='center',
            color=match_color, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor=match_color, alpha=0.9))

    ax.set_title(title, fontsize=10, fontweight='bold', pad=8)
    ax.text(0.98, 0.97, model_info, transform=ax.transAxes,
            fontsize=7, ha='right', va='top', color='#555', fontstyle='italic')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # Load pre-image results
    d08_rc = load_preimage('preimage/sub-08_V4_rc_opponent_preimage.json')
    d08_2c = load_preimage('preimage_2component/sub-08_V4_2component_preimage.json')
    d09_mach = load_preimage('preimage/sub-09_V4_machado_1way_preimage.json')
    d09_2c = load_preimage('preimage_2component/sub-09_V4_2component_preimage.json')

    # --- Build opponent → CIELab inverse ---
    # Normal vision: CIELab [0,45,...,315] → Opponent [313.47, 299.86, ...]
    target_opponent = np.array(d08_rc['target_angles_opponent'])
    opp2lab = build_opponent_to_cielab(target_opponent, CIELAB_ANGLES)

    # --- Verify: HC target should map back to original CIELab ---
    hc_cielab_equiv = opp2lab(target_opponent)
    print("HC target → CIELab-equiv (should be 0,45,...,315):")
    print("  ", np.round(hc_cielab_equiv, 1))

    # --- Common ---
    original_rgb = render_colors(CIELAB_ANGLES)
    target_rgb = render_colors(hc_cielab_equiv)  # Should ≈ original_rgb

    # === Helper: prepare panel data ===
    def prepare_panel(data):
        """Extract angles and convert opponent→CIELab for rendering."""
        perceived_opp = np.array(data['forward_model_at_original']['perceived'])
        preimage_cielab = np.array(data['preimage_angles'])
        restored_opp = np.array(data['perceived_angles'])
        residuals = np.array(data['residuals'])

        # Convert perception rows: opponent → CIELab-equivalent
        perceived_cielab = opp2lab(perceived_opp)
        restored_cielab = opp2lab(restored_opp)

        print(f"\n  {data['subject']} {data['model']}:")
        print(f"    Perceived CIELab-equiv: {np.round(perceived_cielab, 1)}")
        print(f"    Preimage CIELab:        {np.round(preimage_cielab, 1)}")
        print(f"    Restored CIELab-equiv:  {np.round(restored_cielab, 1)}")
        print(f"    Max residual:           {np.max(residuals):.4f}°")

        perceived_rgb = render_colors(perceived_cielab)
        modified_rgb = render_colors(preimage_cielab)
        restored_rgb = render_colors(restored_cielab)
        fail_idx = [i for i in range(8) if residuals[i] > 1.0]

        return perceived_rgb, modified_rgb, restored_rgb, fail_idx

    s08_rc = prepare_panel(d08_rc)
    s08_2c = prepare_panel(d08_2c)
    s09_m = prepare_panel(d09_mach)
    s09_2c = prepare_panel(d09_2c)

    # === Create figure ===
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.subplots_adjust(hspace=0.30, wspace=0.15, left=0.06, right=0.98,
                        top=0.90, bottom=0.04)

    draw_panel(axes[0, 0], original_rgb, s08_rc[0], s08_rc[1], s08_rc[2], target_rgb,
               title='Sub-08 (Deutan) — R+C Model',
               model_info=r'$\Delta\lambda$=2.0nm, g=+2.25 | $\rho$=0.857, p=0.005**',
               fail_indices=s08_rc[3])

    draw_panel(axes[0, 1], original_rgb, s08_2c[0], s08_2c[1], s08_2c[2], target_rgb,
               title='Sub-08 (Deutan) — 2-Component Model',
               model_info=r'$\beta_s$=38°, $\beta_c$=-14° | $\rho$=0.881, p=0.004**',
               fail_indices=s08_2c[3])

    draw_panel(axes[1, 0], original_rgb, s09_m[0], s09_m[1], s09_m[2], target_rgb,
               title='Sub-09 (Protan) — Machado Model',
               model_info=r'$\Delta\lambda$=13.5nm | $\rho$=0.762, p=0.018*',
               fail_indices=s09_m[3])

    draw_panel(axes[1, 1], original_rgb, s09_2c[0], s09_2c[1], s09_2c[2], target_rgb,
               title='Sub-09 (Protan) — 2-Component Model',
               model_info=r'$\beta_s$=6°, $\beta_c$=-22° | $\rho$=0.690, p=0.035*',
               fail_indices=s09_2c[3])

    # Row labels
    fig.text(0.01, 0.72, 'Sub-08\n(mild deutan)', fontsize=11, fontweight='bold',
             ha='center', va='center', rotation=90, color='#333')
    fig.text(0.01, 0.28, 'Sub-09\n(mod. protan)', fontsize=11, fontweight='bold',
             ha='center', va='center', rotation=90, color='#333')

    # Column headers
    fig.text(0.30, 0.93, 'Cone-Level Model', fontsize=12, fontweight='bold',
             ha='center', va='bottom', color='#555')
    fig.text(0.75, 0.93, 'Cortical-Level Model (2-Component)', fontsize=12,
             fontweight='bold', ha='center', va='bottom', color='#555')

    fig.suptitle('CVD Color Distortion & Filter Correction: Model Comparison',
                 fontsize=14, fontweight='bold', y=0.98)

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor='#eee', edgecolor='#333', linewidth=1.5,
                       label='(A) Original stimulus'),
        mpatches.Patch(facecolor='#eee', edgecolor='#C62828', linewidth=1.5,
                       label='(B) CVD perceived (distorted)'),
        mpatches.Patch(facecolor='#eee', edgecolor='#1565C0', linewidth=1.5,
                       label='(C) Filter-modified stimulus'),
        mpatches.Patch(facecolor='#eee', edgecolor='#2E7D32', linewidth=1.5,
                       label='(D) CVD perceived after filter'),
        mpatches.Patch(facecolor='#eee', edgecolor='#555', linewidth=1.0,
                       label='(E) Healthy target (= normal sees A)'),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=5,
               fontsize=8, frameon=True, fancybox=True, shadow=False,
               bbox_to_anchor=(0.52, -0.01))

    # Save
    out_dir = _PIPELINE_DIR / 'results' / 'loco_filter' / 'preimage_2component' / 'figures'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'filter_comparison_all_models.png'
    fig.savefig(out_path, dpi=200, bbox_inches='tight', facecolor='white')
    print(f'\nSaved: {out_path}')
    plt.close()

    shared_dir = _PIPELINE_DIR / 'results' / 'loco_filter' / 'preimage' / 'figures'
    shared_path = shared_dir / 'filter_comparison_all_models.png'
    shutil.copy2(out_path, shared_path)
    print(f'Copied to: {shared_path}')


if __name__ == '__main__':
    main()
