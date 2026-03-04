#!/usr/bin/env python3
"""
Phase 1: MDS Diagnostic for LOCO Decoder Improvement

Diagnoses whether 8 colors form circular structure in neural representations
and which alignment method best preserves it.

6 sub-analyses:
  1. Stress plot (1-6D MDS) per ROI x alignment
  2. 2D MDS embedding visualization
  3. Circular order test (arctan2 -> Spearman rank)
  4. Shepard plot (original vs fitted distances)
  5. Cross-alignment Procrustes comparison
  6. Mantel test (neural RDM vs ideal circular RDM)

Usage (local):
    conda activate srm
    python scripts/mds_diagnostic.py

Output:
    results/mds_diagnostic/ (figures + summary JSON)
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
from scipy.linalg import orthogonal_procrustes
from sklearn.manifold import MDS

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
RESULTS_DIR = PROJECT_DIR / 'results' / 'mds_diagnostic'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Data path (local)
DATA_DIR = Path(__file__).resolve().parents[3] / \
    'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

# Constants
HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

ROIS = ['V1', 'V2', 'V3', 'hV4']
ROI_DIRS = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}

ALIGNMENTS = ['raw', 'procrustes', 'srm']
HUE_ANGLES = np.array([i * 45 for i in range(8)])  # 0, 45, ..., 315

# Color RGB for plotting (from CIELab)
COLOR_RGBS = [
    (0.85, 0.25, 0.30),  # color_1: red
    (0.90, 0.55, 0.20),  # color_2: orange
    (0.70, 0.55, 0.15),  # color_3: yellow-brown
    (0.15, 0.70, 0.30),  # color_4: green
    (0.20, 0.72, 0.65),  # color_5: cyan
    (0.30, 0.55, 0.80),  # color_6: blue
    (0.40, 0.30, 0.75),  # color_7: purple
    (0.70, 0.30, 0.65),  # color_8: magenta
]

COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']


# ============================================================================
# Data Loading
# ============================================================================

def load_amplitudes(subject, roi, alignment='raw'):
    """Load amplitudes for a subject-ROI-alignment combination."""
    roi_dir = ROI_DIRS[roi]
    amp_path = DATA_DIR / f'sub-{subject}' / roi_dir / f'amplitudes_{alignment}.npy'
    if not amp_path.exists():
        raise FileNotFoundError(f'Not found: {amp_path}')
    return np.load(amp_path)  # (6, 8, n_features)


def compute_rdm(patterns):
    """Compute RDM from (8, n_features) using correlation distance."""
    return squareform(pdist(patterns, metric='correlation'))


def ideal_circular_rdm():
    """Compute ideal circular RDM based on angular distances between 8 hues."""
    n = len(HUE_ANGLES)
    rdm = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            diff = abs(HUE_ANGLES[i] - HUE_ANGLES[j])
            rdm[i, j] = min(diff, 360 - diff)
    # Normalize to 0-1
    return rdm / rdm.max()


# ============================================================================
# Analysis 1: Stress Plot (1-6D)
# ============================================================================

def normalized_stress(rdm, coords):
    """Compute Kruskal's normalized stress-1."""
    # squareform converts square matrix -> condensed 1D vector
    dists_orig = squareform(rdm)
    dists_mds = pdist(coords, metric='euclidean')
    return np.sqrt(np.sum((dists_orig - dists_mds) ** 2) / np.sum(dists_orig ** 2))


def compute_stress_curve(rdm, max_dims=6, n_init=10, random_state=42):
    """Compute MDS normalized stress for dimensions 1 to max_dims."""
    stresses = []
    for n_dim in range(1, max_dims + 1):
        mds = MDS(n_components=n_dim, metric=True, n_init=n_init,
                  max_iter=500, random_state=random_state,
                  dissimilarity='precomputed')
        coords = mds.fit_transform(rdm)
        stress = normalized_stress(rdm, coords)
        stresses.append(stress)
    return stresses


