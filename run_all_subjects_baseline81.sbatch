#!/bin/bash
#SBATCH --job-name=baseline81
#SBATCH --nodelist=node2
#SBATCH --array=0-9
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32GB
#SBATCH --time=3:00:00
#SBATCH --output=logs/feature_selection/baseline81_sub-%a_%j.out
#SBATCH --error=logs/feature_selection/baseline81_sub-%a_%j.err

# ============================================================================
# SLURM Batch Script: Baseline 81 (Smooth=6, Standardize=Yes)
# ============================================================================
#
# Configuration: Config 81
#   - Smoothing: 6mm
#   - High-pass: 0.01 Hz
#   - Motion: cosine
#   - Drift: none
#   - Standardize: Yes
#   - PCA: 30 components
#
# Job Array Processing:
#   - 10 parallel jobs (array 0-9), one per subject
#   - Each job processes: 4 ROIs (V1, V2, V3, hV4)
#   - Total: 10 subjects × 4 ROIs = 40 analyses
#
# Usage:
#   sbatch run_all_subjects_baseline81.sbatch
#
# Output (per subject):
#   - logs/feature_selection/baseline81_sub-{ARRAY_ID}_{JOB_ID}.out
#
# ============================================================================

echo "================================================================"
echo "Baseline 81 Analysis - Subject ${SLURM_ARRAY_TASK_ID}"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Start: $(date)"
echo "================================================================"

# Fixed configuration for Baseline 81
DATASET="deoblique_v2"
SMOOTH=6
HIGHPASS="--highpass 0.01"
MOTION="cosine"
COMPCOR=""
DRIFT="none"
STANDARDIZE="--standardize"
USE_PCA="--use-pca"
N_COMPONENTS=30

# Map SLURM_ARRAY_TASK_ID to subject
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
ROIS=(V1 V2 V3 hV4)

# Get subject for this array task
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

# Display configuration
echo ""
echo "Configuration (Baseline 81):"
echo "  Subject: ${SUBJECT}"
echo "  Dataset: ${DATASET}"
echo "  Smoothing FWHM: ${SMOOTH}mm"
echo "  High-pass filter: 0.01 Hz"
echo "  Motion confounds: ${MOTION}"
echo "  CompCor: No"
echo "  Drift model: ${DRIFT}"
echo "  Standardize: Yes"
echo "  Use PCA: Yes (${N_COMPONENTS} components)"
echo ""

# Generate timestamp (shared across array tasks if started together)
TIMESTAMP="baseline81"
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
echo "Results saved to: derivatives/BH2009/${TIMESTAMP}/"
echo ""
echo "Completion time: $(date)"
echo "================================================================"

# Exit with error if any runs failed
if [ $FAIL_COUNT -gt 0 ]; then
    echo ""
    echo "⚠️  Warning: $FAIL_COUNT ROIs failed for subject ${SUBJECT}"
    echo "Check log: logs/feature_selection/baseline81_sub-${SLURM_ARRAY_TASK_ID}_${SLURM_JOB_ID}.{out,err}"
    exit 1
else
    echo ""
    echo "✓ Subject ${SUBJECT}: All ROIs completed successfully!"
    exit 0
fi
