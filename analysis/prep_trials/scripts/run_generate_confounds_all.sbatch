#!/bin/bash
#SBATCH --job-name=confounds_all
#SBATCH --array=1-60%10
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/confounds_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/confounds_%A_%a.err
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --qos=shared
#SBATCH --nodelist=node2

################################################################################
# Generate confounds with aCompCor for all subjects and runs
#
# Array job: 10 subjects × 6 runs = 60 tasks
# Parallel: 10 tasks at a time
#
# Outputs:
#   - Confounds TSV for each run (with aCompCor)
#   - QC visualizations per subject
################################################################################

set -e

# Subject-run mapping
SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
RUNS=(1 2 3 4 5 6)

# Calculate subject and run from array task ID
TOTAL_RUNS=6
SUBJECT_IDX=$(( (SLURM_ARRAY_TASK_ID - 1) / TOTAL_RUNS ))
RUN_IDX=$(( (SLURM_ARRAY_TASK_ID - 1) % TOTAL_RUNS ))

SUBJECT_ID=${SUBJECTS[$SUBJECT_IDX]}
RUN=${RUNS[$RUN_IDX]}

echo "================================================================================"
echo "Generate Confounds with aCompCor"
echo "================================================================================"
echo "Task ID: ${SLURM_ARRAY_TASK_ID}"
echo "Job ID: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Subject: sub-${SUBJECT_ID}"
echo "Run: ${RUN}"
echo "Start time: $(date)"
echo "================================================================================"
echo ""

# Environment setup
source ~/.bashrc
conda activate nilearn

# Run confounds generation
cd /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/scripts

python generate_confounds.py \
    --subject ${SUBJECT_ID} \
    --run ${RUN} \
    --method method3_header_mi \
    --tr 1.5

echo ""
echo "================================================================================"
echo "Task ${SLURM_ARRAY_TASK_ID} Complete: sub-${SUBJECT_ID} run-${RUN}"
echo "================================================================================"
echo "End time: $(date)"
echo ""
