#!/usr/bin/env python3
"""cycle13_family_baseline.py — Family assignment 검증 + baseline_rho 회귀 보정.

Cycle 12 분석 후 사용자가 제기한 두 가지 critical issue:
1. Family assignment 비검증: sub-08=deutan, sub-09=protan은 cone test 기반 가정.
   data-driven 검증 필요 — protan vs deutan loss 직접 비교.
2. Baseline_rho confound: HC LOCO FPR=100% (Job 96600), z_combined가 baseline BOLD
   outlier와 CVD signal을 구별 못함. baseline_rho 회귀 보정 필요.

Output:
  cycle13_family_baseline.json
    - family_test: per CVD, z_combined under each family
    - baseline_correction: residual z_combined after baseline_rho regression
"""
import json
import csv
import numpy as np
from pathlib import Path

ROOT = Path('/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/'
            'colorBlind_analysis/analysis/future_phase2_filter_optimization')
RES = ROOT / 'results/cycles'
RES_VOX = RES / 'cycle6_voxel_diag'
BASELINE_CSV = ROOT / 'results/visualizations/diagnostic_protan_vs_deutan/neural_baseline_decomp.csv'
OUT = RES / 'cycle13_family_baseline.json'

HC = ['01', '02', '03', '04', '05', '06']
CVD = ['08', '09']
ROIS = ['V1', 'V2', 'V4']
COLOR_IDX = {'yellow': 2, 'magenta': 7}
FAMILIES = {'deutan': ('yellow', -1.0), 'protan': ('magenta', +1.0)}

# True (cone-test-based) family
TRUE_FAMILY = {'08': 'deutan', '09': 'protan'}

_bs = np.arange(0.0, 81.0, 2.0)
_bc = np.arange(-60.0, 61.0, 2.0)
_BS, _BC = np.meshgrid(_bs, _bc, indexing='ij')
NORM_GRID = (_BS / 80.0) ** 2 + (_BC / 60.0) ** 2


def L_set(target, roi, lam=0.2):
    p = RES / f'sub-{target}_{roi}_landscape.json'
    if not p.exists():
        return None
    with open(p) as f:
        d = json.load(f)
    topk = np.array(d['l_topk_jaccard'])
    return float((topk + lam * NORM_GRID).min())


def L_vox(target, roi, fam_color, fam_sign):
    p = RES_VOX / f'{roi}_summary.json'
    with open(p) as f:
        d = json.load(f)
    if target not in d['per_subject']:
        return None
    r = d['per_subject'][target]
    sigs_z = r['sigs_z']
    rdm_z = np.array(r['rdm_z'])
    c_idx = COLOR_IDX[fam_color]
    z_mean = float(sigs_z['mean_amp'][c_idx])
    z_rdm = float(np.abs(rdm_z[c_idx]).mean())
    z_runc = float(sigs_z['run_consistency'][c_idx])
    return -(fam_sign * z_mean + abs(z_rdm) + abs(z_runc))


def pool_stats(pool, roi):
    Ls = [L_set(s, roi) for s in pool if L_set(s, roi) is not None]
    out = {'Ls_mu': float(np.mean(Ls)), 'Ls_sd': float(np.std(Ls, ddof=1))}
    for fam_name, (fc, fs) in FAMILIES.items():
        Lv = [L_vox(s, roi, fc, fs) for s in pool if L_vox(s, roi, fc, fs) is not None]
        out[f'Lv_{fam_name}_mu'] = float(np.mean(Lv))
        out[f'Lv_{fam_name}_sd'] = float(np.std(Lv, ddof=1))
    return out


def evaluate_z(target, pool, roi_set, roi_vox, fam):
    """Same/cross-ROI z_combined."""
    fc, fs = FAMILIES[fam]
    Ls = L_set(target, roi_set)
    Lv = L_vox(target, roi_vox, fc, fs)
    s_set = pool_stats(pool, roi_set)
    s_vox = pool_stats(pool, roi_vox)
    z_set = (Ls - s_set['Ls_mu']) / s_set['Ls_sd']
    z_vox = (Lv - s_vox[f'Lv_{fam}_mu']) / s_vox[f'Lv_{fam}_sd']
    return z_set + z_vox


