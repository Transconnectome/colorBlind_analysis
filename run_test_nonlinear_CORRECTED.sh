#!/bin/bash
#SBATCH --job-name=test_nonlinear_corrected
#SBATCH --nodelist=node2
#SBATCH --time=01:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=8
#SBATCH --output=logs/test_nonlinear_corrected_%j.out
#SBATCH --error=logs/test_nonlinear_corrected_%j.err

# ============================================================================
# SBATCH Script for Testing Nonlinear Forward Models (CORRECTED)
# ============================================================================
#
# Purpose: Test Linear, RF, and MLP forward models
# Baseline: visualize_Edits/fir_reconstruction_zScore.py
# Output: derivatives/{timestamp}/sub-{ID}/zScore_NONLINEAR/{ROI}_universal_hrf/
#
# Changes from previous version:
# - Corrected to match visualize_Edits baseline (not visualize_Edits_FIXED)
# - Correct output directory structure
# - Default PCA=6 (as per CLAUDE.md)
#
# Usage:
#   sbatch run_test_nonlinear_CORRECTED.sh
#
# ============================================================================

echo "=========================================="
echo "Nonlinear Forward Model Test (CORRECTED)"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Started: $(date)"
echo ""

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Check environment
echo "Python: $(which python)"
echo "Conda env: $CONDA_DEFAULT_ENV"
echo ""

# Move to working directory
cd /scratch/connectome/haba6030/colorBlind

# Create logs directory if needed
mkdir -p logs

# ============================================================================
# Test on sub-01, V2, PCA=6 (baseline comparison)
# ============================================================================

echo "Test: All models on sub-01/V2/PCA=6"
echo "===================================="
echo "Baseline: V2 6.09° (from ANALYSIS_SUMMARY_20251117)"
echo ""

python test_nonlinear_models_CORRECTED.py \
    --subject 01 \
    --roi V2 \
    --n-components 6 \
    --models linear rf mlp \
    --rf-n-estimators 100 \
    --rf-max-depth 5 \
    --rf-min-samples-leaf 3 \
    --mlp-n-hidden 12 \
    --mlp-learning-rate 0.001 \
    --mlp-weight-decay 0.05 \
    --mlp-dropout 0.3 \
    --mlp-n-epochs 100

echo ""
echo "Expected:"
echo "  Linear: ~6-20° (baseline)"
echo "  RF: Potentially better if nonlinearity helps"
echo "  MLP: Potentially better with smooth interpolation"
echo ""

# ============================================================================
# Summary
# ============================================================================

echo "=========================================="
echo "Test completed!"
echo "=========================================="
echo "Finished: $(date)"
echo ""

# Find the output directory
LATEST_DIR=$(ls -td derivatives/*/sub-01/zScore_NONLINEAR/V2_universal_hrf 2>/dev/null | head -1)

if [ -d "$LATEST_DIR" ]; then
    echo "Results saved in:"
    echo "  $LATEST_DIR"
    echo ""
    echo "Summary:"
    if [ -f "$LATEST_DIR/summary.csv" ]; then
        cat "$LATEST_DIR/summary.csv"
    fi
    echo ""
    echo "To download results:"
    echo "  scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/$LATEST_DIR ~/Desktop/"
else
    echo "WARNING: Output directory not found"
    echo "Check logs for errors"
fi

echo ""
echo "=========================================="
