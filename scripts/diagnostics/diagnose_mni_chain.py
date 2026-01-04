#!/usr/bin/env python3
"""
MNI Registration Chain Diagnosis Script

Systematically checks MNI registration chain to identify where misalignment occurs:
1. T1w → MNI transformation
2. BOLD → MNI transformation
3. Grid/affine consistency between T1w(MNI) and BOLD(MNI)

Usage:
    python diagnose_mni_chain.py --subject 01 --fmriprep-dir <path> --run 1
"""

import argparse
import nibabel as nib
import numpy as np
from pathlib import Path
import sys

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def load_and_validate(filepath):
    """Load NIfTI file and return image object, or None if failed"""
    try:
        img = nib.load(filepath)
        print(f"✅ Loaded: {filepath.name}")
        return img
    except Exception as e:
        print(f"❌ Failed to load {filepath.name}: {e}")
        return None

def print_image_info(img, label):
    """Print comprehensive image metadata"""
    print(f"\n📋 {label}:")
    print(f"   Shape:      {img.shape}")
    print(f"   Data type:  {img.get_data_dtype()}")
    print(f"   Affine:\n{img.affine}")

    # Voxel size
    voxel_sizes = nib.affines.voxel_sizes(img.affine)
    print(f"   Voxel size: {voxel_sizes} mm")

    # Bounding box in MNI space
    bbox = nib.affines.apply_affine(img.affine,
                                     np.array([[0, 0, 0],
                                              [img.shape[0]-1, img.shape[1]-1, img.shape[2]-1]]))
    print(f"   MNI bbox:   {bbox[0]} → {bbox[1]}")

def compare_spaces(img1, img2, label1, label2):
    """Compare spatial properties of two images"""
    print(f"\n🔍 Comparing {label1} vs {label2}:")

    # Affine comparison
    affine_match = np.allclose(img1.affine, img2.affine, atol=1e-3)
    print(f"   Affine match:      {'✅ YES' if affine_match else '❌ NO'}")

    if not affine_match:
        diff = np.abs(img1.affine - img2.affine)
        print(f"   Max affine diff:   {diff.max():.6f}")
        print(f"   Mean affine diff:  {diff.mean():.6f}")

    # Shape comparison
    shape_match = img1.shape[:3] == img2.shape[:3]
    print(f"   Shape match:       {'✅ YES' if shape_match else '❌ NO'}")
    if not shape_match:
        print(f"      {label1}: {img1.shape[:3]}")
        print(f"      {label2}: {img2.shape[:3]}")

    # Voxel size comparison
    vox1 = nib.affines.voxel_sizes(img1.affine)
    vox2 = nib.affines.voxel_sizes(img2.affine)
    vox_match = np.allclose(vox1, vox2, atol=0.01)
    print(f"   Voxel size match:  {'✅ YES' if vox_match else '❌ NO'}")
    if not vox_match:
        print(f"      {label1}: {vox1}")
        print(f"      {label2}: {vox2}")

    return affine_match and shape_match

def compute_overlap_metrics(img1, img2, label1, label2):
    """Compute spatial overlap metrics (requires same space)"""
    print(f"\n📊 Overlap metrics ({label1} vs {label2}):")

    try:
        # Get data
        data1 = img1.get_fdata()
        data2 = img2.get_fdata()

        # Handle different shapes by resampling or cropping
        if data1.shape != data2.shape:
            print("   ⚠️  Different shapes - skipping overlap calculation")
            return

        # Mask non-zero voxels
        mask1 = data1 > 0
        mask2 = data2 > 0

        # Dice coefficient
        intersection = np.sum(mask1 & mask2)
        dice = 2 * intersection / (np.sum(mask1) + np.sum(mask2))
        print(f"   Dice coefficient:  {dice:.4f}")

        # Correlation in overlapping region
        overlap_mask = mask1 & mask2
        if np.sum(overlap_mask) > 100:
            corr = np.corrcoef(data1[overlap_mask], data2[overlap_mask])[0, 1]
            print(f"   Correlation:       {corr:.4f}")

    except Exception as e:
        print(f"   ❌ Failed: {e}")

def generate_fsleyes_commands(t1w_mni, bold_mni, template, output_file):
    """Generate fsleyes commands for visual inspection"""
    commands = []

    print_section("Visual Inspection Commands")

    # Step A: T1w(MNI) vs Template
    cmd_a = f"fsleyes {template} {t1w_mni} -cm red -a 50"
    commands.append(("Step A: T1w(MNI) vs Template", cmd_a))

    # Step B: BOLD(MNI) vs Template
    cmd_b = f"fsleyes {template} {bold_mni} -cm blue -a 50"
    commands.append(("Step B: BOLD(MNI) vs Template", cmd_b))

    # Step C: BOLD(MNI) vs T1w(MNI)
    cmd_c = f"fsleyes {t1w_mni} {bold_mni} -cm red -a 50"
    commands.append(("Step C: BOLD(MNI) vs T1w(MNI)", cmd_c))

    # Print commands
    for label, cmd in commands:
        print(f"\n{label}:")
        print(f"  {cmd}")

    # Save to file
    with open(output_file, 'w') as f:
        f.write("# MNI Chain Visual Inspection Commands\n\n")
        for label, cmd in commands:
            f.write(f"# {label}\n")
            f.write(f"{cmd}\n\n")

    print(f"\n💾 Commands saved to: {output_file}")

