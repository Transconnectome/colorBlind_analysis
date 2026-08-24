#!/bin/bash
#SBATCH --job-name=rec_v2_sm
#SBATCH --nodelist=node2
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase5_filter_optimization
#SBATCH --output=logs/param_recovery_v2_smoke_%j.out
#SBATCH --error=logs/param_recovery_v2_smoke_%j.err

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-4}

mkdir -p results/redteam logs

mpirun -np 1 python scripts/param_recovery_voxel.py \
    --m-realizations 3 \
    --candidates S08-stable \
    --hc-subset sub-01,sub-02
