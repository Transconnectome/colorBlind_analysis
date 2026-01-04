#!/bin/bash
#SBATCH --job-name=proc_recon_train
#SBATCH --output=logs/group_level/proc_recon_train_%j.out
#SBATCH --error=logs/group_level/proc_recon_train_%j.err
#SBATCH --time=12:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --qos=shared
#SBATCH --nodelist=node2

# Procrustes Reconstruction: HC Training
# Train common W matrix for HC subjects (03, 05, 06, 07)
# NOTE: sub-02 excluded due to Procrustes analysis issues

echo "=========================================="
echo "Procrustes Reconstruction: HC Training"
echo "=========================================="
echo "Start time: $(date)"
echo ""

source ~/.bashrc
conda activate nilearn

cd /scratch/connectome/haba6030/colorBlind

# Create output directory
mkdir -p results/group_level/procrustes_reconstruction
mkdir -p logs/group_level

echo "Training HC common W matrix for all ROIs..."
echo ""

for roi in V1 V2 V3 hV4; do
    echo "----------------------------------------"
    echo "Training ROI: $roi"
    echo "----------------------------------------"

    python analysis/group_level/reconstruction_with_procrustes.py \
        --mode train \
        --roi $roi \
        --hc-subjects 03 05 06 07 \
        --timestamp baseline81_deob_determin \
        --dataset deoblique_v2 \
        --output-dir results/group_level/procrustes_reconstruction/

    if [ $? -eq 0 ]; then
        echo "✓ $roi training completed successfully"
    else
        echo "✗ $roi training failed"
    fi
    echo ""
done

echo "=========================================="
echo "All ROI training completed!"
echo "End time: $(date)"
echo "=========================================="
