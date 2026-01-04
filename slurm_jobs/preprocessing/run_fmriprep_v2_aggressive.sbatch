#!/bin/bash
#SBATCH --job-name=fprep_aggr
#SBATCH --output=logs/fmriprep_v2_aggr_%A_%a.out
#SBATCH --error=logs/fmriprep_v2_aggr_%A_%a.err
#SBATCH --array=1-10
#SBATCH --time=12:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=32G

################################################################################
# fMRIPrep v2 - Aggressive Array Job (FASTEST!)
#
# Strategy: Reduce resources per job → more parallel jobs
#   - CPU: 6 per job (vs 8)
#   - Memory: 32GB per job (vs 48GB)
#   - Node capacity: ~5 jobs per node
#   - Expected: node2(5) + node4(5) = 10 jobs simultaneously
#
# Expected: 8-12 hours (absolute minimum)
#
# Risk: Resource contention, but fMRIPrep usually handles it well
################################################################################

set -e

# Map array task ID to subject
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT_ID=${SUBJECTS[$((SLURM_ARRAY_TASK_ID - 1))]}

BIDS_DIR="/storage/connectome/haba6030/colorBlind_data_afni_deoblique"
OUTPUT_DIR="/storage/connectome/haba6030/fmriprep_out_afni_deoblique"
WORK_DIR="/storage/connectome/haba6030/fmriprep_work_afni_aggr_${SUBJECT_ID}"
FS_LICENSE="/storage/connectome/haba6030/license.txt"

echo "================================================================================"
echo "fMRIPrep v2 - Aggressive Array [${SLURM_ARRAY_TASK_ID}/10]"
echo "================================================================================"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Node: $SLURM_NODELIST"
echo "Subject: sub-${SUBJECT_ID}"
echo "Start time: $(date)"
echo ""
echo "Strategy: Reduced resources for maximum parallelization"
echo "CPUs: ${SLURM_CPUS_PER_TASK}, Memory: ${SLURM_MEM_PER_NODE}MB"
echo "================================================================================"
echo ""

# Create directories
mkdir -p ${OUTPUT_DIR}
mkdir -p ${WORK_DIR}

# Load Singularity
module load singularity/3.11.4

FMRIPREP_CONTAINER="/storage/connectome/haba6030/fmriprep-24.0.1.sif"

echo "✅ Ready to process sub-${SUBJECT_ID}"
echo ""

# Run fMRIPrep with reduced resources
singularity run --cleanenv \
    -B ${BIDS_DIR}:/data:ro \
    -B ${OUTPUT_DIR}:/out \
    -B ${WORK_DIR}:/work \
    -B ${FS_LICENSE}:/opt/freesurfer/license.txt:ro \
    ${FMRIPREP_CONTAINER} \
    /data /out participant \
    --participant-label ${SUBJECT_ID} \
    --skip_bids_validation \
    --fs-license-file /opt/freesurfer/license.txt \
    --output-spaces MNI152NLin2009cAsym:res-2 \
    --bold2t1w-dof 9 \
    --force-bbr \
    --dummy-scans 0 \
    --skull-strip-fixed-seed \
    --nthreads ${SLURM_CPUS_PER_TASK} \
    --omp-nthreads 3 \
    --mem_mb $((SLURM_MEM_PER_NODE - 4000)) \
    --work-dir /work \
    --write-graph \
    --stop-on-first-crash

EXIT_CODE=$?

echo ""
echo "================================================================================"
if [ ${EXIT_CODE} -eq 0 ]; then
    echo "✅ sub-${SUBJECT_ID} COMPLETE"
else
    echo "❌ sub-${SUBJECT_ID} FAILED (exit code: ${EXIT_CODE})"
fi
echo "================================================================================"
echo ""
echo "End time: $(date)"
echo "================================================================================"

exit ${EXIT_CODE}
