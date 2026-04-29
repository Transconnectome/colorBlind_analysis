#!/bin/bash
#SBATCH --job-name=roi_hier
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --array=0-5
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=results/loco_filter/roi_hierarchy/slurm_%A_%a.out
#SBATCH --no-requeue

SUBJECTS=(08 09 10)
ROIS=(V1 V2)

SUBJ_IDX=$((SLURM_ARRAY_TASK_ID / 2))
ROI_IDX=$((SLURM_ARRAY_TASK_ID % 2))

SUBJ=${SUBJECTS[$SUBJ_IDX]}
ROI=${ROIS[$ROI_IDX]}

echo "=== Task $SLURM_ARRAY_TASK_ID: sub-${SUBJ} ${ROI} ==="
echo "Start: $(date)"

source /usr/anaconda3/etc/profile.d/conda.sh
conda activate nilearn

python scripts/loco_distortion_fit.py \
    --subject $SUBJ \
    --roi $ROI \
    --method shift_at_both \
    --models machado_1way rc_opponent 2component \
    --output_dir results/loco_filter/roi_hierarchy

echo "Done: $(date)"
