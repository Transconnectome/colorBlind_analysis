#!/bin/bash
#SBATCH --job-name=fmriprep_stage_tracking
#SBATCH --output=logs/fmriprep_stage_tracking_%j.out
#SBATCH --error=logs/fmriprep_stage_tracking_%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --qos=shared
#SBATCH --nodelist=node2

echo "========================================="
echo "fMRIPrep Stage Tracking"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo "========================================="
echo ""

# Conda environment
source /home/connectome/haba6030/miniconda3/etc/profile.d/conda.sh
conda activate nilearn

# Working directory
cd /scratch/connectome/haba6030/colorBlind

# Run script
echo "Running TRACE_FMRIPREP_STAGES.py..."
echo ""

python3 TRACE_FMRIPREP_STAGES.py

echo ""
echo "========================================="
echo "Job completed"
echo "End time: $(date)"
echo "========================================="
