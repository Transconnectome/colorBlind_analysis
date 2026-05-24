"""S5 Spearman refit — Nili-faithful (rank-based) L_RDM for L4/L6/L7/L8.

Replaces the cosine-based L_RDM in s5_all_paths_fit.py with Spearman ρ
(1 − ρ as loss). Only re-fits losses that include L_RDM:
  L4_RDM_spearman: 1 − ρ(ΔRDM_sim, ΔRDM_obs)
  L6_neural_composite_sp: 0.5·L_LOCO + 0.5·L4_RDM_spearman
  L7_all_equal_sp: (L1 + L2 + L3 + L4_spearman)/4
  L8_modality_5050_sp: 0.5·L_γ + 0.25·L_LOCO + 0.25·L4_RDM_spearman

L1 (8AFC), L2 (γ), L3 (LOCO), L5 (behav) are unchanged — RDM-free.
For comparison, also recompute their cosine analogues so each fit JSON
carries both metrics at the Spearman-best parameter (and cosine-best
references taken from existing S5 results).

Grid / settings:
  - R+C: g_grid() (61 pts) at 3 Δλ sources per subject (DPS / Boehm / JND-Lamb)
  - 2-Comp: two_comp.BS_GRID × BC_GRID = 26 × 51 = 1326 pts (ASYMMETRIC,
    matches existing S5, NOT S6' symmetric grid)
  - σ = 21° (BEHAV_WEIGHTS reuses S5 default)
  - K = 6 uniform FE (Phase 1 baseline)
  - C_baseline = create_basis_full(K,'fe')[HUE_ANGLES] (matches S5/S6')
  - HC pool: V1 n=7, V4 n=6 (sub-07 dropped) — matches S5
  - spearmanr tie handling: scipy default ('average')

Outputs:
  results/s5_spearman/{subject}_{roi}_sigma21.json
  results/s5_spearman/summary.json
"""
import sys
import json
import time
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import forward_rc, fit_rc_g, compensation_magnitude
from two_comp import forward_2comp, fit_2comp, BS_GRID, BC_GRID
from behav_loss import (
    L_behav_alpha, L_behav_gamma, BEHAV_WEIGHTS, SIGMA_HC,
    load_8afc_per_color, load_jnd_per_pair, compute_hc_jnd_baseline,
)
from neural_loss import (
    L_LOCO, design_from_delta,
    load_amplitudes, load_hc_pool, ROI_K,
    precompute_loco_W_within,
)
from diagnostic_delta_rdm import (
    precompute_hc_W, compute_rdm_correlation, cosine_similarity,
    compute_delta_rdm_obs,
)
from utils_forward_model import create_basis_full, HUE_ANGLES

# Δλ sources (matches S5)
DELTA_LAMBDA_SOURCES = {
    'sub-08': {
        'family': 'deutan',
        'sources': {
            'DPS_lit': 6.0,
            'Boehm_mid': 8.0,
            'JND_Lamb': 6.5,
        },
    },
    'sub-09': {
        'family': 'protan',
        'sources': {
            'DPS_lit': 10.0,
            'Boehm_low': 3.0,
            'JND_Lamb': 1.5,
        },
    },
}

OUT_DIR = SCRIPT_DIR.parent / "results" / "s5_spearman"


# ============================================================================
# Spearman-based L_RDM
# ============================================================================

def _safe_spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman ρ with default scipy tie handling ('average'). 0.0 on degenerate."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if np.std(a) < 1e-15 or np.std(b) < 1e-15:
        return 0.0
    rho, _ = spearmanr(a, b)
    return float(rho) if np.isfinite(rho) else 0.0


def _safe_cosine(a: np.ndarray, b: np.ndarray) -> float:
    val = cosine_similarity(a, b)
    return float(val) if np.isfinite(val) else 0.0


# ============================================================================
# Build loss callables (S5 build_loss_callables clone with Spearman)
# ============================================================================

