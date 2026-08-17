#!/bin/bash
#SBATCH --job-name=C010_hmc
#SBATCH --array=1-40%8
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/C010hmc_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/C010hmc_%A_%a.err
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=2:00:00
#SBATCH --no-requeue
#SBATCH --open-mode=append

################################################################################
# C010 re-run on the HMC tree — Candidate A (2026-08-05).
#
# Runs the FROZEN phase1 pipeline unmodified via run_c010_hmc.py, which only
# rebinds FMRIPREP_DIR and OUTPUT_DIR. ROI masks stay on method3_header_mi so
# both arms share the same voxel set and the difference is HMC alone.
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

python /scratch/connectome/haba6030/colorBlind/analysis/phase0_preprocessing/hmc_reanalysis/run_c010_hmc.py \
    --subject ${SUBJECT} \
    --roi ${ROI}

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "OK: sub-${SUBJECT} ${ROI}"
else
    echo "FAILED: sub-${SUBJECT} ${ROI} (exit ${EXIT_CODE})"
fi
echo "End: $(date)"
exit $EXIT_CODE
