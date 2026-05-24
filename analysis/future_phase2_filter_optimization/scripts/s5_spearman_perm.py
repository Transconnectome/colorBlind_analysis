"""S5 Spearman permutation null — color-label permutation, L4 RDM only.

For each (cell, model):
  observed_rho = Spearman ρ at the Spearman-best fit (from results/s5_spearman/)
  For 200 iters:
    perm = random permutation of color labels [0..7]
    Permute the CVD RDM (8x8 matrix) → recompute ΔRDM_obs_perm
    Best-fit Spearman ρ over the grid → best_rho_perm
  p = (count of best_rho_perm >= observed_rho) / 200

Outputs:
  results/s5_spearman/perm_null_spearman.json

Seed: 42 (reproducibility).
"""
import sys
import json
import time
import numpy as np
from pathlib import Path
from scipy.spatial.distance import squareform
from scipy.stats import spearmanr

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import forward_rc, g_grid
from two_comp import forward_2comp, BS_GRID, BC_GRID
from neural_loss import (
    load_amplitudes, load_hc_pool, ROI_K, design_from_delta,
)
from diagnostic_delta_rdm import (
    precompute_hc_W, compute_rdm_correlation,
)
from utils_forward_model import create_basis_full, HUE_ANGLES

PHASE2 = SCRIPT_DIR.parent
SPEARMAN_DIR = PHASE2 / "results" / "s5_spearman"
OUT_PATH = SPEARMAN_DIR / "perm_null_spearman.json"

CVD_FAMILY = {'sub-08': 'deutan', 'sub-09': 'protan'}
DELTA_LAMBDA_DPS = {'sub-08': 6.0, 'sub-09': 10.0}

N_PERM = 200
SEED = 42


def _safe_spearman(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if np.std(a) < 1e-15 or np.std(b) < 1e-15:
        return 0.0
    rho, _ = spearmanr(a, b)
    return float(rho) if np.isfinite(rho) else 0.0


def permute_rdm(rdm_28vec, perm):
    """Permute color labels in an 8×8 RDM (presented as 28-vec upper tri)."""
    rdm_mat = squareform(rdm_28vec)  # (8,8) symmetric
    rdm_perm = rdm_mat[np.ix_(perm, perm)]
    return squareform(rdm_perm, checks=False)


def precompute_caches(subject, roi):
    K = ROI_K[roi]
    cvd_amp = load_amplitudes(subject, roi)
    hc_amps = load_hc_pool(roi)
    C_baseline = create_basis_full(K, basis_type='fe')[HUE_ANGLES.astype(int)]

    # CVD RDM
    rdm_cvd = compute_rdm_correlation(cvd_amp.mean(axis=0))
    rdm_hc_individual = {
        h: compute_rdm_correlation(amp.mean(axis=0)) for h, amp in hc_amps.items()
    }
    rdm_hc_mean = np.mean(list(rdm_hc_individual.values()), axis=0)

    hc_W, _ = precompute_hc_W(hc_amps, C_baseline)
    rdm_baseline_per_hc = {h: compute_rdm_correlation(C_baseline @ W) for h, W in hc_W.items()}

    return {
        'K': K, 'C_baseline': C_baseline,
        'rdm_cvd': rdm_cvd, 'rdm_hc_mean': rdm_hc_mean,
        'hc_W': hc_W, 'rdm_baseline_per_hc': rdm_baseline_per_hc,
    }


def compute_delta_rdm_sim(delta_8vec, cache):
    C_shifted = design_from_delta(delta_8vec, n_channels=cache['K'])
    parts = []
    for h, W in cache['hc_W'].items():
        Y = C_shifted @ W
        parts.append(compute_rdm_correlation(Y) - cache['rdm_baseline_per_hc'][h])
    return np.mean(parts, axis=0)


def best_rho_rc(delta_lambda, cvd_family, delta_rdm_obs, cache):
    """Grid search g, return best Spearman ρ."""
    grid = g_grid()
    best = -np.inf
    best_g = grid[0]
    for g in grid:
        d = forward_rc(delta_lambda, g, cvd_family)
        sim = compute_delta_rdm_sim(d, cache)
        rho = _safe_spearman(sim, delta_rdm_obs)
        if rho > best:
            best = rho
            best_g = g
    return float(best), float(best_g)


def best_rho_2comp(cvd_family, delta_rdm_obs, cache):
    """Grid search (β_s, β_c), return best Spearman ρ. Uses S5 asymmetric grid."""
    best = -np.inf
    best_bs = BS_GRID[0]
    best_bc = BC_GRID[0]
    for bs in BS_GRID:
        for bc in BC_GRID:
            d = forward_2comp(bs, bc, cvd_family)
            sim = compute_delta_rdm_sim(d, cache)
            rho = _safe_spearman(sim, delta_rdm_obs)
            if rho > best:
                best = rho
                best_bs = bs
                best_bc = bc
    return float(best), float(best_bs), float(best_bc)


def run_cell(subject, roi):
    cvd_family = CVD_FAMILY[subject]
    dl = DELTA_LAMBDA_DPS[subject]
    print(f"\n=== {subject} {roi} (Δλ={dl}, family={cvd_family}) ===")
    t0 = time.time()
    cache = precompute_caches(subject, roi)

    # Observed ΔRDM
    delta_rdm_obs = cache['rdm_cvd'] - cache['rdm_hc_mean']

    # Observed best fits
    obs_rc_rho, obs_g = best_rho_rc(dl, cvd_family, delta_rdm_obs, cache)
    obs_tc_rho, obs_bs, obs_bc = best_rho_2comp(cvd_family, delta_rdm_obs, cache)
    print(f"  Observed R+C ρ_best = {obs_rc_rho:+.3f} at g={obs_g:.2f}")
    print(f"  Observed 2-Comp ρ_best = {obs_tc_rho:+.3f} at "
            f"(βs={obs_bs:.0f}, βc={obs_bc:.0f})")

    # Permutation
    rng = np.random.default_rng(SEED + hash((subject, roi)) % 1000)
    null_rc = np.zeros(N_PERM)
    null_tc = np.zeros(N_PERM)
    for i in range(N_PERM):
        perm = rng.permutation(8)
        rdm_cvd_perm = permute_rdm(cache['rdm_cvd'], perm)
        d_obs_perm = rdm_cvd_perm - cache['rdm_hc_mean']
        rho_rc, _ = best_rho_rc(dl, cvd_family, d_obs_perm, cache)
        rho_tc, _, _ = best_rho_2comp(cvd_family, d_obs_perm, cache)
        null_rc[i] = rho_rc
        null_tc[i] = rho_tc
        if (i + 1) % 50 == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N_PERM - i - 1) / rate
            print(f"    [{i+1}/{N_PERM}] elapsed={elapsed:.1f}s "
                    f"rate={rate:.2f}/s eta={eta:.1f}s")

    # Two-sided / one-sided. ρ is signed; we want test "is obs > null". One-sided.
    p_rc = float((null_rc >= obs_rc_rho).mean())
    p_tc = float((null_tc >= obs_tc_rho).mean())
    elapsed = time.time() - t0
    print(f"  Cell done in {elapsed:.1f}s. p_RC={p_rc:.4f}, p_2C={p_tc:.4f}")

    return {
        'subject': subject, 'roi': roi, 'cvd_family': cvd_family,
        'delta_lambda_nm': dl, 'n_perm': N_PERM, 'seed': SEED,
        'R+C': {
            'rho_obs': obs_rc_rho, 'g_obs': obs_g,
            'null_mean': float(null_rc.mean()),
            'null_max': float(null_rc.max()),
            'null_q975': float(np.quantile(null_rc, 0.975)),
            'p_one_sided': p_rc,
        },
        '2-Comp': {
            'rho_obs': obs_tc_rho, 'beta_s_obs': obs_bs, 'beta_c_obs': obs_bc,
            'null_mean': float(null_tc.mean()),
            'null_max': float(null_tc.max()),
            'null_q975': float(np.quantile(null_tc, 0.975)),
            'p_one_sided': p_tc,
        },
        'null_rc_values': null_rc.tolist(),
        'null_tc_values': null_tc.tolist(),
        'wall_time_s': round(elapsed, 1),
    }


