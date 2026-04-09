#!/usr/bin/env python3
"""
visualize_delta_rdm_sim.py — ΔRDM simulation results visualization.

Visualizes Phase A (ΔRDM fit) + Phase C (LOCO match) results from
the ΔRDM simulation pipeline (run_sim.py / diagnostic_delta_rdm.py).

Figures:
  Fig 1: Polar distortion |δθ| across ROIs (ΔRDM cosine metric)
  Fig 2: Per-color δθ bars (significant + trending results)
  Fig 3: Continuous distortion curve δθ(θ)

Usage:
    conda activate srm
    python scripts/visualize_delta_rdm_sim.py [--output_dir figures/delta_rdm]
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path
from scipy.interpolate import CubicSpline
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
_FWD_DIR = str(_SCRIPT_DIR.parent.parent.parent / 'future_phase1_forward_model' / 'scripts')
if _FWD_DIR not in sys.path:
    sys.path.insert(0, _FWD_DIR)
sys.path.insert(0, str(_SCRIPT_DIR))

from stockman_cone_shift import COLOR_NAMES, HUE_ANGLES_DEG
from utils_cone_3way import compute_shifted_hue_3way, compute_1way_hue_shift

# ============================================================================
# Idealized stimulus colors (L*=75, chroma=40)
# ============================================================================
_L_STAR = 75.0
_CHROMA = 40.0
_M_XYZ_TO_SRGB = np.array([
    [3.2406, -1.5372, -0.4986],
    [-0.9689,  1.8758,  0.0415],
    [0.0557, -0.2040,  1.0570],
])


def lab2rgb(L, a, b):
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


def get_stim_rgb():
    hue_rad = np.deg2rad(HUE_ANGLES_DEG)
    a = _CHROMA * np.cos(hue_rad)
    b = _CHROMA * np.sin(hue_rad)
    return lab2rgb(np.full(8, _L_STAR), a, b)


RESULTS_BASE = _SCRIPT_DIR.parent / 'results'
SIM_DIR = RESULTS_BASE / 'sim'
CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}

# Which sim results to load (from RESULTS_SIM.md, cosine metric)
SIM_CONFIGS = [
    ('09', 'V2', 'cone_1way', 'cosine'),
    ('09', 'V2', 'cone_3way', 'cosine'),
    ('08', 'V1', 'fourier', 'cosine'),
    ('08', 'V2', 'fourier', 'cosine'),
    ('09', 'V1', 'cone_1way', 'cosine'),
    ('08', 'V1', 'cone_1way', 'cosine'),
    ('08', 'V2', 'cone_1way', 'cosine'),
]


# ============================================================================
# Load results
# ============================================================================

def load_sim_results():
    """Load validated simulation results from results/sim/."""
    results = {}
    for subj, roi, model, metric in SIM_CONFIGS:
        dirname = f'sub-{subj}_{roi}_{model}_{metric}'
        result_path = SIM_DIR / dirname / 'result.json'
        if not result_path.exists():
            print(f'  [WARN] Missing: {result_path}')
            continue

        with open(result_path) as f:
            data = json.load(f)

        pa = data['phase_a']
        pc = data['phase_c']

        pa_sig = pa.get('significant', False) and pa['perm_p'] < 0.05
        pc_perm_p = pc['loco_match']['perm_p']
        pc_rho = pc['loco_match']['spearman_rho']

        if pa_sig and pc_perm_p < 0.05:
            sig_level = 'significant'
        elif pa_sig and pc_perm_p < 0.10:
            sig_level = 'trending'
        else:
            sig_level = 'ns'

        key = (subj, roi, model, metric)
        results[key] = {
            'subj': subj, 'roi': roi, 'model': model, 'metric': metric,
            'cvd_type': CVD_TYPE[subj],
            'params': pa['best_params'],
            'delta_theta_deg': np.array(pa['delta_theta_deg']),
            'rdm_r': pa['best_pearson_r'],
            'rdm_p': pa['perm_p'],
            'loco_rho': pc_rho,
            'loco_p': pc_perm_p,
            'worst3_syn': pc['loco_match'].get('worst3_synthetic', []),
            'worst3_obs': pc['loco_match'].get('worst3_observed', []),
            'worst3_overlap': pc['loco_match'].get('worst3_overlap', 0),
            'sig_level': sig_level,
        }

    return results


def get_best_per_roi(sim_results):
    """Select best model per (subject, roi)."""
    best = {}
    rank = {'significant': 0, 'trending': 1, 'ns': 2}
    df_map = {'cone_1way': 1, 'cone_3way': 3, 'fourier': 4}

    for key, res in sim_results.items():
        subj, roi = res['subj'], res['roi']
        sr_key = (subj, roi)
        if sr_key not in best:
            best[sr_key] = res
        else:
            cur = best[sr_key]
            cur_rank = rank[cur['sig_level']]
            new_rank = rank[res['sig_level']]
            if (new_rank < cur_rank or
                (new_rank == cur_rank and
                 df_map.get(res['model'], 99) < df_map.get(cur['model'], 99)) or
                (new_rank == cur_rank and
                 df_map.get(res['model'], 99) == df_map.get(cur['model'], 99) and
                 res['loco_rho'] > cur['loco_rho'])):
                best[sr_key] = res
    return best


# ============================================================================
# Fig 1: Polar Distortion Profile
# ============================================================================

def plot_polar_distortion(output_dir, best_per_roi):
    """Polar radar of |delta_theta| per color across ROIs (ΔRDM only)."""
    stim_rgb = get_stim_rgb()
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5),
                              subplot_kw={'projection': 'polar'})

    roi_colors = {'V1': '#2196F3', 'V2': '#4CAF50'}
    roi_styles = {'V1': '-', 'V2': '--'}
    theta_base = np.deg2rad(HUE_ANGLES_DEG)
    theta_plot = np.append(theta_base, theta_base[0])

    for ax_idx, subj in enumerate(['08', '09']):
        ax = axes[ax_idx]
        cvd_type = CVD_TYPE[subj]

        for j in range(8):
            ax.scatter(theta_base[j], 0, s=120, c=[stim_rgb[j]],
                       edgecolors='black', linewidths=0.8, zorder=10, clip_on=False)

        for roi in ['V1', 'V2']:
            res = best_per_roi.get((subj, roi))
            if res is None:
                continue
            delta = res['delta_theta_deg']
            model = res['model']
            rho = res['loco_rho']
            p = res['loco_p']

            mag = np.abs(delta)
            mag_plot = np.append(mag, mag[0])
            sig_sym = '*' if p < 0.05 else ('\u2020' if p < 0.10 else '')
            label = f'{roi} ({model[:7]}) ' + r'$\rho$' + f'={rho:.2f}{sig_sym}'
            alpha = 0.9 if p < 0.05 else (0.6 if p < 0.10 else 0.3)
            ax.plot(theta_plot, mag_plot, roi_styles.get(roi, '-'),
                    color=roi_colors.get(roi, 'gray'), linewidth=2,
                    label=label, alpha=alpha)
            ax.fill(theta_plot, mag_plot, alpha=0.06,
                    color=roi_colors.get(roi, 'gray'))

        ax.set_theta_zero_location('E')
        ax.set_theta_direction(1)
        ax.set_xticks(theta_base)
        ax.set_xticklabels(COLOR_NAMES, fontsize=7)
        ax.set_title(f'sub-{subj} ({cvd_type})', fontsize=11,
                      fontweight='bold', pad=15)
        ax.legend(loc='upper right', fontsize=7, bbox_to_anchor=(1.35, 1.15))

    fig.suptitle('ΔRDM Hue Distortion |' + r'$\delta\theta$' +
                  '| by ROI (cosine metric)',
                  fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'polar_distortion_delta_rdm.png', dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {output_dir / "polar_distortion_delta_rdm.png"}')


# ============================================================================
# Fig 2: Delta-theta Bar Chart
# ============================================================================

def plot_delta_theta_bars(output_dir, sim_results):
    """Bar chart of per-color delta_theta for validated results."""
    stim_rgb = get_stim_rgb()

    panels = [res for res in sim_results.values()
              if res['sig_level'] in ('significant', 'trending')]

    panels.sort(key=lambda x: (0 if x['sig_level'] == 'significant' else 1,
                                 x['subj'], x['roi']))

    if not panels:
        print('  [SKIP] No significant/trending results.')
        return

    n = len(panels)
    fig, axes = plt.subplots(1, n, figsize=(3.5 * n, 4.5), sharey=True)
    if n == 1:
        axes = [axes]
    x = np.arange(8)

    for idx, res in enumerate(panels):
        ax = axes[idx]
        delta = res['delta_theta_deg']
        bars = ax.bar(x, delta,
                       color=[stim_rgb[j] for j in range(8)],
                       edgecolor='black', linewidth=0.8)
        for j, bar in enumerate(bars):
            if abs(delta[j]) > 10:
                bar.set_edgecolor('red'); bar.set_linewidth(2)

        ax.axhline(0, color='gray', lw=0.8)
        ax.set_xticks(x)
        ax.set_xticklabels(COLOR_NAMES, fontsize=7, rotation=45, ha='right')
        ax.set_ylabel(r'$\delta\theta$ (deg)' if idx == 0 else '', fontsize=10)

        sig_sym = '*' if res['sig_level'] == 'significant' else '\u2020'
        rho = res['loco_rho']
        rdm_r = res.get('rdm_r')

        title_lines = [f"sub-{res['subj']} ({res['cvd_type']}) — {res['roi']}"]
        title_lines.append(f"{res['model']} LOCO " + r'$\rho$' + f"={rho:.2f}{sig_sym}")
        if rdm_r is not None:
            title_lines[-1] += f" | ΔRDM r={rdm_r:.2f}"

        ax.set_title('\n'.join(title_lines), fontsize=8, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

        if res['sig_level'] == 'significant':
            for spine in ax.spines.values():
                spine.set_linewidth(2.5); spine.set_color('#2E7D32')
        elif res['sig_level'] == 'trending':
            for spine in ax.spines.values():
                spine.set_linewidth(1.5); spine.set_color('#FF8F00')

    fig.suptitle('Per-Color Hue Distortion ' + r'$\delta\theta$' +
                  ' (ΔRDM Simulation)\n'
                  'Green = significant (p<.05), Orange = trending (p<.10)',
                  fontsize=11, fontweight='bold', y=1.04)
    plt.tight_layout()
    plt.savefig(output_dir / 'delta_theta_bars_rdm.png', dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {output_dir / "delta_theta_bars_rdm.png"}')


# ============================================================================
# Fig 3: Continuous Distortion Curve
# ============================================================================

def plot_continuous_distortion(output_dir, best_per_roi):
    """Continuous delta_theta(theta) for ΔRDM-validated models."""
    stim_rgb = get_stim_rgb()
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    theta_fine = np.linspace(0, 360, 361)

    for ax_idx, subj in enumerate(['08', '09']):
        ax = axes[ax_idx]
        cvd_type = CVD_TYPE[subj]

        for roi, clr, ls in [('V1', '#2196F3', '-'), ('V2', '#4CAF50', '--')]:
            res = best_per_roi.get((subj, roi))
            if res is None:
                continue

            model = res['model']
            params = res['params']
            p_loco = res['loco_p']

            if model in ('cone_1way', 'cone_3way'):
                if model == 'cone_1way':
                    _, _, delta_8 = compute_1way_hue_shift(params[0], cvd_type)
                else:
                    _, _, delta_8 = compute_shifted_hue_3way(*params)
                delta_uw = np.rad2deg(np.unwrap(np.deg2rad(delta_8)))
                x_p = np.append(HUE_ANGLES_DEG, 360.0)
                y_p = np.append(delta_uw, delta_uw[0])
                cs = CubicSpline(x_p, y_p, bc_type='periodic')
                delta_fine = cs(theta_fine)
            elif model == 'fourier':
                a1, b1, a2, b2 = params
                tr = np.deg2rad(theta_fine)
                delta_fine = (a1 * np.cos(tr) + b1 * np.sin(tr) +
                              a2 * np.cos(2 * tr) + b2 * np.sin(2 * tr))
            else:
                continue

            sig_sym = '*' if p_loco < 0.05 else ('\u2020' if p_loco < 0.10 else ' ns')
            alpha = 0.9 if p_loco < 0.05 else (0.6 if p_loco < 0.10 else 0.3)
            ax.plot(theta_fine, delta_fine, ls, color=clr, lw=2,
                    label=f'{roi} ({model[:7]}) LOCO p={p_loco:.3f}{sig_sym}',
                    alpha=alpha)

        for j in range(8):
            ax.axvline(HUE_ANGLES_DEG[j], color=stim_rgb[j], alpha=0.35, lw=8)

        ax.axhline(0, color='gray', lw=0.8, ls=':')
        ax.set_xlabel('Hue Angle ' + r'$\theta$' + ' (deg)', fontsize=10)
        ax.set_ylabel(r'$\delta\theta$ (deg)', fontsize=10)
        ax.set_title(f'sub-{subj} ({cvd_type})', fontsize=11, fontweight='bold')
        ax.set_xticks(HUE_ANGLES_DEG)
        ax.set_xticklabels(COLOR_NAMES, fontsize=7, rotation=45, ha='right')
        ax.legend(fontsize=8)
        ax.grid(alpha=0.2)
        ax.set_xlim(0, 360)

    fig.suptitle('Continuous Hue Distortion ' +
                  r'$\delta\theta(\theta)$' + ' — ΔRDM Cosine Metric',
                  fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_dir / 'continuous_distortion_rdm.png', dpi=200,
                bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {output_dir / "continuous_distortion_rdm.png"}')


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Visualize ΔRDM simulation results')
    parser.add_argument('--output_dir', type=str,
                        default='figures/delta_rdm')
    args = parser.parse_args()

    output_dir = _SCRIPT_DIR.parent / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('ΔRDM Simulation Visualization')
    print(f'Source: {SIM_DIR}')
    print(f'Output: {output_dir}')
    print('=' * 60)

    print('\n[1] Loading simulation results...')
    sim_results = load_sim_results()
    best_per_roi = get_best_per_roi(sim_results)
    print(f'  Found {len(sim_results)} results')

    print('\n  Summary:')
    for key in sorted(sim_results.keys()):
        res = sim_results[key]
        is_best = best_per_roi.get((res['subj'], res['roi'])) is res
        marker = ' <-- BEST' if is_best else ''
        sig_sym = '*' if res['sig_level'] == 'significant' else (
            '\u2020' if res['sig_level'] == 'trending' else '')
        print(f"  sub-{res['subj']} {res['roi']} {res['model']}x{res['metric']}: "
              f"ΔRDM r={res['rdm_r']:.3f} (p={res['rdm_p']:.4f}) | "
              f"LOCO rho={res['loco_rho']:.3f} (p={res['loco_p']:.4f}) "
              f"[{res['sig_level']}{sig_sym}]{marker}")

    if not sim_results:
        print('[WARN] No simulation results found.')
        return

    print('\n[2] Polar distortion...')
    plot_polar_distortion(output_dir, best_per_roi)

    print('\n[3] Delta-theta bars...')
    plot_delta_theta_bars(output_dir, sim_results)

    print('\n[4] Continuous distortion...')
    plot_continuous_distortion(output_dir, best_per_roi)

    print(f'\nAll figures saved to: {output_dir}')


if __name__ == '__main__':
    main()
