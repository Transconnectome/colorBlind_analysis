#!/usr/bin/env python3
"""
plot_summary.py — Summary figures for cone shift pipeline.

Generates:
  1. Model comparison heatmap (5 models x 3 criteria)
  2. Cross-validation convergence scatter
  3. W constraint verification bars
  4. HC replication permutation histograms

Runs locally (conda env: srm).

Usage:
    python scripts/plot_summary.py \
        --results_dir results \
        --fig_dir figures
"""

import argparse
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import CVD_SUBJECTS, ROIS
from utils_distortion_models import MODELS

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
MODEL_NAMES = list(MODELS.keys())


def plot_model_comparison(results_dir, fig_dir):
    """Figure 1: Model comparison heatmap (5 models x 3 criteria per subject/ROI)."""
    conv_path = results_dir / 'step4_cross_validation' / 'convergence_summary.json'
    if not conv_path.exists():
        print('  Step 4 results not found, skipping model comparison.')
        return

    with open(conv_path) as f:
        data = json.load(f)

    summaries = data.get('summaries', {})

    for key, summary in summaries.items():
        roi, subj = key.split('/')
        models = summary.get('models', {})

        n_models = len(MODEL_NAMES)
        criteria = ['rdm_1a_loss', 'loro_corr', 'loco_rho']
        crit_labels = ['RDM 1a (loss, lower=better)', 'LORO (r, higher=better)',
                       'LOCO (rho, higher=better)']

        matrix = np.full((n_models, 3), np.nan)
        for i, m in enumerate(MODEL_NAMES):
            if m in models:
                scores = models[m].get('scores', {})
                # RDM: negate loss so higher = better for consistent colormap
                if 'rdm_1a_loss' in scores:
                    matrix[i, 0] = -scores['rdm_1a_loss']
                if 'loro_corr' in scores:
                    matrix[i, 1] = scores['loro_corr']
                if 'loco_rho' in scores:
                    matrix[i, 2] = scores['loco_rho']

        fig, ax = plt.subplots(figsize=(8, 5))
        im = ax.imshow(matrix, aspect='auto', cmap='RdYlGn')
        ax.set_xticks(range(3))
        ax.set_xticklabels(crit_labels, rotation=30, ha='right', fontsize=8)
        ax.set_yticks(range(n_models))
        ax.set_yticklabels([f'{m} (df={MODELS[m]["df"]})' for m in MODEL_NAMES],
                           fontsize=9)
        ax.set_title(f'{roi} / {subj} ({CVD_TYPE.get(subj.split("-")[-1], "?")})')
        plt.colorbar(im, ax=ax, label='Score (higher = better)')

        # Annotate cells
        for i in range(n_models):
            for j in range(3):
                val = matrix[i, j]
                if np.isfinite(val):
                    ax.text(j, i, f'{val:.3f}', ha='center', va='center',
                            fontsize=7, color='black')

        plt.tight_layout()
        safe_key = key.replace('/', '_')
        plt.savefig(fig_dir / f'model_comparison_{safe_key}.png', dpi=150)
        plt.close()

    print('  Model comparison heatmaps saved.')


def plot_w_constraint(results_dir, fig_dir):
    """Figure 2: W constraint verification bars."""
    found = False
    fig, axes = plt.subplots(len(ROIS), 1, figsize=(8, 3 * len(ROIS)), squeeze=False)

    for roi_idx, roi in enumerate(ROIS):
        ax = axes[roi_idx, 0]
        subjects = []
        norms = []
        ch_ps = []

        for cvd_subj in CVD_SUBJECTS:
            wc_path = (results_dir / 'step3_w_constraint' / roi
                       / f'sub-{cvd_subj}_w_constraint.json')
            if not wc_path.exists():
                continue
            with open(wc_path) as f:
                wc = json.load(f)
            subjects.append(f'sub-{cvd_subj}')
            norms.append(wc.get('delta_w_norm', 0))
            ch_ps.append(wc.get('crawford_howell', {}).get('p_value', 1))
            found = True

        if subjects:
            x = np.arange(len(subjects))
            bars = ax.bar(x, norms, color=['tab:red' if p < 0.05 else 'tab:blue'
                                            for p in ch_ps])
            ax.set_xticks(x)
            ax.set_xticklabels(subjects)
            ax.set_ylabel('||W_free - W0||_F / ||W0||_F')
            ax.set_title(f'{roi}: W constraint (red = C&H p<0.05)')
            ax.axhline(0.1, color='gray', ls='--', lw=0.8, label='threshold')
            ax.legend(fontsize=8)
        else:
            ax.set_title(f'{roi}: No W constraint data')

    plt.tight_layout()
    if found:
        plt.savefig(fig_dir / 'w_constraint_bars.png', dpi=150)
    plt.close()
    if found:
        print('  W constraint bars saved.')


def plot_replication_histograms(results_dir, fig_dir):
    """Figure 3: HC replication permutation histograms."""
    found = False

    for roi in ROIS:
        for cvd_subj in CVD_SUBJECTS:
            repl_path = (results_dir / 'step5_hc_replication' / roi
                         / f'sub-{cvd_subj}_replication.json')
            if not repl_path.exists():
                continue

            with open(repl_path) as f:
                data = json.load(f)

            models_data = data.get('models', {})
            n_models = len(models_data)
            if n_models == 0:
                continue

            fig, axes = plt.subplots(1, min(n_models, 5), figsize=(4 * min(n_models, 5), 4))
            if min(n_models, 5) == 1:
                axes = [axes]

            for idx, (model_name, mdata) in enumerate(models_data.items()):
                if idx >= 5:
                    break
                ax = axes[idx]
                obs_r = mdata['observed_r']

                # Permutation null (just stats, not full distribution)
                perm = mdata.get('exact_permutation', {})
                mc = mdata.get('monte_carlo', {})

                # Show MC null as histogram approximation
                mc_mean = mc.get('null_mean', 0)
                mc_std = mc.get('null_std', 0.3)
                if mc_std > 0:
                    x_range = np.linspace(mc_mean - 3*mc_std, mc_mean + 3*mc_std, 100)
                    y_norm = np.exp(-0.5 * ((x_range - mc_mean) / mc_std) ** 2)
                    ax.fill_between(x_range, y_norm, alpha=0.3, color='gray',
                                   label='MC null')

                ax.axvline(obs_r, color='red', lw=2, label=f'observed r={obs_r:.3f}')
                ax.set_xlabel('Spearman r')
                ax.set_title(f'{model_name}\nperm p={perm.get("p_value", "?"):.3f}, '
                             f'mc p={mc.get("p_value", "?"):.3f}',
                             fontsize=9)
                ax.legend(fontsize=7)
                found = True

            plt.suptitle(f'{roi} / sub-{cvd_subj}', fontsize=11)
            plt.tight_layout()
            plt.savefig(fig_dir / f'replication_{roi}_sub-{cvd_subj}.png', dpi=150)
            plt.close()

    if found:
        print('  Replication histograms saved.')


def main():
    parser = argparse.ArgumentParser(description='Plot summary figures')
    parser.add_argument('--results_dir', type=str, default='results')
    parser.add_argument('--fig_dir', type=str, default='figures')
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    fig_dir = Path(args.fig_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('Generating Summary Figures')
    print('=' * 60)

    plot_model_comparison(results_dir, fig_dir)
    plot_w_constraint(results_dir, fig_dir)
    plot_replication_histograms(results_dir, fig_dir)

    print(f'\nAll figures saved to {fig_dir}/')


if __name__ == '__main__':
    main()
