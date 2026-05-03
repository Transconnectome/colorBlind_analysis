#!/usr/bin/env python3
"""Experiment B: Weight Sweep + HC LOO Cross-ROI Validation.

Definitive test of whether V1/V2 SRM ΔRDM adds CVD specificity.

For each of 10 subjects (7 HC LOO + 3 CVD):
  - Run cross-ROI pipeline (hV4 LOCO + V1/V2 SRM ΔRDM)
  - Test 3 weight schemes:
      LOCO-only:  [α=1.0, β=0.5, δ=0.0, ε=0.1]  (baseline: no RDM)
      Balanced:   [α=1.0, β=1.0, δ=1.0, ε=0.1]  (equal weight)
      RDM-heavy:  [α=0.5, β=0.5, δ=2.0, ε=0.1]  (RDM dominant)
  - Only machado_1way (1 DOF, lowest FPR) to minimize overfitting
  - Two families: protan, deutan

Output: Per-subject, per-weight-scheme, per-family Δρ
  → Compare CVD vs HC distributions under each scheme
  → Compute FPR for each scheme

Usage (server):
  python experiment_b_weight_sweep.py --output_dir results/experiment_b_weight_sweep

Requires: step0_srm_precompute output + C010 data
Does NOT require BrainIAK (reads precomputed SRM artifacts).
"""

import argparse
import json
import time
import sys
import numpy as np
from pathlib import Path
from itertools import permutations
from scipy.stats import spearmanr
from scipy.spatial.distance import pdist

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_PHASE2_DIR = _SCRIPT_DIR.parent

# Forward model imports
for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from utils_forward_model import (
    load_amplitudes, create_basis_full, HUE_ANGLES, N_CHANNELS
)
from step1_fit_loco_v2 import (
    precompute_hc_W, simulate_mean_hc_wfixed, voxel_pattern_correlation
)
from loco_distortion_fit import (
    get_shifted_design, compute_fit_loss, run_permutation_tests,
    FILTER_MODELS, NORM
)
from step0_srm_precompute import compute_delta_rdm_sim_srm

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
HC_SUBJECTS = ['01', '02', '03', '04', '05', '06', '07']
CVD_SUBJECTS = ['08', '09', '10']
CVD_TYPES = {'08': 'deutan', '09': 'protan', '10': 'normal'}
N_COLORS = 8

# Weight schemes to test
WEIGHT_SCHEMES = {
    'loco_only': {'alpha': 1.0, 'beta': 0.5, 'delta': 0.0, 'epsilon': 0.1},
    'balanced':  {'alpha': 1.0, 'beta': 1.0, 'delta': 1.0, 'epsilon': 0.1},
    'rdm_heavy': {'alpha': 0.5, 'beta': 0.5, 'delta': 2.0, 'epsilon': 0.1},
}

FAMILIES = ['protan', 'deutan']
MODEL = 'machado_1way'  # 1 DOF only, minimize overfitting


def load_data(data_dir):
    """Load amplitudes for all 10 subjects."""
    all_amps = {}
    roi_dir = 'V4'  # hV4 on disk
    for subj in HC_SUBJECTS + CVD_SUBJECTS:
        subj_dir = Path(data_dir) / f'sub-{subj}' / roi_dir
        amp_file = subj_dir / 'amplitudes_procrustes.npy'
        if amp_file.exists():
            all_amps[subj] = np.load(amp_file)
            print(f'  sub-{subj}: {all_amps[subj].shape}')
        else:
            print(f'  WARNING: Missing {amp_file}')
    return all_amps


