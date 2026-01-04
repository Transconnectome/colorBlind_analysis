#!/bin/bash
#SBATCH --job-name=proc_recon_test
#SBATCH --output=logs/group_level/proc_recon_test_%j.out
#SBATCH --error=logs/group_level/proc_recon_test_%j.err
#SBATCH --time=8:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4
#SBATCH --qos=shared
#SBATCH --nodelist=node2

# Procrustes Reconstruction: CVD Testing
# Apply HC common W to CVD subjects (08, 09, 10)

echo "=========================================="
echo "Procrustes Reconstruction: CVD Testing"
echo "=========================================="
echo "Start time: $(date)"
echo ""

source ~/.bashrc
conda activate nilearn

cd /scratch/connectome/haba6030/colorBlind

echo "Testing CVD subjects with HC common W..."
echo ""

for roi in V1 V2 V3 hV4; do
    echo "----------------------------------------"
    echo "Testing ROI: $roi"
    echo "----------------------------------------"

    # Check if HC model exists
    if [ ! -f "results/group_level/procrustes_reconstruction/$roi/procrustes_model.pkl" ]; then
        echo "✗ HC model not found for $roi - skipping"
        continue
    fi

    python analysis/group_level/reconstruction_with_procrustes.py \
        --mode test \
        --roi $roi \
        --cvd-subjects 08 09 10 \
        --timestamp baseline81_deob_determin \
        --dataset deoblique_v2 \
        --output-dir results/group_level/procrustes_reconstruction/

    if [ $? -eq 0 ]; then
        echo "✓ $roi testing completed successfully"
    else
        echo "✗ $roi testing failed"
    fi
    echo ""
done

echo "=========================================="
echo "All ROI testing completed!"
echo "End time: $(date)"
echo "=========================================="

# Display results summary
echo ""
echo "=========================================="
echo "Results Summary"
echo "=========================================="

for roi in V1 V2 V3 hV4; do
    csv_file="results/group_level/procrustes_reconstruction/$roi/cvd_reconstruction_errors.csv"
    if [ -f "$csv_file" ]; then
        echo ""
        echo "$roi:"
        cat "$csv_file"
    fi
done