def build_loss_callables_spearman(subject: str, cvd_amp: np.ndarray,
                                   hc_amps_dict: dict, n_channels: int,
                                   sigma: float = SIGMA_HC):
    """L1/L2/L3/L5 unchanged; L4/L6/L7/L8 use Spearman-based L_RDM.

    Returns 2 dicts:
      losses_sp     : {name: callable} — Spearman variants (L4/L6/L7/L8)
      losses_cos    : {name: callable} — Cosine variants (L4/L6/L7/L8) for cross-metric eval
    Plus the bound rdm helpers (so caller can also compute ρ/cos at any δθ).
    """
    obs_acc = load_8afc_per_color(subject)
    jnd_obs = load_jnd_per_pair(subject)
    hc_baseline, hc_sd = compute_hc_jnd_baseline()

    C_baseline = create_basis_full(n_channels, basis_type='fe')[HUE_ANGLES.astype(int)]

    loco_W_within, _ = precompute_loco_W_within(cvd_amp, C_baseline)
    hc_W, _ = precompute_hc_W(hc_amps_dict, C_baseline)

    # Cache δθ-invariant components
    delta_rdm_obs, _, _, _ = compute_delta_rdm_obs(
        cvd_amp, hc_amps_dict, distance='correlation')

    rdm_baseline_per_hc = {}
    for h, W in hc_W.items():
        Y_b = C_baseline @ W
        rdm_baseline_per_hc[h] = compute_rdm_correlation(Y_b)

    w_alpha, w_gamma = BEHAV_WEIGHTS.get(subject, (0.5, 0.5))

    def _compute_delta_rdm_sim(delta_rc):
        C_shifted = design_from_delta(delta_rc, n_channels=n_channels)
        deltas = []
        for h, W in hc_W.items():
            Y_s = C_shifted @ W
            rdm_s = compute_rdm_correlation(Y_s)
            deltas.append(rdm_s - rdm_baseline_per_hc[h])
        return np.mean(deltas, axis=0)

    # --- shared L1/L2/L3 ---
    def L1(d): return L_behav_alpha(d, obs_acc, sigma)
    def L2(d): return L_behav_gamma(d, jnd_obs, hc_baseline, hc_sd)
    def L3(d): return L_LOCO(d, cvd_amp, loco_W_within, n_channels)

    # --- Spearman L_RDM and composites ---
    def L4_sp(d):
        sim = _compute_delta_rdm_sim(d)
        rho = _safe_spearman(sim, delta_rdm_obs)
        return float(1.0 - rho)

    def L4_cos(d):
        """Cosine variant (for cross-metric reporting)."""
        sim = _compute_delta_rdm_sim(d)
        cos = _safe_cosine(sim, delta_rdm_obs)
        return float(1.0 - cos)

    def L5(d):
        l_a = L1(d) if w_alpha > 0 else 0.0
        l_g = L2(d)
        return w_alpha * l_a + w_gamma * l_g

    def L6_sp(d): return 0.5 * L3(d) + 0.5 * L4_sp(d)
    def L6_cos(d): return 0.5 * L3(d) + 0.5 * L4_cos(d)

    def L7_sp(d): return (L1(d) + L2(d) + L3(d) + L4_sp(d)) / 4.0
    def L7_cos(d): return (L1(d) + L2(d) + L3(d) + L4_cos(d)) / 4.0

    def L8_sp(d): return 0.5 * L2(d) + 0.25 * L3(d) + 0.25 * L4_sp(d)
    def L8_cos(d): return 0.5 * L2(d) + 0.25 * L3(d) + 0.25 * L4_cos(d)

    losses_sp = {
        'L4_RDM_spearman': L4_sp,
        'L6_neural_composite': L6_sp,
        'L7_all_equal': L7_sp,
        'L8_modality_5050': L8_sp,
    }
    losses_cos = {
        'L4_RDM_corr': L4_cos,
        'L6_neural_composite_cos': L6_cos,
        'L7_all_equal_cos': L7_cos,
        'L8_modality_5050_cos': L8_cos,
    }
    components = {
        'L1': L1, 'L2': L2, 'L3': L3,
        'L4_sp': L4_sp, 'L4_cos': L4_cos,
        'compute_delta_rdm_sim': _compute_delta_rdm_sim,
        'delta_rdm_obs': delta_rdm_obs,
        'w_alpha': w_alpha, 'w_gamma': w_gamma,
        'C_baseline': C_baseline,
        'hc_W': hc_W,
        'rdm_baseline_per_hc': rdm_baseline_per_hc,
        'loco_W_within': loco_W_within,
    }
    return losses_sp, losses_cos, components


