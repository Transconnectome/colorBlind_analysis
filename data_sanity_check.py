#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_sanity_check.py
--------------------
Comprehensive data quality checks before running analysis pipeline

This script checks:
1. Functional data properties (mean, std, range)
2. Event file structure and timing
3. ROI-functional alignment
4. Confound file structure
5. Basic signal detection in visual cortex

Run this FIRST before any analysis!
"""

import os
import numpy as np
import pandas as pd
import nibabel as nib
from nilearn import image, plotting
import matplotlib.pyplot as plt
from config import cfg


def check_functional_data(run=1):
    """Check functional data properties"""
    print("\n" + "="*60)
    print("1. FUNCTIONAL DATA PROPERTIES")
    print("="*60)

    func_path = cfg.get_func_img_path(run)
    print(f"\nLoading: {os.path.basename(func_path)}")

    if not os.path.exists(func_path):
        print(f"❌ ERROR: File not found!")
        return False

    # Load data
    func_img = nib.load(func_path)
    data = func_img.get_fdata()

    # Basic properties
    print(f"\nShape: {data.shape}")
    print(f"Voxel size: {func_img.header.get_zooms()[:3]} mm")
    print(f"TR: {func_img.header.get_zooms()[3]:.3f} s")

    # Statistical properties
    print(f"\nData statistics:")
    print(f"  Mean:   {data.mean():.4f}")
    print(f"  Std:    {data.std():.4f}")
    print(f"  Min:    {data.min():.4f}")
    print(f"  Max:    {data.max():.4f}")
    print(f"  Median: {np.median(data):.4f}")

    # Check if data is centered
    if abs(data.mean()) < 1.0:
        print(f"\n⚠️  WARNING: Data appears to be CENTERED (mean ≈ 0)")
        print(f"   This is typical for fMRIPrep desc-preproc output")
        print(f"   DO NOT apply additional centering in GLM!")
    else:
        print(f"\n✅ Data is NOT centered (mean = {data.mean():.2f})")

    # Check for zero/nan values
    n_zero = np.sum(data == 0)
    n_nan = np.sum(np.isnan(data))
    total_voxels = np.prod(data.shape)

    print(f"\nData quality:")
    print(f"  Zero values: {n_zero} ({100*n_zero/total_voxels:.2f}%)")
    print(f"  NaN values:  {n_nan} ({100*n_nan/total_voxels:.2f}%)")

    # Check temporal variance
    temporal_std = data.std(axis=-1)
    print(f"\nTemporal variance:")
    print(f"  Mean std across time: {temporal_std.mean():.4f}")
    print(f"  Active voxels (std > 0): {np.sum(temporal_std > 0)} / {np.prod(data.shape[:3])}")

    # Signal-to-noise estimate (rough)
    temporal_mean = data.mean(axis=-1)
    snr = temporal_mean / (temporal_std + 1e-10)
    valid_voxels = temporal_std > 0

    print(f"\nTemporal SNR (rough estimate):")
    print(f"  Mean tSNR: {snr[valid_voxels].mean():.2f}")
    print(f"  Median tSNR: {np.median(snr[valid_voxels]):.2f}")

    if snr[valid_voxels].mean() < 10:
        print(f"  ⚠️  WARNING: Low tSNR (< 10)")
    elif snr[valid_voxels].mean() > 50:
        print(f"  ✅ Good tSNR (> 50)")

    return True


def check_event_files(run=1):
    """Check event file structure"""
    print("\n" + "="*60)
    print("2. EVENT FILE STRUCTURE")
    print("="*60)

    event_path = cfg.get_event_file_path(run)
    print(f"\nLoading: {os.path.basename(event_path)}")

    if not os.path.exists(event_path):
        print(f"❌ ERROR: File not found!")
        return False

    # Load events
    events = pd.read_csv(event_path, sep='\t')
    print(f"\nShape: {events.shape}")
    print(f"Columns: {list(events.columns)}")

    # Check required columns
    required = ['onset', 'duration', 'trial_type']
    for col in required:
        if col not in events.columns:
            print(f"❌ ERROR: Missing required column '{col}'!")
            return False
        else:
            print(f"✅ Found column: {col}")

    # Check trial types
    print(f"\nTrial types:")
    print(events['trial_type'].value_counts())

    # Check for color conditions
    color_trials = events[events['trial_type'].str.contains('color', case=False, na=False)]
    print(f"\nColor trials: {len(color_trials)}")

    if len(color_trials) == 0:
        print(f"⚠️  WARNING: No trials with 'color' in trial_type")
        print(f"   Expected format: 'color_1', 'color_2', ..., 'color_8'")

        # Check what trial types exist
        unique_types = events['trial_type'].unique()
        print(f"   Available trial types: {unique_types}")

        # Try to infer color trials
        for tt in unique_types:
            if tt.lower() != 'blank' and tt.lower() != 'fixation':
                print(f"   Possible color trial: {tt}")

    # Check timing
    print(f"\nTiming information:")
    print(f"  First onset: {events['onset'].min():.2f} s")
    print(f"  Last onset:  {events['onset'].max():.2f} s")
    print(f"  Duration range: {events['duration'].min():.2f} - {events['duration'].max():.2f} s")
    print(f"  Mean ISI: {np.diff(events['onset']).mean():.2f} s")

    return True


def check_roi_alignment(roi_name='V1'):
    """Check ROI-functional alignment"""
    print("\n" + "="*60)
    print("3. ROI-FUNCTIONAL ALIGNMENT")
    print("="*60)

    # Load functional
    func_path = cfg.get_func_img_path(1)
    if not os.path.exists(func_path):
        print(f"❌ Functional image not found")
        return False

    func_img = nib.load(func_path)
    func_data = func_img.get_fdata()
    print(f"\nFunctional shape: {func_img.shape[:3]}")
    print(f"Functional affine:\n{func_img.affine}")

    # Load ROI
    roi_path = os.path.join(cfg.roi_dir, f'sub-{cfg.SUB_ID}_{roi_name}_mask.nii.gz')
    if not os.path.exists(roi_path):
        print(f"\n⚠️  ROI not found: {roi_name}")
        print(f"   Expected: {roi_path}")
        return False

    roi_img = nib.load(roi_path)
    roi_data = roi_img.get_fdata().astype(bool)
    print(f"\n{roi_name} ROI shape: {roi_img.shape}")
    print(f"{roi_name} ROI affine:\n{roi_img.affine}")

    # Check shape match
    if func_img.shape[:3] != roi_img.shape:
        print(f"\n❌ ERROR: Shape mismatch!")
        print(f"   Functional: {func_img.shape[:3]}")
        print(f"   ROI: {roi_img.shape}")
        return False
    else:
        print(f"\n✅ Shapes match")

    # Check affine match
    if not np.allclose(func_img.affine, roi_img.affine):
        print(f"\n⚠️  WARNING: Affines don't match exactly")
        print(f"   Max difference: {np.abs(func_img.affine - roi_img.affine).max():.6f}")
    else:
        print(f"✅ Affines match")

    # Check overlap
    func_mean = func_data.mean(axis=-1)
    func_active = func_mean != 0

    overlap = np.sum(roi_data & func_active)
    roi_size = np.sum(roi_data)

    print(f"\n{roi_name} ROI:")
    print(f"  Total voxels: {roi_size}")
    print(f"  Overlapping with active functional: {overlap} ({100*overlap/roi_size:.1f}%)")

    if overlap / roi_size < 0.5:
        print(f"  ❌ ERROR: Less than 50% overlap! ROI alignment problem.")
    elif overlap / roi_size < 0.8:
        print(f"  ⚠️  WARNING: Less than 80% overlap")
    else:
        print(f"  ✅ Good overlap (>80%)")

    # Check coverage of visual cortex
    print(f"\nVisual cortex coverage:")
    print(f"  Active voxels in functional: {np.sum(func_active)}")
    print(f"  Active voxels in {roi_name}: {overlap}")

    return True


def check_confounds(run=1):
    """Check confound file structure"""
    print("\n" + "="*60)
    print("4. CONFOUND FILE STRUCTURE")
    print("="*60)

    conf_path = cfg.get_confound_file_path(run)
    print(f"\nLoading: {os.path.basename(conf_path)}")

    if not os.path.exists(conf_path):
        print(f"❌ ERROR: File not found!")
        return False

    # Load confounds
    confounds = pd.read_csv(conf_path, sep='\t')
    print(f"\nShape: {confounds.shape}")
    print(f"Number of columns: {len(confounds.columns)}")

    # Check for motion parameters
    motion_cols = [col for col in confounds.columns if 'trans' in col or 'rot' in col]
    print(f"\nMotion parameters found: {len(motion_cols)}")
    for col in motion_cols[:6]:  # Show first 6
        print(f"  - {col}")

    # Check for CompCor
    compcor_cols = [col for col in confounds.columns if 'comp_cor' in col.lower()]
    print(f"\nCompCor components found: {len(compcor_cols)}")

    if len(compcor_cols) == 0:
        print(f"  ⚠️  WARNING: No CompCor components found")
        print(f"     May need to use nilearn.load_confounds_strategy")

    # Check framewise displacement
    if 'framewise_displacement' in confounds.columns:
        fd = confounds['framewise_displacement']
        print(f"\nFramewise displacement:")
        print(f"  Mean: {fd.mean():.4f} mm")
        print(f"  Max: {fd.max():.4f} mm")
        print(f"  Volumes with FD > 0.5mm: {np.sum(fd > 0.5)}")

        if fd.mean() > 0.3:
            print(f"  ⚠️  WARNING: High mean motion (> 0.3mm)")
        elif fd.mean() > 0.5:
            print(f"  ❌ ERROR: Excessive motion (> 0.5mm)")
        else:
            print(f"  ✅ Good motion quality")

    return True


def plot_functional_quality(run=1, output_dir=None):
    """Create quality control plots"""
    print("\n" + "="*60)
    print("5. QUALITY CONTROL PLOTS")
    print("="*60)

    if output_dir is None:
        output_dir = cfg.analysis_dir
    os.makedirs(output_dir, exist_ok=True)

    func_path = cfg.get_func_img_path(run)
    func_img = nib.load(func_path)

    # Plot mean image
    mean_img = image.mean_img(func_img)

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    # Mean image
    plotting.plot_anat(mean_img, axes=axes[0, 0], title='Mean Functional', display_mode='z', cut_coords=5)

    # Standard deviation map
    std_img = image.math_img('np.std(img, axis=-1)', img=func_img)
    plotting.plot_anat(std_img, axes=axes[0, 1], title='Std Dev (Temporal)', display_mode='z', cut_coords=5)

    # tSNR map (rough)
    data = func_img.get_fdata()
    tsnr = data.mean(axis=-1) / (data.std(axis=-1) + 1e-10)
    tsnr_img = nib.Nifti1Image(tsnr, func_img.affine, func_img.header)
    plotting.plot_anat(tsnr_img, axes=axes[1, 0], title='tSNR Map', display_mode='z', cut_coords=5, vmax=100)

    # Global signal timecourse
    global_signal = data[data != 0].mean(axis=0)
    axes[1, 1].plot(global_signal)
    axes[1, 1].set_xlabel('Volume')
    axes[1, 1].set_ylabel('Mean Signal')
    axes[1, 1].set_title('Global Signal Timecourse')
    axes[1, 1].grid(alpha=0.3)

    plt.tight_layout()

    plot_path = os.path.join(output_dir, f'data_quality_run{run}.png')
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"\n✅ Saved QC plot: {plot_path}")

    return True


def main():
    """Run all sanity checks"""
    print("\n" + "="*60)
    print("DATA SANITY CHECK")
    print("="*60)
    print(f"Subject: sub-{cfg.SUB_ID}")
    print(f"Project: {cfg.PROJECT_DIR}")

    results = {}

    # 1. Check functional data
    results['functional'] = check_functional_data(run=1)

    # 2. Check event files
    results['events'] = check_event_files(run=1)

    # 3. Check ROI alignment
    for roi in ['V1', 'V2', 'BrainMask']:
        results[f'roi_{roi}'] = check_roi_alignment(roi)

    # 4. Check confounds
    results['confounds'] = check_confounds(run=1)

    # 5. Generate QC plots
    try:
        results['plots'] = plot_functional_quality(run=1)
    except Exception as e:
        print(f"\n⚠️  WARNING: Could not generate plots: {e}")
        results['plots'] = False

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    passed = sum(results.values())
    total = len(results)

    print(f"\nChecks passed: {passed}/{total}")

    for check, status in results.items():
        symbol = "✅" if status else "❌"
        print(f"  {symbol} {check}")

    if passed == total:
        print(f"\n✅ ALL CHECKS PASSED - Proceed with caution")
    else:
        print(f"\n⚠️  SOME CHECKS FAILED - Fix issues before proceeding")

    print("\n" + "="*60)


if __name__ == '__main__':
    main()
