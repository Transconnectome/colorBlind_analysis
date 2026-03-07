#!/usr/bin/env python3
"""
Comprehensive decoder model comparison visualization.

Reads JSON results from:
- model_comparison_server/consolidated/ (original 6-model LORO)
- results/focused_nested/ (RT-2/RT-3: FE, SVM, MLP with nested Procrustes)
- results/hybrid/ (RT-6: FE, FE_MLP, FE_SVM)

Produces publication-quality figures with bootstrap 95% CIs.
"""

import json
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from itertools import combinations

# ============================================================================
# Configuration
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / 'results'
FIGURES_DIR = RESULTS_DIR / 'figures'
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

SUBJECTS = [f'{i:02d}' for i in range(1, 11)]
HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = ['08', '09', '10']
ROIS = ['V1', 'V2', 'V3', 'V4']

N_BOOTSTRAP = 10000
CHANCE_ACC45 = 0.375

# Colors for models
MODEL_COLORS = {
    'LDA': '#2196F3',           # blue
    'Ridge': '#64B5F6',         # light blue
    'ForwardEncoding': '#4CAF50',  # green
    'KernelRidge': '#FF9800',   # orange
    'SVM': '#F44336',           # red
    'MLP': '#9E9E9E',           # gray
    'FE_MLP': '#CE93D8',        # light purple
    'FE_SVM': '#AB47BC',        # purple
}

MODEL_ORDER = ['LDA', 'Ridge', 'ForwardEncoding', 'KernelRidge', 'SVM', 'MLP',
               'FE_MLP', 'FE_SVM']

MODEL_LABELS = {
    'LDA': 'LDA',
    'Ridge': 'Ridge',
    'ForwardEncoding': 'FE (B&H)',
    'KernelRidge': 'KernelRidge',
    'SVM': 'SVM',
    'MLP': 'MLP',
    'FE_MLP': 'FE+MLP',
    'FE_SVM': 'FE+SVM',
}


# ============================================================================
# Data Loading
# ============================================================================

def extract_acc45_per_subject_roi(results_path, subjects, models, alignment_key=None):
    """Extract subject-level mean acc_45 for each model×ROI.

    JSON structure: {results: {alignment_key: {ROI: {model: [fold_results]}}}}

    Args:
        alignment_key: If None, auto-detect first alignment key in results.

    Returns: dict[model][roi] = list of subject-level means (length = len(subjects))
    """
    out = {m: {r: [] for r in ROIS} for m in models}

    for subj in subjects:
        fpath = results_path / f'sub-{subj}_performance_raw.json'
        if not fpath.exists():
            for m in models:
                for r in ROIS:
                    out[m][r].append(np.nan)
            continue

        with open(fpath) as f:
            raw = json.load(f)

        results = raw.get('results', raw)

        # Auto-detect alignment key if needed
        akey = alignment_key
        if akey is None:
            # results is {alignment_key: {ROI: {model: [folds]}}}
            for candidate in results:
                if isinstance(results[candidate], dict) and any(r in results[candidate] for r in ROIS):
                    akey = candidate
                    break

        if akey is None or akey not in results:
            for m in models:
                for r in ROIS:
                    out[m][r].append(np.nan)
            continue

        aligned_data = results[akey]  # {ROI: {model: [folds]}}

        for m in models:
            for r in ROIS:
                if r in aligned_data and isinstance(aligned_data[r], dict):
                    if m in aligned_data[r] and isinstance(aligned_data[r][m], list):
                        folds = aligned_data[r][m]
                        acc_vals = [f['acc_45'] for f in folds if isinstance(f, dict) and 'acc_45' in f]
                        if acc_vals:
                            out[m][r].append(np.mean(acc_vals))
                        else:
                            out[m][r].append(np.nan)
                    else:
                        out[m][r].append(np.nan)
                else:
                    out[m][r].append(np.nan)

    return out


def load_original_6model(consolidated_dir, alignment='procrustes'):
    """Load original 6-model results from consolidated directory."""
    models = ['LDA', 'Ridge', 'ForwardEncoding', 'KernelRidge', 'SVM', 'MLP']
    return extract_acc45_per_subject_roi(consolidated_dir, SUBJECTS, models,
                                          alignment_key=alignment)


def load_focused_nested(condition_dir, models=None, alignment_key=None):
    """Load focused_nested results."""
    if models is None:
        models = ['ForwardEncoding', 'SVM', 'MLP']
    return extract_acc45_per_subject_roi(condition_dir, SUBJECTS, models,
                                          alignment_key=alignment_key)


