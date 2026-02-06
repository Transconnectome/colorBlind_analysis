#!/bin/bash
# Quick test script for between-subject Procrustes with ANOVA selection
# Tests single ROI (V1) with k=50

set -e  # Exit on error

echo "=================================="
echo "Quick Test: Between-Subject Procrustes"
echo "=================================="
echo ""

# Activate conda environment
if [ -z "$CONDA_DEFAULT_ENV" ] || [ "$CONDA_DEFAULT_ENV" != "nilearn" ]; then
    echo "Activating nilearn conda environment..."
    conda activate nilearn
fi

# Navigate to script directory
cd "$(dirname "$0")"

# Run test
echo "Running test with V1, k=50..."
python run_pipeline_local.py --roi V1 --test-mode

echo ""
echo "✅ Test completed!"
echo "Check results in: results/"
