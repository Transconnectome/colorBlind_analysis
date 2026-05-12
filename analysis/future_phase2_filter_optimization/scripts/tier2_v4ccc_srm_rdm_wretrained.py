"""tier2_v4ccc_srm_rdm_wretrained.py — V4-CCC + V1+V2 SRM RDM, wretrained simulator.

Loss: L_total = 1.0·L_ccc(V4) + 0.2·L_rdm(V1+V2 SRM avg) + 0.1·L_smooth

V4-CCC part: REUSE cached wretrained landscape from results/old_formula/sub-{08,09}_V4_V4ccc_landscape.json
V1+V2 SRM RDM part: wretrained ridge in SRM space per cell (LOCO procedure)

Output: results/CANDIDATE/tier2_v4ccc_srm_rdm/
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr, pearsonr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR.parent.parent / 'future_phase1_forward_model' / 'scripts'))

from utils_forward_model import HC_SUBJECTS, N_COLORS, HUE_ANGLES, create_basis_full, gcv_select_alpha, fit_W_ridge
from old_formula_refit import get_shifted_design_old, load_cvd_loco_target

_PHASE2 = _THIS_DIR.parent
SRC_V4CCC = _PHASE2 / 'results' / 'old_formula'
SRC_SRM = _PHASE2 / 'results' / 'diagnostics' / 'srm_precompute'
OUT = _PHASE2 / 'results' / 'CANDIDATE' / 'tier2_v4ccc_srm_rdm'
OUT.mkdir(parents=True, exist_ok=True)

WEIGHTS = {'alpha_ccc': 1.0, 'delta_rdm': 0.2, 'epsilon_smooth': 0.1}
NORM_SMOOTH = 32400.0
HC_POOL = ['01', '02', '03', '04', '05', '06', '07']
SUBJECTS = ['08', '09']
N_CHANNELS = 8


def ccc_value(sim, obs):
    sim = np.asarray(sim); obs = np.asarray(obs)
    if np.std(sim) < 1e-10 or np.std(obs) < 1e-10:
        return 0.0
    r, _ = pearsonr(sim, obs)
    if not np.isfinite(r):
        return 0.0
    msim = sim.mean(); mobs = obs.mean()
    ssim = sim.std(); sobs = obs.std()
    denom = ssim**2 + sobs**2 + (msim - mobs)**2
    if denom < 1e-10:
        return 0.0
    return 2.0 * r * ssim * sobs / denom


def rdm_vector(Y):
    """Y: (n_colors, n_features). Return upper-triangular pdist (correlation distance) -> (28,)."""
    return pdist(Y, metric='correlation')


def load_v4ccc_cells(sid):
    fn = SRC_V4CCC / f'sub-{sid}_V4_V4ccc_landscape.json'
    ls = json.load(open(fn))
    cells = ls if isinstance(ls, list) else ls.get('cells', ls)
    return cells


def load_srm_data(roi):
    """Returns: hc_aligned dict {HC_id: (8, K)}, rdm_hc_mean (28,)."""
    d = np.load(SRC_SRM / f'srm_{roi}.npz', allow_pickle=True)
    hc_aligned = {hc: d[f'hc_aligned_{hc}'] for hc in HC_POOL}
    rdm_hc_mean = d['rdm_hc_mean']
    return hc_aligned, rdm_hc_mean


def load_delta_rdm_obs(roi, sid):
    d = np.load(SRC_SRM / f'delta_rdm_obs_srm_{roi}.npz')
    return d[f'sub_{sid}']


def simulate_srm_loco(hc_aligned_pool, C_shifted):
    """For each HC in pool, run LOCO in SRM space with shifted design.

    hc_aligned_pool: dict {HC_id: (8 colors, K SRM features)}
    C_shifted: (8 colors, n_basis)

    Returns: mean RDM (28,) across HC pool after LOCO simulation.
    """
    N_RUNS = 6  # to match step1_fit_loco_v2 / utils_forward_model convention
    rdm_list = []
    for hc_id, Y_hc in hc_aligned_pool.items():
        # Y_hc: (8, K)
        # For each held-out color k:
        #   train ridge: C_shifted[non-k] -> Y_hc[non-k]  (shape (7, n_basis) -> (7, K))
        #   predict: y_pred_k = C_shifted[k] @ W (1, K)
        # After all k: Y_pred_hc (8, K)
        Y_pred = np.zeros_like(Y_hc)
        for k in range(N_COLORS):
            train_idx = [i for i in range(N_COLORS) if i != k]
            C_train = C_shifted[train_idx]   # (7, n_basis)
            Y_train = Y_hc[train_idx]        # (7, K)
            # ridge_gcv per SRM dim
            try:
                # Tile for ridge_gcv convention: it expects (N_RUNS * train_colors, ...)
                # Here we just use plain ridge with small alpha grid since small matrix
                C_t = np.tile(C_train, (N_RUNS, 1))
                Y_t = np.tile(Y_train, (N_RUNS, 1))
                alpha, _ = gcv_select_alpha(C_t, Y_t)
                W = fit_W_ridge(C_t, Y_t, alpha)
                # W: (n_basis, K)
                Y_pred[k] = C_shifted[k] @ W
            except Exception:
                Y_pred[k] = Y_hc.mean(axis=0)  # fallback
        rdm_list.append(rdm_vector(Y_pred))
    rdm_mean = np.mean(rdm_list, axis=0)
    return rdm_mean


def process_subject(sid):
    print(f'\n=== sub-{sid} ===', flush=True)
    t0 = time.time()

    # 1. Load V4-CCC cached landscape
    v4ccc_cells = load_v4ccc_cells(sid)
    print(f'  V4-CCC landscape: {len(v4ccc_cells)} cells', flush=True)

    # 2. Load SRM data
    hc_aligned_V1, rdm_hc_mean_V1 = load_srm_data('V1')
    hc_aligned_V2, rdm_hc_mean_V2 = load_srm_data('V2')
    delta_rdm_obs_V1 = load_delta_rdm_obs('V1', sid)
    delta_rdm_obs_V2 = load_delta_rdm_obs('V2', sid)
    print(f'  SRM data loaded (V1, V2)', flush=True)

    # 3. Process each cell
    out_cells = []
    n_total = len(v4ccc_cells)
    log_every = 100

    for i, cell in enumerate(v4ccc_cells):
        bs, bc = cell['bs'], cell['bc']
        # Reuse cached V4-CCC values
        l_ccc = cell['l_ccc']
        l_smooth = cell['l_smooth']
        spearman_r_V4 = cell['spearman_r']
        ccc_V4 = cell['ccc']

        # Compute SRM RDM for V1 and V2 at this cell
        C_shifted, dt = get_shifted_design_old(bs, bc)
        # Build basis-projected design (basis_type='fe')
        basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
        C_shifted_basis = basis_full[HUE_ANGLES + dt.astype(int).tolist() if False else
                                    (np.array(HUE_ANGLES) + dt).astype(int) % 360]

        # simulate SRM LOCO
        rdm_sim_V1 = simulate_srm_loco(hc_aligned_V1, C_shifted_basis)
        rdm_sim_V2 = simulate_srm_loco(hc_aligned_V2, C_shifted_basis)
        delta_rdm_sim_V1 = rdm_sim_V1 - rdm_hc_mean_V1
        delta_rdm_sim_V2 = rdm_sim_V2 - rdm_hc_mean_V2

        # Cosine similarity
        def cos_sim(a, b):
            an = np.linalg.norm(a); bn = np.linalg.norm(b)
            if an < 1e-10 or bn < 1e-10: return 0.0
            return float(np.dot(a, b) / (an * bn))

        cos_V1 = cos_sim(delta_rdm_sim_V1, delta_rdm_obs_V1)
        cos_V2 = cos_sim(delta_rdm_sim_V2, delta_rdm_obs_V2)
        cos_avg = (cos_V1 + cos_V2) / 2.0
        l_rdm = (1.0 - cos_avg) / 2.0

        l_total = (WEIGHTS['alpha_ccc'] * l_ccc
                   + WEIGHTS['delta_rdm'] * l_rdm
                   + WEIGHTS['epsilon_smooth'] * l_smooth)

        out_cells.append({
            'bs': float(bs), 'bc': float(bc),
            'l_ccc': float(l_ccc),
            'l_rdm_V1': float((1 - cos_V1) / 2),
            'l_rdm_V2': float((1 - cos_V2) / 2),
            'l_rdm_avg': float(l_rdm),
            'l_smooth': float(l_smooth),
            'l_total': float(l_total),
            'spearman_r': float(spearman_r_V4),
            'ccc': float(ccc_V4),
            'cos_V1': cos_V1,
            'cos_V2': cos_V2,
            'vuln_sim': cell['vuln_sim'],   # for downstream viz
        })

        if (i + 1) % log_every == 0 or i == n_total - 1:
            elapsed = time.time() - t0
            eta = elapsed / (i + 1) * (n_total - i - 1)
            print(f'  [{i+1}/{n_total}] best L_total so far: '
                  f'{min(c["l_total"] for c in out_cells):.4f}  '
                  f'elapsed={elapsed:.0f}s eta={eta:.0f}s', flush=True)

    # Save landscape
    out_path = OUT / f'sub-{sid}_V4_V4CCC_SRMRDM_landscape.json'
    with open(out_path, 'w') as f:
        json.dump(out_cells, f)
    print(f'  wrote {out_path.name}', flush=True)

    # Summary
    best = min(out_cells, key=lambda c: c['l_total'])
    summary = {
        'subject': sid,
        'loss': 'L = 1.0·L_ccc + 0.2·L_rdm(V1+V2 SRM) + 0.1·L_smooth',
        'simulator': 'wretrained (V4 cached, V1/V2 SRM-space LOCO retrained per cell)',
        'n_cells': n_total,
        'best': {
            'bs': best['bs'], 'bc': best['bc'],
            'norm': float(np.hypot(best['bs'], best['bc'])),
            'l_total': best['l_total'],
            'l_ccc': best['l_ccc'],
            'l_rdm_V1': best['l_rdm_V1'],
            'l_rdm_V2': best['l_rdm_V2'],
            'l_rdm_avg': best['l_rdm_avg'],
            'l_smooth': best['l_smooth'],
            'spearman_r_V4': best['spearman_r'],
            'ccc_V4': best['ccc'],
            'cos_V1': best['cos_V1'],
            'cos_V2': best['cos_V2'],
        },
        'elapsed_s': time.time() - t0,
    }
    summary_path = OUT / f'sub-{sid}_V4_V4CCC_SRMRDM_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'  wrote {summary_path.name}', flush=True)
    print(f'  BEST: β=({best["bs"]:.0f}, {best["bc"]:+.0f}), '
          f'L_total={best["l_total"]:.4f}, ρ_V4={best["spearman_r"]:.3f}', flush=True)

    return summary


def main():
    print(f'OUTDIR: {OUT}', flush=True)
    print(f'Subjects: {SUBJECTS}, HC pool: {HC_POOL}', flush=True)
    summaries = {}
    for sid in SUBJECTS:
        summaries[f'sub-{sid}'] = process_subject(sid)

    # Combined summary
    combined = {
        'date': '2026-05-12',
        'method': 'Tier 2: V4-CCC (wretrained, V4 LOCO) + V1+V2 SRM RDM (wretrained, SRM-space LOCO)',
        'loss': 'L_total = 1.0·L_ccc(V4) + 0.2·L_rdm(V1+V2 SRM avg) + 0.1·L_smooth',
        'weights': WEIGHTS,
        'subjects': summaries,
    }
    with open(OUT / 'tier2_summary.json', 'w') as f:
        json.dump(combined, f, indent=2)
    print(f'\nDone. Combined summary in tier2_summary.json', flush=True)


if __name__ == '__main__':
    main()
