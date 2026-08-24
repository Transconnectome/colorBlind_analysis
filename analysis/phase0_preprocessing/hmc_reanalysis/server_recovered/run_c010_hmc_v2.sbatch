#!/bin/bash
#SBATCH --job-name=C010_hmcv2
#SBATCH --array=1-36%12
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/C010hmcv2_%A_%a.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/C010hmcv2_%A_%a.err
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=2:00:00
#SBATCH --no-requeue
#SBATCH --open-mode=append

################################################################################
# C010 amplitudes on the corrected HMC arm (hmc_v2, single interpolation).
#
# Uses the existing frozen-pipeline wrapper run_c010_hmc.py, overriding only the
# two path constants. GLM / drift / Procrustes code is byte-identical to canon.
# ROI masks stay on method3_header_mi so both arms share the same voxel set.
#
# Array: 36 tasks = 9 subjects (sub-10 excluded) x 4 ROIs.
################################################################################

SUBJECTS=(01 01 01 01 02 02 02 02 03 03 03 03 04 04 04 04 05 05 05 05 06 06 06 06 07 07 07 07 08 08 08 08 09 09 09 09)
ROIS=(V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4 V1 V2 V3 V4)

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
    --roi ${ROI} \
    --fmriprep-dir /storage/connectome/haba6030/fmriprep_out_method3_hmc_v2 \
    --output-dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010_hmc_v2

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
    echo "OK: sub-${SUBJECT} ${ROI}"
else
    echo "FAILED: sub-${SUBJECT} ${ROI} (exit ${EXIT_CODE})"
fi
echo "End: $(date)"
exit $EXIT_CODE
