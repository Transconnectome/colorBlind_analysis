#!/usr/bin/env python3
"""
analyze_loso_zero_shot.py — Local analysis of LOSO zero-shot results.

Compares LOSO zero-shot (direct eval, frozen W0) against two baselines:
  - LORO ridge_gcv: train on 5 runs, predict held-out run (all 8 colors)
  - LOCO ridge_gcv: train on 7 colors, predict held-out color (hardest)

Produces:
  Table 1: HC summary — ZS direct vs LORO vs LOCO (per ROI)
  Table 2: Per-subject detail (HC)
  Table 3: CVD robustness (mean +/- SD across 7 LOO priors)
  Figure 1: Grouped bar — voxel_corr by ROI (3 conditions)
  Figure 2: Connected dot — per-subject ZS vs LORO vs LOCO
  Figure 3: CVD box plot across 7 priors (with LORO/LOCO baselines)

Usage:
    python scripts/analyze_loso_zero_shot.py \
        --loso_json results/loso_zero_shot/loso_zero_shot.json \
        --validation_dir results/validation \
        --output_dir results/loso_zero_shot
"""

import argparse
import json
import numpy as np
from pathlib import Path
from scipy.stats import ttest_rel

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ROI_ORDER = ['V1', 'V2', 'V3', 'hV4']
# LORO JSON uses 'V4', LOSO JSON uses 'hV4'
LORO_ROI_KEY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}


# ============================================================================
# Data loading
# ============================================================================

def load_loro_baselines(validation_dir):
    """Load LORO ridge_gcv baselines from validation JSONs.

    Returns:
        {roi: {subj: {'voxel_corr': float, 'R2': float, 'rdm_corr': float}}}
    """
    results = {}
    for subj in HC_SUBJECTS + CVD_SUBJECTS:
        path = Path(validation_dir) / f'sub-{subj}_loro.json'
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        for roi in ROI_ORDER:
            if roi not in results:
                results[roi] = {}
            loro_key = LORO_ROI_KEY[roi]
            if loro_key in data and 'ridge_gcv' in data[loro_key]:
                d = data[loro_key]['ridge_gcv']
                results[roi][subj] = {
                    'voxel_corr': d['mean_voxel_corr'],
                    'R2': d['mean_R2'],
                    'rdm_corr': d['mean_rdm_corr'],
                }
    return results


def load_loco_baselines(validation_dir):
    """Load LOCO ridge_gcv baselines from validation JSONs.

    Returns:
        {roi: {subj: {'voxel_corr': float, 'R2': float, 'mae': float}}}
    """
    results = {}
    for subj in HC_SUBJECTS + CVD_SUBJECTS:
        path = Path(validation_dir) / f'sub-{subj}_loco.json'
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        for roi in ROI_ORDER:
            if roi not in results:
                results[roi] = {}
            loro_key = LORO_ROI_KEY[roi]
            if loro_key in data and 'ridge_gcv' in data[loro_key]:
                d = data[loro_key]['ridge_gcv']
                results[roi][subj] = {
                    'voxel_corr': d['mean_voxel_corr'],
                    'R2': d.get('mean_R2', np.nan),
                    'mae': d.get('mean_mae', np.nan),
                }
    return results


# ============================================================================
# Tables
# ============================================================================

