#!/bin/bash
# Run C010 pipeline for all subjects and ROIs (with residuals)

SUBJECTS="01 02 03 04 05 06 07 08 09 10"
ROIS="V1 V2 V3 V4"

echo "Running C010 Pipeline with Residuals"
echo "====================================="
echo ""

for sub in $SUBJECTS; do
    for roi in $ROIS; do
        echo "Processing sub-${sub} ${roi}..."
        python run_full_dataset_C010.py --subject ${sub} --roi ${roi}

        if [ $? -ne 0 ]; then
            echo "ERROR: Failed for sub-${sub} ${roi}"
        fi
    done
done

echo ""
echo "✅ All pairs completed!"
