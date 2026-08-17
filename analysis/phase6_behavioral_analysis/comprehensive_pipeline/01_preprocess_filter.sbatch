#!/bin/bash
#SBATCH --job-name=cb_filt_prep
#SBATCH --array=1-2
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/future_phase3_behavioral_analysis/comprehensive_pipeline/logs/01_preprocess_sub-%a_%A.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/future_phase3_behavioral_analysis/comprehensive_pipeline/logs/01_preprocess_sub-%a_%A.err
#SBATCH --time=12:00:00
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --no-requeue
#SBATCH --open-mode=append

################################################################################
# Filter-Validation Preprocessing (sub-08/09 ses-02)
#
# Per-subject array job: T1w/BOLD registration (method3_header_mi) + confounds
# + ROI masks for the filter-applied session.
#
# Pipeline:
#   Step 1: FreeSurfer brain extraction
#   Step 2: BOLD -> T1w with mri_coreg --regheader
#   Step 3: T1w -> MNI152NLin2009cAsym with FLIRT + FNIRT
#   Step 4: Compose BOLD -> MNI applywarp
#   Step 5: Generate confounds (drift only / C010)
#   Step 6: Build ROI masks for V1/V2/V3/V4
#
# Outputs: ${OUTPUT_DIR}/sub-${SUBJECT_ID}/ses-${SESSION}/
################################################################################

set -e

# -----------------------------------------------------------------------------
# Subject + session config
# -----------------------------------------------------------------------------
SUBJECTS=(08 09)
SUBJECT_ID=${SUBJECTS[$((SLURM_ARRAY_TASK_ID - 1))]}
SESSION=02

echo "================================================================================"
echo "Filter-Validation Preprocess - sub-${SUBJECT_ID} ses-${SESSION}"
echo "Job: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}  Node: ${SLURM_NODELIST}"
echo "Start: $(date)"
echo "================================================================================"

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
PROJECT_ROOT=/scratch/connectome/haba6030/colorBlind
BIDS_DIR=/storage/connectome/haba6030/bids_editted
OUTPUT_DIR=/storage/connectome/haba6030/fmriprep_out_method3_header_mi
WORK_DIR=/storage/connectome/haba6030/fmriprep_work_method3_sub-${SUBJECT_ID}_ses-${SESSION}

# FreeSurfer
export FREESURFER_HOME=/usr/local/freesurfer/7.2.0
export PATH="${FREESURFER_HOME}/bin:${PATH}"
export SUBJECTS_DIR="${WORK_DIR}/freesurfer_subjects"
export FS_LICENSE=${FREESURFER_HOME}/license.txt
mkdir -p ${SUBJECTS_DIR}

# Output namespaces under ses-02 to preserve ses-01
mkdir -p ${OUTPUT_DIR}/sub-${SUBJECT_ID}/ses-${SESSION}/{func,anat,transforms}
mkdir -p ${WORK_DIR}
mkdir -p ${PROJECT_ROOT}/analysis/future_phase3_behavioral_analysis/comprehensive_pipeline/logs

# -----------------------------------------------------------------------------
# Input files (ses-02 BIDS; fall back to ses-01 anat if ses-02 anat absent)
# -----------------------------------------------------------------------------
T1W_FILE_SES02="${BIDS_DIR}/sub-${SUBJECT_ID}/ses-${SESSION}/anat/sub-${SUBJECT_ID}_ses-${SESSION}_acq-mprage_T1w.nii.gz"
T1W_FILE_SES01="${BIDS_DIR}/sub-${SUBJECT_ID}/ses-01/anat/sub-${SUBJECT_ID}_ses-01_acq-mprage_T1w.nii.gz"
T1W_FILE_FLAT="${BIDS_DIR}/sub-${SUBJECT_ID}/anat/sub-${SUBJECT_ID}_acq-mprage_T1w.nii.gz"

if [ -f "${T1W_FILE_SES02}" ]; then
    T1W_FILE=${T1W_FILE_SES02}
    echo "Using ses-02 T1w: ${T1W_FILE}"
elif [ -f "${T1W_FILE_SES01}" ]; then
    T1W_FILE=${T1W_FILE_SES01}
    echo "ses-02 T1w not found - reusing ses-01 T1w: ${T1W_FILE}"
elif [ -f "${T1W_FILE_FLAT}" ]; then
    T1W_FILE=${T1W_FILE_FLAT}
    echo "Reusing flat-layout T1w: ${T1W_FILE}"
else
    echo "ERROR: no T1w found for sub-${SUBJECT_ID}"
    exit 1
fi

