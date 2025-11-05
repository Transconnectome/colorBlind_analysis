#!/bin/bash
# Simpler parallel submission: Uses one script with environment variable
# More elegant than creating multiple copies

set -e

echo "=========================================="
echo "Parallel ROI Submission (Clean Method)"
echo "=========================================="
echo ""

# Check if naive_analysis.py exists
if [ ! -f "naive_analysis.py" ]; then
    echo "ERROR: naive_analysis.py not found"
    exit 1
fi

# ROIs to test
ROIS=("V1" "V2" "V3" "hV4")

echo "Testing ROIs in parallel: ${ROIS[@]}"
echo ""

# Create logs directory
mkdir -p logs

# Submit jobs
echo "Submitting jobs..."
JOB_IDS=()

for ROI in "${ROIS[@]}"; do
    # Create a temporary wrapper script for this ROI
    cat > "run_${ROI}.sh" <<EOF
#!/bin/bash
#SBATCH --job-name=naive_${ROI}
#SBATCH --output=logs/naive_${ROI}_%j.out
#SBATCH --error=logs/naive_${ROI}_%j.err
#SBATCH --time=00:30:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=4

echo "Starting ${ROI} ROI analysis..."
echo "Working directory: \$(pwd)"
echo ""

# Clear cache for this ROI
mkdir -p hrf_test_outputs/cache_${ROI}
rm -f hrf_test_outputs/cache_${ROI}/*.joblib
rm -f hrf_test_outputs/cache_${ROI}/*.csv
echo "Cleared cache: hrf_test_outputs/cache_${ROI}/"
echo ""

# Modify ROI_SELECTION in naive_analysis.py on-the-fly
sed 's/ROI_SELECTION = \[.*\]/ROI_SELECTION = ["${ROI}"]/' naive_analysis.py > naive_analysis_${ROI}_temp.py

# Run analysis
python naive_analysis_${ROI}_temp.py

# Clean up temp file
rm -f naive_analysis_${ROI}_temp.py

echo ""
echo "${ROI} analysis complete!"
EOF

    # Submit job
    JOB_ID=$(sbatch "run_${ROI}.sh" 2>&1 | grep -oP 'Submitted batch job \K\d+' || echo "FAILED")

    if [ "$JOB_ID" != "FAILED" ]; then
        JOB_IDS+=($JOB_ID)
        echo "  ✅ ${ROI}: Job ${JOB_ID} submitted"
    else
        echo "  ❌ ${ROI}: Submission failed"
    fi
done

echo ""
echo "=========================================="
echo "Submitted ${#JOB_IDS[@]} jobs"
echo "=========================================="
echo ""
echo "Job IDs: ${JOB_IDS[@]}"
echo ""

# Save job IDs
echo "${JOB_IDS[@]}" > .parallel_roi_jobs.txt

echo "Monitor progress:"
echo "  squeue -u \$USER"
echo ""
echo "Check logs:"
echo "  tail -f logs/naive_V2_*.out"
echo ""
echo "Wait for all to complete:"
echo "  watch 'squeue -u \$USER | grep naive'"
echo ""
echo "When done, check results:"
echo "  python test_roi_reconstruction.py"
