#!/bin/bash
# diagnose_server.sh
# Run this on the server to diagnose ROI mask and analysis issues
# Usage: bash diagnose_server.sh

echo "======================================================================="
echo "ROI Mask & Analysis Diagnostic Tool"
echo "======================================================================="
echo ""

# ============================================================================
# 1. Check ROI Mask Voxel Counts
# ============================================================================
echo "1. Checking ROI mask voxel counts..."
echo "---------------------------------------------------------------------"
echo "Expected (GOOD): V2=310, V1=511, V3=89, hV4=55"
echo ""

if command -v python3 &> /dev/null; then
    for mask in derivatives/sub-*/roi/*_mask.nii.gz; do
        if [ -f "$mask" ]; then
            python3 -c "import nibabel as nib; import numpy as np; img=nib.load('$mask'); n_vox=int(np.sum(img.get_fdata()>0)); shape=img.shape[:3]; print(f'  {mask}'); print(f'    Voxels: {n_vox}'); print(f'    Shape: {shape}')"
        fi
    done
else
    echo "  ⚠ Python3 not available - skipping voxel count check"
fi

echo ""

# ============================================================================
# 2. Check Reference Functional Images
# ============================================================================
echo "2. Checking reference functional image shapes..."
echo "---------------------------------------------------------------------"
echo "Expected: (97, 115, 97) for res-2"
echo ""

if command -v python3 &> /dev/null; then
    for func in /storage/connectome/haba6030/fmriprep_out/sub-*/func/*run-1*res-2*preproc_bold.nii.gz; do
        if [ -f "$func" ]; then
            python3 -c "import nibabel as nib; img=nib.load('$func'); print(f'  {func}'); print(f'    Shape: {img.shape[:3]}')"
        fi
    done
else
    echo "  ⚠ Python3 not available - skipping shape check"
fi

echo ""

# ============================================================================
# 3. Check Brain Mask Availability
# ============================================================================
echo "3. Checking brain mask availability..."
echo "---------------------------------------------------------------------"

brain_masks_found=0

# Check anat directory
for mask in /storage/connectome/haba6030/fmriprep_out/sub-*/anat/*res-2*brain_mask.nii.gz; do
    if [ -f "$mask" ]; then
        echo "  ✓ Found (anat): $(basename $mask)"
        ((brain_masks_found++))
    fi
done

# Check func directory
for mask in /storage/connectome/haba6030/fmriprep_out/sub-*/func/*res-2*brain_mask.nii.gz; do
    if [ -f "$mask" ]; then
        echo "  ✓ Found (func): $(basename $mask)"
        ((brain_masks_found++))
    fi
done

if [ $brain_masks_found -eq 0 ]; then
    echo "  ⚠ No brain masks found!"
    echo "    This could explain increased voxel counts"
fi

echo ""

# ============================================================================
# 4. Check Analysis Results
# ============================================================================
echo "4. Checking recent analysis results..."
echo "---------------------------------------------------------------------"

# Check for summary.csv files
summary_files=$(find derivatives/sub-*/fir_reconstruction/*/summary.csv logs/sub-*/*/summary.csv troubleshoot/logs/sub-*/*/summary.csv 2>/dev/null | head -20)

if [ -n "$summary_files" ]; then
    echo "  Recent summaries found:"
    for summary in $summary_files; do
        if [ -f "$summary" ]; then
            echo ""
            echo "  File: $summary"
            head -2 "$summary" | tail -1 | awk -F, '{print "    Voxels: "$3", Delay: "$4" TRs, Novel Error: "$9"°"}'
        fi
    done
else
    echo "  No summary.csv files found"
fi

echo ""

# ============================================================================
# 5. Check Directory Structure
# ============================================================================
echo "5. Checking directory structure..."
echo "---------------------------------------------------------------------"

# Check derivatives
if [ -d "derivatives/sub-01" ]; then
    echo "  ✓ derivatives/sub-01/ exists"
    if [ -d "derivatives/sub-01/roi" ]; then
        n_masks=$(ls derivatives/sub-01/roi/*.nii.gz 2>/dev/null | wc -l)
        echo "    - ROI masks: $n_masks files"
    fi
fi

if [ -d "derivatives/sub-P01" ]; then
    echo "  ✓ derivatives/sub-P01/ exists"
    if [ -d "derivatives/sub-P01/roi" ]; then
        n_masks=$(ls derivatives/sub-P01/roi/*.nii.gz 2>/dev/null | wc -l)
        echo "    - ROI masks: $n_masks files"
    fi
fi

# Check for potential conflicts
if [ -d "derivatives/sub-01" ] && [ -d "derivatives/sub-P01" ]; then
    echo ""
    echo "  ⚠ WARNING: Both sub-01 and sub-P01 derivatives exist!"
    echo "    This could indicate old (sub-01) vs new (sub-P01) mask versions"
    echo "    Recommendation: Compare voxel counts to identify GOOD vs BAD"
fi

echo ""

# ============================================================================
# 6. File Timestamps
# ============================================================================
echo "6. Checking ROI mask creation times..."
echo "---------------------------------------------------------------------"

for mask in derivatives/sub-*/roi/*V2_mask.nii.gz; do
    if [ -f "$mask" ]; then
        ls -lh --time-style=long-iso "$mask" | awk '{print "  " $6, $7, ":", $9, "(" $5 ")"}'
    fi
done

echo ""

# ============================================================================
# Summary
# ============================================================================
echo "======================================================================="
echo "DIAGNOSTIC SUMMARY"
echo "======================================================================="
echo ""
echo "Next steps:"
echo "  1. Compare voxel counts above with expected (V2=310)"
echo "  2. If you see 536 or 553 voxels for V2 → These are BAD masks"
echo "  3. If you see 310 voxels for V2 → This is GOOD! Keep it!"
echo "  4. Check which directory (sub-01 vs sub-P01) has the correct masks"
echo "  5. Review DIAGNOSTIC_REPORT_v2.md for detailed fix instructions"
echo ""
echo "======================================================================="
