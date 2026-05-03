#!/usr/bin/env python3
"""Experiment A: SRM ΔRDM Signal Specificity Diagnostic.

Tests whether V1/V2 SRM ΔRDM carries CVD-specific information by comparing
CVD ΔRDM_obs against HC leave-one-out ΔRDM distribution.

Key questions:
  1) Is ||ΔRDM_obs(CVD)|| larger than ||ΔRDM_obs(HC_LOO)||?
  2) Does ΔRDM_obs direction differ between CVD and HC?
  3) Does L_rdm vary meaningfully across the parameter grid?

Runs locally (conda activate srm). No server needed.
"""

import numpy as np
import json
from pathlib import Path
from scipy.spatial.distance import pdist, cosine
from scipy.stats import spearmanr, mannwhitneyu, rankdata

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _SCRIPT_DIR.parent
_RESULTS_DIR = _PHASE2_DIR / 'results'
_SRM_DIR = _RESULTS_DIR / 'diagnostics/srm_precompute'
_CROSS_ROI_DIR = _RESULTS_DIR / 'diagnostics/srm_integrated_loco'
_OUTPUT_DIR = _RESULTS_DIR / 'diagnostic_srm_specificity'

HC_SUBJECTS = ['01', '02', '03', '04', '05', '06', '07']
CVD_SUBJECTS = ['08', '09', '10']
CVD_TYPES = {'08': 'deutan', '09': 'protan', '10': 'normal'}


def load_srm_data(roi):
    """Load SRM precompute artifacts for one ROI."""
    srm_data = np.load(_SRM_DIR / f'srm_{roi}.npz', allow_pickle=True)
    drdm_data = np.load(_SRM_DIR / f'delta_rdm_obs_srm_{roi}.npz',
                        allow_pickle=True)

    # W_combined per HC: {subj: (6, 4)}
    W_combined = {}
    for s in HC_SUBJECTS:
        key = f'W_combined_{s}'
        if key in srm_data:
            W_combined[s] = srm_data[key]

    # HC aligned patterns: {subj: (8, K_srm)}
    hc_aligned = {}
    for s in HC_SUBJECTS:
        key = f'hc_aligned_{s}'
        if key in srm_data:
            hc_aligned[s] = srm_data[key]

    # CVD aligned patterns
    cvd_aligned = {}
    for s in CVD_SUBJECTS:
        key = f'cvd_aligned_{s}'
        if key in srm_data:
            cvd_aligned[s] = srm_data[key]

    # CVD ΔRDM_obs
    delta_rdm_obs_cvd = {}
    for s in CVD_SUBJECTS:
        key = f'sub_{s}'
        if key in drdm_data:
            delta_rdm_obs_cvd[s] = drdm_data[key]

    return W_combined, hc_aligned, cvd_aligned, delta_rdm_obs_cvd


def compute_hc_loo_drdm(hc_aligned):
    """Compute leave-one-out ΔRDM for each HC subject.

    For HC_i: ΔRDM = RDM(HC_i) - RDM(mean of remaining HC)
    This is the HC null distribution for ΔRDM.
    """
    subjects = sorted(hc_aligned.keys())
    hc_loo_drdm = {}

    for i, subj in enumerate(subjects):
        # RDM of this HC
        rdm_i = pdist(hc_aligned[subj], metric='correlation')  # (28,)

        # Mean RDM of remaining HC
        others = [hc_aligned[s] for s in subjects if s != subj]
        other_rdms = [pdist(p, metric='correlation') for p in others]
        rdm_others_mean = np.mean(other_rdms, axis=0)  # (28,)

        hc_loo_drdm[subj] = rdm_i - rdm_others_mean  # (28,)

    return hc_loo_drdm


