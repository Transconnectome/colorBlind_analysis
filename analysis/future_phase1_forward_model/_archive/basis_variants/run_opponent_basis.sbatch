#!/bin/bash
#SBATCH --job-name=opponent_basis
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=08:00:00
#SBATCH --output=logs/opponent_basis_%j.out
#SBATCH --error=logs/opponent_basis_%j.err
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model

source ~/.bashrc
conda activate nilearn

mkdir -p logs

python -u scripts/opponent_basis_test.py
