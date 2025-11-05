
import nibabel as nib
import numpy as np
import os

# Define paths
project_dir = '/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis'
atlas_dir = os.path.join(project_dir, 'ProbAtlas_v4/subj_vol_all')
# Assuming a similar output structure as in the notebook for sub-01
output_roi_dir = os.path.join(project_dir, 'derivatives/sub-01/roi') 
os.makedirs(output_roi_dir, exist_ok=True)

# Load the left and right hemisphere max probability maps
lh_atlas = nib.load(os.path.join(atlas_dir, 'maxprob_vol_lh.nii.gz'))
rh_atlas = nib.load(os.path.join(atlas_dir, 'maxprob_vol_rh.nii.gz'))

# Get the data arrays
lh_data = lh_atlas.get_fdata()
rh_data = rh_atlas.get_fdata()

# Combine the two hemispheres.
# A simple addition works here because the label values in lh and rh maps are disjoint.
# We can just add the two arrays.
combined_data = lh_data + rh_data

# Create a new NIfTI image for the combined atlas
combined_atlas = nib.Nifti1Image(combined_data, lh_atlas.affine, lh_atlas.header)

# Save the combined atlas
output_path = os.path.join(output_roi_dir, 'wang_atlas_combined.nii.gz')
nib.save(combined_atlas, output_path)

print(f"Combined atlas saved to: {output_path}")
