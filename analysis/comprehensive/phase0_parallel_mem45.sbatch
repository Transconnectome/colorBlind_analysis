#!/bin/bash
#SBATCH --job-name=phase0_v3
#SBATCH --nodelist=node2
#SBATCH --qos=shared
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=45GB
#SBATCH --time=24:00:00
#SBATCH --array=1-10
#SBATCH --output=logs/phase0_v3_sub-%a_%A.out
#SBATCH --error=logs/phase0_v3_sub-%a_%A.err

# ============================================================================
# Phase 0: Subject-Parallel Baseline Analysis (Array Job)
# ============================================================================
#
# MEMORY OPTIMIZED VERSION (45GB per task)
# - Total: 45GB × 10 = 450GB < 452GB usable ✓
# - Prevents memory overcommit that caused "Duplicate jobid" error
#
# This script runs Phase 0 (ROI building + Baseline analysis) in parallel
# Each array task processes one subject with 4 ROIs sequentially
#
# SLURM Array Variables:
#   %a = SLURM_ARRAY_TASK_ID (1-10)
#   %A = SLURM_ARRAY_JOB_ID
#
# ============================================================================

# Cleanup function for safe exit
cleanup() {
    local exit_code=$1
    echo "Cleaning up (exit code: $exit_code)..."
    # Kill any remaining Python processes from this job
    pkill -P $$ python 2>/dev/null || true
    exit $exit_code
}

# Set up traps for safe cleanup
trap 'cleanup 1' SIGTERM SIGINT SIGKILL
trap 'cleanup $?' EXIT

echo "================================================================"
echo "Phase 0: Subject-Parallel Analysis - Array Task ${SLURM_ARRAY_TASK_ID}"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}"
echo "Task ID: ${SLURM_ARRAY_TASK_ID}"
echo "Memory: 45GB per task (optimized for node2)"
echo "Start: $(date)"
echo "================================================================"

# Configuration
DATASET="original_v3"
TIMESTAMP="baseline32_original_v3"
ALL_SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
ROIS=(V1 V2 V3 hV4)

# Get subject for this array task
SUBJECT=${ALL_SUBJECTS[$SLURM_ARRAY_TASK_ID-1]}

echo ""
echo "Processing Subject: sub-${SUBJECT}"
echo "ROIs: ${ROIS[@]}"
echo ""

# Baseline32 preprocessing parameters
SMOOTH=0
HIGHPASS="--highpass 0.01"
MOTION="cosine"
COMPCOR=""
DRIFT="none"
STANDARDIZE=""
USE_PCA="--use-pca"
N_COMPONENTS=30

# Paths
BASE_DIR=/scratch/connectome/haba6030/colorBlind
cd $BASE_DIR

# Create necessary directories
echo "Creating required directories..."
mkdir -p logs
mkdir -p derivatives/V3_Comprehensive/ROI_mask
mkdir -p derivatives/V3_Comprehensive/BH2009_original_v3
mkdir -p analysis/phase1_preprocess_decoding
mkdir -p analysis/utils

# Activate conda environment
echo "Activating conda environment..."
source ~/.bashrc
conda activate nilearn

# Verify conda activation
if [ $? -ne 0 ]; then
    echo "✗ ERROR: Failed to activate conda environment 'nilearn'"
    exit 1
fi

echo "✓ Conda environment activated: $(which python)"
echo ""

# ============================================================================
# Phase 0A: ROI Building (per subject)
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 0A: ROI Building for sub-${SUBJECT}"
echo "================================================================"
echo ""

# Build ROI masks for original_v3 dataset
# Output: derivatives/V3_Comprehensive/ROI_mask/sub-${SUBJECT}/roi_pipeline/
echo "Building ROI masks for sub-${SUBJECT}..."
python analysis/phase1_preprocess_decoding/roi_pipeline_comprehensive.py $SUBJECT

if [ $? -eq 0 ]; then
    echo "✓ ROI masks created for sub-${SUBJECT}"
    echo "  Output: derivatives/V3_Comprehensive/ROI_mask/sub-${SUBJECT}/roi_pipeline/"
else
    echo "✗ ROI building failed for sub-${SUBJECT}"
    echo "  Baseline analysis will attempt to use existing masks or fail gracefully"
    # Don't exit - let baseline try to find existing masks
fi

# ============================================================================
# Phase 0C: Baseline Reconstruction & Classification (4 ROIs)
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 0C: Baseline Analysis for sub-${SUBJECT}"
echo "================================================================"
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0
CONSECUTIVE_FAILS=0

for ROI in "${ROIS[@]}"; do
    echo ""
    echo "--- Processing: sub-${SUBJECT}, ROI ${ROI} ---"
    echo "Start: $(date '+%H:%M:%S')"

    python analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py \
        --subject $SUBJECT \
        --roi $ROI \
        --dataset $DATASET \
        --timestamp $TIMESTAMP \
        --smooth $SMOOTH \
        $HIGHPASS \
        --motion $MOTION \
        $COMPCOR \
        --drift $DRIFT \
        $STANDARDIZE \
        $USE_PCA \
        --n-components $N_COMPONENTS

    EXIT_CODE=$?
    echo "End: $(date '+%H:%M:%S')"

    if [ $EXIT_CODE -eq 0 ]; then
        echo "✓ Success: sub-${SUBJECT}, ROI ${ROI}"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        CONSECUTIVE_FAILS=0
    else
        echo "✗ Failed: sub-${SUBJECT}, ROI ${ROI} (exit code: ${EXIT_CODE})"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        CONSECUTIVE_FAILS=$((CONSECUTIVE_FAILS + 1))
        
        # Abort if 2 consecutive failures (likely systemic issue)
        if [ $CONSECUTIVE_FAILS -ge 2 ]; then
            echo ""
            echo "✗ ERROR: 2 consecutive ROI failures detected"
            echo "  Likely systemic issue (memory, data, environment)"
            echo "  Aborting remaining ROIs for sub-${SUBJECT}"
            break
        fi
    fi
done

echo ""
echo "================================================================"
echo "Summary for sub-${SUBJECT}"
echo "================================================================"
echo "  Successful: ${SUCCESS_COUNT}/4 ROIs"
echo "  Failed: ${FAIL_COUNT}/4 ROIs"
echo "  Completion time: $(date)"
echo "================================================================"

# Exit with appropriate code
if [ $FAIL_COUNT -gt 0 ]; then
    echo ""
    echo "⚠️  WARNING: Some ROIs failed for sub-${SUBJECT}"
    exit 1
else
    echo ""
    echo "✓ All ROIs completed successfully for sub-${SUBJECT}"
    exit 0
fi
