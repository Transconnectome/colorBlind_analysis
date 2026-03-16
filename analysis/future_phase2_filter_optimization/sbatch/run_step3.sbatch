#!/bin/bash
#SBATCH --job-name=p2_step3
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --array=1-3
#SBATCH --output=logs/step3_%A_%a.out
#SBATCH --error=logs/step3_%A_%a.err
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization

source ~/.bashrc
conda activate nilearn

mkdir -p logs results/step3_filter

mpirun -np 1 python scripts/step3_filter_estimation.py \
    --model_dir results/step1_model \
    --validation_json ../future_phase1_forward_model/results/cone_shift/cone_shift_validation_results.json \
    --output_dir results/step3_filter \
    --subject_idx ${SLURM_ARRAY_TASK_ID}
