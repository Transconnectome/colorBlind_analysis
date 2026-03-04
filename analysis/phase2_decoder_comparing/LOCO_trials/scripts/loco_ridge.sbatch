#!/bin/bash
#SBATCH --job-name=loco_ridge
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --array=1-10%5
#SBATCH --output=logs/ridge_%a.out
#SBATCH --error=logs/ridge_%a.err
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase2_decoder_comparing/LOCO_trials

source ~/.bashrc
conda activate nilearn

SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT=${SUBJECTS[$((SLURM_ARRAY_TASK_ID - 1))]}

echo "=== Ridge LOCO: sub-${SUBJECT} ==="
echo "Mode: fixed"
echo "Start: $(date)"

# Run all 3 modes sequentially for each subject
for MODE in fixed nested combined; do
    echo ""
    echo "--- Mode: ${MODE} ---"
    mpirun -np 1 python scripts/loco_ridge.py \
        --subject ${SUBJECT} \
        --rois V1 V2 V3 V4 \
        --mode ${MODE} \
        --alignment srm \
        --output_dir results/ridge
done

echo ""
echo "Done: $(date)"
