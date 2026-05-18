#!/bin/bash
#SBATCH --job-name=optC_boot
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization
#SBATCH --output=logs/optC_boot_%j.out
#SBATCH --error=logs/optC_boot_%j.err

set -e
source ~/.bashrc
conda activate nilearn

mkdir -p results/server_bootstrap logs

python scripts/server_weight_bootstrap.py \
    --n_boot 2000 \
    --out_dir results/server_bootstrap

echo "Done."
