#!/usr/bin/env python3
"""
Cone Contrast Coordinate Diagnostic

Tests whether cone-opponent coordinates (DKL-like) predict neural distances
better than hue angle or CIELab.

Computes:
  1. Approximate DKL coordinates from CIELab (a* ≈ L-M, b* ≈ S-(L+M))
  2. Monotonicity test with 4 different distance metrics:
     - Angular (equidistant hue)
     - CIELab Euclidean (a*, b*)
     - L-M only (|a*_i - a*_j|)
     - S-(L+M) only (|b*_i - b*_j|)
     - L-M weighted (2*a*² + b*²) — L-M dominant model
  3. Per-subject Spearman rho for each metric
  4. Direct comparison: which coordinate system best predicts neural RDM?

Usage:
    conda activate srm
    python scripts/cone_contrast_diagnostic.py
"""

import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.spatial.distance import squareform, pdist, cdist
from scipy.stats import spearmanr
from itertools import combinations

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
RESULTS_DIR = PROJECT_DIR / 'results' / 'cone_contrast_diagnostic'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = Path(__file__).resolve().parents[3] / \
    'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

ROIS = ['V1', 'V2', 'V3', 'hV4']
ROI_DIRS = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}
ALIGNMENTS = ['raw', 'procrustes', 'srm']

N_COLORS = 8
HUE_ANGLES = np.array([i * 45 for i in range(N_COLORS)])

# CIELab coordinates of 8 stimulus colors
# From utils/utils_color_decoding.py
COLOR_LAB = np.array([
    [59.90, 62.69,   3.78],   # color_1: Red (0°)
    [64.20, 49.20,  45.58],   # color_2: Orange (45°)
    [57.27, 13.06,  41.69],   # color_3: Yellow (90°)
    [69.08, -55.02, 47.38],   # color_4: Green (135°)
    [74.61, -41.33, -4.89],   # color_5: Cyan (180°)
    [69.14, -11.45, -40.91],  # color_6: Blue (225°)
    [60.68, 19.18,  -54.13],  # color_7: Purple (270°)
    [60.17, 46.82,  -40.31],  # color_8: Magenta (315°)
])

COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green',
               'Cyan', 'Blue', 'Purple', 'Magenta']


# ============================================================================
# Stimulus Distance Matrices (all known a priori, no neural data needed)
# ============================================================================

def angular_distance_matrix():
    """Equidistant circular angular distance (0-180°)."""
    n = N_COLORS
    d = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            diff = abs(HUE_ANGLES[i] - HUE_ANGLES[j])
            d[i, j] = min(diff, 360 - diff)
    return d


def cielab_distance_matrix():
    """CIELab Euclidean distance using (a*, b*) only (ignore L*)."""
    ab = COLOR_LAB[:, 1:3]  # (8, 2) — a* and b*
    return cdist(ab, ab, metric='euclidean')


def lm_distance_matrix():
    """L-M axis distance: |a*_i - a*_j|. Proxy for cone-opponent L-M."""
    a_star = COLOR_LAB[:, 1].reshape(-1, 1)  # (8, 1)
    return cdist(a_star, a_star, metric='euclidean')


def slm_distance_matrix():
    """S-(L+M) axis distance: |b*_i - b*_j|. Proxy for S cone-opponent."""
    b_star = COLOR_LAB[:, 2].reshape(-1, 1)  # (8, 1)
    return cdist(b_star, b_star, metric='euclidean')


def lm_weighted_distance_matrix(w_lm=2.0, w_s=1.0):
    """Weighted cone-opponent distance: sqrt(w_lm*(Δa*)² + w_s*(Δb*)²).

    Emphasizes L-M axis based on V2 literature finding (L-M dominant).
    """
    ab = COLOR_LAB[:, 1:3]  # (8, 2)
    n = N_COLORS
    d = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            da = ab[i, 0] - ab[j, 0]  # Δa* (L-M)
            db = ab[i, 1] - ab[j, 1]  # Δb* (S-(L+M))
            d[i, j] = np.sqrt(w_lm * da**2 + w_s * db**2)
    return d


# ============================================================================
# Data Loading & Neural RDM
# ============================================================================

def load_amplitudes(subject, roi, alignment):
    roi_dir = ROI_DIRS[roi]
    amp_path = DATA_DIR / f'sub-{subject}' / roi_dir / f'amplitudes_{alignment}.npy'
    if not amp_path.exists():
        return None
    return np.load(amp_path)


