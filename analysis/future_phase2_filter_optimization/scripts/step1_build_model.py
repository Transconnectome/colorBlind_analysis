#!/usr/bin/env python3
"""
step1_build_model.py — Build W₀ (prediction engine) + HC reference RDMs.

For each CVD subject, constructs:
  W₀ = (R_new @ A_g).T  — HC group prior projected into CVD voxel space
  Ȳ_CVD = amp.mean(axis=0) — mean CVD response (8 x V_s)

Also computes:
  HC mean RDM — target geometry for filter optimization
  HC per-subject RDMs — for permutation testing

Reuses SRM+group-prior pipeline from cone_shift_loco.py.

Usage:
    mpirun -np 1 python scripts/step1_build_model.py \
        --baseline_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
        --output_dir results/step1_model
"""

import argparse
import json
import sys
import time
import numpy as np
from pathlib import Path
from datetime import datetime

# -- Import from Phase 1 utils --
PHASE1_SCRIPTS = Path(__file__).resolve().parents[2] / 'future_phase1_forward_model' / 'scripts'
sys.path.insert(0, str(PHASE1_SCRIPTS))

from utils_forward_model import (
    HC_SUBJECTS, CVD_SUBJECTS, K_VALUES,
    N_RUNS, N_COLORS, N_CHANNELS,
    HUE_ANGLES, ROIS,
    load_amplitudes, create_basis_matrix,
    compute_rdm, rdm_upper_tri,
    predict_patterns, project_new_subject,
    DEFAULT_BASELINE_DIR,
)
from brainiak.funcalign.srm import SRM

# -- Import SRM functions from cone_shift_loco --
sys.path.insert(0, str(PHASE1_SCRIPTS))
from cone_shift_loco import (
    fit_srm_all_hc,
    build_Ag_all_hc,
    build_W_HC_for_cvd,
)

ROI_DISPLAY = {'V1': 'V1', 'V2': 'V2', 'V3': 'V3', 'V4': 'hV4'}
COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']


