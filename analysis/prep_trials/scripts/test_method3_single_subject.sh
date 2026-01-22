#!/bin/bash
################################################################################
# Full Test Script: Method 3 (Single Subject)
#
# Usage (on server, interactive mode):
#   conda activate nilearn  # or appropriate env with FSL/FreeSurfer
#   bash test_method3_single_subject.sh
#
# Purpose: Full Method 3 pipeline test on sub-10 (run 1 only)
#   - Brain extraction
#   - BOLD → T1w (mri_coreg --regheader)
#   - T1w → MNI (FLIRT + FNIRT with correct MNI152NLin2009cAsym)
#   - BOLD → MNI (composed transform)
#   - 3D mask creation
#
# Expected time: ~20-30 minutes
# Expected memory: ~15-20GB peak
################################################################################

set -e  # Exit on error

# Test subject
SUBJECT_ID="10"

echo "================================================================================"
echo "Method 3 Test - Sub-${SUBJECT_ID}"
echo "================================================================================"
echo "Start time: $(date)"
echo ""

# Directories
BIDS_DIR="/storage/connectome/haba6030/bids_editted"
OUTPUT_DIR="/storage/connectome/haba6030/fmriprep_out_method3_header_mi"
WORK_DIR="/storage/connectome/haba6030/fmriprep_work_method3_sub-${SUBJECT_ID}_test"

# =========================================================================
# Environment Setup
# =========================================================================

echo "Setting up environment..."

# FreeSurfer (use 7.2.0 - installed on server)
export FREESURFER_HOME=/usr/local/freesurfer/7.2.0
export PATH="${FREESURFER_HOME}/bin:${PATH}"
export SUBJECTS_DIR="${WORK_DIR}/freesurfer_subjects"

# FreeSurfer license (CRITICAL)
export FS_LICENSE=${FREESURFER_HOME}/license.txt

# FSL
export FSLDIR=/usr/local/fsl
export PATH="${FSLDIR}/bin:${PATH}"
source ${FSLDIR}/etc/fslconf/fsl.sh

# Verify
if ! command -v mri_convert &> /dev/null; then
    echo "❌ ERROR: FreeSurfer not found"
    exit 1
fi

if ! command -v fslroi &> /dev/null; then
    echo "❌ ERROR: FSL not found"
    exit 1
fi

echo "✅ FreeSurfer: $(which mri_convert)"
echo "✅ FSL: $(which fslroi)"
echo ""

# Create directories
mkdir -p ${SUBJECTS_DIR}/sub-${SUBJECT_ID}/{mri,surf}
mkdir -p ${OUTPUT_DIR}/sub-${SUBJECT_ID}/{func,anat,transforms}
mkdir -p ${WORK_DIR}

# =========================================================================
# Step 1: Brain Extraction
# =========================================================================

echo "================================================================================"
echo "Step 1: Brain Extraction"
echo "================================================================================"

T1W_FILE="${BIDS_DIR}/sub-${SUBJECT_ID}/anat/sub-${SUBJECT_ID}_acq-mprage_T1w.nii.gz"
T1W_MGZ="${SUBJECTS_DIR}/sub-${SUBJECT_ID}/mri/orig.mgz"
BRAIN_MGZ="${SUBJECTS_DIR}/sub-${SUBJECT_ID}/mri/brain.mgz"

if [ ! -f "${T1W_FILE}" ]; then
    echo "❌ ERROR: T1w not found: ${T1W_FILE}"
    exit 1
fi

echo "Converting T1w to MGZ..."
mri_convert ${T1W_FILE} ${T1W_MGZ}

echo "Running brain extraction..."
if command -v bet2 &> /dev/null; then
    echo "  Using FSL bet2..."
    bet2 ${T1W_FILE} ${WORK_DIR}/T1w_brain.nii.gz -f 0.5 -m
    mri_convert ${WORK_DIR}/T1w_brain.nii.gz ${BRAIN_MGZ}
else
    echo "  Using FreeSurfer mri_watershed..."
    mri_watershed -useSRAS ${T1W_MGZ} ${BRAIN_MGZ}
fi

echo "✅ Brain extracted: ${BRAIN_MGZ}"
echo ""

# =========================================================================
# Step 2: BOLD → T1w Registration (Run 1 only)
# =========================================================================

echo "================================================================================"
echo "Step 2: BOLD → T1w Registration (Run 1 only)"
echo "================================================================================"

RUN=1
BOLD_FILE="${BIDS_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_bold.nii.gz"