def load_srm_artifacts(srm_dir):
    """Load precomputed SRM W_combined and ΔRDM_obs."""
    result = {}
    for roi in ['V1', 'V2']:
        srm_data = np.load(srm_dir / f'srm_{roi}.npz', allow_pickle=True)
        drdm_data = np.load(srm_dir / f'delta_rdm_obs_srm_{roi}.npz',
                            allow_pickle=True)

        W_combined = {}
        for s in HC_SUBJECTS:
            key = f'W_combined_{s}'
            if key in srm_data:
                W_combined[s] = srm_data[key]

        delta_rdm_obs = {}
        for s in CVD_SUBJECTS:
            key = f'sub_{s}'
            if key in drdm_data:
                delta_rdm_obs[s] = drdm_data[key]

        # For HC LOO: compute ΔRDM from aligned patterns
        hc_aligned = {}
        for s in HC_SUBJECTS:
            key = f'hc_aligned_{s}'
            if key in srm_data:
                hc_aligned[s] = srm_data[key]

        result[roi] = {
            'W_combined': W_combined,
            'delta_rdm_obs_cvd': delta_rdm_obs,
            'hc_aligned': hc_aligned,
        }
    return result


def compute_hc_loo_drdm(hc_aligned, leave_out_subj):
    """Compute ΔRDM_obs for HC_i (LOO) in SRM space."""
    rdm_i = pdist(hc_aligned[leave_out_subj], metric='correlation')
    others = [hc_aligned[s] for s in hc_aligned if s != leave_out_subj]
    other_rdms = [pdist(p, metric='correlation') for p in others]
    rdm_others_mean = np.mean(other_rdms, axis=0)
    return rdm_i - rdm_others_mean


def compute_loco_vulnerability(hc_W_dict, hc_amps_dict, target_amp):
    """Compute LOCO vulnerability for a target subject using HC W matrices."""
    vuln = np.zeros(N_COLORS)
    for color in range(N_COLORS):
        preds = []
        for subj in hc_W_dict:
            Y_pred = np.zeros_like(target_amp[:, color].mean(axis=0))
            # For each HC's W, predict the target color
            C_orig = create_basis_full(N_CHANNELS, basis_type='fe')
            hue_idx = HUE_ANGLES[color] % 360
            c_row = C_orig[hue_idx:hue_idx+1]  # (1, K)
            pred = (c_row @ hc_W_dict[subj]).flatten()
            preds.append(pred)

        # Mean prediction across HC
        mean_pred = np.mean(preds, axis=0)
        actual = target_amp[:, color].mean(axis=0)

        r = np.corrcoef(mean_pred, actual)[0, 1]
        vuln[color] = r if np.isfinite(r) else 0.0
    return vuln


