#!/usr/bin/env python3
"""
visualize_color_structure.py — Color encoding geometry (hV4).

For each subject, show how the 8 colors are encoded in hV4 based on:
  (A) RDM-based geometry — 2D MDS scatter. HC is the uniform reference
      octagon; CVD shows observed distortion; models show predicted distortion.
  (B) LOCO encoding profile — per-color LOCO vulnerability.
      HC baseline, CVD observed, and model-simulated predictions.

Usage:
    conda activate srm
    python scripts/visualize_color_structure.py
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.spatial.distance import pdist, squareform
from scipy.linalg import orthogonal_procrustes
from sklearn.manifold import MDS
import sys
import warnings

warnings.filterwarnings('ignore', category=UserWarning)

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PIPELINE_DIR = _SCRIPT_DIR.parent
_RESULT_DIR = _PIPELINE_DIR / 'results'
_LOCO_DIR = _RESULT_DIR / 'loco_filter'
_C010_ROOT = (_PIPELINE_DIR.parent / 'phase1_procrustes_decoding' /
              'results' / 'visualization' / 'full_dataset_C010_with_residuals')

_FWD_DIR = str(_PIPELINE_DIR.parent / 'future_phase1_forward_model' / 'scripts')
if _FWD_DIR not in sys.path:
    sys.path.insert(0, _FWD_DIR)
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CIELAB_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
COLOR_NAMES = ['Red', 'Orange', 'Yellow', 'Green', 'Cyan', 'Blue', 'Purple', 'Magenta']
COLOR_LABELS_SHORT = [f'c{i+1}' for i in range(8)]
SIG_THRESHOLD = 0.05

# Exclude sub-07 from HC RDM computation (only 16 voxels in hV4)
HC_SUBJECTS_FOR_RDM = ['01', '02', '03', '04', '05', '06']

STIM_LAB = np.array([
    [59.90, 62.69, 3.78],    # c1 Red
    [64.20, 49.20, 45.58],   # c2 Orange
    [57.27, 13.06, 41.69],   # c3 Yellow
    [69.08, -55.02, 47.38],  # c4 Green
    [74.61, -41.33, -4.89],  # c5 Cyan
    [69.14, -11.45, -40.91], # c6 Blue
    [60.68, 19.18, -54.13],  # c7 Purple
    [60.17, 46.82, -40.31],  # c8 Magenta
])

_M_XYZ_TO_SRGB = np.array([
    [3.2406, -1.5372, -0.4986],
    [-0.9689,  1.8758,  0.0415],
    [0.0557, -0.2040,  1.0570],
])


def lab2rgb(L, a, b):
    L, a, b = np.asarray(L, float), np.asarray(a, float), np.asarray(b, float)
    y = (L + 16) / 116
    x = a / 500 + y
    z = y - b / 200
    xyz = np.stack([x, y, z], axis=-1)
    mask = xyz > 0.206893
    xyz = np.where(mask, xyz ** 3, (xyz - 16 / 116) / 7.787)
    xyz *= np.array([0.95047, 1.0, 1.08883])
    rgb = xyz @ _M_XYZ_TO_SRGB.T
    rgb = np.where(rgb <= 0.0031308, 12.92 * rgb,
                   1.055 * np.power(np.maximum(rgb, 0), 1 / 2.4) - 0.055)
    return np.clip(rgb, 0, 1)


STIM_RGB = lab2rgb(STIM_LAB[:, 0], STIM_LAB[:, 1], STIM_LAB[:, 2])

MODEL_STYLES = {
    'machado_1way': {
        'color': '#2E7D32', 'linestyle': '-.', 'marker': '^',
        'ms': 60, 'lw': 1.6, 'label': 'Machado', 'short': 'Mach',
    },
    'rc_opponent': {
        'color': '#E65100', 'linestyle': ':', 'marker': 'v',
        'ms': 60, 'lw': 1.8, 'label': 'R+C', 'short': 'R+C',
    },
    '2component': {
        'color': '#1565C0', 'linestyle': '--', 'marker': 'D',
        'ms': 55, 'lw': 1.6, 'label': '2-Comp', 'short': '2C',
    },
}

SUBJECTS = [
    {'id': '08', 'cvd_type': 'deutan', 'label': 'Sub-08 (mild deutan)'},
    {'id': '09', 'cvd_type': 'protan', 'label': 'Sub-09 (mod. protan)'},
    {'id': '10', 'cvd_type': 'normal', 'label': 'Sub-10 (control)'},
]

# Reference unit circle at CIELab angles (used as Procrustes target)
_REF_ANGLES_RAD = np.deg2rad(CIELAB_ANGLES)
REF_POSITIONS = np.stack([np.cos(_REF_ANGLES_RAD),
                          np.sin(_REF_ANGLES_RAD)], axis=1)


# ---------------------------------------------------------------------------
# Amplitude loading and RDM computation
# ---------------------------------------------------------------------------

def load_amps(subj_id, roi='V4'):
    """Load amplitudes (6, 8, n_vox) and average over runs → (8, n_vox)."""
    f = _C010_ROOT / f'sub-{subj_id}' / roi / 'amplitudes_procrustes.npy'
    if not f.exists():
        return None
    X = np.load(f)  # (n_runs, 8, n_vox)
    return X.mean(axis=0)


def compute_rdm(amps):
    """Correlation-distance RDM (8×8)."""
    d = pdist(amps, metric='correlation')
    return squareform(d)


def classical_mds(D, k=2):
    """Classical (metric) MDS — deterministic, stable for small point sets.

    D: dissimilarity matrix (n×n). Returns n×k coordinates.
    """
    n = D.shape[0]
    J = np.eye(n) - np.ones((n, n)) / n
    B = -0.5 * J @ (D ** 2) @ J
    eigvals, eigvecs = np.linalg.eigh(B)
    idx = np.argsort(eigvals)[::-1]
    eigvals = eigvals[idx]
    eigvecs = eigvecs[:, idx]
    L = np.diag(np.sqrt(np.maximum(eigvals[:k], 0)))
    return eigvecs[:, :k] @ L


def mds_2d(rdm, random_state=42):
    """Classical 2D MDS."""
    return classical_mds(rdm, k=2)


def procrustes_align(X, target):
    """Align X to target by rigid transform (centering + rotation + reflection).

    Preserves shape (distances) — no scaling.
    """
    Xc = X - X.mean(axis=0)
    Tc = target - target.mean(axis=0)
    # Allow reflection. Use SVD-based orthogonal procrustes.
    R, _ = orthogonal_procrustes(Xc, Tc)
    aligned = Xc @ R
    # Scale to match the target radius (so they are comparable visually)
    scale = np.linalg.norm(Tc) / (np.linalg.norm(aligned) + 1e-12)
    return aligned * scale


def compute_hc_reference_geometry(roi='V4'):
    """Per-subject MDS → Procrustes-align each to CIELab reference → average.

    This gives a cleaner HC reference than pooling RDMs because each subject's
    MDS is independently rotated to best fit the theoretical uniform circle.
    """
    rdms = []
    per_subj_aligned = []
    for s in HC_SUBJECTS_FOR_RDM:
        amps = load_amps(s, roi)
        if amps is None:
            continue
        rdm = compute_rdm(amps)
        if np.any(np.isnan(rdm)):
            continue
        rdms.append(rdm)
        mds_pos = mds_2d(rdm)
        aligned = procrustes_align(mds_pos, REF_POSITIONS)
        per_subj_aligned.append(aligned)
    hc_mean_pos = np.mean(per_subj_aligned, axis=0)
    mean_rdm = np.mean(rdms, axis=0)
    return hc_mean_pos, mean_rdm


def compute_cvd_geometry(subj_id, hc_aligned, roi='V4'):
    """Compute CVD subject's MDS geometry, aligned to HC reference."""
    amps = load_amps(subj_id, roi)
    if amps is None:
        return None, None
    rdm = compute_rdm(amps)
    mds_pos = mds_2d(rdm)
    aligned = procrustes_align(mds_pos, hc_aligned)
    return aligned, rdm


