#!/bin/bash
#SBATCH --job-name=roi_pipeline_all
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --output=logs/roi_pipeline_all_%j.out
#SBATCH --error=logs/roi_pipeline_all_%j.err

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create log directory if it doesn't exist
mkdir -p logs

echo "============================================================================"
echo "Comprehensive ROI Pipeline - ALL SUBJECTS"
echo "============================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo ""
echo "Subjects: 01-10 (10 subjects)"
echo "ROIs per subject: V1, V2, V3, hV4 (4 ROIs)"
echo "Parameter combinations: 5 × 2 × 2 × 3 × 2 × 2 = 240 per ROI"
echo "Total: 10 subjects × 4 ROIs × 240 configs = 9,600 combinations"
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

    # Run comprehensive ROI pipeline for this subject
    # This will process ALL ROIs (V1, V2, V3, hV4) and ALL parameter combinations
    python roi_pipeline_comprehensive.py sub-$SUBJECT 1

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
echo "Results saved in: derivatives/sub-{ID}/roi_pipeline_YYYYMMDD_HHMMSS/"
echo ""
echo "Each subject directory contains:"
echo "  - masks/         : All ROI mask variations"
echo "  - figures/       : Visualization plots"
echo "  - results.csv    : Metrics for all combinations"
echo "  - COMPARISON_REPORT.md : Detailed analysis report"
echo ""
echo "Finished: $(date)"
echo "============================================================================"

# Exit with failure if any subject failed
if [ $FAILED_COUNT -gt 0 ]; then
    exit 1
else
    exit 0
fi
