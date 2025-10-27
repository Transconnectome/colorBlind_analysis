#!/usr/bin/env python3
"""
diagnose_roi_resampling.py
--------------------------------
Resample each ROI mask into each per-run beta grid and report:
 - whether the resampled mask is empty
 - number of voxels in the resampled mask
 - per-run non-zero counts for the betas within the resampled mask

Writes JSON report to: derivatives/sub-<id>/diagnostics/roi_resampling_diagnosis.json
"""
import os
import glob
import json
import numpy as np
import nibabel as nib
from nilearn import image
from config import cfg


def main():
    subj = cfg.SUB_ID
    analysis_dir = cfg.analysis_dir
    roi_dir = cfg.roi_dir
    out_dir = os.path.join(analysis_dir, 'diagnostics')
    os.makedirs(out_dir, exist_ok=True)

    per_run_pattern = os.path.join(analysis_dir, f'sub-{subj}_rsvp_deconv_betas_run-*.nii.gz')
    per_run_files = sorted(glob.glob(per_run_pattern))

    roi_pattern = os.path.join(roi_dir, f'sub-{subj}_*_mask.nii.gz')
    roi_files = sorted(glob.glob(roi_pattern))

    report = {
        'subject': subj,
        'n_per_run_files': len(per_run_files),
        'n_roi_files': len(roi_files),
        'rois': {},
        'notes': []
    }

    if not roi_files:
        report['notes'].append('No ROI mask files found; run roi_build first')
    if not per_run_files:
        report['notes'].append('No per-run beta files found; run deconv_glm first')

    for roi_f in roi_files:
        roi_name = os.path.basename(roi_f).split('_')[1]
        report['rois'][roi_name] = {'per_run': []}
        try:
            mask_img = nib.load(roi_f)
        except Exception as e:
            report['rois'][roi_name]['error'] = f'Failed to load ROI file: {e}'
            continue

        for run_file in per_run_files:
            try:
                run_img = nib.load(run_file)
                # resample mask to run grid
                resampled = image.resample_img(
                    mask_img,
                    target_affine=run_img.affine,
                    target_shape=run_img.shape[1:],
                    interpolation='nearest'
                )
                mask_bool = resampled.get_fdata().astype(bool)
                n_vox = int(np.count_nonzero(mask_bool))

                # get per-color counts inside mask
                data = run_img.get_fdata()  # (colors, X, Y, Z)
                if data.ndim >= 4:
                    colors = data.shape[0]
                    spatial = int(np.prod(run_img.shape[1:]))
                    resh = data.reshape(colors, spatial)
                    mask_flat = mask_bool.reshape(-1)
                    if mask_flat.size != spatial:
                        # clip/pad if necessary
                        min_len = min(mask_flat.size, spatial)
                        mask_flat = mask_flat[:min_len]
                        resh = resh[:, :min_len]
                    per_color_nonzero = [int(np.count_nonzero(resh[i][mask_flat])) for i in range(resh.shape[0])]
                    total_nonzero = int(np.count_nonzero(resh[:, mask_flat]))
                else:
                    per_color_nonzero = []
                    total_nonzero = int(np.count_nonzero(data[mask_bool]))

                entry = {
                    'run_file': os.path.basename(run_file),
                    'n_voxels_in_mask': n_vox,
                    'per_color_nonzero_counts': per_color_nonzero,
                    'total_nonzero_within_mask': total_nonzero
                }
                report['rois'][roi_name]['per_run'].append(entry)
            except Exception as e:
                report['rois'][roi_name]['per_run'].append({'run_file': os.path.basename(run_file), 'error': str(e)})

    outp = os.path.join(out_dir, 'roi_resampling_diagnosis.json')
    with open(outp, 'w') as f:
        json.dump(report, f, indent=2)

    # print brief summary
    print('Wrote ROI resampling diagnostic to:', outp)
    for roi, info in report['rois'].items():
        runs = info.get('per_run', [])
        empties = sum(1 for r in runs if (r.get('n_voxels_in_mask') == 0 if 'n_voxels_in_mask' in r else False))
        print(f"ROI {roi}: {len(runs)} runs checked, {empties} runs empty after resampling")


if __name__ == '__main__':
    main()
