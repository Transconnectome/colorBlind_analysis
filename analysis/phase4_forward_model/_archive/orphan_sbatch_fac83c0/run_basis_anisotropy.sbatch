#!/bin/bash
#SBATCH --job-name=basis_aniso
#SBATCH --output=logs/basis_aniso_%j.out
#SBATCH --error=logs/basis_aniso_%j.err
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --nodelist=node2
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase4_forward_model

# A2: Basis Anisotropy Test
# Uniform vs cool-dense vs warm-dense channel spacing

source ~/.bashrc
conda activate nilearn

export PYTHONPATH="/scratch/connectome/haba6030/colorBlind/analysis/phase4_forward_model/scripts:${PYTHONPATH}"

BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010"

mkdir -p logs
mkdir -p results/basis_anisotropy

echo "========================================================================"
echo "A2: Basis Anisotropy Test"
echo "Started: $(date)"
echo "========================================================================"

mpirun -np 1 python scripts/basis_anisotropy_test.py \
    --baseline_dir "${BASELINE_DIR}" \
    --output_dir "results/basis_anisotropy"

if [ $? -ne 0 ]; then
    echo "ERROR: basis_anisotropy_test.py failed"
    exit 1
fi

echo
echo "========================================================================"
echo "A2 Complete: $(date)"
echo "Results: results/basis_anisotropy/"
echo "========================================================================"
