#!/bin/bash
#SBATCH --job-name=test_nonlinear
#SBATCH --nodelist=node2
#SBATCH --time=01:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=8
#SBATCH --output=logs/test_nonlinear_%j.out
#SBATCH --error=logs/test_nonlinear_%j.err

# ============================================================================
# SBATCH Script for Testing Nonlinear Forward Models
# ============================================================================
#
# Purpose: Test Linear, RF, and MLP forward models on best baseline
# Baseline: sub-01, V2, PCA=6 (6.09° reconstruction error)
#
# Usage:
#   sbatch run_test_nonlinear.sh
#
# Expected time: ~15-20 minutes
# Expected output: test_results_nonlinear/sub-01_V2/
#
# ============================================================================

echo "=========================================="
echo "Nonlinear Forward Model Test"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Started: $(date)"
echo ""

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Check conda environment
echo "Python: $(which python)"
echo "Conda env: $CONDA_DEFAULT_ENV"
echo ""

# Move to working directory
cd /scratch/connectome/haba6030/colorBlind

# Create logs directory if needed
mkdir -p logs

# ============================================================================
# Test 1: Linear baseline (quick validation)
# ============================================================================

echo "Test 1: Linear baseline (validation)"
echo "------------------------------------"

python test_nonlinear_models.py \
    --subject 01 \
    --roi V2 \
    --n-components 6 \
    --models linear \
    --output-dir test_results_nonlinear/test1_linear

echo ""
echo "Expected: ~6-20° error (V2 baseline)"
echo ""

# ============================================================================
# Test 2: RF vs Linear
# ============================================================================

echo "Test 2: Random Forest vs Linear"
echo "--------------------------------"

python test_nonlinear_models.py \
    --subject 01 \
    --roi V2 \
    --n-components 6 \
    --models linear rf \
    --rf-n-estimators 100 \
    --rf-max-depth 5 \
    --rf-min-samples-leaf 3 \
    --output-dir test_results_nonlinear/test2_rf_vs_linear

echo ""
echo "Expected: RF < Linear if nonlinearity helps"
echo ""

# ============================================================================
# Test 3: MLP vs Linear
# ============================================================================

echo "Test 3: Light MLP vs Linear"
echo "----------------------------"

python test_nonlinear_models.py \
    --subject 01 \
    --roi V2 \
    --n-components 6 \
    --models linear mlp \
    --mlp-n-hidden 12 \
    --mlp-learning-rate 0.001 \
    --mlp-weight-decay 0.05 \
    --mlp-dropout 0.3 \
    --mlp-n-epochs 100 \
    --output-dir test_results_nonlinear/test3_mlp_vs_linear

echo ""
echo "Expected: MLP < Linear if smooth interpolation helps"
echo ""

# ============================================================================
# Test 4: Full comparison (all models)
# ============================================================================

echo "Test 4: Full comparison (Linear, RF, MLP)"
echo "------------------------------------------"

python test_nonlinear_models.py \
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
    --mlp-n-epochs 100 \
    --output-dir test_results_nonlinear/test4_full_comparison

echo ""
echo "Expected: Best model < 6° (improvement over baseline)"
echo ""

# ============================================================================
# Summary
# ============================================================================

echo "=========================================="
echo "All tests completed!"
echo "=========================================="
echo "Finished: $(date)"
echo ""
echo "Results saved in:"
echo "  test_results_nonlinear/"
echo ""
echo "To download results:"
echo "  scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/test_results_nonlinear ~/Desktop/"
echo ""
echo "To view summaries:"
echo "  cat test_results_nonlinear/*/summary.csv"
echo ""

# ============================================================================
# Quick Results Summary
# ============================================================================

echo "Quick Results Summary:"
echo "====================="
echo ""

for test_dir in test_results_nonlinear/test*; do
    if [ -d "$test_dir" ]; then
        echo "$(basename $test_dir):"
        if [ -f "$test_dir/sub-01_V2/summary.csv" ]; then
            cat "$test_dir/sub-01_V2/summary.csv"
        fi
        echo ""
    fi
done

echo "=========================================="
