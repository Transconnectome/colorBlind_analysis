#!/bin/bash
#SBATCH --job-name=val_loro_3aln
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=04:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation
#SBATCH --output=logs/val_loro_3aln_%j.out
#SBATCH --error=logs/val_loro_3aln_%j.err

# Environment
source ~/.bashrc
conda activate nilearn

# Paths
BASE=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation
SCRIPT_DIR=${BASE}/scripts
BASELINE_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010

echo "=============================="
echo "Job: $SLURM_JOB_ID"
echo "Node: $(hostname)"
echo "Start: $(date)"
echo "=============================="

for ALN in raw procrustes srm; do
    echo ""
    echo "============================================"
    echo "Alignment: ${ALN}"
    echo "============================================"

    PERF_DIR=${BASE}/results/loro/${ALN}
    OUT_DIR=${BASE}/results/loro/${ALN}/validation

    python ${SCRIPT_DIR}/validation_tests.py \
        --baseline_dir ${BASELINE_DIR} \
        --performance_dir ${PERF_DIR} \
        --output_dir ${OUT_DIR} \
        --alignment ${ALN} \
        --tests bootstrap reliability generalization

    echo "Done: ${ALN} at $(date)"
done

echo "=============================="
echo "All 3 alignments complete: $(date)"
echo "=============================="
