#!/bin/bash
#SBATCH --job-name=st_artifact
#SBATCH --nodelist=node2
#SBATCH --array=1-10%5
#SBATCH --mem=8G
#SBATCH --cpus-per-task=2
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model
#SBATCH --output=logs/st_artifact_%a.out
#SBATCH --error=logs/st_artifact_%a.err

source ~/.bashrc
conda activate nilearn

mkdir -p logs

SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJ=${SUBJECTS[$((SLURM_ARRAY_TASK_ID-1))]}

echo "=== Smooth_tikh Artifact Validation: sub-${SUBJ} ==="
echo "Started: $(date)"

mpirun -np 1 python scripts/validate_smooth_tikh_artifact.py \
    --mode rdm \
    --subject $SUBJ \
    --rois V1 V2 V3 V4 \
    --baseline_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
    --output_dir results/smooth_tikh_artifact

echo "Finished: $(date)"
