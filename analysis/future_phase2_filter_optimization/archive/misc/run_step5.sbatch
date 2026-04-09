#!/bin/bash
#SBATCH --job-name=cone_hc_repl
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline
#SBATCH --output=logs/step5_%j.out
#SBATCH --error=logs/step5_%j.err
#SBATCH --no-requeue

source ~/.bashrc
conda activate nilearn

mkdir -p logs

echo "=== Step 5: HC Replication Null Test ==="
echo "Start: $(date)"
echo "Node: $(hostname)"
echo "Job ID: $SLURM_JOB_ID"

mpirun -np 1 python scripts/step5_hc_replication_null.py \
    --n_mc 1000 \
    --output_dir results/step5_hc_replication

echo "End: $(date)"
