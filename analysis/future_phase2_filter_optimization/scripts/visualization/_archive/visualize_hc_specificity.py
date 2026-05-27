#!/usr/bin/env python3
"""
visualize_hc_specificity.py — Visualize HC specificity test results.

Generates:
  1. Forest plot of p-values (HC vs CVD side-by-side)
  2. Best rho comparison scatter
  3. Per-model FPR bar chart
  4. Console manuscript table

Usage (local):
    python scripts/visualize_hc_specificity.py \
        --results_dir results/hc_specificity \
        --output_dir results/hc_specificity/figures
"""

import argparse
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

# Known CVD results for comparison (from pipeline memory)
CVD_REFERENCE = {
    '08': {'group': 'CVD-D', 'best_model': '2component', 'best_roi': 'hV4',
           'best_rho': 0.83, 'best_p': 0.004},
    '09': {'group': 'CVD-P', 'best_model': 'machado_1way', 'best_roi': 'hV4',
           'best_rho': 0.79, 'best_p': 0.018},
    '10': {'group': 'Ctrl', 'best_model': '-', 'best_roi': '-',
           'best_rho': 0.21, 'best_p': 0.058},
}


def load_hc_results(results_dir):
    """Load all HC specificity JSON files."""
    results = {}
    for f in sorted(Path(results_dir).glob('sub-*_specificity.json')):
        with open(f) as fh:
            data = json.load(fh)
        results[data['subject']] = data
    return results


def load_summary(results_dir):
    """Load summary.json if available."""
    path = Path(results_dir) / 'summary.json'
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def extract_best_per_subject(hc_results):
    """Extract best (min-p) model result for each HC subject."""
    rows = []
    for subj_id in sorted(hc_results.keys()):
        r = hc_results[subj_id]
        best_model, best_roi, best_rho, best_p = '-', '-', 0.0, 1.0
        for roi in ['V1', 'V2', 'V4']:
            if roi not in r or 'families' not in r.get(roi, {}):
                continue
            for fam in ['protan', 'deutan']:
                for mname, mres in r[roi].get('families', {}).get(fam, {}).items():
                    if mres['label_perm_p'] < best_p:
                        best_p = mres['label_perm_p']
                        best_model = mname
                        best_roi = roi
                        best_rho = mres['spearman_r']
        rows.append({
            'subject': subj_id, 'group': 'HC',
            'model': best_model, 'roi': best_roi,
            'rho': best_rho, 'p': best_p,
        })
    return rows


