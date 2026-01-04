#!/bin/bash
#SBATCH --job-name=fprep_orig
#SBATCH --array=1-10
#SBATCH --output=logs/fmriprep_original_%A_%a.out
#SBATCH --error=logs/fmriprep_original_%A_%a.err
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --qos=shared
#SBATCH --nodelist=node2

################################################################################
# fMRIPrep - Original Data (No Deoblique) - All Subjects
#
# Based on PI feedback:
#   - Use original data (no deoblique preprocessing)
#   - Enable slice timing correction (default)
#   - Individual array job per subject
#
# Key settings (optimized for fast, reliable outputs):
#   - DOF 6: Rigid registration (6 parameters)
#   - Slice timing: ENABLED (no --ignore flag)
#   - BBR initialization: register (vs default)
#   - FreeSurfer: DISABLED (--fs-no-reconall) for faster runtime
#   - Output: MNI152NLin2009cAsym:res-2 only (volume-based analysis)
#   - Individual processing: Prevents any cross-subject interference
#
# Input:  /storage/connectome/haba6030/colorBlind_data (ORIGINAL)
# Output: /storage/connectome/haba6030/fmriprep_out_original_v2
# Work:   /storage/connectome/haba6030/fmriprep_work_original_v2_sub-XX
################################################################################

set -e

# Subject mapping
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT_ID=${SUBJECTS[$((SLURM_ARRAY_TASK_ID - 1))]}

echo "================================================================================"
echo "fMRIPrep - Original Data (No Deoblique) - Sub-${SUBJECT_ID}"
echo "================================================================================"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Start time: $(date)"
echo ""
echo "Strategy: Process ORIGINAL data without deoblique preprocessing"
echo "Key features:"
echo "  ✅ Slice timing correction: ENABLED (default)"
echo "  ✅ Registration DOF: 6 (rigid)"
echo "  ✅ BBR initialization: register (better than header)"
echo "  ✅ FreeSurfer: DISABLED (faster runtime, 2-3h vs 12h)"
echo "  ✅ Output: MNI volume only (Wang ROI analysis ready)"
echo "  ✅ Individual array job (no cross-subject interference)"
echo "================================================================================"
echo ""

# Directories
BIDS_DIR="/storage/connectome/haba6030/bids_editted"
OUTPUT_DIR="/storage/connectome/haba6030/fmriprep_out_original_v3"
WORK_DIR="/storage/connectome/haba6030/fmriprep_work_original_v3_sub-${SUBJECT_ID}"

# Singularity settings
APPTAINER=/usr/local/bin/singularity
FMRIprep_IMG=/home/connectome/haba6030/fmriprep-23.2.3.sif
FS_LICENSE=/home/connectome/haba6030/fs_license.txt

echo "Configuration:"
echo "  Subject:       sub-${SUBJECT_ID}"
echo "  Input (BIDS):  ${BIDS_DIR}"
echo "  Output:        ${OUTPUT_DIR}"
echo "  Work:          ${WORK_DIR}"
echo "  CPUs:          ${SLURM_CPUS_PER_TASK}"
echo "  Memory:        ${SLURM_MEM_PER_NODE}MB"
echo ""

# Create directories
mkdir -p ${OUTPUT_DIR}
mkdir -p ${WORK_DIR}
mkdir -p logs

# Verify input data exists
echo "Verifying input data..."
echo "--------------------------------------------------------------------------------"

INPUT_FUNC="${BIDS_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-1_bold.nii.gz"
INPUT_ANAT="${BIDS_DIR}/sub-${SUBJECT_ID}/anat/sub-${SUBJECT_ID}_acq-mprage_T1w.nii.gz"

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
echo ""

# Check obliquity (for reference)
if command -v 3dinfo &> /dev/null; then
    echo "Original data obliquity:"
    3dinfo -obliquity ${INPUT_FUNC} 2>/dev/null || echo "  (3dinfo not available)"
    echo ""
fi

# Verify Singularity
if [ ! -f "${APPTAINER}" ]; then
    echo "❌ ERROR: Singularity not found: ${APPTAINER}"
    exit 1
fi

echo "✅ Singularity: ${APPTAINER}"

# Verify fMRIPrep container
if [ ! -f "${FMRIprep_IMG}" ]; then
    echo "❌ ERROR: fMRIPrep container not found: ${FMRIprep_IMG}"
    exit 1
fi

echo "✅ fMRIPrep container: $(basename ${FMRIprep_IMG})"
echo ""

