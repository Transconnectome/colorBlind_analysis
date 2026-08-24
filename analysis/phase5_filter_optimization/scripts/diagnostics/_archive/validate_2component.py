#!/usr/bin/env python3
"""
validate_2component.py — Validation of 2-Component Angular Dilation model.

Tasks:
  (1) Metric comparison summary from existing JSON results
  (2) Color visualization: original → warped → filter-corrected swatches + wheel
  (3) Machado simulator filter validation with severity sweep
  (4) R+C model comparison for filter validation

Reads results from results/2component_stockman/*.json (corrected Stockman baseline).

Usage:
    conda activate srm
    python scripts/validate_2component.py --output_dir results/diagnostics/filter_validation_2comp_vs_rc
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR.parent))

_FWD_DIR = str(_SCRIPT_DIR.parent.parent.parent / 'phase4_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from machado_simulator import machado_shifted_hue
from visualize_cone_shift_colors import (
    lab2rgb, get_stim_rgb, STIM_LAB_ARR, STIM_L, STIM_A, STIM_B,
    STIM_CHROMA, STIM_HUE_DEG, HUE_ANGLES_DEG,
)
from retinal_cortical import machado_with_opponent_gain, get_design_matrix_rc
from stockman_cone_shift import COLOR_NAMES

# ===========================================================================
# Constants
# ===========================================================================
RESULTS_DIR = _SCRIPT_DIR.parent.parent / 'results' / '2component_stockman'
CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
CONF_AXIS = {'protan': 16.0, 'deutan': 150.0, 'normal': 83.0}
COLOR_HEX = {
    'color_1': '#FF4444', 'color_2': '#FF8800', 'color_3': '#BBBB00',
    'color_4': '#00CC44', 'color_5': '#00BBAA', 'color_6': '#4488CC',
    'color_7': '#8844DD', 'color_8': '#DD44BB',
}


def load_results(subj_id):
    """Load existing JSON results for a subject."""
    p = RESULTS_DIR / f'sub-{subj_id}_2component_results.json'
    if not p.exists():
        raise FileNotFoundError(f'Missing: {p}')
    with open(p) as f:
        return json.load(f)


# ===========================================================================
# (1) Metric Comparison Summary
# ===========================================================================

def metric_comparison_table(subjects=('08', '09', '10')):
    """Compile cross-metric comparison from existing JSON results."""
    rows = []
    for subj in subjects:
        try:
            data = load_results(subj)
        except FileNotFoundError:
            continue
        cvd = data['cvd_type']
        for roi in ['V1', 'V2']:
            if roi not in data:
                continue
            d = data[roi]
            # 4 metric combos
            combos = [
                ('Corr+Cos', d['grid_correlation']['best_cosine'],
                 d['perm_correlation_cosine']['perm_p_cosine']),
                ('Corr+WUC', d['grid_correlation']['best_wuc'],
                 d['perm_correlation_cosine']['perm_p_wuc']),  # evaluated at cos-optimal
                ('Xnobis+Cos', d['grid_crossnobis']['best_cosine'],
                 d['perm_crossnobis_cosine']['perm_p_cosine']),
                ('Xnobis+WUC', d['grid_crossnobis']['best_wuc'],
                 d['perm_crossnobis_cosine']['perm_p_wuc']),  # evaluated at cos-optimal
            ]
            for name, grid, perm_p in combos:
                boundary = (abs(grid['beta_s']) >= 49 or abs(grid['beta_c']) >= 49)
                rows.append({
                    'subject': f'sub-{subj}',
                    'cvd_type': cvd,
                    'roi': roi,
                    'metric': name,
                    'beta_s': grid['beta_s'],
                    'beta_c': grid['beta_c'],
                    'effect': grid['value'],
                    'perm_p': perm_p,
                    'boundary': boundary,
                })
    return rows


def print_metric_table(rows, output_path=None):
    """Print formatted metric comparison and optionally save."""
    lines = []
    lines.append('=' * 100)
    lines.append('METRIC COMPARISON: 2-Component Angular Dilation Model')
    lines.append('=' * 100)
    lines.append(f"{'Subject':<8} {'CVD':<7} {'ROI':<4} {'Metric':<13} "
                 f"{'β_s':>5} {'β_c':>5} {'Effect':>7} {'p':>8} {'Sig':>5} {'Bnd':>4}")
    lines.append('-' * 100)

    for r in rows:
        sig = '***' if r['perm_p'] < 0.01 else ('*' if r['perm_p'] < 0.05 else
              ('†' if r['perm_p'] < 0.10 else 'NS'))
        bnd = '!' if r['boundary'] else ''
        lines.append(f"{r['subject']:<8} {r['cvd_type']:<7} {r['roi']:<4} "
                     f"{r['metric']:<13} {r['beta_s']:5.0f} {r['beta_c']:5.0f} "
                     f"{r['effect']:7.3f} {r['perm_p']:8.4f} {sig:>5} {bnd:>4}")

    # Summary observations
    lines.append('')
    lines.append('KEY OBSERVATIONS:')

    # Best per subject+ROI
    from collections import defaultdict
    best = defaultdict(lambda: None)
    for r in rows:
        key = (r['subject'], r['roi'])
        if best[key] is None or r['perm_p'] < best[key]['perm_p']:
            best[key] = r
    lines.append('')
    lines.append('Best metric per subject × ROI (lowest p):')
    for key in sorted(best.keys()):
        r = best[key]
        if r is not None:
            sig = '*' if r['perm_p'] < 0.05 else ('†' if r['perm_p'] < 0.10 else 'NS')
            lines.append(f"  {r['subject']} {r['roi']}: {r['metric']} "
                         f"β_s={r['beta_s']:.0f}° β_c={r['beta_c']:.0f}° "
                         f"effect={r['effect']:.3f} p={r['perm_p']:.4f} {sig}")

    text = '\n'.join(lines)
    print(text)
    if output_path:
        with open(output_path, 'w') as f:
            f.write(text)
    return text


# ===========================================================================
# (2) Color Visualization
# ===========================================================================

def compute_warped_hue(delta_theta_deg):
    """Apply delta_theta to CIELab hue angles → warped CIELab colors."""
    # Use actual CIELab hue angles (not idealized 0,45,...,315)
    new_hue_rad = np.deg2rad(STIM_HUE_DEG + np.asarray(delta_theta_deg))
    new_a = STIM_CHROMA * np.cos(new_hue_rad)
    new_b = STIM_CHROMA * np.sin(new_hue_rad)
    return lab2rgb(STIM_L, new_a, new_b)


def plot_color_swatches_2comp(output_dir, subjects=('08', '09')):
    """Color swatches: Original → CVD-warped → Filter-corrected."""
    orig_rgb = get_stim_rgb()
    panels = []

    for subj in subjects:
        try:
            data = load_results(subj)
        except FileNotFoundError:
            continue
        delta_theta = np.array(data['delta_theta_deg'])
        cvd = data['cvd_type']
        # Use V1 correlation+cosine results as primary
        v1 = data.get('V1', {})
        corr_cos = v1.get('grid_correlation', {}).get('best_cosine', {})
        perm = v1.get('perm_correlation_cosine', {})
        panels.append({
            'subj': subj,
            'cvd': cvd,
            'delta_theta': delta_theta,
            'beta_s': corr_cos.get('beta_s', 0),
            'beta_c': corr_cos.get('beta_c', 0),
            'cosine': corr_cos.get('value', 0),
            'perm_p': perm.get('perm_p_cosine', 1.0),
        })

    if not panels:
        print('  [SKIP] No data for swatches.')
        return

    n_panels = len(panels)
    fig, axes = plt.subplots(3 * n_panels + 1, 9,
                              figsize=(16, 3.0 * n_panels + 2.0),
                              gridspec_kw={'width_ratios': [2.0] + [1]*8,
                                           'hspace': 0.5, 'wspace': 0.08})

    # Row 0: Original stimuli
    ax = axes[0, 0]
    ax.text(0.5, 0.5, 'Original\n(Normal Vision)', ha='center', va='center',
            fontsize=9, fontweight='bold', transform=ax.transAxes)
    ax.set_facecolor('white')
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    for j in range(8):
        ax = axes[0, j+1]
        ax.set_facecolor(orig_rgb[j])
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(COLOR_NAMES[j], fontsize=8, fontweight='bold', pad=2)
        for sp in ax.spines.values():
            sp.set_linewidth(2); sp.set_color('#333')

    for pi, panel in enumerate(panels):
        dt = panel['delta_theta']
        warped_rgb = compute_warped_hue(dt)
        corrected_rgb = compute_warped_hue(-dt)
        sig = '*' if panel['perm_p'] < 0.05 else ('†' if panel['perm_p'] < 0.10 else '')

        row_info = [
            (f"sub-{panel['subj']} ({panel['cvd']})\n"
             f"CVD Neural Perception\n"
             f"β_s={panel['beta_s']:.0f}° β_c={panel['beta_c']:.0f}°\n"
             f"cos={panel['cosine']:.3f} p={panel['perm_p']:.3f}{sig}",
             warped_rgb, dt, '#D32F2F'),
            (f"Filter-Corrected\n(inverse Δθ applied)",
             corrected_rgb, -dt, '#1565C0'),
            (f"Original\n(reference)",
             orig_rgb, np.zeros(8), '#666666'),
        ]

        for ri, (label, rgb_arr, d_arr, accent) in enumerate(row_info):
            row = 1 + pi * 3 + ri
            ax_lab = axes[row, 0]
            ax_lab.text(0.5, 0.5, label, ha='center', va='center',
                        fontsize=7, color=accent, fontweight='bold',
                        transform=ax_lab.transAxes)
            ax_lab.set_facecolor('white')
            ax_lab.set_xticks([]); ax_lab.set_yticks([])
            for sp in ax_lab.spines.values():
                sp.set_visible(False)

            for j in range(8):
                ax = axes[row, j+1]
                ax.set_facecolor(np.clip(rgb_arr[j], 0, 1))
                ax.set_xticks([]); ax.set_yticks([])
                d = d_arr[j]
                if abs(d) > 0.5:
                    ax.text(0.5, -0.08, f'{d:+.1f}\u00B0',
                            ha='center', va='top', fontsize=6,
                            color=accent, transform=ax.transAxes)
                for sp in ax.spines.values():
                    sp.set_linewidth(1.5 if abs(d) <= 5 else 2.5)
                    sp.set_color(accent if abs(d) > 5 else '#999')

    fig.suptitle('2-Component Angular Dilation: Color Distortion & Filter',
                 fontsize=13, fontweight='bold', y=1.01)
    out = output_dir / 'color_swatches_2component.png'
    plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')


def plot_color_wheel_2comp(output_dir, subjects=('08', '09')):
    """Polar color wheel showing 2-component distortion."""
    orig_rgb = get_stim_rgb()
    n = len(subjects)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 6),
                              subplot_kw={'projection': 'polar'})
    if n == 1:
        axes = [axes]

    for idx, subj in enumerate(subjects):
        ax = axes[idx]
        try:
            data = load_results(subj)
        except FileNotFoundError:
            continue

        dt = np.array(data['delta_theta_deg'])
        hue_base = np.array(data['hue_base_deg'])
        cvd = data['cvd_type']

        # Background hue ring
        n_bg = 360
        bg_hues = np.linspace(0, 360, n_bg, endpoint=False)
        med_L = np.median(STIM_L)
        med_C = np.median(STIM_CHROMA)
        bg_a = med_C * np.cos(np.deg2rad(bg_hues))
        bg_b = med_C * np.sin(np.deg2rad(bg_hues))
        bg_rgb = lab2rgb(np.full(n_bg, med_L), bg_a, bg_b)
        for i in range(n_bg):
            ax.bar(np.deg2rad(bg_hues[i]), 0.25, width=np.deg2rad(1.2),
                   bottom=0.0, color=bg_rgb[i], alpha=0.2, edgecolor='none')

        # Reference circles
        ring_t = np.linspace(0, 2 * np.pi, 200)
        ax.plot(ring_t, np.full(200, 0.72), '-', color='#cccccc', lw=0.5)
        ax.plot(ring_t, np.full(200, 0.48), '-', color='#ffcccc', lw=0.5)

        # Confusion axis line
        theta_conf = CONF_AXIS[cvd]
        ax.plot([np.deg2rad(theta_conf), np.deg2rad(theta_conf + 180)],
                [0.3, 0.3], '--', color='red', alpha=0.3, lw=1.5)
        ax.text(np.deg2rad(theta_conf), 0.88,
                f'Conf. axis\n{theta_conf:.0f}°',
                ha='center', va='center', fontsize=6, color='red', alpha=0.5)

        # S-cone axis
        ax.plot([np.deg2rad(90), np.deg2rad(270)],
                [0.3, 0.3], '--', color='blue', alpha=0.3, lw=1.5)
        ax.text(np.deg2rad(90), 0.88, 'S-cone\n90°',
                ha='center', va='center', fontsize=6, color='blue', alpha=0.5)

        # Plot original and shifted positions (in Stockman space)
        for j in range(8):
            t_orig = np.deg2rad(hue_base[j])
            t_shift = np.deg2rad((hue_base[j] + dt[j]) % 360)

            ax.scatter(t_orig, 0.72, s=300, c=[orig_rgb[j]],
                       edgecolors='black', linewidths=1.5, zorder=5)
            warped_c = compute_warped_hue(dt)
            ax.scatter(t_shift, 0.48, s=200, c=[warped_c[j]],
                       edgecolors='red', linewidths=1.5, zorder=5, marker='D')

            if abs(dt[j]) > 2:
                ax.annotate('', xy=(t_shift, 0.54), xytext=(t_orig, 0.66),
                            arrowprops=dict(arrowstyle='->', color='red',
                                            lw=1.2, alpha=0.6,
                                            connectionstyle='arc3,rad=0.15'))
                # Label delta
                mid_t = np.deg2rad(hue_base[j] + dt[j]/2)
                ax.text(mid_t, 0.40, f'{dt[j]:+.1f}°',
                        ha='center', va='center', fontsize=5.5,
                        color='red', fontweight='bold')

        ax.set_theta_zero_location('E')
        ax.set_theta_direction(1)
        ax.set_ylim(0, 0.95)
        ax.set_yticks([])

        # Custom angle labels at Stockman hue positions
        ax.set_xticks(np.deg2rad(hue_base))
        ax.set_xticklabels([f'{COLOR_NAMES[j]}\n({hue_base[j]:.0f}°)'
                            for j in range(8)], fontsize=6)

        v1_cos = data.get('V1', {}).get('grid_correlation', {}).get('best_cosine', {})
        p_val = data.get('V1', {}).get('perm_correlation_cosine', {}).get('perm_p_cosine', 1.0)
        sig = '*' if p_val < 0.05 else ('†' if p_val < 0.10 else '')
        ax.set_title(f"sub-{subj} ({cvd})\n"
                     f"β_s={v1_cos.get('beta_s',0):.0f}°, "
                     f"β_c={v1_cos.get('beta_c',0):.0f}°, "
                     f"p={p_val:.3f}{sig}\n"
                     f"[Stockman opponent hue space]",
                     fontsize=9, fontweight='bold', pad=20)

    fig.suptitle('2-Component Color Wheel: Original (outer) → CVD-warped (inner)',
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    out = output_dir / 'color_wheel_2component.png'
    plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')


def plot_delta_theta_bars_2comp(output_dir, subjects=('08', '09')):
    """Per-color delta-theta bar chart for 2-component model."""
    orig_rgb = get_stim_rgb()
    n = len(subjects)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5), sharey=True)
    if n == 1:
        axes = [axes]

    for idx, subj in enumerate(subjects):
        ax = axes[idx]
        try:
            data = load_results(subj)
        except FileNotFoundError:
            continue

        dt = np.array(data['delta_theta_deg'])
        cvd = data['cvd_type']
        x = np.arange(8)

        bars = ax.bar(x, dt, color=[orig_rgb[j] for j in range(8)],
                       edgecolor='black', linewidth=0.8)
        for j, bar in enumerate(bars):
            if abs(dt[j]) > 15:
                bar.set_edgecolor('red')
                bar.set_linewidth(2.0)

        ax.axhline(0, color='gray', lw=0.8, ls=':')
        ax.set_xticks(x)
        ax.set_xticklabels(COLOR_NAMES, fontsize=8, rotation=45, ha='right')
        ax.set_ylabel(r'$\Delta\theta$ (deg)' if idx == 0 else '', fontsize=11)
        ax.grid(axis='y', alpha=0.2)

        # Annotate key CVD predictions
        if cvd == 'deutan':
            ax.annotate('S-cone\nexpansion', xy=(6, dt[6]),
                        xytext=(6.5, dt[6]+5), fontsize=7, color='blue',
                        arrowprops=dict(arrowstyle='->', color='blue', lw=0.8))
            ax.annotate('Confusion\ncompression', xy=(5, dt[5]),
                        xytext=(3.5, dt[5]-5), fontsize=7, color='red',
                        arrowprops=dict(arrowstyle='->', color='red', lw=0.8))
        elif cvd == 'protan':
            ax.annotate('S-cone\nexpansion', xy=(6, dt[6]),
                        xytext=(6.5, dt[6]+5), fontsize=7, color='blue',
                        arrowprops=dict(arrowstyle='->', color='blue', lw=0.8))

        v1_cos = data.get('V1', {}).get('grid_correlation', {}).get('best_cosine', {})
        p_val = data.get('V1', {}).get('perm_correlation_cosine', {}).get('perm_p_cosine', 1.0)
        sig = '*' if p_val < 0.05 else ('†' if p_val < 0.10 else '')
        ax.set_title(f"sub-{subj} ({cvd})\n"
                     f"β_s={v1_cos.get('beta_s',0):.0f}° β_c={v1_cos.get('beta_c',0):.0f}° "
                     f"V1 p={p_val:.3f}{sig}",
                     fontsize=10, fontweight='bold')

    fig.suptitle('2-Component Angular Dilation: Per-Color Hue Distortion',
                 fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    out = output_dir / 'delta_theta_bars_2component.png'
    plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')


def plot_continuous_distortion_2comp(output_dir, subjects=('08', '09')):
    """Continuous δθ(θ) showing the 2-component model curves."""
    orig_rgb = get_stim_rgb()
    fig, axes = plt.subplots(1, len(subjects), figsize=(7 * len(subjects), 5))
    if len(subjects) == 1:
        axes = [axes]

    theta_fine = np.linspace(0, 360, 361)

    for idx, subj in enumerate(subjects):
        ax = axes[idx]
        try:
            data = load_results(subj)
        except FileNotFoundError:
            continue

        cvd = data['cvd_type']
        hue_base = np.array(data['hue_base_deg'])
        dt = np.array(data['delta_theta_deg'])
        theta_conf = CONF_AXIS[cvd]

        # Get parameters for primary (V1 corr+cos)
        v1_cos = data.get('V1', {}).get('grid_correlation', {}).get('best_cosine', {})
        beta_s = v1_cos.get('beta_s', 0)
        beta_c = v1_cos.get('beta_c', 0)

        # Continuous model prediction
        dt_model = (beta_s * np.cos(np.radians(theta_fine - 90.0))
                    + beta_c * np.cos(np.radians(theta_fine - theta_conf)))

        # S-cone component alone
        dt_s = beta_s * np.cos(np.radians(theta_fine - 90.0))
        # Confusion component alone
        dt_c = beta_c * np.cos(np.radians(theta_fine - theta_conf))

        ax.fill_between(theta_fine, 0, dt_s, alpha=0.15, color='blue',
                        label=f'S-cone (β_s={beta_s:.0f}°)')
        ax.fill_between(theta_fine, 0, dt_c, alpha=0.15, color='red',
                        label=f'Confusion (β_c={beta_c:.0f}°)')
        ax.plot(theta_fine, dt_model, '-', color='black', lw=2.5,
                label='Combined model', zorder=10)

        # Plot actual data points at Stockman hue positions
        ax.scatter(hue_base, dt, s=120, c=[orig_rgb[j] for j in range(8)],
                   edgecolors='black', linewidths=1.5, zorder=15)

        # Mark axes
        ax.axhline(0, color='gray', lw=0.5, ls=':')
        ax.axvline(90, color='blue', alpha=0.3, lw=1, ls='--',
                   label='S-cone axis (90°)')
        ax.axvline(theta_conf, color='red', alpha=0.3, lw=1, ls='--',
                   label=f'Conf. axis ({theta_conf:.0f}°)')

        # Stimulus position markers
        for j in range(8):
            ax.axvline(hue_base[j], color=orig_rgb[j], alpha=0.3, lw=6)

        ax.set_xlabel('Stockman Opponent Hue Angle (deg)', fontsize=10)
        ax.set_ylabel(r'$\Delta\theta$ (deg)', fontsize=10)
        ax.set_xlim(0, 360)
        ax.legend(fontsize=7, loc='upper right')
        ax.grid(alpha=0.2)

        p_val = data.get('V1', {}).get('perm_correlation_cosine', {}).get('perm_p_cosine', 1.0)
        sig = '*' if p_val < 0.05 else ('†' if p_val < 0.10 else '')
        ax.set_title(f"sub-{subj} ({cvd}) — 2-Component Model\n"
                     f"V1 cos={v1_cos.get('value', 0):.3f} p={p_val:.3f}{sig}",
                     fontsize=10, fontweight='bold')

    fig.suptitle('2-Component Angular Dilation: Continuous Distortion Curve\n'
                 'Blue = S-cone expansion | Red = Confusion axis modulation',
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    out = output_dir / 'continuous_distortion_2component.png'
    plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')


# ===========================================================================
# (3) Machado Simulator Filter Validation
# ===========================================================================

def machado_simulate_perception(lab_colors, delta_lambda, cvd_type):
    """Simulate CVD perception of given CIELab colors via Machado.

    Returns hue angles (in Stockman opponent space) that a CVD observer
    would perceive for the given stimuli.
    """
    from stockman_cone_shift import lab_to_xyz, _compute_spectral_shift_lms, \
        lms_to_opponent, opponent_to_hue_angle, compute_xyz_to_lms_matrix
    from machado_simulator import machado_mixed_fundamentals, _load_stockman_grid

    wl, L, M, S, _, _, M_xyz2lms = _load_stockman_grid()
    xyz = lab_to_xyz(lab_colors)

    if delta_lambda == 0 or cvd_type == 'normal':
        lms = _compute_spectral_shift_lms(wl, L, M, S, M_xyz2lms, xyz)
    else:
        L_a, M_a, S_a = machado_mixed_fundamentals(delta_lambda, cvd_type, wl, L, M, S)
        lms = _compute_spectral_shift_lms(wl, L_a, M_a, S_a, M_xyz2lms, xyz)

    rg, by = lms_to_opponent(lms)
    return opponent_to_hue_angle(rg, by)


def apply_inverse_filter_cielab(delta_theta_deg):
    """Apply inverse 2-component filter in CIELab space.

    Shifts CIELab hue angles by -delta_theta to pre-compensate.
    Returns modified CIELab coordinates (8, 3).
    """
    filtered_hue_rad = np.deg2rad(STIM_HUE_DEG - np.asarray(delta_theta_deg))
    new_a = STIM_CHROMA * np.cos(filtered_hue_rad)
    new_b = STIM_CHROMA * np.sin(filtered_hue_rad)
    return np.column_stack([STIM_L, new_a, new_b])


def filter_validation_sweep(output_dir, subjects=('08', '09')):
    """Machado filter validation with severity sweep.

    For each CVD subject, test the 2-component filter against
    Machado-simulated CVD at multiple severity levels (Δλ).
    """
    results = {}
    dl_range = np.arange(0, 21, 2.0)  # 0 to 20 nm

    for subj in subjects:
        try:
            data = load_results(subj)
        except FileNotFoundError:
            continue

        dt = np.array(data['delta_theta_deg'])
        cvd = data['cvd_type']
        if cvd == 'normal':
            continue

        # Normal-vision hue angles (reference)
        hue_normal = machado_simulate_perception(STIM_LAB_ARR, 0.0, cvd)

        # Filtered stimuli (inverse 2-component warping in CIELab)
        filtered_lab = apply_inverse_filter_cielab(dt)

        sweep_results = []
        for dl in dl_range:
            # Unfiltered CVD perception
            hue_unfiltered = machado_simulate_perception(STIM_LAB_ARR, dl, cvd)
            err_unfiltered = np.abs((hue_unfiltered - hue_normal + 180) % 360 - 180)

            # Filtered CVD perception
            hue_filtered = machado_simulate_perception(filtered_lab, dl, cvd)
            err_filtered = np.abs((hue_filtered - hue_normal + 180) % 360 - 180)

            sweep_results.append({
                'delta_lambda': float(dl),
                'mean_err_unfiltered': float(np.mean(err_unfiltered)),
                'mean_err_filtered': float(np.mean(err_filtered)),
                'improvement_pct': float(
                    (np.mean(err_unfiltered) - np.mean(err_filtered))
                    / max(np.mean(err_unfiltered), 1e-8) * 100
                ) if np.mean(err_unfiltered) > 0 else 0.0,
                'per_color_err_unfiltered': err_unfiltered.tolist(),
                'per_color_err_filtered': err_filtered.tolist(),
            })

        results[subj] = {
            'cvd_type': cvd,
            'sweep': sweep_results,
        }

    # Plot
    fig, axes = plt.subplots(1, len(results), figsize=(7 * len(results), 5))
    if len(results) == 1:
        axes = [axes]

    for idx, (subj, res) in enumerate(sorted(results.items())):
        ax = axes[idx]
        dls = [s['delta_lambda'] for s in res['sweep']]
        err_uf = [s['mean_err_unfiltered'] for s in res['sweep']]
        err_f = [s['mean_err_filtered'] for s in res['sweep']]

        ax.plot(dls, err_uf, 'o-', color='red', lw=2, label='Unfiltered (CVD raw)')
        ax.plot(dls, err_f, 's-', color='blue', lw=2, label='Filtered (2-comp inverse)')
        ax.fill_between(dls, err_uf, err_f,
                        where=np.array(err_uf) > np.array(err_f),
                        alpha=0.2, color='green', label='Filter helps')
        ax.fill_between(dls, err_uf, err_f,
                        where=np.array(err_uf) <= np.array(err_f),
                        alpha=0.2, color='red', label='Filter hurts')

        ax.set_xlabel('Machado Δλ (nm)', fontsize=10)
        ax.set_ylabel('Mean Hue Error (deg)', fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.2)
        ax.set_title(f"sub-{subj} ({res['cvd_type']})\nMachado Filter Validation",
                     fontsize=10, fontweight='bold')

    fig.suptitle('2-Component Filter vs Machado CVD Simulator\n'
                 'Neural geometry filter applied to Machado-simulated perception',
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    out = output_dir / 'filter_validation_sweep.png'
    plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')

    # Save JSON
    out_json = output_dir / 'filter_validation_sweep.json'
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'  Saved: {out_json}')

    return results


# ===========================================================================
# (4) R+C Model Filter Comparison
# ===========================================================================

def rc_filter_validation(output_dir, subjects=('08', '09')):
    """Compare 2-component filter with R+C model filter via Machado.

    R+C model has mechanistic link to Machado (retinal Δλ + cortical g),
    so its filter should work better with the Machado simulator.
    """
    # Known R+C parameters from meeting notes
    rc_params = {
        '08': {'delta_lambda': 2.5, 'g': -2.25, 'cvd_type': 'deutan'},
        '09': {'delta_lambda': 19.5, 'g': -1.10, 'cvd_type': 'protan'},
    }

    results = {}
    for subj in subjects:
        if subj not in rc_params:
            continue
        p = rc_params[subj]
        cvd = p['cvd_type']

        # Normal-vision hue angles
        hue_normal = machado_simulate_perception(STIM_LAB_ARR, 0.0, cvd)

        # R+C model prediction: get the delta_theta from R+C
        _, hue_rc, dt_rc = machado_with_opponent_gain(
            p['delta_lambda'], p['g'], cvd)
        hue_base_rc, _, _ = machado_shifted_hue(0.0, cvd)

        # 2-component delta_theta
        try:
            data = load_results(subj)
            dt_2comp = np.array(data['delta_theta_deg'])
        except FileNotFoundError:
            continue

        # Apply both filters and compare
        filtered_2comp = apply_inverse_filter_cielab(dt_2comp)
        filtered_rc = apply_inverse_filter_cielab(dt_rc)

        # Severity sweep for both
        dl_range = np.arange(0, 21, 2.0)
        sweep = []
        for dl in dl_range:
            hue_uf = machado_simulate_perception(STIM_LAB_ARR, dl, cvd)
            hue_f_2c = machado_simulate_perception(filtered_2comp, dl, cvd)
            hue_f_rc = machado_simulate_perception(filtered_rc, dl, cvd)

            err_uf = np.abs((hue_uf - hue_normal + 180) % 360 - 180)
            err_2c = np.abs((hue_f_2c - hue_normal + 180) % 360 - 180)
            err_rc = np.abs((hue_f_rc - hue_normal + 180) % 360 - 180)

            sweep.append({
                'delta_lambda': float(dl),
                'err_unfiltered': float(np.mean(err_uf)),
                'err_2component': float(np.mean(err_2c)),
                'err_rc': float(np.mean(err_rc)),
            })

        results[subj] = {
            'cvd_type': cvd,
            'rc_params': p,
            'dt_2comp': dt_2comp.tolist(),
            'dt_rc': dt_rc.tolist(),
            'sweep': sweep,
        }

    if not results:
        print('  [SKIP] No R+C data available.')
        return results

    # Plot comparison
    fig, axes = plt.subplots(1, len(results), figsize=(7 * len(results), 5))
    if len(results) == 1:
        axes = [axes]

    for idx, (subj, res) in enumerate(sorted(results.items())):
        ax = axes[idx]
        dls = [s['delta_lambda'] for s in res['sweep']]
        err_uf = [s['err_unfiltered'] for s in res['sweep']]
        err_2c = [s['err_2component'] for s in res['sweep']]
        err_rc = [s['err_rc'] for s in res['sweep']]

        ax.plot(dls, err_uf, 'o-', color='red', lw=2, label='Unfiltered')
        ax.plot(dls, err_2c, 's-', color='blue', lw=2, label='2-Component filter')
        ax.plot(dls, err_rc, 'D-', color='green', lw=2, label='R+C filter')

        # Mark the R+C model's own Δλ
        rc_dl = res['rc_params']['delta_lambda']
        ax.axvline(rc_dl, color='green', alpha=0.3, lw=2, ls='--')
        ax.text(rc_dl + 0.3, ax.get_ylim()[1] * 0.9,
                f"R+C Δλ={rc_dl}nm\ng={res['rc_params']['g']}",
                fontsize=7, color='green')

        ax.set_xlabel('Machado Simulator Δλ (nm)', fontsize=10)
        ax.set_ylabel('Mean Hue Error (deg)', fontsize=10)
        ax.legend(fontsize=8)
        ax.grid(alpha=0.2)
        ax.set_title(f"sub-{subj} ({res['cvd_type']})\n2-Component vs R+C Filter",
                     fontsize=10, fontweight='bold')

    fig.suptitle('Filter Comparison: 2-Component vs R+C via Machado Simulator',
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    out = output_dir / 'filter_comparison_2comp_vs_rc.png'
    plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')

    out_json = output_dir / 'filter_comparison.json'
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=2)
    print(f'  Saved: {out_json}')

    return results


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Validation of 2-Component Angular Dilation model')
    parser.add_argument('--output_dir', type=str,
                        default='results/diagnostics/filter_validation_2comp_vs_rc')
    parser.add_argument('--subjects', nargs='+', default=['08', '09', '10'])
    args = parser.parse_args()

    output_dir = _SCRIPT_DIR.parent / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 70)
    print('2-Component Angular Dilation: Validation Suite')
    print(f'Timestamp: {datetime.now().isoformat()}')
    print(f'Output: {output_dir}')
    print('=' * 70)

    # (1) Metric comparison
    print('\n[1] Metric Comparison Summary')
    print('-' * 50)
    rows = metric_comparison_table(args.subjects)
    print_metric_table(rows, output_dir / 'metric_comparison.txt')

    # (2) Color visualization
    cvd_subjects = [s for s in args.subjects if s != '10']
    print('\n[2] Color Visualization')
    print('-' * 50)
    print('  [2a] Color swatches...')
    plot_color_swatches_2comp(output_dir, cvd_subjects)
    print('  [2b] Color wheel...')
    plot_color_wheel_2comp(output_dir, cvd_subjects)
    print('  [2c] Delta-theta bars...')
    plot_delta_theta_bars_2comp(output_dir, cvd_subjects)
    print('  [2d] Continuous distortion...')
    plot_continuous_distortion_2comp(output_dir, cvd_subjects)

    # (3) Machado filter validation
    print('\n[3] Machado Simulator Filter Validation')
    print('-' * 50)
    filter_results = filter_validation_sweep(output_dir, cvd_subjects)

    # Print summary
    for subj, res in filter_results.items():
        print(f"\n  sub-{subj} ({res['cvd_type']}):")
        print(f"  {'Δλ':>5} {'Unfilt':>8} {'Filt':>8} {'Improv':>8}")
        for s in res['sweep']:
            dl = s['delta_lambda']
            uf = s['mean_err_unfiltered']
            f = s['mean_err_filtered']
            imp = s['improvement_pct']
            marker = '<--' if imp > 0 else ''
            print(f"  {dl:5.0f} {uf:8.1f}° {f:8.1f}° {imp:+7.1f}% {marker}")

    # (4) R+C comparison
    print('\n[4] R+C Model Filter Comparison')
    print('-' * 50)
    rc_results = rc_filter_validation(output_dir, cvd_subjects)

    if rc_results:
        for subj, res in rc_results.items():
            print(f"\n  sub-{subj} ({res['cvd_type']}):")
            print(f"  R+C: Δλ={res['rc_params']['delta_lambda']}nm, "
                  f"g={res['rc_params']['g']}")
            print(f"  {'Δλ':>5} {'Unfilt':>8} {'2-Comp':>8} {'R+C':>8}")
            for s in res['sweep']:
                dl = s['delta_lambda']
                print(f"  {dl:5.0f} {s['err_unfiltered']:8.1f}° "
                      f"{s['err_2component']:8.1f}° {s['err_rc']:8.1f}°")

    print('\n' + '=' * 70)
    print(f'All outputs saved to: {output_dir}')
    print('=' * 70)


if __name__ == '__main__':
    main()
