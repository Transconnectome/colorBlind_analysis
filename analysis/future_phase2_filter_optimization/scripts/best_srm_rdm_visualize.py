"""best_srm_rdm_visualize.py — V1/V2 SRM RDM visualization at BEST argmin.

For each subject (sub-08, sub-09) × ROI (V1, V2):
  - Observed ΔRDM (28-element) as 8x8 heatmap
  - Simulated ΔRDM at BEST argmin
  - Cosine similarity annotation
  - Pair-by-pair scatter

Output: results/BEST_srm_rdm_combined.png  (2x2 subject×ROI grid)
        results/BEST_srm_rdm_sub-{08,09}_V{1,2}.png  (per-subject-ROI detail)
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.distance import squareform
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

_PHASE2 = _THIS_DIR.parent
SRC_SRM = _PHASE2 / 'results' / 'diagnostics' / 'srm_precompute'
SRC_TIER2 = _PHASE2 / 'results' / 'CANDIDATE' / 'tier2_v4ccc_srm_rdm'
OUT = _PHASE2 / 'results'

# BEST argmins
BEST = {
    '08': {'cvd_type': 'deutan', 'color': '#E07B2C', 'bs': 44.0, 'bc': 28.0},
    '09': {'cvd_type': 'protan', 'color': '#2D8E8B', 'bs': 30.0, 'bc': 46.0},
}
HUE_LABELS = ['R', 'O', 'Y', 'G', 'C', 'B', 'P', 'M']

matplotlib.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'],
    'font.size': 7, 'axes.titlesize': 8, 'axes.labelsize': 7,
})


def find_cell_at(cells, bs_target, bc_target, tol=0.5):
    for c in cells:
        if abs(c['bs'] - bs_target) < tol and abs(c['bc'] - bc_target) < tol:
            return c
    raise ValueError(f'cell ({bs_target}, {bc_target}) not in landscape')


def load_delta_rdm_obs(roi, sid):
    d = np.load(SRC_SRM / f'delta_rdm_obs_srm_{roi}.npz')
    return d[f'sub_{sid}']  # (28,) upper triangular


def load_tier2_cell(sid, bs_target, bc_target):
    """Load Tier 2 landscape cell at given (bs, bc) — has cos_V1, cos_V2."""
    fn = SRC_TIER2 / f'sub-{sid}_V4_V4CCC_SRMRDM_landscape.json'
    cells = json.load(open(fn))
    return find_cell_at(cells, bs_target, bc_target)


def compute_delta_rdm_sim(sid, roi, bs_target, bc_target):
    """Reconstruct ΔRDM_sim at BEST argmin using same logic as tier2 runner.

    Quick approximation: use the cos_V1/cos_V2 stored, but for visualization
    we need the full 28-vector. We don't have ΔRDM_sim cached directly.

    Alternative: rerun the simulation here using SRM data + the cached recipe.
    """
    from scipy.spatial.distance import pdist

    # Load SRM precompute
    d = np.load(SRC_SRM / f'srm_{roi}.npz', allow_pickle=True)
    HC_POOL = ['01', '02', '03', '04', '05', '06', '07']
    hc_aligned = {hc: d[f'hc_aligned_{hc}'] for hc in HC_POOL}
    rdm_hc_mean = d['rdm_hc_mean']

    # Forward model imports
    sys.path.insert(0, str(_THIS_DIR.parent.parent / 'future_phase1_forward_model' / 'scripts'))
    from utils_forward_model import create_basis_full, gcv_select_alpha, fit_W_ridge, HUE_ANGLES, N_COLORS
    from old_formula_refit import get_shifted_design_old

    # Generate shifted design (same as tier2 runner)
    _, dt = get_shifted_design_old(bs_target, bc_target)
    N_CHANNELS = 8
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    shifted_angles = (np.array(HUE_ANGLES) + dt).astype(int) % 360
    C_shifted = basis_full[shifted_angles]   # (8, n_basis)

    N_RUNS = 6
    rdm_list = []
    for hc_id in HC_POOL:
        Y_hc = hc_aligned[hc_id]   # (8, K=4)
        Y_pred = np.zeros_like(Y_hc)
        for k in range(N_COLORS):
            train_idx = [i for i in range(N_COLORS) if i != k]
            C_train = C_shifted[train_idx]
            Y_train = Y_hc[train_idx]
            try:
                C_t = np.tile(C_train, (N_RUNS, 1))
                Y_t = np.tile(Y_train, (N_RUNS, 1))
                alpha, _ = gcv_select_alpha(C_t, Y_t)
                W = fit_W_ridge(C_t, Y_t, alpha)
                Y_pred[k] = C_shifted[k] @ W
            except Exception:
                Y_pred[k] = Y_hc.mean(axis=0)
        rdm_list.append(pdist(Y_pred, metric='correlation'))
    rdm_sim = np.mean(rdm_list, axis=0)
    delta_rdm_sim = rdm_sim - rdm_hc_mean
    return delta_rdm_sim, rdm_hc_mean, rdm_sim


def render_subject_roi(sid, roi, ax_obs, ax_sim, ax_delta, ax_scatter, cos_val):
    info = BEST[sid]
    bs, bc = info['bs'], info['bc']
    cvd_type = info['cvd_type']
    color = info['color']

    # Observed
    obs = load_delta_rdm_obs(roi, sid)
    obs_mat = squareform(obs)  # (8, 8)

    # Simulated
    delta_sim, rdm_hc_mean, rdm_sim = compute_delta_rdm_sim(sid, roi, bs, bc)
    sim_mat = squareform(delta_sim)

    # Symmetric colormap range
    vlim = max(np.abs(obs_mat).max(), np.abs(sim_mat).max())

    # L2-normalized disagreement — aligns visual with cosine intuition
    # cos = obs_unit · sim_unit (dot product after L2 normalization)
    # max possible |obs_unit - sim_unit| = sqrt(2) ≈ 1.41 when cos=-1
    # at cos=+1: zero disagreement
    obs_norm_l2 = obs / (np.linalg.norm(obs) + 1e-12)
    sim_norm_l2 = delta_sim / (np.linalg.norm(delta_sim) + 1e-12)
    diff_norm = obs_norm_l2 - sim_norm_l2
    diff_norm_mat = squareform(diff_norm)   # (8, 8)
    # Color scale: ±sqrt(2)/sqrt(N) approximates typical per-element diff
    # Use ±0.4 fixed scale so cos values across subjects directly comparable
    vlim_norm = 0.4
    rmsd = float(np.sqrt(np.mean((obs - delta_sim) ** 2)))

    # Heatmaps
    im_obs = ax_obs.imshow(obs_mat, cmap='RdBu_r', vmin=-vlim, vmax=vlim, aspect='equal')
    ax_obs.set_xticks(range(8)); ax_obs.set_xticklabels(HUE_LABELS, fontsize=6)
    ax_obs.set_yticks(range(8)); ax_obs.set_yticklabels(HUE_LABELS, fontsize=6)
    ax_obs.set_title(f'sub-{sid} {cvd_type} {roi}\nObserved ΔRDM',
                     color=color, fontweight='bold', fontsize=8)

    ax_sim.imshow(sim_mat, cmap='RdBu_r', vmin=-vlim, vmax=vlim, aspect='equal')
    ax_sim.set_xticks(range(8)); ax_sim.set_xticklabels(HUE_LABELS, fontsize=6)
    ax_sim.set_yticks(range(8)); ax_sim.set_yticklabels(HUE_LABELS, fontsize=6)
    ax_sim.set_title(f'Simulated ΔRDM @ BEST (β={bs:.0f},{bc:+.0f})\ncos={cos_val:+.3f}',
                     color=color, fontweight='bold', fontsize=8)

    # L2-normalized disagreement: shows DIRECTION mismatch aligned with cosine
    ax_delta.imshow(diff_norm_mat, cmap='PuOr_r',
                    vmin=-vlim_norm, vmax=vlim_norm, aspect='equal')
    ax_delta.set_xticks(range(8)); ax_delta.set_xticklabels(HUE_LABELS, fontsize=6)
    ax_delta.set_yticks(range(8)); ax_delta.set_yticklabels(HUE_LABELS, fontsize=6)
    max_norm_diff = float(np.abs(diff_norm).max())
    ax_delta.set_title(f'L2-norm disagreement (cosine-aligned)\n'
                       f'cos={cos_val:+.3f}  RMSD_raw={rmsd:.3f}\n'
                       f'max|Δ_norm|={max_norm_diff:.3f}  scale=±0.4',
                       color=color, fontweight='bold', fontsize=7.5)

    # Scatter obs vs sim
    ax_scatter.scatter(obs, delta_sim, s=20, color=color, alpha=0.7, edgecolor='black', lw=0.3)
    lo = min(obs.min(), delta_sim.min())
    hi = max(obs.max(), delta_sim.max())
    ax_scatter.plot([lo, hi], [lo, hi], 'k--', lw=0.5, alpha=0.5, label='y=x')
    ax_scatter.set_xlabel(f'ΔRDM_obs {roi}', fontsize=7)
    ax_scatter.set_ylabel(f'ΔRDM_sim {roi}', fontsize=7)
    ax_scatter.set_title(f'obs vs sim scatter\ncos={cos_val:+.3f}', fontsize=8, fontweight='bold')
    ax_scatter.axhline(0, color='gray', lw=0.3); ax_scatter.axvline(0, color='gray', lw=0.3)
    ax_scatter.grid(alpha=0.3)

    return im_obs, vlim


def main():
    print(f'BEST argmins: {BEST}')

    # Combined 2 subjects × 2 ROIs × 4 panels (obs, sim, delta, scatter)
    fig, axes = plt.subplots(4, 4, figsize=(14, 13), dpi=150)
    fig.suptitle('V1/V2 SRM RDM at BEST argmin (V4-CCC + l_topk wretrained)\n'
                 'Panel: Observed ΔRDM | Simulated ΔRDM | (obs−sim) discrepancy | scatter',
                 fontsize=11, fontweight='bold', y=0.998)

    cos_summary = {}
    row = 0
    for sid in ['08', '09']:
        cos_summary[sid] = {}
        info = BEST[sid]
        cell = load_tier2_cell(sid, info['bs'], info['bc'])
        cos_summary[sid]['cos_V1'] = cell['cos_V1']
        cos_summary[sid]['cos_V2'] = cell['cos_V2']

        for roi in ['V1', 'V2']:
            cos_val = cell[f'cos_{roi}']
            render_subject_roi(sid, roi,
                               axes[row, 0], axes[row, 1], axes[row, 2], axes[row, 3],
                               cos_val)
            print(f'  sub-{sid} {roi}: cos = {cos_val:+.3f}')
            row += 1

    plt.tight_layout()
    out_combined = OUT / 'BEST_srm_rdm_combined.png'
    plt.savefig(out_combined, dpi=150, bbox_inches='tight')
    plt.savefig(str(out_combined).replace('.png', '.pdf'), bbox_inches='tight')
    plt.close()
    print(f'\nwrote {out_combined.name} (+ pdf)')

    # Per-subject-ROI standalone
    for sid in ['08', '09']:
        info = BEST[sid]
        cell = load_tier2_cell(sid, info['bs'], info['bc'])
        for roi in ['V1', 'V2']:
            cos_val = cell[f'cos_{roi}']
            fig, axes = plt.subplots(1, 4, figsize=(14, 3.5), dpi=150)
            render_subject_roi(sid, roi,
                               axes[0], axes[1], axes[2], axes[3], cos_val)
            plt.tight_layout()
            out = OUT / f'BEST_srm_rdm_sub-{sid}_{roi}.png'
            plt.savefig(out, dpi=150, bbox_inches='tight')
            plt.savefig(str(out).replace('.png', '.pdf'), bbox_inches='tight')
            plt.close()
            print(f'wrote {out.name} (+ pdf)')

    # Update BEST_summary.json with SRM RDM cos values
    bs_summary_path = OUT / 'BEST_summary.json'
    if bs_summary_path.exists():
        with open(bs_summary_path) as f:
            bs_summary = json.load(f)
        for sid in ['08', '09']:
            sk = f'sub-{sid}'
            if sk in bs_summary.get('subjects', {}):
                bs_summary['subjects'][sk]['srm_rdm'] = {
                    'cos_V1': cos_summary[sid]['cos_V1'],
                    'cos_V2': cos_summary[sid]['cos_V2'],
                    'l_rdm_V1': (1 - cos_summary[sid]['cos_V1']) / 2,
                    'l_rdm_V2': (1 - cos_summary[sid]['cos_V2']) / 2,
                }
        with open(bs_summary_path, 'w') as f:
            json.dump(bs_summary, f, indent=2)
        print(f'updated {bs_summary_path.name} with srm_rdm cos values')

    print('\n=== SRM RDM cos summary at BEST argmin ===')
    for sid in ['08', '09']:
        print(f"  sub-{sid}: cos_V1={cos_summary[sid]['cos_V1']:+.3f}  "
              f"cos_V2={cos_summary[sid]['cos_V2']:+.3f}")


if __name__ == '__main__':
    main()
