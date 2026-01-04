#!/bin/bash
#SBATCH --job-name=validate_T
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/logs/group_level/validate_transformation_t_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/logs/group_level/validate_transformation_t_%j.err
#SBATCH --time=01:00:00
#SBATCH --mem=32GB
#SBATCH --cpus-per-task=4
#SBATCH --nodelist=node2

echo "==========================================="
echo "Transformation T Validation"
echo "==========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo ""

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Navigate to project directory
cd /scratch/connectome/haba6030/colorBlind

# Create log directory if needed
mkdir -p logs/group_level

# Run validation script
echo "Running transformation T validation..."
python analysis/group_level/validate_transformation_t.py

# Check exit status
if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Validation completed successfully!"
    echo "Results saved to: results/group_level/transformation_validation/"
else
    echo ""
    echo "✗ Validation failed - check error log"
    exit 1
fi

echo ""
echo "End time: $(date)"
echo "==========================================="
