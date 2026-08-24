#!/bin/bash
#SBATCH --job-name=adaptive_basis
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=logs/adaptive_basis_%j.out
#SBATCH --error=logs/adaptive_basis_%j.err
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=analysis/phase4_forward_model/scripts
OUTPUT_DIR=analysis/phase4_forward_model/results/adaptive_basis
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010

mkdir -p ${OUTPUT_DIR}
mkdir -p logs

echo "=== Adaptive Basis Optimization (Section 9k-1) ==="
echo "Start: $(date)"
echo ""

for SUB in 01 02 03 04 05 06 07 08 09 10; do
    for ROI in V1 V2 V3 V4; do
        echo "--- sub-${SUB} ${ROI} ---"
        python ${SCRIPT_DIR}/fit_adaptive_basis.py \
            --subject ${SUB} \
            --roi ${ROI} \
            --output_dir ${OUTPUT_DIR} \
            --baseline_dir ${BASELINE_DIR} \
            --n_restarts 10 \
            --lambda_spacing 0.1
        echo ""
    done
done

echo "=== Done: $(date) ==="
