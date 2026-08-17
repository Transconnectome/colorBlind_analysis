"""S8: Selection rule + Cross-subtype + Form C permutation.

Three deliverables:
  (1) Model-loss selection metrics (AICc, BIC, 8AFC correlation) per fit
  (2) Cross-subtype train-test (sub-08↔sub-09) for subtype-specific filter evidence
  (3) Form C full-grid permutation null (local B=100 quick; full B=1000 deferred to SLURM)

Output: results/s8_final/{selection_table, cross_subtype, perm_null}.json
"""
import sys
import json
import numpy as np
from pathlib import Path
from scipy.stats import pearsonr

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import forward_rc, fit_rc_g
from two_comp import forward_2comp, fit_2comp
from behav_loss import (
    L_behav_alpha, L_behav_gamma, SIGMA_HC,
    load_8afc_per_color, load_jnd_per_pair, compute_hc_jnd_baseline,
    softmax_pred_8afc, HUES,
)

S5_DIR = SCRIPT_DIR.parent / "results" / "s5_all_paths"
OUT_DIR = SCRIPT_DIR.parent / "results" / "s8_final"

CVD_INFO = {
    'sub-08': {'family': 'deutan', 'delta_lambda_dps': 6.0},
    'sub-09': {'family': 'protan', 'delta_lambda_dps': 10.0},
}


def compute_8afc_corr(delta_rc: np.ndarray, obs_acc: np.ndarray, sigma: float = SIGMA_HC) -> float:
    """Pearson correlation between predicted 8AFC accuracy and observed."""
    P = softmax_pred_8afc(delta_rc, sigma)
    pred_acc = np.diagonal(P)
    if np.std(pred_acc) < 1e-10 or np.std(obs_acc) < 1e-10:
        return 0.0
    r, _ = pearsonr(pred_acc, obs_acc)
    return float(r) if np.isfinite(r) else 0.0


def compute_aicc_bic(rss: float, n: int, k: int) -> tuple:
    """AICc and BIC for normal-error model.

    n = number of data points, k = number of free parameters
    """
    if n <= k + 1 or rss <= 0:
        return float('inf'), float('inf')
    aic = n * np.log(rss / n) + 2 * k
    aicc = aic + 2 * k * (k + 1) / (n - k - 1)
    bic = n * np.log(rss / n) + k * np.log(n)
    return float(aicc), float(bic)


# ============================================================================
# Selection metrics from S5 results
# ============================================================================

def compute_selection_metrics():
    """For each S5 fit, compute AICc/BIC (vs JND residual) + 8AFC corr."""
    hc_baseline, hc_sd = compute_hc_jnd_baseline()
    all_results = []

    for json_file in sorted(S5_DIR.glob("sub-*_sigma21.json")):
        with open(json_file) as f:
            d = json.load(f)
        subject = d['subject']
        roi = d['roi']
        obs_acc = load_8afc_per_color(subject)
        jnd_obs = load_jnd_per_pair(subject)

        for fit in d['fits']:
            delta_rc = np.array(fit['delta_theta_at_best'])

            # JND residual sum of squares (8 pairs)
            from behav_loss import predict_jnd_per_pair
            pred_jnd = predict_jnd_per_pair(delta_rc, hc_baseline)
            rss_jnd = float(sum((pred_jnd[p] - jnd_obs[p]) ** 2 for p in pred_jnd
                                  if jnd_obs.get(p) is not None))
            n_jnd = sum(1 for p in pred_jnd if jnd_obs.get(p) is not None)

            # 8AFC residual
            P = softmax_pred_8afc(delta_rc)
            pred_acc = np.diagonal(P)
            rss_8afc = float(np.sum((pred_acc - obs_acc) ** 2))

            k = 1 if fit['model'] == 'R+C' else 2
            aicc_jnd, bic_jnd = compute_aicc_bic(rss_jnd, n_jnd, k)
            aicc_8afc, bic_8afc = compute_aicc_bic(rss_8afc, 8, k)
            corr_8afc = compute_8afc_corr(delta_rc, obs_acc)

            all_results.append({
                'subject': subject, 'roi': roi,
                'model': fit['model'],
                'delta_lambda_source': fit.get('delta_lambda_source', '-'),
                'loss_target': fit['loss_target'],
                'k_params': k,
                'rss_jnd': rss_jnd,
                'rss_8afc': rss_8afc,
                'aicc_jnd': aicc_jnd,
                'bic_jnd': bic_jnd,
                'aicc_8afc': aicc_8afc,
                'bic_8afc': bic_8afc,
                'corr_8afc': corr_8afc,
                'loss_best_S5': fit['loss_best'],
                'g_best': fit.get('g_best', None),
                'beta_s_best': fit.get('beta_s_best', None),
                'beta_c_best': fit.get('beta_c_best', None),
                'misspecified': fit.get('misspecified', None) or fit.get('boundary_bs', None) or fit.get('boundary_bc', None),
            })

    return all_results