def apply_model_rotation(hc_pos, delta_theta_deg):
    """Rotate each HC position by its δθ (degrees). Preserves radial distance."""
    sim = np.zeros_like(hc_pos)
    for i in range(len(hc_pos)):
        x, y = hc_pos[i]
        r = np.sqrt(x * x + y * y)
        theta = np.arctan2(y, x)
        new_theta = theta + np.deg2rad(delta_theta_deg[i])
        sim[i] = [r * np.cos(new_theta), r * np.sin(new_theta)]
    return sim


# ---------------------------------------------------------------------------
# Model results loading (same as before)
# ---------------------------------------------------------------------------

def _load_json(path):
    with open(path) as f:
        return json.load(f)


def load_model_result(subj_id, model_name):
    if model_name == '2component':
        d = _LOCO_DIR / 'phase_a_2component'
    else:
        d = _LOCO_DIR / 'phase_a_v2'
    fname = d / f'sub-{subj_id}_V4_{model_name}.json'
    if not fname.exists():
        return None
    return _load_json(fname)


def load_manifest(subj_id):
    for d in ['phase_a_2component', 'phase_a_v2']:
        fname = _LOCO_DIR / d / f'sub-{subj_id}_V4_manifest.json'
        if fname.exists():
            return _load_json(fname)
    return None


