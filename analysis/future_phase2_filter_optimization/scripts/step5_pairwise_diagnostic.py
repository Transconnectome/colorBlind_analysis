#!/usr/bin/env python3
"""
step5_pairwise_diagnostic.py — Cross-reference filter effect with pre-validation FDR pairs.

Convergent validity test:
  Pre-validation (SRM-based z-scores) identified specific color pairs
  where CVD differs from HC. Does the filter (Procrustes-based) correct
  precisely those pairs?

For each FDR-significant pair:
  1. Compute baseline distance error: |d_baseline_ij - d_HC_ij|
  2. Compute filtered distance error: |d_filtered_ij - d_HC_ij|
  3. "Rescue" = filtered < baseline (error decreased)

Report: fraction of FDR pairs rescued, direction of correction.

Usage:
    mpirun -np 1 python scripts/step5_pairwise_diagnostic.py \
        --model_dir results/step1_model \
        --filter_dir results/step3_filter \
        --prevalidation_json ../pre_validation/results/fdr_corrected/filter_pre_validation_fdr_corrected.json \
        --output_dir results/step5_pairwise
"""

import argparse
import json
import sys
import numpy as np
from pathlib import Path
from datetime import datetime

# -- Imports --
PHASE1_SCRIPTS = Path(__file__).resolve().parents[2] / 'future_phase1_forward_model' / 'scripts'
sys.path.insert(0, str(PHASE1_SCRIPTS))
PHASE2_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(PHASE2_SCRIPTS))

from utils_forward_model import (
    CVD_SUBJECTS, N_CHANNELS, HUE_ANGLES,
    compute_rdm, rdm_upper_tri,
)
from utils_filter import (
    T_psi, compute_predicted_rdm,
    N_PAIRS, PAIR_LABELS, COLOR_NAMES,
)

ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}
ROI_LABEL_TO_KEY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'hV4': 'V4'}
ROIS_FILTER = ['hV4', 'V2', 'V1']


def load_fdr_pairs(prevalidation_json, subject, roi_label):
    """Extract FDR-significant pairs from pre-validation results.

    Args:
        prevalidation_json: dict, loaded JSON
        subject: e.g., 'sub-08'
        roi_label: e.g., 'hV4', 'V2', 'V1'

    Returns:
        fdr_pairs: list of dicts with pair_name, z_score, p_value
    """
    # Map roi_label to pre-validation key
    # Pre-validation uses 'V1', 'V2', 'V3', 'hV4' (need to check)
    by_subj = prevalidation_json.get('by_subject_roi', {})
    subj_data = by_subj.get(subject, {})

    # Try multiple roi key formats
    roi_data = None
    for key in [roi_label, ROI_LABEL_TO_KEY.get(roi_label, roi_label)]:
        if key in subj_data:
            roi_data = subj_data[key]
            break

    if roi_data is None:
        return []

    pairs_data = roi_data.get('pairs', {})
    fdr_pairs = []
    for pair_name, pair_info in pairs_data.items():
        if pair_info.get('significant_fdr_within_roi', False):
            fdr_pairs.append({
                'pair_name': pair_name,
                'z_score': pair_info['z_score'],
                'p_value': pair_info['p_value'],
                'ci_lower': pair_info.get('ci_lower'),
                'ci_upper': pair_info.get('ci_upper'),
            })

    return fdr_pairs


def pair_name_to_index(pair_name):
    """Convert pair name (e.g., 'red-yellow') to pair index in upper triangle.

    Returns:
        idx: int (0-27), or None if not found
    """
    try:
        return PAIR_LABELS.index(pair_name)
    except ValueError:
        # Try reversed order
        parts = pair_name.split('-')
        if len(parts) == 2:
            reversed_name = f'{parts[1]}-{parts[0]}'
            try:
                return PAIR_LABELS.index(reversed_name)
            except ValueError:
                pass
    return None