def print_winners(selection: list):
    """Print AICc, BIC, 8AFC corr winners per (subject, ROI)."""
    keys = sorted(set((r['subject'], r['roi']) for r in selection))
    for subj, roi in keys:
        subset = [r for r in selection if r['subject'] == subj and r['roi'] == roi
                  and r['loss_target'] == 'L8_modality_5050']  # under L8 primary
        if not subset:
            continue
        # Best by each criterion (lower AICc/BIC = better, higher corr = better)
        best_aicc_jnd = min(subset, key=lambda r: r['aicc_jnd'])
        best_bic_jnd = min(subset, key=lambda r: r['bic_jnd'])
        best_corr = max(subset, key=lambda r: r['corr_8afc'])
        print(f"\n  {subj} {roi} (L8 primary):")
        print(f"    AICc(JND) winner: {best_aicc_jnd['model']} ({best_aicc_jnd['delta_lambda_source']}) "
              f"AICc={best_aicc_jnd['aicc_jnd']:.2f}")
        print(f"    BIC(JND) winner:  {best_bic_jnd['model']} ({best_bic_jnd['delta_lambda_source']}) "
              f"BIC={best_bic_jnd['bic_jnd']:.2f}")
        print(f"    8AFC corr winner: {best_corr['model']} ({best_corr['delta_lambda_source']}) "
              f"r={best_corr['corr_8afc']:+.3f}")


# ============================================================================
# Cross-subtype train-test (§6.4)
# ============================================================================

