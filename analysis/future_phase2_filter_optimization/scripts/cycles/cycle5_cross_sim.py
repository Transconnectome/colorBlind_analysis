#!/usr/bin/env python3
"""cycle5_cross_sim.py — Plan 04 Cycle 5 Task 2: cross-simulator robustness.

가설:
  V4 + l_topk + Tikh 의 sub-08 specificity 가 simulator 모델 (2-component, R+C,
  Machado_1way) 무관하게 robust 하면 "set-match is signal, parameters are noise"
  framing 이 검증된다. 변동 < 1.0 → robust. > 1.5 → simulator-conditional.

설계:
  - sub-08 + 6 HC × V4 = 7 fits / simulator. 3 simulator → 21 fits.
  - 2-comp: cycle1 landscape 재사용 (l_topk_jaccard grid + λ·norm_grid).
  - R+C: (Δλ, g) grid Δλ ∈ [0,30] step 1, g ∈ [-3,3] step 0.1 = 31×61=1891 pt.
  - Machado: Δλ ∈ [0,30] step 0.5, family=deutan = 61 pt.
  - λ_tikh=0.2 (cycle3 권장). 정규화:
      2-comp: (β_s/80)² + (β_c/60)²
      R+C   : (Δλ/30)² + (g/3)²
      Mach  : (Δλ/30)²

출력:
  results/cycles/cycle5_cross_sim_aggregate.json
  - simulator × subject: best l_topk + Tikh, ρ@best, best params, raw l_topk
  - sub-08 z (vs HC pool 6) per simulator
  - 변동성: max(z) - min(z), max(value) - min(value)
"""

import json
import sys
import time
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr, pearsonr

_HERE = Path(__file__).resolve().parent
_PHASE2 = _HERE.parent.parent
_PROJ = _PHASE2.parent.parent
sys.path.insert(0, str(_PHASE2 / 'scripts'))
sys.path.insert(0, str(_PHASE2 / 'scripts' / 'older_cycles/cycle_loss_redesign'))

_FWD = _PROJ / 'analysis' / 'future_phase1_forward_model' / 'scripts'
sys.path.insert(0, str(_FWD))

from utils_forward_model import (
    HC_SUBJECTS, N_CHANNELS, N_RUNS, N_COLORS, HUE_ANGLES,
    load_amplitudes, create_basis_full,
)
from step1_fit_loco_v2 import (
    simulate_mean_hc_wfixed, precompute_hc_W, load_cvd_loco_target,
)
from loss_redesign_smoke import get_2component_design
from utils_distortion_models import get_design_matrix
from retinal_cortical import get_design_matrix_rc

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}
LOCAL_DATA = (_PROJ / 'analysis' / 'phase1_procrustes_decoding' / 'results'
              / 'visualization' / 'full_dataset_C010_with_residuals')

ROI = 'V4'
HC_SUBS = ['01', '02', '03', '04', '05', '06']
TARGET_CVD = '08'
LAM_TIKH = 0.2


def family_for_subj(s):
    if s in CVD_TYPE:
        f = CVD_TYPE[s]
        return 'deutan' if f == 'normal' else f
    return 'deutan'


def l_topk_jaccard(vsim, vcvd, k=3):
    s = np.asarray(vsim, dtype=float)
    c = np.asarray(vcvd, dtype=float)
    top_s = set(np.argsort(s)[:k].tolist())
    top_c = set(np.argsort(c)[:k].tolist())
    inter = len(top_s & top_c)
    union = len(top_s | top_c)
    return (1.0 - inter / union) if union > 0 else 1.0


def spearman_rho(vsim, vcvd):
    rho, _ = spearmanr(vsim, vcvd)
    return float(rho) if np.isfinite(rho) else 0.0


# ============================================================================
# Per-simulator grid sweep: returns dict with best loss + best params + ρ@best
# ============================================================================
def sweep_2component(pool_W, pool_amps, vuln_target, family):
    grid_bs = np.arange(0.0, 80.0 + 1e-6, 2.0)
    grid_bc = np.arange(-60.0, 60.0 + 1e-6, 2.0)
    BS, BC = np.meshgrid(grid_bs, grid_bc, indexing='ij')
    norm_grid = (BS / 80.0) ** 2 + (BC / 60.0) ** 2
    n_bs, n_bc = len(grid_bs), len(grid_bc)
    g_topk = np.zeros((n_bs, n_bc))
    g_rho = np.zeros((n_bs, n_bc))
    for i, bs in enumerate(grid_bs):
        for j, bc in enumerate(grid_bc):
            C, _ = get_2component_design(bs, bc, family)
            vs, _ = simulate_mean_hc_wfixed(pool_W, pool_amps, C)
            g_topk[i, j] = l_topk_jaccard(vs, vuln_target)
            g_rho[i, j] = spearman_rho(vs, vuln_target)
    aug = g_topk + LAM_TIKH * norm_grid
    idx = np.unravel_index(int(np.argmin(aug)), aug.shape)
    return {
        'simulator': '2component',
        'best_l_topk_tikh': float(aug.min()),
        'best_l_topk_raw': float(g_topk.min()),
        'best_params': {'beta_s': float(grid_bs[idx[0]]),
                        'beta_c': float(grid_bc[idx[1]])},
        'rho_at_best': float(g_rho[idx]),
        'norm_at_best': float(norm_grid[idx]),
        'grid_size': n_bs * n_bc,
    }


