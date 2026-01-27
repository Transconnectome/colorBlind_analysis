#!/bin/bash
#SBATCH --job-name=decoder_test
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=0:30:00
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/decoder_test_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/decoder_test_%j.err

# ============================================================================
# Test Decoder Model Comparison on sub-01
#
# This script tests the pipeline on sub-01 × 4 ROIs with 3 models
# Quick validation before running full array job
# ============================================================================

echo "========================================================================"
echo "Decoder Model Comparison Test: sub-01"
echo "========================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURM_NODELIST"
echo "Start time: $(date)"
echo "========================================================================"

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Change to project directory
cd /scratch/connectome/haba6030/colorBlind

# Create logs directory if needed
mkdir -p analysis/validation/logs

# Variables
SUBJECT="01"
ROIS="V1 V2 V3 hV4"
TIMESTAMP="test_zscore_FINAL"
DATASET="method3_header_mi"
BASE_DIR="/scratch/connectome/haba6030/colorBlind"

# Output directories
OUTPUT_BEFORE="analysis/validation/results/model_comparison/test_sub01_before"
OUTPUT_AFTER="analysis/validation/results/model_comparison/test_sub01_after"

mkdir -p "$OUTPUT_BEFORE"
mkdir -p "$OUTPUT_AFTER"

echo ""
echo "========================================================================"
echo "Step 1: Before Alignment"
echo "========================================================================"

python analysis/validation/scripts/05_decoder_model_comparison.py \
    --subject "$SUBJECT" \
    --rois $ROIS \
    --timestamp "$TIMESTAMP" \
    --dataset "$DATASET" \
    --base_dir "$BASE_DIR" \
    --aligned False \
    --models ridge forward_encoding mlp \
    --output_dir "$OUTPUT_BEFORE"

if [ $? -eq 0 ]; then
    echo "Step 1 completed successfully!"
else
    echo "ERROR: Step 1 failed!"
    exit 1
fi

echo ""
echo "========================================================================"
echo "Step 2: After Alignment"
echo "========================================================================"

# Check if aligned data exists
ALIGNED_TIMESTAMP="${TIMESTAMP}_procrustes"
ALIGNED_PATH="analysis/validation/results/aligned_amplitudes/${ALIGNED_TIMESTAMP}/sub-${SUBJECT}/V1/amplitudes_z.npy"

if [ ! -f "$ALIGNED_PATH" ]; then
    echo "WARNING: Aligned data not found at: $ALIGNED_PATH"
    echo "Please run 00_prepare_aligned_amplitudes.py first!"
    exit 1
fi

python analysis/validation/scripts/05_decoder_model_comparison.py \
    --subject "$SUBJECT" \
    --rois $ROIS \
    --timestamp "$ALIGNED_TIMESTAMP" \
    --dataset "$DATASET" \
    --base_dir "$BASE_DIR" \
    --aligned True \
    --models ridge forward_encoding mlp \
    --output_dir "$OUTPUT_AFTER"

if [ $? -eq 0 ]; then
    echo "Step 2 completed successfully!"
else
    echo "ERROR: Step 2 failed!"
    exit 1
fi

echo ""
echo "========================================================================"
echo "Test completed!"
echo "========================================================================"
echo "Before results: $OUTPUT_BEFORE"
echo "After results: $OUTPUT_AFTER"
echo ""
echo "Next steps:"
echo "1. Download results to local machine:"
echo "   scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/results/model_comparison/test_sub01_* ."
echo ""
echo "2. Run visualization locally:"
echo "   python analysis/validation/scripts/05c_decoder_visualization.py \\"
echo "       --before_dir test_sub01_before \\"
echo "       --after_dir test_sub01_after \\"
echo "       --subject 01 \\"
echo "       --output_dir test_sub01_figures"
echo "========================================================================"
echo "End time: $(date)"
echo "========================================================================"
