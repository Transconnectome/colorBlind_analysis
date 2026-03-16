#!/bin/bash
#SBATCH --job-name=p2_step5
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:15:00
#SBATCH --output=logs/step5_%j.out
#SBATCH --error=logs/step5_%j.err
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization

source ~/.bashrc
conda activate nilearn

mkdir -p logs results/step5_pairwise

mpirun -np 1 python scripts/step5_pairwise_diagnostic.py \
    --model_dir results/step1_model \
    --filter_dir results/step3_filter \
    --prevalidation_json target_prevalidation/results/fdr_corrected/filter_pre_validation_fdr_corrected.json \
    --output_dir results/step5_pairwise