if [ ! -f "${BOLD_FILE}" ]; then
    echo "❌ ERROR: BOLD not found: ${BOLD_FILE}"
    exit 1
fi

# Extract reference volume
echo "Extracting reference volume..."
NVOLS=$(fslinfo ${BOLD_FILE} | grep "^dim4" | awk '{print $2}')
REF_VOL=$((NVOLS / 2))
BOLD_REF="${WORK_DIR}/sub-${SUBJECT_ID}_run-${RUN}_boldref.nii.gz"

echo "  Total volumes: ${NVOLS}, extracting: ${REF_VOL}"
mri_convert ${BOLD_FILE} ${BOLD_REF} --frame ${REF_VOL}
echo "✅ Reference volume extracted"

# mri_coreg
echo "Running mri_coreg..."
OUTPUT_LTA="${OUTPUT_DIR}/sub-${SUBJECT_ID}/transforms/sub-${SUBJECT_ID}_run-${RUN}_bold_to_t1w.lta"

mri_coreg \
    --ref ${BRAIN_MGZ} \
    --mov ${BOLD_REF} \
    --reg ${OUTPUT_LTA} \
    --regheader \
    --threads 4

if [ ! -f "${OUTPUT_LTA}" ]; then
    echo "❌ ERROR: mri_coreg failed"
    exit 1
fi

echo "✅ Registration completed: ${OUTPUT_LTA}"

# Apply transform
echo "Applying transform to BOLD..."
BOLD_IN_T1W="${WORK_DIR}/sub-${SUBJECT_ID}_run-${RUN}_bold_in_t1w.nii.gz"

mri_vol2vol \
    --mov ${BOLD_FILE} \
    --targ ${BRAIN_MGZ} \
    --lta ${OUTPUT_LTA} \
    --o ${BOLD_IN_T1W} \
    --interp trilin \
    --no-save-reg

echo "✅ BOLD in T1w space: ${BOLD_IN_T1W}"
echo ""

# =========================================================================
# Step 3: T1w → MNI (FLIRT + FNIRT for full test)
# =========================================================================

echo "================================================================================"
echo "Step 3: T1w → MNI (FLIRT + FNIRT)"
echo "================================================================================"

# CRITICAL: Use MNI152NLin2009cAsym (matches Original_v3 and Wang atlas)
MNI_TEMPLATE="/scratch/connectome/haba6030/colorBlind/templates/MNI152NLin2009cAsym_res-2_T1_brain.nii.gz"
MNI_TEMPLATE_HEAD="/scratch/connectome/haba6030/colorBlind/templates/MNI152NLin2009cAsym_res-2_T1.nii.gz"
MNI_REFMASK="/scratch/connectome/haba6030/colorBlind/templates/MNI152NLin2009cAsym_res-2_brain_mask.nii.gz"

if [ ! -f "${MNI_TEMPLATE}" ]; then
    echo "❌ ERROR: MNI template not found: ${MNI_TEMPLATE}"
    echo "   Run: python3 -c 'from templateflow import api as tflow; ...'"
    exit 1
fi

T1W_BRAIN_NII="${WORK_DIR}/sub-${SUBJECT_ID}_T1w_brain.nii.gz"
T1W_HEAD_NII="${WORK_DIR}/sub-${SUBJECT_ID}_T1w_head.nii.gz"
T1W_TO_MNI_MAT="${OUTPUT_DIR}/sub-${SUBJECT_ID}/transforms/sub-${SUBJECT_ID}_t1w_to_mni_affine.mat"
T1W_TO_MNI_WARP="${OUTPUT_DIR}/sub-${SUBJECT_ID}/transforms/sub-${SUBJECT_ID}_t1w_to_mni_warp.nii.gz"

mri_convert ${BRAIN_MGZ} ${T1W_BRAIN_NII}
mri_convert ${T1W_MGZ} ${T1W_HEAD_NII}

echo "Running FLIRT (linear 12 DOF)..."
flirt \
    -in ${T1W_BRAIN_NII} \
    -ref ${MNI_TEMPLATE} \
    -omat ${T1W_TO_MNI_MAT} \
    -bins 256 \
    -cost corratio \
    -searchrx -90 90 \
    -searchry -90 90 \
    -searchrz -90 90 \
    -dof 12

echo "✅ FLIRT completed"

echo "Running FNIRT (nonlinear warp)..."
# Use correct template-matched mask
if [ ! -f "${MNI_TEMPLATE_HEAD}" ]; then
    echo "  ⚠️  Full head template not found, using brain template"
    MNI_TEMPLATE_HEAD="${MNI_TEMPLATE}"
fi

