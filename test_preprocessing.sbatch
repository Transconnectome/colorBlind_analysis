#!/bin/bash
#SBATCH --job-name=preproc_test
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=logs/preproc_test_%j.out
#SBATCH --error=logs/preproc_test_%j.err

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create log directory if it doesn't exist
mkdir -p logs

echo "=================================================="
echo "Preprocessing Level Comparison Test"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "=================================================="
echo

# Run the test script
python test_preprocessing_levels.py

EXIT_CODE=$?

echo
echo "=================================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Test completed successfully"
else
    echo "✗ Test failed with exit code $EXIT_CODE"
fi
echo "Finished: $(date)"
echo "=================================================="

exit $EXIT_CODE
