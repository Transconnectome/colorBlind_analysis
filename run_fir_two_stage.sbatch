#!/bin/bash
#SBATCH --job-name=fir_two_stage
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=2:00:00
#SBATCH --output=logs/fir_two_stage_%A_%a.out
#SBATCH --error=logs/fir_two_stage_%A_%a.err
#SBATCH --array=0-3

# Two-stage FIR GLM per run
# Stage 1: Estimate HRF with FIR
# Stage 2: Use estimated HRF to get single amplitude

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create log directory
mkdir -p logs

# Define subjects and ROIs
SUBJECTS=("P01" "01" "02" "03")
ROIS=("V1" "V2" "V3" "hV4")

# Get subject from array task ID
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

# Timestamp for this batch
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "Two-Stage FIR GLM Per Run"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Subject: $SUBJECT"
echo "Timestamp: $TIMESTAMP"
echo "Node: $(hostname)"
echo "Start time: $(date)"
echo ""

# Run for each ROI
for ROI in "${ROIS[@]}"; do
    echo "--------------------------------------"
    echo "Processing: Subject=$SUBJECT, ROI=$ROI"
    echo "--------------------------------------"

    # Run without PCA
    echo "Running without PCA..."
    python fir_two_stage_per_run.py \
        --subject $SUBJECT \
        --roi $ROI \
        --hrf-method voxel \
        --timestamp ${TIMESTAMP}

    echo ""

    # Run with PCA (6 components)
    echo "Running with PCA (6 components)..."
    python fir_two_stage_per_run.py \
        --subject $SUBJECT \
        --roi $ROI \
        --hrf-method voxel \
        --use-pca \
        --n-components 6 \
        --timestamp ${TIMESTAMP}

    echo ""
done

echo "=========================================="
echo "Completed: $SUBJECT"
echo "End time: $(date)"
echo "=========================================="
