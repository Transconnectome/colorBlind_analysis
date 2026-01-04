#!/bin/bash
#SBATCH --job-name=proc_recon_train_b32
#SBATCH --output=logs/group_level/proc_recon_train_b32_%j.out
#SBATCH --error=logs/group_level/proc_recon_train_b32_%j.err
#SBATCH --time=12:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=4
#SBATCH --qos=shared
#SBATCH --nodelist=node2

# Procrustes Reconstruction: HC Training (baseline32)
# Train common W matrix for HC subjects (03, 05, 06, 07)
# NOTE: sub-02 excluded due to Procrustes analysis issues
# Configuration: baseline32_deob_determin (32 color bins)

echo "=========================================="
echo "Procrustes Reconstruction: HC Training"
echo "Configuration: baseline32_deob_determin"
echo "=========================================="
echo "Start time: $(date)"
echo ""

source ~/.bashrc
conda activate nilearn

cd /scratch/connectome/haba6030/colorBlind

# Create output directory
mkdir -p results/group_level/procrustes_reconstruction_baseline32
mkdir -p logs/group_level

echo "Training HC common W matrix for all ROIs (baseline32)..."
echo ""

for roi in V1 V2 V3 hV4; do
    echo "----------------------------------------"
    echo "Training ROI: $roi (baseline32)"
    echo "----------------------------------------"

    python analysis/group_level/reconstruction_with_procrustes.py \
        --mode train \
        --roi $roi \
        --hc-subjects 03 05 06 07 \
        --timestamp baseline32_deob_determin \
        --dataset deoblique_v2 \
        --output-dir results/group_level/procrustes_reconstruction_baseline32/

    if [ $? -eq 0 ]; then
        echo "✓ $roi training completed successfully"
    else
        echo "✗ $roi training failed"
    fi
    echo ""
done

echo "=========================================="
echo "All ROI training completed (baseline32)!"
echo "End time: $(date)"
echo "=========================================="

# Display voxel counts
echo ""
echo "=========================================="
echo "Voxel Counts Summary (baseline32)"
echo "=========================================="

for roi in V1 V2 V3 hV4; do
    model_file="results/group_level/procrustes_reconstruction_baseline32/$roi/procrustes_model.pkl"
    if [ -f "$model_file" ]; then
        echo "$roi: Checking voxel count..."
        python -c "
import pickle
model = pickle.load(open('$model_file', 'rb'))
print(f'  n_voxels: {model[\"n_voxels\"]}')
print(f'  W shape: {model[\"W_common\"].shape}')
"
    fi
done
