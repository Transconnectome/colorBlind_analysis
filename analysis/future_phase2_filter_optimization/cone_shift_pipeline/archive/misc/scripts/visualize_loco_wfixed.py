#!/usr/bin/env python3
"""
visualize_loco_wfixed.py — W-fixed LOCO results visualization.

Visualizes per-ROI (V1/V2/V3/V4) W-fixed LOCO cone-shift fitting results
from step1_fit_loco_v2.py and step1_fit_loco_v2_joint.py.

Figures:
  Fig 1: Spearman landscape (ρ vs Δλ sweep) per ROI
  Fig 2: Per-color vulnerability bar comparison (HC shifted vs CVD actual)
  Fig 3: Per-model comparison with improvement test results

Usage:
    conda activate srm
    python scripts/visualize_loco_wfixed.py [--results_dir results/v2/step1_loco_wfixed]
"""

import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
_FWD_DIR = str(_SCRIPT_DIR.parent.parent.parent / 'future_phase1_forward_model' / 'scripts')
if _FWD_DIR not in sys.path:
    sys.path.insert(0, _FWD_DIR)
sys.path.insert(0, str(_SCRIPT_DIR))

from stockman_cone_shift import COLOR_NAMES, HUE_ANGLES_DEG

# ============================================================================
# Idealized stimulus colors (L*=75, chroma=40) matching experiment
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
CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
ROI_COLORS = {'V1': '#2196F3', 'V2': '#4CAF50', 'V3': '#9C27B0', 'V4': '#FF9800'}


# ============================================================================
# Load results
# ============================================================================

def load_loco_results(results_dir):
    """Load W-fixed LOCO results from step1_fit_loco_v2.py output."""
    results = {}
    results_path = Path(results_dir)
    for roi_dir in results_path.iterdir():
        if not roi_dir.is_dir():
            continue
        roi = roi_dir.name
        for f in roi_dir.glob('sub-*_loco_v2.json'):
            with open(f) as fh:
                data = json.load(fh)
            subj = data['subject']
            results[(subj, roi)] = data
    return results


def load_joint_results(joint_dir):
    """Load joint cross-ROI results from step1_fit_loco_v2_joint.py."""
    results = {}
    joint_path = Path(joint_dir)
    if not joint_path.exists():
        return results
    for f in joint_path.glob('sub-*_loco_v2_joint.json'):
        with open(f) as fh:
            data = json.load(fh)
        subj = data['subject']
        results[subj] = data
    return results


# ============================================================================
# Fig 1: Spearman Landscape (ρ vs Δλ)
# ============================================================================

def plot_landscape(output_dir, loco_results):
    """Spearman landscape for cone_1way per ROI."""
    stim_rgb = get_stim_rgb()
    subjects_with_landscape = set()

    for (subj, roi), data in loco_results.items():
        if 'landscape_cone_1way' in data:
            subjects_with_landscape.add(subj)

    if not subjects_with_landscape:
        print('  [SKIP] No landscape data found.')
        return

    for subj in sorted(subjects_with_landscape):
        cvd_type = CVD_TYPE.get(subj, 'unknown')
        fig, ax = plt.subplots(figsize=(10, 5))

        for roi in ['V1', 'V2', 'V3', 'V4']:
            key = (subj, roi)
            if key not in loco_results:
                continue
            data = loco_results[key]
            if 'landscape_cone_1way' not in data:
                continue
            land = data['landscape_cone_1way']
            ax.plot(land['delta_range'], land['spearman_r'],
                    color=ROI_COLORS.get(roi, 'gray'), lw=2, label=roi)

            # Mark peak
            best_idx = np.argmax(land['spearman_r'])
            ax.scatter(land['delta_range'][best_idx],
                       land['spearman_r'][best_idx],
                       color=ROI_COLORS.get(roi, 'gray'), s=80, zorder=5)

        ax.axhline(0, color='gray', ls=':', lw=0.8)
        ax.set_xlabel('Δλ (nm)', fontsize=11)
        ax.set_ylabel('Spearman ρ', fontsize=11)
        ax.set_title(f'sub-{subj} ({cvd_type}) — Spearman Landscape (cone_1way, W-fixed)',
                     fontsize=12, fontweight='bold')
        ax.legend(fontsize=10)
        ax.grid(alpha=0.2)

        fname = output_dir / f'landscape_sub-{subj}.png'
        plt.savefig(fname, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f'  Saved: {fname}')


# ============================================================================
# Fig 2: Per-Color Vulnerability Comparison
# ============================================================================

