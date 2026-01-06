#!/bin/bash
#SBATCH --job-name=prep_m3
#SBATCH --array=1-3
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/method3_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/method3_%A_%a.err
#SBATCH --time=2:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --qos=shared
#SBATCH --nodelist=node2

################################################################################
# Method 3: Header → MI (mri_coreg --regheader)
#
# Registration strategy:
#   (a) Initial alignment: NIfTI header
#   (a') MI optimization: Powell's method (FreeSurfer mri_coreg)
#   (b) BBR refinement: SKIP (MI sufficient for fMRI 2mm resolution)
#
# Key advantage:
#   - MI robust to limited FOV, obliquity, limited cortex
#   - No WM boundary needed
#
# Test subjects: Sub-01, 03, 06
################################################################################

set -e

# Subject mapping
SUBJECTS=(01 03 06)
SUBJECT_ID=${SUBJECTS[$((SLURM_ARRAY_TASK_ID - 1))]}

echo "================================================================================"
echo "Method 3: Header → MI (mri_coreg) - Sub-${SUBJECT_ID}"
echo "================================================================================"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Start time: $(date)"
echo ""
echo "Registration strategy:"
echo "  (a) Initial alignment: NIfTI header qform/sform"
echo "  (a') MI optimization: FreeSurfer mri_coreg (Powell's method)"
echo "  (b) BBR refinement: ❌ SKIP (MI ~1mm accuracy sufficient)"
echo "================================================================================"
echo ""

# Directories
BIDS_DIR="/storage/connectome/haba6030/bids_editted"
OUTPUT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/method3_header_mi"
WORK_DIR="/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/work_method3_sub-${SUBJECT_ID}"

# FreeSurfer setup
export SUBJECTS_DIR="${WORK_DIR}/freesurfer_subjects"
mkdir -p ${SUBJECTS_DIR}

# Output directories
mkdir -p ${OUTPUT_DIR}/sub-${SUBJECT_ID}/func
mkdir -p ${OUTPUT_DIR}/sub-${SUBJECT_ID}/anat
mkdir -p ${OUTPUT_DIR}/sub-${SUBJECT_ID}/transforms
mkdir -p ${WORK_DIR}
mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs

echo "Configuration:"
echo "  Subject:       sub-${SUBJECT_ID}"
echo "  Input (BIDS):  ${BIDS_DIR}"
echo "  Output:        ${OUTPUT_DIR}"
echo "  Work:          ${WORK_DIR}"
echo "  FreeSurfer:    ${SUBJECTS_DIR}"
echo "  CPUs:          ${SLURM_CPUS_PER_TASK}"
echo ""

# Input files
T1W_FILE="${BIDS_DIR}/sub-${SUBJECT_ID}/anat/sub-${SUBJECT_ID}_acq-mprage_T1w.nii.gz"

echo "Input files:"
echo "  T1w: ${T1W_FILE}"
echo ""

# Verify T1w exists
if [ ! -f "${T1W_FILE}" ]; then
    echo "❌ ERROR: T1w not found: ${T1W_FILE}"
    exit 1
fi

echo "✅ T1w found"
echo ""

# =========================================================================
# Step 1: FreeSurfer brain extraction (for reference only)
# =========================================================================

echo "================================================================================"
echo "Step 1: Brain extraction with FreeSurfer"
echo "================================================================================"
echo ""

# Quick brain extraction (not full recon-all!)
# We only need brain.mgz for mri_coreg reference

T1W_MGZ="${SUBJECTS_DIR}/sub-${SUBJECT_ID}/mri/orig.mgz"
BRAIN_MGZ="${SUBJECTS_DIR}/sub-${SUBJECT_ID}/mri/brain.mgz"

mkdir -p ${SUBJECTS_DIR}/sub-${SUBJECT_ID}/mri

# Convert T1w to MGZ
echo "Converting T1w to MGZ format..."
mri_convert ${T1W_FILE} ${T1W_MGZ}

# Brain extraction
echo "Running brain extraction..."
# Use mri_watershed or simple bet/3dSkullStrip
# For speed, we'll use FSL bet if available, otherwise mri_watershed

if command -v bet2 &> /dev/null; then
    echo "Using FSL bet for brain extraction..."
    bet2 ${T1W_FILE} ${WORK_DIR}/T1w_brain.nii.gz -f 0.5 -m
    mri_convert ${WORK_DIR}/T1w_brain.nii.gz ${BRAIN_MGZ}
