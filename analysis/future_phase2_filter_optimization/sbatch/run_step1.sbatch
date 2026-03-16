#!/bin/bash
#SBATCH --job-name=p2_step1
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=logs/step1_%j.out
#SBATCH --error=logs/step1_%j.err
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization

source ~/.bashrc
conda activate nilearn

mkdir -p logs results/step1_model

mpirun -np 1 python scripts/step1_build_model.py \
    --baseline_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
    --output_dir results/step1_model
