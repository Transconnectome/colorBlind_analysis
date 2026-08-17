#!/usr/bin/env python3
"""
visualize_loco_decomposition.py — LOCO vs ΔRDM decomposition visualization.

Creates per-subject figures showing:
  Panel A (left):  vuln_obs vs vuln_sim — per-color LOCO vulnerability profile
  Panel B (right): ΔRDM_obs vs ΔRDM_sim — pairwise distance distortion (8×8 heatmap)

Also computes ΔRDM_sim at LOCO-fitted params from precomputed W matrices
and the 2-component model's design matrix.

Usage:
    conda activate srm
    python scripts/visualize_loco_decomposition.py
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from pathlib import Path
from scipy.spatial.distance import squareform
from scipy.stats import spearmanr
import sys

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PIPELINE_DIR = _SCRIPT_DIR.parent
_RESULT_DIR = _PIPELINE_DIR / 'results'
_STEP0_DIR = _RESULT_DIR / 'step0_precompute'
_LOCO_2COMP_DIR = _RESULT_DIR / 'fits' / 'phase_a_2component'

# Forward model utils
_FWD_DIR = str(_PIPELINE_DIR.parent / 'future_phase1_forward_model' / 'scripts')
if _FWD_DIR not in sys.path:
    sys.path.insert(0, _FWD_DIR)
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR.parent))

from utils_forward_model import create_basis_full, N_CHANNELS
from machado_simulator import machado_shifted_hue

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
COLOR_LABELS = ['c1\nred', 'c2\norg', 'c3\nyel', 'c4\ngrn',
                'c5\ncya', 'c6\nblu', 'c7\npur', 'c8\nmag']
COLOR_LABELS_SHORT = ['c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8']
HUE_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
CONF_AXIS = {'protan': 16.0, 'deutan': 150.0, 'normal': 83.0}

# Approx stimulus colors for bars
STIM_COLORS = ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71',
               '#1abc9c', '#3498db', '#9b59b6', '#e91e9f']

CASES = [
    {'subject': '08', 'cvd_type': 'deutan', 'roi': 'V4', 'label': 'Sub-08 hV4 (deutan)',
     'method': 'shift_at_both'},
    {'subject': '08', 'cvd_type': 'deutan', 'roi': 'V1', 'label': 'Sub-08 V1 (deutan)',
     'method': 'w_fixed'},
    {'subject': '09', 'cvd_type': 'protan', 'roi': 'V4', 'label': 'Sub-09 hV4 (protan)',
     'method': 'shift_at_both'},
    {'subject': '09', 'cvd_type': 'protan', 'roi': 'V1', 'label': 'Sub-09 V1 (protan)',
     'method': 'w_fixed'},
    {'subject': '10', 'cvd_type': 'normal', 'roi': 'V1', 'label': 'Sub-10 V1 (control)',
     'method': 'w_fixed'},
]


# ---------------------------------------------------------------------------
# Model functions
# ---------------------------------------------------------------------------

def get_2component_design(bs, bc, cvd_type, n_channels=N_CHANNELS):
    """Compute shifted design matrix for 2-component model."""
    hue_base, _, _ = machado_shifted_hue(0.0, cvd_type)
    theta_conf = CONF_AXIS[cvd_type]
    dt = (bs * np.cos(np.radians(hue_base - 90.0))
          + bc * np.cos(np.radians(hue_base - theta_conf)))
    hue_shifted = (hue_base + dt) % 360.0
    basis_full = create_basis_full(n_channels, basis_type='fe')
    idx = np.round(hue_shifted).astype(int) % 360
    return basis_full[idx], dt


def compute_rdm_correlation(Y):
    """Compute correlation distance RDM (upper triangle, 28 elements)."""
    n = Y.shape[0]
    rdm = np.zeros(n * (n - 1) // 2)
    k = 0
    for i in range(n):
        for j in range(i + 1, n):
            r = np.corrcoef(Y[i], Y[j])[0, 1]
            rdm[k] = 1.0 - r if np.isfinite(r) else 1.0
            k += 1
    return rdm


def compute_delta_rdm_sim(hc_W_dict, C_shifted, C_baseline):
    """Compute ΔRDM_sim = mean_HC[RDM(C_shifted @ W) - RDM(C_baseline @ W)]."""
    drdms = []
    for subj, W in hc_W_dict.items():
        Y_shifted = C_shifted @ W
        Y_baseline = C_baseline @ W
        rdm_s = compute_rdm_correlation(Y_shifted)
        rdm_b = compute_rdm_correlation(Y_baseline)
        drdms.append(rdm_s - rdm_b)
    return np.mean(drdms, axis=0)


def cosine_similarity(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def vec_to_matrix(v, n=8):
    """Convert 28-element upper triangle to 8×8 symmetric matrix."""
    M = np.zeros((n, n))
    M[np.triu_indices(n, k=1)] = v
    M = M + M.T
    return M


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_hc_W(roi):
    """Load precomputed HC weight matrices."""
    data = np.load(_STEP0_DIR / f'hc_W_{roi}.npz', allow_pickle=True)
    subj_ids = list(data['subj_ids'])
    return {s: data[f'W_{s}'] for s in subj_ids}


def load_delta_rdm_obs(roi, subj_id):
    """Load precomputed observed ΔRDM."""
    fname = _STEP0_DIR / f'delta_rdm_obs_{roi}.npz'
    if not fname.exists():
        return None
    data = np.load(fname)
    key = f'delta_rdm_{subj_id}'
    return data[key] if key in data else None


def load_loco_result(subj_id, roi):
    """Load 2-component LOCO fitting result."""
    fname = _LOCO_2COMP_DIR / f'sub-{subj_id}_{roi}_2component.json'
    with open(fname) as f:
        return json.load(f)


def load_manifest(subj_id, roi):
    """Load manifest with vuln_cvd."""
    fname = _LOCO_2COMP_DIR / f'sub-{subj_id}_{roi}_manifest.json'
    with open(fname) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

def plot_case(case, out_dir):
    """Create 2-panel figure for one (subject, ROI) case."""
    subj = case['subject']
    roi = case['roi']
    cvd_type = case['cvd_type']
    label = case['label']

    # Load data
    result = load_loco_result(subj, roi)
    manifest = load_manifest(subj, roi)
    bs, bc = result['best_params']

    vuln_cvd = np.array(manifest['vuln_cvd'])
    vuln_sim = np.array(result['best_loss']['vuln_sim'])
    vuln_baseline = np.array(manifest['vuln_baseline'])
    rho_fit = result['best_loss']['spearman_r']
    rho_base = result['baseline']['spearman_r_baseline']
    perm_p = result['permutation']['label_perm_p']

    # Determine ROI key for ΔRDM and W loading
    roi_w = 'hV4' if roi == 'V4' else roi
    delta_rdm_obs = load_delta_rdm_obs(roi_w, subj)

    # Compute ΔRDM_sim at fitted params
    delta_rdm_sim = None
    rdm_cos_fit = None
    rdm_cos_base = None
    hc_W_fname = _STEP0_DIR / f'hc_W_{roi_w}.npz'

    if delta_rdm_obs is not None and hc_W_fname.exists():
        hc_W = load_hc_W(roi_w)
        C_shifted, _ = get_2component_design(bs, bc, cvd_type)
        C_baseline, _ = get_2component_design(0.0, 0.0, cvd_type)
        delta_rdm_sim = compute_delta_rdm_sim(hc_W, C_shifted, C_baseline)
        rdm_cos_fit = cosine_similarity(delta_rdm_sim, delta_rdm_obs)
        # Baseline ΔRDM_sim is zero vector (no shift) → cosine undefined
        # Use the stored baseline rdm_cosine from landscape if available
        rdm_cos_base = 0.0  # at (0,0), ΔRDM_sim = 0 → cosine = 0

    has_rdm = delta_rdm_obs is not None and delta_rdm_sim is not None

    # --- Create figure ---
    if has_rdm:
        fig, axes = plt.subplots(1, 3, figsize=(16, 5),
                                 gridspec_kw={'width_ratios': [1.2, 1, 1]})
    else:
        fig, axes = plt.subplots(1, 1, figsize=(7, 5))
        axes = [axes]

    fig.suptitle(f'{label}  |  2-Component (β_s={bs:.0f}°, β_c={bc:+.0f}°)  |  p={perm_p:.4f}',
                 fontsize=13, fontweight='bold', y=0.98)

    # --- Panel A: Vulnerability profile ---
    ax = axes[0]
    x = np.arange(8)
    w = 0.28

    bars_base = ax.bar(x - w, vuln_baseline, w, color='lightgray',
                       edgecolor='gray', label=f'HC baseline (ρ={rho_base:.3f})')
    bars_sim = ax.bar(x, vuln_sim, w, color=[c + '80' for c in STIM_COLORS],
                      edgecolor=[c for c in STIM_COLORS], linewidth=1.5,
                      label=f'Model sim (ρ={rho_fit:.3f})')
    bars_obs = ax.bar(x + w, vuln_cvd, w, color=STIM_COLORS,
                      edgecolor='black', linewidth=0.8,
                      label='CVD observed')

    ax.set_xticks(x)
    ax.set_xticklabels(COLOR_LABELS, fontsize=8)
    ax.set_ylabel('LOCO vulnerability', fontsize=10)
    ax.set_title('Per-color vulnerability profile', fontsize=11)
    ax.axhline(0, color='black', linewidth=0.5, linestyle='-')
    ax.legend(fontsize=8, loc='upper right')

    # Annotate Δρ
    ax.text(0.02, 0.95, f'Δρ = {rho_fit - rho_base:+.3f}',
            transform=ax.transAxes, fontsize=9, va='top',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.8))

    if not has_rdm:
        ax.set_title(f'{label}\n(ΔRDM not available for {roi_w})', fontsize=11)
        fig.tight_layout()
        out_path = out_dir / f'decomposition_sub-{subj}_{roi}.png'
        fig.savefig(out_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f'  Saved: {out_path.name}')
        return

    # --- Panel B: ΔRDM_obs heatmap ---
    ax_obs = axes[1]
    M_obs = vec_to_matrix(delta_rdm_obs)
    vmax = max(np.abs(delta_rdm_obs).max(), np.abs(delta_rdm_sim).max()) * 1.05
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0, vmax=vmax)

    im_obs = ax_obs.imshow(M_obs, cmap='RdBu_r', norm=norm, aspect='equal')
    ax_obs.set_xticks(range(8))
    ax_obs.set_yticks(range(8))
    ax_obs.set_xticklabels(COLOR_LABELS_SHORT, fontsize=8)
    ax_obs.set_yticklabels(COLOR_LABELS_SHORT, fontsize=8)
    ax_obs.set_title('ΔRDM observed\n(CVD − mean HC)', fontsize=10)

    # --- Panel C: ΔRDM_sim heatmap ---
    ax_sim = axes[2]
    M_sim = vec_to_matrix(delta_rdm_sim)

    im_sim = ax_sim.imshow(M_sim, cmap='RdBu_r', norm=norm, aspect='equal')
    ax_sim.set_xticks(range(8))
    ax_sim.set_yticks(range(8))
    ax_sim.set_xticklabels(COLOR_LABELS_SHORT, fontsize=8)
    ax_sim.set_yticklabels(COLOR_LABELS_SHORT, fontsize=8)
    ax_sim.set_title(f'ΔRDM model sim\n(cos = {rdm_cos_fit:+.3f})', fontsize=10)

    # Colorbar
    cbar = fig.colorbar(im_sim, ax=[ax_obs, ax_sim], shrink=0.8, pad=0.02)
    cbar.set_label('Δ correlation distance', fontsize=9)

    fig.tight_layout(rect=[0, 0, 0.95, 0.93])
    out_path = out_dir / f'decomposition_sub-{subj}_{roi}.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved: {out_path.name}')

    return rdm_cos_fit


# ---------------------------------------------------------------------------
# Summary figure: all CVD subjects ΔRDM scatter
# ---------------------------------------------------------------------------

def plot_summary(cases_data, out_dir):
    """Create summary figure: ΔRDM_obs vs ΔRDM_sim scatter for cases with ΔRDM."""
    fig, axes = plt.subplots(1, len(cases_data), figsize=(5 * len(cases_data), 4.5))
    if len(cases_data) == 1:
        axes = [axes]

    for ax, (label, drdm_obs, drdm_sim, cos_val) in zip(axes, cases_data):
        ax.scatter(drdm_obs, drdm_sim, c='steelblue', s=30, alpha=0.7, zorder=3)
        # Identity line
        lim = max(np.abs(drdm_obs).max(), np.abs(drdm_sim).max()) * 1.2
        ax.plot([-lim, lim], [-lim, lim], 'k--', alpha=0.3, linewidth=0.8)
        ax.axhline(0, color='gray', linewidth=0.3)
        ax.axvline(0, color='gray', linewidth=0.3)
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_xlabel('ΔRDM observed (28 pairs)', fontsize=9)
        ax.set_ylabel('ΔRDM simulated', fontsize=9)
        ax.set_title(f'{label}\ncos = {cos_val:+.3f}', fontsize=10)
        ax.set_aspect('equal')

    fig.suptitle('ΔRDM observed vs model-simulated at LOCO-fitted params',
                 fontsize=12, fontweight='bold')
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    out_path = out_dir / 'decomposition_drdm_scatter_summary.png'
    fig.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f'  Saved: {out_path.name}')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    out_dir = _RESULT_DIR / 'visualizations' / 'loco_decomposition'
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f'Output: {out_dir}')

    scatter_data = []

    for case in CASES:
        subj = case['subject']
        roi = case['roi']
        roi_w = 'hV4' if roi == 'V4' else roi
        print(f'\nProcessing {case["label"]}...')

        cos_val = plot_case(case, out_dir)

        # Collect for summary scatter if ΔRDM available
        if cos_val is not None:
            drdm_obs = load_delta_rdm_obs(roi_w, subj)
            result = load_loco_result(subj, roi)
            bs, bc = result['best_params']
            hc_W = load_hc_W(roi_w)
            C_shifted, _ = get_2component_design(bs, bc, case['cvd_type'])
            C_baseline, _ = get_2component_design(0.0, 0.0, case['cvd_type'])
            drdm_sim = compute_delta_rdm_sim(hc_W, C_shifted, C_baseline)
            scatter_data.append((case['label'], drdm_obs, drdm_sim, cos_val))

    # Summary scatter
    if scatter_data:
        plot_summary(scatter_data, out_dir)

    # Print summary table
    print('\n' + '=' * 70)
    print('ΔRDM cosine at LOCO-fitted params (post-hoc cross-validation)')
    print('=' * 70)
    for label, _, _, cos_val in scatter_data:
        print(f'  {label}: cos = {cos_val:+.4f}')
    print()


if __name__ == '__main__':
    main()