# ============================================================================
# Per-cell fit
# ============================================================================

def _evaluate_components(delta_rc, components):
    """Return dict of L1/L2/L3/L4_sp/L4_cos at given δθ."""
    return {
        'L1': float(components['L1'](delta_rc)),
        'L2': float(components['L2'](delta_rc)),
        'L3': float(components['L3'](delta_rc)),
        'L4_sp': float(components['L4_sp'](delta_rc)),
        'L4_cos': float(components['L4_cos'](delta_rc)),
    }


def _l_gamma_contribution(delta_rc, components, weight_gamma):
    """% contribution of L_γ to L8 total at given δθ."""
    L2 = components['L2'](delta_rc)
    L3 = components['L3'](delta_rc)
    L4_sp = components['L4_sp'](delta_rc)
    total = weight_gamma * L2 + 0.25 * L3 + 0.25 * L4_sp
    if total <= 0:
        return 0.0
    return float(100.0 * weight_gamma * L2 / total)


def fit_one_subject_roi(subject: str, roi: str, sigma: float = SIGMA_HC) -> dict:
    info = DELTA_LAMBDA_SOURCES.get(subject)
    if info is None:
        raise ValueError(f"No Δλ sources for {subject}")
    cvd_family = info['family']
    K = ROI_K[roi]

    print(f"\n>>> Spearman refit {subject} ROI={roi} (K={K}, σ={sigma})")
    t0 = time.time()

    cvd_amp = load_amplitudes(subject, roi)
    hc_amps = load_hc_pool(roi)

    losses_sp, losses_cos, components = build_loss_callables_spearman(
        subject, cvd_amp, hc_amps, K, sigma=sigma)

    results = {
        'subject': subject,
        'roi': roi,
        'cvd_family': cvd_family,
        'K': K,
        'sigma': sigma,
        'n_hc_used': len(hc_amps),
        'fits': [],
    }

    # === R+C × 3 Δλ × 4 loss (Spearman) ===
    for dl_label, dl_value in info['sources'].items():
        for loss_name, loss_fn in losses_sp.items():
            t_fit = time.time()
            rc_result = fit_rc_g(dl_value, cvd_family, loss_fn)
            g_best = rc_result['g_best']
            delta_rc = forward_rc(dl_value, g_best, cvd_family)
            m_comp = compensation_magnitude(g_best, dl_value)

            # Cross-metric: cosine equivalent at this best δθ
            sim = components['compute_delta_rdm_sim'](delta_rc)
            rho_at_best = _safe_spearman(sim, components['delta_rdm_obs'])
            cos_at_best = _safe_cosine(sim, components['delta_rdm_obs'])

            comp_vals = _evaluate_components(delta_rc, components)
            l_gamma_pct = (_l_gamma_contribution(delta_rc, components, 0.5)
                            if loss_name == 'L8_modality_5050' else None)

            results['fits'].append({
                'model': 'R+C',
                'delta_lambda_source': dl_label,
                'delta_lambda_nm': dl_value,
                'loss_target': loss_name,
                'g_best': g_best,
                'loss_best': rc_result['loss_best'],
                'compensation_magnitude_nm': m_comp,
                'misspecified': rc_result['misspecified'],
                'spearman_rho_best': float(rho_at_best),
                'cosine_at_best': float(cos_at_best),
                'components_at_best': comp_vals,
                'l_gamma_contribution_pct': l_gamma_pct,
                'delta_theta_at_best': delta_rc.tolist(),
                'fit_time_s': round(time.time() - t_fit, 2),
            })

    # === 2-Comp × 4 loss ===
    for loss_name, loss_fn in losses_sp.items():
        t_fit = time.time()
        tc_result = fit_2comp(cvd_family, loss_fn)
        bs = tc_result['beta_s_best']
        bc = tc_result['beta_c_best']
        delta_tc = forward_2comp(bs, bc, cvd_family)

        sim = components['compute_delta_rdm_sim'](delta_tc)
        rho_at_best = _safe_spearman(sim, components['delta_rdm_obs'])
        cos_at_best = _safe_cosine(sim, components['delta_rdm_obs'])
        comp_vals = _evaluate_components(delta_tc, components)
        l_gamma_pct = (_l_gamma_contribution(delta_tc, components, 0.5)
                        if loss_name == 'L8_modality_5050' else None)

        results['fits'].append({
            'model': '2-Comp',
            'loss_target': loss_name,
            'beta_s_best': bs,
            'beta_c_best': bc,
            'loss_best': tc_result['loss_best'],
            'boundary_bs': tc_result['boundary_bs'],
            'boundary_bc': tc_result['boundary_bc'],
            'spearman_rho_best': float(rho_at_best),
            'cosine_at_best': float(cos_at_best),
            'components_at_best': comp_vals,
            'l_gamma_contribution_pct': l_gamma_pct,
            'delta_theta_at_best': delta_tc.tolist(),
            'fit_time_s': round(time.time() - t_fit, 2),
        })

    results['total_time_s'] = round(time.time() - t0, 2)
    print(f"    {subject} {roi} done in {results['total_time_s']:.1f}s "
            f"({len(results['fits'])} fits)")
    return results


