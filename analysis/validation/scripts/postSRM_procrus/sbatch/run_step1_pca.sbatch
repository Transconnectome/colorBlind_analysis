#!/bin/bash
#SBATCH --job-name=postSRM_step1_pca
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=logs/step1_pca_%A_%a.out
#SBATCH --error=logs/step1_pca_%A_%a.err
#SBATCH --array=1-36  # 9 subjects × 4 ROIs

# Procrustes Pipeline - Step 1: PCA Dimension Reduction
# Array job: All subject-ROI combinations

set -e

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Subject and ROI arrays
SUBJECTS=(01 02 03 04 05 06 08 09 10)  # 9 subjects
ROIS=(V1 V2 V3 hV4)  # 4 ROIs

# Calculate subject and ROI from SLURM_ARRAY_TASK_ID
SUBJ_IDX=$(( (SLURM_ARRAY_TASK_ID - 1) / 4 ))
ROI_IDX=$(( (SLURM_ARRAY_TASK_ID - 1) % 4 ))

SUBJECT=${SUBJECTS[$SUBJ_IDX]}
ROI=${ROIS[$ROI_IDX]}

echo "=== Step 1: PCA Dimension Reduction ==="
echo "Job ID: $SLURM_JOB_ID, Array Task: $SLURM_ARRAY_TASK_ID"
echo "Subject: sub-$SUBJECT, ROI: $ROI"
echo "Node: $(hostname)"
echo "Start time: $(date)"

# Paths
SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/postSRM_procrus
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/baseline
OUTPUT_DIR=$SCRIPT_DIR/results/step1_pca

# Create output directory
mkdir -p $OUTPUT_DIR

# Run Step 1
cd $SCRIPT_DIR

python step1a_dimension_reduction_pca.py \
    --subject $SUBJECT \
    --roi $ROI \
    --n-components 50 \
    --baseline-dir $BASELINE_DIR \
    --output-dir $OUTPUT_DIR

echo "End time: $(date)"
echo "✓ Step 1 complete for sub-$SUBJECT $ROI"
