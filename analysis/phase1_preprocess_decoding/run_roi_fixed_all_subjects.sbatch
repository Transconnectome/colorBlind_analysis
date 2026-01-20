#!/bin/bash
#SBATCH --job-name=roi_fixed_all
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=4:00:00
#SBATCH --output=logs/roi_fixed_all_%j.out
#SBATCH --error=logs/roi_fixed_all_%j.err

# ============================================================================
# ROI Pipeline FIXED - ALL SUBJECTS (01-10)
# ============================================================================
# Uses AFNI 3dresample for proper affine matching
# Fixes zero variance issue from incorrect resampling
# ============================================================================

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Create necessary directories
echo "Creating required directories..."
mkdir -p logs
mkdir -p derivatives/V3_Comprehensive/ROI_mask
mkdir -p analysis/phase1_preprocess_decoding
mkdir -p analysis/utils

echo "============================================================================"
echo "ROI Pipeline - original_v3 Dataset"
echo "============================================================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Started: $(date)"
echo ""
echo "Script: roi_pipeline_comprehensive.py"
echo "Dataset: fmriprep_out_original_v3"
echo "Subjects: 01-10 (10 subjects)"
echo "ROIs per subject: V1, V2, V3, hV4 (4 ROIs)"
echo "Output: derivatives/V3_Comprehensive/ROI_mask/sub-{ID}/"
echo "============================================================================"
echo

# Define subjects
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)

TOTAL_SUBJECTS=${#SUBJECTS[@]}

echo "Processing $TOTAL_SUBJECTS subjects..."
echo

# Track progress
CURRENT=0
FAILED_COUNT=0
FAILED_LIST=""

# Loop through all subjects
for SUBJECT in "${SUBJECTS[@]}"; do
    CURRENT=$((CURRENT + 1))

    echo ""
    echo "========================================================================"
    echo "[$CURRENT/$TOTAL_SUBJECTS] Subject: sub-$SUBJECT"
    echo "========================================================================"
    echo "Started: $(date)"
    echo ""

    # Run ROI pipeline for this subject
    # Builds ROI masks from Wang Atlas for original_v3 data
    python roi_pipeline_comprehensive.py $SUBJECT

    EXIT_CODE=$?

    echo ""
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✓ Subject sub-$SUBJECT: SUCCESS (all ROIs validated)"
    else
        echo "✗ Subject sub-$SUBJECT: FAILED (exit code $EXIT_CODE)"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        FAILED_LIST="${FAILED_LIST}sub-${SUBJECT} "
    fi
    echo "Finished: $(date)"
    echo "========================================================================"
    echo ""
done

echo ""
echo "============================================================================"
echo "ROI PIPELINE COMPLETE - FINAL SUMMARY"
echo "============================================================================"
echo "Total subjects processed: $TOTAL_SUBJECTS"
echo "Successful: $((TOTAL_SUBJECTS - FAILED_COUNT))"
echo "Failed: $FAILED_COUNT"

if [ $FAILED_COUNT -gt 0 ]; then
    echo ""
    echo "Failed subjects:"
    echo "$FAILED_LIST"
fi

echo ""
echo "Results saved in: derivatives/V3_Comprehensive/ROI_mask/sub-{ID}/roi_pipeline/"
echo ""
echo "Each subject directory contains ROI masks with parameter combinations:"
echo "  - V1_mask_thr{X}_int{Y}_bin{Z}_mask{W}_gm{T}_subj{S}.nii.gz"
echo "  - V2_mask_thr{X}_int{Y}_bin{Z}_mask{W}_gm{T}_subj{S}.nii.gz"
echo "  - V3_mask_thr{X}_int{Y}_bin{Z}_mask{W}_gm{T}_subj{S}.nii.gz"
echo "  - hV4_mask_thr{X}_int{Y}_bin{Z}_mask{W}_gm{T}_subj{S}.nii.gz"
echo ""
echo "Parameter grid tested:"
echo "  - Threshold: 5, 10, 20, 35, 50 (% atlas probability)"
echo "  - Interpolation: nearest, linear"
echo "  - Binarize: True, False"
echo "  - Brain mask: none, func, epi_intersect"
echo "  - GM probseg: True, False"
echo "  - Subject ROI: True, False"
echo ""

echo "Finished: $(date)"
echo "============================================================================"

# Exit with failure if any subject failed
if [ $FAILED_COUNT -gt 0 ]; then
    exit 1
else
    exit 0
fi
