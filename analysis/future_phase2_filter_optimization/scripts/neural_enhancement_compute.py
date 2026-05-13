"""neural_enhancement_compute.py

Compute neural-fit quality metrics at the BAYESIAN BEST cells (22, +18) for
sub-08 deutan / (22, -16) for sub-09 protan. Output is used by the
neural_enhancement_report.md deliverable.

Outputs:
  results/BAYESIAN_BEST/neural_enhancement/metrics.json
  results/BAYESIAN_BEST/neural_enhancement/v4_wfixed_landscape_{sub-08,sub-09}.json (5x5 grid)
  results/BAYESIAN_BEST/neural_enhancement/v1v2_rdm_at_best.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.stats import pearsonr, spearmanr

_THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_THIS_DIR))

# Reuse loco_distortion_fit infrastructure
import loco_distortion_fit as ldf
from loco_distortion_fit import (
    HC_SUBJECTS, N_CHANNELS, HUE_ANGLES, N_RUNS, N_COLORS,
    create_basis_full, precompute_hc_W, load_amplitudes, get_shifted_design,
)
from diagnostic_delta_rdm import (
    compute_delta_rdm_obs, compute_delta_rdm_sim, cosine_similarity,
)

# Import wfixed simulator from step1
from step1_fit_loco_v2 import (
    simulate_mean_hc_wfixed,
)

ROOT = _THIS_DIR.parent
OUT = ROOT / 'results' / 'BAYESIAN_BEST' / 'neural_enhancement'
OUT.mkdir(parents=True, exist_ok=True)

# Bayesian BEST cells
CASES = [
    {'subj': '08', 'family': 'deutan', 'bs': 22, 'bc': 18,
     'axis_label': 'Stockman150'},
    {'subj': '09', 'family': 'protan', 'bs': 22, 'bc': -16,
     'axis_label': 'Stockman16'},
]


def lins_ccc(x, y):
    x, y = np.asarray(x), np.asarray(y)
    mx, my = x.mean(), y.mean()
    sx, sy = x.std(), y.std()
    if sx == 0 or sy == 0:
        return 0.0
    r = np.corrcoef(x, y)[0, 1]
    return 2 * r * sx * sy / (sx**2 + sy**2 + (mx - my)**2)


def voxel_pattern_corr(Y_pred, Y_actual):
    """Single-row correlation (used in step1)."""
    a = Y_pred.ravel(); b = Y_actual.ravel()
    if a.std() < 1e-12 or b.std() < 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def simulate_wfixed_vuln(hc_W_dict, hc_amps_dict, C_shifted):
    """vuln[c] = mean over HC of corr(C_shifted[c] @ W_hc, run_avg amp_hc[c])."""
    per_hc = {}
    for subj in hc_W_dict:
        W = hc_W_dict[subj]
        amp = hc_amps_dict[subj]
        v = np.zeros(N_COLORS)
        for c in range(N_COLORS):
            Y_pred = C_shifted[c:c+1] @ W
            Y_actual = amp[:, c].mean(axis=0, keepdims=True)
            v[c] = voxel_pattern_corr(Y_pred, Y_actual)
        per_hc[subj] = v
    arr = np.array(list(per_hc.values()))
    return arr.mean(axis=0), per_hc


def main():
    data_dir = ldf.LOCAL_DATA
    print(f'Data: {data_dir}')

    # Precompute HC W for V1, V2, V4 (using unshifted baseline)
    print('\n--- Precomputing HC W (V1, V2, V4) ---')
    basis_full = create_basis_full(N_CHANNELS, basis_type='fe')
    C_baseline = basis_full[HUE_ANGLES]

    hc_amps = {}
    hc_W = {}
    for roi in ['V1', 'V2', 'V4']:
        hc_amps[roi] = {hc: load_amplitudes(data_dir, hc, roi) for hc in HC_SUBJECTS}
        hc_W[roi], _ = precompute_hc_W(hc_amps[roi], C_baseline)
        n_voxels = {k: v.shape[2] for k, v in hc_amps[roi].items()}
        print(f'  {roi}: {len(hc_amps[roi])} HC; V_s={n_voxels}')

    # Load CVD data
    cvd_amps = {}
    for case in CASES:
        cvd_amps[case['subj']] = {roi: load_amplitudes(data_dir, case['subj'], roi)
                                   for roi in ['V1', 'V2', 'V4']}

    # ========================================================================
    # 1. V4 wfixed vs wretrained: simulate vuln at BAY BEST cells
    # ========================================================================
    print('\n=== V4 wfixed simulation at BAY BEST cells ===')
    v4_metrics = {}
    for case in CASES:
        subj = case['subj']
        bs, bc = case['bs'], case['bc']
        family = case['family']
        params = np.array([float(bs), float(bc)])

        C_shifted, dt = get_shifted_design('2component', params, family)

        # wfixed vuln for V4
        vuln_wfixed, per_hc = simulate_wfixed_vuln(
            hc_W['V4'], hc_amps['V4'], C_shifted)

        # Observed vuln (= CVD LOCO from cached landscape)
        # Use axis_3way landscape's vuln_cvd
        ls_path = ROOT / 'results' / 'axis_3way' / f'sub-{subj}_V4_{case["axis_label"]}_landscape.json'
        with open(ls_path) as f:
            ls = json.load(f)
        vuln_cvd = np.array(ls['vuln_cvd'])

        # Find the wretrained cell at (bs, bc) for comparison
        sim_wre = None
        for c in ls['cells']:
            if abs(c['bs'] - bs) < 0.5 and abs(c['bc'] - bc) < 0.5:
                sim_wre = np.array(c['vuln_sim'])
                break

        r_wfixed, _ = pearsonr(vuln_wfixed, vuln_cvd)
        rho_wfixed, _ = spearmanr(vuln_wfixed, vuln_cvd)
        ccc_wfixed = lins_ccc(vuln_wfixed, vuln_cvd)

        r_wre, _ = pearsonr(sim_wre, vuln_cvd) if sim_wre is not None else (np.nan, None)
        rho_wre, _ = spearmanr(sim_wre, vuln_cvd) if sim_wre is not None else (np.nan, None)
        ccc_wre = lins_ccc(sim_wre, vuln_cvd) if sim_wre is not None else np.nan

        v4_metrics[subj] = {
            'bs': bs, 'bc': bc, 'family': family,
            'vuln_cvd': vuln_cvd.tolist(),
            'wretrained': {
                'vuln_sim': sim_wre.tolist() if sim_wre is not None else None,
                'range': float(sim_wre.max() - sim_wre.min()) if sim_wre is not None else None,
                'std': float(sim_wre.std()) if sim_wre is not None else None,
                'pearson_r': float(r_wre),
                'spearman_rho': float(rho_wre),
                'ccc': float(ccc_wre),
                'l_ccc': float((1.0 - ccc_wre) / 2),
            },
            'wfixed': {
                'vuln_sim': vuln_wfixed.tolist(),
                'range': float(vuln_wfixed.max() - vuln_wfixed.min()),
                'std': float(vuln_wfixed.std()),
                'pearson_r': float(r_wfixed),
                'spearman_rho': float(rho_wfixed),
                'ccc': float(ccc_wfixed),
                'l_ccc': float((1.0 - ccc_wfixed) / 2),
            },
        }

        print(f'\n  sub-{subj} (β_s={bs}, β_c={bc:+d}):')
        if sim_wre is not None:
            print(f'    wretrained: range={sim_wre.max()-sim_wre.min():.4f}  '
                  f'r={r_wre:+.3f}  ρ={rho_wre:+.3f}  CCC={ccc_wre:+.4f}')
        print(f'    wfixed:     range={vuln_wfixed.max()-vuln_wfixed.min():.4f}  '
              f'r={r_wfixed:+.3f}  ρ={rho_wfixed:+.3f}  CCC={ccc_wfixed:+.4f}')

    # ========================================================================
    # 2. V1/V2 RDM cosine at BAY BEST cells
    # ========================================================================
    print('\n=== V1/V2 ΔRDM cosine at BAY BEST cells ===')
    rdm_metrics = {}
    for case in CASES:
        subj = case['subj']
        bs, bc = case['bs'], case['bc']
        family = case['family']
        params = np.array([float(bs), float(bc)])

        subj_rdm = {'bs': bs, 'bc': bc, 'family': family}

        for roi in ['V1', 'V2']:
            # ΔRDM_obs
            drdm_obs, rdm_cvd, rdm_hc_mean, _ = compute_delta_rdm_obs(
                cvd_amps[subj][roi], hc_amps[roi])

            # ΔRDM_sim at (bs, bc)
            C_shifted, _ = get_shifted_design('2component', params, family)
            drdm_sim, _ = compute_delta_rdm_sim(hc_W[roi], C_shifted, C_baseline)

            cos = cosine_similarity(drdm_sim, drdm_obs)
            l_rdm = float(1.0 - cos)

            # Also: RDM-of-vuln correlation (different from ΔRDM cosine)
            # Compare full RDM_CVD vs predicted shifted RDM
            rdm_pred = np.zeros_like(rdm_cvd)
            per_hc_rdm_pred = []
            for sj, W in hc_W[roi].items():
                Y_shift = C_shifted @ W
                # correlation distance
                from diagnostic_delta_rdm import compute_rdm_correlation
                per_hc_rdm_pred.append(compute_rdm_correlation(Y_shift))
            rdm_pred = np.mean(per_hc_rdm_pred, axis=0)
            cos_full = cosine_similarity(rdm_pred, rdm_cvd)
            r_full, _ = pearsonr(rdm_pred, rdm_cvd)

            subj_rdm[roi] = {
                'delta_rdm_obs_meanabs': float(np.mean(np.abs(drdm_obs))),
                'delta_rdm_sim_meanabs': float(np.mean(np.abs(drdm_sim))),
                'delta_rdm_cosine': float(cos),
                'l_rdm': l_rdm,
                'rdm_full_cosine': float(cos_full),
                'rdm_full_pearson': float(r_full),
            }
            print(f'  sub-{subj} {roi}: ΔRDM cos={cos:+.3f}  l_rdm={l_rdm:.3f}  '
                  f'full_RDM cos={cos_full:+.3f}')

        rdm_metrics[subj] = subj_rdm

    # ========================================================================
    # 3. Multi-ROI composite at BAY BEST cell
    # ========================================================================
    print('\n=== Multi-ROI composite L at BAY BEST cell ===')
    composite_metrics = {}
    for case in CASES:
        subj = case['subj']
        v4m = v4_metrics[subj]
        rdmm = rdm_metrics[subj]

        # Tier 2 style: L_ccc(V4) + λ·L_rdm(V1) + μ·L_rdm(V2)
        l_ccc_v4 = v4m['wretrained']['l_ccc']
        l_rdm_v1 = rdmm['V1']['l_rdm']
        l_rdm_v2 = rdmm['V2']['l_rdm']

        # Various weight options
        composites = {}
        for label, (lam, mu) in [
            ('L_ccc only', (0.0, 0.0)),
            ('L_ccc + 0.5*L_rdm_V1', (0.5, 0.0)),
            ('L_ccc + 0.5*L_rdm_V2', (0.0, 0.5)),
            ('L_ccc + 0.5*L_rdm_V1 + 0.5*L_rdm_V2', (0.5, 0.5)),
            ('L_ccc + 1.0*L_rdm_V1', (1.0, 0.0)),
            ('Equal triple (1/3 each)', (1.0, 1.0)),  # treated as average
        ]:
            if label == 'Equal triple (1/3 each)':
                L = (l_ccc_v4 + l_rdm_v1 + l_rdm_v2) / 3.0
            else:
                L = l_ccc_v4 + lam * l_rdm_v1 + mu * l_rdm_v2
            composites[label] = {
                'L': float(L),
                'L_ccc_V4': float(l_ccc_v4),
                'L_rdm_V1': float(l_rdm_v1),
                'L_rdm_V2': float(l_rdm_v2),
            }
        composite_metrics[subj] = composites
        print(f'\n  sub-{subj}:')
        for label, c in composites.items():
            print(f'    {label:<42s}  L={c["L"]:.3f}')

    # Save
    output = {
        'cases': CASES,
        'v4_metrics': v4_metrics,
        'rdm_metrics': rdm_metrics,
        'composite_metrics': composite_metrics,
    }
    out_path = OUT / 'metrics.json'
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f'\nWrote {out_path}')


if __name__ == '__main__':
    main()