def plot_vuln_comparison(output_dir, loco_results):
    """Bar chart: HC shifted vuln vs CVD actual vuln per color."""
    stim_rgb = get_stim_rgb()

    for (subj, roi), data in sorted(loco_results.items()):
        fits = data.get('fit_results', {})
        cvd_target = np.array(data.get('cvd_loco_target', []))
        if len(cvd_target) != 8:
            continue

        # Use cone_1way if available
        model = 'cone_1way' if 'cone_1way' in fits else next(iter(fits), None)
        if model is None:
            continue
        fit = fits[model]

        hc_vuln = np.array(fit['mean_hc_vuln'])
        hc_base = np.array(fit['mean_hc_vuln_baseline'])

        x = np.arange(8)
        w = 0.25
        fig, ax = plt.subplots(figsize=(10, 5))

        ax.bar(x - w, cvd_target, w, label='CVD actual',
               color=[stim_rgb[j] for j in range(8)],
               edgecolor='black', linewidth=0.8)
        ax.bar(x, hc_base, w, label='HC baseline (Δλ=0)',
               color='lightgray', edgecolor='black', linewidth=0.8)
        ax.bar(x + w, hc_vuln, w, label=f'HC shifted ({model})',
               color='lightblue', edgecolor='navy', linewidth=0.8)

        ax.set_xticks(x)
        ax.set_xticklabels(COLOR_NAMES, fontsize=9)
        ax.set_ylabel('Voxel Pattern Correlation', fontsize=10)

        rho = fit['spearman_r']
        rho_base = fit['spearman_r_baseline']
        p_impr = fit.get('perm_p_improvement', None)
        delta_rho = fit.get('delta_rho', None)

        title = (f'sub-{subj} {roi} ({CVD_TYPE.get(subj, "?")}) — {model}\n'
                 f'ρ={rho:.3f} (baseline={rho_base:.3f})')
        if delta_rho is not None and p_impr is not None:
            sig = '*' if p_impr < 0.05 else ''
            title += f' | Δρ={delta_rho:+.3f} (p_impr={p_impr:.3f}{sig})'
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(axis='y', alpha=0.2)

        fname = output_dir / f'vuln_comparison_sub-{subj}_{roi}.png'
        plt.savefig(fname, dpi=200, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f'  Saved: {fname}')


# ============================================================================
# Fig 3: Model Comparison Summary (with improvement test)
# ============================================================================

def plot_model_summary(output_dir, loco_results):
    """Summary table-like figure showing all models per subject-ROI."""

    summaries = []
    for (subj, roi), data in sorted(loco_results.items()):
        fits = data.get('fit_results', {})
        for model, fit in fits.items():
            summaries.append({
                'subj': subj, 'roi': roi, 'model': model,
                'rho': fit['spearman_r'],
                'rho_base': fit['spearman_r_baseline'],
                'delta_rho': fit.get('delta_rho', None),
                'p_spearman': fit['perm_p_spearman'],
                'p_improvement': fit.get('perm_p_improvement', None),
            })

    if not summaries:
        print('  [SKIP] No model results to summarize.')
        return

    # Group by (subj, roi)
    from collections import defaultdict
    groups = defaultdict(list)
    for s in summaries:
        groups[(s['subj'], s['roi'])].append(s)

    fig, axes = plt.subplots(len(groups), 1,
                              figsize=(12, 2.5 * len(groups)),
                              squeeze=False)

    for idx, ((subj, roi), models) in enumerate(sorted(groups.items())):
        ax = axes[idx, 0]
        model_names = [m['model'] for m in models]
        rhos = [m['rho'] for m in models]
        rho_bases = [m['rho_base'] for m in models]
        delta_rhos = [m['delta_rho'] for m in models]

        x = np.arange(len(models))
        w = 0.35
        bars1 = ax.bar(x - w/2, rho_bases, w, label='ρ baseline',
                        color='lightgray', edgecolor='gray')
        bars2 = ax.bar(x + w/2, rhos, w, label='ρ fitted',
                        color=ROI_COLORS.get(roi, 'steelblue'),
                        edgecolor='black')

        # Annotate with p_improvement
        for j, m in enumerate(models):
            p_i = m['p_improvement']
            dr = m['delta_rho']
            if p_i is not None and dr is not None:
                sig = '*' if p_i < 0.05 else ''
                color = 'green' if dr > 0 else 'red'
                ax.text(x[j] + w/2, rhos[j] + 0.01,
                        f'Δρ={dr:+.3f}\np={p_i:.3f}{sig}',
                        ha='center', va='bottom', fontsize=7,
                        color=color, fontweight='bold')

        ax.set_xticks(x)
        ax.set_xticklabels(model_names, fontsize=8)
        ax.set_ylabel('Spearman ρ', fontsize=9)
        ax.set_title(f'sub-{subj} {roi} ({CVD_TYPE.get(subj, "?")})',
                     fontsize=10, fontweight='bold')
        ax.legend(fontsize=8, loc='upper right')
        ax.grid(axis='y', alpha=0.2)

    fig.suptitle('LOCO W-fixed Model Comparison (with Improvement Test)',
                 fontsize=13, fontweight='bold', y=1.01)
    plt.tight_layout()
    fname = output_dir / 'model_comparison_summary.png'
    plt.savefig(fname, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {fname}')


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Visualize W-fixed LOCO cone-shift results')
    parser.add_argument('--results_dir', type=str,
                        default=str(RESULTS_BASE / 'v2' / 'step1_loco_wfixed'))
    parser.add_argument('--joint_dir', type=str,
                        default=str(RESULTS_BASE / 'v2' / 'step1_loco_joint'))
    parser.add_argument('--output_dir', type=str, default='figures/loco_wfixed')
    args = parser.parse_args()

    output_dir = _SCRIPT_DIR.parent / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('W-fixed LOCO Results Visualization')
    print(f'Results: {args.results_dir}')
    print(f'Output: {output_dir}')
    print('=' * 60)

    print('\n[1] Loading W-fixed LOCO results...')
    loco_results = load_loco_results(args.results_dir)
    print(f'  Found {len(loco_results)} subject-ROI results')

    joint_results = load_joint_results(args.joint_dir)
    if joint_results:
        print(f'  Found {len(joint_results)} joint results')

    if not loco_results:
        print('[WARN] No results found. Check --results_dir.')
        return

    print('\n[2] Spearman landscape...')
    plot_landscape(output_dir, loco_results)

    print('\n[3] Vulnerability comparison...')
    plot_vuln_comparison(output_dir, loco_results)

    print('\n[4] Model comparison summary...')
    plot_model_summary(output_dir, loco_results)

    print(f'\nAll figures saved to: {output_dir}')


if __name__ == '__main__':
    main()
