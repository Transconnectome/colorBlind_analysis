#!/bin/bash
#SBATCH --job-name=proc_recon_test_b32
#SBATCH --output=logs/group_level/proc_recon_test_b32_%j.out
#SBATCH --error=logs/group_level/proc_recon_test_b32_%j.err
#SBATCH --time=8:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --qos=shared
#SBATCH --nodelist=node2

# Procrustes Reconstruction: CVD Testing (WITH ALIGNMENT, baseline32)
# Apply HC common W to CVD subjects (08, 09, 10) with Procrustes alignment
# Configuration: baseline32_deob_determin

echo "=========================================="
echo "CVD Testing: WITH ALIGNMENT"
echo "Configuration: baseline32_deob_determin"
echo "=========================================="
echo "Start time: $(date)"
echo ""

source ~/.bashrc
conda activate nilearn

cd /scratch/connectome/haba6030/colorBlind

echo "Testing CVD subjects with alignment (baseline32)..."
echo ""

for roi in V1 V2 V3 hV4; do
    echo "----------------------------------------"
    echo "Testing ROI: $roi (WITH ALIGNMENT, baseline32)"
    echo "----------------------------------------"

    # Check if HC model exists
    if [ ! -f "results/group_level/procrustes_reconstruction_baseline32/$roi/procrustes_model.pkl" ]; then
        echo "✗ HC model not found for $roi - skipping"
        continue
    fi

    python analysis/group_level/reconstruction_with_procrustes.py \
        --mode test \
        --roi $roi \
        --cvd-subjects 08 09 10 \
        --timestamp baseline32_deob_determin \
        --dataset deoblique_v2 \
        --output-dir results/group_level/procrustes_reconstruction_baseline32/

    if [ $? -eq 0 ]; then
        echo "✓ $roi testing completed successfully"
    else
        echo "✗ $roi testing failed"
    fi
    echo ""
done

echo "=========================================="
echo "All ROI testing completed (baseline32)!"
echo "End time: $(date)"
echo "=========================================="

# Display results summary
echo ""
echo "=========================================="
echo "Results Summary (baseline32)"
echo "=========================================="

for roi in V1 V2 V3 hV4; do
    csv_file="results/group_level/procrustes_reconstruction_baseline32/$roi/cvd_reconstruction_errors.csv"
    if [ -f "$csv_file" ]; then
        echo ""
        echo "$roi (baseline32, WITH ALIGNMENT):"
        cat "$csv_file"
    fi
done
