#!/bin/bash
#SBATCH --job-name=fwd_improved
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:30:00
#SBATCH --no-requeue
#SBATCH --array=1-10%5
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model
#SBATCH --output=logs/improved_%a_%j.out
#SBATCH --error=logs/improved_%a_%j.err

source ~/.bashrc
conda activate nilearn

PYTHON=$(which python)
echo "Using Python: $PYTHON ($($PYTHON --version 2>&1))"

mkdir -p logs

# Map array index to subject ID
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJ=${SUBJECTS[$((SLURM_ARRAY_TASK_ID - 1))]}

BASELINE=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
OUT_DIR=results/improved_encoding

echo "=== Improved Encoding: sub-${SUBJ} ==="
$PYTHON scripts/validate_improved_encoding.py \
    --subject $SUBJ \
    --rois V1 V2 V3 V4 \
    --baseline_dir $BASELINE \
    --output_dir $OUT_DIR \
    --ranks 2 3 4 \
    --beta_grid 0.01 0.1 1.0 10.0 100.0

echo "Done for sub-${SUBJ}."
