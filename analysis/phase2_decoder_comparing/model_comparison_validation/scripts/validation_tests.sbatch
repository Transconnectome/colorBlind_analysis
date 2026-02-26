#!/bin/bash
#SBATCH --job-name=decoder_val
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=06:00:00
#SBATCH --no-requeue
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/logs/decoder_val_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/logs/decoder_val_%j.err

# Environment
source ~/.bashrc
conda activate nilearn

# Paths
SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/scripts
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
PERF_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/results/model_comparison/consolidated
OUTPUT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation/results/model_comparison/consolidated

echo "=============================="
echo "Job: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Start: $(date)"
echo "=============================="

# Run permutation test + cross-subject generalization
python ${SCRIPT_DIR}/validation_tests.py \
    --baseline_dir ${BASELINE_DIR} \
    --performance_dir ${PERF_DIR} \
    --output_dir ${OUTPUT_DIR} \
    --alignment procrustes \
    --tests permutation generalization

echo "=============================="
echo "End: $(date)"
echo "=============================="
