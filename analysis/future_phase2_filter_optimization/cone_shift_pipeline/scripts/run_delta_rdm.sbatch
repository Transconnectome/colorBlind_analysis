#!/bin/bash
#SBATCH --job-name=drdm_fit
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=4:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind
#SBATCH --output=logs/drdm_fit_%j.log
#SBATCH --error=logs/drdm_fit_%j.err

# ΔRDM Loss Pipeline: Step 1 (fitting) + Step 2 (V4 validation)
#
# Step 1: Fit δθ using V1+V2 ΔRDM combined loss (cosine similarity)
#   - 3 CVD subjects × 3 models = 9 fits
#   - cone_1way: 2-stage grid (coarse 2° + refine 0.5°)
#   - cone_3way/fourier: differential evolution
#   - Exact 8! permutation test (40,320 perms)
#
# Step 2: Validate fitted δθ on V4 LOCO (ridge_gcv)
#   - Reads step1 result.json → best δθ → V4 Spearman
#
# Usage:
#   sbatch analysis/future_phase2_filter_optimization/cone_shift_pipeline/scripts/run_delta_rdm.sbatch

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline/scripts
OUTPUT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline/results/sim
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010

mkdir -p ${OUTPUT_DIR}
mkdir -p /scratch/connectome/haba6030/colorBlind/logs

echo "=== Step 1: ΔRDM Fitting (V1+V2) ==="
echo "Start: $(date)"

mpirun -np 1 python ${SCRIPT_DIR}/step1_fit_delta_rdm.py \
    --output_dir ${OUTPUT_DIR} \
    --baseline_dir ${BASELINE_DIR} \
    --metric cosine \
    --models cone_1way cone_3way fourier \
    --cvd_subjects 08 09 10

echo ""
echo "=== Step 2: V4 LOCO Validation ==="
echo "Start: $(date)"

mpirun -np 1 python ${SCRIPT_DIR}/step2_validate_v4_loco.py \
    --sim_dir ${OUTPUT_DIR} \
    --output_dir ${OUTPUT_DIR} \
    --baseline_dir ${BASELINE_DIR} \
    --models cone_1way cone_3way fourier \
    --cvd_subjects 08 09 10

echo ""
echo "=== All done ==="
echo "End: $(date)"
