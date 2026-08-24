#!/bin/bash
#SBATCH --job-name=fwd_step3_ft
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --array=1-10%5
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase4_forward_model
#SBATCH --output=logs/step3_ft_%a_%j.out
#SBATCH --error=logs/step3_ft_%a_%j.err

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

echo "=== Step D: Fine-Tune sub-${SUBJ} ==="
$PYTHON scripts/step_d_finetune.py \
    --subject $SUBJ \
    --rois V1 V2 V3 V4 \
    --baseline_dir $BASELINE \
    --prior_dir $WEIGHT_DIR \
    --output_dir $WEIGHT_DIR

echo "Step 3 complete for sub-${SUBJ}."
