#!/bin/bash
#SBATCH --job-name=gen_confounds
#SBATCH --array=1-60%20
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/confounds_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/confounds_%A_%a.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --no-requeue

################################################################################
# Generate confounds.tsv files from mcflirt motion parameters
#
# Prerequisites: add_motion_correction.sbatch must be completed first
#
# This creates fMRIPrep-compatible confounds files including:
# - Motion parameters (from mcflirt .par files)
# - Framewise displacement
# - Tissue signals (CSF, WM, global)
# - Cosine drift regressors
################################################################################

set -e

# Activate conda environment
source ~/.bashrc
conda activate nilearn

# Subject-run mapping (10 subjects × 6 runs = 60 jobs)
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
RUNS=(1 2 3 4 5 6)

# Calculate subject and run from array task ID
SUBJECT_IDX=$(( (SLURM_ARRAY_TASK_ID - 1) / 6 ))
RUN_IDX=$(( (SLURM_ARRAY_TASK_ID - 1) % 6 ))

SUBJECT_ID=${SUBJECTS[$SUBJECT_IDX]}
RUN=${RUNS[$RUN_IDX]}

echo "================================================================================"
echo "Generating Confounds: sub-${SUBJECT_ID} run-${RUN}"
echo "================================================================================"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Start time: $(date)"
echo ""

# Directories
SCRIPT_DIR="/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/scripts"
OUTPUT_DIR="/storage/connectome/haba6030/fmriprep_out_method3_header_mi"

# Check if motion .par file exists
MOTION_PAR="${OUTPUT_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_desc-motion.par"

if [ ! -f "${MOTION_PAR}" ]; then
    echo "❌ Motion .par file not found: ${MOTION_PAR}"
    echo "   Run add_motion_correction.sbatch first!"
    exit 1
fi

# Check if confounds file already exists
CONFOUNDS_FILE="${OUTPUT_DIR}/sub-${SUBJECT_ID}/func/sub-${SUBJECT_ID}_task-rsvp_run-${RUN}_desc-confounds_timeseries.tsv"

if [ -f "${CONFOUNDS_FILE}" ]; then
    echo "⚠️  Confounds file already exists, skipping: ${CONFOUNDS_FILE}"
    exit 0
fi

# Run confounds generation
echo "Running generate_confounds_mcflirt.py..."
echo ""

python ${SCRIPT_DIR}/generate_confounds_mcflirt.py \
    --subject ${SUBJECT_ID} \
    --run ${RUN} \
    --tr 1.5

echo ""
echo "================================================================================"
echo "✅ Confounds generation complete: sub-${SUBJECT_ID} run-${RUN}"
echo "================================================================================"
echo "End time: $(date)"
echo ""

exit 0
