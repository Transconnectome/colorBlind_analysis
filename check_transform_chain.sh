#!/bin/bash
#
# Diagnostic script to check ROI transform chain for ROI_ZERO failures
#
# Usage: bash check_transform_chain.sh <subject_id> <run>
#
# This script verifies:
# 1. Wang atlas files exist
# 2. fMRIPrep transform files exist
# 3. Transform inversion flags are correct
# 4. Output ROI files are generated

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <subject_id> <run>"
    echo "Example: $0 09 1"
    exit 1
fi

SUBJECT=$1
RUN=$2

echo "================================================================================"
echo "TRANSFORM CHAIN DIAGNOSTIC: Sub-${SUBJECT} Run-${RUN}"
echo "================================================================================"

# Paths
FMRIPREP_OUT="/storage/connectome/haba6030/fmriprep_out_deoblique_v2"
WANG_ATLAS="/scratch/connectome/haba6030/colorBlind/ProbAtlas_v4_2mm/subj_vol_all"
SUBJECT_DIR="${FMRIPREP_OUT}/sub-${SUBJECT}"

echo ""
echo "📁 Step 1: Checking Wang Atlas Files"
echo "--------------------------------------------------------------------------------"
for HEMI in lh rh; do
    for ROI_NUM in 1 2 3 4; do
        ATLAS_FILE="${WANG_ATLAS}/perc_VTPM_vol_roi${ROI_NUM}_${HEMI}.nii.gz"
        if [ -f "$ATLAS_FILE" ]; then
            VOX=$(fslstats "$ATLAS_FILE" -V | awk '{print $1}')
            echo "✓ ROI${ROI_NUM}_${HEMI}: ${VOX} voxels"
        else
            echo "✗ MISSING: $ATLAS_FILE"
        fi
    done
done

echo ""
echo "📁 Step 2: Checking fMRIPrep Transform Files"
echo "--------------------------------------------------------------------------------"

# MNI → T1w transform
MNI_TO_T1W="${SUBJECT_DIR}/anat/sub-${SUBJECT}_from-MNI152NLin2009cAsym_to-T1w_mode-image_xfm.h5"
if [ -f "$MNI_TO_T1W" ]; then
    echo "✓ MNI→T1w transform exists"
else
    echo "✗ MISSING: $MNI_TO_T1W"
fi

# T1w → boldref transform
BOLDREF_TO_T1W="${SUBJECT_DIR}/func/sub-${SUBJECT}_task-rsvp_run-${RUN}_from-boldref_to-T1w_mode-image_xfm.txt"
if [ -f "$BOLDREF_TO_T1W" ]; then
    echo "✓ boldref→T1w transform exists"
else
    echo "✗ MISSING: $BOLDREF_TO_T1W"
fi

# boldref and masks
BOLDREF="${SUBJECT_DIR}/func/sub-${SUBJECT}_task-rsvp_run-${RUN}_desc-coreg_boldref.nii.gz"
BMASK="${SUBJECT_DIR}/func/sub-${SUBJECT}_task-rsvp_run-${RUN}_desc-brain_mask.nii.gz"

if [ -f "$BOLDREF" ]; then
    DIM=$(fslinfo "$BOLDREF" | grep '^dim[1-4]' | awk '{print $2}' | tr '\n' 'x' | sed 's/x$//')
    echo "✓ BOLDREF exists (dims: $DIM)"
else
    echo "✗ MISSING: $BOLDREF"
fi

if [ -f "$BMASK" ]; then
    VOX=$(fslstats "$BMASK" -V | awk '{print $1}')
    echo "✓ BOLD brain mask exists (${VOX} voxels)"
else
    echo "✗ MISSING: $BMASK"
fi

echo ""
echo "🔬 Step 3: Testing Transform Chain (V1_lh as example)"
echo "--------------------------------------------------------------------------------"

