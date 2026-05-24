"""s5_tregillus_stats.py — Statistical tests for Tregillus R+C fits.

For each (subject, ROI, loss_target ∈ {L2_behav_gamma, L4_RDM_corr}):
  - At every Δλ source: take Tregillus best-fit g, compute loss
  - Permutation null: 200 random color-label permutations
  - Report p_perm = P(loss_perm <= loss_obs | null)

Two color-permutation strategies:
  L_γ (behav JND): apply δθ[perm] before computing JND loss
    (this permutes which canonical hue's δθ is used to predict each pair)
  L_RDM:           permute ΔRDM_obs (28-vec → 8×8 → permute rows/cols → 28-vec)
    while keeping ΔRDM_sim fixed (computed at g_best on un-permuted Δλ)

Also reports loss-landscape flatness:
  flatness = std(losses)/|loss_best| over the g grid (excluding boundary 2 pts)
"""
from __future__ import annotations
import sys
import json
import numpy as np
from pathlib import Path
from scipy.spatial.distance import pdist, squareform

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_opponent_1dof import forward_rc_opp, fit_rc_opp_g
from s5_all_paths_fit import DELTA_LAMBDA_SOURCES
from behav_loss import (
    SIGMA_HC, BEHAV_WEIGHTS,
    L_behav_alpha, L_behav_gamma,
    load_8afc_per_color, load_jnd_per_pair,
    compute_hc_jnd_baseline,
)
from neural_loss import (
    L_LOCO, L_RDM, design_from_delta,
    load_amplitudes, load_hc_pool, ROI_K,
    cosine_similarity,
)
from diagnostic_delta_rdm import (
    precompute_hc_W,
    compute_delta_rdm_obs,
    compute_rdm_correlation,
)
from utils_forward_model import create_basis_full, HUE_ANGLES

OUT_DIR = SCRIPT_DIR.parent / 'results' / 's5_tregillus'
N_PERM = 200
RNG_SEED = 20260524


def permute_rdm_28(rdm_28: np.ndarray, perm: np.ndarray) -> np.ndarray:
    """Re-index a 28-vec correlation RDM by permuting the 8 color labels."""
    sq = squareform(rdm_28)
    sq_perm = sq[perm][:, perm]
    return squareform(sq_perm, checks=False)


def compute_loss_landscape_flatness(losses: list, g_best_idx: int) -> dict:
    """Flatness around best fit: std/|best| in inner grid, plus
    range[loss(g) - loss_best] over interior points."""
    arr = np.asarray(losses, dtype=float)
    # Exclude grid boundary 2 points each side to focus on interior shape
    interior = arr[2:-2]
    span = float(interior.max() - interior.min())
    rel = span / max(abs(arr[g_best_idx]), 1e-6)
    return {
        'interior_loss_min': float(interior.min()),
        'interior_loss_max': float(interior.max()),
        'interior_loss_span': span,
        'rel_to_best': rel,
        'flatness_low': bool(rel < 0.1),
    }