def sweep_rc(pool_W, pool_amps, vuln_target, family):
    grid_dl = np.arange(0.0, 30.0 + 1e-6, 1.0)  # 31 points
    grid_g = np.arange(-3.0, 3.0 + 1e-6, 0.1)   # 61 points
    DL, GG = np.meshgrid(grid_dl, grid_g, indexing='ij')
    norm_grid = (DL / 30.0) ** 2 + (GG / 3.0) ** 2
    n_dl, n_g = len(grid_dl), len(grid_g)
    g_topk = np.zeros((n_dl, n_g))
    g_rho = np.zeros((n_dl, n_g))
    for i, dl in enumerate(grid_dl):
        for j, gv in enumerate(grid_g):
            C = get_design_matrix_rc(float(dl), float(gv), family,
                                      n_channels=N_CHANNELS, basis_type='fe')
            vs, _ = simulate_mean_hc_wfixed(pool_W, pool_amps, C)
            g_topk[i, j] = l_topk_jaccard(vs, vuln_target)
            g_rho[i, j] = spearman_rho(vs, vuln_target)
    aug = g_topk + LAM_TIKH * norm_grid
    idx = np.unravel_index(int(np.argmin(aug)), aug.shape)
    return {
        'simulator': 'rc',
        'best_l_topk_tikh': float(aug.min()),
        'best_l_topk_raw': float(g_topk.min()),
        'best_params': {'delta_lambda': float(grid_dl[idx[0]]),
                        'g': float(grid_g[idx[1]])},
        'rho_at_best': float(g_rho[idx]),
        'norm_at_best': float(norm_grid[idx]),
        'grid_size': n_dl * n_g,
    }


def sweep_machado(pool_W, pool_amps, vuln_target, family):
    grid_dl = np.arange(0.0, 30.0 + 1e-6, 0.5)  # 61 points
    norm_grid = (grid_dl / 30.0) ** 2
    n_dl = len(grid_dl)
    g_topk = np.zeros(n_dl)
    g_rho = np.zeros(n_dl)
    for i, dl in enumerate(grid_dl):
        C = get_design_matrix(
            'machado_1way', [float(dl)], n_channels=N_CHANNELS,
            basis_type='fe', cvd_type=family)
        vs, _ = simulate_mean_hc_wfixed(pool_W, pool_amps, C)
        g_topk[i] = l_topk_jaccard(vs, vuln_target)
        g_rho[i] = spearman_rho(vs, vuln_target)
    aug = g_topk + LAM_TIKH * norm_grid
    idx = int(np.argmin(aug))
    return {
        'simulator': 'machado_1way',
        'best_l_topk_tikh': float(aug.min()),
        'best_l_topk_raw': float(g_topk.min()),
        'best_params': {'delta_lambda': float(grid_dl[idx])},
        'rho_at_best': float(g_rho[idx]),
        'norm_at_best': float(norm_grid[idx]),
        'grid_size': n_dl,
    }


SWEEPER = {
    '2component': sweep_2component,
    'rc': sweep_rc,
    'machado_1way': sweep_machado,
}


