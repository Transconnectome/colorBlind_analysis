#!/bin/bash
#SBATCH --job-name=fwd_step1_srm
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model
#SBATCH --output=logs/step1_srm_%j.out
#SBATCH --error=logs/step1_srm_%j.err

source ~/.bashrc
conda activate nilearn

PYTHON=$(which python)
echo "Using Python: $PYTHON ($($PYTHON --version 2>&1))"

mkdir -p logs results

BASELINE=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
OUT_SRM=results/srm_projections

echo "=== Step A: Fit SRM ==="
/usr/bin/mpirun -np 1 $PYTHON scripts/step_a_fit_srm.py \
    --rois V1 V2 V3 V4 \
    --baseline_dir $BASELINE \
    --output_dir $OUT_SRM

echo ""
echo "=== Split-Half Stability Gate ==="
/usr/bin/mpirun -np 1 $PYTHON scripts/check_rs_stability.py \
    --rois V1 V2 V3 V4 \
    --baseline_dir $BASELINE \
    --output_dir ${OUT_SRM}/stability

echo ""
echo "Step 1 complete."
