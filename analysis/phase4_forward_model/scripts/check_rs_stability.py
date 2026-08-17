#!/usr/bin/env python3
"""
Split-Half R_s Stability Gate.

Fits SRM separately on odd/even runs, then compares RDM structure
of projections through each SRM.  Mean cosine similarity > 0.5 per ROI
is the gate criterion.

Usage:
    mpirun -np 1 python check_rs_stability.py \
        --rois V1 V2 V3 V4 \
        --baseline_dir /path/to/full_dataset_C010 \
        --output_dir results/srm_projections/stability
"""

import argparse
import json
import numpy as np
from pathlib import Path
from scipy.spatial.distance import pdist, cosine

from utils_forward_model import (
    HC_SUBJECTS, ROIS, K_VALUES,
    load_amplitudes, save_config, DEFAULT_BASELINE_DIR,
)

from brainiak.funcalign.srm import SRM

GATE_THRESHOLD = 0.5
ODD_RUNS = [0, 2, 4]
EVEN_RUNS = [1, 3, 5]


def check_stability_for_roi(roi, baseline_dir, n_iter=10):
    """Split-half SRM stability check for one ROI.

    1. Average odd runs -> beta_odd, average even runs -> beta_even
    2. Fit SRM_odd on odd betas, SRM_even on even betas
    3. For each HC subject, project FULL betas through both SRMs
    4. Compute RDM in each projected space, compare via cosine similarity

    Returns:
        cosine_sims: dict {subject: cosine_similarity}
        gate_pass: bool
    """
    k = K_VALUES[roi]

    # Load all HC data
    hc_data = {}
    for subj in HC_SUBJECTS:
        hc_data[subj] = load_amplitudes(baseline_dir, subj, roi)  # (6, 8, V_s)

    # Build SRM inputs for odd and even halves
    srm_input_odd = []
    srm_input_even = []
    for subj in HC_SUBJECTS:
        amp = hc_data[subj]
        beta_odd = amp[ODD_RUNS].mean(axis=0)   # (8, V_s)
        beta_even = amp[EVEN_RUNS].mean(axis=0)  # (8, V_s)
        srm_input_odd.append(beta_odd.T)   # (V_s, 8)
        srm_input_even.append(beta_even.T)

    # Fit split-half SRMs
    srm_odd = SRM(n_iter=n_iter, features=k)
    srm_odd.fit(srm_input_odd)

    srm_even = SRM(n_iter=n_iter, features=k)
    srm_even.fit(srm_input_even)

    # For each HC subject: project full beta through both, compare RDMs
    cosine_sims = {}
    for i, subj in enumerate(HC_SUBJECTS):
        beta_full = hc_data[subj].mean(axis=0).T  # (V_s, 8)

        # Project through each SRM
        Z_odd = srm_odd.w_[i].T @ beta_full   # (k, 8)
        Z_even = srm_even.w_[i].T @ beta_full  # (k, 8)

        # Compute RDMs
        rdm_odd = pdist(Z_odd.T, 'correlation')   # upper tri of (8, 8) RDM
        rdm_even = pdist(Z_even.T, 'correlation')

        # Cosine similarity (1 - cosine distance)
        if np.any(np.isnan(rdm_odd)) or np.any(np.isnan(rdm_even)):
            cosine_sims[subj] = float('nan')
            print(f'  sub-{subj}: NaN in RDM — skipping')
            continue

        cos_sim = 1.0 - cosine(rdm_odd, rdm_even)
        cosine_sims[subj] = float(cos_sim)
        print(f'  sub-{subj}: cosine_sim = {cos_sim:.3f}')

    # Gate: mean cosine > threshold
    valid_sims = [v for v in cosine_sims.values() if np.isfinite(v)]
    mean_sim = float(np.mean(valid_sims)) if valid_sims else 0.0
    gate_pass = mean_sim > GATE_THRESHOLD

    print(f'  Mean cosine: {mean_sim:.3f} '
          f'(threshold={GATE_THRESHOLD}) -> {"PASS" if gate_pass else "FAIL"}')

    return cosine_sims, gate_pass, mean_sim


def main():
    parser = argparse.ArgumentParser(
        description='Split-Half SRM Stability Gate')
    parser.add_argument('--rois', nargs='+', default=ROIS)
    parser.add_argument('--baseline_dir', type=str,
                        default=str(DEFAULT_BASELINE_DIR))
    parser.add_argument('--output_dir', type=str,
                        default='results/srm_projections/stability')
    parser.add_argument('--n_iter', type=int, default=10)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print('=' * 60)
    print('Split-Half SRM Stability Gate')
    print(f'ROIs: {args.rois}')
    print(f'Gate threshold: cosine > {GATE_THRESHOLD}')
    print('=' * 60)

    summary = {}
    all_pass = True

    for roi in args.rois:
        print(f'\n--- {roi} ---')
        cosine_sims, gate_pass, mean_sim = check_stability_for_roi(
            roi, args.baseline_dir, args.n_iter)
        summary[roi] = {
            'cosine_sims': cosine_sims,
            'mean_cosine': mean_sim,
            'gate_pass': gate_pass,
        }
        if not gate_pass:
            all_pass = False

    # Save summary
    result = {
        'gate_threshold': GATE_THRESHOLD,
        'odd_runs': ODD_RUNS,
        'even_runs': EVEN_RUNS,
        'rois': summary,
        'all_pass': all_pass,
    }
    with open(output_dir / 'stability_summary.json', 'w') as f:
        json.dump(result, f, indent=2)

    save_config(output_dir,
                step='check_rs_stability',
                rois=args.rois,
                baseline_dir=args.baseline_dir,
                gate_threshold=GATE_THRESHOLD,
                n_iter=args.n_iter)

    print('\n' + '=' * 60)
    if all_pass:
        print('GATE: ALL ROIs PASSED -> proceed to Step B')
    else:
        failed = [r for r, v in summary.items() if not v['gate_pass']]
        print(f'GATE: FAILED for {failed} -> investigate before proceeding')
    print('=' * 60)


if __name__ == '__main__':
    main()
