#!/bin/bash
#SBATCH --job-name=ext_val
#SBATCH --nodelist=node2
#SBATCH --array=1-10%5
#SBATCH --mem=16G
#SBATCH --cpus-per-task=2
#SBATCH --time=06:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase4_forward_model
#SBATCH --output=logs/ext_val_%a.out
#SBATCH --error=logs/ext_val_%a.err

source ~/.bashrc
conda activate nilearn

mkdir -p logs

SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJ=${SUBJECTS[$((SLURM_ARRAY_TASK_ID-1))]}

echo "=== Extended Validation: sub-${SUBJ} ==="
echo "Started: $(date)"

mpirun -np 1 python scripts/validate_extended_models.py \
    --subject $SUBJ \
    --rois V1 V2 V3 V4 \
    --baseline_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
    --srm_dir results/srm_projections \
    --output_dir results/validation_extended

echo "Finished: $(date)"
