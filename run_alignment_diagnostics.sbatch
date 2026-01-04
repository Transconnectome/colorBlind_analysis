#!/bin/bash
#SBATCH --job-name=align_diag
#SBATCH --nodelist=node2
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8GB
#SBATCH --time=0:30:00
#SBATCH --output=logs/alignment_diagnostics_%j.out
#SBATCH --error=logs/alignment_diagnostics_%j.err

# ============================================================================
# ROI Alignment Diagnostics - Problem Subjects
# ============================================================================
#
# Investigates WHY mask=func fails for sub-02, 03, 04, 09, 10
# Checks:
#   - BOLDREF vs Atlas affine match
#   - Brain mask coverage (especially posterior/visual cortex)
#   - Atlas vs brain mask spatial overlap
#   - Generated ROI mask locations
#
# ============================================================================

echo "================================================================"
echo "ROI Alignment Diagnostics"
echo "Start: $(date)"
echo "================================================================"

# Create log directory
mkdir -p logs

# Activate conda environment
echo ""
echo "Activating conda environment..."
source ~/.bashrc
conda activate nilearn

# Run diagnostics
echo ""
echo "Running alignment diagnostics..."
echo ""

python diagnose_alignment_per_subject.py

EXIT_CODE=$?

echo ""
echo "================================================================"
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Diagnostics completed successfully"
else
    echo "✗ Diagnostics failed (exit code: ${EXIT_CODE})"
fi
echo "Completion time: $(date)"
echo "================================================================"

exit $EXIT_CODE
