#!/bin/bash
#SBATCH --job-name=hc_spec
#SBATCH --nodelist=node2
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --time=06:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=logs/hc_specificity_%j.out
#SBATCH --error=logs/hc_specificity_%j.err

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

mkdir -p results/hc_specificity logs

mpirun -np 1 python scripts/hc_specificity_test.py \
    --output_dir results/hc_specificity \
    --include_drdm
