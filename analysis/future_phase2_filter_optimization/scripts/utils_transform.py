#!/usr/bin/env python3
"""
Shared utilities for the filter optimization pipeline (Future Phase 2).

Step 2 structural validation metrics:
- compute_circular_order_preservation: Spearman rank correlation of angular order
- compute_local_monotonicity: Adjacent pair swap violations on circular hue space
- compute_rdm_rank_preservation: Predicted vs actual RDM rank correlation (Kendall tau)
- compute_trajectory_stability: Pairwise Pearson of 360-degree fold trajectories
"""

import numpy as np
from scipy import stats
from itertools import combinations


def compute_circular_order_preservation(predicted_hues, true_hues):
    """Spearman rank correlation of predicted vs true angular order.

    Try both CW/CCW, take best |rho|.

    Args:
        predicted_hues: (8,) mean predicted hue per color (degrees)
        true_hues: (8,) true hue per color (degrees)

    Returns:
        dict with best_rho, p_value, passed (|rho| > 0.7)
    """
    predicted_hues = np.asarray(predicted_hues, dtype=float)
    true_hues = np.asarray(true_hues, dtype=float)

    # CW: rank both by angle directly
    rho_cw, p_cw = stats.spearmanr(true_hues, predicted_hues)

    # CCW: reverse predicted ordering
    rho_ccw, p_ccw = stats.spearmanr(true_hues, (360 - predicted_hues) % 360)

    if abs(rho_cw) >= abs(rho_ccw):
        best_rho, p_value, direction = rho_cw, p_cw, 'CW'
    else:
        best_rho, p_value, direction = rho_ccw, p_ccw, 'CCW'

    return {
        'best_rho': float(best_rho),
        'p_value': float(p_value),
        'direction': direction,
        'rho_cw': float(rho_cw),
        'rho_ccw': float(rho_ccw),
        'passed': bool(abs(best_rho) > 0.7)
    }


def compute_local_monotonicity(predicted_hues, true_hues):
    """Count adjacent color pairs with swapped predicted order (circular).

    For each adjacent pair (i, i+1 mod 8):
      True direction: (true_hues[i+1] - true_hues[i]) mod 360
      Violation: true goes forward (diff < 180) but predicted goes backward
      (diff >= 180), or vice versa.

    With 45-degree spacing, all true adjacent pairs are forward (CW, diff=45).

    Args:
        predicted_hues: (8,) mean predicted hue per color (degrees)
        true_hues: (8,) true hue per color (degrees)

    Returns:
        dict with n_violations, violation_pairs, passed (n_violations < 2)
    """
    predicted_hues = np.asarray(predicted_hues, dtype=float)
    true_hues = np.asarray(true_hues, dtype=float)
    n = len(true_hues)

    violations = []
    for i in range(n):
        j = (i + 1) % n
        true_diff = (true_hues[j] - true_hues[i]) % 360
        pred_diff = (predicted_hues[j] - predicted_hues[i]) % 360

        true_forward = true_diff < 180
        pred_forward = pred_diff < 180

        if true_forward != pred_forward:
            violations.append((i, j))

    return {
        'n_violations': len(violations),
        'violation_pairs': violations,
        'passed': bool(len(violations) < 2)
    }


def compute_rdm_rank_preservation(amplitudes, W_per_fold, basis_full, hue_angles):
    """Compare predicted RDM with actual data RDM using Kendall tau.

    Actual RDM: mean of 6 per-run correlation-distance RDMs from data.
    Predicted RDM: for each LOCO fold, reconstruct all 8 colors via
        basis_full[hue] @ W, compute correlation-distance RDM, average.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels) actual data
        W_per_fold: list of 8 W matrices, each (n_channels, n_voxels)
        basis_full: (360, n_channels) basis functions
        hue_angles: list of 8 hue angles in degrees

    Returns:
        dict with kendall_tau, p_value, passed (tau > 0.5)
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    # --- Actual data RDM (mean of per-run correlation-distance RDMs) ---
    run_rdms = []
    for r in range(n_runs):
        patterns = amplitudes[r]  # (n_colors, n_voxels)
        corr_matrix = np.corrcoef(patterns)  # (n_colors, n_colors)
        rdm = 1 - corr_matrix
        run_rdms.append(rdm)
    actual_rdm = np.mean(run_rdms, axis=0)

    # --- Predicted RDM (average across LOCO folds) ---
    fold_rdms = []
    for W in W_per_fold:
        # Reconstruct all 8 color patterns from encoding model
        predicted_patterns = np.zeros((n_colors, n_voxels))
        for c in range(n_colors):
            hue_idx = int(hue_angles[c]) % 360
            # basis_full[hue_idx] @ W = (n_channels,) @ (n_channels, n_voxels)
            predicted_patterns[c] = basis_full[hue_idx] @ W

        corr_matrix = np.corrcoef(predicted_patterns)
        rdm = 1 - corr_matrix
        fold_rdms.append(rdm)
    predicted_rdm = np.mean(fold_rdms, axis=0)

    # --- Compare upper triangles ---
    triu_idx = np.triu_indices(n_colors, k=1)
    actual_upper = actual_rdm[triu_idx]
    predicted_upper = predicted_rdm[triu_idx]

    tau, p_value = stats.kendalltau(actual_upper, predicted_upper)

    return {
        'kendall_tau': float(tau),
        'p_value': float(p_value),
        'passed': bool(tau > 0.5)
    }


def compute_trajectory_stability(W_per_fold, basis_full):
    """Pairwise Pearson correlation between fold-level 360-degree trajectories.

    For each fold's W: trajectory = W.T @ basis_full.T -> (n_voxels, 360).
    Flatten, then compute C(n_folds, 2) pairwise Pearson correlations.

    Args:
        W_per_fold: list of W matrices, each (n_channels, n_voxels)
        basis_full: (360, n_channels) basis functions

    Returns:
        dict with mean_correlation, min_correlation, passed (mean > 0.6)
    """
    n_folds = len(W_per_fold)

    # Compute flattened trajectories
    trajectories = []
    for W in W_per_fold:
        # W.T @ basis_full.T = (n_voxels, n_channels) @ (n_channels, 360)
        traj = W.T @ basis_full.T  # (n_voxels, 360)
        trajectories.append(traj.flatten())

    # Pairwise Pearson correlations
    correlations = []
    for i, j in combinations(range(n_folds), 2):
        r, _ = stats.pearsonr(trajectories[i], trajectories[j])
        correlations.append(r)

    mean_corr = float(np.mean(correlations))
    min_corr = float(np.min(correlations))

    return {
        'mean_correlation': mean_corr,
        'min_correlation': min_corr,
        'all_correlations': [float(c) for c in correlations],
        'n_pairs': len(correlations),
        'passed': bool(mean_corr > 0.6)
    }
