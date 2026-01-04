#!/bin/bash
#SBATCH --job-name=b16_deob_det
#SBATCH --nodelist=node2
#SBATCH --array=0-8
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32GB
#SBATCH --time=3:00:00
#SBATCH --output=logs/feature_selection/baseline16_deob_determin_sub-%a_%j.out
#SBATCH --error=logs/feature_selection/baseline16_deob_determin_sub-%a_%j.err

# ============================================================================
# SLURM Batch Script: Baseline 16 (Config 16) - DEOBLIQUE_V2 DETERMINISTIC
# ============================================================================
#
# Configuration: Config 16 (Perfect HRF Representativeness)
#   - Dataset: deoblique_v2 (fmriprep_out_deoblique_v2)
#   - ROI Pipeline: roi_pipeline_deob_determin (binarize=True, binary mask)
#   - Smoothing: 6mm ← Smoothing for perfect HRF repr
#   - High-pass: None (NO high-pass filter) ← KEY for high HRF repr
#   - Motion: None
#   - CompCor: None
#   - Drift: polynomial
#   - Voxel normalization: None
#   - PCA: 30 components
#
# Expected Performance (Grid Search):
#   - HRF representativeness: 0.905 (high, would be 1.0 at 8mm)
#   - SNR: 51.27 (much higher than config 1)
#   - Classification accuracy: Unknown (to be tested)
#
# Job Array Processing:
#   - 9 parallel jobs (array 0-8), one per subject
#   - Each job processes: 4 ROIs (V1, V2, V3, hV4)
#   - Total: 9 subjects × 4 ROIs = 36 analyses
#   - Note: Excludes sub-04 (no V1 signal)
#
# Usage:
#   sbatch run_all_subjects_baseline16_deob.sbatch
#
# Output (per subject):
#   - logs/feature_selection/baseline16_deob_determin_sub-{ARRAY_ID}_{JOB_ID}.out
#   - derivatives/BH2009_deoblique_v2/baseline16_deob_determin/
#
# ============================================================================

echo "================================================================"
echo "Baseline 16 (DEOBLIQUE_V2 DETERMINISTIC) Analysis - Subject ${SLURM_ARRAY_TASK_ID}"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Start: $(date)"
echo "================================================================"

# Fixed configuration for Baseline 16 (Config 16) - DETERMINISTIC
DATASET="deoblique_v2"
ROI_PIPELINE_DIR="roi_pipeline_deob_determin"
SMOOTH=6  # 6mm smoothing (KEY for high HRF repr + high SNR)
HIGHPASS=""  # NO high-pass filter (KEY difference)
MOTION="none"
COMPCOR=""
DRIFT="per_run"
STANDARDIZE=""
USE_PCA="--use-pca"
N_COMPONENTS=30

# Map SLURM_ARRAY_TASK_ID to subject (excludes sub-04: no V1 signal)
SUBJECTS=(01 02 03 05 06 07 08 09 10)
ROIS=(V1 V2 V3 hV4)

# Get subject for this array task
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

# Display configuration
echo ""
echo "Configuration (Baseline 16 - DEOBLIQUE_V2 DETERMINISTIC):"
echo "  Subject: ${SUBJECT}"
echo "  Dataset: ${DATASET}"
echo "  ROI Pipeline: ${ROI_PIPELINE_DIR} (binary mask, binarize=True)"
echo "  Smoothing FWHM: ${SMOOTH}mm ← TESTING HIGH SNR + HIGH HRF REPR"
echo "  High-pass filter: None ← TESTING HIGH HRF REPRESENTATIVENESS"
echo "  Motion confounds: ${MOTION} (none)"
echo "  CompCor: No"
echo "  Drift model: ${DRIFT} (per-run drift regressors)"
echo "  Standardize: None"
echo "  Use PCA: Yes (${N_COMPONENTS} components)"
echo ""
echo "Expected Grid Search Metrics:"
echo "  HRF representativeness: 0.905 (high, would be 1.0 at 8mm)"
echo "  SNR: 51.27 (5x higher than config 1)"
echo ""

# Generate timestamp
TIMESTAMP="baseline16_deob_determin"
echo "Timestamp: ${TIMESTAMP}"
echo ""

# Create log directory if it doesn't exist
mkdir -p logs/feature_selection

# Activate conda environment
echo "Activating conda environment..."
source ~/.bashrc
conda activate nilearn

# Initialize counters
SUCCESS_COUNT=0
FAIL_COUNT=0
NUM_ROIS=${#ROIS[@]}

echo ""
echo "================================================================"
echo "Processing Subject ${SUBJECT}: ${NUM_ROIS} ROIs"
echo "================================================================"
echo ""

# Loop through all ROIs for this subject
for i in $(seq 0 $((NUM_ROIS-1))); do
    ROI=${ROIS[$i]}

    echo "=== [$((i+1))/${NUM_ROIS}] Processing: Subject ${SUBJECT}, ROI ${ROI} ==="
    echo "Start time: $(date '+%H:%M:%S')"
    echo ""

    # Run Python script
    python fir_reconstruction_BH2009_system_clean.py \
        --subject $SUBJECT \
        --roi $ROI \
        --dataset $DATASET \
        --roi-pipeline-dir $ROI_PIPELINE_DIR \
        --timestamp $TIMESTAMP \
        --smooth $SMOOTH \
        $HIGHPASS \
        --motion $MOTION \
        $COMPCOR \
        --drift $DRIFT \
        $STANDARDIZE \
        $USE_PCA \
        --n-components $N_COMPONENTS

    # Check exit status
    EXIT_CODE=$?
    echo ""
    echo "End time: $(date '+%H:%M:%S')"

    if [ $EXIT_CODE -eq 0 ]; then
        echo "✓ Success: Subject ${SUBJECT}, ROI ${ROI}"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "✗ Failed: Subject ${SUBJECT}, ROI ${ROI} (exit code: ${EXIT_CODE})"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi

    echo "---"
    echo ""
done

echo ""
echo "================================================================"
echo "Subject ${SUBJECT}: All ${NUM_ROIS} ROIs complete"
echo "================================================================"
echo ""
echo "Summary for Subject ${SUBJECT}:"
echo "  Successful: ${SUCCESS_COUNT}/${NUM_ROIS}"
echo "  Failed: ${FAIL_COUNT}/${NUM_ROIS}"
if [ $NUM_ROIS -gt 0 ]; then
    echo "  Success rate: $(echo "scale=1; $SUCCESS_COUNT * 100 / $NUM_ROIS" | bc)%"
fi
echo ""
echo "Results saved to: derivatives/BH2009_${DATASET}/${TIMESTAMP}/"
echo ""
echo "Completion time: $(date)"
echo "================================================================"

# Exit with error if any runs failed
if [ $FAIL_COUNT -gt 0 ]; then
    echo ""
    echo "⚠️  Warning: $FAIL_COUNT ROIs failed for subject ${SUBJECT}"
    echo "Check log: logs/feature_selection/baseline16_deob_determin_sub-${SLURM_ARRAY_TASK_ID}_${SLURM_JOB_ID}.{out,err}"
    exit 1
else
    echo ""
    echo "✓ Subject ${SUBJECT}: All ROIs completed successfully!"
    exit 0
fi
