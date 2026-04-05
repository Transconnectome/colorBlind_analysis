#!/usr/bin/env python3
"""
step5_hc_replication_null.py — Statistical testing for LOCO simulation.

Step 3 finds delta* by matching HC_shifted LOCO to CVD's pattern.
Step 5 tests significance with TWO null models:
  1. Exact permutation test (8! = 40,320): permute color labels of CVD LOCO
  2. Monte Carlo null (N random shifts): random delta -> HC LOCO sim -> r distribution

Runs on SERVER (heavy: 7 HC x 8 folds x N_MC random shifts x 4 ROIs).

Usage:
    mpirun -np 1 python scripts/step5_hc_replication_null.py \
        --step3_dir results/step3_loco \
        --n_mc 1000 \
        --output_dir results/step5_hc_replication
"""

import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
from itertools import permutations
from scipy.stats import spearmanr
import sys

_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR))

# Server path for forward model scripts
_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
sys.path.insert(0, _FWD_DIR)

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, ROIS, N_CHANNELS, N_RUNS, N_COLORS,
    HUE_ANGLES, load_amplitudes, create_basis_matrix,
    gcv_select_alpha, fit_W_ridge, voxel_pattern_correlation,
    DEFAULT_BASELINE_DIR,
)
from utils_distortion_models import (
    MODELS, get_design_matrix, get_initial_params,
)

CVD_TYPE = {'08': 'deutan', '09': 'protan', '10': 'normal'}


def simulate_hc_loco_single(hc_amps, C_original, C_shifted):
    """Run LOCO simulation, return HC mean vulnerability (8,)."""
    hc_vuln_all = []
    for amp_hc in hc_amps:
        V_s = amp_hc.shape[2]
        fold_corrs = np.zeros(N_COLORS)
        for color in range(N_COLORS):
            train_colors = [c for c in range(N_COLORS) if c != color]
            X_train = amp_hc[:, train_colors].reshape(-1, V_s)
            C_train = np.tile(C_original[train_colors], (N_RUNS, 1))
            alpha, _ = gcv_select_alpha(C_train, X_train)
            W = fit_W_ridge(C_train, X_train, alpha)
            Y_pred = C_shifted[color:color+1] @ W
            Y_test = amp_hc[:, color].mean(axis=0, keepdims=True)
            r = voxel_pattern_correlation(Y_pred, Y_test)
            fold_corrs[color] = r[0]
        hc_vuln_all.append(fold_corrs)
    return np.mean(hc_vuln_all, axis=0)


def exact_permutation_test(observed_r, hc_vuln, cvd_target):
    """Exact permutation test: permute color labels of CVD LOCO.

    8! = 40,320 permutations (feasible).

    Returns:
        p_value: fraction of permutations with r >= observed_r
        null_distribution: array of r values
    """
    n_perms = 0
    n_exceed = 0
    null_rs = []

    for perm in permutations(range(N_COLORS)):
        cvd_permuted = cvd_target[list(perm)]
        rho, _ = spearmanr(hc_vuln, cvd_permuted)
        if np.isfinite(rho):
            null_rs.append(float(rho))
            if rho >= observed_r:
                n_exceed += 1
        n_perms += 1

    p_value = n_exceed / n_perms if n_perms > 0 else 1.0
    return p_value, np.array(null_rs)


def monte_carlo_null(observed_r, hc_amps, cvd_target, model_name, cvd_type,
                     n_mc=1000, seed=42):
    """Monte Carlo null: random delta -> HC LOCO sim -> r distribution.

    Returns:
        p_value: fraction of random shifts with r >= observed_r
        null_distribution: array of r values
    """
    rng = np.random.RandomState(seed)
    bounds = MODELS[model_name]['bounds']
    C_original = create_basis_matrix(HUE_ANGLES, N_CHANNELS)

    null_rs = []
    for i in range(n_mc):
        if (i + 1) % 100 == 0:
            print(f'      MC iteration {i+1}/{n_mc}')

        # Random params from uniform within bounds
        random_params = np.array([
            rng.uniform(lo, hi) for lo, hi in bounds
        ])

        C_shifted = get_design_matrix(model_name, random_params, cvd_type=cvd_type)
        hc_vuln = simulate_hc_loco_single(hc_amps, C_original, C_shifted)

        rho, _ = spearmanr(hc_vuln, cvd_target)
        null_rs.append(float(rho) if np.isfinite(rho) else 0.0)

    null_rs = np.array(null_rs)
    p_value = float(np.mean(null_rs >= observed_r))
    return p_value, null_rs


