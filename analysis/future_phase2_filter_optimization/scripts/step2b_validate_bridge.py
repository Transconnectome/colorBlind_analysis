#!/usr/bin/env python3
"""
Step 2b: M_s Bridge Quality Validation

Validates whether structural properties survive the SRM projection:
  M_s = W_SRM^T @ W_FE

This is REQUIRED before filter optimization (step3), because:
- Step 2 validates Procrustes-level FE only
- The filter objective operates in SRM latent space
- V1 SRM has stress plateau 0.127 (structure destroyed)
- hV4 SRM has CIELab sign flip (raw r=+0.402 → SRM r=-0.308)

Four checks:
1. M_s trajectory stability (SRM space fold consistency)
2. M_s RDM preservation (predicted SRM RDM vs actual SRM RDM)
3. Procrustes-to-SRM consistency (rank order preservation across spaces)
4. Predicted SRM vs actual SRM correlation (KEY: operational validity)

Dependencies:
- W_FE per LOCO fold: from step2_validate_prediction.py (saved in step1)
- W_SRM: must be re-fit in step1 and saved (NOT saved from Phase 2)
- aligned_amplitudes.npy: from Phase 2 (ground truth for check #4)

Usage:
    python step2b_validate_bridge.py \
        --model_dir results/step1_prediction_model \
        --srm_dir ../phase2_SRM_across_between/results/c010/combined_with_aligned \
        --output_dir results/step2b_bridge

    # Or via SLURM:
    # sbatch step2b_validate_bridge.sbatch
"""

import json
import argparse
import numpy as np
from pathlib import Path
from itertools import combinations
from scipy import stats

HC_SUBJECTS = [f'sub-{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'sub-{i:02d}' for i in range(8, 11)]
ALL_SUBJECTS = HC_SUBJECTS + CVD_SUBJECTS
ROIS = ['V1', 'V2', 'V3', 'V4']
ROI_DIR_MAP = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'V4'}
N_COLORS = 8
TRUE_HUES = np.arange(0, 360, 45)  # 0, 45, ..., 315


def half_wave_rectified_basis(theta_deg, n_channels=6):
    """Generate half-wave rectified cosine basis at angle theta.

    Args:
        theta_deg: angle in degrees (scalar or array)
        n_channels: number of FE channels (default 6)

    Returns:
        (n_channels,) or (n_angles, n_channels) basis values
    """
    theta_rad = np.deg2rad(theta_deg)
    centers = np.linspace(0, 2 * np.pi, n_channels, endpoint=False)
    if np.isscalar(theta_deg):
        basis = np.maximum(0, np.cos(theta_rad - centers))
        return basis
    theta_rad = np.atleast_1d(theta_rad)[:, None]
    basis = np.maximum(0, np.cos(theta_rad - centers))
    return basis


def check1_trajectory_stability(W_FE_folds, W_SRM, n_angles=360):
    """Check 1: M_s trajectory stability in SRM space.

    For each LOCO fold, compute M_s,f = W_SRM^T @ W_FE,f.
    Generate 360-degree trajectory: M_s,f @ basis_full.T → (k, 360).
    Compare C(8,2)=28 pairwise Pearson correlations across folds.

    Args:
        W_FE_folds: list of (n_voxels, 6) arrays, one per LOCO fold
        W_SRM: (n_voxels, k) SRM projection matrix
        n_angles: number of angles for trajectory (default 360)

    Returns:
        dict with mean_correlation, all_correlations, n_folds
    """
    thetas = np.linspace(0, 360, n_angles, endpoint=False)
    basis_full = half_wave_rectified_basis(thetas)  # (360, 6)

    # Compute M_s trajectories per fold
    trajectories = []
    for W_f in W_FE_folds:
        M_s_f = W_SRM.T @ W_f  # (k, 6)
        traj = M_s_f @ basis_full.T  # (k, 360)
        trajectories.append(traj.flatten())

    # Pairwise correlations
    n_folds = len(trajectories)
    corrs = []
    for i, j in combinations(range(n_folds), 2):
        r, _ = stats.pearsonr(trajectories[i], trajectories[j])
        corrs.append(r)

    return {
        'mean_correlation': float(np.mean(corrs)),
        'min_correlation': float(np.min(corrs)),
        'n_folds': n_folds,
        'n_pairs': len(corrs)
    }


