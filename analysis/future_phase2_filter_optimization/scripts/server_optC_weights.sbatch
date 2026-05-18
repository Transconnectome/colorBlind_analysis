#!/bin/bash
#SBATCH --job-name=optC_weights
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=03:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=logs/optC_weights_%j.out
#SBATCH --error=logs/optC_weights_%j.err

set -e
source ~/.bashrc
conda activate nilearn

mkdir -p results/hc_optC_exact logs

python scripts/server_hc_optC_exact_components.py \
    --out_dir results/hc_optC_exact

echo "Done."
