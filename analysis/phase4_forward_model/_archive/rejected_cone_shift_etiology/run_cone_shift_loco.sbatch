#!/bin/bash
#SBATCH --job-name=cs_pred
#SBATCH --output=logs/cs_pred_%j.out
#SBATCH --error=logs/cs_pred_%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --nodelist=node2
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase4_forward_model

# Cone-shift-informed CVD prediction evaluation
# Requires: cone_shift_validation_results.json (from local cone_shift_validation.py)

source ~/.bashrc
conda activate nilearn

BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010"
VALIDATION_JSON="results/cone_shift/cone_shift_validation_results.json"
OUTPUT_DIR="results/cone_shift_loco"

mkdir -p logs
mkdir -p "${OUTPUT_DIR}"

echo "Starting cone-shift prediction evaluation..."
echo "Baseline data: ${BASELINE_DIR}"
echo "Validation: ${VALIDATION_JSON}"
echo "Output: ${OUTPUT_DIR}"

export PYTHONPATH="scripts:${PYTHONPATH}"

mpirun -np 1 python scripts/cone_shift_loco.py \
    --baseline_dir "${BASELINE_DIR}" \
    --validation_json "${VALIDATION_JSON}" \
    --output_dir "${OUTPUT_DIR}" \
    --roi V4

echo "Done - check ${OUTPUT_DIR}/cone_shift_prediction_results.json"
