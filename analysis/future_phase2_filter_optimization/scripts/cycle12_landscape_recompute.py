#!/usr/bin/env python3
"""cycle12_landscape_recompute.py — Full V4+V1 per-cell landscape for cycle12 cross-ROI loss.

Loss formula (cycle12 cross-ROI, α=β=1.0):
    L_total(β_s, β_c) = α · l_topk(V4) + β · l_rank(V1) + λ · Tikh
where:
    l_topk(V4) = top-3 Jaccard distance on V4 LOCO vulnerability
    l_rank(V1) = (1 - Spearman_ρ(V1)) on V1 LOCO vulnerability
    Tikh      = (β_s / 80)^2 + (β_c / 60)^2
    α = β = 1.0, λ = 0.2

Per-cell stored: bs, bc, l_topk_V4, l_rank_V1, tikh, l_total,
                vuln_sim_V4 (8,), vuln_sim_V1 (8,).

Simulator: W-fixed (same as cached `sub-08_V4_landscape.json`). The task brief
said `simulate_mean_hc_loco_legacy` (wretrained) but:
  (a) The cycle12 cached argmins (68,−38) / (30,+26) quoted in the brief are
      W-fixed values (confirmed by composing l_topk + l_rank from cached
      landscapes and verifying argmin).
  (b) Wretrained simulator takes ~3.5h per (subj, ROI) — 4 sweeps would be
      ~14h, far exceeding the 1–2h budget.
  (c) W-fixed is the actual Phase 2 standard (per MEMORY and run_NxM.py).
We use W-fixed and additionally produce a cell-for-cell sanity check against
the cached scalar grids in results/cycles/ to confirm correctness.

Grid: β_s ∈ [0, 80] step 2, β_c ∈ [−60, 60] step 2 = 41×61 = 2501 cells.
(Extends the task-suggested 26×51 to ensure sub-08 (68,−38) is covered.)

Outputs (in results/fixedW_onlyTest/):
  - sub-08_V4V1_cycle12_landscape.json
  - sub-09_V4V1_cycle12_landscape.json
"""
from __future__ import annotations
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

_THIS = Path(__file__).resolve().parent
_PHASE2 = _THIS.parent
sys.path.insert(0, str(_THIS))
sys.path.insert(0, str(_THIS / 'older_cycles' / 'cycle_loss_redesign'))

# future_phase1_forward_model/scripts
_PROJ = _PHASE2.parent
sys.path.insert(0, str(_PROJ / 'future_phase1_forward_model' / 'scripts'))

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS, HUE_ANGLES,
    load_amplitudes, create_basis_full,
)
from step1_fit_loco_v2 import (
    precompute_hc_W, simulate_mean_hc_wfixed, load_cvd_loco_target,
)
from loss_redesign_smoke import compute_extended_loss, get_2component_design

