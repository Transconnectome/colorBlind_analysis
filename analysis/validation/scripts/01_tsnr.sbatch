#!/bin/bash
#SBATCH --job-name=tsnr_validation
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/tsnr_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/tsnr_%j.err

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create log directory
mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/validation/logs

# Set baseline timestamp (passed from run_01_tsnr.sh or manually specified)
# To find available timestamps manually:
# ls -td /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding/*/ | head -1
BASELINE_TIMESTAMP=${1:-"baseline32_method3_header_mi"}  # Default from phase0_parallel_mem24.sbatch

echo "================================================"
echo "tSNR Validation Analysis"
echo "================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Baseline timestamp: $BASELINE_TIMESTAMP"
echo "Start time: $(date)"
echo "================================================"

# Run tSNR analysis
python /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/01_tsnr_analysis.py \
    --baseline-timestamp $BASELINE_TIMESTAMP \
    --subjects sub-01 sub-02 sub-03 sub-04 sub-05 sub-06 sub-07 sub-08 sub-09 sub-10 \
    --rois V1 V2 V3 hV4 \
    --n-runs 6

echo "================================================"
echo "End time: $(date)"
echo "================================================"
