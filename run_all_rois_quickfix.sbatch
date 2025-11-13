#!/bin/bash
#SBATCH -J all_rois_quickfix
#SBATCH -c 8
#SBATCH --mem=128G
#SBATCH -t 12:00:00
#SBATCH -o logs/all_rois_quickfix_%j.out
#SBATCH -e logs/all_rois_quickfix_%j.err
#SBATCH --nodelist=node2

# Run Quick Fix Method (Winner: 52.4° novel error) on All Visual ROIs
# This method uses data-driven optimal delay from universal HRF

echo "========================================================================"
echo "Running Quick Fix Method on All Visual ROIs"
echo "========================================================================"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: ${SLURM_NODELIST}"
echo "Start time: $(date)"
echo "========================================================================"
echo

source $(conda info --base)/etc/profile.d/conda.sh
conda activate nilearn

mkdir -p logs

# Process each ROI sequentially
for ROI in V1 V2 V3 V4 hV4 VO1; do
    echo "========================================================================"
    echo "Processing ROI: ${ROI}"
    echo "Time: $(date)"
    echo "========================================================================"

    python fir_reconstruction_universal_hrf.py \
        --roi ${ROI} \
        --use-pca \
        --n-components 20 \
        --save-zmaps

    if [ $? -eq 0 ]; then
        echo "✓ ${ROI} completed successfully"
    else
        echo "✗ ${ROI} failed with exit code $?"
    fi
    echo
done

# Summary of all results
echo
echo "========================================================================"
echo "ALL ROIs COMPLETE - SUMMARY RESULTS"
echo "========================================================================"
echo

for ROI in V1 V2 V3 V4 hV4 VO1; do
    if [ -f "derivatives/sub-01/fir_reconstruction/${ROI}_universal_hrf/summary.csv" ]; then
        echo "----------------------------------------"
        echo "${ROI}:"
        echo "----------------------------------------"
        tail -1 "derivatives/sub-01/fir_reconstruction/${ROI}_universal_hrf/summary.csv" | \
            awk -F, '{print "  Voxels: " $3 "\n  Optimal delay: " $4 " TRs\n  Classification: " $7*100 "%\n  Novel error: " $9 "°"}'
        echo
    else
        echo "${ROI}: FAILED - no results file"
        echo
    fi
done

echo "========================================================================"
echo "End time: $(date)"
echo "========================================================================"

exit 0