# =============================================================================
# Step 1: FreeSurfer brain extraction
# =============================================================================
echo ""
echo "Step 1: brain extraction"
T1W_MGZ="${SUBJECTS_DIR}/sub-${SUBJECT_ID}/mri/orig.mgz"
BRAIN_MGZ="${SUBJECTS_DIR}/sub-${SUBJECT_ID}/mri/brain.mgz"
mkdir -p ${SUBJECTS_DIR}/sub-${SUBJECT_ID}/mri
mri_convert ${T1W_FILE} ${T1W_MGZ}

if command -v bet2 &> /dev/null; then
    bet2 ${T1W_FILE} ${WORK_DIR}/T1w_brain.nii.gz -f 0.5 -m
    mri_convert ${WORK_DIR}/T1w_brain.nii.gz ${BRAIN_MGZ}
else
    mri_watershed -useSRAS -surf ${SUBJECTS_DIR}/sub-${SUBJECT_ID}/surf/lh.brain ${T1W_MGZ} ${BRAIN_MGZ}
fi
echo "  done: ${BRAIN_MGZ}"

# =============================================================================
# Step 2: BOLD -> T1w (mri_coreg --regheader) per run
# =============================================================================
echo ""
echo "Step 2: BOLD -> T1w (mri_coreg)"
for RUN in 1 2 3 4 5 6; do
    BOLD_FILE="${BIDS_DIR}/sub-${SUBJECT_ID}/ses-${SESSION}/func/sub-${SUBJECT_ID}_ses-${SESSION}_task-rsvp_run-${RUN}_bold.nii.gz"
    if [ ! -f "${BOLD_FILE}" ]; then
        echo "  WARN: run ${RUN} missing - skip"
        continue
    fi

    NVOLS=$(3dinfo -nv ${BOLD_FILE} 2>/dev/null || echo "100")
    REF_VOL=$((NVOLS / 2))
    BOLD_REF="${WORK_DIR}/sub-${SUBJECT_ID}_ses-${SESSION}_run-${RUN}_boldref.nii.gz"
    3dTcat -prefix ${BOLD_REF} ${BOLD_FILE}"[${REF_VOL}]" 2>/dev/null || \
        fslroi ${BOLD_FILE} ${BOLD_REF} ${REF_VOL} 1

    OUT_LTA="${OUTPUT_DIR}/sub-${SUBJECT_ID}/ses-${SESSION}/transforms/sub-${SUBJECT_ID}_ses-${SESSION}_run-${RUN}_bold_to_t1w.lta"
    mri_coreg --ref ${BRAIN_MGZ} --mov ${BOLD_REF} --reg ${OUT_LTA} --regheader \
              --threads ${SLURM_CPUS_PER_TASK}

    if [ ! -f "${OUT_LTA}" ]; then
        echo "  ERROR: mri_coreg failed for run ${RUN}"
        continue
    fi
    echo "  run ${RUN}: $(basename ${OUT_LTA})"
done

# =============================================================================
# Step 3: T1w -> MNI (FLIRT + FNIRT, MNI152NLin2009cAsym)
# =============================================================================
echo ""
echo "Step 3: T1w -> MNI"
MNI_TEMPLATE="${PROJECT_ROOT}/templates/MNI152NLin2009cAsym_res-2_T1_brain.nii.gz"
MNI_TEMPLATE_HEAD="${PROJECT_ROOT}/templates/MNI152NLin2009cAsym_res-2_T1.nii.gz"
[ ! -f "${MNI_TEMPLATE_HEAD}" ] && MNI_TEMPLATE_HEAD=${MNI_TEMPLATE}

if [ ! -f "${MNI_TEMPLATE}" ]; then
    echo "ERROR: MNI template missing: ${MNI_TEMPLATE}"
    exit 1
fi

T1W_BRAIN_NII="${WORK_DIR}/T1w_brain.nii.gz"
[ ! -f "${T1W_BRAIN_NII}" ] && mri_convert ${BRAIN_MGZ} ${T1W_BRAIN_NII}

T1W_HEAD_NII="${WORK_DIR}/T1w_head.nii.gz"
mri_convert ${T1W_MGZ} ${T1W_HEAD_NII}

T1W_TO_MNI_MAT="${OUTPUT_DIR}/sub-${SUBJECT_ID}/ses-${SESSION}/transforms/sub-${SUBJECT_ID}_t1w_to_mni_affine.mat"
T1W_TO_MNI_WARP="${OUTPUT_DIR}/sub-${SUBJECT_ID}/ses-${SESSION}/transforms/sub-${SUBJECT_ID}_t1w_to_mni_warp.nii.gz"

