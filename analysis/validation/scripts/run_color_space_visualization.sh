#!/bin/bash
# Visualize color representational space per subject after SRM between-subject analysis

set -e

echo "=========================================="
echo "Color Space Visualization"
echo "=========================================="

# Configuration
SCRIPT_DIR="/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts"

# Check if results directory is provided
if [ $# -eq 0 ]; then
    echo "Usage: bash run_color_space_visualization.sh <results_directory>"
    echo ""
    echo "Example:"
    echo "  bash run_color_space_visualization.sh results/srm_between_subject/test_local_20260206_123456"
    echo ""
    echo "This script visualizes the 8-color representational space for each subject"
    echo "using MDS projection of RDMs computed from SRM-aligned amplitudes."
    exit 1
fi

RESULTS_DIR="$1"

if [ ! -d "${RESULTS_DIR}" ]; then
    echo "❌ Results directory not found: ${RESULTS_DIR}"
    exit 1
fi

echo ""
echo "Results directory: ${RESULTS_DIR}"
echo ""

# Activate conda environment
echo "Activating srm environment..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate srm

# Find all ROIs with results
ROIS=()
for roi in V1 V2 V3 hV4; do
    if [ -f "${RESULTS_DIR}/${roi}_srm_between_subject_results.json" ]; then
        ROIS+=("${roi}")
    fi
done

if [ ${#ROIS[@]} -eq 0 ]; then
    echo "❌ No SRM between-subject results found in ${RESULTS_DIR}"
    echo ""
    echo "Expected files: {ROI}_srm_between_subject_results.json"
    echo ""
    echo "Please run evaluate_srm_between_subject.py first."
    exit 1
fi

echo "Found results for ROIs: ${ROIS[@]}"
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0

for ROI in "${ROIS[@]}"; do
    echo "=========================================="
    echo "Visualizing: ${ROI}"
    echo "=========================================="
    echo ""

    python -u "${SCRIPT_DIR}/visualize_color_space_per_subject.py" \
        --roi "${ROI}" \
        --results-dir "${RESULTS_DIR}" \
        2>&1

    EXIT_CODE=$?

    if [ ${EXIT_CODE} -eq 0 ]; then
        echo ""
        echo "✓ ${ROI} visualization completed"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo ""
        echo "✗ ${ROI} visualization failed (exit code: ${EXIT_CODE})"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi

    echo ""
done

echo "=========================================="
echo "Visualization Summary"
echo "=========================================="
echo ""
echo "Successful: ${SUCCESS_COUNT}/${#ROIS[@]}"
echo "Failed: ${FAIL_COUNT}/${#ROIS[@]}"
echo ""

if [ ${SUCCESS_COUNT} -gt 0 ]; then
    echo "Output files:"
    ls -lh "${RESULTS_DIR}"/*_color_space*.png 2>/dev/null || echo "  (no color space plots found)"
    echo ""
    echo "View plots:"
    echo "  open ${RESULTS_DIR}/*_color_space*.png"
    echo ""
fi

if [ ${FAIL_COUNT} -eq 0 ]; then
    echo "✅ All visualizations completed successfully!"
else
    echo "⚠️  ${FAIL_COUNT} visualization(s) failed"
fi

echo "=========================================="
