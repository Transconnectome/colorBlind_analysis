#!/bin/bash
#SBATCH --job-name=decoder_comp
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --array=1-28  # 7 subjects × 4 ROIs
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=1:00:00
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/decoder_comp_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/decoder_comp_%A_%a.err

# ============================================================================
# Full Decoder Model Comparison Array Job
#
# Runs comparison for all HC subjects × 4 ROIs
# Both before and after Procrustes alignment
# ============================================================================

echo "========================================================================"
echo "Decoder Model Comparison Array Job"
echo "========================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo "========================================================================"

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Change to project directory
cd /scratch/connectome/haba6030/colorBlind

# Create logs directory
mkdir -p analysis/validation/logs

# ============================================================================
# Array job mapping: 7 subjects × 4 ROIs = 28 tasks
# ============================================================================

SUBJECTS=(01 02 03 05 06 07)
ROIS=(V1 V2 V3 hV4)

# Calculate subject and ROI indices
SUBJECT_IDX=$(( ($SLURM_ARRAY_TASK_ID - 1) / 4 ))
ROI_IDX=$(( ($SLURM_ARRAY_TASK_ID - 1) % 4 ))

SUBJECT=${SUBJECTS[$SUBJECT_IDX]}
ROI=${ROIS[$ROI_IDX]}

echo ""
echo "Processing: sub-$SUBJECT, ROI=$ROI"
echo ""

# Variables
TIMESTAMP="test_zscore_FINAL"
ALIGNED_TIMESTAMP="${TIMESTAMP}_procrustes"
DATASET="method3_header_mi"
BASE_DIR="/scratch/connectome/haba6030/colorBlind"

# Output directories
OUTPUT_BEFORE="analysis/validation/results/model_comparison/before_alignment"
OUTPUT_AFTER="analysis/validation/results/model_comparison/after_alignment"

mkdir -p "$OUTPUT_BEFORE"
mkdir -p "$OUTPUT_AFTER"

# ============================================================================
# Step 1: Before Alignment
# ============================================================================

echo "========================================================================"
echo "Step 1: Before Alignment"
echo "========================================================================"

python analysis/validation/scripts/05_decoder_model_comparison.py \
    --subject "$SUBJECT" \
    --rois "$ROI" \
    --timestamp "$TIMESTAMP" \
    --dataset "$DATASET" \
    --base_dir "$BASE_DIR" \
    --aligned False \
    --models ridge forward_encoding mlp \
    --output_dir "$OUTPUT_BEFORE"

BEFORE_EXIT_CODE=$?

if [ $BEFORE_EXIT_CODE -eq 0 ]; then
    echo "Before alignment completed successfully!"
else
    echo "ERROR: Before alignment failed with exit code $BEFORE_EXIT_CODE"
    exit 1
fi

# ============================================================================
# Step 2: After Alignment
# ============================================================================

echo ""
echo "========================================================================"
echo "Step 2: After Alignment"
echo "========================================================================"

# Check if aligned data exists
ALIGNED_PATH="analysis/validation/results/aligned_amplitudes/${ALIGNED_TIMESTAMP}/sub-${SUBJECT}/${ROI}/amplitudes_z.npy"

if [ ! -f "$ALIGNED_PATH" ]; then
    echo "WARNING: Aligned data not found at: $ALIGNED_PATH"
    echo "Skipping after alignment step."
    exit 0
fi

python analysis/validation/scripts/05_decoder_model_comparison.py \
    --subject "$SUBJECT" \
    --rois "$ROI" \
    --timestamp "$ALIGNED_TIMESTAMP" \
    --dataset "$DATASET" \
    --base_dir "$BASE_DIR" \
    --aligned True \
    --models ridge forward_encoding mlp \
    --output_dir "$OUTPUT_AFTER"

AFTER_EXIT_CODE=$?

if [ $AFTER_EXIT_CODE -eq 0 ]; then
    echo "After alignment completed successfully!"
else
    echo "ERROR: After alignment failed with exit code $AFTER_EXIT_CODE"
    exit 1
fi

# ============================================================================
# Summary
# ============================================================================

echo ""
echo "========================================================================"
echo "Task completed: sub-$SUBJECT, ROI=$ROI"
echo "========================================================================"
echo "Results saved to:"
echo "  Before: $OUTPUT_BEFORE/sub-${SUBJECT}_performance_raw.json"
echo "  After:  $OUTPUT_AFTER/sub-${SUBJECT}_performance_raw.json"
echo ""
echo "End time: $(date)"
echo "========================================================================"
