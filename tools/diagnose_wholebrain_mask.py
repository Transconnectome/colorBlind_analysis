#!/usr/bin/env python3
"""
diagnose_wholebrain_mask.py
--------------------------------
Simple diagnostic for WholeBrain union-mask issues.

Checks per-run beta NIfTI files for:
 - file list, shapes, affines
 - per-color non-zero voxel counts
 - whether shapes/affines are consistent across runs
 - union mask size (non-zero voxels across runs)

Writes JSON report to: derivatives/sub-<id>/diagnostics/wholebrain_mask_diagnosis.json
and prints a short summary to stdout.
"""
import os
import glob
import json
import numpy as np
import nibabel as nib
from config import cfg


def main():
    subj = cfg.SUB_ID
    analysis_dir = cfg.analysis_dir
    out_dir = os.path.join(analysis_dir, 'diagnostics')
    os.makedirs(out_dir, exist_ok=True)

    per_run_pattern = os.path.join(analysis_dir, f'sub-{subj}_rsvp_deconv_betas_run-*.nii.gz')
    per_run_files = sorted(glob.glob(per_run_pattern))

    report = {
        'subject': subj,
        'n_per_run_files': len(per_run_files),
        'files': [],
        'shape_consistent': True,
        'affine_consistent': True,
        'union_mask_nonzero': None,
        'notes': []
    }

    if not per_run_files:
        report['notes'].append('No per-run beta files found; check deconv_glm output')
        outp = os.path.join(out_dir, 'wholebrain_mask_diagnosis.json')
        with open(outp, 'w') as f:
            json.dump(report, f, indent=2)
        print('No per-run beta files found; wrote report to', outp)
        return

    shapes = []
    affines = []
    imgs = []

    for p in per_run_files:
        try:
            img = nib.load(p)
            imgs.append(img)
            data = img.get_fdata()
            # expected: (colors, X, Y, Z)
            file_info = {
                'path': p,
                'shape': img.shape,
                'dtype': str(data.dtype),
                'affine': img.affine.tolist()
            }

            # per-color non-zero voxels
            try:
                if data.ndim >= 4:
                    counts = [int(np.count_nonzero(data[i])) for i in range(data.shape[0])]
                    file_info['per_color_nonzero'] = counts
                    file_info['total_nonzero'] = int(np.count_nonzero(data))
                elif data.ndim == 3:
                    file_info['per_color_nonzero'] = [int(np.count_nonzero(data))]
                    file_info['total_nonzero'] = int(np.count_nonzero(data))
                else:
                    file_info['per_color_nonzero'] = []
                    file_info['total_nonzero'] = int(np.count_nonzero(data))
            except Exception as e:
                file_info['per_color_nonzero'] = []
                file_info['total_nonzero'] = None
                report['notes'].append(f'Could not compute non-zero counts for {p}: {e}')

            report['files'].append(file_info)
            shapes.append(img.shape)
            affines.append(np.array(img.affine))
        except Exception as e:
            report['notes'].append(f'Failed to load {p}: {e}')

    # shape consistency
    unique_shapes = list({str(s) for s in shapes})
    if len(unique_shapes) > 1:
        report['shape_consistent'] = False
        report['notes'].append(f'Inconsistent shapes across per-run betas: {unique_shapes}')

    # affine consistency (compare array equality)
    if affines:
        base_aff = affines[0]
        for i, a in enumerate(affines[1:], start=1):
            if not np.allclose(base_aff, a):
                report['affine_consistent'] = False
                report['notes'].append(f'Affine differs for file index {i}')
                break

    # Compute union mask non-zero voxels across runs/colors if shapes allow
    try:
        # choose reference shape = imgs[0].shape[1:] if colors present else imgs[0].shape
        ref_shape = imgs[0].shape[1:] if imgs[0].ndim >= 4 else imgs[0].shape
        union = None
        for img in imgs:
            data = img.get_fdata()
            if data.ndim >= 4:
                mask = np.any(data != 0, axis=0)
            else:
                mask = (data != 0)
            # ensure mask shape equals ref_shape
            if mask.shape != tuple(ref_shape):
                report['notes'].append(f'Mask shape {mask.shape} != reference {tuple(ref_shape)}; skipping union computation')
                union = None
                break
            if union is None:
                union = mask.copy()
            else:
                union = np.logical_or(union, mask)

        if union is not None:
            report['union_mask_nonzero'] = int(np.count_nonzero(union))
        else:
            report['union_mask_nonzero'] = None
    except Exception as e:
        report['notes'].append(f'Failed computing union mask: {e}')
        report['union_mask_nonzero'] = None

    outp = os.path.join(out_dir, 'wholebrain_mask_diagnosis.json')
    with open(outp, 'w') as f:
        json.dump(report, f, indent=2)

    # Print short summary
    print('Wrote diagnostic report to:', outp)
    print('n per-run files:', report['n_per_run_files'])
    print('shape_consistent:', report['shape_consistent'])
    print('affine_consistent:', report['affine_consistent'])
    print('union_mask_nonzero:', report['union_mask_nonzero'])
    if report['notes']:
        print('\nNotes:')
        for n in report['notes']:
            print(' -', n)


if __name__ == '__main__':
    main()
