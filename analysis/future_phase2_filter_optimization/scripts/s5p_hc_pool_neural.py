"""S5' (neural extension): HC pool g fit on L_LOCO and L_RDM (per ROI × family).

Behavioral S5' (s5p_hc_pool_g_fit.py) uses L_behav only — extends here to
neural losses to address S4 W-asymmetry justification:
  - L3 LOCO (within-subject W) HC pool g distribution
  - L4 RDM (HC pool W + LOO-HC reference) HC pool g distribution

Per ROI ∈ {V1, V4} × family ∈ {protan, deutan} × 7 HC × 3 Δλ sources
→ supports S4 Acknowledged Constraints (1) empirical justification +
  Δλ sensitivity (이번 catch 통합).

Output: results/s5p_hc_pool/g_HC_pool_neural.json
"""
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import fit_rc_g, forward_rc
from neural_loss import (
    L_LOCO, L_RDM, design_from_delta,
    load_amplitudes, load_hc_pool, ROI_K,
    precompute_loco_W_within,
)
from diagnostic_delta_rdm import precompute_hc_W, compute_rdm_correlation
from utils_forward_model import create_basis_full, HUE_ANGLES

ROOT = SCRIPT_DIR.parents[2]
OUT_DIR = SCRIPT_DIR.parent / "results" / "s5p_hc_pool"

HC_SUBJS = ['sub-01', 'sub-02', 'sub-03', 'sub-04', 'sub-05', 'sub-06', 'sub-07']
ROIS = ['V1', 'V4']

# Δλ sources per family (paper-consistent)
DELTA_LAMBDA_BY_FAMILY = {
    'deutan': {'DPS_lit': 6.0, 'Boehm_mid': 8.0, 'JND_Lamb': 6.5},
    'protan': {'DPS_lit': 10.0, 'Boehm_low': 3.0, 'JND_Lamb': 1.5},
}


def fit_hc_g_on_loco(hc_subject: str, roi: str, family: str, delta_lambda: float,
                      K: int) -> dict:
    """L3 LOCO only: fit R+C g for HC h on h's own within-subject LOCO."""
    try:
        hc_amp = load_amplitudes(hc_subject, roi)
        if roi == 'V4' and hc_amp.shape[2] < 20:
            return None  # sub-07 hV4 16 vox excluded
    except FileNotFoundError:
        return None

    C_baseline = create_basis_full(K, basis_type='fe')[HUE_ANGLES.astype(int)]
    loco_W, _ = precompute_loco_W_within(hc_amp, C_baseline)

    def L_loco_fn(delta_rc):
        return L_LOCO(delta_rc, hc_amp, loco_W, K)

    fit = fit_rc_g(delta_lambda, family, L_loco_fn)
    return {
        'hc_subject': hc_subject, 'roi': roi, 'family': family, 'delta_lambda': delta_lambda,
        'g_best': fit['g_best'], 'loss_best': fit['loss_best'],
        'boundary_low': fit['boundary_low'], 'boundary_high': fit['boundary_high'],
    }


def fit_hc_g_on_rdm(hc_subject: str, roi: str, family: str, delta_lambda: float,
                     K: int, hc_amps_pool: dict) -> dict:
    """L4 RDM only: fit R+C g for HC h using LOO-HC RDM reference.

    Reference = mean(RDM_HC_others) — h excluded from HC pool to avoid self-ref.
    Δ_obs = RDM_h − ref. Δ_sim(δθ) computed from HC pool encoder W.
    """
    if hc_subject not in hc_amps_pool:
        return None

    C_baseline = create_basis_full(K, basis_type='fe')[HUE_ANGLES.astype(int)]
    # LOO-HC pool (other HCs as reference)
    others = {k: v for k, v in hc_amps_pool.items() if k != hc_subject}
    if len(others) < 2:
        return None
    hc_amp_h = hc_amps_pool[hc_subject]

    # Precompute HC W for RDM sim (uses others as encoder pool)
    hc_W_others, _ = precompute_hc_W(others, C_baseline)

    # Δ_obs = RDM_h − mean RDM of others
    rdm_h = compute_rdm_correlation(hc_amp_h.mean(axis=0))
    rdm_others = []
    for s, amp in others.items():
        rdm_others.append(compute_rdm_correlation(amp.mean(axis=0)))
    rdm_others_mean = np.mean(rdm_others, axis=0)
    delta_rdm_obs = rdm_h - rdm_others_mean  # (28,)

    def L_rdm_fn(delta_rc):
        C_shifted = design_from_delta(delta_rc, n_channels=K)
        # ΔRDM_sim averaged across other-HC encoders
        rdm_sims = []
        for s, W in hc_W_others.items():
            Y_shifted = C_shifted @ W
            Y_baseline = C_baseline @ W
            rdm_sims.append(compute_rdm_correlation(Y_shifted) -
                             compute_rdm_correlation(Y_baseline))
        delta_rdm_sim = np.mean(rdm_sims, axis=0)
        # 1 − cos(sim, obs)
        n_sim = np.linalg.norm(delta_rdm_sim)
        n_obs = np.linalg.norm(delta_rdm_obs)
        if n_sim < 1e-10 or n_obs < 1e-10:
            return 1.0
        cos = float(np.dot(delta_rdm_sim, delta_rdm_obs) / (n_sim * n_obs))
        return 1.0 - cos

    fit = fit_rc_g(delta_lambda, family, L_rdm_fn)
    return {
        'hc_subject': hc_subject, 'roi': roi, 'family': family, 'delta_lambda': delta_lambda,
        'g_best': fit['g_best'], 'loss_best': fit['loss_best'],
        'boundary_low': fit['boundary_low'], 'boundary_high': fit['boundary_high'],
    }


