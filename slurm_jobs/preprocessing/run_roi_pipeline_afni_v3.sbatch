#!/bin/bash
#SBATCH --job-name=roi_afni_v3
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=12:00:00
#SBATCH --output=logs/roi_pipeline_afni_v3_%j.out
#SBATCH --error=logs/roi_pipeline_afni_v3_%j.err

# ============================================================================
# ROI Pipeline for AFNI V3 - ALL SUBJECTS
# ============================================================================
# Creates ROI masks for all subjects using AFNI-deobliqued fMRIPrep data
# Uses optimized parameters (threshold=50, nearest interpolation, etc.)
# ============================================================================

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create log directory if it doesn't exist
mkdir -p logs

echo "============================================================================"
echo "ROI Pipeline AFNI V3 - ALL SUBJECTS"
echo "============================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo ""
echo "Subjects: 01-10 (10 subjects)"
echo "ROIs per subject: V1, V2, V3, hV4 (4 ROIs)"
echo "Dataset: afni_deoblique_v3 (fmriprep_out_afni_deoblique)"
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

    # Run ROI pipeline for this subject
    # This will process ALL ROIs (V1, V2, V3, hV4) with optimized parameters
    # Note: Pass subject ID without "sub-" prefix (e.g., "01" not "sub-01")
    python roi_pipeline_afni_v3.py $SUBJECT 1

    EXIT_CODE=$?

    echo ""
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✓ Subject sub-$SUBJECT: SUCCESS (all ROIs processed)"
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
echo "Results saved in: derivatives/sub-{ID}/roi_pipeline_afni_v3/"
echo ""
echo "Each subject directory contains:"
echo "  - ROI masks for V1, V2, V3, hV4"
echo "  - Validation metrics and visualizations"
echo ""
echo "Finished: $(date)"
echo "============================================================================"

# Exit with failure if any subject failed
if [ $FAILED_COUNT -gt 0 ]; then
    exit 1
else
    exit 0
fi
