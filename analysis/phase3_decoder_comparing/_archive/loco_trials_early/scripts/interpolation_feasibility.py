#!/usr/bin/env python3
"""
Interpolation Feasibility Diagnostic

8 diagnostics on the 8-color RDM to assess whether model-free interpolation
(e.g., GP regression) is viable, BEFORE attempting any interpolation.

Runs on both Procrustes and SRM alignments for all 10 subjects x 4 ROIs.

Diagnostics:
  1. Triangle inequality violations (metric validity)
  2. MDS eigenvalue spectrum (Euclidean embeddability)
  3. MDS stress-1 in 2D (low dimensionality)
  4. Circular ordering in MDS 2D (ring topology)
  5. Monotonicity: angular dist vs neural dist (Spearman rho)
  6. Adjacent/opposite distance ratio (smoothness)
  7. PCA variance explained by 2 PCs (dimensionality)
  8. Empirical Lipschitz constant (local smoothness)

Usage (local):
    conda activate srm
    python scripts/interpolation_feasibility.py

Output:
    results/interpolation_feasibility/
        diagnostic_summary.json       — full numeric results
        pass_fail_table.png           — visual summary
        per_subject_details.json      — per-subject breakdown
"""

import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.spatial.distance import squareform, pdist
from scipy.stats import spearmanr
from sklearn.manifold import MDS
from sklearn.decomposition import PCA
from itertools import combinations

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
RESULTS_DIR = PROJECT_DIR / 'results' / 'interpolation_feasibility'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = Path(__file__).resolve().parents[3] / \
    'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

ROIS = ['V1', 'V2', 'V3', 'hV4']
ROI_DIRS = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}
ALIGNMENTS = ['raw', 'procrustes', 'srm']

HUE_ANGLES = np.array([i * 45 for i in range(8)])  # 0, 45, ..., 315
N_COLORS = 8

# Thresholds
THRESHOLDS = {
    'triangle_violation_pct': 5.0,      # < 5% violations
    'neg_eigenvalue_ratio': 0.05,       # neg eigenval < 5% of max
    'stress_2d': 0.10,                  # < 0.10
    'circular_crossings': 0,            # 0 crossings
    'monotonicity_rho': 0.6,            # rho > 0.6
    'adj_opp_ratio': 0.7,              # < 0.7
    'pca_var_2pc': 0.70,               # > 70%
    'lipschitz_ratio': 1.5,            # L * 45 / std(y) < 1.5
}

COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green',
               'Cyan', 'Blue', 'Purple', 'Magenta']


# ============================================================================
# Data Loading
# ============================================================================

def load_amplitudes(subject, roi, alignment):
    """Load amplitudes for a subject-ROI-alignment combination.
    Returns (6, 8, n_features) array.
    """
    roi_dir = ROI_DIRS[roi]
    amp_path = DATA_DIR / f'sub-{subject}' / roi_dir / f'amplitudes_{alignment}.npy'
    if not amp_path.exists():
        return None
    return np.load(amp_path)


def compute_mean_pattern(amp):
    """Average across 6 runs to get (8, n_features) mean pattern."""
    return amp.mean(axis=0)


def compute_rdm(patterns):
    """Compute 8x8 RDM from (8, n_features) using correlation distance."""
    return squareform(pdist(patterns, metric='correlation'))


def angular_distance_matrix():
    """8x8 circular angular distance matrix (in degrees)."""
    n = N_COLORS
    d = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            diff = abs(HUE_ANGLES[i] - HUE_ANGLES[j])
            d[i, j] = min(diff, 360 - diff)
    return d


# ============================================================================
# Diagnostic 1: Triangle Inequality Violations
# ============================================================================

