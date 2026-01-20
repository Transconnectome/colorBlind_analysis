#!/usr/bin/env python3
"""
Compute Dice coefficient for BOLD-T1w registration quality

Usage:
    python compute_dice.py --subject 01 --method method2_header_bbr --run 1

Computes Dice coefficient between:
    - BOLD brain mask (in MNI space)
    - T1w brain mask (in MNI space)
"""

import argparse
import nibabel as nib
import numpy as np
from pathlib import Path
import pandas as pd


def compute_dice(mask1, mask2):
    """
    Compute Dice coefficient

    Dice = 2 * |A ∩ B| / (|A| + |B|)
    """
    # Binarize masks
    mask1_bin = (mask1 > 0).astype(np.float32)
    mask2_bin = (mask2 > 0).astype(np.float32)

    # Intersection and union
    intersection = np.sum(mask1_bin * mask2_bin)
    sum_masks = np.sum(mask1_bin) + np.sum(mask2_bin)

    if sum_masks == 0:
        return 0.0

    dice = 2.0 * intersection / sum_masks

    return dice


def compute_overlap_stats(mask1, mask2):
    """
    Compute additional overlap statistics
    """
    mask1_bin = (mask1 > 0).astype(np.float32)
    mask2_bin = (mask2 > 0).astype(np.float32)

    intersection = np.sum(mask1_bin * mask2_bin)
    union = np.sum((mask1_bin + mask2_bin) > 0)

    # Jaccard index
    jaccard = intersection / union if union > 0 else 0.0

    # Overlap fractions
    overlap_in_mask1 = intersection / np.sum(mask1_bin) if np.sum(mask1_bin) > 0 else 0.0
    overlap_in_mask2 = intersection / np.sum(mask2_bin) if np.sum(mask2_bin) > 0 else 0.0

    return {
        'jaccard': jaccard,
        'overlap_frac_bold': overlap_in_mask1,
        'overlap_frac_t1w': overlap_in_mask2,
        'intersection_voxels': int(intersection),
        'bold_voxels': int(np.sum(mask1_bin)),
        't1w_voxels': int(np.sum(mask2_bin)),
    }


def main():
    parser = argparse.ArgumentParser(description='Compute Dice coefficient for registration QC')
    parser.add_argument('--subject', type=str, required=True,
                        help='Subject ID (e.g., 01, 03, 06)')
    parser.add_argument('--method', type=str, required=True,
                        help='Method name (e.g., method2_header_bbr)')
    parser.add_argument('--run', type=int, default=1,
                        help='Run number (default: 1)')
    parser.add_argument('--base_dir', type=str,
                        default='/scratch/connectome/haba6030/colorBlind/analysis/prep_trials',
                        help='Base directory for prep_trials')
    parser.add_argument('--output', type=str, default=None,
                        help='Output CSV file (default: results/dice_{method}.csv)')

    args = parser.parse_args()

    # Paths
    base_dir = Path(args.base_dir)
    method_dir = base_dir / args.method
    subject_dir = method_dir / f'sub-{args.subject}'
    func_dir = subject_dir / 'func'
    anat_dir = subject_dir / 'anat'

    # BOLD mask (in MNI space)
    bold_mask_file = func_dir / f'sub-{args.subject}_task-rsvp_run-{args.run}_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz'

    # T1w mask (in MNI space)
    # Note: T1w mask might be in anat/ or func/ depending on fMRIPrep version
    t1w_mask_candidates = [
        anat_dir / f'sub-{args.subject}_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz',
        anat_dir / f'sub-{args.subject}_acq-mprage_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz',  # fMRIPrep with acq
        func_dir / f'sub-{args.subject}_space-MNI152NLin2009cAsym_res-2_label-brain_mask.nii.gz',
        func_dir / f'sub-{args.subject}_task-rsvp_run-{args.run}_space-MNI152NLin2009cAsym_res-2_label-brain_mask.nii.gz',
    ]

    t1w_mask_file = None
    for candidate in t1w_mask_candidates:
        if candidate.exists():
            t1w_mask_file = candidate
            break

    # Check files exist
    if not bold_mask_file.exists():
        print(f"❌ ERROR: BOLD mask not found: {bold_mask_file}")
        return

    if t1w_mask_file is None or not t1w_mask_file.exists():
        print(f"❌ ERROR: T1w mask not found. Tried:")
        for candidate in t1w_mask_candidates:
            print(f"  {candidate}")
        return

    print(f"Loading masks...")
    print(f"  BOLD: {bold_mask_file.name}")
    print(f"  T1w:  {t1w_mask_file.name}")

    # Load masks
    bold_mask_img = nib.load(str(bold_mask_file))
    t1w_mask_img = nib.load(str(t1w_mask_file))

    bold_mask = bold_mask_img.get_fdata()
    t1w_mask = t1w_mask_img.get_fdata()

    # Check dimensions match
    if bold_mask.shape != t1w_mask.shape:
        print(f"❌ ERROR: Mask dimensions don't match:")
        print(f"  BOLD: {bold_mask.shape}")
        print(f"  T1w:  {t1w_mask.shape}")
        return

    # Compute Dice
    dice = compute_dice(bold_mask, t1w_mask)
    print(f"\n✅ Dice coefficient: {dice:.4f}")

    # Compute additional stats
    stats = compute_overlap_stats(bold_mask, t1w_mask)
    print(f"\nAdditional statistics:")
    print(f"  Jaccard index:         {stats['jaccard']:.4f}")
    print(f"  Overlap in BOLD mask:  {stats['overlap_frac_bold']:.2%}")
    print(f"  Overlap in T1w mask:   {stats['overlap_frac_t1w']:.2%}")
    print(f"  Intersection voxels:   {stats['intersection_voxels']:,}")
    print(f"  BOLD mask voxels:      {stats['bold_voxels']:,}")
    print(f"  T1w mask voxels:       {stats['t1w_voxels']:,}")

    # Quality assessment
    print(f"\nQuality assessment:")
    if dice >= 0.90:
        quality = "Excellent ✅"
    elif dice >= 0.80:
        quality = "Good ✓"
    elif dice >= 0.70:
        quality = "Fair ⚠️"
    else:
        quality = "Poor ❌"
    print(f"  {quality} (Dice: {dice:.4f})")

    # Save results
    results_dir = base_dir / 'results'
    results_dir.mkdir(exist_ok=True)

    if args.output is None:
        output_file = results_dir / f'dice_{args.method}.csv'
    else:
        output_file = Path(args.output)

    # Create or append to CSV
    result_row = {
        'subject': args.subject,
        'method': args.method,
        'run': args.run,
        'dice': dice,
        **stats
    }

    df_new = pd.DataFrame([result_row])

    if output_file.exists():
        df_existing = pd.read_csv(output_file)
        df = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_csv(output_file, index=False)
    print(f"\n✅ Results saved to: {output_file}")


if __name__ == '__main__':
    main()
