#!/bin/bash
#
# Create T1w brain masks in MNI space for Method 3
# Run this after Method 3 completion
#

set -e

SUBJECTS=(01 03 06)
OUTPUT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/method3_header_mi"
MNI_TEMPLATE="/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz"

for SUBJECT in "${SUBJECTS[@]}"; do
    echo "Processing sub-${SUBJECT}..."

    WORK_DIR="/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/work_method3_sub-${SUBJECT}"
    ANAT_DIR="${OUTPUT_DIR}/sub-${SUBJECT}/anat"

    mkdir -p ${ANAT_DIR}

    # Input files (created during Method 3 execution)
    T1W_BRAIN="${WORK_DIR}/sub-${SUBJECT}_T1w_brain.nii.gz"
    T1W_TO_MNI_WARP="${OUTPUT_DIR}/sub-${SUBJECT}/transforms/sub-${SUBJECT}_t1w_to_mni_warp.nii.gz"
    T1W_TO_MNI_MAT="${OUTPUT_DIR}/sub-${SUBJECT}/transforms/sub-${SUBJECT}_t1w_to_mni_affine.mat"

    # Output T1w mask in MNI space
    T1W_MASK_MNI="${ANAT_DIR}/sub-${SUBJECT}_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"

    if [ ! -f "${T1W_BRAIN}" ]; then
        echo "❌ ERROR: T1w brain not found: ${T1W_BRAIN}"
        continue
    fi

    if [ ! -f "${T1W_TO_MNI_WARP}" ]; then
        echo "❌ ERROR: Warp not found: ${T1W_TO_MNI_WARP}"
        continue
    fi

    # Apply warp to T1w brain mask
    echo "  Creating T1w mask in MNI space..."
    applywarp \
        --in=${T1W_BRAIN} \
        --ref=${MNI_TEMPLATE} \
        --out=${T1W_MASK_MNI} \
        --warp=${T1W_TO_MNI_WARP} \
        --premat=${T1W_TO_MNI_MAT} \
        --interp=nn

    # Binarize
    fslmaths ${T1W_MASK_MNI} -bin ${T1W_MASK_MNI}

    echo "  ✅ Created: $(basename ${T1W_MASK_MNI})"
done

echo ""
echo "✅ All T1w masks created in MNI space"
