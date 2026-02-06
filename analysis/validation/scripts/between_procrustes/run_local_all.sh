#!/bin/bash
# Full analysis script for between-subject Procrustes with ANOVA selection
# Runs all ROIs with multiple k values

set -e  # Exit on error

echo "=================================="
echo "Full Analysis: Between-Subject Procrustes"
echo "=================================="
echo ""

# Activate conda environment
if [ -z "$CONDA_DEFAULT_ENV" ] || [ "$CONDA_DEFAULT_ENV" != "nilearn" ]; then
    echo "Activating nilearn conda environment..."
    conda activate nilearn
fi

# Navigate to script directory
cd "$(dirname "$0")"

# ROIs to process
ROIS=(V1 V2 V3 hV4)

# k values to test
K_VALUES="20 50 100"

# Run analysis for each ROI
for ROI in "${ROIS[@]}"; do
    echo ""
    echo "=================================="
    echo "Processing ROI: $ROI"
    echo "=================================="
    echo ""

    python run_pipeline_local.py \
        --roi "$ROI" \
        --k-values $K_VALUES

    echo ""
    echo "✅ Completed $ROI"
done

echo ""
echo "=================================="
echo "✅ All ROIs completed!"
echo "=================================="
echo "Check results in: results/"
