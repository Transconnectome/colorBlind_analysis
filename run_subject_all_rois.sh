#!/bin/bash
################################################################################
# run_subject_all_rois.sh
################################################################################
#
# SLURM script to process ALL ROIs for ONE subject
#
# Arguments:
#   $1: SUBJECT (P01, 01, 02, 03, 04)
#   $2: TIMESTAMP (e.g., 20250117_143022)
#   $3: METHOD (universal_hrf, zScore, voxelSelect)
#   $4: EXTRA_ARGS (e.g., "--use-pca --n-components 6")
#
# Usage (called by run_all_subjects.sh):
#   sbatch run_subject_all_rois.sh 01 20250117_143022 universal_hrf "--use-pca --n-components 6"
#
################################################################################

#SBATCH --job-name=recon_subject
#SBATCH --time=08:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --nodelist=node2

# Parse arguments
SUBJECT=$1
TIMESTAMP=$2
METHOD=${3:-universal_hrf}
EXTRA_ARGS=${4:-""}

# Set up log directory
if [ "$SUBJECT" == "P01" ]; then
    LOG_DIR="logs/pilot"
    SUBJECT_NAME="pilot (P01)"
else
    LOG_DIR="logs/sub-${SUBJECT}"
    SUBJECT_NAME="sub-${SUBJECT}"
fi

mkdir -p $LOG_DIR

# Set up output/error files
exec 1> >(tee "${LOG_DIR}/reconstruction_${TIMESTAMP}.out")
exec 2> >(tee "${LOG_DIR}/reconstruction_${TIMESTAMP}.err" >&2)

# Activate conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate nilearn

# Change to working directory
cd /scratch/connectome/haba6030/colorBlind

# Determine script to run based on method
case $METHOD in
    universal_hrf)
        SCRIPT="visualize_Edits/fir_reconstruction_universal_hrf.py"
        ;;
    zScore)
        SCRIPT="visualize_Edits/fir_reconstruction_zScore.py"
        ;;
    voxelSelect)
        SCRIPT="visualize_Edits/fir_reconstruction_zScore_voxelSelect.py"
        ;;
    *)
        echo "ERROR: Unknown method '$METHOD'"
        echo "Valid methods: universal_hrf, zScore, voxelSelect"
        exit 1
        ;;
esac

# Log header
echo "========================================================================"
echo "Reconstruction Job - All ROIs for $SUBJECT_NAME"
echo "========================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Job name: $SLURM_JOB_NAME"
echo "Node: $SLURMD_NODENAME"
echo "------------------------------------------------------------------------"
echo "Subject: $SUBJECT"
echo "Timestamp: $TIMESTAMP"
echo "Method: $METHOD"
echo "Script: $SCRIPT"
echo "Extra arguments: $EXTRA_ARGS"
echo "------------------------------------------------------------------------"
echo "Processing ROIs: V1, V2, V3, hV4"
echo "Output directory: derivatives/$TIMESTAMP/"
echo "Log directory: $LOG_DIR/"
echo "------------------------------------------------------------------------"
echo "Start time: $(date)"
echo "========================================================================"
echo ""

# ROIs to process
ROIS=(V1 V2 V3 hV4)
FAILED_ROIS=()
SUCCESS_COUNT=0
FAIL_COUNT=0

# Process each ROI sequentially
for ROI in "${ROIS[@]}"; do
    echo ""
    echo "========================================================================"
    echo "[$((SUCCESS_COUNT + FAIL_COUNT + 1))/4] Processing ROI: $ROI"
    echo "========================================================================"
    echo "Start time: $(date)"
    echo ""

    # Run reconstruction
    python $SCRIPT \
        --subject $SUBJECT \
        --roi $ROI \
        --timestamp $TIMESTAMP \
        $EXTRA_ARGS

    # Check exit status
    EXIT_CODE=$?

    echo ""
    echo "------------------------------------------------------------------------"
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✓ $ROI completed successfully!"
        ((SUCCESS_COUNT++))
    else
        echo "✗ $ROI failed with exit code: $EXIT_CODE"
        FAILED_ROIS+=($ROI)
        ((FAIL_COUNT++))
    fi
    echo "End time: $(date)"
    echo "------------------------------------------------------------------------"
done

# Final summary
echo ""
echo "========================================================================"
echo "FINAL SUMMARY - $SUBJECT_NAME"
echo "========================================================================"
echo "Total ROIs processed: 4"
echo "Successful: $SUCCESS_COUNT"
echo "Failed: $FAIL_COUNT"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "✓ All ROIs completed successfully!"
    echo ""
    echo "Results saved to:"
    echo "  derivatives/$TIMESTAMP/$SUBJECT_NAME/"
    FINAL_EXIT=0
else
    echo "✗ Some ROIs failed:"
    for ROI in "${FAILED_ROIS[@]}"; do
        echo "  - $ROI"
    done
    echo ""
    echo "Check logs in: $LOG_DIR/reconstruction_${TIMESTAMP}.err"
    FINAL_EXIT=1
fi

echo ""
echo "Job end time: $(date)"
echo "========================================================================"

exit $FINAL_EXIT
