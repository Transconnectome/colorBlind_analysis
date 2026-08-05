#!/bin/bash
#SBATCH --job-name=prep_align
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=0:30:00
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/prep_align_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/prep_align_%j.err

# ============================================================================
# Prepare Procrustes-aligned amplitudes for decoder comparison
#
# This script applies Procrustes alignment to test_zscore_FINAL baseline
# Must be run before decoder comparison
# ============================================================================

echo "========================================================================"
echo "Preparing Procrustes-aligned amplitudes"
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

# Create logs directory
mkdir -p analysis/validation/logs

# Variables
TIMESTAMP="test_zscore_FINAL"
DATASET="method3_header_mi"
SUBJECTS="01 02 03 05 06 07"
REFERENCE_SUBJECT="02"
ROIS="V1 V2 V3 hV4"
BASE_DIR="/scratch/connectome/haba6030/colorBlind"
OUTPUT_DIR="analysis/validation/results/aligned_amplitudes/${TIMESTAMP}_procrustes"

echo ""
echo "Settings:"
echo "  Timestamp: $TIMESTAMP"
echo "  Dataset: $DATASET"
echo "  Subjects: $SUBJECTS"
echo "  Reference: sub-$REFERENCE_SUBJECT"
echo "  ROIs: $ROIS"
echo "  Output: $OUTPUT_DIR"
echo ""

# Run alignment
python analysis/validation/scripts/00_prepare_aligned_amplitudes.py \
    --timestamp "$TIMESTAMP" \
    --dataset "$DATASET" \
    --subjects $SUBJECTS \
    --reference_subject "$REFERENCE_SUBJECT" \
    --rois $ROIS \
    --base_dir "$BASE_DIR" \
    --output_dir "$OUTPUT_DIR"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "========================================================================"
    echo "Alignment preparation completed successfully!"
    echo "========================================================================"
    echo "Output directory: $OUTPUT_DIR"
    echo ""
    echo "Next steps:"
    echo "1. Verify alignment by checking disparity values in:"
    echo "   $OUTPUT_DIR/alignment_summary.json"
    echo ""
    echo "2. Run decoder comparison test:"
    echo "   sbatch analysis/validation/scripts/run_decoder_test_sub01.sbatch"
    echo ""
    echo "3. After validation, run full array job:"
    echo "   sbatch analysis/validation/scripts/run_decoder_comparison.sbatch"
    echo "========================================================================"
else
    echo ""
    echo "ERROR: Alignment preparation failed with exit code $EXIT_CODE"
    exit 1
fi

echo "End time: $(date)"
echo "========================================================================"