# Verify FreeSurfer license
if [ ! -f "${FS_LICENSE}" ]; then
    echo "❌ ERROR: FreeSurfer license not found: ${FS_LICENSE}"
    exit 1
fi

echo "✅ FreeSurfer license found"
echo ""

# =========================================================================
# Run fMRIPrep on ORIGINAL data
# =========================================================================

echo "================================================================================"
echo "Running fMRIPrep - Sub-${SUBJECT_ID}"
echo "================================================================================"
echo ""

echo "Processing strategy:"
echo "  Input data:              ORIGINAL (oblique, no preprocessing)"
echo "  Slice timing correction: ✅ ENABLED (default, as per PI feedback)"
echo "  Registration DOF:        6 (rigid)"
echo "  BBR initialization:      register (FLIRT-based)"
echo "  FreeSurfer:              ❌ DISABLED (--fs-no-reconall)"
echo "  Output spaces:           MNI152NLin2009cAsym:res-2 only"
echo ""
echo "Starting fMRIPrep..."
echo ""

"$APPTAINER" run --cleanenv \
  -B ${BIDS_DIR}:/data:ro \
  -B ${OUTPUT_DIR}:/out \
  -B ${WORK_DIR}:/work \
  -B ${FS_LICENSE}:/opt/freesurfer/license.txt:ro \
  "$FMRIprep_IMG" \
  /data /out participant \
  --participant-label ${SUBJECT_ID} \
  --fs-license-file /opt/freesurfer/license.txt \
  --output-spaces MNI152NLin2009cAsym:res-2 \
  --fs-no-reconall \
  --bold2t1w-dof 6 \
  --bold2t1w-init register \
  --force-bbr \
  --use-syn-sdc warn \
  --dummy-scans 4 \
  --fd-spike-threshold 0.5 \
  --dvars-spike-threshold 1.5 \
  --nthreads ${SLURM_CPUS_PER_TASK} \
  --omp-nthreads 8 \
  --mem-mb 94000 \
  -w /work \
  --write-graph \
  --skip-bids-validation \
  --notrack \
  -v -v

EXIT_CODE=$?

# =========================================================================
# Verification
# =========================================================================

echo ""
echo "================================================================================"
echo "VERIFICATION - Sub-${SUBJECT_ID}"
echo "================================================================================"
echo ""

if [ ${EXIT_CODE} -ne 0 ]; then
    echo "❌ fMRIPrep exited with error code: ${EXIT_CODE}"
    echo ""
    echo "Check logs for details:"
    echo "  ${SLURM_SUBMIT_DIR}/logs/fmriprep_original_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.err"
    exit ${EXIT_CODE}
fi

echo "fMRIPrep completed successfully"
echo ""

# Check outputs
FUNC_DIR="${OUTPUT_DIR}/sub-${SUBJECT_ID}/func"

if [ ! -d "${FUNC_DIR}" ]; then
    echo "❌ ERROR: Output func directory not found: ${FUNC_DIR}"
    exit 1
fi

echo "✅ Output directory created: ${FUNC_DIR}"
echo ""

# Check for MNI BOLD files
BOLD_COUNT=$(ls ${FUNC_DIR}/sub-${SUBJECT_ID}_task-rsvp_run-*_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz 2>/dev/null | wc -l)

if [ ${BOLD_COUNT} -eq 0 ]; then
    echo "❌ ERROR: No MNI BOLD files found"
    exit 1
fi

echo "✅ Found ${BOLD_COUNT} preprocessed BOLD runs"
echo ""

# Check brain mask
MASK_FILE="${FUNC_DIR}/sub-${SUBJECT_ID}_task-rsvp_run-1_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"

if [ ! -f "${MASK_FILE}" ]; then
    echo "❌ WARNING: Brain mask not found: ${MASK_FILE}"
else
    echo "✅ Brain mask found"

    # Get Z-range using 3dinfo if available
    if command -v 3dinfo &> /dev/null; then
        echo ""
        echo "Brain mask info:"
        3dinfo -n4 -ad3 ${MASK_FILE} | head -5
    fi
fi

echo ""
echo "================================================================================"
echo "Sub-${SUBJECT_ID}: COMPLETE"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. After all subjects complete, run:"
echo "     python COMPARE_ORIGINAL_VS_DEOBLIQUE.py"
echo ""
echo "  2. Check V1 ROI overlap for this subject"
echo ""
echo "Output directory: ${OUTPUT_DIR}/sub-${SUBJECT_ID}"
echo "Work directory:   ${WORK_DIR}"
echo ""
echo "End time: $(date)"
echo "================================================================================"

exit 0