def check_triangle_inequality(rdm):
    """Check fraction of triangle inequality violations in 8x8 RDM.

    For every triple (i,j,k), check d(i,k) <= d(i,j) + d(j,k).
    With 8 stimuli: C(8,3) = 56 triples, 3 inequalities each = 168 checks.
    """
    n = rdm.shape[0]
    n_violations = 0
    n_checks = 0
    max_violation = 0.0

    for i, j, k in combinations(range(n), 3):
        for a, b, c in [(i, j, k), (j, i, k), (i, k, j)]:
            n_checks += 1
            violation = rdm[a, c] - (rdm[a, b] + rdm[b, c])
            if violation > 1e-10:
                n_violations += 1
                max_violation = max(max_violation, violation)

    pct = 100.0 * n_violations / n_checks if n_checks > 0 else 0
    passed = pct < THRESHOLDS['triangle_violation_pct']

    return {
        'n_violations': n_violations,
        'n_checks': n_checks,
        'violation_pct': round(pct, 2),
        'max_violation': round(float(max_violation), 6),
        'passed': passed,
    }


# ============================================================================
# Diagnostic 2: MDS Eigenvalue Spectrum (Euclidean Embeddability)
# ============================================================================

def check_eigenvalues(rdm):
    """Check if RDM is Euclidean-embeddable via classical MDS eigenvalues.

    B = -0.5 * H @ D^2 @ H where H is centering matrix.
    If all eigenvalues >= 0, perfectly Euclidean.
    """
    n = rdm.shape[0]
    H = np.eye(n) - np.ones((n, n)) / n
    D2 = rdm ** 2
    B = -0.5 * H @ D2 @ H

    eigenvalues = np.sort(np.linalg.eigvalsh(B))[::-1]  # descending

    max_pos = eigenvalues[0]
    min_neg = eigenvalues[eigenvalues < 0].min() if np.any(eigenvalues < 0) else 0
    neg_ratio = abs(min_neg) / max_pos if max_pos > 0 else 0

    passed = neg_ratio < THRESHOLDS['neg_eigenvalue_ratio']

    return {
        'eigenvalues': [round(float(e), 6) for e in eigenvalues],
        'max_positive': round(float(max_pos), 6),
        'min_negative': round(float(min_neg), 6),
        'neg_ratio': round(float(neg_ratio), 4),
        'passed': passed,
    }


# ============================================================================
# Diagnostic 3: MDS Stress-1 (2D)
# ============================================================================

def check_stress_2d(rdm):
    """Compute Kruskal's normalized stress-1 for 2D MDS."""
    mds = MDS(n_components=2, metric=True, n_init=20,
              max_iter=500, random_state=42,
              dissimilarity='precomputed')
    coords = mds.fit_transform(rdm)

    dists_orig = squareform(rdm)
    dists_mds = pdist(coords, metric='euclidean')
    stress = np.sqrt(np.sum((dists_orig - dists_mds) ** 2) /
                     np.sum(dists_orig ** 2))

    passed = stress < THRESHOLDS['stress_2d']

    return {
        'stress_2d': round(float(stress), 4),
        'mds_coords': coords,  # for downstream use
        'passed': passed,
    }


# ============================================================================
# Diagnostic 4: Circular Ordering in MDS 2D
# ============================================================================

def check_circular_ordering(mds_coords):
    """Check if MDS 2D embedding preserves hue circular order.

    Extract angles via arctan2, compare rank order with true hue order.
    Test both CW and CCW directions. Count crossings.
    """
    angles_mds = np.arctan2(mds_coords[:, 1], mds_coords[:, 0])
    angles_mds_deg = np.degrees(angles_mds) % 360

    # True hue order: 0, 1, 2, ..., 7
    true_order = np.arange(N_COLORS)

    # MDS order: sort by recovered angle
    mds_order = np.argsort(angles_mds_deg)

    # Count crossings: number of adjacent pairs in mds_order that are
    # NOT adjacent in true circular order
    n_crossings = 0
    for idx in range(N_COLORS):
        curr = mds_order[idx]
        next_mds = mds_order[(idx + 1) % N_COLORS]
        # In true circular order, adjacent means |diff| = 1 or 7
        diff = abs(int(curr) - int(next_mds))
        if diff != 1 and diff != (N_COLORS - 1):
            n_crossings += 1

    # Also compute Spearman rho (CW and CCW)
    rank_true = np.arange(N_COLORS, dtype=float)
    rank_mds_cw = np.argsort(np.argsort(angles_mds_deg)).astype(float)
    rank_mds_ccw = (N_COLORS - 1) - rank_mds_cw

    rho_cw, p_cw = spearmanr(rank_true, rank_mds_cw)
    rho_ccw, p_ccw = spearmanr(rank_true, rank_mds_ccw)

    if abs(rho_cw) >= abs(rho_ccw):
        best_rho, best_p = rho_cw, p_cw
    else:
        best_rho, best_p = rho_ccw, p_ccw

    passed = n_crossings <= THRESHOLDS['circular_crossings']

    return {
        'n_crossings': int(n_crossings),
        'mds_order': [int(x) for x in mds_order],
        'spearman_rho': round(float(best_rho), 3),
        'spearman_p': round(float(best_p), 4),
        'passed': passed,
    }


