#!/bin/bash
#SBATCH --job-name=roi_pipeline
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=4:00:00
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/logs/roi_pipeline_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/logs/roi_pipeline_%j.err

# SLURM configuration for comprehensive ROI pipeline
# CRITICAL: Always use node2, NEVER specify partition

echo "=========================================="
echo "ROI Pipeline - Comprehensive Parameter Search"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Date: $(date)"
echo "=========================================="

# Activate conda environment
# Initialize conda for bash shell
eval "$(conda shell.bash hook)"
conda activate nilearn

# Verify environment
echo "Python: $(which python)"
echo "Python version: $(python --version)"
echo "Conda environment: $CONDA_DEFAULT_ENV"

# Change to working directory
cd /scratch/connectome/haba6030/colorBlind

# Create logs directory if needed
mkdir -p logs

# Get subject ID from command line argument (default P01)
SUBJECT_ID=${1:-P01}
RUN_ID=${2:-1}

echo "Subject: $SUBJECT_ID"
echo "Run: $RUN_ID"
echo "=========================================="

# Run comprehensive pipeline
# Use -u flag to disable Python output buffering for real-time logs
python -u roi_pipeline_comprehensive.py $SUBJECT_ID $RUN_ID

echo "=========================================="
echo "Pipeline completed at: $(date)"
echo "=========================================="
