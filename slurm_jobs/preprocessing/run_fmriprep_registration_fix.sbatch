#!/bin/bash
#SBATCH --job-name=fmriprep_regfix
#SBATCH --array=0-6
#SBATCH --output=logs/fmriprep_regfix_%A_%a.out
#SBATCH --error=logs/fmriprep_regfix_%A_%a.err
#SBATCH --time=6:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --qos=shared
#SBATCH --nodelist=node2

################################################################################
# fMRIPrep Registration Fix - Problematic Subjects
#
# Purpose: Fix BOLD-T1w BBR registration for subjects with V1 ROI overlap issues
#
# Problem subjects:
#   - ZERO overlap (critical): sub-01, 03, 04, 09, 10
#   - Partial overlap: sub-02, 08
# Issue: BOLD-T1w registration quality is suboptimal
#        → MNI transformation loses posterior coverage
#        → V1 ROI overlap = 0%
#
# Solution: Re-run fMRIPrep with improved registration parameters:
#   - --bold2t1w-dof 9: More flexible affine (9 DOF vs default 6)
#   - --bold2t1w-init register: Better FLIRT initialization
#   - --force-bbr: Ensure BBR is used
#   - --fs-no-reconall: Skip FreeSurfer, use ANTs for T1w normalization (faster)
#
# Input:  /storage/connectome/haba6030/colorBlind_data_deoblique (AFNI deobliqued)
# Anat:   /storage/connectome/haba6030/fmriprep_out_afni_deoblique (reuse T1w)
# Output: /storage/connectome/haba6030/fmriprep_out_registration_fix
# Work:   /storage/connectome/haba6030/fmriprep_work_registration_fix
#
# Author: Claude Code
# Date: 2025-12-28
################################################################################

set -e

# Problem subjects (zero + partial V1 overlap)
# ZERO: 01, 03, 04, 09, 10
# Partial: 02, 08
SUBJECTS=(01 02 03 04 08 09 10)
SUBJ_ID=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

echo "================================================================================"
echo "fMRIPrep Registration Fix - Sub-${SUBJ_ID}"
echo "================================================================================"
echo "Job ID: ${SLURM_JOB_ID} (Array task: ${SLURM_ARRAY_TASK_ID})"
echo "Node: ${SLURM_NODELIST}"
echo "Start time: $(date)"
echo ""
echo "Problem: BOLD-T1w registration quality is suboptimal"
echo "  → Native BOLD mask Z:10-88 (normal)"
echo "  → MNI BOLD mask Z:0-46 (posterior loss!)"
echo "  → V1 ROI overlap: 0/810 (0%)"
echo ""
echo "Solution: Improved registration parameters"
echo "  ✅ --bold2t1w-dof 9 (more flexible)"
echo "  ✅ --bold2t1w-init register (better initialization)"
echo "  ✅ --force-bbr (ensure BBR)"
echo "  ✅ --fs-no-reconall (skip FreeSurfer, use ANTs)"
echo "================================================================================"
echo ""

# Configuration
BIDS_DIR="/storage/connectome/haba6030/colorBlind_data_deoblique"
ANAT_DERIVATIVES="/storage/connectome/haba6030/fmriprep_out_afni_deoblique"
OUTPUT_DIR="/storage/connectome/haba6030/fmriprep_out_registration_fix"
WORK_DIR="/storage/connectome/haba6030/fmriprep_work_registration_fix/sub-${SUBJ_ID}"

# Singularity settings - SAME AS WORKING SCRIPTS
APPTAINER=/usr/local/bin/singularity
FMRIPREP_IMG=/storage/connectome/haba6030/fmriprep-23.2.3.sif
FS_LICENSE=/storage/connectome/haba6030/fs_license.txt

echo "Configuration:"
echo "  Input (BIDS):        ${BIDS_DIR}/sub-${SUBJ_ID}"
echo "  Output:              ${OUTPUT_DIR}/sub-${SUBJ_ID}"
echo "  Work directory:      ${WORK_DIR}"
echo "  FreeSurfer license:  ${FS_LICENSE}"
echo "  CPUs:                ${SLURM_CPUS_PER_TASK}"
echo "  Memory:              ${SLURM_MEM_PER_NODE}MB"
echo ""

