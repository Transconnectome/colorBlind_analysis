#!/bin/bash
#SBATCH --job-name=1B_loso
#SBATCH --nodelist=node2
#SBATCH --array=0-6%7
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:10:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/1B_loso_stability
#SBATCH --output=logs/loso_fold%a_%j.out
#SBATCH --error=logs/loso_fold%a_%j.err

# Test 1B: LOSO SRM Stability (7 folds, all ROIs per fold)

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR=/scratch/connectome/haba6030/colorBlind/analysis/phase2_SRM_across_between/validation/1B_loso_stability

echo "=== Test 1B: LOSO Fold ${SLURM_ARRAY_TASK_ID} ==="
echo "Node: $(hostname), Job: ${SLURM_JOB_ID}, Array: ${SLURM_ARRAY_TASK_ID}"
echo "Memory limit: ${SLURM_MEM_PER_NODE}MB"
echo "Start: $(date)"

# Monitor memory in background
(while true; do
    RSS=$(ps -o rss= -p $$ 2>/dev/null | awk '{print $1/1024}')
    echo "[MEM $(date +%H:%M:%S)] ${RSS:-0} MB"
    sleep 60
done) &
MEM_PID=$!

mpirun -np 1 python ${SCRIPT_DIR}/run_loso_srm.py --fold ${SLURM_ARRAY_TASK_ID}

EXIT_CODE=$?
kill $MEM_PID 2>/dev/null

echo "Exit code: ${EXIT_CODE}"
echo "End: $(date)"
exit ${EXIT_CODE}
