#!/usr/bin/env python3
"""
step4_validation.py — LOCO cross-validation + permutation test for RDM filter.

LOCO (8-fold):
  Train on 7 colors (21 pairs) → evaluate on held-out 7 pairs.
  ≥5/8 folds with positive improvement = robust.

Permutation (1000 shuffles):
  Shuffle HC/CVD labels → null distribution of RDM improvement.
  p < 0.05 = systematic effect beyond chance.

Usage:
    mpirun -np 1 python scripts/step4_validation.py \
        --model_dir results/step1_model \
        --filter_dir results/step3_filter \
        --output_dir results/step4_validation \
        --subject_idx 1   # SLURM array: 1=sub-08, 2=sub-09, 3=sub-10
"""

import argparse
import json
import sys
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.optimize import minimize

# -- Imports --
PHASE1_SCRIPTS = Path(__file__).resolve().parents[2] / 'future_phase1_forward_model' / 'scripts'
sys.path.insert(0, str(PHASE1_SCRIPTS))
PHASE2_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(PHASE2_SCRIPTS))

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, K_VALUES, N_CHANNELS, HUE_ANGLES, ROIS,
    load_amplitudes, compute_rdm, rdm_upper_tri,
    DEFAULT_BASELINE_DIR,
)
from utils_filter import (
    T_psi, loss_rdm_with_penalty, compute_predicted_rdm,
    check_monotonicity, N_PAIRS, PAIR_LABELS,
)
from brainiak.funcalign.srm import SRM
from cone_shift_loco import fit_srm_all_hc, build_Ag_all_hc, build_W_HC_for_cvd

ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}
ROIS_FILTER = ['V4', 'V2', 'V1']
N_PERM = 1000


# ============================================================================
# LOCO Validation (8-fold)
# ============================================================================

def get_pair_indices_for_color(held_out_color, n_colors=8):
    """Get indices of pairs involving the held-out color.

    Returns:
        train_pairs: list of pair indices (21 pairs not involving held_out)
        test_pairs: list of pair indices (7 pairs involving held_out)
    """
    train_pairs = []
    test_pairs = []
    idx = 0
    for i in range(n_colors):
        for j in range(i + 1, n_colors):
            if i == held_out_color or j == held_out_color:
                test_pairs.append(idx)
            else:
                train_pairs.append(idx)
            idx += 1
    return train_pairs, test_pairs


def loco_fold(W0, hc_rdm_mean, baseline_rdm, n_channels, held_out_color):
    """Run one LOCO fold: train on 21 pairs, evaluate on 7 held-out pairs.

    Args:
        W0: (K, V_s) encoding weights
        hc_rdm_mean: (8, 8) HC mean RDM
        baseline_rdm: (8, 8) baseline predicted RDM (identity transform)
        n_channels: int
        held_out_color: int (0-7), which color to hold out

    Returns:
        dict with fold results
    """
    train_pairs, test_pairs = get_pair_indices_for_color(held_out_color)

    hc_upper = hc_rdm_mean[np.triu_indices(8, k=1)]
    baseline_upper = baseline_rdm[np.triu_indices(8, k=1)]

    # Create train mask (weight=1 for train pairs, 0 for test)
    train_weights = np.zeros(N_PAIRS)
    train_weights[train_pairs] = 1.0

    # Optimize T_ψ on train pairs only
    def train_obj(psi):
        return loss_rdm_with_penalty(psi, W0, hc_upper, n_channels,
                                     transform='fourier',
                                     weights=train_weights,
                                     penalty_scale=1000.0)

    # Multi-start
    best_res = None
    best_loss = np.inf
    rng = np.random.RandomState(42 + held_out_color)

    starts = [np.zeros(4)]
    for _ in range(3):
        starts.append(rng.uniform(-30, 30, size=4))

    for x0 in starts:
        res = minimize(train_obj, x0=x0, method='L-BFGS-B',
                       options={'maxiter': 500})
        if res.fun < best_loss:
            best_loss = res.fun
            best_res = res

    psi_star = best_res.x
    theta_star = T_psi(HUE_ANGLES, psi_star)

    # Evaluate on test pairs
    pred_rdm = compute_predicted_rdm(W0, theta_star, n_channels)
    pred_upper = pred_rdm[np.triu_indices(8, k=1)]

    # Test pair improvement
    test_baseline_resid = (baseline_upper[test_pairs] - hc_upper[test_pairs]) ** 2
    test_filtered_resid = (pred_upper[test_pairs] - hc_upper[test_pairs]) ** 2

    test_baseline_loss = float(np.sum(test_baseline_resid))
    test_filtered_loss = float(np.sum(test_filtered_resid))

    if test_baseline_loss > 0:
        test_improvement = 100.0 * (1.0 - test_filtered_loss / test_baseline_loss)
    else:
        test_improvement = 0.0

    # Train pair metrics (for diagnostics)
    train_baseline_resid = (baseline_upper[train_pairs] - hc_upper[train_pairs]) ** 2
    train_filtered_resid = (pred_upper[train_pairs] - hc_upper[train_pairs]) ** 2
    train_baseline_loss = float(np.sum(train_baseline_resid))
    train_filtered_loss = float(np.sum(train_filtered_resid))

    is_mono, min_deriv = check_monotonicity(psi_star)

    return {
        'held_out_color': int(held_out_color),
        'held_out_name': ['red', 'orange', 'yellow', 'green',
                          'cyan', 'blue', 'purple', 'magenta'][held_out_color],
        'psi_star': psi_star.tolist(),
        'test_improvement_pct': float(test_improvement),
        'test_baseline_loss': test_baseline_loss,
        'test_filtered_loss': test_filtered_loss,
        'train_baseline_loss': train_baseline_loss,
        'train_filtered_loss': train_filtered_loss,
        'is_monotone': bool(is_mono),
        'n_test_pairs': len(test_pairs),
        'n_train_pairs': len(train_pairs),
    }