def main(rois=('V4', 'V1'), subjects=('sub-08', 'sub-09')):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print(f"S5 Spearman refit — {len(subjects)} subjects × {len(rois)} ROIs")
    print(f"  σ = {SIGMA_HC}°  |  spearmanr tie handling = 'average' (scipy default)")
    print(f"  R+C grid pts = 61 (g∈[0,3] step 0.05)")
    print(f"  2-Comp grid pts = {len(BS_GRID)} × {len(BC_GRID)} = {len(BS_GRID)*len(BC_GRID)} "
          f"(ASYMMETRIC β_s∈[0,50], β_c∈[-50,50] — matches S5, NOT S6')")
    print("=" * 78)

    all_results = {}
    for subject in subjects:
        for roi in rois:
            key = f"{subject}_{roi}_sigma{int(SIGMA_HC)}"
            r = fit_one_subject_roi(subject, roi, sigma=SIGMA_HC)
            all_results[key] = r
            out_path = OUT_DIR / f"{key}.json"
            with open(out_path, 'w') as f:
                json.dump(r, f, indent=2, default=str)
            print(f"    Saved: {out_path}")

    # Master summary
    summary = []
    for key, r in all_results.items():
        for fit in r['fits']:
            summary.append({
                'subject': r['subject'], 'roi': r['roi'], 'sigma': r['sigma'],
                'model': fit['model'],
                'delta_lambda_source': fit.get('delta_lambda_source', '-'),
                'delta_lambda_nm': fit.get('delta_lambda_nm', None),
                'loss_target': fit['loss_target'],
                'loss_best': fit['loss_best'],
                'g_best': fit.get('g_best', None),
                'beta_s_best': fit.get('beta_s_best', None),
                'beta_c_best': fit.get('beta_c_best', None),
                'compensation_magnitude_nm': fit.get('compensation_magnitude_nm', None),
                'spearman_rho_best': fit['spearman_rho_best'],
                'cosine_at_best': fit['cosine_at_best'],
                'l_gamma_contribution_pct': fit.get('l_gamma_contribution_pct', None),
                'misspecified': fit.get('misspecified', None) or fit.get('boundary_bs', None) or fit.get('boundary_bc', None),
            })
    with open(OUT_DIR / "summary.json", 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"\nSaved master summary: {OUT_DIR / 'summary.json'}")
    print(f"  Total fits: {len(summary)}")
    return all_results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--rois', nargs='+', default=['V4', 'V1'])
    parser.add_argument('--subjects', nargs='+', default=['sub-08', 'sub-09'])
    args = parser.parse_args()
    main(rois=tuple(args.rois), subjects=tuple(args.subjects))