# ============================================================================
# Diagnostic 5: Monotonicity (Angular Distance vs Neural Distance)
# ============================================================================

def check_monotonicity(rdm):
    """Spearman correlation between angular distance and neural distance.

    28 unique pairs. Positive rho means closer hues have more similar
    neural patterns.
    """
    ang_dist = angular_distance_matrix()

    # Extract upper triangle
    triu_idx = np.triu_indices(N_COLORS, k=1)
    neural_dists = rdm[triu_idx]
    angular_dists = ang_dist[triu_idx]

    rho, p = spearmanr(angular_dists, neural_dists)

    passed = rho > THRESHOLDS['monotonicity_rho']

    return {
        'spearman_rho': round(float(rho), 3),
        'spearman_p': round(float(p), 4),
        'passed': passed,
    }


# ============================================================================
# Diagnostic 6: Adjacent/Opposite Distance Ratio (Smoothness)
# ============================================================================

def check_adj_opp_ratio(rdm):
    """Ratio of mean adjacent-pair distance to mean opposite-pair distance.

    Adjacent: 45° apart (8 pairs on the circle)
    Opposite: 180° apart (4 pairs)

    A smooth, interpolable space should have ratio << 1.
    """
    ang_dist = angular_distance_matrix()

    adj_mask = ang_dist == 45
    opp_mask = ang_dist == 180

    adj_dists = rdm[adj_mask]
    opp_dists = rdm[opp_mask]

    mean_adj = adj_dists.mean()
    mean_opp = opp_dists.mean()

    ratio = mean_adj / mean_opp if mean_opp > 0 else float('inf')

    passed = ratio < THRESHOLDS['adj_opp_ratio']

    return {
        'mean_adjacent': round(float(mean_adj), 4),
        'mean_opposite': round(float(mean_opp), 4),
        'ratio': round(float(ratio), 4),
        'passed': passed,
    }


# ============================================================================
# Diagnostic 7: PCA Variance Explained (2 PCs)
# ============================================================================

def check_pca_variance(patterns):
    """Fraction of variance explained by first 2 PCs of (8, n_features).

    High explained variance (>70%) means the representation is low-dimensional,
    consistent with a ring/circle, and interpolation is well-supported.
    """
    n_components = min(2, patterns.shape[0], patterns.shape[1])
    pca = PCA(n_components=n_components)
    pca.fit(patterns)

    var_explained = pca.explained_variance_ratio_
    total_2pc = var_explained[:2].sum() if len(var_explained) >= 2 else var_explained.sum()

    passed = total_2pc > THRESHOLDS['pca_var_2pc']

    return {
        'pc1_var': round(float(var_explained[0]), 4),
        'pc2_var': round(float(var_explained[1]), 4) if len(var_explained) > 1 else 0,
        'total_2pc': round(float(total_2pc), 4),
        'all_variances': [round(float(v), 4) for v in var_explained],
        'passed': passed,
    }


# ============================================================================
# Diagnostic 8: Empirical Lipschitz Constant
# ============================================================================