def plot_stress(all_stresses, output_path):
    """
    Stress plot: 4 columns (V1-V4) x 1 row, 3 lines per alignment.
    Horizontal line at stress=0.1.
    """
    fig, axes = plt.subplots(1, 4, figsize=(16, 4), sharey=True)
    dims = list(range(1, 7))
    colors_align = {'raw': '#e74c3c', 'procrustes': '#3498db', 'srm': '#2ecc71'}

    for col, roi in enumerate(ROIS):
        ax = axes[col]
        for align in ALIGNMENTS:
            key = (roi, align)
            if key in all_stresses:
                stresses = all_stresses[key]
                ax.plot(dims, stresses, 'o-', color=colors_align[align],
                        label=align, linewidth=1.5, markersize=4)
        ax.axhline(y=0.1, color='gray', linestyle='--', alpha=0.5, label='stress=0.1')
        ax.set_xlabel('Dimensions')
        ax.set_title(roi)
        ax.set_xticks(dims)
        if col == 0:
            ax.set_ylabel('Normalized Stress')

    axes[0].legend(fontsize=8, loc='upper right')
    fig.suptitle('MDS Stress by Dimensionality (HC group mean RDM)', fontsize=13)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Analysis 2: 2D MDS Visualization
# ============================================================================

def compute_2d_mds(rdm, random_state=42):
    """Compute 2D MDS embedding from RDM."""
    mds = MDS(n_components=2, metric=True, n_init=10, max_iter=500,
              random_state=random_state, dissimilarity='precomputed')
    coords = mds.fit_transform(rdm)
    stress = normalized_stress(rdm, coords)
    return coords, stress


def plot_2d_mds(all_mds_coords, output_path):
    """
    2D MDS: 3 rows (alignment) x 5 columns (HC mean, CVD mean, sub-05, sub-09, sub-10).
    Each subplot shows 8 color points + connecting lines.
    """
    display_cols = [
        ('HC mean', None),
        ('CVD mean', None),
        ('sub-05', '05'),
        ('sub-09', '09'),
        ('sub-10', '10'),
    ]

    fig, axes = plt.subplots(3, 5, figsize=(20, 12))

    for row, align in enumerate(ALIGNMENTS):
        for col, (label, subj) in enumerate(display_cols):
            ax = axes[row, col]
            key = (align, label)

            if key in all_mds_coords:
                coords = all_mds_coords[key]
                # Plot connecting lines (circular order)
                order = list(range(8)) + [0]
                ax.plot(coords[order, 0], coords[order, 1],
                        'k-', alpha=0.3, linewidth=0.8)
                # Plot color points
                for i in range(8):
                    ax.scatter(coords[i, 0], coords[i, 1],
                              c=[COLOR_RGBS[i]], s=80, edgecolors='k',
                              linewidths=0.5, zorder=3)
                    ax.annotate(f'{HUE_ANGLES[i]}',
                               (coords[i, 0], coords[i, 1]),
                               textcoords='offset points', xytext=(5, 5),
                               fontsize=7, alpha=0.7)

            ax.set_aspect('equal')
            ax.set_xticks([])
            ax.set_yticks([])
            if row == 0:
                ax.set_title(label, fontsize=10)
            if col == 0:
                ax.set_ylabel(align, fontsize=10)

    fig.suptitle('2D MDS Embeddings (V1, per alignment)', fontsize=14)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Analysis 3: Circular Order Test
# ============================================================================