def run_step5(roi, cvd_subj, hc_amps, step3_dir, n_mc, output_dir):
    """Run Step 5 for one CVD subject x ROI."""
    cvd_type = CVD_TYPE[cvd_subj]

    # Load Step 3 results
    loco_path = Path(step3_dir) / roi / f'sub-{cvd_subj}_loco_sim.json'
    if not loco_path.exists():
        print(f'    Step 3 results not found: {loco_path}')
        return

    with open(loco_path) as f:
        step3_data = json.load(f)

    cvd_target = np.array(step3_data['cvd_loco_target'])

    model_results = {}
    for model_name in step3_data['models']:
        if model_name not in MODELS:
            continue

        mode_data = step3_data['models'][model_name].get('shift_at_test', {})
        if not mode_data:
            continue

        best_params = np.array(mode_data['params'])
        observed_r = mode_data['spearman_r']
        hc_shifted_vuln = np.array(mode_data['hc_shifted_vuln'])

        print(f'    {model_name}: observed r={observed_r:.3f}')

        # 1. Exact permutation test
        print(f'      Running exact permutation test (8! = 40,320)...')
        perm_p, perm_null = exact_permutation_test(
            observed_r, hc_shifted_vuln, cvd_target)
        print(f'      Permutation p={perm_p:.4f}')

        # 2. Monte Carlo null
        print(f'      Running Monte Carlo null (n={n_mc})...')
        mc_p, mc_null = monte_carlo_null(
            observed_r, hc_amps, cvd_target, model_name, cvd_type, n_mc)
        print(f'      MC p={mc_p:.4f}')

        model_results[model_name] = {
            'observed_r': float(observed_r),
            'best_params': best_params.tolist(),
            'hc_shifted_vuln': hc_shifted_vuln.tolist(),
            'exact_permutation': {
                'p_value': float(perm_p),
                'n_permutations': 40320,
                'null_mean': float(np.mean(perm_null)),
                'null_std': float(np.std(perm_null)),
                'null_95th': float(np.percentile(perm_null, 95)),
            },
            'monte_carlo': {
                'p_value': float(mc_p),
                'n_samples': n_mc,
                'null_mean': float(np.mean(mc_null)),
                'null_std': float(np.std(mc_null)),
                'null_95th': float(np.percentile(mc_null, 95)),
            },
        }

    # Save
    out_dir = Path(output_dir) / roi
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        'subject': cvd_subj,
        'roi': roi,
        'cvd_type': cvd_type,
        'timestamp': datetime.now().isoformat(),
        'n_mc': n_mc,
        'cvd_loco_target': cvd_target.tolist(),
        'models': model_results,
    }
    out_path = out_dir / f'sub-{cvd_subj}_replication.json'
    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2)
    print(f'    Saved to {out_path}')


def main():
    parser = argparse.ArgumentParser(
        description='Step 5: HC replication null test')
    parser.add_argument('--step3_dir', type=str,
                        default='results/step3_loco')
    parser.add_argument('--baseline_dir', type=str,
                        default=str(DEFAULT_BASELINE_DIR))
    parser.add_argument('--n_mc', type=int, default=1000,
                        help='Number of Monte Carlo iterations')
    parser.add_argument('--output_dir', type=str,
                        default='results/step5_hc_replication')
    parser.add_argument('--rois', nargs='+', default=ROIS)
    parser.add_argument('--cvd_subjects', nargs='+', default=CVD_SUBJECTS)
    args = parser.parse_args()

    print('=' * 60)
    print('Step 5: HC Replication Null Test')
    print(f'N_MC: {args.n_mc}')
    print(f'Baseline dir: {args.baseline_dir}')
    print('=' * 60)

    for roi in args.rois:
        print(f'\n--- {roi} ---')

        # Load HC amplitudes
        print(f'  Loading HC amplitudes...')
        hc_amps = []
        for subj in HC_SUBJECTS:
            amp = load_amplitudes(args.baseline_dir, subj, roi)
            hc_amps.append(amp)

        for cvd_subj in args.cvd_subjects:
            print(f'\n  sub-{cvd_subj} ({CVD_TYPE[cvd_subj]}):')
            run_step5(roi, cvd_subj, hc_amps, args.step3_dir, args.n_mc,
                      args.output_dir)

    print('\nStep 5 complete.')


if __name__ == '__main__':
    main()