def load_all_models(subj_id):
    results = []
    for mname in ['machado_1way', 'rc_opponent', '2component']:
        r = load_model_result(subj_id, mname)
        if r is None:
            continue
        perm_p = r['permutation']['label_perm_p']
        rho = r['best_loss']['spearman_r']
        results.append({
            'model_name': mname,
            'params': r['best_params'],
            'vuln_sim': np.array(r['best_loss']['vuln_sim']),
            'delta_theta': np.array(r['best_loss']['delta_theta']),
            'rho': rho,
            'perm_p': perm_p,
            'significant': perm_p < SIG_THRESHOLD,
        })
    results.sort(key=lambda x: (-x['significant'], -x['rho']))
    return results


def format_params(model_name, params):
    if model_name == 'machado_1way':
        return f'$\\Delta\\lambda$={params[0]:.1f}nm'
    elif model_name == 'rc_opponent':
        return f'$\\Delta\\lambda$={params[0]:.1f}, g={params[1]:+.2f}'
    elif model_name == '2component':
        return f'$\\beta_s$={params[0]:.0f}$^\\circ$, $\\beta_c$={params[1]:+.0f}$^\\circ$'
    return str(params)


# ---------------------------------------------------------------------------
# Panel A: RDM-based color geometry (2D MDS scatter)
# ---------------------------------------------------------------------------

def _extract_angles(positions_2d):
    """Get angles (degrees, 0-360) of each point from 2D coordinates."""
    angles = np.rad2deg(np.arctan2(positions_2d[:, 1], positions_2d[:, 0]))
    return angles % 360.0


def _ring_positions(angles_deg, radius):
    """Given 8 angles (deg), return (x,y) on a circle of given radius."""
    a = np.deg2rad(angles_deg)
    return np.stack([radius * np.cos(a), radius * np.sin(a)], axis=1)


def _draw_ring(ax, angles_deg, radius, stim_rgb, marker, edge_color,
               ms, line_color, line_lw, line_alpha, polygon_fill=None,
               zorder=3):
    """Draw one ring: smooth reference circle at given radius + colored dots.

    Dots are placed at each color's angle (not connected as a polygon —
    avoids self-intersections when empirical angles differ from theoretical).
    """
    # Smooth reference circle
    theta_circle = np.linspace(0, 2 * np.pi, 256)
    ax.plot(radius * np.cos(theta_circle), radius * np.sin(theta_circle),
            '-', color=line_color, linewidth=line_lw,
            alpha=line_alpha * 0.55, zorder=zorder)
    # Optional faint band fill (thin annulus) for emphasis
    if polygon_fill is not None:
        band_w = 0.08
        inner = (radius - band_w) * np.array([np.cos(theta_circle),
                                              np.sin(theta_circle)])
        outer = (radius + band_w) * np.array([np.cos(theta_circle),
                                              np.sin(theta_circle)])
        verts_x = np.concatenate([outer[0], inner[0][::-1]])
        verts_y = np.concatenate([outer[1], inner[1][::-1]])
        ax.fill(verts_x, verts_y, color=polygon_fill, alpha=0.08,
                zorder=zorder - 1)
    # Dots at each color's angle
    pts = _ring_positions(angles_deg, radius)
    for i in range(8):
        ax.scatter(pts[i, 0], pts[i, 1], c=[stim_rgb[i]], s=ms,
                   marker=marker, edgecolors=edge_color, linewidths=1.5,
                   zorder=zorder + 2)
    return pts


