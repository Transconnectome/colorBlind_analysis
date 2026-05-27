"""
S11 diagnostic round 2: Across iterations, where do atom argmins go?

For each of N_ITER iterations (sample 1 HC as 'CVD', sample 5 of remaining 6
as subset), compute:
  - γ_YG argmin (degenerate line — pick where on the line argmin lands)
  - RDM_V1 argmin (single attractor or migrating?)
  - RDM_V4 argmin (single attractor or migrating?)
  - composite z-sum argmin

Question: is the inter-iteration argmin variance dominated by ONE atom (e.g.
RDM_V1 has wide spread) or by all atoms together?
"""
import json
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import s10b_v3_extended as v3
from two_comp import forward_2comp, BS_GRID, BC_GRID
from behav_loss import load_jnd_per_pair, HC_JND_SUBJS
from neural_loss import load_amplitudes, load_hc_pool, ROI_K
from utils_forward_model import create_basis_full, HUE_ANGLES  # type: ignore

OUT_DIR = SCRIPT_DIR.parent / "results" / "s11_pre_phase_c_null_sim" / "diagnostic"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HC_ALL = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
N_ITER = 30  # subset of 50 for speed


def eval_grid(fn, family='deutan'):
    out = np.zeros((len(BS_GRID), len(BC_GRID)))
    for i, bs in enumerate(BS_GRID):
        for j, bc in enumerate(BC_GRID):
            try:
                v = float(fn(forward_2comp(bs, bc, family)))
                out[i, j] = v if np.isfinite(v) else np.nan
            except Exception:
                out[i, j] = np.nan
    return out


def argmin2d(grid):
    if np.all(np.isnan(grid)):
        return (np.nan, np.nan)
    idx = np.nanargmin(grid.ravel())
    i, j = np.unravel_index(idx, grid.shape)
    return float(BS_GRID[i]), float(BC_GRID[j])


def zscore(arr):
    arr = np.asarray(arr, dtype=float)
    mu = np.nanmean(arr); s = np.nanstd(arr)
    if not np.isfinite(s) or s < 1e-10:
        return np.full_like(arr, np.nan)
    return (arr - mu) / s


def main():
    print("S11 diagnostic 2: per-iteration atom argmin trajectories", flush=True)

    # Pre-load
    all_hc_amps = {}
    K_by_roi = {}
    C_by_roi = {}
    for hc in HC_ALL:
        all_hc_amps[hc] = {}
        for roi in v3.ROIS:
            try:
                all_hc_amps[hc][roi] = load_amplitudes(hc, roi)
            except Exception:
                pass
    for roi in v3.ROIS:
        K_by_roi[roi] = ROI_K[roi]
        C_by_roi[roi] = create_basis_full(K_by_roi[roi], basis_type='fe')[
            HUE_ANGLES.astype(int)]
    all_hc_jnd = {hc: load_jnd_per_pair(hc) for hc in HC_ALL}

    rng = np.random.default_rng(5678)
    records = []
    for it in range(N_ITER):
        # NOTE: original sim drew 1 random HC then SUBSET_SIZE=4 from remaining 6.
        # We re-run with same seed semantics.
        cvd = HC_ALL[rng.integers(0, len(HC_ALL))]
        pool = [h for h in HC_ALL if h != cvd]
        sel = sorted(rng.choice(len(pool), size=4, replace=False).tolist())
        subset = [pool[k] for k in sel]
        train_jnd_subjs = [h for h in subset if h in HC_JND_SUBJS]
        if not train_jnd_subjs:
            continue
        cvd_amps = {roi: all_hc_amps[cvd].get(roi) for roi in v3.ROIS}
        pool_amps = {roi: {h: all_hc_amps[h][roi] for h in subset
                            if roi in all_hc_amps[h]} for roi in v3.ROIS}
        if any(cvd_amps[r] is None for r in ['V1', 'V4']):
            continue
        # Atoms
        cvd_jnd = all_hc_jnd[cvd]
        fn_g = v3.make_gamma_pair_atom('YG', cvd_jnd, train_jnd_subjs)
        fn_v1 = v3.make_rdm_atom('V1', cvd_amps['V1'], pool_amps['V1'],
                                   C_by_roi['V1'], K_by_roi['V1'])
        fn_v4 = v3.make_rdm_atom('V4', cvd_amps['V4'], pool_amps['V4'],
                                   C_by_roi['V4'], K_by_roi['V4'])
        if fn_g is None or fn_v1 is None or fn_v4 is None:
            continue
        g_grid = eval_grid(fn_g)
        v1_grid = eval_grid(fn_v1)
        v4_grid = eval_grid(fn_v4)
        # Composite z
        zg = zscore(g_grid); zv1 = zscore(v1_grid); zv4 = zscore(v4_grid)
        comp = (zg + zv1 + zv4) / np.sqrt(3)

        rec = {
            'it': it, 'cvd': cvd, 'subset': subset,
            'gamma_argmin': argmin2d(g_grid),
            'rdm_v1_argmin': argmin2d(v1_grid),
            'rdm_v4_argmin': argmin2d(v4_grid),
            'composite_argmin': argmin2d(comp),
        }
        records.append(rec)
        print(f"[{it:02d}] cvd={cvd} subset={subset[:2]}... "
              f"γ={rec['gamma_argmin']} V1={rec['rdm_v1_argmin']} "
              f"V4={rec['rdm_v4_argmin']} comp={rec['composite_argmin']}", flush=True)

    # Summary: dispersion of each atom's argmin across iterations
    print("\n=== Across iterations, argmin dispersion ===", flush=True)
    for key in ['gamma_argmin', 'rdm_v1_argmin', 'rdm_v4_argmin', 'composite_argmin']:
        bs_arr = np.array([r[key][0] for r in records if np.isfinite(r[key][0])])
        bc_arr = np.array([r[key][1] for r in records if np.isfinite(r[key][1])])
        if len(bs_arr) == 0:
            continue
        print(f"  {key}: bs median={np.median(bs_arr):+.0f} IQR={np.percentile(bs_arr,75)-np.percentile(bs_arr,25):.0f} range=[{bs_arr.min():.0f},{bs_arr.max():.0f}]", flush=True)
        print(f"     {' '*len(key)}  bc median={np.median(bc_arr):+.0f} IQR={np.percentile(bc_arr,75)-np.percentile(bc_arr,25):.0f} range=[{bc_arr.min():.0f},{bc_arr.max():.0f}]", flush=True)
        # boundary rate
        bdy_bs = ((bs_arr == 0) | (bs_arr == 50)).mean()
        bdy_bc = ((bc_arr == -50) | (bc_arr == 50)).mean()
        print(f"     {' '*len(key)}  boundary rate: bs={bdy_bs*100:.0f}%, bc={bdy_bc*100:.0f}%", flush=True)

    out_path = OUT_DIR / 'diagnose_multi_iter.json'
    out_path.write_text(json.dumps({'n_iter': len(records), 'records': records},
                                    indent=2, default=str))
    print(f"\nSaved: {out_path}", flush=True)


if __name__ == '__main__':
    main()
