#!/bin/bash
#SBATCH --job-name=four_way_comp
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=0:30:00
#SBATCH --output=logs/four_way_comparison_%j.out
#SBATCH --error=logs/four_way_comparison_%j.err
#SBATCH --no-requeue

echo "========================================"
echo "Four-Way Pipeline Comparison"
echo "Job ID: $SLURM_JOB_ID"
echo "========================================"

# Activate conda
source ~/.bashrc
conda activate nilearn

# Run analysis
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/preprocess_detrend_temp

python test_whitening_before_procrustes.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Analysis completed successfully"
    echo "Results saved to: /scratch/connectome/haba6030/colorBlind/derivatives/"
else
    echo "✗ Analysis failed (exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE
