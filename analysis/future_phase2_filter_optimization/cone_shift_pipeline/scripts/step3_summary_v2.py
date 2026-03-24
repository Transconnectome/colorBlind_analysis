#!/usr/bin/env python3
"""
step3_summary_v2.py — Summary and visualization for cone-shift pipeline v2.

Generates:
  1. Cross-criterion convergence figure
  2. Model comparison (AICc) bar chart
  3. 7-fold consistency box plot
  4. Per-CVD-subject profile comparison
  5. Per-color residual overlay
  6. MSE decomposition (bias vs profile)

Usage:
    python scripts/step3_summary_v2.py \
        --rdm_dir results/v2/step1_rdm \
        --loco_dir results/v2/step1_loco \
        --cross_dir results/v2/step2_cross \
        --output_dir results/v2/figures
"""

import argparse
import json
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import sys
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import HC_SUBJECTS, CVD_SUBJECTS

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']
COLOR_HEX = ['#E53935', '#FB8C00', '#FDD835', '#43A047',
             '#00ACC1', '#1E88E5', '#8E24AA', '#D81B60']


def load_json(path):
    with open(path) as f:
        return json.load(f)


# ============================================================================
# Figure 1: Cross-criterion convergence (δθ comparison)
# ============================================================================

def plot_convergence(cross_data, output_dir, cvd_subj, roi):
    """Plot RDM-fit vs LOCO-fit δθ per model."""
    models = cross_data.get('models', {})
    if not models:
        return

    fig, axes = plt.subplots(1, len(models), figsize=(4 * len(models), 4),
                             squeeze=False)
    axes = axes.ravel()

    for idx, (model_name, mdata) in enumerate(models.items()):
        ax = axes[idx]
        conv = mdata.get('convergence', {})
        rdm_dt = conv.get('rdm_delta_theta', [])
        loco_dt = conv.get('loco_delta_theta', [])

        if not rdm_dt or not loco_dt:
            ax.set_title(f'{model_name}\n(no data)')
            continue

        x = np.arange(8)
        ax.bar(x - 0.15, rdm_dt, 0.3, label='RDM-fit', alpha=0.8,
               color='steelblue')
        ax.bar(x + 0.15, loco_dt, 0.3, label='LOCO-fit', alpha=0.8,
               color='coral')
        ax.set_xticks(x)
        ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=7)
        ax.set_ylabel('δθ (degrees)')
        ax.axhline(0, color='gray', linewidth=0.5)

        status = 'CONV' if conv.get('converged') else 'DIV'
        rmsd = conv.get('rmsd_degrees', 0)
        ax.set_title(f'{model_name}\nRMSD={rmsd:.1f}° [{status}]',
                     fontsize=10)
        ax.legend(fontsize=7)

    fig.suptitle(f'Cross-Criterion Convergence — sub-{cvd_subj} {roi}',
                 fontsize=12, fontweight='bold')
    plt.tight_layout()
    out = Path(output_dir) / f'sub-{cvd_subj}_{roi}_convergence.png'
    plt.savefig(out, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {out}')


# ============================================================================
# Figure 2: Model comparison (AICc)
# ============================================================================

def plot_model_comparison(rdm_data, output_dir, cvd_subj, roi):
    """Bar chart of AICc per model (path A and path B)."""
    agg = rdm_data.get('aggregate', {})
    if not agg:
        return

    models_a = {k.replace('_path_A', ''): v for k, v in agg.items()
                if '_path_A' in k}
    models_b = {k.replace('_path_B', ''): v for k, v in agg.items()
                if '_path_B' in k}

    model_names = sorted(set(list(models_a.keys()) + list(models_b.keys())))
    if not model_names:
        return

    x = np.arange(len(model_names))
    aicc_a = [models_a.get(m, {}).get('aicc_median', np.nan)
              for m in model_names]
    aicc_b = [models_b.get(m, {}).get('aicc_median', np.nan)
              for m in model_names]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(x - 0.15, aicc_a, 0.3, label='Path A (GP)',
           color='steelblue', alpha=0.8)
    ax.bar(x + 0.15, aicc_b, 0.3, label='Path B (Ridge)',
           color='coral', alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(model_names, rotation=30, ha='right')
    ax.set_ylabel('AICc (median over 7 folds)')
    ax.set_title(f'Model Comparison — sub-{cvd_subj} {roi}')
    ax.legend()
    ax.axhline(0, color='gray', linewidth=0.5, linestyle='--')

    plt.tight_layout()
    out = Path(output_dir) / f'sub-{cvd_subj}_{roi}_model_comp.png'
    plt.savefig(out, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {out}')


# ============================================================================
# Figure 3: 7-fold consistency (RDM) and 7-HC consistency (LOCO)
# ============================================================================

def plot_consistency(rdm_data, loco_data, output_dir, cvd_subj, roi):
    """Box plots of parameter consistency across folds/HC subjects."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # RDM: 7-fold params for cone_1way path_A
    folds = rdm_data.get('folds', [])
    if folds:
        params_by_model = {}
        for fold in folds:
            for m, mdata in fold.get('models', {}).items():
                if m not in params_by_model:
                    params_by_model[m] = {'A': [], 'B': []}
                pa = mdata.get('path_A', {}).get('params', [])
                pb = mdata.get('path_B', {}).get('params', [])
                if pa:
                    params_by_model[m]['A'].append(pa[0] if len(pa) == 1 else pa)
                if pb:
                    params_by_model[m]['B'].append(pb[0] if len(pb) == 1 else pb)

        # Plot cone_1way Δλ across folds
        if 'cone_1way' in params_by_model:
            bp = ax1.boxplot(
                [params_by_model['cone_1way']['A'],
                 params_by_model['cone_1way']['B']],
                labels=['Path A (GP)', 'Path B (Ridge)'],
                patch_artist=True)
            bp['boxes'][0].set_facecolor('steelblue')
            bp['boxes'][1].set_facecolor('coral')
            for b in bp['boxes']:
                b.set_alpha(0.6)

    ax1.set_ylabel('Δλ (nm)')
    ax1.set_title(f'RDM: 7-fold Consistency\n(cone_1way)')

    # LOCO: per-HC params for cone_1way
    per_hc = loco_data.get('per_hc', {})
    if per_hc:
        cone1_params = []
        for subj, hc_data in per_hc.items():
            if 'cone_1way' in hc_data:
                p = hc_data['cone_1way'].get('params', [])
                if p:
                    cone1_params.append(p[0])

        if cone1_params:
            ax2.boxplot([cone1_params], labels=['cone_1way'],
                        patch_artist=True,
                        boxprops=dict(facecolor='mediumpurple', alpha=0.6))
            for val in cone1_params:
                ax2.plot(1, val, 'ko', alpha=0.5, markersize=5)

    ax2.set_ylabel('Δλ (nm)')
    ax2.set_title(f'LOCO: 7-HC Consistency\n(cone_1way)')

    fig.suptitle(f'Parameter Consistency — sub-{cvd_subj} {roi}',
                 fontsize=12, fontweight='bold')
    plt.tight_layout()
    out = Path(output_dir) / f'sub-{cvd_subj}_{roi}_consistency.png'
    plt.savefig(out, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {out}')


# ============================================================================
# Figure 4: Per-color vulnerability overlay
# ============================================================================

def plot_vulnerability_overlay(loco_data, cross_data, output_dir,
                               cvd_subj, roi):
    """Overlay CVD actual vs HC shifted vulnerability profiles."""
    cvd_vuln = loco_data.get('cvd_loco_target')
    if cvd_vuln is None:
        return

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    x = np.arange(8)

    # --- Left: per-HC scatter for best model ---
    ax = axes[0]
    per_hc = loco_data.get('per_hc', {})
    best_model = 'cone_1way'
    ax.bar(x, cvd_vuln, 0.6, alpha=0.3, color='gray', label='CVD actual')

    for subj in sorted(per_hc.keys()):
        hc_data = per_hc[subj].get(best_model, {})
        hc_vuln = hc_data.get('hc_shifted_vuln')
        if hc_vuln:
            ax.plot(x, hc_vuln, 'o-', alpha=0.4, markersize=4,
                    label=f'HC-{subj}')

    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=8)
    ax.set_ylabel('LOCO voxel correlation')
    ax.set_title(f'{best_model}: Per-HC shifted vulnerability')
    ax.legend(fontsize=6, ncol=2)
    ax.axhline(0, color='gray', linewidth=0.5)

    # --- Right: cross-eval A→B overlay ---
    ax2 = axes[1]
    models_cross = cross_data.get('models', {})
    ax2.bar(x, cvd_vuln, 0.6, alpha=0.3, color='gray', label='CVD actual')

    colors_model = {'cone_1way': 'steelblue', 'cone_3way': 'coral',
                    'fourier': 'green', 'per_color': 'purple'}

    for model_name, mdata in models_cross.items():
        a2b = mdata.get('A_to_B', {}).get('per_hc', {})
        if not a2b:
            continue
        # Mean across HC
        all_vuln = [v.get('hc_vuln', []) for v in a2b.values()]
        all_vuln = [v for v in all_vuln if v]
        if all_vuln:
            mean_vuln = np.mean(all_vuln, axis=0)
            ax2.plot(x, mean_vuln, 's-', alpha=0.7, markersize=5,
                     color=colors_model.get(model_name, 'black'),
                     label=f'{model_name} (A→B)')

    ax2.set_xticks(x)
    ax2.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=8)
    ax2.set_ylabel('LOCO voxel correlation')
    ax2.set_title('Cross-eval: RDM-fit δθ → LOCO')
    ax2.legend(fontsize=7)
    ax2.axhline(0, color='gray', linewidth=0.5)

    fig.suptitle(f'Vulnerability Profile — sub-{cvd_subj} {roi}',
                 fontsize=12, fontweight='bold')
    plt.tight_layout()
    out = Path(output_dir) / f'sub-{cvd_subj}_{roi}_vuln_overlay.png'
    plt.savefig(out, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {out}')


# ============================================================================
# Figure 5: MSE decomposition
# ============================================================================

def plot_mse_decomposition(loco_data, output_dir, cvd_subj, roi):
    """Stacked bar: bias² vs profile MSE per model."""
    agg = loco_data.get('aggregate', {})
    per_hc = loco_data.get('per_hc', {})
    if not per_hc:
        return

    model_names = sorted(agg.keys())
    if not model_names:
        return

    bias_vals = []
    prof_vals = []
    for m in model_names:
        biases = []
        profs = []
        for subj, hc_data in per_hc.items():
            if m in hc_data:
                biases.append(hc_data[m].get('bias_sq', 0))
                profs.append(hc_data[m].get('profile_mse', 0))
        bias_vals.append(np.median(biases) if biases else 0)
        prof_vals.append(np.median(profs) if profs else 0)

    x = np.arange(len(model_names))
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(x, bias_vals, 0.6, label='Bias²', color='steelblue', alpha=0.8)
    ax.bar(x, prof_vals, 0.6, bottom=bias_vals, label='Profile MSE',
           color='coral', alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(model_names, rotation=30, ha='right')
    ax.set_ylabel('MSE (median over 7 HC)')
    ax.set_title(f'MSE Decomposition — sub-{cvd_subj} {roi}')
    ax.legend()

    plt.tight_layout()
    out = Path(output_dir) / f'sub-{cvd_subj}_{roi}_mse_decomp.png'
    plt.savefig(out, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {out}')


# ============================================================================
# Summary table (text)
# ============================================================================

def print_summary_table(rdm_data, loco_data, cross_data, cvd_subj, roi):
    """Print compact summary table."""
    print(f'\n  {"="*70}')
    print(f'  SUMMARY: sub-{cvd_subj} {roi}')
    print(f'  {"="*70}')

    # RDM aggregate
    rdm_agg = rdm_data.get('aggregate', {})
    print(f'  RDM (7-fold):')
    for key, val in sorted(rdm_agg.items()):
        print(f'    {key}: r_med={val.get("spearman_r_median", "?"):.3f} '
              f'AICc_med={val.get("aicc_median", "?"):.1f}')

    # LOCO aggregate
    loco_agg = loco_data.get('aggregate', {})
    print(f'  LOCO (7-HC):')
    for m, val in sorted(loco_agg.items()):
        print(f'    {m}: MSE_med={val.get("mse_median", "?"):.4f} '
              f'CCC_med={val.get("ccc_median", "?"):.3f} '
              f'perm_p_med={val.get("perm_p_median", "?"):.3f}')

    # Cross-eval
    cross_models = cross_data.get('models', {})
    print(f'  Cross-eval:')
    for m, mdata in sorted(cross_models.items()):
        conv = mdata.get('convergence', {})
        a2b = mdata.get('A_to_B', {})
        b2a = mdata.get('B_to_A', {})
        print(f'    {m}: '
              f'A→B MSE={a2b.get("mse_median", "?"):.4f} '
              f'B→A r={b2a.get("spearman_r_median", "?"):.3f} '
              f'conv={conv.get("converged", "?")}')


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Step 3: Summary and visualization (v2)')
    parser.add_argument('--rdm_dir', type=str,
                        default='results/v2/step1_rdm')
    parser.add_argument('--loco_dir', type=str,
                        default='results/v2/step1_loco')
    parser.add_argument('--cross_dir', type=str,
                        default='results/v2/step2_cross')
    parser.add_argument('--output_dir', type=str,
                        default='results/v2/figures')
    parser.add_argument('--rois', nargs='+', default=['V4'])
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    args = parser.parse_args()

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('Step 3: Summary and Visualization (v2)')
    print('=' * 60)

    for roi in args.rois:
        for cvd_subj in args.cvd_subjects:
            print(f'\n--- sub-{cvd_subj} {roi} ---')

            # Load results
            rdm_path = Path(args.rdm_dir) / roi / f'sub-{cvd_subj}_rdm_v2.json'
            loco_path = Path(args.loco_dir) / roi / f'sub-{cvd_subj}_loco_v2.json'
            cross_path = Path(args.cross_dir) / roi / f'sub-{cvd_subj}_cross_v2.json'

            rdm_data = load_json(rdm_path) if rdm_path.exists() else {}
            loco_data = load_json(loco_path) if loco_path.exists() else {}
            cross_data = load_json(cross_path) if cross_path.exists() else {}

            if not rdm_data and not loco_data:
                print('  No results found, skipping.')
                continue

            # Summary table
            print_summary_table(rdm_data, loco_data, cross_data,
                                cvd_subj, roi)

            # Generate figures
            if cross_data:
                plot_convergence(cross_data, args.output_dir, cvd_subj, roi)
            if rdm_data:
                plot_model_comparison(rdm_data, args.output_dir, cvd_subj, roi)
            if rdm_data and loco_data:
                plot_consistency(rdm_data, loco_data, args.output_dir,
                                 cvd_subj, roi)
            if loco_data and cross_data:
                plot_vulnerability_overlay(loco_data, cross_data,
                                           args.output_dir, cvd_subj, roi)
            if loco_data:
                plot_mse_decomposition(loco_data, args.output_dir,
                                       cvd_subj, roi)

    print('\nStep 3 (Summary v2) complete.')


if __name__ == '__main__':
    main()
