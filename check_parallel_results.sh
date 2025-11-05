#!/bin/bash
# Check the status and results of parallel ROI jobs

echo "=========================================="
echo "Parallel ROI Results Checker"
echo "=========================================="
echo ""

ROIS=("V1" "V2" "V3" "hV4")

# Check if jobs are still running
echo "Job Status:"
echo "----------------------------------------"
RUNNING=$(squeue -u $USER | grep -E "naive_V[1-4]|naive_hV4" | wc -l)

if [ $RUNNING -gt 0 ]; then
    echo "⏳ $RUNNING jobs still running..."
    squeue -u $USER | grep -E "naive_V[1-4]|naive_hV4" | head -20
    echo ""
    echo "Check again in a few minutes or run: watch -n 10 '$0'"
    exit 0
else
    echo "✅ All jobs completed!"
fi

echo ""
echo "=========================================="
echo "Results Summary"
echo "=========================================="
echo ""

# Check cache files for each ROI
for ROI in "${ROIS[@]}"; do
    CACHE_DIR="hrf_test_outputs/cache_${ROI}"
    CSV_FILE="$CACHE_DIR/reconstruction_results.csv"

    echo "ROI: $ROI"
    echo "----------------------------------------"

    if [ -f "$CSV_FILE" ]; then
        echo "✅ Results found: $CSV_FILE"

        # Extract results from CSV
        echo ""
        echo "Run-by-run results:"
        tail -n +2 "$CSV_FILE" | while IFS=, read run hit_rate p_value threshold; do
            if [ ! -z "$run" ]; then
                printf "  Run %s: hit=%.3f, p=%.3f\n" "$run" "$hit_rate" "$p_value"
            fi
        done

        # Calculate mean (using awk)
        MEAN_HIT=$(tail -n +2 "$CSV_FILE" | awk -F, '{sum+=$2; count++} END {printf "%.3f", sum/count}')
        MEAN_P=$(tail -n +2 "$CSV_FILE" | awk -F, '{sum+=$3; count++} END {printf "%.3f", sum/count}')

        echo ""
        printf "  MEAN: hit=%.3f, p=%.3f " "$MEAN_HIT" "$MEAN_P"

        # Check if significant
        if (( $(echo "$MEAN_P < 0.05" | bc -l) )); then
            echo "✅ SIGNIFICANT!"
        elif (( $(echo "$MEAN_P < 0.10" | bc -l) )); then
            echo "⚠️  Nearly significant"
        else
            echo "❌ Not significant"
        fi
    else
        echo "❌ No results found - job may have failed"
        echo "   Check log: logs/naive_${ROI}_*.out"
    fi

    echo ""
done

echo "=========================================="
echo "Detailed Comparison"
echo "=========================================="
echo ""
echo "Running test_roi_reconstruction.py for full comparison..."
python test_roi_reconstruction.py

echo ""
echo "=========================================="
echo "Log Files"
echo "=========================================="
echo ""
echo "To check detailed logs for any ROI:"
for ROI in "${ROIS[@]}"; do
    LATEST_LOG=$(ls -t logs/naive_${ROI}_*.out 2>/dev/null | head -1)
    if [ ! -z "$LATEST_LOG" ]; then
        echo "  ${ROI}: tail -100 $LATEST_LOG"
    fi
done

echo ""
echo "=========================================="
echo "Next Steps"
echo "=========================================="
echo ""
echo "If any ROI achieved p<0.05:"
echo "  1. Use that ROI for future analyses"
echo "  2. Move to Step 2: CVD correction filter design"
echo ""
echo "If none reached significance:"
echo "  1. Try FIR model (bh_anal.py)"
echo "  2. Optimize lambda parameter"
echo "  3. Consider waiting for main experiment data"
