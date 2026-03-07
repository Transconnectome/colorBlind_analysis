#!/bin/bash
#SBATCH --job-name=step2_val
#SBATCH --nodelist=node2
#SBATCH --array=1-10
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=00:30:00
#SBATCH --output=logs/step2_%A_%a.log
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --no-requeue

source ~/.bashrc
conda activate nilearn

# Map array task ID to subject
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID - 1]}

echo "=== Step 2: Prediction Validation ==="
echo "Subject: sub-${SUBJECT}"
echo "Task ID: ${SLURM_ARRAY_TASK_ID}"
echo "Node: $(hostname)"
echo "Time: $(date)"

python scripts/step2_validate_prediction.py \
    --subject ${SUBJECT} \
    --rois V1 V2 V3 V4 \
    --baseline_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
    --output_dir results/step2_validation

echo "=== Done: $(date) ==="
