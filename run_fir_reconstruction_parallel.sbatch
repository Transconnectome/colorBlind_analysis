#!/bin/bash
#SBATCH -J fir_recon_array
#SBATCH -c 4
#SBATCH --mem=64G
#SBATCH -t 10:00:00
#SBATCH -o logs/fir_recon_%A_%a.out
#SBATCH -e logs/fir_recon_%A_%a.err
#SBATCH --array=0-5
#SBATCH --nodelist=node2

# FIR Reconstruction Pipeline - Parallel Execution
# Runs multiple ROIs in parallel using job arrays

# ============================================================================
# Configuration
# ============================================================================

# ROIs to process (add more as needed)
ROIS=(
    "V1"
    "V2"
    "V3"
    "V4"
    "hV4"
    "VO1"
)

# PCA settings (set USE_PCA=0 to disable, 1 to enable)
USE_PCA=1
N_COMPONENTS=20

# Whether to save z-maps (can be slow and use disk space)
SAVE_ZMAPS=1

# ============================================================================
# Setup
# ============================================================================

# Get ROI for this array task
ROI=${ROIS[$SLURM_ARRAY_TASK_ID]}

echo "========================================================================"
echo "FIR Reconstruction - Array Job ${SLURM_ARRAY_TASK_ID}"
echo "========================================================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Array Job ID: ${SLURM_ARRAY_JOB_ID}"
echo "Array Task ID: ${SLURM_ARRAY_TASK_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "ROI: ${ROI}"
echo "Use PCA: ${USE_PCA}"
if [ $USE_PCA -eq 1 ]; then
    echo "PCA components: ${N_COMPONENTS}"
fi
echo "Save z-maps: ${SAVE_ZMAPS}"
echo "Working directory: $(pwd)"
echo "========================================================================"
echo

# Activate conda environment
echo "Activating nilearn environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate nilearn

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate nilearn environment"
    exit 1
fi

echo "Environment activated: $(which python)"
echo "Python version: $(python --version)"
echo

# Create logs directory
mkdir -p logs

# ============================================================================
# Run Analysis
# ============================================================================

echo "Starting FIR reconstruction for ROI: ${ROI}"
echo "Start time: $(date)"
echo

# Build command
CMD="python fir_reconstruction.py --roi ${ROI}"

if [ $USE_PCA -eq 1 ]; then
    CMD="${CMD} --use-pca --n-components ${N_COMPONENTS}"
fi

if [ $SAVE_ZMAPS -eq 1 ]; then
    CMD="${CMD} --save-zmaps"
fi

echo "Command: ${CMD}"
echo

# Run the analysis
${CMD}

EXIT_CODE=$?

echo
echo "Exit code: ${EXIT_CODE}"
echo "End time: $(date)"
echo

if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ ${ROI} completed successfully"

    # Show quick results
    echo
    echo "========================================================================"
    echo "Quick Results for ${ROI}:"
    echo "========================================================================"
    SUMMARY_FILE="derivatives/sub-01/fir_reconstruction/${ROI}/summary.csv"
    if [ -f "${SUMMARY_FILE}" ]; then
        cat ${SUMMARY_FILE}
    fi
else
    echo "❌ ${ROI} failed with exit code ${EXIT_CODE}"
    echo
    echo "Check error log: logs/fir_recon_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.err"
fi

echo "========================================================================"

exit ${EXIT_CODE}
