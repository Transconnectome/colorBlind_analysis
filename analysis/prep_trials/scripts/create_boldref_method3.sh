#!/bin/bash
# =============================================================================
# Create BOLD Reference Images for method3_header_mi Dataset
# =============================================================================
#
# Since method3_header_mi preprocessing didn't generate boldref files,
# this script extracts a single reference volume from each BOLD timeseries.
#
# Usage:
#   bash create_boldref_method3.sh              # All subjects
#   bash create_boldref_method3.sh 01           # Single subject
#   bash create_boldref_method3.sh 01 02 03     # Specific subjects
#
# Requirements: FSL (fslroi command)
#
# =============================================================================

set -e  # Exit on error

# Configuration
FMRIPREP_DIR="/storage/connectome/haba6030/fmriprep_out_method3_header_mi"
ALL_SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
RUNS=(1 2 3 4 5 6)

# Determine which subjects to process
if [ $# -eq 0 ]; then
    SUBJECTS=("${ALL_SUBJECTS[@]}")
    echo "Processing all subjects: ${SUBJECTS[@]}"
else
    SUBJECTS=("$@")
    echo "Processing specified subjects: ${SUBJECTS[@]}"
fi

echo ""
echo "================================================================================"
echo "Creating BOLD Reference Images for method3_header_mi"
echo "================================================================================"
echo "Method: Extract middle volume from BOLD timeseries"
echo "Output: *_boldref.nii.gz files in func/ directory"
echo "================================================================================"
echo ""

# Check if FSL is available
if ! command -v fslroi &> /dev/null; then
    echo "❌ ERROR: FSL (fslroi) not found!"
    echo "Please load FSL module or activate FSL environment:"
    echo "  module load fsl"
    echo "  or"
    echo "  source \$FSLDIR/etc/fslconf/fsl.sh"
    exit 1
fi

echo "✓ FSL found: $(which fslroi)"
echo ""

# Process each subject
TOTAL_SUCCESS=0
TOTAL_SKIP=0
TOTAL_FAIL=0

for SUBJECT in "${SUBJECTS[@]}"; do
    echo "--------------------------------------------------------------------------------"
    echo "Subject: sub-${SUBJECT}"
    echo "--------------------------------------------------------------------------------"

    SUBJ_DIR="${FMRIPREP_DIR}/sub-${SUBJECT}/func"

    if [ ! -d "$SUBJ_DIR" ]; then
        echo "⚠️  WARNING: Subject directory not found: $SUBJ_DIR"
        echo "   Skipping sub-${SUBJECT}"
        echo ""
        continue
    fi

    for RUN in "${RUNS[@]}"; do
        BOLD_FILE="${SUBJ_DIR}/sub-${SUBJECT}_task-rsvp_run-${RUN}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
        BOLDREF_FILE="${SUBJ_DIR}/sub-${SUBJECT}_task-rsvp_run-${RUN}_space-MNI152NLin2009cAsym_res-2_boldref.nii.gz"

        # Check if BOLD file exists
        if [ ! -f "$BOLD_FILE" ]; then
            echo "  ⚠️  Run ${RUN}: BOLD file not found, skipping"
            TOTAL_SKIP=$((TOTAL_SKIP + 1))
            continue
        fi

        # Check if boldref already exists
        if [ -f "$BOLDREF_FILE" ]; then
            echo "  ✓ Run ${RUN}: boldref already exists, skipping"
            TOTAL_SKIP=$((TOTAL_SKIP + 1))
            continue
        fi

        # Get number of volumes in BOLD timeseries
        NVOLS=$(fslinfo "$BOLD_FILE" | grep "^dim4" | awk '{print $2}')

        if [ -z "$NVOLS" ] || [ "$NVOLS" -eq 0 ]; then
            echo "  ❌ Run ${RUN}: Failed to get number of volumes"
            TOTAL_FAIL=$((TOTAL_FAIL + 1))
            continue
        fi

        # Extract middle volume (more stable than first volume)
        MIDDLE_VOL=$((NVOLS / 2))

        echo -n "  Processing Run ${RUN}: Extracting volume ${MIDDLE_VOL}/${NVOLS}... "

        if fslroi "$BOLD_FILE" "$BOLDREF_FILE" $MIDDLE_VOL 1 2>/dev/null; then
            echo "✓"
            TOTAL_SUCCESS=$((TOTAL_SUCCESS + 1))
        else
            echo "❌ FAILED"
            TOTAL_FAIL=$((TOTAL_FAIL + 1))
        fi
    done

    echo ""
done

echo "================================================================================"
echo "Summary"
echo "================================================================================"
echo "  Created: ${TOTAL_SUCCESS} boldref files"
echo "  Skipped: ${TOTAL_SKIP} files (already exist or BOLD not found)"
echo "  Failed:  ${TOTAL_FAIL} files"
echo "================================================================================"

if [ $TOTAL_FAIL -gt 0 ]; then
    echo ""
    echo "⚠️  Some files failed to process. Please check the errors above."
    exit 1
fi

if [ $TOTAL_SUCCESS -gt 0 ]; then
    echo ""
    echo "✓ Successfully created ${TOTAL_SUCCESS} boldref files!"
    echo ""
    echo "Next steps:"
    echo "  1. Verify a sample boldref file:"
    echo "     fslinfo ${FMRIPREP_DIR}/sub-01/func/sub-01_task-rsvp_run-1_*_boldref.nii.gz"
    echo ""
    echo "  2. Run the memory diagnostic:"
    echo "     bash analysis/comprehensive/diagnose_memory.sh 01"
    echo ""
    echo "  3. Proceed with the pipeline:"
    echo "     sbatch analysis/comprehensive/phase0_parallel_node4_throttle.sbatch"
fi

echo ""
