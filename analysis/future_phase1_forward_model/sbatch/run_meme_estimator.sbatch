#!/bin/bash
#SBATCH --job-name=meme_estimator
#SBATCH --output=logs/meme_estimator_%j.out
#SBATCH --error=logs/meme_estimator_%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --nodelist=node2
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model

# MEME Estimator for Unbiased Dimensionality
# Implements eigenmoment matching (Li et al. 2014, Pospisil & Pillow 2024)

source ~/.bashrc
conda activate nilearn

BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010"
OUTPUT_DIR="results/meme_dimensionality"

mkdir -p logs
mkdir -p "${OUTPUT_DIR}"

echo "Starting MEME dimensionality estimation..."
echo "Baseline data: ${BASELINE_DIR}"
echo "Output: ${OUTPUT_DIR}"

python scripts/fit_meme_eigenspectrum.py \
    --baseline_dir "${BASELINE_DIR}" \
    --output_dir "${OUTPUT_DIR}" \
    --n_moments 3 \
    --noise_percentile 95

echo "Done - check ${OUTPUT_DIR}/meme_results.json"