# Create directories
mkdir -p ${OUTPUT_DIR}
mkdir -p ${WORK_DIR}
mkdir -p logs

# Clean up previous failed attempts for this subject
echo "Cleaning up previous failed attempts..."
if [ -d "${OUTPUT_DIR}/sub-${SUBJ_ID}" ]; then
    echo "  Removing previous output for sub-${SUBJ_ID}..."
    rm -rf ${OUTPUT_DIR}/sub-${SUBJ_ID}
fi

if [ -d "${OUTPUT_DIR}/sourcedata/freesurfer/sub-${SUBJ_ID}" ]; then
    echo "  Removing previous FreeSurfer output for sub-${SUBJ_ID}..."
    rm -rf ${OUTPUT_DIR}/sourcedata/freesurfer/sub-${SUBJ_ID}
fi

echo "  ✅ Cleanup complete"
echo ""

# Verify input data exists
echo "Verifying input data..."
echo "--------------------------------------------------------------------------------"

INPUT_FUNC="${BIDS_DIR}/sub-${SUBJ_ID}/func/sub-${SUBJ_ID}_task-rsvp_run-1_bold.nii.gz"
INPUT_ANAT="${BIDS_DIR}/sub-${SUBJ_ID}/anat/sub-${SUBJ_ID}_acq-mprage_T1w.nii.gz"

if [ ! -f "${INPUT_FUNC}" ]; then
    echo "❌ ERROR: Input BOLD not found: ${INPUT_FUNC}"
    exit 1
fi

if [ ! -f "${INPUT_ANAT}" ]; then
    echo "❌ ERROR: Input T1w not found: ${INPUT_ANAT}"
    exit 1
fi

echo "  ✅ Input BOLD found: ${INPUT_FUNC}"
echo "  ✅ Input T1w found: ${INPUT_ANAT}"
echo "  ℹ️  FreeSurfer skipped, using ANTs only (faster, ~2-3 hours per subject)"

echo ""

# Verify Singularity
if [ ! -f "${APPTAINER}" ]; then
    echo "❌ ERROR: Singularity not found: ${APPTAINER}"
    exit 1
fi

echo "✅ Singularity: ${APPTAINER}"

# Verify fMRIPrep container
if [ ! -f "${FMRIPREP_IMG}" ]; then
    echo "❌ ERROR: fMRIPrep container not found: ${FMRIPREP_IMG}"
    exit 1
fi

echo "✅ fMRIPrep container: $(basename ${FMRIPREP_IMG})"
echo ""

# Verify FreeSurfer license
if [ ! -f "${FS_LICENSE}" ]; then
    echo "❌ ERROR: FreeSurfer license not found: ${FS_LICENSE}"
    exit 1
fi

echo "✅ FreeSurfer license found"
echo ""

# =========================================================================
# Run fMRIPrep with improved registration parameters
# =========================================================================

echo "================================================================================"
echo "Running fMRIPrep - Sub-${SUBJ_ID}"
echo "================================================================================"
echo ""

echo "Registration improvements:"
echo "  --bold2t1w-dof 9          : 9 DOF affine (vs default 6 DOF rigid)"
echo "  --bold2t1w-init register  : Use FLIRT for initialization (vs header)"
echo "  --force-bbr               : Force boundary-based registration"
echo ""
echo "Processing improvements:"
echo "  --fs-no-reconall          : Skip FreeSurfer, use ANTs for normalization (faster & more robust)"
echo "  --dummy-scans 4           : Standard dummy scan removal"
echo ""
echo "Starting fMRIPrep..."
echo ""

# FreeSurfer will write to output directory
# Remove read-only flag from FreeSurfer bind

