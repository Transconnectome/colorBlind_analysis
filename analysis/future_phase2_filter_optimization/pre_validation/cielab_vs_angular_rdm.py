#!/usr/bin/env python3
"""
CIELab vs Angular RDM Diagnostic

Determines whether neural RDMs in V1/V2 reflect:
  (a) equidistant angular structure (45° spacing assumption), or
  (b) perceptual CIELab structure (cone-opponent, non-uniform spacing)

This is critical for filter pre-validation: if neural RDMs align with CIELab
rather than equidistant geometry, Phase 1's Mantel "failures" in V1/V2 were
false negatives caused by an inappropriate reference model.

6 analyses:
  1. Stress curve (1-7D) — find dimensionality where stress < 0.10
  2. Reference RDM comparison (Mantel) — angular vs CIELab(a*b*) vs a*-only vs b*-only
  3. Persistent homology — H1 (loop) detection
  4. Higher-D MDS + PCA best 2D plane
  5. Isomap vs MDS comparison
  6. Per-subject analysis (HC vs CVD)

Usage (local):
    conda activate srm
    cd analysis/future_phase2_filter_optimization/pre_validation
    python cielab_vs_angular_rdm.py

Output:
    results/cielab_diagnostic/
"""

import sys
import json
import warnings
import socket
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
# CONFIG
# ============================================================================

SCRIPT_DIR = Path(__file__).resolve().parent

# Import CIELab coordinates from utils
sys.path.insert(0, str(SCRIPT_DIR.parents[1] / 'utils'))
from utils_color_decoding import COLOR_LAB

HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS

ROIS = ['V1', 'V2', 'V3', 'hV4']
ROI_DIRS = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}
SRM_K = {'V1': 4, 'V2': 4, 'V3': 3, 'hV4': 3}

ALIGNMENTS = ['raw', 'procrustes', 'srm']
HUE_ANGLES = np.array([i * 45 for i in range(8)])
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']

COLOR_RGBS = [
    (0.85, 0.25, 0.30), (0.90, 0.55, 0.20), (0.70, 0.55, 0.15),
    (0.15, 0.70, 0.30), (0.20, 0.72, 0.65), (0.30, 0.55, 0.80),
    (0.40, 0.30, 0.75), (0.70, 0.30, 0.65),
]

# Data path
if socket.gethostname().startswith('node'):
    DATA_DIR = Path("/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010")
else:
    DATA_DIR = Path(__file__).resolve().parents[2] / \
        'phase1_preprocess_decoding' / 'results' / 'full_dataset_C010'

# Output
RESULTS_DIR = SCRIPT_DIR / 'results' / 'cielab_diagnostic'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Bonferroni: 4 reference models × 4 ROIs = 16 tests
BONFERRONI_ALPHA = 0.05 / 16


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


# ============================================================================
# Reference RDMs
# ============================================================================

def angular_rdm():
    """Equidistant circular RDM: min(|θi-θj|, 360-|θi-θj|) / 180."""
    n = len(HUE_ANGLES)
    rdm = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            diff = abs(HUE_ANGLES[i] - HUE_ANGLES[j])
            rdm[i, j] = min(diff, 360 - diff)
    return rdm / rdm.max()


def cielab_rdm(metric='ab'):
    """
    Perceptual RDM from CIELab coordinates.

    Args:
        metric: 'ab' (full a*,b*), 'a_only' (L-M axis), 'b_only' (S-LM axis)
    """
    colors = [f'color_{i}' for i in range(1, 9)]
    if metric == 'ab':
        coords = np.array([[COLOR_LAB[c][1], COLOR_LAB[c][2]] for c in colors])
    elif metric == 'a_only':
        coords = np.array([[COLOR_LAB[c][1]] for c in colors])
    elif metric == 'b_only':
        coords = np.array([[COLOR_LAB[c][2]] for c in colors])
    else:
        raise ValueError(f'Unknown metric: {metric}')
    rdm = squareform(pdist(coords, metric='euclidean'))
    if rdm.max() > 0:
        rdm = rdm / rdm.max()
    return rdm


# ============================================================================
# Core Functions
# ============================================================================

def normalized_stress(rdm, coords):
    """Kruskal's normalized stress-1."""
    dists_orig = squareform(rdm)
    dists_mds = pdist(coords, metric='euclidean')
    return np.sqrt(np.sum((dists_orig - dists_mds) ** 2) / np.sum(dists_orig ** 2))