def plot_rdm_geometry(ax, hc_pos, cvd_pos, models, subj_label, cvd_type):
    """Concentric rings showing color interval structure per condition.

    From outer → inner:
      r=2.00 Theoretical (CIELab uniform 45°)
      r=1.60 HC empirical (RDM MDS)
      r=1.20 CVD observed
      r=0.80 Model sim 1 (most significant)
      r=0.40 Model sim 2 (second)
    """
    hc_angles = _extract_angles(hc_pos)
    cvd_angles = _extract_angles(cvd_pos)

    # Background radial guides at theoretical CIELab angles
    for a in CIELAB_ANGLES:
        ar = np.deg2rad(a)
        ax.plot([0, 2.20 * np.cos(ar)], [0, 2.20 * np.sin(ar)],
                color='#eeeeee', lw=0.7, zorder=0)

    # ---- Theoretical ring (outermost, uniform reference) ----
    _draw_ring(ax, CIELAB_ANGLES, radius=2.00, stim_rgb=STIM_RGB,
               marker='o', edge_color='#aaa', ms=85,
               line_color='#bbb', line_lw=1.0, line_alpha=0.55,
               polygon_fill=None, zorder=2)

    # ---- HC empirical ring (main reference point) ----
    _draw_ring(ax, hc_angles, radius=1.60, stim_rgb=STIM_RGB,
               marker='o', edge_color='#111', ms=170,
               line_color='#222', line_lw=2.2, line_alpha=0.9,
               polygon_fill=None, zorder=3)

    # ---- CVD observed ring ----
    _draw_ring(ax, cvd_angles, radius=1.20, stim_rgb=STIM_RGB,
               marker='s', edge_color='#C62828', ms=140,
               line_color='#C62828', line_lw=1.8, line_alpha=0.88,
               polygon_fill=None, zorder=4)

    # ---- Model simulated rings (apply δθ to HC angles) ----
    sig_models = [m for m in models if m['significant']]
    sim_radii = [0.80, 0.40]
    sim_ms    = [110, 85]
    for k, m in enumerate(sig_models[:2]):
        style = MODEL_STYLES[m['model_name']]
        sim_angles = (hc_angles + m['delta_theta']) % 360.0
        _draw_ring(ax, sim_angles, radius=sim_radii[k], stim_rgb=STIM_RGB,
                   marker=style['marker'],
                   edge_color=style['color'], ms=sim_ms[k],
                   line_color=style['color'], line_lw=1.6,
                   line_alpha=0.88,
                   polygon_fill=None, zorder=5 + k)

    # Color labels outside outer ring (at theoretical positions)
    for i in range(8):
        lr = 2.35
        a = np.deg2rad(CIELAB_ANGLES[i])
        lx = lr * np.cos(a)
        ly = lr * np.sin(a)
        ax.text(lx, ly, COLOR_LABELS_SHORT[i], fontsize=10.5, fontweight='bold',
                ha='center', va='center',
                color=np.clip(STIM_RGB[i] * 0.55, 0, 1),
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                          edgecolor='none', alpha=0.85))

    # Ring labels — compact proxy legend at top-left, outside ring
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ccc',
               markeredgecolor='#888', markersize=7,
               label='Theoretical (uniform 45°)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#ddd',
               markeredgecolor='#111', markersize=10,
               label='HC empirical'),
        Line2D([0], [0], marker='s', color='w', markerfacecolor='#ddd',
               markeredgecolor='#C62828', markersize=9,
               label='CVD observed'),
    ]
    for m in sig_models[:2]:
        style = MODEL_STYLES[m['model_name']]
        handles.append(Line2D(
            [0], [0], marker=style['marker'], color='w',
            markerfacecolor='#ddd', markeredgecolor=style['color'],
            markersize=8,
            label=f'{style["label"]} sim ($\\rho$={m["rho"]:.2f})'))
    ax.legend(handles=handles, loc='upper left',
              bbox_to_anchor=(-0.05, 1.02),
              fontsize=7.0, framealpha=0.9, handlelength=1.2,
              borderpad=0.4, labelspacing=0.3)

    ax.set_aspect('equal')
    lim = 2.55
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.axis('off')
    ax.set_title(f'{subj_label} — hV4  Color Encoding',
                 fontsize=11, fontweight='bold', pad=6)


# ---------------------------------------------------------------------------
# Panel B: LOCO encoding profile (grouped bars)
# ---------------------------------------------------------------------------

