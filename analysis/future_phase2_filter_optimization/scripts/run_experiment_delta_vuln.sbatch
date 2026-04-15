#!/bin/bash
#SBATCH --job-name=exp_c_delta_vuln
#SBATCH --nodelist=node2
#SBATCH --mem=8G
#SBATCH --cpus-per-task=1
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=logs/exp_c_delta_vuln_%j.out
#SBATCH --error=logs/exp_c_delta_vuln_%j.err

source ~/.bashrc
conda activate nilearn

mkdir -p logs

echo "=== Experiment C: Delta-Vulnerability ==="
echo "Start: $(date)"
echo "Node: $(hostname)"
echo "PWD: $(pwd)"

python scripts/experiment_delta_vuln.py \
    --output_dir results/experiment_c_delta_vuln

echo "End: $(date)"