def circular_order_correlation(coords_2d):
    """Spearman rank correlation between MDS angular order and true hue order."""
    angles_deg = np.rad2deg(np.arctan2(coords_2d[:, 1], coords_2d[:, 0])) % 360
    true_ranks = np.argsort(np.argsort(HUE_ANGLES))
    rho1, p1 = spearmanr(true_ranks, np.argsort(np.argsort(angles_deg)))
    rho2, p2 = spearmanr(true_ranks, np.argsort(np.argsort(360 - angles_deg)))
    return (rho1, p1) if abs(rho1) >= abs(rho2) else (rho2, p2)


def mantel_test(rdm_neural, rdm_ref, n_permutations=10000, random_state=42):
    """Mantel test: Spearman correlation between two RDMs, permutation p-value."""
    rng = np.random.default_rng(random_state)
    triu_idx = np.triu_indices(rdm_neural.shape[0], k=1)
    vec_neural = rdm_neural[triu_idx]
    vec_ref = rdm_ref[triu_idx]
    r_obs, _ = spearmanr(vec_neural, vec_ref)

    n = rdm_neural.shape[0]
    null_dist = np.zeros(n_permutations)
    for i in range(n_permutations):
        perm = rng.permutation(n)
        rdm_perm = rdm_neural[np.ix_(perm, perm)]
        null_dist[i], _ = spearmanr(rdm_perm[triu_idx], vec_ref)
    p_value = np.mean(null_dist >= r_obs)
    return r_obs, p_value, null_dist


# ============================================================================
# Analysis 1: Full Stress Curve (1-7D)
# ============================================================================

def compute_stress_curve(rdm, max_dims=7, n_init=10, random_state=42):
    stresses = []
    for n_dim in range(1, max_dims + 1):
        mds = MDS(n_components=n_dim, metric=True, n_init=n_init,
                  max_iter=500, random_state=random_state,
                  dissimilarity='precomputed', normalized_stress=False)
        coords = mds.fit_transform(rdm)
        stresses.append(float(normalized_stress(rdm, coords)))
    return stresses


def plot_stress_curve(stress_data, output_path):
    fig, axes = plt.subplots(1, 4, figsize=(18, 4.5), sharey=True)
    colors_align = {'raw': '#e74c3c', 'procrustes': '#3498db', 'srm': '#2ecc71'}

    for col, roi in enumerate(ROIS):
        ax = axes[col]
        dims = list(range(1, 8))
        for align in ALIGNMENTS:
            key = (roi, align)
            if key in stress_data:
                ax.plot(dims, stress_data[key], 'o-', color=colors_align[align],
                        label=align, linewidth=1.5, markersize=5)
        ax.axhline(y=0.10, color='gray', linestyle='--', alpha=0.5, label='stress=0.10')
        ax.axvline(x=SRM_K[roi], color='orange', linestyle=':', alpha=0.6,
                   label=f'SRM k={SRM_K[roi]}')
        ax.set_xlabel('Dimensions')
        ax.set_title(f'{roi} (k={SRM_K[roi]})')
        ax.set_xticks(dims)
        ax.set_ylim(-0.02, 0.40)
        if col == 0:
            ax.set_ylabel('Normalized Stress')
    axes[0].legend(fontsize=7, loc='upper right')
    fig.suptitle('Stress Curve (1-7D, HC group mean RDM)', fontsize=13)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Analysis 2: Reference RDM Comparison (Mantel)
# ============================================================================

def reference_mantel_comparison(rdm_neural, n_permutations=10000, random_state=42):
    """Compare neural RDM against 4 reference models."""
    models = {
        'angular': angular_rdm(),
        'cielab_ab': cielab_rdm('ab'),
        'cielab_a_only': cielab_rdm('a_only'),
        'cielab_b_only': cielab_rdm('b_only'),
    }
    results = {}
    for name, rdm_ref in models.items():
        r_obs, p_val, null_dist = mantel_test(
            rdm_neural, rdm_ref, n_permutations=n_permutations,
            random_state=random_state)
        results[name] = {'r': float(r_obs), 'p': float(p_val), 'null_dist': null_dist}
    return results