def print_table_1(loso_data, loro_bl, loco_bl):
    """Table 1: HC summary — ZS direct vs LORO ridge_gcv vs LOCO ridge_gcv."""
    print('\n' + '=' * 90)
    print('Table 1: HC Summary — LOSO Zero-Shot vs Baselines')
    print('  ZS     = direct eval, all 8 colors (frozen W0, no subject data)')
    print('  LORO   = ridge_gcv, train 5 runs -> test 1 run (all 8 colors)')
    print('  LOCO   = ridge_gcv, train 7 colors -> test 1 color (hardest)')
    print('=' * 90)
    print(f'{"ROI":>6s}  {"ZS_vc":>7s} {"sd":>6s}  '
          f'{"LORO_vc":>7s} {"sd":>6s}  '
          f'{"LOCO_vc":>7s} {"sd":>6s}  '
          f'{"t(ZS-LORO)":>10s}  {"p":>7s}')
    print('-' * 90)

    for roi in ROI_ORDER:
        if roi not in loso_data['results']:
            continue
        s = loso_data['results'][roi]['hc_stats']

        # LORO baseline per-subject
        loro_vals = [loro_bl[roi][subj]['voxel_corr']
                     for subj in HC_SUBJECTS
                     if roi in loro_bl and subj in loro_bl.get(roi, {})]
        # LOCO baseline per-subject
        loco_vals = [loco_bl[roi][subj]['voxel_corr']
                     for subj in HC_SUBJECTS
                     if roi in loco_bl and subj in loco_bl.get(roi, {})]

        # ZS per-subject
        hc = loso_data['results'][roi]['hc']
        zs_vals = [hc[subj]['zero_shot']['mean_voxel_corr']
                   for subj in HC_SUBJECTS if subj in hc]

        # Paired t: ZS vs LORO (same-difficulty comparison)
        n = min(len(zs_vals), len(loro_vals))
        if n >= 2:
            t_val, p_val = ttest_rel(zs_vals[:n], loro_vals[:n])
        else:
            t_val, p_val = np.nan, np.nan

        loro_m = np.mean(loro_vals) if loro_vals else np.nan
        loro_sd = np.std(loro_vals, ddof=1) if len(loro_vals) > 1 else 0.0
        loco_m = np.mean(loco_vals) if loco_vals else np.nan
        loco_sd = np.std(loco_vals, ddof=1) if len(loco_vals) > 1 else 0.0

        sig = '*' if p_val < 0.05 else ''
        print(f'{roi:>6s}  '
              f'{s["zs_voxel_corr_mean"]:>7.4f} {s["zs_voxel_corr_sd"]:>6.3f}  '
              f'{loro_m:>7.4f} {loro_sd:>6.3f}  '
              f'{loco_m:>7.4f} {loco_sd:>6.3f}  '
              f'{t_val:>10.3f}  {p_val:>6.4f}{sig}')

    print('\n  Note: ZS direct >> LOCO is expected (ZS evaluates known colors,')
    print('        LOCO tests 45-deg interpolation). Fair comparison = ZS vs LORO.')


def print_table_2(loso_data, loro_bl, loco_bl):
    """Table 2: Per-subject detail (HC)."""
    print('\n' + '=' * 90)
    print('Table 2: Per-Subject Detail (HC)')
    print('=' * 90)

    for roi in ROI_ORDER:
        if roi not in loso_data['results']:
            continue
        hc = loso_data['results'][roi]['hc']
        print(f'\n  {roi}:')
        print(f'  {"Subj":>7s}  {"ZS_vc":>7s}  {"ZS_rdm":>7s}  {"ZS_MAE":>7s}  '
              f'{"LORO_vc":>7s}  {"LOCO_vc":>7s}  {"LOCO_MAE":>8s}')
        print(f'  {"-"*62}')

        for subj in HC_SUBJECTS:
            if subj not in hc:
                continue
            zs = hc[subj]['zero_shot']
            zs_mae = zs['mean_mae']
            zs_mae_s = f'{zs_mae:>7.1f}' if np.isfinite(zs_mae) else '    NaN'

            loro_vc = loro_bl.get(roi, {}).get(subj, {}).get('voxel_corr', np.nan)
            loco_vc = loco_bl.get(roi, {}).get(subj, {}).get('voxel_corr', np.nan)
            loco_mae = loco_bl.get(roi, {}).get(subj, {}).get('mae', np.nan)

            print(f'  sub-{subj}  '
                  f'{zs["mean_voxel_corr"]:>7.4f}  '
                  f'{zs["rdm_corr"]:>7.4f}  '
                  f'{zs_mae_s}  '
                  f'{loro_vc:>7.4f}  '
                  f'{loco_vc:>7.4f}  '
                  f'{loco_mae:>8.1f}')