def plot_loco_bars(ax, vuln_hc, vuln_cvd, models, subj_label):
    """Grouped bar chart of per-color LOCO vulnerability values."""
    x = np.arange(8)
    sig_models = [m for m in models if m['significant']]
    n_sim = min(len(sig_models), 2)
    n_groups = 2 + n_sim
    total_w = 0.78
    w = total_w / n_groups
    # Offsets center bars on each tick
    offsets = np.linspace(-(n_groups - 1) / 2, (n_groups - 1) / 2, n_groups) * w

    # HC bar
    ax.bar(x + offsets[0], vuln_hc, w, color='#666', alpha=0.85,
           edgecolor='#333', linewidth=0.8,
           label='HC baseline (uniform expected)', zorder=3)
    # CVD bar (outlined with stim colors)
    for i in range(8):
        ax.bar(x[i] + offsets[1], vuln_cvd[i], w,
               color=STIM_RGB[i], alpha=0.75,
               edgecolor='#C62828', linewidth=1.3, zorder=3)
    # Dummy for legend
    ax.bar([], [], w, color='#C62828', alpha=0.75,
           edgecolor='#C62828', linewidth=1.3, label='CVD observed')

    # Model sim bars
    for k, m in enumerate(sig_models[:2]):
        style = MODEL_STYLES[m['model_name']]
        for i in range(8):
            ax.bar(x[i] + offsets[2 + k], m['vuln_sim'][i], w,
                   color=STIM_RGB[i], alpha=0.55,
                   edgecolor=style['color'], linewidth=1.3,
                   hatch='///' if k == 1 else None, zorder=3)
        # Dummy for legend
        ax.bar([], [], w, color=style['color'], alpha=0.55,
               edgecolor=style['color'], linewidth=1.3,
               hatch='///' if k == 1 else None,
               label=f'{style["label"]} sim ($\\rho$={m["rho"]:.2f}, p={m["perm_p"]:.3f})')

    # Zero line
    ax.axhline(0, color='black', lw=0.6, ls=':', alpha=0.6)

    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_LABELS_SHORT, fontsize=9, fontweight='bold')
    for label, rgb in zip(ax.get_xticklabels(), STIM_RGB):
        label.set_color(np.clip(rgb * 0.6, 0, 1))

    ax.set_ylabel('LOCO vulnerability\n(higher = harder to interpolate)',
                  fontsize=8)
    ax.set_title(f'{subj_label} — hV4\nLOCO Encoding Profile',
                 fontsize=11, fontweight='bold', pad=6)
    ax.legend(loc='best', fontsize=6.5, framealpha=0.88)
    ax.grid(axis='y', linestyle=':', alpha=0.35)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


# ---------------------------------------------------------------------------
# Main figure
# ---------------------------------------------------------------------------

def main():
    out_dir = _RESULT_DIR / 'color_structure'
    out_dir.mkdir(exist_ok=True)
    print(f'Output: {out_dir}')

    print('Computing HC reference geometry (hV4)...')
    hc_pos, hc_rdm = compute_hc_reference_geometry(roi='V4')
    print(f'  HC mean RDM from {len(HC_SUBJECTS_FOR_RDM)} subjects.')
    print(f'  HC MDS positions (aligned to unit reference):')
    for i, p in enumerate(hc_pos):
        angle = np.rad2deg(np.arctan2(p[1], p[0])) % 360
        print(f'    c{i+1} ({COLOR_NAMES[i]:8s}): '
              f'pos=({p[0]:+.3f},{p[1]:+.3f}) angle={angle:6.1f}° '
              f'(CIELab={CIELAB_ANGLES[i]:.0f}°)')

    fig = plt.figure(figsize=(16, 15))
    gs = fig.add_gridspec(3, 2, width_ratios=[1.0, 1.15],
                          hspace=0.36, wspace=0.25)

    for row, subj in enumerate(SUBJECTS):
        subj_id = subj['id']
        cvd_type = subj['cvd_type']
        label = subj['label']
        print(f'\n  {label}...')

        manifest = load_manifest(subj_id)
        models = load_all_models(subj_id)

        vuln_hc = np.array(manifest['vuln_baseline'])
        vuln_cvd = np.array(manifest['vuln_cvd'])

        # CVD geometry
        cvd_pos, cvd_rdm = compute_cvd_geometry(subj_id, hc_pos, roi='V4')

        # Report geometry differences
        delta_mean = np.linalg.norm(cvd_pos - hc_pos, axis=1).mean()
        print(f'    mean HC↔CVD position shift: {delta_mean:.3f}')

        # Col 0: RDM geometry
        ax_geo = fig.add_subplot(gs[row, 0])
        plot_rdm_geometry(ax_geo, hc_pos, cvd_pos, models, label, cvd_type)

        # Col 1: LOCO bars
        ax_loco = fig.add_subplot(gs[row, 1])
        plot_loco_bars(ax_loco, vuln_hc, vuln_cvd, models, label)

    fig.suptitle('Color Encoding Structure — hV4\n'
                 'RDM Geometry + LOCO Profile (HC reference vs CVD vs models)',
                 fontsize=14, fontweight='bold', y=0.995)

    out_path = out_dir / 'color_structure_hV4_encoding.png'
    fig.savefig(out_path, dpi=180, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'\nSaved: {out_path}')


if __name__ == '__main__':
    main()
