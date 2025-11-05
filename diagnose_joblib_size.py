#!/usr/bin/env python3
"""
Diagnose why firstlevel.joblib file is 8GB
"""

import joblib
import sys
import numpy as np

def analyze_joblib(filepath):
    print(f"\n{'='*60}")
    print(f"Analyzing: {filepath}")
    print(f"{'='*60}\n")

    # Load the model
    first_level = joblib.load(filepath)

    # Check what's stored
    print("Attributes in first_level object:")
    for attr in dir(first_level):
        if not attr.startswith('_'):
            print(f"  {attr}")

    print(f"\n{'='*60}")
    print("Key data arrays:")
    print(f"{'='*60}\n")

    # Check predicted images
    if hasattr(first_level, 'predicted') and first_level.predicted is not None:
        print(f"predicted: {len(first_level.predicted)} runs")
        total_size = 0
        for i, pred in enumerate(first_level.predicted):
            data = pred.get_fdata()
            size_mb = data.nbytes / (1024**2)
            total_size += size_mb
            print(f"  Run {i+1}: shape={data.shape}, size={size_mb:.1f} MB")
        print(f"  Total predicted size: {total_size:.1f} MB ({total_size/1024:.2f} GB)")
    else:
        print("predicted: None (memory minimized)")

    print()

    # Check residuals
    if hasattr(first_level, 'residuals') and first_level.residuals is not None:
        print(f"residuals: {len(first_level.residuals)} runs")
        total_size = 0
        for i, resid in enumerate(first_level.residuals):
            data = resid.get_fdata()
            size_mb = data.nbytes / (1024**2)
            total_size += size_mb
            print(f"  Run {i+1}: shape={data.shape}, size={size_mb:.1f} MB")
        print(f"  Total residuals size: {total_size:.1f} MB ({total_size/1024:.2f} GB)")
    else:
        print("residuals: None (memory minimized)")

    print()

    # Check design matrices
    if hasattr(first_level, 'design_matrices_') and first_level.design_matrices_ is not None:
        print(f"design_matrices: {len(first_level.design_matrices_)} runs")
        total_size = 0
        for i, dm in enumerate(first_level.design_matrices_):
            size_mb = dm.values.nbytes / (1024**2)
            total_size += size_mb
            print(f"  Run {i+1}: shape={dm.shape}, size={size_mb:.1f} MB")
        print(f"  Total design matrices size: {total_size:.1f} MB")

    print()

    # Check labels
    if hasattr(first_level, 'labels_'):
        print(f"labels: {first_level.labels_}")

    print(f"\n{'='*60}")
    print("minimize_memory setting:")
    print(f"{'='*60}\n")

    if hasattr(first_level, 'minimize_memory'):
        print(f"minimize_memory = {first_level.minimize_memory}")
    else:
        print("minimize_memory attribute not found")

    print()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python diagnose_joblib_size.py <path_to_joblib_file>")
        print("\nExample:")
        print("  python diagnose_joblib_size.py hrf_test_outputs/sub-01_rsvp_firstlevel.joblib")
        sys.exit(1)

    filepath = sys.argv[1]
    analyze_joblib(filepath)

    print(f"\n{'='*60}")
    print("SOLUTION to reduce file size:")
    print(f"{'='*60}\n")
    print("Change minimize_memory=False to minimize_memory=True")
    print("This will:")
    print("  - Not store predicted/residuals (saves ~8GB)")
    print("  - Still keep design matrices and fitted parameters")
    print("  - You can still compute contrasts")
    print("  - You just can't access .predicted or .residuals after")
    print("\nIn your code:")
    print("  first_level = FirstLevelModel(")
    print("      t_r=TR0, hrf_model=HRF_MODEL,")
    print("      drift_model=DRIFT_MODEL, high_pass=HIGH_PASS,")
    print("      noise_model=NOISE_MODEL, minimize_memory=True  # <- Change this")
    print("  ).fit(fmri_imgs, design_matrices=design_mats)")
    print()
