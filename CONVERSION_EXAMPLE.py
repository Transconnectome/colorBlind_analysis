#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CONVERSION_EXAMPLE.py
---------------------
Example showing how to convert existing analysis scripts to use
the new reorganized output structure.

This shows the key changes needed to convert from:
  OLD: logs/TIMESTAMP/sub-{ID}/{ROI}_universal_hrf/
  NEW: logs/TIMESTAMP/{METHOD}_{ROI}/sub-{ID}_*

Date: 2025-11-17
"""

import sys
import os
import argparse
import pickle
import numpy as np
import pandas as pd
import nibabel as nib
from pathlib import Path
import matplotlib.pyplot as plt
from datetime import datetime

# ============================================================================
# IMPORT OUTPUT MANAGER (NEW)
# ============================================================================
from output_manager import OutputManager

# ============================================================================
# Parse Arguments
# ============================================================================

def parse_args():
    parser = argparse.ArgumentParser(description='FIR-based color reconstruction')
    parser.add_argument('--subject', type=str, default='01',
                        help='Subject ID (e.g., 01, 02, 03, 04)')
    parser.add_argument('--roi', type=str, default='V2',
                        help='ROI name (e.g., V1, V2, V3, V4, hV4, VO1)')
    parser.add_argument('--method', type=str, default='zScore',
                        help='Analysis method (e.g., zScore, voxelSelect, rawBeta)')
    parser.add_argument('--timestamp', type=str, default=None,
                        help='Timestamp for output directory (default: auto-generate)')
    parser.add_argument('--use-pca', action='store_true',
                        help='Use PCA dimensionality reduction')
    parser.add_argument('--n-components', type=int, default=20,
                        help='Number of PCA components (only if --use-pca)')
    return parser.parse_args()

args = parse_args()

SUBJECT_ID = args.subject
ROI_NAME = args.roi
METHOD_NAME = args.method
USE_PCA = args.use_pca
N_PCA_COMPONENTS = args.n_components

# ============================================================================
# Setup Output Directory (NEW WAY)
# ============================================================================

# OLD WAY (COMMENTED OUT):
# output_dir = Path(f"logs/TEST/persub/sub-{SUBJECT_ID}/{ROI_NAME}_universal_hrf")
# output_dir.mkdir(parents=True, exist_ok=True)
# fig_dir = output_dir / "figures"
# fig_dir.mkdir(exist_ok=True)

# NEW WAY:
om = OutputManager(
    subject_id=SUBJECT_ID,
    roi_name=ROI_NAME,
    method_name=METHOD_NAME,
    timestamp=args.timestamp,  # Use provided timestamp or auto-generate
    create_dirs=True
)

# ============================================================================
# Setup Dual Logging (NEW WAY)
# ============================================================================

# OLD WAY (COMMENTED OUT):
# class DualLogger:
#     def __init__(self, filename):
#         self.terminal = sys.stdout
#         self.log = open(filename, 'w', buffering=1)
#     ...
# log_file = output_dir / "log.txt"
# sys.stdout = DualLogger(log_file)

# NEW WAY (DualLogger is in OutputManager):
sys.stdout = om.create_dual_logger()
sys.stderr = sys.stdout

# ============================================================================
# Print Configuration
# ============================================================================

print("="*70)
print("Universal HRF Reconstruction Pipeline (Reorganized Output)")
print("="*70)
print(f"Subject: sub-{SUBJECT_ID}")
print(f"ROI: {ROI_NAME}")
print(f"Method: {METHOD_NAME}")
print(f"Use PCA: {USE_PCA}")
if USE_PCA:
    print(f"PCA components: {N_PCA_COMPONENTS}")
print(f"\nOutput Manager: {om}")
print(f"Output directory: {om.method_roi_dir}")
print()
sys.stdout.flush()

# ============================================================================
# Example: Load and Process Data (same as before)
# ============================================================================

print("[1/N] Loading data...")
# ... your data loading code here ...
print()

# ============================================================================
# Example: Save Results (NEW WAY)
# ============================================================================

print("[X/N] Saving results...")

# 1. Save summary CSV
# OLD: summary_csv_path = output_dir / "summary.csv"
# NEW:
summary_df = pd.DataFrame({
    'ROI': [ROI_NAME],
    'Method': [METHOD_NAME],
    'Subject': [f'sub-{SUBJECT_ID}'],
    'Accuracy': [0.95],
    'Error': [10.5]
})
summary_df.to_csv(om.get_summary_path(), index=False)
print(f"  ✓ Summary: {om.get_summary_path()}")

# 2. Save results pickle
# OLD: results_pkl_path = output_dir / "results.pkl"
# NEW:
results = {
    'subject': SUBJECT_ID,
    'roi': ROI_NAME,
    'method': METHOD_NAME,
    'data': np.random.randn(100, 10)
}
with open(om.get_results_path(), 'wb') as f:
    pickle.dump(results, f)
print(f"  ✓ Results: {om.get_results_path()}")

# 3. Save figures
# OLD: confusion_plot_path = fig_dir / f"{ROI_NAME}_confusion_matrix.png"
# NEW:
fig, ax = plt.subplots(figsize=(8, 6))
ax.plot([1, 2, 3], [1, 4, 2])
ax.set_title('Example Confusion Matrix')
plt.savefig(om.get_figure_path('confusion_matrix'), dpi=150, bbox_inches='tight')
plt.close()
print(f"  ✓ Figure: {om.get_figure_path('confusion_matrix')}")

# OLD: circular_plot_path = fig_dir / f"{ROI_NAME}_circular_color_space.png"
# NEW:
fig, ax = plt.subplots(figsize=(8, 8))
theta = np.linspace(0, 2*np.pi, 100)
ax.plot(np.cos(theta), np.sin(theta))
ax.set_title('Example Circular Color Space')
plt.savefig(om.get_figure_path('circular_color_space'), dpi=150, bbox_inches='tight')
plt.close()
print(f"  ✓ Figure: {om.get_figure_path('circular_color_space')}")

# 4. Save HRF figure (note: ROI prefix is automatically removed)
# OLD: hrf_fig_path = fig_dir / f"{ROI_NAME}_universal_hrf.png"
# NEW: (both of these work - ROI prefix is automatically stripped)
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(np.arange(10), np.random.randn(10))
ax.set_title('Universal HRF')
plt.savefig(om.get_figure_path('universal_hrf'), dpi=150, bbox_inches='tight')
# or: plt.savefig(om.get_figure_path(f'{ROI_NAME}_universal_hrf'), ...)
plt.close()
print(f"  ✓ Figure: {om.get_figure_path('universal_hrf')}")

# 5. Save mask (if applicable, e.g., for voxel selection)
# OLD: mask_path = output_dir / f"{ROI_NAME}_functional_selection_mask.nii.gz"
# NEW:
# Create dummy mask for example
# mask_img = nib.Nifti1Image(np.random.rand(10, 10, 10), np.eye(4))
# nib.save(mask_img, om.get_mask_path())
# print(f"  ✓ Mask: {om.get_mask_path()}")

print()
print("="*70)
print("CONVERSION EXAMPLE COMPLETE")
print("="*70)
print(f"\nAll files saved to: {om.method_roi_dir}")
print("\nFile listing:")
for file in sorted(om.method_roi_dir.glob('sub-*')):
    print(f"  {file.name}")

# ============================================================================
# Key Differences Summary
# ============================================================================

print("\n" + "="*70)
print("KEY DIFFERENCES: OLD vs NEW")
print("="*70)

differences = [
    ("Output Directory",
     f"logs/TEST/sub-{SUBJECT_ID}/{ROI_NAME}_universal_hrf/",
     f"logs/{om.timestamp}/{METHOD_NAME}_{ROI_NAME}/"),

    ("Log File",
     f"logs/.../sub-{SUBJECT_ID}/.../log.txt",
     f"logs/.../{METHOD_NAME}_{ROI_NAME}/sub-{SUBJECT_ID}_log.txt"),

    ("Summary CSV",
     f"output_dir/summary.csv",
     f"om.get_summary_path() → sub-{SUBJECT_ID}_summary.csv"),

    ("Results PKL",
     f"output_dir/results.pkl",
     f"om.get_results_path() → sub-{SUBJECT_ID}_results.pkl"),

    ("Figure Path",
     f"fig_dir/{ROI_NAME}_confusion_matrix.png",
     f"om.get_figure_path('confusion_matrix') → sub-{SUBJECT_ID}_confusion_matrix.png"),

    ("Mask File",
     f"output_dir/{ROI_NAME}_functional_selection_mask.nii.gz",
     f"om.get_mask_path() → sub-{SUBJECT_ID}_{ROI_NAME}_mask.nii.gz"),
]

for label, old, new in differences:
    print(f"\n{label}:")
    print(f"  OLD: {old}")
    print(f"  NEW: {new}")

print("\n" + "="*70)
print("BENEFITS OF NEW STRUCTURE")
print("="*70)
print("""
1. Easy comparison across subjects for same method-ROI
   → All sub-*_summary.csv files in one directory

2. Easy comparison across methods for same ROI
   → Compare zScore_V1/ vs voxelSelect_V1/

3. Simplified batch analysis
   → No need to navigate nested subject directories

4. Consistent naming
   → All files follow sub-{ID}_{filename} pattern

5. Better organization
   → Related analyses grouped together
""")

# ============================================================================
# Batch Processing Example
# ============================================================================

print("\n" + "="*70)
print("BATCH PROCESSING EXAMPLE")
print("="*70)
print("""
# For running multiple subjects with same timestamp:

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

for SUBJECT in 01 02 03 04; do
    for ROI in V1 V2 V3 hV4; do
        python analysis_script.py \\
            --subject $SUBJECT \\
            --roi $ROI \\
            --method zScore \\
            --timestamp $TIMESTAMP
    done
done

# This creates:
# logs/TIMESTAMP/
#   zScore_V1/
#     sub-01_*, sub-02_*, sub-03_*, sub-04_*
#   zScore_V2/
#     sub-01_*, sub-02_*, sub-03_*, sub-04_*
#   ...
""")

print("\nDone!")
