#!/bin/bash
#SBATCH --job-name=s10b_v2
#SBATCH --nodelist=node2
#SBATCH --array=0-1
#SBATCH --time=03:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=logs/s10b_v2_%A_%a.out
#SBATCH --error=logs/s10b_v2_%A_%a.err

set -euo pipefail

mkdir -p logs results/s10_inclusion

PYTHON=/scratch/connectome/haba6030/colorBlind/.venv/bin/python

SUBJECTS=("sub-08" "sub-09")
SUBJECT=${SUBJECTS[$SLURM_ARRAY_TASK_ID]}

echo "==================================================================="
echo "S10b v2: 1000× resample inclusion screening"
echo "  Array task: $SLURM_ARRAY_TASK_ID  Subject: $SUBJECT"
echo "  Node: $(hostname)  Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "==================================================================="

$PYTHON scripts/s10b_v2_resample.py --subject $SUBJECT

echo "==================================================================="
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