def check_lipschitz(patterns):
    """Empirical Lipschitz constant: max gradient of neural response over hue angle.

    L_hat = max over adjacent pairs: ||y_i - y_{i+1}|| / 45°
    Then check L_hat * 45 / std(y) < threshold.

    This tests whether the neural response changes too rapidly between
    adjacent measured colors for reliable interpolation.
    """
    # Compute L2 norms of differences between adjacent colors (circular)
    gradients = []
    for i in range(N_COLORS):
        j = (i + 1) % N_COLORS
        diff_norm = np.linalg.norm(patterns[i] - patterns[j])
        gradients.append(diff_norm / 45.0)  # per degree

    L_hat = max(gradients)
    mean_std = np.std(patterns, axis=0).mean()  # mean voxel std across colors

    ratio = (L_hat * 45.0) / mean_std if mean_std > 0 else float('inf')

    passed = ratio < THRESHOLDS['lipschitz_ratio']

    return {
        'L_hat': round(float(L_hat), 6),
        'mean_voxel_std': round(float(mean_std), 6),
        'lipschitz_ratio': round(float(ratio), 4),
        'per_pair_gradients': [round(float(g), 6) for g in gradients],
        'passed': passed,
    }


# ============================================================================
# Run All Diagnostics
# ============================================================================

def run_diagnostics(patterns, rdm):
    """Run all 8 diagnostics on a single subject-ROI-alignment."""
    results = {}

    # 1. Triangle inequality
    results['1_triangle'] = check_triangle_inequality(rdm)

    # 2. Eigenvalue spectrum
    results['2_eigenvalue'] = check_eigenvalues(rdm)

    # 3. MDS stress-1 (2D)
    stress_result = check_stress_2d(rdm)
    mds_coords = stress_result.pop('mds_coords')
    results['3_stress'] = stress_result

    # 4. Circular ordering
    results['4_circular'] = check_circular_ordering(mds_coords)

    # 5. Monotonicity
    results['5_monotonicity'] = check_monotonicity(rdm)

    # 6. Adjacent/opposite ratio
    results['6_adj_opp'] = check_adj_opp_ratio(rdm)

    # 7. PCA variance
    results['7_pca'] = check_pca_variance(patterns)

    # 8. Lipschitz
    results['8_lipschitz'] = check_lipschitz(patterns)

    # Count passes
    n_passed = sum(1 for v in results.values() if v.get('passed', False))
    results['total_passed'] = n_passed
    results['total_diagnostics'] = 8

    return results


# ============================================================================
# Visualization
# ============================================================================