def cross_subtype_test():
    """Train sub-08 → apply to sub-09 (and reverse): subtype-specific filter evidence.

    Apply trained R+C g* with target subject's Δλ_DPS and family.
    Predict target's behavioral/neural data → compute error.
    Compare with within-subject fit error.
    """
    hc_baseline, hc_sd = compute_hc_jnd_baseline()
    # Load S5 results (V4 primary)
    s5 = {}
    for json_file in sorted(S5_DIR.glob("sub-*_V4_sigma21.json")):
        with open(json_file) as f:
            d = json.load(f)
        s5[d['subject']] = d

    cross_results = {}
    for train_subj, target_subj in [('sub-08', 'sub-09'), ('sub-09', 'sub-08')]:
        train_info = CVD_INFO[train_subj]
        target_info = CVD_INFO[target_subj]

        # Get train subject's L8 R+C fit under their DPS Δλ
        train_fits = s5[train_subj]['fits']
        train_rc_l8 = [f for f in train_fits if f['model'] == 'R+C'
                       and f.get('delta_lambda_source') == 'DPS_lit'
                       and f['loss_target'] == 'L8_modality_5050'][0]
        train_g = train_rc_l8['g_best']

        # Apply train's g to TARGET's family + Δλ
        # Question: does the same cortical g work for the OTHER subtype?
        delta_pred = forward_rc(target_info['delta_lambda_dps'], train_g, target_info['family'])

        # Compute target's losses under this transferred δθ
        obs_acc_target = load_8afc_per_color(target_subj)
        jnd_obs_target = load_jnd_per_pair(target_subj)

        L_alpha_cross = L_behav_alpha(delta_pred, obs_acc_target, SIGMA_HC)
        L_gamma_cross = L_behav_gamma(delta_pred, jnd_obs_target, hc_baseline, hc_sd)
        # Use target's behavioral weights
        if target_subj == 'sub-09':
            w_alpha, w_gamma = 0.0, 1.0
        else:
            w_alpha, w_gamma = 0.5, 0.5
        L_behav_cross = w_alpha * L_alpha_cross + w_gamma * L_gamma_cross

        # Within-subject target fit (L_behav at target's own g*)
        target_fits = s5[target_subj]['fits']
        target_rc_l8 = [f for f in target_fits if f['model'] == 'R+C'
                        and f.get('delta_lambda_source') == 'DPS_lit'
                        and f['loss_target'] == 'L8_modality_5050'][0]
        target_g = target_rc_l8['g_best']
        delta_within = forward_rc(target_info['delta_lambda_dps'], target_g, target_info['family'])
        L_alpha_within = L_behav_alpha(delta_within, obs_acc_target, SIGMA_HC)
        L_gamma_within = L_behav_gamma(delta_within, jnd_obs_target, hc_baseline, hc_sd)
        L_behav_within = w_alpha * L_alpha_within + w_gamma * L_gamma_within

        cross_results[f"{train_subj}_to_{target_subj}"] = {
            'train_subject': train_subj,
            'target_subject': target_subj,
            'train_g_used': train_g,
            'target_g_own': target_g,
            'delta_pred_at_target_subtype': delta_pred.tolist(),
            'L_behav_cross': L_behav_cross,
            'L_behav_within_target': L_behav_within,
            'error_ratio_cross_vs_within': L_behav_cross / max(L_behav_within, 1e-9),
            'L_alpha_cross': L_alpha_cross,
            'L_alpha_within': L_alpha_within,
            'L_gamma_cross': L_gamma_cross,
            'L_gamma_within': L_gamma_within,
        }
    return cross_results


# ============================================================================
# Form C: full-grid permutation null (local B=100 quick)
# ============================================================================