def print_table_3(loso_data, loro_bl, loco_bl):
    """Table 3: CVD robustness across 7 LOO priors + baselines."""
    print('\n' + '=' * 80)
    print('Table 3: CVD Robustness (mean +/- SD across 7 LOO priors)')
    print('=' * 80)
    print(f'{"ROI":>6s}  {"Subj":>7s}  {"ZS_vc":>9s}  {"ZS_sd":>6s}  '
          f'{"LORO_vc":>7s}  {"LOCO_vc":>7s}')
    print('-' * 60)

    for roi in ROI_ORDER:
        if roi not in loso_data['results']:
            continue
        cvd = loso_data['results'][roi].get('cvd', {})
        for subj in CVD_SUBJECTS:
            if subj not in cvd:
                continue
            cr = cvd[subj]
            loro_vc = loro_bl.get(roi, {}).get(subj, {}).get('voxel_corr', np.nan)
            loco_vc = loco_bl.get(roi, {}).get(subj, {}).get('voxel_corr', np.nan)

            print(f'{roi:>6s}  sub-{subj}  '
                  f'{cr["voxel_corr_mean"]:>9.4f}  '
                  f'{cr["voxel_corr_sd"]:>6.4f}  '
                  f'{loro_vc:>7.4f}  '
                  f'{loco_vc:>7.4f}')


# ============================================================================
# Figures
# ============================================================================