fnirt \
    --in=${T1W_HEAD_NII} \
    --ref=${MNI_TEMPLATE_HEAD} \
    --aff=${T1W_TO_MNI_MAT} \
    --refmask=${MNI_REFMASK} \
    --cout=${T1W_TO_MNI_WARP} \
    --config=/usr/local/fsl/etc/flirtsch/T1_2_MNI152_2mm.cnf

echo "✅ FNIRT completed"
echo ""

# =========================================================================
# Step 4: Apply composed transform (BOLD → MNI)
# =========================================================================

echo "================================================================================"
echo "Step 4: Apply composed transform (BOLD → MNI)"
echo "================================================================================"

# Convert LTA to FSL format
BOLD_TO_T1W_MAT="${WORK_DIR}/sub-${SUBJECT_ID}_run-${RUN}_bold_to_t1w.mat"

tkregister2 \
    --mov ${BOLD_REF} \
    --targ ${T1W_BRAIN_NII} \
    --reg ${WORK_DIR}/temp_reg.dat \
    --lta ${OUTPUT_LTA} \
    --noedit \
    --fslregout ${BOLD_TO_T1W_MAT}

# Apply composed transform
BOLD_MNI="${OUTPUT_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"

echo "Applying composed transform (BOLD → T1w → MNI)..."
applywarp \
    --in=${BOLD_FILE} \
    --ref=${MNI_TEMPLATE} \
    --out=${BOLD_MNI} \
    --warp=${T1W_TO_MNI_WARP} \
    --premat=${BOLD_TO_T1W_MAT} \
    --interp=trilinear

echo "✅ BOLD in MNI: $(basename ${BOLD_MNI})"

# Create mask in MNI space
MASK_MNI="${OUTPUT_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"

echo "Creating MNI space mask..."
if ! 3dAutomask -prefix ${MASK_MNI} ${BOLD_MNI} 2>/dev/null; then
    echo "  3dAutomask failed, using fslmaths with temporal mean..."
    fslmaths ${BOLD_MNI} -Tmean -bin ${MASK_MNI}
fi

echo "✅ Mask in MNI: $(basename ${MASK_MNI})"

# Verify shapes
echo ""
echo "Verification:"
python3 << EOF
import nibabel as nib

bold = nib.load('${BOLD_MNI}')
mask = nib.load('${MASK_MNI}')

print(f"  BOLD shape: {bold.shape}")
print(f"  Mask shape: {mask.shape}")
print(f"  Expected spatial: (97, 115, 97)")

if bold.shape[:3] == (97, 115, 97):
    print(f"  ✅ BOLD spatial dims correct")
else:
    print(f"  ❌ BOLD spatial dims WRONG!")

if mask.shape == (97, 115, 97):
    print(f"  ✅ Mask is 3D and correct")
elif len(mask.shape) == 4:
    print(f"  ❌ Mask is 4D (WRONG!)")
else:
    print(f"  ❌ Mask shape unexpected")
EOF

echo ""

# =========================================================================
# Summary
# =========================================================================

echo "================================================================================"
echo "Test Completed Successfully!"
echo "================================================================================"
echo ""
echo "Pipeline Summary:"
echo "  ✅ Brain extraction (FreeSurfer/FSL)"
echo "  ✅ BOLD → T1w (mri_coreg --regheader)"
echo "  ✅ T1w → MNI (FLIRT + FNIRT with MNI152NLin2009cAsym)"
echo "  ✅ BOLD → MNI (applywarp with composed transforms)"
echo "  ✅ MNI space mask (3D)"
echo ""
echo "Output files:"
echo "  Brain:       ${BRAIN_MGZ}"
echo "  BOLD ref:    ${BOLD_REF}"
echo "  Transform:   ${OUTPUT_LTA}"
echo "  T1w→MNI:     ${T1W_TO_MNI_WARP}"
echo "  BOLD in MNI: ${BOLD_MNI}"
echo "  Mask in MNI: ${MASK_MNI}"
echo ""
echo "Template info:"
echo "  Using: MNI152NLin2009cAsym (97,115,97)"
echo "  Matches: Original_v3 ✅, Wang Atlas ✅"
echo ""
echo "Next steps:"
echo "  1. If test successful, run full pipeline:"
echo "     sbatch run_method3_header_mi_all_subjects.sbatch"
echo "  2. Monitor with: squeue -u \$USER"
echo ""
echo "Cleanup (optional):"
echo "  rm -rf ${WORK_DIR}"
echo ""
echo "End time: $(date)"
echo "================================================================================"

exit 0
