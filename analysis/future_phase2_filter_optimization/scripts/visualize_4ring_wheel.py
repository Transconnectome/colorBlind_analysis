#!/usr/bin/env python3
"""
visualize_4ring_wheel.py — 4-ring color wheel: original / perceived / modified / expected

For each subject (sub-08, sub-09, sub-10), shows 4 concentric rings:
  Ring 1 (innermost): Original stimulus colors (CIELab positions)
  Ring 2: CVD-perceived colors (opponent angles, unfiltered)
  Ring 3: Modified stimulus (preimage/separation CIELab angles)
  Ring 4 (outermost): Expected CVD perception after filter (opponent angles)

Color rendering:
  Stimulus rings (1, 3): lab2rgb at CIELab angle → actual physical stimulus color
  Perception rings (2, 4): lab2rgb at opponent angle → visual approximation of
                            what the person perceives (CIELab ≠ opponent, but
                            close enough for intuition)

Usage (local, conda srm):
    python scripts/visualize_4ring_wheel.py
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from pathlib import Path
import sys

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PIPELINE_DIR = _SCRIPT_DIR.parent
# cone_shift_pipeline/scripts → future_phase2_.../cone_shift_pipeline/scripts
# utils is at analysis/utils
_ANALYSIS_DIR = _SCRIPT_DIR.parent.parent.parent
sys.path.insert(0, str(_ANALYSIS_DIR / 'utils'))

from utils_color_decoding import lab2rgb_accurate, COLOR_LAB

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']
CIELAB_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)


def angle_to_rgb(theta_deg, L_star=65.0, chroma=45.0):
    """CIELab angle → RGB for rendering on the wheel."""
    theta_rad = np.deg2rad(theta_deg)
    L = L_star
    a = chroma * np.cos(theta_rad)
    b = chroma * np.sin(theta_rad)
    return lab2rgb_accurate(L, a, b)


def stimulus_rgb(color_idx):
    """Get the actual experimental stimulus RGB for color_idx (0-7)."""
    key = f'color_{color_idx + 1}'
    L, a, b = COLOR_LAB[key]
    return lab2rgb_accurate(L, a, b)


# ---------------------------------------------------------------------------
# Drawing
# ---------------------------------------------------------------------------

def draw_4ring_wheel(ax, original_angles, perceived_angles,
                     modified_angles, expected_angles,
                     title, subject_label, use_stimulus_colors=True):
    """Draw 4-ring color wheel on a polar axes.

    Parameters
    ----------
    original_angles : (8,) CIELab angles of original stimulus
    perceived_angles : (8,) opponent angles of CVD perception (unfiltered)
    modified_angles : (8,) CIELab angles of filtered stimulus
    expected_angles : (8,) opponent angles of expected CVD perception (filtered)
    """
    # Ring radii (inner to outer)
    radii = [0.50, 0.67, 0.84, 1.00]
    ring_names = ['Original\nStimulus', 'CVD\nPerceived', 'Modified\nStimulus',
                  'Expected\nPerception']
    # Marker styles
    sizes = [220, 180, 180, 220]
    edge_colors = ['black', '#555555', 'navy', 'black']
    linewidths = [1.8, 1.2, 1.2, 1.8]
    markers = ['o', 's', 'D', 'o']  # circle, square, diamond, circle

    ax.set_theta_zero_location("E")
    ax.set_theta_direction(1)
    ax.set_rticks([])
    ax.grid(alpha=0.12)
    ax.set_ylim(0, 1.22)

    all_ring_data = [
        (original_angles,  True),   # CIELab-based
        (perceived_angles, False),  # Opponent-based
        (modified_angles,  True),   # CIELab-based
        (expected_angles,  False),  # Opponent-based
    ]

    for ring_idx, ((angles, is_stimulus), r, s, ec, lw, mk) in enumerate(
            zip(all_ring_data, radii, sizes, edge_colors, linewidths, markers)):
        for c_idx in range(8):
            angle = angles[c_idx]

            # Render color
            if is_stimulus and use_stimulus_colors and ring_idx == 0:
                # Use actual experimental stimulus colors for ring 1
                rgb = stimulus_rgb(c_idx)
            else:
                # Render from CIELab at the given angle
                rgb = angle_to_rgb(angle)

            theta_rad = np.deg2rad(angle)
            ax.scatter([theta_rad], [r], s=s, color=rgb,
                       edgecolor=ec, linewidth=lw, zorder=5 + ring_idx,
                       marker=mk)

            # Color number label on inner ring
            if ring_idx == 0:
                # Use white or black text depending on brightness
                brightness = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
                txt_color = 'white' if brightness < 0.5 else 'black'
                ax.annotate(f'c{c_idx+1}', xy=(theta_rad, r), fontsize=5.5,
                            ha='center', va='center', color=txt_color,
                            fontweight='bold', zorder=15)

    # Ring labels at fixed angle
    label_angle_deg = 55
    for r, label in zip(radii, ring_names):
        ax.annotate(label, xy=(np.deg2rad(label_angle_deg), r),
                    fontsize=5.5, ha='center', va='bottom',
                    color='gray', alpha=0.65, style='italic')

    ax.set_title(title, fontsize=11, fontweight='bold', pad=18)

    # Subject label in center
    ax.text(0, 0.15, subject_label, transform=ax.transAxes,
            fontsize=9, ha='center', va='center', color='#333',
            fontweight='bold')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    preimage_dir = _PIPELINE_DIR / 'results' / 'fits' / 'preimage'
    fig_dir = preimage_dir / 'figures'
    fig_dir.mkdir(parents=True, exist_ok=True)

    # --- Load data ---
    # Sub-08 (R+C, deutan)
    with open(preimage_dir / 'sub-08_V4_rc_opponent_preimage.json') as f:
        d08 = json.load(f)

    # Sub-09 (Machado, protan) — separation-optimized
    sep_path = preimage_dir / 'sub-09_V4_machado_1way_separation.json'
    pre_path = preimage_dir / 'sub-09_V4_machado_1way_preimage.json'
    if sep_path.exists():
        with open(sep_path) as f:
            d09 = json.load(f)
        d09_type = 'separation'
    else:
        with open(pre_path) as f:
            d09 = json.load(f)
        d09_type = 'preimage'

    # Sub-10 (normal, identity)
    with open(preimage_dir / 'sub-10_V4_machado_1way_preimage.json') as f:
        d10 = json.load(f)

    # --- Organize ring data ---
    # Healthy target (opponent angles of 8 colors under normal vision)
    healthy_target = np.array(d08['target_angles_opponent'])

    # Sub-08
    s08_original = CIELAB_ANGLES.copy()
    s08_perceived = np.array(d08['forward_model_at_original']['perceived'])
    s08_modified = np.array(d08['preimage_angles'])
    s08_expected = np.array(d08['perceived_angles'])

    # Sub-09
    s09_original = CIELAB_ANGLES.copy()
    s09_perceived = np.array(d09.get('forward_model_landscape', d09.get('forward_model_at_original', {}))
                              .get('perceived_at_original',
                                   d09.get('forward_model_at_original', {}).get('perceived', [])))
    if len(s09_perceived) == 0:
        # Fallback: from the preimage JSON
        with open(pre_path) as f:
            d09_pre = json.load(f)
        s09_perceived = np.array(d09_pre['forward_model_at_original']['perceived'])

    s09_modified = np.array(d09['final_theta_in'] if 'final_theta_in' in d09
                            else d09['preimage_angles'])
    s09_expected = np.array(d09['final_perceived'] if 'final_perceived' in d09
                            else d09['perceived_angles'])

    # Sub-10
    s10_original = CIELAB_ANGLES.copy()
    s10_perceived = np.array(d10['forward_model_at_original']['perceived'])
    s10_modified = np.array(d10['preimage_angles'])
    s10_expected = np.array(d10['perceived_angles'])

    # ===== Figure 1: 1×3 color wheels =====
    fig, axes = plt.subplots(1, 3, figsize=(18, 6.5),
                              subplot_kw={'projection': 'polar'})

    draw_4ring_wheel(
        axes[0], s08_original, s08_perceived, s08_modified, s08_expected,
        'Sub-08 (Deutan)\nR+C Pre-Image', 'sub-08'
    )
    draw_4ring_wheel(
        axes[1], s09_original, s09_perceived, s09_modified, s09_expected,
        f'Sub-09 (Protan)\nSeparation Optimized' if d09_type == 'separation'
        else 'Sub-09 (Protan)\nPre-Image',
        'sub-09'
    )
    draw_4ring_wheel(
        axes[2], s10_original, s10_perceived, s10_modified, s10_expected,
        'Sub-10 (Normal)\nIdentity Filter', 'sub-10'
    )

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
               markeredgecolor='black', markersize=10, linewidth=0,
               label='Ring 1 (inner): Original Stimulus'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor='gray',
               markeredgecolor='#555', markersize=9, linewidth=0,
               label='Ring 2: CVD Perceived (unfiltered)'),
        Line2D([0], [0], marker='D', color='w', markerfacecolor='gray',
               markeredgecolor='navy', markersize=9, linewidth=0,
               label='Ring 3: Modified Stimulus (filter input)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
               markeredgecolor='black', markersize=10, linewidth=0,
               label='Ring 4 (outer): Expected CVD Perception'),
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=2,
               fontsize=9, frameon=True, fancybox=True,
               bbox_to_anchor=(0.5, -0.02))

    fig.suptitle('Pre-Image Filter: 4-Ring Color Wheel\n'
                 '(Inner → Outer: Original → Perceived → Modified → Expected)',
                 fontsize=13, fontweight='bold', y=1.02)

    plt.tight_layout()
    out_path = fig_dir / 'four_ring_color_wheel_all_subjects.png'
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_path}")

    # ===== Figure 2: Angle comparison bar chart =====
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    for ax, subj, orig, perc, mod, exp, label in [
        (axes[0], '08', s08_original, s08_perceived, s08_modified, s08_expected,
         'Sub-08 (Deutan, R+C)'),
        (axes[1], '09', s09_original, s09_perceived, s09_modified, s09_expected,
         'Sub-09 (Protan, Separation)'),
        (axes[2], '10', s10_original, s10_perceived, s10_modified, s10_expected,
         'Sub-10 (Normal, Identity)'),
    ]:
        x = np.arange(8)
        width = 0.20

        # Plot bars
        bars1 = ax.bar(x - 1.5*width, orig, width, label='Original (CIELab)',
                        color='steelblue', alpha=0.8)
        bars2 = ax.bar(x - 0.5*width, perc, width, label='CVD Perceived',
                        color='salmon', alpha=0.8)
        bars3 = ax.bar(x + 0.5*width, mod, width, label='Modified (filter)',
                        color='seagreen', alpha=0.8)
        bars4 = ax.bar(x + 1.5*width, exp, width, label='Expected after filter',
                        color='mediumpurple', alpha=0.8)

        # Healthy targets as horizontal lines
        for c_idx in range(8):
            ax.hlines(healthy_target[c_idx], c_idx - 2*width, c_idx + 2*width,
                      colors='gold', linewidths=2, linestyles='--', zorder=5)

        ax.set_xticks(x)
        ax.set_xticklabels([f'c{i+1}\n{n}' for i, n in enumerate(COLOR_NAMES)],
                           fontsize=7)
        ax.set_ylabel('Hue Angle (°)', fontsize=9)
        ax.set_title(label, fontsize=10, fontweight='bold')
        ax.set_ylim(0, 370)
        ax.axhline(360, color='lightgray', linestyle=':', alpha=0.5)

        if ax == axes[0]:
            ax.legend(fontsize=7, loc='upper right')

    # Add gold dashed line to legend
    from matplotlib.lines import Line2D
    gold_line = Line2D([0], [0], color='gold', linewidth=2, linestyle='--',
                       label='HC target (opponent)')
    axes[0].legend(handles=axes[0].get_legend_handles_labels()[1]
                   if False else list(axes[0].get_legend().legend_handles) + [gold_line],
                   fontsize=6.5, loc='upper right')

    fig.suptitle('Hue Angle Comparison: Original → Perceived → Modified → Expected',
                 fontsize=12, fontweight='bold')
    plt.tight_layout()
    out_path2 = fig_dir / 'four_condition_angle_comparison.png'
    plt.savefig(out_path2, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_path2}")

    # ===== Figure 3: Detailed sub-09 landscape showing D(θ) compression =====
    # Show the forward model D mapping to illustrate the 96° arc
    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    # Dense forward model map for sub-09
    theta_in = np.arange(0, 360, 0.5)
    # We don't have the forward model here, so use the separation JSON data
    if 'forward_model_landscape' in d09:
        fml = d09['forward_model_landscape']
        # The JSON has min/max perceived, but not the dense map
        # Let's plot the key data points instead

        # Original 8 stimuli → perceived
        ax.scatter(s09_original, s09_perceived, s=120, c='salmon',
                   edgecolor='black', linewidth=1.5, zorder=5,
                   label='Original → CVD Perceived (unfiltered)')

        # Modified (separation) → expected
        ax.scatter(s09_modified, s09_expected, s=120, c='seagreen',
                   edgecolor='black', linewidth=1.5, zorder=5, marker='D',
                   label='Modified → CVD Expected (filtered)')

        # Healthy targets
        ax.scatter(s08_original, healthy_target, s=80, c='gold',
                   edgecolor='black', linewidth=1.0, zorder=4, marker='*',
                   label='HC targets (at original CIELab)')

        # Identity line for reference
        ax.plot([0, 360], [0, 360], 'k--', alpha=0.2, label='Identity (no distortion)')

        # Shade the achievable arc
        p_min = fml['min_perceived']
        p_max = fml['max_perceived']
        ax.axhspan(p_min, p_max, alpha=0.08, color='blue',
                   label=f'Achievable arc: {p_min:.0f}°–{p_max:.0f}° ({p_max-p_min:.0f}°)')

        # Annotate merged colors
        for c_idx in [3, 4, 5, 6]:
            ax.annotate(f'c{c_idx+1}({COLOR_NAMES[c_idx]})',
                        xy=(s09_original[c_idx], s09_perceived[c_idx]),
                        xytext=(s09_original[c_idx]+15, s09_perceived[c_idx]-8),
                        fontsize=7, color='red',
                        arrowprops=dict(arrowstyle='->', color='red', lw=0.8))

    ax.set_xlabel('CIELab Input Angle (°)', fontsize=11)
    ax.set_ylabel('Opponent Perceived Angle (°)', fontsize=11)
    ax.set_title('Sub-09 Protan (Δλ=13.5nm): Forward Model D Compression\n'
                 '360° CIELab → ~96° Opponent Space', fontsize=12, fontweight='bold')
    ax.legend(fontsize=8, loc='upper left')
    ax.set_xlim(-5, 365)
    ax.set_ylim(-5, 365)
    ax.set_aspect('equal')
    ax.grid(alpha=0.2)

    plt.tight_layout()
    out_path3 = fig_dir / 'sub09_forward_model_compression.png'
    plt.savefig(out_path3, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_path3}")

    # ===== Summary table to stdout =====
    print("\n" + "="*80)
    print("SUMMARY: Per-Color Angles (degrees)")
    print("="*80)

    for subj, orig, perc, mod, exp, label in [
        ('08', s08_original, s08_perceived, s08_modified, s08_expected, 'Sub-08 Deutan'),
        ('09', s09_original, s09_perceived, s09_modified, s09_expected, 'Sub-09 Protan'),
        ('10', s10_original, s10_perceived, s10_modified, s10_expected, 'Sub-10 Normal'),
    ]:
        print(f"\n--- {label} ---")
        print(f"{'Color':<10} {'Original':>10} {'Perceived':>10} {'Modified':>10} {'Expected':>10} {'HC Target':>10}")
        for i in range(8):
            print(f"c{i+1} {COLOR_NAMES[i]:<7} {orig[i]:10.1f} {perc[i]:10.1f} "
                  f"{mod[i]:10.1f} {exp[i]:10.1f} {healthy_target[i]:10.1f}")


if __name__ == '__main__':
    main()
