#!/bin/bash
################################################################################
# Local Test: Generate confounds with aCompCor for one subject/run
#
# Purpose: Verify aCompCor implementation before running on server
#
# Usage:
#   bash test_generate_confounds_local.sh
#
# Expected outputs:
#   - Confounds TSV file with a_comp_cor_00 ~ a_comp_cor_09
#   - QC visualizations: tissue_masks.png, acompcor_qc.png
#   - Mask statistics JSON
################################################################################

set -e

# Test configuration
SUBJECT_ID="01"
RUN=1
METHOD="method3_header_mi"

echo "================================================================================"
echo "Local Test: Generate Confounds with aCompCor"
echo "================================================================================"
echo "Subject: sub-${SUBJECT_ID}"
echo "Run: ${RUN}"
echo "Method: ${METHOD}"
echo ""

# This script assumes you're testing with local files
# Modify paths if needed

python generate_confounds.py \
    --subject ${SUBJECT_ID} \
    --run ${RUN} \
    --method ${METHOD} \
    --tr 1.5

echo ""
echo "================================================================================"
echo "Test Complete"
echo "================================================================================"
echo ""
echo "Check outputs:"
echo "  1. Confounds file: ..../func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_desc-confounds_timeseries.tsv"
echo "  2. QC visualizations: ..../qc/sub-${SUBJECT_ID}/"
echo ""
echo "Verify confounds file contains:"
echo "  - Motion: trans_x/y/z, rot_x/y/z"
echo "  - aCompCor: a_comp_cor_00 ~ a_comp_cor_09 (10 components total)"
echo "  - Tissue signals: csf, white_matter"
echo "  - Drift: cosine00, cosine01, ..."
echo ""
echo "Inspect QC plots:"
echo "  - tissue_masks.png: Check CSF (blue) and WM (red) coverage"
echo "  - acompcor_qc.png: Verify component timeseries and variance explained"
echo ""
