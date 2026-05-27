"""
S11 diagnostic: Root cause analysis of 2-comp null non-recovery.

For sub-08 C1 candidate (γYG | RDMV1+V4 | noLOCO):
- H2: Is L_γYG(β_s, β_c) a degenerate line (single-pair atom)?
- H3: Is L_RDM_V1 / L_RDM_V4 unimodal or bimodal?
- H4: Does z-scoring + summing create bimodal attractor where individual atoms are unimodal?

Approach:
1. Mathematical/analytic verification of H2 (γYG degeneracy).
2. Empirically compute atom landscapes for one fixed iteration (subset of 5 HCs,
   sub-08 as 'CVD').  Save heatmaps and 1D slices.
3. Test composite formation: z-score sum vs raw sum.

Outputs to: results/s11_pre_phase_c_null_sim/diagnostic/
"""
import json
import sys
from pathlib import Path

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import s10b_v3_extended as v3
from two_comp import forward_2comp, BS_GRID, BC_GRID
from behav_loss import load_jnd_per_pair, HC_JND_SUBJS, PAIR_HUES
from neural_loss import load_amplitudes, load_hc_pool, ROI_K

OUT_DIR = SCRIPT_DIR.parent / "results" / "s11_pre_phase_c_null_sim" / "diagnostic"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HC_ALL = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']

# Reproducibility: same seed as v1 sim, but use only 1 iteration
rng = np.random.default_rng(5678)


def evaluate_atom_grid(atom_fn, family='deutan'):
    """Return (26, 51) loss grid for atom_fn over (β_s, β_c)."""
    out = np.zeros((len(BS_GRID), len(BC_GRID)))
    for i, bs in enumerate(BS_GRID):
        for j, bc in enumerate(BC_GRID):
            delta = forward_2comp(bs, bc, family)
            try:
                v = float(atom_fn(delta))
                out[i, j] = v if np.isfinite(v) else np.nan
            except Exception:
                out[i, j] = np.nan
    return out


def zscore(arr):
    arr = np.asarray(arr, dtype=float)
    mu = np.nanmean(arr); s = np.nanstd(arr)
    if not np.isfinite(s) or s < 1e-10:
        return np.full_like(arr, np.nan)
    return (arr - mu) / s


def landscape_summary(grid, name):
    """Return dict: argmin, valley topology, etc."""
    if np.all(np.isnan(grid)):
        return {'name': name, 'all_nan': True}
    flat = grid.ravel()
    flat_idx = np.nanargmin(flat)
    i, j = np.unravel_index(flat_idx, grid.shape)
    # find all cells within 5% of best loss
    best = float(grid[i, j])
    rng_l = float(np.nanmax(grid) - best)
    near_best_mask = (grid - best) <= 0.05 * rng_l
    near_best_count = int(np.sum(near_best_mask))
    return {
        'name': name,
        'argmin_bs': float(BS_GRID[i]),
        'argmin_bc': float(BC_GRID[j]),
        'argmin_value': best,
        'loss_at_zero': float(grid[0, np.searchsorted(BC_GRID, 0.0)]),
        'loss_range': rng_l,
        'near_best_pct_of_grid': near_best_count / grid.size * 100,
        'boundary_argmin': bool(i == 0 or i == len(BS_GRID) - 1 or
                                j == 0 or j == len(BC_GRID) - 1),
    }


