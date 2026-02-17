#!/bin/bash
#SBATCH --job-name=1C_split
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --array=0-3%4
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --output=logs/split_half_%a_%j.out
#SBATCH --error=logs/split_half_%a_%j.err

# Test 1C: Split-Half SRM Reliability (4 ROIs)

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/1C_split_half
ROIS=(V1 V2 V3 hV4)
ROI=${ROIS[$SLURM_ARRAY_TASK_ID]}

echo "=== Test 1C: Split-Half SRM — ROI=${ROI} ==="
echo "Node: $(hostname), Job: ${SLURM_JOB_ID}, Array: ${SLURM_ARRAY_TASK_ID}"
echo "Start: $(date)"

(while true; do
    RSS=$(ps -o rss= -p $$ 2>/dev/null | awk '{print $1/1024}')
    echo "[MEM $(date +%H:%M:%S)] ${RSS:-0} MB"
    sleep 60
done) &
MEM_PID=$!

python ${SCRIPT_DIR}/run_split_half_srm.py --roi ${ROI}

EXIT_CODE=$?
kill $MEM_PID 2>/dev/null

echo "Exit code: ${EXIT_CODE}"
echo "End: $(date)"
exit ${EXIT_CODE}
