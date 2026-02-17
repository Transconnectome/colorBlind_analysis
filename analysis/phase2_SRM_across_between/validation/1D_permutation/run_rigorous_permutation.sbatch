#!/bin/bash
#SBATCH --job-name=rig_perm
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --no-requeue
#SBATCH --array=1-4                    # 4 ROIs
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G                      # SRM training memory-intensive
#SBATCH --time=24:00:00                # Each ROI: 1000 perms × ~1-2min = ~24h
#SBATCH --output=logs/rigorous_perm_%A_%a.out

source ~/.bashrc
conda activate nilearn

# Map array index to ROI
ROIS=(V1 V2 V3 hV4)
ROI=${ROIS[$SLURM_ARRAY_TASK_ID-1]}

echo "========================================="
echo "Rigorous Color Permutation Test"
echo "========================================="
echo "ROI: $ROI"
echo "Permutations: 1000"
echo "Method: Shuffle → Retrain SRM → Compute"
echo "========================================="
echo ""

# Run rigorous permutation test
python run_color_permutation_with_srm_retraining.py \
    --roi $ROI \
    --n_permutations 1000 \
    --output_dir /scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/1D_permutation/results_rigorous

echo ""
echo "✅ Completed: $ROI"
