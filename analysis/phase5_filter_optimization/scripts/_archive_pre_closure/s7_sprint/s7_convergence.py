"""S7: Convergence matrix — within-model loss + cross-model δθ + Δλ source.

Analyses S5 all-paths fit results:
  - Within-model: 8 loss g* (R+C) or (β_s,β_c) (2-Comp) variance + pairwise distance
  - Δλ-source (R+C): 3-way comparison per loss
  - Cross-model: R+C vs 2-Comp δθ Spearman correlation per (subj, ROI)

Output: results/s7_convergence/{report.json, summary.md}
"""
import sys
import json
import numpy as np
from pathlib import Path
from scipy.stats import spearmanr

SCRIPT_DIR = Path(__file__).resolve().parent
S5_DIR = SCRIPT_DIR.parent / "results" / "s5_all_paths"
OUT_DIR = SCRIPT_DIR.parent / "results" / "s7_convergence"


def load_s5_results() -> dict:
    """Load all S5 fits, organized by (subject, ROI)."""
    out = {}
    for json_file in sorted(S5_DIR.glob("sub-*_sigma21.json")):
        with open(json_file) as f:
            d = json.load(f)
        key = (d['subject'], d['roi'])
        out[key] = d
    return out


def analyze_subject_roi(d: dict) -> dict:
    """Per-subject-ROI convergence analysis."""
    subject = d['subject']
    roi = d['roi']
    fits = d['fits']

    # === R+C g* across loss (per Δλ source) ===
    rc_per_source = {}
    for fit in fits:
        if fit['model'] != 'R+C':
            continue
        src = fit['delta_lambda_source']
        if src not in rc_per_source:
            rc_per_source[src] = []
        rc_per_source[src].append({
            'loss': fit['loss_target'],
            'g': fit['g_best'],
            'delta_lambda': fit['delta_lambda_nm'],
            'delta_theta': np.array(fit['delta_theta_at_best']),
        })

    rc_convergence = {}
    for src, items in rc_per_source.items():
        gs = np.array([it['g'] for it in items])
        rc_convergence[src] = {
            'g_mean': float(np.mean(gs)),
            'g_sd': float(np.std(gs, ddof=1)),
            'g_min': float(gs.min()),
            'g_max': float(gs.max()),
            'g_range': float(gs.max() - gs.min()),
            'per_loss': {it['loss']: it['g'] for it in items},
        }

    # === Δλ source convergence (per loss, R+C) ===
    losses_seen = sorted(set(it['loss'] for items in rc_per_source.values() for it in items))
    rc_dl_source_conv = {}
    for loss in losses_seen:
        gs = []
        srcs = []
        for src, items in rc_per_source.items():
            for it in items:
                if it['loss'] == loss:
                    gs.append(it['g'])
                    srcs.append(src)
        gs = np.array(gs)
        rc_dl_source_conv[loss] = {
            'g_per_source': dict(zip(srcs, gs.tolist())),
            'g_mean': float(np.mean(gs)),
            'g_sd': float(np.std(gs, ddof=1)),
            'g_range': float(gs.max() - gs.min()),
            'all_agree_within_05': bool(gs.max() - gs.min() < 0.5),
        }

    # === 2-Comp convergence across loss ===
    tc_per_loss = {}
    for fit in fits:
        if fit['model'] != '2-Comp':
            continue
        tc_per_loss[fit['loss_target']] = {
            'beta_s': fit['beta_s_best'],
            'beta_c': fit['beta_c_best'],
            'delta_theta': np.array(fit['delta_theta_at_best']),
        }
    bs_arr = np.array([v['beta_s'] for v in tc_per_loss.values()])
    bc_arr = np.array([v['beta_c'] for v in tc_per_loss.values()])
    tc_convergence = {
        'beta_s_mean': float(np.mean(bs_arr)),
        'beta_s_sd': float(np.std(bs_arr, ddof=1)),
        'beta_s_range': float(bs_arr.max() - bs_arr.min()),
        'beta_c_mean': float(np.mean(bc_arr)),
        'beta_c_sd': float(np.std(bc_arr, ddof=1)),
        'beta_c_range': float(bc_arr.max() - bc_arr.min()),
        'per_loss': {loss: {'beta_s': v['beta_s'], 'beta_c': v['beta_c']}
                     for loss, v in tc_per_loss.items()},
    }

    # === Cross-model δθ Spearman (R+C primary [DPS, L8] vs 2-Comp [L8]) ===
    # Most informative: R+C(DPS Δλ, L8) δθ vs 2-Comp(L8) δθ
    cross_model = {}
    rc_l8_dps = [it for src, items in rc_per_source.items() if 'DPS' in src
                 for it in items if it['loss'] == 'L8_modality_5050']
    tc_l8 = tc_per_loss.get('L8_modality_5050')
    if rc_l8_dps and tc_l8 is not None:
        rc_dth = rc_l8_dps[0]['delta_theta']
        tc_dth = tc_l8['delta_theta']
        rho, p_val = spearmanr(rc_dth, tc_dth)
        # Bootstrap CI of Spearman (across 8 colors)
        rng = np.random.default_rng(42)
        rhos = []
        for _ in range(1000):
            idx = rng.choice(8, size=8, replace=True)
            if len(set(idx)) < 2:
                continue
            r, _ = spearmanr(rc_dth[idx], tc_dth[idx])
            if np.isfinite(r):
                rhos.append(r)
        rhos = np.array(rhos)
        cross_model['R+C_L8_DPS_vs_2C_L8'] = {
            'spearman_rho': float(rho) if np.isfinite(rho) else None,
            'spearman_p': float(p_val) if np.isfinite(p_val) else None,
            'bootstrap_rho_mean': float(np.mean(rhos)) if len(rhos) > 0 else None,
            'bootstrap_rho_ci': [float(np.percentile(rhos, 2.5)),
                                  float(np.percentile(rhos, 97.5))] if len(rhos) > 0 else None,
            'cosine_sim': float(np.dot(rc_dth, tc_dth) / (np.linalg.norm(rc_dth) * np.linalg.norm(tc_dth))),
            'mae_deg': float(np.mean(np.abs(rc_dth - tc_dth))),
            'rc_delta_theta': rc_dth.tolist(),
            'tc_delta_theta': tc_dth.tolist(),
        }

    return {
        'subject': subject,
        'roi': roi,
        'rc_within_loss_convergence': rc_convergence,
        'rc_delta_lambda_source_convergence': rc_dl_source_conv,
        'two_comp_within_loss_convergence': tc_convergence,
        'cross_model_convergence': cross_model,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("S7 Convergence matrix")
    print("=" * 78)

    all_data = load_s5_results()
    reports = []
    for key, d in all_data.items():
        r = analyze_subject_roi(d)
        reports.append(r)

        print(f"\n--- {r['subject']} ROI={r['roi']} ---")
        # R+C within-loss
        for src, conv in r['rc_within_loss_convergence'].items():
            print(f"  R+C ({src}): g mean={conv['g_mean']:.2f}, "
                  f"SD={conv['g_sd']:.2f}, range={conv['g_range']:.2f}")
        # Δλ source convergence
        print(f"  Δλ source convergence (g across 3 sources per loss):")
        for loss, dc in r['rc_delta_lambda_source_convergence'].items():
            ag = "✓" if dc['all_agree_within_05'] else "⚠"
            print(f"    {loss}: g={list(dc['g_per_source'].values())}, "
                  f"range={dc['g_range']:.2f} {ag}")
        # 2-Comp
        tc = r['two_comp_within_loss_convergence']
        print(f"  2-Comp: β_s mean={tc['beta_s_mean']:.1f} SD={tc['beta_s_sd']:.1f}, "
              f"β_c mean={tc['beta_c_mean']:.1f} SD={tc['beta_c_sd']:.1f}")
        # Cross-model
        for label, cm in r['cross_model_convergence'].items():
            print(f"  Cross-model δθ ({label}):")
            print(f"    Spearman ρ = {cm['spearman_rho']:.3f} (p={cm['spearman_p']:.3f})")
            print(f"    Bootstrap ρ 95% CI: [{cm['bootstrap_rho_ci'][0]:.3f}, {cm['bootstrap_rho_ci'][1]:.3f}]")
            print(f"    Cosine = {cm['cosine_sim']:.3f}, MAE = {cm['mae_deg']:.2f}°")

    # Save
    out_data = {
        'reports': reports,
        'summary': 'See per-subject-ROI sections',
    }
    with open(OUT_DIR / "convergence_matrix.json", 'w') as f:
        json.dump(out_data, f, indent=2, default=str)
    print(f"\nSaved: {OUT_DIR / 'convergence_matrix.json'}")


if __name__ == "__main__":
    main()