def main():
    out_dir = _PHASE2 / 'results' / 'cycles'
    out_dir.mkdir(parents=True, exist_ok=True)
    data_dir = Path(LOCAL_DATA)

    # Load V4 HC pool
    print(f'[Loading HC pool, ROI={ROI}]')
    hc_amps = {}
    for hc in HC_SUBJECTS:
        try:
            hc_amps[hc] = load_amplitudes(data_dir, hc, ROI)
        except FileNotFoundError as e:
            print(f'  [warn] sub-{hc}: {e}')
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_orig = basis_full[HUE_ANGLES]
    full_W, _ = precompute_hc_W(hc_amps, C_orig)
    print(f'  W precomputed for {len(full_W)} HC')

    aggregate = {
        'config': {
            'cycle': 5,
            'task': 'cross_simulator_robustness',
            'roi': ROI,
            'lam_tikh': LAM_TIKH,
            'simulators': ['2component', 'rc', 'machado_1way'],
            'target_subject': TARGET_CVD,
            'hc_subjects': HC_SUBS,
            'note': 'sub-08 deutan, all sweeps use deutan family. '
                    'k_topk=3 for all simulators.',
        },
        'fits': {},  # fits[simulator][subj] = sweep result
        'specificity': {},  # specificity[simulator] = {hc_mean, hc_std, sub08 z}
    }

    t0 = time.time()
    for sim_name, sweeper in SWEEPER.items():
        print(f'\n=== Simulator: {sim_name} ===')
        sim_fits = {}
        # CVD: sub-08 (no LOO)
        vt08 = load_cvd_loco_target(TARGET_CVD, ROI)
        fam08 = family_for_subj(TARGET_CVD)
        ts = time.time()
        sim_fits[TARGET_CVD] = sweeper(full_W, hc_amps, vt08, fam08)
        sim_fits[TARGET_CVD]['family'] = fam08
        sim_fits[TARGET_CVD]['group'] = 'CVD'
        print(f'  sub-{TARGET_CVD}({fam08}) → '
              f'l_topk_tikh={sim_fits[TARGET_CVD]["best_l_topk_tikh"]:.3f} '
              f'raw={sim_fits[TARGET_CVD]["best_l_topk_raw"]:.3f}  '
              f'params={sim_fits[TARGET_CVD]["best_params"]}  '
              f'ρ={sim_fits[TARGET_CVD]["rho_at_best"]:+.3f}  '
              f'[{time.time()-ts:.1f}s]')

        # HC: LOO each
        for hc in HC_SUBS:
            try:
                vt = load_cvd_loco_target(hc, ROI)
            except FileNotFoundError:
                print(f'  [skip] sub-{hc}: no LOCO target')
                continue
            pool_W = {k: v for k, v in full_W.items() if k != hc}
            pool_amps = {k: v for k, v in hc_amps.items() if k != hc}
            ts = time.time()
            r = sweeper(pool_W, pool_amps, vt, 'deutan')
            r['family'] = 'deutan'
            r['group'] = 'HC'
            sim_fits[hc] = r
            print(f'  sub-{hc}(HC) → '
                  f'l_topk_tikh={r["best_l_topk_tikh"]:.3f} '
                  f'raw={r["best_l_topk_raw"]:.3f}  '
                  f'params={r["best_params"]}  '
                  f'ρ={r["rho_at_best"]:+.3f}  [{time.time()-ts:.1f}s]')

        aggregate['fits'][sim_name] = sim_fits

        # Specificity
        hc_vals = np.array([sim_fits[h]['best_l_topk_tikh']
                            for h in HC_SUBS if h in sim_fits])
        cv = sim_fits[TARGET_CVD]['best_l_topk_tikh']
        z = (cv - hc_vals.mean()) / hc_vals.std() if hc_vals.std() > 0 else 0.0
        p_emp = float((np.sum(hc_vals <= cv) + 1) / (len(hc_vals) + 1))

        aggregate['specificity'][sim_name] = {
            'hc_values': hc_vals.tolist(),
            'hc_mean': float(hc_vals.mean()),
            'hc_std': float(hc_vals.std()),
            'sub08_value': float(cv),
            'sub08_z': float(z),
            'sub08_p_emp': float(p_emp),
        }

    # ---- Robustness across simulators ----
    z_list = [aggregate['specificity'][s]['sub08_z']
              for s in ['2component', 'rc', 'machado_1way']]
    val_list = [aggregate['specificity'][s]['sub08_value']
                for s in ['2component', 'rc', 'machado_1way']]
    aggregate['robustness'] = {
        'z_min': float(min(z_list)),
        'z_max': float(max(z_list)),
        'z_range': float(max(z_list) - min(z_list)),
        'value_min': float(min(val_list)),
        'value_max': float(max(val_list)),
        'value_range': float(max(val_list) - min(val_list)),
        'verdict_z': ('framing_validated' if (max(z_list) - min(z_list)) < 1.0
                      else 'simulator_conditional'
                      if (max(z_list) - min(z_list)) > 1.5 else 'mixed'),
    }

    # Save
    out_path = out_dir / 'cycle5_cross_sim_aggregate.json'
    with open(out_path, 'w') as f:
        json.dump(aggregate, f, indent=2, default=str)
    print(f'\n[Wrote] {out_path}')
    print(f'[Done] elapsed={time.time()-t0:.1f}s')

    # Summary table
    print('\n' + '=' * 110)
    print('=== Cross-simulator robustness (sub-08 V4, l_topk + λ=0.2 Tikh) ===')
    print(f'{"sim":>14} | {"HCμ":>7} {"HCσ":>7} | '
          f'{"sub08 val":>10} {"sub08 z":>8} {"sub08 p":>8}')
    print('-' * 110)
    for s in ['2component', 'rc', 'machado_1way']:
        sp = aggregate['specificity'][s]
        print(f'{s:>14} | {sp["hc_mean"]:>+7.3f} {sp["hc_std"]:>7.3f} | '
              f'{sp["sub08_value"]:>+10.3f} {sp["sub08_z"]:>+8.3f} '
              f'{sp["sub08_p_emp"]:>8.3f}')
    print('-' * 110)
    rb = aggregate['robustness']
    print(f'  z range = [{rb["z_min"]:+.3f}, {rb["z_max"]:+.3f}] '
          f'(spread {rb["z_range"]:.3f})')
    print(f'  val range = [{rb["value_min"]:.3f}, {rb["value_max"]:.3f}] '
          f'(spread {rb["value_range"]:.3f})')
    print(f'  verdict_z: {rb["verdict_z"]}')


if __name__ == '__main__':
    main()
