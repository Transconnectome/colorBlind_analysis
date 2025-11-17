#!/bin/bash
################################################################################
# run_all_subjects_rois.sh
################################################################################
#
# Purpose: Run reconstruction for all subjects and ROIs with a SINGLE timestamp
#
# Usage:
#   bash run_all_subjects_rois.sh [method] [options]
#
# Examples:
#   bash run_all_subjects_rois.sh universal_hrf --use-pca --n-components 6
#   bash run_all_subjects_rois.sh zScore --use-pca --n-components 6
#   bash run_all_subjects_rois.sh voxelSelect --use-pca --n-components 6
#
# Output:
#   All results saved to: derivatives/{TIMESTAMP}/
#
################################################################################

# Configuration
SUBJECTS=(P01 01 02 03 04)
ROIS=(V1 V2 V3 hV4)

# Generate common timestamp (CRITICAL: only once!)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "========================================================================"
echo "Running Reconstruction for All Subjects × ROIs"
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
echo "Submitting jobs..."
echo "------------------------------------------------------------------------"

# Counter
TOTAL_JOBS=0

# Submit jobs for all combinations
for SUBJECT in "${SUBJECTS[@]}"; do
    for ROI in "${ROIS[@]}"; do
        # Job name
        JOB_NAME="${SUBJECT}_${ROI}_${TIMESTAMP}"

        # Submit job
        sbatch --job-name=$JOB_NAME \
               run_reconstruction.sh $SUBJECT $ROI $TIMESTAMP $METHOD "$EXTRA_ARGS"

        echo "  Submitted: $JOB_NAME"

        ((TOTAL_JOBS++))
    done
done

echo "------------------------------------------------------------------------"
echo "Total jobs submitted: $TOTAL_JOBS"
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
