#!/bin/bash
#SBATCH --job-name=centered_perm
#SBATCH --nodelist=node2
#SBATCH --mem=16G
#SBATCH --cpus-per-task=2
#SBATCH --time=08:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model
#SBATCH --output=logs/centered_perm.out
#SBATCH --error=logs/centered_perm.err

source ~/.bashrc
conda activate nilearn

mkdir -p logs results/permutation_centered

echo "=== Condition-Centered Permutation Test ==="
echo "Started: $(date)"
echo "Models: ridge_gcv_centered, smooth_fixed_centered, smooth_reopt_centered"
echo "N_perms: 10000"

mpirun -np 1 python scripts/permutation_test_centered.py \
    --baseline_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
    --output_dir results/permutation_centered \
    --n_perms 10000 \
    --seed 42 \
    --rois V1 V2 V3 V4

echo "Finished: $(date)"
