#!/bin/bash
#SBATCH --job-name=loco_gp
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --array=1-10%5
#SBATCH --output=logs/gp_%a.out
#SBATCH --error=logs/gp_%a.err
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase3_decoder_comparing/LOCO_trials

source ~/.bashrc
conda activate nilearn

SUBJECTS=(01 02 03 04 05 06 07 08 09 10)
SUBJECT=${SUBJECTS[$((SLURM_ARRAY_TASK_ID - 1))]}

echo "=== GP LOCO: sub-${SUBJECT} ==="
echo "Start: $(date)"

# Run all subphases
mpirun -np 1 python scripts/loco_gp.py \
    --subject ${SUBJECT} \
    --rois V1 V2 V3 V4 \
    --subphase all \
    --alignment srm \
    --output_dir results/gp

echo ""
echo "Done: $(date)"
