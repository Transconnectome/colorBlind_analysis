#!/bin/bash
#SBATCH --job-name=C010_motshift
#SBATCH --array=1-40%8
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/C010motshift_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/C010motshift_%A_%a.err
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=2:00:00
#SBATCH --no-requeue
#SBATCH --open-mode=append

################################################################################
# C010 + motion regression (재샘플링 없음) — 2026-08-05.
#
# Runs the FROZEN phase1 pipeline unmodified via run_c010_motreg.py. FMRIPREP_DIR
# stays on the ORIGINAL method3 tree (no resampling); only the GLM design gains 12
# MCFLIRT motion regressors. ROI masks unchanged, so the difference is motion-
# correlated variance alone.
#
# Array: 40 tasks = 10 subjects x 4 ROIs.
################################################################################

SUBJECTS=(01 01 01 01 02 02 02 02 03 03 03 03 04 04 04 04 05 05 05 05 06 06 06 06 07 07 07 07 08 08 08 08 09 09 09 09 10 10 10 10)
ROIS=(V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4)

IDX=$((SLURM_ARRAY_TASK_ID - 1))
SUBJECT=${SUBJECTS[$IDX]}
ROI=${ROIS[$IDX]}

echo "========================================"
echo "Job: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}   Node: ${SLURM_NODELIST}"
echo "sub-${SUBJECT}  ${ROI}"
echo "Start: $(date)"
echo "========================================"

source ~/.bashrc
conda activate nilearn

python /scratch/connectome/haba6030/colorBlind/analysis/phase0_preprocessing/hmc_reanalysis/run_c010_motreg.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --circshift 42 \
    --output-dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010_motshift

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "OK: sub-${SUBJECT} ${ROI}"
else
    echo "FAILED: sub-${SUBJECT} ${ROI} (exit ${EXIT_CODE})"
fi
echo "End: $(date)"
exit $EXIT_CODE
