#!/bin/bash
# check_roi_masks.sh
# Check which ROI masks exist for each subject
# Usage: bash check_roi_masks.sh

SUBJECTS="01 02 03 04"
ROIS="V1 V2 V3 hV4"

echo "=========================================="
echo "ROI Mask Availability Check"
echo "=========================================="
echo ""

TOTAL_MASKS=0
EXISTING_MASKS=0
MISSING_MASKS=0

for SUBJECT in $SUBJECTS; do
    echo "Subject: sub-${SUBJECT}"
    echo "----------------------------------------"

    for ROI in $ROIS; do
        ROI_MASK_PATH="derivatives/sub-${SUBJECT}/roi/sub-${SUBJECT}_${ROI}_mask.nii.gz"

        if [ -f "$ROI_MASK_PATH" ]; then
            VOXELS=$(python -c "import nibabel as nib; import numpy as np; print(int(np.sum(nib.load('$ROI_MASK_PATH').get_fdata() > 0)))" 2>/dev/null)
            if [ $? -eq 0 ]; then
                echo "  ✓ $ROI: $VOXELS voxels"
            else
                echo "  ✓ $ROI: exists"
            fi
            EXISTING_MASKS=$((EXISTING_MASKS + 1))
        else
            echo "  ✗ $ROI: missing"
            MISSING_MASKS=$((MISSING_MASKS + 1))
        fi
        TOTAL_MASKS=$((TOTAL_MASKS + 1))
    done
    echo ""
done

echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Total expected masks: $TOTAL_MASKS"
echo "Existing masks: $EXISTING_MASKS"
echo "Missing masks: $MISSING_MASKS"
echo ""

if [ $MISSING_MASKS -gt 0 ]; then
    echo "⚠ Some ROI masks are missing"
    echo "  They will be built automatically when you run the analysis"
    echo "  or you can build them manually with:"
    echo "    python build_roi_masks.py --subject XX"
else
    echo "✓ All ROI masks exist!"
fi
echo ""