"$APPTAINER" run --cleanenv \
    -B ${BIDS_DIR}:/data:ro \
    -B ${OUTPUT_DIR}:/out \
    -B ${WORK_DIR}:/work \
    -B ${FS_LICENSE}:/opt/freesurfer/license.txt:ro \
    "$FMRIPREP_IMG" \
    /data /out participant \
    --participant-label ${SUBJ_ID} \
    --skip-bids-validation \
    --fs-license-file /opt/freesurfer/license.txt \
    --fs-no-reconall \
    --output-spaces MNI152NLin2009cAsym:res-2 \
    --bold2t1w-dof 9 \
    --bold2t1w-init register \
    --force-bbr \
    --dummy-scans 4 \
    --fd-spike-threshold 0.5 \
    --dvars-spike-threshold 1.5 \
    --ignore slicetiming \
    --nthreads ${SLURM_CPUS_PER_TASK} \
    --omp-nthreads 8 \
    --mem-mb 94000 \
    -w /work \
    --write-graph \
    --notrack \
    -v -v

EXIT_CODE=$?

# =========================================================================
# Verification
# =========================================================================

echo ""
echo "================================================================================"
echo "VERIFICATION - Sub-${SUBJ_ID}"
echo "================================================================================"
echo ""

if [ ${EXIT_CODE} -ne 0 ]; then
    echo "❌ fMRIPrep exited with error code: ${EXIT_CODE}"
    echo ""
    echo "Check logs for details:"
    echo "  ${SLURM_SUBMIT_DIR}/logs/fmriprep_regfix_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.err"
    exit ${EXIT_CODE}
fi

echo "fMRIPrep completed successfully"
echo ""

# Check outputs
FUNC_DIR="${OUTPUT_DIR}/sub-${SUBJ_ID}/func"

if [ ! -d "${FUNC_DIR}" ]; then
    echo "❌ ERROR: Output func directory not found: ${FUNC_DIR}"
    exit 1
fi

echo "✅ Output directory created: ${FUNC_DIR}"
echo ""

# Check for MNI BOLD files
BOLD_COUNT=$(ls ${FUNC_DIR}/sub-${SUBJ_ID}_task-rsvp_run-*_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz 2>/dev/null | wc -l)

if [ ${BOLD_COUNT} -eq 0 ]; then
    echo "❌ ERROR: No MNI BOLD files found"
    exit 1
fi

echo "✅ Found ${BOLD_COUNT} preprocessed BOLD runs"
echo ""

# Check brain mask
MASK_FILE="${FUNC_DIR}/sub-${SUBJ_ID}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"

if [ ! -f "${MASK_FILE}" ]; then
    echo "❌ WARNING: Brain mask not found: ${MASK_FILE}"
else
    echo "✅ Brain mask found"

    # Get Z-range using 3dinfo
    if command -v 3dinfo &> /dev/null; then
        echo ""
        echo "Brain mask info:"
        3dinfo -n4 -ad3 ${MASK_FILE} | head -5
    fi
fi

echo ""

# Check registration quality files
REG_DIR="${WORK_DIR}/fmriprep_23_2_wf/single_subject_${SUBJ_ID}_wf"

if [ -d "${REG_DIR}" ]; then
    echo "Registration files in work directory:"

    # Find registration transforms
    REG_FILES=$(find ${REG_DIR} -name "*desc-coreg*.mat" -o -name "registration.lta" 2>/dev/null | head -5)

    if [ ! -z "${REG_FILES}" ]; then
        echo "${REG_FILES}"
    else
        echo "  (Registration files will be in nested subdirectories)"
    fi
else
    echo "⚠️  Work directory structure differs from expected"
fi

echo ""
echo "================================================================================"
echo "Sub-${SUBJ_ID}: COMPLETE"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Check registration quality:"
echo "     python CHECK_BOLD_T1W_REGISTRATION_FIXED.py (update paths)"
echo ""
echo "  2. Verify V1 ROI overlap:"
echo "     python CHECK_ALL_SUBJECTS_OVERLAP.sh (add registration_fix output)"
echo ""
echo "  3. Compare with original:"
echo "     Original: V1 overlap = 0/810 (0%)"
echo "     Expected: V1 overlap > 500/810 (>60%)"
echo ""
echo "Output directory: ${OUTPUT_DIR}/sub-${SUBJ_ID}"
echo "Work directory:   ${WORK_DIR}"
echo ""
echo "End time: $(date)"
echo "================================================================================"

exit 0
