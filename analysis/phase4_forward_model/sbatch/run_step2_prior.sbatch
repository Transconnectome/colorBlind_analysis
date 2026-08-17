#!/bin/bash
#SBATCH --job-name=fwd_step2_prior
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model
#SBATCH --output=logs/step2_prior_%j.out
#SBATCH --error=logs/step2_prior_%j.err

source ~/.bashrc
conda activate nilearn

PYTHON=$(which python)
echo "Using Python: $PYTHON ($($PYTHON --version 2>&1))"

mkdir -p logs results

BASELINE=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
SRM_DIR=results/srm_projections
PRIOR_DIR=results/group_prior
WEIGHT_DIR=results/subject_weights

echo "=== Step B: Group Prior ==="
$PYTHON scripts/step_b_group_prior.py \
    --rois V1 V2 V3 V4 \
    --baseline_dir $BASELINE \
    --srm_dir $SRM_DIR \
    --output_dir $PRIOR_DIR

echo ""
echo "=== Step C: Project Prior -> W0 ==="
/usr/bin/mpirun -np 1 $PYTHON scripts/step_c_project_prior.py \
    --subjects 01 02 03 04 05 06 07 08 09 10 \
    --rois V1 V2 V3 V4 \
    --baseline_dir $BASELINE \
    --srm_dir $SRM_DIR \
    --prior_dir $PRIOR_DIR \
    --output_dir $WEIGHT_DIR

echo ""
echo "Step 2 complete."
