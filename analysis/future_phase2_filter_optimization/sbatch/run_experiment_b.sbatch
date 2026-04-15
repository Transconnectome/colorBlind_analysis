#!/bin/bash
#SBATCH --job-name=exp_b_weight
#SBATCH --nodelist=node2
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=logs/experiment_b_%j.out
#SBATCH --error=logs/experiment_b_%j.err

source ~/.bashrc
conda activate nilearn

export PYTHONUNBUFFERED=1

echo "=== Experiment B: Weight Sweep + HC LOO Validation ==="
echo "Date: $(date)"
echo "Node: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"
echo ""

mkdir -p logs results/experiment_b_weight_sweep

python scripts/experiment_b_weight_sweep.py \
    --subjects 01 02 03 04 05 06 07 08 09 10 \
    --output_dir results/experiment_b_weight_sweep

echo ""
echo "=== Done: $(date) ==="
