#!/bin/bash
#SBATCH --job-name=exp3_block_perm
#SBATCH --nodelist=node2
#SBATCH --mem=24G
#SBATCH --cpus-per-task=8
#SBATCH --time=10:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase5_filter_optimization
#SBATCH --output=logs/exp3_block_perm_%j.out
#SBATCH --error=logs/exp3_block_perm_%j.err

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

mkdir -p results/redteam logs

mpirun -np 1 python scripts/null_label_permutation_block.py \
    --n-perm 1000 \
    --candidates all
