#!/bin/bash
#SBATCH --job-name=voxel_preference
#SBATCH --output=logs/voxel_preference_%j.out
#SBATCH --error=logs/voxel_preference_%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --nodelist=node2
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase4_forward_model

# Voxel Color Preference Mapping (Bannert & Bartels 2025 framework)
# KDE-based visualization of which voxels prefer which colors

source ~/.bashrc
conda activate nilearn

export PYTHONPATH="/scratch/connectome/haba6030/colorBlind/analysis/phase4_forward_model/scripts:${PYTHONPATH}"

BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010"
OUTPUT_DIR="results/population_organization/voxel_preference"

mkdir -p logs
mkdir -p "${OUTPUT_DIR}"

echo "Starting voxel color preference mapping..."
echo "Baseline data: ${BASELINE_DIR}"
echo "Output: ${OUTPUT_DIR}"

python scripts/population_organization/map_voxel_color_preference.py \
    --baseline_dir "${BASELINE_DIR}" \
    --output_dir "${OUTPUT_DIR}" \
    --bandwidth_method scott

echo "Done - check ${OUTPUT_DIR}/preference_results.json"
