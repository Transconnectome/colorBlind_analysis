#!/bin/bash
#SBATCH --job-name=baseline_unfilt
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --array=1-9%4
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/between_procrustes/logs/baseline_unfilt_%A_%a.log

# Map SLURM_ARRAY_TASK_ID to subject (excluding sub-07)
SUBJECTS=(sub-01 sub-02 sub-03 sub-04 sub-05 sub-06 sub-08 sub-09 sub-10)
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID-1]}

ROIS=(V1 V2 V3 hV4)

# Activate conda environment
source ~/miniconda3/etc/profile.d/conda.sh
conda activate nilearn

# Navigate to script directory
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/between_procrustes

# Run preprocessing for each ROI
for ROI in "${ROIS[@]}"; do
    echo "Processing $SUBJECT $ROI..."
    python fir_reconstruction_no_voxel_filtering.py \
        --subject ${SUBJECT#sub-} \
        --roi $ROI \
        --dataset deoblique_v2

    echo "Completed $SUBJECT $ROI"
    echo "---"
done

echo "All ROIs completed for $SUBJECT"