def check2_rdm_preservation(M_s, actual_srm_patterns):
    """Check 2: RDM preservation in SRM space.

    Compare predicted SRM RDM vs actual SRM RDM (Kendall tau).

    Args:
        M_s: (k, 6) bridge matrix (pooled W)
        actual_srm_patterns: (8, k) actual SRM-aligned patterns per color

    Returns:
        dict with kendall_tau, p_value
    """
    # Predicted RDM: M_s @ basis(hue_c) for each color
    basis_8 = half_wave_rectified_basis(TRUE_HUES)  # (8, 6)
    predicted_patterns = (M_s @ basis_8.T).T  # (8, k)

    # Build RDMs (correlation distance)
    n = N_COLORS
    predicted_rdm = np.zeros((n, n))
    actual_rdm = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            predicted_rdm[i, j] = 1 - np.corrcoef(
                predicted_patterns[i], predicted_patterns[j])[0, 1]
            actual_rdm[i, j] = 1 - np.corrcoef(
                actual_srm_patterns[i], actual_srm_patterns[j])[0, 1]

    # Upper triangle
    idx = np.triu_indices(n, k=1)
    tau, p = stats.kendalltau(predicted_rdm[idx], actual_rdm[idx])

    return {
        'kendall_tau': float(tau),
        'p_value': float(p)
    }


def check3_cross_space_consistency(W_FE_pooled, W_SRM):
    """Check 3: Procrustes-to-SRM consistency.

    Compare predicted RDM rank order in Procrustes vs SRM space.
    If high tau → SRM projection preserves rank order.
    If low (especially V1) → M_s distorts structure.

    Args:
        W_FE_pooled: (n_voxels, 6) pooled FE weights
        W_SRM: (n_voxels, k) SRM projection matrix

    Returns:
        dict with kendall_tau, p_value
    """
    basis_8 = half_wave_rectified_basis(TRUE_HUES)  # (8, 6)

    # Predicted Procrustes patterns
    proc_patterns = (W_FE_pooled @ basis_8.T).T  # (8, n_voxels)
    M_s = W_SRM.T @ W_FE_pooled  # (k, 6)
    srm_patterns = (M_s @ basis_8.T).T  # (8, k)

    n = N_COLORS
    proc_rdm = np.zeros((n, n))
    srm_rdm = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            proc_rdm[i, j] = 1 - np.corrcoef(
                proc_patterns[i], proc_patterns[j])[0, 1]
            srm_rdm[i, j] = 1 - np.corrcoef(
                srm_patterns[i], srm_patterns[j])[0, 1]

    idx = np.triu_indices(n, k=1)
    tau, p = stats.kendalltau(proc_rdm[idx], srm_rdm[idx])

    return {
        'kendall_tau': float(tau),
        'p_value': float(p)
    }


def check4_predicted_vs_actual_srm(M_s, actual_srm_patterns):
    """Check 4 (KEY): Predicted SRM vs actual SRM correlation.

    For each color c:
      predicted: s_hat(c) = M_s @ channels(hue_c) → (k,)
      actual: aligned_amplitudes mean across runs → (k,)
    Pearson r per color, then mean across colors.

    This directly tests whether M_s faithfully reproduces observed
    SRM-space representations — the operational requirement for
    filter optimization.

    Args:
        M_s: (k, 6) bridge matrix (pooled W)
        actual_srm_patterns: (8, k) actual SRM-aligned patterns per color
            (mean across runs from aligned_amplitudes.npy)

    Returns:
        dict with mean_r, per_color_r, min_r
    """
    basis_8 = half_wave_rectified_basis(TRUE_HUES)  # (8, 6)
    predicted = (M_s @ basis_8.T).T  # (8, k)

    per_color_r = []
    for c in range(N_COLORS):
        r, _ = stats.pearsonr(predicted[c], actual_srm_patterns[c])
        per_color_r.append(float(r))

    return {
        'mean_r': float(np.mean(per_color_r)),
        'min_r': float(np.min(per_color_r)),
        'per_color_r': per_color_r
    }


