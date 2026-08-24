#!/bin/bash
#SBATCH --job-name=eigenspectrum_decay
#SBATCH --output=logs/eigenspectrum_decay_%j.out
#SBATCH --error=logs/eigenspectrum_decay_%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --nodelist=node2
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase4_forward_model

# Eigenspectrum Decay Analysis (Pospisil & Pillow 2024 framework)
# Computes PCA eigenvalues and fits broken power law

source ~/.bashrc
conda activate nilearn

BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010"
OUTPUT_DIR="results/dimensionality/eigenspectrum"

mkdir -p logs
mkdir -p "${OUTPUT_DIR}"

echo "Starting eigenspectrum decay analysis..."
echo "Baseline data: ${BASELINE_DIR}"
echo "Output: ${OUTPUT_DIR}"

python scripts/dimensionality/analyze_eigenspectrum_decay.py \
    --baseline_dir "${BASELINE_DIR}" \
    --output_dir "${OUTPUT_DIR}" \
    --n_early 10 \
    --n_late 50

echo "Done - check ${OUTPUT_DIR}/eigenspectrum_results.json"