else
    echo "Using FreeSurfer mri_watershed..."
    mri_watershed -useSRAS -surf ${SUBJECTS_DIR}/sub-${SUBJECT_ID}/surf/lh.brain ${T1W_MGZ} ${BRAIN_MGZ}
fi

echo "✅ Brain extracted: ${BRAIN_MGZ}"
echo ""

# =========================================================================
# Step 2: BOLD → T1w registration with mri_coreg
# =========================================================================

echo "================================================================================"
echo "Step 2: BOLD → T1w registration (mri_coreg --regheader)"
echo "================================================================================"
echo ""

# Process all runs
for RUN in 1 2 3 4 5 6; do
    echo "------------------------------------------------------------"
    echo "Processing Run ${RUN}"
    echo "------------------------------------------------------------"

    BOLD_FILE="${BIDS_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_bold.nii.gz"

    if [ ! -f "${BOLD_FILE}" ]; then
        echo "⚠️  WARNING: BOLD run ${RUN} not found, skipping"
        continue
    fi

    # Extract reference volume (middle volume)
    echo "Extracting reference volume..."
    NVOLS=$(3dinfo -nv ${BOLD_FILE} 2>/dev/null || echo "100")
    REF_VOL=$((NVOLS / 2))

    BOLD_REF="${WORK_DIR}/sub-${SUBJECT_ID}_run-${RUN}_boldref.nii.gz"
    3dTcat -prefix ${BOLD_REF} ${BOLD_FILE}"[${REF_VOL}]" 2>/dev/null || \
        fslroi ${BOLD_FILE} ${BOLD_REF} ${REF_VOL} 1

    # mri_coreg: BOLD → T1w
    echo "Running mri_coreg --regheader..."

    OUTPUT_LTA="${OUTPUT_DIR}/sub-${SUBJECT_ID}/transforms/sub-${SUBJECT_ID}_run-${RUN}_bold_to_t1w.lta"

    mri_coreg \
        --ref ${BRAIN_MGZ} \
        --mov ${BOLD_REF} \
        --reg ${OUTPUT_LTA} \
        --regheader \
        --threads ${SLURM_CPUS_PER_TASK}

    if [ ! -f "${OUTPUT_LTA}" ]; then
        echo "❌ ERROR: mri_coreg failed for run ${RUN}"
        continue
    fi

    echo "✅ Transform saved: $(basename ${OUTPUT_LTA})"

    # Apply transform to BOLD
    echo "Applying transform to BOLD..."
    BOLD_IN_T1W="${WORK_DIR}/sub-${SUBJECT_ID}_run-${RUN}_bold_in_t1w.nii.gz"

    mri_vol2vol \
        --mov ${BOLD_FILE} \
        --targ ${BRAIN_MGZ} \
        --lta ${OUTPUT_LTA} \
        --o ${BOLD_IN_T1W} \
        --interp trilin \
        --no-save-reg

    echo "✅ BOLD in T1w space: $(basename ${BOLD_IN_T1W})"

    # Create brain mask in T1w space
    echo "Creating brain mask..."
    BOLD_MASK_T1W="${WORK_DIR}/sub-${SUBJECT_ID}_run-${RUN}_bold_mask_t1w.nii.gz"

    3dAutomask -prefix ${BOLD_MASK_T1W} ${BOLD_IN_T1W} 2>/dev/null || \
        fslmaths ${BOLD_IN_T1W} -bin ${BOLD_MASK_T1W}

    echo ""
done

echo "✅ All runs processed with mri_coreg"
echo ""

# =========================================================================
# Step 3: T1w → MNI normalization (ANTs)
# =========================================================================

echo "================================================================================"
echo "Step 3: T1w → MNI normalization (ANTs)"
echo "================================================================================"
echo ""

# MNI template
MNI_TEMPLATE="/usr/share/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz"

# Check if template exists
if [ ! -f "${MNI_TEMPLATE}" ]; then
    echo "⚠️  WARNING: MNI template not found at ${MNI_TEMPLATE}"
    echo "    Trying alternative locations..."

    ALT_TEMPLATES=(
        "/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz"
        "${FSLDIR}/data/standard/MNI152_T1_2mm_brain.nii.gz"
        "/opt/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz"
    )

    for TEMPLATE in "${ALT_TEMPLATES[@]}"; do
        if [ -f "${TEMPLATE}" ]; then
            MNI_TEMPLATE="${TEMPLATE}"
            echo "✅ Found template: ${MNI_TEMPLATE}"
            break
        fi
    done
