#!/bin/bash
#SBATCH --job-name=2D_align
#SBATCH --nodelist=node2
#SBATCH --array=0-3%4
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/2D_alignment_comparison
#SBATCH --output=logs/alignment_comp_%a_%j.out
#SBATCH --error=logs/alignment_comp_%a_%j.err

# Test 2D: Alignment Method Comparison (4 ROIs)

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/2D_alignment_comparison
ROIS=(V1 V2 V3 hV4)
ROI=${ROIS[$SLURM_ARRAY_TASK_ID]}

echo "=== Test 2D: Alignment Comparison — ROI=${ROI} ==="
echo "Node: $(hostname), Job: ${SLURM_JOB_ID}, Array: ${SLURM_ARRAY_TASK_ID}"
echo "Start: $(date)"

(while true; do
    RSS=$(ps -o rss= -p $$ 2>/dev/null | awk '{print $1/1024}')
    echo "[MEM $(date +%H:%M:%S)] ${RSS:-0} MB"
    sleep 60
done) &
MEM_PID=$!

mpirun -np 1 python ${SCRIPT_DIR}/compare_alignment_stability.py --roi ${ROI}

EXIT_CODE=$?
kill $MEM_PID 2>/dev/null

echo "Exit code: ${EXIT_CODE}"
echo "End: $(date)"
exit ${EXIT_CODE}