def diagnose_pairs(W0, hc_rdm_mean, baseline_rdm, filter_results,
                   fdr_pairs, n_channels):
    """Diagnose whether filter rescues FDR-significant pairs.

    Args:
        W0: (K, V_s)
        hc_rdm_mean: (8, 8)
        baseline_rdm: (8, 8)
        filter_results: dict from step3 (contains psi_star)
        fdr_pairs: list of dicts from load_fdr_pairs
        n_channels: int

    Returns:
        dict with per-pair rescue analysis
    """
    if not fdr_pairs:
        return {'n_fdr_pairs': 0, 'pairs': [], 'rescue_fraction': None}

    # Get optimal psi from Model A
    model_a = filter_results.get('model_A', {})
    psi_star = model_a.get('psi_star')

    if psi_star is None:
        return {'n_fdr_pairs': len(fdr_pairs), 'pairs': [],
                'error': 'No Model A results found'}

    psi_star = np.array(psi_star)
    theta_star = T_psi(HUE_ANGLES, psi_star)
    filtered_rdm = compute_predicted_rdm(W0, theta_star, n_channels)

    hc_upper = hc_rdm_mean[np.triu_indices(8, k=1)]
    baseline_upper = baseline_rdm[np.triu_indices(8, k=1)]
    filtered_upper = filtered_rdm[np.triu_indices(8, k=1)]

    pair_diagnostics = []
    n_rescued = 0

    for fdr_pair in fdr_pairs:
        pair_name = fdr_pair['pair_name']
        idx = pair_name_to_index(pair_name)

        if idx is None:
            pair_diagnostics.append({
                'pair_name': pair_name,
                'error': f'Could not map to index',
            })
            continue

        # Errors
        baseline_error = abs(baseline_upper[idx] - hc_upper[idx])
        filtered_error = abs(filtered_upper[idx] - hc_upper[idx])
        rescued = filtered_error < baseline_error

        if rescued:
            n_rescued += 1

        # Direction analysis
        z_score = fdr_pair['z_score']
        baseline_diff = baseline_upper[idx] - hc_upper[idx]
        filtered_diff = filtered_upper[idx] - hc_upper[idx]

        pair_diagnostics.append({
            'pair_name': pair_name,
            'pair_index': int(idx),
            'fdr_z_score': float(z_score),
            'fdr_direction': 'elevation' if z_score > 0 else 'deficit',
            'hc_distance': float(hc_upper[idx]),
            'baseline_distance': float(baseline_upper[idx]),
            'filtered_distance': float(filtered_upper[idx]),
            'baseline_error': float(baseline_error),
            'filtered_error': float(filtered_error),
            'error_reduction': float(baseline_error - filtered_error),
            'error_reduction_pct': float(
                100 * (1 - filtered_error / baseline_error)
                if baseline_error > 0 else 0),
            'rescued': bool(rescued),
            'correction_direction': (
                'increased' if filtered_diff > baseline_diff else 'decreased'
            ),
        })

    rescue_fraction = n_rescued / len(fdr_pairs) if fdr_pairs else 0

    return {
        'n_fdr_pairs': len(fdr_pairs),
        'n_rescued': n_rescued,
        'rescue_fraction': float(rescue_fraction),
        'rescue_above_50pct': bool(rescue_fraction > 0.5),
        'pairs': pair_diagnostics,
    }


def run_all(model_dir, filter_dir, prevalidation_json_path, output_dir):
    """Run pairwise diagnostic for all CVD subjects and ROIs."""
    model_dir = Path(model_dir)
    filter_dir = Path(filter_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load pre-validation FDR results
    with open(prevalidation_json_path) as f:
        prevalidation_data = json.load(f)

    for cvd_subj in CVD_SUBJECTS:
        subject = f'sub-{cvd_subj}'
        print(f'\n{"="*60}')
        print(f'{subject}')
        print(f'{"="*60}')

        # Load filter results
        filter_file = filter_dir / f'{subject}_filter_results.json'
        if not filter_file.exists():
            print(f'  SKIP: no filter results at {filter_file}')
            continue

        with open(filter_file) as f:
            filter_data = json.load(f)

        subject_results = {
            'subject': subject,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }

        for roi_label in ROIS_FILTER:
            print(f'\n  {roi_label}:')

            # Load step1 data
            try:
                W0 = np.load(model_dir / roi_label / subject / 'W0.npy')
                hc_rdm_mean = np.load(model_dir / roi_label / 'hc_rdm_mean.npy')
                baseline_rdm = np.load(model_dir / roi_label / subject / 'baseline_rdm.npy')
            except FileNotFoundError as e:
                print(f'    SKIP: {e}')
                continue

            # Get filter results for this ROI
            roi_filter = filter_data.get(roi_label, {})
            if not roi_filter:
                print(f'    SKIP: no filter results for {roi_label}')
                continue

            # Load FDR pairs
            fdr_pairs = load_fdr_pairs(prevalidation_data, subject, roi_label)
            print(f'    FDR pairs: {len(fdr_pairs)}')

            if not fdr_pairs:
                subject_results[roi_label] = {
                    'n_fdr_pairs': 0,
                    'note': 'No FDR-significant pairs for this subject-ROI',
                }
                continue

            # Diagnose
            diagnostic = diagnose_pairs(
                W0, hc_rdm_mean, baseline_rdm, roi_filter,
                fdr_pairs, N_CHANNELS)

            print(f'    Rescued: {diagnostic["n_rescued"]}/{diagnostic["n_fdr_pairs"]} '
                  f'({diagnostic["rescue_fraction"]*100:.0f}%)')
            print(f'    Above 50%: {diagnostic["rescue_above_50pct"]}')

            for pd in diagnostic['pairs']:
                status = 'RESCUED' if pd.get('rescued') else 'NOT rescued'
                print(f'      {pd["pair_name"]}: z={pd.get("fdr_z_score", "?"):.2f}, '
                      f'err {pd.get("baseline_error", 0):.4f}→{pd.get("filtered_error", 0):.4f} '
                      f'[{status}]')

            subject_results[roi_label] = diagnostic

        # Save
        out_file = output_dir / f'{subject}_pairwise_diagnostic.json'
        with open(out_file, 'w') as f:
            json.dump(subject_results, f, indent=2)
        print(f'\n  Saved to {out_file}')


def main():
    parser = argparse.ArgumentParser(
        description='Step 5: Pairwise FDR diagnostic')
    parser.add_argument('--model_dir', type=str,
                        default='results/step1_model')
    parser.add_argument('--filter_dir', type=str,
                        default='results/step3_filter')
    parser.add_argument('--prevalidation_json', type=str,
                        default='target_prevalidation/results/fdr_corrected/filter_pre_validation_fdr_corrected.json')
    parser.add_argument('--output_dir', type=str,
                        default='results/step5_pairwise')
    args = parser.parse_args()

    run_all(args.model_dir, args.filter_dir, args.prevalidation_json,
            args.output_dir)


if __name__ == '__main__':
    main()
