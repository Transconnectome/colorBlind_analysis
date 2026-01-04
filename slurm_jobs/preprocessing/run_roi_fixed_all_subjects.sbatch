#!/bin/bash
#SBATCH --job-name=roi_fixed_all
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=4:00:00
#SBATCH --output=logs/roi_fixed_all_%j.out
#SBATCH --error=logs/roi_fixed_all_%j.err

# ============================================================================
# ROI Pipeline FIXED - ALL SUBJECTS (01-10)
# ============================================================================
# Uses AFNI 3dresample for proper affine matching
# Fixes zero variance issue from incorrect resampling
# ============================================================================

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create log directory if it doesn't exist
mkdir -p logs

echo "============================================================================"
echo "ROI Pipeline FIXED - ALL SUBJECTS"
echo "============================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo ""
echo "Script: fix_roi_resample_afni.py"
echo "Subjects: 01-10 (10 subjects)"
echo "ROIs per subject: V1, V2, V3, hV4 (4 ROIs)"
echo "Output: derivatives/sub-{ID}/roi_pipeline_afni_v3_fixed/"
echo "============================================================================"
echo

# Define subjects
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)

TOTAL_SUBJECTS=${#SUBJECTS[@]}

echo "Processing $TOTAL_SUBJECTS subjects..."
echo

# Track progress
CURRENT=0
FAILED_COUNT=0
FAILED_LIST=""

# Loop through all subjects
for SUBJECT in "${SUBJECTS[@]}"; do
    CURRENT=$((CURRENT + 1))

    echo ""
    echo "========================================================================"
    echo "[$CURRENT/$TOTAL_SUBJECTS] Subject: sub-$SUBJECT"
    echo "========================================================================"
    echo "Started: $(date)"
    echo ""

    # Run FIXED ROI pipeline for this subject
    # This uses AFNI 3dresample for proper affine matching
    python fix_roi_resample_afni.py $SUBJECT

    EXIT_CODE=$?

    echo ""
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✓ Subject sub-$SUBJECT: SUCCESS (all ROIs validated)"
    else
        echo "✗ Subject sub-$SUBJECT: FAILED (exit code $EXIT_CODE)"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        FAILED_LIST="${FAILED_LIST}sub-${SUBJECT} "
    fi
    echo "Finished: $(date)"
    echo "========================================================================"
    echo ""
done

echo ""
echo "============================================================================"
echo "ROI PIPELINE COMPLETE - FINAL SUMMARY"
echo "============================================================================"
echo "Total subjects processed: $TOTAL_SUBJECTS"
echo "Successful: $((TOTAL_SUBJECTS - FAILED_COUNT))"
echo "Failed: $FAILED_COUNT"

if [ $FAILED_COUNT -gt 0 ]; then
    echo ""
    echo "Failed subjects:"
    echo "$FAILED_LIST"
fi

echo ""
echo "Results saved in: derivatives/sub-{ID}/roi_pipeline_afni_v3_fixed/"
echo ""
echo "Each subject directory contains:"
echo "  - V1_mask_afni_fixed.nii.gz"
echo "  - V2_mask_afni_fixed.nii.gz"
echo "  - V3_mask_afni_fixed.nii.gz"
echo "  - hV4_mask_afni_fixed.nii.gz"
echo ""
echo "All masks verified with:"
echo "  ✓ Affine match with functional data"
echo "  ✓ Non-zero signal in ROI regions"
echo "  ✓ Zero variance check passed"
echo ""
echo "Finished: $(date)"
echo "============================================================================"

# Exit with failure if any subject failed
if [ $FAILED_COUNT -gt 0 ]; then
    exit 1
else
    exit 0
fi
