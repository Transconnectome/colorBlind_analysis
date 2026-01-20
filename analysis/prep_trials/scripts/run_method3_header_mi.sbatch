#!/bin/bash
#SBATCH --job-name=prep_m3
#SBATCH --array=1-3
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/method3_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/method3_%A_%a.err
#SBATCH --time=12:00:00
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
OUTPUT_DIR="/storage/connectome/haba6030/fmriprep_out_method3_header_mi"
WORK_DIR="/storage/connectome/haba6030/fmriprep_work_method3_sub-${SUBJECT_ID}"

# FreeSurfer setup (Node2 has FreeSurfer 7.2.0 installed)
export FREESURFER_HOME=/usr/local/freesurfer/7.2.0
export PATH="${FREESURFER_HOME}/bin:${PATH}"
export SUBJECTS_DIR="${WORK_DIR}/freesurfer_subjects"
mkdir -p ${SUBJECTS_DIR}

# FreeSurfer license (CRITICAL)
export FS_LICENSE=${FREESURFER_HOME}/license.txt

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
# Step 3: T1w → MNI normalization (FSL FLIRT + FNIRT)
# =========================================================================

echo "================================================================================"
echo "Step 3: T1w → MNI normalization (FSL)"
echo "================================================================================"
echo ""
echo "NOTE: Using FSL FLIRT + FNIRT (nonlinear), matching original_v3 pipeline"
echo ""

# MNI template
MNI_TEMPLATE="/usr/local/fsl/data/standard/MNI152_T1_2mm_brain.nii.gz"

if [ ! -f "${MNI_TEMPLATE}" ]; then
    echo "❌ ERROR: MNI template not found: ${MNI_TEMPLATE}"
    exit 1
fi

# Convert T1w brain to NIfTI
T1W_BRAIN_NII="${WORK_DIR}/sub-${SUBJECT_ID}_T1w_brain.nii.gz"
mri_convert ${BRAIN_MGZ} ${T1W_BRAIN_NII}

echo "Running FLIRT + FNIRT (T1w → MNI, nonlinear)..."

# Step 3a: Linear registration with FLIRT
T1W_TO_MNI_MAT="${OUTPUT_DIR}/sub-${SUBJECT_ID}/transforms/sub-${SUBJECT_ID}_t1w_to_mni_affine.mat"
T1W_TO_MNI_LINEAR="${WORK_DIR}/sub-${SUBJECT_ID}_T1w_in_MNI_linear.nii.gz"

echo "  FLIRT (linear 12 DOF)..."
flirt \
    -in ${T1W_BRAIN_NII} \
    -ref ${MNI_TEMPLATE} \
    -out ${T1W_TO_MNI_LINEAR} \
    -omat ${T1W_TO_MNI_MAT} \
    -bins 256 \
    -cost corratio \
    -searchrx -90 90 \
    -searchry -90 90 \
    -searchrz -90 90 \
    -dof 12

echo "  ✅ Linear registration done"

# Step 3b: Nonlinear registration with FNIRT
T1W_TO_MNI_WARP="${OUTPUT_DIR}/sub-${SUBJECT_ID}/transforms/sub-${SUBJECT_ID}_t1w_to_mni_warp.nii.gz"
T1W_TO_MNI_NONLINEAR="${WORK_DIR}/sub-${SUBJECT_ID}_T1w_in_MNI_nonlinear.nii.gz"

# MNI template (non-brain for FNIRT)
MNI_TEMPLATE_HEAD="/usr/local/fsl/data/standard/MNI152_T1_2mm.nii.gz"
MNI_CONFIG="/usr/local/fsl/etc/flirtsch/T1_2_MNI152_2mm.cnf"

# Convert brain.mgz to full head T1w
T1W_HEAD_NII="${WORK_DIR}/sub-${SUBJECT_ID}_T1w_head.nii.gz"
T1W_ORIG_MGZ="${SUBJECTS_DIR}/sub-${SUBJECT_ID}/mri/orig.mgz"
mri_convert ${T1W_ORIG_MGZ} ${T1W_HEAD_NII}

