#!/bin/bash
#SBATCH --job-name=exp2_gt_grid
#SBATCH --nodelist=node2
#SBATCH --array=0-2
#SBATCH --mem=24G
#SBATCH --cpus-per-task=8
#SBATCH --time=20:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=logs/exp2_gt_grid_%A_%a.out
#SBATCH --error=logs/exp2_gt_grid_%A_%a.err

source ~/.bashrc
conda activate nilearn

export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-8}

mkdir -p results/redteam logs

CANDIDATES=("S08-stable" "S08-robust" "S09-primary")
CAND=${CANDIDATES[$SLURM_ARRAY_TASK_ID]}

echo "Task $SLURM_ARRAY_TASK_ID → candidate $CAND"

mpirun -np 1 python scripts/exp_gt_grid_sweep.py \
    --m-realizations 20 \
    --candidates "$CAND"