def plot_combined(hc_rows, output_path, cvd_ref=None):
    """Two-panel figure: forest plot (left) + rho scatter (right)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5),
                                    gridspec_kw={'width_ratios': [1.3, 1]})

    # Collect all subjects for plotting
    labels, p_vals, rhos, colors = [], [], [], []

    # HC subjects
    for row in hc_rows:
        labels.append(f'sub-{row["subject"]} (HC)')
        p_vals.append(row['p'])
        rhos.append(row['rho'])
        colors.append('steelblue')

    # Separator
    labels.append('')
    p_vals.append(None)
    rhos.append(None)
    colors.append('white')

    # CVD reference
    if cvd_ref:
        color_map = {'CVD-D': '#d62728', 'CVD-P': '#ff7f0e', 'Ctrl': '#7f7f7f'}
        for subj_id in sorted(cvd_ref.keys()):
            info = cvd_ref[subj_id]
            labels.append(f'sub-{subj_id} ({info["group"]})')
            p_vals.append(info['best_p'])
            rhos.append(info['best_rho'])
            colors.append(color_map.get(info['group'], 'gray'))

    n = len(labels)
    y_pos = list(range(n))

    # ── Panel A: Forest plot (-log10 p) ──────────────────────────────
    for i in range(n):
        if p_vals[i] is None:
            continue
        logp = -np.log10(max(p_vals[i], 1e-10))
        ax1.barh(y_pos[i], logp, color=colors[i], alpha=0.75, height=0.6,
                 edgecolor='none')
        ax1.text(logp + 0.05, y_pos[i], f'{p_vals[i]:.3f}',
                 va='center', fontsize=8)

    ax1.axvline(-np.log10(0.05), color='red', linestyle='--', linewidth=1,
                alpha=0.7, label='p = 0.05')
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(labels, fontsize=9)
    ax1.set_xlabel('$-\\log_{10}(p)$', fontsize=10)
    ax1.set_title('A. Min p-value per Subject', fontsize=11, fontweight='bold')
    ax1.legend(loc='lower right', fontsize=8)
    ax1.invert_yaxis()
    ax1.set_xlim(left=0)

    # ── Panel B: Best rho scatter ────────────────────────────────────
    for i in range(n):
        if rhos[i] is None:
            continue
        ax2.barh(y_pos[i], rhos[i], color=colors[i], alpha=0.75, height=0.6,
                 edgecolor='none')
        ax2.text(rhos[i] + 0.01, y_pos[i], f'{rhos[i]:.3f}',
                 va='center', fontsize=8)

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(['' for _ in labels])  # labels on left panel only
    ax2.set_xlabel('Best Spearman $\\rho$', fontsize=10)
    ax2.set_title('B. Best Fit Correlation', fontsize=11, fontweight='bold')
    ax2.invert_yaxis()
    ax2.set_xlim(left=0, right=1.05)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'Saved: {output_path}')


def plot_model_fpr(summary, output_path):
    """Bar chart of per-model FPR."""
    if 'model_fpr' not in summary:
        return

    models = list(summary['model_fpr'].keys())
    fprs = [summary['model_fpr'][m]['fpr'] for m in models]
    n_fp = [summary['model_fpr'][m]['n_fp'] for m in models]
    n_tested = [summary['model_fpr'][m]['n_tested'] for m in models]

    fig, ax = plt.subplots(figsize=(8, 4))
    x = range(len(models))
    bars = ax.bar(x, fprs, color='steelblue', alpha=0.7, edgecolor='none')

    for i, bar in enumerate(bars):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                f'{n_fp[i]}/{n_tested[i]}', ha='center', va='bottom',
                fontsize=9)

    ax.axhline(0.05, color='red', linestyle='--', linewidth=1, alpha=0.7,
               label='Nominal $\\alpha$ = 0.05')
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=20, ha='right', fontsize=9)
    ax.set_ylabel('False Positive Rate', fontsize=10)
    ax.set_title('Per-Model FPR (HC Specificity Test)', fontsize=11,
                 fontweight='bold')
    ax.set_ylim(0, max(max(fprs) + 0.1, 0.15))
    ax.legend(fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f'Saved: {output_path}')


def print_manuscript_table(hc_rows, cvd_ref=None):
    """Print manuscript-ready table to console."""
    print('\n' + '=' * 65)
    print('MANUSCRIPT TABLE: HC Specificity + CVD Results')
    print('=' * 65)
    print(f'{"Subject":10s} {"Group":7s} {"Best Model":15s} {"ROI":5s} '
          f'{"rho":>6s} {"p":>8s} {"Sig":3s}')
    print('-' * 65)

    for row in hc_rows:
        sig = '**' if row['p'] < 0.01 else ('*' if row['p'] < 0.05 else '')
        print(f'sub-{row["subject"]:5s} {"HC":7s} {row["model"]:15s} '
              f'{row["roi"]:5s} {row["rho"]:6.3f} {row["p"]:8.4f} {sig:3s}')

    if cvd_ref:
        print('-' * 65)
        for subj_id in sorted(cvd_ref.keys()):
            info = cvd_ref[subj_id]
            sig = '**' if info['best_p'] < 0.01 else (
                '*' if info['best_p'] < 0.05 else '')
            print(f'sub-{subj_id:5s} {info["group"]:7s} '
                  f'{info["best_model"]:15s} {info["best_roi"]:5s} '
                  f'{info["best_rho"]:6.3f} {info["best_p"]:8.4f} {sig:3s}')

    n_hc = len(hc_rows)
    n_fp = sum(1 for r in hc_rows if r['p'] < 0.05)
    print('-' * 65)
    print(f'FPR = {n_fp}/{n_hc} = {n_fp/n_hc:.3f}')
    print('=' * 65)


def main():
    parser = argparse.ArgumentParser(
        description='Visualize HC specificity test results')
    parser.add_argument('--results_dir', type=str,
                        default='results/hc_specificity',
                        help='Directory with HC specificity JSON results')
    parser.add_argument('--output_dir', type=str, default=None,
                        help='Figure output dir (default: results_dir/figures)')
    parser.add_argument('--no_cvd', action='store_true',
                        help='Omit CVD reference data from plots')
    args = parser.parse_args()

    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir) if args.output_dir else results_dir / 'visualizations'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load HC results
    hc_results = load_hc_results(results_dir)
    if not hc_results:
        print(f'No results found in {results_dir}')
        return

    print(f'Loaded {len(hc_results)} HC subjects from {results_dir}')
    hc_rows = extract_best_per_subject(hc_results)

    cvd_ref = None if args.no_cvd else CVD_REFERENCE

    # Plots
    plot_combined(hc_rows, output_dir / 'hc_specificity_combined.png',
                  cvd_ref=cvd_ref)

    summary = load_summary(results_dir)
    if summary:
        plot_model_fpr(summary, output_dir / 'hc_specificity_model_fpr.png')

    # Console table
    print_manuscript_table(hc_rows, cvd_ref=cvd_ref)

    # Print FPR summary if available
    if summary:
        print(f'\nBinomial test: P(X >= {summary.get("n_fp_loco", 0)} | '
              f'n={summary.get("n_subjects", 0)}, alpha=0.05) = '
              f'{summary.get("binom_p_loco", 1.0):.4f}')


if __name__ == '__main__':
    main()
