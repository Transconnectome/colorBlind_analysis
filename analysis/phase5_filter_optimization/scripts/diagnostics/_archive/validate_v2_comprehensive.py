#!/usr/bin/env python3
"""
validate_v2_comprehensive.py — Comprehensive validation using v2 results.

Uses:
  - results/fits/canonical_2component_v2/ (2-Component with bootstrap, corrected baseline)
  - results/fits/canonical_rc_opponent_v2/  (R+C model with LOCO validation)
  - results/2component_stockman/          (fallback for sub-10)

Generates:
  (1) Updated metric comparison table (v2 crossnobis is more consistent)
  (2) Bootstrap CI visualization (β_s, β_c distributions)
  (3) R+C model delta-theta bars + color wheel (side-by-side with 2-component)
  (4) R+C LOCO validation summary
  (5) Model head-to-head comparison figure

Usage:
    conda activate srm
    python scripts/validate_v2_comprehensive.py --output_dir results/validation_v2
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

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR.parent))

_FWD_DIR = str(_SCRIPT_DIR.parent.parent.parent / 'phase4_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from machado_simulator import machado_shifted_hue
from retinal_cortical import machado_with_opponent_gain
from visualize_cone_shift_colors import (
    lab2rgb, get_stim_rgb, STIM_LAB_ARR, STIM_L, STIM_A, STIM_B,
    STIM_CHROMA, STIM_HUE_DEG,
)
from stockman_cone_shift import COLOR_NAMES

# ===========================================================================
# Constants
# ===========================================================================
_PIPE_DIR = _SCRIPT_DIR.parent
RESULTS_V2 = _PIPE_DIR / 'results' / 'fits/canonical_2component_v2'
RESULTS_RC = _PIPE_DIR / 'results' / 'fits/canonical_rc_opponent_v2'
RESULTS_STK = _PIPE_DIR / 'results' / '2component_stockman'

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
CONF_AXIS = {'protan': 16.0, 'deutan': 150.0, 'normal': 83.0}


def load_2comp(subj_id):
    """Load 2-component results, preferring v2, falling back to stockman."""
    for d in [RESULTS_V2, RESULTS_STK]:
        p = d / f'sub-{subj_id}_2component_results.json'
        if p.exists():
            with open(p) as f:
                data = json.load(f)
            data['_source'] = str(d.name)
            return data
    raise FileNotFoundError(f'No 2-component results for sub-{subj_id}')


def load_rc(subj_id):
    """Load R+C model results."""
    p = RESULTS_RC / f'sub-{subj_id}_opponent_rg_machado_1way.json'
    if not p.exists():
        raise FileNotFoundError(f'No R+C results for sub-{subj_id}')
    with open(p) as f:
        return json.load(f)


# ===========================================================================
# (1) Updated Metric Comparison
# ===========================================================================

def metric_comparison_v2(subjects=('08', '09', '10')):
    """Metric comparison using v2 results (corrected crossnobis)."""
    rows = []
    for subj in subjects:
        try:
            data = load_2comp(subj)
        except FileNotFoundError:
            continue
        cvd = data['cvd_type']
        src = data.get('_source', '?')
        for roi in ['V1', 'V2']:
            if roi not in data:
                continue
            d = data[roi]
            combos = [
                ('Corr+Cos', d['grid_correlation']['best_cosine'],
                 d['perm_correlation_cosine']['perm_p_cosine']),
                ('Corr+WUC', d['grid_correlation']['best_wuc'],
                 d['perm_correlation_cosine']['perm_p_wuc']),
                ('Xnobis+Cos', d['grid_crossnobis']['best_cosine'],
                 d['perm_crossnobis_cosine']['perm_p_cosine']),
                ('Xnobis+WUC', d['grid_crossnobis']['best_wuc'],
                 d['perm_crossnobis_cosine']['perm_p_wuc']),
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
                    'source': src,
                })
    return rows


def print_metric_table_v2(rows, output_path=None):
    """Print formatted metric comparison."""
    lines = []
    lines.append('=' * 110)
    lines.append('METRIC COMPARISON (v2): 2-Component Angular Dilation Model')
    lines.append('=' * 110)
    lines.append(f"{'Subject':<8} {'CVD':<7} {'ROI':<4} {'Metric':<13} "
                 f"{'beta_s':>6} {'beta_c':>6} {'Effect':>7} {'p':>8} {'Sig':>5} "
                 f"{'Bnd':>4} {'Src':<20}")
    lines.append('-' * 110)

    for r in rows:
        sig = '***' if r['perm_p'] < 0.01 else ('*' if r['perm_p'] < 0.05 else
              ('t' if r['perm_p'] < 0.10 else 'NS'))
        bnd = '!' if r['boundary'] else ''
        lines.append(f"{r['subject']:<8} {r['cvd_type']:<7} {r['roi']:<4} "
                     f"{r['metric']:<13} {r['beta_s']:6.0f} {r['beta_c']:6.0f} "
                     f"{r['effect']:7.3f} {r['perm_p']:8.4f} {sig:>5} {bnd:>4} "
                     f"{r['source']:<20}")

    # v2 vs stockman comparison for sub-09 crossnobis
    lines.append('')
    lines.append('KEY v2 CHANGE: Sub-09 V1 crossnobis parameter recovery')
    lines.append('  Stockman:  beta_s=4, beta_c=2  (cos=0.612, p=0.012)')
    lines.append('  v2:        beta_s=20, beta_c=5  (cos=0.590, p=0.007)')
    lines.append('  -> v2 beta_s=20 is MUCH more consistent with corr beta_s=24')
    lines.append('  -> v2 p=0.007 is more significant than stockman p=0.012')

    text = '\n'.join(lines)
    print(text)
    if output_path:
        with open(output_path, 'w') as f:
            f.write(text)
    return text


# ===========================================================================
# (2) Bootstrap CI Visualization
# ===========================================================================

def plot_bootstrap_ci(output_dir, subjects=('08', '09')):
    """Bootstrap parameter distributions and CIs from v2 data."""
    panels = []
    for subj in subjects:
        try:
            data = load_2comp(subj)
        except FileNotFoundError:
            continue
        boot = data.get('bootstrap_V1')
        if boot is None:
            continue
        panels.append({
            'subj': subj,
            'cvd': data['cvd_type'],
            'boot': boot,
            'v1_corr_cos': data.get('V1', {}).get('grid_correlation', {}).get('best_cosine', {}),
        })

    if not panels:
        print('  [SKIP] No bootstrap data.')
        return

    n = len(panels)
    fig, axes = plt.subplots(2, n, figsize=(6 * n, 8))
    if n == 1:
        axes = axes.reshape(2, 1)

    for idx, panel in enumerate(panels):
        boot = panel['boot']
        bs_dist = np.array(boot['beta_s_dist'])
        bc_dist = np.array(boot['beta_c_dist'])
        bs_ci = boot['beta_s_ci95']
        bc_ci = boot['beta_c_ci95']
        bs_mean = boot['beta_s_mean']
        bc_mean = boot['beta_c_mean']
        bs_std = boot['beta_s_std']
        bc_std = boot['beta_c_std']

        # Point estimate from grid search
        bs_point = panel['v1_corr_cos'].get('beta_s', bs_mean)
        bc_point = panel['v1_corr_cos'].get('beta_c', bc_mean)

        sig_s = '0 excluded' if (bs_ci[0] > 0 or bs_ci[1] < 0) else '0 INCLUDED'
        sig_c = '0 excluded' if (bc_ci[0] > 0 or bc_ci[1] < 0) else '0 INCLUDED'

        # beta_s histogram
        ax = axes[0, idx]
        ax.hist(bs_dist, bins=30, color='steelblue', alpha=0.7, edgecolor='white')
        ax.axvline(bs_mean, color='red', lw=2, ls='-', label=f'Mean={bs_mean:.1f}')
        ax.axvline(bs_ci[0], color='red', lw=1.5, ls='--', label=f'95% CI=[{bs_ci[0]:.0f}, {bs_ci[1]:.0f}]')
        ax.axvline(bs_ci[1], color='red', lw=1.5, ls='--')
        ax.axvline(bs_point, color='green', lw=2, ls=':', label=f'Point est.={bs_point:.0f}')
        ax.axvline(0, color='black', lw=1, ls='-', alpha=0.5)
        ax.set_xlabel(r'$\beta_s$ (degrees)', fontsize=11)
        ax.set_ylabel('Count (n=500)', fontsize=10)
        ax.set_title(f"sub-{panel['subj']} ({panel['cvd']}) — $\\beta_s$\n"
                     f"Mean={bs_mean:.1f} SD={bs_std:.1f} [{sig_s}]",
                     fontsize=10, fontweight='bold')
        ax.legend(fontsize=7)

        # beta_c histogram
        ax = axes[1, idx]
        ax.hist(bc_dist, bins=30, color='coral', alpha=0.7, edgecolor='white')
        ax.axvline(bc_mean, color='red', lw=2, ls='-', label=f'Mean={bc_mean:.1f}')
        ax.axvline(bc_ci[0], color='red', lw=1.5, ls='--', label=f'95% CI=[{bc_ci[0]:.0f}, {bc_ci[1]:.0f}]')
        ax.axvline(bc_ci[1], color='red', lw=1.5, ls='--')
        ax.axvline(bc_point, color='green', lw=2, ls=':', label=f'Point est.={bc_point:.0f}')
        ax.axvline(0, color='black', lw=1, ls='-', alpha=0.5)
        ax.set_xlabel(r'$\beta_c$ (degrees)', fontsize=11)
        ax.set_ylabel('Count (n=500)', fontsize=10)
        ax.set_title(f"sub-{panel['subj']} ({panel['cvd']}) — $\\beta_c$\n"
                     f"Mean={bc_mean:.1f} SD={bc_std:.1f} [{sig_c}]",
                     fontsize=10, fontweight='bold')
        ax.legend(fontsize=7)

    fig.suptitle('Bootstrap Parameter Distributions (500 HC resamples)\n'
                 '2-Component Angular Dilation, V1, Correlation + Cosine',
                 fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    out = output_dir / 'bootstrap_ci_v2.png'
    plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')


def plot_bootstrap_scatter(output_dir, subjects=('08', '09')):
    """2D bootstrap scatter (beta_s vs beta_c) showing parameter coupling."""
    panels = []
    for subj in subjects:
        try:
            data = load_2comp(subj)
        except FileNotFoundError:
            continue
        boot = data.get('bootstrap_V1')
        if boot is None:
            continue
        panels.append({
            'subj': subj,
            'cvd': data['cvd_type'],
            'boot': boot,
        })

    if not panels:
        return

    n = len(panels)
    fig, axes = plt.subplots(1, n, figsize=(6 * n, 5))
    if n == 1:
        axes = [axes]

    for idx, panel in enumerate(panels):
        ax = axes[idx]
        bs = np.array(panel['boot']['beta_s_dist'])
        bc = np.array(panel['boot']['beta_c_dist'])

        ax.scatter(bs, bc, alpha=0.3, s=15, c='steelblue', edgecolors='none')
        ax.scatter(panel['boot']['beta_s_mean'], panel['boot']['beta_c_mean'],
                   s=200, c='red', marker='*', edgecolors='black', linewidths=1,
                   zorder=10, label=f"Mean ({panel['boot']['beta_s_mean']:.0f}, "
                                    f"{panel['boot']['beta_c_mean']:.0f})")
        ax.axhline(0, color='gray', lw=0.5, ls=':')
        ax.axvline(0, color='gray', lw=0.5, ls=':')
        ax.set_xlabel(r'$\beta_s$ (degrees)', fontsize=11)
        ax.set_ylabel(r'$\beta_c$ (degrees)', fontsize=11)

        # Correlation
        r = np.corrcoef(bs, bc)[0, 1]
        ax.set_title(f"sub-{panel['subj']} ({panel['cvd']})\n"
                     f"r(beta_s, beta_c) = {r:.2f}",
                     fontsize=10, fontweight='bold')
        ax.legend(fontsize=8)
        ax.grid(alpha=0.2)

    fig.suptitle('Bootstrap Joint Distribution (500 HC resamples)',
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    out = output_dir / 'bootstrap_scatter_v2.png'
    plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')


# ===========================================================================
# (3) R+C Model Visualizations
# ===========================================================================

def compute_warped_hue(delta_theta_deg):
    """Apply delta_theta to CIELab hue angles -> warped CIELab colors."""
    new_hue_rad = np.deg2rad(STIM_HUE_DEG + np.asarray(delta_theta_deg))
    new_a = STIM_CHROMA * np.cos(new_hue_rad)
    new_b = STIM_CHROMA * np.sin(new_hue_rad)
    return lab2rgb(STIM_L, new_a, new_b)


def plot_model_comparison_bars(output_dir, subjects=('08', '09')):
    """Side-by-side delta-theta bars: 2-Component vs R+C."""
    orig_rgb = get_stim_rgb()
    n = len(subjects)
    fig, axes = plt.subplots(2, n, figsize=(6 * n, 9), sharey='row')
    if n == 1:
        axes = axes.reshape(2, 1)

    for idx, subj in enumerate(subjects):
        # 2-Component data
        try:
            data_2c = load_2comp(subj)
            dt_2c = np.array(data_2c['delta_theta_deg'])
            cvd = data_2c['cvd_type']
        except FileNotFoundError:
            continue

        # R+C data
        try:
            data_rc = load_rc(subj)
            diag = data_rc.get('opponent_gain_diagnostic', {})
            hue_base = np.array(diag['hue_baseline_deg'])
            hue_final = np.array(diag['hue_final_deg'])
            dt_rc = ((np.array(hue_final) - np.array(hue_base) + 180) % 360 - 180)
            rc_dl = data_rc['best']['delta_v1_nm']
            rc_g = data_rc['best']['g']
            rc_p = data_rc['permutation_null']['label_perm_p']
        except (FileNotFoundError, KeyError):
            dt_rc = np.zeros(8)
            rc_dl = 0
            rc_g = 0
            rc_p = 1.0

        x = np.arange(8)
        w = 0.35

        # Top: 2-Component
        ax = axes[0, idx]
        bars = ax.bar(x, dt_2c, color=[orig_rgb[j] for j in range(8)],
                       edgecolor='black', linewidth=0.8)
        ax.axhline(0, color='gray', lw=0.8, ls=':')
        ax.set_xticks(x)
        ax.set_xticklabels(COLOR_NAMES, fontsize=7, rotation=45, ha='right')
        ax.set_ylabel(r'$\Delta\theta$ (deg)', fontsize=10)
        ax.grid(axis='y', alpha=0.2)

        v1 = data_2c.get('V1', {})
        corr_cos = v1.get('grid_correlation', {}).get('best_cosine', {})
        perm = v1.get('perm_correlation_cosine', {})
        p_2c = perm.get('perm_p_cosine', 1.0)
        sig_2c = '*' if p_2c < 0.05 else ('t' if p_2c < 0.10 else '')
        ax.set_title(f"sub-{subj} ({cvd}) — 2-Component\n"
                     f"V1: beta_s={corr_cos.get('beta_s', 0):.0f} "
                     f"beta_c={corr_cos.get('beta_c', 0):.0f} "
                     f"p={p_2c:.3f}{sig_2c}",
                     fontsize=9, fontweight='bold')

        # Bottom: R+C
        ax = axes[1, idx]
        bars = ax.bar(x, dt_rc, color=[orig_rgb[j] for j in range(8)],
                       edgecolor='black', linewidth=0.8)
        ax.axhline(0, color='gray', lw=0.8, ls=':')
        ax.set_xticks(x)
        ax.set_xticklabels(COLOR_NAMES, fontsize=7, rotation=45, ha='right')
        ax.set_ylabel(r'$\Delta\theta$ (deg)', fontsize=10)
        ax.grid(axis='y', alpha=0.2)

        sig_rc = '*' if rc_p < 0.05 else ('t' if rc_p < 0.10 else '')
        ax.set_title(f"sub-{subj} ({cvd}) — R+C Model\n"
                     f"V1: dl={rc_dl:.1f}nm g={rc_g:.2f} "
                     f"p={rc_p:.3f}{sig_rc}",
                     fontsize=9, fontweight='bold')

    fig.suptitle('Model Comparison: Per-Color Hue Distortion\n'
                 'Top: 2-Component Angular Dilation | Bottom: Retinal+Cortical Gain',
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    out = output_dir / 'model_comparison_delta_theta.png'
    plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')


def plot_model_overlay(output_dir, subjects=('08', '09')):
    """Overlay 2-component and R+C delta-theta on same axes."""
    orig_rgb = get_stim_rgb()
    n = len(subjects)
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 5))
    if n == 1:
        axes = [axes]

    for idx, subj in enumerate(subjects):
        ax = axes[idx]

        # 2-Component
        try:
            data_2c = load_2comp(subj)
            dt_2c = np.array(data_2c['delta_theta_deg'])
            hue_base = np.array(data_2c['hue_base_deg'])
            cvd = data_2c['cvd_type']
        except FileNotFoundError:
            continue

        # R+C
        try:
            data_rc = load_rc(subj)
            diag = data_rc.get('opponent_gain_diagnostic', {})
            hue_final_rc = np.array(diag['hue_final_deg'])
            hue_base_rc = np.array(diag['hue_baseline_deg'])
            dt_rc = ((hue_final_rc - hue_base_rc + 180) % 360 - 180)
            rc_dl = data_rc['best']['delta_v1_nm']
            rc_g = data_rc['best']['g']
        except (FileNotFoundError, KeyError):
            dt_rc = np.zeros(8)
            rc_dl = 0
            rc_g = 0

        x = np.arange(8)
        w = 0.35

        bars_2c = ax.bar(x - w/2, dt_2c, w, color='steelblue', alpha=0.7,
                          edgecolor='navy', linewidth=0.8, label='2-Component')
        bars_rc = ax.bar(x + w/2, dt_rc, w, color='coral', alpha=0.7,
                          edgecolor='darkred', linewidth=0.8, label='R+C Model')

        ax.axhline(0, color='gray', lw=0.8, ls=':')
        ax.set_xticks(x)
        ax.set_xticklabels(COLOR_NAMES, fontsize=8, rotation=45, ha='right')
        ax.set_ylabel(r'$\Delta\theta$ (deg)', fontsize=10)
        ax.legend(fontsize=9)
        ax.grid(axis='y', alpha=0.2)

        # Correlation between the two
        r = np.corrcoef(dt_2c, dt_rc)[0, 1]
        ax.set_title(f"sub-{subj} ({cvd})\n"
                     f"2-Comp vs R+C: r={r:.2f}",
                     fontsize=10, fontweight='bold')

    fig.suptitle('2-Component vs R+C: Per-Color Delta-Theta Comparison',
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    out = output_dir / 'model_overlay_delta_theta.png'
    plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')


# ===========================================================================
# (4) R+C LOCO Validation Summary
# ===========================================================================

def rc_loco_summary(output_dir, subjects=('08', '09', '10')):
    """Summarize R+C LOCO validation results."""
    lines = []
    lines.append('=' * 90)
    lines.append('R+C MODEL LOCO VALIDATION SUMMARY')
    lines.append('=' * 90)
    lines.append(f"{'Subject':<8} {'CVD':<7} {'ROI':<5} {'dl_nm':>6} {'g':>7} "
                 f"{'rho_fit':>8} {'rho_base':>9} {'delta_rho':>10} {'p':>8} {'Sig':>5}")
    lines.append('-' * 90)

    all_data = {}
    for subj in subjects:
        try:
            data = load_rc(subj)
        except FileNotFoundError:
            continue
        all_data[subj] = data
        cvd = data['cvd_type']
        dl = data['best']['delta_v1_nm']
        g = data['best']['g']

        loco = data.get('loco_validation', {})
        for roi in ['V1', 'V2', 'V4']:
            if roi not in loco:
                continue
            lv = loco[roi]
            p = lv['label_p']
            sig = '***' if p < 0.01 else ('*' if p < 0.05 else
                  ('t' if p < 0.10 else 'NS'))
            lines.append(f"sub-{subj:<5} {cvd:<7} {roi:<5} {dl:6.1f} {g:7.2f} "
                         f"{lv['rho_fit']:8.3f} {lv['rho_base']:9.3f} "
                         f"{lv['delta_rho']:10.3f} {p:8.4f} {sig:>5}")

    # R+C overall stats
    lines.append('')
    lines.append('R+C DRDM SIGNIFICANCE:')
    for subj in subjects:
        if subj in all_data:
            d = all_data[subj]
            pn = d.get('permutation_null', {})
            p = pn.get('label_perm_p', 1.0)
            l3 = d['best'].get('l3_rc', 0)
            sig = '*' if p < 0.05 else ('t' if p < 0.10 else 'NS')
            lines.append(f"  sub-{subj} ({d['cvd_type']}): L3_RC={l3:.3f} "
                         f"perm_p={p:.4f} {sig}")

    text = '\n'.join(lines)
    print(text)
    out = output_dir / 'rc_loco_summary.txt'
    with open(out, 'w') as f:
        f.write(text)
    print(f'  Saved: {out}')

    return all_data


# ===========================================================================
# (5) Head-to-Head Comparison Figure
# ===========================================================================

def plot_head_to_head(output_dir, subjects=('08', '09')):
    """Comprehensive head-to-head: 2-Component vs R+C across all criteria."""
    panels = []
    for subj in subjects:
        try:
            d2c = load_2comp(subj)
            drc = load_rc(subj)
        except FileNotFoundError:
            continue

        # 2-Component stats
        v1_2c = d2c.get('V1', {})
        corr_cos = v1_2c.get('grid_correlation', {}).get('best_cosine', {})
        xnob_cos = v1_2c.get('grid_crossnobis', {}).get('best_cosine', {})
        p_corr = v1_2c.get('perm_correlation_cosine', {}).get('perm_p_cosine', 1.0)
        p_xnob = v1_2c.get('perm_crossnobis_cosine', {}).get('perm_p_cosine', 1.0)

        # R+C stats
        rc_best = drc['best']
        rc_perm = drc.get('permutation_null', {})
        rc_loco = drc.get('loco_validation', {})

        panels.append({
            'subj': subj,
            'cvd': d2c['cvd_type'],
            # 2-Component
            '2c_cos_corr': corr_cos.get('value', 0),
            '2c_cos_xnob': xnob_cos.get('value', 0),
            '2c_p_corr': p_corr,
            '2c_p_xnob': p_xnob,
            '2c_bs': corr_cos.get('beta_s', 0),
            '2c_bc': corr_cos.get('beta_c', 0),
            # R+C
            'rc_cos_v1': rc_best.get('cosine_full_V1', 0),
            'rc_cos_v2': rc_best.get('cosine_full_V2', 0),
            'rc_p': rc_perm.get('label_perm_p', 1.0),
            'rc_dl': rc_best.get('delta_v1_nm', 0),
            'rc_g': rc_best.get('g', 0),
            'rc_loco_v1_p': rc_loco.get('V1', {}).get('label_p', 1.0),
            'rc_loco_v4_p': rc_loco.get('V4', {}).get('label_p', 1.0),
        })

    if not panels:
        return

    # Create comparison table figure
    fig, ax = plt.subplots(figsize=(14, 4 + 1.5 * len(panels)))
    ax.axis('off')

    col_labels = ['Criterion', 'sub-08 (deutan)', 'sub-09 (protan)']
    row_data = []

    criteria = [
        ('DRDM Cosine (V1)', '2c_cos_corr', 'rc_cos_v1'),
        ('DRDM Perm p (V1)', '2c_p_corr', 'rc_p'),
        ('LOCO V1 p', None, 'rc_loco_v1_p'),
        ('LOCO hV4 p', None, 'rc_loco_v4_p'),
        ('Key params', None, None),
    ]

    cell_text = []
    row_labels = []
    for criterion_name, key_2c, key_rc in criteria:
        row_labels.append(criterion_name)
        row = []
        for panel in panels:
            if criterion_name == 'Key params':
                val = (f"2C: bs={panel['2c_bs']:.0f} bc={panel['2c_bc']:.0f}\n"
                       f"RC: dl={panel['rc_dl']:.1f}nm g={panel['rc_g']:.2f}")
            elif criterion_name.startswith('LOCO'):
                val_rc = panel.get(key_rc, 1.0)
                sig = '*' if val_rc < 0.05 else ('t' if val_rc < 0.10 else 'NS')
                val = f"R+C: p={val_rc:.3f} {sig}"
            else:
                val_2c = panel.get(key_2c, 0) if key_2c else 0
                val_rc = panel.get(key_rc, 0) if key_rc else 0
                if 'p' in criterion_name.lower():
                    sig_2c = '*' if val_2c < 0.05 else ('t' if val_2c < 0.10 else 'NS')
                    sig_rc = '*' if val_rc < 0.05 else ('t' if val_rc < 0.10 else 'NS')
                    val = f"2C: {val_2c:.3f}{sig_2c}  RC: {val_rc:.3f}{sig_rc}"
                else:
                    val = f"2C: {val_2c:.3f}  RC: {val_rc:.3f}"
            row.append(val)
        cell_text.append(row)

    table = ax.table(cellText=cell_text,
                     rowLabels=row_labels,
                     colLabels=[f"sub-{p['subj']} ({p['cvd']})" for p in panels],
                     cellLoc='center', rowLoc='right',
                     loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 2.0)

    # Color significant cells
    for i, (cname, _, _) in enumerate(criteria):
        for j, panel in enumerate(panels):
            cell = table[i + 1, j]
            text = cell_text[i][j]
            if '*' in text and 'NS' not in text:
                cell.set_facecolor('#e8f5e9')
            elif 'NS' in text:
                cell.set_facecolor('#fff3e0')

    ax.set_title('Head-to-Head: 2-Component vs R+C Model\n'
                 'Green = significant | Orange = NS',
                 fontsize=12, fontweight='bold', pad=20)

    out = output_dir / 'head_to_head_comparison.png'
    plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')

    return panels


# ===========================================================================
# (6) Continuous Model Comparison
# ===========================================================================

def plot_continuous_comparison(output_dir, subjects=('08', '09')):
    """Overlay 2-component continuous curve with R+C discrete points."""
    orig_rgb = get_stim_rgb()
    n = len(subjects)
    fig, axes = plt.subplots(1, n, figsize=(7 * n, 5))
    if n == 1:
        axes = [axes]

    theta_fine = np.linspace(0, 360, 361)

    for idx, subj in enumerate(subjects):
        ax = axes[idx]

        # 2-Component continuous
        try:
            data_2c = load_2comp(subj)
            cvd = data_2c['cvd_type']
            dt_2c = np.array(data_2c['delta_theta_deg'])
            hue_base = np.array(data_2c['hue_base_deg'])
            v1_cos = data_2c.get('V1', {}).get('grid_correlation', {}).get('best_cosine', {})
            beta_s = v1_cos.get('beta_s', 0)
            beta_c = v1_cos.get('beta_c', 0)
        except FileNotFoundError:
            continue

        theta_conf = CONF_AXIS[cvd]
        dt_model = (beta_s * np.cos(np.radians(theta_fine - 90.0))
                    + beta_c * np.cos(np.radians(theta_fine - theta_conf)))

        ax.plot(theta_fine, dt_model, '-', color='steelblue', lw=2.5,
                label=f'2-Comp (bs={beta_s:.0f}, bc={beta_c:.0f})', zorder=8)
        ax.scatter(hue_base, dt_2c, s=120, c=[orig_rgb[j] for j in range(8)],
                   edgecolors='navy', linewidths=2, zorder=15,
                   label='2-Comp data')

        # R+C discrete points
        try:
            data_rc = load_rc(subj)
            diag = data_rc.get('opponent_gain_diagnostic', {})
            hue_base_rc = np.array(diag['hue_baseline_deg'])
            hue_final_rc = np.array(diag['hue_final_deg'])
            dt_rc = ((hue_final_rc - hue_base_rc + 180) % 360 - 180)
            rc_dl = data_rc['best']['delta_v1_nm']
            rc_g = data_rc['best']['g']
            ax.scatter(hue_base_rc, dt_rc, s=120, c=[orig_rgb[j] for j in range(8)],
                       edgecolors='darkred', linewidths=2, zorder=14, marker='D',
                       label=f'R+C (dl={rc_dl:.1f}, g={rc_g:.2f})')
        except (FileNotFoundError, KeyError):
            pass

        ax.axhline(0, color='gray', lw=0.5, ls=':')
        ax.axvline(90, color='blue', alpha=0.3, lw=1, ls='--')
        ax.axvline(theta_conf, color='red', alpha=0.3, lw=1, ls='--')

        for j in range(8):
            ax.axvline(hue_base[j], color=orig_rgb[j], alpha=0.15, lw=6)

        ax.set_xlabel('Stockman Opponent Hue Angle (deg)', fontsize=10)
        ax.set_ylabel(r'$\Delta\theta$ (deg)', fontsize=10)
        ax.set_xlim(0, 360)
        ax.legend(fontsize=7, loc='best')
        ax.grid(alpha=0.2)
        ax.set_title(f"sub-{subj} ({cvd})", fontsize=10, fontweight='bold')

    fig.suptitle('2-Component Continuous Model vs R+C Discrete Predictions\n'
                 'Circles=2-Comp | Diamonds=R+C | Curve=2-Comp model',
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    out = output_dir / 'continuous_model_comparison.png'
    plt.savefig(out, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'  Saved: {out}')


# ===========================================================================
# Main
# ===========================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Comprehensive validation with v2 results')
    parser.add_argument('--output_dir', type=str,
                        default='results/validation_v2')
    parser.add_argument('--subjects', nargs='+', default=['08', '09', '10'])
    args = parser.parse_args()

    output_dir = _PIPE_DIR / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 70)
    print('v2 Comprehensive Validation: 2-Component + R+C Models')
    print(f'Timestamp: {datetime.now().isoformat()}')
    print(f'Output: {output_dir}')
    print('=' * 70)

    # (1) Metric comparison
    print('\n[1] Updated Metric Comparison (v2)')
    print('-' * 50)
    rows = metric_comparison_v2(args.subjects)
    print_metric_table_v2(rows, output_dir / 'metric_comparison_v2.txt')

    cvd_subjects = [s for s in args.subjects if s != '10']

    # (2) Bootstrap CI
    print('\n[2] Bootstrap CI Visualization')
    print('-' * 50)
    print('  [2a] Histograms...')
    plot_bootstrap_ci(output_dir, cvd_subjects)
    print('  [2b] Joint scatter...')
    plot_bootstrap_scatter(output_dir, cvd_subjects)

    # (3) Model comparison
    print('\n[3] Model Comparison Visualizations')
    print('-' * 50)
    print('  [3a] Side-by-side bars...')
    plot_model_comparison_bars(output_dir, cvd_subjects)
    print('  [3b] Overlay bars...')
    plot_model_overlay(output_dir, cvd_subjects)
    print('  [3c] Continuous comparison...')
    plot_continuous_comparison(output_dir, cvd_subjects)

    # (4) R+C LOCO validation
    print('\n[4] R+C LOCO Validation Summary')
    print('-' * 50)
    rc_data = rc_loco_summary(output_dir, args.subjects)

    # (5) Head-to-head
    print('\n[5] Head-to-Head Comparison')
    print('-' * 50)
    h2h = plot_head_to_head(output_dir, cvd_subjects)

    # Print final model recommendation
    print('\n' + '=' * 70)
    print('MODEL RECOMMENDATION SUMMARY')
    print('=' * 70)
    print()
    print('2-COMPONENT ANGULAR DILATION:')
    print('  Strengths: Interpretable params (beta_s ~ Emery 2021)')
    print('             Cross-subject S-cone convergence')
    print('             Bootstrap CIs exclude 0 (both subjects beta_s)')
    print('             Continuous model function for prediction')
    print('  Weaknesses: V1 only (V2 weaker)')
    print('              Filter fails Machado simulation')
    print('              Sub-10 V1 false positive')
    print()
    print('R+C MODEL (RETINAL + CORTICAL GAIN):')
    print('  Strengths: Mechanistic link to Machado')
    print('             Sub-09 DRDM p=0.026*')
    print('             Sub-08 V1 LOCO p=0.047*')
    print('             Sub-10: g=0 (perfect null)')
    print('  Weaknesses: Sub-08 g=-2.25 (biologically extreme)')
    print('              Sub-09 LOCO validation fails (rho negative)')
    print('              Sub-08 DRDM p=0.179 (NS)')
    print()
    print(f'All outputs saved to: {output_dir}')
    print('=' * 70)


if __name__ == '__main__':
    main()
