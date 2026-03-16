#!/bin/bash
#SBATCH --job-name=p2_step4
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --array=1-3
#SBATCH --output=logs/step4_%A_%a.out
#SBATCH --error=logs/step4_%A_%a.err
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization

source ~/.bashrc
conda activate nilearn

mkdir -p logs results/step4_validation

mpirun -np 1 python scripts/step4_validation.py \
    --model_dir results/step1_model \
    --filter_dir results/step3_filter \
    --baseline_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
    --output_dir results/step4_validation \
    --subject_idx ${SLURM_ARRAY_TASK_ID} \
    --n_perm 1000
