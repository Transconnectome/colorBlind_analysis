#!/bin/bash
#SBATCH --job-name=BH2009_voxel_specific
#SBATCH --nodelist=node2
#SBATCH --array=0  # Single subject for now (sub-01)
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=logs/voxel_specific_%A_%a.out
#SBATCH --error=logs/voxel_specific_%A_%a.err

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create log directory
mkdir -p logs

# Configuration
SUBJECT_ID="01"
ROIS=("V1" "V2" "V3" "hV4")

echo "=================================================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Subject: $SUBJECT_ID"
echo "ROIs to process: ${ROIS[@]}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "=================================================================="
echo

# Process each ROI
for ROI in "${ROIS[@]}"; do
    echo
    echo "=================================================================="
    echo "Processing: Subject=$SUBJECT_ID, ROI=$ROI"
    echo "Started: $(date)"
    echo "=================================================================="

    python fir_reconstruction_voxel_specific.py \
        --subject $SUBJECT_ID \
        --roi $ROI \
        --use-pca

    if [ $? -eq 0 ]; then
        echo "SUCCESS: Completed $SUBJECT_ID $ROI"
    else
        echo "ERROR: Analysis failed for $SUBJECT_ID $ROI with exit code $?"
        echo "Continuing with next ROI..."
    fi

    echo "Finished: $(date)"
    echo "=================================================================="
done

echo
echo "=================================================================="
echo "All ROIs completed for subject $SUBJECT_ID"
echo "Finished: $(date)"
echo "=================================================================="
