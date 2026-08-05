#!/bin/bash
#SBATCH --job-name=pgrp_perm
#SBATCH --nodelist=node2
#SBATCH --no-requeue
#SBATCH --array=1-4
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=24:00:00
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/1D_permutation
#SBATCH --output=logs/pergroup_perm_%A_%a.out

source ~/.bashrc
conda activate nilearn

# Map array index to ROI
ROIS=(V1 V2 V3 hV4)
ROI=${ROIS[$SLURM_ARRAY_TASK_ID-1]}

echo "========================================="
echo "Per-Group Disparity Permutation Test"
echo "========================================="
echo "ROI: $ROI"
echo "Permutations: 1000"
echo "Method: Shuffle → Retrain SRM → Per-group metrics"
echo "========================================="
echo ""

mpirun -np 1 python run_pergroup_disparity_permutation.py \
    --roi $ROI \
    --n_permutations 1000

echo ""
echo "Completed: $ROI"