def circular_order_correlation(coords_2d):
    """
    Compute Spearman rank correlation between MDS angular order and true hue order.

    Args:
        coords_2d: (8, 2) MDS coordinates

    Returns:
        rho: Spearman r
        pval: p-value
    """
    # Compute angles from MDS coordinates
    angles = np.arctan2(coords_2d[:, 1], coords_2d[:, 0])
    angles_deg = np.rad2deg(angles) % 360

    # Rank both
    true_ranks = np.argsort(np.argsort(HUE_ANGLES))

    # Try both CW and CCW orderings (MDS can flip)
    angles_sorted = np.argsort(np.argsort(angles_deg))
    rho1, p1 = spearmanr(true_ranks, angles_sorted)

    # Flip
    angles_flipped = np.argsort(np.argsort(360 - angles_deg))
    rho2, p2 = spearmanr(true_ranks, angles_flipped)

    # Return the better one
    if abs(rho1) >= abs(rho2):
        return rho1, p1
    else:
        return rho2, p2


# ============================================================================
# Analysis 4: Shepard Plot
# ============================================================================

def compute_shepard_r2(rdm, coords_2d):
    """Compute R2 for Shepard plot (original distances vs MDS distances)."""
    # squareform converts square matrix -> condensed 1D vector
    orig_flat = squareform(rdm)
    mds_flat = pdist(coords_2d, metric='euclidean')

    # R2
    ss_res = np.sum((orig_flat - mds_flat) ** 2)
    ss_tot = np.sum((orig_flat - np.mean(orig_flat)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    return r2, orig_flat, mds_flat


def plot_shepard(all_shepard, output_path):
    """
    Shepard plot: 4 rows (ROI) x 3 columns (alignment).
    Scatter + diagonal.
    """
    fig, axes = plt.subplots(4, 3, figsize=(12, 16))

    for row, roi in enumerate(ROIS):
        for col, align in enumerate(ALIGNMENTS):
            ax = axes[row, col]
            key = (roi, align)
            if key in all_shepard:
                orig, fitted, r2 = all_shepard[key]
                ax.scatter(orig, fitted, s=10, alpha=0.6, c='steelblue')
                lims = [0, max(orig.max(), fitted.max()) * 1.05]
                ax.plot(lims, lims, 'k--', alpha=0.3)
                ax.set_xlim(lims)
                ax.set_ylim(lims)
                ax.text(0.05, 0.92, f'R2={r2:.3f}', transform=ax.transAxes,
                        fontsize=9, va='top')
            if row == 0:
                ax.set_title(align, fontsize=10)
            if col == 0:
                ax.set_ylabel(f'{roi}\nMDS distance', fontsize=9)
            if row == 3:
                ax.set_xlabel('Original distance', fontsize=9)

    fig.suptitle('Shepard Plots (HC group mean RDM)', fontsize=13)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Analysis 5: Cross-Alignment Procrustes Comparison
# ============================================================================

def procrustes_disparity(coords_a, coords_b):
    """Compute Procrustes disparity between two 2D MDS solutions."""
    # Center
    a = coords_a - coords_a.mean(axis=0)
    b = coords_b - coords_b.mean(axis=0)
    # Scale to unit Frobenius norm
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    # Optimal rotation
    R, scale = orthogonal_procrustes(a, b)
    a_rot = a @ R
    # Disparity
    disparity = np.sum((a_rot - b) ** 2)
    return disparity


# ============================================================================
# Analysis 6: Mantel Test
# ============================================================================

def mantel_test(rdm_neural, rdm_ideal, n_permutations=10000, random_state=42):
    """
    Mantel test: Spearman correlation between neural RDM and ideal circular RDM.
    Permutation test: shuffle rows+cols of one RDM.

    Returns:
        r_obs: observed Spearman r
        p_value: proportion of permuted r >= observed r
        null_dist: array of permuted r values
    """
    rng = np.random.default_rng(random_state)

    # Upper triangle vectors
    triu_idx = np.triu_indices(rdm_neural.shape[0], k=1)
    vec_neural = rdm_neural[triu_idx]
    vec_ideal = rdm_ideal[triu_idx]

    r_obs, _ = spearmanr(vec_neural, vec_ideal)

    null_dist = np.zeros(n_permutations)
    n = rdm_neural.shape[0]

    for i in range(n_permutations):
        perm = rng.permutation(n)
        rdm_perm = rdm_neural[np.ix_(perm, perm)]
        vec_perm = rdm_perm[triu_idx]
        null_dist[i], _ = spearmanr(vec_perm, vec_ideal)

    p_value = np.mean(null_dist >= r_obs)
    return r_obs, p_value, null_dist


def plot_mantel(all_mantel, output_path):
    """
    Mantel test: 4 rows (ROI) x 3 columns (alignment).
    Null distribution histogram + observed r vertical line.
    """
    fig, axes = plt.subplots(4, 3, figsize=(12, 16))

    for row, roi in enumerate(ROIS):
        for col, align in enumerate(ALIGNMENTS):
            ax = axes[row, col]
            key = (roi, align)
            if key in all_mantel:
                r_obs, p_val, null_dist = all_mantel[key]
                ax.hist(null_dist, bins=50, color='lightblue', edgecolor='gray',
                        alpha=0.7)
                ax.axvline(r_obs, color='red', linewidth=2, label=f'r={r_obs:.3f}')
                ax.text(0.05, 0.92, f'p={p_val:.4f}',
                        transform=ax.transAxes, fontsize=9, va='top')
                if r_obs > 0:
                    ax.legend(fontsize=8, loc='upper left')
            if row == 0:
                ax.set_title(align, fontsize=10)
            if col == 0:
                ax.set_ylabel(roi, fontsize=10)
            if row == 3:
                ax.set_xlabel('Spearman r', fontsize=9)

    fig.suptitle('Mantel Test: Neural RDM vs Ideal Circular RDM (HC mean)', fontsize=13)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Main
# ============================================================================

def main():
    print('=' * 70)
    print('Phase 1: MDS Diagnostic')
    print('=' * 70)
    print(f'Data dir: {DATA_DIR}')
    print(f'Output: {RESULTS_DIR}')
    print()

    # Containers for all analyses
    all_stresses = {}      # (roi, align) -> [stress1..stress6]
    all_mds_coords = {}    # (align, label) -> (8, 2)
    all_circular = {}      # (roi, align) -> (rho, p)
    all_shepard = {}       # (roi, align) -> (orig_flat, mds_flat, r2)
    all_mantel = {}        # (roi, align) -> (r_obs, p_val, null_dist)
    all_procrustes = {}    # (roi, align_a, align_b) -> disparity

    rdm_ideal = ideal_circular_rdm()

    for roi in ROIS:
        print(f'\n--- {roi} ---')
        roi_dir = ROI_DIRS[roi]

        for align in ALIGNMENTS:
            print(f'  {align}:')

            # Load all subjects
            rdms_hc = []
            rdms_cvd = []
            rdms_all = {}

            for subj in ALL_SUBJECTS:
                try:
                    amp = load_amplitudes(subj, roi, align)
                    mean_pattern = amp.mean(axis=0)  # (8, n_features)
                    rdm = compute_rdm(mean_pattern)
                    rdms_all[subj] = rdm
                    if subj in HC_SUBJECTS:
                        rdms_hc.append(rdm)
                    else:
                        rdms_cvd.append(rdm)
                except FileNotFoundError:
                    print(f'    WARNING: sub-{subj} {roi} {align} not found')

            if not rdms_hc:
                print(f'    No HC data, skipping')
                continue

            # HC group mean RDM
            rdm_hc_mean = np.mean(rdms_hc, axis=0)
            rdm_cvd_mean = np.mean(rdms_cvd, axis=0) if rdms_cvd else None

            # --- Analysis 1: Stress curve ---
            stresses = compute_stress_curve(rdm_hc_mean)
            all_stresses[(roi, align)] = stresses
            print(f'    Stress (2D): {stresses[1]:.4f}')

            # --- Analysis 2 & 3 & 4: 2D MDS ---
            coords_hc, stress_2d = compute_2d_mds(rdm_hc_mean)

            # Store HC mean coords for V1 (main ROI for detailed 2D plot)
            if roi == 'V1':
                all_mds_coords[(align, 'HC mean')] = coords_hc
                if rdm_cvd_mean is not None:
                    coords_cvd, _ = compute_2d_mds(rdm_cvd_mean)
                    all_mds_coords[(align, 'CVD mean')] = coords_cvd

                for label, subj in [('sub-05', '05'), ('sub-09', '09'), ('sub-10', '10')]:
                    if subj in rdms_all:
                        c, _ = compute_2d_mds(rdms_all[subj])
                        all_mds_coords[(align, label)] = c

            # --- Analysis 3: Circular order ---
            rho, p = circular_order_correlation(coords_hc)
            all_circular[(roi, align)] = (rho, p)
            print(f'    Circular order: rho={rho:.3f}, p={p:.4f}')

            # --- Analysis 4: Shepard ---
            r2, orig_flat, mds_flat = compute_shepard_r2(rdm_hc_mean, coords_hc)
            all_shepard[(roi, align)] = (orig_flat, mds_flat, r2)
            print(f'    Shepard R2: {r2:.3f}')

            # --- Analysis 6: Mantel test ---
            r_obs, p_val, null_dist = mantel_test(rdm_hc_mean, rdm_ideal)
            all_mantel[(roi, align)] = (r_obs, p_val, null_dist)
            print(f'    Mantel: r={r_obs:.3f}, p={p_val:.4f}')

        # --- Analysis 5: Cross-alignment Procrustes ---
        for i, a1 in enumerate(ALIGNMENTS):
            for a2 in ALIGNMENTS[i+1:]:
                k1 = (roi, a1)
                k2 = (roi, a2)
                # Use HC mean 2D coords from stress analysis
                rdm1_key = (roi, a1)
                rdm2_key = (roi, a2)
                if rdm1_key in all_stresses and rdm2_key in all_stresses:
                    # Recompute 2D MDS for both
                    # We already have rdm_hc_mean for the last alignment...
                    # Recompute from stored RDMs
                    pass  # Will compute below

    # Compute cross-alignment Procrustes for each ROI
    print('\n--- Cross-Alignment Procrustes ---')
    for roi in ROIS:
        coords_per_align = {}
        for align in ALIGNMENTS:
            # Reload HC group mean RDM
            rdms_hc = []
            for subj in HC_SUBJECTS:
                try:
                    amp = load_amplitudes(subj, roi, align)
                    mean_pattern = amp.mean(axis=0)
                    rdm = compute_rdm(mean_pattern)
                    rdms_hc.append(rdm)
                except FileNotFoundError:
                    pass
            if rdms_hc:
                rdm_hc_mean = np.mean(rdms_hc, axis=0)
                coords, _ = compute_2d_mds(rdm_hc_mean)
                coords_per_align[align] = coords

        for i, a1 in enumerate(ALIGNMENTS):
            for a2 in ALIGNMENTS[i+1:]:
                if a1 in coords_per_align and a2 in coords_per_align:
                    d = procrustes_disparity(coords_per_align[a1], coords_per_align[a2])
                    all_procrustes[(roi, a1, a2)] = d
                    print(f'  {roi}: {a1} vs {a2} -> disparity={d:.4f}')

    # ========================================================================
    # Generate Figures
    # ========================================================================
    print('\n--- Generating Figures ---')

    # Fig 1: Stress plot
    plot_stress(all_stresses, RESULTS_DIR / 'fig1_stress_plot.png')

    # Fig 2: 2D MDS (V1 only, detailed)
    plot_2d_mds(all_mds_coords, RESULTS_DIR / 'fig2_2d_mds_V1.png')

    # Fig 3: Shepard plots
    plot_shepard(all_shepard, RESULTS_DIR / 'fig3_shepard.png')

    # Fig 4: Mantel test
    plot_mantel(all_mantel, RESULTS_DIR / 'fig4_mantel.png')

    # ========================================================================
    # Save Summary JSON
    # ========================================================================
    summary = {
        'analysis': 'MDS_Diagnostic_Phase1',
        'data_dir': str(DATA_DIR),
        'decision_criteria': {
            '2D_stress_threshold': 0.10,
            'circular_order_threshold': 0.8,
            'mantel_r_threshold': 0.5,
            'shepard_r2_threshold': 0.80,
        },
        'stress_2d': {},
        'circular_order': {},
        'shepard_r2': {},
        'mantel': {},
        'procrustes_disparity': {},
    }

    for roi in ROIS:
        for align in ALIGNMENTS:
            key = f'{roi}_{align}'

            if (roi, align) in all_stresses:
                summary['stress_2d'][key] = float(all_stresses[(roi, align)][1])

            if (roi, align) in all_circular:
                rho, p = all_circular[(roi, align)]
                summary['circular_order'][key] = {
                    'rho': float(rho), 'p': float(p)
                }

            if (roi, align) in all_shepard:
                _, _, r2 = all_shepard[(roi, align)]
                summary['shepard_r2'][key] = float(r2)

            if (roi, align) in all_mantel:
                r_obs, p_val, _ = all_mantel[(roi, align)]
                summary['mantel'][key] = {
                    'r': float(r_obs), 'p': float(p_val)
                }

    for (roi, a1, a2), d in all_procrustes.items():
        summary['procrustes_disparity'][f'{roi}_{a1}_vs_{a2}'] = float(d)

    # Decision summary
    decisions = {}
    for roi in ROIS:
        roi_decision = {}
        for align in ALIGNMENTS:
            key = f'{roi}_{align}'
            checks = {}
            if key in summary['stress_2d']:
                checks['2d_stress_pass'] = summary['stress_2d'][key] < 0.10
            if key in summary['circular_order']:
                checks['circular_order_pass'] = abs(summary['circular_order'][key]['rho']) > 0.8
            if key in summary['mantel']:
                m = summary['mantel'][key]
                checks['mantel_pass'] = m['r'] > 0.5 and m['p'] < 0.05
            if key in summary['shepard_r2']:
                checks['shepard_pass'] = summary['shepard_r2'][key] > 0.80
            roi_decision[align] = checks
        decisions[roi] = roi_decision
    summary['decisions'] = decisions

    json_path = RESULTS_DIR / 'mds_summary.json'
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'  Saved: {json_path}')

    # ========================================================================
    # Print Decision Summary
    # ========================================================================
    print('\n' + '=' * 70)
    print('DECISION SUMMARY')
    print('=' * 70)
    for roi in ROIS:
        print(f'\n{roi}:')
        for align in ALIGNMENTS:
            key = f'{roi}_{align}'
            d = decisions[roi].get(align, {})
            stress = summary['stress_2d'].get(key, 'N/A')
            circ = summary['circular_order'].get(key, {})
            mantel = summary['mantel'].get(key, {})
            shepard = summary['shepard_r2'].get(key, 'N/A')

            passes = sum(1 for v in d.values() if v)
            total = len(d)

            stress_str = f'{stress:.4f}' if isinstance(stress, float) else stress
            circ_str = f'r={circ.get("rho", "?"):.3f}' if circ else 'N/A'
            mantel_str = f'r={mantel.get("r", "?"):.3f},p={mantel.get("p", "?"):.4f}' if mantel else 'N/A'
            shep_str = f'{shepard:.3f}' if isinstance(shepard, float) else shepard

            print(f'  {align:12s}: stress={stress_str} | circ={circ_str} | '
                  f'mantel={mantel_str} | shepard={shep_str} | '
                  f'{passes}/{total} pass')

    print('\n' + '=' * 70)
    print('Phase 1 complete. Check results/mds_diagnostic/ for figures and JSON.')
    print('=' * 70)


if __name__ == '__main__':
    main()
