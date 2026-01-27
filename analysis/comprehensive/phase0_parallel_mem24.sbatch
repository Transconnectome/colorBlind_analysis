#!/bin/bash
#SBATCH --job-name=phase0_m3_24G
#SBATCH --nodelist=node2,node4
#SBATCH --qos=shared
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=24GB
#SBATCH --time=24:00:00
#SBATCH --array=1-10
#SBATCH --no-requeue
#SBATCH --open-mode=append
#SBATCH --output=analysis/comprehensive/logs/phase0_m3_24G_sub-%a_%A.out
#SBATCH --error=analysis/comprehensive/logs/phase0_m3_24G_sub-%a_%A.err

# ============================================================================
# Phase 0: Subject-Parallel Baseline Analysis (Array Job)
# ============================================================================
#
# MEMORY OPTIMIZED VERSION (24GB per task)
# - Total: 24GB × 10 = 240GB < 452GB usable ✓
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
echo "Memory: 24GB per task (max 10 concurrent)"
echo "Node: node2 or node4"
echo "Dataset: method3_header_mi"
echo "Start: $(date)"
echo "================================================================"

# Configuration
DATASET="method3_header_mi"
TIMESTAMP="baseline32_method3_header_mi"
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
mkdir -p analysis/roi_masks/${DATASET}
mkdir -p analysis/phase1_preprocess_decoding/${DATASET}/results/baseline_decoding
mkdir -p analysis/phase1_preprocess_decoding/${DATASET}/logs
mkdir -p analysis/utils

# Activate conda environment
echo "Activating conda environment..."

# Initialize conda for this script (if not already initialized)
eval "$(conda shell.bash hook)"
conda activate nilearn

# Verify conda activation
if [ $? -ne 0 ]; then
    echo "✗ ERROR: Failed to activate conda environment 'nilearn'"
    exit 1
fi

echo "✓ Conda environment activated: $(which python)"
echo "Python version: $(python --version)"
echo ""

# ============================================================================
# Phase 0A: ROI Building (per subject)
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 0A: ROI Building for sub-${SUBJECT}"
echo "================================================================"
echo ""

# Build ROI masks for method3_header_mi dataset
# Output: analysis/roi_masks/method3_header_mi/sub-${SUBJECT}/roi_pipeline/
echo "Building ROI masks for sub-${SUBJECT}..."
echo "Dataset: ${DATASET}"
echo "fMRIPrep directory: /storage/connectome/haba6030/fmriprep_out_${DATASET}"
echo "ROI masks output: analysis/roi_masks/${DATASET}/"
echo "Logs output: analysis/phase1_preprocess_decoding/${DATASET}/logs/"
echo ""

python analysis/phase1_preprocess_decoding/roi_pipeline_selected_1202used.py $SUBJECT --dataset $DATASET

if [ $? -eq 0 ]; then
    echo "✓ ROI masks created for sub-${SUBJECT}"
    echo "  Output: analysis/roi_masks/${DATASET}/sub-${SUBJECT}/roi_pipeline/"
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