def aggregate_pool(per_hc_results: list) -> dict:
    g_vals = [r['g_best'] for r in per_hc_results if r is not None]
    if len(g_vals) == 0:
        return {'pool_n': 0}
    g_arr = np.array(g_vals)
    return {
        'pool_n': len(g_vals),
        'pool_mean': float(np.mean(g_arr)),
        'pool_median': float(np.median(g_arr)),
        'pool_sd': float(np.std(g_arr, ddof=1)) if len(g_arr) > 1 else 0.0,
        'pool_range': [float(g_arr.min()), float(g_arr.max())],
        'per_hc': {r['hc_subject']: r['g_best'] for r in per_hc_results if r is not None},
        'n_boundary_low': sum(1 for r in per_hc_results if r is not None and r.get('boundary_low')),
        'n_boundary_high': sum(1 for r in per_hc_results if r is not None and r.get('boundary_high')),
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("S5' neural extension: HC pool g on L3 LOCO + L4 RDM")
    print("  ROI × family × Δλ source × 7 HC")
    print("=" * 78)

    results = {}
    for roi in ROIS:
        K = ROI_K[roi]
        hc_amps_pool = load_hc_pool(roi)
        print(f"\n=== ROI {roi} (K={K}, HC pool n={len(hc_amps_pool)}) ===")
        results[roi] = {}
        for fam, dl_sources in DELTA_LAMBDA_BY_FAMILY.items():
            results[roi][fam] = {}
            for src_name, dl in dl_sources.items():
                # L3 LOCO
                per_hc_loco = []
                for hc in HC_SUBJS:
                    r = fit_hc_g_on_loco(hc, roi, fam, dl, K)
                    if r is not None:
                        per_hc_loco.append(r)
                pool_loco = aggregate_pool(per_hc_loco)

                # L4 RDM
                per_hc_rdm = []
                for hc in HC_SUBJS:
                    r = fit_hc_g_on_rdm(hc, roi, fam, dl, K, hc_amps_pool)
                    if r is not None:
                        per_hc_rdm.append(r)
                pool_rdm = aggregate_pool(per_hc_rdm)

                results[roi][fam][src_name] = {
                    'delta_lambda': dl,
                    'L3_LOCO_pool': pool_loco,
                    'L4_RDM_pool': pool_rdm,
                }
                print(f"  {fam} {src_name} (Δλ={dl}):")
                if pool_loco['pool_n'] > 0:
                    print(f"    L3 LOCO HC pool: n={pool_loco['pool_n']} "
                          f"mean={pool_loco['pool_mean']:.2f}±{pool_loco['pool_sd']:.2f} "
                          f"range={pool_loco['pool_range']}  "
                          f"boundary_low={pool_loco['n_boundary_low']} high={pool_loco['n_boundary_high']}")
                if pool_rdm['pool_n'] > 0:
                    print(f"    L4 RDM  HC pool: n={pool_rdm['pool_n']} "
                          f"mean={pool_rdm['pool_mean']:.2f}±{pool_rdm['pool_sd']:.2f} "
                          f"range={pool_rdm['pool_range']}  "
                          f"boundary_low={pool_rdm['n_boundary_low']} high={pool_rdm['n_boundary_high']}")

    out = {
        'results_by_roi_family_source': results,
        'design': 'L3 LOCO (within-subject W) + L4 RDM (LOO-HC reference, HC pool W encoder)',
        'delta_lambda_sources': DELTA_LAMBDA_BY_FAMILY,
        'K': 6,
        'note': 'Compares to L_behav HC pool g (s5p_hc_pool_g_fit.py) — addresses S4 W-asymmetry justification',
    }
    with open(OUT_DIR / "g_HC_pool_neural.json", 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved: {OUT_DIR / 'g_HC_pool_neural.json'}")


if __name__ == "__main__":
    main()