if [ -f "$MNI_TO_T1W" ] && [ -f "$BOLDREF_TO_T1W" ] && [ -f "$BOLDREF" ]; then
    WANG_V1_LH="${WANG_ATLAS}/perc_VTPM_vol_roi1_lh.nii.gz"

    echo "Applying: Wang_V1_lh (MNI) → T1w → boldref"

    # Try FORWARD inversion (current QC script)
    echo ""
    echo "TEST A: MNI→T1w [FORWARD], T1w→boldref [INVERSE]"
    antsApplyTransforms -d 3 \
        -i "$WANG_V1_LH" \
        -r "$BOLDREF" \
        -o /tmp/test_roi_v1_lh_forward.nii.gz \
        -t ["${BOLDREF_TO_T1W}",1] \
        -t "${MNI_TO_T1W}" \
        -n Linear

    VOX_FWD=$(fslstats /tmp/test_roi_v1_lh_forward.nii.gz -V | awk '{print $1}')
    MAX_FWD=$(fslstats /tmp/test_roi_v1_lh_forward.nii.gz -R | awk '{print $2}')
    echo "   Result: ${VOX_FWD} voxels, max=${MAX_FWD}"

    # Try INVERSE inversion (alternative)
    echo ""
    echo "TEST B: MNI→T1w [FORWARD], T1w→boldref [FORWARD - wrong direction]"
    antsApplyTransforms -d 3 \
        -i "$WANG_V1_LH" \
        -r "$BOLDREF" \
        -o /tmp/test_roi_v1_lh_inverse.nii.gz \
        -t "${BOLDREF_TO_T1W}" \
        -t "${MNI_TO_T1W}" \
        -n Linear

    VOX_INV=$(fslstats /tmp/test_roi_v1_lh_inverse.nii.gz -V | awk '{print $1}')
    MAX_INV=$(fslstats /tmp/test_roi_v1_lh_inverse.nii.gz -R | awk '{print $2}')
    echo "   Result: ${VOX_INV} voxels, max=${MAX_INV}"

    # Threshold test
    echo ""
    echo "🔍 Applying threshold=20 to both:"
    fslmaths /tmp/test_roi_v1_lh_forward.nii.gz -thr 20 -bin /tmp/test_roi_v1_lh_forward_thr20.nii.gz
    fslmaths /tmp/test_roi_v1_lh_inverse.nii.gz -thr 20 -bin /tmp/test_roi_v1_lh_inverse_thr20.nii.gz

    VOX_FWD_THR=$(fslstats /tmp/test_roi_v1_lh_forward_thr20.nii.gz -V | awk '{print $1}')
    VOX_INV_THR=$(fslstats /tmp/test_roi_v1_lh_inverse_thr20.nii.gz -V | awk '{print $1}')

    echo "   TEST A (current): ${VOX_FWD_THR} voxels after threshold"
    echo "   TEST B (alt):     ${VOX_INV_THR} voxels after threshold"

    echo ""
    echo "================================================================================"
    echo "CONCLUSION"
    echo "================================================================================"

    if [ "$VOX_FWD_THR" -eq 0 ] && [ "$VOX_INV_THR" -eq 0 ]; then
        echo "❌ BOTH methods produce 0 voxels → Registration itself is catastrophically bad"
        echo "   → Check fMRIPrep HTML report for this subject"
    elif [ "$VOX_FWD_THR" -gt 0 ]; then
        echo "✅ Current method (TEST A) works: ${VOX_FWD_THR} voxels"
        echo "   → Transform chain is CORRECT"
        echo "   → QC script issue or threshold too high"
    elif [ "$VOX_INV_THR" -gt 0 ]; then
        echo "🔧 TRANSFORM INVERSION BUG FOUND!"
        echo "   Current (TEST A): 0 voxels"
        echo "   Fixed (TEST B):   ${VOX_INV_THR} voxels"
        echo "   → FIX: Remove '[xfm,1]' inversion flag in qc_runwise_improved.sh"
    else
        echo "⚠️  Unexpected result - manual inspection needed"
    fi

else
    echo "⚠️  Cannot test - missing transform files"
fi

echo ""
echo "📊 For comparison with QC results, run:"
echo "   grep 'sub\|${SUBJECT}' preps/qc_runwise_sub-${SUBJECT}.tsv | head -5"
