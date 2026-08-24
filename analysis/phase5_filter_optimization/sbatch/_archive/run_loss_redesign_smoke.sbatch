#!/bin/bash
#SBATCH --job-name=loss_redesign_smoke
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/phase5_filter_optimization
#SBATCH --output=results/cycle_loss_redesign/slurm_%j.log

# Cycle 1-2 loss-redesign smoke run on server.
# Runs 2-component grid sweep with extended loss metrics for
#   CVD subjects (08, 09) + HC pool (01..06)
# across V1, V2, V4 ROIs. sub-07 excluded (no LOCO json in validation).

source /home/haba6030/.bashrc
conda activate nilearn

OUT_BASE=results/cycle_loss_redesign

for ROI in V4 V2 V1; do
    echo "=== ROI=${ROI} =================================================="
    python scripts/cycle_loss_redesign/loss_redesign_smoke.py \
        --subjects 08 09 01 02 03 04 05 06 \
        --roi ${ROI} \
        --bs_step 2.0 --bc_step 2.0 \
        --output_dir ${OUT_BASE}/${ROI}_full \
        --data_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010

    python scripts/cycle_loss_redesign/loss_redesign_smoke.py \
        --subjects 08 09 01 02 03 04 05 06 \
        --roi ${ROI} \
        --bs_step 2.0 --bc_step 2.0 --bs_max 20.0 --bc_max 20.0 \
        --output_dir ${OUT_BASE}/${ROI}_restricted \
        --data_dir /scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
done

echo "ALL DONE"
