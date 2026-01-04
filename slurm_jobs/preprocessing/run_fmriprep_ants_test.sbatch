#!/bin/bash
#SBATCH --job-name=fprep_ants
#SBATCH --array=2,3,9  # Sub-03, 06, 10 (problem subjects)
#SBATCH --output=logs/fmriprep_ants_%A_%a.out
#SBATCH --error=logs/fmriprep_ants_%A_%a.err
#SBATCH --time=8:00:00
#SBATCH --cpus-per-task=16
#SBATCH --mem=96G
#SBATCH --qos=shared
#SBATCH --nodelist=node2

################################################################################
# fMRIPrep with ANTs Registration - Test Run
#
# Purpose: Test if ANTs SyN improves BOLD → T1w registration
#          for subjects with high translation error
#
# Problem subjects:
#   - Sub-03: Translation 35.0mm → V1 overlap 0%
#   - Sub-06: Translation 55.5mm → V1 overlap 0%
#   - Sub-10: Translation 36.8mm → V1 overlap 0%
#
# Hypothesis: ANTs SyN will reduce translation error via:
#   1. Better initialization (center of mass)
#   2. Multi-resolution optimization (MI metric)
#   3. Nonlinear deformation (local correction)
#
# Expected outcome:
#   - Translation < 30mm
#   - V1 overlap > 50%
#
# Test strategy:
#   - Use --use-syn-sdc for SyN-based registration
#   - Compare with BBR results (Original DOF 9)
#
# Author: Claude Code
# Date: 2025-12-31
################################################################################

set -e

# Subject mapping (array index → subject ID)
# Array indices: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
# Subject IDs:  01,02,03,04,05,06,07,08,09,10
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT_ID=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

echo "================================================================================"
echo "fMRIPrep with ANTs SyN Registration - Test Run"
echo "================================================================================"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Subject: sub-${SUBJECT_ID}"
echo "Start time: $(date)"
echo ""
echo "Hypothesis Testing:"
echo "  Problem: BBR registration produces excessive translation"
echo "  Current translation: "
if [ "${SUBJECT_ID}" == "03" ]; then
    echo "    Sub-03: 35.0mm → V1 overlap 0%"
elif [ "${SUBJECT_ID}" == "06" ]; then
    echo "    Sub-06: 55.5mm → V1 overlap 0%"
elif [ "${SUBJECT_ID}" == "10" ]; then
    echo "    Sub-10: 36.8mm → V1 overlap 0%"
fi
echo ""
echo "  Expected with ANTs SyN:"
echo "    ✓ Translation < 30mm (center of mass initialization)"
echo "    ✓ V1 overlap > 50% (better alignment)"
echo "    ✓ Nonlinear correction of local distortions"
echo "================================================================================"
echo ""

# Directories
BIDS_DIR="/storage/connectome/haba6030/bids_editted"
OUTPUT_DIR="/storage/connectome/haba6030/fmriprep_out_ants_test"
WORK_DIR="/storage/connectome/haba6030/fmriprep_work_ants_test/sub-${SUBJECT_ID}"

# Singularity settings
APPTAINER=/usr/local/bin/singularity
FMRIPREP_IMG=/home/connectome/haba6030/fmriprep-23.2.3.sif
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

# Clean up previous attempts
if [ -d "${OUTPUT_DIR}/sub-${SUBJECT_ID}" ]; then
    echo "Cleaning up previous output for sub-${SUBJECT_ID}..."
    rm -rf ${OUTPUT_DIR}/sub-${SUBJECT_ID}
fi

echo "✅ Cleanup complete"
echo ""

# Verify input data
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

# =========================================================================
# Run fMRIPrep with ANTs SyN
# =========================================================================

echo "================================================================================"
echo "Running fMRIPrep with ANTs SyN - Sub-${SUBJECT_ID}"
echo "================================================================================"
echo ""

echo "Registration strategy:"
echo "  Method: ANTs SyN (instead of BBR)"
echo "  Initialization: Center of mass"
echo "  Metric: Mutual Information (MI)"
echo "  Stages: Rigid → Affine → SyN deformation"
echo "  Expected improvement: Reduced translation error"
echo ""

