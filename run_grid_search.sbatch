#!/bin/bash
#SBATCH --job-name=grid_search_preproc
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=logs/grid_search_%j.out
#SBATCH --error=logs/grid_search_%j.err

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create log directory if it doesn't exist
mkdir -p logs

echo "=================================================================="
echo "Preprocessing Grid Search for B&H (2009) Pipeline"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "=================================================================="
echo

# Run the grid search
python grid_search_preprocessing.py

EXIT_CODE=$?

echo
echo "=================================================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Grid search completed successfully"
else
    echo "✗ Grid search failed with exit code $EXIT_CODE"
fi
echo "Finished: $(date)"
echo "=================================================================="

exit $EXIT_CODE
