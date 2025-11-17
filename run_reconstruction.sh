#!/bin/bash
################################################################################
# run_reconstruction.sh
################################################################################
#
# SLURM script for individual reconstruction job
#
# Arguments:
#   $1: SUBJECT (P01, 01, 02, 03, 04)
#   $2: ROI (V1, V2, V3, hV4)
#   $3: TIMESTAMP (e.g., 20250116_143022)
#   $4: METHOD (universal_hrf, zScore, voxelSelect)
#   $5: EXTRA_ARGS (e.g., "--use-pca --n-components 6")
#
# Usage (called by run_all_subjects_rois.sh):
#   sbatch run_reconstruction.sh P01 V2 20250116_143022 universal_hrf "--use-pca --n-components 6"
#
################################################################################

#SBATCH --job-name=reconstruction
#SBATCH --output=logs/slurm_%x_%j.out
#SBATCH --error=logs/slurm_%x_%j.err
#SBATCH --time=02:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=2
#SBATCH --nodelist=node2

# Parse arguments
SUBJECT=$1
ROI=$2
TIMESTAMP=$3
METHOD=${4:-universal_hrf}
EXTRA_ARGS=${5:-""}

# Activate conda environment (using dynamic conda path detection)
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

# Log information
echo "========================================================================"
echo "Reconstruction Job"
echo "========================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Job name: $SLURM_JOB_NAME"
echo "Node: $SLURMD_NODENAME"
echo "------------------------------------------------------------------------"
echo "Subject: $SUBJECT"
echo "ROI: $ROI"
echo "Timestamp: $TIMESTAMP"
echo "Method: $METHOD"
echo "Script: $SCRIPT"
echo "Extra arguments: $EXTRA_ARGS"
echo "------------------------------------------------------------------------"
echo "Output directory:"
echo "  derivatives/$TIMESTAMP/sub-$SUBJECT/fir_reconstruction_uni_hrf/"
echo "========================================================================"
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
echo "========================================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "Job completed successfully!"
    echo "Results saved to: derivatives/$TIMESTAMP/sub-$SUBJECT/"
else
    echo "Job failed with exit code: $EXIT_CODE"
fi
echo "========================================================================"

exit $EXIT_CODE
