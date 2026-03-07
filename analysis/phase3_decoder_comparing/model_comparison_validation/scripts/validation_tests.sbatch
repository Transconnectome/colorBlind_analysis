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
BASE=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation
SCRIPT_DIR=${BASE}/scripts
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
PERF_DIR=${BASE}/results/loro/procrustes
OUTPUT_DIR=${BASE}/results/validation
LOCO_DIR=${BASE}/results/loco/procrustes
GP_DIR=${BASE}/results/FE_group_prior/loco_nested

echo "=============================="
echo "Job: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Start: $(date)"
echo "=============================="

# 1. LORO validation: permutation + generalization
echo "--- LORO Validation ---"
python ${SCRIPT_DIR}/validation_tests.py \
    --baseline_dir ${BASELINE_DIR} \
    --performance_dir ${PERF_DIR} \
    --output_dir ${OUTPUT_DIR} \
    --alignment procrustes \
    --tests permutation generalization

# 2. LOCO + GP validation
echo "--- LOCO + GP Validation ---"
python ${SCRIPT_DIR}/validation_tests.py \
    --baseline_dir ${BASELINE_DIR} \
    --performance_dir ${PERF_DIR} \
    --output_dir ${OUTPUT_DIR} \
    --alignment procrustes \
    --loco_dir ${LOCO_DIR} \
    --gp_dir ${GP_DIR} \
    --tests loco_bootstrap loco_group loco_permutation gp_comparison

echo "=============================="
echo "End: $(date)"
echo "=============================="
