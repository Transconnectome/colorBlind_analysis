#!/usr/bin/env python3
"""
Inspect per-run deconvolution beta NIfTIs and compare sample/label consistency and masks.

Features:
 - Detect per-run n_colors, NaNs, all-zero runs.
 - Compare provided explicit mask to script-derived run mask (Jaccard, overlaps).
 - Report runs that differ in n_colors (and propose padding or trimming).
 - Offer mitigations (resample betas to mask grid, pad/trim color dim, merge masks) when --apply is used.

Usage examples:
  # dry-run diagnostics
  python tools/compare_samples_and_masks.py --sub sub-01 --data_dir derivatives --mask_path output/pilot/sub-01/anat/..._desc-brain_mask.nii.gz

  # apply mitigation: pad shorter runs to expected number of colors (pads with zeros)
  python tools/compare_samples_and_masks.py --sub sub-01 --data_dir derivatives --outdir derivatives/sub-01/diagnostics --pad_colors --apply

"""

import argparse
import os
import glob
import json
import numpy as np
import nibabel as nib
from nilearn.image import resample_to_img


def find_beta_files(subdir, subj):
    pattern = os.path.join(subdir, f"{subj}*deconv_betas_run-*.nii*")
    files = sorted(glob.glob(pattern))
    return files


def load_run_betas(fname):
    img = nib.load(fname)
    data = img.get_fdata(dtype=np.float32)
    affine = img.affine
    # Normalize to (n_colors, X, Y, Z)
    if data.ndim == 4:
        if data.shape[0] < 50:
            arr = data
        else:
            arr = np.moveaxis(data, -1, 0)
    else:
        raise ValueError(f"Unexpected beta image shape {data.shape} in {fname}")
    return arr, affine, fname


def compute_mask_from_run(run_arr, aff):
    # run_arr: (n_colors, X, Y, Z)
    mean_img = np.mean(run_arr, axis=0)
    return nib.Nifti1Image((np.abs(mean_img) > 0).astype(np.uint8), aff)


def resample_beta_to_target_grid(run_arr, run_aff, target_img, interp='continuous'):
    # Resample each 3D volume to target_img grid; return stacked (n_colors, X, Y, Z)
    out_vols = []
    for i in range(run_arr.shape[0]):
        vol = nib.Nifti1Image(run_arr[i].astype(np.float32), run_aff)
        if interp == 'nearest':
            vol_rs = resample_to_img(vol, target_img, interpolation='nearest')
        else:
            vol_rs = resample_to_img(vol, target_img, interpolation='continuous')
        out_vols.append(vol_rs.get_fdata())
    out_stack = np.stack(out_vols, axis=0)
    return out_stack, vol_rs.affine


