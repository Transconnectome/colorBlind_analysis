#!/bin/bash
#
# Transform ROI from MNI atlas to T1w space
#
# Purpose: Create individual ROI masks in T1w space for analysis
#
# Pipeline:
#   1. MNI ROI → T1w native (using ANTs inverse warp)
#   2. Create binary mask (threshold > 20)
#   3. Visual QC overlay with T1w space BOLD
#
# Analysis uses T1w space BOLD data (space-T1w_desc-preproc_bold.nii.gz)
#
# Usage: bash transform_roi_to_native.sh <subject_id> <roi_name> [run]
#
# Example: bash transform_roi_to_native.sh 02 V1 1
#
# Author: Modified for T1w space analysis
# Date: 2025-01-23

set -e

# ============================================================================
# Environment Setup
# ============================================================================

# Change to project directory FIRST (required for .bashrc)
PROJECT_DIR="/scratch/connectome/haba6030/colorBlind"
cd "$PROJECT_DIR"

# Activate conda environment (for ANTs, FSL tools)
source ~/.bashrc
conda activate nilearn

# ============================================================================
# Parse Arguments
# ============================================================================

if [ $# -lt 2 ]; then
    echo "Usage: $0 <subject_id> <roi_name> [run]"
    echo ""
    echo "Arguments:"
    echo "  subject_id  : Subject ID (e.g., 02, 03, 05)"
    echo "  roi_name    : ROI name (V1, V2, V3, hV4)"
    echo "  run         : Run number (default: 1)"
    echo ""
    echo "Example:"
    echo "  $0 02 V1 1"
    exit 1
fi

SUBJECT=$1
ROI=$2
RUN=${3:-1}

# ============================================================================
# Path Configuration
# ============================================================================

# Server paths (will be used when running on server)
FMRIPREP_OUT="/storage/connectome/haba6030/fmriprep_out_method3_header_mi"
WANG_ATLAS_DIR="/scratch/connectome/haba6030/colorBlind/ProbAtlas_v4_2mm/subj_vol_all"
OUTPUT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/results/native_roi"

# Singularity container (for ANTs)
APPTAINER="/usr/local/bin/singularity"
IMG="/home/connectome/haba6030/fmriprep-23.2.3.sif"

# Create output directory
mkdir -p "${OUTPUT_DIR}/sub-${SUBJECT}"

echo "================================================================================"
echo "ROI Transform to Native BOLD Space"
echo "================================================================================"
echo "Subject: sub-${SUBJECT}"
echo "ROI: ${ROI}"
echo "Run: ${RUN}"
echo ""

# ============================================================================
# Step 1: Verify Required Files
# ============================================================================

echo "📁 Step 1: Verifying required files..."
echo "--------------------------------------------------------------------------------"

# fMRIPrep output paths
SUBJECT_DIR="${FMRIPREP_OUT}/sub-${SUBJECT}"
ANAT_DIR="${SUBJECT_DIR}/anat"
FUNC_DIR="${SUBJECT_DIR}/func"

# Transform files
MNI_TO_T1W="${ANAT_DIR}/sub-${SUBJECT}_acq-mprage_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5"

# Reference images
T1W_REF="${ANAT_DIR}/sub-${SUBJECT}_acq-mprage_desc-preproc_T1w.nii.gz"
BOLD_T1W="${FUNC_DIR}/sub-${SUBJECT}_task-rsvp_run-${RUN}_space-T1w_desc-preproc_bold.nii.gz"

# Check required files exist
MISSING_FILES=0

for file in "$MNI_TO_T1W" "$T1W_REF" "$BOLD_T1W"; do
    if [ ! -f "$file" ]; then
        echo "✗ MISSING: $file"
        MISSING_FILES=$((MISSING_FILES + 1))
    else
        echo "✓ Found: $(basename $file)"
    fi
done

if [ $MISSING_FILES -gt 0 ]; then
    echo ""
    echo "❌ Missing $MISSING_FILES required file(s). Cannot proceed."
    exit 1
fi

echo ""

# ============================================================================
# Step 2: Combine Wang Atlas ROI (MNI space)
# ============================================================================

echo "🧠 Step 2: Creating combined MNI ROI from Wang atlas..."
echo "--------------------------------------------------------------------------------"

# Map ROI name to Wang atlas ROI numbers
case "$ROI" in
    V1)
        ROI_NUMS="1 2"
        ;;
    V2)
        ROI_NUMS="3 4"
        ;;
    V3)
        ROI_NUMS="5 6"
        ;;
    hV4)
        ROI_NUMS="7"
        ;;
    *)
        echo "❌ Unknown ROI: $ROI"
        echo "   Valid ROIs: V1, V2, V3, hV4"
        exit 1
        ;;
esac

# Temporary directory for intermediate files
TMP_DIR="${OUTPUT_DIR}/tmp_sub-${SUBJECT}_${ROI}"
mkdir -p "$TMP_DIR"

# Combine hemispheres and ROI parts
COMBINED_ROI_MNI="${TMP_DIR}/wang_${ROI}_MNI.nii.gz"
FIRST_FILE=1

