#!/bin/bash
#SBATCH --job-name=hierarch
#SBATCH --output=logs/hierarch_%j.out
#SBATCH --error=logs/hierarch_%j.err
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --nodelist=node2
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model

# B3: Hierarchical FE — HC Prior + CVD Deviation
# Nested LOCO with lambda grid search

source ~/.bashrc
conda activate nilearn

export PYTHONPATH="/scratch/connectome/haba6030/colorBlind/analysis/future_phase1_forward_model/scripts:${PYTHONPATH}"

BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010"

mkdir -p logs
mkdir -p results/hierarchical_fe

echo "========================================================================"
echo "B3: Hierarchical FE — HC Prior + CVD Deviation"
echo "Started: $(date)"
echo "========================================================================"

mpirun -np 1 python scripts/fit_hierarchical_fe.py \
    --baseline_dir "${BASELINE_DIR}" \
    --output_dir "results/hierarchical_fe"

if [ $? -ne 0 ]; then
    echo "ERROR: fit_hierarchical_fe.py failed"
    exit 1
fi

echo
echo "========================================================================"
echo "B3 Complete: $(date)"
echo "Results: results/hierarchical_fe/"
echo "========================================================================"
