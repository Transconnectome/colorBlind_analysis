#!/bin/bash
#
# Run complete native space ROI pipeline for a single subject
#
# This script runs all steps of the native space ROI validation:
#   1. Transform ROI to native BOLD space
#   2. Create detailed visualizations
#   3. Run functional sanity check
#
# Usage: bash run_native_roi_pipeline.sh <subject_id> <roi_name> [run]
#
# Example: bash run_native_roi_pipeline.sh 02 V1 1

set -e

if [ $# -lt 2 ]; then
    echo "Usage: $0 <subject_id> <roi_name> [run]"
    echo ""
    echo "Arguments:"
    echo "  subject_id  : Subject ID (e.g., 02, 03, 05)"
    echo "  roi_name    : ROI name (V1, V2, V3, hV4)"
    echo "  run         : Run number (default: 1)"
    echo ""
    echo "Example:"
    echo "  $0 02 V1 1"
    exit 1
fi

SUBJECT=$1
ROI=$2
RUN=${3:-1}

# ============================================================================
# Environment Setup
# ============================================================================

# Change to project directory FIRST (required for .bashrc)
PROJECT_DIR="/scratch/connectome/haba6030/colorBlind"
cd "$PROJECT_DIR"

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Script directory
SCRIPT_DIR="${PROJECT_DIR}/scripts"

echo "================================================================================"
echo "Native Space ROI Pipeline"
echo "================================================================================"
echo "Subject: sub-${SUBJECT}"
echo "ROI: ${ROI}"
echo "Run: ${RUN}"
echo "Project directory: ${PROJECT_DIR}"
echo ""

# ============================================================================
# Step 1: Transform ROI to native BOLD space
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 1: Transforming ROI to native BOLD space"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

bash "${SCRIPT_DIR}/transform_roi_to_native.sh" $SUBJECT $ROI $RUN

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ ROI transformation failed"
    exit 1
fi

echo ""

# ============================================================================
# Step 2: Create detailed visualizations
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 2: Creating detailed visualizations"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python "${SCRIPT_DIR}/visualize_native_roi.py" \
    --subject $SUBJECT \
    --roi $ROI \
    --run $RUN

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠ Visualization failed (non-critical)"
fi

echo ""

# ============================================================================
# Step 3: Run functional sanity check
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 3: Running functional sanity check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

python "${SCRIPT_DIR}/sanity_check_native_roi.py" \
    --subject $SUBJECT \
    --roi $ROI \
    --run $RUN

if [ $? -ne 0 ]; then
    echo ""
    echo "⚠ Functional check failed (non-critical)"
fi

echo ""

# ============================================================================
# Summary
# ============================================================================

echo "================================================================================"
echo "Pipeline Complete"
echo "================================================================================"
echo ""
echo "Output directory:"
echo "  /scratch/connectome/haba6030/colorBlind/derivatives/native_space_roi/sub-${SUBJECT}/"
echo ""
echo "Next steps:"
echo "  1. Review QC images:"
echo "     - QC_sub-${SUBJECT}_${ROI}_run-${RUN}_overlay.png"
echo "     - QC_sub-${SUBJECT}_${ROI}_run-${RUN}_detailed.png"
echo "  2. Check functional diagnostics:"
echo "     - sanity_check_sub-${SUBJECT}_${ROI}_run-${RUN}.png"
echo "  3. If ROI location is correct, proceed with analysis in native space"
echo ""
echo "✓ All steps completed"