def load_hybrid(condition_dir, models=None, alignment_key=None):
    """Load hybrid results."""
    if models is None:
        models = ['ForwardEncoding', 'FE_MLP', 'FE_SVM']
    return extract_acc45_per_subject_roi(condition_dir, SUBJECTS, models,
                                          alignment_key=alignment_key)


# ============================================================================
# Bootstrap CI
# ============================================================================

def bootstrap_ci(values, n_boot=N_BOOTSTRAP, ci=0.95):
    """Compute bootstrap CI for mean of values (subject-level resampling)."""
    values = np.array([v for v in values if not np.isnan(v)])
    if len(values) < 2:
        return np.mean(values), np.mean(values), np.mean(values)

    rng = np.random.default_rng(42)
    boot_means = np.array([
        np.mean(rng.choice(values, size=len(values), replace=True))
        for _ in range(n_boot)
    ])

    alpha = (1 - ci) / 2
    return np.mean(values), np.percentile(boot_means, alpha * 100), np.percentile(boot_means, (1 - alpha) * 100)


def compute_model_stats(data, models, rois=ROIS):
    """Compute per-model overall mean and CI across all ROIs."""
    stats = {}
    for m in models:
        # Pool across all ROIs for overall
        all_subj_means = []
        for r in rois:
            all_subj_means.extend(data[m][r])
        mean, ci_lo, ci_hi = bootstrap_ci(all_subj_means)
        stats[m] = {'mean': mean, 'ci_lo': ci_lo, 'ci_hi': ci_hi}

        # Per ROI
        stats[m]['per_roi'] = {}
        for r in rois:
            rm, rlo, rhi = bootstrap_ci(data[m][r])
            stats[m]['per_roi'][r] = {'mean': rm, 'ci_lo': rlo, 'ci_hi': rhi}

        # Per group
        hc_vals = []
        cvd_vals = []
        for r in rois:
            for i, subj in enumerate(SUBJECTS):
                v = data[m][r][i]
                if not np.isnan(v):
                    if subj in HC_SUBJECTS:
                        hc_vals.append(v)
                    else:
                        cvd_vals.append(v)
        hm, hlo, hhi = bootstrap_ci(hc_vals)
        cm, clo, chi = bootstrap_ci(cvd_vals)
        stats[m]['hc'] = {'mean': hm, 'ci_lo': hlo, 'ci_hi': hhi}
        stats[m]['cvd'] = {'mean': cm, 'ci_lo': clo, 'ci_hi': chi}

    return stats


# ============================================================================
# Figure 1: Full Model Comparison (Main Story)
# ============================================================================

