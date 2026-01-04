#!/usr/bin/env python3
"""
Python-based Deoblique Script
Uses nibabel to deoblique NIfTI files without AFNI dependency
"""

import nibabel as nib
import numpy as np
from pathlib import Path
import sys
import shutil

def get_obliquity(affine):
    """Calculate obliquity angle from affine matrix"""
    # Extract rotation component
    rotation = affine[:3, :3]

    # Normalize to get pure rotation (remove scaling)
    scales = np.sqrt(np.sum(rotation**2, axis=0))
    rotation_norm = rotation / scales

    # Calculate deviation from cardinal axes
    # Identity matrix = perfect cardinal alignment
    identity = np.eye(3)

    # Frobenius norm of difference
    deviation = np.linalg.norm(rotation_norm - identity, 'fro')

    # Convert to approximate angle in degrees
    angle = np.degrees(np.arcsin(min(deviation / np.sqrt(2), 1.0)))

    return angle

def deoblique_nifti(input_file, output_file):
    """
    Deoblique a NIfTI file by aligning to cardinal axes

    Returns:
        tuple: (original_obliquity, new_obliquity)
    """
    # Load image
    img = nib.load(input_file)
    data = img.get_fdata()
    affine = img.affine.copy()
    header = img.header.copy()

    # Calculate original obliquity
    orig_obliquity = get_obliquity(affine)

    # Extract components
    rotation = affine[:3, :3]
    translation = affine[:3, 3]

    # Get voxel sizes (scales)
    scales = np.sqrt(np.sum(rotation**2, axis=0))

    # Create cardinal affine
    # Preserve voxel sizes but align to axes
    new_affine = np.eye(4)
    new_affine[:3, :3] = np.diag(scales)
    new_affine[:3, 3] = translation

    # Update header to remove obliquity info
    header.set_sform(new_affine, code='aligned')
    header.set_qform(new_affine, code='aligned')

    # Create new image
    new_img = nib.Nifti1Image(data, new_affine, header)

    # Save
    nib.save(new_img, output_file)

    # Calculate new obliquity
    new_obliquity = get_obliquity(new_affine)

    return orig_obliquity, new_obliquity

def main():
    # Configuration
    raw_dir = Path('/storage/connectome/haba6030/bids_editted')
    out_dir = Path('/storage/connectome/haba6030/colorBlind_data_deoblique')
    subjects = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10']

    print("=" * 80)
    print("Python-based Deoblique Processing")
    print("=" * 80)
    print()

    # Create output directory
    out_dir.mkdir(parents=True, exist_ok=True)

    for sub in subjects:
        print("=" * 40)
        print(f"Processing Sub-{sub}...")
        print("=" * 40)

        sub_id = f'sub-{sub}'

        # Create directories
        (out_dir / sub_id / 'func').mkdir(parents=True, exist_ok=True)
        (out_dir / sub_id / 'fmap').mkdir(parents=True, exist_ok=True)
        (out_dir / sub_id / 'anat').mkdir(parents=True, exist_ok=True)

        # Copy T1w (not oblique)
        print("  [1/4] Copying T1w...")
        anat_files = list((raw_dir / sub_id / 'anat').glob('*.nii.gz'))
        for anat_file in anat_files:
            shutil.copy2(anat_file, out_dir / sub_id / 'anat' / anat_file.name)
        print(f"    ✅ {len(anat_files)} anatomical files copied")

        # Deoblique BOLD runs
        print("  [2/4] Deobliquing BOLD runs...")
        for run in range(1, 7):
            input_file = raw_dir / sub_id / 'func' / f'{sub_id}_task-rsvp_run-{run}_bold.nii.gz'
            output_file = out_dir / sub_id / 'func' / f'{sub_id}_task-rsvp_run-{run}_bold.nii.gz'

            if input_file.exists():
                try:
                    orig_obl, new_obl = deoblique_nifti(input_file, output_file)
                    print(f"    Run {run}: {orig_obl:.2f}° → {new_obl:.2f}°")
                except Exception as e:
                    print(f"    Run {run}: ❌ Error: {e}")
            else:
                print(f"    Run {run}: ⚠️  Not found")

        # Deoblique fieldmaps
        print("  [3/4] Deobliquing fieldmaps...")
        fmap_files = list((raw_dir / sub_id / 'fmap').glob('*.nii.gz'))
        fmap_count = 0
        for fmap_file in fmap_files:
            output_file = out_dir / sub_id / 'fmap' / fmap_file.name
            try:
                orig_obl, new_obl = deoblique_nifti(fmap_file, output_file)
                print(f"    {fmap_file.name}: {orig_obl:.2f}° → {new_obl:.2f}°")
                fmap_count += 1
            except Exception as e:
                print(f"    {fmap_file.name}: ❌ Error: {e}")
        print(f"    ✅ {fmap_count} fieldmap files processed")

        # Copy JSON/TSV files
        print("  [4/4] Copying JSON/TSV files...")
        for ext in ['*.json', '*.tsv']:
            for src_dir in ['func', 'fmap', 'anat']:
                src_path = raw_dir / sub_id / src_dir
                dst_path = out_dir / sub_id / src_dir
                if src_path.exists():
                    for metadata_file in src_path.glob(ext):
                        shutil.copy2(metadata_file, dst_path / metadata_file.name)
        print("    ✅ Metadata copied")

        print(f"  ✅ Sub-{sub} complete")
        print()

    # Copy dataset-level files
    print("=" * 40)
    print("Copying dataset-level files...")
    print("=" * 40)
    for dataset_file in raw_dir.glob('*.json'):
        shutil.copy2(dataset_file, out_dir / dataset_file.name)
    for dataset_file in raw_dir.glob('*.tsv'):
        shutil.copy2(dataset_file, out_dir / dataset_file.name)
    print("✅ Dataset files copied")
    print()

    # Summary
    print("=" * 40)
    print("Deoblique Summary")
    print("=" * 40)
    print(f"Output directory: {out_dir}")
    print()
    print("Verification:")
    for sub in subjects:
        sub_id = f'sub-{sub}'
        test_file = out_dir / sub_id / 'func' / f'{sub_id}_task-rsvp_run-1_bold.nii.gz'
        if test_file.exists():
            img = nib.load(test_file)
            obliq = get_obliquity(img.affine)
            print(f"  Sub-{sub}: {obliq:.2f}°")
        else:
            print(f"  Sub-{sub}: ❌ Not found")

    print()
    print("=" * 80)
    print("Deoblique Processing Complete")
    print("=" * 80)
    print()
    print("Next step:")
    print("  sbatch run_fmriprep_deoblique.sbatch")

if __name__ == '__main__':
    main()
