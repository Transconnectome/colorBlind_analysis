#!/bin/bash
#SBATCH --job-name=C010hmc2
#SBATCH --array=1-16%8
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/C010hmc2_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/C010hmc2_%A_%a.err
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=2:00:00
#SBATCH --no-requeue
#SBATCH --open-mode=append

################################################################################
# exp2 C010 re-run on the HMC tree — Candidate A (2026-08-05).
# Array: 16 = 2 subjects x 4 ROIs x 2 mask variants (native, matched).
# Both variants are produced because downstream exp2 scripts accept --variant
# and the reported analyses use both.
################################################################################

SUBJECTS=(08 08 08 08 09 09 09 09 08 08 08 08 09 09 09 09)
ROIS=(V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4)
VARIANTS=(native native native native native native native native matched matched matched matched matched matched matched matched)

IDX=$((SLURM_ARRAY_TASK_ID - 1))
SUBJECT=${SUBJECTS[$IDX]}
ROI=${ROIS[$IDX]}
VARIANT=${VARIANTS[$IDX]}

echo "========================================"
echo "Job: ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}   Node: ${SLURM_NODELIST}"
echo "sub-${SUBJECT}  ${ROI}  variant=${VARIANT}"
echo "Start: $(date)"
echo "========================================"

source ~/.bashrc
conda activate nilearn

python /scratch/connectome/haba6030/colorBlind/analysis/phase0_preprocessing/hmc_reanalysis/run_c010_hmc_exp2.py \
    --subject ${SUBJECT} \
    --roi ${ROI} \
    --mask-variant ${VARIANT}

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "OK: sub-${SUBJECT} ${ROI} ${VARIANT}"
else
    echo "FAILED: sub-${SUBJECT} ${ROI} ${VARIANT} (exit ${EXIT_CODE})"
fi
echo "End: $(date)"
exit $EXIT_CODE
