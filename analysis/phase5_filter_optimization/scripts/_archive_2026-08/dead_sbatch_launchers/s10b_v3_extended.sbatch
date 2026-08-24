#!/bin/bash
#SBATCH --job-name=s10b_v3
#SBATCH --nodelist=node2
#SBATCH --array=0-4
#SBATCH --time=03:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=12G
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase5_filter_optimization
#SBATCH --output=logs/s10b_v3_%A_%a.out
#SBATCH --error=logs/s10b_v3_%A_%a.err

set -euo pipefail
mkdir -p logs results/s10_inclusion
export PYTHONUNBUFFERED=1
export PYTHONDONTWRITEBYTECODE=1

# Defensive: clean any stale __pycache__ before run
find /scratch/connectome/haba6030/colorBlind/analysis -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

PYTHON=/scratch/connectome/haba6030/colorBlind/.venv/bin/python

# Task 0 = sub-09 (7 combos, single chunk)
# Tasks 1-4 = sub-08 (40 combos split into 4 chunks of 10)

case $SLURM_ARRAY_TASK_ID in
  0) CMD="--subject sub-09" ;;
  1) CMD="--subject sub-08 --combo-start 0 --combo-end 10" ;;
  2) CMD="--subject sub-08 --combo-start 10 --combo-end 20" ;;
  3) CMD="--subject sub-08 --combo-start 20 --combo-end 30" ;;
  4) CMD="--subject sub-08 --combo-start 30 --combo-end 40" ;;
  *) echo "Invalid task id"; exit 1 ;;
esac

echo "==================================================================="
echo "S10b v3 array task $SLURM_ARRAY_TASK_ID: $CMD"
echo "Node: $(hostname)  Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "==================================================================="

$PYTHON scripts/s10b_v3_extended.py $CMD

echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
