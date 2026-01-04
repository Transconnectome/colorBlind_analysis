#!/bin/bash
#SBATCH -J fprep_fast
#SBATCH -c 6
#SBATCH --mem=32G
#SBATCH -t 12:00:00
#SBATCH -o logs/fprep_afni_fast_%A_%a.out
#SBATCH -e logs/fprep_afni_fast_%A_%a.err
#SBATCH --array=1-10
#SBATCH --nodelist=node2,node4

################################################################################
# fMRIPrep - AFNI Deobliqued Data - Aggressive Array (FASTEST!)
#
# Based on working configuration
# Reduced resources for maximum parallelization (8-12 hours)
################################################################################

# Map array task ID to subject
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT_ID=${SUBJECTS[$((SLURM_ARRAY_TASK_ID - 1))]}

echo "============================================================================"
echo "fMRIPrep FAST - AFNI Deobliqued [${SLURM_ARRAY_TASK_ID}/10]"
echo "============================================================================"
echo "Start time: $(date)"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Node: $(hostname)"
echo "Subject: sub-${SUBJECT_ID}"
echo "Strategy: Reduced resources for maximum parallelization"
echo ""

# Directories
INPUT_DIR=/storage/connectome/haba6030/colorBlind_data_afni_deoblique
OUTPUT_DIR=/storage/connectome/haba6030/fmriprep_out_afni_deoblique
WORK_DIR=/storage/connectome/haba6030/fmriprep_work_afni_fast_${SUBJECT_ID}

# Singularity settings - SHARED STORAGE (accessible from all nodes)
APPTAINER=/usr/local/bin/singularity
FMRIprep_IMG=/storage/connectome/haba6030/fmriprep-23.2.3.sif
FS_LICENSE=/storage/connectome/haba6030/fs_license.txt

# Create directories
mkdir -p ${OUTPUT_DIR}
mkdir -p ${WORK_DIR}
mkdir -p logs

echo "Configuration:"
echo "  Subject: sub-${SUBJECT_ID}"
echo "  Threads: 6 (reduced for parallelization)"
echo "  Memory:  32GB (reduced for parallelization)"
echo ""

# Clean FreeSurfer IsRunning files
FS_DIR="${OUTPUT_DIR}/sourcedata/freesurfer"
if [ -d "${FS_DIR}/sub-${SUBJECT_ID}" ]; then
    ISRUNNING_FILES="${FS_DIR}/sub-${SUBJECT_ID}/scripts/IsRunning*"
    if ls ${ISRUNNING_FILES} 2>/dev/null 1>&2; then
        rm -f ${ISRUNNING_FILES}
    fi
fi

# Clean crashed nodes
if [ -d "${WORK_DIR}" ]; then
    find ${WORK_DIR} -name "*.lock" -delete 2>/dev/null || true
    find ${WORK_DIR} -name "_0x*.json" -delete 2>/dev/null || true
fi

echo "============================================================================"
echo "Running fMRIPrep for sub-${SUBJECT_ID}..."
echo "============================================================================"
echo ""

# Run fMRIPrep - Reduced resources
"$APPTAINER" run --cleanenv \
  -B ${INPUT_DIR}:/data:ro \
  -B ${OUTPUT_DIR}:/out \
  -B ${WORK_DIR}:/work \
  -B ${FS_LICENSE}:/opt/freesurfer/license.txt:ro \
  "$FMRIprep_IMG" \
  /data /out participant \
  --participant-label ${SUBJECT_ID} \
  --skip_bids_validation \
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
  --nthreads 6 \
  --omp-nthreads 3 \
  --mem-mb 30000 \
  -w /work \
  --write-graph \
  --notrack \
  -v -v

EXIT_CODE=$?

echo ""
echo "============================================================================"
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ SUCCESS - sub-${SUBJECT_ID}"
    PREPROC_COUNT=$(ls ${OUTPUT_DIR}/sub-${SUBJECT_ID}/func/*desc-preproc_bold.nii.gz 2>/dev/null | wc -l)
    echo "  Preprocessed files: ${PREPROC_COUNT}/6"
else
    echo "❌ FAILED - sub-${SUBJECT_ID} (Exit code: ${EXIT_CODE})"
fi
echo "End time: $(date)"
echo "============================================================================"

exit ${EXIT_CODE}
