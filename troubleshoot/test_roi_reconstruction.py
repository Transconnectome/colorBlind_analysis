#!/usr/bin/env python
"""
Quick test: Compare reconstruction performance across different ROIs
Tests: V1, V2, V3, hV4, V1-V4 combined, and brain mask
"""

import os
import sys
import numpy as np
from pathlib import Path
import joblib
import pandas as pd

# Handle different nilearn versions
try:
    from nilearn.maskers import NiftiMasker
except ImportError:
    from nilearn.input_data import NiftiMasker

from sklearn.linear_model import Ridge

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Configuration
SUB = 'sub-01'
TASK = 'rsvp'
SPACE = 'MNI152NLin2009cAsym'
OUTDIR = './hrf_test_outputs'

# ROI paths (check these exist)
ROI_PATHS = {
    'V1': f'derivatives/{SUB}/roi/{SUB}_acq-mprage_space-{SPACE}_res-2_desc-V1_mask.nii.gz',
    'V2': f'derivatives/{SUB}/roi/{SUB}_acq-mprage_space-{SPACE}_res-2_desc-V2_mask.nii.gz',
    'V3': f'derivatives/{SUB}/roi/{SUB}_acq-mprage_space-{SPACE}_res-2_desc-V3_mask.nii.gz',
    'hV4': f'derivatives/{SUB}/roi/{SUB}_acq-mprage_space-{SPACE}_res-2_desc-hV4_mask.nii.gz',
    'brain': f'output/pilot/{SUB}/anat/{SUB}_acq-mprage_space-{SPACE}_res-2_desc-brain_mask.nii.gz',
}

# Lab hue values (corrected for pilot)
LABEL2HUE_DEG = {
    'color_1': 182.142053052572436,
    'color_2': 287.979026187069735,
    'color_3': 305.226546308759566,
    'color_4': 330.204721787408289,
    'color_5': 35.269500805260478,
    'color_6': 73.365061454288877,
    'color_7': 125.585145639335096,
    'color_8': 143.909094545652778,
}

print("=" * 80)
print("ROI-BASED RECONSTRUCTION TEST")
print("=" * 80)
print()

# Check which ROIs exist
print("Checking ROI availability...")
available_rois = {}
for roi_name, roi_path in ROI_PATHS.items():
    exists = os.path.exists(roi_path)
    status = "✅" if exists else "❌"
    print(f"  {status} {roi_name}: {roi_path}")
    if exists:
        available_rois[roi_name] = roi_path

if not available_rois:
    print("\n❌ ERROR: No ROI masks found!")
    print("Please check that ROI masks have been created using roi_build.py")
    sys.exit(1)

print()
print(f"Found {len(available_rois)} available ROIs")
print()

# Load cached reconstruction results from brain mask for comparison
brain_cache = os.path.join(OUTDIR, 'cache_brain', 'reconstruction_results.joblib')
if os.path.exists(brain_cache):
    print("Loading brain mask results for comparison...")
    brain_results = joblib.load(brain_cache)

    # Handle different result structures
    if 'all_hits' in brain_results and 'all_ps' in brain_results:
        # This is the actual structure from naive_analysis.py
        mean_hit = np.mean(brain_results['all_hits'])
        mean_p = np.mean(brain_results['all_ps'])
    elif 'mean_hit_rate' in brain_results:
        mean_hit = brain_results['mean_hit_rate']
        mean_p = brain_results['mean_p_value']
    elif 'per_run_results' in brain_results:
        per_run = brain_results['per_run_results']
        mean_hit = np.mean([r['hit_rate'] for r in per_run])
        mean_p = np.mean([r['p_value'] for r in per_run])
    else:
        # Try to compute from raw data
        print(f"  Keys in brain_results: {list(brain_results.keys())}")
        mean_hit = np.nan
        mean_p = np.nan

    if not np.isnan(mean_hit):
        print(f"  Brain mask: {mean_hit:.3f} hit rate, p={mean_p:.3f}")
    print()

# Test each ROI
print("=" * 80)
print("TESTING RECONSTRUCTION WITH DIFFERENT ROIs")
print("=" * 80)
print()

results_summary = []

