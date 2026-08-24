#!/bin/bash
#SBATCH --job-name=exp1_atom_decomp
#SBATCH --nodelist=node2
#SBATCH --mem=24G
#SBATCH --cpus-per-task=8
#SBATCH --time=06:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase5_filter_optimization
#SBATCH --output=logs/exp1_atom_decomp_%j.out
#SBATCH --error=logs/exp1_atom_decomp_%j.err

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

mkdir -p results/redteam logs

mpirun -np 1 python scripts/exp_atom_decomp_at_zero.py \
    --m-realizations 20 \
    --candidates all
