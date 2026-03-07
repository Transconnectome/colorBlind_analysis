#!/usr/bin/env python3
"""
Phase 1b: Extended V1/V2 Diagnostic

Follows up on Phase 1 MDS diagnostic where V1/V2 failed all 4 criteria.
Tests whether failure was due to inappropriate reference model (equidistant RDM)
vs genuine absence of color structure.

6 analyses:
  1. Full stress curve (1-7D) — elbow detection
  2. CIELab-based Mantel test — equidistant vs CIELab(ab) vs a*-only vs b*-only
  3. Persistent homology — H1 cycle detection via ripser
  4. Higher-D MDS + PCA 2D projection — recover circular order from 3D/4D
  5. Isomap vs MDS — nonlinear manifold comparison
  6. Per-subject V1/V2 analysis — individual circularity, ISC, CIELab Mantel

Usage (local):
    conda activate srm
    pip install ripser  # one-time
    python scripts/mds_extended_v1v2.py

Output:
    results/mds_diagnostic/extended_v1v2_summary.json
    results/mds_diagnostic/fig_ext1_stress_curve_7d.png
    results/mds_diagnostic/fig_ext2_cielab_mantel.png
    results/mds_diagnostic/fig_ext3_persistence.png
    results/mds_diagnostic/fig_ext4_higher_d_mds.png
    results/mds_diagnostic/fig_ext5_isomap_vs_mds.png
    results/mds_diagnostic/fig_ext6_per_subject.png
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
from sklearn.manifold import MDS, Isomap
from sklearn.decomposition import PCA

# ============================================================================
# Paths
# ============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent  # LOCO_trials/
RESULTS_DIR = PROJECT_DIR / 'results' / 'mds_diagnostic'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Import from mds_diagnostic.py (same directory)
sys.path.insert(0, str(SCRIPT_DIR))
from mds_diagnostic import (
    load_amplitudes, compute_rdm, normalized_stress, circular_order_correlation,
    mantel_test, ideal_circular_rdm,
    HC_SUBJECTS, CVD_SUBJECTS, ALL_SUBJECTS, ROIS, ROI_DIRS, ALIGNMENTS,
    HUE_ANGLES, COLOR_RGBS, COLOR_NAMES, DATA_DIR,
)

# CIELab coordinates from utils
UTILS_DIR = Path(__file__).resolve().parents[3] / 'utils'
sys.path.insert(0, str(UTILS_DIR))
from utils_color_decoding import COLOR_LAB

# Geometric analysis utils
VALIDATION_DIR = Path(__file__).resolve().parents[3] / 'validation' / 'scripts' / 'postSRM_procrustes' / 'utils'
sys.path.insert(0, str(VALIDATION_DIR))
from geometric_analysis import compute_circularity_mds, compute_geometric_consistency_isc

# ============================================================================
# Constants
# ============================================================================
SRM_K = {'V1': 4, 'V2': 4, 'V3': 3, 'hV4': 3}
FOCUS_ROIS = ['V1', 'V2']  # Extended diagnostics focus
ALL_ROIS = ['V1', 'V2', 'V3', 'hV4']  # For comparison
ALIGNMENT = 'srm'  # SRM is the canonical alignment

# Bonferroni correction: 4 models x 4 ROIs = 16 tests
BONFERRONI_ALPHA = 0.05 / 16


# ============================================================================
# CIELab Reference RDM Construction
# ============================================================================

def cielab_rdm(metric='ab'):
    """
    Construct CIELab-based reference RDM.

    Args:
        metric: 'ab' (full a*,b*), 'a_only' (L-M axis), 'b_only' (S-LM axis)

    Returns:
        rdm: (8, 8) normalized RDM (max=1)
    """
    n = 8
    coords = np.zeros((n, 2))  # even for 1D, we use 2D array for pdist

    for i in range(n):
        lab = COLOR_LAB[f'color_{i+1}']
        a_star, b_star = lab[1], lab[2]

        if metric == 'ab':
            coords[i] = [a_star, b_star]
        elif metric == 'a_only':
            coords[i] = [a_star, 0.0]
        elif metric == 'b_only':
            coords[i] = [0.0, b_star]
        else:
            raise ValueError(f"Unknown metric: {metric}")

    rdm = squareform(pdist(coords, metric='euclidean'))
    if rdm.max() > 0:
        rdm = rdm / rdm.max()
    return rdm


# ============================================================================
# Analysis 1: Full Stress Curve (1-7D)
# ============================================================================

def compute_stress_curve_extended(rdm, max_dims=7, n_init=10, random_state=42):
    """Compute MDS stress for dimensions 1 to max_dims."""
    stresses = []
    for n_dim in range(1, max_dims + 1):
        mds = MDS(n_components=n_dim, metric=True, n_init=n_init,
                  max_iter=500, random_state=random_state,
                  dissimilarity='precomputed')
        coords = mds.fit_transform(rdm)
        stress = normalized_stress(rdm, coords)
        stresses.append(float(stress))
    return stresses


def plot_stress_curve_7d(stress_data, output_path):
    """
    Plot stress curves for all 4 ROIs (SRM alignment only), 1-7D.
    Mark SRM k value and stress=0.10 threshold.
    """
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.5), sharey=True)
    dims = list(range(1, 8))

    for col, roi in enumerate(ALL_ROIS):
        ax = axes[col]
        if roi in stress_data:
            stresses = stress_data[roi]
            ax.plot(dims, stresses, 'o-', color='#2ecc71', linewidth=2, markersize=6,
                    label='SRM', zorder=3)

            # Mark SRM k
            k = SRM_K[roi]
            if k <= len(stresses):
                ax.axvline(x=k, color='#e74c3c', linestyle=':', alpha=0.7,
                           label=f'SRM k={k}')
                ax.scatter([k], [stresses[k-1]], s=120, color='#e74c3c',
                           marker='D', zorder=4, edgecolors='k', linewidths=0.5)

        ax.axhline(y=0.10, color='gray', linestyle='--', alpha=0.5, label='stress=0.10')
        ax.set_xlabel('Dimensions')
        ax.set_title(roi, fontsize=12, fontweight='bold')
        ax.set_xticks(dims)
        if col == 0:
            ax.set_ylabel('Normalized Stress')
        ax.legend(fontsize=8, loc='upper right')
        ax.set_ylim(bottom=-0.01)

    fig.suptitle('Analysis 1: Full Stress Curve (1-7D, SRM alignment, HC group mean)',
                 fontsize=13)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Analysis 2: CIELab-based Mantel Test
# ============================================================================

def cielab_mantel_comparison(rdm_neural, n_perm=10000, random_state=42):
    """
    Compare 4 reference RDMs via Mantel test.

    Returns:
        results: dict of {model_name: {'r': float, 'p': float}}
    """
    models = {
        'equidistant': ideal_circular_rdm(),
        'CIELab_ab': cielab_rdm('ab'),
        'CIELab_a_only': cielab_rdm('a_only'),
        'CIELab_b_only': cielab_rdm('b_only'),
    }

    results = {}
    for name, rdm_ref in models.items():
        r_obs, p_val, null_dist = mantel_test(rdm_neural, rdm_ref,
                                               n_permutations=n_perm,
                                               random_state=random_state)
        results[name] = {
            'r': float(r_obs),
            'p': float(p_val),
            'p_bonferroni': float(min(p_val * 16, 1.0)),
            'null_mean': float(np.mean(null_dist)),
            'null_std': float(np.std(null_dist)),
        }
    return results


def plot_cielab_mantel(mantel_data, output_path):
    """
    Bar chart: 4 ROIs x 4 reference models, showing Mantel r.
    Stars for significant p < 0.05/16 (Bonferroni).
    """
    fig, axes = plt.subplots(1, 4, figsize=(18, 5), sharey=True)
    model_names = ['equidistant', 'CIELab_ab', 'CIELab_a_only', 'CIELab_b_only']
    model_labels = ['Equidist', 'CIELab(a*,b*)', 'a*-only\n(L-M)', 'b*-only\n(S-LM)']
    colors = ['#95a5a6', '#e74c3c', '#3498db', '#f39c12']

    for col, roi in enumerate(ALL_ROIS):
        ax = axes[col]
        if roi not in mantel_data:
            ax.set_title(roi, fontsize=12, fontweight='bold')
            continue

        rs = []
        ps = []
        for model in model_names:
            if model in mantel_data[roi]:
                rs.append(mantel_data[roi][model]['r'])
                ps.append(mantel_data[roi][model]['p_bonferroni'])
            else:
                rs.append(0)
                ps.append(1.0)

        bars = ax.bar(range(4), rs, color=colors, edgecolor='k', linewidth=0.5)

        # Significance stars
        for i, (r, p) in enumerate(zip(rs, ps)):
            if p < 0.05:
                star = '***' if p < 0.001 else '**' if p < 0.01 else '*'
                y_pos = r + 0.02 if r >= 0 else r - 0.05
                ax.text(i, y_pos, star, ha='center', fontsize=12, fontweight='bold',
                        color='red')

        ax.set_xticks(range(4))
        ax.set_xticklabels(model_labels, fontsize=8, rotation=15, ha='right')
        ax.set_title(roi, fontsize=12, fontweight='bold')
        ax.axhline(y=0, color='k', linewidth=0.5)
        if col == 0:
            ax.set_ylabel('Mantel r (Spearman)')

        # Highlight V1/V2
        if roi in FOCUS_ROIS:
            ax.patch.set_facecolor('#fff9c4')
            ax.patch.set_alpha(0.3)

    fig.suptitle('Analysis 2: CIELab-based Mantel Test (SRM, HC group mean)\n'
                 '* p<0.05, ** p<0.01, *** p<0.001 (Bonferroni corrected)',
                 fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Analysis 3: Persistent Homology
# ============================================================================

def persistent_homology_test(rdm, srm_k, n_perm=1000, random_state=42):
    """
    Test for H1 (1-cycle/loop) in the neural RDM using ripser.

    Null model: random unit vectors on S^{k-1} (uniform on hypersphere).
    This is the correct null because:
      - Matches data dimensionality (SRM k)
      - Matches distance metric (correlation distance ~ angular distance)
      - Generates structureless point clouds (no topological bias)
      - Avoids the label-invariance problem of row/col permutation

    The original row/col permutation null was INVALID: TDA is label-invariant,
    so permuting a symmetric distance matrix yields the same persistence diagram
    every time (null_std = 0, all p = 1.0).

    Args:
        rdm: (8, 8) correlation distance RDM
        srm_k: SRM dimensionality (3 or 4) for generating matched null
        n_perm: number of null samples
        random_state: random seed

    Returns:
        result: dict with H1 lifetime, p-value, and method used
    """
    rng = np.random.default_rng(random_state)

    try:
        from ripser import ripser
        use_ripser = True
    except ImportError:
        print('    WARNING: ripser not installed. Using Betti number fallback.')
        use_ripser = False

    if use_ripser:
        # Run persistent homology on observed RDM
        result_ph = ripser(rdm, maxdim=1, distance_matrix=True)
        dgm_h1 = result_ph['dgms'][1]  # H1 diagram: (birth, death) pairs

        if len(dgm_h1) == 0:
            return {
                'method': 'ripser_random_sphere',
                'h1_detected': False,
                'max_lifetime': 0.0,
                'n_h1_features': 0,
                'p_value': 1.0,
                'srm_k': srm_k,
            }

        # Filter out infinite death values
        finite_mask = np.isfinite(dgm_h1[:, 1])
        dgm_h1_finite = dgm_h1[finite_mask]

        if len(dgm_h1_finite) == 0:
            return {
                'method': 'ripser_random_sphere',
                'h1_detected': True,
                'max_lifetime': float('inf'),
                'n_h1_features': len(dgm_h1),
                'p_value': 0.0,
                'srm_k': srm_k,
            }

        lifetimes = dgm_h1_finite[:, 1] - dgm_h1_finite[:, 0]
        max_lifetime = float(np.max(lifetimes))
        n_features = len(lifetimes)

        # Null model: random unit vectors on S^{k-1}
        # Generate 8 random points uniformly on the unit hypersphere in R^k,
        # compute correlation distance RDM, run ripser, record max H1 lifetime.
        n_points = rdm.shape[0]  # 8
        null_lifetimes = np.zeros(n_perm)

        for i in range(n_perm):
            # Random unit vectors in R^k (uniform on S^{k-1})
            random_patterns = rng.standard_normal((n_points, srm_k))
            norms = np.linalg.norm(random_patterns, axis=1, keepdims=True)
            norms = np.where(norms < 1e-10, 1.0, norms)
            random_patterns = random_patterns / norms

            # Correlation distance RDM
            null_rdm = squareform(pdist(random_patterns, metric='correlation'))

            try:
                res_null = ripser(null_rdm, maxdim=1, distance_matrix=True)
                dgm_null = res_null['dgms'][1]
                finite_null = dgm_null[np.isfinite(dgm_null[:, 1])]
                if len(finite_null) > 0:
                    null_lifetimes[i] = np.max(finite_null[:, 1] - finite_null[:, 0])
            except Exception:
                null_lifetimes[i] = 0.0

        p_value = float(np.mean(null_lifetimes >= max_lifetime))

        return {
            'method': 'ripser_random_sphere',
            'h1_detected': True,
            'max_lifetime': max_lifetime,
            'n_h1_features': n_features,
            'p_value': p_value,
            'null_mean': float(np.mean(null_lifetimes)),
            'null_std': float(np.std(null_lifetimes)),
            'all_lifetimes': [float(l) for l in lifetimes],
            'h1_diagram': dgm_h1_finite.tolist(),
            'srm_k': srm_k,
        }
    else:
        # Betti number fallback: check if any H1 feature exists
        n = rdm.shape[0]
        triu = squareform(rdm)
        sorted_dists = np.sort(triu)

        h1_found = False
        for threshold in sorted_dists:
            adj = (rdm <= threshold) & (rdm > 0)
            n_edges = adj.sum() // 2
            if n_edges > n - 1:
                h1_found = True
                break

        return {
            'method': 'betti_fallback',
            'h1_detected': h1_found,
            'max_lifetime': None,
            'n_h1_features': None,
            'p_value': None,
            'srm_k': srm_k,
        }


def plot_persistence(ph_data, output_path):
    """
    Persistence diagrams for all 4 ROIs.
    Top row: persistence diagram (birth vs death).
    Bottom row: barcode (lifetime bars).
    """
    fig, axes = plt.subplots(2, 4, figsize=(18, 8))

    for col, roi in enumerate(ALL_ROIS):
        ax_diag = axes[0, col]
        ax_bar = axes[1, col]

        if roi not in ph_data or ph_data[roi]['method'] not in ('ripser', 'ripser_random_sphere'):
            ax_diag.text(0.5, 0.5, 'No ripser data', ha='center', va='center',
                         transform=ax_diag.transAxes, fontsize=10)
            ax_bar.text(0.5, 0.5, 'No ripser data', ha='center', va='center',
                        transform=ax_bar.transAxes, fontsize=10)
            ax_diag.set_title(roi, fontsize=12, fontweight='bold')
            continue

        data = ph_data[roi]
        h1_diag = np.array(data.get('h1_diagram', []))
        p_val = data['p_value']
        max_lt = data['max_lifetime']

        # Persistence diagram
        if len(h1_diag) > 0:
            ax_diag.scatter(h1_diag[:, 0], h1_diag[:, 1], c='#e74c3c', s=60,
                           edgecolors='k', linewidths=0.5, zorder=3, label='H1')
            lim_max = max(h1_diag.max() * 1.1, 0.5)
            ax_diag.plot([0, lim_max], [0, lim_max], 'k--', alpha=0.3)
            ax_diag.set_xlim(-0.02, lim_max)
            ax_diag.set_ylim(-0.02, lim_max)
        else:
            ax_diag.text(0.5, 0.5, 'No H1 features', ha='center', va='center',
                         transform=ax_diag.transAxes)

        sig_str = f'p={p_val:.3f}' if p_val is not None else 'N/A'
        color_title = '#e74c3c' if (p_val is not None and p_val < 0.05) else 'black'
        ax_diag.set_title(f'{roi} ({sig_str})', fontsize=12, fontweight='bold',
                          color=color_title)
        ax_diag.set_xlabel('Birth')
        if col == 0:
            ax_diag.set_ylabel('Death')

        # Barcode
        lifetimes = data.get('all_lifetimes', [])
        if lifetimes:
            sorted_lt = sorted(lifetimes, reverse=True)
            for i, lt in enumerate(sorted_lt):
                color = '#e74c3c' if lt == max_lt else '#3498db'
                ax_bar.barh(i, lt, color=color, edgecolor='k', linewidth=0.3, height=0.6)
            ax_bar.set_xlabel('Lifetime')
            if col == 0:
                ax_bar.set_ylabel('H1 features')
            ax_bar.invert_yaxis()
        else:
            ax_bar.text(0.5, 0.5, 'No lifetimes', ha='center', va='center',
                        transform=ax_bar.transAxes)

        # Highlight focus ROIs
        if roi in FOCUS_ROIS:
            ax_diag.patch.set_facecolor('#fff9c4')
            ax_diag.patch.set_alpha(0.3)
            ax_bar.patch.set_facecolor('#fff9c4')
            ax_bar.patch.set_alpha(0.3)

    axes[0, 0].legend(fontsize=8)
    fig.suptitle('Analysis 3: Persistent Homology (H1 cycle detection, SRM, HC mean)\n'
                 'Null: random unit vectors on S$^{k-1}$ | Red bar = max lifetime',
                 fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Analysis 4: Higher-D MDS + PCA 2D Projection
# ============================================================================

def higher_d_mds_analysis(rdm, target_dims=(3, 4), n_init=10, random_state=42):
    """
    Perform MDS in 3D and 4D, then PCA-project to best 2D plane.

    Returns:
        results: dict per dimension with stress, circular order rho, Shepard R2
    """
    results = {}

    for n_dim in target_dims:
        mds = MDS(n_components=n_dim, metric=True, n_init=n_init,
                  max_iter=500, random_state=random_state,
                  dissimilarity='precomputed')
        coords = mds.fit_transform(rdm)
        stress = normalized_stress(rdm, coords)

        # Shepard R2 in this dimensionality
        orig_flat = squareform(rdm)
        mds_flat = pdist(coords, metric='euclidean')
        ss_res = np.sum((orig_flat - mds_flat) ** 2)
        ss_tot = np.sum((orig_flat - np.mean(orig_flat)) ** 2)
        shepard_r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

        # PCA to best 2D plane
        pca = PCA(n_components=2)
        coords_2d = pca.fit_transform(coords)

        # Circular order test on PCA 2D
        rho, p = circular_order_correlation(coords_2d)

        results[n_dim] = {
            'stress': float(stress),
            'shepard_r2': float(shepard_r2),
            'circular_rho': float(rho),
            'circular_p': float(p),
            'pca_variance_explained': [float(v) for v in pca.explained_variance_ratio_],
            'coords_2d': coords_2d,
            'coords_full': coords,
        }

    return results


def plot_higher_d_mds(hd_data, output_path):
    """
    For each ROI: 2D MDS vs 3D->PCA2D vs 4D->PCA2D embeddings.
    4 ROIs x 3 columns.
    """
    fig, axes = plt.subplots(4, 3, figsize=(14, 18))
    col_labels = ['2D MDS (direct)', '3D MDS -> PCA 2D', '4D MDS -> PCA 2D']

    for row, roi in enumerate(ALL_ROIS):
        if roi not in hd_data:
            for col in range(3):
                axes[row, col].text(0.5, 0.5, 'No data', ha='center', va='center',
                                     transform=axes[row, col].transAxes)
            continue

        for col, (dim_label, dim_key) in enumerate(
                [('2d', 2), ('3d', 3), ('4d', 4)]):
            ax = axes[row, col]

            if dim_key not in hd_data[roi]:
                ax.text(0.5, 0.5, 'N/A', ha='center', va='center',
                        transform=ax.transAxes)
                continue

            info = hd_data[roi][dim_key]
            coords = info['coords_2d']
            rho = info['circular_rho']
            stress = info['stress']

            # Plot points with color + connecting lines
            order = list(range(8)) + [0]
            ax.plot(coords[order, 0], coords[order, 1], 'k-', alpha=0.3, linewidth=0.8)
            for i in range(8):
                ax.scatter(coords[i, 0], coords[i, 1], c=[COLOR_RGBS[i]], s=80,
                          edgecolors='k', linewidths=0.5, zorder=3)
                ax.annotate(COLOR_NAMES[i], (coords[i, 0], coords[i, 1]),
                           textcoords='offset points', xytext=(5, 5), fontsize=6,
                           alpha=0.7)

            ax.set_aspect('equal')
            ax.set_xticks([])
            ax.set_yticks([])

            rho_color = '#2ecc71' if abs(rho) > 0.7 else '#e74c3c'
            stress_color = '#2ecc71' if stress < 0.10 else '#e74c3c'
            ax.set_xlabel(f'rho={rho:.3f}', fontsize=9, color=rho_color, fontweight='bold')

            if row == 0:
                ax.set_title(col_labels[col], fontsize=10)
            if col == 0:
                ax.set_ylabel(roi, fontsize=12, fontweight='bold')

            # Stress annotation
            ax.text(0.02, 0.98, f'stress={stress:.3f}', transform=ax.transAxes,
                    fontsize=8, va='top', color=stress_color)

            # Highlight focus ROIs
            if roi in FOCUS_ROIS:
                ax.patch.set_facecolor('#fff9c4')
                ax.patch.set_alpha(0.3)

    fig.suptitle('Analysis 4: Higher-D MDS + PCA 2D Projection (SRM, HC mean)\n'
                 'Green = pass threshold', fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Analysis 5: Isomap vs MDS
# ============================================================================

def isomap_vs_mds(rdm, patterns, n_neighbors=3, random_state=42):
    """
    Compare Isomap and MDS 2D embeddings.

    Args:
        rdm: (8, 8) RDM for MDS
        patterns: (8, n_features) mean patterns for Isomap

    Returns:
        results: dict with both embeddings and circular order stats
    """
    # MDS
    mds = MDS(n_components=2, metric=True, n_init=10, max_iter=500,
              random_state=random_state, dissimilarity='precomputed')
    coords_mds = mds.fit_transform(rdm)
    rho_mds, p_mds = circular_order_correlation(coords_mds)
    stress_mds = normalized_stress(rdm, coords_mds)

    # Isomap (try n_neighbors=3, fallback to 4)
    for nn in [n_neighbors, n_neighbors + 1, n_neighbors + 2]:
        try:
            iso = Isomap(n_neighbors=nn, n_components=2)
            coords_iso = iso.fit_transform(patterns)
            rho_iso, p_iso = circular_order_correlation(coords_iso)
            break
        except Exception as e:
            if nn == n_neighbors + 2:
                # All failed
                return {
                    'mds': {'coords': coords_mds, 'rho': float(rho_mds),
                            'p': float(p_mds), 'stress': float(stress_mds)},
                    'isomap': {'coords': None, 'rho': None, 'p': None,
                               'n_neighbors': None, 'error': str(e)},
                    'isomap_better': None,
                }
            continue

    return {
        'mds': {'coords': coords_mds, 'rho': float(rho_mds),
                'p': float(p_mds), 'stress': float(stress_mds)},
        'isomap': {'coords': coords_iso, 'rho': float(rho_iso),
                   'p': float(p_iso), 'n_neighbors': nn},
        'isomap_better': abs(rho_iso) > abs(rho_mds),
    }


def plot_isomap_vs_mds(iso_data, output_path):
    """
    Side-by-side MDS vs Isomap for each ROI.
    4 ROIs x 2 columns (MDS, Isomap).
    """
    fig, axes = plt.subplots(4, 2, figsize=(10, 18))

    for row, roi in enumerate(ALL_ROIS):
        if roi not in iso_data:
            for col in range(2):
                axes[row, col].text(0.5, 0.5, 'No data', ha='center', va='center',
                                     transform=axes[row, col].transAxes)
            continue

        data = iso_data[roi]

        for col, (method, key) in enumerate([('MDS', 'mds'), ('Isomap', 'isomap')]):
            ax = axes[row, col]
            info = data[key]
            coords = info.get('coords')

            if coords is None:
                ax.text(0.5, 0.5, f'Failed: {info.get("error", "?")}',
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=8, style='italic')
                ax.set_title(f'{method}', fontsize=10)
                if col == 0:
                    ax.set_ylabel(roi, fontsize=12, fontweight='bold')
                continue

            rho = info['rho']

            # Plot
            order = list(range(8)) + [0]
            ax.plot(coords[order, 0], coords[order, 1], 'k-', alpha=0.3, linewidth=0.8)
            for i in range(8):
                ax.scatter(coords[i, 0], coords[i, 1], c=[COLOR_RGBS[i]], s=80,
                          edgecolors='k', linewidths=0.5, zorder=3)
                ax.annotate(COLOR_NAMES[i], (coords[i, 0], coords[i, 1]),
                           textcoords='offset points', xytext=(5, 5), fontsize=6,
                           alpha=0.7)

            ax.set_aspect('equal')
            ax.set_xticks([])
            ax.set_yticks([])

            rho_color = '#2ecc71' if abs(rho) > 0.7 else '#e74c3c'
            rho_str = f'rho={rho:.3f}' if rho is not None else 'N/A'

            if row == 0:
                ax.set_title(method, fontsize=11, fontweight='bold')
            if col == 0:
                ax.set_ylabel(roi, fontsize=12, fontweight='bold')

            ax.text(0.02, 0.98, rho_str, transform=ax.transAxes, fontsize=9,
                    va='top', color=rho_color, fontweight='bold')

            # Winner badge
            if data['isomap_better'] is not None:
                is_winner = (key == 'isomap' and data['isomap_better']) or \
                            (key == 'mds' and not data['isomap_better'])
                if is_winner:
                    ax.text(0.98, 0.98, 'BETTER', transform=ax.transAxes,
                            fontsize=8, va='top', ha='right', color='white',
                            bbox=dict(boxstyle='round,pad=0.2',
                                     facecolor='#2ecc71', alpha=0.8))

            if roi in FOCUS_ROIS:
                ax.patch.set_facecolor('#fff9c4')
                ax.patch.set_alpha(0.3)

    fig.suptitle('Analysis 5: Isomap vs MDS (SRM, HC mean)\n'
                 'Isomap uses geodesic distances (nonlinear manifold)', fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Analysis 6: Per-Subject V1/V2 Analysis
# ============================================================================

def per_subject_analysis(roi, alignment='srm'):
    """
    Compute individual-level metrics for V1 or V2.

    Returns:
        subjects_data: list of dicts per subject
    """
    # Load all individual RDMs
    rdms = {}
    patterns = {}
    for subj in ALL_SUBJECTS:
        try:
            amp = load_amplitudes(subj, roi, alignment)
            mean_pat = amp.mean(axis=0)  # (8, n_features)
            rdm = compute_rdm(mean_pat)
            rdms[subj] = rdm
            patterns[subj] = mean_pat
        except FileNotFoundError:
            print(f'    WARNING: sub-{subj} {roi} {alignment} not found')

    if not rdms:
        return []

    # HC group mean RDM (LOO for ISC)
    hc_rdms = [rdms[s] for s in HC_SUBJECTS if s in rdms]
    hc_mean = np.mean(hc_rdms, axis=0) if hc_rdms else None

    # CIELab reference
    rdm_cielab = cielab_rdm('ab')

    subjects_data = []
    for subj in ALL_SUBJECTS:
        if subj not in rdms:
            continue

        rdm_subj = rdms[subj]
        group = 'HC' if subj in HC_SUBJECTS else 'CVD'

        # 1. Circularity via MDS
        circularity, mds_stress, embedding = compute_circularity_mds(rdm_subj)

        # 2. Circular order correlation
        if embedding is not None and embedding.shape[1] == 2:
            rho, p = circular_order_correlation(embedding)
        else:
            rho, p = np.nan, np.nan

        # 3. ISC (leave-one-out for HC, vs full HC mean for CVD)
        if group == 'HC':
            others = [rdms[s] for s in HC_SUBJECTS if s in rdms and s != subj]
            if others:
                loo_mean = np.mean(others, axis=0)
                isc = compute_geometric_consistency_isc(rdm_subj, loo_mean)
            else:
                isc = np.nan
        else:
            isc = compute_geometric_consistency_isc(rdm_subj, hc_mean) if hc_mean is not None else np.nan

        # 4. CIELab Mantel r (no permutation — too slow per-subject)
        triu_idx = np.triu_indices(8, k=1)
        vec_neural = rdm_subj[triu_idx]
        vec_cielab = rdm_cielab[triu_idx]
        r_cielab, _ = spearmanr(vec_neural, vec_cielab)

        # 5. Equidistant Mantel r for comparison
        rdm_equi = ideal_circular_rdm()
        vec_equi = rdm_equi[triu_idx]
        r_equi, _ = spearmanr(vec_neural, vec_equi)

        subjects_data.append({
            'subject': f'sub-{subj}',
            'group': group,
            'circularity': float(circularity) if circularity is not None else None,
            'circular_rho': float(rho),
            'circular_p': float(p),
            'isc': float(isc) if not np.isnan(isc) else None,
            'cielab_mantel_r': float(r_cielab),
            'equi_mantel_r': float(r_equi),
            'cielab_advantage': float(r_cielab - r_equi),
        })

    return subjects_data


def plot_per_subject(subject_data_all, output_path):
    """
    Dot plots for V1 and V2: 4 metrics x 2 ROIs.
    HC = blue, CVD = red.
    """
    metrics = [
        ('circularity', 'Circularity Index'),
        ('isc', 'ISC (vs HC mean)'),
        ('cielab_mantel_r', 'CIELab Mantel r'),
        ('cielab_advantage', 'CIELab advantage\n(r_cielab - r_equi)'),
    ]

    fig, axes = plt.subplots(len(metrics), 2, figsize=(12, 14))

    for col, roi in enumerate(FOCUS_ROIS):
        if roi not in subject_data_all:
            for row in range(len(metrics)):
                axes[row, col].text(0.5, 0.5, 'No data', ha='center', va='center',
                                     transform=axes[row, col].transAxes)
            continue

        data = subject_data_all[roi]

        for row, (metric_key, metric_label) in enumerate(metrics):
            ax = axes[row, col]

            hc_vals = []
            cvd_vals = []
            hc_labels = []
            cvd_labels = []

            for d in data:
                val = d.get(metric_key)
                if val is None:
                    continue
                if d['group'] == 'HC':
                    hc_vals.append(val)
                    hc_labels.append(d['subject'])
                else:
                    cvd_vals.append(val)
                    cvd_labels.append(d['subject'])

            # Plot HC
            if hc_vals:
                x_hc = np.zeros(len(hc_vals))
                jitter = np.random.default_rng(42).uniform(-0.15, 0.15, len(hc_vals))
                ax.scatter(x_hc + jitter, hc_vals, c='#3498db', s=60,
                          edgecolors='k', linewidths=0.5, label='HC', zorder=3)
                for lbl, j, v in zip(hc_labels, jitter, hc_vals):
                    ax.annotate(lbl.replace('sub-', ''), (j, v),
                               textcoords='offset points', xytext=(8, 0),
                               fontsize=7, alpha=0.6)

            # Plot CVD
            if cvd_vals:
                x_cvd = np.ones(len(cvd_vals))
                jitter_cvd = np.random.default_rng(43).uniform(-0.15, 0.15, len(cvd_vals))
                ax.scatter(x_cvd + jitter_cvd, cvd_vals, c='#e74c3c', s=80,
                          edgecolors='k', linewidths=0.5, label='CVD', zorder=3,
                          marker='D')
                for lbl, j, v in zip(cvd_labels, jitter_cvd, cvd_vals):
                    ax.annotate(lbl.replace('sub-', ''), (1 + j, v),
                               textcoords='offset points', xytext=(8, 0),
                               fontsize=7, alpha=0.6, color='#e74c3c')

            # Group means
            if hc_vals:
                ax.axhline(np.mean(hc_vals), color='#3498db', linestyle='--', alpha=0.4)
            if cvd_vals:
                ax.axhline(np.mean(cvd_vals), color='#e74c3c', linestyle='--', alpha=0.4)

            # Reference lines
            if metric_key == 'cielab_advantage':
                ax.axhline(0, color='k', linewidth=0.5)

            ax.set_xticks([0, 1])
            ax.set_xticklabels(['HC', 'CVD'])
            ax.set_xlim(-0.5, 1.5)

            if col == 0:
                ax.set_ylabel(metric_label, fontsize=10)
            if row == 0:
                ax.set_title(roi, fontsize=12, fontweight='bold')
            if row == 0 and col == 1:
                ax.legend(fontsize=8, loc='upper right')

    fig.suptitle('Analysis 6: Per-Subject V1/V2 Diagnostics (SRM)\n'
                 'CIELab advantage > 0 = CIELab model fits better than equidistant',
                 fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Decision Framework
# ============================================================================

def compute_verdict(results_roi):
    """
    Determine verdict for a single ROI based on 4 criteria.

    Q1: CIELab > equidistant?  (Mantel r difference + CIELab p < 0.05 Bonferroni)
    Q2: H1 topology?           (Persistence p < 0.05)
    Q3: Higher-D improvement?  (3D/4D stress < 0.10 OR |rho| > 0.7)
    Q4: Isomap better?         (Isomap |rho| > MDS |rho|)

    Returns:
        verdict: 'structured', 'marginal', or 'unstructured'
        passes: dict of Q1-Q4 booleans
    """
    passes = {}

    # Q1: CIELab > equidistant
    mantel = results_roi.get('mantel_comparison', {})
    r_cielab = mantel.get('CIELab_ab', {}).get('r', -1)
    p_cielab = mantel.get('CIELab_ab', {}).get('p_bonferroni', 1)
    r_equi = mantel.get('equidistant', {}).get('r', -1)
    passes['Q1_cielab_better'] = (r_cielab > r_equi) and (p_cielab < 0.05)

    # Q2: H1 topology
    ph = results_roi.get('persistent_homology', {})
    p_h1 = ph.get('p_value')
    passes['Q2_h1_topology'] = (p_h1 is not None and p_h1 < 0.05)

    # Q3: Higher-D improvement
    hd = results_roi.get('higher_d_mds', {})
    q3 = False
    for dim in [3, 4]:
        if dim in hd:
            if hd[dim]['stress'] < 0.10 or abs(hd[dim]['circular_rho']) > 0.7:
                q3 = True
    passes['Q3_higher_d'] = q3

    # Q4: Isomap better
    iso = results_roi.get('isomap_comparison', {})
    passes['Q4_isomap_better'] = bool(iso.get('isomap_better', False))

    n_pass = sum(passes.values())
    if n_pass >= 2:
        verdict = 'structured'
    elif n_pass == 1:
        verdict = 'marginal'
    else:
        verdict = 'unstructured'

    return verdict, passes


# ============================================================================
# Main
# ============================================================================

def main():
    print('=' * 70)
    print('Phase 1b: Extended V1/V2 Diagnostic')
    print('=' * 70)
    print(f'Data dir: {DATA_DIR}')
    print(f'Output: {RESULTS_DIR}')
    print(f'Alignment: {ALIGNMENT}')
    print(f'Focus ROIs: {FOCUS_ROIS} (all 4 ROIs for comparison)')
    print()

    # ========================================================================
    # Load data for all ROIs
    # ========================================================================
    print('--- Loading data ---')
    hc_mean_rdms = {}
    hc_mean_patterns = {}
    all_rdms = {}  # {roi: {subj: rdm}}

    for roi in ALL_ROIS:
        rdms_hc = []
        patterns_hc = []
        all_rdms[roi] = {}

        for subj in ALL_SUBJECTS:
            try:
                amp = load_amplitudes(subj, roi, ALIGNMENT)
                mean_pat = amp.mean(axis=0)  # (8, n_features)
                rdm = compute_rdm(mean_pat)
                all_rdms[roi][subj] = rdm
                if subj in HC_SUBJECTS:
                    rdms_hc.append(rdm)
                    patterns_hc.append(mean_pat)
            except FileNotFoundError:
                print(f'  WARNING: sub-{subj} {roi} {ALIGNMENT} not found')

        if rdms_hc:
            hc_mean_rdms[roi] = np.mean(rdms_hc, axis=0)
            hc_mean_patterns[roi] = np.mean(patterns_hc, axis=0)
            print(f'  {roi}: {len(rdms_hc)} HC subjects loaded, pattern shape={patterns_hc[0].shape}')
        else:
            print(f'  {roi}: NO HC data!')

    # ========================================================================
    # Analysis 1: Full Stress Curve (1-7D)
    # ========================================================================
    print('\n--- Analysis 1: Full Stress Curve (1-7D) ---')
    stress_data = {}
    for roi in ALL_ROIS:
        if roi in hc_mean_rdms:
            stresses = compute_stress_curve_extended(hc_mean_rdms[roi], max_dims=7)
            stress_data[roi] = stresses
            print(f'  {roi}: stress = {[f"{s:.3f}" for s in stresses]}')
            k = SRM_K[roi]
            print(f'    At SRM k={k}: stress={stresses[k-1]:.4f}')

    plot_stress_curve_7d(stress_data, RESULTS_DIR / 'fig_ext1_stress_curve_7d.png')

    # ========================================================================
    # Analysis 2: CIELab-based Mantel Test
    # ========================================================================
    print('\n--- Analysis 2: CIELab-based Mantel Test ---')
    mantel_data = {}
    for roi in ALL_ROIS:
        if roi in hc_mean_rdms:
            print(f'  {roi}:')
            mantel_data[roi] = cielab_mantel_comparison(hc_mean_rdms[roi])
            for model, res in mantel_data[roi].items():
                sig = '*' if res['p_bonferroni'] < 0.05 else ''
                print(f'    {model:20s}: r={res["r"]:.3f}, p_raw={res["p"]:.4f}, '
                      f'p_bonf={res["p_bonferroni"]:.4f} {sig}')

    plot_cielab_mantel(mantel_data, RESULTS_DIR / 'fig_ext2_cielab_mantel.png')

    # ========================================================================
    # Analysis 3: Persistent Homology
    # ========================================================================
    print('\n--- Analysis 3: Persistent Homology ---')
    ph_data = {}
    for roi in ALL_ROIS:
        if roi in hc_mean_rdms:
            print(f'  {roi}:')
            ph_data[roi] = persistent_homology_test(hc_mean_rdms[roi], srm_k=SRM_K[roi])
            d = ph_data[roi]
            print(f'    Method: {d["method"]}')
            print(f'    H1 detected: {d["h1_detected"]}')
            if d.get('max_lifetime') is not None:
                print(f'    Max lifetime: {d["max_lifetime"]:.4f}')
            if d.get('p_value') is not None:
                print(f'    p-value: {d["p_value"]:.4f}')

    plot_persistence(ph_data, RESULTS_DIR / 'fig_ext3_persistence.png')

    # ========================================================================
    # Analysis 4: Higher-D MDS + PCA 2D
    # ========================================================================
    print('\n--- Analysis 4: Higher-D MDS + PCA 2D ---')
    hd_data = {}
    for roi in ALL_ROIS:
        if roi in hc_mean_rdms:
            # Also compute 2D for direct comparison
            mds_2d = MDS(n_components=2, metric=True, n_init=10, max_iter=500,
                         random_state=42, dissimilarity='precomputed')
            coords_2d = mds_2d.fit_transform(hc_mean_rdms[roi])
            stress_2d = normalized_stress(hc_mean_rdms[roi], coords_2d)
            rho_2d, p_2d = circular_order_correlation(coords_2d)

            results = higher_d_mds_analysis(hc_mean_rdms[roi])
            # Add 2D baseline
            results[2] = {
                'stress': float(stress_2d),
                'shepard_r2': None,
                'circular_rho': float(rho_2d),
                'circular_p': float(p_2d),
                'coords_2d': coords_2d,
            }
            hd_data[roi] = results

            print(f'  {roi}:')
            for dim in [2, 3, 4]:
                r = results[dim]
                print(f'    {dim}D: stress={r["stress"]:.3f}, rho={r["circular_rho"]:.3f}')

    plot_higher_d_mds(hd_data, RESULTS_DIR / 'fig_ext4_higher_d_mds.png')

    # ========================================================================
    # Analysis 5: Isomap vs MDS
    # ========================================================================
    print('\n--- Analysis 5: Isomap vs MDS ---')
    iso_data = {}
    for roi in ALL_ROIS:
        if roi in hc_mean_rdms and roi in hc_mean_patterns:
            iso_data[roi] = isomap_vs_mds(hc_mean_rdms[roi], hc_mean_patterns[roi])
            d = iso_data[roi]
            rho_mds = d['mds']['rho']
            rho_iso = d['isomap']['rho']
            better = d['isomap_better']
            iso_str = f'{rho_iso:.3f}' if rho_iso is not None else 'FAILED'
            print(f'  {roi}: MDS rho={rho_mds:.3f}, Isomap rho={iso_str}, '
                  f'Isomap better={better}')

    plot_isomap_vs_mds(iso_data, RESULTS_DIR / 'fig_ext5_isomap_vs_mds.png')

    # ========================================================================
    # Analysis 6: Per-Subject V1/V2
    # ========================================================================
    print('\n--- Analysis 6: Per-Subject V1/V2 ---')
    subject_data_all = {}
    for roi in FOCUS_ROIS:
        print(f'  {roi}:')
        subject_data_all[roi] = per_subject_analysis(roi, ALIGNMENT)
        for d in subject_data_all[roi]:
            print(f'    {d["subject"]} ({d["group"]}): '
                  f'circ={d["circularity"]:.2f}, ISC={d["isc"]:.3f}, '
                  f'CIELab_r={d["cielab_mantel_r"]:.3f}, '
                  f'adv={d["cielab_advantage"]:+.3f}')

    plot_per_subject(subject_data_all, RESULTS_DIR / 'fig_ext6_per_subject.png')

    # ========================================================================
    # Compile Summary JSON
    # ========================================================================
    print('\n--- Compiling Summary ---')

    summary = {
        'analysis': 'Phase1b_Extended_V1V2_Diagnostic',
        'alignment': ALIGNMENT,
        'data_dir': str(DATA_DIR),
        'bonferroni_alpha': BONFERRONI_ALPHA,
        'n_tests_bonferroni': 16,
        'srm_k': SRM_K,
    }

    # Stress curves
    summary['stress_curves'] = {}
    for roi, stresses in stress_data.items():
        summary['stress_curves'][roi] = {
            f'{d+1}D': stresses[d] for d in range(len(stresses))
        }

    # Mantel comparisons
    summary['mantel_comparison'] = {}
    for roi, models in mantel_data.items():
        summary['mantel_comparison'][roi] = {
            model: {k: v for k, v in res.items() if k != 'null_dist'}
            for model, res in models.items()
        }

    # Persistent homology
    summary['persistent_homology'] = {}
    for roi, data in ph_data.items():
        ph_clean = {k: v for k, v in data.items()
                    if k not in ('h1_diagram',)}
        summary['persistent_homology'][roi] = ph_clean

    # Higher-D MDS
    summary['higher_d_mds'] = {}
    for roi, dims in hd_data.items():
        summary['higher_d_mds'][roi] = {}
        for dim, info in dims.items():
            summary['higher_d_mds'][roi][f'{dim}D'] = {
                'stress': info['stress'],
                'circular_rho': info['circular_rho'],
                'circular_p': info.get('circular_p'),
                'shepard_r2': info.get('shepard_r2'),
                'pca_variance_explained': info.get('pca_variance_explained'),
            }

    # Isomap vs MDS
    summary['isomap_comparison'] = {}
    for roi, data in iso_data.items():
        summary['isomap_comparison'][roi] = {
            'mds_rho': data['mds']['rho'],
            'mds_stress': data['mds']['stress'],
            'isomap_rho': data['isomap']['rho'],
            'isomap_n_neighbors': data['isomap'].get('n_neighbors'),
            'isomap_better': data['isomap_better'],
        }

    # Per-subject
    summary['per_subject'] = {}
    for roi, data in subject_data_all.items():
        summary['per_subject'][roi] = data

    # ========================================================================
    # Decision Framework
    # ========================================================================
    print('\n--- Decision Framework ---')
    decisions = {}

    for roi in ALL_ROIS:
        roi_results = {
            'mantel_comparison': mantel_data.get(roi, {}),
            'persistent_homology': ph_data.get(roi, {}),
            'higher_d_mds': hd_data.get(roi, {}),
            'isomap_comparison': iso_data.get(roi, {}),
        }
        verdict, passes = compute_verdict(roi_results)
        decisions[roi] = {
            'verdict': verdict,
            'criteria': {k: bool(v) for k, v in passes.items()},
            'n_pass': sum(passes.values()),
        }
        n = sum(passes.values())
        print(f'  {roi}: {verdict.upper()} ({n}/4 pass)')
        for q, v in passes.items():
            mark = 'PASS' if v else 'FAIL'
            print(f'    {q}: {mark}')

    summary['decisions'] = decisions

    # Save
    json_path = RESULTS_DIR / 'extended_v1v2_summary.json'
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f'\n  Saved: {json_path}')

    # ========================================================================
    # Final Summary Table
    # ========================================================================
    print('\n' + '=' * 70)
    print('PHASE 1b SUMMARY')
    print('=' * 70)
    print(f'{"ROI":<6} {"Verdict":<14} {"Q1:CIELab":<12} {"Q2:H1":<10} '
          f'{"Q3:HighD":<10} {"Q4:Isomap":<10}')
    print('-' * 62)
    for roi in ALL_ROIS:
        d = decisions[roi]
        v = d['verdict'].upper()
        c = d['criteria']
        q1 = 'PASS' if c.get('Q1_cielab_better') else 'FAIL'
        q2 = 'PASS' if c.get('Q2_h1_topology') else 'FAIL'
        q3 = 'PASS' if c.get('Q3_higher_d') else 'FAIL'
        q4 = 'PASS' if c.get('Q4_isomap_better') else 'FAIL'
        marker = ' <--' if roi in FOCUS_ROIS else ''
        print(f'{roi:<6} {v:<14} {q1:<12} {q2:<10} {q3:<10} {q4:<10}{marker}')

    print()
    print('Key results:')
    for roi in FOCUS_ROIS:
        m = mantel_data.get(roi, {})
        r_equi = m.get('equidistant', {}).get('r', '?')
        r_cielab = m.get('CIELab_ab', {}).get('r', '?')
        p_cielab = m.get('CIELab_ab', {}).get('p_bonferroni', '?')
        if isinstance(r_equi, float) and isinstance(r_cielab, float):
            print(f'  {roi}: equidist r={r_equi:.3f}, CIELab r={r_cielab:.3f} '
                  f'(p_bonf={p_cielab:.4f}), diff={r_cielab - r_equi:+.3f}')

    print('\n' + '=' * 70)
    print('Phase 1b complete. Check results/mds_diagnostic/ for figures and JSON.')
    print('=' * 70)


if __name__ == '__main__':
    main()