echo "  FNIRT (nonlinear warp)..."
fnirt \
    --in=${T1W_HEAD_NII} \
    --ref=${MNI_TEMPLATE_HEAD} \
    --aff=${T1W_TO_MNI_MAT} \
    --cout=${T1W_TO_MNI_WARP} \
    --iout=${T1W_TO_MNI_NONLINEAR} \
    --config=${MNI_CONFIG}

echo "  ✅ Nonlinear registration done"
echo "✅ T1w → MNI transform computed (FLIRT + FNIRT)"
echo ""

# =========================================================================
# Step 4: Apply composed transforms (BOLD → T1w → MNI)
# =========================================================================

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

    # FreeSurfer LTA transform
    OUTPUT_LTA="${OUTPUT_DIR}/sub-${SUBJECT_ID}/transforms/sub-${SUBJECT_ID}_run-${RUN}_bold_to_t1w.lta"

    # Convert LTA to FSL format
    BOLD_TO_T1W_MAT="${WORK_DIR}/sub-${SUBJECT_ID}_run-${RUN}_bold_to_t1w.mat"

    # Extract middle volume as reference
    NVOLS=$(3dinfo -nv ${BOLD_FILE} 2>/dev/null || echo "100")
    REF_VOL=$((NVOLS / 2))
    BOLD_REF="${WORK_DIR}/sub-${SUBJECT_ID}_run-${RUN}_boldref.nii.gz"

    if [ ! -f "${BOLD_REF}" ]; then
        3dTcat -prefix ${BOLD_REF} ${BOLD_FILE}"[${REF_VOL}]" 2>/dev/null || \
            fslroi ${BOLD_FILE} ${BOLD_REF} ${REF_VOL} 1
    fi

    # Use tkregister2 to convert LTA to FSL format
    tkregister2 \
        --mov ${BOLD_REF} \
        --targ ${T1W_BRAIN_NII} \
        --reg ${WORK_DIR}/temp_reg.dat \
        --lta ${OUTPUT_LTA} \
        --noedit \
        --fslregout ${BOLD_TO_T1W_MAT}

    # Apply composed transform: BOLD → T1w (linear) → MNI (nonlinear)
    BOLD_MNI="${OUTPUT_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
    BOLD_TO_T1W_MAT="${WORK_DIR}/sub-${SUBJECT_ID}_run-${RUN}_bold_to_t1w.mat"

    # Use applywarp to apply both linear (premat) and nonlinear (warp) transforms
    applywarp \
        --in=${BOLD_FILE} \
        --ref=${MNI_TEMPLATE} \
        --out=${BOLD_MNI} \
        --warp=${T1W_TO_MNI_WARP} \
        --premat=${BOLD_TO_T1W_MAT} \
        --interp=trilinear

    # Create mask in MNI space
    MASK_MNI="${OUTPUT_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"

    3dAutomask -prefix ${MASK_MNI} ${BOLD_MNI} 2>/dev/null || \
        fslmaths ${BOLD_MNI} -bin ${MASK_MNI}

    echo "  ✅ BOLD in MNI: $(basename ${BOLD_MNI})"
    echo "  ✅ Mask in MNI: $(basename ${MASK_MNI})"
done

echo ""
echo "✅ All runs mapped to MNI space"

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
echo "  (b) BBR: ❌ SKIP (MI sufficient)"
echo "  (c) MNI normalization: ✅ FSL FLIRT + FNIRT (nonlinear, same as original_v3)"
echo ""
echo "Output files:"
echo "  Transforms: ${OUTPUT_DIR}/sub-${SUBJECT_ID}/transforms/"
echo "  BOLD (MNI): ${OUTPUT_DIR}/sub-${SUBJECT_ID}/func/*_space-MNI*"
echo "  Masks (MNI): ${OUTPUT_DIR}/sub-${SUBJECT_ID}/func/*_desc-brain_mask.nii.gz"
echo ""
echo "Next steps:"
echo "  1. Compute Dice:"
echo "     python scripts/compute_dice.py --subject ${SUBJECT_ID} --method method3_header_mi"
echo ""
echo "End time: $(date)"
echo "================================================================================"

exit 0