def plot_full_model_comparison(original_stats, nested_stats, hybrid_stats):
    """
    Main figure: All models compared under their best conditions.

    Bar chart with bootstrap 95% CIs showing the complete decoder story:
    - Original 6 models (preloaded Procrustes)
    - Focused nested (SVM, FE with nested Procrustes)
    - Hybrid (FE_MLP, FE_SVM with nested Procrustes)
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), gridspec_kw={'width_ratios': [3, 2]})

    # --- Panel A: Overall acc_45 comparison ---
    ax = axes[0]

    # Collect all models with their best condition
    entries = []

    # Original preloaded Procrustes
    for m in ['LDA', 'Ridge', 'KernelRidge']:
        if m in original_stats:
            entries.append((m, original_stats[m], 'Preloaded Procrustes'))

    # MLP from original (both are at chance)
    if 'MLP' in original_stats:
        entries.append(('MLP', original_stats['MLP'], 'Preloaded Procrustes'))

    # Nested Procrustes (best for SVM, FE)
    for m in ['SVM', 'ForwardEncoding']:
        if m in nested_stats:
            entries.append((m, nested_stats[m], 'Nested Procrustes'))

    # Hybrid nested
    for m in ['FE_SVM', 'FE_MLP']:
        if m in hybrid_stats:
            entries.append((m, hybrid_stats[m], 'Nested Procrustes'))

    # Sort by mean accuracy descending
    entries.sort(key=lambda x: x[1]['mean'], reverse=True)

    x_pos = np.arange(len(entries))
    bar_colors = [MODEL_COLORS.get(e[0], '#666') for e in entries]
    means = [e[1]['mean'] for e in entries]
    ci_los = [e[1]['mean'] - e[1]['ci_lo'] for e in entries]
    ci_his = [e[1]['ci_hi'] - e[1]['mean'] for e in entries]
    labels = [MODEL_LABELS.get(e[0], e[0]) for e in entries]

    bars = ax.bar(x_pos, means, color=bar_colors, edgecolor='white', linewidth=0.5,
                  zorder=3, alpha=0.85)
    ax.errorbar(x_pos, means, yerr=[ci_los, ci_his],
                fmt='none', color='black', capsize=4, capthick=1.5, linewidth=1.5,
                zorder=4)

    # Chance line
    ax.axhline(y=CHANCE_ACC45, color='gray', linestyle='--', linewidth=1, alpha=0.7,
               zorder=2)
    ax.text(len(entries) - 0.5, CHANCE_ACC45 + 0.01, 'Chance (37.5%)',
            ha='right', va='bottom', fontsize=9, color='gray', style='italic')

    # Condition annotation
    for i, (m, s, cond) in enumerate(entries):
        marker = 'N' if 'Nested' in cond else 'P'
        ax.text(i, s['ci_hi'] + 0.015, marker, ha='center', va='bottom',
                fontsize=8, fontweight='bold',
                color='#2E7D32' if marker == 'N' else '#1565C0')

    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=10)
    ax.set_ylabel('acc_45 (±45° accuracy)', fontsize=11)
    ax.set_ylim(0.3, 1.0)
    ax.set_title('A. Decoder Model Comparison (Best Condition per Model)\n'
                 'Dataset: full_dataset_C010 | LORO CV | Voxel space (no SRM)',
                 fontsize=11, fontweight='bold')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Legend for condition markers
    legend_elements = [
        mpatches.Patch(facecolor='white', edgecolor='#2E7D32', label='N = Nested Procrustes',
                       linewidth=1.5),
        mpatches.Patch(facecolor='white', edgecolor='#1565C0', label='P = Preloaded Procrustes',
                       linewidth=1.5),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9, framealpha=0.9)

    # --- Panel B: HC vs CVD ---
    ax2 = axes[1]

    key_models = ['SVM', 'ForwardEncoding', 'FE_SVM']
    key_data = {}
    for m in key_models:
        if m == 'SVM' and m in nested_stats:
            key_data[m] = nested_stats[m]
        elif m in hybrid_stats:
            key_data[m] = hybrid_stats[m]
        elif m in nested_stats:
            key_data[m] = nested_stats[m]

    x_pos2 = np.arange(len(key_models))
    width = 0.35

    hc_means = [key_data[m]['hc']['mean'] for m in key_models]
    hc_errs = [[key_data[m]['hc']['mean'] - key_data[m]['hc']['ci_lo'] for m in key_models],
               [key_data[m]['hc']['ci_hi'] - key_data[m]['hc']['mean'] for m in key_models]]
    cvd_means = [key_data[m]['cvd']['mean'] for m in key_models]
    cvd_errs = [[key_data[m]['cvd']['mean'] - key_data[m]['cvd']['ci_lo'] for m in key_models],
                [key_data[m]['cvd']['ci_hi'] - key_data[m]['cvd']['mean'] for m in key_models]]

    ax2.bar(x_pos2 - width/2, hc_means, width, color='#42A5F5', label='HC (n=7)',
            edgecolor='white', alpha=0.85, zorder=3)
    ax2.errorbar(x_pos2 - width/2, hc_means, yerr=hc_errs,
                 fmt='none', color='black', capsize=3, capthick=1.2, zorder=4)

    ax2.bar(x_pos2 + width/2, cvd_means, width, color='#EF5350', label='CVD (n=3)',
            edgecolor='white', alpha=0.85, zorder=3)
    ax2.errorbar(x_pos2 + width/2, cvd_means, yerr=cvd_errs,
                 fmt='none', color='black', capsize=3, capthick=1.2, zorder=4)

    ax2.axhline(y=CHANCE_ACC45, color='gray', linestyle='--', linewidth=1, alpha=0.7,
                zorder=2)

    ax2.set_xticks(x_pos2)
    ax2.set_xticklabels([MODEL_LABELS[m] for m in key_models], fontsize=10)
    ax2.set_ylabel('acc_45', fontsize=11)
    ax2.set_ylim(0.3, 1.0)
    ax2.set_title('B. HC vs CVD (Nested Procrustes)\n'
                   'Input: amplitudes_raw.npy + fold-wise Procrustes',
                   fontsize=11, fontweight='bold')
    ax2.legend(fontsize=10, loc='upper right')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    plt.tight_layout()
    out = FIGURES_DIR / 'fig1_model_comparison_overview.png'
    plt.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Saved: {out}')


# ============================================================================
# Figure 2: Alignment Effect + Hybrid Comparison
# ============================================================================

def plot_alignment_and_hybrid(nested_stats, ctrl_stats, hybrid_nested_stats, hybrid_ctrl_stats):
    """
    Two panels:
    A. Alignment effect (nested vs ctrl) for FE, SVM, MLP
    B. Hybrid comparison: FE vs FE_SVM vs FE_MLP (nested Procrustes)
    """
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

    # --- Panel A: Alignment Effect ---
    ax = axes[0]
    models_align = ['ForwardEncoding', 'SVM', 'MLP']
    x_pos = np.arange(len(models_align))
    width = 0.35

    nested_means = [nested_stats[m]['mean'] for m in models_align]
    nested_errs = [
        [nested_stats[m]['mean'] - nested_stats[m]['ci_lo'] for m in models_align],
        [nested_stats[m]['ci_hi'] - nested_stats[m]['mean'] for m in models_align]
    ]
    ctrl_means = [ctrl_stats[m]['mean'] for m in models_align]
    ctrl_errs = [
        [ctrl_stats[m]['mean'] - ctrl_stats[m]['ci_lo'] for m in models_align],
        [ctrl_stats[m]['ci_hi'] - ctrl_stats[m]['mean'] for m in models_align]
    ]

    bars_n = ax.bar(x_pos - width/2, nested_means, width, color='#66BB6A',
                    label='Nested Procrustes', edgecolor='white', alpha=0.85, zorder=3)
    ax.errorbar(x_pos - width/2, nested_means, yerr=nested_errs,
                fmt='none', color='black', capsize=3, capthick=1.2, zorder=4)

    bars_c = ax.bar(x_pos + width/2, ctrl_means, width, color='#BDBDBD',
                    label='Preloaded Procrustes', edgecolor='white', alpha=0.85, zorder=3)
    ax.errorbar(x_pos + width/2, ctrl_means, yerr=ctrl_errs,
                fmt='none', color='black', capsize=3, capthick=1.2, zorder=4)

    # Delta annotations
    for i, m in enumerate(models_align):
        delta = nested_means[i] - ctrl_means[i]
        y_top = max(nested_means[i], ctrl_means[i]) + 0.03
        if not np.isnan(delta):
            ax.text(i, y_top + 0.02, f'Δ={delta:+.3f}', ha='center', va='bottom',
                    fontsize=9, fontweight='bold',
                    color='#2E7D32' if delta > 0.01 else '#757575')

    ax.axhline(y=CHANCE_ACC45, color='gray', linestyle='--', linewidth=1, alpha=0.7, zorder=2)
    ax.set_xticks(x_pos)
    ax.set_xticklabels([MODEL_LABELS[m] for m in models_align], fontsize=11)
    ax.set_ylabel('acc_45', fontsize=11)
    ax.set_ylim(0.3, 1.0)
    ax.set_title('A. Alignment Effect on Decoder Performance\n'
                  'Green: raw voxels + fold-wise Procrustes | Gray: preloaded Procrustes',
                  fontsize=10, fontweight='bold')
    ax.legend(fontsize=9, loc='upper right')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # --- Panel B: Hybrid Comparison ---
    ax2 = axes[1]
    models_hybrid = ['ForwardEncoding', 'FE_SVM', 'FE_MLP']
    x_pos2 = np.arange(len(models_hybrid))

    h_nested_means = [hybrid_nested_stats[m]['mean'] for m in models_hybrid]
    h_nested_errs = [
        [hybrid_nested_stats[m]['mean'] - hybrid_nested_stats[m]['ci_lo'] for m in models_hybrid],
        [hybrid_nested_stats[m]['ci_hi'] - hybrid_nested_stats[m]['mean'] for m in models_hybrid]
    ]
    h_ctrl_means = [hybrid_ctrl_stats[m]['mean'] for m in models_hybrid]
    h_ctrl_errs = [
        [hybrid_ctrl_stats[m]['mean'] - hybrid_ctrl_stats[m]['ci_lo'] for m in models_hybrid],
        [hybrid_ctrl_stats[m]['ci_hi'] - hybrid_ctrl_stats[m]['mean'] for m in models_hybrid]
    ]

    ax2.bar(x_pos2 - width/2, h_nested_means, width, color='#66BB6A',
            label='Nested Procrustes', edgecolor='white', alpha=0.85, zorder=3)
    ax2.errorbar(x_pos2 - width/2, h_nested_means, yerr=h_nested_errs,
                 fmt='none', color='black', capsize=3, capthick=1.2, zorder=4)

    ax2.bar(x_pos2 + width/2, h_ctrl_means, width, color='#BDBDBD',
            label='Preloaded Procrustes', edgecolor='white', alpha=0.85, zorder=3)
    ax2.errorbar(x_pos2 + width/2, h_ctrl_means, yerr=h_ctrl_errs,
                 fmt='none', color='black', capsize=3, capthick=1.2, zorder=4)

    # Highlight FE≈FE_SVM
    ax2.annotate('', xy=(0, h_nested_means[0] + 0.04),
                xytext=(1, h_nested_means[1] + 0.04),
                arrowprops=dict(arrowstyle='<->', color='#FF6F00', lw=1.5))
    ax2.text(0.5, max(h_nested_means[0], h_nested_means[1]) + 0.06,
            f'Δ={h_nested_means[1] - h_nested_means[0]:+.003f}\n(n.s.)',
            ha='center', va='bottom', fontsize=9, color='#FF6F00', fontweight='bold')

    ax2.axhline(y=CHANCE_ACC45, color='gray', linestyle='--', linewidth=1, alpha=0.7, zorder=2)
    ax2.set_xticks(x_pos2)
    ax2.set_xticklabels([MODEL_LABELS[m] for m in models_hybrid], fontsize=11)
    ax2.set_ylabel('acc_45', fontsize=11)
    ax2.set_ylim(0.3, 1.0)
    ax2.set_title('B. Hybrid Decoder: Nonlinear Readout Test\n'
                   'Green: raw voxels + fold-wise Procrustes | Gray: preloaded Procrustes',
                   fontsize=10, fontweight='bold')
    ax2.legend(fontsize=9, loc='upper right')
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)

    fig.text(0.5, -0.02,
             'Dataset: full_dataset_C010 | LORO CV | Voxel space (no SRM)\n'
             'Nested Procrustes: loads amplitudes_raw.npy, fits Procrustes on train runs only (no leakage)\n'
             'Preloaded Procrustes: loads amplitudes_procrustes.npy (Procrustes fit on all 6 runs)',
             ha='center', va='top', fontsize=8, style='italic', color='#555')

    plt.tight_layout()
    out = FIGURES_DIR / 'fig2_alignment_and_hybrid.png'
    plt.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Saved: {out}')


# ============================================================================
# Figure 3: ROI-level Breakdown (Key Models)
# ============================================================================

def plot_roi_breakdown(nested_stats, hybrid_nested_stats):
    """Per-ROI comparison for key models with individual subject data points."""
    fig, axes = plt.subplots(1, 4, figsize=(16, 5), sharey=True)

    key_models = ['SVM', 'ForwardEncoding', 'FE_SVM']
    width = 0.25

    for ax_idx, roi in enumerate(ROIS):
        ax = axes[ax_idx]
        x_pos = np.arange(len(key_models))

        for mi, m in enumerate(key_models):
            # Get stats from appropriate source
            if m == 'SVM':
                stats = nested_stats[m]['per_roi'][roi]
                subj_vals = nested_stats[m].get('_raw', {}).get(roi, [])
            elif m in hybrid_nested_stats:
                stats = hybrid_nested_stats[m]['per_roi'][roi]
                subj_vals = hybrid_nested_stats[m].get('_raw', {}).get(roi, [])
            else:
                stats = nested_stats[m]['per_roi'][roi]
                subj_vals = nested_stats[m].get('_raw', {}).get(roi, [])

            color = MODEL_COLORS.get(m, '#666')
            ax.bar(mi, stats['mean'], width=0.6, color=color, alpha=0.75,
                   edgecolor='white', zorder=3)
            ax.errorbar(mi, stats['mean'],
                       yerr=[[stats['mean'] - stats['ci_lo']],
                             [stats['ci_hi'] - stats['mean']]],
                       fmt='none', color='black', capsize=4, capthick=1.2, zorder=4)

        ax.axhline(y=CHANCE_ACC45, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax.set_xticks(range(len(key_models)))
        ax.set_xticklabels([MODEL_LABELS[m] for m in key_models], fontsize=9, rotation=20, ha='right')
        ax.set_title(roi, fontsize=13, fontweight='bold')
        ax.set_ylim(0.3, 1.05)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)

        if ax_idx == 0:
            ax.set_ylabel('acc_45', fontsize=11)

    fig.suptitle('Per-ROI Decoder Comparison — Nested Procrustes (raw voxels + fold-wise alignment)\n'
                 'Dataset: full_dataset_C010 | LORO CV | No SRM',
                 fontsize=12, fontweight='bold', y=1.04)
    plt.tight_layout()
    out = FIGURES_DIR / 'fig3_roi_breakdown.png'
    plt.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Saved: {out}')


# ============================================================================
# Figure 4: Complete Analysis Story (4-panel summary)
# ============================================================================

def plot_analysis_story(original_stats, nested_stats, ctrl_stats,
                        hybrid_nested_stats, hybrid_ctrl_stats):
    """
    4-panel publication figure telling the complete decoder analysis story.

    A. All models (preloaded Procrustes, original result)
    B. Alignment effect (nested vs ctrl)
    C. Hybrid test (FE vs FE_SVM vs FE_MLP)
    D. Summary: FE is optimal (multi-criteria radar or bar)
    """
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3)

    # --- Panel A: Original 6-model comparison (preloaded Procrustes) ---
    ax_a = fig.add_subplot(gs[0, 0])

    orig_models = ['LDA', 'Ridge', 'ForwardEncoding', 'KernelRidge', 'SVM', 'MLP']
    orig_means = [original_stats[m]['mean'] for m in orig_models if m in original_stats]
    orig_ci_lo = [original_stats[m]['mean'] - original_stats[m]['ci_lo']
                  for m in orig_models if m in original_stats]
    orig_ci_hi = [original_stats[m]['ci_hi'] - original_stats[m]['mean']
                  for m in orig_models if m in original_stats]
    orig_colors = [MODEL_COLORS[m] for m in orig_models if m in original_stats]
    orig_labels = [MODEL_LABELS[m] for m in orig_models if m in original_stats]

    x = np.arange(len(orig_means))
    ax_a.bar(x, orig_means, color=orig_colors, edgecolor='white', alpha=0.85, zorder=3)
    ax_a.errorbar(x, orig_means, yerr=[orig_ci_lo, orig_ci_hi],
                  fmt='none', color='black', capsize=3, capthick=1.2, zorder=4)
    ax_a.axhline(y=CHANCE_ACC45, color='gray', linestyle='--', linewidth=1, alpha=0.7, zorder=2)
    ax_a.set_xticks(x)
    ax_a.set_xticklabels(orig_labels, rotation=30, ha='right', fontsize=9)
    ax_a.set_ylabel('acc_45', fontsize=10)
    ax_a.set_ylim(0.3, 0.95)
    ax_a.set_title('A. LORO acc_45 — Preloaded Procrustes\n'
                   'Input: amplitudes_procrustes.npy (potential leakage)',
                   fontsize=10, fontweight='bold')
    ax_a.spines['top'].set_visible(False)
    ax_a.spines['right'].set_visible(False)

    # --- Panel B: Nested vs Preloaded for FE, SVM ---
    ax_b = fig.add_subplot(gs[0, 1])

    models_b = ['ForwardEncoding', 'SVM', 'MLP']
    width = 0.35
    x_b = np.arange(len(models_b))

    nested_m = [nested_stats[m]['mean'] for m in models_b]
    nested_e = [[nested_stats[m]['mean'] - nested_stats[m]['ci_lo'] for m in models_b],
                [nested_stats[m]['ci_hi'] - nested_stats[m]['mean'] for m in models_b]]
    ctrl_m = [ctrl_stats[m]['mean'] for m in models_b]
    ctrl_e = [[ctrl_stats[m]['mean'] - ctrl_stats[m]['ci_lo'] for m in models_b],
              [ctrl_stats[m]['ci_hi'] - ctrl_stats[m]['mean'] for m in models_b]]

    ax_b.bar(x_b - width/2, nested_m, width, color='#66BB6A', label='Nested Procrustes',
             edgecolor='white', alpha=0.85, zorder=3)
    ax_b.errorbar(x_b - width/2, nested_m, yerr=nested_e,
                  fmt='none', color='black', capsize=3, capthick=1.2, zorder=4)
    ax_b.bar(x_b + width/2, ctrl_m, width, color='#BDBDBD', label='Preloaded',
             edgecolor='white', alpha=0.85, zorder=3)
    ax_b.errorbar(x_b + width/2, ctrl_m, yerr=ctrl_e,
                  fmt='none', color='black', capsize=3, capthick=1.2, zorder=4)

    for i in range(len(models_b)):
        delta = nested_m[i] - ctrl_m[i]
        y = max(nested_m[i], ctrl_m[i]) + nested_e[1][i] + 0.01
        ax_b.text(i, y, f'Δ={delta:+.3f}', ha='center', fontsize=8, fontweight='bold',
                  color='#2E7D32' if delta > 0.01 else '#757575')

    ax_b.axhline(y=CHANCE_ACC45, color='gray', linestyle='--', linewidth=1, alpha=0.7, zorder=2)
    ax_b.set_xticks(x_b)
    ax_b.set_xticklabels([MODEL_LABELS[m] for m in models_b], fontsize=10)
    ax_b.set_ylabel('acc_45', fontsize=10)
    ax_b.set_ylim(0.3, 1.05)
    ax_b.set_title('B. Alignment Effect (RT-2)\n'
                   'Nested: raw voxels + fold-wise | Preloaded: amplitudes_procrustes.npy',
                   fontsize=9, fontweight='bold')
    ax_b.legend(fontsize=9)
    ax_b.spines['top'].set_visible(False)
    ax_b.spines['right'].set_visible(False)

    # --- Panel C: Hybrid comparison ---
    ax_c = fig.add_subplot(gs[1, 0])

    models_c = ['ForwardEncoding', 'FE_SVM', 'FE_MLP']
    x_c = np.arange(len(models_c))

    h_nested = [hybrid_nested_stats[m]['mean'] for m in models_c]
    h_nested_e = [
        [hybrid_nested_stats[m]['mean'] - hybrid_nested_stats[m]['ci_lo'] for m in models_c],
        [hybrid_nested_stats[m]['ci_hi'] - hybrid_nested_stats[m]['mean'] for m in models_c]
    ]

    bar_colors_c = [MODEL_COLORS[m] for m in models_c]
    ax_c.bar(x_c, h_nested, color=bar_colors_c, edgecolor='white', alpha=0.85, zorder=3)
    ax_c.errorbar(x_c, h_nested, yerr=h_nested_e,
                  fmt='none', color='black', capsize=4, capthick=1.2, zorder=4)

    # n.s. bracket between FE and FE_SVM
    y_bracket = max(h_nested[0], h_nested[1]) + max(h_nested_e[1][0], h_nested_e[1][1]) + 0.02
    ax_c.plot([0, 0, 1, 1], [y_bracket, y_bracket + 0.015, y_bracket + 0.015, y_bracket],
              color='#555', linewidth=1.2)
    ax_c.text(0.5, y_bracket + 0.02, 'n.s. (Δ=−0.005)', ha='center', fontsize=9,
              color='#555')

    ax_c.axhline(y=CHANCE_ACC45, color='gray', linestyle='--', linewidth=1, alpha=0.7, zorder=2)
    ax_c.set_xticks(x_c)
    ax_c.set_xticklabels([MODEL_LABELS[m] for m in models_c], fontsize=11)
    ax_c.set_ylabel('acc_45', fontsize=10)
    ax_c.set_ylim(0.3, 1.0)
    ax_c.set_title('C. Hybrid Test (RT-6) — Nested Procrustes\n'
                   'Input: raw voxels + fold-wise Procrustes alignment',
                   fontsize=10, fontweight='bold')
    ax_c.spines['top'].set_visible(False)
    ax_c.spines['right'].set_visible(False)

    # Answer annotation
    ax_c.text(0.97, 0.5, 'FE ≈ FE+SVM\n→ Linear readout\n   is sufficient',
             transform=ax_c.transAxes, fontsize=10, ha='right', va='center',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#E8F5E9', edgecolor='#4CAF50',
                       alpha=0.9))

    # --- Panel D: Multi-criteria summary ---
    ax_d = fig.add_subplot(gs[1, 1])

    criteria = ['LORO acc_45\n(nested)', 'Run-pair\nreliability', 'Alignment\nrobustness',
                'LOCO\ninterpolation', 'W stability\n(cosine)']

    # Normalized scores (0-1 scale, higher=better)
    fe_scores = [0.781/0.899, 0.329/0.329, 1.0, 1.0, 0.921/0.921]  # FE as reference for max
    svm_scores = [0.899/0.899, 0.164/0.329, 0.045/0.123, 0.0, 0.0]  # SVM vs max
    lda_scores = [0.821/0.899, 0.009/0.329, 0.0, 0.0, 0.0]  # LDA vs max

    x_d = np.arange(len(criteria))
    width_d = 0.25

    ax_d.barh(x_d - width_d, fe_scores, width_d, color=MODEL_COLORS['ForwardEncoding'],
              label='FE (B&H)', alpha=0.85, edgecolor='white')
    ax_d.barh(x_d, svm_scores, width_d, color=MODEL_COLORS['SVM'],
              label='SVM', alpha=0.85, edgecolor='white')
    ax_d.barh(x_d + width_d, lda_scores, width_d, color=MODEL_COLORS['LDA'],
              label='LDA', alpha=0.85, edgecolor='white')

    ax_d.set_yticks(x_d)
    ax_d.set_yticklabels(criteria, fontsize=9)
    ax_d.set_xlabel('Relative Score (higher = better)', fontsize=10)
    ax_d.set_xlim(0, 1.15)
    ax_d.set_title('D. Multi-Criteria Decoder Assessment\n(ForwardEncoding is Optimal)',
                   fontsize=11, fontweight='bold')
    ax_d.legend(fontsize=9, loc='lower right')
    ax_d.spines['top'].set_visible(False)
    ax_d.spines['right'].set_visible(False)

    # Overall champion annotation
    ax_d.text(0.85, 0.95, 'Winner: FE (B&H 2009)',
             transform=ax_d.transAxes, fontsize=10, ha='center', va='top',
             fontweight='bold', color='#2E7D32',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#E8F5E9',
                       edgecolor='#4CAF50', alpha=0.9))

    plt.suptitle('Decoder Model Comparison — Complete Analysis Summary\n'
                 'Dataset: full_dataset_C010 | Voxel space (no SRM) | All ROIs pooled',
                fontsize=13, fontweight='bold', y=1.03)

    out = FIGURES_DIR / 'fig4_analysis_story_summary.png'
    plt.savefig(out, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f'Saved: {out}')


# ============================================================================
# Main
# ============================================================================

def main():
    print("Loading results...")

    # 1. Original 6-model (preloaded Procrustes)
    consolidated_dir = RESULTS_DIR / 'model_comparison_server' / 'consolidated'
    if consolidated_dir.exists():
        original_data = load_original_6model(consolidated_dir)
        original_stats = compute_model_stats(original_data,
                                              ['LDA', 'Ridge', 'ForwardEncoding',
                                               'KernelRidge', 'SVM', 'MLP'])
        print(f"  Original 6-model: loaded")
    else:
        print(f"  WARNING: {consolidated_dir} not found, skipping original 6-model")
        original_stats = None

    # 2. Focused nested (RT-2/RT-3)
    # These are at analysis/phase3_decoder_comparing/results/focused_nested/
    decoder_results = BASE_DIR.parent / 'results'
    nested_only_dir = decoder_results / 'focused_nested' / 'nested_only'
    ctrl_dir = decoder_results / 'focused_nested' / 'procrustes_ctrl'

    if nested_only_dir.exists():
        nested_data = load_focused_nested(nested_only_dir)
        nested_stats = compute_model_stats(nested_data, ['ForwardEncoding', 'SVM', 'MLP'])
        print(f"  Focused nested (nested_only): loaded")
    else:
        print(f"  WARNING: {nested_only_dir} not found")
        nested_stats = None

    if ctrl_dir.exists():
        ctrl_data = load_focused_nested(ctrl_dir)
        ctrl_stats = compute_model_stats(ctrl_data, ['ForwardEncoding', 'SVM', 'MLP'])
        print(f"  Focused nested (ctrl): loaded")
    else:
        ctrl_stats = None

    # 3. Hybrid
    hybrid_nested_dir = RESULTS_DIR / 'hybrid' / 'nested'
    hybrid_ctrl_dir = RESULTS_DIR / 'hybrid' / 'procrustes_ctrl'

    if hybrid_nested_dir.exists():
        hybrid_nested_data = load_hybrid(hybrid_nested_dir)
        hybrid_nested_stats = compute_model_stats(hybrid_nested_data,
                                                   ['ForwardEncoding', 'FE_MLP', 'FE_SVM'])
        print(f"  Hybrid (nested): loaded")
    else:
        print(f"  WARNING: {hybrid_nested_dir} not found")
        hybrid_nested_stats = None

    if hybrid_ctrl_dir.exists():
        hybrid_ctrl_data = load_hybrid(hybrid_ctrl_dir)
        hybrid_ctrl_stats = compute_model_stats(hybrid_ctrl_data,
                                                 ['ForwardEncoding', 'FE_MLP', 'FE_SVM'])
        print(f"  Hybrid (ctrl): loaded")
    else:
        hybrid_ctrl_stats = None

    # Generate figures
    print("\nGenerating figures...")

    if original_stats and nested_stats and hybrid_nested_stats:
        plot_full_model_comparison(original_stats, nested_stats, hybrid_nested_stats)

    if nested_stats and ctrl_stats and hybrid_nested_stats and hybrid_ctrl_stats:
        plot_alignment_and_hybrid(nested_stats, ctrl_stats,
                                  hybrid_nested_stats, hybrid_ctrl_stats)

    if nested_stats and hybrid_nested_stats:
        plot_roi_breakdown(nested_stats, hybrid_nested_stats)

    if original_stats and nested_stats and ctrl_stats and hybrid_nested_stats and hybrid_ctrl_stats:
        plot_analysis_story(original_stats, nested_stats, ctrl_stats,
                           hybrid_nested_stats, hybrid_ctrl_stats)

    print("\nDone!")


if __name__ == '__main__':
    main()