flirt -in ${T1W_BRAIN_NII} -ref ${MNI_TEMPLATE} \
      -out ${WORK_DIR}/T1w_in_MNI_linear.nii.gz \
      -omat ${T1W_TO_MNI_MAT} \
      -bins 256 -cost corratio \
      -searchrx -90 90 -searchry -90 90 -searchrz -90 90 -dof 12

fnirt --in=${T1W_HEAD_NII} --ref=${MNI_TEMPLATE_HEAD} \
      --aff=${T1W_TO_MNI_MAT} --cout=${T1W_TO_MNI_WARP} \
      --iout=${WORK_DIR}/T1w_in_MNI_nonlinear.nii.gz \
      --config=/usr/local/fsl/etc/flirtsch/T1_2_MNI152_2mm.cnf

echo "  done: ${T1W_TO_MNI_WARP}"

# =============================================================================
# Step 4: Compose BOLD -> MNI per run
# =============================================================================
echo ""
echo "Step 4: BOLD -> MNI (applywarp)"
for RUN in 1 2 3 4 5 6; do
    BOLD_FILE="${BIDS_DIR}/sub-${SUBJECT_ID}/ses-${SESSION}/func/sub-${SUBJECT_ID}_ses-${SESSION}_task-rsvp_run-${RUN}_bold.nii.gz"
    [ ! -f "${BOLD_FILE}" ] && continue

    OUT_LTA="${OUTPUT_DIR}/sub-${SUBJECT_ID}/ses-${SESSION}/transforms/sub-${SUBJECT_ID}_ses-${SESSION}_run-${RUN}_bold_to_t1w.lta"
    BOLD_TO_T1W_MAT="${WORK_DIR}/sub-${SUBJECT_ID}_ses-${SESSION}_run-${RUN}_bold_to_t1w.mat"
    BOLD_REF="${WORK_DIR}/sub-${SUBJECT_ID}_ses-${SESSION}_run-${RUN}_boldref.nii.gz"

    tkregister2 --mov ${BOLD_REF} --targ ${T1W_BRAIN_NII} \
                --reg ${WORK_DIR}/temp_reg_${RUN}.dat \
                --lta ${OUT_LTA} --noedit \
                --fslregout ${BOLD_TO_T1W_MAT}

    BOLD_MNI="${OUTPUT_DIR}/sub-${SUBJECT_ID}/ses-${SESSION}/func/sub-${SUBJECT_ID}_ses-${SESSION}_task-rsvp_run-${RUN}_space-MNI152NLin2009cAsym_res-2_desc-preproc_bold.nii.gz"
    MASK_MNI="${OUTPUT_DIR}/sub-${SUBJECT_ID}/ses-${SESSION}/func/sub-${SUBJECT_ID}_ses-${SESSION}_task-rsvp_run-${RUN}_space-MNI152NLin2009cAsym_res-2_desc-brain_mask.nii.gz"

    applywarp --in=${BOLD_FILE} --ref=${MNI_TEMPLATE} --out=${BOLD_MNI} \
              --warp=${T1W_TO_MNI_WARP} --premat=${BOLD_TO_T1W_MAT} \
              --interp=trilinear

    3dAutomask -prefix ${MASK_MNI} ${BOLD_MNI} 2>/dev/null || \
        fslmaths ${BOLD_MNI} -Tmean -bin ${MASK_MNI}

    echo "  run ${RUN}: $(basename ${BOLD_MNI})"
done

# =============================================================================
# Step 5: Confounds generation (drift / C010)
# =============================================================================
echo ""
echo "Step 5: confounds"
eval "$(conda shell.bash hook)"
conda activate nilearn

python ${PROJECT_ROOT}/analysis/phase0_preprocessing/scripts/generate_confounds.py \
    --subject ${SUBJECT_ID} --session ${SESSION} --dataset method3_header_mi \
    || { echo "ERROR: generate_confounds failed"; exit 2; }

# =============================================================================
# Step 6: ROI masks (V1/V2/V3/V4)
# =============================================================================
echo ""
echo "Step 6: ROI masks"
python ${PROJECT_ROOT}/analysis/phase1_procrustes_decoding/roi_pipeline_selected_1202used.py \
    ${SUBJECT_ID} --session ${SESSION} --dataset method3_header_mi \
    || { echo "ERROR: roi_pipeline failed"; exit 3; }

echo ""
echo "================================================================================"
echo "sub-${SUBJECT_ID} ses-${SESSION} preprocess COMPLETE"
echo "End: $(date)"
echo "================================================================================"
exit 0
