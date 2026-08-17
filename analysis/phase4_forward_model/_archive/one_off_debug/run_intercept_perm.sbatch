#!/bin/bash
#SBATCH --job-name=intercept_perm
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=logs/intercept_perm_%j.out
#SBATCH --error=logs/intercept_perm_%j.err
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model

source ~/.bashrc
conda activate nilearn

mkdir -p logs

python -u scripts/intercept_permutation_test.py
