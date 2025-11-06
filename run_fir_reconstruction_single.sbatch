#!/bin/bash
#SBATCH -J fir_recon
#SBATCH -c 4
#SBATCH --mem=64G
#SBATCH -t 10:00:00
#SBATCH -o logs/fir_recon_%j.out
#SBATCH -e logs/fir_recon_%j.err
#SBATCH --nodelist=node2

# FIR Reconstruction Pipeline - Single ROI
# Usage: sbatch --export=ROI=V2,USE_PCA=1,N_COMPONENTS=20 run_fir_reconstruction_single.sbatch

# ============================================================================
# Configuration (can be overridden with --export)
# ============================================================================

# Default values if not provided via --export
: ${ROI:=V2}
: ${USE_PCA:=1}
: ${N_COMPONENTS:=20}
: ${SAVE_ZMAPS:=1}

# ============================================================================
# Setup
# ============================================================================

echo "========================================================================"
echo "FIR Reconstruction - Single ROI"
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
    echo "Quick Results:"
    echo "========================================================================"
    SUMMARY_FILE="derivatives/sub-01/fir_reconstruction/${ROI}/summary.csv"
    if [ -f "${SUMMARY_FILE}" ]; then
        cat ${SUMMARY_FILE}
    else
        echo "Warning: Summary file not found at ${SUMMARY_FILE}"
    fi
else
    echo "❌ ${ROI} failed with exit code ${EXIT_CODE}"
    echo
    echo "Check error log for details:"
    echo "  logs/fir_recon_${SLURM_JOB_ID}.err"
    echo
    echo "Check analysis log for details:"
    echo "  derivatives/sub-01/fir_reconstruction/${ROI}/log.txt"
fi

echo "========================================================================"

exit ${EXIT_CODE}