def validate_subject_roi(subject, roi, model_dir, srm_dir):
    """Run all 4 bridge checks for one subject-ROI.

    Args:
        subject: e.g., 'sub-01'
        roi: e.g., 'V1'
        model_dir: directory with step1 outputs (W_FE, W_SRM, M_s)
        srm_dir: directory with aligned_amplitudes.npy from Phase 2

    Returns:
        dict with check results, or None if data missing
    """
    roi_dir = ROI_DIR_MAP.get(roi, roi)

    # --- Load W_FE (pooled and per-fold) ---
    # TODO: Define exact file paths once step1 is implemented
    w_fe_path = Path(model_dir) / subject / roi_dir / 'W_FE_pooled.npy'
    w_srm_path = Path(model_dir) / subject / roi_dir / 'W_SRM.npy'
    m_s_path = Path(model_dir) / subject / roi_dir / 'M_s.npy'

    if not all(p.exists() for p in [w_fe_path, w_srm_path, m_s_path]):
        print(f'  SKIP {subject} {roi}: missing model files')
        return None

    W_FE_pooled = np.load(w_fe_path)   # (n_voxels, 6)
    W_SRM = np.load(w_srm_path)        # (n_voxels, k)
    M_s = np.load(m_s_path)            # (k, 6)

    # --- Load W_FE per LOCO fold ---
    fold_dir = Path(model_dir) / subject / roi_dir / 'loco_folds'
    W_FE_folds = []
    for fold_idx in range(N_COLORS):
        fold_path = fold_dir / f'W_FE_fold{fold_idx}.npy'
        if fold_path.exists():
            W_FE_folds.append(np.load(fold_path))

    if len(W_FE_folds) < 2:
        print(f'  SKIP {subject} {roi}: insufficient LOCO folds')
        return None

    # --- Load actual SRM patterns (aligned_amplitudes) ---
    # aligned_amplitudes.npy shape: (n_subjects, 6, 8, k)
    # or per-subject: need to check actual saved format
    aligned_path = Path(srm_dir) / f'{roi_dir}_procrustes_aligned_amplitudes.npy'
    if not aligned_path.exists():
        print(f'  SKIP {subject} {roi}: missing aligned_amplitudes')
        return None

    aligned_all = np.load(aligned_path, allow_pickle=True).item()
    # Format: dict {subject_id: (8_colors, k_dim)} — run-mean already computed
    if subject not in aligned_all:
        print(f'  SKIP {subject} {roi}: not in aligned_amplitudes')
        return None
    actual_srm_patterns = aligned_all[subject]  # (8, k)

    # --- Run checks ---
    results = {
        'subject': subject,
        'roi': roi,
        'n_voxels': W_FE_pooled.shape[0],
        'k_dim': W_SRM.shape[1],
    }

    # Check 1: M_s trajectory stability
    if len(W_FE_folds) >= 2:
        results['check1_trajectory'] = check1_trajectory_stability(
            W_FE_folds, W_SRM)

    # Check 2: RDM preservation
    results['check2_rdm'] = check2_rdm_preservation(M_s, actual_srm_patterns)

    # Check 3: Procrustes-to-SRM consistency
    results['check3_consistency'] = check3_cross_space_consistency(
        W_FE_pooled, W_SRM)

    # Check 4 (KEY): Predicted SRM vs actual SRM correlation
    results['check4_predicted_vs_actual'] = check4_predicted_vs_actual_srm(
        M_s, actual_srm_patterns)

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Step 2b: M_s bridge quality validation')
    parser.add_argument('--model_dir', type=str, required=True,
                        help='Directory with step1 outputs (W_FE, W_SRM, M_s)')
    parser.add_argument('--srm_dir', type=str, required=True,
                        help='Directory with aligned_amplitudes.npy')
    parser.add_argument('--output_dir', type=str, required=True,
                        help='Directory for bridge validation results')
    parser.add_argument('--subjects', type=str, nargs='+', default=None,
                        help='Subjects to validate (default: all)')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    subjects = args.subjects or [s for s in ALL_SUBJECTS]

    print('Step 2b: M_s Bridge Quality Validation')
    print('=' * 50)
    print(f'  Model dir: {args.model_dir}')
    print(f'  SRM dir: {args.srm_dir}')
    print(f'  Subjects: {len(subjects)}')
    print()

    print('NOTE: This script requires W_SRM matrices from step1.')
    print('      W_SRM is NOT saved from Phase 2 (only aligned_amplitudes).')
    print('      Step 1 must re-fit SRM and save W_SRM before running this.')
    print()

    all_results = {}
    for subject in subjects:
        for roi in ROIS:
            result = validate_subject_roi(
                subject, roi, args.model_dir, args.srm_dir)
            if result is not None:
                key = f'{subject}_{roi}'
                all_results[key] = result

                # Save per-subject-ROI
                out_path = output_dir / f'{subject}_{roi}_bridge.json'
                with open(out_path, 'w') as f:
                    json.dump(result, f, indent=2)

    # Summary
    summary = {
        'n_validated': len(all_results),
        'results': all_results
    }
    summary_path = output_dir / 'bridge_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f'\nSummary saved: {summary_path}')

    if not all_results:
        print('\nNo results produced. Likely causes:')
        print('  1. step1 has not been run yet (W_SRM not saved)')
        print('  2. File paths do not match expected structure')
        print('  3. aligned_amplitudes.npy format needs adaptation')


if __name__ == '__main__':
    main()
