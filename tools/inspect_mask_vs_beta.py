#!/usr/bin/env python3
import glob, os
import nibabel as nib
import numpy as np
from nilearn.maskers import NiftiMasker

mask_path = os.path.join('output','pilot','sub-01','anat','sub-01_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz')
print('Mask path exists?', os.path.exists(mask_path), mask_path)

beta_glob = os.path.join('derivatives','sub-01','*deconv_betas_run-*.nii*')
beta_files = sorted(glob.glob(beta_glob))
print('Found beta files:', len(beta_files))
if beta_files:
    print('First beta:', beta_files[0])

# If mask exists, load and report
if os.path.exists(mask_path):
    mimg = nib.load(mask_path)
    mdata = mimg.get_fdata()
    print('Mask shape, affine (upper-left 3x3):', mdata.shape, mimg.affine[:3,:3].tolist())
    print('Mask nonzero voxels (raw):', int((mdata>0).sum()))
else:
    print('Mask not found on disk; cannot load')

# If a beta exists, load and report
if beta_files:
    bimg = nib.load(beta_files[0])
    bdata = bimg.get_fdata()
    print('Beta image shape (raw):', bdata.shape)
    print('Beta affine (upper-left 3x3):', bimg.affine[:3,:3].tolist())
    # handle color dim
    if bdata.ndim == 4:
        if bdata.shape[0] < 50:
            n_colors = bdata.shape[0]
            first_run_mean = bdata.mean(axis=0)
        else:
            n_colors = bdata.shape[-1]
            first_run_mean = bdata.mean(axis=-1)
    else:
        n_colors = None
    print('Detected n_colors:', n_colors)
    # count nonzero voxels per condition (report first up to 8)
    if bdata.ndim == 4:
        if bdata.shape[0] < 50:
            per_cond_nonzero = [int((bdata[i]!=0).sum()) for i in range(bdata.shape[0])]
        else:
            per_cond_nonzero = [int((bdata[...,i]!=0).sum()) for i in range(bdata.shape[-1])]
        print('Per-condition nonzero voxels (first 8):', per_cond_nonzero[:8])

    # If mask exists, try applying it via NiftiMasker to the mean image to see resulting voxels
    if os.path.exists(mask_path):
        mean_nifti = nib.Nifti1Image(first_run_mean.astype('float32'), bimg.affine)
        masker = NiftiMasker(mask_img=mask_path, standardize=False)
        try:
            masker.fit()
            X = masker.transform(mean_nifti)
            # X shape is (n_samples, n_vox)
            print('Masker.transform produced shape:', X.shape)
            if X.ndim == 2:
                print('Number of voxels after masking:', X.shape[1])
        except Exception as e:
            print('Error running masker.transform:', e)
else:
    print('No beta files to inspect')
