"""sub09_protan_theta_conf_refit.py — sub-09 V4 refit under protan-correct θ_conf=16°.

Background:
  Current BEST/Tier 2 sub-09 argmins (30,+46)/(34,+44) were computed with
  θ_conf=150° (deutan confusion axis), as that is the value hard-coded in
  old_formula_refit.py:dt_old. CONF_AXIS_STOCKMAN in forward_models/two_component.py
  specifies protan=16°, deutan=150°, normal=83° — sub-09 should use 16°.

  This refit re-runs the wfixed simulator landscape sweep for sub-09 V4 only,
  with θ_conf=16°. It checks whether the BEST argmin shifts significantly.

Pipeline (mirrors phase3_cache_vulnsim_old.py):
  Grid: β_s ∈ [0, 50] step 2, β_c ∈ [-50, 50] step 2  → 1326 cells
  For each cell:
    δθ = β_s·cos(θ-90°) + β_c·cos(θ-θ_conf)   [θ_conf=16° here]
    C_shifted = basis at (θ + δθ)
    vuln_sim = LOCO predict using mean-HC W on C_shifted
    L_ccc = (1 - CCC(vuln_sim, vuln_cvd)) / 2
    l_topk = 1 - |top3(sim) ∩ top3(obs)| / |top3 ∪ top3|
    L_combined = 1·L_ccc + 0.5·l_topk + 0.1·Tikh   (matches BEST V4-CCC+l_topk)

Output → results/sub09_protan_refit/
  sub-09_V4_protan16_landscape.json
  sub-09_V4_protan16_compare.md
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))
sys.path.insert(0, str(_THIS_DIR / 'forward_models'))

from old_formula_refit import (
    HC_SUBJECTS, N_CHANNELS, THETA_8,
    load_amplitudes, create_basis_full,
    LOCAL_DATA, SERVER_DATA,
)
from step1_fit_loco_v2 import (
    simulate_mean_hc_loco_legacy,
    load_cvd_loco_target,
)

OUT = _THIS_DIR.parent / 'results' / 'sub09_protan_refit'
OUT.mkdir(parents=True, exist_ok=True)

THETA_CONF_PROTAN = 16.0
THETA_CONF_DEUTAN = 150.0
TIKH_NORM = 32400.0  # (2*sqrt(50^2 + 50^2))^2 ≈ ‖(50,50)‖² × 2 (matches BEST)
K_TOPK = 3
LAMBDA_TOPK = 0.5
LAMBDA_CCC = 1.0
LAMBDA_REG = 0.1


def dt_family(bs: float, bc: float, theta_conf: float,
              theta: np.ndarray = THETA_8) -> np.ndarray:
    return (bs * np.cos(np.radians(theta - 90.0))
            + bc * np.cos(np.radians(theta - theta_conf)))


def get_shifted_design(bs: float, bc: float, theta_conf: float):
    dt = dt_family(bs, bc, theta_conf)
    hue_shifted = (THETA_8 + dt) % 360.0
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    idx = np.round(hue_shifted).astype(int) % 360
    return basis_full[idx], dt


def ccc_value(sim: np.ndarray, obs: np.ndarray) -> float:
    sim = np.asarray(sim, dtype=float); obs = np.asarray(obs, dtype=float)
    if np.std(sim) < 1e-10 or np.std(obs) < 1e-10:
        return 0.0
    r, _ = pearsonr(sim, obs)
    if not np.isfinite(r):
        return 0.0
    msim = sim.mean(); mobs = obs.mean()
    ssim = sim.std();  sobs = obs.std()
    denom = ssim**2 + sobs**2 + (msim - mobs)**2
    if denom < 1e-10:
        return 0.0
    return float(2.0 * r * ssim * sobs / denom)


def l_topk_jaccard(vuln_sim: np.ndarray, vuln_obs: np.ndarray, K: int = K_TOPK) -> float:
    """1 - Jaccard(top-K most vulnerable colors)."""
    sim_sort = np.argsort(vuln_sim)[:K]   # smallest correlations = most vulnerable
    obs_sort = np.argsort(vuln_obs)[:K]
    S_sim = set(int(i) for i in sim_sort)
    S_obs = set(int(i) for i in obs_sort)
    inter = S_sim & S_obs
    union = S_sim | S_obs
    if not union:
        return 1.0
    return float(1.0 - len(inter) / len(union))


def run_refit(subj_id: str = '09', roi: str = 'V4',
              theta_conf: float = THETA_CONF_PROTAN):
    data_dir = SERVER_DATA if SERVER_DATA.exists() else LOCAL_DATA
    print(f'data_dir: {data_dir}')
    print(f'θ_conf:   {theta_conf}°  (protan-correct: 16°, deutan: 150°)')

    hc_amps = {s: load_amplitudes(data_dir, s, roi) for s in HC_SUBJECTS}
    print(f'HC amps loaded: {[(s, hc_amps[s].shape) for s in HC_SUBJECTS]}')
    vuln_cvd = load_cvd_loco_target(subj_id, roi)
    print(f'sub-{subj_id} {roi} LOCO target: {vuln_cvd.round(3)}')

    bs_range = np.arange(0, 51, 2, dtype=float)
    bc_range = np.arange(-50, 51, 2, dtype=float)
    n_cells = len(bs_range) * len(bc_range)
    print(f'Grid: {len(bs_range)} × {len(bc_range)} = {n_cells} cells')

    landscape = []
    t0 = time.time()
    for i, bs in enumerate(bs_range):
        for bc in bc_range:
            C_shifted, dt = get_shifted_design(bs, bc, theta_conf)
            vuln_sim, _ = simulate_mean_hc_loco_legacy(hc_amps, C_shifted)
            ccc = ccc_value(vuln_sim, vuln_cvd)
            l_ccc = (1.0 - ccc) / 2.0
            lt = l_topk_jaccard(vuln_sim, vuln_cvd, K=K_TOPK)
            tikh = (float(bs)**2 + float(bc)**2) / TIKH_NORM
            L = LAMBDA_CCC * l_ccc + LAMBDA_TOPK * lt + LAMBDA_REG * tikh
            landscape.append({
                'bs': float(bs), 'bc': float(bc),
                'vuln_sim': vuln_sim.tolist(),
                'delta_theta': dt.tolist(),
                'ccc': ccc, 'l_ccc': l_ccc,
                'l_topk': lt, 'tikh': tikh,
                'L_combined': L,
            })
        if (i + 1) % 5 == 0 or i == len(bs_range) - 1:
            print(f'  [{i+1:2d}/{len(bs_range)} β_s] elapsed={time.time()-t0:.0f}s')

    elapsed = time.time() - t0
    print(f'\nDone in {elapsed:.0f}s')

    best = min(landscape, key=lambda c: c['L_combined'])
    print(f"\nθ_conf={theta_conf}° BEST argmin: "
          f"(β_s={best['bs']:.0f}, β_c={best['bc']:+.0f})  "
          f"L={best['L_combined']:.4f}  CCC={best['ccc']:+.3f}  "
          f"l_topk={best['l_topk']:.3f}")

    # Top-5 alternatives
    top5 = sorted(landscape, key=lambda c: c['L_combined'])[:5]
    print(f"\nTop-5 alternatives:")
    for k, c in enumerate(top5):
        print(f"  #{k+1}: (β_s={c['bs']:.0f}, β_c={c['bc']:+.0f})  "
              f"L={c['L_combined']:.4f}  CCC={c['ccc']:+.3f}  l_topk={c['l_topk']:.3f}")

    out = {
        'subject': f'sub-{subj_id}', 'roi': roi,
        'theta_conf': theta_conf,
        'family': 'protan' if abs(theta_conf - 16.0) < 1 else 'deutan',
        'loss': '1·L_ccc + 0.5·l_topk + 0.1·Tikh',
        'grid': {'bs': [0, 50, 2], 'bc': [-50, 50, 2]},
        'best': best,
        'top5': top5,
        'vuln_cvd': vuln_cvd.tolist(),
        'cells': landscape,
    }
    out_fn = OUT / f'sub-{subj_id}_{roi}_protan{int(theta_conf)}_landscape.json'
    with open(out_fn, 'w') as f:
        json.dump(out, f)
    print(f'\nWrote {out_fn.name} ({out_fn.stat().st_size/1024:.0f} KB)')
    return out, best


if __name__ == '__main__':
    out_protan, best_protan = run_refit('09', 'V4', THETA_CONF_PROTAN)
