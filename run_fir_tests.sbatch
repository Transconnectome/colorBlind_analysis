#!/bin/bash
#SBATCH --job-name=fir_tests
#SBATCH --output=logs/fir_tests_%j.out
#SBATCH --error=logs/fir_tests_%j.err
#SBATCH --time=01:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --partition=batch

# FIR Model Testing: Both approaches
# Option A: Feature Selection + Regularization
# Option B: Diagonal LDA (Paper Method)

echo "========================================================================"
echo "FIR Testing Job Started: $(date)"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "========================================================================"
echo

# Activate conda environment
echo "Activating nilearn environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate nilearn
echo "Environment activated: $(which python)"
echo

# Create logs directory if it doesn't exist
mkdir -p logs

# Timestamp for output files
TIMESTAMP=$(date +%s)

echo "========================================================================"
echo "OPTION A: Feature Selection + Regularization"
echo "========================================================================"
echo "Start time: $(date)"
echo "Output: logs/fir_regularized_${TIMESTAMP}.out"
echo

python fir_test_regularized.py > logs/fir_regularized_${TIMESTAMP}.out 2>&1
EXIT_CODE_A=$?

echo "Exit code: $EXIT_CODE_A"
echo "End time: $(date)"
echo

if [ $EXIT_CODE_A -eq 0 ]; then
    echo "✅ Option A completed successfully"
else
    echo "❌ Option A failed with exit code $EXIT_CODE_A"
fi
echo

echo "========================================================================"
echo "OPTION B+C: Diagonal LDA (Paper Method)"
echo "========================================================================"
echo "Start time: $(date)"
echo "Output: logs/fir_diagonal_lda_${TIMESTAMP}.out"
echo

python fir_test_diagonal_lda.py > logs/fir_diagonal_lda_${TIMESTAMP}.out 2>&1
EXIT_CODE_B=$?

echo "Exit code: $EXIT_CODE_B"
echo "End time: $(date)"
echo

if [ $EXIT_CODE_B -eq 0 ]; then
    echo "✅ Option B completed successfully"
else
    echo "❌ Option B failed with exit code $EXIT_CODE_B"
fi
echo

echo "========================================================================"
echo "SUMMARY"
echo "========================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Option A (Regularized) exit code: $EXIT_CODE_A"
echo "Option B (Diagonal LDA) exit code: $EXIT_CODE_B"
echo

echo "Output files:"
echo "  - logs/fir_regularized_${TIMESTAMP}.out"
echo "  - logs/fir_diagonal_lda_${TIMESTAMP}.out"
echo

# Show quick results preview if successful
if [ $EXIT_CODE_A -eq 0 ]; then
    echo "--- Option A Results Preview ---"
    grep -A 2 "Mean accuracy:" logs/fir_regularized_${TIMESTAMP}.out | head -4
    echo
fi

if [ $EXIT_CODE_B -eq 0 ]; then
    echo "--- Option B Results Preview ---"
    grep -A 2 "Mean accuracy:" logs/fir_diagonal_lda_${TIMESTAMP}.out | head -4
    echo
fi

echo "========================================================================"
echo "Job completed: $(date)"
echo "========================================================================"

# Exit with failure if either test failed
if [ $EXIT_CODE_A -ne 0 ] || [ $EXIT_CODE_B -ne 0 ]; then
    exit 1
fi

exit 0
