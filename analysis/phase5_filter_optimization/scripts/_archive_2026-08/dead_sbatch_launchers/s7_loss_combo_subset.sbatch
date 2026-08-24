#!/bin/bash
#SBATCH --job-name=s7_combo
#SBATCH --nodelist=node2
#SBATCH --array=7-11
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase5_filter_optimization
#SBATCH --output=logs/s7_combo_%A_%a.out
#SBATCH --error=logs/s7_combo_%A_%a.err

set -euo pipefail

mkdir -p logs results/s7_loss_combo_subset

PYTHON=/scratch/connectome/haba6030/colorBlind/.venv/bin/python

echo "==================================================================="
echo "S7: Loss combination + HC subset resample sprint"
echo "  Array task: $SLURM_ARRAY_TASK_ID / 11"
echo "  Node: $(hostname)"
echo "  Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "  Python: $PYTHON"
echo "==================================================================="

$PYTHON scripts/s7_loss_combo_subset.py --cell-idx $SLURM_ARRAY_TASK_ID

echo "==================================================================="
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "==================================================================="