def build_all(baseline_dir, output_dir):
    """Build W₀ + HC RDMs for all ROIs and CVD subjects."""
    baseline_dir = Path(baseline_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for roi in ROIS:
        roi_label = ROI_DISPLAY.get(roi, roi)
        k = K_VALUES[roi]
        print(f'\n{"="*60}')
        print(f'ROI: {roi_label} (k={k})')
        print(f'{"="*60}')

        # 1. Fit SRM on all HC subjects
        t0 = time.time()
        srm, R_dict = fit_srm_all_hc(roi, baseline_dir, k)
        print(f'  SRM fit: {time.time()-t0:.1f}s')

        # 2. Build group prior A_g
        A_g = build_Ag_all_hc(roi, baseline_dir, R_dict)
        print(f'  A_g shape: {A_g.shape}')

        # 3. HC reference RDMs (from actual data, not model predictions)
        hc_rdms = []
        hc_rdm_results = {}
        for subj in HC_SUBJECTS:
            amp = load_amplitudes(baseline_dir, subj, roi)
            Y_mean = amp.mean(axis=0)  # (8, V_s)
            rdm = compute_rdm(Y_mean, 'correlation')
            hc_rdms.append(rdm)
            hc_rdm_results[f'sub-{subj}'] = {
                'rdm_upper_tri': rdm_upper_tri(rdm).tolist(),
                'n_voxels': int(Y_mean.shape[1]),
            }

        hc_rdms_arr = np.array(hc_rdms)  # (7, 8, 8)
        hc_rdm_mean = np.mean(hc_rdms_arr, axis=0)  # (8, 8)

        # Save HC RDMs
        roi_dir = output_dir / roi_label
        roi_dir.mkdir(exist_ok=True)
        np.save(roi_dir / 'hc_rdm_mean.npy', hc_rdm_mean)
        np.save(roi_dir / 'hc_rdm_per_subject.npy', hc_rdms_arr)

        print(f'  HC RDM saved: mean shape {hc_rdm_mean.shape}')

        results[roi_label] = {
            'k': k,
            'n_hc': len(HC_SUBJECTS),
            'hc_rdm_mean_upper': rdm_upper_tri(hc_rdm_mean).tolist(),
        }

        # 4. CVD subjects: build W₀ and save Ȳ_CVD
        for cvd_subj in CVD_SUBJECTS:
            print(f'\n  CVD sub-{cvd_subj}:')
            try:
                amp = load_amplitudes(baseline_dir, cvd_subj, roi)
            except FileNotFoundError as e:
                print(f'    SKIP: {e}')
                continue

            Y_mean = amp.mean(axis=0)  # (8, V_s)
            n_voxels = Y_mean.shape[1]

            # Build W₀ = (R_new @ A_g).T
            W0 = build_W_HC_for_cvd(roi, baseline_dir, srm, A_g, cvd_subj)
            print(f'    W₀ shape: {W0.shape}, n_voxels: {n_voxels}')

            # Compute baseline predicted RDM (no transform)
            C_baseline = create_basis_matrix(HUE_ANGLES, N_CHANNELS)
            Y_pred_baseline = predict_patterns(W0, C_baseline)  # (8, V_s)
            baseline_rdm = compute_rdm(Y_pred_baseline, 'correlation')

            # Compute actual CVD RDM
            cvd_rdm = compute_rdm(Y_mean, 'correlation')

            # Verification: baseline voxel correlation (should match cone_shift_loco)
            from utils_forward_model import voxel_pattern_correlation
            voxel_corrs = voxel_pattern_correlation(Y_pred_baseline, Y_mean)
            mean_corr = float(np.mean(voxel_corrs))
            print(f'    Baseline voxel_corr: {mean_corr:.4f}')

            # Save
            subj_dir = roi_dir / f'sub-{cvd_subj}'
            subj_dir.mkdir(exist_ok=True)
            np.save(subj_dir / 'W0.npy', W0)
            np.save(subj_dir / 'Y_mean.npy', Y_mean)
            np.save(subj_dir / 'baseline_rdm.npy', baseline_rdm)
            np.save(subj_dir / 'cvd_rdm.npy', cvd_rdm)

            # Store metadata
            subj_key = f'sub-{cvd_subj}'
            if subj_key not in results[roi_label]:
                results[roi_label][subj_key] = {}
            results[roi_label][subj_key] = {
                'n_voxels': n_voxels,
                'W0_shape': list(W0.shape),
                'baseline_voxel_corr': mean_corr,
                'baseline_rdm_upper': rdm_upper_tri(baseline_rdm).tolist(),
                'cvd_rdm_upper': rdm_upper_tri(cvd_rdm).tolist(),
                'per_color_corr': voxel_corrs.tolist(),
            }

    # Save config
    config = {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'baseline_dir': str(baseline_dir),
        'output_dir': str(output_dir),
        'hc_subjects': HC_SUBJECTS,
        'cvd_subjects': CVD_SUBJECTS,
        'k_values': K_VALUES,
        'n_channels': N_CHANNELS,
        'hue_angles': HUE_ANGLES.tolist(),
        'rois': ROIS,
    }
    with open(output_dir / 'config.json', 'w') as f:
        json.dump(config, f, indent=2)

    with open(output_dir / 'results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f'\nAll outputs saved to {output_dir}')
    return results


def main():
    parser = argparse.ArgumentParser(description='Step 1: Build W₀ + HC RDMs')
    parser.add_argument('--baseline_dir', type=str,
                        default=str(DEFAULT_BASELINE_DIR))
    parser.add_argument('--output_dir', type=str,
                        default='results/step1_model')
    args = parser.parse_args()

    build_all(args.baseline_dir, args.output_dir)


if __name__ == '__main__':
    main()
