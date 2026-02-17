#!/bin/bash
#SBATCH --job-name=2C_ksel
#SBATCH --nodelist=node2
#SBATCH --array=0-27%14
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/2C_optimal_k_selection
#SBATCH --output=logs/k_selection_%a_%j.out
#SBATCH --error=logs/k_selection_%a_%j.err

# Test 2C: k-Selection CV (7 folds × 4 ROIs = 28 tasks)

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/2C_optimal_k_selection
ROIS=(V1 V2 V3 hV4)

# Decode array task ID: fold = task_id / 4, roi_idx = task_id % 4
FOLD=$(( SLURM_ARRAY_TASK_ID / 4 ))
ROI_IDX=$(( SLURM_ARRAY_TASK_ID % 4 ))
ROI=${ROIS[$ROI_IDX]}

echo "=== Test 2C: k-Selection CV — Fold=${FOLD}, ROI=${ROI} ==="
echo "Node: $(hostname), Job: ${SLURM_JOB_ID}, Array: ${SLURM_ARRAY_TASK_ID}"
echo "Start: $(date)"

(while true; do
    RSS=$(ps -o rss= -p $$ 2>/dev/null | awk '{print $1/1024}')
    echo "[MEM $(date +%H:%M:%S)] ${RSS:-0} MB"
    sleep 60
done) &
MEM_PID=$!

mpirun -np 1 python ${SCRIPT_DIR}/run_k_selection_cv.py --fold ${FOLD} --roi ${ROI}

EXIT_CODE=$?
kill $MEM_PID 2>/dev/null

echo "Exit code: ${EXIT_CODE}"
echo "End: $(date)"
exit ${EXIT_CODE}