def compute_neural_rdm(amp):
    """From (6, 8, n_features) → run-averaged (8, n_features) → correlation RDM."""
    patterns = amp.mean(axis=0)  # (8, n_features)
    if np.any(np.isnan(patterns)):
        return None
    return squareform(pdist(patterns, metric='correlation'))


# ============================================================================
# Monotonicity Test
# ============================================================================

def test_monotonicity(neural_rdm, stim_rdm):
    """Spearman rho between upper-triangle of neural RDM and stimulus RDM."""
    triu = np.triu_indices(N_COLORS, k=1)
    neural_vec = neural_rdm[triu]
    stim_vec = stim_rdm[triu]
    rho, p = spearmanr(stim_vec, neural_vec)
    return float(rho), float(p)


# ============================================================================
# Main
# ============================================================================

def main():
    print('=' * 70)
    print('Cone Contrast Coordinate Diagnostic')
    print('=' * 70)

    # Compute all stimulus distance matrices
    stim_dists = {
        'angular': angular_distance_matrix(),
        'cielab_ab': cielab_distance_matrix(),
        'LM_only': lm_distance_matrix(),
        'S_only': slm_distance_matrix(),
        'LM_weighted': lm_weighted_distance_matrix(w_lm=2.0, w_s=1.0),
    }

    # Print stimulus pairwise distances for reference
    print('\n--- Stimulus Pairwise Distances (selected pairs) ---')
    pair_labels = []
    triu = np.triu_indices(N_COLORS, k=1)
    for i, j in zip(triu[0], triu[1]):
        pair_labels.append(f'{COLOR_NAMES[i][:3]}-{COLOR_NAMES[j][:3]}')

    print(f'{"Pair":>10} {"Angle":>7} {"CIELab":>7} {"L-M":>7} {"S":>7} {"LMw":>7}')
    for idx, (i, j) in enumerate(zip(triu[0], triu[1])):
        if abs(HUE_ANGLES[i] - HUE_ANGLES[j]) <= 45 or abs(HUE_ANGLES[i] - HUE_ANGLES[j]) >= 315:
            label = f'{COLOR_NAMES[i][:3]}-{COLOR_NAMES[j][:3]}'
            vals = [stim_dists[k][i, j] for k in stim_dists]
            print(f'{label:>10} {vals[0]:7.1f} {vals[1]:7.1f} {vals[2]:7.1f} {vals[3]:7.1f} {vals[4]:7.1f}')

    # Run monotonicity test for all subjects x ROIs x alignments x metrics
    all_results = {}

    for alignment in ALIGNMENTS:
        for subj in ALL_SUBJECTS:
            for roi in ROIS:
                amp = load_amplitudes(subj, roi, alignment)
                if amp is None:
                    continue
                neural_rdm = compute_neural_rdm(amp)
                if neural_rdm is None:
                    continue

                result = {}
                for metric_name, stim_rdm in stim_dists.items():
                    rho, p = test_monotonicity(neural_rdm, stim_rdm)
                    result[metric_name] = {'rho': round(rho, 3), 'p': round(p, 4)}

                key = f'sub-{subj}_{roi}_{alignment}'
                all_results[key] = result

    # ========================================================================
    # Summary: HC mean rho per ROI x alignment x metric
    # ========================================================================
    print('\n' + '=' * 70)
    print('HC Mean Spearman rho: Stimulus Distance vs Neural Distance')
    print('=' * 70)

    metric_names = list(stim_dists.keys())
    metric_short = ['Angle', 'CIELab', 'L-M', 'S', 'LMw']

    header = f'{"ROI":>4} {"Align":>10} | ' + \
             ' '.join(f'{m:>8}' for m in metric_short) + ' | Best'
    print(header)
    print('-' * len(header))

    summary = {}

    for alignment in ALIGNMENTS:
        for roi in ROIS:
            rhos_by_metric = {m: [] for m in metric_names}

            for subj in HC_SUBJECTS:
                key = f'sub-{subj}_{roi}_{alignment}'
                if key not in all_results:
                    continue
                for m in metric_names:
                    rhos_by_metric[m].append(all_results[key][m]['rho'])

            means = {m: np.mean(rhos_by_metric[m]) for m in metric_names
                     if rhos_by_metric[m]}
            if not means:
                continue

            best_metric = max(means, key=means.get)
            best_rho = means[best_metric]

            vals_str = ' '.join(f'{means[m]:8.3f}' for m in metric_names)
            best_short = metric_short[metric_names.index(best_metric)]
            print(f'{roi:>4} {alignment:>10} | {vals_str} | {best_short} ({best_rho:.3f})')

            summary[f'{roi}_{alignment}'] = {
                m: round(means[m], 3) for m in metric_names
            }
            summary[f'{roi}_{alignment}']['best'] = best_metric

    # ========================================================================
    # Per-subject detail for best metric
    # ========================================================================
    print('\n--- Per-Subject Detail (Procrustes, rho) ---')
    print(f'{"Subject":>8} {"Group":>4} | ' +
          ' '.join(f'{m:>8}' for m in metric_short))
    print('-' * 60)

    for roi in ROIS:
        print(f'\n  {roi}:')
        for subj in ALL_SUBJECTS:
            key = f'sub-{subj}_{roi}_procrustes'
            if key not in all_results:
                continue
            group = 'CVD' if subj in CVD_SUBJECTS else 'HC'
            vals = [all_results[key][m]['rho'] for m in metric_names]
            best_val = max(vals)
            best_idx = vals.index(best_val)
            mark = ' *' if best_val > 0.4 else ''
            vals_str = ' '.join(f'{v:8.3f}' for v in vals)
            print(f'  sub-{subj} {group:>4} | {vals_str}{mark}')

    # ========================================================================
    # Statistical significance: how many subjects have rho > 0.4 per metric?
    # ========================================================================
    print('\n--- HC Subjects with rho > 0.4 (Procrustes) ---')
    print(f'{"ROI":>4} | ' + ' '.join(f'{m:>8}' for m in metric_short))
    for roi in ROIS:
        counts = []
        for m in metric_names:
            n = sum(1 for subj in HC_SUBJECTS
                    if f'sub-{subj}_{roi}_procrustes' in all_results and
                    all_results[f'sub-{subj}_{roi}_procrustes'][m]['rho'] > 0.4)
            counts.append(n)
        counts_str = ' '.join(f'{c:>6}/7 ' for c in counts)
        print(f'{roi:>4} | {counts_str}')

    # ========================================================================
    # Save
    # ========================================================================
    with open(RESULTS_DIR / 'cone_contrast_results.json', 'w') as f:
        json.dump({'per_subject': all_results, 'hc_summary': summary},
                  f, indent=2)
    print(f'\nSaved: {RESULTS_DIR / "cone_contrast_results.json"}')

    # ========================================================================
    # Visualization: HC mean rho barplot
    # ========================================================================
    fig, axes = plt.subplots(1, 3, figsize=(15, 5), sharey=True)

    colors_metric = ['#e74c3c', '#3498db', '#e67e22', '#9b59b6', '#2ecc71']

    for ax_idx, alignment in enumerate(ALIGNMENTS):
        ax = axes[ax_idx]
        x = np.arange(len(ROIS))
        width = 0.15

        for mi, m in enumerate(metric_names):
            means = []
            sems = []
            for roi in ROIS:
                rhos = []
                for subj in HC_SUBJECTS:
                    key = f'sub-{subj}_{roi}_{alignment}'
                    if key in all_results:
                        rhos.append(all_results[key][m]['rho'])
                means.append(np.mean(rhos) if rhos else 0)
                sems.append(np.std(rhos) / np.sqrt(len(rhos)) if rhos else 0)

            offset = (mi - 2) * width
            ax.bar(x + offset, means, width, yerr=sems,
                   label=metric_short[mi], color=colors_metric[mi], alpha=0.8)

        ax.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        ax.axhline(y=0.6, color='gray', linestyle='--', alpha=0.3,
                   label='threshold (0.6)')
        ax.set_xticks(x)
        ax.set_xticklabels(ROIS)
        ax.set_title(f'{alignment.capitalize()}', fontweight='bold')
        if ax_idx == 0:
            ax.set_ylabel('Spearman rho\n(stimulus dist vs neural dist)')
        if ax_idx == 2:
            ax.legend(fontsize=7, loc='upper right')

    fig.suptitle('Which stimulus coordinate predicts neural distance?',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / 'cone_contrast_comparison.png',
                dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved: {RESULTS_DIR / "cone_contrast_comparison.png"}')

    print('\nDone.')


if __name__ == '__main__':
    main()
