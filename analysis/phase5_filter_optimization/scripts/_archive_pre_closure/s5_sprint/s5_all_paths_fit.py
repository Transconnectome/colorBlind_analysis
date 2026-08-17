"""S5: All-paths fit — R+C (3 Δλ × 8 loss) + 2-Comp (8 loss) per subject per ROI.

Outputs comprehensive fit matrix:
  results/s5_all_paths/{subject}_{roi}.json

Each entry contains:
  - Model (R+C / 2-Comp), Δλ_source (R+C only), loss target, best params
  - Loss landscape diagnostics (boundary hit, monotonicity, etc.)
  - σ sensitivity sweep (default σ=21, sweep {15,18,21,24,28})

Primary fit: σ=21°. σ sweep separate.

Reference δθ at fit: paper-level filter design source.
"""
import sys
import json
import time
import numpy as np
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import forward_rc, fit_rc_g, compensation_magnitude
from two_comp import forward_2comp, fit_2comp, BS_GRID, BC_GRID
from behav_loss import (
    L_behav_alpha, L_behav_gamma, BEHAV_WEIGHTS, SIGMA_HC,
    load_8afc_per_color, load_jnd_per_pair, compute_hc_jnd_baseline,
)
from neural_loss import (
    L_LOCO, L_RDM, design_from_delta,
    load_amplitudes, load_hc_pool, ROI_K,
    precompute_loco_W_within,
)
from diagnostic_delta_rdm import precompute_hc_W
from utils_forward_model import create_basis_full, HUE_ANGLES

# Δλ sources from S1
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

OUT_DIR = SCRIPT_DIR.parent / "results" / "s5_all_paths"
SIGMA_VARIANTS = [15.0, 18.0, 21.0, 24.0, 28.0]  # primary σ=21°


def build_loss_callables(subject: str, cvd_amp: np.ndarray, hc_amps_dict: dict,
                          n_channels: int, sigma: float = SIGMA_HC):
    """Construct (L1..L8) callables that take δθ 8-vec → float loss."""
    obs_acc = load_8afc_per_color(subject)
    jnd_obs = load_jnd_per_pair(subject)
    hc_baseline, hc_sd = compute_hc_jnd_baseline()

    C_baseline = create_basis_full(n_channels, basis_type='fe')[HUE_ANGLES.astype(int)]

    # Neural pre-computes
    loco_W_within, _ = precompute_loco_W_within(cvd_amp, C_baseline)
    hc_W, _ = precompute_hc_W(hc_amps_dict, C_baseline)

    # Cache δθ-invariant components (ΔRDM_obs, baselines)
    from diagnostic_delta_rdm import compute_delta_rdm_obs, compute_rdm_correlation
    from neural_loss import cosine_similarity
    delta_rdm_obs, _, _, _ = compute_delta_rdm_obs(cvd_amp, hc_amps_dict, distance='correlation')

    # Pre-compute RDM_baseline per HC (C_baseline @ W_h)
    rdm_baseline_per_hc = {}
    for h, W in hc_W.items():
        Y_b = C_baseline @ W
        rdm_baseline_per_hc[h] = compute_rdm_correlation(Y_b)

    # Subject-specific α/γ weights (L8 uniform 정의 위해 w_alpha=0 in L8 specifically)
    w_alpha, w_gamma = BEHAV_WEIGHTS.get(subject, (0.5, 0.5))

    def L1(delta_rc):
        return L_behav_alpha(delta_rc, obs_acc, sigma)

    def L2(delta_rc):
        return L_behav_gamma(delta_rc, jnd_obs, hc_baseline, hc_sd)

    def L3(delta_rc):
        return L_LOCO(delta_rc, cvd_amp, loco_W_within, n_channels)

    def L4(delta_rc):
        """L_RDM with cached ΔRDM_obs and RDM_baseline."""
        C_shifted = design_from_delta(delta_rc, n_channels=n_channels)
        # Per-HC ΔRDM_sim using cached baselines
        delta_rdm_per_hc = []
        for h, W in hc_W.items():
            Y_s = C_shifted @ W
            rdm_s = compute_rdm_correlation(Y_s)
            delta_rdm_per_hc.append(rdm_s - rdm_baseline_per_hc[h])
        delta_rdm_sim = np.mean(delta_rdm_per_hc, axis=0)
        cos = cosine_similarity(delta_rdm_sim, delta_rdm_obs)
        if not np.isfinite(cos):
            cos = 0.0
        return float(1.0 - cos)

    def L5(delta_rc):
        """L_behav composite (subject-specific α weight)."""
        l_a = L1(delta_rc) if w_alpha > 0 else 0.0
        l_g = L2(delta_rc)
        return w_alpha * l_a + w_gamma * l_g

    def L6(delta_rc):
        """L_neural composite (modality-equal)."""
        return 0.5 * L3(delta_rc) + 0.5 * L4(delta_rc)

    def L7(delta_rc):
        """L_all_equal (1/4 each individual)."""
        return (L1(delta_rc) + L2(delta_rc) + L3(delta_rc) + L4(delta_rc)) / 4.0

    def L8(delta_rc):
        """L8 PRIMARY — uniform across subjects (advisor catch).
        L8 = 0.5·L_γ + 0.25·L_LOCO + 0.25·L_RDM (drop L_α for uniformity)."""
        return 0.5 * L2(delta_rc) + 0.25 * L3(delta_rc) + 0.25 * L4(delta_rc)

    return {
        'L1_behav_alpha': L1,
        'L2_behav_gamma': L2,
        'L3_LOCO': L3,
        'L4_RDM_corr': L4,
        'L5_behav_composite': L5,
        'L6_neural_composite': L6,
        'L7_all_equal': L7,
        'L8_modality_5050': L8,
    }


