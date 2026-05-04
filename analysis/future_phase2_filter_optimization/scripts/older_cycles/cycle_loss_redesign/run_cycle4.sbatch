#!/bin/bash
#SBATCH --job-name=cycle4_loss
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/logs/cycle4_loss_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/logs/cycle4_loss_%j.err
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --chdir=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/scripts/cycle_loss_redesign

# ---------------------------------------------------------------------------
# Cycle 4 — extended grid (β_s ∈ [0,80], β_c ∈ [-60,60]) + alt metrics
# Run on hV4 (V4), V1, V2 sequentially. Subject set:
#   CVD: 08, 09, 10
#   HC : 01, 02, 03, 04, 05, 06   (sub-07 excluded — no LOCO json)
# ---------------------------------------------------------------------------

source /home/haba6030/miniconda3/etc/profile.d/conda.sh
conda activate nilearn

DATA_DIR=/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010
OUT_BASE=/scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/results/cycle_loss_redesign

for ROI in V4 V1 V2; do
    OUT_DIR=${OUT_BASE}/cycle4_extended_${ROI}
    mkdir -p "$OUT_DIR"
    echo "=== ROI ${ROI} ==="
    python cycle4_alt_metrics.py \
        --roi ${ROI} \
        --data_dir ${DATA_DIR} \
        --output_dir ${OUT_DIR} \
        --bs_max 80 --bc_max 60 \
        --bs_step 2 --bc_step 2
done

echo "Done"
