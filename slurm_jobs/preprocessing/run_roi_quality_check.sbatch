#!/bin/bash
#SBATCH --job-name=roi_quality_check
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=logs/roi_quality_check.out
#SBATCH --error=logs/roi_quality_check.err

# ROI Quality Check: Compare deoblique_v2 vs original_v3
#
# Checks if sub-01 and sub-04 issues are present in both versions
#
# Usage:
#   sbatch run_roi_quality_check.sbatch

set -e

echo "========================================="
echo "ROI Quality Comparison"
echo "========================================="
echo "Date:     $(date)"
echo "Node:     $(hostname)"
echo "========================================="
echo ""

# Paths
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind"
cd ${SCRIPT_DIR}

# Activate conda
echo "🔧 Activating conda environment..."
source ~/.bashrc
conda activate nilearn

# Check script exists
if [ ! -f "check_roi_quality_comparison.py" ]; then
    echo "❌ ERROR: check_roi_quality_comparison.py not found"
    echo "   Please upload the script first"
    exit 1
fi

# Run comparison
echo "🔍 Running ROI quality comparison..."
echo ""

python check_roi_quality_comparison.py

EXIT_CODE=$?

echo ""
echo "========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Comparison completed successfully"
else
    echo "❌ Comparison failed with exit code: $EXIT_CODE"
fi
echo "========================================="

exit $EXIT_CODE
