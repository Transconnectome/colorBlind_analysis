"""S9: Retroactive defenses (user catch 2026-05-21).

(1) §6.3 transfer test — 7-fold HC LOO, (X) LOCO + (Z) 8AFC negative transfer
    (Y) ΔRDM 이미 S4 framework에서 V_s-invariant — extension here.
(2) L_behav FPR test for new framework — each HC treated as "fake CVD",
    bootstrap CI of g_HC vs label-permutation null.
"""
import sys
import json
import numpy as np
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import forward_rc, fit_rc_g
from two_comp import forward_2comp, fit_2comp
from behav_loss import (
    L_behav_alpha, L_behav_gamma, SIGMA_HC,
    softmax_pred_8afc, predict_jnd_per_pair,
    load_8afc_per_color, load_jnd_per_pair, compute_hc_jnd_baseline,
    HC_8AFC_SUBJS, HC_JND_SUBJS,
)
from neural_loss import (
    L_LOCO, design_from_delta,
    load_amplitudes, load_hc_pool, ROI_K,
    precompute_loco_W_within,
)
from utils_forward_model import create_basis_full, HUE_ANGLES

OUT_DIR = SCRIPT_DIR.parent / "results" / "s9_retroactive"

CVD_INFO = {
    'sub-08': {'family': 'deutan', 'delta_lambda_dps': 6.0,
               'g_best_l8': 2.25, 'beta_s': 48, 'beta_c': -36},
    'sub-09': {'family': 'protan', 'delta_lambda_dps': 10.0,
               'g_best_l8': 2.60, 'beta_s': 28, 'beta_c': 0},
}


# ============================================================================
# Part 1: §6.3 Transfer test
# ============================================================================

def transfer_test_per_hc(cvd_subj: str, target_hc: str, roi: str,
                          model: str, hc_baseline: dict, hc_sd: dict) -> dict:
    """Apply CVD's params* to held-out HC h.

    (X) LOCO: h's W @ C_shifted(params*) vs h's own pattern → ρ_per_color
    (Z) 8AFC: params* → δθ → softmax pred → vs h's own 8AFC
    Compare to "no shift" baseline (δθ=0).

    Logic: HC h is normal → δθ=0 best fit. Applying CVD's δθ to h should
    DEGRADE fit. Larger degradation = stronger evidence that model δθ
    captures CVD-specific signal.
    """
    cvd_info = CVD_INFO[cvd_subj]
    fam = cvd_info['family']
    dl = cvd_info['delta_lambda_dps']

    # Compute CVD's δθ under the chosen model
    if model == 'R+C':
        delta_cvd = forward_rc(dl, cvd_info['g_best_l8'], fam)
    elif model == '2-Comp':
        delta_cvd = forward_2comp(cvd_info['beta_s'], cvd_info['beta_c'], fam)
    else:
        raise ValueError(f"Unknown model {model}")
    delta_zero = np.zeros(8)

    result = {
        'cvd_subj': cvd_subj, 'target_hc': target_hc, 'roi': roi, 'model': model,
        'delta_lambda_nm': dl, 'cvd_family': fam,
    }

    # === (X) LOCO transfer ===
    try:
        h_amp = load_amplitudes(target_hc, roi)
        # sub-07 hV4 sparse: 16 voxels, skip
        if roi == 'V4' and h_amp.shape[2] < 20:
            result['X_LOCO'] = None
            result['X_LOCO_skip_reason'] = f'sparse V_s={h_amp.shape[2]}'
        else:
            K = ROI_K[roi]
            C_baseline = create_basis_full(K, basis_type='fe')[HUE_ANGLES.astype(int)]
            h_loco_W, _ = precompute_loco_W_within(h_amp, C_baseline)

            loco_zero = L_LOCO(delta_zero, h_amp, h_loco_W, K)  # baseline (HC own fit)
            loco_cvd = L_LOCO(delta_cvd, h_amp, h_loco_W, K)  # transfer
            result['X_LOCO'] = {
                'L_LOCO_baseline_delta0': float(loco_zero),
                'L_LOCO_transfer_cvd_delta': float(loco_cvd),
                'transfer_degradation': float(loco_cvd - loco_zero),
                'degradation_ratio': float(loco_cvd / max(loco_zero, 1e-9)),
            }
    except FileNotFoundError:
        result['X_LOCO'] = None
        result['X_LOCO_skip_reason'] = 'no data'

    # === (Z) 8AFC transfer ===
    if target_hc in HC_8AFC_SUBJS:
        h_obs_acc = load_8afc_per_color(target_hc)
        L_a_zero = L_behav_alpha(delta_zero, h_obs_acc, SIGMA_HC)
        L_a_cvd = L_behav_alpha(delta_cvd, h_obs_acc, SIGMA_HC)
        result['Z_8AFC'] = {
            'L_alpha_baseline_delta0': float(L_a_zero),
            'L_alpha_transfer_cvd_delta': float(L_a_cvd),
            'transfer_degradation': float(L_a_cvd - L_a_zero),
            'degradation_ratio': float(L_a_cvd / max(L_a_zero, 1e-9)),
        }
    else:
        result['Z_8AFC'] = None

    # === JND transfer (L_γ) ===
    h_jnd = load_jnd_per_pair(target_hc)
    L_g_zero = L_behav_gamma(delta_zero, h_jnd, hc_baseline, hc_sd)
    L_g_cvd = L_behav_gamma(delta_cvd, h_jnd, hc_baseline, hc_sd)
    result['Y_JND'] = {
        'L_gamma_baseline_delta0': float(L_g_zero),
        'L_gamma_transfer_cvd_delta': float(L_g_cvd),
        'transfer_degradation': float(L_g_cvd - L_g_zero),
        'degradation_ratio': float(L_g_cvd / max(L_g_zero, 1e-9)),
    }
    return result