LOCAL_DATA = (_PROJ / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')

# Cycle 12 / run_NxM.py used HC_SUBJECTS = 01..07 (sub-07 included for W precompute;
# sub-07 has no CVD LOCO target but is part of the HC training pool for CVD analysis).
# For CVD subjects there is no LOO drop, so the full 7-HC pool is used.
HC_POOL = ['01', '02', '03', '04', '05', '06', '07']
CVD_TYPE = {'08': 'deutan', '09': 'protan'}
ROIS = ('V4', 'V1')

ALPHA = 1.0
BETA = 1.0
LAM = 0.2
BS_MAX = 80.0
BC_MAX = 60.0
BS_STEP = 2.0
BC_STEP = 2.0


def make_grid():
    bs = np.arange(0.0, BS_MAX + 0.5 * BS_STEP, BS_STEP)
    bc = np.arange(-BC_MAX, BC_MAX + 0.5 * BC_STEP, BC_STEP)
    return bs, bc


def tikh_grid(bs, bc):
    BS, BC = np.meshgrid(bs, bc, indexing='ij')
    return (BS / BS_MAX) ** 2 + (BC / BC_MAX) ** 2


def precompute_pool(data_dir, roi):
    """Load HC amplitudes and precompute W per HC for this ROI."""
    hc_amps = {}
    for s in HC_POOL:
        hc_amps[s] = load_amplitudes(data_dir, s, roi)
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_orig = basis_full[HUE_ANGLES]
    hc_W, hc_alpha = precompute_hc_W(hc_amps, C_orig)
    return hc_amps, hc_W


def sweep_subject_roi(subj, roi, family, bs_arr, bc_arr, data_dir, log_every=400):
    """Return per-cell {l_topk_jaccard, l_rank, vuln_sim} arrays."""
    print(f'[{subj} {roi}] loading data and precomputing W ...')
    hc_amps, hc_W = precompute_pool(data_dir, roi)
    vuln_cvd = load_cvd_loco_target(subj, roi)
    print(f'[{subj} {roi}] vuln_cvd = {np.round(vuln_cvd, 3).tolist()}')

    n_bs, n_bc = len(bs_arr), len(bc_arr)
    n_cells = n_bs * n_bc
    l_topk = np.zeros((n_bs, n_bc), dtype=np.float64)
    l_rank = np.zeros((n_bs, n_bc), dtype=np.float64)
    vuln_grid = np.zeros((n_bs, n_bc, N_COLORS), dtype=np.float64)

    t0 = time.time()
    count = 0
    for i, bs in enumerate(bs_arr):
        for j, bc in enumerate(bc_arr):
            C_sh, _ = get_2component_design(float(bs), float(bc), family)
            vsim, _ = simulate_mean_hc_wfixed(hc_W, hc_amps, C_sh)
            metrics = compute_extended_loss(vsim, vuln_cvd)
            l_topk[i, j] = metrics['l_topk_jaccard']
            l_rank[i, j] = metrics['l_rank']
            vuln_grid[i, j, :] = vsim
            count += 1
            if count % log_every == 0:
                el = time.time() - t0
                eta = el / count * (n_cells - count)
                print(f'[{subj} {roi}] {count}/{n_cells} cells '
                      f'elapsed={el:.0f}s eta={eta:.0f}s')

    el = time.time() - t0
    print(f'[{subj} {roi}] done {n_cells} cells in {el:.1f}s '
          f'(mean {el / n_cells * 1000:.1f} ms/cell)')
    return {
        'l_topk_V4_or_roi': l_topk,
        'l_rank_V1_or_roi': l_rank,
        'vuln_sim': vuln_grid,
        'vuln_cvd': vuln_cvd,
    }


def sanity_check_against_cached(subj, roi, l_topk, l_rank):
    """Compare freshly computed l_topk / l_rank with cached landscape JSON."""
    p = _PHASE2 / 'results' / 'cycles' / f'sub-{subj}_{roi}_landscape.json'
    if not p.exists():
        print(f'[sanity] cached landscape {p.name} not found; skipping.')
        return None
    with open(p) as f:
        cached = json.load(f)
    cached_topk = np.array(cached['l_topk_jaccard'])
    cached_rank = np.array(cached['l_rank'])
    # Cached grid: bs 0..80 step 2 (41), bc -60..60 step 2 (61); same as ours.
    if cached_topk.shape != l_topk.shape:
        print(f'[sanity] shape mismatch: cached {cached_topk.shape} vs new {l_topk.shape}')
        return None
    max_topk = float(np.nanmax(np.abs(cached_topk - l_topk)))
    max_rank = float(np.nanmax(np.abs(cached_rank - l_rank)))
    print(f'[sanity] sub-{subj} {roi}: max|Δl_topk|={max_topk:.3e}, '
          f'max|Δl_rank|={max_rank:.3e}')
    return {'max_abs_dtopk': max_topk, 'max_abs_drank': max_rank}


def assemble_cycle12(v4_pack, v1_pack, bs_arr, bc_arr):
    """Combine V4 l_topk and V1 l_rank into L_total and find argmin."""
    Tikh = tikh_grid(bs_arr, bc_arr)
    g_topk_V4 = v4_pack['l_topk_V4_or_roi']
    g_rank_V1 = v1_pack['l_rank_V1_or_roi']
    L = ALPHA * g_topk_V4 + BETA * g_rank_V1 + LAM * Tikh
    idx = np.unravel_index(np.argmin(L), L.shape)
    return L, Tikh, idx


def save_landscape(subj, v4_pack, v1_pack, bs_arr, bc_arr, out_dir,
                   sanity_v4, sanity_v1):
    Tikh = tikh_grid(bs_arr, bc_arr)
    g_topk_V4 = v4_pack['l_topk_V4_or_roi']
    g_rank_V1 = v1_pack['l_rank_V1_or_roi']
    L_total = ALPHA * g_topk_V4 + BETA * g_rank_V1 + LAM * Tikh
    idx = np.unravel_index(np.argmin(L_total), L_total.shape)
    best = {
        'bs': float(bs_arr[idx[0]]),
        'bc': float(bc_arr[idx[1]]),
        'L_total': float(L_total[idx]),
        'l_topk_V4': float(g_topk_V4[idx]),
        'l_rank_V1': float(g_rank_V1[idx]),
        'tikh': float(LAM * Tikh[idx]),
        'vuln_sim_V4': v4_pack['vuln_sim'][idx[0], idx[1]].tolist(),
        'vuln_sim_V1': v1_pack['vuln_sim'][idx[0], idx[1]].tolist(),
    }
    cells = []
    n_bs, n_bc = L_total.shape
    for i in range(n_bs):
        for j in range(n_bc):
            cells.append({
                'bs': float(bs_arr[i]),
                'bc': float(bc_arr[j]),
                'l_topk_V4': float(g_topk_V4[i, j]),
                'l_rank_V1': float(g_rank_V1[i, j]),
                'tikh': float(LAM * Tikh[i, j]),
                'l_total': float(L_total[i, j]),
                'vuln_sim_V4': [float(x) for x in v4_pack['vuln_sim'][i, j]],
                'vuln_sim_V1': [float(x) for x in v1_pack['vuln_sim'][i, j]],
            })
    payload = {
        'meta': {
            'cycle': 12,
            'loss': ('L_total = alpha*l_topk(V4) + beta*l_rank(V1) '
                     '+ lambda*Tikh(β_s, β_c)'),
            'alpha': ALPHA,
            'beta': BETA,
            'lambda': LAM,
            'simulator': 'W-fixed (simulate_mean_hc_wfixed) — see script docstring',
            'tikh_normalization': '(β_s / 80)^2 + (β_c / 60)^2',
            'hc_pool': HC_POOL,
            'grid': {
                'bs': bs_arr.tolist(),
                'bc': bc_arr.tolist(),
                'shape': list(L_total.shape),
                'n_cells': int(L_total.size),
            },
            'roi_topk': 'V4',
            'roi_rank': 'V1',
            'cvd_type': CVD_TYPE[subj],
        },
        'sanity_check_vs_cached': {
            'V4': sanity_v4,
            'V1': sanity_v1,
        },
        'argmin': best,
        'vuln_cvd_V4': v4_pack['vuln_cvd'].tolist(),
        'vuln_cvd_V1': v1_pack['vuln_cvd'].tolist(),
        'cells': cells,
    }
    p = out_dir / f'sub-{subj}_V4V1_cycle12_landscape.json'
    with open(p, 'w') as f:
        json.dump(payload, f)
    print(f'[{subj}] wrote {p}')
    return best, L_total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subjects', nargs='+', default=['08', '09'])
    parser.add_argument('--data_dir', default=str(LOCAL_DATA))
    parser.add_argument('--output_dir',
                        default=str(_PHASE2 / 'results' / 'fixedW_onlyTest'))
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir = Path(args.data_dir)

    bs_arr, bc_arr = make_grid()
    print(f'[grid] bs={bs_arr.min()}..{bs_arr.max()} step {BS_STEP} '
          f'({len(bs_arr)} pts); '
          f'bc={bc_arr.min()}..{bc_arr.max()} step {BC_STEP} '
          f'({len(bc_arr)} pts); total={len(bs_arr) * len(bc_arr)} cells')

    summary = {}
    for subj in args.subjects:
        family = CVD_TYPE[subj]
        print(f'\n=== sub-{subj} ({family}) ===')

        v4_pack = sweep_subject_roi(subj, 'V4', family, bs_arr, bc_arr, data_dir)
        sanity_v4 = sanity_check_against_cached(
            subj, 'V4',
            v4_pack['l_topk_V4_or_roi'],
            v4_pack['l_rank_V1_or_roi'],
        )

        v1_pack = sweep_subject_roi(subj, 'V1', family, bs_arr, bc_arr, data_dir)
        sanity_v1 = sanity_check_against_cached(
            subj, 'V1',
            v1_pack['l_topk_V4_or_roi'],
            v1_pack['l_rank_V1_or_roi'],
        )

        best, L_total = save_landscape(
            subj, v4_pack, v1_pack, bs_arr, bc_arr, out_dir,
            sanity_v4, sanity_v1,
        )
        summary[subj] = {
            'best': best,
            'l_total_min': float(L_total.min()),
            'l_total_max': float(L_total.max()),
            'l_total_median': float(np.median(L_total)),
        }
        print(f'[{subj}] cycle12 argmin: '
              f'(β_s={best["bs"]:.0f}, β_c={best["bc"]:+.0f}) '
              f'L_total={best["L_total"]:.4f} '
              f'l_topk_V4={best["l_topk_V4"]:.4f} '
              f'l_rank_V1={best["l_rank_V1"]:.4f} '
              f'tikh={best["tikh"]:.4f}')

    with open(out_dir / 'cycle12_landscape_recompute_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print('\n[done]')


if __name__ == '__main__':
    main()
