#!/bin/bash
#SBATCH --job-name=cross_type
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=logs/cross_type_%j.out
#SBATCH --error=logs/cross_type_%j.err
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind

source ~/.bashrc
conda activate nilearn

mkdir -p logs

cd /scratch/connectome/haba6030/colorBlind

mpirun -np 1 python analysis/future_phase2_filter_optimization/cone_shift_pipeline/scripts/cross_type_validation.py