def transfer_test_all(roi: str = 'V4') -> dict:
    """7-fold HC transfer test for both CVD subjects × both models."""
    hc_baseline, hc_sd = compute_hc_jnd_baseline()
    all_results = []
    for cvd in ['sub-08', 'sub-09']:
        for model in ['R+C', '2-Comp']:
            for h in HC_JND_SUBJS:
                r = transfer_test_per_hc(cvd, h, roi, model, hc_baseline, hc_sd)
                all_results.append(r)
    return all_results


def summarize_transfer(transfer_results: list) -> dict:
    """Summarize transfer test across 7 HC folds.

    Strong evidence: CVD's δθ DEGRADES HC fit consistently (ratio > 1 across HCs).
    """
    summary = {}
    for cvd in ['sub-08', 'sub-09']:
        for model in ['R+C', '2-Comp']:
            key = f"{cvd}_{model}"
            subset = [r for r in transfer_results if r['cvd_subj'] == cvd and r['model'] == model]

            # LOCO ratios
            x_ratios = [r['X_LOCO']['degradation_ratio'] for r in subset
                        if r.get('X_LOCO')]
            y_ratios = [r['Y_JND']['degradation_ratio'] for r in subset]
            z_ratios = [r['Z_8AFC']['degradation_ratio'] for r in subset
                        if r.get('Z_8AFC')]

            def stats(arr, name):
                a = np.array(arr)
                return {
                    'name': name, 'n': len(a),
                    'mean': float(np.mean(a)) if len(a) > 0 else None,
                    'median': float(np.median(a)) if len(a) > 0 else None,
                    'min': float(np.min(a)) if len(a) > 0 else None,
                    'max': float(np.max(a)) if len(a) > 0 else None,
                    'frac_above_1': float(np.mean(a > 1.0)) if len(a) > 0 else None,
                }

            summary[key] = {
                'X_LOCO_ratio_across_HCs': stats(x_ratios, 'X_LOCO'),
                'Y_JND_ratio_across_HCs': stats(y_ratios, 'Y_JND'),
                'Z_8AFC_ratio_across_HCs': stats(z_ratios, 'Z_8AFC'),
            }
    return summary


# ============================================================================
# Part 2: L_behav FPR test — new framework
# ============================================================================

def fit_g_fake_cvd(fake_cvd_hc: str, cvd_family: str, delta_lambda: float,
                    hc_baseline: dict, hc_sd: dict) -> float:
    """Treat HC as if it were a CVD with given family + Δλ. Fit g on L_behav."""
    obs_acc = load_8afc_per_color(fake_cvd_hc) if fake_cvd_hc in HC_8AFC_SUBJS else None
    jnd_obs = load_jnd_per_pair(fake_cvd_hc)

    if obs_acc is not None:
        w_a, w_g = 0.5, 0.5

        def L_behav(delta_rc):
            return (w_a * L_behav_alpha(delta_rc, obs_acc, SIGMA_HC)
                    + w_g * L_behav_gamma(delta_rc, jnd_obs, hc_baseline, hc_sd))
    else:
        w_a, w_g = 0.0, 1.0

        def L_behav(delta_rc):
            return L_behav_gamma(delta_rc, jnd_obs, hc_baseline, hc_sd)

    return fit_rc_g(delta_lambda, cvd_family, L_behav)['g_best']


