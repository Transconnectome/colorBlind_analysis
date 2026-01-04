#!/bin/bash
#SBATCH --job-name=reliability_check
#SBATCH --output=logs/step1_reliability_sub-%A.out
#SBATCH --error=logs/step1_reliability_sub-%A.err
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --qos=shared
#SBATCH --nodelist=node2

# Step 1.2: Reliability Comparison
# Usage: sbatch run_step1_reliability_check.sbatch <subject_id> <roi>
# Example: sbatch run_step1_reliability_check.sbatch 02 V1

echo "=========================================="
echo "Step 1.2: Reliability Comparison"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo "=========================================="

# Parameters from command line
SUBJECT=${1:-02}
ROI=${2:-V1}

echo "Subject: $SUBJECT"
echo "ROI: $ROI"
echo ""

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Change to script directory
cd /scratch/connectome/haba6030/colorBlind/prediction_model/scripts

# Create logs directory
mkdir -p ../logs

# Run reliability comparison
echo "Running reliability comparison..."
python 01_reliability_comparison.py \
    --subject $SUBJECT \
    --roi $ROI \
    --fmriprep_dir /storage/connectome/haba6030/fmriprep_out_deoblique_v2 \
    --bids_dir /storage/connectome/haba6030/colorBlind_data_deoblique \
    --output_dir ../results/reliability_check \
    --smoothing_fwhm 6.0 \
    --confounds_strategy motion

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "End time: $(date)"
echo "Exit code: $EXIT_CODE"
echo "=========================================="

exit $EXIT_CODE