def main():
    print("=" * 100, flush=True)
    print("S11 diagnostic: 2-comp null non-recovery root cause", flush=True)
    print("=" * 100, flush=True)

    # ---------- H2: γYG single-pair atom analytic ----------
    print("\n[H2] γYG single-pair atom degeneracy", flush=True)
    # γ_YG forward: depends only on δθ[c2] (yellow=90°, i=2) and δθ[c3] (green=135°, j=3).
    # forward_2comp at hue θ: β_s·cos(θ−90°) + β_c·cos(θ−150°) for deutan.
    # At θ=90: cos(0)·β_s + cos(−60°)·β_c = β_s + 0.5·β_c
    # At θ=135: cos(45°)·β_s + cos(−15°)·β_c = 0.707·β_s + 0.966·β_c
    # δθ_YG := δθ[c3] - δθ[c2] = (0.707-1)·β_s + (0.966-0.5)·β_c
    #                          = -0.293·β_s + 0.466·β_c
    # So γYG depends on a *single* linear combination of (β_s, β_c).
    # The level set is a 1-D line in (β_s, β_c) space ⇒ degenerate.
    c2_bs = np.cos(np.deg2rad(90 - 90))   # 1
    c2_bc = np.cos(np.deg2rad(90 - 150))  # 0.5
    c3_bs = np.cos(np.deg2rad(135 - 90))  # 0.707
    c3_bc = np.cos(np.deg2rad(135 - 150))  # 0.966
    a = c3_bs - c2_bs
    b = c3_bc - c2_bc
    print(f"  δθ[c3]−δθ[c2] = {a:.3f}·β_s + {b:.3f}·β_c", flush=True)
    print(f"  Slope of level set in (β_s, β_c): β_c = -({a:.3f}/{b:.3f})·β_s "
          f"= {-a/b:+.3f}·β_s", flush=True)
    print("  ⇒ γYG atom encodes ONE linear combination of (β_s, β_c).", flush=True)
    print("  ⇒ Level set is a LINE, not a point. H2 = CONFIRMED a priori.", flush=True)

    # ---------- Empirical: pick one fixed iteration ----------
    print("\n[Setup] Pick fixed iteration: 'CVD' = sub-04 (median voxel count),"
          " pool = remaining 6 HCs, 5 sampled.", flush=True)
    cvd_id = 'sub-04'  # fixed
    pool_hcs = [h for h in HC_ALL if h != cvd_id]
    rng_local = np.random.default_rng(5678)
    sel = sorted(rng_local.choice(len(pool_hcs), size=5, replace=False).tolist())
    subset = [pool_hcs[i] for i in sel]
    print(f"  CVD='{cvd_id}' (left out); subset = {subset}", flush=True)

    # Load amps and JND
    cvd_amps = {}
    pool_amps = {}
    K_by_roi = {}
    from utils_forward_model import create_basis_full, HUE_ANGLES  # type: ignore
    C_by_roi = {}
    for roi in v3.ROIS:
        try:
            cvd_amps[roi] = load_amplitudes(cvd_id, roi)
            K_by_roi[roi] = ROI_K[roi]
            C_by_roi[roi] = create_basis_full(K_by_roi[roi], basis_type='fe')[
                HUE_ANGLES.astype(int)]
            full_pool = load_hc_pool(roi)
            pool_amps[roi] = {h: full_pool[h] for h in subset if h in full_pool}
        except Exception as e:
            print(f"  skip {roi}: {e}", flush=True)
    cvd_jnd = load_jnd_per_pair(cvd_id)

    # Build atoms (focus on C1 = γYG + RDMV1 + RDMV4)
    print("\n[Build atoms] γYG, RDM_V1, RDM_V4", flush=True)
    train_jnd_subjs = [h for h in subset if h in HC_JND_SUBJS]
    print(f"  train_jnd_subjs: {train_jnd_subjs}", flush=True)
    fn_g = v3.make_gamma_pair_atom('YG', cvd_jnd, train_jnd_subjs)
    fn_r_v1 = v3.make_rdm_atom('V1', cvd_amps['V1'], pool_amps['V1'],
                                 C_by_roi['V1'], K_by_roi['V1'])
    fn_r_v4 = v3.make_rdm_atom('V4', cvd_amps['V4'], pool_amps['V4'],
                                 C_by_roi['V4'], K_by_roi['V4'])
    if fn_g is None or fn_r_v1 is None or fn_r_v4 is None:
        print("  Some atom is None; aborting.", flush=True)
        return

    # Compute atom landscapes
    print("\n[Compute atom landscapes over (β_s, β_c)]", flush=True)
    g_grid = evaluate_atom_grid(fn_g)
    rv1_grid = evaluate_atom_grid(fn_r_v1)
    rv4_grid = evaluate_atom_grid(fn_r_v4)

    # Sanity report
    g_summ = landscape_summary(g_grid, 'γ_YG')
    rv1_summ = landscape_summary(rv1_grid, 'RDM_V1')
    rv4_summ = landscape_summary(rv4_grid, 'RDM_V4')
    print("  γ_YG argmin: bs={:.0f}, bc={:.0f}, value={:.3g}, boundary={}".format(
        g_summ['argmin_bs'], g_summ['argmin_bc'], g_summ['argmin_value'], g_summ['boundary_argmin']), flush=True)
    print("  RDM_V1 argmin: bs={:.0f}, bc={:.0f}, value={:.3g}, boundary={}".format(
        rv1_summ['argmin_bs'], rv1_summ['argmin_bc'], rv1_summ['argmin_value'], rv1_summ['boundary_argmin']), flush=True)
    print("  RDM_V4 argmin: bs={:.0f}, bc={:.0f}, value={:.3g}, boundary={}".format(
        rv4_summ['argmin_bs'], rv4_summ['argmin_bc'], rv4_summ['argmin_value'], rv4_summ['boundary_argmin']), flush=True)
    print("  Near-best (top 5% by loss) fraction of grid:", flush=True)
    print("    γ_YG: {:.1f}% — expect HIGH (degenerate line)".format(g_summ['near_best_pct_of_grid']), flush=True)
    print("    RDM_V1: {:.1f}%".format(rv1_summ['near_best_pct_of_grid']), flush=True)
    print("    RDM_V4: {:.1f}%".format(rv4_summ['near_best_pct_of_grid']), flush=True)

    # Composite: z-score sum / sqrt(n_atoms)
    print("\n[Composite landscapes]", flush=True)
    z_g = zscore(g_grid); z_rv1 = zscore(rv1_grid); z_rv4 = zscore(rv4_grid)
    composite_z = (z_g + z_rv1 + z_rv4) / np.sqrt(3)
    comp_z_summ = landscape_summary(composite_z, 'composite_z')
    print("  Z-composite argmin: bs={:.0f}, bc={:.0f}, value={:.3g}, boundary={}".format(
        comp_z_summ['argmin_bs'], comp_z_summ['argmin_bc'], comp_z_summ['argmin_value'],
        comp_z_summ['boundary_argmin']), flush=True)

    # Raw composite (no z-scoring; normalize by atom-specific mean abs to keep
    # similar magnitudes)
    g_raw_norm = g_grid / np.nanmean(np.abs(g_grid))
    rv1_raw_norm = rv1_grid / np.nanmean(np.abs(rv1_grid))
    rv4_raw_norm = rv4_grid / np.nanmean(np.abs(rv4_grid))
    composite_raw = g_raw_norm + rv1_raw_norm + rv4_raw_norm
    comp_raw_summ = landscape_summary(composite_raw, 'composite_raw_norm')
    print("  Raw-composite argmin: bs={:.0f}, bc={:.0f}, value={:.3g}, boundary={}".format(
        comp_raw_summ['argmin_bs'], comp_raw_summ['argmin_bc'], comp_raw_summ['argmin_value'],
        comp_raw_summ['boundary_argmin']), flush=True)

    # ---------- Bimodality test: find local minima count in composite ----------
    def count_local_minima(grid, eps=1e-9):
        H, W = grid.shape
        count = 0
        mins = []
        for i in range(1, H - 1):
            for j in range(1, W - 1):
                v = grid[i, j]
                if not np.isfinite(v):
                    continue
                neighbors = [grid[i-1, j], grid[i+1, j], grid[i, j-1], grid[i, j+1],
                              grid[i-1, j-1], grid[i-1, j+1], grid[i+1, j-1], grid[i+1, j+1]]
                if all(np.isfinite(n) and v <= n + eps for n in neighbors):
                    count += 1
                    mins.append((BS_GRID[i], BC_GRID[j], v))
        return count, mins

    n_min_z, mins_z = count_local_minima(composite_z)
    n_min_raw, mins_raw = count_local_minima(composite_raw)
    print(f"\n[Bimodality] z-composite: {n_min_z} local minima", flush=True)
    for bs, bc, v in mins_z[:10]:
        print(f"    ({bs:+.0f}, {bc:+.0f}): {v:.3g}", flush=True)
    print(f"[Bimodality] raw-composite: {n_min_raw} local minima", flush=True)
    for bs, bc, v in mins_raw[:10]:
        print(f"    ({bs:+.0f}, {bc:+.0f}): {v:.3g}", flush=True)

    # ---------- Save full grids for plotting ----------
    out = {
        'config': {
            'cvd': cvd_id, 'subset': subset, 'family': 'deutan',
            'atoms': ['gamma_YG', 'rdm_V1', 'rdm_V4'],
        },
        'H2_analytic': {
            'slope_a': float(a), 'slope_b': float(b),
            'bc_slope_per_bs': float(-a / b),
            'note': 'γ_YG depends only on (a·β_s + b·β_c); level set is a line.',
        },
        'atom_summary': {'gamma_YG': g_summ, 'rdm_V1': rv1_summ, 'rdm_V4': rv4_summ},
        'composite_summary': {'z_score': comp_z_summ, 'raw_norm': comp_raw_summ},
        'local_minima': {
            'z_composite_count': n_min_z,
            'raw_composite_count': n_min_raw,
            'z_composite_top': [{'bs': float(b1), 'bc': float(b2), 'value': float(v)}
                                  for b1, b2, v in mins_z[:10]],
            'raw_composite_top': [{'bs': float(b1), 'bc': float(b2), 'value': float(v)}
                                    for b1, b2, v in mins_raw[:10]],
        },
    }
    out_path = OUT_DIR / 'diagnose_landscape.json'
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved: {out_path}", flush=True)

    # Save grids as npz
    grids_path = OUT_DIR / 'diagnose_grids.npz'
    np.savez(grids_path,
             gamma_YG=g_grid, rdm_V1=rv1_grid, rdm_V4=rv4_grid,
             composite_z=composite_z, composite_raw=composite_raw,
             BS_GRID=BS_GRID, BC_GRID=BC_GRID)
    print(f"Saved grids: {grids_path}", flush=True)


if __name__ == '__main__':
    main()
