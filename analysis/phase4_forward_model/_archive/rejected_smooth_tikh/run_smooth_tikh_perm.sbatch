#!/bin/bash
#SBATCH --job-name=st_perm
#SBATCH --nodelist=node2
#SBATCH --mem=16G
#SBATCH --cpus-per-task=2
#SBATCH --time=04:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase4_forward_model
#SBATCH --output=logs/st_perm.out
#SBATCH --error=logs/st_perm.err

source ~/.bashrc
conda activate nilearn

mkdir -p logs

echo "=== Smooth_tikh Permutation Test (10K) ==="
echo "Started: $(date)"

mpirun -np 1 python scripts/validate_smooth_tikh_artifact.py \
    --mode perm \
    --rois V1 V2 V3 V4 \
    --baseline_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010 \
    --output_dir results/smooth_tikh_artifact \
    --n_perms 10000 \
    --seed 42

echo "Finished: $(date)"