def run_loco_validation(W0, hc_rdm_mean, baseline_rdm, n_channels):
    """Run all 8 LOCO folds."""
    folds = []
    for held_out in range(8):
        fold = loco_fold(W0, hc_rdm_mean, baseline_rdm, n_channels, held_out)
        folds.append(fold)

    improvements = [f['test_improvement_pct'] for f in folds]
    n_positive = sum(1 for x in improvements if x > 0)

    return {
        'folds': folds,
        'n_folds_positive': n_positive,
        'n_folds_total': 8,
        'robust': bool(n_positive >= 5),
        'mean_improvement': float(np.mean(improvements)),
        'std_improvement': float(np.std(improvements)),
        'min_improvement': float(np.min(improvements)),
        'max_improvement': float(np.max(improvements)),
    }


# ============================================================================
# Permutation Test
# ============================================================================

def run_permutation_test(baseline_dir, model_dir, roi, roi_label, cvd_subj,
                         n_perm=N_PERM):
    """Permutation test: shuffle HC/CVD labels, refit filter.

    For each permutation:
      1. Randomly assign 7 subjects as "HC", 3 as "CVD"
      2. Rebuild W₀ for the "CVD" subjects using "HC" SRM
      3. Fit Model A filter
      4. Record RDM improvement

    The null hypothesis: the observed improvement is no better than
    random label assignment.

    Args:
        baseline_dir: path to C010 data
        model_dir: path to step1 outputs
        roi: ROI key (e.g., 'V4')
        roi_label: display name (e.g., 'hV4')
        cvd_subj: target CVD subject ID
        n_perm: number of permutations

    Returns:
        dict with null_distribution, observed_improvement, p_value
    """
    baseline_dir = Path(baseline_dir)
    k = K_VALUES[roi]

    # Load observed filter results
    W0 = np.load(Path(model_dir) / roi_label / f'sub-{cvd_subj}' / 'W0.npy')
    hc_rdm_mean = np.load(Path(model_dir) / roi_label / 'hc_rdm_mean.npy')
    baseline_rdm = np.load(Path(model_dir) / roi_label / f'sub-{cvd_subj}' / 'baseline_rdm.npy')

    hc_upper = hc_rdm_mean[np.triu_indices(8, k=1)]
    baseline_upper = baseline_rdm[np.triu_indices(8, k=1)]
    baseline_rss = float(np.sum((baseline_upper - hc_upper) ** 2))

    # Observed improvement (from step3 results)
    # Re-fit to get the observed RDM improvement
    def rdm_obj(psi):
        return loss_rdm_with_penalty(psi, W0, hc_upper, N_CHANNELS,
                                     transform='fourier', penalty_scale=1000.0)

    res = minimize(rdm_obj, x0=np.zeros(4), method='L-BFGS-B',
                   options={'maxiter': 500})
    observed_rss = float(res.fun)
    if baseline_rss > 0:
        observed_improvement = 100.0 * (1.0 - observed_rss / baseline_rss)
    else:
        observed_improvement = 0.0

    # All subjects
    all_subjects = HC_SUBJECTS + CVD_SUBJECTS
    n_total = len(all_subjects)

    # Permutation loop
    null_improvements = []
    rng = np.random.RandomState(42)

    for perm_i in range(n_perm):
        if (perm_i + 1) % 100 == 0:
            print(f'    Permutation {perm_i + 1}/{n_perm}')

        # Random partition: 7 as "HC", 3 as "CVD"
        perm_idx = rng.permutation(n_total)
        perm_hc = [all_subjects[i] for i in perm_idx[:7]]
        perm_cvd_target = all_subjects[perm_idx[7]]  # use first "CVD" as target

        try:
            # Fit SRM on permuted "HC" subjects
            srm_input = []
            for subj in perm_hc:
                amp = load_amplitudes(baseline_dir, subj, roi)
                beta = amp.mean(axis=0)
                srm_input.append(beta.T)

            srm = SRM(n_iter=10, features=k)
            srm.fit(srm_input)

            # Build A_g from permuted HC
            from utils_forward_model import create_basis_matrix, project_new_subject
            C = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
            CtC_inv = np.linalg.inv(C.T @ C)

            A_list = []
            for i_s, subj in enumerate(perm_hc):
                R_i = srm.w_[i_s]
                amp = load_amplitudes(baseline_dir, subj, roi)
                beta = amp.mean(axis=0)
                Z_i = R_i.T @ beta.T
                A_i = Z_i @ C @ CtC_inv
                A_list.append(A_i)
            A_g = np.mean(A_list, axis=0)

            # Build W₀ for permuted CVD target
            amp_cvd = load_amplitudes(baseline_dir, perm_cvd_target, roi)
            beta_cvd = amp_cvd.mean(axis=0)
            R_new = project_new_subject(srm, beta_cvd.T)
            W0_perm = (R_new @ A_g).T

            # Compute permuted HC mean RDM
            perm_hc_rdms = []
            for subj in perm_hc:
                amp = load_amplitudes(baseline_dir, subj, roi)
                Y_mean = amp.mean(axis=0)
                rdm = compute_rdm(Y_mean, 'correlation')
                perm_hc_rdms.append(rdm)
            perm_hc_rdm_mean = np.mean(perm_hc_rdms, axis=0)
            perm_hc_upper = perm_hc_rdm_mean[np.triu_indices(8, k=1)]

            # Baseline for this permutation
            from utils_forward_model import create_basis_full, predict_patterns
            C_baseline = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
            Y_pred_baseline = predict_patterns(W0_perm, C_baseline)
            perm_baseline_rdm = compute_rdm(Y_pred_baseline, 'correlation')
            perm_baseline_upper = perm_baseline_rdm[np.triu_indices(8, k=1)]
            perm_baseline_rss = float(np.sum(
                (perm_baseline_upper - perm_hc_upper) ** 2))

            # Fit filter on permuted data
            def perm_obj(psi):
                return loss_rdm_with_penalty(psi, W0_perm, perm_hc_upper,
                                             N_CHANNELS, transform='fourier',
                                             penalty_scale=1000.0)

            res_perm = minimize(perm_obj, x0=np.zeros(4), method='L-BFGS-B',
                                options={'maxiter': 500})
            perm_rss = float(res_perm.fun)

            if perm_baseline_rss > 0:
                perm_improvement = 100.0 * (1.0 - perm_rss / perm_baseline_rss)
            else:
                perm_improvement = 0.0

            null_improvements.append(perm_improvement)
        except Exception as e:
            # Some permutations may fail (e.g., singular matrices)
            null_improvements.append(0.0)

    null_improvements = np.array(null_improvements)
    p_value = float(np.mean(null_improvements >= observed_improvement))

    return {
        'observed_improvement': float(observed_improvement),
        'observed_rss': float(observed_rss),
        'baseline_rss': float(baseline_rss),
        'null_mean': float(np.mean(null_improvements)),
        'null_std': float(np.std(null_improvements)),
        'null_median': float(np.median(null_improvements)),
        'null_95th': float(np.percentile(null_improvements, 95)),
        'p_value': float(p_value),
        'significant': bool(p_value < 0.05),
        'n_perm': n_perm,
        'null_distribution': null_improvements.tolist(),
    }


