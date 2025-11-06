#!/bin/bash
#SBATCH -J fir_universal
#SBATCH -c 4
#SBATCH --mem=64G
#SBATCH -t 10:00:00
#SBATCH -o logs/fir_universal_%j.out
#SBATCH -e logs/fir_universal_%j.err
#SBATCH --nodelist=node2

# FIR Reconstruction with UNIVERSAL HRF (B&H 2009 Method)
# This uses averaged HRF across voxels to determine optimal delay
# Provides maximum parameter reduction: 3,100 → 10 HRF parameters

# ============================================================================
# Configuration
# ============================================================================

# ROI to process (can be overridden with: sbatch --export=ROI=V1 ...)
ROI=${ROI:-"V2"}

# PCA settings (can be overridden with: sbatch --export=USE_PCA=1,N_COMPONENTS=10 ...)
USE_PCA=${USE_PCA:-1}
N_COMPONENTS=${N_COMPONENTS:-20}

# Whether to save z-maps
SAVE_ZMAPS=${SAVE_ZMAPS:-1}

# ============================================================================
# Setup
# ============================================================================

echo "========================================================================"
echo "FIR Reconstruction - UNIVERSAL HRF (B&H 2009 Method)"
echo "========================================================================"
echo "Job ID: ${SLURM_JOB_ID}"
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

echo "Starting UNIVERSAL HRF FIR reconstruction for ROI: ${ROI}"
echo "Start time: $(date)"
echo

# Build command
CMD="python fir_reconstruction_universal_hrf.py --roi ${ROI}"

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
    echo "Quick Results for ${ROI} (UNIVERSAL HRF):"
    echo "========================================================================"
    SUMMARY_FILE="derivatives/sub-01/fir_reconstruction/${ROI}_universal_hrf/summary.csv"
    if [ -f "${SUMMARY_FILE}" ]; then
        cat ${SUMMARY_FILE}
    fi
else
    echo "❌ ${ROI} failed with exit code ${EXIT_CODE}"
    echo
    echo "Check error log: logs/fir_universal_${SLURM_JOB_ID}.err"
fi

echo "========================================================================"

exit ${EXIT_CODE}
