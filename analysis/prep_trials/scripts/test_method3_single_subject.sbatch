#!/bin/bash
#SBATCH --job-name=test_m3
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/test_method3_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/test_method3_%j.err
#SBATCH --time=1:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --qos=shared
#SBATCH --nodelist=node2

################################################################################
# Quick Test Script: Method 3 (Single Subject - SBATCH version)
#
# Usage (on server):
#   sbatch test_method3_single_subject.sbatch
#
# Purpose: Test Method 3 pipeline on sub-10 only (fast validation)
################################################################################

set -e  # Exit on error

# Test subject
SUBJECT_ID="10"

echo "================================================================================"
echo "Method 3 Test - Sub-${SUBJECT_ID}"
echo "================================================================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: ${SLURM_NODELIST}"
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
source ${FSLDIR}/etc/fslconf/fsl.sh 2>/dev/null || true

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
mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs

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
    --threads ${SLURM_CPUS_PER_TASK}

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
# Step 3: T1w → MNI (FLIRT only, skip FNIRT for speed)
# =========================================================================

echo "================================================================================"
echo "Step 3: T1w → MNI (FLIRT only - fast test)"
echo "================================================================================"

MNI_TEMPLATE="/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz"
T1W_BRAIN_NII="${WORK_DIR}/sub-${SUBJECT_ID}_T1w_brain.nii.gz"
T1W_TO_MNI_MAT="${OUTPUT_DIR}/sub-${SUBJECT_ID}/transforms/sub-${SUBJECT_ID}_t1w_to_mni_affine.mat"

mri_convert ${BRAIN_MGZ} ${T1W_BRAIN_NII}

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

echo "✅ T1w → MNI linear registration completed"
echo ""
echo "NOTE: FNIRT (nonlinear) skipped for quick testing"
echo "      Full pipeline will include FNIRT"
echo ""

# =========================================================================
# Summary
# =========================================================================

echo "================================================================================"
echo "Test Completed Successfully!"
echo "================================================================================"
echo ""
echo "Outputs:"
echo "  Brain: ${BRAIN_MGZ}"
echo "  BOLD ref: ${BOLD_REF}"
echo "  Transform: ${OUTPUT_LTA}"
echo "  BOLD in T1w: ${BOLD_IN_T1W}"
echo "  T1w → MNI: ${T1W_TO_MNI_MAT}"
echo ""
echo "Next step: Run full pipeline with run_method3_header_mi_all_subjects.sbatch"
echo ""
echo "Cleanup (optional):"
echo "  rm -rf ${WORK_DIR}"
echo ""
echo "End time: $(date)"
echo "================================================================================"

exit 0
