#!/bin/bash
#SBATCH --job-name=native_roi
#SBATCH --output=logs/native_roi/native_roi_%A_%a.out
#SBATCH --error=logs/native_roi/native_roi_%A_%a.err
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --array=0-27  # 7 subjects × 4 ROIs = 28 jobs (0-27)

# ============================================================================
# SLURM batch script for native space ROI transformation and validation
# ============================================================================
#
# Purpose: Transform ROIs to native BOLD space and validate alignment
#
# This is independent of MNI registration quality and tests whether:
#   1. ROI can be properly fitted to individual anatomy
#   2. Functional analysis is possible in native space
#   3. Hyperalignment/Procrustes can proceed without MNI
#
# Array job configuration:
#   - 7 subjects: 01, 02, 03, 05, 06, 07, 08
#   - 4 ROIs: V1, V2, V3, hV4
#   - Total: 28 combinations
#
# Author: Created for native space validation
# Date: 2025-01-04
# ============================================================================

set -e

# ============================================================================
# Job Array Configuration
# ============================================================================

# Subject list (excluding sub-04 - no BOLD signal at V1)
SUBJECTS=(01 02 03 05 06 07 08)

# ROI list
ROIS=(V1 V2 V3 hV4)

# Calculate subject and ROI from array task ID
N_ROIS=${#ROIS[@]}
SUBJ_IDX=$((SLURM_ARRAY_TASK_ID / N_ROIS))
ROI_IDX=$((SLURM_ARRAY_TASK_ID % N_ROIS))

SUBJECT=${SUBJECTS[$SUBJ_IDX]}
ROI=${ROIS[$ROI_IDX]}

# Run number (can be modified to process multiple runs)
RUN=1

# ============================================================================
# Environment Setup
# ============================================================================

# Change to project directory FIRST (required for .bashrc)
cd /scratch/connectome/haba6030/colorBlind

# Create log directory
mkdir -p logs/native_roi

# Activate conda environment
source ~/.bashrc
conda activate nilearn

echo "================================================================================"
echo "SLURM Job: Native Space ROI Pipeline"
echo "================================================================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Array Task ID: ${SLURM_ARRAY_TASK_ID}"
echo "Node: ${SLURM_NODELIST}"
echo ""
echo "Configuration:"
echo "  Subject: sub-${SUBJECT}"
echo "  ROI: ${ROI}"
echo "  Run: ${RUN}"
echo ""
echo "Start time: $(date)"
echo "================================================================================"
echo ""

# ============================================================================
# Path Configuration
# ============================================================================

SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/scripts"

# ============================================================================
# Step 1: Transform ROI to native BOLD space
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Transforming ROI to native BOLD space"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bash "${SCRIPT_DIR}/transform_roi_to_native.sh" $SUBJECT $ROI $RUN

TRANSFORM_STATUS=$?

echo ""

# ============================================================================
# Step 2: Create detailed visualizations
# ============================================================================

if [ $TRANSFORM_STATUS -eq 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 2: Creating detailed visualizations"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    python "${SCRIPT_DIR}/visualize_native_roi.py" \
        --subject $SUBJECT \
        --roi $ROI \
        --run $RUN || echo "⚠ Visualization failed (non-critical)"

    echo ""
fi

# ============================================================================
# Step 3: Run functional sanity check
# ============================================================================

if [ $TRANSFORM_STATUS -eq 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step 3: Running functional sanity check"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    python "${SCRIPT_DIR}/sanity_check_native_roi.py" \
        --subject $SUBJECT \
        --roi $ROI \
        --run $RUN || echo "⚠ Functional check failed (non-critical)"

    echo ""
fi

# ============================================================================
# Summary
# ============================================================================

echo "================================================================================"
echo "Job Summary"
echo "================================================================================"
echo "Subject: sub-${SUBJECT}"
echo "ROI: ${ROI}"
echo "Run: ${RUN}"
echo ""

if [ $TRANSFORM_STATUS -eq 0 ]; then
    echo "✅ Transformation successful"
    echo ""
    echo "Output directory:"
    echo "  ${PROJECT_DIR}/derivatives/native_space_roi/sub-${SUBJECT}/"
else
    echo "❌ Transformation failed"
    echo "   Check logs for details"
fi

echo ""
echo "End time: $(date)"
echo "================================================================================"

exit $TRANSFORM_STATUS
