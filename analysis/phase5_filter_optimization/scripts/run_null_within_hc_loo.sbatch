#!/bin/bash
#SBATCH --job-name=null_loo
#SBATCH --nodelist=node2
#SBATCH --mem=24G
#SBATCH --cpus-per-task=4
#SBATCH --time=08:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=logs/null_within_hc_loo_%j.out
#SBATCH --error=logs/null_within_hc_loo_%j.err

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

mkdir -p results/redteam logs

mpirun -np 1 python scripts/null_within_hc_loo.py \
    --m-noise 20 \
    --candidates all
