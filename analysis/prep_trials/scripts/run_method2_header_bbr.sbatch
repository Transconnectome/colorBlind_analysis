#!/bin/bash
#SBATCH --job-name=prep_m2
#SBATCH --array=1-3
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/method2_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/method2_%A_%a.err
#SBATCH --time=24:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --qos=shared
#SBATCH --nodelist=node2

################################################################################
# Method 2: Header → BBR (FreeSurfer)
#
# IMPORTANT DISCOVERY:
#   --bold2anat-init header requires FreeSurfer BBR!
#   FSL BBR (--fs-no-reconall) does NOT support header initialization
#   → Error: "Header-based registration initialization not supported for FSL"
#
# Registration strategy:
#   (a) Initial alignment: SKIP (use header qform/sform)
#   (b) BBR refinement: FreeSurfer WM surfaces (NOT FSL FAST!)
#
# Difference from original_v3:
#   --bold2t1w-init register → --bold2t1w-init header
#   --fs-no-reconall REMOVED (FreeSurfer recon-all required!)
#
# Test subjects: Sub-01, 03, 06
# Expected time: ~8-10 hours/subject (FreeSurfer recon-all included)
################################################################################

set -e

# Subject mapping (only 3 subjects for trial)
SUBJECTS=(01 03 06)
SUBJECT_ID=${SUBJECTS[$((SLURM_ARRAY_TASK_ID - 1))]}

echo "================================================================================"
echo "Method 2: Header → BBR (FreeSurfer) - Sub-${SUBJECT_ID}"
echo "================================================================================"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Start time: $(date)"
echo ""
echo "IMPORTANT: FreeSurfer recon-all required for header initialization!"
echo "Expected time: ~8-10 hours/subject"
echo ""
echo "Registration strategy:"
echo "  (a) Initial alignment: ❌ SKIP (use NIfTI header qform/sform)"
echo "  (b) BBR refinement: ✅ FreeSurfer WM surfaces (NOT FSL FAST!)"
echo "================================================================================"
echo ""

# Directories
BIDS_DIR="/storage/connectome/haba6030/bids_editted"
OUTPUT_DIR="/storage/connectome/haba6030/fmriprep_out_method2_header_bbr"
WORK_DIR="/storage/connectome/haba6030/fmriprep_work_method2_sub-${SUBJECT_ID}"

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
mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs

# Verify input data
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

echo "✅ Input BOLD found: ${INPUT_FUNC}"
echo "✅ Input T1w found: ${INPUT_ANAT}"
echo ""

# Display header info (qform)
echo "BOLD qform (for reference):"
3dinfo -prefix -space -orient -obliquity ${INPUT_FUNC} 2>/dev/null || echo "  (3dinfo not available)"
echo ""

echo "T1w qform (for reference):"
3dinfo -prefix -space -orient -obliquity ${INPUT_ANAT} 2>/dev/null || echo "  (3dinfo not available)"
echo ""

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
# Run fMRIPrep - Method 2: Header → BBR
# =========================================================================

echo "================================================================================"
echo "Running fMRIPrep Method 2 - Sub-${SUBJECT_ID}"
echo "================================================================================"
echo ""

echo "Registration strategy:"
echo "  (a) Initial alignment:   ❌ SKIP (NIfTI header qform/sform)"
echo "  (b) BBR refinement:      ✅ FSL FAST WM boundary"
echo ""
echo "Key difference from original_v3:"
echo "  --bold2t1w-init register → --bold2t1w-init header ⭐"
echo ""
echo "Starting fMRIPrep..."
echo ""

"$APPTAINER" exec --userns --cleanenv \
  -B ${BIDS_DIR}:/data:ro \
  -B ${OUTPUT_DIR}:/out \
  -B ${WORK_DIR}:/work \
  -B ${FS_LICENSE}:/opt/freesurfer/license.txt:ro \
  "$FMRIprep_IMG" fmriprep \
  /data /out participant \
  --participant-label ${SUBJECT_ID} \
  --fs-license-file /opt/freesurfer/license.txt \
  --output-spaces MNI152NLin2009cAsym:res-2 \
  --bold2t1w-dof 6 \
  --bold2t1w-init header \
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
    echo "  /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/method2_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.err"
    exit ${EXIT_CODE}
fi

echo "✅ fMRIPrep completed successfully"
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
fi

echo ""
echo "================================================================================"
echo "Sub-${SUBJECT_ID}: Method 2 COMPLETE"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Run Dice computation:"
echo "     python scripts/compute_dice.py --subject ${SUBJECT_ID} --method method2_header_bbr"
echo ""
echo "Output directory: ${OUTPUT_DIR}/sub-${SUBJECT_ID}"
echo "Work directory:   ${WORK_DIR}"
echo ""
echo "End time: $(date)"
echo "================================================================================"

exit 0