def stats_one_cell(subject: str, roi: str, loss_target: str, sigma=SIGMA_HC,
                    n_perm: int = N_PERM, rng=None) -> dict:
    """Permutation null + flatness for one (subject, ROI, loss) cell.

    We do this per Δλ source, taking the Tregillus best-fit g.
    """
    if rng is None:
        rng = np.random.default_rng(RNG_SEED)

    info = DELTA_LAMBDA_SOURCES[subject]
    cvd_family = info['family']
    K = ROI_K[roi]

    # Load data + shared precomputes
    cvd_amp = load_amplitudes(subject, roi)
    hc_amps = load_hc_pool(roi)
    C_baseline = create_basis_full(K, basis_type='fe')[HUE_ANGLES.astype(int)]
    hc_W, _ = precompute_hc_W(hc_amps, C_baseline)

    # Observation-side caches
    delta_rdm_obs, _, _, _ = compute_delta_rdm_obs(
        cvd_amp, hc_amps, distance='correlation')

    # RDM baselines per HC (un-permuted)
    rdm_baseline_per_hc = {h: compute_rdm_correlation(C_baseline @ W)
                           for h, W in hc_W.items()}

    # Behav refs
    jnd_obs = load_jnd_per_pair(subject)
    hc_jnd_baseline, hc_jnd_sd = compute_hc_jnd_baseline()
    obs_acc = load_8afc_per_color(subject)

    out = {
        'subject': subject, 'roi': roi, 'loss_target': loss_target,
        'sigma': sigma, 'n_perm': n_perm, 'per_source': {},
    }

    for src_label, dl in info['sources'].items():
        # ============= Fit g_best under un-permuted loss =============
        if loss_target == 'L2_behav_gamma':
            def loss_fn(delta_rc):
                return L_behav_gamma(delta_rc, jnd_obs, hc_jnd_baseline,
                                     hc_jnd_sd)
        elif loss_target == 'L4_RDM_corr':
            def loss_fn(delta_rc):
                C_shifted = design_from_delta(delta_rc, n_channels=K)
                delta_rdm_per_hc = []
                for h, W in hc_W.items():
                    Y_s = C_shifted @ W
                    rdm_s = compute_rdm_correlation(Y_s)
                    delta_rdm_per_hc.append(rdm_s - rdm_baseline_per_hc[h])
                drs = np.mean(delta_rdm_per_hc, axis=0)
                cos = cosine_similarity(drs, delta_rdm_obs)
                if not np.isfinite(cos):
                    cos = 0.0
                return float(1.0 - cos)
        else:
            raise ValueError(loss_target)

        fit = fit_rc_opp_g(dl, cvd_family, loss_fn)
        g_best = fit['g_best']
        loss_obs = fit['loss_best']
        delta_obs = forward_rc_opp(dl, g_best, cvd_family)

        # Find best idx for flatness
        g_grid = np.asarray(fit['grid'])
        best_idx = int(np.argmin(fit['losses']))
        flatness = compute_loss_landscape_flatness(fit['losses'], best_idx)

        # ============= Permutation null =============
        perm_losses = np.zeros(n_perm)

        if loss_target == 'L2_behav_gamma':
            # Permute the COLOR labels in jnd_obs by reindexing pair predictions
            # Equivalent: shuffle delta_obs into delta_obs[perm] and recompute
            # (this reshuffles which canonical δθ enters each pair prediction)
            for k in range(n_perm):
                perm = rng.permutation(8)
                delta_perm = delta_obs[perm]
                perm_losses[k] = L_behav_gamma(
                    delta_perm, jnd_obs, hc_jnd_baseline, hc_jnd_sd)

        elif loss_target == 'L4_RDM_corr':
            # Compute ΔRDM_sim ONCE at g_best, then permute ΔRDM_obs each iter
            C_shifted = design_from_delta(delta_obs, n_channels=K)
            delta_rdm_per_hc = []
            for h, W in hc_W.items():
                Y_s = C_shifted @ W
                rdm_s = compute_rdm_correlation(Y_s)
                delta_rdm_per_hc.append(rdm_s - rdm_baseline_per_hc[h])
            delta_rdm_sim = np.mean(delta_rdm_per_hc, axis=0)
            for k in range(n_perm):
                perm = rng.permutation(8)
                drm_perm = permute_rdm_28(delta_rdm_obs, perm)
                cos = cosine_similarity(delta_rdm_sim, drm_perm)
                if not np.isfinite(cos):
                    cos = 0.0
                perm_losses[k] = float(1.0 - cos)

        # p_perm = P(loss_perm <= loss_obs)
        # (smaller loss = better; we test whether observed fit is better than chance)
        n_better_or_equal = int(np.sum(perm_losses <= loss_obs))
        p_perm = (n_better_or_equal + 1) / (n_perm + 1)

        out['per_source'][src_label] = {
            'delta_lambda_nm': float(dl),
            'g_best': float(g_best),
            'loss_obs': float(loss_obs),
            'delta_theta_at_best': delta_obs.tolist(),
            'boundary_low': fit['boundary_low'],
            'boundary_high': fit['boundary_high'],
            'in_tregillus_zone': bool(-1.0 <= g_best <= 0.0),
            'flatness': flatness,
            'perm': {
                'n_perm': n_perm,
                'perm_loss_mean': float(perm_losses.mean()),
                'perm_loss_median': float(np.median(perm_losses)),
                'perm_loss_min': float(perm_losses.min()),
                'perm_loss_p05': float(np.quantile(perm_losses, 0.05)),
                'perm_loss_p95': float(np.quantile(perm_losses, 0.95)),
                'n_better_or_equal': n_better_or_equal,
                'p_perm': float(p_perm),
                'sig_05': bool(p_perm < 0.05),
            },
        }

    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(RNG_SEED)
    summary = {'rng_seed': RNG_SEED, 'n_perm': N_PERM, 'cells': []}

    targets = [
        ('sub-08', 'V1', 'L2_behav_gamma'),
        ('sub-08', 'V1', 'L4_RDM_corr'),
        ('sub-08', 'V4', 'L2_behav_gamma'),
        ('sub-08', 'V4', 'L4_RDM_corr'),
        ('sub-09', 'V1', 'L2_behav_gamma'),
        ('sub-09', 'V1', 'L4_RDM_corr'),
        ('sub-09', 'V4', 'L2_behav_gamma'),
        ('sub-09', 'V4', 'L4_RDM_corr'),
    ]
    for subj, roi, loss in targets:
        print(f'  stats: {subj} {roi} {loss}')
        cell = stats_one_cell(subj, roi, loss, n_perm=N_PERM, rng=rng)
        summary['cells'].append(cell)

    with open(OUT_DIR / 'stats_summary.json', 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f'\nSaved {OUT_DIR / "stats_summary.json"}')

    # Brief stdout report
    print('\n--- p_perm summary (key cells) ---')
    for c in summary['cells']:
        for src, d in c['per_source'].items():
            zone = 'IN' if d['in_tregillus_zone'] else 'OUT'
            bd = ('LO' if d['boundary_low']
                  else ('HI' if d['boundary_high'] else '--'))
            print(f"  {c['subject']} {c['roi']} {c['loss_target']:<18} "
                  f"{src:<10} Δλ={d['delta_lambda_nm']:>4.1f} "
                  f"g={d['g_best']:+.2f} ({zone},{bd}) "
                  f"loss={d['loss_obs']:.4f} "
                  f"p={d['perm']['p_perm']:.4f} "
                  f"flat={d['flatness']['rel_to_best']:.3f}")


if __name__ == '__main__':
    main()