def plot_mantel_comparison(mantel_data, output_path):
    """4 rows (ROI) × 4 cols (reference model), SRM alignment."""
    model_names = ['angular', 'cielab_ab', 'cielab_a_only', 'cielab_b_only']
    model_labels = ['Angular\n(equidistant)', 'Perceptual\nCIELab (a*,b*)',
                    'a*-only\n(L-M axis)', 'b*-only\n(S-LM axis)']

    fig, axes = plt.subplots(4, 4, figsize=(16, 14))
    for row, roi in enumerate(ROIS):
        for col, (model, label) in enumerate(zip(model_names, model_labels)):
            ax = axes[row, col]
            key = (roi, 'srm', model)
            if key in mantel_data:
                d = mantel_data[key]
                ax.hist(d['null_dist'], bins=50, color='lightblue',
                        edgecolor='gray', alpha=0.7)
                color = 'red' if d['p'] < BONFERRONI_ALPHA else (
                    'orange' if d['p'] < 0.05 else 'gray')
                ax.axvline(d['r'], color=color, linewidth=2)
                sig = '***' if d['p'] < BONFERRONI_ALPHA else (
                    '*' if d['p'] < 0.05 else 'ns')
                ax.text(0.05, 0.92, f'r={d["r"]:.3f}\np={d["p"]:.4f} {sig}',
                        transform=ax.transAxes, fontsize=8, va='top',
                        fontweight='bold' if d['p'] < 0.05 else 'normal')
            if row == 0:
                ax.set_title(label, fontsize=9)
            if col == 0:
                ax.set_ylabel(roi, fontsize=10, fontweight='bold')
            if row == 3:
                ax.set_xlabel('Spearman r', fontsize=8)
    fig.suptitle(f'Neural RDM vs Reference Models (SRM, HC mean)\n'
                 f'Bonferroni α = {BONFERRONI_ALPHA:.4f}', fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Analysis 3: Persistent Homology (H1)
# ============================================================================

def persistent_homology_test(rdm, n_permutations=1000, random_state=42):
    rng = np.random.default_rng(random_state)
    result = {'has_ripser': False, 'max_h1_lifetime': 0.0, 'p_value': 1.0}
    try:
        from ripser import ripser as ripser_fn
        result['has_ripser'] = True
    except ImportError:
        warnings.warn('ripser not installed. Skipping persistent homology.')
        return result

    rips = ripser_fn(rdm, maxdim=1, distance_matrix=True)
    h1 = rips['dgms'][1]
    if len(h1) == 0:
        result['h1_diagram'] = []
        return result

    lifetimes = h1[:, 1] - h1[:, 0]
    finite = np.isfinite(lifetimes)
    lifetimes = lifetimes[finite]
    if len(lifetimes) == 0:
        result['h1_diagram'] = h1.tolist()
        return result

    result['max_h1_lifetime'] = float(np.max(lifetimes))
    result['h1_diagram'] = h1[finite].tolist()

    n = rdm.shape[0]
    null = np.zeros(n_permutations)
    for i in range(n_permutations):
        perm = rng.permutation(n)
        rips_p = ripser_fn(rdm[np.ix_(perm, perm)], maxdim=1, distance_matrix=True)
        h1_p = rips_p['dgms'][1]
        if len(h1_p) > 0:
            lt = h1_p[:, 1] - h1_p[:, 0]
            lt = lt[np.isfinite(lt)]
            null[i] = float(np.max(lt)) if len(lt) > 0 else 0.0
    result['p_value'] = float(np.mean(null >= result['max_h1_lifetime']))
    result['null_lifetimes'] = null
    return result


def plot_persistence(ph_data, output_path):
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for row, roi in enumerate(['V1', 'V2']):
        key = (roi, 'srm')
        # Persistence diagram
        ax = axes[row, 0]
        if key in ph_data and ph_data[key].get('has_ripser'):
            h1 = np.array(ph_data[key]['h1_diagram'])
            if len(h1) > 0:
                ax.scatter(h1[:, 0], h1[:, 1], c='red', s=60, zorder=3)
                lim = max(h1[:, 1].max() * 1.1, 1.0)
                ax.plot([0, lim], [0, lim], 'k--', alpha=0.3)
                ax.set_xlim(-0.05, lim)
                ax.set_ylim(-0.05, lim)
            else:
                ax.text(0.5, 0.5, 'No H1 features', transform=ax.transAxes, ha='center')
        else:
            ax.text(0.5, 0.5, 'ripser not available', transform=ax.transAxes, ha='center')
        ax.set_xlabel('Birth')
        ax.set_ylabel('Death')
        ax.set_title(f'{roi} SRM — Persistence Diagram (H1)')

        # Null distribution
        ax2 = axes[row, 1]
        if key in ph_data and 'null_lifetimes' in ph_data[key]:
            null = ph_data[key]['null_lifetimes']
            obs = ph_data[key]['max_h1_lifetime']
            p = ph_data[key]['p_value']
            ax2.hist(null, bins=40, color='lightblue', edgecolor='gray', alpha=0.7)
            ax2.axvline(obs, color='red' if p < 0.05 else 'gray', linewidth=2,
                       label=f'Observed={obs:.3f}')
            ax2.text(0.05, 0.92, f'p = {p:.4f}', transform=ax2.transAxes, fontsize=10,
                    va='top', fontweight='bold' if p < 0.05 else 'normal')
            ax2.set_xlabel('Max H1 Lifetime')
            ax2.set_ylabel('Count')
            ax2.legend(fontsize=8)
        ax2.set_title(f'{roi} SRM — H1 Permutation Test')
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Analysis 4: Higher-D MDS + PCA 2D
# ============================================================================

def higher_d_mds(rdm, target_dims=(2, 3, 4), random_state=42):
    results = {}
    for n_dim in target_dims:
        mds = MDS(n_components=n_dim, metric=True, n_init=10, max_iter=500,
                  random_state=random_state, dissimilarity='precomputed',
                  normalized_stress=False)
        coords = mds.fit_transform(rdm)
        stress = normalized_stress(rdm, coords)
        pca = PCA(n_components=min(2, n_dim))
        coords_2d = pca.fit_transform(coords) if n_dim > 2 else coords
        rho, p = circular_order_correlation(coords_2d)
        # Shepard R2
        orig = squareform(rdm)
        fitted = pdist(coords, metric='euclidean')
        ss_res = np.sum((orig - fitted) ** 2)
        ss_tot = np.sum((orig - np.mean(orig)) ** 2)
        results[n_dim] = {
            'coords': coords, 'stress': float(stress),
            'pca_2d': coords_2d,
            'pca_var_ratio': pca.explained_variance_ratio_.tolist() if n_dim > 2 else [],
            'circular_rho': float(rho), 'circular_p': float(p),
            'shepard_r2': float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0,
        }
    return results


def plot_higher_d(hd_data, output_path):
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    for row, roi in enumerate(['V1', 'V2']):
        key = (roi, 'srm')
        for col, (label, dim) in enumerate([('2D MDS', 2), ('3D→PCA 2D', 3), ('4D→PCA 2D', 4)]):
            ax = axes[row, col]
            if key in hd_data and dim in hd_data[key]:
                d = hd_data[key][dim]
                c2d = d['pca_2d'] if dim > 2 else d['coords']
                order = list(range(8)) + [0]
                ax.plot(c2d[order, 0], c2d[order, 1], 'k-', alpha=0.3, linewidth=0.8)
                for i in range(8):
                    ax.scatter(c2d[i, 0], c2d[i, 1], c=[COLOR_RGBS[i]], s=100,
                              edgecolors='k', linewidths=0.5, zorder=3)
                    ax.annotate(COLOR_NAMES[i], (c2d[i, 0], c2d[i, 1]),
                               textcoords='offset points', xytext=(6, 6), fontsize=7)
                sig = '*' if d['circular_p'] < 0.05 else 'ns'
                info = f'stress={d["stress"]:.3f}\nρ={d["circular_rho"]:.3f} (p={d["circular_p"]:.3f}) {sig}'
                if dim > 2:
                    vr = d['pca_var_ratio']
                    info += f'\nPCA: {vr[0]:.0%}+{vr[1]:.0%}'
                ax.text(0.03, 0.97, info, transform=ax.transAxes, fontsize=8, va='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            ax.set_aspect('equal')
            ax.set_xticks([])
            ax.set_yticks([])
            if row == 0:
                ax.set_title(label, fontsize=11)
            if col == 0:
                ax.set_ylabel(roi, fontsize=11, fontweight='bold')
    fig.suptitle('Higher-D MDS + PCA Best 2D (SRM, HC mean)', fontsize=13)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Analysis 5: Isomap vs MDS
# ============================================================================

def isomap_vs_mds(patterns, rdm, n_neighbors=3):
    mds = MDS(n_components=2, metric=True, n_init=10, max_iter=500,
              random_state=42, dissimilarity='precomputed', normalized_stress=False)
    mds_c = mds.fit_transform(rdm)
    mds_rho, mds_p = circular_order_correlation(mds_c)

    try:
        iso = Isomap(n_components=2, n_neighbors=n_neighbors)
        iso_c = iso.fit_transform(patterns)
        iso_rho, iso_p = circular_order_correlation(iso_c)
    except Exception:
        try:
            iso = Isomap(n_components=2, n_neighbors=4)
            iso_c = iso.fit_transform(patterns)
            iso_rho, iso_p = circular_order_correlation(iso_c)
        except Exception:
            iso_c = mds_c.copy()
            iso_rho, iso_p = 0.0, 1.0

    return {
        'mds_rho': float(mds_rho), 'mds_p': float(mds_p), 'mds_coords': mds_c,
        'isomap_rho': float(iso_rho), 'isomap_p': float(iso_p), 'isomap_coords': iso_c,
    }


def plot_isomap(iso_data, output_path):
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    for row, roi in enumerate(['V1', 'V2']):
        key = (roi, 'srm')
        for col, (method, ck, rk, pk) in enumerate([
            ('MDS', 'mds_coords', 'mds_rho', 'mds_p'),
            ('Isomap', 'isomap_coords', 'isomap_rho', 'isomap_p'),
        ]):
            ax = axes[row, col]
            if key in iso_data:
                d = iso_data[key]
                c2d = d[ck]
                order = list(range(8)) + [0]
                ax.plot(c2d[order, 0], c2d[order, 1], 'k-', alpha=0.3, linewidth=0.8)
                for i in range(8):
                    ax.scatter(c2d[i, 0], c2d[i, 1], c=[COLOR_RGBS[i]], s=100,
                              edgecolors='k', linewidths=0.5, zorder=3)
                    ax.annotate(COLOR_NAMES[i], (c2d[i, 0], c2d[i, 1]),
                               textcoords='offset points', xytext=(6, 6), fontsize=7)
                sig = '*' if d[pk] < 0.05 else 'ns'
                ax.text(0.05, 0.95, f'ρ={d[rk]:.3f} (p={d[pk]:.3f}) {sig}',
                       transform=ax.transAxes, fontsize=9, va='top',
                       bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            ax.set_aspect('equal')
            ax.set_xticks([])
            ax.set_yticks([])
            if row == 0:
                ax.set_title(method, fontsize=11)
            if col == 0:
                ax.set_ylabel(roi, fontsize=11, fontweight='bold')
    fig.suptitle('Isomap vs MDS (SRM, HC mean)', fontsize=13)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Analysis 6: Per-Subject
# ============================================================================

def per_subject_analysis(roi, align='srm'):
    results = []
    rdms = {}
    for subj in ALL_SUBJECTS:
        try:
            amp = load_amplitudes(subj, roi, align)
            rdms[subj] = compute_rdm(amp.mean(axis=0))
        except FileNotFoundError:
            pass
    if not rdms:
        return results

    hc_rdms = [rdms[s] for s in HC_SUBJECTS if s in rdms]
    rdm_hc_mean = np.mean(hc_rdms, axis=0) if hc_rdms else None
    rdm_ang = angular_rdm()
    rdm_cie = cielab_rdm('ab')

    for subj in ALL_SUBJECTS:
        if subj not in rdms:
            continue
        rdm_s = rdms[subj]
        group = 'HC' if subj in HC_SUBJECTS else 'CVD'

        # 2D MDS + circular order
        try:
            mds = MDS(n_components=2, metric=True, n_init=10, max_iter=500,
                      random_state=42, dissimilarity='precomputed', normalized_stress=False)
            c2d = mds.fit_transform(rdm_s)
            stress = float(normalized_stress(rdm_s, c2d))
            rho, rho_p = circular_order_correlation(c2d)
        except Exception:
            stress, rho, rho_p = np.nan, 0.0, 1.0

        # ISC vs HC mean
        isc = 0.0
        if rdm_hc_mean is not None:
            triu = np.triu_indices(8, k=1)
            isc, _ = spearmanr(rdm_s[triu], rdm_hc_mean[triu])
            isc = float(isc)

        # Mantel: angular vs CIELab
        r_ang, p_ang, _ = mantel_test(rdm_s, rdm_ang, n_permutations=1000, random_state=42)
        r_cie, p_cie, _ = mantel_test(rdm_s, rdm_cie, n_permutations=1000, random_state=42)

        results.append({
            'subject': f'sub-{subj}', 'group': group,
            'stress_2d': stress,
            'circular_rho': float(rho), 'circular_p': float(rho_p),
            'isc': isc,
            'mantel_angular_r': float(r_ang), 'mantel_angular_p': float(p_ang),
            'mantel_cielab_r': float(r_cie), 'mantel_cielab_p': float(p_cie),
        })
    return results


def plot_per_subject(subj_data, output_path):
    from matplotlib.lines import Line2D
    metrics = [
        ('stress_2d', '2D Stress', False),
        ('circular_rho', 'Circular ρ', True),
        ('isc', 'ISC (vs HC mean)', True),
        ('mantel_cielab_r', 'CIELab Mantel r', True),
    ]
    fig, axes = plt.subplots(2, 4, figsize=(18, 8))
    for row, roi in enumerate(['V1', 'V2']):
        if roi not in subj_data or not subj_data[roi]:
            continue
        data = subj_data[roi]
        for col, (mk, label, _) in enumerate(metrics):
            ax = axes[row, col]
            hc_vals = [d[mk] for d in data if d['group'] == 'HC' and np.isfinite(d[mk])]
            cvd_list = [d for d in data if d['group'] == 'CVD' and np.isfinite(d[mk])]
            if hc_vals:
                jitter = np.random.default_rng(42).uniform(-0.15, 0.15, len(hc_vals))
                ax.scatter(hc_vals, jitter, c='steelblue', s=40, alpha=0.7,
                          edgecolors='k', linewidths=0.3, label='HC')
                ax.axvline(np.mean(hc_vals), color='steelblue', linestyle='--', alpha=0.5)
            cvd_colors = {'sub-08': '#e74c3c', 'sub-09': '#f39c12', 'sub-10': '#9b59b6'}
            for d in cvd_list:
                ax.scatter(d[mk], 0.3, c=cvd_colors.get(d['subject'], 'red'), s=80,
                          marker='D', edgecolors='k', linewidths=0.5, zorder=4)
                ax.annotate(d['subject'].replace('sub-', 's'), (d[mk], 0.3),
                           textcoords='offset points', xytext=(0, 8), fontsize=7, ha='center')
            ax.set_ylim(-0.5, 0.7)
            ax.set_yticks([])
            ax.set_xlabel(label, fontsize=9)
            if col == 0:
                ax.set_ylabel(roi, fontsize=11, fontweight='bold')
            if mk == 'stress_2d':
                ax.axvline(0.10, color='gray', linestyle=':', alpha=0.5)

    legend_els = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='steelblue', markersize=8, label='HC'),
        Line2D([0], [0], marker='D', color='w', markerfacecolor='#e74c3c', markersize=8, label='sub-08'),
        Line2D([0], [0], marker='D', color='w', markerfacecolor='#f39c12', markersize=8, label='sub-09'),
        Line2D([0], [0], marker='D', color='w', markerfacecolor='#9b59b6', markersize=8, label='sub-10'),
    ]
    fig.legend(handles=legend_els, loc='lower center', ncol=4, fontsize=9, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle('Per-Subject V1/V2 Diagnostic (SRM)', fontsize=13)
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f'  Saved: {output_path}')


# ============================================================================
# Main
# ============================================================================

def main():
    print('=' * 70)
    print('CIELab vs Angular RDM Diagnostic (Filter Pre-Validation)')
    print('=' * 70)
    print(f'Data: {DATA_DIR}')
    print(f'Output: {RESULTS_DIR}')
    print()

    # Print CIELab non-uniformity evidence
    print('--- CIELab Non-Uniformity Evidence ---')
    colors = [f'color_{i}' for i in range(1, 9)]
    ab = np.array([[COLOR_LAB[c][1], COLOR_LAB[c][2]] for c in colors])
    for i in range(8):
        j = (i + 1) % 8
        dist = np.linalg.norm(ab[i] - ab[j])
        print(f'  {COLOR_NAMES[i]:>8s} → {COLOR_NAMES[j]:<8s}: '
              f'Δa*={ab[j,0]-ab[i,0]:+6.1f}, Δb*={ab[j,1]-ab[i,1]:+6.1f}, '
              f'dist={dist:.1f}')
    dists = [np.linalg.norm(ab[(i+1)%8] - ab[i]) for i in range(8)]
    print(f'  Range: {min(dists):.1f} ~ {max(dists):.1f} (ratio={max(dists)/min(dists):.1f}x)')
    print()

    # Load data
    group_rdms = {}
    group_patterns = {}
    for roi in ROIS:
        for align in ALIGNMENTS:
            rdms_hc, pats_hc = [], []
            for subj in HC_SUBJECTS:
                try:
                    amp = load_amplitudes(subj, roi, align)
                    mp = amp.mean(axis=0)  # (8, n_features)
                    rdms_hc.append(compute_rdm(mp))
                    if align == 'srm':
                        pats_hc.append(mp)
                except FileNotFoundError:
                    pass
            if rdms_hc:
                group_rdms[(roi, align)] = np.mean(rdms_hc, axis=0)
                if align == 'srm' and pats_hc:
                    group_patterns[(roi, align)] = np.mean(pats_hc, axis=0)

    # Containers
    stress_data = {}
    mantel_data = {}
    ph_data = {}
    hd_data = {}
    iso_data = {}
    subj_data = {}

    # === Analysis 1: Stress Curve ===
    print('--- Analysis 1: Stress Curve (1-7D) ---')
    for roi in ROIS:
        for align in ALIGNMENTS:
            key = (roi, align)
            if key in group_rdms:
                stresses = compute_stress_curve(group_rdms[key])
                stress_data[key] = stresses
                dims_pass = [d+1 for d, s in enumerate(stresses) if s < 0.10]
                md = dims_pass[0] if dims_pass else '>7'
                print(f'  {roi} {align:12s}: stress<0.10 @ dim={md}  '
                      f'[{", ".join(f"{s:.3f}" for s in stresses)}]')
    plot_stress_curve(stress_data, RESULTS_DIR / 'fig1_stress_curve.png')

    # === Analysis 2: Reference RDM Comparison ===
    print('\n--- Analysis 2: Neural RDM vs Reference Models ---')
    for roi in ROIS:
        for align in ALIGNMENTS:
            key = (roi, align)
            if key in group_rdms:
                res = reference_mantel_comparison(group_rdms[key])
                for model, vals in res.items():
                    mantel_data[(roi, align, model)] = vals
                    sig = '***' if vals['p'] < BONFERRONI_ALPHA else (
                        '*' if vals['p'] < 0.05 else '')
                    print(f'  {roi} {align:12s} vs {model:15s}: '
                          f'r={vals["r"]:.3f}, p={vals["p"]:.4f} {sig}')
    plot_mantel_comparison(mantel_data, RESULTS_DIR / 'fig2_mantel_comparison.png')

    # === Analysis 3: Persistent Homology ===
    print('\n--- Analysis 3: Persistent Homology (H1) ---')
    for roi in ['V1', 'V2']:
        key = (roi, 'srm')
        if key in group_rdms:
            r = persistent_homology_test(group_rdms[key])
            ph_data[key] = r
            if r['has_ripser']:
                print(f'  {roi} SRM: max_H1={r["max_h1_lifetime"]:.4f}, p={r["p_value"]:.4f}')
            else:
                print(f'  {roi} SRM: ripser not installed')
    plot_persistence(ph_data, RESULTS_DIR / 'fig3_persistence.png')

    # === Analysis 4: Higher-D MDS ===
    print('\n--- Analysis 4: Higher-D MDS + PCA 2D ---')
    for roi in ['V1', 'V2']:
        key = (roi, 'srm')
        if key in group_rdms:
            r = higher_d_mds(group_rdms[key])
            hd_data[key] = r
            for dim in (2, 3, 4):
                d = r[dim]
                print(f'  {roi} SRM {dim}D: stress={d["stress"]:.3f}, '
                      f'Shepard R²={d["shepard_r2"]:.3f}, '
                      f'ρ={d["circular_rho"]:.3f} (p={d["circular_p"]:.3f})')
    plot_higher_d(hd_data, RESULTS_DIR / 'fig4_higher_d_mds.png')

    # === Analysis 5: Isomap vs MDS ===
    print('\n--- Analysis 5: Isomap vs MDS ---')
    for roi in ['V1', 'V2']:
        key = (roi, 'srm')
        if key in group_rdms and key in group_patterns:
            r = isomap_vs_mds(group_patterns[key], group_rdms[key])
            iso_data[key] = r
            winner = 'Isomap' if abs(r['isomap_rho']) > abs(r['mds_rho']) else 'MDS'
            print(f'  {roi} SRM: MDS ρ={r["mds_rho"]:.3f}, '
                  f'Isomap ρ={r["isomap_rho"]:.3f} → {winner}')
    plot_isomap(iso_data, RESULTS_DIR / 'fig5_isomap_vs_mds.png')

    # === Analysis 6: Per-Subject ===
    print('\n--- Analysis 6: Per-Subject V1/V2 ---')
    for roi in ['V1', 'V2']:
        results = per_subject_analysis(roi)
        subj_data[roi] = results
        for d in results:
            sa = '*' if d['mantel_angular_p'] < 0.05 else ''
            sc = '*' if d['mantel_cielab_p'] < 0.05 else ''
            print(f'  {roi} {d["subject"]} ({d["group"]}): '
                  f'Angular r={d["mantel_angular_r"]:.3f}{sa}, '
                  f'CIELab r={d["mantel_cielab_r"]:.3f}{sc}, '
                  f'ISC={d["isc"]:.3f}')
    plot_per_subject(subj_data, RESULTS_DIR / 'fig6_per_subject.png')

    # === Decision Framework ===
    print('\n' + '=' * 70)
    print('DECISION FRAMEWORK')
    print('=' * 70)

    decisions = {}
    for roi in ROIS:
        dec = {'checks': {}, 'verdict': 'unstructured'}

        # Q1: CIELab > Angular?
        k_ang = (roi, 'srm', 'angular')
        k_cie = (roi, 'srm', 'cielab_ab')
        if k_ang in mantel_data and k_cie in mantel_data:
            r_a, r_c = mantel_data[k_ang]['r'], mantel_data[k_cie]['r']
            p_c = mantel_data[k_cie]['p']
            dec['checks']['Q1_cielab_superior'] = {
                'pass': bool(r_c > r_a and p_c < 0.05),
                'r_angular': float(r_a), 'r_cielab': float(r_c), 'p_cielab': float(p_c),
            }

        # Q2: H1 topology?
        pk = (roi, 'srm')
        if pk in ph_data and ph_data[pk].get('has_ripser'):
            dec['checks']['Q2_H1_topology'] = {
                'pass': bool(ph_data[pk]['p_value'] < 0.05),
                'max_lifetime': float(ph_data[pk]['max_h1_lifetime']),
                'p_value': float(ph_data[pk]['p_value']),
            }

        # Q3: Higher-D?
        if pk in hd_data:
            bs = min(hd_data[pk][d]['stress'] for d in (3, 4) if d in hd_data[pk])
            br = max(abs(hd_data[pk][d]['circular_rho']) for d in (3, 4) if d in hd_data[pk])
            dec['checks']['Q3_higher_d'] = {
                'pass': bool(bs < 0.10 or br > 0.7),
                'best_stress': float(bs), 'best_rho': float(br),
            }

        # Q4: Isomap > MDS?
        if pk in iso_data:
            mr = abs(iso_data[pk]['mds_rho'])
            ir = abs(iso_data[pk]['isomap_rho'])
            dec['checks']['Q4_isomap_superior'] = {
                'pass': bool(ir > mr), 'mds_rho': float(mr), 'isomap_rho': float(ir),
            }

        n_pass = sum(1 for c in dec['checks'].values() if c.get('pass'))
        dec['verdict'] = 'structured' if n_pass >= 2 else ('marginal' if n_pass == 1 else 'unstructured')
        dec['n_pass'] = n_pass
        decisions[roi] = dec

        print(f'\n{roi}: {n_pass}/4 pass → {dec["verdict"].upper()}')
        for q, v in dec['checks'].items():
            status = 'PASS' if v.get('pass') else 'FAIL'
            detail = {k: val for k, val in v.items() if k != 'pass'}
            print(f'  {q}: {status} — {detail}')

    # === Save JSON ===
    summary = {
        'analysis': 'CIELab_vs_Angular_RDM_Diagnostic',
        'data_dir': str(DATA_DIR),
        'bonferroni_alpha': BONFERRONI_ALPHA,
        'srm_k': SRM_K,
        'cielab_coordinates': {f'color_{i}': COLOR_LAB[f'color_{i}'] for i in range(1, 9)},
        'adjacent_cielab_distances': {
            f'{COLOR_NAMES[i]}-{COLOR_NAMES[(i+1)%8]}': float(np.linalg.norm(ab[(i+1)%8] - ab[i]))
            for i in range(8)
        },
        'stress_curves': {f'{r}_{a}': v for (r, a), v in stress_data.items()},
        'mantel_comparison': {
            f'{r}_{a}_{m}': {'r': v['r'], 'p': v['p']}
            for (r, a, m), v in mantel_data.items()
        },
        'persistent_homology': {
            f'{r}_{a}': {'has_ripser': v['has_ripser'],
                         'max_h1_lifetime': v['max_h1_lifetime'],
                         'p_value': v['p_value']}
            for (r, a), v in ph_data.items()
        },
        'higher_d_mds': {
            f'{r}_{a}_{d}D': {k: v for k, v in vals.items() if k not in ('coords', 'pca_2d')}
            for (r, a), dims in hd_data.items() for d, vals in dims.items()
        },
        'isomap_vs_mds': {
            f'{r}_{a}': {k: v for k, v in vals.items() if 'coords' not in k}
            for (r, a), vals in iso_data.items()
        },
        'per_subject': subj_data,
        'decisions': decisions,
    }

    json_path = RESULTS_DIR / 'cielab_diagnostic_summary.json'
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f'\nSaved: {json_path}')

    print('\n' + '=' * 70)
    print('Done. Figures: fig1~fig6 in results/cielab_diagnostic/')
    print('=' * 70)


if __name__ == '__main__':
    main()
