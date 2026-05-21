"""S5': HC pool g fit on L_behav — Tregillus reduction null (Form B).

For each HC h, fit R+C 1-DOF g on h's own JND + 8AFC under hypothetical CVD family
(Δλ = DPS literature). Builds g_HC pool distribution for compensation null reference.

Form B (advisor catch): Δλ=0 makes g unidentifiable. Use CVD's Δλ assumption.
This tests: "If HC were under same Δλ as CVD, what g would fit their behavior?"
Expected: g_HC ≈ 2 (perfect compensation = HC behavior under any assumed Δλ).
CVD g* != g_HC mean → compensation evidence.

Output: results/s5p_hc_pool/g_HC_pool.json
"""
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from rc_1dof import forward_rc, fit_rc_g, compensation_magnitude
from behav_loss import (
    L_behav_alpha, L_behav_gamma, BEHAV_WEIGHTS, SIGMA_HC,
    load_8afc_per_color, load_jnd_per_pair, compute_hc_jnd_baseline,
    HC_8AFC_SUBJS, HC_JND_SUBJS,
)

ROOT = SCRIPT_DIR.parents[2]
DATA_DIR = ROOT / "data" / "behavior"
OUT_DIR = SCRIPT_DIR.parent / "results" / "s5p_hc_pool"

# Match CVD's Δλ source (DPS primary)
HC_DELTA_ASSUMPTION = {
    'protan': 10.0,   # DPS lit
    'deutan': 6.0,
}

# CVD reference g (from S5 L8 DPS)
CVD_REFERENCE_G = {
    'sub-08': {'roi_V4': 2.25, 'roi_V1': 2.25, 'family': 'deutan', 'delta_lambda': 6.0},
    'sub-09': {'roi_V4': 2.60, 'roi_V1': 2.60, 'family': 'protan', 'delta_lambda': 10.0},
}


def has_8afc(subject: str) -> bool:
    csv = DATA_DIR / f"{subject}_rsvp_8afc_ses1_run1.csv"
    return csv.exists()


def fit_hc_g_on_behav(hc_subject: str, cvd_family: str, delta_lambda: float,
                       hc_baseline: dict, hc_sd: dict) -> dict:
    """Fit R+C g for HC h on h's own JND + 8AFC under hypothetical CVD Δλ."""
    jnd_obs = load_jnd_per_pair(hc_subject)
    if has_8afc(hc_subject):
        obs_acc = load_8afc_per_color(hc_subject)
        loss_name = 'L_behav_α+γ (0.5+0.5)'

        def L_behav(delta_rc):
            l_a = L_behav_alpha(delta_rc, obs_acc, SIGMA_HC)
            l_g = L_behav_gamma(delta_rc, jnd_obs, hc_baseline, hc_sd)
            return 0.5 * l_a + 0.5 * l_g
    else:
        loss_name = 'L_behav_γ only'

        def L_behav(delta_rc):
            return L_behav_gamma(delta_rc, jnd_obs, hc_baseline, hc_sd)

    fit = fit_rc_g(delta_lambda, cvd_family, L_behav)
    return {
        'hc_subject': hc_subject,
        'cvd_family_assumed': cvd_family,
        'delta_lambda_nm': delta_lambda,
        'loss_form': loss_name,
        'has_8afc': has_8afc(hc_subject),
        'g_best': fit['g_best'],
        'loss_best': fit['loss_best'],
        'loss_at_g1': fit['loss_at_g1'],
        'compensation_magnitude_nm': compensation_magnitude(fit['g_best'], delta_lambda),
        'boundary_high': fit['boundary_high'],
        'boundary_low': fit['boundary_low'],
        'misspecified': fit['misspecified'],
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("S5' — HC pool g fit on L_behav (Form B Tregillus reduction null)")
    print("=" * 78)

    hc_baseline, hc_sd = compute_hc_jnd_baseline()

    all_results = []
    for fam, dl in HC_DELTA_ASSUMPTION.items():
        print(f"\n--- HC pool under {fam} assumption (Δλ = {dl} nm) ---")
        for hc in HC_JND_SUBJS:
            r = fit_hc_g_on_behav(hc, fam, dl, hc_baseline, hc_sd)
            all_results.append(r)
            flag = ""
            if r['boundary_low']:
                flag = " [boundary LOW]"
            elif r['boundary_high']:
                flag = " [boundary HIGH]"
            afc = "+8AFC" if r['has_8afc'] else ""
            print(f"  {hc}: g* = {r['g_best']:.3f} {afc} "
                  f"(loss {r['loss_best']:.4f}){flag}")

    # Pool stats per family
    print("\n" + "=" * 78)
    print("HC pool g distribution per family")
    print("=" * 78)
    pool_stats = {}
    for fam in ['protan', 'deutan']:
        gs = [r['g_best'] for r in all_results if r['cvd_family_assumed'] == fam]
        gs_arr = np.array(gs)
        pool_stats[fam] = {
            'n': len(gs),
            'mean': float(np.mean(gs_arr)),
            'median': float(np.median(gs_arr)),
            'sd': float(np.std(gs_arr, ddof=1)),
            'min': float(np.min(gs_arr)),
            'max': float(np.max(gs_arr)),
            'q25': float(np.percentile(gs_arr, 25)),
            'q75': float(np.percentile(gs_arr, 75)),
            'all_g': gs,
        }
        print(f"\n{fam} (N={len(gs)}):")
        print(f"  g_HC mean ± SD = {pool_stats[fam]['mean']:.3f} ± {pool_stats[fam]['sd']:.3f}")
        print(f"  Range [{pool_stats[fam]['min']:.3f}, {pool_stats[fam]['max']:.3f}]")
        print(f"  Median = {pool_stats[fam]['median']:.3f}")

    # CVD vs HC comparison
    print("\n" + "=" * 78)
    print("CVD g* vs HC pool g distribution")
    print("=" * 78)
    cvd_compare = {}
    for cvd_subj, info in CVD_REFERENCE_G.items():
        fam = info['family']
        g_cvd = info['roi_V4']  # use V4 reference (also V1 if needed)
        pool = pool_stats[fam]
        # Percentile of CVD g in HC distribution
        hc_gs = np.array(pool['all_g'])
        pct = float(np.mean(hc_gs < g_cvd) * 100)
        # Z-score
        z = (g_cvd - pool['mean']) / pool['sd'] if pool['sd'] > 0 else float('inf')
        cvd_compare[cvd_subj] = {
            'cvd_family': fam,
            'g_cvd': g_cvd,
            'hc_mean': pool['mean'],
            'hc_sd': pool['sd'],
            'percentile_in_hc': pct,
            'z_score_vs_hc': z,
            'delta_lambda_nm': info['delta_lambda'],
        }
        print(f"\n{cvd_subj} ({fam}, V4 g*={g_cvd:.2f}):")
        print(f"  HC pool g_HC mean = {pool['mean']:.3f} ± {pool['sd']:.3f}")
        print(f"  Percentile of CVD in HC = {pct:.1f}%")
        print(f"  Z-score = {z:+.2f}")

    # Save
    out_data = {
        'per_hc_fits': all_results,
        'hc_pool_stats': pool_stats,
        'cvd_vs_hc': cvd_compare,
    }
    with open(OUT_DIR / "g_HC_pool.json", 'w') as f:
        json.dump(out_data, f, indent=2, default=str)
    print(f"\nSaved: {OUT_DIR / 'g_HC_pool.json'}")


if __name__ == "__main__":
    main()
