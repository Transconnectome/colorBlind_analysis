#!/bin/bash
# Script to test all ROIs (V1, V2, V3, hV4) in parallel using SLURM job arrays
# Each ROI analysis runs independently with its own cache directory

set -e  # Exit on error

echo "=========================================="
echo "Parallel ROI Testing Script"
echo "=========================================="
echo ""

# ROIs to test
ROIS=("V1" "V2" "V3" "hV4")

echo "Will test the following ROIs in parallel:"
for roi in "${ROIS[@]}"; do
    echo "  - $roi"
done
echo ""

# Check if naive_analysis.py exists
if [ ! -f "naive_analysis.py" ]; then
    echo "ERROR: naive_analysis.py not found in current directory"
    exit 1
fi

# Create separate analysis scripts for each ROI
echo "Creating temporary analysis scripts..."
for roi in "${ROIS[@]}"; do
    cp naive_analysis.py "naive_analysis_${roi}.py"

    # Replace ROI_SELECTION line
    sed -i.bak "s/ROI_SELECTION = \[.*\]/ROI_SELECTION = [\"${roi}\"]/" "naive_analysis_${roi}.py"

    echo "  Created: naive_analysis_${roi}.py"
done
echo ""

# Create sbatch scripts for each ROI
echo "Creating SLURM batch scripts..."
for roi in "${ROIS[@]}"; do
    cat > "sbatch_${roi}.sub" <<EOF
#!/bin/bash
#SBATCH --job-name=naive_${roi}
#SBATCH --output=logs/naive_${roi}_%j.out
#SBATCH --error=logs/naive_${roi}_%j.err
#SBATCH --time=00:30:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4

# ROI-specific analysis: ${roi}
echo "Starting ${roi} ROI analysis..."
echo "Output directory: hrf_test_outputs/cache_${roi}/"
echo ""

# Delete old cache for this ROI
rm -f hrf_test_outputs/cache_${roi}/*.joblib
rm -f hrf_test_outputs/cache_${roi}/*.csv
echo "Cleared cache for ${roi}"
echo ""

# Run analysis
python naive_analysis_${roi}.py

echo ""
echo "${roi} analysis complete!"
EOF

    chmod +x "sbatch_${roi}.sub"
    echo "  Created: sbatch_${roi}.sub"
done
echo ""

# Submit all jobs
echo "=========================================="
echo "Submitting jobs to SLURM..."
echo "=========================================="
echo ""

JOB_IDS=()
for roi in "${ROIS[@]}"; do
    job_id=$(sbatch "sbatch_${roi}.sub" | awk '{print $4}')
    JOB_IDS+=($job_id)
    echo "  Submitted ${roi}: Job ID ${job_id}"
done
echo ""

echo "=========================================="
echo "All jobs submitted!"
echo "=========================================="
echo ""
echo "Job IDs: ${JOB_IDS[@]}"
echo ""
echo "Monitor progress:"
echo "  squeue -u \$USER"
echo ""
echo "Check individual logs:"
for roi in "${ROIS[@]}"; do
    echo "  tail -f logs/naive_${roi}_*.out"
done
echo ""
echo "After all complete, compare results:"
echo "  python test_roi_reconstruction.py"
echo ""

# Save job IDs to file
echo "${JOB_IDS[@]}" > parallel_roi_jobs.txt
echo "Job IDs saved to: parallel_roi_jobs.txt"
echo ""

echo "=========================================="
echo "Waiting for jobs to complete..."
echo "=========================================="
echo ""
echo "Run this to check status:"
echo "  watch squeue -u \$USER"
echo ""
echo "Or wait for all jobs:"
echo "  squeue -u \$USER | grep -E '$(IFS=\|; echo "${ROIS[*]}")'"