for HEMI in lh rh; do
    for ROI_NUM in $ROI_NUMS; do
        ATLAS_FILE="${WANG_ATLAS_DIR}/perc_VTPM_vol_roi${ROI_NUM}_${HEMI}.nii.gz"

        if [ ! -f "$ATLAS_FILE" ]; then
            echo "⚠ Missing: $(basename $ATLAS_FILE)"
            continue
        fi

        if [ $FIRST_FILE -eq 1 ]; then
            # First file: copy as base
            cp "$ATLAS_FILE" "$COMBINED_ROI_MNI"
            FIRST_FILE=0
            echo "  Base: ROI${ROI_NUM}_${HEMI}"
        else
            # Add to existing
            fslmaths "$COMBINED_ROI_MNI" -add "$ATLAS_FILE" "$COMBINED_ROI_MNI"
            echo "  Add: ROI${ROI_NUM}_${HEMI}"
        fi
    done
done

# Verify combined ROI
VOX_MNI=$(fslstats "$COMBINED_ROI_MNI" -V | awk '{print $1}')
echo "✓ Combined MNI ROI: ${VOX_MNI} voxels"

if [ "$VOX_MNI" -eq 0 ]; then
    echo "❌ Empty ROI - check Wang atlas files"
    exit 1
fi

echo ""

# ============================================================================
# Step 3: MNI ROI → T1w Native
# ============================================================================

echo "🔄 Step 3: Transforming MNI ROI → T1w native..."
echo "--------------------------------------------------------------------------------"

ROI_T1W="${OUTPUT_DIR}/sub-${SUBJECT}/sub-${SUBJECT}_${ROI}_space-T1w.nii.gz"

# Use Singularity container for ANTs
${APPTAINER} exec --cleanenv \
    -B /storage:/storage -B /scratch:/scratch "${IMG}" \
    antsApplyTransforms -d 3 \
        -i "$COMBINED_ROI_MNI" \
        -r "$T1W_REF" \
        -o "$ROI_T1W" \
        -t "$MNI_TO_T1W" \
        -n Linear

# Verify output
if [ ! -f "$ROI_T1W" ]; then
    echo "❌ Failed to create T1w ROI"
    exit 1
fi

VOX_T1W=$(fslstats "$ROI_T1W" -V | awk '{print $1}')
MAX_T1W=$(fslstats "$ROI_T1W" -R | awk '{print $2}')
echo "✓ T1w ROI created: ${VOX_T1W} voxels, max=${MAX_T1W}"

echo ""

# ============================================================================
# Step 4: Create Binary Mask (threshold > 20)
# ============================================================================

echo "🎭 Step 4: Creating binary mask (threshold=20)..."
echo "--------------------------------------------------------------------------------"

ROI_MASK="${OUTPUT_DIR}/sub-${SUBJECT}/sub-${SUBJECT}_${ROI}_space-T1w_mask.nii.gz"

fslmaths "$ROI_T1W" -thr 20 -bin "$ROI_MASK"

VOX_MASK=$(fslstats "$ROI_MASK" -V | awk '{print $1}')
echo "✓ Binary mask created: ${VOX_MASK} voxels"

if [ "$VOX_MASK" -eq 0 ]; then
    echo "⚠ WARNING: Binary mask is empty (0 voxels > threshold 20)"
    echo "   This suggests transformation failed or threshold too high"
fi

echo ""

# ============================================================================
# Step 5: Generate QC Overlay Image
# ============================================================================

echo "📊 Step 5: Generating QC overlay image..."
echo "--------------------------------------------------------------------------------"

QC_PNG="${OUTPUT_DIR}/sub-${SUBJECT}/QC_sub-${SUBJECT}_${ROI}_overlay.png"

# Use FSL's slicer for quick QC (overlay ROI on T1w space BOLD)
slicer "$BOLD_T1W" "$ROI_T1W" \
    -a "$QC_PNG"

echo "✓ QC image saved: $QC_PNG"
echo ""

# ============================================================================
# Summary
# ============================================================================

echo "================================================================================"
echo "SUMMARY"
echo "================================================================================"
echo "Subject: sub-${SUBJECT}"
echo "ROI: ${ROI}"
echo ""
echo "Voxel counts:"
echo "  MNI space:  ${VOX_MNI} voxels"
echo "  T1w space:  ${VOX_T1W} voxels (${MAX_T1W} max intensity)"
echo "  Binary mask: ${VOX_MASK} voxels (threshold > 20)"
echo ""
echo "Output files:"
echo "  T1w ROI (probabilistic): $ROI_T1W"
echo "  T1w mask (binary):       $ROI_MASK"
echo "  QC overlay:              $QC_PNG"
echo ""
echo "Analysis space: T1w (using space-T1w_desc-preproc_bold.nii.gz)"
echo ""

# Interpretation
if [ "$VOX_MASK" -gt 100 ]; then
    echo "✅ SUCCESS: ROI successfully transformed to T1w space"
    echo "   → Analysis can proceed in T1w space"
    echo "   → Higher resolution than MNI space"
elif [ "$VOX_MASK" -gt 0 ]; then
    echo "⚠ PARTIAL: ROI present but small (${VOX_MASK} voxels)"
    echo "   → Manual inspection recommended"
else
    echo "❌ FAILURE: No voxels in binary mask"
    echo "   → Check QC overlay and registration quality"
fi

echo ""
echo "Next steps:"
echo "  1. Visual inspection: $QC_PNG"
echo "  2. Verify ROI location in posterior occipital cortex"
echo "  3. If successful, run functional analysis using T1w space BOLD"
echo ""

# Clean up temp directory
rm -rf "$TMP_DIR"

echo "✓ Complete"
