#!/bin/bash
################################################################################
# run_all_subjects.sh
################################################################################
#
# Purpose: Submit reconstruction jobs for all subjects
#          Each subject processes all 4 ROIs in a single SLURM job
#
# Usage:
#   bash run_all_subjects.sh [method] [options]
#
# Examples:
#   bash run_all_subjects.sh universal_hrf --use-pca --n-components 6
#   bash run_all_subjects.sh zScore --use-pca --n-components 6
#   bash run_all_subjects.sh voxelSelect --use-pca --n-components 6
#
# Output:
#   - All results: derivatives/{TIMESTAMP}/
#   - Logs: logs/pilot/, logs/sub-01/, logs/sub-02/, etc.
#
################################################################################

# Configuration
SUBJECTS=(P01 01 02 03 04)

# Generate common timestamp (CRITICAL: only once!)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "========================================================================"
echo "Running Reconstruction for All Subjects"
echo "========================================================================"
echo "Timestamp: $TIMESTAMP"
echo "Subjects: ${SUBJECTS[@]}"
echo "ROIs per subject: V1, V2, V3, hV4"
echo ""

# Get method (default: universal_hrf)
METHOD=${1:-universal_hrf}
shift  # Remove first argument

# Remaining arguments are passed to the script
EXTRA_ARGS="$@"

echo "Method: $METHOD"
echo "Extra arguments: $EXTRA_ARGS"
echo ""

# Create log directories
echo "Creating log directories..."
mkdir -p logs/pilot
for SUBJECT in 01 02 03 04; do
    mkdir -p logs/sub-${SUBJECT}
done
echo ""

echo "Submitting jobs..."
echo "------------------------------------------------------------------------"

# Submit jobs for all subjects
for SUBJECT in "${SUBJECTS[@]}"; do
    # Job name
    if [ "$SUBJECT" == "P01" ]; then
        JOB_NAME="pilot_${TIMESTAMP}"
        SUBJECT_LABEL="pilot (P01)"
    else
        JOB_NAME="sub-${SUBJECT}_${TIMESTAMP}"
        SUBJECT_LABEL="sub-${SUBJECT}"
    fi

    # Submit job
    JOB_OUTPUT=$(sbatch --job-name=$JOB_NAME \
                       run_subject_all_rois.sh $SUBJECT $TIMESTAMP $METHOD "$EXTRA_ARGS" 2>&1)

    # Extract job ID
    JOB_ID=$(echo $JOB_OUTPUT | grep -oP 'Submitted batch job \K[0-9]+')

    if [ -n "$JOB_ID" ]; then
        echo "  ✓ Submitted: $SUBJECT_LABEL (Job ID: $JOB_ID)"
    else
        echo "  ✗ Failed to submit: $SUBJECT_LABEL"
        echo "    Error: $JOB_OUTPUT"
    fi
done

echo "------------------------------------------------------------------------"
echo "Total jobs submitted: ${#SUBJECTS[@]}"
echo ""
echo "Results will be saved to:"
echo "  derivatives/$TIMESTAMP/"
echo ""
echo "Logs will be saved to:"
echo "  logs/pilot/reconstruction_${TIMESTAMP}.out"
echo "  logs/sub-01/reconstruction_${TIMESTAMP}.out"
echo "  logs/sub-02/reconstruction_${TIMESTAMP}.out"
echo "  logs/sub-03/reconstruction_${TIMESTAMP}.out"
echo "  logs/sub-04/reconstruction_${TIMESTAMP}.out"
echo ""
echo "Monitor jobs with:"
echo "  squeue -u \$USER"
echo ""
echo "Check specific subject log:"
echo "  tail -f logs/sub-01/reconstruction_${TIMESTAMP}.out"
echo ""
echo "Check all logs at once:"
echo "  tail -f logs/*/reconstruction_${TIMESTAMP}.out"
echo ""
echo "========================================================================"