def plot_figure_1(loso_data, loro_bl, loco_bl, output_dir):
    """Figure 1: Grouped bar — ZS vs LORO vs LOCO by ROI."""
    fig, ax = plt.subplots(figsize=(10, 6))

    rois = [r for r in ROI_ORDER if r in loso_data['results']]
    n_rois = len(rois)
    x = np.arange(n_rois)
    width = 0.25

    zs_means, zs_sds = [], []
    loro_means, loro_sds = [], []
    loco_means, loco_sds = [], []

    for roi in rois:
        s = loso_data['results'][roi]['hc_stats']
        zs_means.append(s['zs_voxel_corr_mean'])
        zs_sds.append(s['zs_voxel_corr_sd'])

        loro_vals = [loro_bl[roi][subj]['voxel_corr']
                     for subj in HC_SUBJECTS
                     if roi in loro_bl and subj in loro_bl.get(roi, {})]
        loro_means.append(np.mean(loro_vals) if loro_vals else 0)
        loro_sds.append(np.std(loro_vals, ddof=1) if len(loro_vals) > 1 else 0)

        loco_vals = [loco_bl[roi][subj]['voxel_corr']
                     for subj in HC_SUBJECTS
                     if roi in loco_bl and subj in loco_bl.get(roi, {})]
        loco_means.append(np.mean(loco_vals) if loco_vals else 0)
        loco_sds.append(np.std(loco_vals, ddof=1) if len(loco_vals) > 1 else 0)

    ax.bar(x - width, zs_means, width, yerr=zs_sds,
           capsize=3, color='#2196F3', alpha=0.85, label='LOSO Zero-Shot (direct)')
    ax.bar(x, loro_means, width, yerr=loro_sds,
           capsize=3, color='#FF9800', alpha=0.85, label='Ridge-GCV (LORO)')
    ax.bar(x + width, loco_means, width, yerr=loco_sds,
           capsize=3, color='#4CAF50', alpha=0.85, label='Ridge-GCV (LOCO)')

    ax.axhline(0, color='black', linewidth=0.8, linestyle='-')
    ax.set_xlabel('ROI', fontsize=12)
    ax.set_ylabel('Voxel Pattern Correlation (r)', fontsize=12)
    ax.set_title('HC: LOSO Zero-Shot vs LORO vs LOCO Baselines',
                 fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(rois, fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    out_path = Path(output_dir) / 'fig1_zs_vs_loro_vs_loco.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {out_path}')


def plot_figure_2(loso_data, loro_bl, loco_bl, output_dir):
    """Figure 2: Connected dot — per-subject ZS vs LORO vs LOCO."""
    rois = [r for r in ROI_ORDER if r in loso_data['results']]

    fig, axes = plt.subplots(1, len(rois), figsize=(4.5 * len(rois), 5),
                             sharey=True)
    if len(rois) == 1:
        axes = [axes]

    for ax, roi in zip(axes, rois):
        hc = loso_data['results'][roi]['hc']
        subjects = sorted([s for s in hc.keys()])

        for subj in subjects:
            zs_v = hc[subj]['zero_shot']['mean_voxel_corr']
            loro_v = loro_bl.get(roi, {}).get(subj, {}).get('voxel_corr', np.nan)
            loco_v = loco_bl.get(roi, {}).get(subj, {}).get('voxel_corr', np.nan)

            # Lines: ZS -> LORO -> LOCO
            ax.plot([0, 1, 2], [zs_v, loro_v, loco_v], '-',
                    color='#888888', alpha=0.4, linewidth=1)
            ax.plot(0, zs_v, 'o', color='#2196F3', markersize=6, zorder=5)
            ax.plot(1, loro_v, 's', color='#FF9800', markersize=6, zorder=5)
            ax.plot(2, loco_v, '^', color='#4CAF50', markersize=6, zorder=5)
            ax.annotate(f'{subj}', (0, zs_v), textcoords='offset points',
                        xytext=(-15, 0), fontsize=7, ha='right')

        ax.axhline(0, color='black', linewidth=0.8, linestyle='-')
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(['ZS\n(direct)', 'LORO\n(ridge)', 'LOCO\n(ridge)'],
                           fontsize=9)
        ax.set_title(roi, fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

    axes[0].set_ylabel('Voxel Pattern Correlation (r)', fontsize=11)
    fig.suptitle('Per-Subject: LOSO Zero-Shot vs LORO vs LOCO',
                 fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    out_path = Path(output_dir) / 'fig2_connected_dot.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {out_path}')


def plot_figure_3(loso_data, loro_bl, loco_bl, output_dir):
    """Figure 3: CVD box plot — ZS across 7 priors, with LORO/LOCO baselines."""
    rois = [r for r in ROI_ORDER if r in loso_data['results']]
    cvd_subjects = [s for s in CVD_SUBJECTS
                    if any(s in loso_data['results'].get(r, {}).get('cvd', {})
                           for r in rois)]

    if not cvd_subjects:
        print('No CVD data for Figure 3, skipping.')
        return

    fig, axes = plt.subplots(1, len(rois), figsize=(4.5 * len(rois), 5),
                             sharey=True)
    if len(rois) == 1:
        axes = [axes]

    cvd_colors = {'08': '#e41a1c', '09': '#377eb8', '10': '#984ea3'}

    for ax, roi in zip(axes, rois):
        cvd = loso_data['results'][roi].get('cvd', {})
        positions = []
        data = []
        labels = []
        colors = []

        for j, subj in enumerate(cvd_subjects):
            if subj not in cvd:
                continue
            per_prior = cvd[subj]['per_prior']
            vals = [pp['voxel_corr'] for pp in per_prior]
            data.append(vals)
            positions.append(j)
            labels.append(f'sub-{subj}')
            colors.append(cvd_colors.get(subj, '#666666'))

        if data:
            bp = ax.boxplot(data, positions=positions, widths=0.5,
                            patch_artist=True, showfliers=True)
            for patch, c in zip(bp['boxes'], colors):
                patch.set_facecolor(c)
                patch.set_alpha(0.5)
            for median in bp['medians']:
                median.set_color('black')
                median.set_linewidth(1.5)

            # Baseline markers
            for j, subj in enumerate(cvd_subjects):
                if subj not in cvd:
                    continue
                loro_v = loro_bl.get(roi, {}).get(subj, {}).get(
                    'voxel_corr', np.nan)
                loco_v = loco_bl.get(roi, {}).get(subj, {}).get(
                    'voxel_corr', np.nan)
                if np.isfinite(loro_v):
                    ax.plot(j - 0.15, loro_v, 's', color='#FF9800',
                            markersize=8, zorder=5,
                            label='LORO ridge' if j == 0 else '')
                if np.isfinite(loco_v):
                    ax.plot(j + 0.15, loco_v, '^', color='#4CAF50',
                            markersize=8, zorder=5,
                            label='LOCO ridge' if j == 0 else '')

        ax.axhline(0, color='black', linewidth=0.8, linestyle='-')
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, fontsize=9, rotation=30)
        ax.set_title(roi, fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

    axes[0].set_ylabel('Voxel Pattern Correlation (r)', fontsize=11)
    if axes[-1].get_legend_handles_labels()[1]:
        axes[-1].legend(fontsize=9, loc='upper right')
    fig.suptitle('CVD: LOSO Zero-Shot across 7 LOO Priors',
                 fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    out_path = Path(output_dir) / 'fig3_cvd_boxplot.png'
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {out_path}')


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Analyze LOSO zero-shot results')
    parser.add_argument('--loso_json', type=str,
                        default='results/loso_zero_shot/loso_zero_shot.json')
    parser.add_argument('--validation_dir', type=str,
                        default='results/validation')
    parser.add_argument('--output_dir', type=str,
                        default='results/loso_zero_shot')
    args = parser.parse_args()

    loso_path = Path(args.loso_json)
    if not loso_path.exists():
        print(f'ERROR: {loso_path} not found')
        return
    loso_data = json.loads(loso_path.read_text())

    # Load baselines from validation dir
    loro_bl = load_loro_baselines(args.validation_dir)
    loco_bl = load_loco_baselines(args.validation_dir)
    print(f'Loaded LORO baselines: {sum(len(v) for v in loro_bl.values())} entries')
    print(f'Loaded LOCO baselines: {sum(len(v) for v in loco_bl.values())} entries')

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Tables
    print_table_1(loso_data, loro_bl, loco_bl)
    print_table_2(loso_data, loro_bl, loco_bl)
    print_table_3(loso_data, loro_bl, loco_bl)

    # Figures
    plot_figure_1(loso_data, loro_bl, loco_bl, output_dir)
    plot_figure_2(loso_data, loro_bl, loco_bl, output_dir)
    plot_figure_3(loso_data, loro_bl, loco_bl, output_dir)

    # Key interpretation
    print('\n' + '=' * 70)
    print('KEY INTERPRETATION')
    print('=' * 70)
    print('\n  Difficulty hierarchy: LOCO (90-deg gap) >> LORO (run gen.) ~ ZS (subj gen.)')
    print('  Fair comparison: ZS direct vs LORO (both predict all 8 colors)')
    print()

    for roi in ROI_ORDER:
        if roi not in loso_data['results']:
            continue
        s = loso_data['results'][roi]['hc_stats']
        zs_vc = s['zs_voxel_corr_mean']

        loro_vals = [loro_bl[roi][subj]['voxel_corr']
                     for subj in HC_SUBJECTS
                     if roi in loro_bl and subj in loro_bl.get(roi, {})]
        loro_m = np.mean(loro_vals) if loro_vals else np.nan

        loco_vals = [loco_bl[roi][subj]['voxel_corr']
                     for subj in HC_SUBJECTS
                     if roi in loco_bl and subj in loco_bl.get(roi, {})]
        loco_m = np.mean(loco_vals) if loco_vals else np.nan

        delta_loro = zs_vc - loro_m if np.isfinite(loro_m) else np.nan
        print(f'  {roi}: ZS={zs_vc:.4f}  LORO={loro_m:.4f}  '
              f'LOCO={loco_m:.4f}  delta(ZS-LORO)={delta_loro:+.4f}')

    print('\n  If ZS >= LORO: group prior (no subject data) matches')
    print('    subject-specific model with run-level training data.')
    print('  If ZS < LORO: group prior captures less than subject-specific model.')
    print('  LOCO always lowest: 45-deg interpolation gap is the hardest test.')


if __name__ == '__main__':
    main()
