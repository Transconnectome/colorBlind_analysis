#!/bin/bash
#SBATCH --job-name=fir_simple
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=2:00:00
#SBATCH --output=logs/fir_simple_%A_%a.out
#SBATCH --error=logs/fir_simple_%A_%a.err
#SBATCH --array=0-3

# FIR-only approach: Direct use of FIR amplitudes for classification
# Testing multiple strategies for using FIR β values

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create log directory
mkdir -p logs

# Define subjects and ROIs
SUBJECTS=("01" "02" "03" "04")
ROIS=("V1" "V2" "V3" "hV4")

# Get subject from array task ID
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

# Timestamp for this batch
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "=========================================="
echo "FIR-Only GLM (Simple Strategies)"
echo "=========================================="
echo "Job ID: $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Subject: $SUBJECT"
echo "Timestamp: $TIMESTAMP"
echo "Node: $(hostname)"
echo "Start time: $(date)"
echo ""

# Test multiple strategies
STRATEGIES=("flatten" "average" "delay3" "delay4" "delay5")

# Run for each ROI
for ROI in "${ROIS[@]}"; do
    echo "======================================"
    echo "ROI: $ROI"
    echo "======================================"

    for STRATEGY in "${STRATEGIES[@]}"; do
        echo "--------------------------------------"
        echo "Processing: $SUBJECT, $ROI, Strategy=$STRATEGY"
        echo "--------------------------------------"

        # Run without PCA
        echo "Running without PCA..."
        python fir_per_run_simple.py \
            --subject $SUBJECT \
            --roi $ROI \
            --strategy $STRATEGY \
            --timestamp ${TIMESTAMP}

        echo ""

        # Run with PCA (6 components)
        echo "Running with PCA (6 components)..."
        python fir_per_run_simple.py \
            --subject $SUBJECT \
            --roi $ROI \
            --strategy $STRATEGY \
            --use-pca \
            --n-components 6 \
            --timestamp ${TIMESTAMP}

        echo ""
    done
done

echo "=========================================="
echo "Completed: $SUBJECT"
echo "End time: $(date)"
echo "=========================================="