def load_baseline_rho():
    """Load baseline_rho per subject per ROI from machado_1way diagnostic."""
    out = {}  # [subj][roi] = rho_baseline
    with open(BASELINE_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            subj = row['subject']
            roi_name = row['roi'].replace('hV4', 'V4')
            rho_b = float(row['rho_baseline'])
            out.setdefault(subj, {})[roi_name] = rho_b
    return out


# ============================================================================
# 1. FAMILY ASSIGNMENT TEST
# ============================================================================
def family_test():
    """For each CVD subject, evaluate z_combined under BOTH families.
    Test: does data-driven family (lower z_combined) agree with cone-test family?
    """
    results = {}
    print('=== FAMILY ASSIGNMENT TEST ===')
    print('For each CVD, compute z_combined under deutan AND protan family.')
    print('Best family = more negative z_combined.')
    print()
    print(f'{"target":<6} {"true":<7} {"V4|V4 deut":>12} {"V4|V4 prot":>12} {"V1|V4 deut":>12} {"V1|V4 prot":>12} {"data-driven":<14} {"agree?":<7}')
    print('-' * 95)

    for target in CVD:
        true_fam = TRUE_FAMILY[target]
        results[target] = {'true_family': true_fam, 'cells': {}}
        # V4|V4 same-ROI
        z_v44_deut = evaluate_z(target, HC, 'V4', 'V4', 'deutan')
        z_v44_prot = evaluate_z(target, HC, 'V4', 'V4', 'protan')
        # V1|V4 cross-ROI
        z_v14_deut = evaluate_z(target, HC, 'V1', 'V4', 'deutan')
        z_v14_prot = evaluate_z(target, HC, 'V1', 'V4', 'protan')
        # V1+V4 sum (4-term)
        # = z_set(V1) + z_set(V4) + z_vox(V1) + z_vox(V4)
        sum_deut = (evaluate_z(target, HC, 'V1', 'V1', 'deutan')
                    + evaluate_z(target, HC, 'V4', 'V4', 'deutan')) / 2  # avg z
        # Actually V1+V4 sum: just sum 4 terms
        # Use existing approach: for each ROI compute z_set + z_vox at same ROI, sum
        s1 = pool_stats(HC, 'V1'); s4 = pool_stats(HC, 'V4')
        Ls1 = L_set(target, 'V1'); Ls4 = L_set(target, 'V4')
        z_set1 = (Ls1 - s1['Ls_mu']) / s1['Ls_sd']
        z_set4 = (Ls4 - s4['Ls_mu']) / s4['Ls_sd']
        Lv1_deut = L_vox(target, 'V1', 'yellow', -1.0)
        Lv4_deut = L_vox(target, 'V4', 'yellow', -1.0)
        Lv1_prot = L_vox(target, 'V1', 'magenta', +1.0)
        Lv4_prot = L_vox(target, 'V4', 'magenta', +1.0)
        zv1_deut = (Lv1_deut - s1['Lv_deutan_mu']) / s1['Lv_deutan_sd']
        zv4_deut = (Lv4_deut - s4['Lv_deutan_mu']) / s4['Lv_deutan_sd']
        zv1_prot = (Lv1_prot - s1['Lv_protan_mu']) / s1['Lv_protan_sd']
        zv4_prot = (Lv4_prot - s4['Lv_protan_mu']) / s4['Lv_protan_sd']
        sum_deut = z_set1 + z_set4 + zv1_deut + zv4_deut
        sum_prot = z_set1 + z_set4 + zv1_prot + zv4_prot

        # Pick best family from each cell
        best_v44 = 'deutan' if z_v44_deut < z_v44_prot else 'protan'
        best_v14 = 'deutan' if z_v14_deut < z_v14_prot else 'protan'
        best_sum = 'deutan' if sum_deut < sum_prot else 'protan'

        # Consensus
        votes = [best_v44, best_v14, best_sum]
        from collections import Counter
        consensus = Counter(votes).most_common(1)[0][0]
        agree = '✓' if consensus == true_fam else '✗ MISMATCH'

        results[target]['cells'] = {
            'V4|V4': {'deutan': z_v44_deut, 'protan': z_v44_prot, 'best': best_v44},
            'V1|V4': {'deutan': z_v14_deut, 'protan': z_v14_prot, 'best': best_v14},
            'V1+V4_sum': {'deutan': sum_deut, 'protan': sum_prot, 'best': best_sum},
        }
        results[target]['data_driven_consensus'] = consensus
        results[target]['agreement'] = (consensus == true_fam)

        print(f'sub-{target} {true_fam:<7} '
              f'{z_v44_deut:>+12.2f} {z_v44_prot:>+12.2f} '
              f'{z_v14_deut:>+12.2f} {z_v14_prot:>+12.2f} '
              f'{consensus:<14} {agree:<7}')

    print()
    print('=== Per-cell family margin (more negative wins) ===')
    for target in CVD:
        true_fam = TRUE_FAMILY[target]
        for cell, vals in results[target]['cells'].items():
            margin = vals['protan'] - vals['deutan']  # negative if deutan wins
            print(f'  sub-{target} {cell}: deut={vals["deutan"]:+.2f}, prot={vals["protan"]:+.2f}, '
                  f'margin={margin:+.2f}, best={vals["best"]} '
                  f'({"matches true" if vals["best"] == true_fam else "MISMATCH"})')
    return results


# ============================================================================
# 2. BASELINE_RHO CORRECTION
# ============================================================================
def baseline_correction():
    """Regress out baseline_rho from z_combined.

    HC pool: z_combined ~ baseline_rho (linear regression)
    Residual: z_combined - predicted
    CVD residual: same regression coefficients applied
    Compare CVD residual to HC residual distribution.
    """
    baseline = load_baseline_rho()
    results = {}

    print('\n=== BASELINE_RHO CORRECTION ===')
    print('Regress out baseline_rho from z_combined (V4|V4 same-ROI).')
    print('Compare CVD residual to HC LOO residual distribution.')
    print()

    # For each ROI × family, regress on full HC + CVD baseline_rho
    for roi in ['V1', 'V4']:
        for fam in FAMILIES:
            # Get baseline_rho per subject for this ROI
            # Each subject in baseline CSV has rho_baseline per ROI
            # Use sub-08, sub-09 baseline_rho directly; for HC need to estimate
            # baseline data only has CVD subjects (08, 09, 10) — limited!
            available_baseline = [s for s in HC + CVD if s in baseline and roi in baseline[s]]
            if len(available_baseline) < 4:
                continue

            # Compute z_combined for all available
            zs = {}
            for s in available_baseline:
                pool = HC if s in CVD else [h for h in HC if h != s]
                if len(pool) < 2:
                    continue
                zs[s] = evaluate_z(s, pool, roi, roi, fam)

            # Print
            print(f'--- {roi} {fam} ---')
            for s in available_baseline:
                if s in zs:
                    rho_b = baseline[s][roi]
                    z_c = zs[s]
                    role = 'CVD' if s in CVD else 'HC'
                    print(f'  sub-{s} ({role}): baseline_rho={rho_b:+.3f}, z_combined={z_c:+.2f}')

            # Linear regression on HC only
            hc_subj = [s for s in HC if s in zs and s in baseline and roi in baseline[s]]
            if len(hc_subj) >= 3:
                X_hc = np.array([baseline[s][roi] for s in hc_subj])
                Y_hc = np.array([zs[s] for s in hc_subj])
                # Linear fit
                slope, intercept = np.polyfit(X_hc, Y_hc, 1)
                print(f'  HC regression (n={len(hc_subj)}): z_combined = {slope:+.2f}*baseline_rho + {intercept:+.2f}')
                # Compute residuals
                Y_hc_pred = slope * X_hc + intercept
                resid_hc = Y_hc - Y_hc_pred
                resid_sd = float(np.std(resid_hc, ddof=1))
                print(f'  HC residual: mean={float(np.mean(resid_hc)):+.2f}, SD={resid_sd:.2f}')

                for s in CVD:
                    if s not in zs or s not in baseline or roi not in baseline[s]:
                        continue
                    rho_b = baseline[s][roi]
                    pred = slope * rho_b + intercept
                    resid = zs[s] - pred
                    z_resid = resid / resid_sd if resid_sd > 0 else np.nan
                    fp_marker = '✓ outside HC residual range' if abs(z_resid) > 2 else 'within HC residual'
                    print(f'  sub-{s} (CVD): baseline_rho={rho_b:+.3f}, raw_z={zs[s]:+.2f}, '
                          f'pred={pred:+.2f}, residual={resid:+.2f}, z_residual={z_resid:+.2f}  {fp_marker}')

                results[f'{roi}_{fam}'] = {
                    'roi': roi, 'family': fam,
                    'hc_regression': {'slope': float(slope), 'intercept': float(intercept), 'residual_sd': resid_sd},
                    'hc_n': len(hc_subj),
                }
            print()

    # Note: baseline CSV only has CVD subjects (08, 09, 10). HC baseline missing.
    print('!!! NOTE: baseline_rho CSV only contains CVD subjects (08, 09, 10).')
    print('!!! HC baseline_rho missing — cannot compute HC regression.')
    print('!!! Need to compute HC baseline_rho separately (Δλ=0 LOCO ρ).')
    return results


def main():
    family_results = family_test()
    baseline_results = baseline_correction()

    out = {
        'meta': {
            'cycle': 13,
            'task': 'family assignment + baseline_rho correction',
            'true_family_assumption': TRUE_FAMILY,
            'note': 'baseline_rho CSV has CVD only (08,09,10); HC baseline missing for full regression',
        },
        'family_test': family_results,
        'baseline_correction': baseline_results,
    }

    with open(OUT, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\nSaved: {OUT}')


if __name__ == '__main__':
    main()