def fit_one_subject_roi(subject: str, roi: str, sigma: float = SIGMA_HC) -> dict:
    """All-paths fit for one (subject, ROI) at given σ. Returns dict."""
    info = DELTA_LAMBDA_SOURCES.get(subject)
    if info is None:
        raise ValueError(f"No Δλ sources for {subject}")
    cvd_family = info['family']
    K = ROI_K[roi]

    print(f"\n>>> Fitting {subject} ROI={roi} (K={K}, σ={sigma})")
    t0 = time.time()

    # Load data
    cvd_amp = load_amplitudes(subject, roi)
    hc_amps = load_hc_pool(roi)

    # Build all 8 loss callables
    losses = build_loss_callables(subject, cvd_amp, hc_amps, K, sigma=sigma)

    results = {
        'subject': subject,
        'roi': roi,
        'cvd_family': cvd_family,
        'K': K,
        'sigma': sigma,
        'n_hc_used': len(hc_amps),
        'fits': [],
    }

    # === R+C × 3 Δλ × 8 loss ===
    for dl_label, dl_value in info['sources'].items():
        for loss_name, loss_fn in losses.items():
            t_fit = time.time()
            rc_result = fit_rc_g(dl_value, cvd_family, loss_fn)
            g_best = rc_result['g_best']
            delta_rc = forward_rc(dl_value, g_best, cvd_family)
            m_comp = compensation_magnitude(g_best, dl_value)
            fit_record = {
                'model': 'R+C',
                'delta_lambda_source': dl_label,
                'delta_lambda_nm': dl_value,
                'loss_target': loss_name,
                'g_best': g_best,
                'loss_best': rc_result['loss_best'],
                'compensation_magnitude_nm': m_comp,
                'misspecified': rc_result['misspecified'],
                'delta_theta_at_best': delta_rc.tolist(),
                'fit_time_s': round(time.time() - t_fit, 2),
            }
            results['fits'].append(fit_record)

    # === 2-Comp × 8 loss ===
    for loss_name, loss_fn in losses.items():
        t_fit = time.time()
        tc_result = fit_2comp(cvd_family, loss_fn)
        bs = tc_result['beta_s_best']
        bc = tc_result['beta_c_best']
        delta_tc = forward_2comp(bs, bc, cvd_family)
        fit_record = {
            'model': '2-Comp',
            'loss_target': loss_name,
            'beta_s_best': bs,
            'beta_c_best': bc,
            'loss_best': tc_result['loss_best'],
            'boundary_bs': tc_result['boundary_bs'],
            'boundary_bc': tc_result['boundary_bc'],
            'delta_theta_at_best': delta_tc.tolist(),
            'fit_time_s': round(time.time() - t_fit, 2),
        }
        results['fits'].append(fit_record)

    results['total_time_s'] = round(time.time() - t0, 2)
    print(f"    {subject} {roi} done in {results['total_time_s']:.1f}s "
          f"({len(results['fits'])} fits)")
    return results


def main(rois=('V4', 'V1'), subjects=('sub-08', 'sub-09'),
         do_sigma_sweep=False):
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 78)
    print(f"S5 all-paths fit — {len(subjects)} subjects × {len(rois)} ROIs")
    print(f"  Primary σ = {SIGMA_HC}°")
    if do_sigma_sweep:
        print(f"  σ sweep: {SIGMA_VARIANTS}")
    print("=" * 78)

    all_results = {}
    for subject in subjects:
        for roi in rois:
            # Primary fit
            key = f"{subject}_{roi}_sigma{int(SIGMA_HC)}"
            r = fit_one_subject_roi(subject, roi, sigma=SIGMA_HC)
            all_results[key] = r
            out_path = OUT_DIR / f"{key}.json"
            with open(out_path, 'w') as f:
                json.dump(r, f, indent=2, default=str)
            print(f"    Saved: {out_path}")

            # σ sensitivity sweep (optional)
            if do_sigma_sweep:
                for sg in SIGMA_VARIANTS:
                    if sg == SIGMA_HC:
                        continue
                    key_s = f"{subject}_{roi}_sigma{int(sg)}"
                    r_s = fit_one_subject_roi(subject, roi, sigma=sg)
                    all_results[key_s] = r_s
                    with open(OUT_DIR / f"{key_s}.json", 'w') as f:
                        json.dump(r_s, f, indent=2, default=str)

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
    parser.add_argument('--sigma-sweep', action='store_true')
    args = parser.parse_args()
    main(rois=tuple(args.rois), subjects=tuple(args.subjects),
         do_sigma_sweep=args.sigma_sweep)