def plot_pass_fail_table(all_results, output_path):
    """Plot pass/fail heatmap: rows=subjects, cols=ROI×alignment, color=pass count."""
    diagnostic_names = [
        '1.Triangle', '2.Eigenval', '3.Stress',
        '4.Circular', '5.Monotone', '6.AdjOpp',
        '7.PCA', '8.Lipschitz'
    ]
    diag_keys = [
        '1_triangle', '2_eigenvalue', '3_stress',
        '4_circular', '5_monotonicity', '6_adj_opp',
        '7_pca', '8_lipschitz'
    ]

    # Build the matrix: rows = ROI x alignment, cols = diagnostics
    # Group by alignment, then aggregate across subjects
    n_align = len(ALIGNMENTS)
    fig, axes = plt.subplots(1, n_align, figsize=(7 * n_align, 10))
    if n_align == 1:
        axes = [axes]

    for ax_idx, alignment in enumerate(ALIGNMENTS):
        ax = axes[ax_idx]

        row_labels = []
        matrix = []

        for subj in ALL_SUBJECTS:
            for roi in ROIS:
                key = (subj, roi, alignment)
                if key not in all_results:
                    continue

                r = all_results[key]
                row = []
                for dk in diag_keys:
                    if dk in r and 'passed' in r[dk]:
                        row.append(1 if r[dk]['passed'] else 0)
                    else:
                        row.append(-1)  # missing

                row_labels.append(f'sub-{subj} {roi}')
                matrix.append(row)

        if not matrix:
            ax.set_title(f'{alignment.capitalize()} — No data')
            continue

        matrix = np.array(matrix)

        # Color map: 0=red (fail), 1=green (pass), -1=gray (missing)
        cmap = plt.cm.RdYlGn
        im = ax.imshow(matrix, cmap=cmap, aspect='auto', vmin=0, vmax=1)

        ax.set_xticks(range(len(diagnostic_names)))
        ax.set_xticklabels(diagnostic_names, rotation=45, ha='right', fontsize=7)
        ax.set_yticks(range(len(row_labels)))
        ax.set_yticklabels(row_labels, fontsize=6)

        # Add pass count on right
        for i, row in enumerate(matrix):
            n_pass = int((row == 1).sum())
            ax.text(len(diagnostic_names) - 0.3, i, f'{n_pass}/8',
                    va='center', ha='left', fontsize=6, fontweight='bold')

        ax.set_title(f'{alignment.capitalize()}', fontsize=12, fontweight='bold')

    fig.suptitle('Interpolation Feasibility: Pass/Fail per Subject × ROI',
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


def plot_summary_heatmap(all_results, output_path):
    """HC group-mean pass rate per ROI x alignment x diagnostic."""
    diagnostic_names = [
        'Triangle', 'Eigenval', 'Stress2D',
        'CircOrder', 'Monotone', 'AdjOpp',
        'PCA_2PC', 'Lipschitz'
    ]
    diag_keys = [
        '1_triangle', '2_eigenvalue', '3_stress',
        '4_circular', '5_monotonicity', '6_adj_opp',
        '7_pca', '8_lipschitz'
    ]

    n_align = len(ALIGNMENTS)
    fig, axes = plt.subplots(1, n_align, figsize=(6 * n_align, 5))
    if n_align == 1:
        axes = [axes]

    for ax_idx, alignment in enumerate(ALIGNMENTS):
        ax = axes[ax_idx]
        matrix = []
        row_labels = []

        for roi in ROIS:
            pass_rates = []
            for dk in diag_keys:
                passes = []
                for subj in HC_SUBJECTS:
                    key = (subj, roi, alignment)
                    if key in all_results and dk in all_results[key]:
                        passes.append(1 if all_results[key][dk]['passed'] else 0)
                rate = np.mean(passes) if passes else 0
                pass_rates.append(rate)
            matrix.append(pass_rates)
            row_labels.append(roi)

        matrix = np.array(matrix)
        im = ax.imshow(matrix, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)

        # Annotate with percentages
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                val = matrix[i, j]
                color = 'white' if val < 0.3 or val > 0.7 else 'black'
                ax.text(j, i, f'{val:.0%}', ha='center', va='center',
                        fontsize=8, color=color, fontweight='bold')

        ax.set_xticks(range(len(diagnostic_names)))
        ax.set_xticklabels(diagnostic_names, rotation=45, ha='right', fontsize=8)
        ax.set_yticks(range(len(row_labels)))
        ax.set_yticklabels(row_labels, fontsize=10)
        ax.set_title(f'{alignment.capitalize()}', fontsize=12, fontweight='bold')

        fig.colorbar(im, ax=ax, shrink=0.8, label='HC pass rate')

    fig.suptitle('Interpolation Feasibility: HC Pass Rate by ROI × Diagnostic',
                 fontsize=13, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Main
# ============================================================================

def main():
    print('=' * 70)
    print('Interpolation Feasibility Diagnostic')
    print('=' * 70)

    all_results = {}

    for alignment in ALIGNMENTS:
        print(f'\n--- Alignment: {alignment} ---')

        for subj in ALL_SUBJECTS:
            for roi in ROIS:
                try:
                    amp = load_amplitudes(subj, roi, alignment)
                    if amp is None:
                        print(f'  [SKIP] sub-{subj} {roi}/{alignment}: file not found')
                        continue

                    patterns = compute_mean_pattern(amp)  # (8, n_features)

                    # Check for NaN
                    if np.any(np.isnan(patterns)):
                        print(f'  [SKIP] sub-{subj} {roi}/{alignment}: NaN in patterns')
                        continue

                    rdm = compute_rdm(patterns)

                    # Check for NaN in RDM (happens with low-voxel ROIs)
                    if np.any(np.isnan(rdm)):
                        print(f'  [SKIP] sub-{subj} {roi}/{alignment}: NaN in RDM')
                        continue

                    results = run_diagnostics(patterns, rdm)
                    key = (subj, roi, alignment)
                    all_results[key] = results

                    group = 'CVD' if subj in CVD_SUBJECTS else 'HC'
                    n_pass = results['total_passed']
                    print(f'  sub-{subj} ({group}) {roi:>3}/{alignment}: '
                          f'{n_pass}/8 passed')

                except Exception as e:
                    print(f'  [ERROR] sub-{subj} {roi}/{alignment}: {e}')

    # ========================================================================
    # Summary statistics
    # ========================================================================
    print('\n' + '=' * 70)
    print('SUMMARY: HC Pass Rate by ROI × Alignment × Diagnostic')
    print('=' * 70)

    diag_keys = [
        '1_triangle', '2_eigenvalue', '3_stress',
        '4_circular', '5_monotonicity', '6_adj_opp',
        '7_pca', '8_lipschitz'
    ]
    diag_short = ['Tri', 'Eig', 'Str', 'Circ', 'Mono', 'A/O', 'PCA', 'Lip']

    header = f'{"ROI":>4} {"Align":>10} | ' + ' '.join(f'{d:>5}' for d in diag_short) + ' | Total'
    print(header)
    print('-' * len(header))

    summary_for_json = {}

    for alignment in ALIGNMENTS:
        for roi in ROIS:
            pass_counts = {dk: 0 for dk in diag_keys}
            n_subjects = 0

            for subj in HC_SUBJECTS:
                key = (subj, roi, alignment)
                if key not in all_results:
                    continue
                n_subjects += 1
                for dk in diag_keys:
                    if dk in all_results[key] and all_results[key][dk].get('passed'):
                        pass_counts[dk] += 1

            if n_subjects == 0:
                continue

            rates = [pass_counts[dk] / n_subjects for dk in diag_keys]
            total_rate = np.mean(rates)

            rates_str = ' '.join(f'{r:5.0%}' for r in rates)
            print(f'{roi:>4} {alignment:>10} | {rates_str} | {total_rate:.0%}')

            summary_for_json[f'{roi}_{alignment}'] = {
                'hc_pass_rates': {dk: round(pass_counts[dk] / n_subjects, 2)
                                  for dk in diag_keys},
                'overall_rate': round(float(total_rate), 2),
                'n_hc_subjects': n_subjects,
            }

    # ========================================================================
    # CVD summary
    # ========================================================================
    print('\n--- CVD Individual Results ---')
    for alignment in ALIGNMENTS:
        for subj in CVD_SUBJECTS:
            for roi in ROIS:
                key = (subj, roi, alignment)
                if key not in all_results:
                    continue
                r = all_results[key]
                n_pass = r['total_passed']
                failed = [dk.split('_')[1] for dk in diag_keys
                          if dk in r and not r[dk].get('passed', False)]
                print(f'  sub-{subj} {roi:>3}/{alignment:>10}: '
                      f'{n_pass}/8 | Failed: {", ".join(failed) if failed else "none"}')

    # ========================================================================
    # Save results
    # ========================================================================

    # Convert to JSON-serializable format
    json_results = {}
    for (subj, roi, align), res in all_results.items():
        json_key = f'sub-{subj}_{roi}_{align}'
        json_results[json_key] = {}
        for k, v in res.items():
            if isinstance(v, dict):
                json_results[json_key][k] = v
            else:
                json_results[json_key][k] = v

    with open(RESULTS_DIR / 'diagnostic_summary.json', 'w') as f:
        json.dump(summary_for_json, f, indent=2)
    print(f'\nSaved: {RESULTS_DIR / "diagnostic_summary.json"}')

    with open(RESULTS_DIR / 'per_subject_details.json', 'w') as f:
        json.dump(json_results, f, indent=2, default=str)
    print(f'Saved: {RESULTS_DIR / "per_subject_details.json"}')

    # Plots
    plot_pass_fail_table(all_results, RESULTS_DIR / 'pass_fail_table.png')
    plot_summary_heatmap(all_results, RESULTS_DIR / 'hc_summary_heatmap.png')

    print('\nDone.')


if __name__ == '__main__':
    main()
