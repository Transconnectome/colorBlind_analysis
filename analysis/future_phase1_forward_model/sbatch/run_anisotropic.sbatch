#!/bin/bash
#SBATCH --job-name=aniso
#SBATCH --output=logs/aniso_%j.out
#SBATCH --error=logs/aniso_%j.err
#SBATCH --time=03:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --nodelist=node2
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model

# B2: Anisotropic Basis — Parametric Channel Shift
# Nested LOCO with (a,b) grid search (21x21 = 441 points)

source ~/.bashrc
conda activate nilearn

export PYTHONPATH="/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model/scripts:${PYTHONPATH}"

BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010"

mkdir -p logs
mkdir -p results/anisotropic_basis

echo "========================================================================"
echo "B2: Anisotropic Basis — Parametric Channel Shift"
echo "Started: $(date)"
echo "========================================================================"

mpirun -np 1 python scripts/fit_anisotropic_basis.py \
    --baseline_dir "${BASELINE_DIR}" \
    --output_dir "results/anisotropic_basis" \
    --ab_n_grid 21 \
    --ab_range 0.5

if [ $? -ne 0 ]; then
    echo "ERROR: fit_anisotropic_basis.py failed"
    exit 1
fi

echo
echo "========================================================================"
echo "B2 Complete: $(date)"
echo "Results: results/anisotropic_basis/"
echo "========================================================================"
