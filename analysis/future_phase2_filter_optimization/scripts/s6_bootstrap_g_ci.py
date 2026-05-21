"""S6: Bootstrap CI of g per CVD subject (T-1 Form A) — PRIMARY double-dipping defense.

For each CVD subject:
  Bootstrap (JND 8-pair, 8AFC 8-color) B=1000 times
  Per resample: re-fit g on L8 (uniform) under DPS Δλ
  95% CI of g*
  Test H0: g=1 (no compensation, retinal-only) vs H1: g≠1

HC pool baseline: HC bootstrap g distribution under same Δλ family.

Output: results/s6_bootstrap/{subject}_g_ci.json
"""
import sys
import json
import numpy as np
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import forward_rc, fit_rc_g, compensation_magnitude, g_grid
from behav_loss import (
    L_behav_alpha, L_behav_gamma, SIGMA_HC, PAIR_HUES,
    load_8afc_per_color, load_jnd_per_pair, compute_hc_jnd_baseline,
    HC_8AFC_SUBJS, HC_JND_SUBJS, HUES,
)
from neural_loss import (
    L_LOCO, L_RDM, design_from_delta,
    load_amplitudes, load_hc_pool, ROI_K,
    precompute_loco_W_within,
)
from diagnostic_delta_rdm import precompute_hc_W, compute_delta_rdm_obs, compute_rdm_correlation
from neural_loss import cosine_similarity
from utils_forward_model import create_basis_full, HUE_ANGLES

ROOT = SCRIPT_DIR.parents[2]
DATA_DIR = ROOT / "data" / "behavior"
OUT_DIR = SCRIPT_DIR.parent / "results" / "s6_bootstrap"

CVD_INFO = {
    'sub-08': {'family': 'deutan', 'delta_lambda': 6.0},
    'sub-09': {'family': 'protan', 'delta_lambda': 10.0},
}

# B (bootstrap iterations) — small for behavior-only (cheap), larger for neural
B_BEHAV = 1000
B_NEURAL = 200   # neural bootstrap slower (per-color resample), keep modest


def bootstrap_resample_jnd(jnd_obs: dict, rng) -> dict:
    """Resample JND pairs with replacement (across 8 pairs)."""
    pairs = list(jnd_obs.keys())
    sampled = rng.choice(pairs, size=len(pairs), replace=True)
    # Build new dict: keep selected, None for unselected
    out = {p: None for p in pairs}
    for p in sampled:
        out[p] = jnd_obs[p]
    return out


def bootstrap_resample_8afc(obs_acc_8vec: np.ndarray, rng) -> np.ndarray:
    """Resample 8 colors with replacement → 8-vec (uses sampled color accuracy)."""
    n = len(obs_acc_8vec)
    sampled_idx = rng.choice(n, size=n, replace=True)
    out = np.zeros(n)
    counts = np.zeros(n)
    for idx in sampled_idx:
        out[idx] += obs_acc_8vec[idx]
        counts[idx] += 1
    return np.where(counts > 0, out / np.maximum(counts, 1), obs_acc_8vec)


def fit_g_on_resample(subject_family: str, delta_lambda: float,
                       obs_acc_resampled: np.ndarray, jnd_resampled: dict,
                       hc_baseline: dict, hc_sd: dict,
                       w_alpha: float, w_gamma: float) -> float:
    """Fit g on bootstrap resample of behavioral data."""
    def L_behav(delta_rc):
        l_a = L_behav_alpha(delta_rc, obs_acc_resampled, SIGMA_HC) if w_alpha > 0 else 0.0
        l_g = L_behav_gamma(delta_rc, jnd_resampled, hc_baseline, hc_sd)
        return w_alpha * l_a + w_gamma * l_g
    return fit_rc_g(delta_lambda, subject_family, L_behav)['g_best']