def permutation_null(subject: str, B: int = 100, seed: int = 42) -> dict:
    """Permute color labels in CVD's behavioral data → re-fit g → null distribution.

    For each permutation: shuffle color indices in obs_acc + jnd_obs.
    Re-fit g on L_behav (subject-specific weights, DPS Δλ).
    Record min loss + argmin g per permutation.

    Compare real-data argmin loss vs null.
    """
    hc_baseline, hc_sd = compute_hc_jnd_baseline()
    info = CVD_INFO[subject]
    fam = info['family']
    dl = info['delta_lambda_dps']

    obs_acc = load_8afc_per_color(subject)
    jnd_obs = load_jnd_per_pair(subject)

    if subject == 'sub-09':
        w_alpha, w_gamma = 0.0, 1.0
    else:
        w_alpha, w_gamma = 0.5, 0.5

    pairs = list(jnd_obs.keys())
    rng = np.random.default_rng(seed)

    null_losses = []
    null_gs = []
    for b in range(B):
        # Permute 8 color accuracies
        perm_idx = rng.permutation(8)
        obs_acc_perm = obs_acc[perm_idx]
        # Permute JND pair values (assign 8 obs values to 8 pair names randomly)
        pair_vals = np.array([jnd_obs[p] for p in pairs])
        perm_pair_vals = pair_vals[rng.permutation(len(pairs))]
        jnd_perm = dict(zip(pairs, perm_pair_vals))

        def L_behav_perm(delta_rc):
            l_a = L_behav_alpha(delta_rc, obs_acc_perm, SIGMA_HC) if w_alpha > 0 else 0.0
            l_g = L_behav_gamma(delta_rc, jnd_perm, hc_baseline, hc_sd)
            return w_alpha * l_a + w_gamma * l_g

        fit = fit_rc_g(dl, fam, L_behav_perm)
        null_losses.append(fit['loss_best'])
        null_gs.append(fit['g_best'])

    # Real-data
    def L_behav_real(delta_rc):
        l_a = L_behav_alpha(delta_rc, obs_acc, SIGMA_HC) if w_alpha > 0 else 0.0
        l_g = L_behav_gamma(delta_rc, jnd_obs, hc_baseline, hc_sd)
        return w_alpha * l_a + w_gamma * l_g

    real_fit = fit_rc_g(dl, fam, L_behav_real)
    null_losses = np.array(null_losses)
    null_gs = np.array(null_gs)
    p_value = float(np.mean(null_losses <= real_fit['loss_best']))

    return {
        'subject': subject,
        'B_permutations': B,
        'real_loss': real_fit['loss_best'],
        'real_g': real_fit['g_best'],
        'null_loss_mean': float(np.mean(null_losses)),
        'null_loss_median': float(np.median(null_losses)),
        'null_loss_min': float(null_losses.min()),
        'null_loss_p2.5': float(np.percentile(null_losses, 2.5)),
        'null_g_mean': float(np.mean(null_gs)),
        'null_g_sd': float(np.std(null_gs, ddof=1)),
        'p_value': p_value,
    }


# ============================================================================
# Main
# ============================================================================

def main(B_perm: int = 100):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("S8 Final — Selection metrics + Cross-subtype + Form C permutation")
    print("=" * 78)

    # (1) Selection metrics
    print("\n--- (1) Selection metrics ---")
    selection = compute_selection_metrics()
    with open(OUT_DIR / "selection_metrics.json", 'w') as f:
        json.dump(selection, f, indent=2, default=str)
    print(f"  Computed {len(selection)} fits' AICc/BIC/8AFC corr")
    print_winners(selection)

    # (2) Cross-subtype
    print("\n--- (2) Cross-subtype train-test ---")
    cross = cross_subtype_test()
    with open(OUT_DIR / "cross_subtype.json", 'w') as f:
        json.dump(cross, f, indent=2, default=str)
    for label, r in cross.items():
        print(f"\n  {label}:")
        print(f"    train_g_used = {r['train_g_used']:.2f}, target_g_own = {r['target_g_own']:.2f}")
        print(f"    L_behav cross = {r['L_behav_cross']:.4f}, within = {r['L_behav_within_target']:.4f}")
        print(f"    Error ratio (cross/within) = {r['error_ratio_cross_vs_within']:.3f}")
        print(f"    → If >> 1: subtype-specific; if ≈ 1: subtype-generic")

    # (3) Form C permutation null
    print(f"\n--- (3) Form C permutation null (B={B_perm}) ---")
    perm_results = {}
    for subj in ['sub-08', 'sub-09']:
        r = permutation_null(subj, B=B_perm)
        perm_results[subj] = r
        print(f"\n  {subj}:")
        print(f"    Real loss = {r['real_loss']:.4f}, real g* = {r['real_g']:.2f}")
        print(f"    Null loss mean ± SD = {r['null_loss_mean']:.4f} ± SD")
        print(f"    Null g mean = {r['null_g_mean']:.2f} ± {r['null_g_sd']:.2f}")
        print(f"    p-value = {r['p_value']:.4f}")
    with open(OUT_DIR / "perm_null.json", 'w') as f:
        json.dump(perm_results, f, indent=2, default=str)

    print(f"\nAll S8 results saved to: {OUT_DIR}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--B-perm', type=int, default=100)
    args = parser.parse_args()
    main(B_perm=args.B_perm)
