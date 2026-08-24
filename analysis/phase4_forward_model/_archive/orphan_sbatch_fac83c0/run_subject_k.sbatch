#!/bin/bash
#SBATCH --job-name=subj_k
#SBATCH --output=logs/subj_k_%j.out
#SBATCH --error=logs/subj_k_%j.err
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --nodelist=node2
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase4_forward_model

# B1: Subject-Specific K Selection
# Sweeps K in [2,3,4,5,6,8,10,12] for each subject x ROI

source ~/.bashrc
conda activate nilearn

export PYTHONPATH="/scratch/connectome/haba6030/colorBlind/analysis/phase4_forward_model/scripts:${PYTHONPATH}"

BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010"

mkdir -p logs
mkdir -p results/subject_k

echo "========================================================================"
echo "B1: Subject-Specific K Selection"
echo "Started: $(date)"
echo "========================================================================"

mpirun -np 1 python scripts/subject_k_selection.py \
    --baseline_dir "${BASELINE_DIR}" \
    --output_dir "results/subject_k"

if [ $? -ne 0 ]; then
    echo "ERROR: subject_k_selection.py failed"
    exit 1
fi

echo
echo "========================================================================"
echo "B1 Complete: $(date)"
echo "Results: results/subject_k/"
echo "========================================================================"
