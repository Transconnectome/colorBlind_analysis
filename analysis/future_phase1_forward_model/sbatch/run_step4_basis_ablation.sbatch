#!/bin/bash
#SBATCH --job-name=fwd_basis_abl
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --array=1-10%5
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model
#SBATCH --output=logs/basis_abl_%a_%j.out
#SBATCH --error=logs/basis_abl_%a_%j.err

source ~/.bashrc
conda activate nilearn

PYTHON=$(which python)
echo "Using Python: $PYTHON ($($PYTHON --version 2>&1))"

mkdir -p logs

# Map array index to subject ID
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJ=${SUBJECTS[$((SLURM_ARRAY_TASK_ID - 1))]}

BASELINE=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
WEIGHT_DIR=results/subject_weights
SRM_DIR=results/srm_projections

echo "=== Basis Ablation: sub-${SUBJ} ==="

# --- LF-4: Fourier basis with 4 channels ---
echo "--- LF-4 ---"
$PYTHON scripts/validate_loro_loco_loso.py \
    --subject $SUBJ \
    --rois V1 V2 V3 V4 \
    --baseline_dir $BASELINE \
    --prior_dir $WEIGHT_DIR \
    --srm_dir $SRM_DIR \
    --output_dir results/validation_lf4 \
    --basis_type lf \
    --n_channels 4 \
    --models ols ridge_gcv

# --- LF-6: Fourier basis with 6 channels ---
echo "--- LF-6 ---"
$PYTHON scripts/validate_loro_loco_loso.py \
    --subject $SUBJ \
    --rois V1 V2 V3 V4 \
    --baseline_dir $BASELINE \
    --prior_dir $WEIGHT_DIR \
    --srm_dir $SRM_DIR \
    --output_dir results/validation_lf6 \
    --basis_type lf \
    --n_channels 6 \
    --models ols ridge_gcv

echo "Basis ablation complete for sub-${SUBJ}."