def main():
    SPEARMAN_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print(f"S5 Spearman permutation null — color-label perm, L4 RDM only")
    print(f"  N_PERM={N_PERM}, seed={SEED}")
    print(f"  R+C grid 61 pts; 2-Comp grid {len(BS_GRID)}×{len(BC_GRID)}={len(BS_GRID)*len(BC_GRID)} pts")
    print("=" * 78)

    cells = [('sub-08', 'V1'), ('sub-08', 'V4'),
              ('sub-09', 'V1'), ('sub-09', 'V4')]
    t_start = time.time()
    all_results = []
    for subj, roi in cells:
        all_results.append(run_cell(subj, roi))

    total_elapsed = time.time() - t_start
    out = {
        'meta': {
            'n_perm': N_PERM, 'seed': SEED,
            'distance': 'correlation',
            'tie_handling': 'average (scipy spearmanr default)',
            'rc_grid_size': len(g_grid()),
            'tc_grid_size': len(BS_GRID) * len(BC_GRID),
            'total_wall_time_s': round(total_elapsed, 1),
        },
        'cells': all_results,
    }
    with open(OUT_PATH, 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved: {OUT_PATH}")
    print(f"Total time: {total_elapsed:.1f}s")

    # Compact p-value table
    print(f"\n{'Cell':<12} {'R+C ρ_obs':<12} {'R+C p':<8} {'2C ρ_obs':<12} {'2C p':<8}")
    for r in all_results:
        cell = f"{r['subject']} {r['roi']}"
        print(f"{cell:<12} {r['R+C']['rho_obs']:<+12.3f} "
                f"{r['R+C']['p_one_sided']:<8.4f} "
                f"{r['2-Comp']['rho_obs']:<+12.3f} "
                f"{r['2-Comp']['p_one_sided']:<8.4f}")


if __name__ == "__main__":
    main()