def save_beta_stack(arr, affine, outpath):
    img = nib.Nifti1Image(arr.astype(np.float32), affine)
    nib.save(img, outpath)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--sub', default='sub-01')
    p.add_argument('--data_dir', default='derivatives')
    p.add_argument('--outdir', default=None)
    p.add_argument('--mask_path', default=None, help='Optional explicit brain mask to compare against')
    p.add_argument('--apply', action='store_true', help='Apply mitigation actions when requested')
    p.add_argument('--pad_colors', action='store_true', help='Pad runs with fewer colors up to expected by adding zero volumes')
    p.add_argument('--trim_colors', action='store_true', help='Trim runs with more colors down to expected (drops last colors)')
    p.add_argument('--resample_to_mask', action='store_true', help='Resample beta volumes to provided mask grid and save resampled files')
    p.add_argument('--merge_masks', choices=['union','intersection'], default=None, help='Create merged mask from provided mask and script default and save it')
    args = p.parse_args()

    if args.outdir is None:
        args.outdir = os.path.join(args.data_dir, args.sub, 'diagnostics')
    os.makedirs(args.outdir, exist_ok=True)

    beta_files = find_beta_files(os.path.join(args.data_dir, args.sub), args.sub)
    if not beta_files:
        beta_files = find_beta_files(os.path.join(args.data_dir, ''), args.sub)
    if not beta_files:
        raise FileNotFoundError(f"No deconv beta files found for {args.sub} in {args.data_dir}")

    runs = [load_run_betas(f) for f in beta_files]
    per_run_info = []
    n_colors_list = [r[0].shape[0] for r in runs]
    expected_n_colors = int(max(n_colors_list))

    for run_arr, aff, fname in runs:
        info = {'fname': fname, 'n_colors': int(run_arr.shape[0]), 'shape': list(run_arr.shape[1:])}
        info['has_nan'] = bool(np.isnan(run_arr).any())
        info['all_zero'] = bool(np.allclose(run_arr, 0.0))
        # count nonzero voxels across mean
        mean_vol = np.mean(run_arr, axis=0)
        info['nonzero_voxels'] = int((np.abs(mean_vol) > 0).sum())
        per_run_info.append(info)

    summary = {
        'sub': args.sub,
        'n_runs': len(runs),
        'n_colors_list': n_colors_list,
        'expected_n_colors': expected_n_colors,
        'per_run': per_run_info,
    }

    # Mask comparisons
    if args.mask_path is not None and os.path.exists(args.mask_path):
        provided_img = nib.load(args.mask_path)
        summary['mask_path'] = args.mask_path
        mask_stats = []
        for run_arr, aff, fname in runs:
            run_mean_nifti = nib.Nifti1Image(np.mean(run_arr, axis=0).astype(np.float32), aff)
            # resample provided to run grid for comparison
            try:
                provided_rs = resample_to_img(provided_img, run_mean_nifti, interpolation='nearest')
                a = (provided_rs.get_fdata() > 0)
                b = (run_mean_nifti.get_fdata() != 0)
                inter = int(np.logical_and(a, b).sum())
                union = int(np.logical_or(a, b).sum())
                a_tot = int(a.sum())
                b_tot = int(b.sum())
                jaccard = inter / float(union) if union>0 else 0.0
                mask_stats.append({'fname': fname, 'a_total': a_tot, 'b_total': b_tot, 'intersection': inter, 'union': union, 'jaccard': jaccard})
            except Exception as e:
                mask_stats.append({'fname': fname, 'error': str(e)})
        summary['mask_stats_per_run'] = mask_stats

    # Identify mismatches
    mismatches = {'n_colors_mismatch_runs': [], 'nan_runs': [], 'all_zero_runs': []}
    for info in per_run_info:
        if info['n_colors'] != expected_n_colors:
            mismatches['n_colors_mismatch_runs'].append(info['fname'])
        if info['has_nan']:
            mismatches['nan_runs'].append(info['fname'])
        if info['all_zero']:
            mismatches['all_zero_runs'].append(info['fname'])
    summary['mismatches'] = mismatches

    out_json = os.path.join(args.outdir, f"compare_samples_and_masks_{args.sub}.json")
    with open(out_json, 'w') as fh:
        json.dump(summary, fh, indent=2)
    print(f"Wrote diagnostics summary to {out_json}")

    # Recommendations
    recs = []
    if mismatches['n_colors_mismatch_runs']:
        recs.append(f"Runs with n_colors != expected ({expected_n_colors}): {len(mismatches['n_colors_mismatch_runs'])}. Consider padding (zeros) or trimming.")
    if mismatches['nan_runs']:
        recs.append(f"Runs with NaNs: {mismatches['nan_runs']}. Fix GLM or drop runs.")
    if 'mask_stats_per_run' in summary:
        # summarize jaccard distribution
        jaccards = [m['jaccard'] for m in summary['mask_stats_per_run'] if 'jaccard' in m]
        if jaccards:
            recs.append(f"Mask Jaccard (provided vs per-run mean) min/mean/max: {min(jaccards):.3f}/{np.mean(jaccards):.3f}/{max(jaccards):.3f}")

    summary['recommendations'] = recs
    with open(out_json, 'w') as fh:
        json.dump(summary, fh, indent=2)

    # Mitigation actions (only when --apply)
    if args.apply:
        print("Applying requested mitigations...")
        # Action: pad or trim runs to expected_n_colors
        if args.pad_colors:
            for run_arr, aff, fname in runs:
                if run_arr.shape[0] < expected_n_colors:
                    n_missing = expected_n_colors - run_arr.shape[0]
                    pad_shape = (n_missing,) + run_arr.shape[1:]
                    pad = np.zeros(pad_shape, dtype=np.float32)
                    new_stack = np.concatenate([run_arr, pad], axis=0)
                    outp = os.path.join(args.outdir, os.path.basename(fname).replace('.nii', '.padded.nii'))
                    save_beta_stack(new_stack, aff, outp)
                    print(f"Padded {os.path.basename(fname)} -> {os.path.basename(outp)} (+{n_missing} zero volumes)")
        if args.trim_colors:
            for run_arr, aff, fname in runs:
                if run_arr.shape[0] > expected_n_colors:
                    new_stack = run_arr[:expected_n_colors]
                    outp = os.path.join(args.outdir, os.path.basename(fname).replace('.nii', '.trimmed.nii'))
                    save_beta_stack(new_stack, aff, outp)
                    print(f"Trimmed {os.path.basename(fname)} -> {os.path.basename(outp)} (kept {expected_n_colors} vols)")
        if args.resample_to_mask and args.mask_path is not None:
            target_img = nib.load(args.mask_path)
            for run_arr, aff, fname in runs:
                try:
                    rs_stack, rs_aff = resample_beta_to_target_grid(run_arr, aff, target_img, interp='continuous')
                    outp = os.path.join(args.outdir, os.path.basename(fname).replace('.nii', '.resampled_to_mask.nii'))
                    save_beta_stack(rs_stack, rs_aff, outp)
                    print(f"Resampled {os.path.basename(fname)} -> {os.path.basename(outp)}")
                except Exception as e:
                    print(f"Failed to resample {fname}: {e}")
        if args.merge_masks and args.mask_path is not None:
            provided_img = nib.load(args.mask_path)
            # build script-default mask on first run
            run_arr0, aff0, _ = runs[0]
            run_mean_nifti = nib.Nifti1Image(np.mean(run_arr0, axis=0).astype(np.float32), aff0)
            provided_rs = resample_to_img(provided_img, run_mean_nifti, interpolation='nearest')
            a = (provided_rs.get_fdata() > 0)
            b = (run_mean_nifti.get_fdata() != 0)
            if args.merge_masks == 'union':
                merged = (np.logical_or(a, b)).astype(np.uint8)
            else:
                merged = (np.logical_and(a, b)).astype(np.uint8)
            merged_nifti = nib.Nifti1Image(merged, run_mean_nifti.affine)
            outp = os.path.join(args.outdir, f"merged_mask_{args.merge_masks}.nii.gz")
            nib.save(merged_nifti, outp)
            print(f"Saved merged mask to {outp}")

    else:
        print("Dry-run complete. To apply mitigations re-run with --apply and one or more mitigation flags (e.g. --pad_colors).")


if __name__ == '__main__':
    main()