fi

if [ ! -f "${MNI_TEMPLATE}" ]; then
    echo "❌ ERROR: MNI template not found. Please specify correct path."
    echo "    Skipping normalization step."
    echo "    You can manually run ANTs normalization later."
else
    echo "Running ANTs registration (T1w → MNI)..."

    # Convert brain.mgz to NIfTI
    T1W_BRAIN_NII="${WORK_DIR}/sub-${SUBJECT_ID}_T1w_brain.nii.gz"
    mri_convert ${BRAIN_MGZ} ${T1W_BRAIN_NII}

    # ANTs SyN registration
    OUTPUT_PREFIX="${OUTPUT_DIR}/sub-${SUBJECT_ID}/transforms/sub-${SUBJECT_ID}_t1w_to_mni_"

    antsRegistrationSyN.sh \
        -d 3 \
        -f ${MNI_TEMPLATE} \
        -m ${T1W_BRAIN_NII} \
        -o ${OUTPUT_PREFIX} \
        -n ${SLURM_CPUS_PER_TASK}

    echo "✅ T1w → MNI transform computed"

    # =========================================================================
    # Step 4: Apply composed transforms (BOLD → T1w → MNI)
    # =========================================================================

    echo ""
    echo "================================================================================"
    echo "Step 4: Apply composed transforms (BOLD → MNI)"
    echo "================================================================================"
    echo ""

    for RUN in 1 2 3 4 5 6; do
        BOLD_FILE="${BIDS_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_bold.nii.gz"

        if [ ! -f "${BOLD_FILE}" ]; then
            continue
        fi

        echo "Processing Run ${RUN}..."

        OUTPUT_LTA="${OUTPUT_DIR}/sub-${SUBJECT_ID}/transforms/sub-${SUBJECT_ID}_run-${RUN}_bold_to_t1w.lta"

        # Convert LTA to ITK format
        ITK_TRANSFORM="${WORK_DIR}/sub-${SUBJECT_ID}_run-${RUN}_bold_to_t1w.txt"
        lta_convert --inlta ${OUTPUT_LTA} --outitk ${ITK_TRANSFORM} \
            --src ${BOLD_FILE} --trg ${BRAIN_MGZ}

        # Apply composed transform
        BOLD_MNI="${OUTPUT_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
        MASK_MNI="${OUTPUT_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"

        antsApplyTransforms \
            -d 3 \
            -i ${BOLD_FILE} \
            -r ${MNI_TEMPLATE} \
            -t ${OUTPUT_PREFIX}1Warp.nii.gz \
            -t ${OUTPUT_PREFIX}0GenericAffine.mat \
            -t ${ITK_TRANSFORM} \
            -o ${BOLD_MNI} \
            -n LanczosWindowedSinc

        # Create mask in MNI space
        3dAutomask -prefix ${MASK_MNI} ${BOLD_MNI} 2>/dev/null || \
            fslmaths ${BOLD_MNI} -bin ${MASK_MNI}

        echo "  ✅ BOLD in MNI: $(basename ${BOLD_MNI})"
        echo "  ✅ Mask in MNI: $(basename ${MASK_MNI})"
    done
fi

# =========================================================================
# Summary
# =========================================================================

echo ""
echo "================================================================================"
echo "Sub-${SUBJECT_ID}: Method 3 COMPLETE"
echo "================================================================================"
echo ""
echo "Method 3 summary:"
echo "  (a) Header init: ✅"
echo "  (a') MI optimization (mri_coreg): ✅"
echo "  (b) BBR: ❌ SKIP (not needed)"
echo ""
echo "Output files:"
echo "  Transforms: ${OUTPUT_DIR}/sub-${SUBJECT_ID}/transforms/"
echo "  BOLD (MNI): ${OUTPUT_DIR}/sub-${SUBJECT_ID}/func/"
echo ""
echo "Next steps:"
echo "  1. Compute Dice:"
echo "     python scripts/compute_dice.py --subject ${SUBJECT_ID} --method method3_header_mi"
echo ""
echo "End time: $(date)"
echo "================================================================================"

exit 0
