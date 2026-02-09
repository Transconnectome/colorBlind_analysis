#!/bin/bash
#SBATCH --job-name=c010_srm_between
#SBATCH --output=logs/c010_srm_%A_%a.out
#SBATCH --error=logs/c010_srm_%A_%a.err
#SBATCH --qos=shared
#SBATCH --nodelist=node2,node4
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=2:00:00
#SBATCH --array=1-4%2
#SBATCH --no-requeue

# C010 Between-Subject SRM Analysis (SLURM Array Job)
#
# CONSERVATIVE SETTINGS (Default):
# - Memory: 16G per task (adjust after profiling test)
# - CPUs: 2 per task (SRM is memory-bound, not CPU-bound)
# - Max concurrent: 2 tasks (32GB total peak)
# - Nodes: node2, node4 (CPU nodes with shared QoS)
#
# IMPORTANT: Run test_c010_srm_server.sh first to measure actual resource usage
# and adjust --mem if needed.
#
# Array task mapping:
# 1 = V1, 2 = V2, 3 = V3, 4 = V4

set -e

echo "======================================"
echo "C010 Between-Subject SRM (Array Job)"
echo "======================================"
echo "Job ID: $SLURM_JOB_ID"
echo "Array Task ID: $SLURM_ARRAY_TASK_ID"
echo "Node: $SLURMD_NODENAME"
echo "CPUs: $SLURM_CPUS_PER_TASK"
echo "Memory: 16G"
echo ""

# Activate environment
source ~/.bashrc
conda activate nilearn

# ROI mapping
ROIS=(V1 V2 V3 V4)
ROI=${ROIS[$((SLURM_ARRAY_TASK_ID - 1))]}

echo "Processing ROI: $ROI"
echo ""

# Change to work directory
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/SRM

# Create logs directory
mkdir -p logs

# Run analysis
echo "Starting analysis..."
python evaluate_srm_c010_between_subject.py --roi $ROI

echo ""
echo "Completed: $ROI"
echo "======================================"
