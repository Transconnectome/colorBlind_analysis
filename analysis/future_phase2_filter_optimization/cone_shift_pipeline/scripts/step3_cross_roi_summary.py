#!/usr/bin/env python3
"""
step3_cross_roi_summary.py — Cross-ROI summary and visualization.

Generates:
  1. Cross-ROI delta_lambda comparison table
  2. Between-ROI cross-evaluation results
  3. W-fixed vs shift_at_both comparison (V4)
  4. RDM criterion: V1/V2 vs V4 comparison
  5. SRM baseline vs cone-shift improvement
  6. Summary figures

Usage:
    python scripts/step3_cross_roi_summary.py \
        --rdm_dir results/v2/step1_rdm \
        --loco_dir results/v2/step1_loco_wfixed \
        --cross_dir results/v2/step2_cross \
        --cross_roi_dir results/v2/step2b_cross_roi \
        --baseline_dir_srm results/v2/srm_baseline \
        --loco_legacy_dir results/v2/step1_loco \
        --output_dir results/v2/cross_roi_figures
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
    if not Path(path).exists():
        return {}
    with open(path) as f:
        return json.load(f)


# ============================================================================
# Figure 1: Cross-ROI delta_lambda comparison
# ============================================================================

def plot_cross_roi_deltas(all_results, output_dir):
    """Bar chart comparing delta_lambda across ROIs for each CVD subject."""
    rois = ['V1', 'V2', 'V4']
    criteria = ['RDM', 'LOCO']

    for cvd_subj in CVD_SUBJECTS:
        fig, ax = plt.subplots(figsize=(8, 4))
        x = np.arange(len(rois))
        width = 0.35

        rdm_deltas = []
        rdm_sds = []
        loco_deltas = []

        for roi in rois:
            # RDM delta
            rdm_data = all_results.get(f'rdm_{roi}_{cvd_subj}', {})
            agg = rdm_data.get('aggregate', {})
            key = 'cone_1way_path_A'
            if key in agg:
                rdm_deltas.append(agg[key]['params_median'][0])
                rdm_sds.append(agg[key]['params_sd'][0])
            else:
                rdm_deltas.append(np.nan)
                rdm_sds.append(0)

            # LOCO delta
            loco_data = all_results.get(f'loco_{roi}_{cvd_subj}', {})
            fits = loco_data.get('fit_results', {})
            if 'cone_1way' in fits:
                loco_deltas.append(fits['cone_1way']['params'][0])
            else:
                loco_deltas.append(np.nan)

        rdm_deltas = np.array(rdm_deltas)
        loco_deltas = np.array(loco_deltas)
        rdm_sds = np.array(rdm_sds)

        mask_rdm = ~np.isnan(rdm_deltas)
        mask_loco = ~np.isnan(loco_deltas)

        if mask_rdm.any():
            ax.bar(x[mask_rdm] - width/2, rdm_deltas[mask_rdm], width,
                   yerr=rdm_sds[mask_rdm], label='RDM (median +/- SD)',
                   color='steelblue', alpha=0.8, capsize=3)
        if mask_loco.any():
            ax.bar(x[mask_loco] + width/2, loco_deltas[mask_loco], width,
                   label='LOCO (W-fixed)', color='coral', alpha=0.8)

        ax.set_xticks(x)
        ax.set_xticklabels(rois)
        ax.set_ylabel('Fitted Δλ (nm)')
        ax.set_title(f'Cross-ROI Cone Shift — sub-{cvd_subj} '
                     f'({CVD_TYPE[cvd_subj]})')
        ax.legend()
        ax.axhline(0, color='gray', linewidth=0.5, linestyle='--')

        plt.tight_layout()
        out = Path(output_dir) / f'sub-{cvd_subj}_cross_roi_deltas.png'
        plt.savefig(out, dpi=200, bbox_inches='tight')
        plt.close()
        print(f'  Saved: {out}')


# ============================================================================
# Figure 2: Between-ROI cross-evaluation
# ============================================================================

def plot_cross_roi_eval(all_results, output_dir):
    """Visualize between-ROI cross-evaluation results."""
    for cvd_subj in CVD_SUBJECTS:
        cross_data = all_results.get(f'cross_roi_{cvd_subj}', {})
        if not cross_data:
            continue

        cross_results = cross_data.get('cross_results', {})
        if not cross_results:
            continue

        src_rois = sorted(cross_results.keys())
        fig, axes = plt.subplots(1, len(src_rois), figsize=(6*len(src_rois), 5),
                                 squeeze=False)
        axes = axes.ravel()
        x = np.arange(8)

        cvd_vuln = cross_data.get('cvd_vuln_target', [0]*8)

        for idx, src_roi in enumerate(src_rois):
            ax = axes[idx]
            cr = cross_results[src_roi]

            ax.bar(x, cvd_vuln, 0.6, alpha=0.3, color='gray',
                   label='CVD V4 actual')

            # Forward: source RDM -> target LOCO
            fwd = cr.get('forward_rdm_to_loco')
            if fwd and 'mean_hc_vuln' in fwd:
                ax.plot(x, fwd['mean_hc_vuln'], 'o-',
                        color='steelblue', markersize=5, linewidth=1.5,
                        label=f'{src_roi} RDM→V4 LOCO\n'
                              f'r={fwd["spearman_r"]:.3f} '
                              f'p={fwd["perm_p_spearman"]:.3f}')

            # Cross-LOCO
            cl = cr.get('cross_loco')
            if cl and 'mean_hc_vuln' in cl:
                ax.plot(x, cl['mean_hc_vuln'], 's--',
                        color='coral', markersize=5, linewidth=1.5,
                        label=f'{src_roi} LOCO→V4 LOCO\n'
                              f'r={cl["spearman_r"]:.3f} '
                              f'p={cl["perm_p_spearman"]:.3f}')

            ax.set_xticks(x)
            ax.set_xticklabels(COLOR_NAMES, rotation=45, ha='right',
                               fontsize=7)
            ax.set_ylabel('Voxel correlation')
            ax.set_title(f'{src_roi} → V4')
            ax.legend(fontsize=7)
            ax.axhline(0, color='gray', linewidth=0.5)

        fig.suptitle(f'Between-ROI Cross-Evaluation — sub-{cvd_subj} '
                     f'({CVD_TYPE[cvd_subj]})',
                     fontsize=12, fontweight='bold')
        plt.tight_layout()
        out = Path(output_dir) / f'sub-{cvd_subj}_cross_roi_eval.png'
        plt.savefig(out, dpi=200, bbox_inches='tight')
        plt.close()
        print(f'  Saved: {out}')


# ============================================================================
# Figure 3: W-fixed vs shift_at_both comparison (V4)
# ============================================================================

def plot_wfixed_vs_legacy(all_results, output_dir):
    """Compare W-fixed and legacy (shift_at_both) LOCO results for V4."""
    for cvd_subj in CVD_SUBJECTS:
        wfixed = all_results.get(f'loco_V4_{cvd_subj}', {})
        legacy = all_results.get(f'loco_legacy_V4_{cvd_subj}', {})

        if not wfixed or not legacy:
            continue

        wf_fits = wfixed.get('fit_results', {})
        lg_fits = legacy.get('fit_results', {})

        if 'cone_1way' not in wf_fits or 'cone_1way' not in lg_fits:
            continue

        wf = wf_fits['cone_1way']
        lg = lg_fits['cone_1way']

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        x = np.arange(8)

        cvd_vuln = wfixed.get('cvd_loco_target', [0]*8)

        # Left: vulnerability profiles
        ax1.bar(x, cvd_vuln, 0.6, alpha=0.3, color='gray',
                label='CVD actual')
        ax1.plot(x, wf.get('mean_hc_vuln', [0]*8), 'o-',
                 color='steelblue', markersize=5, linewidth=1.5,
                 label=f'W-fixed (r={wf["spearman_r"]:.3f}, '
                       f'p={wf["perm_p_spearman"]:.3f})')
        ax1.plot(x, lg.get('mean_hc_vuln', [0]*8), 's--',
                 color='coral', markersize=5, linewidth=1.5,
                 label=f'Legacy (r={lg["spearman_r"]:.3f}, '
                       f'p={lg["perm_p_spearman"]:.3f})')
        ax1.set_xticks(x)
        ax1.set_xticklabels(COLOR_NAMES, rotation=45, ha='right', fontsize=8)
        ax1.set_ylabel('LOCO voxel correlation')
        ax1.set_title('Vulnerability Profiles')
        ax1.legend(fontsize=7)
        ax1.axhline(0, color='gray', linewidth=0.5)

        # Right: landscape comparison (if available)
        wf_land = wfixed.get('landscape_cone_1way', {})
        lg_land = legacy.get('landscape_cone_1way', {})
        if wf_land and lg_land:
            ax2.plot(wf_land['delta_range'], wf_land['spearman_r'],
                     '-', color='steelblue', linewidth=1.5,
                     label=f'W-fixed (peak: '
                           f'{wf["params"][0]:.1f}nm)')
            ax2.plot(lg_land['delta_range'], lg_land['spearman_r'],
                     '--', color='coral', linewidth=1.5,
                     label=f'Legacy (peak: '
                           f'{lg["params"][0]:.1f}nm)')
            ax2.set_xlabel('Δλ (nm)')
            ax2.set_ylabel('Spearman ρ')
            ax2.set_title('Landscape: Spearman r vs Δλ')
            ax2.legend(fontsize=8)
            ax2.axhline(0, color='gray', linewidth=0.5, linestyle='--')
        else:
            ax2.text(0.5, 0.5, 'No landscape data',
                     ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Landscape (not computed)')

        fig.suptitle(f'W-fixed vs Legacy — sub-{cvd_subj} V4 '
                     f'({CVD_TYPE[cvd_subj]})',
                     fontsize=12, fontweight='bold')
        plt.tight_layout()
        out = Path(output_dir) / f'sub-{cvd_subj}_V4_wfixed_vs_legacy.png'
        plt.savefig(out, dpi=200, bbox_inches='tight')
        plt.close()
        print(f'  Saved: {out}')


# ============================================================================
# Summary table (text)
# ============================================================================

def print_master_summary(all_results):
    """Print comprehensive cross-ROI summary table."""
    rois = ['V1', 'V2', 'V4']

    print(f'\n{"="*80}')
    print('MASTER SUMMARY: Cone-Shift Pipeline V1/V2 Extension')
    print(f'{"="*80}')

    # Table 1: Fitted delta_lambda
    print(f'\n  Table 1: Fitted Δλ (nm) — cone_1way')
    print(f'  {"Subject":>10} | {"ROI":>4} | {"RDM":>12} | {"LOCO":>12} | '
          f'{"RDM p":>7} | {"LOCO p":>7}')
    print(f'  {"-"*10}-+-{"-"*4}-+-{"-"*12}-+-{"-"*12}-+-{"-"*7}-+-{"-"*7}')

    for cvd_subj in CVD_SUBJECTS:
        for roi in rois:
            rdm_data = all_results.get(f'rdm_{roi}_{cvd_subj}', {})
            loco_data = all_results.get(f'loco_{roi}_{cvd_subj}', {})

            rdm_delta = '—'
            rdm_p = '—'
            loco_delta = '—'
            loco_p = '—'

            agg = rdm_data.get('aggregate', {})
            key = 'cone_1way_path_A'
            if key in agg:
                rdm_delta = f'{agg[key]["params_median"][0]:.2f}'
                rdm_p = f'{agg[key]["spearman_r_median"]:.3f}'

            fits = loco_data.get('fit_results', {})
            if 'cone_1way' in fits:
                loco_delta = f'{fits["cone_1way"]["params"][0]:.2f}'
                loco_p = f'{fits["cone_1way"]["perm_p_spearman"]:.4f}'

            print(f'  sub-{cvd_subj:>5} | {roi:>4} | {rdm_delta:>12} | '
                  f'{loco_delta:>12} | {rdm_p:>7} | {loco_p:>7}')

    # Table 2: Cross-ROI cross-evaluation
    print(f'\n  Table 2: Between-ROI Cross-Evaluation')
    print(f'  {"Subject":>10} | {"Source":>6} | {"Direction":>15} | '
          f'{"rho":>6} | {"perm_p":>7} | {"Δλ_src":>7} | {"Δλ_tgt":>7}')
    print(f'  {"-"*10}-+-{"-"*6}-+-{"-"*15}-+-{"-"*6}-+-{"-"*7}-+-'
          f'{"-"*7}-+-{"-"*7}')

    for cvd_subj in CVD_SUBJECTS:
        cross_data = all_results.get(f'cross_roi_{cvd_subj}', {})
        cross_results = cross_data.get('cross_results', {})
        for src_roi, cr in cross_results.items():
            fwd = cr.get('forward_rdm_to_loco')
            if fwd:
                rdm_p = cr.get('rdm_params', [None])
                v4_p = cr.get('v4_loco_params', [None])
                print(f'  sub-{cvd_subj:>5} | {src_roi:>6} | '
                      f'{"RDM→V4 LOCO":>15} | '
                      f'{fwd["spearman_r"]:>6.3f} | '
                      f'{fwd["perm_p_spearman"]:>7.4f} | '
                      f'{rdm_p[0] if rdm_p[0] else "—":>7} | '
                      f'{v4_p[0] if v4_p[0] else "—":>7}')

    # Table 3: SRM baseline
    print(f'\n  Table 3: SRM Baseline Prediction Quality')
    print(f'  {"ROI":>4} | {"Pred RDM r":>10} | {"Z corr":>8} | '
          f'{"Inter-run r":>11}')
    print(f'  {"-"*4}-+-{"-"*10}-+-{"-"*8}-+-{"-"*11}')

    for roi in rois:
        baseline = all_results.get(f'srm_baseline_{roi}', {})
        agg = baseline.get('aggregate', {})
        pred_r = agg.get('rdm_rho_pred_held', {}).get('mean', float('nan'))
        z_c = agg.get('z_corr_pred_held', {}).get('mean', float('nan'))
        ir = agg.get('inter_run_rdm_rho_mean', {}).get('mean', float('nan'))
        print(f'  {roi:>4} | {pred_r:>10.3f} | {z_c:>8.3f} | {ir:>11.3f}')


def main():
    parser = argparse.ArgumentParser(
        description='Step 3b: Cross-ROI summary and visualization')
    parser.add_argument('--rdm_dir', type=str,
                        default='results/v2/step1_rdm')
    parser.add_argument('--loco_dir', type=str,
                        default='results/v2/step1_loco_wfixed')
    parser.add_argument('--cross_dir', type=str,
                        default='results/v2/step2_cross')
    parser.add_argument('--cross_roi_dir', type=str,
                        default='results/v2/step2b_cross_roi')
    parser.add_argument('--baseline_dir_srm', type=str,
                        default='results/v2/srm_baseline')
    parser.add_argument('--loco_legacy_dir', type=str,
                        default='results/v2/step1_loco')
    parser.add_argument('--output_dir', type=str,
                        default='results/v2/cross_roi_figures')
    parser.add_argument('--rois', nargs='+', default=['V1', 'V2', 'V4'])
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    args = parser.parse_args()

    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('Step 3b: Cross-ROI Summary and Visualization')
    print('=' * 60)

    # Load all results
    all_results = {}

    for roi in args.rois:
        for cvd_subj in args.cvd_subjects:
            # RDM results
            rdm_path = Path(args.rdm_dir) / roi / f'sub-{cvd_subj}_rdm_v2.json'
            all_results[f'rdm_{roi}_{cvd_subj}'] = load_json(rdm_path)

            # LOCO results (W-fixed)
            loco_path = Path(args.loco_dir) / roi / f'sub-{cvd_subj}_loco_v2.json'
            all_results[f'loco_{roi}_{cvd_subj}'] = load_json(loco_path)

            # LOCO legacy results
            legacy_path = (Path(args.loco_legacy_dir) / roi
                           / f'sub-{cvd_subj}_loco_v2.json')
            all_results[f'loco_legacy_{roi}_{cvd_subj}'] = load_json(legacy_path)

        # SRM baseline
        baseline_path = Path(args.baseline_dir_srm) / f'{roi}_baseline.json'
        all_results[f'srm_baseline_{roi}'] = load_json(baseline_path)

    for cvd_subj in args.cvd_subjects:
        cross_roi_path = (Path(args.cross_roi_dir)
                          / f'sub-{cvd_subj}_cross_roi.json')
        all_results[f'cross_roi_{cvd_subj}'] = load_json(cross_roi_path)

    # Print master summary
    print_master_summary(all_results)

    # Generate figures
    print('\nGenerating figures...')
    plot_cross_roi_deltas(all_results, args.output_dir)
    plot_cross_roi_eval(all_results, args.output_dir)
    plot_wfixed_vs_legacy(all_results, args.output_dir)

    # Save summary JSON
    summary = {
        'timestamp': str(np.datetime64('now')),
        'rois': args.rois,
        'cvd_subjects': args.cvd_subjects,
    }

    # Collect key metrics
    for cvd_subj in args.cvd_subjects:
        subj_summary = {}
        for roi in args.rois:
            roi_metrics = {}

            # RDM
            rdm = all_results.get(f'rdm_{roi}_{cvd_subj}', {})
            agg = rdm.get('aggregate', {})
            if 'cone_1way_path_A' in agg:
                roi_metrics['rdm_delta_nm'] = agg['cone_1way_path_A']['params_median'][0]
                roi_metrics['rdm_spearman_r'] = agg['cone_1way_path_A']['spearman_r_median']

            # LOCO
            loco = all_results.get(f'loco_{roi}_{cvd_subj}', {})
            fits = loco.get('fit_results', {})
            if 'cone_1way' in fits:
                roi_metrics['loco_delta_nm'] = fits['cone_1way']['params'][0]
                roi_metrics['loco_spearman_r'] = fits['cone_1way']['spearman_r']
                roi_metrics['loco_perm_p'] = fits['cone_1way']['perm_p_spearman']

            subj_summary[roi] = roi_metrics
        summary[f'sub_{cvd_subj}'] = subj_summary

    out_path = Path(args.output_dir) / 'cross_roi_summary.json'
    with open(out_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'\nSaved summary: {out_path}')

    print('\nStep 3b (Cross-ROI Summary) complete.')


if __name__ == '__main__':
    main()