def bootstrap_cvd_g(subject: str, hc_baseline: dict, hc_sd: dict,
                     B: int = B_BEHAV, seed: int = 42) -> dict:
    """Bootstrap g CI for one CVD subject."""
    info = CVD_INFO[subject]
    fam = info['family']
    dl = info['delta_lambda']

    obs_acc = load_8afc_per_color(subject)
    jnd_obs = load_jnd_per_pair(subject)

    # Subject-specific weights (sub-09 8AFC ceiling)
    if subject == 'sub-09':
        w_alpha, w_gamma = 0.0, 1.0
    else:
        w_alpha, w_gamma = 0.5, 0.5

    rng = np.random.default_rng(seed)
    g_samples = []
    for b in range(B):
        jnd_re = bootstrap_resample_jnd(jnd_obs, rng)
        obs_re = bootstrap_resample_8afc(obs_acc, rng)
        g = fit_g_on_resample(fam, dl, obs_re, jnd_re, hc_baseline, hc_sd,
                              w_alpha, w_gamma)
        g_samples.append(g)
    g_arr = np.array(g_samples)

    ci_low, ci_high = np.percentile(g_arr, [2.5, 97.5])
    # Test against null g=1 (no compensation) and g=2 (full HC compensation)
    p_excl_1 = float(np.mean(g_arr > 1.0)) if np.median(g_arr) > 1.0 else float(np.mean(g_arr < 1.0))
    p_excl_2 = float(np.mean(g_arr > 2.0)) if np.median(g_arr) > 2.0 else float(np.mean(g_arr < 2.0))

    return {
        'subject': subject,
        'cvd_family': fam,
        'delta_lambda_nm': dl,
        'B': B,
        'g_mean': float(np.mean(g_arr)),
        'g_median': float(np.median(g_arr)),
        'g_sd': float(np.std(g_arr, ddof=1)),
        'g_ci_95': [float(ci_low), float(ci_high)],
        'fraction_above_1': float(np.mean(g_arr > 1.0)),
        'fraction_above_2': float(np.mean(g_arr > 2.0)),
        'p_excl_g1': p_excl_1,
        'p_excl_g2': p_excl_2,
        'compensation_evidence': bool(ci_low > 1.0),  # CI excludes 1 → g>1 compensation
        'overcompensation_evidence': bool(ci_low > 2.0),  # CI excludes 2 → g>2 overcomp
        'g_samples': g_arr.tolist()[:20],  # first 20 for debugging
    }


def bootstrap_hc_g(hc_baseline: dict, hc_sd: dict,
                    family: str, delta_lambda: float, B: int = B_BEHAV,
                    seed: int = 42) -> dict:
    """HC pool bootstrap baseline: for each HC, bootstrap data and fit g.

    HC pool null distribution of g_HC under same family assumption.
    """
    rng = np.random.default_rng(seed)
    all_g = []
    per_hc_g = {}
    for hc in HC_JND_SUBJS:
        jnd_obs = load_jnd_per_pair(hc)
        has_afc = hc in HC_8AFC_SUBJS
        if has_afc:
            obs_acc = load_8afc_per_color(hc)
            w_alpha, w_gamma = 0.5, 0.5
        else:
            obs_acc = np.zeros(8)
            w_alpha, w_gamma = 0.0, 1.0

        g_samples = []
        for b in range(B):
            jnd_re = bootstrap_resample_jnd(jnd_obs, rng)
            obs_re = bootstrap_resample_8afc(obs_acc, rng) if has_afc else obs_acc
            g = fit_g_on_resample(family, delta_lambda, obs_re, jnd_re,
                                  hc_baseline, hc_sd, w_alpha, w_gamma)
            g_samples.append(g)
        per_hc_g[hc] = {
            'g_mean': float(np.mean(g_samples)),
            'g_ci_95': [float(np.percentile(g_samples, 2.5)),
                        float(np.percentile(g_samples, 97.5))],
        }
        all_g.extend(g_samples)
    all_g = np.array(all_g)
    return {
        'family': family,
        'delta_lambda_nm': delta_lambda,
        'pool_mean': float(np.mean(all_g)),
        'pool_median': float(np.median(all_g)),
        'pool_sd': float(np.std(all_g, ddof=1)),
        'pool_ci_95': [float(np.percentile(all_g, 2.5)),
                       float(np.percentile(all_g, 97.5))],
        'per_hc': per_hc_g,
    }


