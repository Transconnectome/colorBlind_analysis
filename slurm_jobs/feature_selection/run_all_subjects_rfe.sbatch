#!/bin/bash
#SBATCH --job-name=rfe_all
#SBATCH --nodelist=node2
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32GB
#SBATCH --time=12:00:00
#SBATCH --output=logs/feature_selection/rfe_all_%j.out

# ============================================================================
# SLURM Batch Script: RFE Feature Selection for All Subject-ROI Pairs
# ============================================================================
#
# This script runs feature_selection_rfe.py for all 8 subject-ROI
# combinations with user-specified preprocessing parameters.
#
# Usage:
#   sbatch run_all_subjects_rfe.sbatch [preprocessing options]
#
# Preprocessing Options:
#   --smooth <0|6|8>        Spatial smoothing FWHM in mm (default: 0)
#   --highpass <0.01>       High-pass filter cutoff in Hz (default: none)
#   --motion <none|cosine|extended>  Motion confounds (default: none)
#   --compcor <5>           Number of aCompCor components (default: none)
#   --drift <none|per_run>  Drift modeling (default: none)
#   --standardize           Apply z-score standardization (default: false)
#
# Examples:
#   # Minimal preprocessing
#   sbatch run_all_subjects_rfe.sbatch --smooth 0 --highpass 0.01
#
#   # With standardization
#   sbatch run_all_subjects_rfe.sbatch --smooth 0 --standardize
#
#   # Subject 02 style (with drift)
#   sbatch run_all_subjects_rfe.sbatch --smooth 0 --drift per_run
#
# Note: RFE is computationally expensive!
#   - Memory: 32GB (higher than ANOVA due to iterative SVM training)
#   - Time: 12 hours (each subject-ROI pair may take 1-2 hours)
#   - Consider reducing K_VALUES in feature_selection_rfe.py if too slow
#
# ============================================================================

echo "================================================================"
echo "RFE Feature Selection - All Subjects and ROIs"
echo "Start: $(date)"
echo "================================================================"

# Parse command-line arguments for preprocessing configuration
SMOOTH=0
HIGHPASS=""
MOTION="none"
COMPCOR=""
DRIFT="none"
STANDARDIZE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --smooth)
            SMOOTH="$2"
            shift 2
            ;;
        --highpass)
            HIGHPASS="$2"
            shift 2
            ;;
        --motion)
            MOTION="$2"
            shift 2
            ;;
        --compcor)
            COMPCOR="$2"
            shift 2
            ;;
        --drift)
            DRIFT="$2"
            shift 2
            ;;
        --standardize)
            STANDARDIZE="true"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Display configuration
echo ""
echo "Preprocessing Configuration:"
echo "  Smoothing FWHM: ${SMOOTH}mm"
echo "  High-pass filter: $([ -n "$HIGHPASS" ] && echo "${HIGHPASS} Hz" || echo "None")"
echo "  Motion confounds: ${MOTION}"
echo "  CompCor: $([ -n "$COMPCOR" ] && echo "${COMPCOR} components" || echo "None")"
echo "  Drift model: ${DRIFT}"
echo "  Standardize: $([ -n "$STANDARDIZE" ] && echo "Yes" || echo "No")"
echo ""

# Generate timestamp (should match preprocessing run timestamp)
# Note: This assumes preprocessing was already run with the same config
TIMESTAMP="BHbase"  # Using fixed name for baseline runs
echo "Using timestamp: ${TIMESTAMP}"
echo ""

# Create log directory
mkdir -p logs/feature_selection

# Activate conda environment
echo "Activating conda environment..."
source ~/.bashrc
conda activate nilearn

# Define subject-ROI pairs
SUBJECTS=(01 01 01 01 02 02 02 02)
ROIS=(V1 V2 V3 hV4 V1 V2 V3 hV4)

# Initialize counters
SUCCESS_COUNT=0
FAIL_COUNT=0

echo ""
echo "================================================================"
echo "Processing 8 subject-ROI pairs"
echo "⚠️  RFE is computationally expensive - this may take several hours"
echo "================================================================"
echo ""

# Loop through all subject-ROI pairs
for i in {0..7}; do
    SUBJECT=${SUBJECTS[$i]}
    ROI=${ROIS[$i]}

    echo "=== [$((i+1))/8] RFE Feature Selection: Subject ${SUBJECT}, ROI ${ROI} ==="
    echo "Start time: $(date '+%H:%M:%S')"
    echo ""

    # Build Python command with preprocessing arguments
    CMD="python feature_selection_rfe.py \
        --subject $SUBJECT \
        --roi $ROI \
        --timestamp $TIMESTAMP \
        --smooth $SMOOTH \
        --motion $MOTION \
        --drift $DRIFT"

    # Add optional arguments
    [ -n "$HIGHPASS" ] && CMD="$CMD --highpass $HIGHPASS"
    [ -n "$COMPCOR" ] && CMD="$CMD --compcor $COMPCOR"
    [ -n "$STANDARDIZE" ] && CMD="$CMD --standardize"

    # Execute
    eval $CMD

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
echo "All 8 subject-ROI pairs complete"
echo "================================================================"
echo ""
echo "Summary:"
echo "  Successful: ${SUCCESS_COUNT}/8"
echo "  Failed: ${FAIL_COUNT}/8"
echo ""
echo "Results saved to: derivatives/feature_selection/"
echo ""
echo "Completion time: $(date)"
echo "================================================================"

# Exit with error if any runs failed
if [ $FAIL_COUNT -gt 0 ]; then
    exit 1
else
    exit 0
fi
