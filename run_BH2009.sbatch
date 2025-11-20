#!/bin/bash
#SBATCH --job-name=BH2009_reconstruction
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=12:00:00
#SBATCH --output=logs/BH2009_%A_%a.out
#SBATCH --error=logs/BH2009_%A_%a.err
#SBATCH --array=0-3  # 4 subjects (each processes 4 ROIs sequentially)

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Define subjects and ROIs
SUBJECTS=(01 02 03 04)
ROIS=(V1 V2 V3 hV4)

# Get subject for this array task
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

# Create log directory if it doesn't exist
mkdir -p logs

echo "=================================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Subject: $SUBJECT"
echo "ROIs to process: ${ROIS[@]}"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo "=================================================="
echo

# Process all ROIs for this subject sequentially
for ROI in "${ROIS[@]}"; do
    echo ""
    echo "=================================================="
    echo "Processing: Subject=$SUBJECT, ROI=$ROI"
    echo "Started: $(date)"
    echo "=================================================="

    python fir_reconstruction_BH2009.py \
        --subject $SUBJECT \
        --roi $ROI \
        --use-pca \
        --n-components 6

    EXIT_CODE=$?

    if [ $EXIT_CODE -ne 0 ]; then
        echo "ERROR: Analysis failed for $SUBJECT $ROI with exit code $EXIT_CODE"
        echo "Continuing with next ROI..."
    else
        echo "SUCCESS: Completed $SUBJECT $ROI"
    fi

    echo "Finished: $(date)"
    echo "=================================================="
done

echo ""
echo "=================================================="
echo "All ROIs completed for subject $SUBJECT"
echo "Finished: $(date)"
echo "=================================================="

exit 0