def main(B: int = 1000):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print(f"S6 Bootstrap CI of g — Form A (T-1) PRIMARY defense (B={B})")
    print("=" * 78)

    hc_baseline, hc_sd = compute_hc_jnd_baseline()

    # CVD bootstrap
    cvd_results = {}
    for subj in ['sub-08', 'sub-09']:
        print(f"\n--- {subj} bootstrap ---")
        r = bootstrap_cvd_g(subj, hc_baseline, hc_sd, B=B)
        cvd_results[subj] = r
        print(f"  g_mean = {r['g_mean']:.3f} ± {r['g_sd']:.3f}")
        print(f"  95% CI: [{r['g_ci_95'][0]:.3f}, {r['g_ci_95'][1]:.3f}]")
        print(f"  P(g > 1) = {r['fraction_above_1']:.3f}  (compensation evidence: {r['compensation_evidence']})")
        print(f"  P(g > 2) = {r['fraction_above_2']:.3f}  (overcompensation evidence: {r['overcompensation_evidence']})")

    # HC pool bootstrap (under both family assumptions)
    print(f"\n--- HC pool bootstrap (Tregillus null) ---")
    hc_pool_results = {}
    for fam, dl in [('protan', 10.0), ('deutan', 6.0)]:
        print(f"\n  {fam} (Δλ={dl}):")
        r = bootstrap_hc_g(hc_baseline, hc_sd, fam, dl, B=B)
        hc_pool_results[fam] = r
        print(f"    Pool g_HC mean = {r['pool_mean']:.3f} ± {r['pool_sd']:.3f}")
        print(f"    Pool 95% CI: [{r['pool_ci_95'][0]:.3f}, {r['pool_ci_95'][1]:.3f}]")

    # CVD vs HC pool bootstrap comparison
    print(f"\n{'=' * 78}")
    print("CVD vs HC pool bootstrap — compensation evidence")
    print(f"{'=' * 78}")
    for subj, r_cvd in cvd_results.items():
        fam = r_cvd['cvd_family']
        r_hc = hc_pool_results[fam]
        diff = r_cvd['g_mean'] - r_hc['pool_mean']
        # Approximate two-sample z under pooled SD
        pooled_sd = np.sqrt(r_cvd['g_sd'] ** 2 + r_hc['pool_sd'] ** 2)
        z = diff / pooled_sd if pooled_sd > 0 else float('inf')
        print(f"\n{subj} ({fam}):")
        print(f"  CVD g_mean = {r_cvd['g_mean']:.3f}, HC pool g_mean = {r_hc['pool_mean']:.3f}")
        print(f"  Δg = {diff:+.3f}, z (two-sample approx) = {z:+.2f}")
        # CI overlap check
        cvd_low, cvd_high = r_cvd['g_ci_95']
        hc_low, hc_high = r_hc['pool_ci_95']
        ci_separate = (cvd_low > hc_high) or (cvd_high < hc_low)
        print(f"  CVD CI: [{cvd_low:.3f}, {cvd_high:.3f}]")
        print(f"  HC CI:  [{hc_low:.3f}, {hc_high:.3f}]")
        print(f"  CI separation: {ci_separate} (non-overlapping)")

    # Save
    out = {
        'cvd_bootstrap': cvd_results,
        'hc_pool_bootstrap': hc_pool_results,
        'B': B,
    }
    with open(OUT_DIR / "g_bootstrap.json", 'w') as f:
        json.dump(out, f, indent=2, default=str)
    print(f"\nSaved: {OUT_DIR / 'g_bootstrap.json'}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--B', type=int, default=1000)
    args = parser.parse_args()
    main(B=args.B)