for roi_name in ['V1', 'V2', 'V3', 'hV4', 'brain']:
    if roi_name not in available_rois:
        print(f"⚠️  Skipping {roi_name} (not available)")
        continue

    print(f"\n{'='*80}")
    print(f"Testing: {roi_name}")
    print(f"{'='*80}")

    roi_path = available_rois[roi_name]
    cache_dir = os.path.join(OUTDIR, f'cache_{roi_name}')

    # Check if results already exist
    cache_file = os.path.join(cache_dir, 'reconstruction_results.joblib')
    if os.path.exists(cache_file):
        print(f"✅ Loading cached results from {cache_file}")
        roi_results = joblib.load(cache_file)

        # Try to extract results from different possible structures
        if 'all_hits' in roi_results and 'all_ps' in roi_results:
            # This is the actual structure from naive_analysis.py
            all_hits = roi_results['all_hits']
            all_ps = roi_results['all_ps']
            all_thrs = roi_results.get('all_thrs', [])

            mean_hit = np.mean(all_hits)
            mean_p = np.mean(all_ps)

            # Build per_run list for display
            per_run = [
                {'hit_rate': h, 'p_value': p, 'threshold': t}
                for h, p, t in zip(all_hits, all_ps, all_thrs or [np.nan]*len(all_hits))
            ]
        elif 'mean_hit_rate' in roi_results:
            mean_hit = roi_results['mean_hit_rate']
            mean_p = roi_results['mean_p_value']
            per_run = roi_results.get('per_run_results', [])
        elif 'per_run_results' in roi_results:
            per_run = roi_results['per_run_results']
            mean_hit = np.mean([r['hit_rate'] for r in per_run])
            mean_p = np.mean([r['p_value'] for r in per_run])
        else:
            # Debug: show what's in the file
            print(f"   ⚠️  Unexpected structure. Keys: {list(roi_results.keys())}")
            mean_hit = np.nan
            mean_p = np.nan
            per_run = []

        print(f"\n📊 RESULTS for {roi_name}:")
        print(f"   Mean hit rate: {mean_hit:.3f}")
        print(f"   Mean p-value:  {mean_p:.3f}")
        print(f"   Significant:   {'✅ YES' if mean_p < 0.05 else '❌ NO'}")

        if per_run:
            print(f"\n   Per-run breakdown:")
            for i, run_res in enumerate(per_run, 1):
                hit = run_res.get('hit_rate', np.nan)
                p = run_res.get('p_value', np.nan)
                print(f"     Run {i}: hit={hit:.3f}, p={p:.3f}")

        results_summary.append({
            'ROI': roi_name,
            'Hit Rate': mean_hit,
            'p-value': mean_p,
            'Significant': 'Yes' if mean_p < 0.05 else 'No',
            'Status': '✅' if mean_p < 0.05 else '❌'
        })
    else:
        print(f"⚠️  No cached results found at {cache_file}")
        print(f"   Run naive_analysis.py with {roi_name} mask to generate results")
        results_summary.append({
            'ROI': roi_name,
            'Hit Rate': np.nan,
            'p-value': np.nan,
            'Significant': 'N/A',
            'Status': '⏳'
        })

# Summary table
print("\n" + "=" * 80)
print("SUMMARY: Reconstruction Performance by ROI")
print("=" * 80)
print()

df_summary = pd.DataFrame(results_summary)
print(df_summary.to_string(index=False))
print()

# Recommendations
print("=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)
print()

if any(df_summary['Significant'] == 'Yes'):
    best_roi = df_summary.loc[df_summary['Hit Rate'].idxmax(), 'ROI']
    best_hit = df_summary.loc[df_summary['Hit Rate'].idxmax(), 'Hit Rate']
    best_p = df_summary.loc[df_summary['Hit Rate'].idxmax(), 'p-value']
    print(f"✅ SUCCESS! Best ROI: {best_roi}")
    print(f"   Hit rate: {best_hit:.3f}, p-value: {best_p:.3f}")
    print()
    print("   Use this ROI for further analysis and CVD filter development.")
else:
    print("❌ No ROI achieved significant reconstruction (p<0.05)")
    print()
    print("Next steps:")
    print("  1. Try FIR model (bh_anal.py) instead of canonical HRF")
    print("  2. Optimize regularization parameter (try lambda=0.1, 1.0, 10.0)")
    print("  3. Combine V1+V2+V3+hV4 into single mask")
    print("  4. Consider data quality issues (motion, attention)")
    print("  5. Switch to main experiment data (better color spacing)")

print()
print("=" * 80)
print("To run analysis for a specific ROI:")
print("  1. Edit naive_analysis.py line ~950 to specify ROI path")
print("  2. Run: python naive_analysis.py")
print("  3. Re-run this script to see updated results")
print("=" * 80)
