#!/bin/bash
#SBATCH --job-name=loso_zs
#SBATCH --output=logs/loso_zs_%j.out
#SBATCH --error=logs/loso_zs_%j.err
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --nodelist=node2
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model

# LOSO Zero-Shot Validation
# Refits SRM per fold (no leakage), direct eval on all 8 colors

source ~/.bashrc
conda activate nilearn

BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010"
OUTPUT_DIR="results/loso_zero_shot"

mkdir -p logs
mkdir -p "${OUTPUT_DIR}"

echo "Starting LOSO zero-shot validation (SRM refit per fold)..."
echo "Baseline data: ${BASELINE_DIR}"
echo "Output: ${OUTPUT_DIR}"

export PYTHONPATH="scripts:${PYTHONPATH}"

mpirun -np 1 python scripts/validate_loso_zero_shot.py \
    --baseline_dir "${BASELINE_DIR}" \
    --output_dir "${OUTPUT_DIR}" \
    --rois V1 V2 V3 V4

echo "Done - check ${OUTPUT_DIR}/loso_zero_shot.json"
