#!/usr/bin/env python3
"""
Step 2: Prediction Model Structural Validation

Validates that the FE+Procrustes prediction engine preserves structural
properties of the color space before proceeding to filter optimization.

Runs LOCO FE in Procrustes space, computes 5 structural metrics per ROI:
  1. MAE (circular error, chance = 90 degrees)
  2. Circular order preservation (Spearman rho, threshold |rho| > 0.7)
  3. Local monotonicity (adjacent swap violations, threshold < 2)
  4. RDM rank preservation (Kendall tau, threshold > 0.5)
  5. Trajectory stability (pairwise Pearson, threshold mean > 0.6)

Usage:
    python step2_validate_prediction.py --subject 01 --rois V1 V2 V3 V4 \
        --baseline_dir /path/to/full_dataset_C010 \
        --output_dir ./results/step2_validation
"""

import sys
import argparse
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import importlib.util

# Resolve paths
SCRIPT_DIR = Path(__file__).resolve().parent
ANALYSIS_DIR = SCRIPT_DIR.parents[1]  # analysis/

# Import create_basis_functions from utils_color_decoding via importlib
_spec = importlib.util.spec_from_file_location(
    'utils_color_decoding',
    ANALYSIS_DIR / 'utils' / 'utils_color_decoding.py'
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
create_basis_functions = _mod.create_basis_functions
circular_diff_deg = _mod.circular_diff_deg

# Import structural validation metrics (same directory)
sys.path.insert(0, str(SCRIPT_DIR))
from utils_transform import (
    compute_circular_order_preservation,
    compute_local_monotonicity,
    compute_rdm_rank_preservation,
    compute_trajectory_stability
)

# ============================================================================
# Constants
# ============================================================================

HUE_ANGLES = [0, 45, 90, 135, 180, 225, 270, 315]
HC_SUBJECTS = [f'{i:02d}' for i in range(1, 8)]
CVD_SUBJECTS = [f'{i:02d}' for i in range(8, 11)]
ROIS = ['V1', 'V2', 'V3', 'V4']

# Default data path (server)
BASELINE_DIR = Path(
    '/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010'
)


# ============================================================================
# Core Functions (local definitions to avoid import chain issues)
# ============================================================================

def load_amplitudes(baseline_dir, subject, roi):
    """Load procrustes-aligned amplitudes.

    Args:
        baseline_dir: Path to full_dataset_C010
        subject: Subject ID (e.g., '01')
        roi: ROI name ('V1', 'V2', 'V3', 'V4')

    Returns:
        amplitudes: (n_runs=6, n_colors=8, n_voxels) array
    """
    amp_path = (Path(baseline_dir) / f"sub-{subject}" / roi
                / "amplitudes_procrustes.npy")
    if not amp_path.exists():
        raise FileNotFoundError(f"Not found: {amp_path}")
    return np.load(amp_path)


def circular_distance(y_true, y_pred):
    """Absolute circular distance in degrees (0-180)."""
    diff = np.abs(np.asarray(y_true, dtype=float)
                  - np.asarray(y_pred, dtype=float))
    return np.minimum(diff, 360 - diff)


def fit_W(X, hues, n_channels=6, alpha=0):
    """Fit encoding weights W with optional Ridge.

    W = pinv(C) @ X  (OLS when alpha=0)

    Args:
        X: (n_samples, n_voxels) pooled brain patterns
        hues: (n_samples,) hue angles in degrees
        n_channels: number of basis channels
        alpha: Ridge penalty (0 = OLS)

    Returns:
        W: (n_channels, n_voxels)
        basis_full: (360, n_channels)
    """
    basis_full = create_basis_functions(n_channels=n_channels)
    C = basis_full[np.asarray(hues, dtype=int)]  # (n_samples, n_channels)

    if alpha > 0:
        W = np.linalg.solve(
            C.T @ C + alpha * np.eye(n_channels),
            C.T @ X
        )
    else:
        W = np.linalg.pinv(C) @ X

    return W, basis_full


def decode_with_W(W, basis_full, X_test):
    """Decode hue using correlation template matching.

    Args:
        W: (n_channels, n_voxels)
        basis_full: (360, n_channels)
        X_test: (n_samples, n_voxels)

    Returns:
        pred_hues: (n_samples,) predicted hue angles (0-359)
    """
    channel_responses = W @ X_test.T  # (n_channels, n_samples)
    n_samples = X_test.shape[0]
    pred_hues = np.zeros(n_samples)

    for i in range(n_samples):
        resp = channel_responses[:, i]
        corrs = np.array([
            np.corrcoef(resp, basis_full[h])[0, 1] for h in range(360)
        ])
        pred_hues[i] = np.nanargmax(corrs)

    return pred_hues


def circular_mean_deg(angles_deg):
    """Circular mean of angles in degrees."""
    rad = np.deg2rad(angles_deg)
    mean_sin = np.mean(np.sin(rad))
    mean_cos = np.mean(np.cos(rad))
    return np.rad2deg(np.arctan2(mean_sin, mean_cos)) % 360


# ============================================================================
# Validation
# ============================================================================

def validate_roi(amplitudes, roi_name):
    """Run LOCO FE validation for a single ROI.

    For each LOCO fold (test_color = 0..7):
      - Train: 7 colors x 6 runs = 42 samples
      - fit_W (OLS, alpha=0) -> W, basis_full
      - decode_with_W -> predicted hues per run
      - Store W matrix, circular mean predicted hue

    Then compute 5 structural metrics.

    Args:
        amplitudes: (n_runs, n_colors, n_voxels)
        roi_name: ROI name for logging

    Returns:
        dict with all 5 metrics and overall pass/fail
    """
    n_runs, n_colors, n_voxels = amplitudes.shape

    W_per_fold = []
    mean_pred_hues = np.zeros(n_colors)
    per_color_errors = []

    for test_color in range(n_colors):
        train_colors = [c for c in range(n_colors) if c != test_color]
        train_hues = np.array([HUE_ANGLES[c] for c in train_colors])
        test_hue = HUE_ANGLES[test_color]

        # Training data: 7 colors x 6 runs = 42 samples
        X_train = amplitudes[:, train_colors, :].reshape(-1, n_voxels)
        hues_train = np.tile(train_hues, n_runs)

        # Test data: 6 runs of held-out color
        X_test = amplitudes[:, test_color, :]  # (6, n_voxels)

        # Fit W (OLS, alpha=0) — consistent with LOCO_trials baseline
        W, basis_full = fit_W(X_train, hues_train, alpha=0)
        W_per_fold.append(W)

        # Decode
        pred_hues = decode_with_W(W, basis_full, X_test)

        # Circular mean of predicted hues across 6 runs
        mean_pred_hues[test_color] = circular_mean_deg(pred_hues)

        # Errors
        errors = circular_distance(np.full(n_runs, test_hue), pred_hues)
        per_color_errors.append(float(np.mean(errors)))

    # ---- Metric 1: MAE ----
    mae = float(np.mean(per_color_errors))
    metric1 = {
        'mae': mae,
        'per_color_errors': per_color_errors,
        'passed': bool(mae < 90.0)  # chance level = 90 degrees
    }

    # ---- Metric 2: Circular Order Preservation ----
    true_hues = np.array(HUE_ANGLES, dtype=float)
    metric2 = compute_circular_order_preservation(mean_pred_hues, true_hues)

    # ---- Metric 3: Local Monotonicity ----
    metric3 = compute_local_monotonicity(mean_pred_hues, true_hues)
    # Convert tuples to lists for JSON serialization
    metric3['violation_pairs'] = [list(p) for p in metric3['violation_pairs']]

    # ---- Metric 4: RDM Rank Preservation ----
    metric4 = compute_rdm_rank_preservation(
        amplitudes, W_per_fold, basis_full, HUE_ANGLES)

    # ---- Metric 5: Trajectory Stability ----
    metric5 = compute_trajectory_stability(W_per_fold, basis_full)

    # Overall pass
    metrics_passed = [
        metric1['passed'],
        metric2['passed'],
        metric3['passed'],
        metric4['passed'],
        metric5['passed']
    ]

    return {
        'n_voxels': int(n_voxels),
        'metric1_mae': metric1,
        'metric2_circular_order': metric2,
        'metric3_monotonicity': metric3,
        'metric4_rdm_rank': metric4,
        'metric5_trajectory': metric5,
        'overall_pass': all(metrics_passed),
        'n_passed': sum(metrics_passed)
    }


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Step 2: Prediction Model Structural Validation')
    parser.add_argument('--subject', type=str, required=True,
                        help='Subject ID (e.g., 01)')
    parser.add_argument('--rois', nargs='+', default=ROIS)
    parser.add_argument('--baseline_dir', type=str,
                        default=str(BASELINE_DIR))
    parser.add_argument('--output_dir', type=str,
                        default=str(SCRIPT_DIR.parent / 'results'
                                    / 'step2_validation'))
    args = parser.parse_args()

    baseline_dir = Path(args.baseline_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    subject_group = 'HC' if args.subject in HC_SUBJECTS else 'CVD'

    print('=' * 70)
    print('Step 2: Prediction Model Structural Validation')
    print(f'Subject: sub-{args.subject} ({subject_group})')
    print(f'ROIs: {args.rois}')
    print(f'Data: {baseline_dir}')
    print('=' * 70)

    results = {}

    for roi in args.rois:
        print(f'\n--- {roi} ---')

        # Skip sub-07 hV4 (16 voxels -> NaN risk)
        if args.subject == '07' and roi == 'V4':
            print('  SKIPPED: sub-07 V4 (hV4) has only 16 voxels')
            results[roi] = {'skipped': True, 'reason': '16 voxels, NaN risk'}
            continue

        try:
            amp = load_amplitudes(args.baseline_dir, args.subject, roi)
            print(f'  Loaded: {amp.shape}')
        except FileNotFoundError as e:
            print(f'  ERROR: {e}')
            results[roi] = {'error': str(e)}
            continue

        roi_result = validate_roi(amp, roi)
        results[roi] = roi_result

        # Print summary
        m1 = roi_result['metric1_mae']
        m2 = roi_result['metric2_circular_order']
        m3 = roi_result['metric3_monotonicity']
        m4 = roi_result['metric4_rdm_rank']
        m5 = roi_result['metric5_trajectory']

        print(f'  MAE:           {m1["mae"]:.1f} deg '
              f'({"PASS" if m1["passed"] else "FAIL"})')
        print(f'  Order rho:     {m2["best_rho"]:.3f} '
              f'({"PASS" if m2["passed"] else "FAIL"})')
        print(f'  Monotonicity:  {m3["n_violations"]} violations '
              f'({"PASS" if m3["passed"] else "FAIL"})')
        print(f'  RDM tau:       {m4["kendall_tau"]:.3f} '
              f'({"PASS" if m4["passed"] else "FAIL"})')
        print(f'  Trajectory:    {m5["mean_correlation"]:.3f} '
              f'({"PASS" if m5["passed"] else "FAIL"})')
        print(f'  Overall:       {roi_result["n_passed"]}/5 passed')

    # Save per-subject results
    output_file = output_dir / f'sub-{args.subject}_validation.json'
    save_data = {
        'subject': args.subject,
        'subject_group': subject_group,
        'rois': args.rois,
        'baseline_dir': str(baseline_dir),
        'alignment': 'procrustes',
        'alpha': 0,
        'results': results,
        'timestamp': datetime.now().isoformat()
    }
    with open(output_file, 'w') as f:
        json.dump(save_data, f, indent=2)
    print(f'\nSaved: {output_file}')

    # Config (safe to overwrite — identical across subjects)
    config_file = output_dir / 'config.json'
    config_data = {
        'description': 'Step 2: Prediction Model Structural Validation',
        'metrics': {
            'metric1_mae': 'Mean Absolute Error (circular, chance=90 deg)',
            'metric2_circular_order':
                'Spearman rank correlation (|rho| > 0.7)',
            'metric3_monotonicity':
                'Adjacent pair swap violations (< 2)',
            'metric4_rdm_rank':
                'Kendall tau of predicted vs actual RDM (tau > 0.5)',
            'metric5_trajectory':
                'Mean pairwise Pearson of 360 deg trajectories (r > 0.6)'
        },
        'method': 'LOCO FE (OLS, alpha=0, 6 channels)',
        'alignment': 'procrustes',
        'baseline_dir': str(baseline_dir),
        'created': datetime.now().isoformat()
    }
    with open(config_file, 'w') as f:
        json.dump(config_data, f, indent=2)

    # Summary
    print(f'\n{"=" * 70}')
    print('SUMMARY')
    print(f'{"=" * 70}')
    for roi in args.rois:
        if roi not in results:
            continue
        r = results[roi]
        if r.get('skipped') or r.get('error'):
            status = r.get('reason', r.get('error', 'unknown'))
            print(f'  {roi}: {status}')
        else:
            print(f'  {roi}: {r["n_passed"]}/5 passed | '
                  f'MAE={r["metric1_mae"]["mae"]:.1f} deg | '
                  f'rho={r["metric2_circular_order"]["best_rho"]:.3f} | '
                  f'tau={r["metric4_rdm_rank"]["kendall_tau"]:.3f}')


if __name__ == '__main__':
    main()
