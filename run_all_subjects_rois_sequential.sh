#!/bin/bash
################################################################################
# run_all_subjects_rois_sequential.sh
################################################################################
#
# Purpose: Run reconstruction for all subjects and ROIs SEQUENTIALLY
#          to avoid resource exhaustion
#
# Usage:
#   bash run_all_subjects_rois_sequential.sh [method] [options]
#
# Examples:
#   bash run_all_subjects_rois_sequential.sh universal_hrf --use-pca --n-components 6
#
################################################################################

# Configuration
SUBJECTS=(P01 01 02 03 04)
ROIS=(V1 V2 V3 hV4)

# Generate common timestamp (CRITICAL: only once!)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "========================================================================"
echo "Running Reconstruction for All Subjects × ROIs (SEQUENTIAL)"
echo "========================================================================"
echo "Timestamp: $TIMESTAMP"
echo "Subjects: ${SUBJECTS[@]}"
echo "ROIs: ${ROIS[@]}"
echo ""

# Get method (default: universal_hrf)
METHOD=${1:-universal_hrf}
shift  # Remove first argument

# Remaining arguments are passed to the script
EXTRA_ARGS="$@"

echo "Method: $METHOD"
echo "Extra arguments: $EXTRA_ARGS"
echo ""
echo "Submitting jobs SEQUENTIALLY with dependency chain..."
echo "------------------------------------------------------------------------"

# Counter
TOTAL_JOBS=0
PREV_JOB_ID=""

# Submit jobs for all combinations with dependencies
for SUBJECT in "${SUBJECTS[@]}"; do
    for ROI in "${ROIS[@]}"; do
        # Job name
        JOB_NAME="${SUBJECT}_${ROI}_${TIMESTAMP}"

        # Submit job with dependency on previous job
        if [ -z "$PREV_JOB_ID" ]; then
            # First job - no dependency
            JOB_OUTPUT=$(sbatch --job-name=$JOB_NAME \
                               run_reconstruction.sh $SUBJECT $ROI $TIMESTAMP $METHOD "$EXTRA_ARGS" 2>&1)
        else
            # Subsequent jobs - wait for previous to finish
            JOB_OUTPUT=$(sbatch --job-name=$JOB_NAME \
                               --dependency=afterany:$PREV_JOB_ID \
                               run_reconstruction.sh $SUBJECT $ROI $TIMESTAMP $METHOD "$EXTRA_ARGS" 2>&1)
        fi

        # Extract job ID from output (format: "Submitted batch job 12345")
        PREV_JOB_ID=$(echo $JOB_OUTPUT | grep -oP 'Submitted batch job \K[0-9]+')

        echo "  Submitted: $JOB_NAME (Job ID: $PREV_JOB_ID)"

        ((TOTAL_JOBS++))
    done
done

echo "------------------------------------------------------------------------"
echo "Total jobs submitted: $TOTAL_JOBS"
echo ""
echo "Jobs will run SEQUENTIALLY (one at a time)"
echo ""
echo "Results will be saved to:"
echo "  derivatives/$TIMESTAMP/"
echo ""
echo "Monitor jobs with:"
echo "  squeue -u \$USER"
echo ""
echo "Check results with:"
echo "  ls derivatives/$TIMESTAMP/"
echo "========================================================================"