def analyze_drdm_specificity(hc_loo_drdm, cvd_drdm, roi):
    """Compare CVD vs HC LOO ΔRDM vectors."""
    print(f'\n{"="*60}')
    print(f'  ΔRDM SPECIFICITY: {roi}')
    print(f'{"="*60}')

    # 1. Norm comparison
    hc_norms = {s: np.linalg.norm(v) for s, v in hc_loo_drdm.items()}
    cvd_norms = {s: np.linalg.norm(v) for s, v in cvd_drdm.items()}

    hc_norm_vals = np.array(sorted(hc_norms.values()))
    print(f'\n  HC LOO ||ΔRDM||: mean={np.mean(hc_norm_vals):.3f}, '
          f'SD={np.std(hc_norm_vals):.3f}, '
          f'range=[{hc_norm_vals.min():.3f}, {hc_norm_vals.max():.3f}]')

    for s in CVD_SUBJECTS:
        if s in cvd_norms:
            n = cvd_norms[s]
            rank = np.sum(hc_norm_vals < n) + 1
            emp_p = 1 - rank / (len(hc_norm_vals) + 1)
            print(f'  CVD sub-{s} ({CVD_TYPES[s]}): ||ΔRDM||={n:.3f}, '
                  f'rank={rank}/{len(hc_norm_vals)+1}, emp_p={emp_p:.3f}')

    # 2. Direction comparison (mean cosine similarity within group)
    hc_vecs = np.array([hc_loo_drdm[s] for s in sorted(hc_loo_drdm.keys())])
    cvd_vecs = np.array([cvd_drdm[s] for s in CVD_SUBJECTS if s in cvd_drdm])

    # Within-HC cosine similarities
    hc_cos_pairs = []
    for i in range(len(hc_vecs)):
        for j in range(i+1, len(hc_vecs)):
            c = 1 - cosine(hc_vecs[i], hc_vecs[j])
            hc_cos_pairs.append(c)
    hc_cos_pairs = np.array(hc_cos_pairs)

    # CVD-to-HC cosine similarities
    cvd_hc_cos = []
    for cv in cvd_vecs:
        for hv in hc_vecs:
            c = 1 - cosine(cv, hv)
            cvd_hc_cos.append(c)
    cvd_hc_cos = np.array(cvd_hc_cos)

    print(f'\n  Within-HC ΔRDM cosine: mean={np.mean(hc_cos_pairs):.3f}, '
          f'SD={np.std(hc_cos_pairs):.3f}')
    print(f'  CVD-to-HC ΔRDM cosine: mean={np.mean(cvd_hc_cos):.3f}, '
          f'SD={np.std(cvd_hc_cos):.3f}')

    # Mann-Whitney U test
    if len(cvd_hc_cos) > 0 and len(hc_cos_pairs) > 0:
        U, mwu_p = mannwhitneyu(cvd_hc_cos, hc_cos_pairs,
                                 alternative='two-sided')
        print(f'  MWU test (CVD-HC vs HC-HC cosines): U={U:.0f}, p={mwu_p:.4f}')

    # 3. Per-CVD detailed comparison
    print(f'\n  Per-CVD ΔRDM direction analysis:')
    for s in CVD_SUBJECTS:
        if s not in cvd_drdm:
            continue
        cv = cvd_drdm[s]
        # Cosine with each HC
        cos_to_hc = [1 - cosine(cv, hc_loo_drdm[h]) for h in sorted(hc_loo_drdm.keys())]
        print(f'    sub-{s} ({CVD_TYPES[s]}): '
              f'cos_to_HC = [{", ".join(f"{c:.3f}" for c in cos_to_hc)}]')
        print(f'      mean={np.mean(cos_to_hc):.3f}, '
              f'max={np.max(cos_to_hc):.3f} (HC-{sorted(hc_loo_drdm.keys())[np.argmax(cos_to_hc)]})')

    return {
        'hc_norms': {s: float(v) for s, v in hc_norms.items()},
        'cvd_norms': {s: float(v) for s, v in cvd_norms.items()},
        'within_hc_cosine_mean': float(np.mean(hc_cos_pairs)),
        'within_hc_cosine_std': float(np.std(hc_cos_pairs)),
        'cvd_to_hc_cosine_mean': float(np.mean(cvd_hc_cos)),
        'cvd_to_hc_cosine_std': float(np.std(cvd_hc_cos)),
    }


