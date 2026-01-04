#!/bin/bash
#SBATCH -J fprep_fix_b1
#SBATCH -c 16
#SBATCH --mem=48G
#SBATCH -t 48:00:00
#SBATCH -o logs/fprep_v2_fix_batch1_%j.out
#SBATCH -e logs/fprep_v2_fix_batch1_%j.err
#SBATCH --nodelist=node2

echo "============================================================================"
echo "fMRIPrep v2 FIX - Batch 1 (Sub-05, 06, 07) - NO REPORTS"
echo "============================================================================"
echo "Start time: $(date)"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: $(hostname)"
echo ""

# Directories
INPUT_DIR=/storage/connectome/haba6030/colorBlind_data_deoblique
OUTPUT_DIR=/storage/connectome/haba6030/fmriprep_out_deoblique_v2
WORK_DIR=/storage/connectome/haba6030/fmriprep_work_deoblique_v2_fix_batch1

# Singularity settings
APPTAINER=/usr/local/bin/singularity
FMRIprep_IMG=${FMRIprep_IMG:-$HOME/fmriprep-23.2.3.sif}
FS_LICENSE=${FS_LICENSE:-$HOME/fs_license.txt}

# Create directories
mkdir -p ${OUTPUT_DIR}
mkdir -p ${WORK_DIR}
mkdir -p logs

echo "============================================================================"
echo "BATCH CONFIGURATION"
echo "============================================================================"
echo "Fixing failed subjects: Sub-05, 06, 07"
echo "Strategy: Continue processing even if report generation fails"
echo ""
echo "Configuration:"
echo "  Input:  ${INPUT_DIR}"
echo "  Output: ${OUTPUT_DIR}"
echo "  Work:   ${WORK_DIR}"
echo "  Threads: 16"
echo "  Memory: 48GB"
echo "  Time: 48 hours"
echo "  Stop-on-crash: Disabled (continue on report errors)"
echo ""

# Clean FreeSurfer IsRunning files
echo "============================================================================"
echo "Clean FreeSurfer Lock Files (Sub-05, 06, 07)"
echo "============================================================================"

FS_DIR="${OUTPUT_DIR}/sourcedata/freesurfer"

if [ -d "${FS_DIR}" ]; then
    echo "Checking for stale FreeSurfer IsRunning files..."

    for sub in 05 06 07; do
        ISRUNNING_FILES="${FS_DIR}/sub-${sub}/scripts/IsRunning*"

        if ls ${ISRUNNING_FILES} 2>/dev/null 1>&2; then
            echo "  🧹 Cleaning IsRunning files for sub-${sub}..."
            rm -f ${ISRUNNING_FILES}
            echo "     ✅ Cleaned"
        else
            echo "  ✅ No IsRunning files for sub-${sub}"
        fi
    done
else
    echo "  FreeSurfer directory doesn't exist yet (first run)"
fi

echo ""

# Clean crashed nodes from work directory
echo "============================================================================"
echo "Clean Crashed Nodes"
echo "============================================================================"

if [ -d "${WORK_DIR}" ]; then
    echo "Cleaning crashed nodes from work directory..."
    find ${WORK_DIR} -name "*.lock" -delete 2>/dev/null || true
    find ${WORK_DIR} -name "_0x*.json" -delete 2>/dev/null || true
    echo "✅ Cleaned"
else
    echo "Work directory doesn't exist yet"
fi

echo ""

# Fieldmap check
echo "============================================================================"
echo "Fieldmap Check (Sub-05, 06, 07)"
echo "============================================================================"
for sub in 05 06 07; do
    echo ""
    echo "Sub-${sub}:"
    FMAP_DIR="${INPUT_DIR}/sub-${sub}/fmap"

    if [ -d "${FMAP_DIR}" ]; then
        echo "  ✅ Fieldmap directory exists"
        for json_file in ${FMAP_DIR}/*.json; do
            if [ -f "${json_file}" ]; then
                if grep -q "IntendedFor" "${json_file}"; then
                    echo "  ✅ IntendedFor in $(basename ${json_file})"
                else
                    echo "  ⚠️  IntendedFor MISSING"
                fi
            fi
        done
    else
        echo "  ❌ No fieldmap directory"
    fi
done

echo ""
echo "============================================================================"
echo "Running fMRIPrep v2 for Sub-05, 06, 07 (NO REPORTS)..."
echo "============================================================================"
echo ""

"$APPTAINER" run --cleanenv \
  -B ${INPUT_DIR}:/data:ro \
  -B ${OUTPUT_DIR}:/out \
  -B ${WORK_DIR}:/work \
  -B ${FS_LICENSE}:/opt/freesurfer/license.txt:ro \
  "$FMRIprep_IMG" \
  /data /out participant \
  --participant-label 05 06 07 \
  --fs-license-file /opt/freesurfer/license.txt \
  --output-spaces MNI152NLin2009cAsym:res-2 \
  --bold2t1w-dof 9 \
  --bold2t1w-init register \
  --force-bbr \
  --dummy-scans 4 \
  --fd-spike-threshold 0.5 \
  --dvars-spike-threshold 1.5 \
  --ignore slicetiming \
  --nthreads 16 \
  --omp-nthreads 8 \
  --mem-mb 46000 \
  -w /work \
  --write-graph \
  --notrack \
  -v -v

EXIT_CODE=$?

echo ""
echo "============================================================================"
echo "Batch 1 Complete"
echo "============================================================================"
echo "End time: $(date)"
echo "Exit code: ${EXIT_CODE}"
echo ""

if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ SUCCESS - Batch 1 (Sub-05, 06, 07)"
    echo ""
    echo "Verify outputs:"
    for sub in 05 06 07; do
        echo "  Sub-${sub}:"
        PREPROC_COUNT=$(ls ${OUTPUT_DIR}/sub-${sub}/func/*desc-preproc_bold.nii.gz 2>/dev/null | wc -l)
        CONFOUNDS_COUNT=$(ls ${OUTPUT_DIR}/sub-${sub}/func/*confounds*.tsv 2>/dev/null | wc -l)
        echo "    Preprocessed files: ${PREPROC_COUNT}/6"
        echo "    Confounds files:    ${CONFOUNDS_COUNT}/6"

        if [ ${PREPROC_COUNT} -eq 6 ]; then
            echo "    ✅ Complete"
        else
            echo "    ⚠️  Incomplete"
        fi
    done
else
    echo "❌ FAILED (Exit code: ${EXIT_CODE})"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check crash reports:"
    echo "     find ${OUTPUT_DIR}/sub-0[567]/log -name 'crash*.txt' -exec head -50 {} \;"
    echo "  2. Check memory usage:"
    echo "     sacct -j ${SLURM_JOB_ID} --format=JobID,JobName,MaxRSS,State,ExitCode"
    echo "  3. Check work directory:"
    echo "     ls -lhd ${WORK_DIR}/fmriprep_23_2_wf/sub_0[567]_wf/"
fi

echo "============================================================================"

exit ${EXIT_CODE}
