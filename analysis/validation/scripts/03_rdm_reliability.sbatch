#!/bin/bash
#SBATCH --job-name=rdm_reliability
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=01:00:00
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/rdm_reliability_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/rdm_reliability_%j.err

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create log directory
mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/validation/logs

# Set baseline timestamp
BASELINE_TIMESTAMP=${1:-"baseline32_method3_header_mi"}

echo "================================================"
echo "RDM Reliability Analysis"
echo "================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Baseline timestamp: $BASELINE_TIMESTAMP"
echo "Start time: $(date)"
echo "================================================"

# Run RDM reliability analysis
python /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/03_rdm_reliability.py \
    --baseline-timestamp $BASELINE_TIMESTAMP \
    --subjects sub-01 sub-02 sub-03 sub-04 sub-05 sub-06 sub-07 sub-08 sub-09 sub-10 \
    --rois V1 V2 V3 hV4

echo "================================================"
echo "End time: $(date)"
echo "================================================"