def analyze_lrdm_variability():
    """Check how much L_rdm varies across models/families from saved results."""
    print(f'\n{"="*60}')
    print(f'  L_rdm VARIABILITY ACROSS MODELS')
    print(f'{"="*60}')

    results = {}
    for f in sorted(_CROSS_ROI_DIR.glob('sub-*.json')):
        data = json.loads(f.read_text())
        subj = f.stem.split('_')[0].replace('sub-', '')
        family = f.stem.split('_')[1]
        model = '_'.join(f.stem.split('_')[2:])
        key = f'{subj}_{family}_{model}'

        bl = data.get('best_loss', {})
        results[key] = {
            'subject': subj,
            'family': family,
            'model': model,
            'l_rdm': bl.get('l_rdm', np.nan),
            'rdm_cosine': bl.get('rdm_cosine', np.nan),
            'l_vuln': bl.get('l_vuln', np.nan),
            'l_rank': bl.get('l_rank', np.nan),
            'l_fit': bl.get('l_fit', np.nan),
            'spearman_r': bl.get('spearman_r', np.nan),
        }

    # Per-subject L_rdm range
    for subj in ['08', '09', '10']:
        subj_results = {k: v for k, v in results.items()
                        if v['subject'] == subj}
        if not subj_results:
            continue

        l_rdm_vals = [v['l_rdm'] for v in subj_results.values()
                      if np.isfinite(v['l_rdm'])]
        l_vuln_vals = [v['l_vuln'] for v in subj_results.values()
                       if np.isfinite(v['l_vuln'])]
        rdm_cos_vals = [v['rdm_cosine'] for v in subj_results.values()
                        if v['rdm_cosine'] is not None and np.isfinite(v['rdm_cosine'])]

        print(f'\n  Sub-{subj} ({CVD_TYPES[subj]}):')
        print(f'    L_rdm   range: [{min(l_rdm_vals):.4f}, {max(l_rdm_vals):.4f}]'
              f'  span={max(l_rdm_vals)-min(l_rdm_vals):.4f}')
        print(f'    L_vuln  range: [{min(l_vuln_vals):.4f}, {max(l_vuln_vals):.4f}]'
              f'  span={max(l_vuln_vals)-min(l_vuln_vals):.4f}')
        print(f'    rdm_cos range: [{min(rdm_cos_vals):.3f}, {max(rdm_cos_vals):.3f}]'
              f'  span={max(rdm_cos_vals)-min(rdm_cos_vals):.3f}')

        # Weighted contribution ratio
        l_rdm_weighted_range = (max(l_rdm_vals) - min(l_rdm_vals)) * 0.2
        l_vuln_weighted_range = (max(l_vuln_vals) - min(l_vuln_vals)) * 1.0
        l_rank_vals = [v['l_rank'] for v in subj_results.values()
                       if np.isfinite(v['l_rank'])]
        l_rank_weighted_range = (max(l_rank_vals) - min(l_rank_vals)) * 0.5

        total = l_rdm_weighted_range + l_vuln_weighted_range + l_rank_weighted_range
        if total > 0:
            print(f'    Weighted discrimination power:')
            print(f'      L_vuln: {l_vuln_weighted_range:.4f} '
                  f'({l_vuln_weighted_range/total*100:.1f}%)')
            print(f'      L_rank: {l_rank_weighted_range:.4f} '
                  f'({l_rank_weighted_range/total*100:.1f}%)')
            print(f'      L_rdm:  {l_rdm_weighted_range:.4f} '
                  f'({l_rdm_weighted_range/total*100:.1f}%)')

    # Cross-ROI vs hV4-only comparison for models with both results
    print(f'\n  RDM cosine by family (correct vs wrong):')
    for subj, true_fam in [('08', 'deutan'), ('09', 'protan')]:
        wrong_fam = 'protan' if true_fam == 'deutan' else 'deutan'
        for model in ['machado_1way', 'rc_opponent', '2component']:
            correct = results.get(f'{subj}_{true_fam}_{model}', {})
            wrong = results.get(f'{subj}_{wrong_fam}_{model}', {})
            if correct and wrong:
                c_cos = correct.get('rdm_cosine', np.nan)
                w_cos = wrong.get('rdm_cosine', np.nan)
                better = 'CORRECT' if (c_cos or 0) > (w_cos or 0) else 'WRONG'
                print(f'    sub-{subj} {model}: '
                      f'correct({true_fam})={c_cos:.3f}, '
                      f'wrong({wrong_fam})={w_cos:.3f} → {better}')

    return results