def diagnose_chain(t1w_img, bold_img, template_img):
    """Perform systematic diagnosis and return interpretation"""
    print_section("Chain Diagnosis")

    # Step A: T1w(MNI) ↔ Template
    t1_ok = compare_spaces(t1w_img, template_img, "T1w(MNI)", "Template")

    # Step B: BOLD(MNI) ↔ Template
    bold_ok = compare_spaces(bold_img, template_img, "BOLD(MNI)", "Template")

    # Step C: BOLD(MNI) ↔ T1w(MNI)
    mutual_ok = compare_spaces(bold_img, t1w_img, "BOLD(MNI)", "T1w(MNI)")

    # Interpret results
    print_section("Diagnosis Interpretation")

    if not t1_ok:
        print("❌ T1w → MNI transformation problem")
        print("   → Check fMRIPrep T1w normalization logs")
        print("   → Verify template used matches expected")

    elif not bold_ok and t1_ok:
        print("❌ BOLD → MNI transformation problem")
        print("   → Check BOLD → T1w registration")
        print("   → Check susceptibility distortion correction (SDC)")

    elif t1_ok and bold_ok and not mutual_ok:
        print("❌ Grid/affine/resolution mismatch")
        print("   → Images in correct MNI space but different grids")
        print("   → Check fMRIPrep resolution flags")

    elif t1_ok and bold_ok and mutual_ok:
        print("✅ MNI chain appears normal")
        print("   → ROI alignment issue likely in analysis code")
        print("   → Re-check ROI atlas registration")

    else:
        print("⚠️  Mixed results - needs detailed investigation")

    return t1_ok, bold_ok, mutual_ok

def main():
    parser = argparse.ArgumentParser(description='Diagnose MNI registration chain')
    parser.add_argument('--subject', required=True, help='Subject ID (e.g., 01)')
    parser.add_argument('--fmriprep-dir', required=True, type=Path,
                       help='fMRIPrep output directory')
    parser.add_argument('--run', type=int, default=1, help='Run number (default: 1)')
    parser.add_argument('--template', type=Path,
                       help='MNI template path (if not specified, uses fMRIPrep default)')
    parser.add_argument('--output', type=Path, default=Path('mni_chain_diagnosis.txt'),
                       help='Output file for fsleyes commands')

    args = parser.parse_args()

    # Construct file paths
    sub_id = args.subject.zfill(2)
    fmriprep_dir = args.fmriprep_dir / f'sub-{sub_id}'

    # Find T1w MNI space
    t1w_pattern = list((fmriprep_dir / 'anat').glob('*_space-MNI*_desc-preproc_T1w.nii.gz'))
    if not t1w_pattern:
        print(f"❌ No T1w MNI file found in {fmriprep_dir / 'anat'}")
        sys.exit(1)
    t1w_mni = t1w_pattern[0]

    # Find BOLD MNI space (boldref)
    bold_pattern = list((fmriprep_dir / 'func').glob(f'*_run-{args.run}_*space-MNI*boldref.nii.gz'))
    if not bold_pattern:
        print(f"❌ No BOLD MNI boldref file found for run-{args.run}")
        sys.exit(1)
    bold_mni = bold_pattern[0]

    # Get template
    if args.template:
        template = args.template
    else:
        # Try to find template from fMRIPrep
        # IMPORTANT: Use same template as fMRIPrep (MNI152NLin2009cAsym)
        template_dirs = [
            # Priority 1: TemplateFlow (matches fMRIPrep)
            Path.home() / '.cache/templateflow/tpl-MNI152NLin2009cAsym/tpl-MNI152NLin2009cAsym_res-02_T1w.nii.gz',
            # Priority 2: FSL standard (different bounding box!)
            Path('/usr/local/fsl/data/standard/MNI152_T1_2mm.nii.gz'),
        ]
        template = None
        for t in template_dirs:
            if t.exists():
                template = t
                print(f"   Using template: {t}")
                break

        if template is None:
            print("⚠️  No template found. Please specify --template")
            print("   Common locations:")
            for t in template_dirs:
                print(f"     {t}")
            print("\n   To download TemplateFlow template:")
            print("   python -c \"from templateflow import api; api.get('MNI152NLin2009cAsym', resolution=2, suffix='T1w')\"")
            sys.exit(1)

    print_section("MNI Registration Chain Diagnosis")
    print(f"Subject:  sub-{sub_id}")
    print(f"Run:      {args.run}")
    print(f"T1w:      {t1w_mni.name}")
    print(f"BOLD:     {bold_mni.name}")
    print(f"Template: {template.name}")

    # Load images
    print_section("Loading Images")
    t1w_img = load_and_validate(t1w_mni)
    bold_img = load_and_validate(bold_mni)
    template_img = load_and_validate(template)

    if None in [t1w_img, bold_img, template_img]:
        print("\n❌ Failed to load required images")
        sys.exit(1)

    # Print metadata
    print_section("Image Metadata")
    print_image_info(template_img, "MNI Template")
    print_image_info(t1w_img, "T1w(MNI)")
    print_image_info(bold_img, "BOLD(MNI)")

    # Diagnose chain
    t1_ok, bold_ok, mutual_ok = diagnose_chain(t1w_img, bold_img, template_img)

    # Generate visualization commands
    generate_fsleyes_commands(t1w_mni, bold_mni, template, args.output)

    # Final summary
    print_section("Summary")
    print(f"T1w → MNI:        {'✅ OK' if t1_ok else '❌ PROBLEM'}")
    print(f"BOLD → MNI:       {'✅ OK' if bold_ok else '❌ PROBLEM'}")
    print(f"Grid consistency: {'✅ OK' if mutual_ok else '❌ PROBLEM'}")
    print(f"\n📝 Next: Run fsleyes commands from {args.output} for visual confirmation")

if __name__ == '__main__':
    main()