def l_behav_fpr_test(B: int = 1000, seed: int = 42) -> dict:
    """For each HC, fit g as if HC were CVD. Compute fraction of "HC-as-CVD" g
    that exceed CVD's actual g_best_l8 (=> false positive)."""
    hc_baseline, hc_sd = compute_hc_jnd_baseline()
    rng = np.random.default_rng(seed)
    results = {}

    for cvd_subj in ['sub-08', 'sub-09']:
        info = CVD_INFO[cvd_subj]
        fam = info['family']
        dl = info['delta_lambda_dps']
        cvd_g = info['g_best_l8']

        # Point fits: each HC treated as "fake CVD" of same family
        hc_g_point = {}
        for hc in HC_JND_SUBJS:
            hc_g_point[hc] = fit_g_fake_cvd(hc, fam, dl, hc_baseline, hc_sd)

        # FPR: fraction of HCs with g_HC ≥ CVD's g (at point estimate)
        hc_gs = np.array(list(hc_g_point.values()))
        fpr_point = float(np.mean(hc_gs >= cvd_g))

        # Permutation null: shuffle HC labels (which HC is "CVD") B times,
        # for each shuffle, draw 1 HC randomly to be "CVD", fit g, compare to
        # remaining HC pool. Compute Z of "CVD-impostor" g vs pool.
        # Simpler: compute g_HC distribution, ask if CVD g is within HC range
        # under bootstrap with replacement of HC.
        boot_hc_means = []
        for b in range(B):
            sampled = rng.choice(HC_JND_SUBJS, size=len(HC_JND_SUBJS), replace=True)
            gs = [hc_g_point[s] for s in sampled]
            boot_hc_means.append(np.mean(gs))
        boot_arr = np.array(boot_hc_means)
        # Effective p: prob that bootstrap HC mean ≥ CVD g
        p_hc_exceeds_cvd = float(np.mean(boot_arr >= cvd_g))

        results[cvd_subj] = {
            'cvd_subj': cvd_subj, 'cvd_g': cvd_g, 'family': fam, 'delta_lambda_nm': dl,
            'hc_g_point_fits': hc_g_point,
            'hc_g_mean': float(np.mean(hc_gs)),
            'hc_g_max': float(np.max(hc_gs)),
            'hc_g_n_exceed_cvd': int(np.sum(hc_gs >= cvd_g)),
            'fpr_point': fpr_point,
            'bootstrap_hc_mean_exceeds_cvd_p': p_hc_exceeds_cvd,
            'B_bootstrap': B,
        }
    return results


# ============================================================================
# Main
# ============================================================================

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("S9 Retroactive defenses")
    print("=" * 78)

    # (1) Transfer test §6.3
    print("\n--- (1) §6.3 Transfer test (HC LOO) ---")
    for roi in ['V4', 'V1']:
        print(f"\nROI = {roi}:")
        results = transfer_test_all(roi=roi)
        summary = summarize_transfer(results)

        for key, s in summary.items():
            cvd, model = key.split('_', 1)
            print(f"\n  {cvd} model={model}:")
            for metric_name, label in [('X_LOCO', '(X) LOCO'),
                                        ('Y_JND', '(Y) JND'),
                                        ('Z_8AFC', '(Z) 8AFC')]:
                key_full = f"{metric_name}_ratio_across_HCs"
                s_m = s[key_full]
                if s_m['n'] == 0:
                    print(f"    {label}: N=0 (no data)")
                    continue
                print(f"    {label}: ratio mean={s_m['mean']:.3f}, "
                      f"median={s_m['median']:.3f}, "
                      f"range=[{s_m['min']:.3f}, {s_m['max']:.3f}], "
                      f"frac>1={s_m['frac_above_1']:.2f} (N={s_m['n']})")

        with open(OUT_DIR / f"transfer_test_{roi}.json", 'w') as f:
            json.dump({'results': results, 'summary': summary}, f, indent=2, default=str)

    # (2) L_behav FPR test
    print("\n--- (2) L_behav framework FPR test ---")
    fpr = l_behav_fpr_test(B=1000)
    for cvd_subj, r in fpr.items():
        print(f"\n  {cvd_subj} (CVD g* = {r['cvd_g']:.2f}, family={r['family']}):")
        print(f"    HC g pool point: mean={r['hc_g_mean']:.3f}, max={r['hc_g_max']:.3f}")
        print(f"    N HC with g ≥ CVD g: {r['hc_g_n_exceed_cvd']}/{len(HC_JND_SUBJS)}")
        print(f"    Point FPR (HC g ≥ CVD g) = {r['fpr_point']:.3f}")
        print(f"    Bootstrap (HC mean ≥ CVD g) p = {r['bootstrap_hc_mean_exceeds_cvd_p']:.3f}")
        print(f"    Individual HC g_fits: {r['hc_g_point_fits']}")

    with open(OUT_DIR / "fpr_test.json", 'w') as f:
        json.dump(fpr, f, indent=2, default=str)

    print(f"\nSaved to {OUT_DIR}")


if __name__ == "__main__":
    main()
