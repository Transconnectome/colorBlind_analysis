#!/bin/bash
#SBATCH --job-name=phase2a_extract_81
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=1:30:00
#SBATCH --output=logs/phase2a_extract_baseline81_%j.out
#SBATCH --error=logs/phase2a_extract_baseline81_%j.err

echo "=========================================="
echo "Phase 2A Pattern Extraction (baseline81)"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo ""

# Change to project directory
cd /scratch/connectome/haba6030/colorBlind

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Run extraction
echo "Running pattern extraction..."
python -u scripts/phase2a_extract_patterns_baseline81.py

echo ""
echo "Job completed at: $(date)"
