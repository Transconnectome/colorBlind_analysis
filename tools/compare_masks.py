#!/usr/bin/env python3
import os, glob
import nibabel as nib
import numpy as np
from nilearn.maskers import NiftiMasker
from nilearn.image import resample_to_img
import json

mask_path = os.path.join('output','pilot','sub-01','anat','sub-01_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz')
beta_glob = os.path.join('derivatives','sub-01','*deconv_betas_run-*.nii*')
beta_files = sorted(glob.glob(beta_glob))
if not beta_files:
    raise SystemExit('No beta files found')

beta0 = beta_files[0]
print('Beta file:', beta0)
print('Notebook mask exists?', os.path.exists(mask_path), mask_path)

bimg = nib.load(beta0)
bdata = bimg.get_fdata()
# derive first_run_mean exactly like script
if bdata.ndim == 4:
    if bdata.shape[0] < 50:
        first_run_mean = bdata.mean(axis=0)
    else:
        first_run_mean = bdata.mean(axis=-1)
else:
    raise SystemExit('Unexpected beta dim')
mean_nifti = nib.Nifti1Image(first_run_mean.astype('float32'), bimg.affine)

# Script-default masker: fit on mean image
masker_script = NiftiMasker(mask_img=None, standardize=False).fit(mean_nifti)
mask_img_script = masker_script.mask_img_
mask_script_data = (mask_img_script.get_fdata()>0)
print('Script-default masked voxels:', int(mask_script_data.sum()))

# Notebook mask-based masker
if os.path.exists(mask_path):
    masker_nb = NiftiMasker(mask_img=mask_path, standardize=False).fit()
    mask_img_nb = masker_nb.mask_img_
    # resample notebook mask to beta grid by resampling mask_img_nb to mean_nifti
    mask_nb_res = resample_to_img(mask_img_nb, mean_nifti, interpolation='nearest')
    mask_nb_data = (mask_nb_res.get_fdata()>0)
    print('Notebook mask resampled voxels:', int(mask_nb_data.sum()))
else:
    raise SystemExit('Notebook mask missing')

# Ensure shapes match by resampling script mask to mean image if needed
if mask_script_data.shape != mask_nb_data.shape:
    mask_script_res = resample_to_img(mask_img_script, mean_nifti, interpolation='nearest')
    mask_script_data = (mask_script_res.get_fdata()>0)
    print('Resampled script mask shape:', mask_script_res.shape)

# Compute intersection/union
inter = np.logical_and(mask_script_data, mask_nb_data).sum()
union = np.logical_or(mask_script_data, mask_nb_data).sum()
only_script = np.logical_and(mask_script_data, ~mask_nb_data).sum()
only_nb = np.logical_and(~mask_script_data, mask_nb_data).sum()

res = {
    'script_mask_total': int(mask_script_data.sum()),
    'notebook_mask_total': int(mask_nb_data.sum()),
    'intersection': int(inter),
    'union': int(union),
    'only_script': int(only_script),
    'only_notebook': int(only_nb),
    'overlap_nb': float(inter / float(mask_nb_data.sum())),
    'overlap_script': float(inter / float(mask_script_data.sum())),
    'jaccard': float(inter / float(union)),
}
print(json.dumps(res, indent=2))

# Also show masker.transform shapes
X_script = masker_script.transform(mean_nifti)
X_nb = masker_nb.transform(mean_nifti)
print('masker.transform shapes:', X_script.shape, X_nb.shape)