def run_for_subject(subj, all_amps, srm_artifacts, output_dir, is_hc=False):
    """Run cross-ROI grid search for one subject under all weight schemes."""

    t0 = time.time()
    print(f'\n{"="*60}')
    print(f'  Subject: sub-{subj} ({"HC LOO" if is_hc else "CVD"})')
    print(f'{"="*60}')

    # --- Determine HC pool (LOO for HC subjects) ---
    if is_hc:
        hc_pool = [s for s in HC_SUBJECTS if s != subj]
    else:
        hc_pool = HC_SUBJECTS

    # hV4 amps for pool
    hc_amps_hv4 = {s: all_amps[s] for s in hc_pool if s in all_amps}
    target_amp = all_amps.get(subj)
    if target_amp is None:
        print(f'  ERROR: No amplitude data for sub-{subj}')
        return

    # Precompute hV4 W for pool
    C_original = create_basis_full(N_CHANNELS, basis_type='fe')[HUE_ANGLES]
    hc_W_hv4, _ = precompute_hc_W(hc_amps_hv4, C_original)

    # Compute target LOCO vulnerability (baseline: unshifted)
    # For HC LOO: target_amp is the left-out HC's hV4 data
    # For CVD: target_amp is the CVD subject's hV4 data
    # vuln_target[c] = mean over HC_j of corr(C_orig[c] @ W_j, target_amp[:, c].mean())
    # Note: each HC_j's W_j maps to HC_j's voxel space, so we must compute
    # the prediction in the target's voxel space by training a separate W on
    # target data. Instead, use existing LOCO target from step1 results.
    C_baseline = C_original.copy()

    # For the target subject, compute vulnerability = how well the pool's
    # mean prediction matches this subject. Each HC_j predicts in its OWN
    # voxel space, then corr with HC_j's actual pattern. So vuln_target is
    # the per-color accuracy of the pool predicting the TARGET's patterns.
    #
    # Since target has its own V_s, we need to train W for target too:
    # fit W_target on target_amp, then predict with shifted C, compare with
    # target's actual patterns. This is the standard LOCO approach.
    #
    # For simplicity, we reuse the pool's mean vulnerability (how well
    # pool predicts pool) as the baseline, and compute the target's
    # self-vulnerability for the objective.
    from step1_fit_loco_v2 import fit_W_ridge, gcv_select_alpha

    # Fit W for the target subject
    target_pooled = target_amp.reshape(-1, target_amp.shape[-1])  # (48, V_s)
    C_pooled = np.tile(C_original, (target_amp.shape[0], 1))  # (48, K)
    alpha_target, _ = gcv_select_alpha(C_pooled, target_pooled)
    W_target = fit_W_ridge(C_pooled, target_pooled, alpha_target)  # (K, V_s)

    # vuln_target[c] = corr(C_baseline[c] @ W_target, target_amp[:, c].mean())
    vuln_target = np.zeros(N_COLORS)
    for c in range(N_COLORS):
        Y_pred = (C_baseline[c:c+1] @ W_target).flatten()  # (V_s,)
        Y_actual = target_amp[:, c].mean(axis=0)  # (V_s,)
        r = np.corrcoef(Y_pred, Y_actual)[0, 1]
        vuln_target[c] = r if np.isfinite(r) else 0.0

    # Baseline ρ = Spearman between pool's mean vuln and target's vuln
    vuln_pool_baseline, _ = simulate_mean_hc_wfixed(
        hc_W_hv4, hc_amps_hv4, C_baseline)
    baseline_rho, _ = spearmanr(vuln_pool_baseline, vuln_target)
    if not np.isfinite(baseline_rho):
        baseline_rho = 0.0
    print(f'  Baseline ρ = {baseline_rho:.3f}')
    print(f'  Target vuln: [{", ".join(f"{v:.3f}" for v in vuln_target)}]')

    # --- SRM ΔRDM_obs ---
    drdm_obs_per_roi = {}
    W_combined_per_roi = {}
    for roi in ['V1', 'V2']:
        art = srm_artifacts[roi]
        if is_hc and subj in art['hc_aligned']:
            # HC LOO: compute ΔRDM from aligned patterns
            drdm_obs_per_roi[roi] = compute_hc_loo_drdm(
                art['hc_aligned'], subj)
        elif subj in art['delta_rdm_obs_cvd']:
            drdm_obs_per_roi[roi] = art['delta_rdm_obs_cvd'][subj]
        else:
            print(f'  WARNING: No ΔRDM_obs for sub-{subj} in {roi}')
            drdm_obs_per_roi[roi] = np.zeros(28)

        # W_combined: use LOO pool for HC
        if is_hc:
            W_combined_per_roi[roi] = {
                s: art['W_combined'][s] for s in hc_pool
                if s in art['W_combined']
            }
        else:
            W_combined_per_roi[roi] = art['W_combined']

    # Average ΔRDM_obs across V1 + V2
    drdm_obs_avg = 0.5 * drdm_obs_per_roi['V1'] + 0.5 * drdm_obs_per_roi['V2']

    # --- Grid search for each weight scheme and family ---
    subject_results = {}

    model_info = FILTER_MODELS[MODEL]
    bounds = model_info['bounds']
    steps = model_info['grid_step']
    axes = [np.arange(lo, hi + step * 0.5, step)
            for (lo, hi), step in zip(bounds, steps)]
    grid = [(x,) for x in axes[0]]  # 1D for machado

    for scheme_name, weights in WEIGHT_SCHEMES.items():
        for family in FAMILIES:
            key = f'{scheme_name}_{family}'

            best_loss_val = np.inf
            best_entry = None

            for params in grid:
                params_arr = np.array(params)
                C_shifted, delta_theta = get_shifted_design(
                    MODEL, params_arr, family)

                # hV4 LOCO
                vuln_sim, _ = simulate_mean_hc_wfixed(
                    hc_W_hv4, hc_amps_hv4, C_shifted)

                # V1/V2 SRM ΔRDM_sim
                drdm_sim_V1, _ = compute_delta_rdm_sim_srm(
                    W_combined_per_roi['V1'], C_shifted, C_baseline)
                drdm_sim_V2, _ = compute_delta_rdm_sim_srm(
                    W_combined_per_roi['V2'], C_shifted, C_baseline)
                drdm_sim_avg = 0.5 * drdm_sim_V1 + 0.5 * drdm_sim_V2

                loss = compute_fit_loss(vuln_sim, vuln_target, delta_theta,
                                        drdm_sim_avg, drdm_obs_avg, weights)

                if loss['l_fit'] < best_loss_val:
                    best_loss_val = loss['l_fit']
                    best_entry = {
                        'params': params_arr.tolist(),
                        'vuln_sim': vuln_sim.tolist(),
                        **loss,
                    }

            # Permutation test
            if best_entry is not None:
                vuln_sim_best = np.array(best_entry['vuln_sim'])
                perm = run_permutation_tests(vuln_sim_best, vuln_target)

                subject_results[key] = {
                    'scheme': scheme_name,
                    'family': family,
                    'best_params': best_entry['params'],
                    'spearman_r': best_entry['spearman_r'],
                    'rdm_cosine': best_entry.get('rdm_cosine'),
                    'l_fit': best_entry['l_fit'],
                    'l_vuln': best_entry['l_vuln'],
                    'l_rank': best_entry['l_rank'],
                    'l_rdm': best_entry['l_rdm'],
                    'label_perm_p': perm['label_perm_p'],
                    'delta_rho': best_entry['spearman_r'] - baseline_rho,
                }

                print(f'  {key}: Δλ={best_entry["params"][0]:.1f}, '
                      f'ρ={best_entry["spearman_r"]:.3f}, '
                      f'Δρ={subject_results[key]["delta_rho"]:.3f}, '
                      f'p={perm["label_perm_p"]:.4f}, '
                      f'rdm_cos={best_entry.get("rdm_cosine", "N/A")}')

    # Save
    output = {
        'subject': subj,
        'group': 'HC' if is_hc else 'CVD',
        'cvd_type': CVD_TYPES.get(subj, 'normal' if is_hc else 'unknown'),
        'baseline_rho': float(baseline_rho),
        'vuln_target': vuln_target.tolist(),
        'results': subject_results,
        'elapsed_s': time.time() - t0,
    }

    save_path = output_dir / f'sub-{subj}.json'
    with open(save_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f'  Saved: {save_path} ({time.time() - t0:.1f}s)')

    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subjects', nargs='+',
                        default=HC_SUBJECTS + CVD_SUBJECTS)
    parser.add_argument('--data_dir', default=None)
    parser.add_argument('--srm_dir', default=None)
    parser.add_argument('--output_dir',
                        default='results/experiment_b_weight_sweep')
    args = parser.parse_args()

    # Auto-detect data dir
    data_dir = args.data_dir
    if data_dir is None:
        candidates = [
            Path('/scratch/connectome/haba6030/colorBlind/derivatives/'
                 'full_dataset_C010'),
            _PHASE2_DIR.parent / 'phase1_procrustes_decoding' / 'results' /
            'visualization' / 'full_dataset_C010_with_residuals',
        ]
        for c in candidates:
            if c.exists():
                data_dir = str(c)
                break
    if data_dir is None:
        print('ERROR: Could not find C010 data directory')
        sys.exit(1)
    print(f'Data dir: {data_dir}')

    # SRM dir
    srm_dir = Path(args.srm_dir) if args.srm_dir else (
        _PHASE2_DIR / 'results' / 'diagnostics/srm_precompute')
    if not srm_dir.exists():
        print(f'ERROR: SRM precompute dir not found: {srm_dir}')
        sys.exit(1)
    print(f'SRM dir: {srm_dir}')

    # Output
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = _PHASE2_DIR / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load data
    print('\n--- Loading amplitudes ---')
    all_amps = load_data(data_dir)

    print('\n--- Loading SRM artifacts ---')
    srm_artifacts = load_srm_artifacts(srm_dir)

    # Run for each subject
    all_results = {}
    for subj in args.subjects:
        is_hc = subj in HC_SUBJECTS
        result = run_for_subject(subj, all_amps, srm_artifacts,
                                 output_dir, is_hc=is_hc)
        if result:
            all_results[subj] = result

    # --- Summary ---
    print(f'\n{"="*70}')
    print('SUMMARY: WEIGHT SCHEME COMPARISON')
    print(f'{"="*70}')

    for scheme in WEIGHT_SCHEMES:
        print(f'\n  Scheme: {scheme} (weights: {WEIGHT_SCHEMES[scheme]})')
        print(f'  {"Subject":>8} {"Group":>5} {"Family":>7} {"Δλ":>6} '
              f'{"ρ":>7} {"Δρ":>7} {"p":>8} {"Sig":>4}')

        hc_delta_rhos = []
        cvd_delta_rhos = {}

        for subj in sorted(all_results.keys()):
            res = all_results[subj]
            group = res['group']
            # Best across families for this scheme
            best_key = None
            best_rho = -2
            for family in FAMILIES:
                key = f'{scheme}_{family}'
                if key in res['results']:
                    r = res['results'][key]['spearman_r']
                    if r > best_rho:
                        best_rho = r
                        best_key = key

            if best_key is not None:
                r = res['results'][best_key]
                sig = '*' if r['label_perm_p'] < 0.05 else ''
                if r['label_perm_p'] < 0.01:
                    sig = '**'
                if r['label_perm_p'] < 0.001:
                    sig = '***'

                print(f'  sub-{subj:>4} {group:>5} {r["family"]:>7} '
                      f'{r["best_params"][0]:>6.1f} '
                      f'{r["spearman_r"]:>7.3f} '
                      f'{r["delta_rho"]:>7.3f} '
                      f'{r["label_perm_p"]:>8.4f} {sig:>4}')

                if group == 'HC':
                    hc_delta_rhos.append(r['delta_rho'])
                else:
                    cvd_delta_rhos[subj] = r['delta_rho']

        # FPR and specificity
        if hc_delta_rhos:
            n_fp = sum(1 for k, v in all_results.items()
                       if v['group'] == 'HC'
                       and any(v['results'].get(f'{scheme}_{f}', {})
                               .get('label_perm_p', 1) < 0.05
                               for f in FAMILIES))
            fpr = n_fp / len([s for s in all_results if all_results[s]['group'] == 'HC'])
            print(f'\n  HC FPR: {n_fp}/{len(hc_delta_rhos)} = {fpr:.2%}')
            print(f'  HC Δρ: mean={np.mean(hc_delta_rhos):.3f}, '
                  f'range=[{min(hc_delta_rhos):.3f}, {max(hc_delta_rhos):.3f}]')

            for s, dr in sorted(cvd_delta_rhos.items()):
                rank = sum(1 for h in hc_delta_rhos if h < dr) + 1
                emp_p = 1 - rank / (len(hc_delta_rhos) + 1)
                print(f'  CVD sub-{s} Δρ={dr:.3f}: '
                      f'rank={rank}/{len(hc_delta_rhos)+1}, '
                      f'emp_p={emp_p:.3f}')

    # Save summary
    summary = {
        'date': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'model': MODEL,
        'weight_schemes': WEIGHT_SCHEMES,
        'subjects': list(all_results.keys()),
    }
    with open(output_dir / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'\nSummary saved to {output_dir}/summary.json')


if __name__ == '__main__':
    main()
