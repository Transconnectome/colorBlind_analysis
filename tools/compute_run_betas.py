#!/usr/bin/env python3
"""
Compute per-run effect-size beta maps using Nilearn FirstLevelModel following the notebook.

This script mirrors `fit_one_run_and_get_betas` from `nilearn_test.ipynb`:
- For each preprocessed BOLD run, load events.tsv, fit a FirstLevelModel on that run,
  compute effect-size maps for each color regressor, and save a stacked NIfTI
  with shape (n_colors, X, Y, Z) as well as a masked numpy vector (n_vox, n_colors).

Outputs are saved under `outdir`.
"""
import argparse
import os
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd
import nibabel as nib
from nilearn.glm.first_level import FirstLevelModel
from nilearn.maskers import NiftiMasker
from nilearn.image import load_img


def get_run_tag_from_basename(bname: str):
    parts = bname.split("_")
    for p in parts:
        if p.startswith("run-"):
            return p
    return None


def events_path_for_bold(bold_path, bids_dir):
    bname = os.path.basename(bold_path)
    run_tag = get_run_tag_from_basename(bname)
    sub = bname.split("_")[0]
    if run_tag is None:
        return f"{bids_dir}/{sub}/func/{sub}_task-rsvp_events.tsv"
    else:
        return f"{bids_dir}/{sub}/func/{sub}_task-rsvp_{run_tag}_events.tsv"


def find_bold_runs(sub, fmri_dir):
    pattern = os.path.join(fmri_dir, f"{sub}_task-rsvp_*_desc-preproc_bold.nii*")
    return sorted(glob.glob(pattern))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--sub', default='sub-01')
    p.add_argument('--fmri_dir', default='output/pilot/sub-01/func')
    p.add_argument('--bids_dir', default='pilot')
    p.add_argument('--outdir', default='derivatives/sub-01')
    p.add_argument('--mask_path', default=None)
    p.add_argument('--hrf_model', default='glover')
    p.add_argument('--drift_model', default='cosine')
    p.add_argument('--high_pass', type=float, default=0.01)
    p.add_argument('--noise_model', default='ar1')
    args = p.parse_args()

    Path(args.outdir).mkdir(parents=True, exist_ok=True)
    bolds = find_bold_runs(args.sub, args.fmri_dir)
    if not bolds:
        raise FileNotFoundError('No bold runs found in fmri_dir')

    for bold_path in bolds:
        print('Processing', bold_path)
        ev_path = events_path_for_bold(bold_path, args.bids_dir)
        if not os.path.exists(ev_path):
            print('  events not found:', ev_path, ' -- skipping')
            continue
        ev = pd.read_csv(ev_path, sep='\t')
        all_conds = sorted(ev['trial_type'].unique().tolist())
        conds = [c for c in all_conds if c.startswith('color_')]
        if len(conds) == 0:
            print('  no color conditions found -- skipping')
            continue

        img = load_img(bold_path)
        # frame times / TR handled internally by FirstLevelModel when fitting from file

        glm = FirstLevelModel(t_r=1.5, hrf_model=args.hrf_model, drift_model=args.drift_model,
                               high_pass=args.high_pass, noise_model=args.noise_model, minimize_memory=False)
        try:
            glm = glm.fit(bold_path, events=ev)
        except Exception as e:
            print('  GLM fit failed:', e)
            continue

        # determine base_regs similar to notebook: choose regressor names that match conds
        design = glm.design_matrices_[0]
        color_regressors = [c for c in design.columns if any(c.startswith(cc) for cc in conds)]
        base_regs = []
        for cc in conds:
            base = [r for r in color_regressors if r == cc or (r.startswith(cc) and ('deriv' not in r and 'post' not in r))]
            base_regs.append(base[0] if base else cc)

        # prepare masker
        masker = NiftiMasker(mask_img=args.mask_path, standardize=False).fit()

        # collect effect-size maps and stack
        beta_imgs = []
        for cc in base_regs:
            try:
                beta_img = glm.compute_contrast(cc, output_type='effect_size')
            except Exception as e:
                print('  contrast compute failed for', cc, e)
                beta_img = None
            beta_imgs.append(beta_img)

        # save stacked nifti (n_colors, X, Y, Z)
        # determine reference header/shape from first non-None beta
        good = [bi for bi in beta_imgs if bi is not None]
        if not good:
            print('  no valid betas for run -- skipping')
            continue
        ref = good[0]
        stacked = np.stack([bi.get_fdata(dtype=np.float32) if bi is not None else np.zeros(ref.shape, dtype=np.float32) for bi in beta_imgs], axis=0)
        out_nifti = nib.Nifti1Image(stacked, ref.affine, header=ref.header)
        run_tag = get_run_tag_from_basename(os.path.basename(bold_path)) or 'run-?'
        out_fname = os.path.join(args.outdir, f'{args.sub}_deconv_betas_{run_tag}.nii.gz')
        out_nifti.to_filename(out_fname)
        print('  saved stacked betas:', out_fname)

        # also save masked vectors (n_vox, n_colors)
        X_list = []
        for bi in beta_imgs:
            if bi is None:
                X_list.append(np.zeros((1, masker.mask_img_.get_fdata().sum()), dtype=np.float32))
            else:
                X_list.append(masker.transform(bi))
        X = np.vstack(X_list).T  # (n_vox, n_colors)
        out_vec = out_fname.replace('.nii.gz', '.npy')
        np.save(out_vec, X)
        print('  saved masked beta vectors:', out_vec)


if __name__ == '__main__':
    main()
