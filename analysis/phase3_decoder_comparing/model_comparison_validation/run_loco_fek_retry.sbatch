#!/bin/bash
#SBATCH --job-name=loco_fek
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/model_comparison_validation
#SBATCH --output=logs/loco_fek_%j.out
#SBATCH --error=logs/loco_fek_%j.err
#SBATCH --no-requeue

source ~/.bashrc
conda activate nilearn

SCRIPT_DIR="scripts"
BASELINE_DIR="/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010"
OUTPUT_DIR="results/loco_fek_retry"

mkdir -p "$OUTPUT_DIR"
mkdir -p logs

SUBJECTS="01 02 03 04 05 06 07 08 09 10"

for SUB in $SUBJECTS; do
    echo "=== sub-${SUB} ==="
    mpirun -np 1 python "${SCRIPT_DIR}/loco_fek_retry.py" \
        --baseline_dir "$BASELINE_DIR" \
        --output_dir "$OUTPUT_DIR" \
        --subject "$SUB" \
        --alignment procrustes
    echo ""
done

echo "All subjects done."