def analyze_random_cosine_null(dim=28, n_samples=100000):
    """Monte Carlo null for cosine similarity of random vectors in R^28."""
    print(f'\n{"="*60}')
    print(f'  COSINE SIMILARITY NULL DISTRIBUTION (dim={dim})')
    print(f'{"="*60}')

    rng = np.random.default_rng(42)
    v1 = rng.standard_normal((n_samples, dim))
    v2 = rng.standard_normal((n_samples, dim))

    # Normalize
    v1 /= np.linalg.norm(v1, axis=1, keepdims=True)
    v2 /= np.linalg.norm(v2, axis=1, keepdims=True)

    cos_null = np.sum(v1 * v2, axis=1)

    print(f'  Random cosine in R^{dim}: '
          f'mean={np.mean(cos_null):.4f}, SD={np.std(cos_null):.4f}')
    print(f'  95th percentile: {np.percentile(cos_null, 95):.4f}')
    print(f'  99th percentile: {np.percentile(cos_null, 99):.4f}')

    # Test observed rdm_cosine values against null
    obs_values = {
        '08_protan_2comp': 0.233,
        '08_deutan_2comp': 0.206,
        '09_protan_machado': 0.365,
        '09_protan_2comp': 0.241,
    }
    for key, val in obs_values.items():
        p = np.mean(cos_null >= val)
        print(f'  {key}: cos={val:.3f}, p(null)={p:.4f}'
              f' {"*" if p < 0.05 else "NS"}')

    return float(np.std(cos_null))


def main():
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results_all = {}

    # --- Test 1: Cosine null distribution ---
    cos_null_std = analyze_random_cosine_null()

    # --- Test 2: SRM ΔRDM specificity per ROI ---
    for roi in ['V1', 'V2']:
        try:
            W_combined, hc_aligned, cvd_aligned, cvd_drdm = load_srm_data(roi)
        except Exception as e:
            print(f'  ERROR loading {roi}: {e}')
            continue

        if not hc_aligned:
            print(f'  WARNING: No HC aligned data for {roi}, '
                  f'using W_combined to reconstruct')
            # Cannot compute LOO ΔRDM without aligned patterns
            # Skip to next test
            continue

        hc_loo_drdm = compute_hc_loo_drdm(hc_aligned)
        results_all[roi] = analyze_drdm_specificity(
            hc_loo_drdm, cvd_drdm, roi)

    # --- Test 3: L_rdm variability ---
    model_results = analyze_lrdm_variability()

    # --- Test 4: Combined V1+V2 ΔRDM specificity ---
    print(f'\n{"="*60}')
    print(f'  COMBINED V1+V2 ΔRDM ANALYSIS')
    print(f'{"="*60}')

    # Average V1+V2 norms (as used in pipeline)
    for s in CVD_SUBJECTS:
        v1_norm = results_all.get('V1', {}).get('cvd_norms', {}).get(s, np.nan)
        v2_norm = results_all.get('V2', {}).get('cvd_norms', {}).get(s, np.nan)
        if np.isfinite(v1_norm) and np.isfinite(v2_norm):
            avg = 0.5 * (v1_norm + v2_norm)
            print(f'  sub-{s}: V1={v1_norm:.3f}, V2={v2_norm:.3f}, avg={avg:.3f}')

    # --- Summary verdict ---
    print(f'\n{"="*60}')
    print(f'  VERDICT')
    print(f'{"="*60}')
    print(f'  (Computed automatically based on above tests)')

    # Save
    output = {
        'cos_null_std_28d': cos_null_std,
        'per_roi': results_all,
        'model_comparison': {k: {kk: vv for kk, vv in v.items()
                                  if isinstance(vv, (int, float, str))}
                             for k, v in (model_results or {}).items()},
    }
    out_path = _OUTPUT_DIR / 'srm_specificity_results.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2, default=lambda x: float(x)
                  if isinstance(x, np.floating) else str(x))
    print(f'\n  Results saved: {out_path}')


if __name__ == '__main__':
    main()
