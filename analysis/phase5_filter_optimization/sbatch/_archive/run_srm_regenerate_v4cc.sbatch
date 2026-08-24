#!/bin/bash
#SBATCH --job-name=srm_v4cc_regen
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase5_filter_optimization
#SBATCH --output=logs/srm_v4cc_regen_%j.log
#SBATCH --error=logs/srm_v4cc_regen_%j.err

mkdir -p logs

# BrainIAK MPI requires mpirun even for single process
source /home/haba6030/miniconda3/etc/profile.d/conda.sh
conda activate srm

# Regenerate SRM amplitudes for V4 with multiple K values to compare
mpirun -np 1 python scripts/_server_srm_v4cc_regen.py
