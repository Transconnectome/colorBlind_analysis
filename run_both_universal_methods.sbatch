#!/bin/bash
#SBATCH -J both_universal
#SBATCH -c 8
#SBATCH --mem=128G
#SBATCH -t 20:00:00
#SBATCH -o logs/both_universal_%j.out
#SBATCH -e logs/both_universal_%j.err
#SBATCH --nodelist=node2

# Run BOTH universal HRF methods in parallel for comparison
# 1. Quick fix (corrected delay selection)
# 2. True paper method (GLM with universal HRF basis)

# ============================================================================
# Configuration
# ============================================================================

ROI=${ROI:-"V2"}
USE_PCA=${USE_PCA:-1}
N_COMPONENTS=${N_COMPONENTS:-20}
SAVE_ZMAPS=${SAVE_ZMAPS:-1}

# ============================================================================
# Setup
# ============================================================================

echo "========================================================================"
echo "Running BOTH Universal HRF Methods in Parallel"
echo "========================================================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "ROI: ${ROI}"
echo "========================================================================"
echo

# Activate conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate nilearn

mkdir -p logs

# ============================================================================
# Method 1: Quick Fix (Corrected Delay Selection)
# ============================================================================

echo "Starting Method 1: Quick Fix..."
echo "Time: $(date)"

CMD1="python fir_reconstruction_universal_hrf.py --roi ${ROI}"
if [ $USE_PCA -eq 1 ]; then
    CMD1="${CMD1} --use-pca --n-components ${N_COMPONENTS}"
fi
if [ $SAVE_ZMAPS -eq 1 ]; then
    CMD1="${CMD1} --save-zmaps"
fi

${CMD1} &
PID1=$!

echo "Method 1 started (PID: $PID1)"

# ============================================================================
# Method 2: True Paper Method (GLM with Universal HRF)
# ============================================================================

echo "Starting Method 2: True Paper Method..."
echo "Time: $(date)"

CMD2="python fir_reconstruction_true_paper.py --roi ${ROI}"
if [ $USE_PCA -eq 1 ]; then
    CMD2="${CMD2} --use-pca --n-components ${N_COMPONENTS}"
fi
if [ $SAVE_ZMAPS -eq 1 ]; then
    CMD2="${CMD2} --save-zmaps"
fi

${CMD2} &
PID2=$!

echo "Method 2 started (PID: $PID2)"

# ============================================================================
# Wait for both to complete
# ============================================================================

echo
echo "Waiting for both methods to complete..."
echo

wait $PID1
EXIT1=$?
echo "Method 1 (Quick Fix) completed with exit code: $EXIT1"

wait $PID2
EXIT2=$?
echo "Method 2 (True Paper) completed with exit code: $EXIT2"

# ============================================================================
# Compare Results
# ============================================================================

echo
echo "========================================================================"
echo "RESULTS COMPARISON"
echo "========================================================================"
echo

echo "Method 1 (Quick Fix - Corrected Delay):"
if [ -f "derivatives/sub-01/fir_reconstruction/${ROI}_universal_hrf/summary.csv" ]; then
    cat "derivatives/sub-01/fir_reconstruction/${ROI}_universal_hrf/summary.csv"
fi

echo
echo "Method 2 (True Paper - GLM Basis):"
if [ -f "derivatives/sub-01/fir_reconstruction/${ROI}_true_paper/summary.csv" ]; then
    cat "derivatives/sub-01/fir_reconstruction/${ROI}_true_paper/summary.csv"
fi

echo
echo "========================================================================"
echo "End time: $(date)"
echo "========================================================================"

exit 0
