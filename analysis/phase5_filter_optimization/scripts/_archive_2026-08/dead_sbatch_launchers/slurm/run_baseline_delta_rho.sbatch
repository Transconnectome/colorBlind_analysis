#!/bin/bash
#SBATCH --job-name=base_drho
#SBATCH --nodelist=node2
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase5_filter_optimization
#SBATCH --output=logs/baseline_delta_rho_%j.out
#SBATCH --error=logs/baseline_delta_rho_%j.err

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

mkdir -p results/baseline_delta_rho logs

mpirun -np 1 python scripts/baseline_delta_rho_diagnostic.py \
    --subjects 01 02 03 04 05 06 07 08 09 10 \
    --output_dir results/baseline_delta_rho