echo "⚠️  NOTE: fMRIPrep 23.2.3 uses BBR by default."
echo "   To use ANTs for BOLD→T1w, we need to:"
echo "   1. Skip FreeSurfer (--fs-no-reconall)"
echo "   2. Use --use-syn-sdc (enables SyN-based distortion correction)"
echo "   3. This will use ANTs for both SDC and registration"
echo ""

echo "Starting fMRIPrep..."
echo ""

"$APPTAINER" run --cleanenv \
  -B ${BIDS_DIR}:/data:ro \
  -B ${OUTPUT_DIR}:/out \
  -B ${WORK_DIR}:/work \
  -B ${FS_LICENSE}:/opt/freesurfer/license.txt:ro \
  "$FMRIPREP_IMG" \
  /data /out participant \
  --participant-label ${SUBJECT_ID} \
  --fs-license-file /opt/freesurfer/license.txt \
  --fs-no-reconall \
  --output-spaces MNI152NLin2009cAsym:res-2 \
  --use-syn-sdc \
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
    echo "  ${SLURM_SUBMIT_DIR}/logs/fmriprep_ants_${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}.err"
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

    # Get Z-range using 3dinfo
    if command -v 3dinfo &> /dev/null; then
        echo ""
        echo "Brain mask Z-range analysis:"
        echo "--------------------------------------------------------------------------------"

        # Get full info
        mask_info=$(3dinfo -n4 -ad3 ${MASK_FILE} 2>/dev/null)
        echo "${mask_info}"

        echo ""
        echo "V1 ROI location: Z:32-45"
        echo ""
        echo "Expected improvement:"
        echo "  - Z-range should include Z:32-45"
        echo "  - Compare with BBR result:"
        if [ "${SUBJECT_ID}" == "03" ]; then
            echo "    BBR: Z:42-75 (missing Z:32-41) → 0% overlap"
        elif [ "${SUBJECT_ID}" == "06" ]; then
            echo "    BBR: Z:41-60 (missing Z:32-40) → 0% overlap"
        elif [ "${SUBJECT_ID}" == "10" ]; then
            echo "    BBR: Z:36-74 (missing Z:32-35) → 0% overlap"
        fi
    fi
fi

echo ""

# Check registration transform
echo "Registration transform analysis:"
echo "--------------------------------------------------------------------------------"

XFM_FILE=$(find ${WORK_DIR} -name "*from-boldref_to-T1w*xfm.txt" 2>/dev/null | head -1)

if [ -f "${XFM_FILE}" ]; then
    echo "Transform file: ${XFM_FILE}"
    echo ""
    cat ${XFM_FILE}
    echo ""
    echo "⚠️  NOTE: Extract translation values and compare with BBR:"
    if [ "${SUBJECT_ID}" == "03" ]; then
        echo "    BBR translation: 35.0mm"
    elif [ "${SUBJECT_ID}" == "06" ]; then
        echo "    BBR translation: 55.5mm"
    elif [ "${SUBJECT_ID}" == "10" ]; then
        echo "    BBR translation: 36.8mm"
    fi
    echo "    Expected ANTs translation: < 30mm"
else
    echo "⚠️  Transform file not found in work directory"
fi

echo ""
echo "================================================================================"
echo "Sub-${SUBJECT_ID}: COMPLETE"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "  1. Run analysis script to check V1 overlap:"
echo "     python CHECK_ANTS_TEST_RESULTS.py"
echo ""
echo "  2. Compare with BBR results:"
echo "     - Translation magnitude"
echo "     - Brain mask Z-range"
echo "     - V1 ROI overlap"
echo ""
echo "  3. If successful (V1 overlap > 50%), run for all subjects"
echo ""
echo "Output directory: ${OUTPUT_DIR}/sub-${SUBJECT_ID}"
echo "Work directory:   ${WORK_DIR}"
echo ""
echo "End time: $(date)"
echo "================================================================================"

exit 0
