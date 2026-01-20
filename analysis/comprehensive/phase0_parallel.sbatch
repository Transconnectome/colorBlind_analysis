#!/bin/bash
#SBATCH --job-name=phase0_v3
#SBATCH --nodelist=node2
#SBATCH --qos=shared
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64GB
#SBATCH --time=24:00:00
#SBATCH --array=1-10
#SBATCH --output=logs/phase0_v3_sub-%a_%A.out
#SBATCH --error=logs/phase0_v3_sub-%a_%A.err

# ============================================================================
# Phase 0: Subject-Parallel Baseline Analysis (Array Job)
# ============================================================================
#
# This script runs Phase 0 (ROI building + Baseline analysis) in parallel
# Each array task processes one subject with 4 ROIs sequentially
#
# SLURM Array Variables:
#   %a = SLURM_ARRAY_TASK_ID (1-10)
#   %A = SLURM_ARRAY_JOB_ID
#
# ============================================================================

echo "================================================================"
echo "Phase 0: Subject-Parallel Analysis - Array Task ${SLURM_ARRAY_TASK_ID}"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}"
echo "Task ID: ${SLURM_ARRAY_TASK_ID}"
echo "Start: $(date)"
echo "================================================================"

# Configuration - Dataset-Agnostic (accepts arguments)
DATASET="${1:-original_v3}"
TIMESTAMP="${2:-baseline32_${DATASET}}"
ALL_SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
ROIS=(V1 V2 V3 hV4)

echo "Dataset: ${DATASET}"
echo "Timestamp: ${TIMESTAMP}"

# Validate dataset
case $DATASET in
    original_v3|method3_header_mi|deoblique_v2)
        echo "✓ Valid dataset: ${DATASET}"
        ;;
    *)
        echo "ERROR: Invalid dataset '${DATASET}'"
        echo "Valid: original_v3, method3_header_mi, deoblique_v2"
        exit 1
        ;;
esac

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

# ============================================================================
# Phase 0A: ROI Building (per subject)
# ============================================================================
echo ""
echo "================================================================"
echo "PHASE 0A: ROI Building for sub-${SUBJECT}"
echo "================================================================"
echo ""

# Build ROI masks for specified dataset
# Output: derivatives/V3_Comprehensive/ROI_mask/sub-${SUBJECT}/roi_pipeline/
echo "Building ROI masks for sub-${SUBJECT} with dataset ${DATASET}..."
python analysis/phase1_preprocess_decoding/roi_pipeline_selected_1202used.py $SUBJECT --dataset $DATASET

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
    else
        echo "✗ Failed: sub-${SUBJECT}, ROI ${ROI} (exit code: ${EXIT_CODE})"
        FAIL_COUNT=$((FAIL_COUNT + 1))
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

exit 0
