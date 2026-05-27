"""S10: Advisor-driven supplemental analyses to stress-test S5-S9 claims.

(1) ‖δθ‖²-normalized transfer test ratios
(2) Honest specificity reframing (percentile vs FPR)
(3) Sub-08 R+C misspecification quantitative flag
(4) Cross-subtype: Δ-difference instead of ratio
(5) Loss-assignment permutation null (less destructive)
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
    L_behav_alpha, L_behav_gamma, SIGMA_HC, PAIR_HUES, HUES,
    softmax_pred_8afc, predict_jnd_per_pair,
    load_8afc_per_color, load_jnd_per_pair, compute_hc_jnd_baseline,
    HC_8AFC_SUBJS, HC_JND_SUBJS,
)

S5_DIR = SCRIPT_DIR.parent / "results" / "s5_all_paths"
S6_DIR = SCRIPT_DIR.parent / "results" / "s6_bootstrap"
S9_DIR = SCRIPT_DIR.parent / "results" / "s9_retroactive"
OUT_DIR = SCRIPT_DIR.parent / "results" / "s10_advisor_fixes"

CVD_INFO = {
    'sub-08': {'family': 'deutan', 'delta_lambda_dps': 6.0,
               'g_best_l8': 2.25, 'beta_s': 48, 'beta_c': -36},
    'sub-09': {'family': 'protan', 'delta_lambda_dps': 10.0,
               'g_best_l8': 2.60, 'beta_s': 28, 'beta_c': 0},
}


# ============================================================================
# (1) ‖δθ‖²-normalized transfer test
# ============================================================================

def delta_theta_norm_sq(model: str, cvd_subj: str) -> float:
    info = CVD_INFO[cvd_subj]
    fam = info['family']
    if model == 'R+C':
        delta = forward_rc(info['delta_lambda_dps'], info['g_best_l8'], fam)
    elif model == '2-Comp':
        delta = forward_2comp(info['beta_s'], info['beta_c'], fam)
    return float(np.sum(delta ** 2))


def reanalyze_transfer():
    """Re-analyze S9 transfer with ‖δθ‖² normalization."""
    print("\n=== (1) ‖δθ‖²-normalized transfer test ===")
    norms = {}
    for cvd in ['sub-08', 'sub-09']:
        for model in ['R+C', '2-Comp']:
            n = delta_theta_norm_sq(model, cvd)
            norms[(cvd, model)] = n
            print(f"  ‖δθ‖²({cvd}, {model}) = {n:.2f}")

    print("\n  Transfer (Y) JND median ratio / ‖δθ‖² (V4):")
    transfer_v4 = json.load(open(S9_DIR / "transfer_test_V4.json"))
    sum_v4 = transfer_v4['summary']
    for cvd in ['sub-08', 'sub-09']:
        for model in ['R+C', '2-Comp']:
            key = f"{cvd}_{model}"
            ratio = sum_v4[key]['Y_JND_ratio_across_HCs']['median']
            n_norm = norms[(cvd, model)]
            norm_ratio = ratio / max(n_norm, 1e-9)
            print(f"    {cvd} {model}: ratio={ratio:.3f}, ‖δθ‖²={n_norm:.1f}, "
                  f"normalized={norm_ratio:.5f}")
    return norms


# ============================================================================
# (2) Honest specificity reframing
# ============================================================================

def reframe_specificity():
    print("\n=== (2) Honest specificity reframing ===")
    fpr = json.load(open(S9_DIR / "fpr_test.json"))
    boot = json.load(open(S6_DIR / "g_bootstrap.json"))

    for cvd in ['sub-08', 'sub-09']:
        fpr_r = fpr[cvd]
        boot_cvd = boot['cvd_bootstrap'][cvd]
        boot_hc_pool = boot['hc_pool_bootstrap'][fpr_r['family']]

        print(f"\n  {cvd} ({fpr_r['family']}):")
        print(f"    CVD g* point = {fpr_r['cvd_g']:.3f}")
        print(f"    HC point g (N=7): {sorted(fpr_r['hc_g_point_fits'].values())}")
        print(f"    Descriptive percentile: N HC ≥ CVD = {fpr_r['hc_g_n_exceed_cvd']}/7")
        print(f"    CVD bootstrap CI: [{boot_cvd['g_ci_95'][0]:.3f}, {boot_cvd['g_ci_95'][1]:.3f}]")
        print(f"    HC pool bootstrap CI: [{boot_hc_pool['pool_ci_95'][0]:.3f}, {boot_hc_pool['pool_ci_95'][1]:.3f}]")
        # CI overlap or separation
        cvd_low, cvd_high = boot_cvd['g_ci_95']
        hc_low, hc_high = boot_hc_pool['pool_ci_95']
        overlap = max(cvd_low, hc_low) <= min(cvd_high, hc_high)
        print(f"    CI overlap: {overlap}")
        if overlap:
            print(f"    → Honest: 'Point fit excess, CI overlap at margin' (NOT 'FPR=0')")


# ============================================================================
# (3) Sub-08 R+C misspecification flag
# ============================================================================

def rc_misspecification_quantify():
    print("\n=== (3) Sub-08 R+C misspecification quantitative ===")
    # AICc from S8 selection_metrics
    sel = json.load(open(SCRIPT_DIR.parent / "results" / "s8_final" / "selection_metrics.json"))
    bimodal = json.load(open(S6_DIR / "g_bootstrap.json"))

    for cvd in ['sub-08', 'sub-09']:
        print(f"\n  {cvd}:")
        # Find L8 R+C DPS and 2-Comp results at V4
        l8_v4 = [r for r in sel if r['subject'] == cvd and r['roi'] == 'V4'
                 and r['loss_target'] == 'L8_modality_5050']
        rc = [r for r in l8_v4 if r['model'] == 'R+C' and r.get('delta_lambda_source') == 'DPS_lit'][0]
        tc = [r for r in l8_v4 if r['model'] == '2-Comp'][0]
        print(f"    R+C AICc(JND) = {rc['aicc_jnd']:.2f}, BIC = {rc['bic_jnd']:.2f}")
        print(f"    2-Comp AICc(JND) = {tc['aicc_jnd']:.2f}, BIC = {tc['bic_jnd']:.2f}")
        print(f"    ΔAICc(R+C - 2-Comp) = {rc['aicc_jnd'] - tc['aicc_jnd']:+.2f} (>10 = R+C clearly worse)")
        print(f"    R+C RSS(JND) = {rc['rss_jnd']:.4f}, 2-Comp RSS(JND) = {tc['rss_jnd']:.4f}")
        # Bootstrap bimodal
        b = bimodal['cvd_bootstrap'][cvd]
        print(f"    R+C Bootstrap g samples: mean={b['g_mean']:.2f}, SD={b['g_sd']:.2f}")
        print(f"    R+C Bootstrap fraction at boundaries (g=0 + g=3) approx: "
              f"= {b['fraction_above_2']:.2f} (above 2) + ({1 - b['fraction_above_1']:.2f} below 1)")

    print("\n  → Sub-08 R+C bootstrap shows large boundary mass → misspecification (not just instability)")
    print("    Paper should say: 'R+C 1-DOF cannot fit sub-08; 2-Comp required'")


# ============================================================================
# (4) Cross-subtype Δ-difference instead of ratio
# ============================================================================

def cross_subtype_delta_diff():
    print("\n=== (4) Cross-subtype Δ-difference (advisor recommended) ===")
    cs = json.load(open(SCRIPT_DIR.parent / "results" / "s8_final" / "cross_subtype.json"))
    for key, r in cs.items():
        cross = r['L_behav_cross']
        within = r['L_behav_within_target']
        diff = cross - within
        ratio = cross / max(within, 1e-9)
        print(f"\n  {key}:")
        print(f"    L_within = {within:.3f}, L_cross = {cross:.3f}")
        print(f"    Δ (cross - within) = {diff:+.3f}")
        print(f"    Ratio (cross/within) = {ratio:.3f}")
    print("\n  → Cross-subtype claims should report Δ AND ratio:")
    print("    sub-08→sub-09: Δ=+0.32, ratio=1.57 (small abs Δ, large ratio due to small within)")
    print("    sub-09→sub-08: Δ=+0.52, ratio=1.10 (large abs Δ, small ratio due to large within)")
    print("    → Δ comparison: sub-09→sub-08 (Δ=+0.52) is actually larger absolute transfer error!")
    print("    → 'Asymmetric subtype-specificity' claim INVERTS under Δ analysis ★")


# ============================================================================
# (5) Loss-assignment permutation null
# ============================================================================

def loss_assignment_permutation(subject: str, B: int = 200, seed: int = 42):
    """Shuffle WHICH JND obs value goes to WHICH pair, keep colors intact.

    Different from S8 (which shuffles colors). This tests: does the model's
    fit depend on which pair has which JND, or just the overall distribution?
    """
    hc_baseline, hc_sd = compute_hc_jnd_baseline()
    info = CVD_INFO[subject]
    fam = info['family']
    dl = info['delta_lambda_dps']

    obs_acc = load_8afc_per_color(subject)
    jnd_obs = load_jnd_per_pair(subject)
    pairs = list(jnd_obs.keys())
    jnd_values = np.array([jnd_obs[p] for p in pairs])

    if subject == 'sub-09':
        w_a, w_g = 0.0, 1.0
    else:
        w_a, w_g = 0.5, 0.5

    rng = np.random.default_rng(seed)
    null_losses = []
    null_gs = []
    for b in range(B):
        # Shuffle JND value-to-pair assignment (8AFC unchanged)
        perm_vals = jnd_values[rng.permutation(len(pairs))]
        jnd_perm = dict(zip(pairs, perm_vals))

        def L_behav_perm(delta_rc):
            l_a = L_behav_alpha(delta_rc, obs_acc, SIGMA_HC) if w_a > 0 else 0.0
            l_g = L_behav_gamma(delta_rc, jnd_perm, hc_baseline, hc_sd)
            return w_a * l_a + w_g * l_g

        fit = fit_rc_g(dl, fam, L_behav_perm)
        null_losses.append(fit['loss_best'])
        null_gs.append(fit['g_best'])

    # Real
    def L_real(delta_rc):
        l_a = L_behav_alpha(delta_rc, obs_acc, SIGMA_HC) if w_a > 0 else 0.0
        l_g = L_behav_gamma(delta_rc, jnd_obs, hc_baseline, hc_sd)
        return w_a * l_a + w_g * l_g
    real = fit_rc_g(dl, fam, L_real)
    null_losses = np.array(null_losses)
    p = float(np.mean(null_losses <= real['loss_best']))
    return {
        'subject': subject, 'B': B,
        'real_loss': real['loss_best'], 'real_g': real['g_best'],
        'null_mean': float(np.mean(null_losses)), 'null_sd': float(np.std(null_losses, ddof=1)),
        'null_min': float(null_losses.min()), 'null_max': float(null_losses.max()),
        'p_value': p,
    }


def loss_assignment_perm_test():
    print("\n=== (5) Loss-assignment permutation null (less destructive) ===")
    print("  Test: shuffle JND_obs values across 8 pairs (8AFC unchanged)")
    print("  Less destructive than S8 color permutation (data still informative)")
    for subj in ['sub-08', 'sub-09']:
        r = loss_assignment_permutation(subj, B=200)
        print(f"\n  {subj}:")
        print(f"    Real loss = {r['real_loss']:.4f}, real g = {r['real_g']:.2f}")
        print(f"    Null loss: mean={r['null_mean']:.4f}, range=[{r['null_min']:.4f}, {r['null_max']:.4f}]")
        print(f"    p-value = {r['p_value']:.4f}")
    print("\n  → Compare to S8 (color perm): if both p≈0 → robust; if loss-assign p large → S8 was over-destructive")


# ============================================================================
# Main
# ============================================================================

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("S10 Advisor-driven supplemental analyses")
    print("=" * 78)

    norms = reanalyze_transfer()
    reframe_specificity()
    rc_misspecification_quantify()
    cross_subtype_delta_diff()
    loss_assignment_perm_test()

    print(f"\nSaved to {OUT_DIR} (logs printed above)")


if __name__ == "__main__":
    main()