def run_subject(cvd_subj, model_dir, baseline_dir, output_dir, n_perm=N_PERM):
    """Run LOCO + permutation for one CVD subject."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model_dir = Path(model_dir)

    results = {
        'subject': f'sub-{cvd_subj}',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }

    for roi in ROIS_FILTER:
        roi_label = ROI_DISPLAY.get(roi, roi)
        n_channels = N_CHANNELS
        print(f'\n{"="*60}')
        print(f'sub-{cvd_subj} | {roi_label} — Validation')
        print(f'{"="*60}')

        try:
            W0 = np.load(model_dir / roi_label / f'sub-{cvd_subj}' / 'W0.npy')
            hc_rdm_mean = np.load(model_dir / roi_label / 'hc_rdm_mean.npy')
            baseline_rdm = np.load(model_dir / roi_label / f'sub-{cvd_subj}' / 'baseline_rdm.npy')
        except FileNotFoundError as e:
            print(f'  SKIP: {e}')
            continue

        # LOCO validation
        t0 = time.time()
        print(f'  Running LOCO (8-fold)...')
        loco = run_loco_validation(W0, hc_rdm_mean, baseline_rdm, n_channels)
        print(f'  LOCO done ({time.time()-t0:.1f}s): '
              f'{loco["n_folds_positive"]}/8 positive, '
              f'mean={loco["mean_improvement"]:.1f}%, '
              f'robust={loco["robust"]}')

        # Permutation test
        t0 = time.time()
        print(f'  Running permutation test ({n_perm} shuffles)...')
        perm = run_permutation_test(baseline_dir, model_dir, roi, roi_label,
                                    cvd_subj, n_perm=n_perm)
        print(f'  Permutation done ({time.time()-t0:.1f}s): '
              f'p={perm["p_value"]:.4f}, '
              f'observed={perm["observed_improvement"]:.1f}%, '
              f'null_mean={perm["null_mean"]:.1f}%')

        results[roi_label] = {
            'loco': loco,
            'permutation': perm,
        }

    # Save
    # LOCO results
    loco_file = output_dir / f'sub-{cvd_subj}_loco_validation.json'
    perm_file = output_dir / f'sub-{cvd_subj}_permutation.json'

    loco_data = {k: v for k, v in results.items() if k != 'timestamp'}
    loco_data['timestamp'] = results['timestamp']

    with open(loco_file, 'w') as f:
        # Save LOCO + permutation together
        json.dump(results, f, indent=2)
    print(f'\nResults saved to {loco_file}')

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Step 4: LOCO + permutation validation')
    parser.add_argument('--model_dir', type=str,
                        default='results/step1_model')
    parser.add_argument('--filter_dir', type=str,
                        default='results/step3_filter')
    parser.add_argument('--baseline_dir', type=str,
                        default=str(DEFAULT_BASELINE_DIR))
    parser.add_argument('--output_dir', type=str,
                        default='results/step4_validation')
    parser.add_argument('--subject_idx', type=int, default=None,
                        help='SLURM array index: 1=sub-08, 2=sub-09, 3=sub-10')
    parser.add_argument('--n_perm', type=int, default=N_PERM)
    args = parser.parse_args()

    n_perm = args.n_perm

    if args.subject_idx is not None:
        cvd_subj = CVD_SUBJECTS[args.subject_idx - 1]
        run_subject(cvd_subj, args.model_dir, args.baseline_dir,
                    args.output_dir, n_perm=n_perm)
    else:
        for cvd_subj in CVD_SUBJECTS:
            run_subject(cvd_subj, args.model_dir, args.baseline_dir,
                        args.output_dir, n_perm=n_perm)


if __name__ == '__main__':
    main()
